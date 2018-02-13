# -*- coding: utf-8 -*-

"""
file: span.py

Description: defines the SpannedBounds object.

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

from sem.span import Span

class SpannedBounds(object):
    """
    The SpanBounds object. Its purpose is to represent (word, sentence, etc.)
    bounds as spans to later produce (word, sentence, etc.) spans.
    
    Attributes
    ----------
    _bounds : list of Span
        the list of bounds between words, sentences, etc.
    _forbidden : set of int
        the list of indices that cannot be a word bound. It is forbidden
        to split a word at this index
    """
    
    def __init__(self):
        self._bounds    = []
        self._forbidden = set()
    
    def __iter__(self):
        for e in self._bounds:
            yield e
    
    def __getitem__(self, i):
        return self._bounds[i]
    
    def __len__(self):
        return len(self._bounds)
    
    def add_forbiddens_regex(self, regex, s):
        for match in regex.finditer(s):
            for index in range(match.start()+1, match.end()):
                self._forbidden.add(index)
    
    def force_regex(self, regex, s):
        """
        Applies a regex for elements that should be segmented in a certain
        way and splits elements accordingly.
        """
        
        for match in regex.finditer(s):
            self.add(Span(match.start(), match.start()))
            self.add(Span(match.end(), match.end()))
    
    def find(self, i):
        """
        Locate an index "i" somewhere in self._bounds.
        """
        
        for nth, span in enumerate(self._bounds):
            if i < span.lb:
                return (nth, False)
            elif i > span.ub:
                continue
            elif (i in span):
                return (nth, True)
        return (-1, False)
    
    def append(self, span):
        """
        Appends "span" at the end of bounds (Span list).
        """
        
        for index in range(span.lb, span.ub+1):
            if self.is_forbidden(index): return
        
        if len(self._bounds) > 0:
            if span in self._bounds[-1] or span == self._bounds[-1]: return
            if len(span) == 0 and self._bounds[-1].ub >= span.lb: return
        
        self._bounds.append(span)
    
    def add(self, span):
        """
        Add "span" at the best index of self._bounds
        """
        
        for index in range(span.lb, span.ub):
            if self.is_forbidden(index): return
        
        index, found = self.find(span.lb)
        if found:
            return
        else:
            if (index > 0 and self[index-1].lb == self[index].ub):
                None
            elif index == -1:
                self._bounds.append(span)
            else:
                self._bounds.insert(index, span)
    
    def add_last(self, span):
        """
        Appends "span" at the end of bounds (Span list). If the last
        span's upper bound is equal to "span's" lower bound, the last
        span's upper bound is extended instead.
        """
        
        for index in range(span.lb, span.ub+1):
            if self.is_forbidden(index): return
        if span in self._bounds[-1]: return
        
        if self._bounds[-1].ub == span.lb:
            self._bounds[-1].expand_ub(span.ub - self._bounds[-1].ub)
        else:
            self._bounds.append(span)
    
    def is_forbidden(self, i):
        return i in self._forbidden
