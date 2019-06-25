from __future__ import absolute_import

import io
import json
import logging
import os
import re
import sys
from datetime import datetime

import wx

from . import units
from .config import Config
from ..dialog import SettingsDialog
from ..ecad.common import EcadParser, Component


class Logger(object):

    def __init__(self, cli=False):
        self.cli = cli
        self.logger = logging.getLogger('InteractiveHtmlBom')
        self.logger.setLevel(logging.INFO)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter(
                "%(asctime)-15s %(levelname)s %(message)s")
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    def info(self, *args):
        if self.cli:
            self.logger.info(*args)

    def error(self, msg):
        if self.cli:
            self.logger.error(msg)
        else:
            wx.MessageBox(msg)

    def warn(self, msg):
        if self.cli:
            self.logger.warn(msg)
        else:
            wx.LogWarning(msg)


log = None  # type: Logger or None


def skip_component(m, config, extra_data):
    # type: (Component, Config, dict) -> bool
    # skip blacklisted components
    ref_prefix = re.findall('^[A-Z]*', m.ref)[0]
    if m.ref in config.component_blacklist:
        return True
    if ref_prefix + '*' in config.component_blacklist:
        return True

    if config.blacklist_empty_val and m.val in ['', '~']:
        return True

    # skip virtual components if needed
    if config.blacklist_virtual and m.attr == 'Virtual':
        return True

    # skip components with dnp field not empty
    if config.dnp_field and m.ref in extra_data \
            and config.dnp_field in extra_data[m.ref] \
            and extra_data[m.ref][config.dnp_field]:
        return True

    # skip components with wrong variant field
    if config.board_variant_field and config.board_variant_whitelist:
        if m.ref in extra_data:
            ref_variant = extra_data[m.ref].get(config.board_variant_field, '')
            if ref_variant not in config.board_variant_whitelist:
                return True

    if config.board_variant_field and config.board_variant_blacklist:
        if m.ref in extra_data:
            ref_variant = extra_data[m.ref].get(config.board_variant_field, '')
            if ref_variant and ref_variant in config.board_variant_blacklist:
                return True

    return False


def generate_bom(pcb_modules, config, extra_data):
    # type: (list, Config, dict) -> dict
    """
    Generate BOM from pcb layout.
    :param pcb_modules: list of modules on the pcb
    :param config: Config object
    :param extra_data: Extra fields data
    :return: dict of BOM tables (qty, value, footprint, refs) and dnp components
    """

    def convert(text):
        return int(text) if text.isdigit() else text.lower()

    def alphanum_key(key):
        return [convert(c)
                for c in re.split('([0-9]+)', key)]

    def natural_sort(l):
        """
        Natural sort for strings containing numbers
        """

        return sorted(l, key=lambda r: (alphanum_key(r[0]), r[1]))

    # build grouped part list
    warning_shown = False
    skipped_components = []
    part_groups = {}
    for i, m in enumerate(pcb_modules):
        if skip_component(m, config, extra_data):
            skipped_components.append(i)
            continue

        # group part refs by value and footprint
        norm_value = units.componentValue(m.val)

        extras = []
        if config.extra_fields:
            if m.ref in extra_data:
                extras = [extra_data[m.ref].get(f, '')
                          for f in config.extra_fields]
            else:
                # Some components are on pcb but not in schematic data.
                # Show a warning about possibly outdated netlist/xml file.
                log.warn(
                        'Component %s is missing from schematic data.' % m.ref)
                warning_shown = True
                extras = [''] * len(config.extra_fields)

        group_key = (norm_value, tuple(extras), m.footprint, m.attr)
        valrefs = part_groups.setdefault(group_key, [m.val, []])
        valrefs[1].append((m.ref, i))

    if warning_shown:
        log.warn('Netlist/xml file is likely out of date.')
    # build bom table, sort refs
    bom_table = []
    for (norm_value, extras, footprint, attr), valrefs in part_groups.items():
        bom_row = (
            len(valrefs[1]), valrefs[0], footprint,
            natural_sort(valrefs[1]), extras)
        bom_table.append(bom_row)

    # sort table by reference prefix, footprint and quantity
    def sort_func(row):
        qty, _, fp, rf, e = row
        prefix = re.findall('^[A-Z]*', rf[0][0])[0]
        if prefix in config.component_sort_order:
            ref_ord = config.component_sort_order.index(prefix)
        else:
            ref_ord = config.component_sort_order.index('~')
        return ref_ord, e, fp, -qty, alphanum_key(rf[0][0])

    if '~' not in config.component_sort_order:
        config.component_sort_order.append('~')
    bom_table = sorted(bom_table, key=sort_func)

    result = {
        'both': bom_table,
        'skipped': skipped_components
    }

    for layer in ['F', 'B']:
        filtered_table = []
        for row in bom_table:
            filtered_refs = [ref for ref in row[3]
                             if pcb_modules[ref[1]].layer == layer]
            if filtered_refs:
                filtered_table.append((len(filtered_refs), row[1],
                                       row[2], filtered_refs, row[4]))

        result[layer] = sorted(filtered_table, key=sort_func)

    return result


