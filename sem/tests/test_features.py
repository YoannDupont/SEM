#-*- encoding: utf-8 -*-

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
import codecs, os.path

from sem import SEM_DATA_DIR

from sem.features import IdentityFeature, DictGetterFeature, FindForwardFeature, FindBackwardFeature
from sem.features import BOSFeature, EOSFeature, LowerFeature, SubstringFeature, IsUpperFeature, SubstitutionFeature, SequencerFeature # arity features
from sem.features import CheckFeature, SubsequenceFeature, TokenFeature
from sem.features import SomeFeature, AllFeature, NoneFeature
from sem.features import TokenDictionaryFeature, MultiwordDictionaryFeature, MapperFeature

class TestFeatures(unittest.TestCase):
    def test_basic_getters(self):
        data = [
            {u"word":u"Ceci", u"token":u"_Ceci"},
            {u"word":u"est", u"token":u"_est"},
            {u"word":u"un", u"token":u"_un"},
            {u"word":u"test", u"token":u"_test"},
            {u"word":u".", u"token":u"_."}
        ]
        
        identity = IdentityFeature()
        current_word = DictGetterFeature(entry=u"word", shift=0)
        previous_token = DictGetterFeature(entry=u"token", shift=-1)
        next_token = DictGetterFeature(entry=u"token", shift=1)
        
        self.assertEquals(identity(u"word"), u"word")
        self.assertEquals(identity(data), data)
        self.assertEquals(identity(data[0]), data[0])
        self.assertEquals(identity(data[0][u"word"]), u"Ceci")
        self.assertEquals(identity(data[0][u"token"]), u"_Ceci")
        
        for i in range(len(data)):
            self.assertEquals(current_word(data, i), data[i][u"word"])
        
        self.assertEquals(previous_token(data, 0), None)
        for i in range(1, len(data)):
            self.assertEquals(previous_token(data, i), data[i-1][u"token"])
        
        for i in range(len(data)-1):
            self.assertEquals(next_token(data, i), data[i+1][u"token"])
        self.assertEquals(next_token(data, len(data)-1), None)
    
    def test_arity_features(self):
        data = [
            {u"word":u"Ceci"},
            {u"word":u"est"},
            {u"word":u"un"},
            {u"word":u"test"},
            {u"word":u"."}
        ]
        
        cwg = DictGetterFeature(entry="word", x=0) # current word getter feature
        
        bos = BOSFeature(entry="word", getter=cwg)
        self.assertEquals(bos(data, 0), True)
        for i in range(1, len(data)):
            self.assertEquals(bos(data, i), False)
        
        eos = EOSFeature(getter=cwg)
        for i in range(len(data)-1):
            self.assertEquals(eos(data, i), False)
        self.assertEquals(eos(data, len(data)-1), True)
        
        lower = LowerFeature(getter=cwg)
        for i in range(len(data)):
            self.assertEquals(lower(data, i), data[i][u"word"].lower())
        
        prefix_3 = SubstringFeature(getter=cwg, from_index=0, to_index=3, default=u"#")
        for i in range(len(data)):
            self.assertEquals(prefix_3(data, i), data[i][u"word"][prefix_3._from_index : prefix_3._to_index])
        
        sw_upper = IsUpperFeature(getter=cwg, index=0)
        self.assertEquals(sw_upper(data, 0), True)
        for i in range(1, len(data)):
            self.assertEquals(sw_upper(data, i), False)
        
        e2a = SubstitutionFeature("e", "a", getter=cwg)
        self.assertEquals(e2a(data, 0), u"Caci")
        self.assertEquals(e2a(data, 1), u"ast")
        self.assertEquals(e2a(data, 2), u"un")
        self.assertEquals(e2a(data, 3), u"tast")
        self.assertEquals(e2a(data, 4), u".")
        
        char_class = SequencerFeature(SubstitutionFeature("[A-Z]", "A", getter=cwg), SubstitutionFeature("[a-z]", "a"), SubstitutionFeature("[0-9]", "0"), SubstitutionFeature("[^Aa0]", "x"))
        self.assertEquals(char_class(data, 0), u"Aaaa")
        self.assertEquals(char_class(data, 1), u"aaa")
        self.assertEquals(char_class(data, 2), u"aa")
        self.assertEquals(char_class(data, 3), u"aaaa")
        self.assertEquals(char_class(data, 4), u"x")
    
    def test_regexp_features(self):
        data = [
            {u"word":u"Ceci"},
            {u"word":u"est"},
            {u"word":u"un"},
            {u"word":u"test"},
            {u"word":u"."}
        ]
        
        cwg = DictGetterFeature(entry="word", x=0) # current word getter feature
        sw_upper = IsUpperFeature(getter=cwg, index=0)
        
        check = CheckFeature(u"^...", getter=cwg)
        sub = SubsequenceFeature(u"^...", getter=cwg)
        token = TokenFeature(u"^...", getter=cwg)
        
        self.assertEquals(check(data, 0), True)
        self.assertEquals(check(data, 1), True)
        self.assertEquals(check(data, 2), False)
        self.assertEquals(check(data, 3), True)
        self.assertEquals(check(data, 4), False)
        
        self.assertEquals(sub(data, 0), u"Cec")
        self.assertEquals(sub(data, 1), u"est")
        self.assertEquals(sub(data, 2), u"#")
        self.assertEquals(sub(data, 3), u"tes")
        self.assertEquals(sub(data, 4), u"#")
        
        self.assertEquals(token(data, 0), u"Ceci")
        self.assertEquals(token(data, 1), u"est")
        self.assertEquals(token(data, 2), u"#")
        self.assertEquals(token(data, 3), u"test")
        self.assertEquals(token(data, 4), u"#")
    
    def test_list_features(self):
        data = [
            {u"word":u"Ceci"},
            {u"word":u"est"},
            {u"word":u"un"},
            {u"word":u"test"},
            {u"word":u"."}
        ]
        
        cwg = DictGetterFeature(entry="word", x=0) # current word getter feature
        sw_upper = IsUpperFeature(getter=cwg, index=0)
        has_punctuation = CheckFeature(u"^\\.", getter=cwg)
        
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
        data = [
            {u"word":u"Ceci"},
            {u"word":u"est"},
            {u"word":u"un"},
            {u"word":u"test"},
            {u"word":u"."}
        ]
        
        cwg = DictGetterFeature(entry="word", x=0) # current word getter feature
        token = TokenDictionaryFeature(getter=cwg, path=None, entries=[u"Ceci", u"test"])
        multiword1 = MultiwordDictionaryFeature(entry="word", path=None, appendice="-test1", entries=[u"Ceci est", u"est un", u"un", "."])
        multiword2 = MultiwordDictionaryFeature(entry="word", path=None, appendice="-test2", entries=[u"test ."])
        mapper = MapperFeature(getter=cwg, path=None, entries=[u"un\tune", u"test\trévolution"])
        
        self.assertEquals(token(data, 0), True)
        self.assertEquals(token(data, 1), False)
        self.assertEquals(token(data, 2), False)
        self.assertEquals(token(data, 3), True)
        self.assertEquals(token(data, 4), False)
        
        self.assertEquals(multiword1(data), [u"B-test1", u"I-test1", u"B-test1", u"O", u"B-test1"])
        self.assertEquals(multiword2(data), [u"O", u"O", u"O", u"B-test2", u"I-test2"])
        
        self.assertEquals(mapper(data, 0), u"O")
        self.assertEquals(mapper(data, 1), u"O")
        self.assertEquals(mapper(data, 2), u"une")
        self.assertEquals(mapper(data, 3), u"révolution")
        self.assertEquals(mapper(data, 4), u"O")


if __name__ == '__main__':
    unittest.main(verbosity=2)
