# -*- coding: utf-8 -*-
"""playerbot_status_tail.py - the client root's half of a bot's status bubble.

    docker run --rm -v "$(pwd -W)":/w -w /w python:2.7-slim python tests/playerbot_status_tail_test.py
    docker run --rm -v "$(pwd -W)":/w -w /w python:3.12-slim python tests/playerbot_status_tail_test.py

The client runs Python 2.7, so the module is written for it and checked on both.
"""
import os
import sys
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', 'linux-port-mt2009', 'client-root'))
import playerbot_status_tail as status


def hexed(raw):
    return ''.join('%02x' % b for b in bytearray(raw))


def as_bytes(text):
    if isinstance(text, type(u'')):
        return bytearray(text, 'latin-1')
    return bytearray(text)


class StatusTailTest(unittest.TestCase):
    def test_cp1250_spaces_and_colon_arrive_as_sent(self):
        raw = u'Idę do kowala: żółć, ąęśćń!'.encode('cp1250')
        vid, text = status.decode_status('42', hexed(raw))
        self.assertEqual(vid, 42)
        self.assertEqual(as_bytes(text), bytearray(raw))

    def test_upper_case_hex_is_accepted(self):
        self.assertEqual(status.decode_status('7', '4142')[1], 'AB')

    def test_refused(self):
        for vid, text in [('0', '61'), ('-1', '61'), ('4294967296', '61'), ('x', '61'),
                          (None, '61'), ('1', ''), ('1', None), ('1', 'f'), ('1', 'zz'),
                          ('1', '+1'), ('1', ' 1'), ('1', '00'), ('1', '0a'), ('1', '1f'),
                          ('1', '7f'), ('1', '61' * 160)]:
            self.assertIsNone(status.decode_status(vid, text), (vid, text))

    def test_limits(self):
        self.assertEqual(status.decode_status('4294967295', '61'), (-1, 'a'))
        self.assertEqual(status.decode_status('2147483648', '61'), (-2147483648, 'a'))
        self.assertEqual(status.decode_status('1', '61' * 159), (1, 'a' * 159))

    def test_only_the_native_tail_is_called(self):
        calls = []
        native = types.ModuleType('textTail')
        native.RegisterChatTail = lambda vid, text: calls.append((vid, text))
        old = sys.modules.get('textTail')
        sys.modules['textTail'] = native
        try:
            status.show('42', '6162')
            status.show('42', '6364')
            status.show('42', 'xx')
            status.show('0', '6162')
            self.assertEqual(calls, [(42, 'ab'), (42, 'cd')])
        finally:
            if old is None:
                del sys.modules['textTail']
            else:
                sys.modules['textTail'] = old


class TitleTest(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.now = [100.0]
        native = types.ModuleType('textTail')
        native.AttachTitle = lambda vid, text, r, g, b: self.calls.append((vid, text))
        clock = types.ModuleType('app')
        clock.GetTime = lambda: self.now[0]
        self.saved = dict((name, sys.modules.get(name)) for name in ('textTail', 'app'))
        sys.modules['textTail'] = native
        sys.modules['app'] = clock
        status._keeper = None

    def tearDown(self):
        for name, module in self.saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module
        status._keeper = None

    def test_decoding(self):
        self.assertEqual(status.decode_title('42', '3'), (42, 3))
        self.assertEqual(status.decode_title('4294967295', '10'), (-1, 10))
        for vid, personality in [('0', '1'), ('42', '11'), ('42', '-1'), ('x', '1'),
                                 ('42', None), ('4294967296', '1')]:
            self.assertIsNone(status.decode_title(vid, personality), (vid, personality))

    def test_every_personality_has_a_title_and_a_colour(self):
        self.assertEqual(sorted(status.PERSONALITY_TITLES), list(range(11)))
        self.assertEqual(sorted(status.PERSONALITY_COLOURS), list(range(11)))

    def test_attached_and_kept_for_a_minute(self):
        self.assertTrue(status.show_title('42', '1'))
        self.assertEqual(self.calls, [(42, status.PERSONALITY_TITLES[1])])
        keeper = status.GetTitleKeeper()
        self.assertTrue(keeper.CanUpdate())
        self.now[0] += 1.5
        keeper.OnUpdate()
        self.assertEqual(len(self.calls), 2)
        self.now[0] += 0.5
        keeper.OnUpdate()
        self.assertEqual(len(self.calls), 2)
        self.now[0] += 61.0
        keeper.OnUpdate()
        self.assertEqual(len(self.calls), 2)
        self.assertFalse(keeper.CanUpdate())

    def test_a_client_without_attach_title_draws_nothing(self):
        del sys.modules['textTail'].AttachTitle
        self.assertFalse(status.show_title('42', '1'))
        self.assertEqual(self.calls, [])


if __name__ == '__main__':
    unittest.main()
