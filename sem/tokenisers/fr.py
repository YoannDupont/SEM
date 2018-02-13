#-*- encoding:utf-8 -*-

"""
file: fr.py

Description: the tokeniser for french text

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
        super(Tokeniser, self).__init__()
        
        self._cls         = re.compile(r"(-je|-tu|-nous|-vous|(:?-t)?-(:?on|ils?|elles?))\b", re.U + re.I)
        self._is_abn      = re.compile(r"\b(dr|me?lles?|mme?s?|mr?s?|st)\.?", re.U + re.I)
        self._abbrev      = re.compile(r"\b(i\.e\.|e\.g\.|c-à-d)", re.U + re.I)
        self._digit_valid = set(u"0123456789,.-")
        
        self._forbidden.append(self._is_abn)
        self._forbidden.append(self._abbrev)
        
        self._force.append(self._cls)
    
    def word_bounds(self, s):
        bounds = SpannedBounds()
        bounds.append(Span(0,0))
        
        atomic     = set(u";:«»()[]{}=+*$£€/\\\"?!…%€$£")
        apostrophe = set(u"'ʼ’")
        
        for forbidden in self._forbidden:
            bounds.add_forbiddens_regex(forbidden, s)
        
        previous = ""
        for index, c in enumerate(s):
            is_first = index == 0
            is_last  = index == len(s)-1
            
            if c.isspace():
                if (index == bounds[-1].ub) and previous.isspace() or (index == (bounds[-1].lb) and index == (bounds[-1].ub)):
                    bounds[-1].expand_ub(1)
                else:
                    bounds.append(Span(index, index+1))
            elif c in atomic:
                bounds.add_last(Span(index, index))
                bounds.append(Span(index+1, index+1))
            elif c in apostrophe:
                bounds.append(Span(index+1, index+1))
            elif c.isdigit():
                if is_first or not(previous.isupper() or previous in self._digit_valid):
                    bounds.append(Span(index, index))
                if is_last or not (s[index+1].isupper() or s[index+1] in self._digit_valid):
                    bounds.append(Span(index+1, index+1))
            elif c == u',':
                if is_first or is_last or not (previous.isdigit() and s[index+1].isdigit()):
                    bounds.add_last(Span(index, index))
                    bounds.append(Span(index+1, index+1))
            elif c == u".":
                no_dot_before = previous != u"."
                no_dot_after  = is_last or s[index+1] != u"."
                if is_first or is_last or s[index+1] in u"\r\n" or not (previous.isdigit() and s[index+1].isdigit()):
                    if no_dot_before:
                        bounds.add_last(Span(index, index))
                    if no_dot_after:
                        bounds.append(Span(index+1, index+1))
            elif c == u'-':
                if not(previous) or previous.isspace():
                    bounds.add_last(Span(index, index))
                    bounds.append(Span(index+1, index+1))
                elif not is_last and s[index+1].isspace():
                    bounds.add_last(Span(index, index))
                    bounds.append(Span(index+1, index+1))
            previous = c
        
        for force in self._force:
            bounds.force_regex(force, s)
        
        bounds.append(Span(len(s), len(s)))
        
        return bounds
    
    def sentence_bounds(self, content, token_spans):
        sent_bounds    = SpannedBounds()
        tokens         = [content[t.lb : t.ub] for t in token_spans]
        opening_counts = [0 for i in token_spans]
        count          = 0
        for i in range(len(opening_counts)):
            if tokens[i] in u"«([":
                count += 1
            elif tokens[i] in u"»)]":
                count -= 1
            opening_counts[i] = count
        
        sent_bounds.append(Span(0,0))
        for index, span in enumerate(token_spans):
            token = tokens[index]
            if re.match(u"^[?!]+$", token) or token == u"…" or re.match(u"\.\.+", token):
                sent_bounds.append(Span(index+1, index+1))
            elif token == u".":
                if opening_counts[index] == 0:
                    sent_bounds.append(Span(index+1, index+1))
            elif index<len(token_spans)-1 and content[span.ub : token_spans[index+1].lb].count("\n") > 1:
                sent_bounds.append(Span(index+1, index+1))
        sent_bounds.append(Span(len(tokens), len(tokens)))
        
        return sent_bounds
