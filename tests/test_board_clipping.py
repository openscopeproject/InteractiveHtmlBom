"""Native geometry regressions; runnable with unittest or pytest inside KiCad."""
import json
import os
import re
import subprocess
import sys
import tempfile
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
        # KiCad 7 distinguishes footprint graphics from board graphics.
        shape = (pcbnew.FP_SHAPE if isinstance(board, pcbnew.FOOTPRINT)
                 and hasattr(pcbnew, "FP_SHAPE") else pcbnew.PCB_SHAPE)
        edge = shape(board)
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
    if hasattr(pad, "SetPos0"):
        # Older versions serialize this separate footprint-local position.
        pad.SetPos0(point(x, y))
    pad.SetDrillSize(point(width, height))
    pad.SetDrillShape(pcbnew.PAD_DRILL_SHAPE_CIRCLE if width == height
                      else pcbnew.PAD_DRILL_SHAPE_OBLONG)
    pad.SetOrientationDegrees(angle)
    footprint.Add(pad)
    return pad


def bezier(board, start, c1, c2, end):
    edge = pcbnew.PCB_SHAPE(board)
    edge.SetShape(pcbnew.S_CURVE)
    edge.SetLayer(pcbnew.Edge_Cuts)
    edge.SetStart(point(*start))
    edge.SetEnd(point(*end))
    edge.SetBezierC1(point(*c1))
    edge.SetBezierC2(point(*c2))
    edge.SetWidth(pcbnew.FromMM(0.05))
    board.Add(edge)
    return edge


