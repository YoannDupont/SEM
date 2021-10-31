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


def model_from_string(mdl_str, encoding="utf-8"):
    with tempfile.NamedTemporaryFile() as fl:
        fl.write(mdl_str.encode(encoding=encoding))
        fl.seek(0)
        return WapitiModel(encoding=encoding, model=fl.name)


class SEMModule(RootModule):
    def __init__(
        self, model, field, annotation_fields=None, model_str=None, model_encoding="utf-8", **kwargs
    ):
        super(SEMModule, self).__init__(**kwargs)
        self._expected_mode = kwargs.get("expected_mode", self.pipeline_mode)

        if model is not None and model_str is not None:
            raise ValueError("both 'model' and 'model_str' were provided, only one may be given.")

        self._wapiti_model = None
        self._mdl_str = model_str
        self._model_encoding = model_encoding
        self._model = model
        if self._model is not None:
            self._model = str(self._model)
        self._field = field
        self._annotation_fields = annotation_fields
        if type(self._annotation_fields) == str:
            self._annotation_fields = self._annotation_fields.split(",")

        self.load_model()

    def __getstate__(self):
        state = self.__dict__.copy()
        del state['_wapiti_model']
        state['_wapiti_model'] = None
        return state

    def __setstate__(self, newstate):
        self.__dict__.update(newstate)
        if self._mdl_str is not None:
            self._wapiti_model = model_from_string(self._mdl_str, self._model_encoding)
        elif self._model is not None:
            # loading a model through api will not raise an exception if file does not exist
            try:
                with open(self._model):
                    pass
                self._wapiti_model = WapitiModel(encoding="utf-8", model=self._model)
            except FileNotFoundError:
                sem.logger.warning(
                    "Model file {} does not exist, you will need to train one.".format(self._model)
                )
        else:
            sem.logger.warning("No model in serialized file, you will need to train one.")

    @property
    def field(self):
        return self._field

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, model):
        self._model = model
        if self._model is not None:
            self._model = str(self._model)

        pipeline_mode = self.pipeline_mode
        if pipeline_mode == "all" or self._expected_mode in ("all", "label", pipeline_mode):
            check_model_available(self._model)
            self._wapiti_model = WapitiModel(encoding="utf-8", model=self._model)
            with open(self._model, "rb") as input_stream:
                self._mdl_str = input_stream.read()
        else:
            sem.logger.warning("Invalid mode for loading model: %s", pipeline_mode)

    def check_mode(self, expected_mode):
        if (self._wapiti_model is None) and self.pipeline_mode == expected_mode:
            check_model_available(self._model)
            self._wapiti_model = WapitiModel(encoding="utf-8", model=self._model)
            with open(self._model, "rb") as input_stream:
                self._mdl_str = input_stream.read()

    def load_model(self):
        if self._model is not None:
            check_model_available(self._model)
            self._wapiti_model = WapitiModel(encoding="utf-8", model=self._model)
        elif self._mdl_str is not None:
            self._wapiti_model = model_from_string(self._mdl_str, self._model_encoding)
        else:
            sem.logger.warning("No available model to load.")

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

    def _tag_as_wrapper(self, sequence, fields, encoding=None):
        encoding = encoding or self._model_encoding
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
