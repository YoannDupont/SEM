# -*- encoding: utf-8 -*-

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

import sem.importers
from sem import SEM_DATA_DIR
from sem.storage import Document, Corpus
from sem.modules import EnrichModule, CleanModule, WapitiLabelModule, LabelConsistencyModule
from sem.modules.enrich import Entry
from sem.features import DictGetterFeature
from sem.features import BOSFeature, EOSFeature


class TestModules(unittest.TestCase):
    def test_enrich(self):
        document = Document("document", "Ceci est un test.")
        corpus = Corpus(["word"], sentences=[[
            {"word": "Ceci"},
            {"word": "est"},
            {"word": "un"},
            {"word": "test"},
            {"word": "."}
        ]])
        document._corpus = corpus

        features = []
        cwg = DictGetterFeature(entry="word", x=0)
        features.append(BOSFeature(name="BOS", entry="word", getter=cwg))
        features.append(EOSFeature(name="EOS", entry="word", getter=cwg))

        enrich = EnrichModule(bentries=[Entry("word")], features=features)

        self.assertEquals(document._corpus.fields, ["word"])

        enrich.process_document(document)

        self.assertEquals(document._corpus.fields, ["word", "BOS", "EOS"])

    def test_clean(self):
        document = Document("document", "Ceci est un test.")
        corpus = Corpus(["word", "remove"], sentences=[[
            {"word": "Ceci", "remove": "Ceci"},
            {"word": "est", "remove": "est"},
            {"word": "un", "remove": "un"},
            {"word": "test", "remove": "test"},
            {"word": ".", "remove": "."}
        ]])
        document._corpus = corpus

        self.assertEquals(document._corpus.fields, ["word", "remove"])

        clean = CleanModule(to_keep=["word"])
        clean.process_document(document)

        self.assertEquals(document._corpus.fields, ["word"])

    def test_wapiti_label(self):
        document = Document("document", "Ceci est un test.")
        corpus = Corpus(["word"], sentences=[[
            {"word": "Ceci"},
            {"word": "est"},
            {"word": "un"},
            {"word": "test"},
            {"word": "."}
        ]])
        document._corpus = corpus

        self.assertEquals(document._corpus.fields, ["word"])

        wapiti_label = WapitiLabelModule(
            SEM_DATA_DIR / "non-regression" / "models" / "model",
            "the_new_field"
        )
        wapiti_label.process_document(document)

        self.assertEquals(document._corpus.fields, ["word", "the_new_field"])

        sentence = document._corpus.sentences[0]
        self.assertEquals(sentence[0]["the_new_field"], "A")
        self.assertEquals(sentence[1]["the_new_field"], "B")
        self.assertEquals(sentence[2]["the_new_field"], "B")
        self.assertEquals(sentence[3]["the_new_field"], "A")
        self.assertEquals(sentence[4]["the_new_field"], "O")

    def test_label_consistency(self):
        corpus = Corpus(["word", "tag"], sentences=[
            [
                {"word": "Ceci", "tag": "B-tag"},
                {"word": "est", "tag": "O"},
                {"word": "un", "tag": "O"},
                {"word": "test", "tag": "O"},
                {"word": ".", "tag": "O"}
            ],
            [
                {"word": "Ceci", "tag": "O"},
                {"word": "est", "tag": "O"},
                {"word": "un", "tag": "O"},
                {"word": "test", "tag": "O"},
                {"word": ".", "tag": "O"}
            ],
            [
                {"word": "ceci", "tag": "O"},
                {"word": "est", "tag": "O"},
                {"word": "un", "tag": "O"},
                {"word": "test", "tag": "O"},
                {"word": ".", "tag": "O"}
            ],
        ])
        document = sem.importers.conll_data("document", corpus, "word")
        tags = []
        for sentence in document._corpus.sentences:
            for token in sentence:
                tags.append(token["tag"])
        self.assertEquals(tags.count("O"), 14)
        self.assertEquals(tags.count("B-tag"), 1)

        label_consistency = LabelConsistencyModule("tag", token_field="word")
        label_consistency.process_document(document)

        self.assertEquals(document._corpus.sentences[0][0]["tag"], "B-tag")
        self.assertEquals(document._corpus.sentences[1][0]["tag"], "B-tag")
        self.assertEquals(document._corpus.sentences[2][0]["tag"], "O")

        tags = []
        for sentence in document._corpus.sentences:
            for token in sentence:
                tags.append(token["tag"])
        self.assertEquals(tags.count("O"), 13)
        self.assertEquals(tags.count("B-tag"), 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
