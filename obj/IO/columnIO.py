# -*- coding: utf-8 -*-

"""
file: columnIO.py

Description: an IO module for CoNLL-formatted files when column
identifiers are not available or not needed.

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

def tab_join(s):
    return u"\t".join(s)


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
