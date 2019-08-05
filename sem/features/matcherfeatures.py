# -*- coding: utf-8 -*-

"""
file: matcherfeatures.py

Description: features based on regex. Implements various regex
functionalities. Does not implement substitution, as it is defined in
arityfeatures.

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

from sem.features.feature import Feature
from sem.features.getterfeatures import DEFAULT_GETTER


class MatchFeature(Feature):
    def __init__(self, pattern, flags=0, getter=DEFAULT_GETTER, default="#", *args, **kwargs):
        super(MatchFeature, self).__init__(pattern, *args, flags=flags, getter=getter, **kwargs)
        self._regexp = re.compile(pattern, flags)
        self._getter = getter
        self._default = default

    def __call__(self, *args, **kwargs):
        return self._regexp.search(self._getter(*args, **kwargs))


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
            if self._default:
                return self._default
            else:
                return self._getter(*args, **kwargs)
        else:
            return matcher.group()


class TokenFeature(MatchFeature):
    def __call__(self, *args, **kwargs):
        matcher = super(TokenFeature, self).__call__(*args, **kwargs)
        if matcher is None:
            if self._default:
                return self._default
            else:
                return self._getter(*args, **kwargs)
        else:
            return matcher.string
