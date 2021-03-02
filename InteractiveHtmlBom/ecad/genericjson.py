import io
import json
from jsonschema import validate, ValidationError

from .common import EcadParser, Component, BoundingBox


class GenericJsonParser(EcadParser):
    COMPATIBLE_SPEC_VERSIONS = [1]

    def get_generic_json_pcb(self):
        from os import path
        with io.open(self.file_name, 'r', encoding='utf-8') as f:
            pcb = json.load(f)

        if 'spec_version' not in pcb:
            raise ValidationError("'spec_version' is a required property")

        if pcb['spec_version'] not in self.COMPATIBLE_SPEC_VERSIONS:
            raise ValidationError("Unsupported spec_version ({})"
                                  .format(pcb['spec_version']))

        schema_dir = path.join(path.dirname(__file__), 'schema')
        schema_file_name = path.join(schema_dir,
                                     'genericjsonpcbdata_v{}.schema'
                                     .format(pcb['spec_version']))

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

    def parse(self):
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

        self.logger.info('Successfully parsed {}'.format(self.file_name))

        pcbdata = pcb['pcbdata']
        components = [Component(**c) for c in pcb['components']]

        # override board bounding box based on edges
        board_outline_bbox = BoundingBox()
        for drawing in pcbdata['edges']:
            self.add_drawing_bounding_box(drawing, board_outline_bbox)
        if board_outline_bbox.initialized():
            pcbdata['edges_bbox'] = board_outline_bbox.to_dict()

        if self.config.extra_fields:
            for c in components:
                extra_field_data = {}
                for f in self.config.extra_fields:
                    fv = ("" if f not in c.extra_fields else c.extra_fields[f])
                    extra_field_data[f] = fv
                c.extra_fields = extra_field_data

        return pcbdata, components