def open_file(filename):
    import subprocess
    try:
        if sys.platform.startswith('win'):
            os.startfile(filename)
        elif sys.platform.startswith('darwin'):
            subprocess.call(('open', filename))
        elif sys.platform.startswith('linux'):
            subprocess.call(('xdg-open', filename))
    except OSError as oe:
        log.warn('Failed to open browser: {}'.format(oe.message))


def process_substitutions(bom_name_format, pcb_file_name, metadata):
    # type: (str, str, dict)->str
    name = bom_name_format.replace('%f', os.path.splitext(pcb_file_name)[0])
    name = name.replace('%p', metadata['title'])
    name = name.replace('%c', metadata['company'])
    name = name.replace('%r', metadata['revision'])
    name = name.replace('%d', metadata['date'].replace(':', '-'))
    now = datetime.now()
    name = name.replace('%D', now.strftime('%Y-%m-%d'))
    name = name.replace('%T', now.strftime('%H-%M-%S'))
    # sanitize the name to avoid characters illegal in file systems
    name = name.replace('\\', '/')
    name = re.sub(r'[?%*:|"<>]', '_', name)
    return name + '.html'


def generate_file(pcb_file_dir, pcb_file_name, pcbdata, config):
    def get_file_content(file_name):
        path = os.path.join(os.path.dirname(__file__), "..", "web", file_name)
        with io.open(path, 'r', encoding='utf-8') as f:
            return f.read()

    log.info("Dumping pcb json data")

    if os.path.isabs(config.bom_dest_dir):
        bom_file_dir = config.bom_dest_dir
    else:
        bom_file_dir = os.path.join(pcb_file_dir, config.bom_dest_dir)
    bom_file_name = process_substitutions(
            config.bom_name_format, pcb_file_name, pcbdata['metadata'])
    bom_file_name = os.path.join(bom_file_dir, bom_file_name)
    bom_file_dir = os.path.dirname(bom_file_name)
    if not os.path.isdir(bom_file_dir):
        os.makedirs(bom_file_dir)
    pcbdata_js = "var pcbdata = " + json.dumps(pcbdata)
    config_js = "var config = " + config.get_html_config()
    html = get_file_content("ibom.html")
    html = html.replace('///CSS///', get_file_content('ibom.css'))
    html = html.replace('///SPLITJS///', get_file_content('split.js'))
    html = html.replace('///POINTER_EVENTS_POLYFILL///',
                        get_file_content('pep.js'))
    html = html.replace('///CONFIG///', config_js)
    html = html.replace('///PCBDATA///', pcbdata_js)
    html = html.replace('///UTILJS///', get_file_content('util.js'))
    html = html.replace('///RENDERJS///', get_file_content('render.js'))
    html = html.replace('///IBOMJS///', get_file_content('ibom.js'))
    with io.open(bom_file_name, 'wt', encoding='utf-8') as bom:
        bom.write(html)
    log.info("Created file %s", bom_file_name)
    return bom_file_name


def main(parser, config, logger):
    # type: (EcadParser, Config, Logger) -> None
    global log
    log = logger
    pcb_file_name = os.path.basename(parser.file_name)
    pcb_file_dir = os.path.dirname(parser.file_name)

    # Get extra field data
    extra_fields = None
    if config.netlist_file and os.path.isfile(config.netlist_file):
        extra_fields = parser.extra_data_func(
                config.netlist_file, config.normalize_field_case)

    need_extra_fields = (config.extra_fields or
                         config.board_variant_whitelist or
                         config.board_variant_blacklist or
                         config.dnp_field)

    if not config.netlist_file and need_extra_fields:
        logger.warn('Ignoring extra fields related config parameters '
                    'since no netlist/xml file was specified.')
        config.extra_fields = []
        config.board_variant_whitelist = []
        config.board_variant_blacklist = []
        config.dnp_field = ''
        need_extra_fields = False

    if extra_fields is None and need_extra_fields:
        logger.error('Failed parsing %s' % config.netlist_file)
        return

    extra_fields = extra_fields[1] if extra_fields else None

    pcbdata, components = parser.parse()
    if not pcbdata or not components:
        logger.error('Parsing failed.')
        return

    pcbdata["bom"] = generate_bom(components, config, extra_fields)

    # build BOM
    bom_file = generate_file(pcb_file_dir, pcb_file_name, pcbdata, config)

    if config.open_browser:
        logger.info("Opening file in browser")
        open_file(bom_file)


def run_with_dialog(parser, config, logger):
    # type: (EcadParser, Config, Logger) -> None
    def save_config(dialog_panel):
        config.set_from_dialog(dialog_panel)
        config.save()

    dlg = SettingsDialog(
            extra_data_func=parser.extra_data_func,
            config_save_func=save_config,
            file_name_format_hint=config.FILE_NAME_FORMAT_HINT,
    )
    try:
        config.netlist_initial_directory = os.path.dirname(parser.file_name)
        extra_data_file = parser.latest_extra_data(
                extra_dirs=[config.bom_dest_dir])
        if extra_data_file is not None:
            dlg.set_extra_data_path(extra_data_file)
        config.transfer_to_dialog(dlg.panel)
        if dlg.ShowModal() == wx.ID_OK:
            config.set_from_dialog(dlg.panel)
            main(parser, config, logger)
    finally:
        dlg.Destroy()
