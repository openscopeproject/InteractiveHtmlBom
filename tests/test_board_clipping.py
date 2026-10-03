"""Native geometry regressions; runnable with unittest or pytest inside KiCad."""
import json
from pathlib import Path
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pcbnew
from InteractiveHtmlBom.ecad import kicad


def point(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def rectangle(board, x, y, width, height):
    points = [(x, y), (x + width, y),
              (x + width, y + height), (x, y + height)]
    for i in range(4):
        edge = pcbnew.PCB_SHAPE(board)
        edge.SetShape(pcbnew.S_SEGMENT)
        edge.SetLayer(pcbnew.Edge_Cuts)
        edge.SetStart(point(*points[i]))
        edge.SetEnd(point(*points[(i + 1) % 4]))
        edge.SetWidth(pcbnew.FromMM(0.05))
        board.Add(edge)


def add_drill(board, x, y, width=2, height=2, angle=0, npth=False):
    footprint = pcbnew.FOOTPRINT(board)
    board.Add(footprint)
    pad = pcbnew.PAD(footprint)
    pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH if npth else pcbnew.PAD_ATTRIB_PTH)
    pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
    pad.SetSize(point(width + 2, height + 2))
    pad.SetPosition(point(x, y))
    pad.SetDrillSize(point(width, height))
    pad.SetDrillShape(pcbnew.PAD_DRILL_SHAPE_CIRCLE if width == height
                      else pcbnew.PAD_DRILL_SHAPE_OBLONG)
    pad.SetOrientationDegrees(angle)
    footprint.Add(pad)
    return pad


def parse_clip(board):
    parser = object.__new__(kicad.PcbnewParser)
    parser.board = board
    parser.footprints = list(board.GetFootprints())
    parser.logger = SimpleNamespace(warn=lambda message: None)
    return parser.parse_board_clip()


def contains(region, x, y):
    """Independent even-odd point test on the exported contours."""
    result = False
    for polygon in region['polygons']:
        previous = polygon[-1]
        for current in polygon:
            x1, y1 = previous
            x2, y2 = current
            if (y1 > y) != (y2 > y):
                if x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                    result = not result
            previous = current
    return result


