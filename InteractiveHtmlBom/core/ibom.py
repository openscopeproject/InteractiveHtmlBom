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
from ..errors import ParsingException


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
            self.logger.warning(msg)
        else:
            wx.LogWarning(msg)


log = None


def skip_component(m, config):
    # type: (Component, Config) -> bool
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
    if config.dnp_field \
            and config.dnp_field in m.extra_fields \
            and m.extra_fields[config.dnp_field]:
        return True

    # skip components with wrong variant field
    if config.board_variant_field and config.board_variant_whitelist:
        ref_variant = m.extra_fields.get(config.board_variant_field, '')
        if ref_variant not in config.board_variant_whitelist:
            return True

    if config.board_variant_field and config.board_variant_blacklist:
        ref_variant = m.extra_fields.get(config.board_variant_field, '')
        if ref_variant and ref_variant in config.board_variant_blacklist:
            return True

    return False


def generate_bom(pcb_footprints, config):
    # type: (list, Config) -> dict
    """
    Generate BOM from pcb layout.
    :param pcb_footprints: list of footprints on the pcb
    :param config: Config object
    :return: dict of BOM tables (qty, value, footprint, refs)
             and dnp components
    """

    def convert(text):
        return int(text) if text.isdigit() else text.lower()

    def alphanum_key(key):
        return [convert(c)
                for c in re.split('([0-9]+)', key)]

    def natural_sort(lst):
        """
        Natural sort for strings containing numbers
        """

        return sorted(lst, key=lambda r: (alphanum_key(r[0]), r[1]))

    # build grouped part list
    skipped_components = []
    part_groups = {}
    group_by = set(config.group_fields)
    index_to_fields = {}

    for i, f in enumerate(pcb_footprints):
        if skip_component(f, config):
            skipped_components.append(i)
            continue

        # group part refs by value and footprint
        fields = []
        group_key = []

        for field in config.show_fields:
            if field == "Value":
                fields.append(f.val)
                if "Value" in group_by:
                    norm_value, unit = units.componentValue(f.val, f.ref)
                    group_key.append(norm_value)
                    group_key.append(unit)
            elif field == "Footprint":
                fields.append(f.footprint)
                if "Footprint" in group_by:
                    group_key.append(f.footprint)
                    group_key.append(f.attr)
            else:
                fields.append(f.extra_fields.get(field, ''))
                if field in group_by:
                    group_key.append(f.extra_fields.get(field, ''))

        index_to_fields[i] = fields
        refs = part_groups.setdefault(tuple(group_key), [])
        refs.append((f.ref, i))

    bom_table = []

    # If some extra fields are just integers then convert the whole column
    # so that sorting will work naturally
    for i, field in enumerate(config.show_fields):
        if field in ["Value", "Footprint"]:
            continue
        all_num = True
        for f in index_to_fields.values():
            if not f[i].isdigit() and len(f[i].strip()) > 0:
                all_num = False
                break
        if all_num:
            for f in index_to_fields.values():
                if f[i].isdigit():
                    f[i] = int(f[i])

    for _, refs in part_groups.items():
        # Fixup values to normalized string
        if "Value" in group_by and "Value" in config.show_fields:
            index = config.show_fields.index("Value")
            value = index_to_fields[refs[0][1]][index]
            for ref in refs:
                index_to_fields[ref[1]][index] = value

        bom_table.append(natural_sort(refs))

    # sort table by reference prefix and quantity
    def row_sort_key(element):
        prefix = re.findall('^[^0-9]*', element[0][0])[0]
        if prefix in config.component_sort_order:
            ref_ord = config.component_sort_order.index(prefix)
        else:
            ref_ord = config.component_sort_order.index('~')
        return ref_ord, -len(element), alphanum_key(element[0][0])

    if '~' not in config.component_sort_order:
        config.component_sort_order.append('~')

    bom_table = sorted(bom_table, key=row_sort_key)

    result = {
        'both': bom_table,
        'skipped': skipped_components,
        'fields': index_to_fields
    }

    for layer in ['F', 'B']:
        filtered_table = []
        for row in bom_table:
            filtered_refs = [ref for ref in row
                             if pcb_footprints[ref[1]].layer == layer]
            if filtered_refs:
                filtered_table.append(filtered_refs)

        result[layer] = sorted(filtered_table, key=row_sort_key)

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
    except Exception as e:
        log.warn('Failed to open browser: {}'.format(e))


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


