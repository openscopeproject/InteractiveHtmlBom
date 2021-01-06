import io
import json
from jsonschema import validate, ValidationError

from .common import EcadParser, Component


class GenericJsonParser(EcadParser):
    COMPATIBLE_SPEC_VERSIONS = [1]

    def get_generic_json_pcb(self):
        from os import path
        with io.open(self.file_name, 'r') as f:
            pcb = json.load(f)

        if '_spec_version' not in pcb:
            raise ValidationError("'_spec_version' is a required property")

        if pcb['_spec_version'] not in self.COMPATIBLE_SPEC_VERSIONS:
            raise ValidationError("Unsupported _spec_version ({})"
                                  .format(pcb['_spec_version']))

        schema_dir = path.join(path.dirname(__file__), 'schema')
        if pcb['_spec_version'] == 1:
            schema_file_name = path.join(schema_dir,
                                         'genericjsonpcbdata_v{}.schema'
                                         .format(pcb['_spec_version']))

        with io.open(schema_file_name, 'r') as f:
            schema = json.load(f)

        validate(instance=pcb, schema=schema)

        return pcb

    def _verify(self, pcb):

        """Spot check the pcb object."""

        if len(pcb['pcbdata']['footprints']) != len(pcb['components']):
            self.logger.error("length of components list doesn't match"
                              " length of footprints list")
            return False

        return True

    def parse(self):
        try:
            pcb = self.get_generic_json_pcb()
        except ValidationError as e:
            self.logger.error(e.message)
            return None, None

        if not self._verify(pcb):
            self.logger.error('File {} does not appear to be valid generic'
                              ' InteractiveHtmlBom json file.'
                              .format(self.file_name))
            return None, None

        self.logger.info('Successfully parsed {}'.format(self.file_name))

        pcbdata = pcb['pcbdata']
        components = [Component(**c) for c in pcb['components']]

        return pcbdata, components
