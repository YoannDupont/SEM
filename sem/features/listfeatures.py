# -*- coding: utf-8 -*-

"""
file: listfeatures.py

Description: defines features based on lists. They are somewhat similar
to token dictionaries, at the difference that one can explicitly choose
of not matching a term, or all terms in a list.

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

class ListFeature(Feature):
    def __init__(self, *args, **kwargs):
        super(ListFeature, self).__init__(*args, **kwargs)
        self._elements   = args
        self._is_boolean = True
        
        for element in self._elements:
            if not element.is_boolean:
                raise TypeError("Non boolean element in list node: {0}".format(element.__class__.__name__))

class SomeFeature(ListFeature):
    def __init__(self, *args, **kwargs):
        super(SomeFeature, self).__init__(*args, **kwargs)
    
    def __call__(self, *args, **kwargs):
        for element in self._elements:
            if element(*args, **kwargs):
                return True
        return False

class AllFeature(ListFeature):
    def __init__(self, *args, **kwargs):
        super(AllFeature, self).__init__(*args, **kwargs)
    
    def __call__(self, *args, **kwargs):
        for element in self._elements:
            if not element(*args, **kwargs):
                return False
        return True

class NoneFeature(ListFeature):
    def __init__(self, *args, **kwargs):
        super(NoneFeature, self).__init__(*args, **kwargs)
    
    def __call__(self, *args, **kwargs):
        for element in self._elements:
            if element(*args, **kwargs):
                return False
        return True