def round_floats(o, precision):
    if isinstance(o, float):
        return round(o, precision)
    if isinstance(o, dict):
        return {k: round_floats(v, precision) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [round_floats(x, precision) for x in o]
    return o


def get_pcbdata_javascript(pcbdata, compression):
    from .lzstring import LZString

    js = "var pcbdata = {}"
    pcbdata_str = json.dumps(round_floats(pcbdata, 6))

    if compression:
        log.info("Compressing pcb data")
        pcbdata_str = json.dumps(LZString().compress_to_base64(pcbdata_str))
        js = "var pcbdata = JSON.parse(LZString.decompressFromBase64({}))"

    return js.format(pcbdata_str)


def generate_file(pcb_file_dir, pcb_file_name, pcbdata, config):
    def get_file_content(file_name):
        path = os.path.join(os.path.dirname(__file__), "..", "web", file_name)
        if not os.path.exists(path):
            return ""
        with io.open(path, 'r', encoding='utf-8') as f:
            return f.read()

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
    pcbdata_js = get_pcbdata_javascript(pcbdata, config.compression)
    log.info("Dumping pcb data")
    config_js = "var config = " + config.get_html_config()
    html = get_file_content("ibom.html")
    html = html.replace('///CSS///', get_file_content('ibom.css'))
    html = html.replace('///USERCSS///', get_file_content('user.css'))
    html = html.replace('///SPLITJS///', get_file_content('split.js'))
    html = html.replace('///LZ-STRING///',
                        get_file_content('lz-string.js')
                        if config.compression else '')
    html = html.replace('///POINTER_EVENTS_POLYFILL///',
                        get_file_content('pep.js'))
    html = html.replace('///CONFIG///', config_js)
    html = html.replace('///UTILJS///', get_file_content('util.js'))
    html = html.replace('///RENDERJS///', get_file_content('render.js'))
    html = html.replace('///TABLEUTILJS///', get_file_content('table-util.js'))
    html = html.replace('///IBOMJS///', get_file_content('ibom.js'))
    html = html.replace('///USERJS///', get_file_content('user.js'))
    html = html.replace('///USERHEADER///',
                        get_file_content('userheader.html'))
    html = html.replace('///USERFOOTER///',
                        get_file_content('userfooter.html'))
    # Replace pcbdata last for better performance.
    html = html.replace('///PCBDATA///', pcbdata_js)

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

    pcbdata, components = parser.parse()
    if not pcbdata and not components:
        raise ParsingException('Parsing failed.')

    pcbdata["bom"] = generate_bom(components, config)
    pcbdata["ibom_version"] = config.version

    # build BOM
    bom_file = generate_file(pcb_file_dir, pcb_file_name, pcbdata, config)

    if config.open_browser:
        logger.info("Opening file in browser")
        open_file(bom_file)


def run_with_dialog(parser, config, logger):
    # type: (EcadParser, Config, Logger) -> None
    def save_config(dialog_panel, locally=False):
        config.set_from_dialog(dialog_panel)
        config.save(locally)

    config.load_from_ini()
    dlg = SettingsDialog(extra_data_func=parser.parse_extra_data,
                         extra_data_wildcard=parser.extra_data_file_filter(),
                         config_save_func=save_config,
                         file_name_format_hint=config.FILE_NAME_FORMAT_HINT,
                         version=config.version)
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
