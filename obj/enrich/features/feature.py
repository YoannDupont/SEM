# -*- coding: utf-8 -*-

"""
file: feature.py

Description: the top-level object for features. Defines basic attributes
and functionalities.

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

class Feature(object):
    def __init__(self, *args, **kwargs):
        self._is_boolean  = False
        self._is_sequence = False
        self._name        = kwargs.pop("name", None)
        self._display     = kwargs.pop("display", "yes").lower()
        
        self._display = {"yes":True,"y":True,"true":True, "no":False,"n":False,"false":False}[self._display]
    
    def __call__(self, *args, **kwargs):
        raise TypeError('Cannot call %s object' %self.__class__.__name__)
    
    @property
    def is_boolean(self):
        return self._is_boolean
    
    @property
    def is_sequence(self):
        return self._is_sequence
    
    @property
    def name(self):
        return self._name
    
    @property
    def display(self):
        return self._display
