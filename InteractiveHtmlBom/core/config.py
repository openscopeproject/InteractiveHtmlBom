"""Config object"""

import argparse
import os
import re

from wx import FileConfig

from .. import dialog


class Config:
    FILE_NAME_FORMAT_HINT = (
        'Output file name format supports substitutions:\n'
        '\n'
        '    %f : original pcb file name without extension.\n'
        '    %p : pcb/project title from pcb metadata.\n'
        '    %c : company from pcb metadata.\n'
        '    %r : revision from pcb metadata.\n'
        '    %d : pcb date from metadata if available, '
        'file modification date otherwise.\n'
        '    %D : bom generation date.\n'
        '    %T : bom generation time.\n'
        '\n'
        'Extension .html will be added automatically.'
    )  # type: str

    # Helper constants
    config_file = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
    bom_view_choices = ['bom-only', 'left-right', 'top-bottom']
    layer_view_choices = ['F', 'FB', 'B']
    default_sort_order = [
        'C', 'R', 'L', 'D', 'U', 'Y', 'X', 'F', 'SW', 'A',
        '~',
        'HS', 'CNN', 'J', 'P', 'NT', 'MH',
    ]
    default_checkboxes = ['Sourced', 'Placed']
    html_config_fields = [
        'dark_mode', 'show_pads', 'show_fabrication', 'show_silkscreen',
        'highlight_pin1', 'redraw_on_drag', 'board_rotation', 'checkboxes',
        'bom_view', 'layer_view', 'extra_fields'
    ]

    # Defaults

    # HTML section
    dark_mode = False
    show_pads = True
    show_fabrication = False
    show_silkscreen = True
    highlight_pin1 = False
    redraw_on_drag = True
    board_rotation = 0
    checkboxes = ','.join(default_checkboxes)
    bom_view = bom_view_choices[1]
    layer_view = layer_view_choices[1]
    open_browser = True

    # General section
    bom_dest_dir = 'bom/'  # This is relative to pcb file directory
    bom_name_format = 'ibom'
    component_sort_order = default_sort_order
    component_blacklist = []
    blacklist_virtual = True
    blacklist_empty_val = False

    # Extra fields section
    netlist_file = None
    netlist_initial_directory = ''  # This is relative to pcb file directory
    extra_fields = []
    normalize_field_case = False
    board_variant_field = ''
    board_variant_whitelist = []
    board_variant_blacklist = []
    dnp_field = ''

    @staticmethod
    def _split(s):
        """Splits string by ',' and drops empty strings from resulting array."""
        return [a.replace('\\,', ',') for a in re.split(r'(?<!\\),', s) if a]

    def __init__(self):
        """Init from config file if it exists."""
        if not os.path.isfile(self.config_file):
            return
        f = FileConfig(localFilename=self.config_file)

        f.SetPath('/html_defaults')
        self.dark_mode = f.ReadBool('dark_mode', self.dark_mode)
        self.show_pads = f.ReadBool('show_pads', self.show_pads)
        self.show_fabrication = f.ReadBool(
                'show_fabrication', self.show_fabrication)
        self.show_silkscreen = f.ReadBool(
                'show_silkscreen', self.show_silkscreen)
        self.highlight_pin1 = f.ReadBool('highlight_pin1', self.highlight_pin1)
        self.redraw_on_drag = f.ReadBool('redraw_on_drag', self.redraw_on_drag)
        self.board_rotation = f.ReadInt('board_rotation', self.board_rotation)
        self.checkboxes = f.Read('checkboxes', self.checkboxes)
        self.bom_view = f.Read('bom_view', self.bom_view)
        self.layer_view = f.Read('layer_view', self.layer_view)
        self.open_browser = f.ReadBool('open_browser', self.open_browser)

        f.SetPath('/general')
        self.bom_dest_dir = f.Read('bom_dest_dir', self.bom_dest_dir)
        self.bom_name_format = f.Read('bom_name_format', self.bom_name_format)
        self.component_sort_order = self._split(f.Read(
                'component_sort_order',
                ','.join(self.component_sort_order)))
        self.component_blacklist = self._split(f.Read(
                'component_blacklist',
                ','.join(self.component_blacklist)))
        self.blacklist_virtual = f.ReadBool(
                'blacklist_virtual', self.blacklist_virtual)
        self.blacklist_empty_val = f.ReadBool(
                'blacklist_empty_val', self.blacklist_empty_val)

        f.SetPath('/extra_fields')
        self.extra_fields = self._split(f.Read(
                'extra_fields',
                ','.join(self.extra_fields)))
        self.normalize_field_case = f.ReadBool(
                'normalize_field_case', self.normalize_field_case)
        self.board_variant_field = f.Read(
                'board_variant_field', self.board_variant_field)
        self.board_variant_whitelist = self._split(f.Read(
                'board_variant_whitelist',
                ','.join(self.board_variant_whitelist)))
        self.board_variant_blacklist = self._split(f.Read(
                'board_variant_blacklist',
                ','.join(self.board_variant_blacklist)))
        self.dnp_field = f.Read('dnp_field', self.dnp_field)

    def save(self):
        f = FileConfig(localFilename=self.config_file)

        f.SetPath('/html_defaults')
        f.WriteBool('dark_mode', self.dark_mode)
        f.WriteBool('show_pads', self.show_pads)
        f.WriteBool('show_fabrication', self.show_fabrication)
        f.WriteBool('show_silkscreen', self.show_silkscreen)
        f.WriteBool('highlight_pin1', self.highlight_pin1)
        f.WriteBool('redraw_on_drag', self.redraw_on_drag)
        f.WriteInt('board_rotation', self.board_rotation)
        f.Write('checkboxes', self.checkboxes)
        f.Write('bom_view', self.bom_view)
        f.Write('layer_view', self.layer_view)
        f.WriteBool('open_browser', self.open_browser)

        f.SetPath('/general')
        bom_dest_dir = self.bom_dest_dir
        if bom_dest_dir.startswith(self.netlist_initial_directory):
            bom_dest_dir = os.path.relpath(
                    bom_dest_dir, self.netlist_initial_directory)
        f.Write('bom_dest_dir', bom_dest_dir)
        f.Write('bom_name_format', self.bom_name_format)
        f.Write('component_sort_order',
                ','.join(self.component_sort_order))
        f.Write('component_blacklist',
                ','.join(self.component_blacklist))
        f.WriteBool('blacklist_virtual', self.blacklist_virtual)
        f.WriteBool('blacklist_empty_val', self.blacklist_empty_val)

        f.SetPath('/extra_fields')
        f.Write('extra_fields', ','.join(self.extra_fields))
        f.WriteBool('normalize_field_case', self.normalize_field_case)
        f.Write('board_variant_field', self.board_variant_field)
        f.Write('board_variant_whitelist',
                ','.join(self.board_variant_whitelist))
        f.Write('board_variant_blacklist',
                ','.join(self.board_variant_blacklist))
        f.Write('dnp_field', self.dnp_field)
        f.Flush()

    def set_from_dialog(self, dlg):
        # type: (dialog.settings_dialog.SettingsDialogPanel) -> None
        # Html
        self.dark_mode = dlg.html.darkModeCheckbox.IsChecked()
        self.show_pads = dlg.html.showPadsCheckbox.IsChecked()
        self.show_fabrication = dlg.html.showFabricationCheckbox.IsChecked()
        self.show_silkscreen = dlg.html.showSilkscreenCheckbox.IsChecked()
        self.highlight_pin1 = dlg.html.highlightPin1Checkbox.IsChecked()
        self.redraw_on_drag = dlg.html.continuousRedrawCheckbox.IsChecked()
        self.board_rotation = dlg.html.boardRotationSlider.Value
        self.checkboxes = dlg.html.bomCheckboxesCtrl.Value
        self.bom_view = self.bom_view_choices[dlg.html.bomDefaultView.Selection]
        self.layer_view = self.layer_view_choices[
            dlg.html.layerDefaultView.Selection]
        self.open_browser = dlg.html.openBrowserCheckbox.IsChecked()

        # General
        self.bom_dest_dir = dlg.general.bomDirPicker.Path
        self.bom_name_format = dlg.general.fileNameFormatTextControl.Value
        self.component_sort_order = dlg.general.componentSortOrderBox.GetItems()
        self.component_blacklist = dlg.general.blacklistBox.GetItems()
        self.blacklist_virtual = \
            dlg.general.blacklistVirtualCheckbox.IsChecked()
        self.blacklist_empty_val = \
            dlg.general.blacklistEmptyValCheckbox.IsChecked()

        # Extra fields
        self.netlist_file = dlg.extra.netlistFilePicker.Path
        self.extra_fields = list(dlg.extra.extraFieldsList.GetCheckedStrings())
        self.normalize_field_case = dlg.extra.normalizeCaseCheckbox.Value
        self.board_variant_field = dlg.extra.boardVariantFieldBox.Value
        if self.board_variant_field == dlg.extra.NONE_STRING:
            self.board_variant_field = ''
        self.board_variant_whitelist = list(
                dlg.extra.boardVariantWhitelist.GetCheckedStrings())
        self.board_variant_blacklist = list(
                dlg.extra.boardVariantBlacklist.GetCheckedStrings())
        self.dnp_field = dlg.extra.dnpFieldBox.Value
        if self.dnp_field == dlg.extra.NONE_STRING:
            self.dnp_field = ''

    def transfer_to_dialog(self, dlg):
        # type: (dialog.settings_dialog.SettingsDialogPanel) -> None
        # Html
        dlg.html.darkModeCheckbox.Value = self.dark_mode
        dlg.html.showPadsCheckbox.Value = self.show_pads
        dlg.html.showFabricationCheckbox.Value = self.show_fabrication
        dlg.html.showSilkscreenCheckbox.Value = self.show_silkscreen
        dlg.html.highlightPin1Checkbox.Value = self.highlight_pin1
        dlg.html.continuousRedrawCheckbox.value = self.redraw_on_drag
        dlg.html.boardRotationSlider.Value = self.board_rotation
        dlg.html.bomCheckboxesCtrl.Value = self.checkboxes
        dlg.html.bomDefaultView.Selection = self.bom_view_choices.index(
                self.bom_view)
        dlg.html.layerDefaultView.Selection = self.layer_view_choices.index(
                self.layer_view)
        dlg.html.openBrowserCheckbox.Value = self.open_browser

        # General
        import os.path
        if os.path.isabs(self.bom_dest_dir):
            dlg.general.bomDirPicker.Path = self.bom_dest_dir
        else:
            dlg.general.bomDirPicker.Path = os.path.join(
                    self.netlist_initial_directory, self.bom_dest_dir)
        dlg.general.fileNameFormatTextControl.Value = self.bom_name_format
        dlg.general.componentSortOrderBox.SetItems(self.component_sort_order)
        dlg.general.blacklistBox.SetItems(self.component_blacklist)
        dlg.general.blacklistVirtualCheckbox.Value = self.blacklist_virtual
        dlg.general.blacklistEmptyValCheckbox.Value = self.blacklist_empty_val

        # Extra fields
        dlg.extra.netlistFilePicker.SetInitialDirectory(
                self.netlist_initial_directory)

        def safe_set_checked_strings(clb, strings):
            safe_strings = list(clb.GetStrings())
            clb.SetCheckedStrings([s for s in strings if s in safe_strings])

        safe_set_checked_strings(dlg.extra.extraFieldsList, self.extra_fields)
        dlg.extra.normalizeCaseCheckbox.Value = self.normalize_field_case
        dlg.extra.boardVariantFieldBox.Value = self.board_variant_field
        dlg.extra.OnBoardVariantFieldChange(None)
        safe_set_checked_strings(dlg.extra.boardVariantWhitelist,
                                 self.board_variant_whitelist)
        safe_set_checked_strings(dlg.extra.boardVariantBlacklist,
                                 self.board_variant_blacklist)
        dlg.extra.dnpFieldBox.Value = self.dnp_field

        dlg.finish_init()

    # noinspection PyTypeChecker
    def add_options(self, parser, file_name_format_hint):
        # type: (argparse.ArgumentParser, str) -> None
        parser.add_argument('--show-dialog', action='store_true',
                            help='Shows config dialog. All other flags '
                                 'will be ignored.')
        # Html
        parser.add_argument('--dark-mode', help='Default to dark mode.',
                            action='store_true')
        parser.add_argument('--hide-pads',
                            help='Hide footprint pads by default.',
                            action='store_true')
        parser.add_argument('--show-fabrication',
                            help='Show fabrication layer by default.',
                            action='store_true')
        parser.add_argument('--hide-silkscreen',
                            help='Hide silkscreen by default.',
                            action='store_true')
        parser.add_argument('--highlight-pin1',
                            help='Highlight pin1 by default.',
                            action='store_true')
        parser.add_argument('--no-redraw-on-drag',
                            help='Do not redraw pcb on drag by default.',
                            action='store_true')
        parser.add_argument('--board-rotation', type=int,
                            default=self.board_rotation * 5,
                            help='Board rotation in degrees (-180 to 180). '
                                 'Will be rounded to multiple of 5.')
        parser.add_argument('--checkboxes',
                            default=self.checkboxes,
                            help='Comma separated list of checkbox columns.')
        parser.add_argument('--bom-view', default=self.bom_view,
                            choices=self.bom_view_choices,
                            help='Default BOM view.')
        parser.add_argument('--layer-view', default=self.layer_view,
                            choices=self.layer_view_choices,
                            help='Default layer view.')
        parser.add_argument('--no-browser', help='Do not launch browser.',
                            action='store_true')

        # General
        parser.add_argument('--dest-dir', default=self.bom_dest_dir,
                            help='Destination directory for bom file '
                                 'relative to pcb file directory.')
        parser.add_argument('--name-format', default=self.bom_name_format,
                            help=file_name_format_hint.replace('%', '%%'))
        parser.add_argument('--sort-order',
                            help='Default sort order for components. '
                                 'Must contain "~" once.',
                            default=','.join(self.component_sort_order))
        parser.add_argument('--blacklist',
                            default=','.join(self.component_blacklist),
                            help='List of comma separated blacklisted '
                                 'components or prefixes with *. E.g. "X1,MH*"')
        parser.add_argument('--no-blacklist-virtual', action='store_true',
                            help='Do not blacklist virtual components.')
        parser.add_argument('--blacklist-empty-val', action='store_true',
                            help='Blacklist components with empty value.')

        # Extra fields section
        parser.add_argument('--netlist-file',
                            help='Path to netlist or xml file.')
        parser.add_argument('--extra-fields',
                            default=','.join(self.extra_fields),
                            help='Comma separated list of extra fields to '
                                 'pull from netlist or xml file.')
        parser.add_argument('--normalize-field-case',
                            help='Normalize extra field name case. E.g. "MPN" '
                                 'and "mpn" will be considered the same field.',
                            action='store_true')
        parser.add_argument('--variant-field',
                            help='Name of the extra field that stores board '
                                 'variant for component.')
        parser.add_argument('--variants-whitelist', default='', nargs='+',
                            help='List of board variants to '
                                 'include in the BOM.')
        parser.add_argument('--variants-blacklist', default='', nargs='+',
                            help='List of board variants to '
                                 'exclude from the BOM.')
        parser.add_argument('--dnp-field', default=self.dnp_field,
                            help='Name of the extra field that indicates '
                                 'do not populate status. Components with this '
                                 'field not empty will be blacklisted.')

    def set_from_args(self, args):
        # type: (argparse.Namespace) -> None
        import math

        # Html
        self.dark_mode = args.dark_mode
        self.show_pads = not args.hide_pads
        self.show_fabrication = args.show_fabrication
        self.show_silkscreen = not args.hide_silkscreen
        self.highlight_pin1 = args.highlight_pin1
        self.redraw_on_drag = not args.no_redraw_on_drag
        self.board_rotation = math.fmod(args.board_rotation // 5, 37)
        self.checkboxes = args.checkboxes
        self.bom_view = args.bom_view
        self.layer_view = args.layer_view
        self.open_browser = not args.no_browser

        # General
        self.bom_dest_dir = args.dest_dir
        self.bom_name_format = args.name_format
        self.component_sort_order = self._split(args.sort_order)
        self.component_blacklist = self._split(args.blacklist)
        self.blacklist_virtual = not args.no_blacklist_virtual
        self.blacklist_empty_val = args.blacklist_empty_val

        # Extra
        self.netlist_file = args.netlist_file
        self.extra_fields = self._split(args.extra_fields)
        self.normalize_field_case = args.normalize_field_case
        self.board_variant_field = args.variant_field
        self.board_variant_whitelist = args.variants_whitelist
        self.board_variant_blacklist = args.variants_blacklist
        self.dnp_field = args.dnp_field

    def get_html_config(self):
        import json
        d = {f: getattr(self, f) for f in self.html_config_fields}
        return json.dumps(d)
