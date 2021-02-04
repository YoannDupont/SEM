# -*- coding: utf-8 -*-

"""file: storage.py

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

import pathlib
import cgi
import re

try:
    from xml.etree import cElementTree as ET
except ImportError:
    from xml.etree import ElementTree as ET

try:
    from HTMLParser import HTMLParser
except ImportError:
    from html.parser import HTMLParser

import sem
import sem.misc
import sem.logger
from sem.constants import BEGIN, IN, LAST, SINGLE, OUT
from sem.constants import NUL


class Holder(object):
    def __init__(self, **kwargs):
        self.__dict__ = kwargs

    def __getitem__(self, field):
        return getattr(self, field)

    def __setitem__(self, field, value):
        return setattr(self, field, value)

    def get(self, field, default=None):
        return getattr(self, field, default)


class Span:
    """The Span object.

    Attributes
    ----------
    _lb : int
        the lower bound of a Span.
    _ub : int
        the upper bound of a Span.
    """

    __slots__ = ("_lb", "_ub")

    def __init__(self, lb, ub, length=-1):
        self._lb = min(lb, ub) if length < 0 else lb
        self._ub = max(lb, ub) if length < 0 else lb + length

    def __eq__(self, span):
        return self.lb == span.lb and self.ub == span.ub

    def __contains__(self, i):
        try:
            return self._lb <= i and i < self._ub
        except TypeError:
            return (self.lb <= i.lb) and (i.ub <= self.ub)

    def __len__(self):
        return self._ub - self._lb

    def __str__(self):
        return "[{span.lb}:{span.ub}]".format(span=self)

    @property
    def lb(self):
        return self._lb

    @property
    def ub(self):
        return self._ub

    @lb.setter
    def lb(self, lb):
        self._lb = min(lb, self._ub)

    @ub.setter
    def ub(self, ub):
        self._ub = max(ub, self._lb)

    def strictly_contains(self, i):
        return i > self._lb and i < self.ub

    def expand_lb(self, length):
        self._lb -= length

    def expand_ub(self, length):
        self._ub += length


class SpannedBounds:
    """The SpannedBounds object. Its purpose is to represent (word, sentence, etc.)
    bounds as spans to later produce (word, sentence, etc.) spans.

    Attributes
    ----------
    _bounds : list of Span
        the list of bounds between words, sentences, etc.
    _forbidden : set of int
        the list of indices that cannot be a word bound. It is forbidden
        to split a word at this index
    """

    def __init__(self):
        self._bounds = []
        self._forbidden = set()

    def __iter__(self):
        for e in self._bounds:
            yield e

    def __getitem__(self, i):
        return self._bounds[i]

    def __len__(self):
        return len(self._bounds)

    def add_forbiddens_regex(self, regex, s):
        for match in regex.finditer(s):
            for index in range(match.start() + 1, match.end()):
                self._forbidden.add(index)

    def force_regex(self, regex, s):
        """Applies a regex for elements that should be segmented in a certain
        way and splits elements accordingly.
        """

        for match in regex.finditer(s):
            self.add(Span(match.start(), match.start()))
            self.add(Span(match.end(), match.end()))

    def find(self, i):
        """Locate an index "i" somewhere in self._bounds."""

        for nth, span in enumerate(self._bounds):
            if i < span.lb:
                return (nth, False)
            elif i > span.ub:
                continue
            elif i in span:
                return (nth, True)
        return (-1, False)

    def append(self, span):
        """Appends "span" at the end of bounds (Span list)."""

        for index in range(span.lb, span.ub + 1):
            if self.is_forbidden(index):
                return

        if len(self._bounds) > 0:
            if span in self._bounds[-1] or span == self._bounds[-1]:
                return
            if len(span) == 0 and self._bounds[-1].ub >= span.lb:
                return

        self._bounds.append(span)

    def add(self, span):
        """Add "span" at the best index of self._bounds"""

        for index in range(span.lb, span.ub):
            if self.is_forbidden(index):
                return

        index, found = self.find(span.lb)
        if found:
            return
        else:
            if index > 0 and self[index - 1].lb == self[index].ub:
                None
            elif index == -1:
                self._bounds.append(span)
            else:
                self._bounds.insert(index, span)

    def add_last(self, span):
        """Appends "span" at the end of bounds (Span list). If the last
        span's upper bound is equal to "span's" lower bound, the last
        span's upper bound is extended instead.
        """

        for index in range(span.lb, span.ub + 1):
            if self.is_forbidden(index):
                return
        if span in self._bounds[-1]:
            return

        if self._bounds[-1].ub == span.lb:
            self._bounds[-1].expand_ub(span.ub - self._bounds[-1].ub)
        else:
            self._bounds.append(span)

    def is_forbidden(self, i):
        return i in self._forbidden


class Tag:

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


class Annotation:
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


def chunks_to_annotation(lst, shift=0, strict=False):
    annotation = Annotation("")
    start = 0
    length = 0
    value = ""
    last = len(lst) - 1
    for index, tag in enumerate(lst):
        flag = tag[0]
        if flag in OUT:
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


def chunk_annotation_from_sentence(sentence, column, shift=0, strict=False):
    return chunks_to_annotation(sentence.feature(column), shift=shift, strict=strict)


def chunk_annotation_from_corpus(corpus, column, name, reference=None, strict=False):
    """Return an annotation from a sentence. The annotation has to have one
    of the following tagging schemes:
       - BIO (Begin In Out)
       - BILOU (Begin In Last Out Unit-length)
       - BIOES (Begin In Out End Single)

    we define a general approach to handle the three at the same time.
    """

    annotation = Annotation(name, reference=reference)
    shift = 0
    for sentence in corpus:
        annotation.extend(
            chunk_annotation_from_sentence(sentence, column, shift=shift, strict=strict).annotations
        )
        shift += len(sentence)
    return annotation


def tag_annotation_from_sentence(sentence, column, shift=0, strict=False):
    def is_begin(tag):
        return tag[0] != "_" or tag.startswith("__")

    annotation = Annotation("")
    start = 0
    length = 0
    value = ""
    last = len(sentence) - 1
    for index, tag in enumerate(sentence.feature(column)):
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
    """Return an annotation from a sentence. The annotation has the following
    scheme:
        add "_" at the beginning of an annotation if it "continues"
        the previous tag. It is the same as BIO, "B-" is replaced by None
        and "I-" by "_".
    """
    annotation = Annotation(name, reference=reference)
    shift = 0
    for sentence in corpus:
        annotation.extend(
            tag_annotation_from_sentence(sentence, column, shift=shift, strict=strict).annotations
        )
        shift += len(sentence)
    return annotation


def annotation_from_sentence(sentence, column, shift=0, strict=False):
    """Return an Annotation object for sentence. Checks sentence before
    calling either tag_annotation_from_sentence
    or chunk_annotation_from_sentence
    """
    flags = BEGIN + IN + LAST + SINGLE + OUT
    if all([token[column][0] in flags for token in sentence]):
        return chunk_annotation_from_sentence(sentence, column, shift=shift, strict=strict)
    else:
        return tag_annotation_from_sentence(sentence, column, shift=shift, strict=strict)


_train_set = set(["train", "eval", "evaluate", "evaluation"])
_train = "train"
_label_set = set(["label", "annotate", "annotation"])
_label = "label"
_modes = _train_set | _label_set
_equivalence = dict(
    [[mode, _train] for mode in _train_set] + [[mode, _label] for mode in _label_set]
)


class Entry:
    """The Entry object. It represents a field's identifier in a CoNLL corpus.
    An Entry may be used only in certain circumstances: for example, the
    output tag may only appear in train mode.
    """

    def __init__(self, name, mode="label"):
        if mode not in _modes:
            raise ValueError("Unallowed mode for entry: {0}".format(mode))
        self._name = name
        self._mode = _equivalence[mode]

    def __eq__(self, other):
        return self.name == other.name

    @property
    def name(self):
        return self._name

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, mode):
        self._mode = _equivalence[mode]

    @property
    def is_train(self):
        return self.mode == _train

    @property
    def is_label(self):
        return self.mode == _label

    @staticmethod
    def fromXML(xml_element):
        return Entry(**xml_element.attrib)

    def has_mode(self, mode):
        return self.mode == _equivalence[mode]


class Sentence:

    __slots__ = ("_features")

    def __init__(self, features=None):
        self._features = features or {}
        if self._features:
            iterator = iter(self._features.items())
            lst = len(next(iterator)[1])
            for key, value in self._features.items():
                if len(value) != lst:
                    raise ValueError("Invalid sentence: features of different lengths.")

    def __len__(self):
        keys = self.keys()
        if keys:
            return len(self._features[list(keys)[0]])
        return 0

    def conll(self, keys):
        return "\n".join("\t".join(seq) for seq in zip(*[self.feature(key) for key in keys]))

    def keys(self):
        return self._features.keys()

    def add(self, feature, key):
        """Add a feature to the sentence by mapping the feature function
        to the sentence.

        Parameters
        ----------
        feature : function Sentence -> list or list
            the feature function to apply to the Sentence or the list of values
        key : str
            The key where to put the output of the feature function
        """
        try:
            feature.__call__
        except AttributeError:  # not callable
            value = feature
        else:
            value = feature(self)
        self._features[key] = value

    def update(self, features_keys):
        """Update Sentence with every feature given in argument.

        Parameters
        ----------
        features_keys : List[(function Sentence -> list, str)]
            the list of "feature function" and "key" pairs to add the Sentence.
        """
        for feature, key in features_keys:
            self.add(feature, key)

    def feature(self, name):
        return self._features[name]


class Corpus:
    def __init__(self, sentences=None, fields=None):
        self.sentences = sentences or []
        self._fields = fields

    def __contains__(self, item):
        return item in self.fields

    def __len__(self):
        return len(self.sentences)

    def __iter__(self):
        for element in self.sentences:
            yield element

    def __unicode__(self):
        return self.unicode(self.fields)

    @property
    def fields(self):
        return self._fields or self.sentences[0].keys()

    @fields.setter
    def fields(self, value):
        missing = sorted(set(value) - set(self.sentences[0].keys()))
        if missing:
            raise KeyError("missing fields: {}".format(','.join(missing)))
        self._fields = value

    def unicode(self, fields, separator="\t"):
        sentences = []
        for sentence in self:
            sentences.append([])
            for token in zip(*[sentence.feature(key) for key in fields]):
                sentences[-1].append(("\t".join(token)) + "\n")
        return "\n".join(["".join(sentence) for sentence in sentences])

    def is_empty(self):
        return 0 == len(self.sentences)

    def has_key(self, key):
        return key in self.fields

    def from_sentences(self, sentences, field_name="word"):
        del self.sentences[:]

        for sentence in sentences:
            self.sentences.append({field_name: sentence})

    def from_segmentation(self, content, tokens, sentences, field_name="word"):
        self.sentences = [
            Sentence({
                field_name: [
                    content[token.lb: token.ub]
                    for token in tokens.spans[sentence.lb: sentence.ub]
                ]
            })
            for sentence in sentences
        ]

    def write(self, fd, fields=None):
        for sentence in self:
            for token in zip(*[sentence.feature(key) for key in (fields or self.fields)]):
                fd.write(("\t".join(str(item) for item in token)) + "\n")
            fd.write("\n")


def compile_token(iterator):
    tokens = set()
    for item in iterator:
        item = item.split("#", 1)[0].strip()
        if item:
            tokens.add(item)
    return tokens


def compile_multiword(iterator):
    trie = Trie()
    for item in iterator:
        item = item.split("#", 1)[0].strip()
        if item:
            seq = item.split()
            trie.add(seq)
    return trie


def compile_map(iterator):
    out_map = {}
    for item in iterator:
        item = item.strip()
        if item != "":
            try:
                key, value = item.split("\t")
            except ValueError:
                key = item
                value = ""
            out_map[key] = value
    return out_map


class Segmentation:
    """Segmentation is just a holder for bounds. Those bounds can be word
    bounds or sentence bounds for example.
    By itself, it is not very useful, it become good in the context of
    a document for which it hold minimum useful information
    """

    def __init__(self, name, reference=None, spans=None):
        """parameters
        ----------
        name: unicode
            the name of the segmentation (tokens, sentences, paragraphs, etc.)
        reference: unicode or Segmentation
            if unicode: the name of the referenced segmentation in the document
            if Segmentation: the referenced segmentation
        spans: list of span
        bounds: list of span
        """

        self._name = name
        self._document = None
        self._reference = reference
        self._spans = spans

    def __len__(self):
        return len(self.spans)

    def __getitem__(self, i):
        return self._spans[i]

    def __iter__(self):
        for element in self.spans:
            yield element

    def append(self, span):
        if self._spans is None:
            self._spans = []
        self._spans.append(span)

    @property
    def name(self):
        return self._name

    @property
    def reference(self):
        return self._reference

    @property
    def spans(self):
        return self._spans

    def get_reference_spans(self):
        """returns spans according to the reference chain."""

        if self.reference is None:
            return self.spans
        else:
            reference_spans = self.reference.get_reference_spans()
            return [
                Span(reference_spans[element.lb].lb, reference_spans[element.ub - 1].ub)
                for element in self.spans
            ]


class Document:
    def __init__(
        self, name, content=None, encoding=None, lang=None, mime_type=None, corpus=None,
        original_content=None, **kwargs
    ):
        self._name = name
        self._content = content
        self.original_content = original_content
        self._segmentations = {}
        self._annotations = {}
        self._corpus = corpus or Corpus()
        self._metadatas = {}
        if encoding is not None:
            self._metadatas["encoding"] = encoding
        if lang is not None:
            self._metadatas["lang"] = lang
        if mime_type is not None:
            self._metadatas["MIME"] = mime_type

    @property
    def name(self):
        return self._name

    @property
    def content(self):
        return self._content

    @property
    def corpus(self):
        return self._corpus

    @content.setter
    def content(self, content):
        self._content = content

    @property
    def segmentations(self):
        return self._segmentations

    @property
    def annotations(self):
        return self._annotations

    @property
    def metadatas(self):
        return self._metadatas

    @staticmethod
    def from_xml(xml, chunks_to_load=None, load_subtypes=True, type_separator="."):
        if isinstance(xml, str):
            data = ET.parse(xml)
        elif isinstance(xml, ET.ElementTree):
            data = xml
        elif isinstance(xml, type(ET.Element("a"))):  # did not ind a better way to do this
            data = xml
        else:
            raise TypeError("Invalid type for loading XML-SEM document: {0}".format(type(xml)))

        if isinstance(data, ET.ElementTree):
            root = data.getroot()
        elif isinstance(data, type(ET.Element("a"))):
            root = data

        if root.tag == "sem":
            root = list(root)[0]
        elif root.tag != "document":
            raise TypeError("Invalid XML document type for XML-SEM document: {0}".format(root.tag))

        htmlparser = HTMLParser()
        document = Document(root.attrib.get("name", "_DOCUMENT_"))
        for element in list(root):
            if element.tag == "metadata":
                document._metadatas = element.attrib
            elif element.tag == "content":
                document.content = htmlparser.unescape(element.text)
            elif element.tag == "segmentations":
                for segmentation in list(element):
                    spans = [
                        Span(
                            lb=int(span.attrib.get("start", span.attrib["s"])),
                            ub=0,
                            length=int(span.attrib.get("length", span.attrib["l"])),
                        )
                        for span in list(segmentation)
                    ]
                    reference = segmentation.get("reference", None)
                    if reference:
                        reference = document.segmentation(reference)
                    document.add_segmentation(
                        Segmentation(segmentation.attrib["name"], spans=spans, reference=reference)
                    )
            elif element.tag == "annotations":
                for annotation in list(element):
                    tags = []
                    for tag in list(annotation):
                        value = tag.attrib.get("value", tag.attrib["v"])
                        if not load_subtypes:
                            value = value.strip(type_separator).split(type_separator)[0]
                        tags.append(
                            Tag(
                                value=value,
                                lb=int(tag.attrib.get("start", tag.attrib["s"])),
                                ub=0,
                                length=int(tag.attrib.get("length", tag.attrib["l"])),
                            )
                        )
                    reference = annotation.get("reference", None)
                    if reference:
                        reference = document.segmentation(reference)
                    annotation = Annotation(annotation.attrib["name"], reference=reference)
                    annotation.annotations = tags
                    document.add_annotation(annotation)

        if document.segmentation("tokens") and document.segmentation("sentences"):
            document.corpus.from_segmentation(
                document.content,
                document.segmentation("tokens"),
                document.segmentation("sentences"),
            )

            if chunks_to_load is not None:
                for chunk_to_load in chunks_to_load:
                    cur_annot = document.annotation(chunk_to_load)
                    if cur_annot and cur_annot.reference is None:
                        document.set_reference(cur_annot.name, "tokens")
                    i = 0
                    sent_iter = iter(document.corpus)
                    shift = 0
                    present = set([(a.lb, a.ub) for a in cur_annot])
                    for sentence in document.segmentation("sentences"):
                        sent = next(sent_iter)
                        annots = []
                        while i < len(cur_annot) and cur_annot[i].ub <= sentence.ub:
                            annots.append(cur_annot[i])
                            if tuple([cur_annot[i].lb, cur_annot[i].ub]) not in present:
                                raise Exception
                            i += 1
                        l1 = ["O" for _ in range(len(sentence))]
                        for annot in annots:
                            l1[annot.lb - shift] = "B-{0}".format(annot.value)
                            for j in range(annot.lb + 1 - shift, annot.ub - shift):
                                l1[j] = "I-{}".format(annot.value)
                        for j in range(len(l1)):
                            sent[j]["NER"] = l1[j]
                        shift += len(sentence)
                    document.corpus.fields.append(chunk_to_load)

        return document

    def escaped_name(self):
        name = pathlib.Path(self._name).name
        if sem.ON_WINDOWS:
            return re.sub(r'[:\\?"<>|]', "", name)
        else:
            return name

    def get_tokens(self):
        tokens = []
        content = self.content
        for span in self.segmentation("tokens"):
            tokens.append(content[span.lb: span.ub])
        return tokens

    def set_content(self, content):
        self._content = content

    def add_segmentation(self, segmentation):
        self._segmentations[segmentation.name] = segmentation
        self._segmentations[segmentation.name]._document = self

    def segmentation(self, name):
        return self._segmentations.get(name, None)

    def add_annotation(self, annotation):
        self._annotations[annotation.name] = annotation
        self._annotations[annotation.name]._document = self

    def annotation(self, name):
        return self._annotations.get(name, None)

    def add_metadata(self, key, value):
        self._metadatas[key] = value

    def metadata(self, name):
        return self._metadatas.get(name, None)

    def mime_type(self):
        return self.metadata("MIME")

    def write(self, f, depth=0, indent=4, add_header=False):
        if add_header:
            f.write('<?xml version="1.0" encoding="{0}" ?>\n'.format(f.encoding or "ASCII"))
        f.write(
            '{0}<document name="{1}">\n'.format(
                depth * indent * " ", self.name.replace('"', "&quot;")
            )
        )
        depth += 1
        f.write("{}<metadata".format(depth * indent * " "))
        for metakey, metavalue in sorted(self._metadatas.items()):
            f.write(' {0}="{1}"'.format(metakey, metavalue))
        f.write(" />\n")
        f.write(
            "{0}<content>{1}</content>\n".format(depth * indent * " ", cgi.escape(self.content))
        )

        if len(self.segmentations) > 0:
            f.write("{0}<segmentations>\n".format(depth * indent * " "))
            refs = [seg.reference for seg in self.segmentations.values() if seg.reference]
            for seg in sorted(
                self.segmentations.values(),
                key=lambda x: (x.reference is not None and x.reference.reference in refs, x.name),
            ):
                depth += 1
                ref = (
                    seg.reference.name if isinstance(seg.reference, Segmentation) else seg.reference
                )
                ref_str = "" if ref is None else ' reference="{0}"'.format(ref)
                f.write(
                    '{0}<segmentation name="{1}"{2}>'.format(
                        depth * indent * " ", seg.name, ref_str
                    )
                )
                depth += 1
                for i, element in enumerate(seg):
                    lf = i == 0 or (i % 5 == 0)
                    if lf:
                        f.write("\n{0}".format(depth * indent * " "))
                    f.write(
                        '{0}<s s="{1}" l="{2}" />'.format(
                            ("" if lf else " "), element.lb, len(element)
                        )
                    )
                f.write("\n")
                depth -= 1
                f.write("{0}</segmentation>\n".format(depth * indent * " "))
                depth -= 1
            f.write("{0}</segmentations>\n".format(depth * indent * " "))

        if len(self.annotations) > 0:
            f.write("{0}<annotations>\n".format(depth * indent * " "))
            for annotation in self.annotations.values():
                depth += 1
                reference = (
                    ""
                    if not annotation.reference
                    else ' reference="{0}"'.format(
                        annotation.reference
                        if isinstance(annotation.reference, str)
                        else annotation.reference.name
                    )
                )
                f.write(
                    '{0}<annotation name="{1}"{2}>\n'.format(
                        depth * indent * " ", annotation.name, reference
                    )
                )
                depth += 1
                for tag in annotation:
                    f.write(
                        '{0}<tag v="{1}" s="{2}" l="{3}"/>\n'.format(
                            depth * indent * " ", tag.getValue(), tag.lb, len(tag)
                        )
                    )
                depth -= 1
                f.write("{0}</annotation>\n".format(depth * indent * " "))
                depth -= 1
            f.write("{0}</annotations>\n".format(depth * indent * " "))

        depth -= 1
        f.write("{0}</document>\n".format(depth * indent * " "))

    def set_reference(
        self, annotation_name, reference_name, add_to_corpus=False, filter=get_top_level
    ):
        annot = self.annotation(annotation_name)

        if annot is not None and (
            annot.reference is None or annot.reference.name != reference_name
        ):
            spans = self.segmentation(reference_name).get_reference_spans()
            begin = 0
            i = 0
            for annotation in annot:
                start = annotation.lb
                end = annotation.ub
                while not (spans[i].lb <= start and start < spans[i].ub):
                    i += 1
                begin = i
                while spans[i].ub < end:
                    i += 1
                annotation.lb = begin
                annotation.ub = i + 1
                i = max(begin - 1, 0)
                begin = 0
            annot._reference = self.segmentation(reference_name)

        if add_to_corpus:
            self.add_to_corpus(annotation_name, filter=filter)

    def add_to_corpus(self, annotation_name, filter=get_top_level):
        base_annotations = self.annotation(annotation_name) or Annotation(annotation_name)
        annotations = base_annotations.get_reference_annotations()

        spans = self.segmentation("tokens").get_reference_spans()
        begin = 0
        i = 0
        to_remove = []  # annotations that cannot be aligned with tokens will be removed
        for j, annotation in enumerate(annotations):
            start = annotation.lb
            end = annotation.ub
            while (i > 0) and start < spans[i].lb:
                i -= 1
            while (i < len(spans)) and not (spans[i].lb <= start < spans[i].ub):
                i += 1
            if i < len(spans):
                begin = i
                while spans[i].ub < end:
                    i += 1
                annotation.lb = begin
                annotation.ub = i + 1
            else:
                sem.logger.warn("cannot add annotation {0}".format(annotation))
                to_remove.append(j)
            i = max(begin, 0)
            begin = 0
        for i in to_remove[::-1]:
            del annotations[i]

        if filter:
            annotations = filter(annotations)
        sentence_spans = iter(self.segmentation("sentences"))
        annot_index = 0
        if len(annotations) == 0:
            annots = []
            cur_annot = None
        else:
            annots = annotations
            cur_annot = annots[annot_index]
        shift = 0
        for sentence in self.corpus.sentences:
            span = next(sentence_spans)
            tags = ["O" for _ in range(len(sentence))]
            while cur_annot is not None and cur_annot.lb >= span.lb and cur_annot.ub <= span.ub:
                tags[cur_annot.lb - shift] = "B-{0}".format(cur_annot.value)
                for k in range(cur_annot.lb + 1, cur_annot.ub):
                    tags[k - shift] = "I-{0}".format(cur_annot.value)
                try:
                    annot_index += 1
                    cur_annot = annots[annot_index]
                except IndexError:
                    cur_annot = None
            sentence.add(tags, annotation_name)
            if cur_annot is not None and (cur_annot.lb in span and cur_annot.ub > span.ub):
                # annotation spans over at least two sentences
                sem.logger.warn(
                    "Annotation {0} spans over multiple sentences, ignoring".format(cur_annot)
                )
                try:
                    annot_index += 1
                    cur_annot = annots[annot_index]
                except IndexError:
                    cur_annot = None
            shift += len(sentence)
        self.corpus.fields.append(annotation_name)

    def add_annotation_from_tags(self, tags, field, annotation_name):
        BIO = all([tag[0] in "BIO" for tag in tags[0]])
        if self._annotations.get(annotation_name, None):
            del self._annotations[annotation_name]._annotations[:]
        if BIO:
            self.add_chunking(tags, field, annotation_name)
        else:
            self.add_tagging(tags, field, annotation_name)
        if field not in self.corpus:
            self.corpus.fields += [field]

    def add_tagging(self, sentence_tags, field, annotation_name):
        nth_token = 0
        annotation = []

        for nth_sentence, tags in enumerate(sem.misc.correct_pos_tags(sentence_tags)):
            index = len(annotation)
            i = len(tags) - 1
            n = 0
            current = None  # current tag value (for multiword tags)
            while i >= 0:
                if tags[i][0] != "_":
                    annotation.insert(index, Tag(tags[i], nth_token + i, 0, length=n + 1))
                    current = None
                    n = 0
                else:
                    if current is None:
                        current = tags[i].lstrip("_")
                        n = 0
                    n += 1
                i -= 1
            self.corpus.sentences[nth_sentence].add(tags, field)
            nth_token += len(tags)
        self._annotations[annotation_name] = Annotation(
            annotation_name, reference=self.segmentation("tokens")
        )
        self._annotations[annotation_name].annotations = annotation[:]

    def add_chunking(self, sentence_tags, field, annotation_name):
        for nth_sentence, tags in enumerate(sentence_tags):
            self.corpus.sentences[nth_sentence].add(tags, field)
        self._annotations[annotation_name] = chunk_annotation_from_corpus(
            self.corpus, field, annotation_name, reference=self.segmentation("tokens")
        )


class SEMCorpus:
    def __init__(self, documents=None):
        if documents is None:
            self._documents = []
        else:
            self._documents = documents

    def __getitem__(self, index):
        return self._documents[index]

    def __len__(self):
        return len(self._documents)

    def __iter__(self):
        return iter(self._documents)

    @property
    def documents(self):
        return self._documents

    @staticmethod
    def from_xml(xml, chunks_to_load=None, load_subtypes=True, type_separator="."):
        if isinstance(xml, str):
            data = ET.parse(xml)
        elif isinstance(xml, ET.ElementTree):
            data = xml
        elif isinstance(xml, type(ET.Element("a"))):  # did not ind a better way to do this
            data = xml
        else:
            raise TypeError("Invalid type for loading XML-SEM document: {0}".format(type(xml)))

        root = data.getroot()
        if root.tag != "sem":
            raise ValueError("Not sem xml file type: '{0}'".format(root.tag))
        doc_list = []
        for document in list(root):
            doc_list.append(Document.from_xml(document))
        return SEMCorpus(doc_list)

    def add_document(self, document):
        ok = not any([d.name == document.name for d in self.documents])
        if ok:
            self._documents.append(document)

    def write(self, f, indent=4):
        f.write('<?xml version="1.0" encoding="{0}" ?>\n'.format(f.encoding or "ASCII"))
        f.write("<sem>\n")
        for document in self._documents:
            document.write(f, depth=1, indent=indent, add_header=False)
        f.write("</sem>")


str2docfilter = {
    "all documents": lambda x, y: True,
    "only documents with annotations": lambda d, a: len(d.annotation(a) or []) > 0,
}


class Trie(object):
    """The Trie object.

    Attributes
    ----------
    _data : dict
        the structure where all the entries of a multiword dictionary
        are loaded.
    """

    def __init__(self, filename=None, encoding=None):
        self._data = {}

        if filename:
            encoding = encoding or "UTF-8"
            for l in open(filename, "rU", encoding=encoding):
                seq = l.strip().split()

                self.add(seq)

    def __iter__(self):
        seq = []

        def dfs(dic):
            """Depth First Search"""
            keys = set(dic.keys())
            found = NUL in keys

            if found:
                keys.remove(NUL)
                if dic[NUL]:
                    yield seq
            keys = list(keys)
            keys.sort()
            for k in keys:
                seq.append(k)
                for i in dfs(dic[k]):
                    yield i
                seq.pop()

        for i in dfs(self._data):
            yield i

    def __len__(self):
        length = 0
        for _ in self:
            length += 1
        return length

    @property
    def data(self):
        return self._data

    def add(self, sequence):
        iterator = sequence.__iter__()
        d = self._data

        try:
            while True:
                token = next(iterator)

                if token not in d:
                    d[token] = {}

                d = d[token]
        except StopIteration:
            pass

        d[NUL] = {}

    def add_with_value(self, sequence, value):
        iterator = iter(sequence)
        d = self._data

        try:
            while True:
                token = next(iterator)

                if token not in d:
                    d[token] = {}

                d = d[token]
        except StopIteration:
            pass

        d[NUL] = value

    def contains(self, sequence):
        iterator = iter(sequence)
        d = self._data
        result = True

        try:
            while True:
                token = next(iterator)

                if token not in d:
                    result = False
                    break

                d = d[token]
        except StopIteration:
            pass

        return result and (NUL in d)

    def remove(self, sequence):
        def remove(dic, iterator):
            try:
                elt = next(iterator)
                if elt in dic:
                    remove(dic[elt], iterator)
                    if dic[elt] == {}:
                        del dic[elt]
            except StopIteration:
                if NUL in dic:
                    del dic[NUL]

        remove(self._data, iter(sequence))

    def goto(self, sequence):
        iterator = iter(sequence)
        d = self._data
        result = True

        try:
            while True:
                token = next(iterator)

                if token not in d:
                    result = False
                    break

                d = d[token]
        except StopIteration:
            pass

        if result:
            return d
        else:
            return None


class Coder(object):
    def __init__(self):
        self._encoder = {}
        self._decoder = []

    def __len__(self):
        return len(self._decoder)

    def __iter__(self):
        return iter(self._decoder[:])

    def __contains__(self, element):
        return element in self._encoder

    def keys(self):
        return self._decoder[:]

    def add(self, element, strict=False):
        if element not in self._encoder:
            self._encoder[element] = len(self)
            self._decoder.append(element)
        elif strict:
            raise KeyError("'{0}' already in coder".format(element))

    def insert(self, index, element):
        if element not in self._encoder:
            self._decoder.insert(index, element)
            self._encoder[element] = index
            for nth in range(index + 1, len(self._encoder)):
                self._encoder[self._decoder[nth]] = nth

    def encode(self, element):
        return self._encoder.get(element, -1)

    def decode(self, integer):
        try:
            return self._decoder[integer]
        except Exception:
            return None
