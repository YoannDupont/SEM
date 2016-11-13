# -*- coding: utf-8 -*-

"""
file: matcherfeatures.py

Description: features based on regex. Implements various regex
functionalities. Does not implement substitution, as it is defined in
arityfeatures.

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

class MatchFeature(Feature):
    def __init__(self, pattern, flags=0, getter=DEFAULT_GETTER, *args, **kwargs):
        super(MatchFeature, self).__init__(pattern, *args, flags=flags, getter=getter, **kwargs)
        self._regexp = re.compile(pattern, flags)
        self._getter = getter
    
    def __call__(self, *args, **kwargs):
        return self._regexp.search(self._getter(*args, **kwargs) or "")

class CheckFeature(MatchFeature):
    def __init__(self, pattern, flags=0, getter=DEFAULT_GETTER, *args, **kwargs):
        super(CheckFeature, self).__init__(pattern, flags=flags, getter=getter, *args, **kwargs)
        self._is_boolean = True
    
    def __call__(self, *args, **kwargs):
        return super(CheckFeature, self).__call__(*args, **kwargs) is not None

class SubsequenceFeature(MatchFeature):
    def __call__(self, *args, **kwargs):
        matcher = super(SubsequenceFeature, self).__call__(*args, **kwargs)
        if matcher is None:
            return matcher
        else:
            return matcher.group()

class TokenFeature(MatchFeature):
    def __call__(self, *args, **kwargs):
        matcher = super(TokenFeature, self).__call__(*args, **kwargs)
        if matcher is None:
            return matcher
        else:
            return matcher.string
