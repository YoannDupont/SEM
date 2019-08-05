# -*- coding: utf-8 -*-

"""
file: feature.py

Description: the top-level object for features. Defines basic attributes
and functionalities.

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

from sem.misc import str2bool


class Feature(object):
    def __init__(self, *args, **kwargs):
        self._is_boolean = False
        self._is_sequence = False
        self._name = kwargs.pop("name", None)
        self._display = kwargs.pop("display", "yes").lower()

        self._display = str2bool(self._display)

    def __call__(self, *args, **kwargs):
        raise TypeError("Cannot call {0} object".format(self.__class__.__name__))

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

    def default(self):
        return "#"
