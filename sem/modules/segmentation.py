# -*- coding:utf-8 -*-

"""
file: segmentation.py

Description: performs text segmentation according to given tokeniser.

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
import pathlib

from sem.storage import Document
import sem.logger
from sem.processors import SegmentationProcessor


def main(argv=None):
    segmentation(parser.parse_args(argv))


def segmentation(args):
    if args.log_file is not None:
        sem.logger.addHandler(sem.logger.file_handler(args.log_file))
    sem.logger.setLevel(args.log_level)

    ienc = args.ienc or args.enc
    oenc = args.oenc or args.enc
    segmenter = SegmentationProcessor(args.tokeniser_name)
    document = Document(
        pathlib.Path(args.infile).name,
        content=open(args.infile, "rU", encoding=ienc).read().replace("\r", ""),
    )
    segmenter.process_document(document)
    tokens_spans = document.segmentation("tokens")
    sentence_spans = document.segmentation("sentences")
    joiner = "\n" if args.output_format == "vector" else " "
    content = document.content
    with open(args.outfile, "w", encoding=oenc) as output_stream:
        for sentence in sentence_spans:
            sentence_token_spans = tokens_spans[sentence.lb: sentence.ub]
            sentence_tokens = [content[s.lb: s.ub] for s in sentence_token_spans]
            output_stream.write(joiner.join(sentence_tokens))
            if args.output_format == "vector":
                output_stream.write("\n")
            output_stream.write("\n")


parser = argparse.ArgumentParser(
    "Segments the textual content of a sentence into tokens."
    " They can either be outputted line per line or in a vectorised format."
)

parser.add_argument("infile", help="The input file (raw text)")
parser.add_argument("tokeniser_name", help="The name of the tokeniser to import")
parser.add_argument("outfile", help="The output file")
parser.add_argument(
    "--output-format",
    dest="output_format",
    choices=("line", "vector"),
    default="vector",
    help="The output format (default: %(default)s)",
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
