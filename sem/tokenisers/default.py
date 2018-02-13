#-*- encoding:utf-8 -*-

"""
file: default.py

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

import sem.constants

from sem.span          import Span
from sem.spannedbounds import SpannedBounds

class Tokeniser(object):
    def __init__(self):
        self._forbidden = []
        self._force     = []
        
        # adding some "basic" things to not tokenise across languages.
        self._forbidden.append(sem.constants.url_re)
        self._forbidden.append(sem.constants.email_re)
    
    def word_bounds(self, content):
        """
        Returns a list of bounds matching words.
        
        Parameters
        ----------
        content : str / unicode
            the input string
        """
        bounds = SpannedBounds()
        bounds.append(0)
        
        for index, c in enumerate(content):
            if c.isspace():
                bounds.add_last(index)
                bounds.add_last(index+1)
        
        return bounds
    
    def sentence_bounds(self, content, token_spans):
        """
        Returns a list of bounds matching sentences.
        
        Parameters
        ----------
        token_spans : list of Span
            the list of tokens spans
        """
        sent_bounds = SpannedBounds()
        
        sent_bounds.add(Span(0,0))
        for index, span in enumerate(token_spans):
            token = content[span.lb : span.ub]
            if token in u"\r\n":
                sent_bounds.add_last(Span(index, index+1))
        sent_bounds.add_last(Span(len(token_spans), len(token_spans)))
        
        return sent_bounds
    
    def paragraph_bounds(self, content, sentence_spans, token_spans):
        """
        Returns a list of bounds matching paragraphs.
        
        Parameters
        ----------
        sentence_spans : list of Span
            the list of sentence spans
        """
        s_spans = [Span(token_spans[e.lb].lb, token_spans[e.ub-1].ub) for e in sentence_spans]
        
        paragraph_bounds = SpannedBounds()
        
        paragraph_bounds.add(Span(0, 0))
        for index, sentence in enumerate(sentence_spans[1:], 1):
            substring = content[s_spans[index-1].ub : s_spans[index].lb]
            if substring.count(u"\n") > 1:
                paragraph_bounds.append(Span(index, index))
        paragraph_bounds.append(Span(len(sentence_spans), len(sentence_spans)))
        
        return paragraph_bounds
    
    def tokenise(self, sequence, bounds):
        """
        Returns a tokenised version of a sequence according to given bounds.
        
        Parameters
        ----------
        sequence : str / list
            the sequence to tokenise. Its bounds have been guessed
            previously. Should be called after word_/sentence_ bounds
        bounds : SpannedBounds
            the precomputed bounds for the sequence in argument
        """
        tokens = []
        for i in range(0, len(bounds)-1):
            tokens.append(sequence[bounds[i].ub : bounds[i+1].lb])
        return tokens
    
    def bounds2spans(self, bounds):
        """
        creates spans from bounds
        """
        spans = [Span(bounds[i].ub, bounds[i+1].lb) for i in range(0, len(bounds)-1)]
        spans = [span for span in spans if span.lb != span.ub]
        return spans
