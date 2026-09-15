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
