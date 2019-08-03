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

from sem.storage.span import Span

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

        self._name = name
        self._document = None
        self._reference = reference
        self._spans = spans

    def __len__(self):
        return len(self.spans)

    def __getitem__(self, i):
        return self._spans[i]

    def __iter__(self):
        for element in self.spans:
            yield element

    def append(self, span):
        if self._spans is None:
            self._spans = []
        self._spans.append(span)

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
            return [
                Span(reference_spans[element.lb].lb, reference_spans[element.ub-1].ub)
                for element in self.spans
            ]
