# -*- coding: utf-8 -*-

"""
file: processors.py

Description: formerly sem_modules. The purpose is to improve the code in two
main ways: terminology and organization. "Module" conflicts with python modules
while "processor" is more accepted (plus the "main" method of a "module" was...
process_document). Organization is improved because we do not conflate the
processing object with the "user interface" that made using processors in code
a little bit unwieldy and awkward. This file also replaces pipeline.py

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
import tempfile
import re
import sys
from datetime import timedelta

try:
    from xml.etree.cElementTree import ElementTree, tostring as element2string
except ImportError:
    from xml.etree.ElementTree import ElementTree, tostring as element2string

from wapiti.api import Model as WapitiModel

import pymorphy2

import sem.logger
import sem.annotators

from sem.util import (strip_html, read_chunks, check_model_available, longest_common_substring)
from sem.tokenisers import get_tokeniser
from sem.storage import (
    AnnotationSet, Entry, Segmentation, Sentence, Span, Tag, Trie,
    chunk_annotation_from_sentence, compile_map
)
from sem.features import (xml2feat, NUL)
from sem.exporters import get_exporter


DEFAULT_LICENSE = (
    "No license provided.\n"
    "Unless you find contradictory information from an official source,"
    " this is provided for research, teaching and personal use only,"
    " it may not be used for any other purpose."
)


class Processor:
    def __init__(self, pipeline_mode="all", license=None, **kwargs):
        self.pipeline_mode = pipeline_mode
        self._license = license or DEFAULT_LICENSE

    @property
    def license(self):
        return self._license

    @license.setter
    def license(self, license):
        if self._license and self._license != DEFAULT_LICENSE:
            sem.logger.warning("changing non default license.")
        self._license = license

    def check_mode(self, expected_mode):
        return expected_mode == "all" or self.pipeline_mode in ("all", expected_mode)

    def process_document(self, document, **kwargs):
        raise NotImplementedError(
            "process_document not implemented for root type {}".format(self.__class__)
        )


class AnnotateProcessor(Processor):
    def __init__(self, annotator, field, *args, **kwargs):
        super(AnnotateProcessor, self).__init__(**kwargs)

        self._annotator = sem.annotators.get_annotator(annotator).load(field, *args, **kwargs)

    def process_document(self, document, **kwargs):
        start = time.time()
        self._annotator.process_document(document)
        laps = time.time() - start
        sem.logger.info("done in {}".format(timedelta(seconds=laps)))


def token_spans_buffered(tokeniser, content):
    """Return the token spans of content.
    This does the same as tokeniser.word_spans, but this method buffers
    the input to allow a quicker processing of large content.
    """
    rem = ""  # remainder of unsegmented tokens
    shift = 0
    token_spans = []
    for chunk in read_chunks(content):
        chnk = rem + chunk
        spans = tokeniser.word_spans(chnk)
        if not spans:
            rem = chnk
            continue
        elif spans[-1].ub < len(chnk):
            rem = chnk[spans[-1].ub:]
        elif spans[-1].ub == len(chnk):
            rem = chnk[spans[-1].lb:]
            del spans[-1]
        else:
            rem = ""
        token_spans.extend([Span(shift + s.lb, shift + s.ub) for s in spans])
        shift += len(chnk) - len(rem)
        del spans[:]

    if rem:
        spans = tokeniser.word_spans(rem) or [Span(0, len(rem))]
        token_spans.extend([Span(shift + s.lb, shift + s.ub) for s in spans])
    if not content[token_spans[-1].lb: token_spans[-1].ub].strip():
        del token_spans[-1]

    return token_spans


class SegmentationProcessor(Processor):
    def __init__(self, tokeniser, **kwargs):
        super(SegmentationProcessor, self).__init__(**kwargs)

        if isinstance(tokeniser, str):
            sem.logger.info('Getting tokeniser "{0}"'.format(tokeniser))
            self._tokeniser = get_tokeniser(tokeniser)()
        else:
            self._tokeniser = tokeniser

    def process_document(self, document, **kwargs):
        """
        Updates a document with various segmentations and creates
        an sem.corpus (CoNLL-formatted data) using field argument as index.

        Parameters
        ----------
        document : sem.storage.Document
            the input data. It is a document with only a content
        """

        start = time.time()

        current_tokeniser = self._tokeniser

        sem.logger.debug('segmenting "%s" content', document.name)

        content = document.content
        if document.metadata("MIME") == "text/html":
            content = strip_html(content, keep_offsets=True)

        if document.segmentation("tokens") is None:
            token_spans = token_spans_buffered(current_tokeniser, document.content)
            document.add_segmentation(Segmentation("tokens", spans=token_spans))
        else:
            sem.logger.info("{} already has tokens".format(document.name))
            token_spans = document.segmentation("tokens").spans

        if document.segmentation("sentences") is None:
            sentence_spans = current_tokeniser.sentence_spans(content, token_spans)
            document.add_segmentation(
                Segmentation(
                    "sentences", reference=document.segmentation("tokens"), spans=sentence_spans
                )
            )
        else:
            sem.logger.info("{} already has sentences".format(document.name))
            sentence_spans = document.segmentation("sentences").spans

        if document.segmentation("paragraphs") is None:
            paragraph_spans = current_tokeniser.paragraph_spans(
                content, sentence_spans, token_spans
            )
            document.add_segmentation(
                Segmentation(
                    "paragraphs",
                    reference=document.segmentation("sentences"),
                    spans=paragraph_spans,
                )
            )
        else:
            sem.logger.info("{} already has paragraphs".format(document.name))

        if len(document.corpus) == 0:
            document.corpus.from_segmentation(
                document.content,
                document.segmentation("tokens"),
                document.segmentation("sentences"),
            )

        sem.logger.info(
            '"{0}" segmented in {1} sentences, {2} tokens'.format(
                document.name, len(sentence_spans), len(token_spans)
            )
        )

        laps = time.time() - start
        sem.logger.info("in {0}".format(timedelta(seconds=laps)))


class EnrichProcessor(Processor):
    def __init__(
        self,
        path=None,
        bentries=None,
        aentries=None,
        features=None,
        mode="label",
        **kwargs,
    ):
        super(EnrichProcessor, self).__init__(**kwargs)

        self._mode = mode
        self._source = path
        self._bentries = []  # informations that are before newly added information
        self._aentries = []  # informations that are after ...
        self._features = []  # informations that are added
        self._names = set()
        self._temporary = set()  # features that will be deleted at the end of process
        self._x2f = None  # the feature parser, initialised in parse

        if self._source is not None:
            sem.logger.info("loading %s", self._source)
            self._parse(self._source)
        else:
            self._bentries = (
                [entry for entry in bentries if entry.has_mode(self._mode)]
                if bentries
                else self._bentries
            )
            self._aentries = (
                [entry for entry in aentries if entry.has_mode(self._mode)]
                if aentries
                else self._aentries
            )
            self._features = features
            self._names = set([entry.name for entry in self._aentries + self._bentries])

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, mode):
        if not isinstance(self._source, str):
            raise RuntimeError(
                "cannot change mode for Enrich module: source for informations is not a file."
            )
        self._mode = mode
        sem.logger.info("loading %s", self._source)
        self._parse(self._source)

    @property
    def bentries(self):
        return self._bentries

    @property
    def aentries(self):
        return self._aentries

    @property
    def features(self):
        return self._features

    def fields(self):
        fields = [entry.name for entry in self._bentries]
        fields += [name for (feature, name) in self.features if name not in self._temporary]
        fields += [entry.name for entry in self._aentries]
        return fields

    def process_document(self, document, **kwargs):
        """
        Updates the CoNLL-formatted corpus inside a document with various
        features.

        Parameters
        ----------
        document : sem.storage.Document
            the input data, contains an object representing CoNLL-formatted
            data. Each token is a dict which works like TSV.
        """

        start = time.time()

        missing_fields = set([entry.name for entry in self.bentries + self.aentries]) - set(
            document.corpus.fields
        )

        if len(missing_fields) > 0:
            raise ValueError(
                "Missing fields in input corpus: {0}".format(",".join(sorted(missing_fields)))
            )

        sem.logger.info('enriching file "%s"', document.name)

        fields = self.fields()
        nth = 0
        for i, p in enumerate(document.corpus):
            p.update(self.features)
            for tmp in self._temporary:
                p.remove(tmp)
            nth += 1
            if 0 == nth % 1000:
                sem.logger.debug("%i sentences enriched", nth)
        sem.logger.debug("%i sentences enriched", nth)
        document.corpus.fields = fields[:]

        laps = time.time() - start
        sem.logger.info("done in %s", timedelta(seconds=laps))

    def _parse(self, filename):
        def check_entry(entry_name):
            if entry_name in self._names:
                raise ValueError('Duplicated column name: "{}"'.format(entry_name))
            else:
                self._names.add(entry_name)

        parsing = ElementTree()
        parsing.parse(filename)

        children = parsing.getroot().getchildren()

        if len(children) != 2:
            raise RuntimeError(
                "Enrichment file requires exactly 2 fields, {0} given.".format(len(children))
            )
        else:
            if children[0].tag != "entries":
                raise RuntimeError(
                    'Expected "entries" as first field, got "{0}".'.format(children[0].tag)
                )
            if children[1].tag != "features":
                raise RuntimeError(
                    'Expected "features" as second field, got "{0}".'.format(children[1].tag)
                )

        entries = list(children[0])
        if len(entries) not in (1, 2):
            raise RuntimeError(
                "Entries takes exactly 1 or 2 fields, {0} given".format(len(entries))
            )
        else:
            entry1 = entries[0].tag.lower()
            entry2 = entries[1].tag.lower() if len(entries) == 2 else None
            if entry1 not in ("before", "after"):
                raise RuntimeError(
                    'For entry position, expected "before" or "after", got "{0}".'.format(entry1)
                )
            if entry2 and entry2 not in ("before", "after"):
                raise RuntimeError(
                    'For entry position, expected "before" or "after", got "{0}".'.format(entry2)
                )
            if entry1 == entry2:
                raise RuntimeError("Both entry positions are the same, they should be different")

        for entry in entries:
            for c in entry.getchildren():
                current_entry = Entry.fromXML(c)
                check_entry(current_entry.name)
                if entry.tag == "before" and current_entry.has_mode(self._mode):
                    self._bentries.append(current_entry)
                elif entry.tag == "after" and current_entry.has_mode(self._mode):
                    self._aentries.append(current_entry)

        features = list(children[1])
        del self._features[:]
        for feature in features:
            feature_name = feature.attrib.get("name")
            if not sem.util.str2bool(feature.attrib.get("display", "yes")):
                self._temporary.add(feature_name)
            self._features.append((xml2feat(feature, path=filename), feature_name))
            if not feature_name:
                try:
                    raise ValueError("Nameless feature found.")
                except ValueError as exc:
                    for line in element2string(feature).rstrip().split("\n"):
                        sem.logger.error(line.strip())
                    sem.logger.exception(exc)
                    raise
            check_entry(feature_name)


class CleanProcessor(Processor):
    def __init__(self, to_keep, **kwargs):
        super(CleanProcessor, self).__init__(**kwargs)

        if isinstance(to_keep, str):
            self._allowed = to_keep.split(",")  # comma-separated named fields
        else:
            self._allowed = to_keep

        if len(self._allowed) == 0:
            raise ValueError("No more data after cleaning !")

    def process_document(self, document, **kwargs):
        """
        Cleans the sem.storage.corpus of a document, removing unwanted fields.

        Parameters
        ----------
        document : sem.storage.Document
            the document containing the corpus to clean.
        ranges : str or list of int or list of str
            if str: fields to remove will be induced
            if list of int: each element in the list is the index of a field
            to remove in corpus.fields
            if list of string: the list of fields to remove
        """

        start = time.time()

        sem.logger.info("cleaning document")

        allowed = set(self._allowed)
        fields = set(field for field in document.corpus.fields)

        if len(allowed - fields) > 0:
            sem.logger.warning(
                "the following fields are not present in document,"
                " this might cause an error sometime later: {}".format(", ".join(allowed - fields))
            )

        for sentence in document.corpus.sentences:
            sentence = Sentence({key: sentence.feature(key) for key in allowed})
        document._corpus.fields = self._allowed[:]

        laps = time.time() - start
        sem.logger.info("done in {0}".format(timedelta(seconds=laps)))


def model_from_string(mdl_str, encoding="utf-8"):
    with tempfile.NamedTemporaryFile() as fl:
        try:
            fl.write(mdl_str.encode(encoding=encoding))
        except AttributeError:
            fl.write(mdl_str)
        fl.seek(0)
        return WapitiModel(encoding=encoding, model=fl.name)


class WapitiLabelProcessor(Processor):
    def __init__(
        self, model, field, annotation_fields=None, model_str=None, model_encoding="utf-8", **kwargs
    ):
        super(WapitiLabelProcessor, self).__init__(**kwargs)

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
        self.load_model()

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

        check_model_available(self._model)
        self._wapiti_model = WapitiModel(encoding="utf-8", model=self._model)
        with open(self._model, "rb") as input_stream:
            self._mdl_str = input_stream.read()

    def load_model(self):
        if self._mdl_str is not None:
            self._wapiti_model = model_from_string(self._mdl_str, self._model_encoding)
        elif self._model is not None:
            try:
                check_model_available(self._model)
                self._wapiti_model = WapitiModel(encoding="utf-8", model=self._model)
            except FileNotFoundError:
                sem.logger.warning(
                    "Model file {} does not exist, you will need to train one.".format(self._model)
                )
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


def normalize(token):
    normalized = re.sub("[\u2019]", "'", token, flags=re.U)
    normalized = re.sub("[àáâãäåæ]", "a", normalized, flags=re.U)
    normalized = re.sub("[ÀÁÂÃÄÅÆ]", "A", normalized, flags=re.U)
    normalized = re.sub("[éèêë]", "e", normalized, flags=re.U)
    normalized = re.sub("[ÉÈÊË]", "E", normalized, flags=re.U)
    normalized = re.sub("[ìíîï]", "i", normalized, flags=re.U)
    normalized = re.sub("[ÌÍÎÏ]", "I", normalized, flags=re.U)
    return normalized


def abbrev_candidate(token):
    return token.isupper() and all([c.isalpha() for c in token])


def tokens_from_bounds(document, start, end):
    word_spans = document.segmentation("tokens")
    toks = []
    for span in word_spans:
        if span.lb >= start:
            toks.append(document.content[span.lb: span.ub])
            if span.ub >= end:
                break
        if span.lb > end:
            break
    return toks


def tokens2regex(tokens, flags=re.U):
    apostrophes = "['\u2019]"
    apos_re = re.compile(apostrophes, re.U)
    pattern = "{}{}{}".format("\\b", "\\b *\\b".join(tokens), "\\b")
    pattern = apos_re.sub(apostrophes, pattern)
    pattern = re.escape(pattern)
    return re.compile(pattern, flags)


def detect_abbreviations(document, field):
    content = document.content
    word_spans = document.segmentation("tokens")
    if document.segmentation("sentences") is not None:
        sentence_spans = document.segmentation("sentences").spans
        sentence_spans_ref = document.segmentation("sentences").get_reference_spans()
    else:
        sentence_spans_ref = [Span(0, len(document.content))]
    tokens = [content[span.lb: span.ub] for span in word_spans]
    annotations = document.annotationset(field).get_reference_annotations()

    counts = {}
    positions = {}
    for i, token in enumerate(tokens):
        if (
            abbrev_candidate(token)
            and len(token) > 1
            and not (
                (i > 1 and abbrev_candidate(tokens[i - 1]))
                or (i < len(tokens) - 1 and abbrev_candidate(tokens[i + 1]))
            )
        ):
            if token not in counts:
                counts[token] = 0
                positions[token] = []
            counts[token] += 1
            positions[token].append(i)
    position2sentence = {}
    for token, indices in positions.items():
        for index in indices:
            for i, span in enumerate(sentence_spans):
                if span.lb <= index and span.ub >= index:
                    position2sentence[index] = sentence_spans_ref[i]

    reg2type = {}
    for key in counts:
        all_solutions = []
        for position in positions[key]:
            span = position2sentence[position]
            word_span = word_spans[position]
            lb = span.lb
            ub = word_span.lb
            solutions = longest_common_substring(
                content[lb:ub], tokens[position], casesensitive=False
            )
            if solutions == []:
                solutions = longest_common_substring(
                    normalize(content[lb:ub]), tokens[position], casesensitive=False
                )
            solutions = [
                solution for solution in solutions if len(solution) == len(tokens[position])
            ]
            if len(solutions) > 0:
                all_solutions.extend(
                    [[(x + lb, y + lb) for (x, y) in solution] for solution in solutions]
                )
        if len(all_solutions) > 0:
            all_solutions.sort(key=lambda x: x[-1][0] - x[0][0])
            best_solution = all_solutions[0]
            lo = best_solution[0][0]
            hi = best_solution[-1][0]
            lo_tokens = [tok for tok in word_spans if tok.lb <= lo and tok.ub > lo]
            hi_tokens = [tok for tok in word_spans if tok.lb <= hi and tok.ub > hi]
            abbrev_annots = []
            for position in positions[key]:
                span = word_spans[position]
                abbrev_annots.extend(
                    [
                        annotation
                        for annotation in annotations
                        if annotation.lb == span.lb and annotation.ub == span.ub
                    ]
                )
            try:
                toks = tokens_from_bounds(document, lo_tokens[0].lb, hi_tokens[0].ub)
                reg = tokens2regex(toks, re.U + re.I)
                for match in reg.finditer(content):
                    annots = [
                        annotation
                        for annotation in annotations
                        if (
                            (annotation.lb <= match.start() and match.start() <= annotation.ub)
                            or (annotation.lb <= match.end() and match.end() <= annotation.ub)
                        )
                    ]
                    if len(annots) > 0:
                        annot = annots[0]
                        new_toks = tokens_from_bounds(
                            document, min(annot.lb, match.start()), max(annot.ub, match.end())
                        )
                        new_reg = tokens2regex(new_toks, re.U + re.I)
                        if new_reg.pattern not in reg2type:
                            reg2type[new_reg.pattern] = []
                        reg2type[new_reg.pattern].append(annots[0].value)
                        if abbrev_annots == []:
                            abbrev_reg = tokens2regex([key], re.U)
                            if abbrev_reg.pattern not in reg2type:
                                reg2type[abbrev_reg.pattern] = []
                            reg2type[abbrev_reg.pattern].append(annots[0].value)
                if len(abbrev_annots) > 0:
                    tag = abbrev_annots[0]
                    new_reg = tokens2regex(toks, re.U + re.I)
                    if new_reg.pattern not in reg2type:
                        reg2type[new_reg.pattern] = []
                    reg2type[new_reg.pattern].append(tag.value)
            except IndexError:
                pass

    new_tags = []
    for v in reg2type.keys():
        type_counts = sorted(
            [(the_type, reg2type[v].count(the_type)) for the_type in set(reg2type[v])],
            key=lambda x: (-x[-1], x[0]),
        )
        fav_type = type_counts[0][0]
        regexp = re.compile(v, re.U + re.I * (" " in v))
        for match in regexp.finditer(content):
            lo_tok = word_spans.spans.index([t for t in word_spans if t.lb == match.start()][0])
            hi_tok = word_spans.spans.index([t for t in word_spans if t.ub == match.end()][0]) + 1
            new_tags.append(Tag(fav_type, lo_tok, hi_tok))

    to_remove_tags = []
    for new_tag in new_tags:
        to_remove_tags.extend(
            [
                ann
                for ann in document.annotationset(field)
                if new_tag.lb <= ann.lb and ann.ub <= new_tag.ub and ann.value == new_tag.value
            ]
        )
    for to_remove_tag in to_remove_tags:
        try:
            document.annotationset(field)._annotations.remove(to_remove_tag)
        except ValueError:
            pass

    all_tags = [sent.feature(field) for sent in document.corpus.sentences]
    new_tags.sort(key=lambda x: (x.lb, -x.ub))
    for new_tag in new_tags:
        nth_word = 0
        nth_sent = 0
        sents = document.corpus.sentences
        while nth_word + len(sents[nth_sent]) - 1 < new_tag.lb:
            nth_word += len(sents[nth_sent])
            nth_sent += 1
        start = new_tag.lb - nth_word
        end = new_tag.ub - nth_word
        document.corpus.sentences[nth_sent][start][field] = "B-{}".format(new_tag.value)
        all_tags[nth_sent][start] = "B-{0}".format(new_tag.value)
        for index in range(start + 1, end):
            document.corpus.sentences[nth_sent][index][field] = "I-{0}".format(new_tag.value)
            all_tags[nth_sent][index] = "I-{0}".format(new_tag.value)

    document.add_annotation_from_tags(all_tags, field, field)


def non_overriding_label_consistency(sentence, form2entity, trie, entry, ne_entry):
    length = len(sentence)
    res = sentence.feature(ne_entry)[:]
    tmp = trie
    fst = 0
    lst = -1  # last match found
    cur = 0
    ckey = None  # Current KEY
    tokens = sentence.feature(entry)
    while fst < length - 1:
        cont = True
        while cont and (cur < length):
            ckey = tokens[cur]
            if res[cur] == "O":
                if NUL in tmp:
                    lst = cur
                tmp = tmp.get(ckey, {})
                cont = len(tmp) != 0
                cur += int(cont)
            else:
                cont = False

        if NUL in tmp:
            lst = cur

        if lst != -1:
            form = " ".join([tokens[i] for i in range(fst, lst)])
            appendice = "-{}".format(form2entity[form])
            res[fst] = "B{}".format(appendice)
            for i in range(fst + 1, lst):
                res[i] = "I{}".format(appendice)
            fst = lst
            cur = fst
        else:
            fst += 1
            cur = fst

        tmp = trie
        lst = -1

    if NUL in trie.get(tokens[-1], []) and res[-1] == "O":
        res[-1] = "B-{}".format(form2entity[tokens[-1]])

    return res


def overriding_label_consistency(sentence, form2entity, trie, entry, ne_entry):
    length = len(sentence)
    res = ["O" for _ in range(length)]
    tmp = trie
    fst = 0
    lst = -1  # last match found
    cur = 0
    ckey = None  # Current KEY
    entities = []
    tokens = sentence.feature(entry)
    while fst < length - 1:
        cont = True
        while cont and (cur < length):
            ckey = tokens[cur]
            if res[cur] == "O":
                if NUL in tmp:
                    lst = cur
                tmp = tmp.get(ckey, {})
                cont = len(tmp) != 0
                cur += int(cont)
            else:
                cont = False

        if NUL in tmp:
            lst = cur

        if lst != -1:
            form = " ".join([tokens[i] for i in range(fst, lst)])
            entities.append(Tag(form2entity[form], fst, lst))
            fst = lst
            cur = fst
        else:
            fst += 1
            cur = fst

        tmp = trie
        lst = -1

    if NUL in trie.get(tokens[-1], []):
        entities.append(
            Tag(form2entity[tokens[-1]], length - 1, length)
        )

    gold = chunk_annotation_from_sentence(sentence, ne_entry).annotations

    for i in reversed(range(len(entities))):
        e = entities[i]
        for r in gold:
            if r.lb == e.lb and r.ub == e.ub:
                del entities[i]
                break

    for i in reversed(range(len(gold))):
        r = gold[i]
        for e in entities:
            if r.lb >= e.lb and r.ub <= e.ub:
                del gold[i]
                break

    for r in gold + entities:
        appendice = "-{}".format(r.value)
        res[r.lb] = "B{}".format(appendice)
        for i in range(r.lb + 1, r.ub):
            res[i] = "I{}".format(appendice)

    return res


class LabelConsistencyProcessor(Processor):
    def __init__(
        self,
        field,
        token_field="word",
        label_consistency="overriding",
        **kwargs,
    ):
        super(LabelConsistencyProcessor, self).__init__(**kwargs)
        self._field = field
        self._token_field = token_field

        if label_consistency == "overriding":
            self._feature = overriding_label_consistency
        else:
            self._feature = non_overriding_label_consistency

    def process_document(self, document, abbreviation_resolution=True, **kwargs):
        corpus = document.corpus.sentences
        field = self._field
        token_field = self._token_field

        entities = {}
        counts = {}
        for p in corpus:
            G = chunk_annotation_from_sentence(p, column=field)
            for entity in G:
                id = entity.value
                form = " ".join(p.feature(token_field)[entity.lb: entity.ub])
                if form not in counts:
                    counts[form] = {}
                if id not in counts[form]:
                    counts[form][id] = 0
                counts[form][id] += 1

        for form, count in counts.items():
            if len(count) == 1:
                entities[form] = list(count.keys())[0]
            else:
                best = sorted(count.keys(), key=lambda x: -count[x])[0]
                entities[form] = best

        value = Trie()
        for entry in entities.keys():
            entry = entry.strip()
            if entry:
                value.add(entry.split())

        for p in corpus:
            p.add(self._feature(p, entities, value.data, token_field, field), field)

        tags = [sentence.feature(field) for sentence in corpus]
        document.add_annotation_from_tags(tags, field, field)

        if abbreviation_resolution:
            detect_abbreviations(document, field)


class MapAnnotationsProcessor(Processor):
    def __init__(self, mapping, annotation_name, **kwargs):
        super(MapAnnotationsProcessor, self).__init__(**kwargs)

        if isinstance(mapping, str):
            with open(mapping, 'r', encoding="utf-8") as input_stream:
                self._mapping = compile_map(input_stream)
        else:
            self._mapping = mapping

        self._annotation_name = annotation_name

    def process_document(self, document, **kwargs):
        """Updates a document with various segmentations and creates
        an sem.corpus (CoNLL-formatted data) using field argument as index.

        Parameters
        ----------
        document : sem.storage.Document
            the input data. It is a document with only a content
        """

        start = time.time()

        ref_annotation = document.annotationset(self._annotation_name)
        ref_annotations = ref_annotation.annotations
        new_annotations = [
            Tag(self._mapping.get(annotation.value, annotation.value), annotation.lb, annotation.ub)
            for annotation in ref_annotations
            if self._mapping.get(annotation.value, None) != ""
        ]

        document.add_annotationset(
            AnnotationSet(
                self._annotation_name,
                reference=ref_annotation.reference,
                annotations=new_annotations,
            )
        )

        laps = time.time() - start
        sem.logger.info("in %s", timedelta(seconds=laps))


class ExportProcessor(Processor):
    def __init__(
        self,
        exporter,
        lang="fr",
        lang_style="default.css",
        pos_column=None,
        chunk_column=None,
        ner_column=None,
        **kwargs,
    ):
        super(ExportProcessor, self).__init__(**kwargs)

        self._lang = lang
        self._lang_style = lang_style
        self._pos_column = pos_column
        self._chunk_column = chunk_column
        self._ner_column = ner_column
        if isinstance(exporter, str):
            sem.logger.info("getting exporter {0}".format(exporter))
            Exporter = get_exporter(exporter)
            self._exporter = Exporter(lang=self._lang, lang_style=self._lang_style)
        else:
            sem.logger.info("using loaded exporter")
            self._exporter = exporter

    def process_document(self, document, outfile=sys.stdout, output_encoding="utf-8", **kwargs):
        start = time.time()

        sem.logger.debug("setting name/column couples for exportation")

        pos_column = self._pos_column
        chunk_column = self._chunk_column
        ner_column = self._ner_column

        couples = {}
        if "word" in document.corpus.fields:
            couples["token"] = "word"
        elif "token" in document.corpus.fields:
            couples["token"] = "token"

        if pos_column:
            couples["pos"] = pos_column
            sem.logger.debug("POS column is {0}".format(pos_column))
        if chunk_column:
            couples["chunking"] = chunk_column
            sem.logger.debug("chunking column is {0}".format(chunk_column))
        if ner_column:
            couples["ner"] = ner_column
            sem.logger.debug("NER column is {0}".format(ner_column))

        sem.logger.debug("exporting document to {0} format".format(self._exporter.extension))

        self._exporter.document_to_file(document, couples, outfile, encoding=output_encoding)

        laps = time.time() - start
        sem.logger.info("done in %s", timedelta(seconds=laps))


class PymorphyProcessor(Processor):
    def __init__(self, token_field="word", *args, **kwargs):
        super(PymorphyProcessor, self).__init__(**kwargs)

        self._token_field = token_field
        self._morph = pymorphy2.MorphAnalyzer()

    def process_document(self, document, **kwargs):
        start = time.time()
        annotations = AnnotationSet("POS", reference=document.segmentation("tokens"))
        current = 0
        for sentence in document.corpus:
            lemma = []
            pos = []
            for token in sentence.feature(self._token_field):
                analyzed = self._morph.parse(token)
                lemma.append(analyzed[0].normal_form)
                pos.append(str(analyzed[0].tag.POS or analyzed[0].tag).split(',')[0])
                annotations.append(Tag(pos[-1], current, current+1))
                current += 1
            sentence.add(lemma[:], "lemma")
            sentence.add(pos[:], "POS")
        document.add_annotationset(annotations)
        laps = time.time() - start
        sem.logger.info(u'done in %fs' % laps)


__name2class = {
    "segmentation": SegmentationProcessor,
    "enrich": EnrichProcessor,
    "wapiti_label": WapitiLabelProcessor,
    "clean": CleanProcessor,
    "label_consistency": LabelConsistencyProcessor,
    "map_annotations": MapAnnotationsProcessor,
}


def build_processor(name, additional_names=None, **kwargs):
    name2class = __name2class
    name2class.update(additional_names or {})
    return name2class[name](**kwargs)
