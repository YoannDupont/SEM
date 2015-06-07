#! /usr/bin/python
# -*- coding: utf-8 -*-

#-------------------------------------------------------------------------------
#
# file: trie.py
#
#-------------------------------------------------------------------------------

import codecs

_NUL = u"" # end of sequence marker

class Trie(object):
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
    