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
from sem.storage import Document, Corpus, Sentence, Entry
from sem.processors import (
    EnrichProcessor, CleanProcessor, WapitiLabelProcessor, LabelConsistencyProcessor
)
from sem.features import bos, eos


class TestProcessors(unittest.TestCase):
    def test_enrich(self):
        corpus = Corpus(
            fields=["word"], sentences=[Sentence({"word": ["Ceci", "est", "un", "test", "."]})]
        )
        document = Document("document", "Ceci est un test.", corpus=corpus)

        enrich = EnrichProcessor(bentries=[Entry("word")], features=[(bos, "BOS"), (eos, "EOS")])

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

        clean = CleanProcessor(to_keep=["word"])
        clean.process_document(document)

        self.assertEquals(document._corpus.fields, ["word"])

    def test_wapiti_label(self):
        model_as_string = (
            "#mdl#2#5\n"
            "#rdr#1/0/0\n"
            "14:u:word=%x[0,0],\n"
            "#qrk#3\n"
            "1:A,\n"
            "1:B,\n"
            "1:O,\n"
            "#qrk#5\n"
            "11:u:word=Ceci,\n"
            "10:u:word=est,\n"
            "9:u:word=un,\n"
            "11:u:word=test,\n"
            "8:u:word=.,\n"
            "0=0x1.0000000000000p+3\n"
            "4=0x1.0000000000000p+3\n"
            "7=0x1.0000000000000p+3\n"
            "9=0x1.0000000000000p+3\n"
            "14=0x1.0000000000000p+3\n"
        )

        corpus = Corpus(
            fields=["word"], sentences=[Sentence({"word": ["Ceci", "est", "un", "test", "."]})]
        )
        document = Document("document", "Ceci est un test.", corpus=corpus)

        self.assertEquals(document._corpus.fields, ["word"])

        wapiti_label = WapitiLabelProcessor(None, "the_new_field", model_str=model_as_string)
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

        label_consistency = LabelConsistencyProcessor("tag", token_field="word")
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
