import io
import json
import os.path
from jsonschema import validate, ValidationError

from .common import EcadParser, Component, BoundingBox
from ..core.fontparser import FontParser
from ..errors import ParsingException


class GenericJsonParser(EcadParser):
    COMPATIBLE_SPEC_VERSIONS = [1]

    def extra_data_file_filter(self):
        return "Json file ({f})|{f}".format(f=os.path.basename(self.file_name))

    def latest_extra_data(self, extra_dirs=None):
        return self.file_name

    def get_extra_field_data(self, file_name):
        if os.path.abspath(file_name) != os.path.abspath(self.file_name):
            return None

        _, components = self._parse()
        field_set = set()
        comp_dict = {}

        for c in components:
            ref_fields = comp_dict.setdefault(c.ref, {})

            for k, v in c.extra_fields.items():
                field_set.add(k)
                ref_fields[k] = v

        return list(field_set), comp_dict

    def get_generic_json_pcb(self):
        with io.open(self.file_name, 'r', encoding='utf-8') as f:
            pcb = json.load(f)

        if 'spec_version' not in pcb:
            raise ValidationError("'spec_version' is a required property")

        if pcb['spec_version'] not in self.COMPATIBLE_SPEC_VERSIONS:
            raise ValidationError("Unsupported spec_version ({})"
                                  .format(pcb['spec_version']))

        schema_dir = os.path.join(os.path.dirname(__file__), 'schema')
        schema_file_name = os.path.join(schema_dir,
                                        'genericjsonpcbdata_v{}.schema'.format(
                                            pcb['spec_version']))

        with io.open(schema_file_name, 'r', encoding='utf-8') as f:
            schema = json.load(f)

        validate(instance=pcb, schema=schema)

        return pcb

    def _verify(self, pcb):
        """Spot check the pcb object."""

        if len(pcb['pcbdata']['footprints']) != len(pcb['components']):
            self.logger.error("Length of components list doesn't match"
                              " length of footprints list.")
            return False

        return True

    @staticmethod
    def _texts(pcbdata):
        for layer in pcbdata['drawings'].values():
            for side in layer.values():
                for dwg in side:
                    if 'text' in dwg:
                        yield dwg

    @staticmethod
    def _remove_control_codes(s):
        import unicodedata
        return ''.join(c for c in s if unicodedata.category(c)[0] != "C")

    def _parse_font_data(self, pcbdata):
        font_parser = FontParser()
        for dwg in self._texts(pcbdata):
            if 'svgpath' not in dwg:
                dwg['text'] = self._remove_control_codes(dwg['text'])
                font_parser.parse_font_for_string(dwg['text'])

        if font_parser.get_parsed_font():
            pcbdata['font_data'] = font_parser.get_parsed_font()

    def _check_font_data(self, pcbdata):
        mc = set()
        for dwg in self._texts(pcbdata):
            dwg['text'] = self._remove_control_codes(dwg['text'])
            mc.update({c for c in dwg['text'] if 'svgpath' not in dwg and
                      c not in pcbdata['font_data']})

        if mc:
            s = ''.join(mc)
            self.logger.error('Provided font_data is missing character(s)'
                              f' "{s}" that are present in text drawing'
                              ' objects')
            return False
        else:
            return True

    def _parse(self):
        try:
            pcb = self.get_generic_json_pcb()
        except ValidationError as e:
            self.logger.error('File {f} does not comply with json schema. {m}'
                              .format(f=self.file_name, m=e.message))
            return None, None

        if not self._verify(pcb):
            self.logger.error('File {} does not appear to be valid generic'
                              ' InteractiveHtmlBom json file.'
                              .format(self.file_name))
            return None, None

        pcbdata = pcb['pcbdata']
        components = [Component(**c) for c in pcb['components']]

        if 'font_data' in pcbdata:
            if not self._check_font_data(pcbdata):
                raise ParsingException(f'Failed parsing {self.file_name}')
        else:
            self._parse_font_data(pcbdata)
            if 'font_data' in pcbdata:
                self.logger.info('No font_data provided in JSON, using '
                                 'newstroke font')

        self.logger.info('Successfully parsed {}'.format(self.file_name))

        return pcbdata, components

    def parse(self):
        pcbdata, components = self._parse()

        # override board bounding box based on edges
        board_outline_bbox = BoundingBox()
        for drawing in pcbdata['edges']:
            self.add_drawing_bounding_box(drawing, board_outline_bbox)
        if board_outline_bbox.initialized():
            pcbdata['edges_bbox'] = board_outline_bbox.to_dict()

        extra_fields = set(self.config.show_fields)
        extra_fields.discard("Footprint")
        extra_fields.discard("Value")
        if self.config.dnp_field:
            extra_fields.add(self.config.dnp_field)
        if self.config.board_variant_field:
            extra_fields.add(self.config.board_variant_field)
        if extra_fields:
            for c in components:
                c.extra_fields = {
                    f: c.extra_fields.get(f, "") for f in extra_fields}

        self.config.kicad_text_formatting = False

        return pcbdata, components
