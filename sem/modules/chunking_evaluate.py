"""
file: chunking_fscore.py

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


def float2spreadsheet(f):
    """
    For spreadsheets, dots should be replaced by commas.
    """
    return (u"%.2f" %f).replace(u".",u",")

def precision(d):
    return float(len(d["correct"])) / len(d["correct"]+d["type"]+d["boundary"]+d["type+boundary"]+d["noise"])

def recall(d):
    return float(len(d["correct"])) / len(d["correct"]+d["type"]+d["boundary"]+d["type+boundary"]+d["silence"])

def undergeneration(d):
    return float(len(d["silence"])) / len(d["correct"]+d["type"]+d["boundary"]+d["type+boundary"]+d["silence"])

def overgeneration(d):
    return float(len(d["noise"])) / len(d["correct"]+d["type"]+d["boundary"]+d["type+boundary"]+d["noise"])

def substitution(d):
    return float(len(d["type"]+d["boundary"]+d["type+boundary"])) / len(d["correct"]+d["type"]+d["boundary"]+d["type+boundary"])

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
            print "reference_file not handled for CoNLL files"
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
    
    print "reference:", len_ref
    print "tagging:", len_tag
    for key in ["correct", "type", "boundary", "type+boundary", "noise", "silence"]:
        print key, len(d[key])
    
    lines = []
    with codecs.open(infile, "rU", "utf-8") as O:
        lines = O.readlines()
    """for L,R in d["type+boundary"]:
        print L, R
        print u"".join(lines[L.lb : L.ub])
        print"""
    
    print
    print "precision:", precision(d)
    print "recall:", recall(d)
    print
    print "undergeneration:", undergeneration(d)
    print "overgeneration:", overgeneration(d)
    print "substitution:", substitution(d)


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
