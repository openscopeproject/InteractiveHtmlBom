#!/usr/bin/python3
from __future__ import absolute_import

import argparse
import os
import sys


# python 2 and 3 compatibility hack
def to_utf(s):
    if isinstance(s, bytes):
        return s.decode('utf-8')
    else:
        return s


if __name__ == "__main__":
    # Add ../ to the path
    # Works if this script is executed without installing the module
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(script_dir))
    os.environ['INTERACTIVE_HTML_BOM_CLI_MODE'] = 'True'
    import InteractiveHtmlBom

    from InteractiveHtmlBom.core import ibom
    from InteractiveHtmlBom.core.config import Config
    from InteractiveHtmlBom.ecad import get_parser_by_extension
    from InteractiveHtmlBom.version import version
    from InteractiveHtmlBom.errors import (ExitCodes, ParsingException,
                                          exit_error)

    create_wx_app = 'INTERACTIVE_HTML_BOM_NO_DISPLAY' not in os.environ
    if create_wx_app:
        import wx
        app = wx.App()

    parser = argparse.ArgumentParser(
            description='KiCad InteractiveHtmlBom plugin CLI.',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('file',
                        type=lambda s: to_utf(s),
                        help="KiCad PCB file")
    config = Config(version)
    config.add_options(parser, config.FILE_NAME_FORMAT_HINT)
    args = parser.parse_args()
    logger = ibom.Logger(cli=True)
    if not os.path.isfile(args.file):
        exit_error(logger, ExitCodes.ERROR_FILE_NOT_FOUND,
                   "File %s does not exist." % args.file)
    print("Loading %s" % args.file)
    parser = get_parser_by_extension(os.path.abspath(args.file), config, logger)
    if args.show_dialog:
        if not create_wx_app:
            exit_error(logger, ExitCodes.ERROR_NO_DISPLAY, "Can not show dialog when "
                       "INTERACTIVE_HTML_BOM_NO_DISPLAY is set.")
        try:
            ibom.run_with_dialog(parser, config, logger)
        except ParsingException as e:
            exit_error(logger, ExitCodes.ERROR_PARSE, e)
    else:
        config.set_from_args(args)
        try:
            ibom.main(parser, config, logger)
        except ParsingException as e:
            exit_error(logger, ExitCodes.ERROR_PARSE, str(e))
