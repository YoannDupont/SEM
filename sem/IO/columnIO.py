# -*- coding: utf-8 -*-

"""
file: columnIO.py

Description: an IO module for CoNLL-formatted files when column
identifiers are not available or not needed.

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

import codecs

from . import tab_join

class Reader(object):
    def __init__(self, name, encoding, cleaner=unicode.strip, splitter=unicode.split):
        self._name     = name
        self._encoding = encoding
        self._cleaner  = cleaner
        self._splitter = splitter
        self._length   = None
        
        if None == self._cleaner:
            self._cleaner = Reader.identity
        if None == self._splitter:
            self._splitter = Reader.identity
        
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
                line = self._splitter(line)
                paragraph.append(line)
            elif paragraph != []:
                yield paragraph
                del paragraph[:]
        if paragraph != []:
            yield paragraph
    
    def line_iter(self):
        paragraph = []
        n_line = -1
        for line_number, line in enumerate(codecs.open(self._name, "rU", self._encoding), 0):
            line  = self._cleaner(line)
            if line != "":
                if paragraph == []:
                    n_line = line_number
                line = self._splitter(line)
                paragraph.append(line)
            elif paragraph != []:
                yield n_line, paragraph
                del paragraph[:]
        if paragraph != []:
            yield n_line, paragraph
    
    @property
    def length(self):
        if self._length is None:
            self._length = 0
            for x in self:
                self._length += 1
        return self._length



class Writer(object):
    def __init__(self, name, encoding, joiner=tab_join):
        self._name     = name
        self._encoding = encoding
        self._joiner   = joiner
        self._fd       = codecs.open(self._name, "w", self._encoding)
        
        if None == self._joiner:
            self._joiner = Writer.identity
        
        # The following instructions will raise an exception if they are not callable.
        self._joiner.__call__
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, exc_tb):
        self._fd.close()
    
    @staticmethod
    def identity(s):
        return s
    
    def write(self, entries):
        for p in entries:
            for l in p:
                self._fd.write(self._joiner(l))
                self._fd.write(u"\n")
            self._fd.write(u"\n")
    
    def write_p(self, p):
        for l in p:
            self._fd.write(self._joiner(l))
            self._fd.write(u"\n")
        self._fd.write(u"\n")
    
    def write_l(self, l):
        self._fd.write(self._joiner(l))
        self._fd.write(u"\n")
    
    def close(self):
        self._fd.close()
