class ParserBase:
    DEFAULT_FIELDS = []

    def __init__(self, file_name):
        """
        :param file_name: path to file that should be parsed.
        """
        self.file_name = file_name

    @staticmethod
    def normalize_field_names(data):
        field_map = {f.lower(): f for f in reversed(data[0])}

        def remap(ref_fields):
            return {field_map[f.lower()]: v for (f, v) in
                    sorted(ref_fields.items(), reverse=True)}

        field_data = {r: remap(d) for (r, d) in data[1].items()}
        return field_map.values(), field_data

    def parse(self, normalize_case):
        data = self.get_extra_field_data()
        if normalize_case:
            data = self.normalize_field_names(data)
        return sorted(data[0]), data[1]

    def get_extra_field_data(self):
        # type: () -> tuple
        """
        Parses the file and returns a extra field data.
        :return: tuple of the format
            (
                [field_name1, field_name2,... ],
                {
                    ref1: {
                        field_name1: field_value1,
                        field_name2: field_value2,
                        ...
                    ],
                    ref2: ...
                }
            )
        """
        pass
