import os

from xmlparser import XmlParser

PARSERS = {
    'xml': XmlParser
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
