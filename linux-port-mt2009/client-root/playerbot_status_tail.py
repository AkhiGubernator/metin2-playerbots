# A bot's status over its head, and not a line in the chat history.
#
# The server (SendPlayerBotOverheadChat in playerbot_status.h) sends a bot's
# status as the command "PlayerBotStatus <vid> <hex>" rather than as talking:
# the client puts every talking packet from a character into the chat history
# beside its text tail (RecvChatPacket), so a town full of bots filled the chat
# window. The text travels as hex because the command parser splits its line on
# spaces; the bytes are the status's own CP1250, shown as they came. The native
# tail replaces the bubble of the same VID and ignores a VID nobody can see.
#
# Written for the client's Python 2.7 without a module it might lack, and
# checked on Python 3 as well (tests/playerbot_status_tail_test.py).

MAX_STATUS_BYTES = 159
HEX_DIGITS = "0123456789abcdefABCDEF"


def decode_status(vid_arg, hex_arg):
	try:
		vid = int(vid_arg)
	except (ValueError, TypeError):
		return None
	if vid <= 0 or vid > 0xffffffff:
		return None
	if not hex_arg or len(hex_arg) > MAX_STATUS_BYTES * 2 or len(hex_arg) % 2:
		return None
	chars = []
	for i in range(0, len(hex_arg), 2):
		pair = hex_arg[i:i + 2]
		if pair[0] not in HEX_DIGITS or pair[1] not in HEX_DIGITS:
			return None
		value = int(pair, 16)
		if value < 32 or value == 127:
			return None
		chars.append(chr(value))
	# RegisterChatTail reads the VID as a signed int and keeps it as a DWORD.
	if vid >= 0x80000000:
		vid -= 0x100000000
	return vid, "".join(chars)


def show(vid_arg, hex_arg):
	status = decode_status(vid_arg, hex_arg)
	if status is None:
		return
	import textTail
	textTail.RegisterChatTail(status[0], status[1])


# A bot's personality where a player's alignment title stands.
#
# The server (ManagePlayerBotPersonalityTitle in playerbot_status.h) sends
# "PlayerBotTitle <vid> <personality>" while a player is near, about every ten
# seconds. textTail.AttachTitle writes it in the title's place, and the client
# writes the alignment title back there whenever the bot's alignment changes -
# which is every kill - so the keeper, one of game.py's updateables, attaches
# the personality again once a second for every bot heard from in the last
# minute. The names are the classic panel's, in CP1250 like every name the
# client draws; the colours are neither the alignment titles' green nor their
# red, so a personality does not read as a rank.

PERSONALITY_TITLES = {
	0: "Wytrwa\xb3y poszukiwacz",
	1: "Pogromca Metin\xf3w",
	2: "Towarzysz dru\xbfyny",
	3: "Mistrz ekwipunku",
	4: "Rozwa\xbfny zbieracz",
	5: "Handlarz",
	6: "W\xeadrowiec",
	7: "Dropek Metin\xf3w",
	8: "Dropek z M3",
	9: "Dropek z M2",
	10: "Dropek medali",
}

PERSONALITY_COLOURS = {
	0: (0.75, 0.85, 1.0),
	1: (1.0, 0.65, 0.3),
	2: (0.45, 0.9, 0.95),
	3: (1.0, 0.85, 0.35),
	4: (0.7, 0.95, 0.6),
	5: (1.0, 0.95, 0.5),
	6: (0.85, 0.75, 1.0),
	7: (1.0, 0.6, 0.6),
	8: (0.95, 0.7, 0.95),
	9: (0.8, 0.85, 0.65),
	10: (0.95, 0.8, 0.55),
}

TITLE_REFRESH_SECONDS = 1.0
TITLE_FORGET_SECONDS = 60.0


def decode_title(vid_arg, personality_arg):
	try:
		vid = int(vid_arg)
		personality = int(personality_arg)
	except (ValueError, TypeError):
		return None
	if vid <= 0 or vid > 0xffffffff or personality not in PERSONALITY_TITLES:
		return None
	# AttachTitle reads the VID as a signed int, like RegisterChatTail.
	if vid >= 0x80000000:
		vid -= 0x100000000
	return vid, personality


def attach_title(vid, personality):
	import textTail
	if not hasattr(textTail, "AttachTitle"):
		return False
	(r, g, b) = PERSONALITY_COLOURS.get(personality, (1.0, 1.0, 1.0))
	textTail.AttachTitle(vid, PERSONALITY_TITLES[personality], r, g, b)
	return True


class TitleKeeper(object):
	"""One of game.py's updateables: every title heard from, attached again."""

	def __init__(self):
		self.titles = {}
		self.nextRefresh = 0.0

	def Remember(self, vid, personality, now):
		self.titles[vid] = (personality, now)

	def CanUpdate(self):
		return bool(self.titles)

	def OnUpdate(self):
		import app
		now = app.GetTime()
		if now < self.nextRefresh:
			return
		self.nextRefresh = now + TITLE_REFRESH_SECONDS
		for vid, (personality, heard) in list(self.titles.items()):
			if now - heard > TITLE_FORGET_SECONDS:
				del self.titles[vid]
				continue
			attach_title(vid, personality)

	def Destroy(self):
		self.titles = {}


_keeper = None


def GetTitleKeeper():
	global _keeper
	if _keeper is None:
		_keeper = TitleKeeper()
	return _keeper


def show_title(vid_arg, personality_arg):
	decoded = decode_title(vid_arg, personality_arg)
	if decoded is None or not attach_title(decoded[0], decoded[1]):
		return False
	import app
	GetTitleKeeper().Remember(decoded[0], decoded[1], app.GetTime())
	return True
