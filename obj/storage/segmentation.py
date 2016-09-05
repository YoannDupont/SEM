# -*- coding: utf-8 -*-

"""
file: segmentation.py

Description: defines Segmentation object. A segmentation is a list of
spans refering to a sequence. A segmentation being a sequence, it is
possible to have the segmentation of a segmentation.
For example, sentence segmentation references token segmentation: it is
a segmentation of another segmentation.
Segmentations that have no references are supposed to reference a string
or unicode.

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

from obj.span import Span

class Segmentation(object):
    """
    Segmentation is just a holder for bounds. Those bounds can be word
    bounds or sentence bounds for example.
    By itself, it is not very useful, it become good in the context of
    a document for which it hold minimum useful information
    """
    def __init__(self, name, reference=None, spans=None):
        """
        parameters
        ==========
        name: unicode
            the name of the segmentation (tokens, sentences, paragraphs, etc.)
        reference: unicode or Segmentation
            if unicode: the name of the referenced segmentation in the document
            if Segmentation: the referenced segmentation
        spans: list of span
        bounds: list of span
        """
        
        self._name      = name
        self._document  = None
        self._reference = reference
        self._spans     = spans
    
    def __len__(self):
        return len(self.spans)
    
    def __getitem__(self, i):
        return self._spans[i]
    
    def __iter__(self):
        for element in self.spans:
            yield element
    
    @property
    def name(self):
        return self._name
    
    @property
    def reference(self):
        return self._reference
    
    @property
    def spans(self):
        return self._spans
    
    def get_reference_spans(self):
        """
        returns spans according to the reference chain.
        """
        
        if self.reference is None:
            return self.spans
        else:
            reference_spans = self.reference.get_reference_spans()
            return [Span(reference_spans[element.lb].lb, reference_spans[element.ub-1].ub) for element in self.spans]
