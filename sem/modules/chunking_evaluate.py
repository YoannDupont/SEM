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

import sys, codecs

from sem.IO.columnIO import Reader
from sem.storage import Tag, Annotation

import sem.importers

def compile_chunks(sentence, column=-1, shift=0):
    entity_chunks = []
    label = u""
    start = -1
    for index, token in enumerate(sentence):
        ne = token[column]
        
        if ne == "O":
            if label:
                entity_chunks.append(Tag(start+shift, index+shift, label))
                label = u""
                start = -1
        elif ne[0] == "B":
            if label:
                entity_chunks.append(Tag(start+shift, index+shift, label))
            start = index
            label = ne[2:]
        elif ne[0] == "I":
            None
        else:
            raise ValueError(ne)
    if label:
        entity_chunks.append(Tag(start+shift, index+shift, label))
        label = u""
        start = -1
    
    return entity_chunks

def mean(numbers):
    return float(sum(numbers)) / len(numbers)

def precision(d):
    numerator = float(len(d["correct"]))
    denominator  = float(len(d["correct"]+d["type"]+d["boundary"]+d["type+boundary"]+d["noise"]))
    if denominator == 0.0:
        return 0.0
    else:
        return numerator / denominator
    return float(len(d["correct"])) / len(d["correct"]+d["type"]+d["boundary"]+d["type+boundary"]+d["noise"])

def recall(d):
    numerator = float(len(d["correct"]))
    denominator = len(d["correct"]+d["type"]+d["boundary"]+d["type+boundary"]+d["silence"])
    if denominator == 0.0:
        return 0.0
    else:
        return numerator / denominator
    return float(len(d["correct"])) / len(d["correct"]+d["type"]+d["boundary"]+d["type+boundary"]+d["silence"])

def undergeneration(d):
    numerator = float(len(d["silence"]))
    denominator = float(len(d["correct"]+d["type"]+d["boundary"]+d["type+boundary"]+d["silence"]))
    if denominator == 0.0:
        return 0.0
    else:
        return numerator / denominator
    return float(len(d["silence"])) / len(d["correct"]+d["type"]+d["boundary"]+d["type+boundary"]+d["silence"])

def overgeneration(d):
    numerator = float(len(d["noise"]))
    denominator = float(len(d["correct"]+d["type"]+d["boundary"]+d["type+boundary"]+d["noise"]))
    if denominator == 0.0:
        return 0.0
    else:
        return numerator / denominator
    return float(len(d["noise"])) / len(d["correct"]+d["type"]+d["boundary"]+d["type+boundary"]+d["noise"])

def substitution(d):
    numerator = float(len(d["type"]+d["boundary"]+d["type+boundary"]))
    denominator = float(len(d["correct"]+d["type"]+d["boundary"]+d["type+boundary"]))
    if denominator == 0.0:
        return 0.0
    else:
        return numerator / denominator
    return float(len(d["type"]+d["boundary"]+d["type+boundary"])) / len(d["correct"]+d["type"]+d["boundary"]+d["type+boundary"])

def fscore(P, R, beta=1.0):
    return ((1+(beta**2))*P*R / (((beta**2)*P)+R) if P+R != 0 else 0.0)

