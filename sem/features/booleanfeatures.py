# -*- coding: utf-8 -*-

"""
file: booleanfeatures.py

Description: features for defining boolean expressions.

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

from sem.features.feature import Feature


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
