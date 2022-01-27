"""This submodule contains very stripped down bare bones version of
svgpathtools module:
https://github.com/mathandy/svgpathtools

All external dependencies are removed. This code can parse path strings with
segments and arcs, calculate bounding box and that's about it. This is all
that is needed in ibom parsers at the moment.
"""

# External dependencies
from __future__ import division, absolute_import, print_function

import re
from cmath import exp
from math import sqrt, cos, sin, acos, degrees, radians, pi


def clip(a, a_min, a_max):
    return min(a_max, max(a_min, a))


class Line(object):
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __repr__(self):
        return 'Line(start=%s, end=%s)' % (self.start, self.end)

    def __eq__(self, other):
        if not isinstance(other, Line):
            return NotImplemented
        return self.start == other.start and self.end == other.end

    def __ne__(self, other):
        if not isinstance(other, Line):
            return NotImplemented
        return not self == other

    def __len__(self):
        return 2

    def bbox(self):
        """returns the bounding box for the segment in the form
        (xmin, xmax, ymin, ymax)."""
        xmin = min(self.start.real, self.end.real)
        xmax = max(self.start.real, self.end.real)
        ymin = min(self.start.imag, self.end.imag)
        ymax = max(self.start.imag, self.end.imag)
        return xmin, xmax, ymin, ymax


