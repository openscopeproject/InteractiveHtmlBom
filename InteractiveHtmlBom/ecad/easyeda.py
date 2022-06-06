import io
import sys

from .common import EcadParser, Component, BoundingBox


if sys.version_info >= (3, 0):
    string_types = str
else:
    string_types = basestring  # noqa F821: ignore undefined


class EasyEdaParser(EcadParser):
    TOP_COPPER_LAYER = 1
    BOT_COPPER_LAYER = 2
    TOP_SILK_LAYER = 3
    BOT_SILK_LAYER = 4
    BOARD_OUTLINE_LAYER = 10
    TOP_ASSEMBLY_LAYER = 13
    BOT_ASSEMBLY_LAYER = 14
    ALL_LAYERS = 11

    def get_easyeda_pcb(self):
        import json
        with io.open(self.file_name, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def tilda_split(s):
        # type: (str) -> list
        return s.split('~')

    @staticmethod
    def sharp_split(s):
        # type: (str) -> list
        return s.split('#@$')

    def _verify(self, pcb):
        """Spot check the pcb object."""
        if 'head' not in pcb:
            self.logger.error('No head attribute.')
            return False
        head = pcb['head']
        if len(head) < 2:
            self.logger.error('Incorrect head attribute ' + pcb['head'])
            return False
        if head['docType'] != '3':
            self.logger.error('Incorrect document type: ' + head['docType'])
            return False
        if 'canvas' not in pcb:
            self.logger.error('No canvas attribute.')
            return False
        canvas = self.tilda_split(pcb['canvas'])
        if len(canvas) < 18:
            self.logger.error('Incorrect canvas attribute ' + pcb['canvas'])
            return False
        self.logger.info('EasyEDA editor version ' + head['editorVersion'])
        return True

    @staticmethod
    def normalize(v):
        if isinstance(v, string_types):
            v = float(v)
        return v

    def parse_track(self, shape):
        shape = self.tilda_split(shape)
        assert len(shape) >= 5, 'Invalid track ' + str(shape)
        width = self.normalize(shape[0])
        layer = int(shape[1])
        points = [self.normalize(v) for v in shape[3].split(' ')]

        points_xy = [[points[i], points[i + 1]] for i in
                     range(0, len(points), 2)]
        segments = [(points_xy[i], points_xy[i + 1]) for i in
                    range(len(points_xy) - 1)]
        segments_json = []
        for segment in segments:
            segments_json.append({
                "type": "segment",
                "start": segment[0],
                "end": segment[1],
                "width": width,
            })

        return layer, segments_json

    def parse_rect(self, shape):
        shape = self.tilda_split(shape)
        assert len(shape) >= 9, 'Invalid rect ' + str(shape)
        x = self.normalize(shape[0])
        y = self.normalize(shape[1])
        width = self.normalize(shape[2])
        height = self.normalize(shape[3])
        layer = int(shape[4])
        fill = shape[8]

        if fill == "none":
            thickness = self.normalize(shape[7])
            return layer, [{
                "type": "rect",
                "start": [x, y],
                "end": [x + width, y + height],
                "width": thickness,
            }]
        else:
            return layer, [{
                "type": "polygon",
                "pos": [x, y],
                "angle": 0,
                "polygons": [
                    [[0, 0], [width, 0], [width, height], [0, height]]
                ]
            }]

    def parse_circle(self, shape):
        shape = self.tilda_split(shape)
        assert len(shape) >= 6, 'Invalid circle ' + str(shape)
        cx = self.normalize(shape[0])
        cy = self.normalize(shape[1])
        r = self.normalize(shape[2])
        width = self.normalize(shape[3])
        layer = int(shape[4])

        return layer, [{
            "type": "circle",
            "start": [cx, cy],
            "radius": r,
            "width": width
        }]

    def parse_solid_region(self, shape):
        shape = self.tilda_split(shape)
        assert len(shape) >= 5, 'Invalid solid region ' + str(shape)
        layer = int(shape[0])
        svgpath = shape[2]

        return layer, [{
            "type": "polygon",
            "svgpath": svgpath,
        }]

    def parse_text(self, shape):
        shape = self.tilda_split(shape)
        assert len(shape) >= 12, 'Invalid text ' + str(shape)
        text_type = shape[0]
        stroke_width = self.normalize(shape[3])
        layer = int(shape[6])
        text = shape[9]
        svgpath = shape[10]
        hide = shape[11]

        return layer, [{
            "type": "text",
            "text": text,
            "thickness": stroke_width,
            "attr": [],
            "svgpath": svgpath,
            "hide": hide,
            "text_type": text_type,
        }]

    def parse_arc(self, shape):
        shape = self.tilda_split(shape)
        assert len(shape) >= 6, 'Invalid arc ' + str(shape)
        width = self.normalize(shape[0])
        layer = int(shape[1])
        svgpath = shape[3]

        return layer, [{
            "type": "arc",
            "svgpath": svgpath,
            "width": width
        }]

    def parse_hole(self, shape):
        shape = self.tilda_split(shape)
        assert len(shape) >= 4, 'Invalid hole ' + str(shape)
        cx = self.normalize(shape[0])
        cy = self.normalize(shape[1])
        radius = self.normalize(shape[2])

        return self.BOARD_OUTLINE_LAYER, [{
            "type": "circle",
            "start": [cx, cy],
            "radius": radius,
            "width": 0.1,  # 1 mil
        }]

    def parse_pad(self, shape):
        shape = self.tilda_split(shape)
        assert len(shape) >= 15, 'Invalid pad ' + str(shape)
        pad_shape = shape[0]
        x = self.normalize(shape[1])
        y = self.normalize(shape[2])
        width = self.normalize(shape[3])
        height = self.normalize(shape[4])
        layer = int(shape[5])
        number = shape[7]
        hole_radius = self.normalize(shape[8])
        if shape[9]:
            points = [self.normalize(v) for v in shape[9].split(' ')]
        else:
            points = []
        angle = int(shape[10])
        hole_length = self.normalize(shape[12]) if shape[12] else 0

        pad_layers = {
            self.TOP_COPPER_LAYER: ['F'],
            self.BOT_COPPER_LAYER: ['B'],
            self.ALL_LAYERS: ['F', 'B']
        }.get(layer)
        pad_shape = {
            "ELLIPSE": "circle",
            "RECT": "rect",
            "OVAL": "oval",
            "POLYGON": "custom",
        }.get(pad_shape)
        pad_type = "smd" if len(pad_layers) == 1 else "th"

        json = {
            "layers": pad_layers,
            "pos": [x, y],
            "size": [width, height],
            "angle": angle,
            "shape": pad_shape,
            "type": pad_type,
        }
        if number == '1':
            json['pin1'] = 1
        if pad_shape == "custom":
            polygon = [(points[i], points[i + 1]) for i in
                       range(0, len(points), 2)]
            # translate coordinates to be relative to footprint
            polygon = [(p[0] - x, p[1] - y) for p in polygon]
            json["polygons"] = [polygon]
            json["angle"] = 0
        if pad_type == "th":
            if hole_length > 1e-6:
                json["drillshape"] = "oblong"
                json["drillsize"] = [hole_radius * 2, hole_length]
            else:
                json["drillshape"] = "circle"
                json["drillsize"] = [hole_radius * 2, hole_radius * 2]

        return layer, [{
            "type": "pad",
            "pad": json,
        }]

    @staticmethod
    def add_pad_bounding_box(pad, bbox):
        # type: (dict, BoundingBox) -> None

        def add_circle():
            bbox.add_circle(pad['pos'][0], pad['pos'][1], pad['size'][0] / 2)

        def add_rect():
            bbox.add_rectangle(pad['pos'][0], pad['pos'][1],
                               pad['size'][0], pad['size'][1],
                               pad['angle'])

        def add_custom():
            x = pad['pos'][0]
            y = pad['pos'][1]
            polygon = pad['polygons'][0]
            for point in polygon:
                bbox.add_point(x + point[0], y + point[1])

        {
            'circle': add_circle,
            'rect': add_rect,
            'oval': add_rect,
            'custom': add_custom,
        }.get(pad['shape'])()

    def parse_lib(self, shape):
        parts = self.sharp_split(shape)
        head = self.tilda_split(parts[0])
        inner_shapes, _, _ = self.parse_shapes(parts[1:])
        x = self.normalize(head[0])
        y = self.normalize(head[1])
        attr = head[2]
        fp_layer = int(head[6])

        attr = attr.split('`')
        if len(attr) % 2 != 0:
            attr.pop()
        attr = {attr[i]: attr[i + 1] for i in range(0, len(attr), 2)}
        fp_layer = 'F' if fp_layer == self.TOP_COPPER_LAYER else 'B'
        val = '??'
        ref = '??'
        footprint = attr.get('package', '??')

        pads = []
        copper_drawings = []
        extra_drawings = []
        bbox = BoundingBox()
        for layer, shapes in inner_shapes.items():
            for s in shapes:
                if s["type"] == "pad":
                    pads.append(s["pad"])
                    continue
                if s["type"] == "text":
                    if s["text_type"] == "N":
                        val = s["text"]
                    if s["text_type"] == "P":
                        ref = s["text"]
                    del s["text_type"]
                    if s["hide"]:
                        continue
                if layer in [self.TOP_COPPER_LAYER, self.BOT_COPPER_LAYER]:
                    copper_drawings.append({
                        "layer": (
                            'F' if layer == self.TOP_COPPER_LAYER else 'B'),
                        "drawing": s,
                    })
                elif layer in [self.TOP_SILK_LAYER,
                               self.BOT_SILK_LAYER,
                               self.TOP_ASSEMBLY_LAYER,
                               self.BOT_ASSEMBLY_LAYER,
                               self.BOARD_OUTLINE_LAYER]:
                    extra_drawings.append((layer, s))

        for pad in pads:
            self.add_pad_bounding_box(pad, bbox)
        for drawing in copper_drawings:
            self.add_drawing_bounding_box(drawing['drawing'], bbox)
        for _, drawing in extra_drawings:
            self.add_drawing_bounding_box(drawing, bbox)
        bbox.pad(0.5)  # pad by 5 mil
        if not bbox.initialized():
            # if bounding box is not calculated yet
            # set it to 100x100 mil square
            bbox.add_rectangle(x, y, 10, 10, 0)

        footprint_json = {
            "ref": ref,
            "center": [x, y],
            "bbox": bbox.to_component_dict(),
            "pads": pads,
            "drawings": copper_drawings,
            "layer": fp_layer,
        }

        component = Component(ref, val, footprint, fp_layer)

        return fp_layer, component, footprint_json, extra_drawings

    def parse_shapes(self, shapes):
        drawings = {}
        footprints = []
        components = []

        for shape_str in shapes:
            shape = shape_str.split('~', 1)
            parse_func = {
                'TRACK': self.parse_track,
                'RECT': self.parse_rect,
                'CIRCLE': self.parse_circle,
                'SOLIDREGION': self.parse_solid_region,
                'TEXT': self.parse_text,
                'ARC': self.parse_arc,
                'PAD': self.parse_pad,
                'HOLE': self.parse_hole,
            }.get(shape[0], None)
            if parse_func:
                layer, json_list = parse_func(shape[1])
                drawings.setdefault(layer, []).extend(json_list)
            if shape[0] == 'LIB':
                layer, component, json, extras = self.parse_lib(shape[1])
                for drawing_layer, drawing in extras:
                    drawings.setdefault(drawing_layer, []).append(drawing)
                footprints.append(json)
                components.append(component)

        return drawings, footprints, components

    def get_metadata(self, pcb):
        if hasattr(pcb, 'metadata'):
            return pcb.metadata
        else:
            import os
            from datetime import datetime
            pcb_file_name = os.path.basename(self.file_name)
            title = os.path.splitext(pcb_file_name)[0]
            file_mtime = os.path.getmtime(self.file_name)
            file_date = datetime.fromtimestamp(file_mtime).strftime(
                '%Y-%m-%d %H:%M:%S')
            return {
                "title": title,
                "revision": "",
                "company": "",
                "date": file_date,
            }

    def parse(self):
        pcb = self.get_easyeda_pcb()
        if not self._verify(pcb):
            self.logger.error(
                'File ' + self.file_name +
                ' does not appear to be valid EasyEDA json file.')
            return None, None

        drawings, footprints, components = self.parse_shapes(pcb['shape'])

        board_outline_bbox = BoundingBox()
        for drawing in drawings.get(self.BOARD_OUTLINE_LAYER, []):
            self.add_drawing_bounding_box(drawing, board_outline_bbox)
        if board_outline_bbox.initialized():
            bbox = board_outline_bbox.to_dict()
        else:
            # if nothing is drawn on outline layer then rely on EasyEDA bbox
            x = self.normalize(pcb['BBox']['x'])
            y = self.normalize(pcb['BBox']['y'])
            bbox = {
                "minx": x,
                "miny": y,
                "maxx": x + self.normalize(pcb['BBox']['width']),
                "maxy": y + self.normalize(pcb['BBox']['height'])
            }

        pcbdata = {
            "edges_bbox": bbox,
            "edges": drawings.get(self.BOARD_OUTLINE_LAYER, []),
            "drawings": {
                "silkscreen": {
                    'F': drawings.get(self.TOP_SILK_LAYER, []),
                    'B': drawings.get(self.BOT_SILK_LAYER, []),
                },
                "fabrication": {
                    'F': drawings.get(self.TOP_ASSEMBLY_LAYER, []),
                    'B': drawings.get(self.BOT_ASSEMBLY_LAYER, []),
                },
            },
            "footprints": footprints,
            "metadata": self.get_metadata(pcb),
            "bom": {},
            "font_data": {}
        }

        if self.config.include_tracks:
            def filter_tracks(drawing_list, drawing_type, keys):
                result = []
                for d in drawing_list:
                    if d["type"] == drawing_type:
                        r = {}
                        for key in keys:
                            r[key] = d[key]
                        result.append(r)
                return result

            pcbdata["tracks"] = {
                'F': filter_tracks(drawings.get(self.TOP_COPPER_LAYER, []),
                                   "segment", ["start", "end", "width"]),
                'B': filter_tracks(drawings.get(self.BOT_COPPER_LAYER, []),
                                   "segment", ["start", "end", "width"]),
            }
            # zones are not supported
            pcbdata["zones"] = {'F': [], 'B': []}

        return pcbdata, components
