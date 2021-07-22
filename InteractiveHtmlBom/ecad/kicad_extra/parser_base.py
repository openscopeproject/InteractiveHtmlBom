class ParserBase:

    def __init__(self, file_name):
        """
        :param file_name: path to file that should be parsed.
        """
        self.file_name = file_name

    def get_extra_field_data(self):
        # type: () -> tuple
        """
        Parses the file and returns extra field data.
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
