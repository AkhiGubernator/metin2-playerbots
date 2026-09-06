#ifndef __INC_METIN2_PLAYERBOT_CONSUMABLES_H__
#define __INC_METIN2_PLAYERBOT_CONSUMABLES_H__

// The Moonlight Treasure Chest, and the boosters that come out of it.
//
// A chest is an ITEM_USE the engine opens itself - UseItem on 50011 draws one
// line of the chest's special item group into the bag - so opening one is a
// matter of noticing it is there. What it holds the bot already knows how to
// spend: the bonus scrolls go through playerbot_bonus.h, which takes a scroll
// from the bag before it buys one; the speed potions through UseUtilityPotions;
// the big potions through the ordinary potion lists. The two boosters, Hand of
// the Critic and Hand of Penetration, are new: a twenty-percent chance for ten
// minutes, worth drinking when a fight starts and pointless at an NPC.
//
// An implementation fragment in the sense playerbot_types.h describes: include
// it exactly once, after playerbot_gear.h.

namespace
{
	// Opens one chest per pass. UseItem refuses when the bag has no room, and
	// says so in the engine's own log; the bot's next town visit makes room.
	bool ManagePlayerBotChests(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || !ch->IsItemLoaded() || dwNow < state.dwNextChestTime)
			return false;
		state.dwNextChestTime = dwNow + PLAYERBOT_CHEST_INTERVAL;
		for (WORD cell = 0; cell < INVENTORY_MAX_NUM; ++cell)
		{
			LPITEM item = ch->GetInventoryItem(cell);
			if (!item || item->GetVnum() != PLAYERBOT_MOONLIGHT_CHEST_VNUM)
				continue;
			if (ch->GetEmptyInventory(1) < 0)
				return false;
			const int before = ch->GetEmptyInventory(1);
			if (ch->UseItem(TItemPos(INVENTORY, cell)))
			{
				sys_log(0, "PLAYERBOT_CHEST: opened pid=%u name=%s level=%u map=%ld free_before=%d free_after=%d",
						ch->GetPlayerID(), ch->GetName(), ch->GetLevel(), ch->GetMapIndex(),
						before, ch->GetEmptyInventory(1));
				return true;
			}
			return false;
		}
		return false;
	}

	// A booster at the start of a fight. The engine keeps one of each running
	// at a time and refuses a second, so a failed use is the usual case and
	// nothing to log; a minute between attempts is enough.
	bool UsePlayerBotBoosters(LPCHARACTER ch, TPlayerBotAIState& state, DWORD dwNow)
	{
		if (!ch || dwNow < state.dwNextBoosterTime)
			return false;
		if (state.bCurrentAction != BOT_ACTION_FIGHT || state.bVisitingShop ||
				state.bRecoveringAfterDeath || state.bTacticalRetreat)
			return false;
		state.dwNextBoosterTime = dwNow + PLAYERBOT_BOOSTER_INTERVAL;
		bool used = false;
		for (size_t b = 0; b < sizeof(PLAYERBOT_BOOSTER_VNUMS) / sizeof(PLAYERBOT_BOOSTER_VNUMS[0]); ++b)
		{
			for (WORD cell = 0; cell < INVENTORY_MAX_NUM; ++cell)
			{
				LPITEM item = ch->GetInventoryItem(cell);
				if (!item || item->GetVnum() != PLAYERBOT_BOOSTER_VNUMS[b])
					continue;
				const DWORD vnum = item->GetVnum();
				if (ch->UseItem(TItemPos(INVENTORY, cell)))
				{
					sys_log(0, "PLAYERBOT_CHEST: booster pid=%u name=%s vnum=%u",
							ch->GetPlayerID(), ch->GetName(), vnum);
					used = true;
				}
				break;
			}
		}
		return used;
	}
}

#endif
