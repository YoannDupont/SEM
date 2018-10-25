# -*- coding: utf-8 -*-

"""
file: getterfeatures.py

Description: getter features are features whose sole purpose is to look
for the right token and return it or one of its fields.

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

from .feature import Feature

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

class ListGetterFeature(GetterFeature):
    def __init__(self, *args, **kwargs):
        super(ListGetterFeature, self).__init__(*args, **kwargs)
        self.index = kwargs.get("index", 0)
        self.shift = int(kwargs.get("shift", 0))
    
    def __call__(self, list2dict, position, *args, **kwargs):
        current_position = position + self.shift
        
        if not(0 <= current_position < len(list2dict)):
            return None
        
        return list2dict[current_position][self.index]
