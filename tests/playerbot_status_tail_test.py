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


if __name__ == '__main__':
    unittest.main()
