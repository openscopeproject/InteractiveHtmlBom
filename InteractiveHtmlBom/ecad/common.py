import math

from .svgpath import parse_path


class EcadParser(object):

    def __init__(self, file_name, config, logger):
        """
        :param file_name: path to file that should be parsed.
        :param config: Config instance
        :param logger: logging object.
        """
        self.file_name = file_name
        self.config = config
        self.logger = logger

    def parse(self):
        """
        Abstract method that should be overridden in implementations.
        Performs all the parsing and returns a tuple of
        (pcbdata, components)
        pcbdata is described in DATAFORMAT.md
        components is list of Component objects
        :return:
        """
        pass

    @staticmethod
    def normalize_field_names(data):
        field_map = {f.lower(): f for f in reversed(data[0])}

        def remap(ref_fields):
            return {field_map[f.lower()]: v for (f, v) in
                    sorted(ref_fields.items(), reverse=True)}

        field_data = {r: remap(d) for (r, d) in data[1].items()}
        return field_map.values(), field_data

    def get_extra_field_data(self, file_name):
        """
        Abstract method that may be overridden in implementations that support
        extra field data.
        :return: tuple of the format
            (
                [field_name1, field_name2,... ],
                {
                    ref1: {
                        field_name1: field_value1,
                        field_name2: field_value2,
                        ...
                    ],
                    ref2: ...
                }
            )
        """
        return [], {}

    def parse_extra_data(self, file_name, normalize_case):
        """
        Parses the file and returns extra field data.
        :param file_name: path to file containing extra data
        :param normalize_case: if true, normalize case so that
                               "mpn", "Mpn", "MPN" fields are combined
        :return:
        """
        data = self.get_extra_field_data(file_name)
        if normalize_case:
            data = self.normalize_field_names(data)
        return sorted(data[0]), data[1]

    def latest_extra_data(self, extra_dirs=None):
        """
        Abstract method that may be overridden in implementations that support
        extra field data.
        :param extra_dirs: List of extra directories to search.
        :return: File name of most recent file with extra field data.
        """
        return None

    def extra_data_file_filter(self):
        """
        Abstract method that may be overridden in implementations that support
        extra field data.
        :return: File open dialog filter string, eg:
                 "Netlist and xml files (*.net; *.xml)|*.net;*.xml"
        """
        return None

    def add_drawing_bounding_box(self, drawing, bbox):
        # type: (dict, BoundingBox) -> None

        def add_segment():
            bbox.add_segment(drawing['start'][0], drawing['start'][1],
                             drawing['end'][0], drawing['end'][1],
                             drawing['width'] / 2)

        def add_circle():
            bbox.add_circle(drawing['start'][0], drawing['start'][1],
                            drawing['radius'] + drawing['width'] / 2)

        def add_svgpath():
            width = drawing.get('width', 0)
            bbox.add_svgpath(drawing['svgpath'], width, self.logger)

        def add_polygon():
            if 'polygons' not in drawing:
                add_svgpath()
                return
            polygon = drawing['polygons'][0]
            for point in polygon:
                bbox.add_point(point[0], point[1])

        def add_arc():
            if 'svgpath' in drawing:
                add_svgpath()
            else:
                width = drawing.get('width', 0)
                xc, yc = drawing['start'][:2]
                a1 = drawing['startangle']
                a2 = drawing['endangle']
                r = drawing['radius']
                x1 = xc + math.cos(math.radians(a1))
                y1 = xc + math.sin(math.radians(a1))
                x2 = xc + math.cos(math.radians(a2))
                y2 = xc + math.sin(math.radians(a2))
                da = a2 - a1 if a2 > a1 else a2 + 360 - a1
                la = 1 if da > 180 else 0
                svgpath = 'M %s %s A %s %s 0 %s 1 %s %s' % \
                          (x1, y1, r, r, la, x2, y2)
                bbox.add_svgpath(svgpath, width, self.logger)

        {
            'segment': add_segment,
            'rect': add_segment,  # bbox of a rect and segment are the same
            'circle': add_circle,
            'arc': add_arc,
            'polygon': add_polygon,
            'text': lambda: None,  # text is not really needed for bounding box
        }.get(drawing['type'])()


class Component(object):
    """Simple data object to store component data needed for bom table."""

    def __init__(self, ref, val, footprint, layer, attr=None, extra_fields={}):
        self.ref = ref
        self.val = val
        self.footprint = footprint
        self.layer = layer
        self.attr = attr
        self.extra_fields = extra_fields


class BoundingBox(object):
    """Geometry util to calculate and combine bounding box of simple shapes."""

    def __init__(self):
        self._x0 = None
        self._y0 = None
        self._x1 = None
        self._y1 = None

    def to_dict(self):
        # type: () -> dict
        return {
            "minx": self._x0,
            "miny": self._y0,
            "maxx": self._x1,
            "maxy": self._y1,
        }

    def to_component_dict(self):
        # type: () -> dict
        return {
            "pos": [self._x0, self._y0],
            "relpos": [0, 0],
            "size": [self._x1 - self._x0, self._y1 - self._y0],
            "angle": 0,
        }

    def add(self, other):
        """Add another bounding box.
        :type other: BoundingBox
        """
        if other._x0 is not None:
            self.add_point(other._x0, other._y0)
            self.add_point(other._x1, other._y1)
        return self

    @staticmethod
    def _rotate(x, y, rx, ry, angle):
        sin = math.sin(math.radians(angle))
        cos = math.cos(math.radians(angle))
        new_x = rx + (x - rx) * cos - (y - ry) * sin
        new_y = ry + (x - rx) * sin + (y - ry) * cos
        return new_x, new_y

    def add_point(self, x, y, rx=0, ry=0, angle=0):
        x, y = self._rotate(x, y, rx, ry, angle)
        if self._x0 is None:
            self._x0 = x
            self._y0 = y
            self._x1 = x
            self._y1 = y
        else:
            self._x0 = min(self._x0, x)
            self._y0 = min(self._y0, y)
            self._x1 = max(self._x1, x)
            self._y1 = max(self._y1, y)
        return self

    def add_segment(self, x0, y0, x1, y1, r):
        self.add_circle(x0, y0, r)
        self.add_circle(x1, y1, r)
        return self

    def add_rectangle(self, x, y, w, h, angle=0):
        self.add_point(x - w / 2, y - h / 2, x, y, angle)
        self.add_point(x + w / 2, y - h / 2, x, y, angle)
        self.add_point(x - w / 2, y + h / 2, x, y, angle)
        self.add_point(x + w / 2, y + h / 2, x, y, angle)
        return self

    def add_circle(self, x, y, r):
        self.add_point(x - r, y)
        self.add_point(x, y - r)
        self.add_point(x + r, y)
        self.add_point(x, y + r)
        return self

    def add_svgpath(self, svgpath, width, logger):
        w = width / 2
        for segment in parse_path(svgpath, logger):
            x0, x1, y0, y1 = segment.bbox()
            self.add_point(x0 - w, y0 - w)
            self.add_point(x1 + w, y1 + w)

    def pad(self, amount):
        """Add small padding to the box."""
        if self._x0 is not None:
            self._x0 -= amount
            self._y0 -= amount
            self._x1 += amount
            self._y1 += amount

    def initialized(self):
        return self._x0 is not None
