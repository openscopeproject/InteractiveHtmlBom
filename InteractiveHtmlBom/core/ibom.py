from __future__ import absolute_import

import io
import json
import logging
import os
import re
import sys
from datetime import datetime

import pcbnew
import wx

from . import units
from .config import Config
from .fontparser import FontParser


def setup_logger():
    logger = logging.getLogger('InteractiveHtmlBom')
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter(
            "%(asctime)-15s %(levelname)s %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


logger = setup_logger()
is_cli = False
font_parser = FontParser()


def loginfo(*args):
    if is_cli:
        logger.info(*args)


def logerror(msg):
    if is_cli:
        logger.error(msg)
    else:
        wx.MessageBox(msg)


def logwarn(msg):
    if is_cli:
        logger.warn(msg)
    else:
        wx.LogWarning(msg)


def skip_component(m, config, extra_data, filter_layer):
    # type: (pcbnew.MODULE, Config, dict, int) -> bool
    # filter part by layer
    if filter_layer is not None and filter_layer != m.GetLayer():
        return True

    # skip blacklisted components
    ref = m.GetReference()
    ref_prefix = re.findall('^[A-Z]*', ref)[0]
    if ref in config.component_blacklist:
        return True
    if ref_prefix + '*' in config.component_blacklist:
        return True

    val = m.GetValue()
    if config.blacklist_empty_val and val in ['', '~']:
        return True

    # skip components with dnp field not empty
    if config.dnp_field and ref in extra_data \
            and config.dnp_field in extra_data[ref] \
            and extra_data[ref][config.dnp_field]:
        return True

    # skip components with wrong variant field
    if config.board_variant_field and config.board_variant_whitelist:
        if ref in extra_data:
            ref_variant = extra_data[ref].get(config.board_variant_field, '')
            if ref_variant not in config.board_variant_whitelist:
                return True

    if config.board_variant_field and config.board_variant_blacklist:
        if ref in extra_data:
            ref_variant = extra_data[ref].get(config.board_variant_field, '')
            if ref_variant and ref_variant in config.board_variant_blacklist:
                return True

    return False


def generate_bom(pcb_modules, config, extra_data, filter_layer=None):
    # type: (list, Config, dict, int) -> list
    """
    Generate BOM from pcb layout.
    :param pcb_modules: list of modules on the pcb
    :param config: Config object
    :param extra_data: Extra fields data
    :param filter_layer: include only parts for given layer
    :return: BOM table (qty, value, footprint, refs)
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

    attr_dict = {0: 'Normal',
                 1: 'Normal+Insert',
                 2: 'Virtual'
                 }

    # build grouped part list
    warning_shown = False
    part_groups = {}
    for i, m in enumerate(pcb_modules):
        if skip_component(m, config, extra_data, filter_layer):
            continue

        # group part refs by value and footprint
        value = m.GetValue()
        norm_value = units.componentValue(value)
        try:
            footprint = str(m.GetFPID().GetFootprintName())
        except:
            footprint = str(m.GetFPID().GetLibItemName())
        attr = m.GetAttributes()
        if attr in attr_dict:
            attr = attr_dict[attr]
        else:
            attr = str(attr)

        # skip virtual components if needed
        if config.blacklist_virtual and attr == 'Virtual':
            continue

        ref = m.GetReference()
        extras = []
        if config.extra_fields:
            if ref in extra_data:
                extras = [extra_data[ref].get(f, '')
                          for f in config.extra_fields]
            else:
                # Some components are on pcb but not in schematic data.
                # Show a warning about possibly outdated netlist/xml file.
                # Doing it only once when generating full bom is enough.
                if filter_layer is None:
                    logwarn(
                            'Component %s is missing from schematic data.' % ref)
                    warning_shown = True
                extras = [''] * len(config.extra_fields)

        group_key = (norm_value, tuple(extras), footprint, attr)
        valrefs = part_groups.setdefault(group_key, [value, []])
        valrefs[1].append((ref, i))

    if warning_shown:
        logwarn('Netlist/xml file is likely out of date.')
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

    return bom_table


def normalize(point):
    return [point[0] * 1e-6, point[1] * 1e-6]


def parse_draw_segment(d):
    shape = {
        pcbnew.S_SEGMENT: "segment",
        pcbnew.S_CIRCLE: "circle",
        pcbnew.S_ARC: "arc",
        pcbnew.S_POLYGON: "polygon",
    }.get(d.GetShape(), "")
    if shape == "":
        loginfo("Unsupported shape %s, skipping", d.GetShape())
        return None
    start = normalize(d.GetStart())
    end = normalize(d.GetEnd())
    if shape == "segment":
        return {
            "type": shape,
            "start": start,
            "end": end,
            "width": d.GetWidth() * 1e-6
        }
    if shape == "circle":
        return {
            "type": shape,
            "start": start,
            "radius": d.GetRadius() * 1e-6,
            "width": d.GetWidth() * 1e-6
        }
    if shape == "arc":
        a1 = d.GetArcAngleStart() * 0.1
        a2 = (d.GetArcAngleStart() + d.GetAngle()) * 0.1
        if d.GetAngle() < 0:
            (a1, a2) = (a2, a1)
        r = d.GetRadius() * 1e-6
        return {
            "type": shape,
            "start": start,
            "radius": r,
            "startangle": a1,
            "endangle": a2,
            "width": d.GetWidth() * 1e-6
        }
    if shape == "polygon":
        if hasattr(d, "GetPolyShape"):
            polygons = parse_poly_set(d.GetPolyShape())
        else:
            loginfo("Polygons not supported for KiCad 4, skipping")
            return None
        angle = 0
        if d.GetParentModule() is not None:
            angle = d.GetParentModule().GetOrientation() * 0.1,
        return {
            "type": shape,
            "pos": start,
            "angle": angle,
            "polygons": polygons
        }


def parse_poly_set(polygon_set):
    result = []
    for polygon_index in range(polygon_set.OutlineCount()):
        outline = polygon_set.Outline(polygon_index)
        if not hasattr(outline, "PointCount"):
            logwarn("No PointCount method on outline object. "
                    "Unpatched kicad version?")
            return result
        parsed_outline = []
        for point_index in range(outline.PointCount()):
            point = outline.Point(point_index)
            parsed_outline.append(normalize([point.x, point.y]))
        result.append(parsed_outline)

    return result


def parse_text(d, ref_val=None):
    pos = normalize(d.GetPosition())
    if not d.IsVisible():
        return None
    if d.GetClass() == "MTEXT":
        angle = d.GetDrawRotation() * 0.1
    else:
        if hasattr(d, "GetTextAngle"):
            angle = d.GetTextAngle() * 0.1
        else:
            angle = d.GetOrientation() * 0.1
    if hasattr(d, "GetTextHeight"):
        height = d.GetTextHeight() * 1e-6
        width = d.GetTextWidth() * 1e-6
    else:
        height = d.GetHeight() * 1e-6
        width = d.GetWidth() * 1e-6
    if hasattr(d, "GetShownText"):
        text = d.GetShownText()
    else:
        text = d.GetText()
    font_parser.parse_font_for_string(text)
    attributes = []
    if d.IsMirrored():
        attributes.append("mirrored")
    if d.IsItalic():
        attributes.append("italic")
    if d.IsBold():
        attributes.append("bold")
    return {
        "pos": pos,
        "text": text,
        "height": height,
        "width": width,
        "horiz_justify": d.GetHorizJustify(),
        "thickness": d.GetThickness() * 1e-6,
        "attr": attributes,
        "angle": angle
    }


def parse_drawing(d):
    if d.GetClass() in ["DRAWSEGMENT", "MGRAPHIC"]:
        return parse_draw_segment(d)
    elif d.GetClass() in ["PTEXT", "MTEXT"]:
        return parse_text(d)
    else:
        loginfo("Unsupported drawing class %s, skipping", d.GetClass())
        return None


def parse_edges(pcb):
    edges = []
    drawings = list(pcb.GetDrawings())
    bbox = None
    for m in pcb.GetModules():
        for g in m.GraphicalItems():
            drawings.append(g)
    for d in drawings:
        if d.GetLayer() == pcbnew.Edge_Cuts:
            parsed_drawing = parse_drawing(d)
            if parsed_drawing:
                edges.append(parsed_drawing)
                if bbox is None:
                    bbox = d.GetBoundingBox()
                else:
                    bbox.Merge(d.GetBoundingBox())
    if bbox:
        bbox.Normalize()
    return edges, bbox


def parse_drawings_on_layers(drawings, f_layer, b_layer):
    front = []
    back = []

    for d in drawings:
        if d[1].GetLayer() not in [f_layer, b_layer]:
            continue
        drawing = parse_drawing(d[1])
        if not drawing:
            continue
        if d[0] in ["ref", "val"]:
            drawing[d[0]] = 1
        if d[1].GetLayer() == f_layer:
            front.append(drawing)
        else:
            back.append(drawing)

    return {
        "F": front,
        "B": back
    }


def get_all_drawings(pcb):
    drawings = [(d.GetClass(), d) for d in list(pcb.GetDrawings())]
    for m in pcb.GetModules():
        drawings.append(("ref", m.Reference()))
        drawings.append(("val", m.Value()))
        for d in m.GraphicalItems():
            drawings.append((d.GetClass(), d))
    return drawings


def parse_pad(pad):
    layers_set = list(pad.GetLayerSet().Seq())
    layers = []
    if pcbnew.F_Cu in layers_set:
        layers.append("F")
    if pcbnew.B_Cu in layers_set:
        layers.append("B")
    pos = normalize(pad.GetPosition())
    size = normalize(pad.GetSize())
    is_pin1 = pad.GetPadName() in ['1', 'A', 'A1', 'P1', 'PAD1']
    angle = pad.GetOrientation() * -0.1
    shape_lookup = {
        pcbnew.PAD_SHAPE_RECT: "rect",
        pcbnew.PAD_SHAPE_OVAL: "oval",
        pcbnew.PAD_SHAPE_CIRCLE: "circle",
    }
    if hasattr(pcbnew, "PAD_SHAPE_ROUNDRECT"):
        shape_lookup[pcbnew.PAD_SHAPE_ROUNDRECT] = "roundrect"
    if hasattr(pcbnew, "PAD_SHAPE_CUSTOM"):
        shape_lookup[pcbnew.PAD_SHAPE_CUSTOM] = "custom"
    shape = shape_lookup.get(pad.GetShape(), "")
    if shape == "":
        loginfo("Unsupported pad shape %s, skipping.", pad.GetShape())
        return None
    pad_dict = {
        "layers": layers,
        "pos": pos,
        "size": size,
        "angle": angle,
        "shape": shape
    }
    if is_pin1:
        pad_dict['pin1'] = 1
    if shape == "custom":
        polygon_set = pad.GetCustomShapeAsPolygon()
        if polygon_set.HasHoles():
            logwarn('Detected holes in custom pad polygons')
        if polygon_set.IsSelfIntersecting():
            logwarn('Detected self intersecting polygons in custom pad')
        pad_dict["polygons"] = parse_poly_set(polygon_set)
    if shape == "roundrect":
        pad_dict["radius"] = pad.GetRoundRectCornerRadius() * 1e-6
    if (pad.GetAttribute() == pcbnew.PAD_ATTRIB_STANDARD or
            pad.GetAttribute() == pcbnew.PAD_ATTRIB_HOLE_NOT_PLATED):
        pad_dict["type"] = "th"
        pad_dict["drillshape"] = {
            pcbnew.PAD_DRILL_SHAPE_CIRCLE: "circle",
            pcbnew.PAD_DRILL_SHAPE_OBLONG: "oblong"
        }.get(pad.GetDrillShape())
        pad_dict["drillsize"] = normalize(pad.GetDrillSize())
    else:
        pad_dict["type"] = "smd"
    if hasattr(pad, "GetOffset"):
        pad_dict["offset"] = normalize(pad.GetOffset())

    return pad_dict


def parse_modules(pcb_modules):
    # type: (list) -> list
    modules = []
    for m in pcb_modules:
        ref = m.GetReference()
        center = normalize(m.GetCenter())

        # bounding box
        mrect = m.GetFootprintRect()
        mrect_pos = normalize(mrect.GetPosition())
        mrect_size = normalize(mrect.GetSize())
        bbox = {
            "pos": mrect_pos,
            "size": mrect_size
        }

        # graphical drawings
        drawings = []
        for d in m.GraphicalItems():
            # we only care about copper ones, silkscreen is taken care of
            if d.GetLayer() not in [pcbnew.F_Cu, pcbnew.B_Cu]:
                continue
            drawing = parse_drawing(d)
            if not drawing:
                continue
            drawings.append({
                "layer": "F" if d.GetLayer() == pcbnew.F_Cu else "B",
                "drawing": drawing,
            })

        # footprint pads
        pads = []
        for p in m.Pads():
            pad_dict = parse_pad(p)
            if pad_dict is not None:
                pads.append((p.GetPadName(), pad_dict))

        # If no pads have common 'first' pad name then pick lexicographically.
        pin1_pads = [p for p in pads if 'pin1' in p[1]]
        if pads and not pin1_pads:
            pads = sorted(pads, key=lambda el: el[0])
            for pad_name, pad_dict in pads:
                if pad_name:
                    pad_dict['pin1'] = 1
                    break

        pads = [p[1] for p in pads]

        # add module
        modules.append({
            "ref": ref,
            "center": center,
            "bbox": bbox,
            "pads": pads,
            "drawings": drawings,
            "layer": {
                pcbnew.F_Cu: "F",
                pcbnew.B_Cu: "B"
            }.get(m.GetLayer())
        })

    return modules


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
        logwarn('Failed to open browser: {}'.format(oe.message))


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
    name = re.sub(r'[/\\?%*:|"<>]', '_', name)
    return name + '.html'


def generate_file(pcb_file_dir, pcb_file_name, pcbdata, config):
    def get_file_content(file_name):
        path = os.path.join(os.path.dirname(__file__), "..", "web", file_name)
        with io.open(path, 'r', encoding='utf-8') as f:
            return f.read()

    loginfo("Dumping pcb json data")

    if os.path.isabs(config.bom_dest_dir):
        bom_file_dir = config.bom_dest_dir
    else:
        bom_file_dir = os.path.join(pcb_file_dir, config.bom_dest_dir)
    if not os.path.isdir(bom_file_dir):
        os.makedirs(bom_file_dir)
    bom_file_name = process_substitutions(
            config.bom_name_format, pcb_file_name, pcbdata['metadata'])
    bom_file_name = os.path.join(bom_file_dir, bom_file_name)
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
    loginfo("Created file %s", bom_file_name)
    return bom_file_name


def main(pcb, config, parse_schematic_data, cli=False):
    # type: (pcbnew.BOARD, Config, lambda: str, bool) -> None
    global is_cli
    is_cli = cli
    pcb_file_name = pcb.GetFileName()
    # Get extra field data
    extra_fields = None
    if config.netlist_file and os.path.isfile(config.netlist_file):
        extra_fields = parse_schematic_data(
                config.netlist_file, config.normalize_field_case)

    need_extra_fields = (config.extra_fields or
                         config.board_variant_whitelist or
                         config.board_variant_blacklist or
                         config.dnp_field)

    if not config.netlist_file and need_extra_fields:
        logwarn('Ignoring extra fields related config parameters '
                'since no netlist/xml file was specified.')
        config.extra_fields = []
        config.board_variant_whitelist = []
        config.board_variant_blacklist = []
        config.dnp_field = ''
        need_extra_fields = False

    if extra_fields is None and need_extra_fields:
        logerror('Failed parsing %s' % config.netlist_file)
        return

    extra_fields = extra_fields[1] if extra_fields else None

    pcb_file_dir = os.path.dirname(pcb_file_name)

    title_block = pcb.GetTitleBlock()
    file_date = title_block.GetDate()
    if not file_date:
        file_mtime = os.path.getmtime(pcb_file_name)
        file_date = datetime.fromtimestamp(file_mtime).strftime(
                '%Y-%m-%d %H:%M:%S')
    title = title_block.GetTitle()
    pcb_file_name = os.path.basename(pcb_file_name)
    if not title:
        # remove .kicad_pcb extension
        title = os.path.splitext(pcb_file_name)[0]
    edges, bbox = parse_edges(pcb)
    if bbox is None:
        logerror('Please draw pcb outline on the edges '
                 'layer on sheet or any module before '
                 'generating BOM.')
        return
    bbox = {
        "minx": bbox.GetPosition().x * 1e-6,
        "miny": bbox.GetPosition().y * 1e-6,
        "maxx": bbox.GetRight() * 1e-6,
        "maxy": bbox.GetBottom() * 1e-6,
    }

    pcb_modules = list(pcb.GetModules())
    drawings = get_all_drawings(pcb)

    pcbdata = {
        "edges_bbox": bbox,
        "edges": edges,
        "silkscreen": parse_drawings_on_layers(
                drawings, pcbnew.F_SilkS, pcbnew.B_SilkS),
        "fabrication": parse_drawings_on_layers(
                drawings, pcbnew.F_Fab, pcbnew.B_Fab),
        "modules": parse_modules(pcb_modules),
        "metadata": {
            "title": title,
            "revision": title_block.GetRevision(),
            "company": title_block.GetCompany(),
            "date": file_date,
        },
        "bom": {},
    }
    pcbdata["bom"]["both"] = generate_bom(pcb_modules, config, extra_fields)

    # build BOM
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        bom_table = generate_bom(pcb_modules, config, extra_fields,
                                 filter_layer=layer)
        pcbdata["bom"]["F" if layer == pcbnew.F_Cu else "B"] = bom_table

    pcbdata["font_data"] = font_parser.get_parsed_font()
    bom_file = generate_file(pcb_file_dir, pcb_file_name, pcbdata, config)

    if config.open_browser:
        loginfo("Opening file in browser")
        open_file(bom_file)
