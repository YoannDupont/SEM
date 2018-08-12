# -*- coding: utf-8 -*-

"""
file: keyIO.py

Description: an IO module for CoNLL-formatted files when column
identifiers are available.

author: Yoann Dupont

MIT License

Copyright (c) 2018 Yoann Dupont

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from sem import PY2

import codecs

class KeyReader(object):
    def __init__(self, name, encoding, keys, cleaner=(unicode.strip if PY2 else str.strip), splitter=(unicode.split if PY2 else str.strip)):
        self._name     = name
        self._encoding = encoding
        self._keys     = keys
        self._cleaner  = cleaner
        self._splitter = splitter
        self._length   = None
        
        if not self._keys:
            raise ValueError("Cannot give empty key set to KeyReader object.")
        if None == self._cleaner:
            self._cleaner = unicode.strip
        if None == self._splitter:
            self._splitter = unicode.split
        
        # The following instructions will raise an exception if they are not callable.
        self._cleaner.__call__
        self._splitter.__call__
    
    @staticmethod
    def identity(obj):
        return obj
    
    def __iter__(self):
        paragraph = []
        for line in codecs.open(self._name, "rU", self._encoding):
            line  = self._cleaner(line)
            if line != "":
                line = dict(zip(self._keys, self._splitter(line)))
                paragraph.append(line)
            elif paragraph != []:
                yield paragraph
                del paragraph[:]
        if paragraph != []:
            yield paragraph
    
    @property
    def length(self):
        if self._length is None:
            self._length = 0
            for x in self:
                self._length += 1
        return self._length


class KeyWriter(object):
    def __init__(self, name, encoding, keys, joiner="\t"):
        self._name     = name
        self._encoding = encoding
        self._keys     = keys
        self._joiner   = joiner
        self._fd       = codecs.open(self._name, "w", self._encoding)
        
        if None == self._joiner:
            self._joiner = ""
        
        self._format = self._joiner.join([u"{{{0}}}".format(key) for key in self._keys])
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, exc_tb):
        self._fd.close()
    
    def write(self, entries):
        for p in entries:
            for l in p:
                self._fd.write(self._format.format(**l))
                self._fd.write(u"\n")
            self._fd.write(u"\n")
    
    def write_p(self, p):
        for l in p:
            self._fd.write(self._format.format(**l))
            self._fd.write(u"\n")
        self._fd.write(u"\n")
    
    def write_l(self, l):
        self._fd.write(self._format.format(**l))
        self._fd.write(u"\n")
    
    def close(self):
        self._fd.close()
