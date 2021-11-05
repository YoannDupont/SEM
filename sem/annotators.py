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

from sem.features import (directory_feature, xml2feat, multiword_dictionary)
from sem.CRF import Model as WapitiModel
from sem.util import check_model_available
from sem.storage import (compile_multiword, chunks_to_annotation, get_top_level)


class LexicaAnnotator:
    """An annotator that uses lexica to provide annotations."""

    __strategies = ("replace", "overriding", "non-overriding")

    def __init__(self, field, lexica, strategy="replace", *args, **kwargs):
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
        self._strategy = strategy
        if self._strategy not in LexicaAnnotator.__strategies:
            raise ValueError(f"Unsupported strategy: '{strategy}' {LexicaAnnotator.__strategies}")

    @classmethod
    def load(
        cls,
        field,
        features=None,
        xmllist=(),
        path=None,
        lexica=None,
        token_field="word",
        strategy="replace",
        **kwargs
    ):
        lexica = lexica or {}
        dirfeat = None  # directory_feature
        features = features or []
        if features:
            dirfeat = functools.partial(directory_feature, features=features)
            return LexicaAnnotator(field, dirfeat)
        elif xmllist:
            path = path or pathlib.Path(".")
            for child in xmllist:
                features.append(xml2feat(child, default_entry=token_field, path=path))
            dirfeat = functools.partial(directory_feature, features=features)
            return LexicaAnnotator(field, dirfeat)
        elif lexica:
            feats = []
            for tag_value, entries in lexica.items():
                appendice = f"-{tag_value}"
                trie = compile_multiword(entries)
                feat = functools.partial(
                    multiword_dictionary, trie=trie, y=token_field, appendice=appendice
                )
                feats.append(feat)
            dirfeat = functools.partial(directory_feature, features=feats)
            return LexicaAnnotator(field, dirfeat, strategy=strategy)
        else:
            raise ValueError(f"No data provided for loading {cls.__name__}.")

    def process_document(self, document, *args, **kwargs):
        tags = []
        for sequence in document.corpus:
            tagging = self._feature(sequence)
            try:
                existing = sequence.feature(self._field)
            except KeyError:
                existing = []
            tagging = self.merge(tagging, existing)
            sequence.add(tagging[:], self._field)
            tags.append(tagging[:])

        document.add_annotation_from_tags(tags, self._field, self._field)

    def merge(self, new, old):
        strategy = self._strategy
        if strategy == "replace":
            return new
        elif strategy == "overriding":
            source = chunks_to_annotation(new)
            candidates = chunks_to_annotation(old)
        elif strategy == "non-overriding":
            source = chunks_to_annotation(old)
            candidates = chunks_to_annotation(new)

        indices_new = [set(range(ann.lb, ann.ub)) for ann in source]
        for candidate in candidates:
            indices = set(range(candidate.lb, candidate.ub))
            if not any(indices & idxs for idxs in indices_new):
                source.add(candidate)
        source = get_top_level(source)
        tags = ["O" for _ in new]
        for tag in source:
            val = tag.value
            tags[tag.lb] = f"B-{val}"
            for i in range(tag.lb+1, tag.ub):
                tags[i] = f"I-{val}"
        return tags


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
