from xml.dom import minidom

from .parser_base import ParserBase


class XmlParser(ParserBase):
    @staticmethod
    def get_text(nodelist):
        rc = []
        for node in nodelist:
            if node.nodeType == node.TEXT_NODE:
                rc.append(node.data)
        return ''.join(rc)

    def get_extra_field_data(self):
        xml = minidom.parse(self.file_name)
        components = xml.getElementsByTagName('comp')
        field_set = set()
        comp_dict = {}
        for c in components:
            ref_fields = comp_dict.setdefault(c.attributes['ref'].value, {})
            for f in c.getElementsByTagName('field'):
                name = f.attributes['name'].value
                if name not in self.DEFAULT_FIELDS:
                    field_set.add(name)
                    ref_fields[name] = self.get_text(f.childNodes)

        return list(field_set), comp_dict
