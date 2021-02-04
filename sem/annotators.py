# -*- coding: utf-8 -*-

"""
file: annotators.py

Description: some annotators that can be used in SEM.

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

import pathlib
import functools

from sem.features import (directory_feature, xml2feat)
from sem.CRF import Model as WapitiModel
from sem.misc import check_model_available


class LexicaAnnotator:
    """An annotator that uses lexica to provide annotations."""

    def __init__(self, field, lexica, *args, **kwargs):
        """The initialisation method of LexicaAnnotator.

        Parameters
        ----------
        lexica : function sem.storage.Sentence -> list[str]
            Lexica is a functools.partial of `sem.features.directory_feature` with multiple
            lexica that are either token or multiword features, used to provide annotations.
        field : str
            the name of the CoNLL field where annotations will be put. It is also the name
            of the annotation set where annotations will be stored.
        """
        self._field = field
        self._feature = lexica

    @classmethod
    def load(cls, field, features=None, xmllist=(), path=None, token_field="word", **kwargs):
        lexica = None
        features = features or []
        if features:
            lexica = functools.partial(directory_feature, features=features)
            return LexicaAnnotator(field, lexica)
        elif xmllist:
            path = path or pathlib.Path(".")
            for child in xmllist:
                features.append(xml2feat(child, default_entry=token_field, path=path))
            lexica = functools.partial(directory_feature, features=features)
            return LexicaAnnotator(field, lexica)
        else:
            raise ValueError(f"No data provided for loading {cls.__name__}.")

    def process_document(self, document, *args, **kwargs):
        tags = []
        for sequence in document.corpus:
            tagging = self._feature(sequence)
            sequence.add(tagging[:], self._field)
            tags.append(tagging[:])

        document.add_annotation_from_tags(tags, self._field, self._field)


class WapitiAnnotator:
    """An annotator that uses a (python implementation of) wapiti model to provide annotations."""

    def __init__(self, field, model):
        self._field = field
        self._model = model

    @classmethod
    def load(cls, field, location, input_encoding=None, *args, **kwargs):
        check_model_available(location)
        return (field, WapitiModel.from_wapiti_model(location, encoding=input_encoding))

    def process_document(
        self, document, annotation_name=None, annotation_fields=None, *args, **kwargs
    ):
        if annotation_name is None:
            annotation_name = str(self._field)

        tags = []
        for sequence in document.corpus:
            tagging, _, _ = self._model.tag_viterbi(sequence)
            tags.append(tagging[:])

        document.add_annotation_from_tags(tags, self._field, annotation_name)


def load(kind, *args, **kwargs):
    clss = __annotators[kind]
    return clss.load(*args, **kwargs)


__annotators = {
    "lexica": LexicaAnnotator,
    "wapiti": WapitiAnnotator
}


def get_annotator(name):
    return __annotators[name]
