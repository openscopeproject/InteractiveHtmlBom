"""KiCad IPC API parser.

Talks to a running KiCad instance through the IPC API using the kipy
(kicad-python) bindings instead of the legacy SWIG pcbnew module.
Produces the same pcbdata structure as the legacy PcbnewParser so the
rest of iBOM (and the html renderer) is unaffected.

Requires KiCad 9.0.3+ with the API server enabled and kicad-python 0.7+.
"""

import math
import os
from datetime import datetime

from kipy import KiCad
from kipy.board_types import (
    ArcTrack,
    BoardArc,
    BoardBezier,
    BoardCircle,
    BoardPolygon,
    BoardRectangle,
    BoardSegment,
    BoardText,
    BoardTextBox,
    Field,
    Track,
    Via,
)
from kipy.proto.board import board_types_pb2

from .common import EcadParser, Component, ExtraFieldData
from .kicad_extra import find_latest_schematic_data, parse_schematic_data
from .svgpath import create_path

BL = board_types_pb2.BoardLayer
PAD_TYPE = board_types_pb2.PadType
PAD_STACK_TYPE = board_types_pb2.PadStackType
PAD_STACK_SHAPE = board_types_pb2.PadStackShape
DRILL_SHAPE = board_types_pb2.DrillShape
ULR = board_types_pb2.UnconnectedLayerRemoval
ZONE_TYPE = board_types_pb2.ZoneType

OUTER_COPPER_LAYERS = [(BL.BL_F_Cu, "F"), (BL.BL_B_Cu, "B")]

# Bitmask values matching pcbnew's RECT_CHAMFER_POSITIONS, which is what
# the html renderer expects in the "chamfpos" field.
CHAMFER_TOP_LEFT = 1
CHAMFER_TOP_RIGHT = 2
CHAMFER_BOTTOM_LEFT = 4
CHAMFER_BOTTOM_RIGHT = 8