class BoardClippingTests(unittest.TestCase):
    def setUp(self):
        self.board = pcbnew.BOARD()
        rectangle(self.board, 0, 0, 20, 10)

    def test_round_castellation_and_regular_hole(self):
        add_drill(self.board, 0, 5)
        add_drill(self.board, 5, 5)
        data = parse_clip(self.board)
        self.assertFalse(contains(data['board_clip'], 0.5, 5))
        self.assertTrue(contains(data['board_clip'], 1.5, 5))
        self.assertTrue(contains(data['board_clip'], 5, 5))
        self.assertTrue(contains(data['edge_drills'], -0.5, 5))
        self.assertFalse(contains(data['edge_drills'], 5, 5))

    def test_external_internal_and_tangent_drills_are_not_castellations(self):
        for x, y in [(-3, 3), (5, 5), (1, 8), (-1, 8)]:
            add_drill(self.board, x, y)
        self.assertNotIn('edge_drills', parse_clip(self.board))

    def test_overlapping_and_duplicate_edge_drills_are_unioned(self):
        for y in [5, 5, 5.5]:
            add_drill(self.board, 0, y)
        data = parse_clip(self.board)
        self.assertTrue(contains(data['edge_drills'], 0.2, 5.25))
        self.assertFalse(contains(data['board_clip'], 0.2, 5.25))

    def test_rotated_slot_uses_drill_not_copper_offset(self):
        pad = add_drill(self.board, 20, 5, 2, 4, 30)
        pad.SetOffset(point(3, 0))
        data = parse_clip(self.board)
        self.assertFalse(contains(data['board_clip'], 19.8, 5))
        self.assertTrue(contains(data['board_clip'], 17, 5))
        self.assertTrue(contains(data['edge_drills'], 20.2, 5))

    def test_cutout_edge_and_separate_island(self):
        rectangle(self.board, 6, 3, 4, 4)
        rectangle(self.board, 25, 0, 5, 5)
        add_drill(self.board, 6, 5)
        data = parse_clip(self.board)
        self.assertFalse(contains(data['board_clip'], 8, 5))
        self.assertFalse(contains(data['board_clip'], 5.5, 5))
        self.assertTrue(contains(data['board_clip'], 4.5, 5))
        self.assertTrue(contains(data['board_clip'], 27, 2))
        self.assertFalse(contains(data['board_clip'], 22, 2))

    def test_npth_edge_openings(self):
        add_drill(self.board, 0, 5, npth=True)
        self.assertFalse(contains(parse_clip(self.board)['board_clip'], 0.5, 5))

    def test_circle_outline(self):
        board = pcbnew.BOARD()
        edge = pcbnew.PCB_SHAPE(board)
        edge.SetShape(pcbnew.S_CIRCLE)
        edge.SetLayer(pcbnew.Edge_Cuts)
        edge.SetStart(point(10, 10))
        edge.SetEnd(point(20, 10))
        board.Add(edge)
        add_drill(board, 20, 10)
        clip = parse_clip(board)['board_clip']
        self.assertTrue(contains(clip, 10, 10))
        self.assertFalse(contains(clip, 19.5, 10))
        self.assertFalse(contains(clip, 1, 1))

    def test_outline_in_footprint(self):
        board = pcbnew.BOARD()
        footprint = pcbnew.FOOTPRINT(board)
        board.Add(footprint)
        rectangle(footprint, 0, 0, 20, 10)
        add_drill(board, 0, 5)
        clip = parse_clip(board)['board_clip']
        self.assertTrue(contains(clip, 10, 5))
        self.assertFalse(contains(clip, 0.5, 5))

    def test_optional_clipping_schema(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest("jsonschema is not installed in this KiCad runtime")
        schema_path = (Path(__file__).resolve().parents[1] /
                       'InteractiveHtmlBom/ecad/schema/genericjsonpcbdata_v1.schema')
        schema = json.loads(schema_path.read_text())
        schema['$ref'] = '#/definitions/Pcbdata'
        # Validate the optional contract independently of the metadata schema.
        schema['definitions']['Pcbdata']['required'] = []
        data = {}
        jsonschema.validate(data, schema)
        add_drill(self.board, 0, 5)
        data.update(parse_clip(self.board))
        jsonschema.validate(data, schema)
        data['board_clip']['polygons'] = 'invalid'
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(data, schema)

    def test_missing_and_open_outlines_fall_back(self):
        self.assertEqual(parse_clip(pcbnew.BOARD()), {})
        self.board.Remove(list(self.board.GetDrawings())[0])
        self.assertEqual(parse_clip(self.board), {})

    def test_unavailable_drill_binding_falls_back(self):
        parser = object.__new__(kicad.PcbnewParser)
        parser.board = self.board
        parser.footprints = [SimpleNamespace(Pads=lambda: [object()])]
        parser.logger = SimpleNamespace(warn=lambda message: None)
        self.assertEqual(parser.parse_board_clip(), {})

    def test_older_outline_signature(self):
        native = self.board
        calls = []
        # Capture the installed API before mocking the version.
        current_version = kicad.KICAD_VERSION[0]
        def get_outline(polygons):
            calls.append(True)
            if current_version >= 10:
                return native.GetBoardPolygonOutlines(polygons, False)
            return native.GetBoardPolygonOutlines(polygons)
        parser = object.__new__(kicad.PcbnewParser)
        parser.board = SimpleNamespace(GetBoardPolygonOutlines=get_outline)
        parser.footprints = []
        parser.logger = SimpleNamespace(warn=lambda message: None)
        with patch.object(kicad, 'KICAD_VERSION', [9, 0, 0]):
            self.assertIn('board_clip', parser.parse_board_clip())
        self.assertEqual(calls, [True])

    def test_older_boolean_mode_argument(self):
        calls = []
        api = SimpleNamespace(SHAPE_POLY_SET=SimpleNamespace(PM_STRICTLY_SIMPLE=17))
        with patch.object(kicad, 'pcbnew', api):
            kicad.PcbnewParser._polygon_operation(
                lambda *args: calls.append(args), 'a', 'b')
        self.assertEqual(calls, [('a', 'b', 17)])


if __name__ == '__main__':
    unittest.main()
