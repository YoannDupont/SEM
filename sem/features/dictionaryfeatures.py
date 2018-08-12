# -*- coding: utf-8 -*-

"""
file: dictionaryfeatures.py

Description: features using dictionary matching.

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

import os.path

from .feature        import Feature
from .getterfeatures import DEFAULT_GETTER

from sem.storage import NUL
from sem.storage import Trie
from sem.storage import compile_token, compile_multiword , compile_map

try:
    import cPickle as pickle
except ImportError:
    import pickle

class DictionaryFeature(Feature):
    def __init__(self, path=None, value=None, entries=None, getter=DEFAULT_GETTER, *args, **kwargs):
        super(DictionaryFeature, self).__init__(*args, **kwargs)
        self._path = path
        if path is not None:
            self._path = os.path.abspath(os.path.expanduser(path))
        self._value  = value
        self._getter = getter
        self._entries = entries

class TokenDictionaryFeature(DictionaryFeature):
    def __init__(self, getter=DEFAULT_GETTER, *args, **kwargs):
        super(TokenDictionaryFeature, self).__init__(getter=getter, *args, **kwargs)
        self._is_boolean = True
        
        if self._path is not None:
            try:
                self._value = pickle.load(open(self._path))
            except (pickle.UnpicklingError, ImportError, EOFError, IndexError, TypeError):
                self._value = compile_token(self._path, "utf-8")
            self._entries = None
        elif self._entries is not None:
            self._value = set()
            for entry in self._entries:
                entry = entry.strip()
                if entry:
                    self._value.add(entry)
        
        assert self._value is not None
    
    def __call__(self, *args, **kwargs):
        return self._getter(*args, **kwargs) in self._value

class MultiwordDictionaryFeature(DictionaryFeature):
    def __init__(self, *args, **kwargs):
        super(MultiwordDictionaryFeature, self).__init__(*args, **kwargs)
        self._is_sequence = True
        self._entry       = kwargs["entry"]
        self._appendice   = kwargs.get("appendice", "")
        
        if self._path is not None:
            try:
                self._value = pickle.load(open(self._path))
            except (pickle.UnpicklingError, ImportError, EOFError):
                self._value = compile_multiword(self._path, "utf-8")
            self._entries = None
        elif self._entries:
            self._value = Trie()
            for entry in self._entries:
                entry = entry.strip()
                if entry:
                    self._value.add(entry.split())
        else:
            self._value = Trie()
    
    def __call__(self, list2dict, *args, **kwargs):
        l         = ["O"]*len(list2dict)
        tmp       = self._value._data
        length    = len(list2dict)
        fst       = 0
        lst       = -1 # last match found
        cur       = 0
        ckey      = None  # Current KEY
        entry     = self._entry
        appendice = self._appendice
        while fst < length - 1:
            cont = True
            while cont and (cur < length):
                ckey  = list2dict[cur][entry]
                if NUL in tmp: lst = cur
                tmp   = tmp.get(ckey, {})
                cont  = len(tmp) != 0
                cur  += int(cont)
            
            if NUL in tmp: lst = cur
            
            if lst != -1:
                l[fst] = u'B' + appendice
                for i in range(fst+1, lst):
                    l[i] = u'I' + appendice
                fst = lst
                cur = fst
            else:
                fst += 1
                cur  = fst
            
            tmp = self._value._data
            lst = -1
        
        if NUL in self._value._data.get(list2dict[-1][entry], []):
            l[-1] = u'B' + appendice
        
        return l
    
    def step(self, list2dict, i, *args, **kwargs):
        tmp       = self._value._data
        length    = len(list2dict)
        fst       = i
        lst       = -1 # last match found
        cur       = fst
        ckey      = None  # Current KEY
        entry     = self._entry
        while fst < length - 1:
            cont = True
            while cont and (cur < length):
                ckey  = list2dict[cur][entry]
                if NUL in tmp: lst = cur
                tmp   = tmp.get(ckey, {})
                cont  = len(tmp) != 0
                cur  += int(cont)
            
            if NUL in tmp: lst = cur
            
            if lst != -1:
                return lst - fst
            
            return 0
        
        if NUL in self._value._data.get(list2dict[-1][entry], []):
            return 1
        
        return 0

class MapperFeature(DictionaryFeature):
    def __init__(self, getter=DEFAULT_GETTER, default="O", *args, **kwargs):
        super(MapperFeature, self).__init__(getter=getter, *args, **kwargs)
        
        self._default = default
        
        if self._path is not None:
            self._value = compile_map(self._path, "utf-8")
            self._entries = None
        elif self._entries is not None:
            self._value = {}
            for entry in self._entries:
                entry = entry.strip()
                if entry:
                    key,value = entry.split(u"\t")
                    self._value[key] = value
        
        assert self._value is not None
    
    def __call__(self, *args, **kwargs):
        return self._value.get(self._getter(*args, **kwargs), self._default)

