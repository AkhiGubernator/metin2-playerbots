import os
import time
from datetime import datetime
from pathlib import Path

import pymysql

INTERVAL = int(os.environ.get("SEBAN_COLLECTOR_INTERVAL", "300"))
# First retry after a failed snapshot, in seconds; doubled up to INTERVAL.
RETRY_MIN = 5
STATUS_GLOB = os.environ.get("PLAYERBOTS_STATUS_GLOB", "/opt/metin2/var/channel1/*/playerbot_status.tsv")


def connect():
    return pymysql.connect(host=os.environ.get("DB_HOST", "mariadb"), port=int(os.environ.get("DB_PORT", "3306")), user=os.environ["DB_USER"], password=os.environ["DB_PASSWORD"], charset="utf8mb4", autocommit=True)


def host_metrics(previous=None):
    try:
        with open("/host/proc/stat") as f:
            parts = f.readline().split()[1:]
        total = sum(map(int, parts)); idle = int(parts[3]) + int(parts[4])
        with open("/host/proc/meminfo") as f:
            mem = {line.split(":")[0]: int(line.split()[1]) for line in f if ":" in line}
        total_mb = mem["MemTotal"] // 1024; used_mb = (mem["MemTotal"] - mem.get("MemAvailable", mem.get("MemFree", 0))) // 1024
        disk = os.statvfs("/hostfs")
        disk_total_mb = (disk.f_blocks * disk.f_frsize) // (1024 * 1024)
        disk_used_mb = ((disk.f_blocks - disk.f_bavail) * disk.f_frsize) // (1024 * 1024)
        if previous:
            cpu = round(100 * (1 - (idle - previous[1]) / max(1, total - previous[0])), 1)
        else:
            with open("/host/proc/loadavg") as f:
                load_1m = float(f.read().split()[0])
            with open("/host/proc/cpuinfo") as f:
                cpu_count = max(1, sum(1 for line in f if line.startswith("processor")))
            cpu = round(min(100, 100 * load_1m / cpu_count), 1)
        return (total, idle), cpu, used_mb, total_mb, disk_used_mb, disk_total_mb
    except (OSError, KeyError, ValueError):
        return previous, 0, 0, 0, 0, 0


