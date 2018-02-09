#-*- coding: utf-8 -*-

"""
file: enrich.py

Description: this program is used to enrich a CoNLL-formatted file with
various features.

author: Yoann Dupont
copyright (c) 2016 Yoann Dupont - all rights reserved

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import logging, codecs

# measuring time laps
import time
from datetime import timedelta

from multiprocessing import Pool
import functools

from .sem_module import SEMModule as RootModule
from sem.logger import default_handler, file_handler

import sem.taggers

from sem.CRF.model import Model

from sem.IO.columnIO import Reader

import os.path
tagging_logger = logging.getLogger("sem.%s" %os.path.basename(__file__).split(".")[0])
tagging_logger.addHandler(default_handler)

class SEMModule(RootModule):
    def __init__(self, name, field, log_level="WARNING", log_file=None, *args, **kwargs):
        super(SEMModule, self).__init__(log_level=log_level, log_file=log_file, **kwargs)
        
        self._tagger = sem.taggers.get_tagger(name)(field, *args, **kwargs)
    
    def process_document(self, document, **kwargs):
        start = time.time()
        if self._log_file is not None:
            tagging_logger.addHandler(file_handler(self._log_file))
        tagging_logger.setLevel(self._log_level)
        self._tagger.process_document(document)
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
    mdl = Model.from_wapiti_model(args.modelfile)
    viterbi = mdl.tag_viterbi
    
    """with codecs.open(args.outfile, "w", "utf-8") as O:
        nth = 0
        for sentence in Reader(args.infile, "utf-8"):
            tagging, _, _ = viterbi(sentence)
            for i in range(len(sentence)):
                sentence[i].append(tagging[i])
                O.write(u"\t".join(sentence[i]))
                O.write(u"\n")
            O.write(u"\n")"""
    sentences = []
    for sentence in Reader(args.infile, "utf-8"):
        sentences.append(sentence)
    start = time.time()
    pool = Pool(processes=4)
    results = pool.map(mdl, sentences)
    print results[0]
    """for sentence in sentences:
        tagging, _, _ = viterbi(sentence)
        for i in range(len(sentence)):
            sentence[i].append(tagging[i])"""
    
    laps = time.time() - start
    tagging_logger.info("done in %s", timedelta(seconds=laps))



import sem
import argparse, sys

_subparsers = sem.argument_subparsers

parser = _subparsers.add_parser(os.path.splitext(os.path.basename(__file__))[0], description="Tag file with Wapiti.")

parser.add_argument("infile",
                    help="The input file (CoNLL format)")
parser.add_argument("modelfile",
                    help="The wapiti model file")
parser.add_argument("outfile",
                    help="The output file (CoNLL format)")
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