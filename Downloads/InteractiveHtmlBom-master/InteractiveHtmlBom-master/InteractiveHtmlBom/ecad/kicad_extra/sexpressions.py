import re

term_regex = r'''(?mx)
    \s*(?:
        (?P<open>\()|
        (?P<close>\))|
        (?P<sq>"(?:\\\\|\\"|[^"])*")|
        (?P<s>[^(^)\s]+)
       )'''
pattern = re.compile(term_regex)


def parse_sexpression(sexpression):
    stack = []
    out = []
    for terms in pattern.finditer(sexpression):
        term, value = [(t, v) for t, v in terms.groupdict().items() if v][0]
        if term == 'open':
            stack.append(out)
            out = []
        elif term == 'close':
            assert stack, "Trouble with nesting of brackets"
            tmp, out = out, stack.pop(-1)
            out.append(tmp)
        elif term == 'sq':
            out.append(value[1:-1].replace('\\\\', '\\').replace('\\"', '"'))
        elif term == 's':
            out.append(value)
        else:
            raise NotImplementedError("Error: %s, %s" % (term, value))
    assert not stack, "Trouble with nesting of brackets"
    return out[0]
