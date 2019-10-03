import io
import sys

from .common import EcadParser, Component, BoundingBox
from .kicad_extra.parser_base import ParserBase

PY3 = sys.version_info[0] == 3

if PY3:
    string_types = str
else:
    string_types = basestring

# TODO:
# - pin 1 marking
# - add parsing for remaining standard figures
# - input file verification

class AllegroParser(EcadParser):
    TOP_COPPER_LAYER = 1
    BOT_COPPER_LAYER = 2
    TOP_SILK_LAYER = 3
    BOT_SILK_LAYER = 4
    TOP_ASSEMBLY_LAYER = 5
    BOT_ASSEMBLY_LAYER = 6
    BOARD_OUTLINE_LAYER = 7

    def __init__(self, file_name, logger):
        super(AllegroParser, self).__init__(file_name, logger)
        self.extra_data_func = self.parse_schematic_data

    def parse_schematic_data(self, file_name, normalize_case):
        field_names = []
        field_values = {}
        with open(file_name, 'r') as f:
            for line in f:
                if line.startswith('A'):
                    # A record contains the labels for each data field
                    field_names = line.split('!')[1:-1]
                elif line.startswith('S'):
                    # S records contain data values
                    values = line.split('!')[1:-1]
                    d = dict(zip(field_names, values))
                    ref = d['REFDES']
                    for k, v in d.items():
                        field_values.setdefault(ref, {})[k] = v

        data = (field_names, field_values)
        if normalize_case:
            data = ParserBase.normalize_field_names(data)
        return sorted(data[0]), data[1]

    @staticmethod
    def parse_font():
        import re

        with open('ansifont.dat', 'r') as f:
            font = f.readlines()

        width = 0
        height = 0
        index = 0
        font_data = {}
        path = []

        for line in font:
            # remove comments from the file
            line = re.sub(r'/\*.+\*/', '', line)
            line = line.split()

            if line[0] == 'Width':
                width = int(line[1])
            if line[0] == 'Height':
                height = int(line[1])
            elif len(line) == 1:
                # line contains the number of steps for the next character
                step = 0
                steps = int(line[0])

                if steps == 0:
                    index += 1
                else:
                    font_data[chr(index)] = {
                        # the font is monospace, and we scale every character to be 1 unit wide
                        'w': 1,
                        'l': []
                    }
            elif len(line) == 3:
                # line contains a command and coordinates for the step
                # commands:
                # 1 = move to point
                # 2 = draw horizontally
                # 3 = draw vertically
                # 4 = draw

                line = [int(x) for x in line]
                point = [line[1] / width, -line[2] / height]

                if line[0] == 1 and len(path) > 0:
                    font_data[chr(index)]['l'].append(path)
                    path = []

                path.append(point)

                step += 1
                if step == steps:
                    font_data[chr(index)]['l'].append(path)
                    path = []
                    index += 1

        font_data[' '] = {
            'w': 1,
            'l': []
        }

        return font_data


    @staticmethod
    def normalize(v):
        if isinstance(v, string_types):
            v = float(v)
        return v


    @staticmethod
    def rotate(origin, point, angle):
        import math
        angle = math.radians(angle)

        ox, oy = origin
        px, py = point

        qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
        qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
        return qx, qy


    def get_shape_layer(self, shape):
        return {
            'BOARD GEOMETRY': {
                'CUTOUT': self.BOARD_OUTLINE_LAYER,
                'DESIGN_OUTLINE': self.BOARD_OUTLINE_LAYER,
                'OUTLINE': self.BOARD_OUTLINE_LAYER,
                'SILKSCREEN_TOP': self.TOP_SILK_LAYER,
                'SILKSCREEN_BOTTOM': self.BOT_SILK_LAYER,
            },
            'PACKAGE GEOMETRY': {
                'ASSEMBLY_TOP': self.TOP_ASSEMBLY_LAYER,
                'ASSEMBLY_BOTTOM': self.BOT_ASSEMBLY_LAYER,
                'SILKSCREEN_TOP': self.TOP_SILK_LAYER,
                'SILKSCREEN_BOTTOM': self.BOT_SILK_LAYER,
            },
            'PIN': {
                'TOP': self.TOP_COPPER_LAYER,
                'BOTTOM': self.BOT_COPPER_LAYER,
            },
            'REF DES': {
                'SILKSCREEN_TOP': self.TOP_SILK_LAYER,
                'SILKSCREEN_BOTTOM': self.BOT_SILK_LAYER,
            }
        }.get(shape['CLASS'], {}).get(shape['SUBCLASS'])


    def shape_is_copper(self, shape):
        return self.get_shape_layer(shape) in [self.TOP_COPPER_LAYER, self.BOT_COPPER_LAYER]


    def get_allegro_pcb(self):
        shapes = []
        extents = []

        with io.open(self.file_name, 'r', encoding='utf-8') as f:
            keys = []
            for line in f:
                if line.startswith('A'):
                    # A record contains the labels for each data field
                    keys = line.split('!')[1:-1]
                elif line.startswith('J'):
                    # J record contains global data about the design
                    values = line.split('!')[1:-1]
                    name = values[0]
                    datetime = values[1]
                    minx = self.normalize(values[2])
                    miny = self.normalize(values[3])
                    maxx = self.normalize(values[4])
                    maxy = self.normalize(values[5])
                    extents = [[minx, miny], [maxx, maxy]]
                elif line.startswith('S'):
                    # S records contain data values
                    values = line.split('!')[1:-1]
                    d = dict(zip(keys, values))
                    d['RECORD_TAG'] = d['RECORD_TAG'].split(' ')
                    shapes.append(d)

        return {
            'datetime': datetime,
            'extents': extents,
            'name': name,
            'shape': shapes,
        }


    def parse_line(self, shape, use_svgpath=False, use_moveto=False):
        x1 = self.normalize(shape['GRAPHIC_DATA_1'])
        y1 = self.normalize(shape['GRAPHIC_DATA_2'])
        x2 = self.normalize(shape['GRAPHIC_DATA_3'])
        y2 = self.normalize(shape['GRAPHIC_DATA_4'])
        width = self.normalize(shape['GRAPHIC_DATA_5'])

        if use_svgpath:
            svgpath = ''
            if use_moveto:
                svgpath += f'M{x1},{-y1}'
            svgpath += f'L{x2},{-y2}'

            return svgpath

        return [{
            "type": "segment",
            "start": [x1, -y1],
            "end": [x2, -y2],
            "width": width,
        }]


    def parse_circle(self, shape, into_pad=False):
        cx = self.normalize(shape['GRAPHIC_DATA_1'])
        cy = self.normalize(shape['GRAPHIC_DATA_2'])
        r = self.normalize(shape['GRAPHIC_DATA_3']) / 2.0

        if into_pad:
            return {
                'shape': 'circle',
                'pos': [cx, -cy],
                'size': [2*r, 2*r]
            }

        return [{
            "type": "circle",
            "start": [cx, -cy],
            "radius": r,
            "width": 0.0
        }]


    def parse_arc(self, shape, use_svgpath=False, use_moveto=False):
        import math
        x1 = self.normalize(shape['GRAPHIC_DATA_1'])
        y1 = self.normalize(shape['GRAPHIC_DATA_2'])
        x2 = self.normalize(shape['GRAPHIC_DATA_3'])
        y2 = self.normalize(shape['GRAPHIC_DATA_4'])
        x = self.normalize(shape['GRAPHIC_DATA_5'])
        y = self.normalize(shape['GRAPHIC_DATA_6'])
        r = self.normalize(shape['GRAPHIC_DATA_7'])
        width = self.normalize(shape['GRAPHIC_DATA_8'])
        direction = shape['GRAPHIC_DATA_9']

        if use_svgpath:
            svgpath = ''
            if use_moveto:
                svgpath += f'M{x1},{-y1}'

            sweep_flag = 1 if direction == 'CLOCKWISE' else 0
            svgpath += f'A{r},{r},0,0,{sweep_flag},{x2},{-y2}'
            return svgpath

        if x1 == x2 and y1 == y2:
            return [{
                "type": "circle",
                "start": [x, -y],
                "radius": r,
                "width": width,
            }]

        angle1 = math.degrees(math.atan2(y1 - y, x1 - x))
        angle2 = math.degrees(math.atan2(y2 - y, x2 - x))

        angle1, angle2 = 360 - angle2, 360 - angle1

        if direction == 'CLOCKWISE':
            angle1, angle2 = angle2, angle1

        return [{
            "type": "arc",
            "width": width,
            "start": [x, -y],
            "radius": r,
            "startangle": angle1,
            "endangle": angle2,
        }]


    def parse_rectangle(self, shape, into_pad=False):
        x1 = self.normalize(shape['GRAPHIC_DATA_1'])
        y1 = self.normalize(shape['GRAPHIC_DATA_2'])
        x2 = self.normalize(shape['GRAPHIC_DATA_3'])
        y2 = self.normalize(shape['GRAPHIC_DATA_4'])

        if into_pad:
            return {
                'shape': 'rect',
                'pos': [x1, -y1],
                'size': [x2, y2]
            }

        filled = shape['GRAPHIC_DATA_5'] == '1'

        vertices = [[x1, -y1], [x1, -y2], [x2, -y2], [x2, -y1]]

        if filled:
            return [{
                "type": "polygon",
                "pos": [x1, -y1],
                "angle": 0,
                "polygons": [vertices]
            }]
        else:
            return [{
                "type": "segment",
                "start": vertices[0],
                "end": vertices[1],
                "width": 0,
            }, {
                "type": "segment",
                "start": vertices[1],
                "end": vertices[2],
                "width": 0,
            }, {
                "type": "segment",
                "start": vertices[2],
                "end": vertices[3],
                "width": 0,
            }, {
                "type": "segment",
                "start": vertices[3],
                "end": vertices[0],
                "width": 0,
            }]


    def parse_text(self, shape):
        x = self.normalize(shape['GRAPHIC_DATA_1'])
        y = self.normalize(shape['GRAPHIC_DATA_2'])
        angle = self.normalize(shape['GRAPHIC_DATA_3'])
        mirrored = shape['GRAPHIC_DATA_4'] == 'YES'
        justify = {
            'LEFT': -1,
            'CENTER': 0,
            'RIGHT': 1
        }.get(shape['GRAPHIC_DATA_5'], -1)

        font_params = shape['GRAPHIC_DATA_6'].split(' ')
        height = float(font_params[2])
        width = float(font_params[3])
        char_spacing = float(font_params[5])
        thickness = float(font_params[7])

        text = shape['GRAPHIC_DATA_7']

        # TODO ok for center, right justify?
        (offset_x, offset_y) = self.rotate((0, 0), (0, height/2), angle)
        x += offset_x
        y += offset_y

        drawing = {
            "text": text,
            "pos": [x, -y],
            "height": height,
            "width": width,
            "horiz_justify": justify,
            "thickness": thickness,
            "attr": ["mirrored" if mirrored else ""],
            "angle": angle,
            "char_spacing": char_spacing,
        }

        if shape['SUBCLASS'] == 'SILKSCREEN_TOP' or shape['SUBCLASS'] == 'SILKSCREEN_BOTTOM':
            if shape['CLASS'] == 'REF DES':
                drawing['ref'] = 1

        return [drawing]


    def parse_shape(self, shape):
        parse_func = {
            'ARC': self.parse_arc,
            'CIRCLE': self.parse_circle,
            'LINE': self.parse_line,
            'SQUARE': self.parse_rectangle,
            'RECTANGLE': self.parse_rectangle,
            'TEXT': self.parse_text,

            # TODO: take care of these other shapes
            'OCTAGON': None,
            'CROSS': None,
            'DIAMOND': None,
            'OBLONG_X': None,
            'OBLONG_Y': None,
            'HEXAGON_X': None,
            'HEXAGON_Y': None,
            'TRIANGLE_1': None,
        }.get(shape['GRAPHIC_DATA_NAME'], None)
        if parse_func:
            return parse_func(shape)

        return None


    def parse_shapes(self, pcb):
        drawings = {}
        refdes_list = []

        for shape in pcb['shape']:
            json_list = self.parse_shape(shape)
            layer = self.get_shape_layer(shape)
            if json_list and layer:
                drawings.setdefault(layer, []).extend(json_list)

            # Since we're already looping through all shapes,
            # let's build a list of reference designators
            # to make parsing them (and their pads) easier later on
            if shape['REFDES'] and shape['REFDES'] not in refdes_list:
                refdes_list.append(shape['REFDES'])

        pcb['refdes_list'] = refdes_list

        return drawings


    def parse_shapes_into_pad(self, shapes):
        pads = []
        pad = {
            'layers': [{
                self.TOP_COPPER_LAYER: 'F',
                self.BOT_COPPER_LAYER: 'B',
            }.get(self.get_shape_layer(shapes[0]))],
            'pos': [0, 0],
            'size': [0, 0],
            'angle': 0,
            'shape': 'svgpath',
            'svgpath': '',
            'type': 'smd',
            'pin1': 1 if shapes[0]['PIN_NUMBER'] in ['1', 'A1'] else 0 # TODO
        }
        hole = None

        if shapes[0]['DRILL_HOLE_NAME']:
            drill_width = self.normalize(shapes[0]['DRILL_HOLE_NAME'])
            drill_height = self.normalize(shapes[0]['DRILL_HOLE_NAME2'])
            drill_x = self.normalize(shapes[0]['DRILL_HOLE_X'])
            drill_y = self.normalize(shapes[0]['DRILL_HOLE_Y'])
            drill_rot = self.normalize(shapes[0]['DRILL_FIGURE_ROTATION']) if shapes[0]['DRILL_FIGURE_ROTATION'] else 0
            hole = {
                "layers": ['F', 'B'],
                'type': 'th',
                'pos': [drill_x, -drill_y],
                'drillshape': 'circle' if drill_width == drill_height else 'oblong',
                'drillsize': [drill_width, drill_height],
                'angle': 360 - drill_rot
            }

        for s in shapes:
            if s['GRAPHIC_DATA_NAME'] == 'LINE':
                pad['svgpath'] += self.parse_line(s, True, not pad['svgpath'])
            elif s['GRAPHIC_DATA_NAME'] == 'ARC':
                pad['svgpath'] += self.parse_arc(s, True, not pad['svgpath'])
            elif s['GRAPHIC_DATA_NAME'] == 'CIRCLE':
                pad.update(self.parse_circle(s, True))
            elif s['GRAPHIC_DATA_NAME'].startswith('OBLONG'):
                x = self.normalize(s['GRAPHIC_DATA_1'])
                y = self.normalize(s['GRAPHIC_DATA_2'])
                width = self.normalize(s['GRAPHIC_DATA_3'])
                height = self.normalize(s['GRAPHIC_DATA_4'])
                pad['shape'] = 'oval'
                pad['pos'] = [x, -y]
                pad['size'] = [width, height]
            elif s['GRAPHIC_DATA_NAME'] == 'FIG_RECTANGLE' or s['GRAPHIC_DATA_NAME'] == 'SQUARE':
                pad.update(self.parse_rectangle(s, True))

        pads.append(pad)
        if hole:
            pads.append(hole)

        return pads

    def parse_modules_components(self, pcb):
        modules = []
        components = []

        for refdes in pcb['refdes_list']:
            pads = []

            refdes_shapes = [s for s in pcb['shape'] if s['REFDES'] == refdes]

            # the following data is the same in each shape for a given refdes,
            # so just pick it from the first shape
            cx = self.normalize(refdes_shapes[0]['SYM_CENTER_X'])
            cy = self.normalize(refdes_shapes[0]['SYM_CENTER_Y'])
            bbox_x1 = self.normalize(refdes_shapes[0]['SYM_BOX_X1'])
            bbox_y1 = self.normalize(refdes_shapes[0]['SYM_BOX_Y1'])
            bbox_x2 = self.normalize(refdes_shapes[0]['SYM_BOX_X2'])
            bbox_y2 = self.normalize(refdes_shapes[0]['SYM_BOX_Y2'])
            bbox_width = abs(bbox_x1 - bbox_x2)
            bbox_height = abs(bbox_y1 - bbox_y2)
            layer = 'F' if refdes_shapes[0]['SYM_MIRROR'] == 'NO' else 'B'
            value = refdes_shapes[0]['VALUE']
            footprint = refdes_shapes[0]['SYM_NAME']

            # get a list of unique record numbers for the current refdes
            # we do this instead of basing it on pin numbers directly
            # because some pins (e.g. mechanical pins) don't have pin numbers
            records = list(set([s['RECORD_TAG'][0] for s in refdes_shapes]))
            for record in records:
                record_shapes = [s for s in refdes_shapes if s['RECORD_TAG'][0] == record and self.shape_is_copper(s)]
                if not record_shapes:
                    continue

                pads.extend(self.parse_shapes_into_pad(record_shapes))

            modules.append({
                "ref": refdes,
                "center": [cx, -cy],
                "bbox": {
                    "pos": [bbox_x1, -bbox_y2],
                    "size": [bbox_width, bbox_height]
                },
                "pads": pads,
                "drawings": [],
                "layer": layer
            })
            components.append(Component(refdes, value, footprint, layer))

        return modules, components


    def get_metadata(self, pcb):
        return {
            'title': self.name,
            'revision': '',
            'company': '',
            'date': self.date,
        }


    def add_drawing_bounding_box(self, drawing, bbox):
        # type: (dict, BoundingBox) -> None

        def add_segment():
            bbox.add_segment(drawing['start'][0], drawing['start'][1],
                             drawing['end'][0], drawing['end'][1],
                             drawing['width'] / 2)

        def add_circle():
            bbox.add_circle(drawing['start'][0], drawing['start'][1],
                            drawing['radius'] + drawing['width'] / 2)

        def add_polygon():
            polygon = drawing['polygons'][0]
            for point in polygon:
                bbox.add_point(point[0], point[1])

        {
            'segment': add_segment,
            'circle': add_circle,
            'arc': lambda: None, # TODO
            'polygon': add_polygon,
            'text': lambda: None,  # text is not really needed for bounding box
        }.get(drawing['type'])()


    def parse(self):
        pcb = self.get_allegro_pcb()
        #if not self._verify(pcb):
        #    self.logger.error('File ' + self.file_name +
        #                      ' does not appear to be a valid Allegro ASCII file.')
        #    return None, None

        drawings = self.parse_shapes(pcb)
        modules, components = self.parse_modules_components(pcb)

        board_outline_bbox = BoundingBox()
        for drawing in drawings.get(self.BOARD_OUTLINE_LAYER, []):
            self.add_drawing_bounding_box(drawing, board_outline_bbox)
        if board_outline_bbox.initialized():
            bbox = board_outline_bbox.to_dict()
        else:
            # if nothing is drawn on outline layer then rely on Allegro design extents
            bbox = {
                "minx": pcb['extents'][0][0],
                "miny": pcb['extents'][0][1],
                "maxx": pcb['extents'][1][0],
                "maxy": pcb['extents'][1][1],
            }

        pcbdata = {
            "edges_bbox": bbox,
            "edges": drawings.get(self.BOARD_OUTLINE_LAYER, []),
            "silkscreen": {
                'F': drawings.get(self.TOP_SILK_LAYER, []),
                'B': drawings.get(self.BOT_SILK_LAYER, []),
            },
            "fabrication": {
                'F': drawings.get(self.TOP_ASSEMBLY_LAYER, []),
                'B': drawings.get(self.BOT_ASSEMBLY_LAYER, []),
            },
            "modules": modules,
            "metadata": self.get_metadata(pcb),
            "bom": {},
            "font_data": self.parse_font(),
        }

        return pcbdata, components