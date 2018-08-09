#!/usr/bin/python2
from datetime import datetime
import pcbnew
import wx
import os
import re
import json
import sys

sys.path.append(os.path.dirname(__file__))
import units


def generate_bom(pcb, filter_layer=None):
    """
    Generate BOM from pcb layout.
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

        return sorted(l, key=alphanum_key)

    attr_dict = {0: 'Normal',
                 1: 'Normal+Insert',
                 2: 'Virtual'
                 }

    # build grouped part list
    part_groups = {}
    for m in pcb.GetModules():
        # filter part by layer
        if filter_layer is not None and filter_layer != m.GetLayer():
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

        group_key = (norm_value, footprint, attr)
        valrefs = part_groups.setdefault(group_key, [value, []])
        valrefs[1].append(m.GetReference())

    # build bom table, sort refs
    bom_table = []
    for (norm_value, footprint, attr), valrefs in part_groups.items():
        if attr == 'Virtual':
            continue
        line = (
            len(valrefs[1]), valrefs[0], footprint, natural_sort(valrefs[1]))
        bom_table.append(line)

    # sort table by reference prefix, footprint and quantity
    def sort_func(row):
        qty, _, fp, rf = row
        prefix = re.findall('^[A-Z]*', rf[0])[0]
        ref_ord = {
            "C": 1,
            "R": 2,
            "L": 3,
            "D": 4,
            "Q": 5,
            "U": 6,
            "Y": 7,
            "X": 8,
            "F": 9,
            "SW": 10,
            "A": 11,
            "HS": 1996,
            "CNN": 1997,
            "J": 1998,
            "P": 1999,
            "NT": 2000,
            "MH": 2001,
        }.get(prefix, 1000)
        return ref_ord, fp, -qty, alphanum_key(rf[0])

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
        print "Unsupported shape", d.GetShape(), "skipping."
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
            print "Polygons not supported for KiCad 4"
            polygons = []
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
    for polygon_index in xrange(polygon_set.OutlineCount()):
        outline = polygon_set.Outline(polygon_index)
        if not hasattr(outline, "PointCount"):
            print "No PointCount method on outline object. " \
                  "Unpatched kicad version?"
            return result
        parsed_outline = []
        for point_index in xrange(outline.PointCount()):
            point = outline.Point(point_index)
            parsed_outline.append(normalize([point.x, point.y]))
        result.append(parsed_outline)

    return result


def parse_text(d):
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
            print d, angle
    if hasattr(d, "GetTextHeight"):
        height = d.GetTextHeight() * 1e-6
        width = d.GetTextWidth() * 1e-6
    else:
        height = d.GetHeight() * 1e-6
        width = d.GetWidth() * 1e-6
    return {
        "pos": pos,
        "text": d.GetText(),
        "height": height,
        "width": width,
        "horiz_justify": d.GetHorizJustify(),
        "angle": angle
    }


def parse_drawing(d):
    if d.GetClass() in ["DRAWSEGMENT", "MGRAPHIC"]:
        return parse_draw_segment(d)
    elif d.GetClass() in ["PTEXT", "MTEXT"]:
        return parse_text(d)
    else:
        print "Unsupported drawing class", d.GetClass(), "skipping."
        return None


def parse_edges(pcb):
    edges = []
    bbox = None;
    for d in pcb.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts:
            parsed_drawing = parse_drawing(d)
            if parsed_drawing:
                edges.append(parsed_drawing)
                if bbox is None:
                    bbox = d.GetBoundingBox()
                else:
                    bbox.Merge(d.GetBoundingBox())
    bbox.Normalize()
    return edges, bbox


def parse_silkscreen(pcb):
    front = []
    back = []
    drawings = list(pcb.GetDrawings())
    for m in pcb.GetModules():
        drawings.append(m.Reference())
        drawings.append(m.Value())
        for d in m.GraphicalItems():
            drawings.append(d)

    for d in drawings:
        if d.GetLayer() not in [pcbnew.F_SilkS, pcbnew.B_SilkS]:
            continue
        drawing = parse_drawing(d)
        if not drawing:
            continue
        if d.GetLayer() == pcbnew.F_SilkS:
            front.append(drawing)
        else:
            back.append(drawing)

    return {
        "F": front,
        "B": back
    }


def parse_modules(pcb):
    modules = {}
    for m in pcb.GetModules():
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
            layers_set = [l for l in p.GetLayerSet().Seq()]
            layers = []
            if pcbnew.F_Cu in layers_set:
                layers.append("F")
            if pcbnew.B_Cu in layers_set:
                layers.append("B")
            pos = normalize(p.GetPosition())
            size = normalize(p.GetSize())
            is_pin1 = p.GetPadName() == "1" or p.GetPadName() == "A1"
            angle = p.GetOrientation() * -0.1
            shape_lookup = {
                pcbnew.PAD_SHAPE_RECT: "rect",
                pcbnew.PAD_SHAPE_OVAL: "oval",
                pcbnew.PAD_SHAPE_CIRCLE: "circle",
            }
            if hasattr(pcbnew, "PAD_SHAPE_ROUNDRECT"):
                shape_lookup[pcbnew.PAD_SHAPE_ROUNDRECT] = "roundrect"
            if hasattr(pcbnew, "PAD_SHAPE_CUSTOM"):
                shape_lookup[pcbnew.PAD_SHAPE_CUSTOM] = "custom"
            shape = shape_lookup.get(p.GetShape(), "")
            if shape == "":
                print "Unsupported pad shape", p.GetShape(), "skipping."
                continue
            pad_dict = {
                "layers": layers,
                "pos": pos,
                "size": size,
                "pin1": is_pin1,
                "angle": angle,
                "shape": shape
            }
            if shape == "custom":
                polygon_set = p.GetCustomShapeAsPolygon()
                if polygon_set.HasHoles():
                    print 'Detected holes in custom pad polygons'
                if polygon_set.IsSelfIntersecting():
                    print 'Detected self intersecting polygons in custom pad'
                pad_dict["polygons"] = parse_poly_set(polygon_set)
            if shape == "roundrect":
                pad_dict["radius"] = p.GetRoundRectCornerRadius() * 1e-6
            if (p.GetAttribute() == pcbnew.PAD_ATTRIB_STANDARD or
                    p.GetAttribute() == pcbnew.PAD_ATTRIB_HOLE_NOT_PLATED):
                pad_dict["type"] = "th"
                pad_dict["drillshape"] = {
                    pcbnew.PAD_DRILL_SHAPE_CIRCLE: "circle",
                    pcbnew.PAD_DRILL_SHAPE_OBLONG: "oblong"
                }.get(p.GetDrillShape())
                pad_dict["drillsize"] = normalize(p.GetDrillSize())
            else:
                pad_dict["type"] = "smd"
            pads.append(pad_dict)

        # add module
        modules[ref] = {
            "ref": ref,
            "center": center,
            "bbox": bbox,
            "pads": pads,
            "drawings": drawings,
            "layer": {
                pcbnew.F_Cu: "F",
                pcbnew.B_Cu: "B"
            }.get(m.GetLayer())
        }

    return modules


def open_file(filename):
    import subprocess
    if sys.platform.startswith('win'):
        os.startfile(filename)
    elif sys.platform.startswith('darwin'):
        subprocess.call(('open', filename))
    elif sys.platform.startswith('linux'):
        subprocess.call(('xdg-open', filename))


def generate_file(dir, pcbdata):
    def get_file_content(file_name):
        with open(os.path.join(os.path.dirname(__file__), file_name), "r") as f:
            return f.read()

    print "Dumping pcb json data"
    bom_file_name = os.path.join(dir, "ibom.html")
    if not os.path.isdir(os.path.dirname(bom_file_name)):
        os.makedirs(os.path.dirname(bom_file_name))
    pcbdata_js = "var pcbdata = " + json.dumps(pcbdata)
    html = get_file_content("ibom.html")
    html = html.replace('///CSS///', get_file_content('ibom.css'))
    html = html.replace('///SPLITJS///', get_file_content('split.js'))
    html = html.replace('///PCBDATA///', pcbdata_js)
    html = html.replace('///RENDERJS///', get_file_content('render.js'))
    html = html.replace('///IBOMJS///', get_file_content('ibom.js'))
    with open(bom_file_name, "wt") as bom:
        bom.write(html)
    print "Created file", bom_file_name
    return bom_file_name


def main(pcb, launch_browser=True):
    pcb_file_name = pcb.GetFileName()
    if not pcb_file_name:
        wx.MessageBox('Please save the board file before generating BOM.')
        return

    bom_file_dir = os.path.join(os.path.dirname(pcb_file_name), "bom")

    title_block = pcb.GetTitleBlock()
    file_date = title_block.GetDate()
    if not file_date:
        file_mtime = os.path.getmtime(pcb_file_name)
        file_date = datetime.fromtimestamp(file_mtime).strftime(
                '%Y-%m-%d %H:%M:%S')
    title = title_block.GetTitle()
    if not title:
        title = os.path.basename(pcb_file_name)
        # remove .kicad_pcb extension
        title = os.path.splitext(title)[0]
    edges, bbox = parse_edges(pcb)
    bbox = {
        "minx": bbox.GetLeft() * 1e-6,
        "miny": bbox.GetTop() * 1e-6,
        "maxx": bbox.GetRight() * 1e-6,
        "maxy": bbox.GetBottom() * 1e-6,
    }
    pcbdata = {
        "edges_bbox": bbox,
        "edges": edges,
        "silkscreen": parse_silkscreen(pcb),
        "modules": parse_modules(pcb),
        "metadata": {
            "title": title,
            "revision": title_block.GetRevision(),
            "company": title_block.GetCompany(),
            "date": file_date,
        },
        "bom": {},
    }
    if len(pcbdata["edges"]) == 0:
        wx.MessageBox('Please draw pcb outline on the edges '
                      'layer before generating BOM.')
        return
    pcbdata["bom"]["both"] = generate_bom(pcb)

    # build BOM
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        bom_table = generate_bom(pcb, filter_layer=layer)
        pcbdata["bom"]["F" if layer == pcbnew.F_Cu else "B"] = bom_table

    bom_file = generate_file(bom_file_dir, pcbdata)

    if launch_browser:
        print "Opening file in browser"
        open_file(bom_file)


class GenerateInteractiveBomPlugin(pcbnew.ActionPlugin):

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
        self.description = "Generate interactive HTML page that contains BOM " \
                           "table and pcb drawing."

    def Run(self):
        main(pcbnew.GetBoard())


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
            description='KiCad PCB pick and place assistant')
    parser.add_argument('file', type=str, help="KiCad PCB file")
    parser.add_argument('--nobrowser', help="Don't launch browser",
                        action="store_true")
    args = parser.parse_args()
    if not os.path.isfile(args.file):
        print("File %s does not exist." % args.file)
        exit(1)
    print("Loading %s" % args.file)
    main(pcbnew.LoadBoard(os.path.abspath(args.file)), not args.nobrowser)
