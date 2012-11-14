import codecs

class ICorpus(object):

    def __init__(self, filename, encoding="UTF-8"):
        self.filename = filename
        self.encoding = encoding
        self._size    = None

    def __iter__(self):
        skipping = True
        entry = []
        for line in codecs.open(self.filename, "rU", self.encoding):
            line = line.strip()
            if not line:
                if entry:
                    yield tuple(entry)
                    del entry[:]
            else:
                entry.append(line)
        if entry:
            yield tuple(entry)

    @property
    def size(self):
        n = self._size
        if n is None:
            n = 0
            for x in self:
                n += 1
        return n

class OCorpus(object):

    def __init__(self, filename, encoding="UTF-8"):
        self._fd = codecs.open(filename, "w", encoding)
        self.bof = True

    def close(self):
        self._fd.close()
        self._fd = None

    def put(self, entry):
        if self.bof:
            self.bof = False
        else:
            self._fd.write(u"\n")
        for line in entry:
            self._fd.write(line)
            self._fd.write(u"\n")

    def put_concise(self, entry):
        if self.bof:
            self.bof = False
        else:
            self._fd.write(u"\n")
        self._fd.write(u"\n".join(entry))

    def putformat(self, entry, format):
        if self.bof:
            self.bof = False
        else:
            self._fd.write(u"\n")
        for line in entry:
            self._fd.write(format %line)
            self._fd.write(u"\n")
