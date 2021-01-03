import io
import json

from .common import EcadParser, Component


class EagleParser(EcadParser):

    class EagleJsonDecoder(json.JSONDecoder):
        def __init__(self, *args, **kwargs):
            json.JSONDecoder.__init__(self,
                                      object_hook=self.object_hook,
                                      *args,
                                      **kwargs)

        def object_hook(self, obj):
            if '_type' in obj and obj['_type'] == \
                    'InteractiveHtmlBom.ecad.common.Component':
                return [Component(c['ref'],
                                  c['val'],
                                  c['footprint'],
                                  c['layer'],
                                  c['attr'])
                        for c in obj['object']]
            else:
                return obj

    def get_eagle_pcb(self):
        with io.open(self.file_name, 'r') as f:
            return json.load(f, cls=self.EagleJsonDecoder)

    def _verify(self, pcb):

        """Spot check the pcb object."""
        if 'pcbdata' not in pcb:
            self.logger.error('No pcbdata object.')
            return False

        if 'components' not in pcb:
            self.logger.error('No components object.')
            return False

        return True

    def parse(self):
        pcb = self.get_eagle_pcb()
        if not self._verify(pcb):
            self.logger.error('File ' + self.file_name +
                              ' does not appear to be valid Eagle json file.')
            return None, None

        return pcb['pcbdata'], pcb['components']
