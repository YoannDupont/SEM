# -*- coding: utf-8 -*-

"""
file: arityfeatures.py

Description: features that could not be categorized and are thus defined
by the number of arguments they take (their arity).

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
        for i in range(1, len(self._features)): # ensuring that we can call the different features sequentially
            self._features[i]._getter = DEFAULT_GETTER
    
    def __call__(self, *args, **kwargs):
        current = self._features[0](*args, **kwargs)
        for feature in self._features[1:]:
            current = feature(current, *args, **kwargs)
        return current
