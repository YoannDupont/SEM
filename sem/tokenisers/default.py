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

import re

import sem.constants
from sem.storage import Span, SpannedBounds

# adding some "basic" things to not tokenise across languages.
_forbidden = [sem.constants.url_re, sem.constants.email_re]
_force = []

spaces = re.compile("\\s+", re.U+re.M)

def word_spans(content):
    l = [match.span() for match in spaces.finditer(content)]
    l1 = [(l[i][1], l[i+1][0]) for i in range(len(l)-1)]

    if l[0][0] != 0:
        l1.insert(0, (0, l[0][0]))
    if l[-1][1] != len(content):
        l1.append((l[-1][1], len(content)))

    return [Span(span[0], span[1]) for span in l1]

def sentence_bounds(content, token_spans):
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
        if token in "\r\n":
            sent_bounds.add_last(Span(index, index+1))
    sent_bounds.add_last(Span(len(token_spans), len(token_spans)))

    return sent_bounds

def paragraph_bounds(content, sentence_spans, token_spans):
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
        if substring.count("\n") > 1:
            paragraph_bounds.append(Span(index, index))
    paragraph_bounds.append(Span(len(sentence_spans), len(sentence_spans)))

    return paragraph_bounds
