import math


class EcadParser(object):

    def __init__(self, file_name, logger):
        """
        :param file_name: path to file that should be parsed.
        :param logger: logging object.
        """
        self.file_name = file_name
        self.logger = logger
        self.extra_data_func = lambda f, b: ([], {})
        self.latest_extra_data = None

    def parse(self):
        """
        Abstract method that should be overridden in implementations.
        Performs all the parsing and returns a tuple of (pcbdata, components)
        pcbdata is described in DATAFORMAT.md
        components is list of Component objects
        :return:
        """
        pass


class Component(object):
    """Simple data object to store component data needed for bom table."""

    def __init__(self, ref, val, footprint, layer, attr=None):
        self.ref = ref
        self.val = val
        self.footprint = footprint
        self.layer = layer
        self.attr = attr


class BoundingBox(object):
    """Geometry util to calculate and compound bounding box of simple shapes."""

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
            "size": [self._x1 - self._x0, self._y1 - self._y0],
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

    def add_arc(self):
        # TODO
        pass

    def pad(self, amount):
        """Add small padding to the box."""
        if self._x0 is not None:
            self._x0 -= amount
            self._y0 -= amount
            self._x1 += amount
            self._y1 += amount

    def initialized(self):
        return self._x0 is not None