class IpcApiParser(EcadParser):

    def __init__(self, file_name, config, logger, kicad=None, board=None):
        self.kicad = kicad if kicad is not None else KiCad()
        self.board = board if board is not None else self.kicad.get_board()
        if not file_name:
            project = self.board.get_project()
            file_name = os.path.join(project.path, self.board.name)
        super(IpcApiParser, self).__init__(file_name, config, logger)
        self.footprints = list(self.board.get_footprints())
        self._text_render_cache = {}

    @staticmethod
    def normalize(point):
        return [point.x * 1e-6, point.y * 1e-6]

    @staticmethod
    def rotate(point, center, angle_degrees):
        # Rotation in kicad's coordinate system (y axis down,
        # positive angle is counterclockwise).
        a = -math.radians(angle_degrees)
        dx = point[0] - center[0]
        dy = point[1] - center[1]
        return [center[0] + dx * math.cos(a) - dy * math.sin(a),
                center[1] + dx * math.sin(a) + dy * math.cos(a)]

    @staticmethod
    def layer_letter(layer):
        return {BL.BL_F_Cu: "F", BL.BL_B_Cu: "B"}.get(layer)

    def parse_poly_line(self, poly_line):
        # type: (...) -> list
        # PolyLine nodes are either points or arcs. Arcs are approximated
        # with their start/mid/end points; filled polygons coming from
        # KiCad are already flattened so this is rarely hit.
        result = []
        for node in poly_line.nodes:
            if node.has_point:
                result.append(self.normalize(node.point))
            elif node.has_arc:
                arc = node.arc
                result.append(self.normalize(arc.start))
                result.append(self.normalize(arc.mid))
                result.append(self.normalize(arc.end))
        return result

    def parse_polygons(self, polygons_with_holes):
        # Holes are not supported by the legacy data format either:
        # SWIG parser warned about them and used outlines only.
        result = []
        for poly in polygons_with_holes:
            if poly.holes:
                self.logger.warn('Detected holes in polygon, ignoring them')
            result.append(self.parse_poly_line(poly.outline))
        return result

    @staticmethod
    def arc_angles_degrees(shape):
        """Computes (startangle, endangle) the way the legacy parser did.

        Angles are in kicad's screen coordinate system (y axis down,
        angles grow clockwise on screen). kipy's start_angle()/end_angle()
        use the math convention (y up) so we compute from the arc's
        start/mid/end points directly.
        """
        center = shape.center()
        if center is None:
            return 0, 0

        def angle_to(p):
            return math.degrees(math.atan2(p.y - center.y, p.x - center.x))

        a1 = angle_to(shape.start)
        am = angle_to(shape.mid)
        a2 = angle_to(shape.end)
        if a1 >= 180 - 1e-3:
            a1 -= 360  # match pcbnew's (-180, 180] -> [-180, 180) edge
        # Determine sweep direction: the mid point must lie on the arc.
        ccw_mid = (am - a1) % 360
        ccw_end = (a2 - a1) % 360
        if ccw_mid <= ccw_end:
            sweep = ccw_end
        else:
            sweep = ccw_end - 360
        a2 = a1 + sweep
        if a2 < a1:
            a1, a2 = a2, a1
        return round(a1, 2), round(a2, 2)

    def parse_shape(self, d):
        if isinstance(d, BoardSegment):
            return {
                "type": "segment",
                "start": self.normalize(d.start),
                "end": self.normalize(d.end),
                "width": d.attributes.stroke.width * 1e-6,
            }
        if isinstance(d, BoardRectangle):
            start = self.normalize(d.top_left)
            end = self.normalize(d.bottom_right)
            return {
                "type": "polygon",
                "pos": [0, 0],
                "angle": 0,
                "polygons": [[
                    start,
                    [end[0], start[1]],
                    end,
                    [start[0], end[1]],
                ]],
                "width": d.attributes.stroke.width * 1e-6,
                "filled": 1 if d.attributes.fill.filled else 0,
            }
        if isinstance(d, BoardCircle):
            radius = (d.radius_point - d.center).length()
            shape_dict = {
                "type": "circle",
                "start": self.normalize(d.center),
                "radius": radius * 1e-6,
                "width": d.attributes.stroke.width * 1e-6,
            }
            if d.attributes.fill.filled:
                shape_dict["filled"] = 1
            return shape_dict
        if isinstance(d, BoardArc):
            a1, a2 = self.arc_angles_degrees(d)
            center = d.center()
            if center is None:
                # Degenerate arc, draw as segment.
                return {
                    "type": "segment",
                    "start": self.normalize(d.start),
                    "end": self.normalize(d.end),
                    "width": d.attributes.stroke.width * 1e-6,
                }
            return {
                "type": "arc",
                "start": self.normalize(center),
                "radius": d.radius() * 1e-6,
                "startangle": a1,
                "endangle": a2,
                "width": d.attributes.stroke.width * 1e-6,
            }
        if isinstance(d, BoardPolygon):
            shape_dict = {
                "type": "polygon",
                "pos": [0.0, 0.0],
                "angle": 0,
                "polygons": self.parse_polygons(d.polygons),
            }
            if not d.attributes.fill.filled:
                shape_dict["filled"] = 0
                shape_dict["width"] = d.attributes.stroke.width * 1e-6
            return shape_dict
        if isinstance(d, BoardBezier):
            return {
                "type": "curve",
                "start": self.normalize(d.start),
                "cpa": self.normalize(d.control1),
                "cpb": self.normalize(d.control2),
                "end": self.normalize(d.end),
                "width": d.attributes.stroke.width * 1e-6,
            }
        self.logger.info("Unsupported shape %s, skipping", type(d).__name__)
        return None

    def _resolve_text_value(self, value, footprint):
        """Expands text variables. Footprint-context variables are
        substituted locally, the rest is expanded by KiCad."""
        if '${' not in value:
            return value
        if footprint is not None:
            subs = {
                'REFERENCE': footprint.reference_field.text.value,
                'VALUE': footprint.value_field.text.value,
                'FOOTPRINT_NAME': footprint.definition.id.name,
                'FOOTPRINT_LIBRARY': footprint.definition.id.library,
            }
            for key, sub in subs.items():
                value = value.replace('${%s}' % key, sub)
        if '${' in value:
            value = self.board.expand_text_variables(value)
        return value

    def _as_common_text(self, d, footprint=None):
        from kipy.common_types import Text

        if isinstance(d, Field):
            text = d.text.as_text()
        elif isinstance(d, BoardText):
            text = d.as_text()
        elif isinstance(d, BoardTextBox):
            return d.as_textbox()
        else:
            text = d  # already a common Text (e.g. dimension text)

        modified = False

        # GetTextAsShapes renders the stored string as-is, with text
        # variables like ${REFERENCE} unexpanded. Resolve them first.
        value = self._resolve_text_value(text.value, footprint)
        if value != text.value:
            text = Text(text.proto)  # copy, do not mutate the board
            text.value = value
            modified = True

        # GetTextAsShapes renders the stored angle as-is, but pcbnew
        # draws keep-upright text rotated back into readable orientation
        # (see EDA_TEXT::GetDrawRotation). Replicate that here, otherwise
        # left/right justified text on rotated footprints renders on the
        # wrong side of its anchor.
        attrs = text.proto.attributes
        if attrs.keep_upright:
            angle = attrs.angle.value_degrees % 360
            if 90 < angle <= 270:
                if not modified:
                    text = Text(text.proto)
                text.proto.attributes.angle.value_degrees = angle - 180
        return text

    def prerender_text_items(self, items):
        """Renders all text items in one IPC round trip.

        KiCad renders text to polygonal shapes server side, which replaces
        the SWIG GetEffectiveTextShape() call. Results are cached keyed by
        the text item's python object id.

        :param items: list of (text_item, parent_footprint_or_None)
        """
        items = [(t, f) for (t, f) in items
                 if id(t) not in self._text_render_cache]
        if not items:
            return
        shapes = self.kicad.get_text_as_shapes(
            [self._as_common_text(t, f) for (t, f) in items])
        for (item, _), compound in zip(items, shapes):
            self._text_render_cache[id(item)] = compound

    def parse_text(self, d, footprint=None):
        common_text = self._as_common_text(d, footprint)
        thickness = common_text.attributes.stroke_width * 1e-6
        compound = self._text_render_cache.get(id(d))
        if compound is None:
            compound = self.kicad.get_text_as_shapes(common_text)[0]
        segments = []
        polygons = []
        from kipy.common_types import Segment, Polygon
        for s in compound.shapes:
            if isinstance(s, Segment):
                segments.append(
                    [self.normalize(s.start), self.normalize(s.end)])
            elif isinstance(s, Polygon):
                polygons.extend(self.parse_polygons(s.polygons))
            else:
                self.logger.warn(
                    "Unsupported subshape in text: %s" % type(s).__name__)
        if segments:
            return {
                "thickness": thickness,
                "svgpath": create_path(segments)
            }
        else:
            return {
                "polygons": polygons
            }

    def parse_drawing(self, d, footprint=None):
        if isinstance(d, (BoardSegment, BoardRectangle, BoardCircle,
                          BoardArc, BoardPolygon, BoardBezier)):
            s = self.parse_shape(d)
            return [s] if s else []
        if isinstance(d, (BoardText, BoardTextBox, Field)):
            s = self.parse_text(d, footprint)
            return [s] if s else []
        self.logger.info("Unsupported drawing type %s, skipping",
                         type(d).__name__)
        return []

    def _field_visible(self, field):
        # Note: BoardText.attributes.visible is deprecated and always
        # True over the IPC API; Field.visible is the reliable flag.
        return field.visible

    def get_all_drawings(self):
        """Returns a list of (kind, item, parent_footprint) tuples for all
        silk/fab drawings.

        kind is "ref"/"val" for reference and value fields so they can be
        tagged in the output, mirroring the SWIG parser.
        """
        drawings = []
        for d in self.board.get_shapes():
            drawings.append(("shape", d, None))
        for t in self.board.get_text():
            if isinstance(t, BoardText) and not t.attributes.visible:
                continue
            drawings.append(("text", t, None))
        for f in self.footprints:
            if self._field_visible(f.reference_field):
                drawings.append(("ref", f.reference_field, f))
            if self._field_visible(f.value_field):
                drawings.append(("val", f.value_field, f))
            for d in f.definition.shapes:
                drawings.append(("shape", d, f))
            ref_val_ids = (f.reference_field.field_id,
                           f.value_field.field_id)
            for t in f.texts_and_fields:
                if isinstance(t, Field):
                    if t.field_id in ref_val_ids:
                        continue
                    if not self._field_visible(t):
                        continue
                elif isinstance(t, BoardText):
                    if not t.attributes.visible:
                        continue
                drawings.append(("text", t, f))
        return drawings

    def parse_drawings_on_layers(self, drawings, f_layer, b_layer):
        front = []
        back = []

        text_items = [(d, f) for (kind, d, f) in drawings
                      if d.layer in [f_layer, b_layer] and
                      not isinstance(d, (BoardSegment, BoardRectangle,
                                         BoardCircle, BoardArc,
                                         BoardPolygon, BoardBezier))]
        self.prerender_text_items(text_items)

        for kind, d, f in drawings:
            if d.layer not in [f_layer, b_layer]:
                continue
            for drawing in self.parse_drawing(d, f):
                if kind in ["ref", "val"]:
                    drawing[kind] = 1
                if d.layer == f_layer:
                    front.append(drawing)
                else:
                    back.append(drawing)

        return {
            "F": front,
            "B": back,
        }

    def _shape_points_with_extents(self, d):
        """Returns points describing the extents of a shape, used for
        bounding box computation on the client side."""
        width = d.attributes.stroke.width
        points = []
        if isinstance(d, BoardSegment):
            points = [d.start, d.end]
        elif isinstance(d, BoardRectangle):
            points = [d.top_left, d.bottom_right]
        elif isinstance(d, (BoardCircle, BoardArc, BoardPolygon,
                            BoardBezier)):
            try:
                box = d.bounding_box()
            except Exception:
                return []
            points = [box.pos,
                      type(box.pos).from_xy(box.pos.x + box.size.x,
                                            box.pos.y + box.size.y)]
        result = []
        for p in points:
            x, y = p.x, p.y
            result.append([(x - width / 2) * 1e-6, (y - width / 2) * 1e-6])
            result.append([(x + width / 2) * 1e-6, (y + width / 2) * 1e-6])
        return result

    def parse_edges(self):
        edges = []
        bbox = None  # [minx, miny, maxx, maxy] in mm

        items = list(self.board.get_shapes())
        for f in self.footprints:
            items.extend(f.definition.shapes)

        for d in items:
            if d.layer != BL.BL_Edge_Cuts:
                continue
            for parsed_drawing in self.parse_drawing(d):
                edges.append(parsed_drawing)
            for p in self._shape_points_with_extents(d):
                if bbox is None:
                    bbox = [p[0], p[1], p[0], p[1]]
                else:
                    bbox = [min(bbox[0], p[0]), min(bbox[1], p[1]),
                            max(bbox[2], p[0]), max(bbox[3], p[1])]
        return edges, bbox

    def _pad_is_through_hole(self, pad):
        return pad.pad_type in [PAD_TYPE.PT_PTH, PAD_TYPE.PT_NPTH]

    def parse_pad(self, pad):
        padstack = pad.padstack
        layers_set = list(padstack.layers)
        layers = []
        for layer, letter in OUTER_COPPER_LAYERS:
            if layer in layers_set:
                layers.append(letter)
        if not layers and not self._pad_is_through_hole(pad):
            return []

        custom_padstack = (
            padstack.type != PAD_STACK_TYPE.PST_NORMAL or
            padstack.unconnected_layer_removal != ULR.ULR_KEEP
        )

        if custom_padstack:
            presence = self.board.check_padstack_presence_on_layers(
                pad, [layer for layer, _ in OUTER_COPPER_LAYERS])
            presence = presence.get(pad, {})
            pads = []
            for layer, letter in OUTER_COPPER_LAYERS:
                if layer in layers_set and presence.get(layer, True):
                    pad_dict = self.parse_pad_layer(pad, layer)
                    if pad_dict is not None:
                        pad_dict["layers"] = [letter]
                        pads.append(pad_dict)
            return pads
        else:
            pad_layer = layers_set[0] if layers_set else BL.BL_F_Cu
            pad_dict = self.parse_pad_layer(pad, pad_layer)
            if pad_dict is None:
                return []
            pad_dict["layers"] = layers
            return [pad_dict]

    def parse_pad_layer(self, pad, layer):
        padstack = pad.padstack
        psl = padstack.copper_layer(layer)
        if psl is None:
            cls = padstack.copper_layers
            psl = cls[0] if cls else None
        if psl is None:
            self.logger.info("Pad %s has no copper layers, skipping.",
                             pad.number)
            return None
        pos = self.normalize(pad.position)
        size = self.normalize(psl.size)
        angle = padstack.angle.degrees
        shape = {
            PAD_STACK_SHAPE.PSS_CIRCLE: "circle",
            PAD_STACK_SHAPE.PSS_RECTANGLE: "rect",
            PAD_STACK_SHAPE.PSS_OVAL: "oval",
            PAD_STACK_SHAPE.PSS_TRAPEZOID: "trapezoid",
            PAD_STACK_SHAPE.PSS_ROUNDRECT: "roundrect",
            PAD_STACK_SHAPE.PSS_CHAMFEREDRECT: "chamfrect",
            PAD_STACK_SHAPE.PSS_CUSTOM: "custom",
        }.get(psl.shape, "")
        if shape == "":
            self.logger.info("Unsupported pad shape %s, skipping.", psl.shape)
            return None
        pad_dict = {
            "pos": pos,
            "size": size,
            "angle": angle,
            "shape": shape
        }
        if shape == "custom":
            polygon = self.board.get_pad_shapes_as_polygons(pad, layer)
            if polygon is None:
                self.logger.info(
                    "Failed to get polygon for custom pad %s", pad.number)
                return None
            # Polygon comes in absolute board coordinates, convert it to
            # pad-relative coordinates that the renderer expects.
            points = self.parse_poly_line(polygon.outline)
            if polygon.holes:
                self.logger.warn('Detected holes in custom pad polygons')
            points = [self.rotate(p, pos, -angle) for p in points]
            points = [[p[0] - pos[0], p[1] - pos[1]] for p in points]
            pad_dict["polygons"] = [points]
        if shape == "trapezoid":
            # treat trapezoid as custom shape
            pad_dict["shape"] = "custom"
            delta = self.normalize(psl.trapezoid_delta)
            size = pad_dict["size"]
            pad_dict["polygons"] = [[
                [size[0] / 2 + delta[1] / 2, size[1] / 2 - delta[0] / 2],
                [-size[0] / 2 - delta[1] / 2, size[1] / 2 + delta[0] / 2],
                [-size[0] / 2 + delta[1] / 2, -size[1] / 2 - delta[0] / 2],
                [size[0] / 2 - delta[1] / 2, -size[1] / 2 + delta[0] / 2],
            ]]

        if shape in ["roundrect", "chamfrect"]:
            pad_dict["radius"] = (psl.corner_rounding_ratio *
                                  min(psl.size.x, psl.size.y) * 1e-6)
        if shape == "chamfrect":
            corners = psl.chamfered_corners
            chamfpos = 0
            if corners.top_left:
                chamfpos |= CHAMFER_TOP_LEFT
            if corners.top_right:
                chamfpos |= CHAMFER_TOP_RIGHT
            if corners.bottom_left:
                chamfpos |= CHAMFER_BOTTOM_LEFT
            if corners.bottom_right:
                chamfpos |= CHAMFER_BOTTOM_RIGHT
            pad_dict["chamfpos"] = chamfpos
            pad_dict["chamfratio"] = psl.chamfer_ratio

        if self._pad_is_through_hole(pad):
            drill = padstack.drill
            pad_dict["type"] = "th"
            pad_dict["drillshape"] = {
                DRILL_SHAPE.DS_CIRCLE: "circle",
                DRILL_SHAPE.DS_OBLONG: "oblong",
            }.get(drill.shape, "circle")
            pad_dict["drillsize"] = self.normalize(drill.diameter)
        else:
            pad_dict["type"] = "smd"

        pad_dict["offset"] = self.normalize(psl.offset)
        if self.config.include_nets:
            pad_dict["net"] = pad.net.name

        return pad_dict

    def _footprint_bbox(self, f):
        """Computes the footprint bounding box at orientation 0, relative
        to the footprint position, like the SWIG parser did by copying the
        footprint and resetting its orientation.
        """
        pos = self.normalize(f.position)
        angle = f.orientation.degrees
        points = []

        for d in f.definition.shapes:
            if d.layer == BL.BL_Edge_Cuts:
                continue
            points.extend(self._shape_points_with_extents(d))

        for pad in f.definition.pads:
            pad_pos = self.normalize(pad.position)
            psl_list = pad.padstack.copper_layers
            half_w = half_h = 0
            for psl in psl_list:
                half_w = max(half_w, psl.size.x * 1e-6 / 2)
                half_h = max(half_h, psl.size.y * 1e-6 / 2)
            drill = pad.padstack.drill
            half_w = max(half_w, drill.diameter.x * 1e-6 / 2)
            half_h = max(half_h, drill.diameter.y * 1e-6 / 2)
            pad_angle = pad.padstack.angle.degrees
            for sx in (-1, 1):
                for sy in (-1, 1):
                    corner = [pad_pos[0] + sx * half_w,
                              pad_pos[1] + sy * half_h]
                    points.append(self.rotate(corner, pad_pos, pad_angle))

        if not points:
            points = [pos]

        # Transform from board coordinates to footprint-local unrotated
        # coordinates.
        local = [self.rotate(p, pos, -angle) for p in points]
        minx = min(p[0] for p in local)
        miny = min(p[1] for p in local)
        maxx = max(p[0] for p in local)
        maxy = max(p[1] for p in local)

        return {
            "pos": pos,
            "relpos": [minx - pos[0], miny - pos[1]],
            "size": [maxx - minx, maxy - miny],
            "angle": angle,
        }

    def parse_footprints(self):
        footprints = []
        for f in self.footprints:
            ref = f.reference_field.text.value

            # graphical drawings on copper layers
            drawings = []
            for d in f.definition.shapes:
                if d.layer not in [BL.BL_F_Cu, BL.BL_B_Cu]:
                    continue
                for drawing in self.parse_drawing(d):
                    drawings.append({
                        "layer": "F" if d.layer == BL.BL_F_Cu else "B",
                        "drawing": drawing,
                    })

            # footprint pads
            pads = []
            for p in f.definition.pads:
                for pad_dict in self.parse_pad(p):
                    pads.append((p.number, pad_dict))

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

            footprints.append({
                "ref": ref,
                "bbox": self._footprint_bbox(f),
                "pads": pads,
                "drawings": drawings,
                "layer": self.layer_letter(f.layer),
            })

        return footprints

    def parse_tracks(self, tracks_and_vias):
        result = {BL.BL_F_Cu: [], BL.BL_B_Cu: []}
        for track in tracks_and_vias:
            if isinstance(track, Via):
                track_dict = {
                    "start": self.normalize(track.position),
                    "end": self.normalize(track.position),
                    "width": track.diameter * 1e-6,
                    "net": track.net.name,
                }
                for layer, _ in OUTER_COPPER_LAYERS:
                    if layer in track.padstack.layers:
                        result[layer].append(track_dict)
            else:
                if track.layer in [BL.BL_F_Cu, BL.BL_B_Cu]:
                    if isinstance(track, ArcTrack):
                        a1, a2 = self.arc_angles_degrees(track)
                        center = track.center()
                        if center is None:
                            continue
                        track_dict = {
                            "center": self.normalize(center),
                            "startangle": a1,
                            "endangle": a2,
                            "radius": track.radius() * 1e-6,
                            "width": track.width * 1e-6,
                        }
                    else:
                        track_dict = {
                            "start": self.normalize(track.start),
                            "end": self.normalize(track.end),
                            "width": track.width * 1e-6,
                        }
                    if self.config.include_nets:
                        track_dict["net"] = track.net.name
                    result[track.layer].append(track_dict)

        return {
            'F': result[BL.BL_F_Cu],
            'B': result[BL.BL_B_Cu],
        }

    def parse_zones(self, zones):
        result = {BL.BL_F_Cu: [], BL.BL_B_Cu: []}
        for zone in zones:
            if not zone.filled or zone.is_rule_area():
                continue
            filled = zone.filled_polygons
            for layer, polys in filled.items():
                if layer not in result:
                    continue
                zone_dict = {
                    "polygons": self.parse_polygons(polys),
                    "width": 0,
                }
                if self.config.include_nets:
                    net = getattr(zone, 'net', None)
                    zone_dict["net"] = net.name if net is not None else ""
                result[layer].append(zone_dict)

        return {
            'F': result[BL.BL_F_Cu],
            'B': result[BL.BL_B_Cu],
        }

    def parse_netlist(self):
        nets = [n.name for n in self.board.get_nets()]
        return sorted(nets)

    def get_footprint_fields(self, f):
        props = {}
        for t in f.texts_and_fields:
            if isinstance(t, Field):
                value = t.text.value
                props[t.name] = value
        # Reference/value/etc are Fields too, keep parity with
        # GetFieldsShownText which includes them.
        expanded = self.board.expand_text_variables(list(props.values()))
        props = dict(zip(props.keys(), expanded))
        if "dnp" in props and props["dnp"] == "":
            del props["dnp"]
            props["kicad_dnp"] = "DNP"
        if f.attributes.do_not_populate:
            props["kicad_dnp"] = "DNP"
        return props

    def parse_extra_data_from_pcb(self):
        field_set = set()
        by_ref = {}
        by_index = {}

        for (i, f) in enumerate(self.footprints):
            props = self.get_footprint_fields(f)
            by_index[i] = props
            ref = f.reference_field.text.value
            ref_fields = by_ref.setdefault(ref, {})

            for k, v in props.items():
                field_set.add(k)
                ref_fields[k] = v

        return ExtraFieldData(list(field_set), by_ref, by_index)

    def get_extra_field_data(self, file_name):
        if os.path.abspath(file_name) == os.path.abspath(self.file_name):
            return self.parse_extra_data_from_pcb()
        if os.path.splitext(file_name)[1] == '.kicad_pcb':
            return None

        data = parse_schematic_data(file_name)

        return ExtraFieldData(data[0], data[1])

    def latest_extra_data(self, extra_dirs=None):
        base_name = os.path.splitext(os.path.basename(self.file_name))[0]
        file_dir_name = os.path.dirname(self.file_name)
        directories = [file_dir_name]
        for dir in (extra_dirs or []):
            if not os.path.isabs(dir):
                dir = os.path.join(file_dir_name, dir)
            if os.path.exists(dir):
                directories.append(dir)
        return find_latest_schematic_data(base_name, directories)

    def extra_data_file_filter(self):
        return ("Netlist, xml and pcb files (*.net; *.xml; *.kicad_pcb)|"
                "*.net;*.xml;*.kicad_pcb")

    def footprint_to_component(self, footprint, extra_fields):
        footprint_name = str(footprint.definition.id.name)

        attr = 'Normal'
        if footprint.attributes.exclude_from_bill_of_materials:
            attr = 'Virtual'

        return Component(footprint.reference_field.text.value,
                         footprint.value_field.text.value,
                         footprint_name,
                         self.layer_letter(footprint.layer),
                         attr,
                         extra_fields)

    def parse(self):
        from ..errors import ParsingException

        # Get extra field data
        field_set = set(self.config.show_fields)
        field_set.discard("Value")
        field_set.discard("Footprint")
        need_extra_fields = (field_set or
                             self.config.board_variant_whitelist or
                             self.config.board_variant_blacklist or
                             self.config.dnp_field)

        if not self.config.extra_data_file and need_extra_fields:
            self.config.extra_data_file = self.file_name
            self.logger.warn('Assuming extra data file to be the pcb file '
                             'since --extra-data-file was not specified.')

        extra_field_data = None
        if (self.config.extra_data_file and
                os.path.isfile(self.config.extra_data_file)):
            extra_field_data = self.parse_extra_data(
                self.config.extra_data_file, self.config.normalize_field_case)

        if extra_field_data is None and need_extra_fields:
            raise ParsingException(
                'Failed parsing %s' % self.config.extra_data_file)

        title_block = self.board.get_title_block_info()
        texts = self.board.expand_text_variables([
            title_block.title,
            title_block.revision,
            title_block.company,
            title_block.date,
        ])
        title, revision, company, file_date = texts

        if not file_date:
            file_mtime = os.path.getmtime(self.file_name)
            file_date = datetime.fromtimestamp(file_mtime).strftime(
                '%Y-%m-%d %H:%M:%S')
        pcb_file_name = os.path.basename(self.file_name)
        if not title:
            # remove .kicad_pcb extension
            title = os.path.splitext(pcb_file_name)[0]

        edges, bbox = self.parse_edges()
        if bbox is None:
            self.logger.error('Please draw pcb outline on the edges '
                              'layer on sheet or any footprint before '
                              'generating BOM.')
            return None, None
        bbox = {
            "minx": bbox[0],
            "miny": bbox[1],
            "maxx": bbox[2],
            "maxy": bbox[3],
        }

        drawings = self.get_all_drawings()

        pcbdata = {
            "edges_bbox": bbox,
            "edges": edges,
            "drawings": {
                "silkscreen": self.parse_drawings_on_layers(
                    drawings, BL.BL_F_SilkS, BL.BL_B_SilkS),
                "fabrication": self.parse_drawings_on_layers(
                    drawings, BL.BL_F_Fab, BL.BL_B_Fab),
            },
            "footprints": self.parse_footprints(),
            "metadata": {
                "title": title,
                "revision": revision,
                "company": company,
                "date": file_date,
                "variant": getattr(self.config, 'kicad_variant', ''),
            },
            "bom": {},
            "font_data": {}
        }
        if self.config.include_tracks:
            tracks_and_vias = (list(self.board.get_tracks()) +
                               list(self.board.get_vias()))
            pcbdata["tracks"] = self.parse_tracks(tracks_and_vias)
            pcbdata["zones"] = self.parse_zones(self.board.get_zones())
        if self.config.include_nets:
            pcbdata["nets"] = self.parse_netlist()

        if extra_field_data and need_extra_fields:
            extra_fields = extra_field_data.fields_by_index
            if extra_fields:
                extra_fields = extra_fields.values()

            if extra_fields is None:
                extra_fields = []
                field_map = extra_field_data.fields_by_ref
                warning_shown = False

                for f in self.footprints:
                    ref = f.reference_field.text.value
                    extra_fields.append(field_map.get(ref, {}))
                    if ref not in field_map:
                        # Some components are on pcb but not in schematic
                        # data. Show a warning about outdated extra data
                        # file.
                        self.logger.warn(
                            'Component %s is missing from schematic data.'
                            % ref)
                        warning_shown = True

                if warning_shown:
                    self.logger.warn('Netlist/xml file is likely out of date.')
        else:
            extra_fields = [{}] * len(self.footprints)

        components = [self.footprint_to_component(f, e)
                      for (f, e) in zip(self.footprints, extra_fields)]

        return pcbdata, components
