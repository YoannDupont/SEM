# -*- coding: utf-8 -*-

"""
file: arityfeatures.py

Description: features that could not be categorized and are thus defined
by the number of arguments they take (their arity).

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

import re

from feature        import Feature
from getterfeatures import DEFAULT_GETTER

class ArityFeature(Feature):
    def __init__(self, *args, **kwargs):
        super(ArityFeature, self).__init__(*args, **kwargs)
        self._getter = kwargs.pop("getter", DEFAULT_GETTER)



class NullaryFeature(ArityFeature):
    def __init__(self, *args, **kwargs):
        super(NullaryFeature, self).__init__(*args, **kwargs)

class BOSFeature(NullaryFeature):
    def __init__(self, *args, **kwargs):
        super(BOSFeature, self).__init__(*args, **kwargs)
        self._is_boolean = True
    
    def __call__(self, list2dict, position, *args, **kwargs):
        return position == 0

class EOSFeature(NullaryFeature):
    def __init__(self, *args, **kwargs):
        super(EOSFeature, self).__init__(*args, **kwargs)
        self._is_boolean = True
    
    def __call__(self, list2dict, position, *args, **kwargs):
        return position == len(list2dict)-1

class LowerFeature(NullaryFeature):
    def __init__(self, *args, **kwargs):
        super(LowerFeature, self).__init__(*args, **kwargs)
    
    def __call__(self, *args, **kwargs):
        return self._getter(*args, **kwargs).lower()
    
class SubstringFeature(NullaryFeature):
    def __init__(self, from_index=0, to_index=2**31, *args, **kwargs):
        super(SubstringFeature, self).__init__(from_index, to_index, *args, **kwargs)
        self._default    = kwargs.pop("default", '""')
        self._from_index = int(from_index)
        self._to_index   = int(to_index)
    
    def __call__(self, *args, **kwargs):
        s = self._getter(*args, **kwargs)[self._from_index : self._to_index]
        if s:
            return s
        else:
            return self._default



class UnaryFeature(ArityFeature):
    def __init__(self, element, *args, **kwargs):
        super(UnaryFeature, self).__init__(*args, **kwargs)
        self._is_boolean = False
        self._element = element

class IsUpperFeature(UnaryFeature):
    def __init__(self, index, *args, **kwargs):
        super(IsUpperFeature, self).__init__(index, *args, **kwargs)
        self._is_boolean = True
        self._index      = self._element
    
    def __call__(self, *args, **kwargs):
        return self._getter(*args, **kwargs)[self._index].isupper()



class BinaryFeature(ArityFeature):
    def __init__(self, element1, element2, *args, **kwargs):
        super(BinaryFeature, self).__init__(*args, **kwargs)
        self._element1 = element1
        self._element2 = element2
    
class SubstitutionFeature(BinaryFeature):
    def __init__(self, pattern, replacement, *args, **kwargs):
        super(SubstitutionFeature, self).__init__(pattern, replacement, *args, **kwargs)
        flags = kwargs.pop("flags", 0)
        self._replacer    = re.compile(pattern, flags)
        self._replacement = replacement
    
    def __call__(self, *args, **kwargs):
        return self._replacer.sub(self._replacement, self._getter(*args, **kwargs))



class NaryFeature(ArityFeature):
    def __init__(self, *args, **kwargs):
        super(NaryFeature, self).__init__(self, *args, **kwargs)

class SequencerFeature(NaryFeature):
    def __init__(self, *args, **kwargs):
        super(SequencerFeature, self).__init__(*args, **kwargs)
        
        if len(args) == 0:
            raise ValueError("%s cannot have less than 1 feature" %(self.__class__.__name__))
        
        self._features = args
        for i in range(1, len(self._features)): # ensuring that we can call thing sequentially
            self._features[i]._getter = DEFAULT_GETTER
    
    def __call__(self, *args, **kwargs):
        current = self._features[0](*args, **kwargs)
        for feature in self._features[1:]:
            current = feature(current, *args, **kwargs)
        return current
