import re


class PatternReplacer:
    def __init__(self, samplepattern, delimiters):
        self.spans = []
        self.delims = []
        regex_inner = '|'.join([re.escape(d) for d in delimiters])
        self.regex = re.compile('((%s)+)' % regex_inner)
        for m in self.regex.finditer(samplepattern):
            self.delims.append(m.groups()[0])
            self.spans.append(m.span())

        if len(self.spans) == 0:
            self.begins_with_delimiter = False
            self.ends_with_delimiter = False
            return

        self.begins_with_delimiter = False
        if self.spans[0][0] == 0:
            self.begins_with_delimiter = True

        self.ends_with_delimiter = False
        if self.spans[-1][-1] == len(samplepattern):
            self.ends_with_delimiter = True

    def get_n_delimiters(self):
        return len(self.delims)

    def verify(self, pattern):
        delims = []
        spans = []
        for m in self.regex.finditer(pattern):
            delims.append(m.groups()[0])
            spans.append(m.span())

        if delims != self.delims:
            return False

        if spans == self.spans:
            # this is especially true for self.spans = []
            return True

        if spans[0][0] == 0 and not self.begins_with_delimiter:
            return False

        if spans[-1][-1] == len(pattern) and not self.ends_with_delimiter:
            return False

        return True

    def get_n_tokens(self):
        return len(self.delims) + 1 - int(self.begins_with_delimiter) - int(self.ends_with_delimiter)

    def replace(self, tokens):
        assert len(tokens) == self.get_n_tokens(), self.get_n_tokens()

        # copy
        delims = [d for d in self.delims]
        delims.append('')
        out = ''
        if self.begins_with_delimiter:
            out += delims[0]

        for i, t in enumerate(tokens, start=int(self.begins_with_delimiter)):
            out += t
            out += delims[i]
        return out

