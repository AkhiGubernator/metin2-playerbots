# -*- coding: utf-8 -*-
"""The nicknames the bots wear, and the SQL that hands them out.

"Pozdrawiam pana botarek7 jest kotem ale brzmi jak bot" - kiciamol, and
jaroszv2 right after: "najgorzej jak biegasz wsrod botow i szukasz tego jednego
nicku a zlewaja sie wszystkie z tymi numerkami". A world of botX7 reads as a
world of bots however well they behave.

The pool is one list, written by a person: Iwakura's, from screenshots of the
Polish servers of 2010-2012 (11 September 2026, "tu jest postaranie"). The
earlier pool - jaksiezabic's list, the first Iwakura list and the names
composed from their words - is gone, and so is the class-and-sex pairing:
Tieru asked for the list as written, for everybody, and for every bot named
from the old pool to be renamed from this one ("te wszystkie stare nicki z
bazy powinny zostac wywalone, ta lista powinna byc aktywna").

A cohort larger than the list gets the list again with v2, then v3 behind the
name, as Tieru asked, until more names are written. Names are handed out in
list order by PID, so a bot keeps its name across regenerations as long as the
list in front of it does not change; a changed list is a new pool version, and
every bot whose name came from an older version is renamed on the next start.

Nothing about renaming is dangerous, and it is worth writing down why:
CPlayerBotManager::LoadRegisteredBots accepts a character by its account login
(playerbot_NNN), its social id and its player_index row, and never looks at the
name; both panels ask the account too; and generate_seed.py treats a renamed
character as still the character the registry describes as long as
common.playerbot_name_history agrees. So the name is the one part of a bot's
identity nothing depends on.

    python linux-port/overlays/playerbot/tools/generate_bot_names.py
"""
from __future__ import print_function

import hashlib
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OVERLAY = os.path.abspath(os.path.join(HERE, '..'))
REPO = os.path.abspath(os.path.join(OVERLAY, '..', '..', '..'))
SOURCE = os.path.join(OVERLAY, 'data', 'bot_names_iwakura.txt')
OUT_SQL = os.path.join(OVERLAY, 'sql', 'playerbot_names.sql')
MIRROR_SQL = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot',
                          'playerbot_names.sql')

# Room for the 2500 seeded bots and for an operator who grows the cohort.
TARGET = 3600
# common/length.h: CHARACTER_NAME_MAX_LEN is 24 on both engines.
MAX_LEN = 24
# A name that gets a v2/v3 behind it must still fit.
SUFFIX_MAX_BASE = MAX_LEN - 2

# What must never be in the pool: crude entries, and anything that reads as
# staff. "bot" is allowed on purpose - botmrok, WcaleNieBot and OdpalamBotaPL
# are jokes people made, and nothing identifies a bot by its name any more.
BLOCKED_STEMS = ('ksujebomoge',)
BLOCKED_PREFIXES = ('gm', 'admin', 'system', 'serwer', 'server')


def clean(name):
    """The name as the engine will take it, or None.

    check_name_alphabet (locale_service.cpp) takes letters and digits and
    nothing else, so an underscore is dropped rather than refused ("Miecz_PL"
    is "MieczPL"); a name of digits alone is left out - it reads as a number.
    """
    name = re.sub(r'[^A-Za-z0-9]', '', name.strip())
    if len(name) < 3 or len(name) > MAX_LEN:
        return None
    if not re.search(r'[A-Za-z]', name):
        return None
    low = name.lower()
    if any(stem in low for stem in BLOCKED_STEMS):
        return None
    if any(low.startswith(p) for p in BLOCKED_PREFIXES):
        return None
    return name


def read_list(path):
    out = []
    seen = set()
    dropped = []
    for line in io.open(path, encoding='utf-8'):
        raw = line.strip()
        if not raw or raw.startswith('#'):
            continue
        name = clean(raw)
        if name is None:
            dropped.append(raw)
            continue
        if name.lower() in seen:
            continue
        seen.add(name.lower())
        out.append(name)
    return out, dropped


def extend(base, target):
    """The list again with v2, v3 ... behind the names, up to target."""
    pool = list(base)
    seen = set(n.lower() for n in base)
    suffix = 2
    while len(pool) < target and suffix < 10:
        for name in base:
            if len(pool) >= target:
                break
            candidate = name[:SUFFIX_MAX_BASE] + 'v%d' % suffix
            if candidate.lower() in seen:
                continue
            seen.add(candidate.lower())
            pool.append(candidate)
        suffix += 1
    return pool


