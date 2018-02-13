# -*- coding: utf-8 -*-

"""
file: span.py

Description: defines the Span object.

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

try:
    from xml.etree.cElementTree import ElementTree as ET
except ImportError:
    from xml.etree.ElementTree import ElementTree as ET

class Span(object):
    """
    The Span object.
    
    Attributes
    ----------
    _lb : int
        the lower bound of a Span.
    _ub : int
        the upper bound of a Span.
    """
    
    def __init__(self, lb, ub, length=-1):
        self._lb = (min(lb, ub) if length<0 else lb)
        self._ub = (max(lb, ub) if length<0 else lb+length)
    
    def __eq__(self, span):
        return self.lb == span.lb and self.ub == span.ub
    
    def __contains__(self, i):
        return self._lb <= i and i < self.ub
    
    def __len__(self):
        return self._ub - self._lb
    
    def __str__(self):
        return "[%i:%i]" %(self._lb, self._ub)
    
    @property
    def lb(self):
        return self._lb
    
    @property
    def ub(self):
        return self._ub
    
    @lb.setter
    def lb(self, lb):
        self._lb = min(lb, self._ub)
    
    @ub.setter
    def ub(self, ub):
        self._ub = max(ub, self._lb)
    
    def toXML(self):
        return '<span s="%i" l="%s" />' %(self._lb, len(self))
    
    @classmethod
    def fromXML(cls, xml):
        if type(node) in (str, unicode):
            node = ET.fromstring(xml)
        else:
            node = xml
        start  = node.attrib.get(u"start", node.attrib[u"s"])
        end    = node.attrib.get(u"end", node.attrib.get(u"e", start))
        length = node.attrib.get(u"length", node.attrib.get(u"l", -1))
        return Span(start, end, length=length)
    
    def strictly_contains(self, i):
        return i > self._lb and i < self.ub
    
    def expand_lb(self, length):
        self._lb -= length
    
    def expand_ub(self, length):
        self._ub += length
