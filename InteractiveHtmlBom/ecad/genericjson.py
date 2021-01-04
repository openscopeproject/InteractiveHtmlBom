import io
import json

from .common import EcadParser, Component


class GenericJsonParser(EcadParser):
    COMPATIBLE_SPEC_VERSIONS = [1]

    def get_generic_json_pcb(self):
        with io.open(self.file_name, 'r') as f:
            return json.load(f)

    def _verify(self, pcb):

        """Spot check the pcb object."""
        if 'pcbdata' not in pcb:
            self.logger.error('No pcbdata object')
            return False
        p = pcb['pcbdata']

        if 'components' not in pcb:
            self.logger.error('No components object')
            return False
        c = pcb['components']

        if pcb['_spec_version'] not in self.COMPATIBLE_SPEC_VERSIONS:
            self.logger.error('Unsupported spec version (%s)'
                              .format(pcb['_spec_version']))
            return False

        if 'footprints' not in p or len(p['footprints']) != len(c):
            self.logger.error("length of components list doesn't match"
                              " length of footprints list")
            return False

        return True

    def parse(self):
        pcb = self.get_generic_json_pcb()

        if not self._verify(pcb):
            self.logger.error('File %s does not appear to be valid generic'
                              ' InteractiveHtmlBom json file.'
                              .format(self.file_name))
            return None, None

        self.logger.info('Successfully parsed %s'.format(self.file_name))

        pcbdata = pcb['pcbdata']
        components = [Component(**c) for c in pcb['components']]

        return pcbdata, components
