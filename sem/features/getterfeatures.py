# -*- coding: utf-8 -*-

"""
file: getterfeatures.py

Description: getter features are features whose sole purpose is to look
for the right token and return it or one of its fields.

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

class GetterFeature(Feature):
    def __init__(self, *args, **kwargs):
        super(GetterFeature, self).__init__(*args, **kwargs)

class IdentityFeature(GetterFeature):
    """
    A getter that return the argument as it is.
    This allows to call features on strings as well as a local position
    in a sentence. This may cause performance issue, but it is the only
    way currently known to have an "feature package" that is consistent.
    """
    def __init__(self, *args, **kwargs):
        super(IdentityFeature, self).__init__(*args, **kwargs)
    
    def __call__(self, element, *args, **kwargs):
        return element
DEFAULT_GETTER = IdentityFeature()

class DictGetterFeature(GetterFeature):
    def __init__(self, *args, **kwargs):
        super(DictGetterFeature, self).__init__(*args, **kwargs)
        self.entry = kwargs.get("entry", "word")
        self.shift = int(kwargs.get("shift", 0))
    
    def __call__(self, list2dict, position, *args, **kwargs):
        current_position = position + self.shift
        
        if not(0 <= current_position < len(list2dict)):
            return None
        
        return list2dict[current_position].get(self.entry, None)

class FindFeature(GetterFeature):
    def __init__(self, *args, **kwargs):
        super(FindFeature, self).__init__(*args, **kwargs)
        self._matcher      = args[0]
        self._return_entry = kwargs.get("return_entry", "word")
        assert self._matcher is not None and self._matcher.is_boolean, "Matcher field in FindFeature does not return a boolean."

class FindForwardFeature(FindFeature):
    def __init__(self, *args, **kwargs):
        super(FindForwardFeature, self).__init__(*args, **kwargs)
        
    def __call__(self, list2dict, position, *args, **kwargs):
        for X in range(position+1, len(list2dict)):
            if self._matcher(list2dict, X):
                return list2dict[X][self._return_entry]
        return None

class FindBackwardFeature(FindFeature):
    def __init__(self, *args, **kwargs):
        super(FindBackwardFeature, self).__init__(*args, **kwargs)
        
    def __call__(self, list2dict, position, *args, **kwargs):
        for X in reversed(range(0, position)):
            if self._matcher(list2dict, X):
                return list2dict[X][self._return_entry]
        return None
