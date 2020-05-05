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
from sem.storage import Document, Corpus, Sentence
from sem.modules import EnrichModule, CleanModule, WapitiLabelModule, LabelConsistencyModule
from sem.modules.enrich import Entry
from sem.features import bos, eos


class TestModules(unittest.TestCase):
    def test_enrich(self):
        corpus = Corpus(
            fields=["word"], sentences=[Sentence({"word": ["Ceci", "est", "un", "test", "."]})]
        )
        document = Document("document", "Ceci est un test.", corpus=corpus)

        enrich = EnrichModule(bentries=[Entry("word")], features=[(bos, "BOS"), (eos, "EOS")])

        self.assertEquals(document._corpus.fields, ["word"])

        enrich.process_document(document)

        self.assertEquals(document._corpus.fields, ["word", "BOS", "EOS"])


    def test_clean(self):
        corpus = Corpus(
            fields=["word", "remove"],
            sentences=[
                Sentence({
                    "word": ["Ceci", "est", "un", "test", "."],
                    "remove": ["Ceci", "est", "un", "test", "."],
                })
            ]
        )
        document = Document("document", "Ceci est un test.", corpus=corpus)

        self.assertEquals(document._corpus.fields, ["word", "remove"])

        clean = CleanModule(to_keep=["word"])
        clean.process_document(document)

        self.assertEquals(document._corpus.fields, ["word"])


    def test_wapiti_label(self):
        corpus = Corpus(
            fields=["word"], sentences=[Sentence({"word": ["Ceci", "est", "un", "test", "."]})]
        )
        document = Document("document", "Ceci est un test.", corpus=corpus)

        self.assertEquals(document._corpus.fields, ["word"])

        wapiti_label = WapitiLabelModule(
            SEM_DATA_DIR / "non-regression" / "models" / "model", "the_new_field"
        )
        wapiti_label.process_document(document)

        self.assertEquals(document._corpus.fields, ["word", "the_new_field"])

        sentence = document._corpus.sentences[0]
        self.assertEquals(sentence.feature("the_new_field"), ["A", "B", "B", "A", "O"])


    def test_label_consistency(self):
        corpus = Corpus(
            fields=["word", "tag"],
            sentences=[
                Sentence({
                    "word": ["Ceci", "est", "un", "test", "."],
                    "tag": ["B-tag", "O", "O", "O", "O"]
                }),
                Sentence({
                    "word": ["Ceci", "est", "un", "test", "."],
                    "tag": ["O", "O", "O", "O", "O"]
                }),
                Sentence({
                    "word": ["ceci", "est", "un", "test", "."],
                    "tag": ["O", "O", "O", "O", "O"]
                })
            ],
        )
        document = sem.importers.conll_data("document", corpus, "word")
        tags = []
        for sentence in document._corpus.sentences:
            tags.extend(sentence.feature("tag"))
        self.assertEquals(tags.count("O"), 14)
        self.assertEquals(tags.count("B-tag"), 1)

        self.assertEquals(document._corpus.sentences[0].feature("tag")[0], "B-tag")
        self.assertEquals(document._corpus.sentences[1].feature("tag")[0], "O")
        self.assertEquals(document._corpus.sentences[2].feature("tag")[0], "O")

        label_consistency = LabelConsistencyModule("tag", token_field="word")
        label_consistency.process_document(document)

        self.assertEquals(document._corpus.sentences[0].feature("tag")[0], "B-tag")
        self.assertEquals(document._corpus.sentences[1].feature("tag")[0], "B-tag")
        self.assertEquals(document._corpus.sentences[2].feature("tag")[0], "O")

        tags = []
        for sentence in document._corpus.sentences:
            tags.extend(sentence.feature("tag"))
        self.assertEquals(tags.count("O"), 13)
        self.assertEquals(tags.count("B-tag"), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
