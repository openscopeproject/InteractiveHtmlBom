import os
from datetime import datetime

import pcbnew

from .common import EcadParser, Component, ExtraFieldData
from .kicad_extra import find_latest_schematic_data, parse_schematic_data
from .svgpath import create_path
from ..core import ibom
from ..core.config import Config
from ..core.fontparser import FontParser


KICAD_VERSION = [5, 1, 0]

if hasattr(pcbnew, 'Version'):
    version = pcbnew.Version().split('.')
    try:
        for i in range(len(version)):
            version[i] = int(version[i].split('-')[0])
    except ValueError:
        pass
    KICAD_VERSION = version


class PcbnewParser(EcadParser):

    def __init__(self, file_name, config, logger, board=None):
        super(PcbnewParser, self).__init__(file_name, config, logger)
        self.board = board
        if self.board is None:
            self.board = pcbnew.LoadBoard(self.file_name)  # type: pcbnew.BOARD
        if hasattr(self.board, 'GetModules'):
            self.footprints = list(self.board.GetModules())  # type: list[pcbnew.MODULE]
        else:
            self.footprints = list(self.board.GetFootprints())  # type: list[pcbnew.FOOTPRINT]
        self.font_parser = FontParser()

    def get_extra_field_data(self, file_name):
        if os.path.abspath(file_name) == os.path.abspath(self.file_name):
            return self.parse_extra_data_from_pcb()
        if os.path.splitext(file_name)[1] == '.kicad_pcb':
            return None

        data = parse_schematic_data(file_name)

        return ExtraFieldData(data[0], data[1])

    @staticmethod
    def get_footprint_fields(f):
        # type: (pcbnew.FOOTPRINT) -> dict
        props = {}
        if hasattr(f, "GetProperties"):
            props = f.GetProperties()
        if hasattr(f, "GetFields"):
            props = f.GetFieldsShownText()
        if "dnp" in props and props["dnp"] == "":
            del props["dnp"]
            props["kicad_dnp"] = "DNP"
        if hasattr(f, "IsDNP"):
            if f.IsDNP():
                props["kicad_dnp"] = "DNP"
        return props

    def parse_extra_data_from_pcb(self):
        field_set = set()
        by_ref = {}
        by_index = {}

        for (i, f) in enumerate(self.footprints):
            props = self.get_footprint_fields(f)
            by_index[i] = props
            ref = f.GetReference()
            ref_fields = by_ref.setdefault(ref, {})

            for k, v in props.items():
                field_set.add(k)
                ref_fields[k] = v

        return ExtraFieldData(list(field_set), by_ref, by_index)

    def latest_extra_data(self, extra_dirs=None):
        base_name = os.path.splitext(os.path.basename(self.file_name))[0]
        extra_dirs.append(self.board.GetPlotOptions().GetOutputDirectory())
        file_dir_name = os.path.dirname(self.file_name)
        directories = [file_dir_name]
        for dir in extra_dirs:
            if not os.path.isabs(dir):
                dir = os.path.join(file_dir_name, dir)
            if os.path.exists(dir):
                directories.append(dir)
        return find_latest_schematic_data(base_name, directories)

    def extra_data_file_filter(self):
        if hasattr(self.board, 'GetModules'):
            return "Netlist and xml files (*.net; *.xml)|*.net;*.xml"
        else:
            return ("Netlist, xml and pcb files (*.net; *.xml; *.kicad_pcb)|"
                    "*.net;*.xml;*.kicad_pcb")

    @staticmethod
    def normalize(point):
        return [point.x * 1e-6, point.y * 1e-6]

    @staticmethod
    def normalize_angle(angle):
        if isinstance(angle, int) or isinstance(angle, float):
            return angle * 0.1
        else:
            return angle.AsDegrees()

    def get_arc_angles(self, d):
        # type: (pcbnew.PCB_SHAPE) -> tuple
        a1 = self.normalize_angle(d.GetArcAngleStart())
        if hasattr(d, "GetAngle"):
            a2 = a1 + self.normalize_angle(d.GetAngle())
        else:
            a2 = a1 + self.normalize_angle(d.GetArcAngle())
        if a2 < a1:
            a1, a2 = a2, a1
        return round(a1, 2), round(a2, 2)

    def parse_shape(self, d):
        # type: (pcbnew.PCB_SHAPE) -> dict | None
        shape = {
            pcbnew.S_SEGMENT: "segment",
            pcbnew.S_CIRCLE: "circle",
            pcbnew.S_ARC: "arc",
            pcbnew.S_POLYGON: "polygon",
            pcbnew.S_CURVE: "curve",
            pcbnew.S_RECT: "rect",
        }.get(d.GetShape(), "")
        if shape == "":
            self.logger.info("Unsupported shape %s, skipping", d.GetShape())
            return None
        start = self.normalize(d.GetStart())
        end = self.normalize(d.GetEnd())
        if shape == "segment":
            return {
                "type": shape,
                "start": start,
                "end": end,
                "width": d.GetWidth() * 1e-6
            }

        if shape == "rect":
            if hasattr(d, "GetRectCorners"):
                points = list(map(self.normalize, d.GetRectCorners()))
            else:
                points = [
                    start,
                    [end[0], start[1]],
                    end,
                    [start[0], end[1]]
                ]
            shape_dict = {
                "type": "polygon",
                "pos": [0, 0],
                "angle": 0,
                "polygons": [points],
                "width": d.GetWidth() * 1e-6,
                "filled": 0
            }
            if hasattr(d, "IsFilled") and d.IsFilled():
                shape_dict["filled"] = 1
            return shape_dict

        if shape == "circle":
            shape_dict = {
                "type": shape,
                "start": start,
                "radius": d.GetRadius() * 1e-6,
                "width": d.GetWidth() * 1e-6
            }
            if hasattr(d, "IsFilled") and d.IsFilled():
                shape_dict["filled"] = 1
            return shape_dict

        if shape == "arc":
            a1, a2 = self.get_arc_angles(d)
            if hasattr(d, "GetCenter"):
                start = self.normalize(d.GetCenter())
            return {
                "type": shape,
                "start": start,
                "radius": d.GetRadius() * 1e-6,
                "startangle": a1,
                "endangle": a2,
                "width": d.GetWidth() * 1e-6
            }

        if shape == "polygon":
            if hasattr(d, "GetPolyShape"):
                polygons = self.parse_poly_set(d.GetPolyShape())
            else:
                self.logger.info(
                    "Polygons not supported for KiCad 4, skipping")
                return None
            angle = 0
            if hasattr(d, 'GetParentModule'):
                parent_footprint = d.GetParentModule()
            else:
                parent_footprint = d.GetParentFootprint()
            if parent_footprint is not None and KICAD_VERSION[0] < 8:
                angle = self.normalize_angle(parent_footprint.GetOrientation())
            shape_dict = {
                "type": shape,
                "pos": start,
                "angle": angle,
                "polygons": polygons
            }
            if hasattr(d, "IsFilled") and not d.IsFilled():
                shape_dict["filled"] = 0
                shape_dict["width"] = d.GetWidth() * 1e-6
            return shape_dict
        if shape == "curve":
            if hasattr(d, "GetBezierC1"):
                c1 = self.normalize(d.GetBezierC1())
                c2 = self.normalize(d.GetBezierC2())
            else:
                c1 = self.normalize(d.GetBezControl1())
                c2 = self.normalize(d.GetBezControl2())
            return {
                "type": shape,
                "start": start,
                "cpa": c1,
                "cpb": c2,
                "end": end,
                "width": d.GetWidth() * 1e-6
            }

    def parse_line_chain(self, shape):
        # type: (pcbnew.SHAPE_LINE_CHAIN) -> list
        result = []
        if not hasattr(shape, "PointCount"):
            self.logger.warn("No PointCount method on outline object. "
                             "Unpatched kicad version?")
            return result

        for point_index in range(shape.PointCount()):
            result.append(
                self.normalize(shape.CPoint(point_index)))

        return result

    def parse_poly_set(self, poly):
        # type: (pcbnew.SHAPE_POLY_SET) -> list
        result = []

        for i in range(poly.OutlineCount()):
            result.append(self.parse_line_chain(poly.Outline(i)))

        return result

    def parse_text(self, d):
        # type: (pcbnew.PCB_TEXT) -> dict
        if not d.IsVisible() and d.GetClass() not in ["PTEXT", "PCB_TEXT"]:
            return None
        pos = self.normalize(d.GetPosition())
        if hasattr(d, "GetTextThickness"):
            thickness = d.GetTextThickness() * 1e-6
        else:
            thickness = d.GetThickness() * 1e-6
        if hasattr(d, 'TransformToSegmentList'):
            segments = [self.normalize(p) for p in d.TransformToSegmentList()]
            lines = []
            for i in range(0, len(segments), 2):
                if i == 0 or segments[i - 1] != segments[i]:
                    lines.append([segments[i]])
                lines[-1].append(segments[i + 1])
            return {
                "thickness": thickness,
                "svgpath": create_path(lines)
            }
        elif hasattr(d, 'GetEffectiveTextShape'):
            shape = d.GetEffectiveTextShape(False)  # type: pcbnew.SHAPE_COMPOUND
            segments = []
            polygons = []
            for s in shape.GetSubshapes():
                if s.Type() == pcbnew.SH_LINE_CHAIN:
                    polygons.append(self.parse_line_chain(s))
                elif s.Type() == pcbnew.SH_SEGMENT:
                    seg = s.GetSeg()
                    segments.append(
                        [self.normalize(seg.A), self.normalize(seg.B)])
                else:
                    self.logger.warn(
                        "Unsupported subshape in text: %s" % s.Type())
            if segments:
                return {
                    "thickness": thickness,
                    "svgpath": create_path(segments)
                }
            else:
                return {
                    "polygons": polygons
                }

        if d.GetClass() == "MTEXT":
            angle = self.normalize_angle(d.GetDrawRotation())
        else:
            if hasattr(d, "GetTextAngle"):
                angle = self.normalize_angle(d.GetTextAngle())
            else:
                angle = self.normalize_angle(d.GetOrientation())
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
        self.font_parser.parse_font_for_string(text)
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
            "justify": [d.GetHorizJustify(), d.GetVertJustify()],
            "thickness": thickness,
            "attr": attributes,
            "angle": angle
        }

    def parse_dimension(self, d):
        # type: (pcbnew.PCB_DIMENSION_BASE) -> dict
        segments = []
        circles = []
        for s in d.GetShapes():
            s = s.Cast()
            if s.Type() == pcbnew.SH_SEGMENT:
                seg = s.GetSeg()
                segments.append(
                    [self.normalize(seg.A), self.normalize(seg.B)])
            elif s.Type() == pcbnew.SH_CIRCLE:
                circles.append(
                    [self.normalize(s.GetCenter()), s.GetRadius() * 1e-6])
            else:
                self.logger.info(
                    "Unsupported shape type in dimension object: %s", s.Type())

        svgpath = create_path(segments, circles=circles)

        return {
            "thickness": d.GetLineThickness() * 1e-6,
            "svgpath": svgpath
        }

    def parse_drawing(self, d):
        # type: (pcbnew.BOARD_ITEM) -> list
        result = []
        s = None
        if d.GetClass() in ["DRAWSEGMENT", "MGRAPHIC", "PCB_SHAPE"]:
            s = self.parse_shape(d)
        elif d.GetClass() in ["PTEXT", "MTEXT", "FP_TEXT", "PCB_TEXT", "PCB_FIELD"]:
            s = self.parse_text(d)
        elif (d.GetClass().startswith("PCB_DIM")
              and hasattr(pcbnew, "VECTOR_SHAPEPTR")):
            result.append(self.parse_dimension(d))
            if hasattr(d, "Text"):
                s = self.parse_text(d.Text())
            else:
                s = self.parse_text(d)
        else:
            self.logger.info("Unsupported drawing class %s, skipping",
                             d.GetClass())
        if s:
            result.append(s)
        return result

    def parse_edges(self, pcb):
        edges = []
        drawings = list(pcb.GetDrawings())
        bbox = None
        for f in self.footprints:
            for g in f.GraphicalItems():
                drawings.append(g)
        for d in drawings:
            if d.GetLayer() == pcbnew.Edge_Cuts:
                for parsed_drawing in self.parse_drawing(d):
                    edges.append(parsed_drawing)
                    if bbox is None:
                        bbox = d.GetBoundingBox()
                    else:
                        bbox.Merge(d.GetBoundingBox())
        if bbox:
            bbox.Normalize()
        return edges, bbox

    def parse_drawings_on_layers(self, drawings, f_layer, b_layer):
        front = []
        back = []

        for d in drawings:
            if d[1].GetLayer() not in [f_layer, b_layer]:
                continue
            for drawing in self.parse_drawing(d[1]):
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

    def get_all_drawings(self):
        drawings = [(d.GetClass(), d) for d in list(self.board.GetDrawings())]
        for f in self.footprints:
            drawings.append(("ref", f.Reference()))
            drawings.append(("val", f.Value()))
            for d in f.GraphicalItems():
                drawings.append((d.GetClass(), d))
            if hasattr(f, "GetFields"):
                fields = f.GetFields() # type: list[pcbnew.PCB_FIELD]
                for field in fields:
                    if field.IsReference() or field.IsValue():
                        continue
                    drawings.append((field.GetClass(), field))

        return drawings

    def parse_pad(self, pad):
        # type: (pcbnew.PAD) -> list[dict]
        custom_padstack = False
        outer_layers = [(pcbnew.F_Cu, "F"), (pcbnew.B_Cu, "B")]
        if hasattr(pad, 'Padstack'):
            padstack = pad.Padstack() # type: pcbnew.PADSTACK
            layers_set = list(padstack.LayerSet().Seq())
            custom_padstack = (
                padstack.Mode() != padstack.MODE_NORMAL or \
                    padstack.UnconnectedLayerMode() == padstack.UNCONNECTED_LAYER_MODE_REMOVE_ALL
            )
        else:
            layers_set = list(pad.GetLayerSet().Seq())
        layers = []
        for layer, letter in outer_layers:
            if layer in layers_set:
                layers.append(letter)
        if not layers:
            return []

        if custom_padstack:
            pads = []
            for layer, letter in outer_layers:
                if layer in layers_set and pad.FlashLayer(layer):
                    pad_dict = self.parse_pad_layer(pad, layer)
                    pad_dict["layers"] = [letter]
                    pads.append(pad_dict)
            return pads
        else:
            pad_dict = self.parse_pad_layer(pad, layers_set[0])
            pad_dict["layers"] = layers
            return [pad_dict]

    def parse_pad_layer(self, pad, layer):
        # type: (pcbnew.PAD, int) -> dict | None
        pos = self.normalize(pad.GetPosition())
        try:
            size = self.normalize(pad.GetSize(layer))
        except TypeError:
            size = self.normalize(pad.GetSize())
        angle = self.normalize_angle(pad.GetOrientation())
        shape_lookup = {
            pcbnew.PAD_SHAPE_RECT: "rect",
            pcbnew.PAD_SHAPE_OVAL: "oval",
            pcbnew.PAD_SHAPE_CIRCLE: "circle",
        }
        if hasattr(pcbnew, "PAD_SHAPE_TRAPEZOID"):
            shape_lookup[pcbnew.PAD_SHAPE_TRAPEZOID] = "trapezoid"
        if hasattr(pcbnew, "PAD_SHAPE_ROUNDRECT"):
            shape_lookup[pcbnew.PAD_SHAPE_ROUNDRECT] = "roundrect"
        if hasattr(pcbnew, "PAD_SHAPE_CUSTOM"):
            shape_lookup[pcbnew.PAD_SHAPE_CUSTOM] = "custom"
        if hasattr(pcbnew, "PAD_SHAPE_CHAMFERED_RECT"):
            shape_lookup[pcbnew.PAD_SHAPE_CHAMFERED_RECT] = "chamfrect"
        try:
            pad_shape = pad.GetShape(layer)
        except TypeError:
            pad_shape = pad.GetShape()
        shape = shape_lookup.get(pad_shape, "")
        if shape == "":
            self.logger.info("Unsupported pad shape %s, skipping.", pad_shape)
            return None
        pad_dict = {
            "pos": pos,
            "size": size,
            "angle": angle,
            "shape": shape
        }
        if shape == "custom":
            polygon_set = pcbnew.SHAPE_POLY_SET()
            try:
                pad.MergePrimitivesAsPolygon(layer, polygon_set)
            except TypeError:
                pad.MergePrimitivesAsPolygon(polygon_set)
            if polygon_set.HasHoles():
                self.logger.warn('Detected holes in custom pad polygons')
            pad_dict["polygons"] = self.parse_poly_set(polygon_set)
        if shape == "trapezoid":
            # treat trapezoid as custom shape
            pad_dict["shape"] = "custom"
            try:
                delta = self.normalize(pad.GetDelta(layer))
            except TypeError:
                delta = self.normalize(pad.GetDelta())
            pad_dict["polygons"] = [[
                [size[0] / 2 + delta[1] / 2, size[1] / 2 - delta[0] / 2],
                [-size[0] / 2 - delta[1] / 2, size[1] / 2 + delta[0] / 2],
                [-size[0] / 2 + delta[1] / 2, -size[1] / 2 - delta[0] / 2],
                [size[0] / 2 - delta[1] / 2, -size[1] / 2 + delta[0] / 2],
            ]]

        if shape in ["roundrect", "chamfrect"]:
            try:
                pad_dict["radius"] = pad.GetRoundRectCornerRadius(layer) * 1e-6
            except TypeError:
                pad_dict["radius"] = pad.GetRoundRectCornerRadius() * 1e-6
        if shape == "chamfrect":
            try:
                pad_dict["chamfpos"] = pad.GetChamferPositions(layer)
                pad_dict["chamfratio"] = pad.GetChamferRectRatio(layer)
            except TypeError:
                pad_dict["chamfpos"] = pad.GetChamferPositions()
                pad_dict["chamfratio"] = pad.GetChamferRectRatio()
        if hasattr(pcbnew, 'PAD_ATTRIB_PTH'):
            through_hole_attributes = [pcbnew.PAD_ATTRIB_PTH,
                                       pcbnew.PAD_ATTRIB_NPTH]
        else:
            through_hole_attributes = [pcbnew.PAD_ATTRIB_STANDARD,
                                       pcbnew.PAD_ATTRIB_HOLE_NOT_PLATED]
        if pad.GetAttribute() in through_hole_attributes:
            pad_dict["type"] = "th"
            pad_dict["drillshape"] = {
                pcbnew.PAD_DRILL_SHAPE_CIRCLE: "circle",
                pcbnew.PAD_DRILL_SHAPE_OBLONG: "oblong"
            }.get(pad.GetDrillShape())
            pad_dict["drillsize"] = self.normalize(pad.GetDrillSize())
        else:
            pad_dict["type"] = "smd"
        if hasattr(pad, "GetOffset"):
            try:
                pad_dict["offset"] = self.normalize(pad.GetOffset(layer))
            except TypeError:
                pad_dict["offset"] = self.normalize(pad.GetOffset())
        if self.config.include_nets:
            pad_dict["net"] = pad.GetNetname()

        return pad_dict

    def parse_footprints(self):
        # type: () -> list
        footprints = []
        for f in self.footprints:
            ref = f.GetReference()

            # bounding box
            if hasattr(pcbnew, 'MODULE'):
                f_copy = pcbnew.MODULE(f)
            else:
                f_copy = pcbnew.FOOTPRINT(f)
            try:
                f_copy.SetOrientation(0)
            except TypeError:
                f_copy.SetOrientation(
                    pcbnew.EDA_ANGLE(0, pcbnew.TENTHS_OF_A_DEGREE_T))
            pos = f_copy.GetPosition()
            pos.x = pos.y = 0
            f_copy.SetPosition(pos)
            if hasattr(f_copy, 'GetFootprintRect'):
                footprint_rect = f_copy.GetFootprintRect()
            else:
                try:
                    footprint_rect = f_copy.GetBoundingBox(False, False)
                except TypeError:
                    footprint_rect = f_copy.GetBoundingBox(False)
            bbox = {
                "pos": self.normalize(f.GetPosition()),
                "relpos": self.normalize(footprint_rect.GetPosition()),
                "size": self.normalize(footprint_rect.GetSize()),
                "angle": self.normalize_angle(f.GetOrientation()),
            }

            # graphical drawings
            drawings = []
            for d in f.GraphicalItems():
                # we only care about copper ones, silkscreen is taken care of
                if d.GetLayer() not in [pcbnew.F_Cu, pcbnew.B_Cu]:
                    continue
                for drawing in self.parse_drawing(d):
                    drawings.append({
                        "layer": "F" if d.GetLayer() == pcbnew.F_Cu else "B",
                        "drawing": drawing,
                    })

            # footprint pads
            pads = []
            for p in f.Pads():
                for pad_dict in self.parse_pad(p):
                    pads.append((p.GetPadName(), pad_dict))

            if pads:
                # Try to guess first pin name.
                pads = sorted(pads, key=lambda el: el[0])
                pin1_pads = [p for p in pads if p[0] in
                             ['1', 'A', 'A1', 'P1', 'PAD1']]
                if pin1_pads:
                    pin1_pad_name = pin1_pads[0][0]
                else:
                    # No pads have common first pin name,
                    # pick lexicographically smallest.
                    pin1_pad_name = pads[0][0]
                for pad_name, pad_dict in pads:
                    if pad_name == pin1_pad_name:
                        pad_dict['pin1'] = 1

            pads = [p[1] for p in pads]

            # add footprint
            footprints.append({
                "ref": ref,
                "bbox": bbox,
                "pads": pads,
                "drawings": drawings,
                "layer": {
                    pcbnew.F_Cu: "F",
                    pcbnew.B_Cu: "B"
                }.get(f.GetLayer())
            })

        return footprints

    def parse_tracks(self, tracks):
        tent_vias = True
        if hasattr(self.board, "GetTentVias"):
            tent_vias = self.board.GetTentVias()
        result = {pcbnew.F_Cu: [], pcbnew.B_Cu: []}
        for track in tracks:
            if track.GetClass() in ["VIA", "PCB_VIA"]:
                track_dict = {
                    "start": self.normalize(track.GetStart()),
                    "end": self.normalize(track.GetEnd()),
                    "width": track.GetWidth() * 1e-6,
                    "net": track.GetNetname(),
                }
                if not tent_vias:
                    track_dict["drillsize"] = track.GetDrillValue() * 1e-6
                for layer in [pcbnew.F_Cu, pcbnew.B_Cu]:
                    if track.IsOnLayer(layer):
                        result[layer].append(track_dict)
            else:
                if track.GetLayer() in [pcbnew.F_Cu, pcbnew.B_Cu]:
                    if track.GetClass() in ["ARC", "PCB_ARC"]:
                        a1, a2 = self.get_arc_angles(track)
                        track_dict = {
                            "center": self.normalize(track.GetCenter()),
                            "startangle": a1,
                            "endangle": a2,
                            "radius": track.GetRadius() * 1e-6,
                            "width": track.GetWidth() * 1e-6,
                        }
                    else:
                        track_dict = {
                            "start": self.normalize(track.GetStart()),
                            "end": self.normalize(track.GetEnd()),
                            "width": track.GetWidth() * 1e-6,
                        }
                    if self.config.include_nets:
                        track_dict["net"] = track.GetNetname()
                    result[track.GetLayer()].append(track_dict)

        return {
            'F': result.get(pcbnew.F_Cu),
            'B': result.get(pcbnew.B_Cu)
        }

    def parse_zones(self, zones):
        # type: (list[pcbnew.ZONE]) -> dict
        result = {pcbnew.F_Cu: [], pcbnew.B_Cu: []}
        for zone in zones:
            if (not zone.IsFilled() or
                    hasattr(zone, 'GetIsKeepout') and zone.GetIsKeepout() or
                    hasattr(zone, 'GetIsRuleArea') and zone.GetIsRuleArea()):
                continue
            layers = [layer for layer in list(zone.GetLayerSet().Seq())
                      if layer in [pcbnew.F_Cu, pcbnew.B_Cu]]
            for layer in layers:
                try:
                    # kicad 5.1 and earlier
                    poly_set = zone.GetFilledPolysList()
                except TypeError:
                    poly_set = zone.GetFilledPolysList(layer)
                width = zone.GetMinThickness() * 1e-6
                if (hasattr(zone, 'GetFilledPolysUseThickness') and
                        not zone.GetFilledPolysUseThickness()):
                    width = 0
                zone_dict = {
                    "polygons": self.parse_poly_set(poly_set),
                    "width": width,
                }
                if self.config.include_nets:
                    zone_dict["net"] = zone.GetNetname()
                result[layer].append(zone_dict)

        return {
            'F': result.get(pcbnew.F_Cu),
            'B': result.get(pcbnew.B_Cu)
        }

    @staticmethod
    def parse_netlist(net_info):
        # type: (pcbnew.NETINFO_LIST) -> list
        nets = net_info.NetsByName().asdict().keys()
        nets = sorted([str(s) for s in nets])
        return nets

    @staticmethod
    def footprint_to_component(footprint, extra_fields):
        try:
            footprint_name = str(footprint.GetFPID().GetFootprintName())
        except AttributeError:
            footprint_name = str(footprint.GetFPID().GetLibItemName())

        attr = 'Normal'
        if hasattr(pcbnew, 'FP_EXCLUDE_FROM_BOM'):
            if footprint.GetAttributes() & pcbnew.FP_EXCLUDE_FROM_BOM:
                attr = 'Virtual'
        elif hasattr(pcbnew, 'MOD_VIRTUAL'):
            if footprint.GetAttributes() == pcbnew.MOD_VIRTUAL:
                attr = 'Virtual'
        layer = {
            pcbnew.F_Cu: 'F',
            pcbnew.B_Cu: 'B',
        }.get(footprint.GetLayer())

        return Component(footprint.GetReference(),
                         footprint.GetValue(),
                         footprint_name,
                         layer,
                         attr,
                         extra_fields)

    def parse(self):
        from ..errors import ParsingException

        # Get extra field data from netlist
        field_set = set(self.config.show_fields)
        field_set.discard("Value")
        field_set.discard("Footprint")
        need_extra_fields = (field_set or
                             self.config.board_variant_whitelist or
                             self.config.board_variant_blacklist or
                             self.config.dnp_field)

        if not self.config.extra_data_file and need_extra_fields:
            self.logger.warn('Ignoring extra fields related config parameters '
                             'since no netlist/xml file was specified.')
            need_extra_fields = False

        extra_field_data = None
        if (self.config.extra_data_file and
                os.path.isfile(self.config.extra_data_file)):
            extra_field_data = self.parse_extra_data(
                self.config.extra_data_file, self.config.normalize_field_case)

        if extra_field_data is None and need_extra_fields:
            raise ParsingException(
                'Failed parsing %s' % self.config.extra_data_file)

        title_block = self.board.GetTitleBlock()
        title = title_block.GetTitle()
        revision = title_block.GetRevision()
        company = title_block.GetCompany()
        file_date = title_block.GetDate()
        if (hasattr(self.board, "GetProject") and
                hasattr(pcbnew, "ExpandTextVars")):
            project = self.board.GetProject()
            title = pcbnew.ExpandTextVars(title, project)
            revision = pcbnew.ExpandTextVars(revision, project)
            company = pcbnew.ExpandTextVars(company, project)
            file_date = pcbnew.ExpandTextVars(file_date, project)

        if not file_date:
            file_mtime = os.path.getmtime(self.file_name)
            file_date = datetime.fromtimestamp(file_mtime).strftime(
                '%Y-%m-%d %H:%M:%S')
        pcb_file_name = os.path.basename(self.file_name)
        if not title:
            # remove .kicad_pcb extension
            title = os.path.splitext(pcb_file_name)[0]
        edges, bbox = self.parse_edges(self.board)
        if bbox is None:
            self.logger.error('Please draw pcb outline on the edges '
                              'layer on sheet or any footprint before '
                              'generating BOM.')
            return None, None
        bbox = {
            "minx": bbox.GetPosition().x * 1e-6,
            "miny": bbox.GetPosition().y * 1e-6,
            "maxx": bbox.GetRight() * 1e-6,
            "maxy": bbox.GetBottom() * 1e-6,
        }

        drawings = self.get_all_drawings()

        pcbdata = {
            "edges_bbox": bbox,
            "edges": edges,
            "drawings": {
                "silkscreen": self.parse_drawings_on_layers(
                    drawings, pcbnew.F_SilkS, pcbnew.B_SilkS),
                "fabrication": self.parse_drawings_on_layers(
                    drawings, pcbnew.F_Fab, pcbnew.B_Fab),
            },
            "footprints": self.parse_footprints(),
            "metadata": {
                "title": title,
                "revision": revision,
                "company": company,
                "date": file_date,
            },
            "bom": {},
            "font_data": self.font_parser.get_parsed_font()
        }
        if self.config.include_tracks:
            pcbdata["tracks"] = self.parse_tracks(self.board.GetTracks())
            if hasattr(self.board, "Zones"):
                pcbdata["zones"] = self.parse_zones(self.board.Zones())
            else:
                self.logger.info("Zones not supported for KiCad 4, skipping")
                pcbdata["zones"] = {'F': [], 'B': []}
        if self.config.include_nets and hasattr(self.board, "GetNetInfo"):
            pcbdata["nets"] = self.parse_netlist(self.board.GetNetInfo())

        if extra_field_data and need_extra_fields:
            extra_fields = extra_field_data.fields_by_index
            if extra_fields:
                extra_fields = extra_fields.values()

            if extra_fields is None:
                extra_fields = []
                field_map = extra_field_data.fields_by_ref
                warning_shown = False

                for f in self.footprints:
                    extra_fields.append(field_map.get(f.GetReference(), {}))
                    if f.GetReference() not in field_map:
                        # Some components are on pcb but not in schematic data.
                        # Show a warning about outdated extra data file.
                        self.logger.warn(
                            'Component %s is missing from schematic data.'
                            % f.GetReference())
                        warning_shown = True

                if warning_shown:
                    self.logger.warn('Netlist/xml file is likely out of date.')
        else:
            extra_fields = [{}] * len(self.footprints)

        components = [self.footprint_to_component(f, e)
                      for (f, e) in zip(self.footprints, extra_fields)]

        return pcbdata, components


class InteractiveHtmlBomPlugin(pcbnew.ActionPlugin, object):

    def __init__(self):
        super(InteractiveHtmlBomPlugin, self).__init__()
        self.name = "Generate Interactive HTML BOM"
        self.category = "Read PCB"
        self.pcbnew_icon_support = hasattr(self, "show_toolbar_button")
        self.show_toolbar_button = True
        icon_dir = os.path.dirname(os.path.dirname(__file__))
        self.icon_file_name = os.path.join(icon_dir, 'icon.png')
        self.description = "Generate interactive HTML page with BOM " \
                           "table and pcb drawing."

    def defaults(self):
        pass

    def Run(self):
        from ..version import version
        from ..errors import ParsingException

        logger = ibom.Logger()
        board = pcbnew.GetBoard()
        pcb_file_name = board.GetFileName()

        if not pcb_file_name:
            logger.error('Please save the board file before generating BOM.')
            return

        config = Config(version, os.path.dirname(pcb_file_name))
        parser = PcbnewParser(pcb_file_name, config, logger, board)

        try:
            ibom.run_with_dialog(parser, config, logger)
        except ParsingException as e:
            logger.error(str(e))
