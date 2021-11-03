# -*- coding:utf-8 -*-

"""file: map_annotations.py

Description: Map annotations according to a mapping. If no mapping is provided
for a given type, it will remain unchanged. If an empty mapping is provided,
every annotation of that type will be discarded. This module only affects
annotations, not CoNLL Corpus.

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

from sem.importers import read_conll
from sem.storage import compile_map


def main(argv=None):
    map_annotations(**vars(parser.parse_args(argv)))


def map_annotations(
    infile,
    mapping,
    outfile,
    column=-1,
    ienc=None,
    oenc=None,
    enc="utf-8",
    log_level="WARNING",
    log_file=None
):
    with open(mapping, encoding=ienc or enc) as input_stream:
        mapping = compile_map(input_stream)

    # here we do not simply go through the processor because of the non-fixed
    # columns that make using the processor a little bit awkward.
    # We instead emulate its behaviour here.
    with open(outfile, "w", encoding=oenc or enc) as output_stream:
        for sentence in read_conll(infile, encoding=ienc or enc):
            columns = sorted(sentence.keys())
            index = columns[column]
            tags = sentence.feature(index)
            prefixes = [
                ("_" if tag[0] == "_" else (tag[:2] if len(tag) > 2 and tag[1] == "-" else tag))
                for tag in tags
            ]
            values = [tags[i][len(prefixes[i]):] for i in range(len(tags))]
            values = [mapping.get(value, value) for value in values]
            values = [prefixes[i]+values[i] for i in range(len(tags))]
            sentence.add(values, index)
            output_stream.write(sentence.conll(columns) + "\n\n")


parser = argparse.ArgumentParser(
    "Map annotations according to a mapping."
    " If no mapping is provided for a given type,"
    " it will remain unchanged."
    " If an empty mapping is provided,"
    " every annotation of that type will be discarded.",
)

parser.add_argument("infile", help="The input file (CoNLL format)")
parser.add_argument("mapping", help="The mapping file")
parser.add_argument("outfile", help="The output file")
parser.add_argument(
    "-c", "--column", type=int, default=-1, help="The column to map (default: %(default)s)"
)
parser.add_argument("--input-encoding", dest="ienc", help="Encoding of the input (default: UTF-8)")
parser.add_argument("--output-encoding", dest="oenc", help="Encoding of the input (default: UTF-8)")
parser.add_argument(
    "--encoding",
    dest="enc",
    default="UTF-8",
    help="Encoding of both the input and the output (default: UTF-8)",
)
parser.add_argument(
    "-l",
    "--log",
    dest="log_level",
    choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
    default="WARNING",
    help="Increase log level (default: %(default)s)",
)
parser.add_argument("--log-file", dest="log_file", help="The name of the log file")
