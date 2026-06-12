#!/usr/bin/env python3
"""Entry point for KiCad's IPC plugin system.

KiCad launches this script in its own process (inside the plugin's
virtual environment) when the user clicks the iBOM action button.
Connection parameters are passed via the KICAD_API_SOCKET and
KICAD_API_TOKEN environment variables, which kipy picks up
automatically.

With wxPython available the regular settings dialog is shown;
otherwise the BOM is generated headlessly with the saved
(or default) settings.
"""

import os
import sys

# Prevent InteractiveHtmlBom/__init__.py from trying to register the
# legacy SWIG action plugin when the package is imported.
os.environ['INTERACTIVE_HTML_BOM_CLI_MODE'] = '1'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from InteractiveHtmlBom.core import ibom  # noqa: E402
from InteractiveHtmlBom.core.config import Config  # noqa: E402
from InteractiveHtmlBom.ecad import get_kicad_ipc_parser  # noqa: E402
from InteractiveHtmlBom.errors import ParsingException  # noqa: E402
from InteractiveHtmlBom.version import version  # noqa: E402
from InteractiveHtmlBom.compat import get_wx  # noqa: E402


def main():
    wx = get_wx()
    app = None
    if wx is not None:
        app = wx.App()
        if hasattr(wx, "APP_ASSERT_SUPPRESS"):
            app.SetAssertMode(wx.APP_ASSERT_SUPPRESS)

    logger = ibom.Logger(cli=(wx is None))

    try:
        from kipy import KiCad
        kicad = KiCad()
        board = kicad.get_board()
    except Exception as e:
        logger.error("Cannot connect to KiCad via the IPC API: %s" % e)
        return 1

    file_name = board.name
    if not file_name:
        logger.error('Please save the board file before generating BOM.')
        return 1

    project = board.get_project()
    pcb_file_name = os.path.join(project.path, file_name)

    config = Config(version, os.path.dirname(pcb_file_name))
    parser = get_kicad_ipc_parser(pcb_file_name, config, logger, kicad, board)

    try:
        if wx is not None:
            ibom.run_with_dialog(parser, config, logger)
        else:
            config.load_from_ini()
            ibom.main(parser, config, logger)
    except ParsingException as e:
        logger.error(str(e))
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
