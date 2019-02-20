from __future__ import absolute_import

import os
import sys

import pcbnew
import wx

if __name__ == "__main__":
    # Circumvent the "scripts can't do relative imports because they are not
    # packages" restriction by asserting dominance and making it a package!
    dirname = os.path.dirname(os.path.abspath(__file__))
    __package__ = os.path.basename(dirname)
    sys.path.insert(0, os.path.dirname(dirname))
    __import__(__package__)

from . import dialog
from .core import ibom
from .core.config import Config
from .schematic_data import find_latest_schematic_data
from .schematic_data import parse_schematic_data


class InteractiveHtmlBomPlugin(pcbnew.ActionPlugin):

    def defaults(self):
        """
        Method defaults must be redefined
        self.name should be the menu label to use
        self.category should be the category (not yet used)
        self.description should be a comprehensive description
          of the plugin
        """
        self.name = "Generate Interactive HTML BOM"
        self.category = "Read PCB"
        self.pcbnew_icon_support = hasattr(self, "show_toolbar_button")
        self.show_toolbar_button = True
        self.icon_file_name = os.path.join(
                os.path.dirname(__file__), 'icon.png')
        self.description = "Generate interactive HTML page that contains BOM " \
                           "table and pcb drawing."

    def Run(self):
        config = Config()
        pcb_file_name = pcbnew.GetBoard().GetFileName()
        if not pcb_file_name:
            ibom.logerror('Please save the board file before generating BOM.')
            return

        self.run_with_dialog(pcbnew.GetBoard(), config, )

    @staticmethod
    def run_with_dialog(board, config, cli=False):
        def save_config(dialog_panel):
            config.set_from_dialog(dialog_panel)
            config.save()

        dlg = dialog.SettingsDialog(
                extra_data_func=parse_schematic_data,
                config_save_func=save_config
        )
        try:
            pcb_file_name = board.GetFileName()
            config.netlist_initial_directory = os.path.dirname(pcb_file_name)
            extra_data_file = find_latest_schematic_data(pcb_file_name)
            if extra_data_file is not None:
                dlg.set_extra_data_path(extra_data_file)
            config.transfer_to_dialog(dlg.panel)
            if dlg.ShowModal() == wx.ID_OK:
                config.set_from_dialog(dlg.panel)
                ibom.main(board, config, parse_schematic_data, cli)
        finally:
            dlg.Destroy()


# python 2 and 3 compatibility hack
def to_utf(s):
    if isinstance(s, bytes):
        return s.decode('utf-8')
    else:
        return s


if __name__ == "__main__":
    app = wx.App()

    import argparse

    parser = argparse.ArgumentParser(
            description='KiCad InteractiveHtmlBom plugin CLI.',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('file',
                        type=lambda s: to_utf(s),
                        help="KiCad PCB file")
    config = Config()
    config.add_options(
            parser, dialog.GeneralSettingsPanel.FILE_NAME_FORMAT_HINT)
    args = parser.parse_args()
    if not os.path.isfile(args.file):
        print("File %s does not exist." % args.file)
        exit(1)
    print("Loading %s" % args.file)
    board = pcbnew.LoadBoard(os.path.abspath(args.file))
    if args.show_dialog:
        InteractiveHtmlBomPlugin.run_with_dialog(board, config, cli=True)
    else:
        config.set_from_args(args)
        ibom.main(board, config, parse_schematic_data, cli=True)
