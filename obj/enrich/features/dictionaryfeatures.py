# -*- coding: utf-8 -*-

"""
file: dictionaryfeatures.py

Description: features using dictionary matching.

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

import os.path

from feature        import Feature
from getterfeatures import DEFAULT_GETTER

from obj.dictionaries import NUL

try:
    import cPickle as pickle
except ImportError:
    import pickle

from obj.dictionaries import compile_token, compile_multiword

class DictionaryFeature(Feature):
    def __init__(self, path=None, value=None, getter=DEFAULT_GETTER, *args, **kwargs):
        super(DictionaryFeature, self).__init__(self, *args, **kwargs)
        self._path = path
        if path is not None:
            self._path = os.path.abspath(os.path.expanduser(path))
        self._value  = value
        self._getter = getter

class TokenDictionaryFeature(DictionaryFeature):
    def __init__(self, getter=DEFAULT_GETTER, *args, **kwargs):
        super(TokenDictionaryFeature, self).__init__(getter=getter, *args, **kwargs)
        self._is_boolean = True
        
        if self._path is not None:
            try:
                self._value = pickle.load(open(self._path))
            except (pickle.UnpicklingError, ImportError, EOFError):
                self._value = compile_token(self._path, "utf-8")
        
        assert self._value is not None
    
    def __call__(self, *args, **kwargs):
        return self._getter(*args, **kwargs) in self._value

class MultiwordDictionaryFeature(DictionaryFeature):
    def __init__(self, *args, **kwargs):
        super(MultiwordDictionaryFeature, self).__init__(*args, **kwargs)
        self._is_sequence = True
        self._entry       = kwargs["entry"]
        self._appendice   = kwargs.get("appendice", "")
        
        try:
            self._value = pickle.load(open(self._path))
        except (pickle.UnpicklingError, ImportError, EOFError):
            self._value = compile_multiword(self._path, "utf-8")
    
    """def __call__(self, list2dict, *args, **kwargs):
        l         = ["O"]*len(list2dict)
        tmp       = self._value._data
        length    = len(list2dict)
        fst       = 0
        lst       = -1 # last match found
        cur       = 0
        criterion = False # stop criterion
        ckey      = None  # Current KEY
        entry     = self._entry
        appendice = self._appendice
        while not criterion:
            cont = True
            while cont and (cur < length):
                ckey = list2dict[cur][entry]
                if (NUL not in tmp):
                    if (ckey in tmp):
                        tmp  = tmp[ckey]
                        cur += 1
                    else:
                        cont = False
                else:
                    lst  = cur
                    cont = ckey in tmp
                    if cont:
                        tmp  = tmp[ckey]
                        cur += 1
            
            if NUL in tmp:
                l[fst] = u'B' + appendice
                for i in xrange(fst+1, cur):
                    l[i] = u'I' + appendice
                fst = cur
            elif lst != -1:
                l[fst] = u'B' + appendice
                for i in xrange(fst+1, lst):
                    l[i] = u'I' + appendice
                fst = lst
                cur = fst
            else:
                fst += 1
                cur  = fst
            
            tmp       = self._value._data
            lst       = -1
            criterion = fst >= length - 1
        
        if NUL in self._value._data.get(list2dict[-1][entry], []):
            l[-1] = u'B' + appendice
        
        return l"""
    
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
                for i in xrange(fst+1, lst):
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

