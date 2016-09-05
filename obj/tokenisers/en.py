#-*- encoding:utf-8 -*-

"""
file: en.py

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

import re

from obj.span               import Span
from obj.spannedbounds      import SpannedBounds
from obj.tokenisers.default import Tokeniser as DefaultTokeniser

class Tokeniser(DefaultTokeniser):
    def __init__(self):
        pass
    
    def word_bounds(self, s):
        bounds = SpannedBounds()
        bounds.append(Span(0,0))
        
        atomic     = set(u";:«»()[]{}=+*$£€/\\\"?!%€$£")
        apostrophe = set(u"'ʼ’")
        
        for index, c in enumerate(s):
            is_first = index == 0
            is_last  = index == len(s)-1
            if c.isspace():
                bounds.add_last(Span(index, index+1))
            elif c in atomic:
                bounds.add_last(Span(index, index))
                bounds.append(Span(index+1, index+1))
            elif c in apostrophe:
                if is_first or is_last:
                    bounds.add_last(Span(index, index))
                    bounds.append(Span(index+1, index+1))
                elif s[index+1] == s[index]:
                    bounds.append(Span(index, index+1))
                else:
                    if s[index-1] == u"n" and s[index+1] == u"t":
                        bounds.append(Span(index-1, index-1))
                        bounds.append(Span(index+2, index+2))
                    elif s[index+1] == u"s":
                        bounds.append(Span(index, index))
                        bounds.append(Span(index+2, index+2))
                    else:
                        bounds.add_last(Span(index, index))
            elif c in u'.,':
                if is_first or is_last:
                    bounds.add_last(Span(index, index))
                    bounds.append(Span(index+1, index+1))
                elif (is_first or not s[index-1].isdigit()) and (is_last or not s[index-1].isdigit()):
                    bounds.add_last(Span(index, index))
                    bounds.append(Span(index+1, index+1))
        
        bounds.append(Span(len(s), len(s)))
        
        return bounds
    
    def sentence_bounds(self, content, token_spans):
        sent_bounds    = SpannedBounds()
        tokens         = [content[t.lb : t.ub] for t in token_spans]
        openings       = set([u"«",u"(",u"[",u"``"])
        closings       = set([u"»",u")",u"]",u"''"])
        opening_counts = [0 for i in tokens]
        count          = 0
        for i in range(len(opening_counts)):
            if tokens[i] in openings:
                count += 1
            elif tokens[i] in closings:
                count -= 1
            opening_counts[i] = count
        
        sent_bounds.append(Span(0,0))
        for index, token in enumerate(tokens):
            if re.match(u"^[?!]+$", token) or token == u"…" or re.match(u"\.\.+", token):
                sent_bounds.append(Span(index+1, index+1))
            elif token == u".":
                if opening_counts[index] == 0:
                    sent_bounds.append(Span(index+1, index+1))
        sent_bounds.append(Span(len(tokens), len(tokens)))
        
        return sent_bounds
