# -*- coding: utf-8 -*-

"""
file: trie.py

Description: Trie object definition. A Trie is here a very convenient
way to model multiword dictionaries. They are, here, the same thing
as a Prefix Tree Automaton (PTA).

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
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import codecs

_NUL = u"" # end of sequence marker

class Trie(object):
    """
    The Trie object.
    
    Attributes
    ----------
    _data : dict
        the structure where all the entries of a multiword dictionary
        are loaded.
    """
    
    def __init__(self, filename=None, encoding=None):
        self._data = {}
        
        if filename:
            encoding = encoding or u"UTF-8"
            for l in codecs.open(filename, u"rU", encoding):
                seq = l.strip().split()
                
                self.add(seq)
    
    def __iter__(self):
        seq = []
        # Depth First Search
        def dfs(dic):
            keys  = set(dic.keys())
            found = _NUL in keys
            
            if found:
                keys.remove(_NUL)
                if dic[_NUL] == {}:
                    yield seq
            keys = list(keys)
            keys.sort()
            for k in keys:
                seq.append(k)
                for i in dfs(dic[k]):
                    yield i
                seq.pop()
        
        for i in dfs(self._data):
            yield i
    
    def __len__(self):
        length = 0
        for i in self:
            length += 1
        return length
    
    @property
    def data(self):
        return self._data
    
    def add(self, sequence):
        iterator = sequence.__iter__()
        d        = self._data
        
        try:
            while True:
                token = next(iterator)
                
                if token not in d:
                    d[token] = {}

                d = d[token]
        except StopIteration:
            pass
        
        d[_NUL] = {}
    
    def contains(self, sequence):
        iterator = sequence.__iter__()
        d        = self._data
        result   = True
        
        try:
            while True:
                token = next(iterator)
                
                if token not in d:
                    result = False
                    break

                d = d[token]
        except StopIteration:
            pass
        
        return result and (_NUL in d)
    
    def remove(self, sequence):
        def remove(dic, iterator):
            try:
                elt = next(iterator)
                if elt in dic:
                    remove(dic[elt], iterator)
                    if dic[elt] == {}:
                        del dic[elt]
            except StopIteration:
                if _NUL in dic:
                    del dic[_NUL]

        remove(self._data, sequence.__iter__())
    
