#-*- coding:utf-8 -*-

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

parser = _subparsers.add_parser(os.path.splitext(os.path.basename(__file__))[0], description='Wrapper for "wapiti label" command.')

parser.add_argument("infile",
                    help="The input file (CoNLL format)")
parser.add_argument("model",
                    help="The name of the model to label data with")
parser.add_argument("outfile",
                    help="The output file")
