# -*- coding: utf-8 -*-

"""
file: trie.py

Description: Trie object definition. A Trie is here a very convenient
way to model multiword dictionaries. They are, here, the same thing
as a Prefix Tree Automaton (PTA).

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

from sem.constants import NUL

class Trie(object):
    """
    The Trie object.

    Attributes
    ----------
    _data : dict
        the structure where all the entries of a multiword dictionary
        are loaded.
    """

    def __init__(self, filename=None, encoding=None):
        self._data = {}

        if filename:
            encoding = encoding or "UTF-8"
            for l in open(filename, "rU", encoding=encoding):
                seq = l.strip().split()

                self.add(seq)

    def __iter__(self):
        seq = []
        # Depth First Search
        def dfs(dic):
            keys = set(dic.keys())
            found = NUL in keys

            if found:
                keys.remove(NUL)
                if dic[NUL]:
                    yield seq
            keys = list(keys)
            keys.sort()
            for k in keys:
                seq.append(k)
                for i in dfs(dic[k]):
                    yield i
                seq.pop()

        for i in dfs(self._data):
            yield i

    def __len__(self):
        length = 0
        for i in self:
            length += 1
        return length

    @property
    def data(self):
        return self._data

    def add(self, sequence):
        iterator = sequence.__iter__()
        d = self._data

        try:
            while True:
                token = next(iterator)

                if token not in d:
                    d[token] = {}

                d = d[token]
        except StopIteration:
            pass

        d[NUL] = {}

    def add_with_value(self, sequence, value):
        iterator = iter(sequence)
        d = self._data

        try:
            while True:
                token = next(iterator)

                if token not in d:
                    d[token] = {}

                d = d[token]
        except StopIteration:
            pass

        d[NUL] = value

    def contains(self, sequence):
        iterator = iter(sequence)
        d = self._data
        result = True

        try:
            while True:
                token = next(iterator)

                if token not in d:
                    result = False
                    break

                d = d[token]
        except StopIteration:
            pass

        return result and (NUL in d)

    def remove(self, sequence):
        def remove(dic, iterator):
            try:
                elt = next(iterator)
                if elt in dic:
                    remove(dic[elt], iterator)
                    if dic[elt] == {}:
                        del dic[elt]
            except StopIteration:
                if NUL in dic:
                    del dic[NUL]

        remove(self._data, iter(sequence))

    def goto(self, sequence):
        iterator = iter(sequence)
        d = self._data
        result = True

        try:
            while True:
                token = next(iterator)

                if token not in d:
                    result = False
                    break

                d = d[token]
        except StopIteration:
            pass

        if result:
            return d
        else:
            return None
