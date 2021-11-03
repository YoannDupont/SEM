# -*- coding: utf-8 -*-

"""
file: pymorphy.py

Description: this module allows to use pymorphy2 for lemmatizing and POS tagging russian.

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

from sem.processors import PymorphyProcessor


def main(argv=None):
    pymorphy(parser.parse_args(argv))


def pymorphy(
    infile,
    outfile,
    token_field,
    ienc=None,
    oenc=None,
    enc="utf-8",
    log_level="WARNING",
    log_file=None,
):
    token_field = int(token_field or 0)
    processor = PymorphyProcessor()

    with open(infile, encoding=ienc or enc) as input_stream:
        with open(outfile, "w", encoding=oenc or enc) as output_stream:
            for line in input_stream:
                parts = line.strip().split()
                if parts:
                    token = parts[token_field]
                    analyzed = processor._morph.parse(token)
                    parts.append(analyzed[0].normal_form)
                    parts.append(str(analyzed[0].tag.POS or analyzed[0].tag).split(',')[0])
                    output_stream.write("\t".join(parts))
                output_stream.write("\n")


parser = argparse.ArgumentParser("Annotate file with pymorphy2.")

parser.add_argument("infile",
                    help="The input file (CoNLL format)")
parser.add_argument("outfile",
                    help="The output file (CoNLL format)")
parser.add_argument("-t", "--token-field",
                    help="The token field. From command line, the token column.")
parser.add_argument("--input-encoding", dest="ienc",
                    help="Encoding of the input (default: UTF-8)")
parser.add_argument("--output-encoding", dest="oenc",
                    help="Encoding of the input (default: UTF-8)")
parser.add_argument("--encoding", dest="enc", default="UTF-8",
                    help="Encoding of both the input and the output (default: UTF-8)")
parser.add_argument("-l", "--log", dest="log_level",
                    choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"), default="WARNING",
                    help="Increase log level (default: %(default)s)")
parser.add_argument("--log-file", dest="log_file",
                    help="The name of the log file")
