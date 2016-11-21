# -*- coding: utf-8 -*-

"""
file: KeyIO.py

Description: an IO module for CoNLL-formatted files when column
identifiers are available.

author: Yoann Dupont
copyright (c) 2016 Yoann Dupont - all rights reserved

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see GNU official website.
"""

import codecs

class KeyReader(object):
    def __init__(self, name, encoding, keys, cleaner=unicode.strip, splitter=unicode.split):
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
        
        self._format = self._joiner.join(["%%(%s)s" %key for key in self._keys])
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, exc_tb):
        self._fd.close()
    
    def write(self, entries):
        for p in entries:
            for l in p:
                self._fd.write(self._format %l)
                self._fd.write(u"\n")
            self._fd.write(u"\n")
    
    def write_p(self, p):
        for l in p:
            self._fd.write(self._format %l)
            self._fd.write(u"\n")
        self._fd.write(u"\n")
    
    def write_l(self, l):
        self._fd.write(self._format %l)
        self._fd.write(u"\n")
    
    def close(self):
        self._fd.close()