def curved_board():
    board = pcbnew.BOARD()
    rectangle(board, 0, 0, 20, 10)
    top = next(edge for edge in board.GetDrawings()
               if edge.GetStart().y == 0 and edge.GetEnd().y == 0)
    board.Remove(top)
    # At t=0.5 this curve passes through (10, -3).
    bezier(board, (0, 0), (0, -4), (20, -4), (20, 0))
    # A closed curved cutout, spanning x=7..13 and y=3..6.
    bezier(board, (7, 4.5), (7, 2.5), (13, 2.5), (13, 4.5))
    bezier(board, (13, 4.5), (13, 6.5), (7, 6.5), (7, 4.5))
    add_drill(board, 10, -3, 0.3, 0.3)
    return board


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
        self.assertEqual(set(data), {'board_clip'})
        self.assertFalse(contains(data['board_clip'], -0.5, 5))

    def test_external_internal_and_tangent_drills_are_not_castellations(self):
        original = parse_clip(self.board)
        for x, y in [(-3, 3), (5, 5), (1, 8), (-1, 8)]:
            add_drill(self.board, x, y)
        # Non-crossing drills must not change the physical perimeter.
        self.assertEqual(parse_clip(self.board), original)

    def test_overlapping_and_duplicate_edge_drills_are_unioned(self):
        for y in [5, 5, 5.5]:
            add_drill(self.board, 0, y)
        data = parse_clip(self.board)
        self.assertFalse(contains(data['board_clip'], 0.2, 5.25))

    def test_rotated_slot_uses_drill_not_copper_offset(self):
        pad = add_drill(self.board, 20, 5, 2, 4, 30)
        pad.SetOffset(point(3, 0))
        data = parse_clip(self.board)
        self.assertFalse(contains(data['board_clip'], 19.8, 5))
        self.assertTrue(contains(data['board_clip'], 17, 5))
        self.assertFalse(contains(data['board_clip'], 20.2, 5))

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

    def test_bezier_outline_cutout_and_crossing_drill(self):
        clip = parse_clip(curved_board())
        self.assertEqual(set(clip), {'board_clip'})
        self.assertTrue(contains(clip['board_clip'], 10, 0))
        self.assertFalse(contains(clip['board_clip'], 10, -3.05))
        self.assertFalse(contains(clip['board_clip'], 10, -2.95))
        self.assertTrue(contains(clip['board_clip'], 10, -2.7))
        self.assertFalse(contains(clip['board_clip'], 10, 4.5))
        self.assertTrue(contains(clip['board_clip'], 10, 7))

    def test_open_bezier_outline_falls_back(self):
        board = curved_board()
        edge = next(edge for edge in board.GetDrawings()
                    if edge.GetShape() == pcbnew.S_CURVE and
                    edge.GetStart().y == 0)
        board.Remove(edge)
        self.assertEqual(parse_clip(board), {})

    def test_cli_generation_with_beziers_and_fallback(self):
        generator = (Path(__file__).resolve().parents[1] /
                     'InteractiveHtmlBom/generate_interactive_bom.py')
        board = curved_board()
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            board_file = directory / 'curved.kicad_pcb'
            pcbnew.SaveBoard(str(board_file), board)
            original = board_file.read_bytes()
            env = dict(os.environ, INTERACTIVE_HTML_BOM_CLI_MODE='1',
                       INTERACTIVE_HTML_BOM_NO_DISPLAY='1',
                       PYTHONDONTWRITEBYTECODE='1')
            for case in ['bezier', 'missing_api', 'open_outline']:
                with self.subTest(case=case):
                    if case == 'open_outline':
                        edge = next(edge for edge in board.GetDrawings()
                                    if edge.GetShape() == pcbnew.S_CURVE and
                                    edge.GetStart().y == 0)
                        board.Remove(edge)
                        pcbnew.SaveBoard(str(board_file), board)
                        original = board_file.read_bytes()
                    args = [str(generator), str(board_file), '--no-browser',
                            '--no-compression', '--dest-dir', str(directory),
                            '--name-format', case]
                    command = [sys.executable, '-B']
                    if case == 'missing_api':
                        command += ['-c',
                            'import pcbnew,runpy,sys; '
                            'pcbnew.BOARD.GetBoardPolygonOutlines=None; '
                            'sys.argv=sys.argv[1:]; '
                            'runpy.run_path(sys.argv[0],run_name="__main__")']
                    result = subprocess.run(command + args, env=env,
                                            capture_output=True, text=True,
                                            timeout=90)
                    self.assertEqual(result.returncode, 0,
                                     result.stdout + result.stderr)
                    html = (directory / (case + '.html')).read_text(encoding='utf-8')
                    match = re.search(r'^var pcbdata = (.+)$', html, re.M)
                    self.assertIsNotNone(match)
                    data = json.loads(match.group(1))
                    self.assertNotIn('edge_drills', data)
                    self.assertTrue(data['edges'])
                    self.assertTrue(data['footprints'])
                    self.assertEqual(board_file.read_bytes(), original)
                    if case == 'bezier':
                        self.assertTrue(any(edge['type'] == 'curve'
                                            for edge in data['edges']))
                        self.assertIn('board_clip', data)
                        self.assertFalse(contains(data['board_clip'], 10, 4.5))
                        self.assertFalse(contains(data['board_clip'], 10, -2.95))
                        self.assertTrue(contains(data['board_clip'], 10, 0))
                    else:
                        self.assertNotIn('board_clip', data)
                    artifacts = os.environ.get('IBOM_TEST_OUTPUT_DIR')
                    if artifacts:
                        output = Path(artifacts)
                        output.mkdir(parents=True, exist_ok=True)
                        (output / (case + '.html')).write_text(html, encoding='utf-8')
                        (output / (case + '.json')).write_text(json.dumps(data))
                        (output / (case + '.log')).write_text(
                            result.stdout + result.stderr)

    def test_missing_optional_geometry_apis(self):
        add_drill(self.board, 0, 5)
        required = [
            (pcbnew, ['SHAPE_POLY_SET', 'FromMM']),
            (pcbnew.BOARD, ['GetBoardPolygonOutlines']),
            (pcbnew.SHAPE_POLY_SET, ['OutlineCount', 'Outline', 'HoleCount',
                                    'Hole', 'Area', 'BooleanIntersection',
                                    'BooleanSubtract', 'BooleanAdd']),
            (pcbnew.PAD, ['TransformHoleToPolygon']),
        ]
        for owner, names in required:
            for name in names:
                with self.subTest(api=name), patch.object(owner, name, None):
                    self.assertEqual(parse_clip(self.board), {})

    def test_missing_and_open_outlines_fall_back(self):
        self.assertEqual(parse_clip(pcbnew.BOARD()), {})
        self.board.Remove(list(self.board.GetDrawings())[0])
        self.assertEqual(parse_clip(self.board), {})

    def test_incompatible_geometry_api_falls_back(self):
        for error in [AttributeError, TypeError, RuntimeError]:
            with self.subTest(error=error), patch.object(
                    pcbnew.BOARD, 'GetBoardPolygonOutlines',
                    side_effect=error('unsupported geometry operation')):
                self.assertEqual(parse_clip(self.board), {})


if __name__ == '__main__':
    unittest.main()
