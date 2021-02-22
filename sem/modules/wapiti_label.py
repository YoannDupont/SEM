# -*- coding:utf-8 -*-

"""
file: wapiti_label.py

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

import time
import argparse
import tempfile
from datetime import timedelta

from wapiti.api import Model as WapitiModel

import sem.importers
import sem.logger
from sem.exporters import CoNLLExporter
from sem.modules.sem_module import SEMModule as RootModule
from sem.misc import check_model_available


def from_string(mdl_str):
    with tempfile.NamedTemporaryFile() as fl:
        fl.write(mdl_str)
        fl.seek(0)
        return WapitiModel(encoding="utf-8", model=fl.name)


class SEMModule(RootModule):
    def __init__(self, model, field, annotation_fields=None, **kwargs):
        super(SEMModule, self).__init__(**kwargs)
        self._expected_mode = kwargs.get("expected_mode", self.pipeline_mode)

        self._model = str(model)
        self._field = field
        self._annotation_fields = annotation_fields
        if type(self._annotation_fields) == str:
            self._annotation_fields = self._annotation_fields.split(",")

        if self.pipeline_mode == "all" or self._expected_mode in ("all", self.pipeline_mode):
            check_model_available(model)
            self._wapiti_model = WapitiModel(encoding="utf-8", model=self._model)
            with open(self._model, "rb") as input_stream:
                self._mdl_str = input_stream.read()
        else:
            self._mdl_str = None
            self._wapiti_model = None

    def __getstate__(self):
        state = self.__dict__.copy()
        del state['_wapiti_model']
        return state

    def __setstate__(self, newstate):
        self.__dict__.update(newstate)
        if self._mdl_str is not None:
            self._wapiti_model = from_string(self._mdl_str)
        elif self._model:
            self._wapiti_model = WapitiModel(encoding="utf-8", model=self._model)

    @property
    def field(self):
        return self._field

    @property
    def model(self):
        return self._model

    def check_mode(self, expected_mode):
        if (not self._wapiti_model) and self.pipeline_mode == expected_mode:
            check_model_available(self._model)
            self._wapiti_model = WapitiModel(encoding="utf-8", model=self._model)
            with open(self._model, "rb") as input_stream:
                self._mdl_str = input_stream.read()

    def process_document(self, document, encoding="utf-8", **kwargs):
        """
        Annotate document with Wapiti.

        Parameters
        ----------
        document : sem.storage.Document
            the input data. It is a document with only a content
        """

        start = time.time()

        if self._field in document.corpus.fields:
            sem.logger.warning(
                "field %s already exists in document, not annotating", self._field
            )

            tags = [[s[self._field] for s in sentence] for sentence in document.corpus]
            document.add_annotation_from_tags(tags, self._field, self._field)
        else:
            sem.logger.info("annotating document with %s field", self._field)

            self._label_document(document, encoding)

        laps = time.time() - start
        sem.logger.info("in %s", timedelta(seconds=laps))

    def _label_document(self, document, encoding="utf-8"):
        fields = self._annotation_fields or document.corpus.fields
        tags = []
        for sequence in document.corpus:
            tagging = self._tag_as_wrapper(sequence, fields)
            tags.append(tagging[:])

        document.add_annotation_from_tags(tags, self._field, self._field)

    def _tag_as_wrapper(self, sequence, fields, encoding="utf-8"):
        seq_str = "\n".join(
            "\t".join(str(it) for it in item)
            for item in zip(*[sequence.feature(field) for field in fields])
        ).encode(encoding)
        s = self._wapiti_model.label_sequence(seq_str).decode(encoding)
        return s.strip().split("\n")


def main(argv=None):
    wapiti_label(parser.parse_args(argv))


def wapiti_label(args):
    for sentence in sem.importers.read_conll(args.infile, "utf-8"):
        fields = ["field-{}".format(i) for i in range(len(sentence[0]))]
        word_field = fields[0]
        break

    document = sem.importers.conll_file(args.infile, fields, word_field)
    labeler = SEMModule(args.model, fields)
    exporter = CoNLLExporter()

    labeler.process_document(document)

    exporter.document_to_file(document, None, args.outfile)


parser = argparse.ArgumentParser("An annotation tool for SEM.")

parser.add_argument("infile", help="The input file (CoNLL format)")
parser.add_argument("model", help="The name of the model to label data with")
parser.add_argument("outfile", help="The output file")
