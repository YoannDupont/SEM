#-*- encoding:utf-8 -*-

"""
file: default.py

Description: 

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
along with this program. If not, see GNU official website.
"""

import obj.constants

from obj.span          import Span
from obj.spannedbounds import SpannedBounds

class Tokeniser(object):
    def __init__(self):
        self._forbidden = []
        self._force     = []
        
        # adding some "basic" things to not tokenise across languages.
        self._forbidden.append(obj.constants.url_re)
        self._forbidden.append(obj.constants.email_re)
    
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
        for index, token in enumerate(tokens):
            if token in u"\r\n":
                sent_bounds.add_last(Span(index, index+1))
        sent_bounds.add_last(Span(len(tokens), len(tokens)))
        
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
        return [Span(bounds[i].ub, bounds[i+1].lb) for i in range(0, len(bounds)-1)]
