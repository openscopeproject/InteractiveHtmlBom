class EcadParser(object):

    def __init__(self, file_name, logger):
        """
        :param file_name: path to file that should be parsed.
        :param logger: logging object.
        """
        self.file_name = file_name
        self.logger = logger
        self.extra_data_func = lambda f, b: ([], {})
        self.latest_extra_data = None

    def parse(self):
        """
        Abstract method that should be overridden in implementations.
        Performs all the parsing and returns a tuple of (pcbdata, components)
        pcbdata is described in DATAFORMAT.md
        components is list of Component objects
        :return:
        """
        pass


class Component(object):
    """Simple data object to store component data needed for bom table."""

    def __init__(self, ref, val, footprint, layer, attr=None):
        self.ref = ref
        self.val = val
        self.footprint = footprint
        self.layer = layer
        self.attr = attr
