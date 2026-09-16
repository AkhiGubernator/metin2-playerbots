# -*- coding: utf-8 -*-
"""Renderuje playerbot_item_tiers.h z listy tierow Iwakury (data/iwakura_tiery.txt).

Jego plik z 16 wrzesnia ("TIERY ITEMOW + BONUSOW"): kazda rodzina bizuterii,
butow i broni oraz kazdy bonus dostaje dwie oceny od 1 (bardzo zly) do 6
(wspanialy) - osobno do PvP i do PvE - a niektore wiersze dopisek "+1 dla
Wojownika" albo "+1 PVE dla Szamana/Sury". Zbroje i tarcze ocenia po poziomie
i po bonusach, nie po nazwie, wiec te dwie sekcje sa opisem, nie tabela.

Wejscie: jego plik plus zrzut item_proto (ten sam, co dla cennika):
    docker exec -i <db> sh -c 'exec mariadb -uroot -p"$MARIADB_ROOT_PASSWORD" -N' > item_proto_hex.tsv
      SELECT vnum, HEX(locale_name), type, subtype, COALESCE(limitvalue0,0) FROM world.item_proto ORDER BY vnum;
Uzycie (z katalogu linux-port/overlays/playerbot):
    python tools/generate_iwakura_tiers.py item_proto_hex.tsv data/iwakura_tiery.txt \\
        src/game/src/playerbot_item_tiers.h

Nazwy rodzin i bonusow rozwiazuje tak samo jak generator cennika (aliasy z
generate_iwakura_prices.py plus kilka pisowni tylko z tego pliku) i tak samo
**przerywa z bledem**, gdy jakiejs nie zwiaze: tabela, w ktorej po cichu brakuje
polowy wierszy, jest gorsza niz jej brak.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_iwakura_prices import (BONUS_APPLIES, GEAR_ALIASES, MT2009_ONLY, Resolver,
                                     ascii_comment, load_hex, norm)

# Pisownie tylko z listy tierow -> klucz z BONUS_APPLIES.
TIER_BONUS_ALIASES = {
    'x% obrażeń dodanych do pż': 'x% obrażen dodanych do pż',
    'x% obrażeń dodanych do pe': 'x% obrażen dodanych do pe',
    'odporność na magię': 'odporność na magie',
    'szansa na uniknięcie strzały': 'szansa na unik. strzały',
    'silny przeciwko diabłom': 'silny przeciwko diablom',
    'silny na nieumarłe': 'silny przeciwko nieumarłym',
    'silny na orki': 'silny przeciwko orkom',
    'silny na zwierzęta': 'silny przeciwko zwierzętom',
}

JOBS = {'wojownik': 0, 'wojownika': 0, 'ninja': 1, 'ninjy': 1, 'sura': 2, 'sury': 2,
        'szaman': 3, 'szamana': 3}
JOB_NAMES = ['JOB_WARRIOR', 'JOB_ASSASSIN', 'JOB_SURA', 'JOB_SHAMAN']

ITEM_SECTIONS = ['Bransolety', 'Kolczyki', 'Naszyjniki', 'Buty', 'Bronie']
LINE_RE = re.compile(r'^(.*?)\s+PVP:\s*(\d)\s+PVE:\s*(\d)\s*(?:\((.*?)\))?\s*$', re.I)
STRIP_RE = re.compile(r'\s*\((?:lvl\s*\d+|nno|nns)\)', re.I)
MOD_RE = re.compile(r'\+1\s*(PVE/PVP|PVP/PVE|PVE|PVP)?\s*dla\s+(.+)$', re.I)


def parse_modifier(note):
    """"+1 PVE dla Szamana/Sury" -> (pve_jobs_mask, pvp_jobs_mask)."""
    if not note:
        return 0, 0
    m = MOD_RE.search(note)
    if not m:
        return 0, 0
    mode = (m.group(1) or 'PVE/PVP').upper()
    mask = 0
    for word in re.split(r'[/ ,]+', m.group(2).strip().lower()):
        if word in JOBS:
            mask |= 1 << JOBS[word]
    if mask == 0:
        raise SystemExit('dopisek bez klasy: %s' % note)
    pve = mask if 'PVE' in mode else 0
    pvp = mask if 'PVP' in mode else 0
    return pve, pvp


def read_sheet(path):
    lines = io.open(path, encoding='utf-8-sig').read().replace('\r\n', '\n').split('\n')
    sections = {}
    current = None
    for line in lines:
        s = line.strip()
        m = re.match(r'^\[(.+)\]$', s)
        if m:
            current = m.group(1)
            sections.setdefault(current, [])
            continue
        if current is not None and s:
            sections[current].append(s)
    return sections


def parse_rows(block):
    for line in block:
        m = LINE_RE.match(line)
        if not m:
            continue
        name = STRIP_RE.sub('', m.group(1)).strip()
        yield name, int(m.group(3)), int(m.group(2)), (m.group(4) or '').strip()


def main(item_path, sheet_path, out_path):
    items = load_hex(item_path)
    resolver = Resolver(items, [])
    sheet = read_sheet(sheet_path)
    for title in ITEM_SECTIONS + ['Bonusy']:
        if title not in sheet:
            raise SystemExit('brak sekcji [%s]' % title)

    item_rows = {}
    for title in ITEM_SECTIONS:
        for name, pve, pvp, note in parse_rows(sheet[title]):
            base = resolver.gear(name)
            if base is None:
                continue
            pve_jobs, pvp_jobs = parse_modifier(note)
            if base in item_rows:
                raise SystemExit('rodzina %s dwa razy (vnum %d)' % (name, base))
            item_rows[base] = (pve, pvp, pve_jobs, pvp_jobs, name)

    bonus_rows = {}
    errors = []
    for name, pve, pvp, note in parse_rows(sheet['Bonusy']):
        key = norm(name)
        key = TIER_BONUS_ALIASES.get(key, key)
        apply = BONUS_APPLIES.get(key)
        if apply is None:
            errors.append('bonus bez APPLY: "%s"' % name)
            continue
        pve_jobs, pvp_jobs = parse_modifier(note)
        row = (pve, pvp, pve_jobs, pvp_jobs)
        if apply in bonus_rows and bonus_rows[apply][:4] != row:
            errors.append('bonus %s ma dwie rozne oceny: %s i %s' % (apply, bonus_rows[apply][4], name))
            continue
        bonus_rows.setdefault(apply, row + (name,))

    problems = resolver.missing + errors
    if problems:
        sys.stderr.write('generate_iwakura_tiers: %d problemow:\n' % len(problems))
        for p in problems:
            sys.stderr.write('  %s\n' % p)
        return 1

    def jobs_text(mask):
        if mask == 0:
            return '0'
        return ' | '.join('(1 << %s)' % JOB_NAMES[j] for j in range(4) if mask & (1 << j))

    out = io.StringIO()
    out.write(u'''// Rendered by linux-port/overlays/playerbot/tools/generate_iwakura_tiers.py from Iwakura's
// tier list (data/iwakura_tiery.txt, 16 September). Do not edit by hand.
//
// Every family of bracelets, earrings, necklaces, boots and weapons, and every
// bonus line, rated 1 (bardzo zly) to 6 (wspanialy) - once for PvE, once for
// PvP - with the "+1 dla Wojownika" notes as job masks. Body armour, helmets
// and shields are judged by level and bonuses, not by name, so they are not
// here. The PvE column steers the hunting set today; the PvP column waits for
// the second set ("na przyszlosc pod posiadanie przez boty dwoch setow").
#ifndef __INC_METIN2_PLAYERBOT_ITEM_TIERS_H__
#define __INC_METIN2_PLAYERBOT_ITEM_TIERS_H__

namespace
{
	const int PLAYERBOT_TIER_MIN = 1;
	const int PLAYERBOT_TIER_MAX = 6;

	// The +0 vnum of the family; the rest of the family is base + refine.
	struct TPlayerBotItemTier { DWORD dwBaseVnum; BYTE bPve; BYTE bPvp; BYTE bPveJobs; BYTE bPvpJobs; };
	const TPlayerBotItemTier PLAYERBOT_ITEM_TIERS[] = {
''')
    for base in sorted(item_rows):
        pve, pvp, pve_jobs, pvp_jobs, name = item_rows[base]
        out.write(u'\t\t{ %d, %d, %d, %s, %s }, // %s\n' % (
            base, pve, pvp, jobs_text(pve_jobs), jobs_text(pvp_jobs), ascii_comment(name)))
    out.write(u'''\t};

	struct TPlayerBotBonusTier { BYTE bApply; BYTE bPve; BYTE bPvp; BYTE bPveJobs; BYTE bPvpJobs; };
	const TPlayerBotBonusTier PLAYERBOT_BONUS_TIERS[] = {
''')
    for apply in sorted(bonus_rows, key=lambda a: (a in MT2009_ONLY, a)):
        pve, pvp, pve_jobs, pvp_jobs, name = bonus_rows[apply]
        row = u'\t\t{ %s, %d, %d, %s, %s }, // %s\n' % (
            apply, pve, pvp, jobs_text(pve_jobs), jobs_text(pvp_jobs), ascii_comment(name))
        if apply in MT2009_ONLY:
            out.write(u'#if defined(PLAYERBOT_ENGINE_MT2009)\n%s#endif\n' % row)
        else:
            out.write(row)
    out.write(u'''\t};

	int PlayerBotTierWithJob(int tier, BYTE jobs, int job)
	{
		if (tier <= 0)
			return 0;
		if (job >= 0 && job < 4 && (jobs & (1 << job)) != 0)
			++tier;
		return tier > PLAYERBOT_TIER_MAX ? PLAYERBOT_TIER_MAX : tier;
	}

	// The family's tier for this job, or 0 when his list does not carry it.
	// `job` is CHARACTER::GetJob(), 0..3; -1 asks without the job notes.
	int GetPlayerBotItemTier(DWORD baseVnum, int job, bool pvp)
	{
		for (size_t i = 0; i < sizeof(PLAYERBOT_ITEM_TIERS) / sizeof(PLAYERBOT_ITEM_TIERS[0]); ++i)
			if (PLAYERBOT_ITEM_TIERS[i].dwBaseVnum == baseVnum)
				return pvp ? PlayerBotTierWithJob(PLAYERBOT_ITEM_TIERS[i].bPvp, PLAYERBOT_ITEM_TIERS[i].bPvpJobs, job)
						: PlayerBotTierWithJob(PLAYERBOT_ITEM_TIERS[i].bPve, PLAYERBOT_ITEM_TIERS[i].bPveJobs, job);
		return 0;
	}

	// The bonus line's tier for this job, or 0 when his list does not name it.
	int GetPlayerBotBonusTier(BYTE apply, int job, bool pvp)
	{
		for (size_t i = 0; i < sizeof(PLAYERBOT_BONUS_TIERS) / sizeof(PLAYERBOT_BONUS_TIERS[0]); ++i)
			if (PLAYERBOT_BONUS_TIERS[i].bApply == apply)
				return pvp ? PlayerBotTierWithJob(PLAYERBOT_BONUS_TIERS[i].bPvp, PLAYERBOT_BONUS_TIERS[i].bPvpJobs, job)
						: PlayerBotTierWithJob(PLAYERBOT_BONUS_TIERS[i].bPve, PLAYERBOT_BONUS_TIERS[i].bPveJobs, job);
		return 0;
	}
}

#endif
''')
    text = out.getvalue()
    if any(ord(ch) > 127 for ch in text):
        raise SystemExit('naglowek ma znaki spoza ASCII')
    io.open(out_path, 'w', encoding='ascii', newline='\n').write(text)
    print('zapisano %s' % out_path)
    print('  rodzin: %d, bonusow: %d (tylko mt2009: %d)' % (
        len(item_rows), len(bonus_rows), sum(1 for a in bonus_rows if a in MT2009_ONLY)))
    return 0


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.stderr.write(__doc__)
        sys.exit(2)
    sys.exit(main(*sys.argv[1:]))
