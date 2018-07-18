#!/usr/bin/python2
from shutil import copy
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
            "R": 3, "C": 3, "L": 1, "D": 1,
            "J": -1, "P": -1
        }.get(rf[0][0], 0)
        return -ref_ord, -qty

    bom_table = sorted(bom_table, key=sort_func)

    return bom_table


def normalize(point):
    return [point[0] * 1e-6, point[1] * 1e-6]


def parse_draw_segment(d):
    shape = {
        pcbnew.S_SEGMENT: "segment",
        pcbnew.S_CIRCLE: "circle",
        pcbnew.S_ARC: "arc"
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
    drawings = []
    for d in pcb.GetDrawings():
        drawings.append(d)
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
            "layer": {
                pcbnew.F_Cu: "F",
                pcbnew.B_Cu: "B"
            }.get(m.GetLayer())
        }

    return modules


def main(pcb):
    pcbdata = {
        "edges": parse_edges(pcb),
        "silkscreen": parse_silkscreen(pcb),
        "modules": parse_modules(pcb),
        "bom": {}
    }
    pcbdata["bom"]["both"] = generate_bom(pcb)

    # build BOM
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        bom_table = generate_bom(pcb, filter_layer=layer)
        pcbdata["bom"]["F" if layer == pcbnew.F_Cu else "B"] = bom_table

    print "Dumping pcb json data"
    picknplace_dir = os.path.dirname(pcb.GetFileName()) + "/picknplace/"
    jsonfilename = picknplace_dir + "pcbdata.js"
    if not os.path.isdir(os.path.dirname(jsonfilename)):
        os.makedirs(os.path.dirname(jsonfilename))
    copy(os.path.dirname(__file__) + "/ibom.html", picknplace_dir)
    with open(jsonfilename, "wt") as js:
        js.write("var pcbdata = ")
        js.write(json.dumps(pcbdata))

    os.system("start " + picknplace_dir + "/ibom.html")


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
        self.description = "Generate interactive HTML page that contains BOM table and pcb drawing."

    def Run(self):
        main(pcbnew.GetBoard())


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
            description='KiCad PCB pick and place assistant')
    parser.add_argument('file', type=str, help="KiCad PCB file")
    args = parser.parse_args()
    print("Loading %s" % args.file)
    main(pcbnew.LoadBoard(args.file))

else:
    GenerateInteractiveBomPlugin().register()
