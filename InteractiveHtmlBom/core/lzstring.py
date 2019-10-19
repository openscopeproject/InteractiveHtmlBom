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
        pass

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

    @staticmethod
    def compress_to_utf16(string):

        if string is None:
            return ''

        output = ''
        current = 0
        status = 0

        string = LZString.compress(string)

        for i in range(len(string)):
            c = ord(string[i])

            if status == 0:
                status += 1
                output += unichr(((c >> 1) + 32))
                current = (c & 1) << 14
            elif status == 1:
                status += 1
                output += unichr(((current + (c >> 2)) + 32))
                current = (c & 3) << 13
            elif status == 2:
                status += 1
                output += unichr(((current + (c >> 3)) + 32))
                current = (c & 7) << 12
            elif status == 3:
                status += 1
                output += unichr(((current + (c >> 4)) + 32))
                current = (c & 15) << 11
            elif status == 4:
                status += 1
                output += unichr(((current + (c >> 5)) + 32))
                current = (c & 31) << 10
            elif status == 5:
                status += 1
                output += unichr(((current + (c >> 6)) + 32))
                current = (c & 63) << 9
            elif status == 6:
                status += 1
                output += unichr(((current + (c >> 7)) + 32))
                current = (c & 127) << 8
            elif status == 7:
                status += 1
                output += unichr(((current + (c >> 8)) + 32))
                current = (c & 255) << 7
            elif status == 8:
                status += 1
                output += unichr(((current + (c >> 9)) + 32))
                current = (c & 511) << 6
            elif status == 9:
                status += 1
                output += unichr(((current + (c >> 10)) + 32))
                current = (c & 1023) << 5
            elif status == 10:
                status += 1
                output += unichr(((current + (c >> 11)) + 32))
                current = (c & 2047) << 4
            elif status == 11:
                status += 1
                output += unichr(((current + (c >> 12)) + 32))
                current = (c & 4095) << 3
            elif status == 12:
                status += 1
                output += unichr(((current + (c >> 13)) + 32))
                current = (c & 8191) << 2
            elif status == 13:
                status += 1
                output += unichr(((current + (c >> 14)) + 32))
                current = (c & 16383) << 1
            elif status == 14:
                status += 1
                output += unichr(((current + (c >> 15)) + 32))
                output += unichr((c & 32767) + 32)

                status = 0

        output += unichr(current + 32)

        return output
