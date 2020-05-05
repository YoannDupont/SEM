# -*- coding:utf-8 -*-

"""
file: label_consistency.py

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
import re

from sem.modules.sem_module import SEMModule as RootModule
from sem.storage import Tag, Trie, Span
from sem.storage import (chunk_annotation_from_sentence, compile_multiword)
from sem.importers import read_conll
from sem.features import NUL
from sem.misc import longest_common_substring
import pickle


def normalize(token):
    apostrophes = re.compile("[\u2019]", re.U)
    lower_a = re.compile("[àáâãäåæ]", re.U)
    upper_a = re.compile("[ÀÁÂÃÄÅÆ]", re.U)
    lower_e = re.compile("[éèêë]", re.U)
    upper_e = re.compile("[ÉÈÊË]", re.U)
    lower_i = re.compile("[ìíîï]", re.U)
    upper_i = re.compile("[ÌÍÎÏ]", re.U)

    normalized = apostrophes.sub("'", token)
    normalized = lower_a.sub("a", normalized)
    normalized = upper_a.sub("A", normalized)
    normalized = lower_e.sub("e", normalized)
    normalized = upper_e.sub("E", normalized)
    normalized = lower_i.sub("i", normalized)
    normalized = upper_i.sub("I", normalized)
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
    annotations = document.annotation(field).get_reference_annotations()

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
                for ann in document.annotation(field)
                if new_tag.lb <= ann.lb and ann.ub <= new_tag.ub and ann.value == new_tag.value
            ]
        )
    for to_remove_tag in to_remove_tags:
        try:
            document.annotation(field)._annotations.remove(to_remove_tag)
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


def label_consistency(sentence, form2entity, trie, entry, ne_entry):
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


class SEMModule(RootModule):
    def __init__(
        self,
        field,
        log_level="WARNING",
        log_file=None,
        token_field="word",
        label_consistency="overriding",
        **kwargs,
    ):
        super(SEMModule, self).__init__(log_level=log_level, log_file=log_file, **kwargs)
        self._field = field
        self._token_field = token_field

        if label_consistency == "overriding":
            self._feature = overriding_label_consistency
        else:
            self._feature = label_consistency

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
            # p[field] = self._feature(p, entities, value.data, token_field, field)
            p.add(self._feature(p, entities, value.data, token_field, field), field)

        tags = [sentence.feature(field) for sentence in corpus]
        document.add_annotation_from_tags(tags, field, field)

        if abbreviation_resolution:
            detect_abbreviations(document, field)


def main(args):
    ienc = args.ienc or args.enc
    oenc = args.oenc or args.enc

    entities = {}
    counts = {}
    for p in read_conll(args.infile, ienc):
        G = chunk_annotation_from_sentence(p, column=args.tag_column)
        for entity in G:
            id = entity.value
            form = " ".join([p[index][args.token_column] for index in range(entity.lb, entity.ub)])
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

    if args.label_consistency == "non-overriding":
        feature = label_consistency
    else:
        feature = overriding_label_consistency

    trie = compile_multiword(entities)
    with open(args.outfile, "w", encoding=oenc) as output_stream:
        for p in read_conll(args.infile, ienc):
            p.add(feature(p, entities, trie.data, args.token_column, args.tag_column), args.tag_column)
            for token in zip(*[p.feature(key) for key in p.keys()]):
                output_stream.write(("\t".join(token)) + "\n")
            output_stream.write("\n")


import sem

_subparsers = sem.argument_subparsers

parser = _subparsers.add_parser(
    pathlib.Path(__file__).stem, description="Broadcasts annotations based on form."
)

parser.add_argument("infile", help="The input file (CoNLL format)")
parser.add_argument("outfile", help="The output file")
parser.add_argument(
    "-t", "--token-column", dest="token_column", type=int, default=0, help="Token column"
)
parser.add_argument(
    "-c", "--tag-column", dest="tag_column", type=int, default=-1, help="Tagging column"
)
parser.add_argument(
    "--label-consistency",
    dest="label_consistency",
    choices=("non-overriding", "overriding"),
    default="overriding",
    help="Non-overriding leaves CRF's annotation as they are,"
    " overriding label_consistency erases them if it finds a longer one"
    " (default=%(default)s).",
)
parser.add_argument("--input-encoding", dest="ienc", help="Encoding of the input (default: utf-8)")
parser.add_argument("--output-encoding", dest="oenc", help="Encoding of the input (default: utf-8)")
parser.add_argument(
    "-e",
    "--encoding",
    dest="enc",
    default="utf-8",
    help="Encoding of both the input and the output (default: utf-8)",
)
parser.add_argument(
    "-v",
    "--verbose",
    dest="verbose",
    action="store_true",
    help="Writes feedback during process (default: no output)",
)