class Arc(object):
    def __init__(self, start, radius, rotation, large_arc, sweep, end,
                 autoscale_radius=True):
        """
        This should be thought of as a part of an ellipse connecting two
        points on that ellipse, start and end.
        Parameters
        ----------
        start : complex
            The start point of the curve. Note: `start` and `end` cannot be the
            same.  To make a full ellipse or circle, use two `Arc` objects.
        radius : complex
            rx + 1j*ry, where rx and ry are the radii of the ellipse (also
            known as its semi-major and semi-minor axes, or vice-versa or if
            rx < ry).
            Note: If rx = 0 or ry = 0 then this arc is treated as a
            straight line segment joining the endpoints.
            Note: If rx or ry has a negative sign, the sign is dropped; the
            absolute value is used instead.
            Note:  If no such ellipse exists, the radius will be scaled so
            that one does (unless autoscale_radius is set to False).
        rotation : float
            This is the CCW angle (in degrees) from the positive x-axis of the
            current coordinate system to the x-axis of the ellipse.
        large_arc : bool
            Given two points on an ellipse, there are two elliptical arcs
            connecting those points, the first going the short way around the
            ellipse, and the second going the long way around the ellipse.  If
            `large_arc == False`, the shorter elliptical arc will be used.  If
            `large_arc == True`, then longer elliptical will be used.
            In other words, `large_arc` should be 0 for arcs spanning less than
            or equal to 180 degrees and 1 for arcs spanning greater than 180
            degrees.
        sweep : bool
            For any acceptable parameters `start`, `end`, `rotation`, and
            `radius`, there are two ellipses with the given major and minor
            axes (radii) which connect `start` and `end`.  One which connects
            them in a CCW fashion and one which connected them in a CW
            fashion.  If `sweep == True`, the CCW ellipse will be used.  If
            `sweep == False`, the CW ellipse will be used.  See note on curve
            orientation below.
        end : complex
            The end point of the curve. Note: `start` and `end` cannot be the
            same.  To make a full ellipse or circle, use two `Arc` objects.
        autoscale_radius : bool
            If `autoscale_radius == True`, then will also scale `self.radius`
            in the case that no ellipse exists with the input parameters
            (see inline comments for further explanation).

        Derived Parameters/Attributes
        -----------------------------
        self.theta : float
            This is the phase (in degrees) of self.u1transform(self.start).
            It is $\\theta_1$ in the official documentation and ranges from
            -180 to 180.
        self.delta : float
            This is the angular distance (in degrees) between the start and
            end of the arc after the arc has been sent to the unit circle
            through self.u1transform().
            It is $\\Delta\\theta$ in the official documentation and ranges
            from -360 to 360; being positive when the arc travels CCW and
            negative otherwise (i.e. is positive/negative when
            sweep == True/False).
        self.center : complex
            This is the center of the arc's ellipse.
        self.phi : float
            The arc's rotation in radians, i.e. `radians(self.rotation)`.
        self.rot_matrix : complex
            Equal to `exp(1j * self.phi)` which is also equal to
            `cos(self.phi) + 1j*sin(self.phi)`.


        Note on curve orientation (CW vs CCW)
        -------------------------------------
        The notions of clockwise (CW) and counter-clockwise (CCW) are reversed
        in some sense when viewing SVGs (as the y coordinate starts at the top
        of the image and increases towards the bottom).
        """
        assert start != end
        assert radius.real != 0 and radius.imag != 0

        self.start = start
        self.radius = abs(radius.real) + 1j * abs(radius.imag)
        self.rotation = rotation
        self.large_arc = bool(large_arc)
        self.sweep = bool(sweep)
        self.end = end
        self.autoscale_radius = autoscale_radius

        # Convenience parameters
        self.phi = radians(self.rotation)
        self.rot_matrix = exp(1j * self.phi)

        # Derive derived parameters
        self._parameterize()

    def __repr__(self):
        params = (self.start, self.radius, self.rotation,
                  self.large_arc, self.sweep, self.end)
        return ("Arc(start={}, radius={}, rotation={}, "
                "large_arc={}, sweep={}, end={})".format(*params))

    def __eq__(self, other):
        if not isinstance(other, Arc):
            return NotImplemented
        return self.start == other.start and self.end == other.end \
            and self.radius == other.radius \
            and self.rotation == other.rotation \
            and self.large_arc == other.large_arc and self.sweep == other.sweep

    def __ne__(self, other):
        if not isinstance(other, Arc):
            return NotImplemented
        return not self == other

    def _parameterize(self):
        # See http://www.w3.org/TR/SVG/implnote.html#ArcImplementationNotes
        # my notation roughly follows theirs
        rx = self.radius.real
        ry = self.radius.imag
        rx_sqd = rx * rx
        ry_sqd = ry * ry

        # Transform z-> z' = x' + 1j*y'
        # = self.rot_matrix**(-1)*(z - (end+start)/2)
        # coordinates.  This translates the ellipse so that the midpoint
        # between self.end and self.start lies on the origin and rotates
        # the ellipse so that the its axes align with the xy-coordinate axes.
        # Note:  This sends self.end to -self.start
        zp1 = (1 / self.rot_matrix) * (self.start - self.end) / 2
        x1p, y1p = zp1.real, zp1.imag
        x1p_sqd = x1p * x1p
        y1p_sqd = y1p * y1p

        # Correct out of range radii
        # Note: an ellipse going through start and end with radius and phi
        # exists if and only if radius_check is true
        radius_check = (x1p_sqd / rx_sqd) + (y1p_sqd / ry_sqd)
        if radius_check > 1:
            if self.autoscale_radius:
                rx *= sqrt(radius_check)
                ry *= sqrt(radius_check)
                self.radius = rx + 1j * ry
                rx_sqd = rx * rx
                ry_sqd = ry * ry
            else:
                raise ValueError("No such elliptic arc exists.")

        # Compute c'=(c_x', c_y'), the center of the ellipse in (x', y') coords
        # Noting that, in our new coord system, (x_2', y_2') = (-x_1', -x_2')
        # and our ellipse is cut out by of the plane by the algebraic equation
        # (x'-c_x')**2 / r_x**2 + (y'-c_y')**2 / r_y**2 = 1,
        # we can find c' by solving the system of two quadratics given by
        # plugging our transformed endpoints (x_1', y_1') and (x_2', y_2')
        tmp = rx_sqd * y1p_sqd + ry_sqd * x1p_sqd
        radicand = (rx_sqd * ry_sqd - tmp) / tmp
        try:
            radical = sqrt(radicand)
        except ValueError:
            radical = 0
        if self.large_arc == self.sweep:
            cp = -radical * (rx * y1p / ry - 1j * ry * x1p / rx)
        else:
            cp = radical * (rx * y1p / ry - 1j * ry * x1p / rx)

        # The center in (x,y) coordinates is easy to find knowing c'
        self.center = exp(1j * self.phi) * cp + (self.start + self.end) / 2

        # Now we do a second transformation, from (x', y') to (u_x, u_y)
        # coordinates, which is a translation moving the center of the
        # ellipse to the origin and a dilation stretching the ellipse to be
        # the unit circle
        u1 = (x1p - cp.real) / rx + 1j * (y1p - cp.imag) / ry
        u2 = (-x1p - cp.real) / rx + 1j * (-y1p - cp.imag) / ry

        # clip in case of floating point error
        u1 = clip(u1.real, -1, 1) + 1j * clip(u1.imag, -1, 1)
        u2 = clip(u2.real, -1, 1) + 1j * clip(u2.imag, -1, 1)

        # Now compute theta and delta (we'll define them as we go)
        # delta is the angular distance of the arc (w.r.t the circle)
        # theta is the angle between the positive x'-axis and the start point
        # on the circle
        if u1.imag > 0:
            self.theta = degrees(acos(u1.real))
        elif u1.imag < 0:
            self.theta = -degrees(acos(u1.real))
        else:
            if u1.real > 0:  # start is on pos u_x axis
                self.theta = 0
            else:  # start is on neg u_x axis
                # Note: This behavior disagrees with behavior documented in
                # http://www.w3.org/TR/SVG/implnote.html#ArcImplementationNotes
                # where theta is set to 0 in this case.
                self.theta = 180

        det_uv = u1.real * u2.imag - u1.imag * u2.real

        acosand = u1.real * u2.real + u1.imag * u2.imag
        acosand = clip(acosand.real, -1, 1) + clip(acosand.imag, -1, 1)

        if det_uv > 0:
            self.delta = degrees(acos(acosand))
        elif det_uv < 0:
            self.delta = -degrees(acos(acosand))
        else:
            if u1.real * u2.real + u1.imag * u2.imag > 0:
                # u1 == u2
                self.delta = 0
            else:
                # u1 == -u2
                # Note: This behavior disagrees with behavior documented in
                # http://www.w3.org/TR/SVG/implnote.html#ArcImplementationNotes
                # where delta is set to 0 in this case.
                self.delta = 180

        if not self.sweep and self.delta >= 0:
            self.delta -= 360
        elif self.large_arc and self.delta <= 0:
            self.delta += 360

    def point(self, t):
        if t == 0:
            return self.start
        if t == 1:
            return self.end
        angle = radians(self.theta + t * self.delta)
        cosphi = self.rot_matrix.real
        sinphi = self.rot_matrix.imag
        rx = self.radius.real
        ry = self.radius.imag

        # z = self.rot_matrix*(rx*cos(angle) + 1j*ry*sin(angle)) + self.center
        x = rx * cosphi * cos(angle) - ry * sinphi * sin(
            angle) + self.center.real
        y = rx * sinphi * cos(angle) + ry * cosphi * sin(
            angle) + self.center.imag
        return complex(x, y)

    def bbox(self):
        """returns a bounding box for the segment in the form
        (xmin, xmax, ymin, ymax)."""
        # a(t) = radians(self.theta + self.delta*t)
        #      = (2*pi/360)*(self.theta + self.delta*t)
        # x'=0: ~~~~~~~~~
        # -rx*cos(phi)*sin(a(t)) = ry*sin(phi)*cos(a(t))
        # -(rx/ry)*cot(phi)*tan(a(t)) = 1
        # a(t) = arctan(-(ry/rx)tan(phi)) + pi*k === atan_x
        # y'=0: ~~~~~~~~~~
        # rx*sin(phi)*sin(a(t)) = ry*cos(phi)*cos(a(t))
        # (rx/ry)*tan(phi)*tan(a(t)) = 1
        # a(t) = arctan((ry/rx)*cot(phi))
        # atanres = arctan((ry/rx)*cot(phi)) === atan_y
        # ~~~~~~~~
        # (2*pi/360)*(self.theta + self.delta*t) = atanres + pi*k
        # Therefore, for both x' and y', we have...
        # t = ((atan_{x/y} + pi*k)*(360/(2*pi)) - self.theta)/self.delta
        # for all k s.t. 0 < t < 1
        from math import atan, tan

        if cos(self.phi) == 0:
            atan_x = pi / 2
            atan_y = 0
        elif sin(self.phi) == 0:
            atan_x = 0
            atan_y = pi / 2
        else:
            rx, ry = self.radius.real, self.radius.imag
            atan_x = atan(-(ry / rx) * tan(self.phi))
            atan_y = atan((ry / rx) / tan(self.phi))

        def angle_inv(ang, q):  # inverse of angle from Arc.derivative()
            return ((ang + pi * q) * (360 / (2 * pi)) -
                    self.theta) / self.delta

        xtrema = [self.start.real, self.end.real]
        ytrema = [self.start.imag, self.end.imag]

        for k in range(-4, 5):
            tx = angle_inv(atan_x, k)
            ty = angle_inv(atan_y, k)
            if 0 <= tx <= 1:
                xtrema.append(self.point(tx).real)
            if 0 <= ty <= 1:
                ytrema.append(self.point(ty).imag)
        return min(xtrema), max(xtrema), min(ytrema), max(ytrema)


