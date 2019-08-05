# -*- encoding: utf-8 -*-

"""
file: test_features.py

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

import unittest

from sem.features import IdentityFeature, DictGetterFeature
from sem.features import (
    BOSFeature,
    EOSFeature,
    LowerFeature,
    SubstringFeature,
    IsUpperFeature,
    SubstitutionFeature,
    SequencerFeature,
)  # arity features
from sem.features import CheckFeature, SubsequenceFeature, TokenFeature
from sem.features import SomeFeature, AllFeature, NoneFeature
from sem.features import TokenDictionaryFeature, MultiwordDictionaryFeature, MapperFeature


class TestFeatures(unittest.TestCase):
    def test_basic_getters(self):
        data = [
            {"word": "Ceci", "token": "_Ceci"},
            {"word": "est", "token": "_est"},
            {"word": "un", "token": "_un"},
            {"word": "test", "token": "_test"},
            {"word": ".", "token": "_."},
        ]

        identity = IdentityFeature()
        current_word = DictGetterFeature(entry="word", shift=0)
        previous_token = DictGetterFeature(entry="token", shift=-1)
        next_token = DictGetterFeature(entry="token", shift=1)

        self.assertEquals(identity("word"), "word")
        self.assertEquals(identity(data), data)
        self.assertEquals(identity(data[0]), data[0])
        self.assertEquals(identity(data[0]["word"]), "Ceci")
        self.assertEquals(identity(data[0]["token"]), "_Ceci")

        for i in range(len(data)):
            self.assertEquals(current_word(data, i), data[i]["word"])

        self.assertEquals(previous_token(data, 0), None)
        for i in range(1, len(data)):
            self.assertEquals(previous_token(data, i), data[i - 1]["token"])

        for i in range(len(data) - 1):
            self.assertEquals(next_token(data, i), data[i + 1]["token"])
        self.assertEquals(next_token(data, len(data) - 1), None)

    def test_arity_features(self):
        data = [{"word": "Ceci"}, {"word": "est"}, {"word": "un"}, {"word": "test"}, {"word": "."}]

        cwg = DictGetterFeature(entry="word", x=0)  # current word getter feature

        bos = BOSFeature(entry="word", getter=cwg)
        self.assertEquals(bos(data, 0), True)
        for i in range(1, len(data)):
            self.assertEquals(bos(data, i), False)

        eos = EOSFeature(getter=cwg)
        for i in range(len(data) - 1):
            self.assertEquals(eos(data, i), False)
        self.assertEquals(eos(data, len(data) - 1), True)

        lower = LowerFeature(getter=cwg)
        for i in range(len(data)):
            self.assertEquals(lower(data, i), data[i]["word"].lower())

        prefix_3 = SubstringFeature(getter=cwg, from_index=0, to_index=3, default="#")
        for i in range(len(data)):
            self.assertEquals(
                prefix_3(data, i), data[i]["word"][prefix_3._from_index: prefix_3._to_index]
            )

        sw_upper = IsUpperFeature(getter=cwg, index=0)
        self.assertEquals(sw_upper(data, 0), True)
        for i in range(1, len(data)):
            self.assertEquals(sw_upper(data, i), False)

        e2a = SubstitutionFeature("e", "a", getter=cwg)
        self.assertEquals(e2a(data, 0), "Caci")
        self.assertEquals(e2a(data, 1), "ast")
        self.assertEquals(e2a(data, 2), "un")
        self.assertEquals(e2a(data, 3), "tast")
        self.assertEquals(e2a(data, 4), ".")

        char_class = SequencerFeature(
            SubstitutionFeature("[A-Z]", "A", getter=cwg),
            SubstitutionFeature("[a-z]", "a"),
            SubstitutionFeature("[0-9]", "0"),
            SubstitutionFeature("[^Aa0]", "x"),
        )
        self.assertEquals(char_class(data, 0), "Aaaa")
        self.assertEquals(char_class(data, 1), "aaa")
        self.assertEquals(char_class(data, 2), "aa")
        self.assertEquals(char_class(data, 3), "aaaa")
        self.assertEquals(char_class(data, 4), "x")

    def test_regexp_features(self):
        data = [{"word": "Ceci"}, {"word": "est"}, {"word": "un"}, {"word": "test"}, {"word": "."}]

        cwg = DictGetterFeature(entry="word", x=0)  # current word getter feature

        check = CheckFeature("^...", getter=cwg)
        sub = SubsequenceFeature("^...", getter=cwg)
        token = TokenFeature("^...", getter=cwg)

        self.assertEquals(check(data, 0), True)
        self.assertEquals(check(data, 1), True)
        self.assertEquals(check(data, 2), False)
        self.assertEquals(check(data, 3), True)
        self.assertEquals(check(data, 4), False)

        self.assertEquals(sub(data, 0), "Cec")
        self.assertEquals(sub(data, 1), "est")
        self.assertEquals(sub(data, 2), "#")
        self.assertEquals(sub(data, 3), "tes")
        self.assertEquals(sub(data, 4), "#")

        self.assertEquals(token(data, 0), "Ceci")
        self.assertEquals(token(data, 1), "est")
        self.assertEquals(token(data, 2), "#")
        self.assertEquals(token(data, 3), "test")
        self.assertEquals(token(data, 4), "#")

    def test_list_features(self):
        data = [{"word": "Ceci"}, {"word": "est"}, {"word": "un"}, {"word": "test"}, {"word": "."}]

        cwg = DictGetterFeature(entry="word", x=0)  # current word getter feature
        sw_upper = IsUpperFeature(getter=cwg, index=0)
        has_punctuation = CheckFeature("^\\.", getter=cwg)

        some_f = SomeFeature(sw_upper, has_punctuation)
        all_f = AllFeature(sw_upper, has_punctuation)
        none_f = NoneFeature(sw_upper, has_punctuation)

        self.assertEquals(some_f(data, 0), True)
        self.assertEquals(some_f(data, 1), False)
        self.assertEquals(some_f(data, 2), False)
        self.assertEquals(some_f(data, 3), False)
        self.assertEquals(some_f(data, 4), True)

        self.assertEquals(all_f(data, 0), False)
        self.assertEquals(all_f(data, 1), False)
        self.assertEquals(all_f(data, 2), False)
        self.assertEquals(all_f(data, 3), False)
        self.assertEquals(all_f(data, 4), False)

        self.assertEquals(none_f(data, 0), False)
        self.assertEquals(none_f(data, 1), True)
        self.assertEquals(none_f(data, 2), True)
        self.assertEquals(none_f(data, 3), True)
        self.assertEquals(none_f(data, 4), False)

    def test_dictionary_features(self):
        data = [{"word": "Ceci"}, {"word": "est"}, {"word": "un"}, {"word": "test"}, {"word": "."}]

        cwg = DictGetterFeature(entry="word", x=0)  # current word getter feature
        token = TokenDictionaryFeature(getter=cwg, path=None, entries=["Ceci", "test"])
        multiword1 = MultiwordDictionaryFeature(
            entry="word", path=None, appendice="-test1", entries=["Ceci est", "est un", "un", "."]
        )
        multiword2 = MultiwordDictionaryFeature(
            entry="word", path=None, appendice="-test2", entries=["test ."]
        )
        mapper = MapperFeature(getter=cwg, path=None, entries=["un\tune", "test\trévolution"])

        self.assertEquals(token(data, 0), True)
        self.assertEquals(token(data, 1), False)
        self.assertEquals(token(data, 2), False)
        self.assertEquals(token(data, 3), True)
        self.assertEquals(token(data, 4), False)

        self.assertEquals(multiword1(data), ["B-test1", "I-test1", "B-test1", "O", "B-test1"])
        self.assertEquals(multiword2(data), ["O", "O", "O", "B-test2", "I-test2"])

        self.assertEquals(mapper(data, 0), "O")
        self.assertEquals(mapper(data, 1), "O")
        self.assertEquals(mapper(data, 2), "une")
        self.assertEquals(mapper(data, 3), "révolution")
        self.assertEquals(mapper(data, 4), "O")


if __name__ == "__main__":
    unittest.main(verbosity=2)