def init(cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_admin_queue (
      id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
      player_name VARCHAR(24) NOT NULL, cmd VARCHAR(32) NOT NULL,
      arg1 VARCHAR(255) NOT NULL DEFAULT '', arg2 VARCHAR(255) NOT NULL DEFAULT '',
      status VARCHAR(24) NOT NULL DEFAULT 'pending',
      created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      KEY pending (status, created), KEY player_status (player_name, status)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_settings (
      name VARCHAR(64) NOT NULL PRIMARY KEY, value VARCHAR(255) NOT NULL,
      updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP) ENGINE=InnoDB""")
    cur.execute("""INSERT IGNORE INTO player.web_seban_settings (name,value) VALUES
      ('panel_name','Metin2 Singleplayer'),('stuck_minutes','5'),('theme','ocean'),('monitor_mode','vps'),
      ('setup_complete','1'),('auth_enabled','0'),('auth_password_hash','')""")
    # One-time branding migration for deployments created before the public-ready build.
    cur.execute("UPDATE player.web_seban_settings SET value='Metin2 Singleplayer' WHERE name='panel_name' AND value='Mt2009'")
    # Single-player suite: no setup wizard, no passphrase - one player at their
    # own machine (Tieru, 13 September). Skip the wizard for installs seeded
    # before this; an operator can still turn auth on from the panel.
    cur.execute("UPDATE player.web_seban_settings SET value='1' WHERE name='setup_complete' AND value='0'")
    # socket0 added 2026-09-13 so a generic Skill Book (vnum 50300 -- the
    # actual skill lives only in socket0, see resolve_item_display_name in
    # app.py) shows up as distinct rows instead of one lump sum. Disposable
    # monitoring history, not player data, so a schema change here drops and
    # recreates rather than an in-place ALTER of the primary key.
    # SHOW COLUMNS on a table that is not there is an error (1146), not an
    # empty answer, and web_seban_shop_item_snapshot is new in 1.41.0: on
    # every install that never had it the check threw before the CREATE, the
    # table was never made and /economy/shops answered 500. information_schema
    # counts zero for a missing table instead (Playerbots 2.0.47).
    cur.execute("""SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='player'
      AND table_name='web_seban_item_snapshot' AND column_name='socket0'""")
    if cur.fetchone()[0] == 0:
        cur.execute("DROP TABLE IF EXISTS player.web_seban_item_snapshot")
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_item_snapshot (
      captured_at DATETIME NOT NULL, vnum INT UNSIGNED NOT NULL, socket0 INT NOT NULL DEFAULT 0,
      amount BIGINT UNSIGNED NOT NULL,
      PRIMARY KEY(captured_at,vnum,socket0), KEY(vnum,captured_at)) ENGINE=InnoDB""")
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_map_snapshot (
      captured_at DATETIME NOT NULL, map_index INT UNSIGNED NOT NULL, character_count INT UNSIGNED NOT NULL,
      PRIMARY KEY(captured_at,map_index), KEY(map_index,captured_at)) ENGINE=InnoDB""")
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_system_snapshot (
      captured_at DATETIME NOT NULL PRIMARY KEY, cpu_percent DECIMAL(5,1) NOT NULL,
      ram_percent DECIMAL(5,1) NOT NULL, ram_used_mb INT UNSIGNED NOT NULL, ram_total_mb INT UNSIGNED NOT NULL,
      disk_percent DECIMAL(5,1) NOT NULL DEFAULT 0, disk_used_mb INT UNSIGNED NOT NULL DEFAULT 0,
      disk_total_mb INT UNSIGNED NOT NULL DEFAULT 0) ENGINE=InnoDB""")
    cur.execute("ALTER TABLE player.web_seban_system_snapshot ADD COLUMN IF NOT EXISTS disk_percent DECIMAL(5,1) NOT NULL DEFAULT 0")
    cur.execute("ALTER TABLE player.web_seban_system_snapshot ADD COLUMN IF NOT EXISTS disk_used_mb INT UNSIGNED NOT NULL DEFAULT 0")
    cur.execute("ALTER TABLE player.web_seban_system_snapshot ADD COLUMN IF NOT EXISTS disk_total_mb INT UNSIGNED NOT NULL DEFAULT 0")
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_metric_snapshot (
      captured_at DATETIME NOT NULL, metric VARCHAR(64) NOT NULL, value BIGINT NOT NULL,
      PRIMARY KEY(captured_at,metric), KEY(metric,captured_at)) ENGINE=InnoDB""")
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_bot_position_snapshot (
      captured_at DATETIME NOT NULL, pid INT UNSIGNED NOT NULL, map_index INT UNSIGNED NOT NULL,
      x INT NOT NULL, y INT NOT NULL, PRIMARY KEY(captured_at,pid), KEY(pid,captured_at)) ENGINE=InnoDB""")
    # Offline shops (IkarusShop "stragany"): player.ikashop_offlineshop is one
    # row per open shop, player.item WHERE window='IKASHOP_OFFLINESHOP' is one
    # row per listed offer, and the offer's price for its whole stack (not
    # per unit) lives in that item's own ikashop_data JSON column
    # ({"yang":N,...}) -- there is no separate price/listing table for this
    # engine's offline shops, confirmed against a live test shop.
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_shop_snapshot (
      captured_at DATETIME NOT NULL, map_index INT UNSIGNED NOT NULL, empire TINYINT UNSIGNED NOT NULL,
      shop_count INT UNSIGNED NOT NULL, offer_count INT UNSIGNED NOT NULL,
      item_count BIGINT UNSIGNED NOT NULL, total_value BIGINT UNSIGNED NOT NULL,
      PRIMARY KEY(captured_at,map_index), KEY(map_index,captured_at)) ENGINE=InnoDB""")
    # Per-vnum history of what is offered in shops, so the shop page can show
    # a price/quantity trend and answer "was this item ever on the market"
    # for items with zero active offers right now -- web_seban_shop_snapshot
    # above only keeps the per-map/empire rollup, not individual vnums.
    # socket0 added 2026-09-13, same reason and same drop/recreate approach
    # as web_seban_item_snapshot above.
    cur.execute("""SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='player'
      AND table_name='web_seban_shop_item_snapshot' AND column_name='socket0'""")
    if cur.fetchone()[0] == 0:
        cur.execute("DROP TABLE IF EXISTS player.web_seban_shop_item_snapshot")
    cur.execute("""CREATE TABLE IF NOT EXISTS player.web_seban_shop_item_snapshot (
      captured_at DATETIME NOT NULL, vnum INT UNSIGNED NOT NULL, socket0 INT NOT NULL DEFAULT 0,
      offers INT UNSIGNED NOT NULL, total_units BIGINT UNSIGNED NOT NULL, total_value BIGINT UNSIGNED NOT NULL,
      PRIMARY KEY(captured_at,vnum,socket0), KEY(vnum,captured_at)) ENGINE=InnoDB""")


def live_positions():
    result = {}
    for path in Path("/").glob(STATUS_GLOB.lstrip("/")):
        try:
            if time.time() - path.stat().st_mtime > 25:
                continue
            for line in path.read_text(encoding="cp1250", errors="replace").splitlines()[1:]:
                values = line.split("\t", 13)
                if len(values) == 14:
                    result[int(values[0])] = (int(values[8]), int(values[9]), int(values[10]))
        except (OSError, ValueError):
            continue
    return result


def live_map_counts():
    counts = {}
    for index, _, _ in live_positions().values():
        counts[index] = counts.get(index, 0) + 1
    return counts


def collect(con, previous):
    now = datetime.now().replace(second=0, microsecond=0)
    previous, cpu, used, total, disk_used, disk_total = host_metrics(previous)
    ram = round(100 * used / total, 1) if total else 0
    disk_percent = round(100 * disk_used / disk_total, 1) if disk_total else 0
    with con.cursor() as cur:
        init(cur)
        cur.execute("""INSERT INTO player.web_seban_system_snapshot
          (captured_at,cpu_percent,ram_percent,ram_used_mb,ram_total_mb,disk_percent,disk_used_mb,disk_total_mb)
          VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
          ON DUPLICATE KEY UPDATE cpu_percent=VALUES(cpu_percent), ram_percent=VALUES(ram_percent),
            ram_used_mb=VALUES(ram_used_mb), ram_total_mb=VALUES(ram_total_mb), disk_percent=VALUES(disk_percent),
            disk_used_mb=VALUES(disk_used_mb), disk_total_mb=VALUES(disk_total_mb)""",
            (now, cpu, ram, used, total, disk_percent, disk_used, disk_total))
        for map_index, count in live_map_counts().items():
            cur.execute("INSERT IGNORE INTO player.web_seban_map_snapshot VALUES (%s,%s,%s)", (now, map_index, count))
        for pid, (map_index, x, y) in live_positions().items():
            cur.execute("INSERT IGNORE INTO player.web_seban_bot_position_snapshot VALUES (%s,%s,%s,%s,%s)", (now, pid, map_index, x, y))
        # Split by socket0 only for vnum 50300 (the generic Skill Book -- see
        # resolve_item_display_name in app.py): splitting every socketed
        # item this way would fragment ordinary equipment into one row per
        # gem combination for no reason, since only 50300's socket0 changes
        # what the item actually *is*.
        cur.execute("""INSERT IGNORE INTO player.web_seban_item_snapshot (captured_at,vnum,socket0,amount)
          SELECT %s, vnum, IF(vnum=50300, socket0, 0), SUM(count)
          FROM player.item GROUP BY vnum, IF(vnum=50300, socket0, 0)""", (now,))
        cur.execute("""INSERT IGNORE INTO player.web_seban_shop_snapshot
          (captured_at, map_index, empire, shop_count, offer_count, item_count, total_value)
          SELECT %s, o.map, pi.empire, COUNT(DISTINCT o.owner), COUNT(i.id),
                 COALESCE(SUM(i.count),0),
                 COALESCE(SUM(CAST(JSON_UNQUOTE(JSON_EXTRACT(i.ikashop_data,'$.yang')) AS UNSIGNED)),0)
          FROM player.ikashop_offlineshop o
          JOIN player.player p ON p.id = o.owner
          JOIN player.player_index pi ON pi.id = p.account_id
          LEFT JOIN player.item i ON i.owner_id = o.owner AND i.window = 'IKASHOP_OFFLINESHOP'
          GROUP BY o.map, pi.empire""", (now,))
        cur.execute("""INSERT IGNORE INTO player.web_seban_shop_item_snapshot (captured_at, vnum, socket0, offers, total_units, total_value)
          SELECT %s, vnum, IF(vnum=50300, socket0, 0), COUNT(*), SUM(count),
                 COALESCE(SUM(CAST(JSON_UNQUOTE(JSON_EXTRACT(ikashop_data,'$.yang')) AS UNSIGNED)),0)
          FROM player.item WHERE window = 'IKASHOP_OFFLINESHOP' GROUP BY vnum, IF(vnum=50300, socket0, 0)""", (now,))
        cur.execute("SELECT COALESCE(SUM(gold),0) FROM player.player WHERE name NOT IN ('[SA]Admin','Test')")
        yang = cur.fetchone()[0]
        cur.execute("INSERT IGNORE INTO player.web_seban_metric_snapshot VALUES (%s,'total_yang',%s)", (now, yang))
    return previous


def main():
    previous = None
    retry = RETRY_MIN
    while True:
        try:
            with connect() as con:
                previous = collect(con, previous)
                print("[seban-collector] snapshot complete", flush=True)
        except Exception as exc:
            # An update recreates this container and the database together,
            # and the database is often a few seconds behind: the first
            # attempt meets "Connection refused". Waiting the whole interval
            # after that left the panel without the tables the first snapshot
            # creates - a 500 on the front page for five minutes after every
            # update. A failure is retried in seconds, doubling up to the
            # interval.
            print(f"[seban-collector] {exc} (retry in {retry}s)", flush=True)
            time.sleep(retry)
            retry = min(INTERVAL, retry * 2)
            continue
        retry = RETRY_MIN
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
