import io

from .parser_base import ParserBase
from .sexpressions import parse_sexpression


class NetlistParser(ParserBase):
    def get_extra_field_data(self):
        with io.open(self.file_name, 'r', encoding='utf-8') as f:
            sexpression = parse_sexpression(f.read())
        components = None
        for s in sexpression:
            if s[0] == 'components':
                components = s[1:]
        if components is None:
            return None
        field_set = set()
        comp_dict = {}
        for c in components:
            ref = None
            fields = None
            datasheet = None
            libsource = None
            for f in c[1:]:
                if f[0] == 'ref':
                    ref = f[1]
                if f[0] == 'fields':
                    fields = f[1:]
                if f[0] == 'datasheet':
                    datasheet = f[1]
                if f[0] == 'libsource':
                    libsource = f[1:]
            if ref is None:
                return None
            ref_fields = comp_dict.setdefault(ref, {})
            if datasheet and datasheet != '~':
                field_set.add('Datasheet')
                ref_fields['Datasheet'] = datasheet
            if libsource is not None:
                for lib_field in libsource:
                    if lib_field[0] == 'description':
                        field_set.add('Description')
                        ref_fields['Description'] = lib_field[1]
            if fields is None:
                continue
            for f in fields:
                if len(f) > 1:
                    field_set.add(f[1][1])
                if len(f) > 2:
                    ref_fields[f[1][1]] = f[2]

        return list(field_set), comp_dict
