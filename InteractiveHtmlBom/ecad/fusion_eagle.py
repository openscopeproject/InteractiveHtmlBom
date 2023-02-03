import io
import math
import os
import string
import zipfile
from datetime import datetime
from xml.etree import ElementTree

from .common import EcadParser, Component, BoundingBox
from .svgpath import Arc
from ..core.fontparser import FontParser


class FusionEagleParser(EcadParser):
    TOP_COPPER_LAYER = '1'
    BOT_COPPER_LAYER = '16'
    TOP_PLACE_LAYER = '21'
    BOT_PLACE_LAYER = '22'
    TOP_NAMES_LAYER = '25'
    BOT_NAMES_LAYER = '26'
    DIMENSION_LAYER = '20'
    TOP_DOCU_LAYER = '51'
    BOT_DOCU_LAYER = '52'

    def __init__(self, file_name, config, logger):
        super(FusionEagleParser, self).__init__(file_name, config, logger)
        self.config = config
        self.font_parser = FontParser()
        self.min_via_w = 1e-3
        self.pcbdata = {
            'drawings': {
                'silkscreen': {
                    'F': [],
                    'B': []
                },
                'fabrication': {
                    'F': [],
                    'B': []
                }
            },
            'edges': [],
            'footprints': [],
            'font_data': {}
        }
        self.components = []

    def _parse_pad_nets(self, signals):
        elements = {}

        for signal in signals.iter('signal'):
            net = signal.attrib['name']
            for c in signal.iter('contactref'):
                e = c.attrib['element']
                if e not in elements:
                    elements[e] = {}
                elements[e][c.attrib['pad']] = net

        self.elements_pad_nets = elements

    @staticmethod
    def _radian(ux, uy, vx, vy):
        dot = ux * vx + uy * vy
        mod = math.sqrt((ux * ux + uy * uy) * (vx * vx + vy * vy))
        rad = math.acos(dot / mod)
        if ux * vy - uy * vx < 0.0:
            rad = -rad
        return rad

    def _curve_to_svgparams(self, el, x=0, y=0, angle=0):
        _x1 = float(el.attrib['x1'])
        _x2 = float(el.attrib['x2'])
        _y1 = -float(el.attrib['y1'])
        _y2 = -float(el.attrib['y2'])

        dx1, dy1 = self._rotate(_x1, _y1, -angle)
        dx2, dy2 = self._rotate(_x2, _y2, -angle)

        x1, y1 = x + dx1, -y + dy1
        x2, y2 = x + dx2, -y + dy2

        chord = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        theta = float(el.attrib['curve'])
        r = abs(0.5 * chord / math.sin(math.radians(theta) / 2))
        la = 0 if abs(theta) < 180 else 1
        sw = 0 if theta > 0 else 1
        return {
            'x1': x1,
            'y1': y1,
            'r': r,
            'la': la,
            'sw': sw,
            'x2': x2,
            'y2': y2
        }

    def _curve_to_svgpath(self, el, x=0, y=0, angle=0):
        p = self._curve_to_svgparams(el, x, y, angle)
        return 'M {x1} {y1} A {r} {r} 0 {la} {sw} {x2} {y2}'.format(**p)

    @staticmethod
    class Rot:
        def __init__(self, rot_string):
            if not rot_string:
                self.mirrored = False
                self.spin = False
                self.angle = 0
                return
            self.mirrored = 'M' in rot_string
            self.spin = 'S' in rot_string
            self.angle = float(''.join(d for d in rot_string
                                       if d in string.digits + '.'))

        def __str__(self):
            return "Mirrored: {0}, Spin: {1}, Angle: {2}".format(self.mirrored,
                                                                 self.spin,
                                                                 self.angle)

    def _rectangle_vertices(self, el):
        # Note: Eagle specifies a rectangle using opposing corners
        # (x1, y1) = lower-left and (x2, y2) = upper-right) and *optionally*
        # a rotation angle.  The size of the rectangle is defined by the
        # corners irrespective of rotation angle, and then it is rotated
        # about its own center point.
        _x1 = float(el.attrib['x1'])
        _x2 = float(el.attrib['x2'])
        _y1 = -float(el.attrib['y1'])
        _y2 = -float(el.attrib['y2'])

        # Center of rectangle
        xc = (_x1 + _x2) / 2
        yc = (_y1 + _y2) / 2

        # Vertices of rectangle relative to its center, un-rotated
        _dv_c = [
            (_x1 - xc, _y1 - yc),
            (_x2 - xc, _y1 - yc),
            (_x2 - xc, _y2 - yc),
            (_x1 - xc, _y2 - yc)
        ]

        elr = self.Rot(el.get('rot'))

        # Rotate the rectangle about its center
        dv_c = [self._rotate(_x, _y, -elr.angle, elr.mirrored)
                for (_x, _y) in _dv_c]

        # Map vertices to position relative to component origin, un-rotated
        return [(_x + xc, _y + yc) for (_x, _y) in dv_c]

    def _add_drawing(self, el):
        layer_dest = {
            self.DIMENSION_LAYER: self.pcbdata['edges'],
            self.TOP_PLACE_LAYER: self.pcbdata['drawings']['silkscreen']['F'],
            self.BOT_PLACE_LAYER: self.pcbdata['drawings']['silkscreen']['B'],
            self.TOP_NAMES_LAYER: self.pcbdata['drawings']['silkscreen']['F'],
            self.BOT_NAMES_LAYER: self.pcbdata['drawings']['silkscreen']['B']
        }
        if ("layer" in el.attrib) and (el.attrib['layer'] in layer_dest):
            dwg = None
            if el.tag == 'wire':
                dwg = {'width': float(el.attrib['width'])}

                if 'curve' in el.attrib:
                    dwg['type'] = 'arc'
                    dwg['svgpath'] = self._curve_to_svgpath(el)
                else:
                    dwg['type'] = 'segment'
                    dwg['start'] = [
                        float(el.attrib['x1']),
                        -float(el.attrib['y1'])
                    ]
                    dwg['end'] = [
                        float(el.attrib['x2']),
                        -float(el.attrib['y2'])
                    ]

            elif el.tag == 'text':
                # Text is not currently supported (except refdes)
                # due to lack of Eagle font data
                pass

            elif el.tag == 'circle':
                dwg = {
                    'type': 'circle',
                    'start': [float(el.attrib['x']), -float(el.attrib['y'])],
                    'radius': float(el.attrib['radius']),
                    'width': float(el.attrib['width'])
                }

            elif el.tag in ['polygonshape', 'polygon']:
                dwg = {
                    'type': 'polygon',
                    'pos': [0, 0],
                    'angle': 0,
                    'polygons': []
                }
                segs = el if el.tag == 'polygon' \
                    else el.find('polygonoutlinesegments')
                polygon = FusionEagleParser._segments_to_polygon(segs)
                dwg['polygons'].append(polygon)

            elif el.tag == 'rectangle':
                vertices = self._rectangle_vertices(el)
                dwg = {
                    'type': 'polygon',
                    'pos': [0, 0],
                    'angle': 0,
                    'polygons': [[list(v) for v in vertices]]
                }

            if dwg:
                layer_dest[el.attrib['layer']].append(dwg)

    def _add_track(self, el, net):
        if el.tag == 'via' or (
                el.tag == 'wire' and el.attrib['layer'] in
                [self.TOP_COPPER_LAYER, self.BOT_COPPER_LAYER]):
            trk = {}
            if self.config.include_nets:
                trk['net'] = net

            if el.tag == 'wire':
                dest = self.pcbdata['tracks']['F'] \
                    if el.attrib['layer'] == self.TOP_COPPER_LAYER\
                    else self.pcbdata['tracks']['B']

                if 'curve' in el.attrib:
                    trk['width'] = float(el.attrib['width'])
                    # Get SVG parameters for the curve
                    p = self._curve_to_svgparams(el)
                    start = complex(p['x1'], p['y1'])
                    end = complex(p['x2'], p['y2'])
                    radius = complex(p['r'], p['r'])
                    large_arc = bool(p['la'])
                    sweep = bool(p['sw'])
                    # Pass SVG parameters to get center parameters
                    arc = Arc(start, radius, 0, large_arc, sweep, end)
                    # Create arc track from center parameters
                    trk['center'] = [arc.center.real, arc.center.imag]
                    trk['radius'] = radius.real
                    if arc.delta < 0:
                        trk['startangle'] = arc.theta + arc.delta
                        trk['endangle'] = arc.theta
                    else:
                        trk['startangle'] = arc.theta
                        trk['endangle'] = arc.theta + arc.delta
                    dest.append(trk)
                else:
                    trk['start'] = [
                        float(el.attrib['x1']),
                        -float(el.attrib['y1'])
                    ]
                    trk['end'] = [
                        float(el.attrib['x2']),
                        -float(el.attrib['y2'])
                    ]
                    trk['width'] = float(el.attrib['width'])
                    dest.append(trk)

            elif el.tag == 'via':
                trk['start'] = [float(el.attrib['x']), -float(el.attrib['y'])]
                trk['end'] = trk['start']
                trk['width'] = float(el.attrib['drill']) + 2 * self.min_via_w \
                    if 'diameter' not in el.attrib else float(
                    el.attrib['diameter'])
                self.pcbdata['tracks']['F'].append(trk)
                self.pcbdata['tracks']['B'].append(trk)

    def _calculate_footprint_bbox(self, package, x, y, angle, mirrored):
        _angle = angle if not mirrored else -angle
        layers = [
            self.TOP_PLACE_LAYER,
            self.BOT_PLACE_LAYER,
            self.TOP_DOCU_LAYER,
            self.BOT_DOCU_LAYER
        ]
        xmax, ymax = -float('inf'), -float('inf')
        xmin, ymin = float('inf'), float('inf')

        for el in package.iter('wire'):
            if el.tag == 'wire' and el.attrib['layer'] in layers:
                xmax = max(xmax,
                           max(float(el.attrib['x1']), float(el.attrib['x2'])))
                ymax = max(ymax,
                           max(float(el.attrib['y1']), float(el.attrib['y2'])))
                xmin = min(xmin,
                           min(float(el.attrib['x1']), float(el.attrib['x2'])))
                ymin = min(ymin,
                           min(float(el.attrib['y1']), float(el.attrib['y2'])))

        for el in package.iter():
            if el.tag in ['smd', 'pad']:
                elx, ely = float(el.attrib['x']), float(el.attrib['y'])
                if el.tag == 'smd':
                    dx, dy = abs(float(el.attrib['dx'])) / 2, abs(
                        float(el.attrib['dy'])) / 2
                else:
                    d = el.get('diameter')
                    if d is None:
                        diameter = float(el.get('drill')) + 2 * self.min_via_w
                    else:
                        diameter = float(d)
                    dx, dy = diameter / 2, diameter / 2
                xmax, ymax = max(xmax, elx + dx), max(ymax, ely + dy)
                xmin, ymin = min(xmin, elx - dx), min(ymin, ely - dy)

        if not math.isinf(xmin):
            if mirrored:
                xmin, xmax = -xmax, -xmin
            dx, dy = self._rotate(xmin, ymax, _angle)
            sx = abs(xmax - xmin)
            sy = abs(ymax - ymin)
        else:
            dx, dy = 0, 0
            sx, sy = 0, 0

        return {
             'pos': [x + dx, -y - dy],
             'angle': _angle,
             'relpos': [0, 0],
             'size': [sx, sy]
        }

    def _footprint_pads(self, package, x, y, angle, mirrored, refdes):
        pads = []
        element_pad_nets = self.elements_pad_nets.get(refdes)
        pin1_allocated = False
        for el in package.iter():
            if el.tag == 'pad':
                elx = float(el.attrib['x'])
                ely = -float(el.attrib['y'])
                drill = float(el.attrib['drill'])

                dx, dy = self._rotate(elx, ely, -angle, mirrored)

                diameter = drill + 2 * self.min_via_w \
                    if 'diameter' not in el.attrib \
                    else float(el.attrib['diameter'])

                pr = self.Rot(el.get('rot'))
                if mirrored ^ pr.mirrored:
                    pad_angle = -angle - pr.angle
                else:
                    pad_angle = angle + pr.angle

                pad = {
                    'layers': ['F', 'B'],
                    'pos': [x + dx, -y + dy],
                    'angle': pad_angle,
                    'type': 'th',
                    'drillshape': 'circle',
                    'drillsize': [
                        drill,
                        drill
                    ]
                }

                if el.get('name') in ['1', 'A', 'A1', 'P1', 'PAD1'] and \
                        not pin1_allocated:
                    pad['pin1'] = 1
                    pin1_allocated = True

                if 'shape' not in el.attrib or el.attrib['shape'] == 'round':
                    pad['shape'] = 'circle'
                    pad['size'] = [diameter, diameter]
                elif el.attrib['shape'] == 'square':
                    pad['shape'] = 'rect'
                    pad['size'] = [diameter, diameter]
                elif el.attrib['shape'] == 'octagon':
                    pad['shape'] = 'chamfrect'
                    pad['size'] = [diameter, diameter]
                    pad['radius'] = 0
                    pad['chamfpos'] = 0b1111  # all corners
                    pad['chamfratio'] = 0.333
                elif el.attrib['shape'] == 'long':
                    pad['shape'] = 'roundrect'
                    pad['radius'] = diameter / 2
                    pad['size'] = [2 * diameter, diameter]
                elif el.attrib['shape'] == 'offset':
                    pad['shape'] = 'roundrect'
                    pad['radius'] = diameter / 2
                    pad['size'] = [2 * diameter, diameter]
                    pad['offset'] = [diameter / 2, 0]
                elif el.attrib['shape'] == 'slot':
                    pad['shape'] = 'roundrect'
                    pad['radius'] = diameter / 2
                    slot_length = float(el.attrib['slotLength'])
                    pad['size'] = [slot_length + diameter / 2, diameter]
                    pad['drillshape'] = 'oblong'
                    pad['drillsize'] = [slot_length, drill]
                else:
                    self.logger.info(
                        "Unsupported footprint pad shape %s, skipping",
                        el.attrib['shape'])

                if self.config.include_nets and element_pad_nets is not None:
                    net = element_pad_nets.get(el.attrib['name'])
                    if net is not None:
                        pad['net'] = net

                pads.append(pad)

            elif el.tag == 'smd':
                layer = el.attrib['layer']
                if layer == '1' and not mirrored or \
                    layer == '16' and mirrored:
                    layers = ['F']
                elif layer == '1' and mirrored or \
                    layer == '16' and not mirrored:
                    layers = ['B']
                else:
                    self.logger.error('Unable to determine layer for '
                                      '{0} pad {1}'.format(refdes,
                                                           el.attrib['name']))
                    layers = None

                if layers is not None:
                    elx = float(el.attrib['x'])
                    ely = -float(el.attrib['y'])

                    dx, dy = self._rotate(elx, ely, -angle, mirrored)

                    pr = self.Rot(el.get('rot'))
                    if mirrored ^ pr.mirrored:
                        pad_angle = -angle - pr.angle
                    else:
                        pad_angle = angle + pr.angle

                    pad = {'layers': layers,
                           'pos': [x + dx, -y + dy],
                           'size': [
                               float(el.attrib['dx']),
                               float(el.attrib['dy'])
                           ],
                           'angle': pad_angle,
                           'type': 'smd',
                           }

                    if el.get('name') in ['1', 'A', 'A1', 'P1', 'PAD1'] and \
                            not pin1_allocated:
                        pad['pin1'] = 1
                        pin1_allocated = True

                    if 'roundness' not in el.attrib:
                        pad['shape'] = 'rect'
                    else:
                        pad['shape'] = 'roundrect'
                        pad['radius'] = (float(el.attrib['roundness']) / 100) \
                                        * float(el.attrib['dy']) / 2

                    if self.config.include_nets and \
                            element_pad_nets is not None:
                        net = element_pad_nets.get(el.attrib['name'])
                        if net is not None:
                            pad['net'] = net

                    pads.append(pad)
        return pads

    @staticmethod
    def _rotate(x, y, angle, mirrored=False):
        sin = math.sin(math.radians(angle))
        cos = math.cos(math.radians(angle))
        xr = x * cos - y * sin
        yr = y * cos + x * sin
        if mirrored:
            return -xr, yr
        else:
            return xr, yr

    def _add_silk_fab(self, el, x, y, angle, mirrored, populate):
        if el.tag == 'hole':
            dwg_layer = self.pcbdata['edges']
        elif el.attrib['layer'] in [self.TOP_PLACE_LAYER, self.BOT_PLACE_LAYER]:
            dwg_layer = self.pcbdata['drawings']['silkscreen']
            top = el.attrib['layer'] == self.TOP_PLACE_LAYER
        elif el.attrib['layer'] in [self.TOP_DOCU_LAYER, self.BOT_DOCU_LAYER]:
            if not populate:
                return
            dwg_layer = self.pcbdata['drawings']['fabrication']
            top = el.attrib['layer'] == self.TOP_DOCU_LAYER
        else:
            return

        dwg = None

        if el.tag == 'wire':
            _dx1 = float(el.attrib['x1'])
            _dx2 = float(el.attrib['x2'])
            _dy1 = -float(el.attrib['y1'])
            _dy2 = -float(el.attrib['y2'])

            dx1, dy1 = self._rotate(_dx1, _dy1, -angle, mirrored)
            dx2, dy2 = self._rotate(_dx2, _dy2, -angle, mirrored)

            x1, y1 = x + dx1, -y + dy1
            x2, y2 = x + dx2, -y + dy2

            if el.get('curve'):
                dwg = {
                    'type': 'arc',
                    'width': float(el.attrib['width']),
                    'svgpath': self._curve_to_svgpath(el, x, y, angle)
                }
            else:
                dwg = {
                    'type': 'segment',
                    'start': [x1, y1],
                    'end': [x2, y2],
                    'width': float(el.attrib['width'])
                }

        elif el.tag == 'rectangle':
            _dv = self._rectangle_vertices(el)

            # Rotate rectangle about component origin based on component angle
            dv = [self._rotate(_x, _y, -angle, mirrored) for (_x, _y) in _dv]

            # Map vertices back to absolute coordinates
            v = [(x + _x, -y + _y) for (_x, _y) in dv]

            dwg = {
                'type': 'polygon',
                'filled': 1,
                'pos': [0, 0],
                'polygons': [v]
            }

        elif el.tag in ['circle', 'hole']:
            _x = float(el.attrib['x'])
            _y = -float(el.attrib['y'])
            dxc, dyc = self._rotate(_x, _y, -angle, mirrored)
            xc, yc = x + dxc, -y + dyc

            if el.tag == 'circle':
                radius = float(el.attrib['radius'])
                width = float(el.attrib['width'])
            else:
                radius = float(el.attrib['drill']) / 2
                width = 0

            dwg = {
                'type': 'circle',
                'start': [xc, yc],
                'radius': radius,
                'width': width
            }

        elif el.tag in ['polygonshape', 'polygon']:
            segs = el if el.tag == 'polygon' \
                else el.find('polygonoutlinesegments')

            dv = self._segments_to_polygon(segs, angle, mirrored)

            polygon = [[x + v[0], -y + v[1]] for v in dv]

            dwg = {
                'type': 'polygon',
                'filled': 1,
                'pos': [0, 0],
                'polygons': [polygon]
            }

        if dwg is not None:
            if el.tag == 'hole':
                dwg_layer.append(dwg)
            else:
                bot = not top

                # Note that in Eagle terminology, 'mirrored' essentially means
                # 'flipped' (i.e. to the opposite side of the board)
                if (mirrored and bot) or (not mirrored and top):
                    dwg_layer['F'].append(dwg)
                elif (mirrored and top) or (not mirrored and bot):
                    dwg_layer['B'].append(dwg)

    def _process_footprint(self, package, x, y, angle, mirrored, populate):
        for el in package.iter():
            if el.tag in ['wire', 'rectangle', 'circle', 'hole',
                          'polygonshape', 'polygon', 'hole']:
                self._add_silk_fab(el, x, y, angle, mirrored, populate)

    def _element_refdes_to_silk(self, el):
        for attr in el.iter('attribute'):
            if attr.attrib['name'] == 'NAME':
                attrx = float(attr.attrib['x'])
                attry = -float(attr.attrib['y'])
                xpos = attrx
                ypos = attry
                elr = self.Rot(el.get('rot'))
                tr = self.Rot(attr.get('rot'))
                text = el.attrib['name']

                angle = tr.angle
                mirrored = tr.mirrored
                spin = elr.spin ^ tr.spin
                if mirrored:
                    angle = -angle

                if 'align' not in attr.attrib:
                    justify = [-1, 1]
                elif attr.attrib['align'] == 'center':
                    justify = [0, 0]
                else:
                    j = attr.attrib['align'].split('-')
                    alignments = {
                        'bottom': 1,
                        'center': 0,
                        'top': -1,
                        'left': -1,
                        'right': 1
                    }
                    justify = [alignments[ss] for ss in j[::-1]]
                if (90 < angle < 270 and not spin) or \
                        (-90 >= angle >= -270 and not spin):
                    angle += 180
                    justify = [-j for j in justify]

                size = float(attr.attrib['size'])
                ratio = float(attr.get('ratio', '8')) / 100
                dwg = {
                    'type': 'text',
                    'text': text,
                    'pos': [xpos, ypos],
                    'height': size,
                    'width': size,
                    'justify': justify,
                    'thickness': size * ratio,
                    'attr': [] if not mirrored else ['mirrored'],
                    'angle': angle
                }

                self.font_parser.parse_font_for_string(text)
                if mirrored:
                    self.pcbdata['drawings']['silkscreen']['B'].append(dwg)
                else:
                    self.pcbdata['drawings']['silkscreen']['F'].append(dwg)

    @staticmethod
    def _segments_to_polygon(segs, angle=0, mirrored=False):
        polygon = []
        for vertex in segs.iter('vertex'):
            _x, _y = float(vertex.attrib['x']), -float(vertex.attrib['y'])
            x, y = FusionEagleParser._rotate(_x, _y, -angle, mirrored)
            polygon.append([x, y])
        return polygon

    def _add_zone(self, poly, net):
        layer = poly.attrib['layer']
        if layer == self.TOP_COPPER_LAYER:
            dest = self.pcbdata['zones']['F']
        elif layer == self.BOT_COPPER_LAYER:
            dest = self.pcbdata['zones']['B']
        else:
            return

        if poly.tag == 'polygonpour':
            segs = poly.find('polygonfilldetails').find('polygonshape') \
                .find('polygonoutlinesegments')
        else:
            segs = poly

        zone = {'polygons': []}
        zone['polygons'].append(self._segments_to_polygon(segs))
        if self.config.include_nets:
            zone['net'] = net
        dest.append(zone)

    def _add_parsed_font_data(self):
        for (c, wl) in self.font_parser.get_parsed_font().items():
            if c not in self.pcbdata['font_data']:
                self.pcbdata['font_data'][c] = wl

    def parse(self):
        ext = os.path.splitext(self.file_name)[1]

        if ext.lower() == '.fbrd':
            with zipfile.ZipFile(self.file_name) as myzip:
                brdfilename = [fname for fname in myzip.namelist() if
                               os.path.splitext(fname)[1] == '.brd']
                with myzip.open(brdfilename[0]) as brdfile:
                    return self._parse(brdfile)

        elif ext.lower() == '.brd':
            with io.open(self.file_name, 'r', encoding='utf-8') as brdfile:
                return self._parse(brdfile)

    def _parse(self, brdfile):
        try:
            brdxml = ElementTree.parse(brdfile)
        except ElementTree.ParseError as err:
            self.logger.error("Exception occurred trying to parse {0}, message:"
                              " {1}"
                              .format(brdfile.name, err.msg))
            return None, None
        if brdxml is None:
            self.logger.error("No data was able to be parsed from {0}"
                              .format(brdfile.name))
            return None, None

        # Pick out key sections
        root = brdxml.getroot()
        board = root.find('drawing').find('board')
        plain = board.find('plain')
        elements = board.find('elements')
        signals = board.find('signals')

        # Build library mapping elements' pads to nets
        self._parse_pad_nets(signals)

        # Determine minimum via annular ring from board design rules
        # (Needed in order to calculate through-hole pad diameters correctly)
        mv = [el.attrib['value'] for el in root.iter('param') if
              el.attrib['name'] == 'rlMinViaOuter']
        if len(mv) == 0:
            self.logger.warning("rlMinViaOuter not found, defaulting to 0")
            self.min_via_w = 0
        else:
            if len(mv) > 1:
                self.logger.warning("Multiple rlMinViaOuter found, using first "
                                    "occurrence")
            mv = mv[0]
            mv_val = float(''.join(d for d in mv if d in string.digits + '.'))
            mv_units = (''.join(d for d in mv if d in string.ascii_lowercase))

            if mv_units == 'mm':
                self.min_via_w = mv_val
            elif mv_units == 'mil':
                self.min_via_w = mv_val * 0.0254
            else:
                self.logger.error("Unsupported units %s on rlMinViaOuter",
                                  mv_units)

        # Edges & silkscreen (partial)
        for el in plain.iter():
            self._add_drawing(el)
        # identify board bounding box based on edges
        board_outline_bbox = BoundingBox()

        for drawing in self.pcbdata['edges']:
            self.add_drawing_bounding_box(drawing, board_outline_bbox)
        if board_outline_bbox.initialized():
            self.pcbdata['edges_bbox'] = board_outline_bbox.to_dict()

        # Signals --> nets
        if self.config.include_nets:
            self.pcbdata['nets'] = []
            for signal in signals.iter('signal'):
                self.pcbdata['nets'].append(signal.attrib['name'])

        # Signals --> tracks, zones
        if self.config.include_tracks:
            self.pcbdata['tracks'] = {'F': [], 'B': []}
            self.pcbdata['zones'] = {'F': [], 'B': []}
            for signal in signals.iter('signal'):
                for wire in signal.iter('wire'):
                    self._add_track(wire, signal.attrib['name'])
                for via in signal.iter('via'):
                    self._add_track(via, signal.attrib['name'])
                for poly in signal.iter('polygonpour'):
                    self._add_zone(poly, signal.attrib['name'])
                for poly in signal.iter('polygon'):
                    self._add_zone(poly, signal.attrib['name'])

        # Elements --> components, footprints, silkscreen
        for el in elements.iter('element'):
            populate = el.get('populate') != 'no'
            elr = self.Rot(el.get('rot'))
            layer = 'B' if elr.mirrored else 'F'
            extra_fields = {}

            for a in el.iter('attribute'):
                if 'value' in a.attrib:
                    extra_fields[a.attrib['name']] = a.attrib['value']

            comp = Component(ref=el.attrib['name'],
                             val='' if 'value' not in el.attrib else el.attrib[
                                 'value'],
                             footprint=el.attrib['package'],
                             layer=layer,
                             attr=None,
                             extra_fields=extra_fields)

            # For component, get footprint data
            libs = [lib for lib in board.find('libraries').findall('library')
                       if lib.attrib['name'] == el.attrib['library']]
            packages = []
            for lib in libs:
                p = [pac for pac in lib.find('packages').findall('package')
                     if pac.attrib['name'] == el.attrib['package']]
                packages.extend(p)
            if not packages:
                self.logger.error("Package {0} in library {1} not found in "
                                  "source file {2} for element {3}"
                                  .format(el.attrib['package'],
                                          el.attrib['library'],
                                          brdfile.name,
                                          el.attrib['name']))
                return None, None
            else:
                package = packages[0]
                if len(packages) > 1:
                    self.logger.warn("Multiple packages found for package {0}"
                                     " in library {1}, using first instance "
                                     "found".format(el.attrib['package'],
                                                    el.attrib['library']))

            elx = float(el.attrib['x'])
            ely = float(el.attrib['y'])
            refdes = el.attrib['name']
            footprint = {
                'ref': refdes,
                'center': [elx, ely],
                'pads': [],
                'drawings': [],
                'layer': layer
            }

            elr = self.Rot(el.get('rot'))
            footprint['pads'] = self._footprint_pads(package, elx, ely,
                                                     elr.angle, elr.mirrored,
                                                     refdes)
            footprint['bbox'] = self._calculate_footprint_bbox(package, elx,
                                                               ely, elr.angle,
                                                               elr.mirrored)
            self.pcbdata['footprints'].append(footprint)

            # Add silkscreen for component footprint & refdes
            self._process_footprint(package, elx, ely, elr.angle, elr.mirrored,
                                    populate)
            self._element_refdes_to_silk(el)

            if populate:
                self.components.append(comp)

        self._add_parsed_font_data()

        # Fabrication & metadata
        company = [a.attrib['value'] for a in root.iter('attribute') if
                   a.attrib['name'] == 'COMPANY']
        company = '' if not company else company[0]
        rev = [a.attrib['value'] for a in root.iter('attribute') if
               a.attrib['name'] == 'REVISION']
        rev = '' if not rev else rev[0]

        if not rev:
            rev = ''

        title = os.path.basename(self.file_name)

        variant = [a.attrib['name'] for a in root.iter('variantdef') if
                   a.get('current') == 'yes']
        variant = None if not variant else variant[0]
        if variant:
            title = "{0}, Variant: {1}".format(title, variant)

        date = datetime.fromtimestamp(
            os.path.getmtime(self.file_name)).strftime('%Y-%m-%d %H:%M:%S')
        self.pcbdata['metadata'] = {'title': title, 'revision': rev,
                                    'company': company, 'date': date}

        return self.pcbdata, self.components
