# -*- coding: utf-8 -*-
"""The client's root scripts this line changes, rendered from the stock ones.

Usage:  python clientrootify.py --root <directory the stock root pack was extracted to>

    python tools/eterpack.py --profile mt2009 extract <Klient>/pack/root <dir>

Writes into client-root/ (beside serverinfo.py, which is hand-written):

  * gamerules.py  - RULES_VERSION bumped, so a client that accepted the public
                    server's terms is shown ours once (client-locale-src/rules.pl.txt);
  * intrologin.py - the three buttons of the login window: the home page is
                    the project's GitHub, the Discord is ours, and the Facebook
                    button - there is no Facebook - opens the buycoffee page.

Exact-string edits on the stock CP1250/CRLF files, byte for byte otherwise.
Idempotent; re-run after a new client package.
"""
import argparse
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, '..', 'client-root'))

EDITS = {
    'gamerules.py': [
        (b'RULES_VERSION = 3\r\n', b'RULES_VERSION = 4\r\n'),
    ],
    'intrologin.py': [
        (b'\t\tself.homePageButton.SAFE_SetEvent(self.OpenURL, "https://mt2009.pl/")\r\n',
         b'\t\tself.homePageButton.SAFE_SetEvent(self.OpenURL, "https://github.com/TieruYT/metin2-playerbots")\r\n'),
        (b'\t\tself.facebookButton.SAFE_SetEvent(self.OpenURL, "https://www.facebook.com/Metin2009PL")\r\n',
         b'\t\tself.facebookButton.SAFE_SetEvent(self.OpenURL, "https://buycoffee.to/metin2-playerbots")\r\n'),
        (b'\t\tself.discordButton.SAFE_SetEvent(self.OpenURL, "https://discord.gg/RhUaGRYZG7")\r\n',
         b'\t\tself.discordButton.SAFE_SetEvent(self.OpenURL, "https://discord.gg/pt5tvnrN6")\r\n'),
    ],
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True, help='directory holding the extracted stock root')
    args = parser.parse_args()
    os.makedirs(OUT, exist_ok=True)
    for name, edits in EDITS.items():
        src = os.path.join(args.root, name)
        if not os.path.isfile(src):
            raise SystemExit('clientrootify: no %s in %s' % (name, args.root))
        data = io.open(src, 'rb').read()
        for old, new in edits:
            if data.count(old) != 1:
                if data.count(new) == 1:
                    continue  # already ours (re-run on our own output)
                raise SystemExit('clientrootify: %s: expected exactly one %r, found %d' % (name, old[:50], data.count(old)))
            data = data.replace(old, new)
        io.open(os.path.join(OUT, name), 'wb').write(data)
        print('clientrootify: client-root/%s (%d bytes)' % (name, len(data)))


if __name__ == '__main__':
    main()