COMMANDS = set('MmZzLlHhVvCcSsQqTtAa')
UPPERCASE = set('MZLHVCSQTA')

COMMAND_RE = re.compile("([MmZzLlHhVvCcSsQqTtAa])")
FLOAT_RE = re.compile(r"[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?")


def _tokenize_path(path_def):
    for x in COMMAND_RE.split(path_def):
        if x in COMMANDS:
            yield x
        for token in FLOAT_RE.findall(x):
            yield token


def parse_path(pathdef, logger, current_pos=0j):
    # In the SVG specs, initial movetos are absolute, even if
    # specified as 'm'. This is the default behavior here as well.
    # But if you pass in a current_pos variable, the initial moveto
    # will be relative to that current_pos. This is useful.
    elements = list(_tokenize_path(pathdef))
    # Reverse for easy use of .pop()
    elements.reverse()
    absolute = False

    segments = []

    start_pos = None
    command = None

    while elements:

        if elements[-1] in COMMANDS:
            # New command.
            command = elements.pop()
            absolute = command in UPPERCASE
            command = command.upper()
        else:
            # If this element starts with numbers, it is an implicit command
            # and we don't change the command. Check that it's allowed:
            if command is None:
                raise ValueError(
                    "Unallowed implicit command in %s, position %s" % (
                        pathdef, len(pathdef.split()) - len(elements)))

        if command == 'M':
            # Moveto command.
            x = elements.pop()
            y = elements.pop()
            pos = float(x) + float(y) * 1j
            if absolute:
                current_pos = pos
            else:
                current_pos += pos

            # when M is called, reset start_pos
            # This behavior of Z is defined in svg spec:
            # http://www.w3.org/TR/SVG/paths.html#PathDataClosePathCommand
            start_pos = current_pos

            # Implicit moveto commands are treated as lineto commands.
            # So we set command to lineto here, in case there are
            # further implicit commands after this moveto.
            command = 'L'

        elif command == 'Z':
            # Close path
            if not (current_pos == start_pos):
                segments.append(Line(current_pos, start_pos))
            current_pos = start_pos
            command = None

        elif command == 'L':
            x = elements.pop()
            y = elements.pop()
            pos = float(x) + float(y) * 1j
            if not absolute:
                pos += current_pos
            segments.append(Line(current_pos, pos))
            current_pos = pos

        elif command == 'H':
            x = elements.pop()
            pos = float(x) + current_pos.imag * 1j
            if not absolute:
                pos += current_pos.real
            segments.append(Line(current_pos, pos))
            current_pos = pos

        elif command == 'V':
            y = elements.pop()
            pos = current_pos.real + float(y) * 1j
            if not absolute:
                pos += current_pos.imag * 1j
            segments.append(Line(current_pos, pos))
            current_pos = pos

        elif command == 'C':
            logger.warn('Encountered Cubic Bezier segment. '
                        'It is currently not supported and will be replaced '
                        'by a line segment.')
            for i in range(4):
                # ignore control points
                elements.pop()
            end = float(elements.pop()) + float(elements.pop()) * 1j

            if not absolute:
                end += current_pos

            segments.append(Line(current_pos, end))
            current_pos = end

        elif command == 'S':
            logger.warn('Encountered Quadratic Bezier segment. '
                        'It is currently not supported and will be replaced '
                        'by a line segment.')
            for i in range(2):
                # ignore control points
                elements.pop()
            end = float(elements.pop()) + float(elements.pop()) * 1j

            if not absolute:
                end += current_pos

            segments.append(Line(current_pos, end))
            current_pos = end

        elif command == 'Q':
            logger.warn('Encountered Quadratic Bezier segment. '
                        'It is currently not supported and will be replaced '
                        'by a line segment.')
            for i in range(2):
                # ignore control points
                elements.pop()
            end = float(elements.pop()) + float(elements.pop()) * 1j

            if not absolute:
                end += current_pos

            segments.append(Line(current_pos, end))
            current_pos = end

        elif command == 'T':
            logger.warn('Encountered Quadratic Bezier segment. '
                        'It is currently not supported and will be replaced '
                        'by a line segment.')

            end = float(elements.pop()) + float(elements.pop()) * 1j

            if not absolute:
                end += current_pos

            segments.append(Line(current_pos, end))
            current_pos = end

        elif command == 'A':
            radius = float(elements.pop()) + float(elements.pop()) * 1j
            rotation = float(elements.pop())
            arc = float(elements.pop())
            sweep = float(elements.pop())
            end = float(elements.pop()) + float(elements.pop()) * 1j

            if not absolute:
                end += current_pos

            segments.append(
                Arc(current_pos, radius, rotation, arc, sweep, end))
            current_pos = end

    return segments


def create_path(lines, circles=[]):
    """Returns a path d-string."""

    def limit_digits(val):
        return format(val, '.6f').rstrip('0').replace(',', '.').rstrip('.')

    def different_points(a, b):
        return abs(a[0] - b[0]) > 1e-6 or abs(a[1] - b[1]) > 1e-6

    parts = []

    for i, line in enumerate(lines):
        if i == 0 or different_points(lines[i - 1][-1], line[0]):
            parts.append('M{},{}'.format(*map(limit_digits, line[0])))
        for point in line[1:]:
            parts.append('L{},{}'.format(*map(limit_digits, point)))

    for circle in circles:
        cx, cy, r = circle[0][0], circle[0][1], circle[1]
        parts.append('M{},{}'.format(limit_digits(cx - r), limit_digits(cy)))
        parts.append('a {},{} 0 1,0 {},0'.format(
                     *map(limit_digits, [r, r, r + r])))
        parts.append('a {},{} 0 1,0 -{},0'.format(
                     *map(limit_digits, [r, r, r + r])))

    return ''.join(parts)
