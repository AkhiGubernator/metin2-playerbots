# -*- coding: utf-8 -*-
"""The pool of human nicknames the bots wear, and the SQL that hands them out.

"Pozdrawiam pana botarek7 jest kotem ale brzmi jak bot" - kiciamol, and
jaroszv2 right after: "najgorzej jak biegasz wsrod botow i szukasz tego jednego
nicku a zlewaja sie wszystkie z tymi numerkami". A world of botX7 reads as a
world of bots however well they behave.

The pool has two halves. The first is a list of 1500 nicknames written by
jaksiezabic for this server ("do lekkiej edycji" - his own words, and this is
that edit: five names are dropped, three for a crude pun and two for starting
with GM, which is not a thing a bot should appear to be). The second is composed
from the vocabulary of the first, because the cohort is 2500 and 1495 names do
not cover it - and the whole point was to stop bots sharing a shape, so the
second half is built from the same parts rather than from numbered variants.

Nothing about renaming is dangerous, and it is worth writing down why:
CPlayerBotManager::LoadRegisteredBots accepts a character by its account login
(playerbot_NNN), its social id and its player_index row, and never looks at the
name; both panels ask the account too; and generate_seed.py already treats a
renamed character as "not the character this registry describes" and leaves it
alone. So the name is the one part of a bot's identity nothing depends on.

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
COMMUNITY = os.path.join(OVERLAY, 'data', 'bot_names_community.txt')
OUT_SQL = os.path.join(OVERLAY, 'sql', 'playerbot_names.sql')
MIRROR_SQL = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot',
                          'playerbot_names.sql')

# Room for the 2500 seeded bots and for an operator who grows the cohort.
TARGET = 3600
# common/length.h: CHARACTER_NAME_MAX_LEN. player.name is varchar(24), and the
# client draws the name over the head, so shorter is better than exactly 24.
MAX_LEN = 20

# What must never be in the pool. Two crude entries and two that read as staff.
BLOCKED_STEMS = ('ksujebomoge', 'gmtomojwujek')
# A bot must not look like the thing the panels used to identify it by, or the
# rename would be pointless.
BLOCKED_PREFIXES = ('bot', 'gm', 'admin', 'mod', 'system', 'serwer', 'server')

# Composed from the vocabulary of the community list, grouped by the shape it
# is used in there. Deliberately no new words: the point is that a generated
# name is indistinguishable from a written one.
ADJECTIVES = [
    'Stary', 'Mlody', 'Szybki', 'Zly', 'Dobry', 'Gruby', 'Maly', 'Potezny',
    'Krwawy', 'Szalony', 'Mroczny', 'Wielki', 'Dziki', 'Zimny', 'Cichy',
    'Twardy', 'Ostry', 'Wesoly', 'Smutny', 'Chytry',
]
NOUNS = [
    'Rycerz', 'Wojek', 'Smok', 'Miecz', 'Topor', 'Wlucznia', 'Dzik', 'Karp',
    'Rzeznik', 'Zabojca', 'Morderca', 'Zlodziej', 'Lurer', 'Dropiciel',
    'Szaman', 'Szamanka', 'Sura', 'Ninja', 'Archer', 'Lord', 'Boss', 'Duch',
    'Cien', 'Maska', 'Kozak', 'Koles', 'Brat', 'Szef', 'Mistrz', 'Krolowa',
    'Krol', 'Pies', 'Wariat', 'Smerf', 'Gumis', 'Kebab', 'Taboret', 'Parowa',
    'Biceps', 'Mielony', 'Noob', 'Tryhard', 'Rib', 'Buff', 'Dagger', 'Woj',
]
SUFFIXES = ['', 'PL', 'Kox', 'Koxu', 'Pro', 'XD', 'M1', 'M2', 'MT', 'Elite',
            'Mega', 'Super']
PREFIXES = ['', 'xX', 'Xx', 'Pro', 'Mega', 'Super', 'Mistrz', 'Krol', 'Elite']


def read_community():
    """The list as written, minus what does not belong in it."""
    out = []
    seen = set()
    for line in io.open(COMMUNITY, encoding='utf-8'):
        name = line.strip()
        if not name or name.startswith('#'):
            continue
        if not acceptable(name) or name.lower() in seen:
            continue
        seen.add(name.lower())
        out.append(name)
    return out


def acceptable(name):
    if not re.match(r'^[A-Za-z][A-Za-z0-9_]*$', name):
        return False
    if len(name) < 3 or len(name) > MAX_LEN:
        return False
    low = name.lower()
    if any(stem in low for stem in BLOCKED_STEMS):
        return False
    if any(low.startswith(p) for p in BLOCKED_PREFIXES):
        return False
    return True


def compose(existing, target):
    """Fill the pool from the same parts, deterministically.

    The order is a hash of the candidate rather than a random shuffle, so the
    generated half is stable across runs and across machines - a pool that
    reshuffles would hand every bot a different name on every regeneration.
    """
    seen = set(n.lower() for n in existing)
    candidates = []
    for prefix in PREFIXES:
        for adjective in [''] + ADJECTIVES:
            for noun in NOUNS:
                for suffix in SUFFIXES:
                    name = prefix + adjective + noun + suffix
                    if prefix == 'xX':
                        name += 'Xx'
                    if not acceptable(name) or name.lower() in seen:
                        continue
                    candidates.append(name)
                    seen.add(name.lower())
    candidates.sort(key=lambda n: hashlib.sha256(n.encode('ascii')).hexdigest())
    return candidates[:max(0, target - len(existing))]


def sql_literal(value):
    return "'" + value.replace('\\', '\\\\').replace("'", "''") + "'"


def render(pool):
    rows = []
    for index, name in enumerate(pool, start=1):
        rows.append('(%d,%s)' % (index, sql_literal(name)))
    chunks = []
    step = 100
    for start in range(0, len(rows), step):
        chunks.append('INSERT INTO playerbot_name_pool (n, name) VALUES\n    ' +
                      ',\n    '.join(rows[start:start + step]) + ';')
    values = '\n'.join(chunks)
    return TEMPLATE.replace('@@COUNT@@', str(len(pool))).replace('@@VALUES@@', values)


TEMPLATE = u"""-- Human nicknames for the playerbots. GENERATED - edit
-- linux-port/overlays/playerbot/tools/generate_bot_names.py and re-run it.
--
-- Applied by mariadb/playerbot/apply.sh after the seed, guarded by
-- @playerbot_human_names, which apply.sh sets from M2_PLAYERBOT_HUMAN_NAMES:
--
--   1        rename every bot still called bot<something>   (the default)
--   0        leave every name exactly as it is
--   restore  put the seed names back and forget the renames
--
-- Only a character whose account login is playerbot_NNN is ever touched, and
-- only while it still carries the name the seed gave it - so a bot an operator
-- renamed by hand keeps that name, and no character of a person is reachable
-- from here at all.
--
-- The old name is kept in common.playerbot_name_history, which is what makes
-- 'restore' possible and what stops a second run renaming the same bot twice.

