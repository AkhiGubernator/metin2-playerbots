#ifndef PLAYERBOT_PVP_POLICY_H
#define PLAYERBOT_PVP_POLICY_H

#include <cstdint>
#include <map>

// A challenge to a duel, kept until the bot's next tick answers it.
//
// CPVPManager::Insert is a two-sided agreement: the first call makes the CPVP
// and tells the victim "%s challenged you to a battle", the second call from
// the other side reaches Agree() and the fight begins. A player types /pvp
// <vid>; a bot has no client to type it back, so a challenge to a bot simply
// sat there unanswered for ever.
//
// The engine's side only records that a bot was challenged (playerbotify.py
// puts the call at the end of Insert, which is reached exactly once per new
// duel - the branch above it returns early when the pair already exists). The
// bot's own tick calls Insert back, which is what the player's second /pvp
// would have been.
//
// The timestamp is taken by the AI, not here: the wait before a bot agrees is
// a matter of how a bot behaves, and the engine has no business knowing about
// it. Zero means "seen for the first time on the next tick".
//
// Included from an engine translation unit as well as from the overlay, so
// everything is inline and nothing of the engine is dragged in. Same shape as
// playerbot_offline_policy.h and playerbot_party_policy.h.
namespace playerbot_pvp {

struct Challenge
{
	uint32_t challengerPid;
	uint32_t seenAt;
};

inline std::map<uint32_t, Challenge> challenges;

// Called from the engine for a bot that was just challenged. The newest
// challenge wins: answering one that somebody has already walked away from is
// worse than answering none.
inline void NoteChallenge(uint32_t challengerPid, uint32_t botPid)
{
	if (!challengerPid || !botPid || challengerPid == botPid)
		return;
	Challenge& challenge = challenges[botPid];
	challenge.challengerPid = challengerPid;
	challenge.seenAt = 0;
}

// Called from the bot's tick. Returns the challenger and stamps the moment the
// bot first saw it, so the caller can let the agreed pause run before agreeing.
inline bool PeekChallenge(uint32_t botPid, uint32_t& challengerPid, uint32_t& seenAt, uint32_t now)
{
	std::map<uint32_t, Challenge>::iterator it = challenges.find(botPid);
	if (it == challenges.end())
		return false;
	if (it->second.seenAt == 0)
		it->second.seenAt = now;
	challengerPid = it->second.challengerPid;
	seenAt = it->second.seenAt;
	return true;
}

inline void Forget(uint32_t botPid)
{
	challenges.erase(botPid);
}

// How long this bot believes it is in an agreed duel.
//
// The engine knows the answer (CPVPManager::IsFighting), but on this line that
// method sits behind ENABLE_NEWSTUFF and the overlay is shared with an engine
// that may not define it at all - so asking it would be a compile-time gamble
// for a fact the bot can simply remember. Set when the bot agrees, cleared when
// it dies or the bound runs out; read by the health-potion pass, because the
// operator's rule is that a duel is fought without drinking.
inline std::map<uint32_t, uint32_t> duelUntil;

inline void NoteDuelStarted(uint32_t botPid, uint32_t until)
{
	if (botPid)
		duelUntil[botPid] = until;
}

inline bool IsInDuel(uint32_t botPid, uint32_t now)
{
	std::map<uint32_t, uint32_t>::iterator it = duelUntil.find(botPid);
	if (it == duelUntil.end())
		return false;
	if (now >= it->second)
	{
		duelUntil.erase(it);
		return false;
	}
	return true;
}

inline void EndDuel(uint32_t botPid)
{
	duelUntil.erase(botPid);
}

} // namespace playerbot_pvp

#endif
