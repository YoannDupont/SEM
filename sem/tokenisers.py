"""
file: tokenisers.py

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
from sem.storage import Span, add_last


spaces = re.compile(r"\s+", re.U + re.M)


def bounds2spans(bounds):
    """Create spans from bounds.
    """
    spans = [Span(bounds[i].ub, bounds[i + 1].lb) for i in range(0, len(bounds) - 1)]
    spans = [span for span in spans if span.lb != span.ub]
    return spans


class Tokeniser:
    """Root tokeniser class"""
    def __init__(self):
        # adding some "basic" things to not tokenise across languages.
        self._forbidden = [sem.constants.url_re, sem.constants.email_re]
        self._force = []

    def word_spans(self, content):
        l1 = [match.span() for match in spaces.finditer(content)]
        l2 = [(l1[i][1], l1[i + 1][0]) for i in range(len(l1) - 1)]

        if l1[0][0] != 0:
            l2.insert(0, (0, l1[0][0]))
        if l1[-1][1] != len(content):
            l2.append((l1[-1][1], len(content)))

        return [Span(span[0], span[1]) for span in l2]

    def sentence_bounds(self, content, token_spans):
        """Return a list of bounds matching sentences.

        Parameters
        ----------
        content : str
            the content to get sentence bounds for.
        token_spans : list of Span
            the list of tokens spans.

        Returns
        -------
        list[span]
            The spans of the sentence bounds.
        """

        sent_bounds = [Span(0, 0)]
        for index, span in enumerate(token_spans):
            token = content[span.lb: span.ub]
            if token in "\r\n":
                add_last(sent_bounds, Span(index, index + 1))
        add_last(sent_bounds, Span(len(token_spans), len(token_spans)))

        return sent_bounds

    def sentence_spans(self, content, token_spans):
        return bounds2spans(self.sentence_bounds(content, token_spans))

    def paragraph_bounds(self, content, sentence_spans, token_spans):
        """Return a list of bounds matching paragraphs.

        Parameters
        ----------
        content : str
            the content to find paragraph bounds for.
        sentence_spans : list[Span]
            the list of sentence spans.
        token_spans : list[Span]
            the list of token spans.

        Returns
        -------
        list[Span]
            The list of paragraph bounds in content.
        """

        s_spans = [Span(token_spans[e.lb].lb, token_spans[e.ub - 1].ub) for e in sentence_spans]
        bounds = [Span(0, 0)]
        for index, sentence in enumerate(sentence_spans[1:], 1):
            substring = content[s_spans[index - 1].ub: s_spans[index].lb]
            if substring.count("\n") > 1:
                bounds.append(Span(index, index))
        bounds.append(Span(len(sentence_spans), len(sentence_spans)))

        return bounds

    def paragraph_spans(self, content, sentence_spans, token_spans):
        return bounds2spans(self.paragraph_bounds(content, sentence_spans, token_spans))


class FrenchTokeniser(Tokeniser):
    def __init__(self):
        self._dots = re.compile(r"(\.{2,})$")
        self._cls = re.compile(r"(-je|-tu|-nous|-vous|(:?-t)?-(:?on|ils?|elles?))\b", re.U + re.I)
        self._is_abn = re.compile(r"\b(dr|me?lles?|mme?s?|mr?s?|st)\.?$", re.U + re.I)
        self._abbrev = re.compile(r"\b(i\.e\.|e\.g\.|c-à-d)", re.U + re.I)
        self._digit_valid = set("0123456789,.-")
        self._simple_smileys = re.compile("^[:;x=],?-?[()DdPp]+$")

        self._forbidden = [self._is_abn, self._abbrev, self._simple_smileys]

        self._force = [sem.constants.url_re, sem.constants.email_re, self._cls]

        self._word = re.compile("^[^\\W\\d]+$", re.U + re.M)
        self._number_with_unit = re.compile("([0-9][^0-9,.])|([^0-9,.][0-9])")
        self._atomic = re.compile('[;:«»()\\[\\]{}=+*$£€/\\"?!…%€$£]')
        self._comma_not_number = re.compile("(?<=[^0-9]),(?![0-9])", re.U + re.M)
        self._apostrophe = re.compile("(?=['ʼ’])", re.U + re.M)

    def word_spans(self, content):
        spans = []
        offset = 0

        part = content
        l1 = [match.span() for match in spaces.finditer(part)]

        if l1:
            l2 = [(l1[i][1], l1[i + 1][0]) for i in range(len(l1) - 1)]
            if l1[0][0] != 0:
                l2.insert(0, (0, l1[0][0]))
            if l1[-1][1] != len(part):
                l2.append((l1[-1][1], len(part)))
        else:
            l2 = [(0, len(part))]

        i = 0
        while i < len(l2):
            span = l2[i]
            text = part[span[0]: span[1]]
            shift = span[0]
            if len(text) == 1:
                i += 1
                continue
            if self._word.match(text):
                i += 1
                continue
            found = False
            for force in self._force:
                found = force.search(text)
                if found:
                    s, e = found.start(), found.end()
                    del l2[i]
                    l2.insert(i, (shift + e, shift + len(text)))
                    l2.insert(i, (shift + s, shift + e))
                    l2.insert(i, (shift, shift + s))
                    i += 2
                    break
            if found:
                continue
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
            for find in self._atomic.finditer(text):
                if prev != shift + find.start():
                    tmp.append((prev, shift + find.start()))
                tmp.append((shift + find.start(), shift + find.end()))
                prev = shift + find.end()
            if tmp:
                if prev != span[1]:
                    tmp.append((prev, span[1]))
                del l2[i]
                for t in reversed(tmp):
                    l2.insert(i, t)
                continue
            # commas
            prev = span[0]
            find = self._comma_not_number.search(text)
            if find:
                tmp.extend(
                    [
                        (prev, shift + find.start()),
                        (shift + find.start(), shift + find.end()),
                        (shift + find.end(), span[1]),
                    ]
                )
                prev = shift + find.end() + 1
            if tmp:
                del l2[i]
                for t in reversed(tmp):
                    l2.insert(i, t)
                continue
            # apostrophes
            prev = span[0]
            for find in self._apostrophe.finditer(text):
                tmp.append((prev, shift + find.start() + 1))
                prev = shift + find.start() + 1
            if prev < span[1]:
                tmp.append((prev, span[1]))
            if len(tmp) > 1:
                del l2[i]
                for t in reversed(tmp):
                    l2.insert(i, t)
                continue
            del tmp[:]
            # number with unit
            prev = span[0]
            for find in self._number_with_unit.finditer(text):
                tmp.append((prev, span[0] + find.start() + 1))
                prev = span[0] + find.start() + 1
            if tmp:
                tmp.append((prev, span[1]))
                del l2[i]
                for t in reversed(tmp):
                    l2.insert(i, t)
                continue
            # dots and ending commas
            if text and (text[-1] in ".," and not (len(text) == 2 and text[0].isupper())):
                mdots = self._dots.search(text)
                length = len(mdots.group(1)) if mdots else 1
                if length != len(text):
                    tmp = [(span[0], span[1] - length), (span[1] - length, span[1])]
            if tmp:
                del l2[i]
                for t in reversed(tmp):
                    l2.insert(i, t)
                continue
            i += 1

        spans = [Span(s[0] + offset, s[1] + offset) for s in l2 if s[0] < s[1]]
        spans = [span for span in spans if len(span) > 0]
        return spans

    def sentence_bounds(self, content, token_spans):
        sent_bounds = []
        tokens = [content[t.lb: t.ub] for t in token_spans]
        opening_counts = [0 for i in token_spans]
        count = 0
        for i in range(len(opening_counts)):
            if tokens[i] in "«([":
                count += 1
            elif tokens[i] in "»)]":
                count -= 1
            opening_counts[i] = count

        sent_bounds.append(Span(0, 0))
        for index, span in enumerate(token_spans):
            token = tokens[index]
            if re.match("^[?!]+$", token) or token == "…" or re.match("\\.\\.+", token):
                sent_bounds.append(Span(index + 1, index + 1))
            elif token == ".":
                if opening_counts[index] == 0:
                    sent_bounds.append(Span(index + 1, index + 1))
            elif (
                index < len(token_spans) - 1
                and content[span.ub: token_spans[index + 1].lb].count("\n") > 1
            ):
                sent_bounds.append(Span(index + 1, index + 1))
        sent_bounds.append(Span(len(tokens), len(tokens)))

        return sent_bounds


class EnglishTokeniser(Tokeniser):
    def word_spans(self, s):
        bounds = [Span(0, 0)]

        atomic = set(';:«»()[]{}=+*$£€/\\"?!%€$£')
        apostrophe = set("'ʼ’")

        for index, c in enumerate(s):
            is_first = index == 0
            is_last = index == len(s) - 1
            if c.isspace():
                add_last(bounds, Span(index, index + 1))
            elif c in atomic:
                add_last(bounds, Span(index, index))
                bounds.append(Span(index + 1, index + 1))
            elif c in apostrophe:
                if is_first or is_last:
                    add_last(bounds, Span(index, index))
                    bounds.append(Span(index + 1, index + 1))
                elif s[index + 1] == s[index]:
                    bounds.append(Span(index, index + 1))
                else:
                    if s[index - 1] == "n" and s[index + 1] == "t":
                        bounds.append(Span(index - 1, index - 1))
                        bounds.append(Span(index + 2, index + 2))
                    elif s[index + 1] == "s":
                        bounds.append(Span(index, index))
                        bounds.append(Span(index + 2, index + 2))
                    else:
                        add_last(bounds, Span(index, index))
            elif c in ".,":
                if is_first or is_last:
                    add_last(bounds, Span(index, index))
                    bounds.append(Span(index + 1, index + 1))
                elif (is_first or not s[index - 1].isdigit()) and (
                    is_last or not s[index - 1].isdigit()
                ):
                    add_last(bounds, Span(index, index))
                    bounds.append(Span(index + 1, index + 1))

        bounds.append(Span(len(s), len(s)))

        return bounds2spans(bounds)

    def sentence_bounds(self, content, token_spans):
        sent_bounds = []
        tokens = [content[t.lb: t.ub] for t in token_spans]
        openings = set(["«", "(", "[", "``"])
        closings = set(["»", ")", "]", "''"])
        opening_counts = [0 for i in tokens]
        count = 0
        for i in range(len(opening_counts)):
            if tokens[i] in openings:
                count += 1
            elif tokens[i] in closings:
                count -= 1
            opening_counts[i] = count

        sent_bounds.append(Span(0, 0))
        for index, token in enumerate(tokens):
            if re.match("^[?!]+$", token) or token == "…" or re.match(r"\.\.+", token):
                sent_bounds.append(Span(index + 1, index + 1))
            elif token == ".":
                if opening_counts[index] == 0:
                    sent_bounds.append(Span(index + 1, index + 1))
        sent_bounds.append(Span(len(tokens), len(tokens)))

        return sent_bounds


__tokenisers = {
    "default": Tokeniser,
    "fr": FrenchTokeniser,
    "en": EnglishTokeniser
}


def get_tokeniser(name):
    """Return the right tokeniser given name.

    Parameters
    ----------
    name : str
        the name of the tokeniser

    Returns
    -------
    Tokeniser
        The tokeniser matching name
    """
    return __tokenisers[name]
