#-*- encoding: utf-8 -*-

"""
file: test_modules.py

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

from sem.storage import Document, Corpus

from sem.modules import EnrichModule, CleanModule, WapitiLabelModule, LabelConsistencyModule

from sem.information import Entry, Informations
from sem.features import DictGetterFeature
from sem.features import BOSFeature, EOSFeature

class TestModules(unittest.TestCase):
    def test_enrich(self):
        document = Document("document", "Ceci est un test.")
        corpus = Corpus([u"word"], sentences=[[
            {u"word":u"Ceci"},
            {u"word":u"est"},
            {u"word":u"un"},
            {u"word":u"test"},
            {u"word":u"."}
        ]])
        document._corpus = corpus
        
        features = []
        cwg = DictGetterFeature(entry="word", x=0)
        features.append(BOSFeature(name="BOS", entry="word", getter=cwg))
        features.append(EOSFeature(name="EOS", entry="word", getter=cwg))
        
        informations = Informations(bentries=[Entry(u"word")], features=features)
        
        enrich = EnrichModule(informations)
        
        self.assertEquals(document._corpus.fields, [u"word"])
        
        enrich.process_document(document)
        
        self.assertEquals(document._corpus.fields, [u"word", u"BOS", u"EOS"])
    
    def test_clean(self):
        document = Document("document", "Ceci est un test.")
        corpus = Corpus([u"word", u"remove"], sentences=[[
            {u"word":u"Ceci", u"remove":u"Ceci"},
            {u"word":u"est", u"remove":u"est"},
            {u"word":u"un", u"remove":u"un"},
            {u"word":u"test", u"remove":u"test"},
            {u"word":u".", u"remove":u"."}
        ]])
        document._corpus = corpus
        
        self.assertEquals(document._corpus.fields, [u"word", u"remove"])
        
        clean = CleanModule(to_keep=[u"word"])
        clean.process_document(document)
        
        self.assertEquals(document._corpus.fields, [u"word"])
    
    def test_wapiti_label(self):
        document = Document("document", "Ceci est un test.")
        corpus = Corpus([u"word"], sentences=[[
            {u"word":u"Ceci"},
            {u"word":u"est"},
            {u"word":u"un"},
            {u"word":u"test"},
            {u"word":u"."}
        ]])
        document._corpus = corpus
        
        self.assertEquals(document._corpus.fields, [u"word"])
        
        wapiti_label = WapitiLabelModule(os.path.join(SEM_DATA_DIR, "non-regression", "models", "model"), u"the_new_field")
        wapiti_label.process_document(document)
        
        self.assertEquals(document._corpus.fields, [u"word", u"the_new_field"])
        
        sentence = document._corpus.sentences[0]
        self.assertEquals(sentence[0]["the_new_field"], u"A")
        self.assertEquals(sentence[1]["the_new_field"], u"B")
        self.assertEquals(sentence[2]["the_new_field"], u"B")
        self.assertEquals(sentence[3]["the_new_field"], u"A")
        self.assertEquals(sentence[4]["the_new_field"], u"O")
    
    def test_wapiti_label(self):
        corpus = Corpus([u"word", u"tag"], sentences=[
            [
                {u"word":u"Ceci", u"tag":u"B-tag"},
                {u"word":u"est", u"tag":u"O"},
                {u"word":u"un", u"tag":u"O"},
                {u"word":u"test", u"tag":u"O"},
                {u"word":u".", u"tag":u"O"}
            ],
            [
                {u"word":u"Ceci", u"tag":u"O"},
                {u"word":u"est", u"tag":u"O"},
                {u"word":u"un", u"tag":u"O"},
                {u"word":u"test", u"tag":u"O"},
                {u"word":u".", u"tag":u"O"}
            ],
            [
                {u"word":u"ceci", u"tag":u"O"},
                {u"word":u"est", u"tag":u"O"},
                {u"word":u"un", u"tag":u"O"},
                {u"word":u"test", u"tag":u"O"},
                {u"word":u".", u"tag":u"O"}
            ],
        ])
        document = Document.from_corpus("document", corpus, u"word")
        tags = []
        for sentence in document._corpus.sentences:
            for token in sentence:
                tags.append(token[u"tag"])
        self.assertEquals(tags.count(u"O"), 14)
        self.assertEquals(tags.count(u"B-tag"), 1)
        
        label_consistency = LabelConsistencyModule(u"tag", token_field=u"word")
        label_consistency.process_document(document)
        
        self.assertEquals(document._corpus.sentences[0][0][u"tag"], u"B-tag")
        self.assertEquals(document._corpus.sentences[1][0][u"tag"], u"B-tag")
        self.assertEquals(document._corpus.sentences[2][0][u"tag"], u"O")
        
        tags = []
        for sentence in document._corpus.sentences:
            for token in sentence:
                tags.append(token[u"tag"])
        self.assertEquals(tags.count(u"O"), 13)
        self.assertEquals(tags.count(u"B-tag"), 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