def main(args):
    infile = args.infile
    reference_column = args.reference_column
    tagging_column = args.tagging_column
    ienc = args.ienc or args.enc
    oenc = args.oenc or args.enc
    verbose = args.verbose
    input_format = args.input_format
    reference_file = args.reference_file
    
    counts = {}
    prf = {}
    if input_format == "conll":
        if reference_file:
            print "%s\treference_file not handled for CoNLL files"
        L = []
        R = []
        for n_line, p in Reader(infile, ienc).line_iter():
            L.extend(compile_chunks(p, column=reference_column, shift=n_line))
            R.extend(compile_chunks(p, column=tagging_column, shift=n_line))
    elif input_format == "brat":
        L = sem.importers.brat_file(reference_file).annotation("NER").get_reference_annotations()
        R = sem.importers.brat_file(infile).annotation("NER").get_reference_annotations()
    else:
        raise RuntimeError("format not handled")
    
    len_ref = len(L)
    len_tag = len(R)
    d = {"correct":[], "type":[], "boundary":[], "type+boundary":[], "silence":[], "noise":[]}
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
                d["correct"].append([LR, RR])
                break
            j += 1
        i += 1
    
    # second pass, typing errors
    i  = 0
    while i < len(L):
        LR = L[i]
        j = 0
        while j < len(R):
            RR = R[j]
            if LR.value != RR.value and LR.lb == RR.lb and LR.ub == RR.ub:
                del L[i]
                del R[j]
                d["type"].append([LR, RR])
                break
            j += 1
        i += 1
    
    # third pass, boundary errors
    i  = 0
    while i < len(L):
        LR = L[i]
        j = 0
        while j < len(R):
            RR = R[j]
            if LR.value == RR.value and ((LR.lb != RR.lb and LR.ub == RR.ub) or (LR.lb == RR.lb and LR.ub != RR.ub)):
                del L[i]
                del R[j]
                i -= 1
                d["boundary"].append([LR, RR])
                break
            j += 1
        i += 1
    
    # fourth pass, both type and boundary errors
    i  = 0
    while i < len(L):
        LR = L[i]
        j = 0
        while j < len(R):
            RR = R[j]
            if LR.value != RR.value and (LR.lb != RR.lb and LR.ub == RR.ub) or (LR.lb == RR.lb and LR.ub != RR.ub):
                del L[i]
                del R[j]
                i -= 1
                d["type+boundary"].append([LR, RR])
                break
            j += 1
        i += 1
    
    d["silence"] = L[:]
    d["noise"] = R[:]
    
    entities = set()
    for l in d.values():
        for e in l:
            try:
                l,r = e
                entities.add(l.value)
                entities.add(r.value)
            except:
                entities.add(e.value)
    
    counts = {}
    for entity in entities:
        sub_d = {}
        sub_d["correct"] = [m for m in d["correct"] if m[0].value == entity]
        sub_d["type"] = [m for m in d["type"] if m[0].value == entity or m[1].value == entity]
        sub_d["boundary"] = [m for m in d["boundary"] if m[0].value == entity or m[1].value == entity]
        sub_d["type+boundary"] = [m for m in d["type+boundary"] if m[0].value == entity or m[1].value == entity]
        sub_d["noise"] = [m for m in d["noise"] if m.value == entity]
        sub_d["silence"] = [m for m in d["silence"] if m.value == entity]
        
        counts[entity] = sub_d
    
    # basic counts
    print u"entity\tmeasure\tvalue"
    for entity in sorted(entities):
        print "%s\tcorrect\t%i" %(entity, len(counts[entity]["correct"]))
        print "%s\ttype\t%i" %(entity, len(counts[entity]["type"]))
        print "%s\tboundary\t%i" %(entity, len(counts[entity]["boundary"]))
        print "%s\ttype+boundary\t%i" %(entity, len(counts[entity]["type+boundary"]))
        print "%s\tnoise\t%i" %(entity, len(counts[entity]["noise"]))
        print "%s\tsilence\t%i" %(entity, len(counts[entity]["silence"]))
    print "global\treference\t%i" %(len_ref)
    print "global\ttagging\t%i" %(len_tag)
    for key in ["correct", "type", "boundary", "type+boundary", "noise", "silence"]:
        print "global\t%s\t%i" %(key, len(d[key]))
    
    # P R F
    precisions = []
    recalls = []
    print
    print u"entity\tmeasure\tvalue"
    for entity in sorted(entities):
        precisions.append(precision(counts[entity]))
        recalls.append(recall(counts[entity]))
        print "%s\tprecision\t%.4f" %(entity, precisions[-1])
        print "%s\trecall\t%.4f" %(entity, recalls[-1])
        print "%s\tfscore\t%.4f" %(entity, fscore(precision(counts[entity]), recall(counts[entity])))
    print "global\tprecision\t%.4f" %(precision(d))
    print "global\trecall\t%.4f" %(recall(d))
    print "global\tfscore\t%.4f" %(fscore(precision(d), recall(d)))
    print "global\tmacro-precision\t%.4f" %(mean(precisions))
    print "global\tmacro-recall\t%.4f" %(mean(recalls))
    print "global\tmacro-fscore\t%.4f" %(fscore(mean(precisions), mean(recalls)))
    
    # over/under generation, substitution
    print
    print u"entity\tmeasure\tvalue"
    for entity in sorted(entities):
        print "%s\tundergeneration\t%.4f" %(entity, undergeneration(counts[entity]))
        print "%s\tovergeneration\t%.4f" %(entity, overgeneration(counts[entity]))
        print "%s\tsubstitution\t%.4f" %(entity, substitution(counts[entity]))
    print "global\tundergeneration\t%.4f" %(undergeneration(d))
    print "global\tovergeneration\t%.4f" %(overgeneration(d))
    print "global\tsubstitution\t%.4f" %(substitution(d))


import os.path
import sem

_subparsers = sem.argument_subparsers

parser = _subparsers.add_parser(os.path.splitext(os.path.basename(__file__))[0], description="Get F1-score for tagging using the IOB scheme.")

parser.add_argument("infile",
                    help="The input file (CoNLL format)")
parser.add_argument("-r", "--reference-column", dest="reference_column", type=int, default=-2,
                    help="Column for reference output (default: %(default)s)")
parser.add_argument("-t", "--tagging-column", dest="tagging_column", type=int, default=-1,
                    help="Column for CRF output (default: %(default)s)")
parser.add_argument("-f", "--format", dest="input_format", default="conll",
                    help="The input format (default: %(default)s)")
parser.add_argument("-c", "--reference-file", dest="reference_file",
                    help="The comparing file")
parser.add_argument("--input-encoding", dest="ienc",
                    help="Encoding of the input (default: utf-8)")
parser.add_argument("--output-encoding", dest="oenc",
                    help="Encoding of the input (default: utf-8)")
parser.add_argument("-e", "--encoding", dest="enc", default="utf-8",
                    help="Encoding of both the input and the output (default: utf-8)")
parser.add_argument("-v", "--verbose", dest="verbose", action="store_true",
                    help="Writes feedback during process (default: no output)")
