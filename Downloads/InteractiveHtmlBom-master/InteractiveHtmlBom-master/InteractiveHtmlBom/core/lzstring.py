"""
Copyright 2014 Eduard Tomasek
This work is free. You can redistribute it and/or modify it under the
terms of the Do What The Fuck You Want To Public License, Version 2,
as published by Sam Hocevar. See the COPYING file for more details.
"""
import sys
if sys.version_info[0] == 3:
    unichr = chr


class LZString:

    def __init__(self):
        self.keyStr = (
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
        )

    @staticmethod
    def compress(uncompressed):

        if uncompressed is None:
            return ''

        context_dictionary = {}
        context_dictionary_to_create = {}
        context_w = ''
        context_enlarge_in = 2

        context_dict_size = 3
        context_num_bits = 2
        context_data_string = ''
        context_data_val = 0
        context_data_position = 0

        uncompressed = uncompressed

        for ii in range(len(uncompressed)):
            context_c = uncompressed[ii]

            if context_c not in context_dictionary:
                context_dictionary[context_c] = context_dict_size
                context_dict_size += 1
                context_dictionary_to_create[context_c] = True

            context_wc = context_w + context_c

            if context_wc in context_dictionary:
                context_w = context_wc
            else:
                if context_w in context_dictionary_to_create:
                    if ord(context_w[0]) < 256:
                        for _ in range(context_num_bits):
                            context_data_val = (context_data_val << 1)

                            if context_data_position == 15:
                                context_data_position = 0
                                context_data_string += unichr(context_data_val)
                                context_data_val = 0
                            else:
                                context_data_position += 1

                        value = ord(context_w[0])

                        for i in range(8):
                            context_data_val = (
                                (context_data_val << 1) | (value & 1)
                            )

                            if context_data_position == 15:
                                context_data_position = 0
                                context_data_string += unichr(context_data_val)
                                context_data_val = 0
                            else:
                                context_data_position += 1

                            value = value >> 1
                    else:
                        value = 1

                        for i in range(context_num_bits):
                            context_data_val = (context_data_val << 1) | value

                            if context_data_position == 15:
                                context_data_position = 0
                                context_data_string += unichr(context_data_val)
                                context_data_val = 0
                            else:
                                context_data_position += 1

                            value = 0

                        value = ord(context_w[0])

                        for i in range(16):
                            context_data_val = (
                                (context_data_val << 1) | (value & 1)
                            )

                            if context_data_position == 15:
                                context_data_position = 0
                                context_data_string += unichr(context_data_val)
                                context_data_val = 0
                            else:
                                context_data_position += 1

                            value = value >> 1

                    context_enlarge_in -= 1

                    if context_enlarge_in == 0:
                        context_enlarge_in = pow(2, context_num_bits)
                        context_num_bits += 1

                    context_dictionary_to_create.pop(context_w, None)
                    # del context_dictionary_to_create[context_w]
                else:
                    value = context_dictionary[context_w]

                    for i in range(context_num_bits):
                        context_data_val = (
                            (context_data_val << 1) | (value & 1)
                        )

                        if context_data_position == 15:
                            context_data_position = 0
                            context_data_string += unichr(context_data_val)
                            context_data_val = 0
                        else:
                            context_data_position += 1

                        value = value >> 1

                context_enlarge_in -= 1

                if context_enlarge_in == 0:
                    context_enlarge_in = pow(2, context_num_bits)
                    context_num_bits += 1

                context_dictionary[context_wc] = context_dict_size
                context_dict_size += 1
                context_w = context_c
        if context_w != '':
            if context_w in context_dictionary_to_create:
                if ord(context_w[0]) < 256:
                    for i in range(context_num_bits):
                        context_data_val = (context_data_val << 1)

                        if context_data_position == 15:
                            context_data_position = 0
                            context_data_string += unichr(context_data_val)
                            context_data_val = 0
                        else:
                            context_data_position += 1

                    value = ord(context_w[0])

                    for i in range(8):
                        context_data_val = (
                            (context_data_val << 1) | (value & 1)
                        )

                        if context_data_position == 15:
                            context_data_position = 0
                            context_data_string += unichr(context_data_val)
                            context_data_val = 0
                        else:
                            context_data_position += 1

                        value = value >> 1
                else:
                    value = 1

                    for i in range(context_num_bits):
                        context_data_val = (context_data_val << 1) | value

                        if context_data_position == 15:
                            context_data_position = 0
                            context_data_string += unichr(context_data_val)
                            context_data_val = 0
                        else:
                            context_data_position += 1

                        value = 0

                    value = ord(context_w[0])

                    for i in range(16):
                        context_data_val = (
                            (context_data_val << 1) | (value & 1)
                        )

                        if context_data_position == 15:
                            context_data_position = 0
                            context_data_string += unichr(context_data_val)
                            context_data_val = 0
                        else:
                            context_data_position += 1

                        value = value >> 1

                context_enlarge_in -= 1

                if context_enlarge_in == 0:
                    context_enlarge_in = pow(2, context_num_bits)
                    context_num_bits += 1

                context_dictionary_to_create.pop(context_w, None)
                # del context_dictionary_to_create[context_w]
            else:
                value = context_dictionary[context_w]

                for i in range(context_num_bits):
                    context_data_val = (context_data_val << 1) | (value & 1)

                    if context_data_position == 15:
                        context_data_position = 0
                        context_data_string += unichr(context_data_val)
                        context_data_val = 0
                    else:
                        context_data_position += 1

                    value = value >> 1

            context_enlarge_in -= 1

            if context_enlarge_in == 0:
                context_num_bits += 1

        value = 2

        for i in range(context_num_bits):
            context_data_val = (context_data_val << 1) | (value & 1)

            if context_data_position == 15:
                context_data_position = 0
                context_data_string += unichr(context_data_val)
                context_data_val = 0
            else:
                context_data_position += 1

            value = value >> 1

        context_data_val = (context_data_val << 1)
        while context_data_position != 15:
            context_data_position += 1
            context_data_val = (context_data_val << 1)
        context_data_string += unichr(context_data_val)

        return context_data_string

    def compress_to_base64(self, string):
        if string is None:
            return ''

        output = ''

        string = self.compress(string)
        str_len = len(string)

        for i in range(0, str_len * 2, 3):
            if (i % 2) == 0:
                chr1 = ord(string[i // 2]) >> 8
                chr2 = ord(string[i // 2]) & 255

                if (i / 2) + 1 < str_len:
                    chr3 = ord(string[(i // 2) + 1]) >> 8
                else:
                    chr3 = None
            else:
                chr1 = ord(string[(i - 1) // 2]) & 255
                if (i + 1) / 2 < str_len:
                    chr2 = ord(string[(i + 1) // 2]) >> 8
                    chr3 = ord(string[(i + 1) // 2]) & 255
                else:
                    chr2 = None
                    chr3 = None

            # python dont support bit operation with NaN like javascript
            enc1 = chr1 >> 2
            enc2 = (
                ((chr1 & 3) << 4) |
                (chr2 >> 4 if chr2 is not None else 0)
            )
            enc3 = (
                ((chr2 & 15 if chr2 is not None else 0) << 2) |
                (chr3 >> 6 if chr3 is not None else 0)
            )
            enc4 = (chr3 if chr3 is not None else 0) & 63

            if chr2 is None:
                enc3 = 64
                enc4 = 64
            elif chr3 is None:
                enc4 = 64

            output += (
                self.keyStr[enc1] +
                self.keyStr[enc2] +
                self.keyStr[enc3] +
                self.keyStr[enc4]
            )

        return output
