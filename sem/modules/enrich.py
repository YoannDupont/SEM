#-*- coding: utf-8 -*-

"""
file: enrich.py

Description: this program is used to enrich a CoNLL-formatted file with
various features.

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

import logging

# measuring time laps
import time
from datetime import timedelta

from .sem_module import SEMModule as RootModule

from sem.information import Informations
from sem.IO import KeyReader, KeyWriter
from sem.logger import default_handler, file_handler
from sem.misc import is_string

import os.path
enrich_logger = logging.getLogger("sem.{0}".format(os.path.basename(__file__).split(".")[0]))
enrich_logger.addHandler(default_handler)

class SEMModule(RootModule):
    def __init__(self, informations, mode=u"label", log_level="WARNING", log_file=None, **kwargs):
        super(SEMModule, self).__init__(log_level=log_level, log_file=log_file, **kwargs)
        
        self._mode = mode
        self._source = informations
        
        if is_string(informations):
            enrich_logger.info('loading {0}'.format(informations))
            self._informations = Informations(self._source, mode=self._mode)
        else:
            self._informations = self._source
    
    @property
    def informations(self):
        return self._informations
    
    @property
    def mode(self):
        return self._mode
    
    @mode.setter
    def mode(self, mode):
        if not is_string(self._source):
            raise RuntimeError("cannot change mode for Enrich module: source for informations is not a file.")
        self._mode = mode
        enrich_logger.info('loading {0}'.format(self._source))
        self._informations = Informations(self._source, mode=self._mode)
    
    def process_document(self, document, **kwargs):
        """
        Updates the CoNLL-formatted corpus inside a document with various
        features.
        
        Parameters
        ----------
        document : sem.storage.Document
            the input data, contains an object representing CoNLL-formatted
            data. Each token is a dict which works like TSV.
        log_level : str or int
            the logging level
        log_file : str
            if not None, the file to log to (does not remove command-line
            logging).
        """
        
        start = time.time()
        
        if self._log_file is not None:
            enrich_logger.addHandler(file_handler(self._log_file))
        enrich_logger.setLevel(self._log_level)
        
        informations = self._informations
        missing_fields = set([I.name for I in informations.bentries + informations.aentries]) - set(document.corpus.fields)
        
        if len(missing_fields) > 0:
            raise ValueError("Missing fields in input corpus: {0}".format(u",".join(sorted(missing_fields))))
        
        enrich_logger.debug('enriching file "{0}"'.format(document.name))
        
        new_fields = [feature.name for feature in informations.features if feature.display]
        document.corpus.fields += new_fields
        nth = 0
        for i, sentence in enumerate(informations.enrich(document.corpus)):
            nth += 1
            if (0 == nth % 1000):
                enrich_logger.debug('{0} sentences enriched'.format(nth))
        enrich_logger.debug('{0} sentences enriched'.format(nth))
        
        laps = time.time() - start
        enrich_logger.info("done in {0}".format(timedelta(seconds=laps)))

def main(args):
    """
    Takes a CoNLL-formatted file and write another CoNLL-formatted file
    with additional features in it.
    
    Parameters
    ----------
    infile : str
        the CoNLL-formatted input file.
    infofile : str
        the XML file containing the different features.
    mode : str
        the mode to use for infofile. Some inputs may only be present in
        a particular mode. For example, the output tag is only available
        in "train" mode.
    log_level : str or int
        the logging level.
    log_file : str
        if not None, the file to log to (does not remove command-line
        logging).
    """
    
    start = time.time()
    
    if args.log_file is not None:
        enrich_logger.addHandler(file_handler(args.log_file))
    enrich_logger.setLevel(args.log_level)
    enrich_logger.info('parsing enrichment file "{0}"'.format(args.infofile))
    
    informations = Informations(path=args.infofile, mode=args.mode)
    
    enrich_logger.debug('enriching file "{0}"'.format(args.infile))
    
    bentries = [entry.name for entry in informations.bentries]
    aentries = [entry.name for entry in informations.aentries]
    features = [feature.name for feature in informations.features if feature.display]
    with KeyWriter(args.outfile, args.oenc or args.enc, bentries + features + aentries) as O:
        nth = 0
        for p in informations.enrich(KeyReader(args.infile, args.ienc or args.enc, bentries + aentries)):
            O.write_p(p)
            nth += 1
            if (0 == nth % 1000):
                enrich_logger.debug('{0} sentences enriched'.format(nth))
        enrich_logger.debug('{0} sentences enriched'.format(nth))
    
    laps = time.time() - start
    enrich_logger.info("done in {0}".format(timedelta(seconds=laps)))



import sem
import argparse, sys

_subparsers = sem.argument_subparsers

parser = _subparsers.add_parser(os.path.splitext(os.path.basename(__file__))[0], description="Adds information to a file using and XML-styled configuration file.")

parser.add_argument("infile",
                    help="The input file (CoNLL format)")
parser.add_argument("infofile",
                    help="The information file (XML format)")
parser.add_argument("outfile",
                    help="The output file (CoNLL format)")
parser.add_argument("-m", "--mode", dest="mode", default=u"train", choices=(u"train", u"label", u"annotate", u"annotation"),
                    help="The mode for enrichment. May make entries vary (default: %(default)s)")
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
