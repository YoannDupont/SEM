# -*- coding: utf-8 -*-

"""
file: chunking_evaluate.py

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

import argparse
import os
import collections

from sem.importers import read_conll
from sem.storage import AnnotationSet
from sem.storage import annotation_from_sentence

import sem.importers

CORRECT = "correct output"
TYPE_ERROR = "type error"
BOUNDARY_ERROR = "boundary error"
TYPE_AND_BOUNDARY_ERROR = "type+boundary error"
NOISE_ERROR = "noise error"
SILENCE_ERROR = "silence error"
TP = "true positive"
FP = "false positive"
FN = "false negative"

ERRORS_KINDS = [
    FP, FN, TYPE_ERROR, BOUNDARY_ERROR, TYPE_AND_BOUNDARY_ERROR, NOISE_ERROR, SILENCE_ERROR
]
OUTPUT_KINDS = [CORRECT] + ERRORS_KINDS


def mean(numbers):
    return sum(numbers) / len(numbers)


def precision(d):
    numerator = len(d.get(TP, []))
    denominator = len(d.get(TP, []) + d.get(FP, []))
    if denominator == 0:
        return 0.0
    else:
        return numerator / denominator


def recall(d):
    numerator = len(d.get(TP, []))
    denominator = len(d.get(TP, []) + d.get(FN, []))
    if denominator == 0:
        return 0.0
    else:
        return numerator / denominator


def fscore(P, R, beta=1.0):
    return (1 + (beta ** 2)) * P * R / (((beta ** 2) * P) + R) if P + R != 0.0 else 0.0


def undergeneration(d):
    numerator = len(d.get(SILENCE_ERROR, []))
    denominator = len(d.get(TP, []) + d.get(FN, []))
    if denominator == 0:
        return 0.0
    else:
        return numerator / denominator


def overgeneration(d):
    numerator = len(d.get(NOISE_ERROR, []))
    denominator = len(d.get(TP, []) + d.get(FP, []))
    if denominator == 0:
        return 0.0
    else:
        return numerator / denominator


def substitution(d):
    numerator = len(d.get(FP, [])) - len(d.get(NOISE_ERROR, []))
    denominator = (
        len(d.get(TP, []) + d.get(FP, [])) - len(d.get(NOISE_ERROR, []))
    )
    if denominator == 0:
        return 0.0
    else:
        return numerator / denominator


def get_diff(content, gold, guess, error_kind, context_size=20):
    if error_kind == TYPE_ERROR:
        diff = content[gold.lb - context_size: gold.lb]
        diff += "{{+<{0}>+}} ".format(guess.value)
        diff += "[-<{0}>-] ".format(gold.value)
        diff += content[gold.lb: gold.ub]
        diff += " [-</{0}>-]".format(gold.value)
        diff += " {{+</{0}>+}}".format(guess.value)
        diff += content[gold.ub: gold.ub + context_size]
    elif error_kind == BOUNDARY_ERROR:
        if gold.lb == guess.lb:
            diff = content[gold.lb - context_size: gold.lb]
            diff += "<{0}> ".format(gold.value)
            gold_min = gold.ub < guess.ub
            diff += content[gold.lb: min(gold.ub, guess.ub)]
            diff += (
                " [-</{0}>-]".format(gold.value)
                if min(gold.ub, guess.ub)
                else " {{+</{0}>+}}".format(guess.value)
            )
            diff += content[min(gold.ub, guess.ub): max(gold.ub, guess.ub)]
            diff += (
                " {{+</{0}>+}}".format(guess.value)
                if min(gold.ub, guess.ub)
                else " [-</{0}>-]".format(gold.value)
            )
            diff += content[max(gold.ub, guess.ub): max(gold.ub, guess.ub) + context_size]
        else:
            gold_min = gold.lb < guess.lb
            diff = content[min(gold.lb, guess.lb) - context_size: min(gold.lb, guess.lb)]
            diff += (
                "[-<{0}>-] ".format(gold.value) if gold_min else "{{+<{0}>+}} ".format(guess.value)
            )
            diff += content[min(gold.lb, guess.lb): max(gold.lb, guess.lb)]
            diff += (
                "{{+<{0}>+}} ".format(guess.value) if gold_min else "[-<{0}>-] ".format(gold.value)
            )
            diff += content[max(gold.lb, guess.lb): gold.ub]
            diff += " </{0}>".format(gold.value)
            diff += content[gold.ub: gold.ub + context_size]
    elif error_kind == TYPE_AND_BOUNDARY_ERROR:
        min_lb = (
            gold
            if gold.lb < guess.lb
            else (gold if gold.lb == guess.lb and gold.ub > guess.ub else guess)
        )
        max_lb = gold if min_lb == guess else guess
        min_ub = (
            gold
            if gold.ub < guess.ub
            else (gold if gold.ub == guess.ub and gold.lb > guess.lb else guess)
        )
        max_ub = gold if min_ub == guess else guess
        diff = content[min_lb.lb - context_size: min_lb.lb]
        if min_lb == gold:
            diff += "[-<{0}>-] ".format(gold.value)
            diff += content[min_lb.lb: max_lb.lb]
            diff += "{{+<{0}>+}} ".format(guess.value)
        else:
            diff += "{{+<{0}>+}} ".format(guess.value)
            diff += content[min_lb.lb: max_lb.lb]
            diff += "[-<{0}>-] ".format(gold.value)
        diff += content[max_lb.lb: min_ub.ub]
        if min_ub == gold:
            diff += " [-</{0}>-]".format(gold.value)
            diff += content[min_ub.ub: max_ub.ub]
            diff += " {{+</{0}>+}}".format(guess.value)
        else:
            diff += " {{+</{0}>+}}".format(guess.value)
            diff += content[min_ub.ub: max_ub.ub]
            diff += " [-</{0}>-]".format(gold.value)
        diff += content[max_ub.ub: max_ub.ub + context_size]
    elif error_kind == NOISE_ERROR:
        diff = content[guess.lb - context_size: guess.lb]
        diff += "{{+<{0}>+}} ".format(guess.value)
        diff += content[guess.lb: guess.ub]
        diff += " {{+</{0}>+}}".format(guess.value)
        diff += content[guess.ub: guess.ub + context_size]
    elif error_kind == SILENCE_ERROR:
        diff = content[gold.lb - context_size: gold.lb]
        diff += "[-<{0}>-] ".format(gold.value)
        diff += content[gold.lb: gold.ub]
        diff += " [-</{0}>-]".format(gold.value)
        diff += content[gold.ub: gold.ub + context_size]
    else:
        raise ValueError("Unknown error kind: {0}".format(error_kind))
    return diff.replace("\r", "").replace("\n", " ").replace('"', '\\"')


def main(argv=None):
    evaluate(**vars(parser.parse_args(argv)))


def evaluate(
    infile=None,
    reference_column=None,
    tagging_column=None,
    ienc=None,
    input_format=None,
    reference_file=None,
    annotation_name=None,
    dump=os.devnull,
    context_size=30,
):
    counts = {}
    if input_format == "conll":
        if reference_file:
            raise ValueError("reference_file not handled for CoNLL files")
        L = []
        R = []
        keys = None
        nth = -1
        n_line = 0
        for p in read_conll(infile, ienc):
            nth += 1
            keys = keys or list(p.keys())
            L.extend(annotation_from_sentence(p, column=keys[reference_column], shift=n_line - nth))
            R.extend(annotation_from_sentence(p, column=keys[tagging_column], shift=n_line - nth))
            n_line += len(p) + 1
        document = sem.importers.conll_file(infile, keys, keys[0], encoding=ienc)
        L = AnnotationSet(
            "", annotations=L, reference=document.segmentation("tokens")
        ).get_reference_annotations()
        R = AnnotationSet(
            "", annotations=R, reference=document.segmentation("tokens")
        ).get_reference_annotations()
    elif input_format == "brat":
        document = sem.importers.brat_file(reference_file)
        L = document.annotationset("NER").get_reference_annotations()
        R = sem.importers.brat_file(infile).annotationset("NER").get_reference_annotations()
    elif input_format in ("sem", "SEM"):
        document = sem.importers.sem_document_from_xml(reference_file)
        system = sem.importers.sem_document_from_xml(infile)
        common_annotations = set(document.annotationsets.keys()) & set(system.annotationsets.keys())
        if len(common_annotations) == 1 and annotation_name is None:
            annotation_name = list(common_annotations)[0]
        if annotation_name is None:
            raise RuntimeError("Could not find an annotation set to evaluate: please provide one")
        L = document.annotationset(annotation_name).get_reference_annotations()
        R = system.annotationset(annotation_name).get_reference_annotations()
    else:
        raise RuntimeError("format not handled: {0}".format(input_format))

    len_ref = len(L)
    len_tag = len(R)
    d = collections.defaultdict(list)
    # first pass, removing correct
    i = 0
    while i < len(L):
        LR = L[i]
        j = 0
        while j < len(R):
            RR = R[j]
            if LR == RR:
                del L[i]
                del R[j]
                i -= 1
                d[CORRECT].append([LR, RR])
                d[TP].append(LR)
                break
            j += 1
        i += 1

    # second pass, typing errors
    i = 0
    while i < len(L):
        LR = L[i]
        j = 0
        while j < len(R):
            RR = R[j]
            if LR.value != RR.value and LR.lb == RR.lb and LR.ub == RR.ub:
                del L[i]
                del R[j]
                d[TYPE_ERROR].append([LR, RR])
                d[FN].append(LR)
                d[FP].append(RR)
                break
            j += 1
        i += 1

    # third pass, boundary errors
    i = 0
    while i < len(L):
        LR = L[i]
        j = 0
        while j < len(R):
            RR = R[j]
            if LR.value == RR.value and (
                (LR.lb != RR.lb and LR.ub == RR.ub) or (LR.lb == RR.lb and LR.ub != RR.ub)
            ):
                del L[i]
                del R[j]
                i -= 1
                d[BOUNDARY_ERROR].append([LR, RR])
                d[FN].append(LR)
                d[FP].append(RR)
                break
            j += 1
        i += 1

    # fourth pass, both type and boundary errors
    i = 0
    while i < len(L):
        LR = L[i]
        j = 0
        while j < len(R):
            RR = R[j]
            if (
                LR.value != RR.value
                and (LR.lb != RR.lb and LR.ub == RR.ub)
                or (LR.lb == RR.lb and LR.ub != RR.ub)
            ):
                del L[i]
                del R[j]
                i -= 1
                d[TYPE_AND_BOUNDARY_ERROR].append([LR, RR])
                d[FN].append(LR)
                d[FP].append(RR)
                break
            j += 1
        i += 1

    d[SILENCE_ERROR] = L[:]
    d[NOISE_ERROR] = R[:]
    d[FN].extend(L[:])
    d[FP].extend(R[:])

    entities = set()
    for vals in d.values():
        for val in vals:
            try:
                left, right = val
                entities.add(left.value)
                entities.add(right.value)
            except (AttributeError, TypeError):
                entities.add(val.value)

    with open(dump, "w", encoding="utf-8") as output_stream:
        output_stream.write("error kind\treference entity\toutput entity\tdiff\n")
        for error_kind in (
            TYPE_ERROR,
            BOUNDARY_ERROR,
            TYPE_AND_BOUNDARY_ERROR,
            NOISE_ERROR,
            SILENCE_ERROR,
        ):
            for ex in d[error_kind]:
                if error_kind == NOISE_ERROR:
                    gold = None
                    guess = ex
                elif error_kind == SILENCE_ERROR:
                    gold = ex
                    guess = None
                else:
                    gold = ex[0]
                    guess = ex[1]
                gold_str = (
                    (
                        "{0}:{1}".format(gold.value, document.content[gold.lb: gold.ub])
                        if gold
                        else ""
                    )
                    .replace("\r", "")
                    .replace("\n", " ")
                )
                guess_str = (
                    (
                        "{0}:{1}".format(guess.value, document.content[guess.lb: guess.ub])
                        if guess
                        else ""
                    )
                    .replace("\r", "")
                    .replace("\n", " ")
                )
                diff = get_diff(
                    document.content, gold, guess, error_kind, context_size=context_size
                )
                output_stream.write(
                    "{0}\t{1}\t{2}\t{3}\n".format(error_kind, gold_str, guess_str, diff)
                )

    counts = {}
    for entity in entities:
        sub_d = {}
        sub_d[CORRECT] = [m for m in d[CORRECT] if m[0].value == entity]
        sub_d[TYPE_ERROR] = [
            m for m in d[TYPE_ERROR] if m[0].value == entity or m[1].value == entity
        ]
        sub_d[BOUNDARY_ERROR] = [
            m for m in d[BOUNDARY_ERROR] if m[0].value == entity or m[1].value == entity
        ]
        sub_d[TYPE_AND_BOUNDARY_ERROR] = [
            m for m in d[TYPE_AND_BOUNDARY_ERROR] if m[0].value == entity or m[1].value == entity
        ]
        sub_d[NOISE_ERROR] = [m for m in d[NOISE_ERROR] if m.value == entity]
        sub_d[SILENCE_ERROR] = [m for m in d[SILENCE_ERROR] if m.value == entity]
        sub_d[TP] = [m for m in d[TP] if m.value == entity]
        sub_d[FP] = [m for m in d[FP] if m.value == entity]
        sub_d[FN] = [m for m in d[FN] if m.value == entity]
        counts[entity] = sub_d

    # basic counts
    print("entity\tmeasure\tvalue")
    for entity in sorted(entities):
        for kind in OUTPUT_KINDS:
            print("{0}\t{1}\t{2}".format(entity, kind, len(counts[entity][kind])))
    print("global\treference\t{0}".format(len_ref))
    print("global\ttagging\t{0}".format(len_tag))
    for kind in OUTPUT_KINDS:
        print("global\t{0}\t{1}".format(kind, len(d[kind])))

    # P R F
    precisions = []
    recalls = []
    print()
    print("entity\tmeasure\tvalue")
    for entity in sorted(entities):
        precisions.append(precision(counts[entity]))
        recalls.append(recall(counts[entity]))
        print("{0}\tprecision\t{1:.4f}".format(entity, precisions[-1]))
        print("{0}\trecall\t{1:.4f}".format(entity, recalls[-1]))
        print(
            "{0}\tfscore\t{1:.4f}".format(
                entity, fscore(precision(counts[entity]), recall(counts[entity]))
            )
        )
    print("global\tprecision\t{0:.4f}".format(precision(d)))
    print("global\trecall\t{0:.4f}".format(recall(d)))
    print("global\tfscore\t{0:.4f}".format(fscore(precision(d), recall(d))))
    print("global\tmacro-precision\t{0:.4f}".format(mean(precisions)))
    print("global\tmacro-recall\t{0:.4f}".format(mean(recalls)))
    print("global\tmacro-fscore\t{0:.4f}".format(fscore(mean(precisions), mean(recalls))))

    # over/under generation, substitution
    print()
    print("entity\tmeasure\tvalue")
    for entity in sorted(entities):
        print("{0}\tundergeneration\t{1:.4f}".format(entity, undergeneration(counts[entity])))
        print("{0}\tovergeneration\t{1:.4f}".format(entity, overgeneration(counts[entity])))
        print("{0}\tsubstitution\t{1:.4f}".format(entity, substitution(counts[entity])))
    print("global\tundergeneration\t{0:.4f}".format(undergeneration(d)))
    print("global\tovergeneration\t{0:.4f}".format(overgeneration(d)))
    print("global\tsubstitution\t{0:.4f}".format(substitution(d)))


parser = argparse.ArgumentParser("Get F1-score for tagging using the IOB scheme.")

parser.add_argument("infile", help="The input file (CoNLL format)")
parser.add_argument(
    "-r",
    "--reference-column",
    dest="reference_column",
    type=int,
    default=-2,
    help="Column for reference output (default: %(default)s)",
)
parser.add_argument(
    "-t",
    "--tagging-column",
    dest="tagging_column",
    type=int,
    default=-1,
    help="Column for CRF output (default: %(default)s)",
)
parser.add_argument(
    "-f",
    "--format",
    dest="input_format",
    default="conll",
    help="The input format (default: %(default)s)",
)
parser.add_argument(
    "-a",
    "--annotation-name",
    dest="annotation_name",
    help="The annotation name, useful for some formats, like SEM.",
)
parser.add_argument("-c", "--reference-file", dest="reference_file", help="The comparing file")
parser.add_argument("--input-encoding", dest="ienc", help="Encoding of the input (default: utf-8)")
parser.add_argument(
    "-d",
    "--dump",
    dest="dump",
    default=os.devnull,
    help="File where to dump errors (default: redirect to devnull)",
)
parser.add_argument(
    "-s",
    "--context-size",
    dest="context_size",
    type=int,
    default=30,
    help="context size (default: %(default)s)",
)
