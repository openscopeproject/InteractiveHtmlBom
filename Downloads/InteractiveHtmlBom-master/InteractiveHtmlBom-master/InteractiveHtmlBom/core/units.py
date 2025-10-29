# _*_ coding:utf-8 _*_

# Stolen from
# https://github.com/SchrodingersGat/KiBoM/blob/master/KiBOM/units.py

"""

This file contains a set of functions for matching values which may be written
in different formats e.g.
0.1uF = 100n (different suffix specified, one has missing unit)
0R1 = 0.1Ohm (Unit replaces decimal, different units)

"""

import re
import locale

current_locale = locale.setlocale(locale.LC_NUMERIC)
try:
    locale.setlocale(locale.LC_NUMERIC, '')
except Exception:
    # sometimes setlocale with empty string doesn't work on OSX
    pass
decimal_separator = locale.localeconv()['decimal_point']
locale.setlocale(locale.LC_NUMERIC, current_locale)

PREFIX_MICRO = [u"μ", u"µ", "u", "micro"]  # first is \u03BC second is \u00B5
PREFIX_MILLI = ["milli", "m"]
PREFIX_NANO = ["nano", "n"]
PREFIX_PICO = ["pico", "p"]
PREFIX_KILO = ["kilo", "k"]
PREFIX_MEGA = ["mega", "meg"]
PREFIX_GIGA = ["giga", "g"]

# All prefices
PREFIX_ALL = PREFIX_PICO + PREFIX_NANO + PREFIX_MICRO + \
    PREFIX_MILLI + PREFIX_KILO + PREFIX_MEGA + PREFIX_GIGA

# Common methods of expressing component units
UNIT_R = ["r", "ohms", "ohm", u"Ω", u"ω"]
UNIT_C = ["farad", "f"]
UNIT_L = ["henry", "h"]

UNIT_ALL = UNIT_R + UNIT_C + UNIT_L

VALUE_REGEX = re.compile(
    "^([0-9\\.]+)(" + "|".join(PREFIX_ALL) + ")*(" + "|".join(
        UNIT_ALL) + ")*(\\d*)$")

REFERENCE_REGEX = re.compile("^(r|rv|c|l)(\\d+)$")


def getUnit(unit):
    """
    Return a simplified version of a units string, for comparison purposes
    """
    if not unit:
        return None

    unit = unit.lower()

    if unit in UNIT_R:
        return "R"
    if unit in UNIT_C:
        return "F"
    if unit in UNIT_L:
        return "H"

    return None


def getPrefix(prefix):
    """
    Return the (numerical) value of a given prefix
    """
    if not prefix:
        return 1

    prefix = prefix.lower()

    if prefix in PREFIX_PICO:
        return 1.0e-12
    if prefix in PREFIX_NANO:
        return 1.0e-9
    if prefix in PREFIX_MICRO:
        return 1.0e-6
    if prefix in PREFIX_MILLI:
        return 1.0e-3
    if prefix in PREFIX_KILO:
        return 1.0e3
    if prefix in PREFIX_MEGA:
        return 1.0e6
    if prefix in PREFIX_GIGA:
        return 1.0e9

    return 1


def compMatch(component):
    """
    Return a normalized value and units for a given component value string
    e.g. compMatch("10R2") returns (1000, R)
    e.g. compMatch("3.3mOhm") returns (0.0033, R)
    """
    component = component.strip().lower()
    if decimal_separator == ',':
        # replace separator with dot
        component = component.replace(",", ".")
    else:
        # remove thousands separator
        component = component.replace(",", "")

    result = VALUE_REGEX.match(component)

    if not result:
        return None

    if not len(result.groups()) == 4:
        return None

    value, prefix, units, post = result.groups()

    # special case where units is in the middle of the string
    # e.g. "0R05" for 0.05Ohm
    # in this case, we will NOT have a decimal
    # we will also have a trailing number

    if post and "." not in value:
        try:
            value = float(int(value))
            postValue = float(int(post)) / (10 ** len(post))
            value = value * 1.0 + postValue
        except ValueError:
            return None

    try:
        val = float(value)
    except ValueError:
        return None

    val = "{0:.15f}".format(val * 1.0 * getPrefix(prefix))

    return (val, getUnit(units))


def componentValue(valString, reference):
    # type: (str, str) -> tuple
    result = compMatch(valString)

    if not result:
        return valString, None  # return the same string back with `None` unit

    if not len(result) == 2:  # result length is incorrect
        return valString, None  # return the same string back with `None` unit

    if result[1] is None:
        # try to infer unit from reference
        match = REFERENCE_REGEX.match(reference.lower())
        if match and len(match.groups()) == 2:
            prefix, _ = match.groups()
            unit = None
            if prefix in ['r', 'rv']:
                unit = 'R'
            if prefix == 'c':
                unit = 'F'
            if prefix == 'l':
                unit = 'H'
            result = (result[0], unit)

    return result  # (val,unit)


def compareValues(c1, c2):
    r1 = compMatch(c1)
    r2 = compMatch(c2)

    if not r1 or not r2:
        return False

    (v1, u1) = r1
    (v2, u2) = r2

    if v1 == v2:
        # values match
        if u1 == u2:
            return True  # units match
        if not u1:
            return True  # no units for component 1
        if not u2:
            return True  # no units for component 2

    return False
