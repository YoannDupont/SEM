#-*- encoding:utf-8 -*-

"""
file: en.py

Description: the tokeniser for English text.

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

import re

from sem.span               import Span
from sem.spannedbounds      import SpannedBounds
from sem.tokenisers.default import Tokeniser as DefaultTokeniser

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
