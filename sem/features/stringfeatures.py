# -*- coding: utf-8 -*-

"""
file: stringfeatures.py

Description: features based on "raw" string values.

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

from feature        import Feature
from getterfeatures import DEFAULT_GETTER

class StringFeature(Feature):
    def __init__(self, reference, getter=DEFAULT_GETTER, *args, **kwargs):
        super(StringFeature, self).__init__(self, reference, *args, **kwargs)
        self._reference = reference
        self._getter    = getter

class EqualFeature(StringFeature):
    def __init__(self, reference, *args, **kwargs):
        super(EqualFeature, self).__init__(reference, *args, **kwargs)
        self._is_boolean = True
    
    def __call__(self, *args, **kwargs):
        return self._reference == self._getter(*args, **kwargs)

class EqualCaselessFeature(StringFeature):
    def __init__(self, reference, *args, **kwargs):
        super(EqualCaselessFeature, self).__init__(reference, *args, **kwargs)
        self._is_boolean = True
        self._reference  = self._reference.lower()
    
    def __call__(self, *args, **kwargs):
        return self._reference == self._getter(*args, **kwargs).lower()