def sql_literal(value):
    return "'" + value.replace('\\', '\\\\').replace("'", "''") + "'"


TEMPLATE = u"""-- Nicknames for the playerbots. GENERATED - edit
-- linux-port/overlays/playerbot/data/bot_names_iwakura.txt and re-run
-- linux-port/overlays/playerbot/tools/generate_bot_names.py.
--
-- Applied by mariadb/playerbot/apply.sh after the seed, guarded by
-- @playerbot_human_names, which apply.sh sets from M2_PLAYERBOT_HUMAN_NAMES:
--
--   1        every bot wears a name from this pool, version @@VERSION@@ (default)
--   0        leave every name exactly as it is
--   restore  put the seed names back and forget the renames
--
-- Only a character whose account login is playerbot_NNN is ever touched: no
-- character of a person is reachable from here. Names go out in list order by
-- PID, so a bot keeps its name for as long as the list in front of it does not
-- change; a bot whose name came from an older version of the pool is renamed
-- on the next start (common.playerbot_name_history.pool_version says which).
-- The seed name stays in that table, which is what makes 'restore' possible.

-- A temporary table needs a default database and the client this is fed to has
-- selected none; playerbots_seed.sql opens the same way and for the same
-- reason. Every other table is named in full.
USE player;

CREATE TABLE IF NOT EXISTS common.playerbot_name_history (
    pid          INT UNSIGNED NOT NULL,
    seed_name    VARCHAR(24) NOT NULL,
    human_name   VARCHAR(24) NOT NULL,
    renamed_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (pid),
    KEY human_name (human_name)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
-- A world renamed by the first pool has no version column yet.
ALTER TABLE common.playerbot_name_history
    ADD COLUMN IF NOT EXISTS pool_version VARCHAR(16) NOT NULL DEFAULT '';

SET @playerbot_human_names = IFNULL(@playerbot_human_names, '1');
SET @playerbot_pool_version = @@VERSION_LITERAL@@;

-- --------------------------------------------------------------------------
-- restore: the seed name goes back, and only onto a character that still
-- wears the name this table handed it. A bot renamed again by hand afterwards
-- is somebody's deliberate choice and is left alone.
-- --------------------------------------------------------------------------
UPDATE player.player AS p
  JOIN common.playerbot_name_history AS h ON h.pid = p.id
   SET p.name = h.seed_name
 WHERE @playerbot_human_names = 'restore'
   AND BINARY p.name = BINARY h.human_name;

DELETE FROM common.playerbot_name_history
 WHERE @playerbot_human_names = 'restore';

SELECT CONCAT('playerbot names: restored ', ROW_COUNT(), ' seed name(s)')
       AS playerbot_names_note
  FROM DUAL
 WHERE @playerbot_human_names = 'restore';

-- --------------------------------------------------------------------------
-- The pool: @@BASE@@ names as written, then the same names with v2, v3 behind
-- them up to @@COUNT@@, in the order they were written.
-- --------------------------------------------------------------------------
DROP TEMPORARY TABLE IF EXISTS playerbot_name_pool;
CREATE TEMPORARY TABLE playerbot_name_pool (
    n    INT UNSIGNED NOT NULL PRIMARY KEY,
    name VARCHAR(24) NOT NULL,
    UNIQUE KEY name (name)
) ENGINE=MEMORY DEFAULT CHARSET=latin1;

@@VALUES@@

-- --------------------------------------------------------------------------
-- Who gets one, and which. Every bot without a name from this version of the
-- pool waits, numbered by PID; every pool name not worn by somebody's own
-- character is free, numbered by its place in the list; the two are joined
-- on the number. One statement, stable: the first free name goes to the
-- lowest waiting PID. A bot's current name never blocks a pool name - all
-- of them are being renamed at once - and player.name is indexed, not
-- unique, so the check against people's characters is the only one there is.
-- --------------------------------------------------------------------------
DROP TEMPORARY TABLE IF EXISTS playerbot_name_plan;
CREATE TEMPORARY TABLE playerbot_name_plan (
    pid        INT UNSIGNED NOT NULL PRIMARY KEY,
    seed_name  VARCHAR(24) NOT NULL,
    human_name VARCHAR(24) NOT NULL,
    UNIQUE KEY human_name (human_name)
) ENGINE=MEMORY DEFAULT CHARSET=latin1;

INSERT INTO playerbot_name_plan (pid, seed_name, human_name)
SELECT waiting.pid, waiting.seed_name, free.name
  FROM (
        SELECT p.id AS pid,
               IFNULL(h.seed_name, p.name) AS seed_name,
               ROW_NUMBER() OVER (ORDER BY p.id) AS rn
          FROM player.player AS p
          JOIN account.account AS a ON a.id = p.account_id
          LEFT JOIN common.playerbot_name_history AS h ON h.pid = p.id
         WHERE LEFT(a.login, 10) = 'playerbot_'
           AND (h.pid IS NULL
                OR h.pool_version <> @playerbot_pool_version
                OR BINARY p.name <> BINARY h.human_name)
       ) AS waiting
  JOIN (
        SELECT np.name,
               ROW_NUMBER() OVER (ORDER BY np.n) AS rn
          FROM playerbot_name_pool AS np
         WHERE NOT EXISTS (SELECT 1
                             FROM player.player AS px
                             JOIN account.account AS ax ON ax.id = px.account_id
                            WHERE px.name = np.name
                              AND LEFT(ax.login, 10) <> 'playerbot_')
       ) AS free
    ON free.rn = waiting.rn
 WHERE @playerbot_human_names = '1';

INSERT INTO common.playerbot_name_history (pid, seed_name, human_name, pool_version, renamed_at)
SELECT pid, seed_name, human_name, @playerbot_pool_version, NOW() FROM playerbot_name_plan
    ON DUPLICATE KEY UPDATE human_name = VALUES(human_name),
                            pool_version = VALUES(pool_version),
                            renamed_at = VALUES(renamed_at);

UPDATE player.player AS p
  JOIN playerbot_name_plan AS pl ON pl.pid = p.id
   SET p.name = pl.human_name;

-- HAVING, not WHERE: the aggregate returns one row over an empty plan, and a
-- 'restore' run would otherwise report "gave 0" straight after "restored 2500".
SELECT CONCAT('playerbot names: gave ', COUNT(*), ' bot(s) a name from pool @@VERSION@@')
       AS playerbot_names_note
  FROM playerbot_name_plan
HAVING @playerbot_human_names = '1';

-- A cohort larger than the pool is the one way this runs out; say so rather
-- than leaving an operator to wonder why some bots kept their old names.
SELECT CONCAT('playerbot names: WARNING ', COUNT(*),
              ' bot(s) got no name - the pool of @@COUNT@@ is used up')
       AS playerbot_names_note
  FROM player.player AS p
  JOIN account.account AS a ON a.id = p.account_id
  LEFT JOIN common.playerbot_name_history AS h ON h.pid = p.id
 WHERE @playerbot_human_names = '1'
   AND LEFT(a.login, 10) = 'playerbot_'
   AND (h.pid IS NULL OR h.pool_version <> @playerbot_pool_version)
HAVING COUNT(*) > 0;

DROP TEMPORARY TABLE IF EXISTS playerbot_name_plan;
DROP TEMPORARY TABLE IF EXISTS playerbot_name_pool;
"""


