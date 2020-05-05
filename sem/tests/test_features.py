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
import functools
import re

from sem.storage import (
    Sentence,
    compile_multiword,
    compile_map
)

from sem.features import (
    sentence_wrapper,
    limited_compose,
    bos,
    eos,
    is_upper_at,
    matches,
    subsequence,
    token,
    substitute,
    multiword_dictionary,
    token_gazetteer,
    apply_mapping,
    check_some,
    check_all,
    check_none
)


class TestFeatures(unittest.TestCase):
    def test_basic_getters(self):
        data = Sentence({
            "word": ["Ceci", "est", "un", "test", "."],
            "token": ["_Ceci", "_est", "_un", "_test", "_."]
        })

        current_word = sentence_wrapper(lambda x: x, x=0, y="word")
        previous_token = sentence_wrapper(lambda x: x, x=-1, y="token") # DictGetterFeature(entry="token", shift=-1)
        next_token = sentence_wrapper(lambda x: x, x=1, y="token") # DictGetterFeature(entry="token", shift=1)

        self.assertEquals(current_word(data), data.feature("word"))

        self.assertEquals(previous_token(data), ["", "_Ceci", "_est", "_un", "_test"])
        self.assertEquals(next_token(data), ["_est", "_un", "_test", "_.", ""])

    def test_arity_features(self):
        data = Sentence({"word": ["Ceci", "est", "un", "test", "."]})

        self.assertEquals(bos(data), [True, False, False, False, False])
        self.assertEquals(eos(data), [False, False, False, False, True])
        self.assertEquals(
            sentence_wrapper(str.lower, 0, "word")(data),
            [item.lower() for item in data.feature("word")]
        )

        # prefix_3 = SubstringFeature(getter=cwg, from_index=0, to_index=3, default="#")
        # for i in range(len(data)):
        #     self.assertEquals(
        #         prefix_3(data, i), data[i]["word"][prefix_3._from_index: prefix_3._to_index]
        #     )

        sw_upper = sentence_wrapper(functools.partial(is_upper_at, index=0), 0, "word")
        self.assertEquals(sw_upper(data), [True, False, False, False, False])

        e2a = sentence_wrapper(functools.partial(substitute, pattern="e", repl="a"), x=0, y="word")
        self.assertEquals(e2a(data), ["Caci", "ast", "un", "tast", "."])

        char_class = sentence_wrapper(
            limited_compose([
                functools.partial(substitute, pattern="[A-Z]", repl="A"),
                functools.partial(substitute, pattern="[a-z]", repl="a"),
                functools.partial(substitute, pattern="[0-9]", repl="0"),
                functools.partial(substitute, pattern="[^Aa0]", repl="x")
            ]),
            x=0,
            y="word"
        )
        self.assertEquals(char_class(data), ["Aaaa", "aaa", "aa", "aaaa", "x"])

    def test_regexp_features(self):
        data = Sentence({"word": ["Ceci", "est", "un", "test", "."]})

        check = functools.partial(matches, regexp=re.compile("^..."), y="word")
        self.assertEquals(check(data), [True, True, False, True, False])

        sub = functools.partial(subsequence, regexp=re.compile("^..."), y="word")
        self.assertEquals(sub(data), ["Cec", "est", "#", "tes", "#"])

        tokens = functools.partial(token, regexp=re.compile("^..."), y="word")
        self.assertEquals(tokens(data), ["Ceci", "est", "#", "test", "#"])

    def test_list_features(self):
        data = Sentence({"word": ["Ceci", "est", "un", "test", "."]})

        sw_upper = sentence_wrapper(functools.partial(is_upper_at, index=0), 0, "word")
        has_punctuation = functools.partial(matches, regexp=re.compile(r"^\."), y="word")

        some_f = functools.partial(check_some, features=[sw_upper, has_punctuation])
        all_f = functools.partial(check_all, features=[sw_upper, has_punctuation])
        none_f = functools.partial(check_none, features=[sw_upper, has_punctuation])

        self.assertEquals(some_f(data), [True, False, False, False, True])
        self.assertEquals(all_f(data), [False, False, False, False, False])
        self.assertEquals(none_f(data), [False, True, True, True, False])

    def test_dictionary_features(self):
        data = Sentence({"word": ["Ceci", "est", "un", "test", "."]})

        token = functools.partial(token_gazetteer, gazetteer=set(["Ceci", "test"]), y="word")
        multiword1 = functools.partial(
            multiword_dictionary,
            trie=compile_multiword(["Ceci est", "est un", "un", "."]),
            appendice="-test1",
            y="word"
        )
        multiword2 = functools.partial(
            multiword_dictionary,
            trie=compile_multiword(["test ."]),
            appendice="-test2",
            y="word"
        )
        mapper = functools.partial(
            apply_mapping, mapping=compile_map(["un\tune", "test\trévolution"]), y="word"
        )

        # self.assertEquals(token(data), [True, False, False, True, False])
        self.assertEquals(token(data), ["B", "O", "O", "B", "O"])

        self.assertEquals(multiword1(data), ["B-test1", "I-test1", "B-test1", "O", "B-test1"])
        self.assertEquals(multiword2(data), ["O", "O", "O", "B-test2", "I-test2"])

        self.assertEquals(mapper(data), ["O", "O", "une", "révolution", "O"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
