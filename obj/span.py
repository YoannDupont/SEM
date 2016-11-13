# -*- coding: utf-8 -*-

"""
file: span.py

Description: defines the Span object.

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
along with this program.  If not, see <http://www.gnu.org/licenses/>.
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
        return i >= self._lb and i <= self.ub
    
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
