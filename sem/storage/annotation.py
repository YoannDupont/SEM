# -*- coding: utf-8 -*-

"""
file: annotation.py

Description: defines multiple objects used for annotation. An annotation
is a set of values positioned using a segmentation.

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

from sem.storage.span import Span
from sem.constants import BEGIN, IN, LAST, SINGLE, OUT


class Tag(object):

    __slots__ = ("_span", "_value", "levels", "ids")

    def __init__(self, value, lb, ub, length=-1):
        self._span = Span(lb, ub, length=length)
        self._value = value
        self.levels = value.strip(".").split(".")
        self.ids = {}

    def __len__(self):
        return len(self._span)

    def __eq__(self, tag):
        return (
            tag is not None and self.value == tag.value and self.lb == tag.lb and self.ub == tag.ub
        )

    def __str__(self):
        return "{0},{1}".format(self.value, self.span)

    def __unicode__(self):
        return "{0},{1}".format(self.value, self.span)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value.strip()
        self.levels = value.strip(".").split(".")

    @property
    def span(self):
        return Span(self._span.lb, self._span.ub)

    @property
    def lb(self):
        return self._span.lb

    @lb.setter
    def lb(self, lb):
        self._span.lb = lb

    @property
    def ub(self):
        return self._span.ub

    @ub.setter
    def ub(self, ub):
        self._span.ub = ub

    def kind(self):
        return "chunking"

    def getLevel(self, nth):
        if nth >= len(self.levels):
            return ""
        return self.levels[nth]

    def setLevel(self, nth, value):
        while nth >= len(self.levels):
            self.levels.append("")
        self.levels[nth] = value
        while self.levels[-1] == "":
            del self.levels[-1]
        while len(self.levels) > nth + 1:
            del self.levels[-1]
        self._value = ".".join(self.levels).strip(".")

    def getValue(self):
        if self.levels == []:
            return self.value

        values = []
        do_it = True
        i = -1
        while do_it:
            i += 1
            value = self.getLevel(i)
            do_it = value != ""
            if do_it:
                values.append(value)
        return ".".join(values)


class Annotation(object):
    def __init__(self, name, reference=None, annotations=None):
        self._name = name
        self._reference = reference
        if annotations is None:
            self._annotations = []
        else:
            self._annotations = annotations

    def __len__(self):
        return len(self._annotations)

    def __getitem__(self, i):
        return self._annotations[i]

    def __iter__(self):
        return iter(self._annotations)

    @property
    def name(self):
        return self._name

    @property
    def reference(self):
        return self._reference

    @property
    def annotations(self):
        return self._annotations

    @annotations.setter
    def annotations(self, annotations):
        self._annotations = annotations

    def add(self, annotation, after=None):
        i = 0
        if after is None:
            while i < len(self._annotations):
                if annotation.lb > self._annotations[i].lb:
                    None
                elif annotation.lb > self._annotations[i].ub:
                    None
                elif annotation.lb > self._annotations[i].ub:
                    break
                elif annotation.lb == self._annotations[i].lb:
                    if self._annotations[i].ub <= annotation.ub:
                        break
                else:
                    break
                i += 1
        else:
            while i < len(self._annotations):
                if self._annotations[i] == after:
                    i += 1
                    break
                i += 1
        self._annotations.insert(i, annotation)

    def append(self, annotation):
        self._annotations.append(annotation)

    def extend(self, annotations):
        self._annotations.extend(annotations)

    def remove(self, annotation):
        try:
            self._annotations.remove(annotation)
        except ValueError:  # annotation not in annotations
            pass

    def sort(self):
        self._annotations.sort(key=lambda x: (x.lb, -x.ub, x.value))

    def get_reference_annotations(self):
        if self.reference is None:
            return [Tag(a.value, a.lb, a.ub) for a in self.annotations]
        else:
            reference_spans = self.reference.get_reference_spans()
            return [
                Tag(
                    element.value,
                    reference_spans[element.lb].lb,
                    reference_spans[element.ub - 1].ub,
                )
                for element in self.annotations
            ]


def get_top_level(annotations):
    result = annotations[:]
    modified = True
    while modified:
        modified = False
        for i in range(len(result) - 1):
            modified = result[i].lb <= result[i + 1].lb and result[i].ub > result[i + 1].lb
            if modified:
                del result[i + 1]
                break
    return result


def get_bottom_level(annotations):
    result = annotations[:]
    modified = True
    while modified:
        modified = False
        for i in range(len(result) - 1):
            modified = result[i].lb <= result[i + 1].lb <= result[i].ub
            if modified:
                del result[i]
                break
    return result


str2filter = {"top level": get_top_level, "bottom level": get_bottom_level}


def chunk_annotation_from_sentence(sentence, column, shift=0, strict=False):
    annotation = Annotation("")
    start = 0
    length = 0
    value = ""
    last = len(sentence) - 1
    for index, element in enumerate(sentence):
        tag = element[column]
        flag = tag[0]

        if tag in OUT:
            if value != "":  # we just got out of a chunk
                annotation.append(Tag(value, start + shift, 0, length=length))
            value = ""
            length = 0
        elif flag in BEGIN:
            if value != "":  # begin after non-empty chunk ==> add annnotation
                annotation.append(Tag(value, start + shift, 0, length=length))
            value = tag[2:]
            start = index
            length = 1
            if index == last:  # last token ==> add annotation
                annotation.append(Tag(value, start + shift, 0, length=length))
        elif flag in IN:
            if value != tag[2:] and strict:
                raise ValueError(
                    'Got different values for same chunk: "{}" <> "{}"'.format(tag[2:], value)
                )
            length += 1
            if index == last:  # last token ==> add annotation
                annotation.append(Tag(value, start + shift, 0, length=length))
        elif flag in LAST:
            annotation.append(Tag(value, start + shift, 0, length=length + 1))
            value = ""
            length = 0
        elif flag in SINGLE:
            if value != "":  # begin after non-empty chunk ==> add annnotation
                annotation.append(Tag(value, start + shift, 0, length=length))
                value = ""
                length = 0
            annotation.append(Tag(tag[2:], index + shift, 0, length=1))

    return annotation


def chunk_annotation_from_corpus(corpus, column, name, reference=None, strict=False):
    """
    Return an annotation from a sentence. The annotation has to have one
    of the following tagging schemes:
       - BIO (Begin In Out)
       - BILOU (Begin In Last Out Unit-length)
       - BIOES (Begin In Out End Single)

    we define a general approach to handle the three at the same time.
    """

    annotation = Annotation(name, reference=reference)
    shift = 0
    for nth, sentence in enumerate(corpus):  # enumerate for better exception message
        annotation.extend(
            chunk_annotation_from_sentence(sentence, column, shift=shift, strict=strict).annotations
        )
        shift += len(sentence)
    return annotation


def tag_annotation_from_sentence(sentence, column, shift=0, strict=False):
    def is_begin(tag):
        return tag[0] != "_"

    annotation = Annotation("")
    start = 0
    length = 0
    value = ""
    last = len(sentence) - 1
    for index, element in enumerate(sentence):
        tag = element[column]

        if is_begin(tag):
            if value != "":  # begin after non-empty chunk ==> add annnotation
                annotation.append(Tag(value, start + shift, 0, length=length))
            value = tag
            start = index
            length = 1
            if index == last:  # last token ==> add annotation
                annotation.append(Tag(value, start + shift, 0, length=length))

        else:
            if value != tag[1:]:
                if strict:
                    raise ValueError(
                        'Got different values for same POS: "{}" <> "{}"'.format(tag[1:], value)
                    )
                else:
                    value = tag[1:]  # most probable tag at the end.
            length += 1
            if index == last:  # last token ==> add annotation
                annotation.append(Tag(value, start + shift, 0, length=length))
    return annotation


def tag_annotation_from_corpus(corpus, column, name, reference=None, strict=False):
    """
    Return an annotation from a sentence. The annotation has the following
    scheme:
        add "_" at the beginning of an annotation if it "continues"
        the previous tag. It is the same as BIO, "B-" is replaced by None
        and "I-" by "_".
    """

    annotation = Annotation(name, reference=reference)
    shift = 0
    for nth, sentence in enumerate(corpus):  # enumerate for better exception message
        annotation.extend(
            tag_annotation_from_sentence(sentence, column, shift=shift, strict=strict).annotations
        )
        shift += len(sentence)
    return annotation


def annotation_from_sentence(sentence, column, shift=0, strict=False):
    """
    Return an Annotation object for sentence. Checks sentence before
    calling either tag_annotation_from_sentence
    or chunk_annotation_from_sentence
    """
    flags = BEGIN + IN + LAST + SINGLE + OUT
    if all([token[column][0] in flags for token in sentence]):
        return chunk_annotation_from_sentence(sentence, column, shift=shift, strict=strict)
    else:
        return tag_annotation_from_sentence(sentence, column, shift=shift, strict=strict)
