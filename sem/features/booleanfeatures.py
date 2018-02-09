# -*- coding: utf-8 -*-

"""
file: booleanfeatures.py

Description: features for defining boolean expressions.

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

from feature import Feature

class BooleanFeature(Feature):
    def __init__(self, *args, **kwargs):
        super(BooleanFeature, self).__init__(*args, **kwargs)
        self._is_boolean = True

class UnaryFeature(BooleanFeature):
    def __init__(self, element, *args, **kwargs):
        super(UnaryFeature, self).__init__(element, *args, **kwargs)
        self.element = element

class NotFeature(UnaryFeature):
    def __init__(self, element, *args, **kwargs):
        super(NotFeature, self).__init__(element, *args, **kwargs)
    
    def __call__(self, *args, **kwargs):
        return not self.element(*args, **kwargs)

class BinaryFeature(BooleanFeature):
    def __init__(self, left, right, *args, **kwargs):
        super(BinaryFeature, self).__init__(left, right, *args, **kwargs)
        self.left = left
        self.right = right

class AndFeature(BinaryFeature):
    def __init__(self, left, right, *args, **kwargs):
        super(AndFeature, self).__init__(left, right, *args, **kwargs)
    
    def __call__(self, *args, **kwargs):
        return self.left(*args, **kwargs) and self.right(*args, **kwargs)

class OrFeature(BinaryFeature):
    def __init__(self, left, right, *args, **kwargs):
        super(OrFeature, self).__init__(left, right, *args, **kwargs)
    
    def __call__(self, *args, **kwargs):
        return self.left(*args, **kwargs) or self.right(*args, **kwargs)
