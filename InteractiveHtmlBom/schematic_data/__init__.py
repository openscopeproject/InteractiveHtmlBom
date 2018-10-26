import os

from xmlparser import XmlParser
from netlistparser import NetlistParser

PARSERS = {
    '.xml': XmlParser,
    '.net': NetlistParser
}


def parse_schematic_data(file_name):
    if not os.path.isfile(file_name):
        return None
    extension = os.path.splitext(file_name)[1]
    if extension not in PARSERS:
        return None
    else:
        parser = PARSERS[extension](file_name)
        return parser.get_extra_field_data()


def find_latest_schematic_data(dir):
    """
    :param dir: directory of the pcb file
    :return: last modified parsable file path or None if not found
    """
    _, _, files = next(os.walk(dir), (None, None, []))
    # filter out files that we can parse
    files = [f for f in files if os.path.splitext(f)[1] in PARSERS.keys()]
    # get their mtime and pick the latest one
    files = [(os.path.getmtime(os.path.join(dir, f)), f) for f in files]
    print files
    if files:
        return os.path.join(dir, sorted(files, reverse=True)[0][1])
    else:
        return None
