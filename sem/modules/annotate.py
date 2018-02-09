#-*- coding:utf-8 -*-

"""
file: segmentation.py

Description: performs text segmentation according to given tokeniser.
It is searched in "obj/tokenisers", a valid name to give to this
script is the basename (without extension) of any .py file that can be
found in this directory.

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

import logging, codecs, time, os.path

from datetime import timedelta

from .sem_module import SEMModule as RootModule
import sem.wapiti

#TODO from sem.annotators            import get_annotator
from sem.storage.document     import Document
from sem.storage.segmentation import Segmentation
from sem.logger               import default_handler, file_handler

annotate_logger = logging.getLogger("sem.modules.annotate")
annotate_logger.addHandler(default_handler)

class SEMModule(RootModule):
    def __init__(self, model, field, annotation_fields=None, log_level="WARNING", log_file=None, **kwargs):
        super(SEMModule, self).__init__(log_level=log_level, log_file=log_file, **kwargs)
        
        self._model = model
        self._field = field
        self._annotation_fields = annotation_fields
        
    
    def process_document(self, document, encoding="utf-8", **kwargs):
        """
        
        Parameters
        ----------
        document : sem.storage.Document
            the input data. It is a document with only a content
        log_level : str or int
            the logging level
        log_file : str
            if not None, the file to log to (does not remove command-line
            logging).
        """
        
        start = time.time()
        
        if self._log_file is not None:
            annotate_logger.addHandler(file_handler(self._log_file))
        annotate_logger.setLevel(self._log_level)
        
        annotate_logger.info("annotating document with %s field", self._field)
        
        sem.wapiti.label_document(document, self._model, self._field, encoding, annotation_name=self._field, annotation_fields=self._annotation_fields)
        
        laps = time.time() - start
        annotate_logger.info('in %s' %(timedelta(seconds=laps)))

def main(args):
    sem.wapiti.label(args.infile, args.model, args.outfile)


import sem

_subparsers = sem.argument_subparsers

parser = _subparsers.add_parser(os.path.splitext(os.path.basename(__file__))[0], description="Segments the textual content of a sentence into tokens. They can either be outputted line per line or in a vectorised format.")

parser.add_argument("infile",
                    help="The input file (raw text)")
parser.add_argument("model",
                    help="The name of the tokeniser to import")
parser.add_argument("outfile",
                    help="The output file")
parser.add_argument("--output-format", dest="output_format", choices=("line", "vector"), default="vector",
                    help="The output format (default: %(default)s)")
parser.add_argument("--input-encoding", dest="ienc",
                    help="Encoding of the input (default: UTF-8)")
parser.add_argument("--output-encoding", dest="oenc",
                    help="Encoding of the input (default: UTF-8)")
parser.add_argument("--encoding", dest="enc", default="UTF-8",
                    help="Encoding of both the input and the output (default: UTF-8)")
parser.add_argument("-l", "--log", dest="log_level", choices=("DEBUG","INFO","WARNING","ERROR","CRITICAL"), default="WARNING",
                    help="Increase log level (default: %(default)s)")
parser.add_argument("--log-file", dest="log_file",
                    help="The name of the log file")