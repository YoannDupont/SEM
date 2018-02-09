# -*- coding: utf-8 -*-

"""
file: listfeatures.py

Description: defines features based on lists. They are somewhat similar
to token dictionaries, at the difference that one can explicitly choose
of not matching a term, or all terms in a list.

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

class ListFeature(Feature):
    def __init__(self, *args, **kwargs):
        super(ListFeature, self).__init__(*args, **kwargs)
        self._elements   = args
        self._is_boolean = True
        
        for element in self._elements:
            if not element.is_boolean:
                raise TypeError("Non boolean element in list node: %s" %(element.__class__.__name__))

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
