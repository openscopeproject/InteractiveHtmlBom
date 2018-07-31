#!/usr/bin/python2
from shutil import copy
from datetime import datetime
import pcbnew
import wx
import os
import re
import json
import sys

sys.path.append(os.path.dirname(__file__))
import units


def natural_sort(l):
    """
    Natural sort for strings containing numbers
    """

    def convert(text): return int(text) if text.isdigit() else text.lower()

    def alphanum_key(key): return [convert(c)
                                   for c in re.split('([0-9]+)', key)]

    return sorted(l, key=alphanum_key)


def generate_bom(pcb, filter_layer=None):
    """
    Generate BOM from pcb layout.
    :param filter_layer: include only parts for given layer
    :return: BOM table (qty, value, footprint, refs)
    """
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

    # sort table by reference prefix and quantity
    def sort_func(row):
        qty, _, _, rf = row
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
            "S": 10,
            "J": 1001,
            "P": 1002
        }.get(rf[0][0], 1000)
        return ref_ord, -qty

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
        print "Unsupported shape", d.GetShape()
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
        print "Circle shape", d.GetRadius() * 1e-6
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
        return {
            "type": shape,
            "pos": start,
            "angle": d.GetParentModule().GetOrientation() * 0.1,
            "polygons": parse_poly_set(d.GetPolyShape())
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
        angle = d.GetTextAngle() * 0.1
    return {
        "pos": pos,
        "text": d.GetText(),
        "height": d.GetTextHeight() * 1e-6,
        "width": d.GetTextWidth() * 1e-6,
        "horiz_justify": d.GetHorizJustify(),
        "angle": angle
    }


def parse_drawing(d):
    if d.GetClass() in ["DRAWSEGMENT", "MGRAPHIC"]:
        return parse_draw_segment(d)
    elif d.GetClass() in ["PTEXT", "MTEXT"]:
        return parse_text(d)
    else:
        print "Unsupported drawing class ", d.GetClass()
        return None


def parse_edges(pcb):
    edges = []
    for d in pcb.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts:
            edges.append(parse_drawing(d))

    return edges


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
            shape = {
                pcbnew.PAD_SHAPE_RECT: "rect",
                pcbnew.PAD_SHAPE_OVAL: "oval",
                pcbnew.PAD_SHAPE_CIRCLE: "circle",
                pcbnew.PAD_SHAPE_ROUNDRECT: "roundrect",
                pcbnew.PAD_SHAPE_CUSTOM: "custom",
            }.get(p.GetShape(), "unsupported")
            if shape == "unsupported":
                print "Unsupported pad shape ", p.GetShape()
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


def main(pcb, launch_browser=True):
    pcb_file_name = pcb.GetFileName()
    if not pcb_file_name:
        wx.MessageBox('Please save the board file before generating BOM.')
        return

    bom_file_name = os.path.splitext(pcb_file_name)[0] + " - iBOM.html"

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
    pcbdata = {
        "edges": parse_edges(pcb),
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

    print "Dumping pcb json data"
    if not os.path.isdir(os.path.dirname(bom_file_name)):
        os.makedirs(os.path.dirname(bom_file_name))
    pcbdata_js = "var pcbdata = " + json.dumps(pcbdata)
    with open(os.path.join(os.path.dirname(__file__), "ibom.html"), "r") as html:
        html_content = html.read()
        html_content = html_content.replace('///PCBDATA///', pcbdata_js)
    with open(bom_file_name, "wt") as bom:
        bom.write(html_content)

    if launch_browser:
        open_file(bom_file_name)


class GenerateInteractiveBomPlugin(pcbnew.ActionPlugin):

    def defaults(self):
        """
        Method defaults must be redefined
        self.name should be the menu label to use
        self.category should be the category (not yet used)
        self.description should be a comprehensive description
          of the plugin
        """
        self.name = "Interactive HTML BOM"
        self.category = "Read PCB"
        self.description = "Generate interactive HTML page that contains BOM table and pcb drawing."

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
