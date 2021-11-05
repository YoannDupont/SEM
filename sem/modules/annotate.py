# -*- coding: utf-8 -*-

"""
file: annotate.py

Description: this module allows annotation of SEM documents.

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
import time
from datetime import timedelta

import sem.annotators
import sem.logger
from sem.importers import read_conll
from sem.importers import conll_file
from sem.exporters import CoNLLExporter
from sem.processors import AnnotateProcessor


def main(argv=None):
    annotate(**vars(parser.parse_args(argv)))


def annotate(
    infile,
    outfile,
    annotator,
    token_field,
    field,
    ienc=None,
    oenc=None,
    enc="utf-8",
    log_level="WARNING",
    log_file=None,
):
    """
    Takes a CoNLL-formatted file and write another CoNLL-formatted file
    with additional features in it.

    Parameters
    ----------
    infile : str
        the CoNLL-formatted input file.
    outfile : str
        the CoNLL-formatted output file.
    mdl : str
        the wapiti model file.
    log_level : str or int
        the logging level.
    log_file : str
        if not None, the file to log to (does not remove command-line
        logging).
    """

    start = time.time()

    if log_file is not None:
        sem.logger.addHandler(sem.logger.file_handler(log_file))
    sem.logger.setLevel(log_level)

    ienc = ienc or enc
    oenc = oenc or enc
    annotator = AnnotateProcessor(
        infile=infile,
        outfile=outfile,
        annotator=annotator,
        token_field=token_field,
        field=field,
        ienc=ienc,
        oenc=oenc,
        enc=enc,
        log_level=log_level,
        log_file=log_file
    )

    length = -1
    fields = None
    for sentence in read_conll(infile, ienc):
        fields = fields or [str(i) for i in range(len(sentence.keys()))]
        if length == -1:
            length = len(fields)
        if length != len(sentence.keys()):
            raise ValueError(
                "{} has inconsistent number of columns, found {} and {}".format(
                    infile, length, len(sentence[0])
                )
            )

    document = conll_file(infile, fields, fields[0], encoding=ienc)

    annotator.process_document(document)

    exporter = CoNLLExporter()

    exporter.document_to_file(document, None, outfile, encoding=oenc)

    laps = time.time() - start
    sem.logger.info("done in %s", timedelta(seconds=laps))


parser = argparse.ArgumentParser("An annotation tool for SEM.")

parser.add_argument("infile", help="The input file (CoNLL format)")
parser.add_argument("outfile", help="The output file (CoNLL format)")
parser.add_argument("annotator", help="The name of the annotator")
parser.add_argument(
    "location",
    help="The location of the data used for annotator" " (model, folder with lexica, etc.).",
)
parser.add_argument("token_field", help="The token field (not always useful).")
parser.add_argument("field", help="The output field.")
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
    help="Increase log level (default: critical)",
)
parser.add_argument("--log-file", dest="log_file", help="The name of the log file")
