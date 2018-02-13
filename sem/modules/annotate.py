#-*- coding: utf-8 -*-

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

import logging, codecs

# measuring time laps
import time
from datetime import timedelta

from multiprocessing import Pool
import functools

from .sem_module import SEMModule as RootModule
from sem.logger import default_handler, file_handler

import sem.annotators

from sem.CRF.model import Model

from sem.IO.columnIO import Reader

from sem.importers import conll_file
from sem.exporters import CoNLLExporter

import os.path
tagging_logger = logging.getLogger("sem.%s" %os.path.basename(__file__).split(".")[0])
tagging_logger.addHandler(default_handler)

class SEMModule(RootModule):
    def __init__(self, annotator, field, log_level="WARNING", log_file=None, *args, **kwargs):
        super(SEMModule, self).__init__(log_level=log_level, log_file=log_file, **kwargs)
        
        if self._log_file is not None:
            tagging_logger.addHandler(file_handler(self._log_file))
        tagging_logger.setLevel(self._log_level)
        
        self._annotator = sem.annotators.get_annotator(annotator)(field, *args, **kwargs)
    
    def process_document(self, document, **kwargs):
        start = time.time()
        self._annotator.process_document(document)
        laps = time.time() - start
        tagging_logger.info(u'done in %s' %timedelta(seconds=laps))

def main(args):
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
    
    if args.log_file is not None:
        tagging_logger.addHandler(file_handler(args.log_file))
    tagging_logger.setLevel(args.log_level)
    
    infile = args.infile
    outfile = args.outfile
    ienc = args.ienc or args.enc
    oenc = args.oenc or args.enc
    annotator = SEMModule(**vars(args))
    
    length = -1
    fields = None
    for sentence in Reader(infile, ienc):
        fields = fields or [unicode(i) for i in range(len(sentence[0]))]
        if length == -1:
            length = len(fields)
        if length != len(sentence[0]):
            raise ValueError(u"%s has inconsistent number of columns, found %i and %i" %(infile, length, len(sentence[0])))
    
    document = conll_file(infile, fields, fields[0], encoding=ienc)
    
    annotator.process_document(document)
    
    exporter = CoNLLExporter()
    
    exporter.document_to_file(document, None, outfile, encoding=oenc)
    
    laps = time.time() - start
    tagging_logger.info("done in %s", timedelta(seconds=laps))



import sem
import argparse, sys

_subparsers = sem.argument_subparsers

parser = _subparsers.add_parser(os.path.splitext(os.path.basename(__file__))[0], description="Annotate file with specified annotator.")

parser.add_argument("infile",
                    help="The input file (CoNLL format)")
parser.add_argument("outfile",
                    help="The output file (CoNLL format)")
parser.add_argument("annotator",
                    help="The name of the annotator")
parser.add_argument("location",
                    help="The location of the data used for annotator (model, folder with lexica, etc.).")
parser.add_argument("token_field",
                    help="The token field (not always useful).")
parser.add_argument("field",
                    help="The output field.")
parser.add_argument("--input-encoding", dest="ienc",
                    help="Encoding of the input (default: UTF-8)")
parser.add_argument("--output-encoding", dest="oenc",
                    help="Encoding of the input (default: UTF-8)")
parser.add_argument("--encoding", dest="enc", default="UTF-8",
                    help="Encoding of both the input and the output (default: UTF-8)")
parser.add_argument("-l", "--log", dest="log_level", choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"), default="WARNING",
                    help="Increase log level (default: critical)")
parser.add_argument("--log-file", dest="log_file",
                    help="The name of the log file")
