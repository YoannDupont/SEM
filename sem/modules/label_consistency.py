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

import argparse

from sem.storage import (chunk_annotation_from_sentence, compile_multiword)
from sem.importers import read_conll
from sem.processors import (overriding_label_consistency, non_overriding_label_consistency)


def main(argv=None):
    label_consistency(**vars(parser.parse_args(argv)))


def label_consistency(
    infile,
    outfile,
    token_column=0,
    tag_column=-1,
    label_consistency="overriding",
    ienc=None,
    oenc=None,
    enc="utf-8",
):
    ienc = ienc or enc
    oenc = oenc or enc

    entities = {}
    counts = {}
    for p in read_conll(infile, ienc):
        G = chunk_annotation_from_sentence(p, column=tag_column)
        for entity in G:
            id = entity.value
            form = " ".join(
                [p.feature(token_column)[index] for index in range(entity.lb, entity.ub)]
            )
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

    if label_consistency == "non-overriding":
        feature = non_overriding_label_consistency
    else:
        feature = overriding_label_consistency

    trie = compile_multiword(entities)
    with open(outfile, "w", encoding=oenc) as output_stream:
        for p in read_conll(infile, ienc):
            p.add(feature(p, entities, trie.data, token_column, tag_column), tag_column)
            for token in zip(*[p.feature(key) for key in p.keys()]):
                output_stream.write(("\t".join(token)) + "\n")
            output_stream.write("\n")


parser = argparse.ArgumentParser("Broadcasts annotations based on form.")

parser.add_argument("infile", help="The input file (CoNLL format)")
parser.add_argument("outfile", help="The output file")
parser.add_argument(
    "-t", "--token-column", type=int, default=0, help="Token column"
)
parser.add_argument(
    "-c", "--tag-column", type=int, default=-1, help="Tagging column"
)
parser.add_argument(
    "--label-consistency",
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