def render(base, pool, version):
    rows = ['(%d,%s)' % (i, sql_literal(n)) for i, n in enumerate(pool, start=1)]
    chunks = []
    for start in range(0, len(rows), 100):
        chunks.append('INSERT INTO playerbot_name_pool (n, name) VALUES\n    ' +
                      ',\n    '.join(rows[start:start + 100]) + ';')
    text = TEMPLATE
    text = text.replace('@@VERSION_LITERAL@@', sql_literal(version))
    text = text.replace('@@VERSION@@', version)
    text = text.replace('@@BASE@@', str(len(base)))
    text = text.replace('@@COUNT@@', str(len(pool)))
    text = text.replace('@@VALUES@@', '\n'.join(chunks))
    return text


def main():
    base, dropped = read_list(SOURCE)
    if not base:
        print('brak nickow w %s' % SOURCE)
        return 1
    version = hashlib.sha256('\n'.join(n.lower() for n in base).encode('utf-8')).hexdigest()[:12]
    pool = extend(base, TARGET)
    text = render(base, pool, version)
    for path in (OUT_SQL, MIRROR_SQL):
        directory = os.path.dirname(path)
        if not os.path.isdir(directory):
            os.makedirs(directory)
        io.open(path, 'w', encoding='utf-8', newline='\n').write(text)
    print('napisano %s: pula %s, %d nickow z listy, %d z dopiskiem vN (razem %d); odrzucone: %d'
          % (OUT_SQL, version, len(base), len(pool) - len(base), len(pool), len(dropped)))
    for d in dropped:
        print('  odrzucony: %r' % d)
    print('kopia:   %s' % MIRROR_SQL)
    return 0


if __name__ == '__main__':
    sys.exit(main())
