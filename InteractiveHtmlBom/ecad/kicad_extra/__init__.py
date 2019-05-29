import os

from .xmlparser import XmlParser
from .netlistparser import NetlistParser

PARSERS = {
    '.xml': XmlParser,
    '.net': NetlistParser
}


def parse_schematic_data(file_name, normalize_case):
    if not os.path.isfile(file_name):
        return None
    extension = os.path.splitext(file_name)[1]
    if extension not in PARSERS:
        return None
    else:
        parser = PARSERS[extension](file_name)
        return parser.parse(normalize_case)


def find_latest_schematic_data(base_name, directories):
    """
    :param base_name: base name of pcb file
    :param directories: list of directories to search
    :return: last modified parsable file path or None if not found
    """
    for dir in directories:
        f = _find_in_dir(base_name, dir)
        if f:
            return f
    return None


def _find_in_dir(base_name, dir):
    _, _, files = next(os.walk(dir), (None, None, []))
    # filter out files that we can not parse
    files = [f for f in files if os.path.splitext(f)[1] in PARSERS.keys()]
    # get their modification time and sort in descending order
    files = [(os.path.getmtime(os.path.join(dir, f)), f) for f in files]
    files = sorted(files, reverse=True)
    if files:
        # try to find first (last modified) file that has name matching pcb file
        for _, f in files:
            if os.path.splitext(f)[0] == base_name:
                return os.path.join(dir, f)
        # if no such file is found just return last modified
        return os.path.join(dir, files[0][1])
    else:
        return None
