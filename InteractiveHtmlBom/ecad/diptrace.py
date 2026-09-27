"""DipTrace PCB XML parser."""

import math
import os
from datetime import datetime
from xml.etree import ElementTree

from .common import BoundingBox, Component, EcadParser


class DipTraceParser(EcadParser):
    """Parse DipTrace's native XML PCB format into the generic pcbdata model."""

    _UNIT_SCALE = {'mm': 1.0, 'mil': 0.0254, 'inch': 25.4}

    def _number(self, value, default=0.0):
        try:
            return float(str(value).replace(',', '.')) * self.scale
        except (TypeError, ValueError):
            return default

    def _point(self, node):
        return [self._number(node.get('X')), self._number(node.get('Y'))]

    @staticmethod
    def _rotate(point, angle, mirror=False):
        x, y = point
        if mirror:
            x = -x
        c, s = math.cos(angle), math.sin(angle)
        return [x * c - y * s, x * s + y * c]

    def _layer(self, name, lay_id=None):
        name = (name or '').lower()
        if name in ('top', 'top silk', 'top assy', 'top outline',
                    'top terminals', 'top courtyard'):
            return 'F'
        if name in ('bottom', 'bottom silk', 'bottom assy', 'bottom outline',
                    'bottom terminals', 'bottom courtyard'):
            return 'B'
        if lay_id is not None:
            lname = self.copper_layers.get(str(lay_id), '').lower()
            if 'bottom' in lname or lname in ('bot', 'b.cu'):
                return 'B'
            if 'top' in lname or lname in ('top', 'f.cu'):
                return 'F'
        return None

    def _parse_patterns(self, root):
        patterns, styles = {}, {}
        for library in root.findall('.//Library[@Type="DipTrace-PatternLibrary"]'):
            for style in library.findall('./PadStyles/PadStyle'):
                styles[style.get('Name')] = style
            for pattern in library.findall('./Patterns/Pattern'):
                key = pattern.get('PatternStyle') or pattern.findtext('Name')
                if key:
                    patterns[key] = pattern
        return patterns, styles

    def _pad(self, pad, style, comp, comp_angle, mirror, net):
        local = [self._number(pad.get('X')) / self.scale,
                 self._number(pad.get('Y')) / self.scale]
        local = self._rotate(local, comp_angle, mirror)
        pos = [comp[0] + local[0] * self.scale,
               comp[1] + local[1] * self.scale]
        pad_angle = comp_angle + self._number(pad.get('Angle')) / self.scale
        stack = style.find('./MainStack') if style is not None else None
        shape_name = (stack.get('Shape') if stack is not None else 'Round').lower()
        shape = {'round': 'circle', 'circle': 'circle', 'rect': 'rect',
                 'rectangle': 'rect', 'obround': 'roundrect',
                 'oval': 'roundrect'}.get(shape_name, 'rect')
        width = self._number(stack.get('Width') if stack is not None else None)
        height = self._number(stack.get('Height') if stack is not None else None, width)
        if not width:
            width = height = self._number(stack.get('Diameter') if stack is not None else None, 1.0)
        through = style is not None and style.get('Type', '').lower() == 'through'
        result = {'pos': pos, 'size': [width, height],
                  'angle': math.degrees(pad_angle), 'shape': shape,
                  'layers': ['F', 'B'] if through else
                  (['B'] if (pad.get('Side') or 'Top').lower() == 'bottom' else ['F']),
                  'type': 'th' if through else 'smd'}
        if shape == 'roundrect':
            result['radius'] = min(width, height) / 2
        if through:
            drill = self._number(style.get('Hole'))
            result.update(drillshape='oblong' if style.get('HoleType') == 'Obround' else 'circle',
                          drillsize=[drill, self._number(style.get('HoleH'), drill)])
        if self.config.include_nets and net is not None:
            result['net'] = net
        return result

    @staticmethod
    def _append_segments(points, width, drawings):
        drawings.extend({'type': 'segment', 'start': a, 'end': b, 'width': width}
                         for a, b in zip(points, points[1:]))

    def _parse_pattern_shapes(self, pattern, origin, angle, mirror):
        drawings = []
        for shape in pattern.findall('./Shapes/Shape'):
            layer = self._layer(shape.get('Layer'))
            if layer is None:
                continue
            points = [self._rotate(self._point(p), angle, mirror)
                      for p in shape.findall('./Points/Point')]
            points = [[p[0] + origin[0], p[1] + origin[1]] for p in points]
            typ = (shape.get('Type') or '').lower()
            width = self._number(shape.get('LineWidth'), 0.15 * self.scale)
            if typ in ('line', 'polyline'):
                self._append_segments(points, width, drawings)
            elif typ == 'rectangle' and len(points) >= 2:
                drawings.append({'type': 'rect', 'start': points[0], 'end': points[1], 'width': width})
            elif typ in ('polygon', 'fillrect', 'fillobround') and points:
                drawings.append({'type': 'polygon', 'pos': [0, 0], 'angle': 0,
                                 'polygons': [points]})
            elif typ == 'obround' and len(points) >= 2:
                drawings.append({'type': 'segment', 'start': points[0], 'end': points[1], 'width': width})
        return drawings

    def _parse(self):
        try:
            root = ElementTree.parse(self.file_name).getroot()
        except (OSError, ElementTree.ParseError) as err:
            self.logger.error('Unable to parse DipTrace file %s: %s', self.file_name, err)
            return None, None
        if root.get('Type') != 'DipTrace-PCB':
            self.logger.error('File %s is not a DipTrace PCB XML file', self.file_name)
            return None, None
        self.scale = self._UNIT_SCALE.get((root.get('Units') or 'mm').lower())
        if self.scale is None:
            self.logger.error('Unsupported DipTrace unit %s', root.get('Units'))
            return None, None
        self.copper_layers = {layer.get('Id'): layer.findtext('Name', '')
                              for layer in root.findall('.//CopperLayers/Lay')}
        patterns, styles = self._parse_patterns(root)
        data = {'drawings': {'silkscreen': {'F': [], 'B': []},
                             'fabrication': {'F': [], 'B': []}},
                'edges': [], 'footprints': [], 'font_data': {}}
        components = []
        board = root.find('./Board')
        if board is None:
            self.logger.error('DipTrace file has no Board element')
            return None, None

        outline = board.find('./BoardOutline/Points')
        if outline is not None:
            points = [self._point(p) for p in outline.findall('Point')]
            if len(points) > 1:
                closed = points[1:] + points[:1]
                data['edges'].extend({'type': 'segment', 'start': a, 'end': b,
                                      'width': 0.1 * self.scale}
                                     for a, b in zip(points, closed))

        net_names = {n.get('Id'): n.findtext('Name', '')
                     for n in board.findall('./Nets/Net')}
        for node in board.findall('./Components/Component'):
            ref = node.findtext('RefDes', '')
            value = node.findtext('Value', node.findtext('Name', ''))
            comp = [self._number(node.get('X')), self._number(node.get('Y'))]
            angle = self._number(node.get('Angle')) / self.scale
            mirror = (node.get('Side') or 'Top').lower() == 'bottom'
            pattern_name = node.get('PatternStyle')
            pattern = patterns.get(pattern_name)
            pad_nets = {p.get('Id'): p.get('NetId') for p in node.findall('./Pads/Pad')}
            pads = []
            drawings = []
            if pattern is not None:
                for pad in pattern.findall('./Pads/Pad'):
                    pads.append(self._pad(pad, styles.get(pad.get('Style')), comp,
                                          angle, mirror, net_names.get(pad_nets.get(pad.get('Id')))))
                drawings = self._parse_pattern_shapes(pattern, comp, angle, mirror)
            if not pads:
                continue
            side = 'B' if mirror else 'F'
            width = self._number(pattern.get('Width')) if pattern is not None else 0
            height = self._number(pattern.get('Height')) if pattern is not None else 0
            data['footprints'].append({'ref': ref, 'center': comp, 'pads': pads,
                                       'drawings': drawings, 'layer': side,
                                       'bbox': {'pos': [comp[0] - width / 2, comp[1] - height / 2],
                                                'relpos': [0, 0], 'size': [width, height],
                                                'angle': math.degrees(angle)}})
            data['drawings']['silkscreen'][side].extend(drawings)
            components.append(Component(ref=ref, val=value,
                                        footprint=pattern_name or '', layer=side))

        if self.config.include_tracks:
            data['tracks'], data['zones'] = {'F': [], 'B': []}, {'F': [], 'B': []}
            for net in board.findall('./Nets/Net'):
                net_name = net.findtext('Name', '')
                for trace in net.findall('./Traces/Trace'):
                    points = trace.findall('./Points/Point')
                    for first, second in zip(points, points[1:]):
                        side = self._layer(None, second.get('Lay'))
                        if side is None:
                            continue
                        track = {'start': self._point(first), 'end': self._point(second),
                                 'width': self._number(second.get('Width'))}
                        if self.config.include_nets:
                            track['net'] = net_name
                        data['tracks'][side].append(track)
            for pour in board.findall('./CopperPours/CopperPour'):
                side = self._layer(None, pour.get('Lay'))
                points = [self._point(p) for p in pour.findall('./Points/Point')]
                if side and len(points) > 2:
                    zone = {'polygons': [points]}
                    if self.config.include_nets:
                        zone['net'] = net_names.get(pour.get('NetId'), '')
                    data['zones'][side].append(zone)

        bbox = BoundingBox()
        for drawing in data['edges']:
            self.add_drawing_bounding_box(drawing, bbox)
        if bbox.initialized():
            data['edges_bbox'] = bbox.to_dict()
        data['metadata'] = {'title': os.path.basename(self.file_name), 'revision': '',
                            'company': '', 'date': datetime.fromtimestamp(
                                os.path.getmtime(self.file_name)).strftime('%Y-%m-%d %H:%M:%S')}
        if self.config.include_nets:
            data['nets'] = list(net_names.values())
        return data, components

    def parse(self):
        return self._parse()
