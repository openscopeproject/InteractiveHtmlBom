import io
import json

from .common import EcadParser, Component


class GenericJsonParser(EcadParser):
    class GenericJsonDecoder(json.JSONDecoder):
        COMPATIBLE_SPEC_VERSIONS = [1]

        class GenericJsonDecodeException(Exception):
            def __init__(self, message):
                self.message = message

        def __init__(self, *args, **kwargs):
            json.JSONDecoder.__init__(self,
                                      object_hook=self.object_hook,
                                      *args,
                                      **kwargs)

        class GenericJsonDecodeException(Exception):
            def __init__(self, message):
                self.message = message

        def object_hook(self, obj):
            if ('_type' in obj
                    and obj['_type'] == 'interactivehtmlbom components'):
                if ('_spec_version' in obj
                        and obj['_spec_version']
                        in self.COMPATIBLE_SPEC_VERSIONS):
                    if obj['_spec_version'] == 1:
                        return [Component(c['ref'],
                                          c['val'],
                                          c['footprint'],
                                          c['layer'],
                                          c['attr'])
                                for c in obj['object']]
                else:
                    v = None if '_spec_version' not in obj \
                             else obj['_spec_version']
                    raise self.GenericJsonDecodeException(
                        'components object spec version ('
                        + str(v)
                        + ') not supported')

            elif ('_type' in obj and
                  obj['_type'] == 'interactivehtmlbom pcbdata'):
                if ('_spec_version' in obj
                        and obj['_spec_version']
                        in self.COMPATIBLE_SPEC_VERSIONS):
                    if obj['_spec_version'] == 1:
                        return obj['object']
                else:
                    v = None if '_spec_version' not in obj \
                        else obj['_spec_version']
                    raise self.GenericJsonDecodeException(
                        'pcbdata object spec version ('
                        + str(v)
                        + ') not supported')

            else:
                return obj

    def get_generic_json_pcb(self):
        with io.open(self.file_name, 'r') as f:
            return json.load(f, cls=self.GenericJsonDecoder)

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

        if type(p) != dict or len(p) != 8:
            self.logger.error('invalid pcbdata object')
            return False

        if type(c) != list:
            self.logger.error('invalid components object')
            return False

        if 'footprints' not in p or len(p['footprints']) != len(c):
            self.logger.error("length of components list doesn't match"
                              " length of footprints list")
            return False

        return True

    def parse(self):
        try:
            pcb = self.get_generic_json_pcb()
        except self.GenericJsonDecoder.GenericJsonDecodeException as exc:
            self.logger.error("while parsing JSON: " + exc.message)
            return None, None

        if not self._verify(pcb):
            self.logger.error('File ' + self.file_name +
                              ' does not appear to be valid generic'
                              ' interactivehtmlbom json file.')
            return None, None

        self.logger.info('Successfully parsed ' + self.file_name)

        return pcb['pcbdata'], pcb['components']