-- A temporary table needs a default database and the client this is fed to has
-- selected none; playerbots_seed.sql opens the same way and for the same
-- reason. Every other table is named in full, so which one it is does not
-- matter beyond that.
USE player;

CREATE TABLE IF NOT EXISTS common.playerbot_name_history (
    pid        INT UNSIGNED NOT NULL,
    seed_name  VARCHAR(24) NOT NULL,
    human_name VARCHAR(24) NOT NULL,
    renamed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (pid),
    KEY human_name (human_name)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

SET @playerbot_human_names = IFNULL(@playerbot_human_names, '1');

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

-- Single-table form on purpose: the multi-table DELETE ... FROM x AS a needs a
-- default database, and this file is fed to a client that has selected none.
DELETE FROM common.playerbot_name_history
 WHERE @playerbot_human_names = 'restore';

SELECT CONCAT('playerbot names: restored ', ROW_COUNT(), ' seed name(s)')
       AS playerbot_names_note
  FROM DUAL
 WHERE @playerbot_human_names = 'restore';

-- --------------------------------------------------------------------------
-- The pool: @@COUNT@@ names, the first 1495 written by jaksiezabic for this
-- server and the rest composed from the same vocabulary.
-- --------------------------------------------------------------------------
DROP TEMPORARY TABLE IF EXISTS playerbot_name_pool;
CREATE TEMPORARY TABLE playerbot_name_pool (
    n    INT UNSIGNED NOT NULL PRIMARY KEY,
    name VARCHAR(24) NOT NULL,
    UNIQUE KEY name (name)
) ENGINE=MEMORY DEFAULT CHARSET=latin1;

@@VALUES@@

-- --------------------------------------------------------------------------
-- Who gets one, and which. Both sides are numbered by a window function and
-- joined on the number, so the pairing is one statement and is stable: the
-- lowest free name goes to the lowest waiting PID.
--
-- A name is free only when no character in the world wears it - player.name is
-- indexed but not unique, so nothing but this check stops two characters
-- sharing one - and when this table has not already handed it out.
-- --------------------------------------------------------------------------
DROP TEMPORARY TABLE IF EXISTS playerbot_name_plan;
CREATE TEMPORARY TABLE playerbot_name_plan (
    pid        INT UNSIGNED NOT NULL PRIMARY KEY,
    seed_name  VARCHAR(24) NOT NULL,
    human_name VARCHAR(24) NOT NULL
) ENGINE=MEMORY DEFAULT CHARSET=latin1;

INSERT INTO playerbot_name_plan (pid, seed_name, human_name)
SELECT waiting.pid, waiting.seed_name, free.name
  FROM (
        SELECT p.id AS pid, p.name AS seed_name,
               ROW_NUMBER() OVER (ORDER BY p.id) AS rn
          FROM player.player AS p
          JOIN account.account AS a ON a.id = p.account_id
         WHERE LEFT(a.login, 10) = 'playerbot_'
           AND p.name LIKE 'bot%'
           AND NOT EXISTS (SELECT 1 FROM common.playerbot_name_history AS h
                            WHERE h.pid = p.id)
       ) AS waiting
  JOIN (
        SELECT np.name, ROW_NUMBER() OVER (ORDER BY np.n) AS rn
          FROM playerbot_name_pool AS np
         WHERE NOT EXISTS (SELECT 1 FROM player.player AS px
                            WHERE px.name = np.name)
           AND NOT EXISTS (SELECT 1 FROM common.playerbot_name_history AS h2
                            WHERE h2.human_name = np.name)
       ) AS free
    ON free.rn = waiting.rn
 WHERE @playerbot_human_names = '1';

INSERT INTO common.playerbot_name_history (pid, seed_name, human_name)
SELECT pid, seed_name, human_name FROM playerbot_name_plan;

UPDATE player.player AS p
  JOIN playerbot_name_plan AS pl ON pl.pid = p.id
   SET p.name = pl.human_name;

-- HAVING, not WHERE: the aggregate returns one row over an empty plan, and a
-- 'restore' run would otherwise report "gave 0" straight after "restored 2500".
SELECT CONCAT('playerbot names: gave ', COUNT(*), ' bot(s) a human nickname')
       AS playerbot_names_note
  FROM playerbot_name_plan
HAVING @playerbot_human_names = '1';

-- A cohort larger than the pool is the one way this runs out; say so rather
-- than leaving an operator to wonder why some bots kept their seed names.
SELECT CONCAT('playerbot names: WARNING ', COUNT(*),
              ' bot(s) still carry a seed name - the pool of @@COUNT@@ is used up')
       AS playerbot_names_note
  FROM player.player AS p
  JOIN account.account AS a ON a.id = p.account_id
 WHERE @playerbot_human_names = '1'
   AND LEFT(a.login, 10) = 'playerbot_'
   AND p.name LIKE 'bot%'
HAVING COUNT(*) > 0;

DROP TEMPORARY TABLE IF EXISTS playerbot_name_plan;
DROP TEMPORARY TABLE IF EXISTS playerbot_name_pool;
"""


def main():
    community = read_community()
    pool = community + compose(community, TARGET)
    if len(pool) < TARGET:
        print('uwaga: pula ma tylko %d nickow (cel %d)' % (len(pool), TARGET))
    text = render(pool)
    for path in (OUT_SQL, MIRROR_SQL):
        directory = os.path.dirname(path)
        if not os.path.isdir(directory):
            os.makedirs(directory)
        io.open(path, 'w', encoding='utf-8', newline='\n').write(text)
    digest = hashlib.sha256(text.encode('utf-8')).hexdigest()
    print('napisano %s (%d nickow: %d od spolecznosci, %d zlozonych, sha256 %s)'
          % (OUT_SQL, len(pool), len(community), len(pool) - len(community), digest))
    print('kopia:   %s' % MIRROR_SQL)
    return 0


if __name__ == '__main__':
    sys.exit(main())
