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

from sem.storage import Span, SpannedBounds
from .default import Tokeniser as DefaultTokeniser

class Tokeniser(DefaultTokeniser):
    def __init__(self):
        super(Tokeniser, self).__init__()
        
        self._cls         = re.compile(r"(-je|-tu|-nous|-vous|(:?-t)?-(:?on|ils?|elles?))\b", re.U + re.I)
        self._is_abn      = re.compile(r"\b(dr|me?lles?|mme?s?|mr?s?|st)\b\.?", re.U + re.I)
        self._abbrev      = re.compile(r"\b(i\.e\.|e\.g\.|c-à-d)", re.U + re.I)
        self._digit_valid = set(u"0123456789,.-")
        
        self._forbidden.append(self._is_abn)
        self._forbidden.append(self._abbrev)
        
        self._force.append(self._cls)
        
        self._spaces = re.compile(u"\s+", re.U+re.M)
        self._word = re.compile(u"^[^\W\d]+$", re.U + re.M)
        self._number_with_unit = re.compile(u"([0-9][^0-9,.])|([^0-9,.][0-9])")
        self._atomic = re.compile(u"[;:«»()\\[\\]{}=+*$£€/\\\"?!…%€$£]")
        self._comma_not_number = re.compile(u"(?<=[^0-9]),(?![0-9])", re.U + re.M)
        self._apostrophe = re.compile(u"(?=['ʼ’])", re.U + re.M)
        self._clitics = re.compile(r"(-je|-tu|-nous|-vous|(:?-t)?-(:?on|ils?|elles?))$", re.U + re.I)
    
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
    
    def word_spans(self, content):
        spaces = self._spaces

        l = [match.span() for match in spaces.finditer(content)]
        l1 = [(l[i][1],l[i+1][0]) for i in range(len(l)-1)]
        
        if not l: # content is a single non-space token
            return [Span(0, len(content))]

        if l[0][0] != 0:
            l1.insert(0, (0, l[0][0]))
        if l[-1][1] != len(content):
            l1.append((l[-1][1], len(content)))
        
        word = self._word
        number_with_unit = self._number_with_unit
        atomic = self._atomic
        comma_not_number = self._comma_not_number
        apostrophe = self._apostrophe
        clitics = self._clitics
        i = 0
        while i < len(l1):
            span = l1[i]
            text = content[span[0] : span[1]]
            if len(text) == 1:
                i += 1
                continue
            if word.match(text):
                i += 1
                continue
            found = False
            for forbidden in self._forbidden:
                found = forbidden.match(text)
                if found:
                    i += 1
                    break
            if found:
                continue
            tmp = []
            # atomic characters, they are always split
            prev = span[0]
            for find in atomic.finditer(text):
                if prev != span[0]+find.start(): tmp.append((prev, span[0]+find.start()))
                tmp.append((span[0]+find.start(), span[0]+find.end()))
                prev = span[0]+find.end()
            if tmp != []:
                if prev != span[1]:
                    tmp.append((prev, span[1]))
                del l1[i]
                for t in reversed(tmp):
                    l1.insert(i, t)
                continue
            del tmp[:]
            # commas
            prev = span[0]
            for find in comma_not_number.finditer(text):
                tmp.extend([(prev, span[0]+find.start()), (span[0]+find.start(), span[0]+find.end()), (span[0]+find.end(), span[1])])
                prev = span[0]+find.end()+1
            if tmp != []:
                del l1[i]
                for t in reversed(tmp):
                    l1.insert(i, t)
                continue
            del tmp[:]
            # apostrophes
            prev = span[0]
            for find in apostrophe.finditer(text):
                tmp.append((prev, span[0]+find.start()+1))
                prev = span[0]+find.start()+1
            if prev < span[1]:
                tmp.append((prev, span[1]))
            if len(tmp) > 1:
                del l1[i]
                for t in reversed(tmp):
                    l1.insert(i, t)
                continue
            del tmp[:]
            # clitics
            prev = span[0]
            for find in clitics.finditer(text):
                tmp.append((prev, span[0]+find.start()))
                prev = span[0]+find.start()
            if tmp:
                if tmp[0][0] == tmp[0][1]:
                    del tmp[:]
                else:
                    tmp.append((prev, span[1]))
            if len(tmp) > 1:
                del l1[i]
                for t in reversed(tmp):
                    l1.insert(i, t)
                continue
            del tmp[:]
            # number with unit
            prev = span[0]
            for find in number_with_unit.finditer(text):
                tmp.append((prev, span[0]+find.start()+1))#, (span[0]+find.start(), span[1])])
                prev = span[0]+find.start()+1
            if tmp:
                tmp.append((prev, span[1]))
                del l1[i]
                for t in reversed(tmp):
                    l1.insert(i, t)
                continue
            del tmp[:]
            # dots and ending commas
            if text and (text[-1] in u".," and not (len(text) == 2 and text[0].isupper())):
                tmp = [(span[0], span[1]-1), (span[1]-1, span[1])]
            if tmp:
                del l1[i]
                for t in reversed(tmp):
                    l1.insert(i, t)
                continue
            i += 1
        
        spans = [Span(s[0], s[1]) for s in l1]
        spans = [span for span in spans if len(span) > 0]
        return spans
    
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
