# -*- coding:utf-8 -*-

"""
file: wapiti_label.py

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

import sem.importers
import sem.logger
from sem.exporters import CoNLLExporter
from sem.processors import WapitiLabelProcessor


def main(argv=None):
    wapiti_label(parser.parse_args(argv))


def wapiti_label(infile, model, outfile):
    for sentence in sem.importers.read_conll(infile, "utf-8"):
        fields = ["field-{}".format(i) for i in range(len(sentence[0]))]
        word_field = fields[0]
        break

    document = sem.importers.conll_file(infile, fields, word_field)
    labeler = WapitiLabelProcessor(model, fields)
    exporter = CoNLLExporter()

    labeler.process_document(document)

    exporter.document_to_file(document, None, outfile)


parser = argparse.ArgumentParser("Label some file with wapiti.")

parser.add_argument("infile", help="The input file (CoNLL format)")
parser.add_argument("model", help="The name of the model to label data with")
parser.add_argument("outfile", help="The output file")
