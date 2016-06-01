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

from obj.span          import Span
from obj.spannedbounds import SpannedBounds

class Tokeniser(object):
    def __init__(self):
        pass
    
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
            elif c in u",;:/\\!?.'\"()[]{}=+$£€":
                bounds.add_last(index)
                bounds.append(index+1)
        
        return bounds
    
    def sentence_bounds(tokens):
        """
        Returns a list of bounds matching sentences.
        
        Parameters
        ----------
        tokens : list of str
            the list of tokens to compute sentence bounds for
        """
        sent_bounds = SpannedBounds()
        
        sent_bounds.append(0)
        for index, token in enumerate(tokens):
            if rtoken == u".?!…":
                sent_bounds.append(index+1)
            elif token == u".":
                if opening_counts[index] == 0:
                    sent_bounds.append(index+1)
        sent_bounds.append(len(tokens))
        
        return sent_bounds
    
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
