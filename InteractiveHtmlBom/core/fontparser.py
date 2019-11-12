from .newstroke_font import NEWSTROKE_FONT


class FontParser:
    STROKE_FONT_SCALE = 1.0 / 21.0
    FONT_OFFSET = -10

    def __init__(self):
        self.parsed_font = {}

    def parse_font_char(self, chr):
        lines = []
        line = []
        glyph_x = 0
        index = ord(chr) - ord(' ')
        if index >= len(NEWSTROKE_FONT):
            index = ord('?') - ord(' ')
        glyph_str = NEWSTROKE_FONT[index]
        for i in range(0, len(glyph_str), 2):
            coord = glyph_str[i:i + 2]

            # The first two values contain the width of the char
            if i < 2:
                glyph_x = (ord(coord[0]) - ord('R')) * self.STROKE_FONT_SCALE
                glyph_width = (ord(coord[1]) - ord(coord[0])) * self.STROKE_FONT_SCALE
            elif coord[0] == ' ' and coord[1] == 'R':
                lines.append(line)
                line = []
            else:
                line.append([
                    (ord(coord[0]) - ord('R')) * self.STROKE_FONT_SCALE - glyph_x,
                    (ord(coord[1]) - ord('R') + self.FONT_OFFSET) * self.STROKE_FONT_SCALE
                ])

        if len(line) > 0:
            lines.append(line)

        return {
            'w': glyph_width,
            'l': lines
        }

    def parse_font_for_string(self, s):
        for c in s:
            if c == '\t' and ' ' not in self.parsed_font:
                # tabs rely on space char to calculate offset
                self.parsed_font[' '] = self.parse_font_char(' ')
            if c not in self.parsed_font and ord(c) >= ord(' '):
                self.parsed_font[c] = self.parse_font_char(c)

    def get_parsed_font(self):
        return self.parsed_font
