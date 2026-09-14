#ifndef PLAYERBOT_MONKEY_POLICY_H
#define PLAYERBOT_MONKEY_POLICY_H

#include <cstdint>
#include <map>

// How long a bot stays in one Monkey Dungeon chamber, and the one number that
// governs both ways of leaving it.
//
// The dungeon is eleven chambers joined only by GOTO NPCs, and warp_npc_event
// moves anyone within three hundred units of one, twice a second. A bot that
// comes through a door is put down beside the door that leads straight back,
// and a bot that stops there to fight is returned where it came from by the
// engine, not by any decision of its own. Measured over 303 returns to the
// entrance chamber: a median of 65 s in the far room and 29% within fifteen
// seconds - while a chosen crossing cannot happen before the dwell has run at
// all, so every one of those under it was the door, not the bot. The "whole
// dungeon run in one line" that players photographed was mostly this: 905
// crossings on map 108, nearly all of them 0<->7 and 0<->1, and almost nothing
// past the first door.
//
// One number closes both halves. The engine refuses to move a bot through a
// GOTO door for kChamberDwellMs after the last door moved it, and the AI does
// not choose a door before the same time has passed in the chamber. The AI's
// clock starts on the bot's own tick, after the engine's, so a chosen crossing
// always finds the block expired and a bounce always finds it standing.
//
// Included from an engine translation unit (char.cpp) as well as the overlay,
// so everything is inline and nothing of the engine is dragged in - the same
// shape as playerbot_party_policy.h and playerbot_pvp_policy.h.
namespace playerbot_monkey {

// Ninety seconds. The four minutes this replaces came from a model of a
// thirty-minute visit that never happened: over 1294 measured visits the
// median is 86 s and three quarters leave within 201 s, because a bot leaves
// the moment its medal drops. At four minutes three visits in four never saw
// a second chamber; at ninety seconds a three-minute visit crosses twice and a
// long one walks most of the dungeon.
const uint32_t kChamberDwellMs = 90000;

inline std::map<uint32_t, uint32_t> gotoCrossedAt;

// Called by the engine on the pass a GOTO door moves a bot.
inline void NoteGotoCrossing(uint32_t botPid, uint32_t now)
{
	if (botPid)
		gotoCrossedAt[botPid] = now;
}

// True while a GOTO door has to leave this bot where it stands.
inline bool IsGotoCrossingBlocked(uint32_t botPid, uint32_t now)
{
	std::map<uint32_t, uint32_t>::iterator it = gotoCrossedAt.find(botPid);
	if (it == gotoCrossedAt.end())
		return false;
	if (now - it->second >= kChamberDwellMs)
	{
		gotoCrossedAt.erase(it);
		return false;
	}
	return true;
}

inline void Forget(uint32_t botPid)
{
	gotoCrossedAt.erase(botPid);
}

} // namespace playerbot_monkey

#endif
