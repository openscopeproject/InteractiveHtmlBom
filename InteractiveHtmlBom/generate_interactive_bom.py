from __future__ import absolute_import

import argparse
import os
import sys

import wx


# python 2 and 3 compatibility hack
def to_utf(s):
    if isinstance(s, bytes):
        return s.decode('utf-8')
    else:
        return s


if __name__ == "__main__":
    # Circumvent the "scripts can't do relative imports because they are not
    # packages" restriction by asserting dominance and making it a package!
    dirname = os.path.dirname(os.path.abspath(__file__))
    __package__ = os.path.basename(dirname)
    sys.path.insert(0, os.path.dirname(dirname))
    os.environ['INTERACTIVE_HTML_BOM_CLI_MODE'] = 'True'
    __import__(__package__)

    from .core import ibom
    from .core.config import Config
    from .ecad import get_parser_by_extension

    app = wx.App()

    parser = argparse.ArgumentParser(
            description='KiCad InteractiveHtmlBom plugin CLI.',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('file',
                        type=lambda s: to_utf(s),
                        help="KiCad PCB file")
    config = Config()
    config.add_options(parser, config.FILE_NAME_FORMAT_HINT)
    args = parser.parse_args()
    if not os.path.isfile(args.file):
        print("File %s does not exist." % args.file)
        exit(1)
    print("Loading %s" % args.file)
    logger = ibom.Logger(cli=True)
    parser = get_parser_by_extension(os.path.abspath(args.file), logger)
    if args.show_dialog:
        ibom.run_with_dialog(parser, config, logger)
    else:
        config.set_from_args(args)
        ibom.main(parser, config, logger)
