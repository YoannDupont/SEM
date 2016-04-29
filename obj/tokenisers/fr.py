#-*- encoding:utf-8 -*-

"""
file: fr.py

Description: the tokeniser for french text

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
        self._cls         = re.compile(u"(-je|-tu|-nous|-vous|(:?-t)?-on|(:?-t)?-ils?|(:?-t)?-elles?)", re.U + re.I)
        self._is_abn      = re.compile(u"(dr|me?lles?|mmes?|mrs?|st)\.?", re.U + re.I)
        self._abbrev      = re.compile(u"(i\.e\.|e\.g\.|c-à-d)", re.U + re.I)
        self._digit_valid = set(u"0123456789,.")
        
        self._forbidden = []
        self._forbidden.append(self._is_abn)
        self._forbidden.append(self._abbrev)
        
        self._force = []
        self._force.append(self._cls)
    
    def word_bounds(self, s):
        bounds = SpannedBounds()
        bounds.append(0)
        
        atomic     = set(u";:«»()[]{}=+*$£€/\\\"?!%€$£")
        apostrophe = set(u"'ʼ’")
        
        for forbidden in self._forbidden:
            bounds.add_forbiddens_regex(forbidden, s)
        
        previous      = ""
        for index, c in enumerate(s):
            is_first = index == 0
            is_last  = index == len(s)-1
            
            if c.isspace():
                if (index == bounds[-1].ub) and previous.isspace() or (index == (bounds[-1].lb) and index == (bounds[-1].ub)):
                    bounds[-1].ub += 1
                else:
                    bounds.append(index)
                    bounds[-1].ub += 1
            elif c in atomic:
                bounds.add_last(index)
                bounds.append(index+1)
            elif c in apostrophe:
                bounds.append(index+1)
            elif c.isdigit():
                if previous not in self._digit_valid:
                    bounds.append(index)
                if is_last or s[index+1] not in self._digit_valid:
                    bounds.append(index+1)
            elif c == u',':
                if is_first or is_last or not (previous.isdigit() and s[index+1].isdigit()):
                    bounds.add_last(index)
                    bounds.append(index+1)
            elif c == u".":
                if is_first or is_last or not (previous.isdigit() and s[index+1].isdigit()):
                    bounds.add_last(index)
                    bounds.append(index+1)
            previous = c
        
        for force in self._force:
            bounds.force_regex(force, s)
        
        return bounds
    
    def sentence_bounds(self, tokens):
        sent_bounds    = SpannedBounds()
        opening_counts = [0 for i in tokens]
        count          = 0
        for i in range(len(opening_counts)):
            if tokens[i] in u"«([":
                count += 1
            elif tokens[i] in u"»)]":
                count -= 1
            opening_counts[i] = count
        
        sent_bounds.add(0)
        for index, token in enumerate(tokens):
            if re.match(u"^[?!]+$", token) or token == u"…" or re.match(u"\.\.+", token):
                sent_bounds.append(index+1)
            elif token == u".":
                if opening_counts[index] == 0:
                    sent_bounds.append(index+1)
        sent_bounds.add_last(len(tokens))
        
        return sent_bounds
