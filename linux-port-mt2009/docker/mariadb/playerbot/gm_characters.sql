-- Four game masters on the tester account, one per class, fully equipped.
--
-- The mt2009 package ships an empty gmlist and no character on `admin'.
-- This file creates Admin (warrior), AdminNinja, AdminSura and AdminSzaman
-- at level ninety, each with IMPLEMENTOR rights, the best +9 set the
-- package has for its class with strong bonus lines, a second weapon, a
-- bag of potions and scrolls, and a level-21 horse with its summon book
-- (50053, what the stable keeper hands out for a grade-3 horse).
--
-- Runs on a fresh world from initdb.d (10-import-dumps.sh) and on every
-- start from apply.sh; it does nothing unless the admin account exists AND
-- has no character at all, so a world where somebody already plays on that
-- account is left exactly as it is. PIDs 9001-9004: the playerbot seed uses
-- 4..2503 with explicit ids, and player.player's AUTO_INCREMENT would have
-- handed a fresh world 1..4 and collided with the seed's pid 4.
--
-- Columns of player.player as playerbots_seed.sql writes them; the rest
-- takes the table's defaults. Bonus lines are POINT numbers (common/length.h):
-- this engine stores POINT ids in item.attrtype, not APPLY ids. Slots 5 and
-- 6 of a weapon carry the two damage lines (122 average, 121 skill) the way
-- item_addon.cpp writes them.

SET @admin_id = (SELECT id FROM account.account WHERE login = 'admin');
SET @admin_has_chars = (SELECT COUNT(*) FROM player.player WHERE account_id = @admin_id);
SET @gm_names_free = (SELECT COUNT(*) FROM player.player
                       WHERE name IN ('Admin', 'AdminNinja', 'AdminSura', 'AdminSzaman')
                          OR id BETWEEN 9001 AND 9004);
SET @go = (@admin_id IS NOT NULL AND @admin_has_chars = 0 AND @gm_names_free = 0);

-- Level 21 horse: c_aHorseStat[21] in horse_rider.cpp is 35 health, 120 stamina.
INSERT INTO player.player
    (id, account_id, name, job, voice, dir, x, y, z, map_index,
     exit_x, exit_y, exit_map_index, hp, mp, stamina, level, level_step,
     st, ht, dx, iq, exp, gold, stat_point, skill_point, skill_group,
     sub_skill_point, stat_reset_count, horse_hp, horse_stamina,
     horse_level, horse_hp_droptime, horse_riding, horse_skill_point,
     last_play)
SELECT c.id, @admin_id, c.name, c.job, 0, 0, 59513, 171123, 0, 21,
       59513, 171123, 21, 20000, 5000, 800, 90, 0,
       90, 90, 90, 90, 0, 500000000, 0, 0, 1,
       0, 0, 35, 120,
       21, 0, 0, 0,
       UTC_TIMESTAMP()
  FROM (SELECT 9001 AS id, 'Admin'       AS name, 0 AS job UNION ALL
        SELECT 9002,       'AdminNinja',         1        UNION ALL
        SELECT 9003,       'AdminSura',          2        UNION ALL
        SELECT 9004,       'AdminSzaman',        3) AS c
 WHERE @go;

-- The character screen reads player_index, and the account has no row yet.
INSERT INTO player.player_index (id, pid1, pid2, pid3, pid4, empire)
SELECT @admin_id, 9001, 9002, 9003, 9004, 2
  FROM DUAL
 WHERE @go AND NOT EXISTS (SELECT 1 FROM player.player_index WHERE id = @admin_id);

INSERT INTO common.gmlist (mAccount, mName, mContactIP, mServerIP, mAuthority)
SELECT 'admin', p.name, '', 'ALL', 'IMPLEMENTOR'
  FROM player.player AS p
 WHERE @go AND p.id BETWEEN 9001 AND 9004
   AND NOT EXISTS (SELECT 1 FROM common.gmlist AS g WHERE g.mName = p.name);

-- Worn set. pos is the wear slot: 0 body, 1 head, 2 foots, 3 wrist, 4 weapon,
-- 5 neck, 6 ear, 10 shield. Jewellery, bracelet and shield are the same for
-- everybody (antiflag 256 = no class limit); body, head, boots and the weapon
-- follow the class.
INSERT INTO player.item
    (owner_id, window, pos, count, vnum,
     attrtype0, attrvalue0, attrtype1, attrvalue1, attrtype2, attrvalue2,
     attrtype3, attrvalue3, attrtype4, attrvalue4, attrtype5, attrvalue5, attrtype6, attrvalue6)
SELECT g.owner_id, 'EQUIPMENT', g.pos, 1, g.vnum,
       g.a0, g.v0, g.a1, g.v1, g.a2, g.v2, g.a3, g.v3, g.a4, g.v4, g.a5, g.v5, g.a6, g.v6
  FROM (
    -- weapons: crit 10, pierce 10, vs monsters 20, vs humans 10, casting speed 20; average 45, skill 20
    SELECT 9001 AS owner_id, 4 AS pos,  469 AS vnum, 40 AS a0, 10 AS v0, 41 AS a1, 10 AS v1, 53 AS a2, 20 AS v2, 43 AS a3, 10 AS v3, 21 AS a4, 20 AS v4, 122 AS a5, 45 AS v5, 121 AS a6, 20 AS v6 UNION ALL
    SELECT 9002, 4, 1349, 40, 10, 41, 10, 53, 20, 43, 10, 21, 20, 122, 45, 121, 20 UNION ALL
    SELECT 9003, 4,  479, 40, 10, 41, 10, 53, 20, 43, 10, 21, 20, 122, 45, 121, 20 UNION ALL
    SELECT 9004, 4, 5349, 40, 10, 41, 10, 53, 20, 43, 10, 21, 20, 122, 45, 121, 20 UNION ALL
    -- body: hp 1500, steal hp 10, attack value 50, casting speed 20, magic resistance 15
    SELECT 9001, 0, 20009, 6, 1500, 63, 10, 95, 50, 21, 20, 77, 15, 0, 0, 0, 0 UNION ALL
    SELECT 9002, 0, 20259, 6, 1500, 63, 10, 95, 50, 21, 20, 77, 15, 0, 0, 0, 0 UNION ALL
    SELECT 9003, 0, 20509, 6, 1500, 63, 10, 95, 50, 21, 20, 77, 15, 0, 0, 0, 0 UNION ALL
    SELECT 9004, 0, 20759, 6, 1500, 63, 10, 95, 50, 21, 20, 77, 15, 0, 0, 0, 0 UNION ALL
    -- head: hp regen 12, attack speed 8, dodge 15, magic resistance 15, vs humans 10
    SELECT 9001, 1, 12289, 32, 12, 17, 8, 68, 15, 77, 15, 43, 10, 0, 0, 0, 0 UNION ALL
    SELECT 9002, 1, 12409, 32, 12, 17, 8, 68, 15, 77, 15, 43, 10, 0, 0, 0, 0 UNION ALL
    SELECT 9003, 1, 12549, 32, 12, 17, 8, 68, 15, 77, 15, 43, 10, 0, 0, 0, 0 UNION ALL
    SELECT 9004, 1, 12689, 32, 12, 17, 8, 68, 15, 77, 15, 43, 10, 0, 0, 0, 0 UNION ALL
    -- boots: hp 1500, attack speed 8, movement speed 20, crit 10, dodge 15
    SELECT 9001, 2, 15379, 6, 1500, 17, 8, 19, 20, 40, 10, 68, 15, 0, 0, 0, 0 UNION ALL
    SELECT 9002, 2, 15399, 6, 1500, 17, 8, 19, 20, 40, 10, 68, 15, 0, 0, 0, 0 UNION ALL
    SELECT 9003, 2, 15419, 6, 1500, 17, 8, 19, 20, 40, 10, 68, 15, 0, 0, 0, 0 UNION ALL
    SELECT 9004, 2, 15439, 6, 1500, 17, 8, 19, 20, 40, 10, 68, 15, 0, 0, 0, 0 UNION ALL
    -- bracelet: hp 1500, sp 250, pierce 10, steal hp 10, vs humans 10
    SELECT 9001, 3, 14529, 6, 1500, 8, 250, 41, 10, 63, 10, 43, 10, 0, 0, 0, 0 UNION ALL
    SELECT 9002, 3, 14529, 6, 1500, 8, 250, 41, 10, 63, 10, 43, 10, 0, 0, 0, 0 UNION ALL
    SELECT 9003, 3, 14529, 6, 1500, 8, 250, 41, 10, 63, 10, 43, 10, 0, 0, 0, 0 UNION ALL
    SELECT 9004, 3, 14529, 6, 1500, 8, 250, 41, 10, 63, 10, 43, 10, 0, 0, 0, 0 UNION ALL
    -- necklace: hp 1500, sp 250, crit 10, pierce 10, hp regen 12
    SELECT 9001, 5, 16529, 6, 1500, 8, 250, 40, 10, 41, 10, 32, 12, 0, 0, 0, 0 UNION ALL
    SELECT 9002, 5, 16529, 6, 1500, 8, 250, 40, 10, 41, 10, 32, 12, 0, 0, 0, 0 UNION ALL
    SELECT 9003, 5, 16529, 6, 1500, 8, 250, 40, 10, 41, 10, 32, 12, 0, 0, 0, 0 UNION ALL
    SELECT 9004, 5, 16529, 6, 1500, 8, 250, 40, 10, 41, 10, 32, 12, 0, 0, 0, 0 UNION ALL
    -- earrings: movement speed 20, vs humans 10, vs animals 20, vs orcs 20, vs undead 20
    SELECT 9001, 6, 17529, 19, 20, 43, 10, 44, 20, 45, 20, 47, 20, 0, 0, 0, 0 UNION ALL
    SELECT 9002, 6, 17529, 19, 20, 43, 10, 44, 20, 45, 20, 47, 20, 0, 0, 0, 0 UNION ALL
    SELECT 9003, 6, 17529, 19, 20, 43, 10, 44, 20, 45, 20, 47, 20, 0, 0, 0, 0 UNION ALL
    SELECT 9004, 6, 17529, 19, 20, 43, 10, 44, 20, 45, 20, 47, 20, 0, 0, 0, 0 UNION ALL
    -- shield: block 15, str 12, vit 12, vs humans 10, reflect melee 10
    SELECT 9001, 10, 13149, 67, 15, 12, 12, 13, 12, 43, 10, 79, 10, 0, 0, 0, 0 UNION ALL
    SELECT 9002, 10, 13149, 67, 15, 12, 12, 13, 12, 43, 10, 79, 10, 0, 0, 0, 0 UNION ALL
    SELECT 9003, 10, 13149, 67, 15, 12, 12, 13, 12, 43, 10, 79, 10, 0, 0, 0, 0 UNION ALL
    SELECT 9004, 10, 13149, 67, 15, 12, 12, 13, 12, 43, 10, 79, 10, 0, 0, 0, 0
  ) AS g
 WHERE @go AND NOT EXISTS (SELECT 1 FROM player.item AS i WHERE i.owner_id = g.owner_id);

-- The bag (5 columns; a weapon is three cells tall, so the second weapon sits
-- at 10 and covers 10, 15, 20). Stacks of two hundred where the item stacks.
INSERT INTO player.item
    (owner_id, window, pos, count, vnum,
     attrtype0, attrvalue0, attrtype1, attrvalue1, attrtype2, attrvalue2,
     attrtype3, attrvalue3, attrtype4, attrvalue4, attrtype5, attrvalue5, attrtype6, attrvalue6)
SELECT p.id, 'INVENTORY', b.pos, b.cnt, b.vnum,
       b.a0, b.v0, b.a1, b.v1, b.a2, b.v2, b.a3, b.v3, b.a4, b.v4, b.a5, b.v5, b.a6, b.v6
  FROM player.player AS p
  JOIN (
    SELECT 0 AS pos, 200 AS cnt, 27007 AS vnum, 0 AS a0, 0 AS v0, 0 AS a1, 0 AS v1, 0 AS a2, 0 AS v2, 0 AS a3, 0 AS v3, 0 AS a4, 0 AS v4, 0 AS a5, 0 AS v5, 0 AS a6, 0 AS v6 UNION ALL
    SELECT 1, 200, 27008, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 UNION ALL
    SELECT 2,  50, 25040, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 UNION ALL
    SELECT 3,  50, 25045, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 UNION ALL
    SELECT 4,  50, 22030, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 UNION ALL
    SELECT 5,  50, 50050, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 UNION ALL
    SELECT 6,   1, 50053, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
  ) AS b
 WHERE @go AND p.id BETWEEN 9001 AND 9004
   AND NOT EXISTS (SELECT 1 FROM player.item AS i WHERE i.owner_id = p.id AND i.window = 'INVENTORY');

-- Second weapon per class: the two-handed sword, the bow (with arrows), the fan.
INSERT INTO player.item
    (owner_id, window, pos, count, vnum,
     attrtype0, attrvalue0, attrtype1, attrvalue1, attrtype2, attrvalue2,
     attrtype3, attrvalue3, attrtype4, attrvalue4, attrtype5, attrvalue5, attrtype6, attrvalue6)
SELECT w.owner_id, 'INVENTORY', w.pos, w.cnt, w.vnum,
       w.a0, w.v0, w.a1, w.v1, w.a2, w.v2, w.a3, w.v3, w.a4, w.v4, w.a5, w.v5, w.a6, w.v6
  FROM (
    SELECT 9001 AS owner_id, 10 AS pos, 1 AS cnt, 3199 AS vnum, 40 AS a0, 10 AS v0, 41 AS a1, 10 AS v1, 53 AS a2, 20 AS v2, 43 AS a3, 10 AS v3, 21 AS a4, 20 AS v4, 122 AS a5, 45 AS v5, 121 AS a6, 20 AS v6 UNION ALL
    SELECT 9002, 10,   1, 2379, 40, 10, 41, 10, 53, 20, 43, 10, 21, 20, 122, 45, 121, 20 UNION ALL
    SELECT 9002,  7, 200, 8009,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,   0,  0,   0,  0 UNION ALL
    SELECT 9004, 10,   1, 7379, 40, 10, 41, 10, 53, 20, 43, 10, 21, 20, 122, 45, 121, 20
  ) AS w
 WHERE @go AND NOT EXISTS (SELECT 1 FROM player.item AS i WHERE i.owner_id = w.owner_id AND i.window = 'INVENTORY' AND i.pos = w.pos);

SELECT CONCAT('gm characters: ', IF(@go, 'created Admin, AdminNinja, AdminSura, AdminSzaman on the admin account',
                                       IF(@admin_id IS NULL, 'no admin account, nothing to do',
                                          'the admin account already has characters, left as they are'))) AS note;
