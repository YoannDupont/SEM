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

from wapiti.api import Model as WapitiModel

import logging, codecs, time, os.path

from datetime import timedelta

import sem.importers
from sem.exporters.conll      import Exporter as CoNLLExporter
from sem.modules.sem_module   import SEMModule as RootModule
from sem                      import PY2
from sem.storage.document     import Document
from sem.storage.segmentation import Segmentation
from sem.logger               import default_handler, file_handler
from sem.misc                 import check_model_available


wapiti_label_logger = logging.getLogger("sem.wapiti_label")
wapiti_label_logger.addHandler(default_handler)
wapiti_label_logger.setLevel("INFO")

class SEMModule(RootModule):
    def __init__(self, model, field, annotation_fields=None, log_level="WARNING", log_file=None, **kwargs):
        super(SEMModule, self).__init__(log_level=log_level, log_file=log_file, **kwargs)
        expected_mode = kwargs.get("expected_mode", self.pipeline_mode)
        
        self._model = model
        self._field = field
        self._annotation_fields = annotation_fields
        
        if self.pipeline_mode == "all" or expected_mode in ("all", self.pipeline_mode):
            check_model_available(model, logger=wapiti_label_logger)
            self._wapiti_model = WapitiModel(encoding="utf-8", model=self._model)
        else:
            self._wapiti_model = None
    
    @property
    def field(self):
        return self._field
    
    @property
    def model(self):
        return self._model
    
    def check_mode(self, expected_mode):
        if (not self._wapiti_model) and self.pipeline_mode == expected_mode:
            check_model_available(model, logger=wapiti_label_logger)
            self._wapiti_model = WapitiModel(encoding="utf-8", model=self._model)
    
    def process_document(self, document, encoding="utf-8", **kwargs):
        """
        Annotate document with Wapiti.
        
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
            wapiti_label_logger.addHandler(file_handler(self._log_file))
        wapiti_label_logger.setLevel(self._log_level)
        
        if self._field in document.corpus.fields:
            wapiti_label_logger.warn("field %s already exists in document, not annotating", self._field)
            
            tags = [[s[self._field] for s in sentence] for sentence in document.corpus]
            document.add_annotation_from_tags(tags, self._field, self._field)
        else:
            wapiti_label_logger.info("annotating document with %s field", self._field)
            
            self._label_document(document, encoding)
        
        laps = time.time() - start
        wapiti_label_logger.info('in %s', timedelta(seconds=laps))
    
    def _label_document(self, document, encoding="utf-8"):
        if self._annotation_fields:
            fields = [document.corpus.entry(field) for field in self._annotation_fields]
        else:
            fields = document.corpus.fields
        tags = []
        for sequence in document.corpus:
            tagging = self._tag_as_wrapper(sequence, fields)
            tags.append(tagging[:])
        
        document.add_annotation_from_tags(tags, self._field, self._field)
    
    def _tag_as_wrapper(self, sequence, fields, encoding="utf-8"):
        if PY2:
            seq_str = u"\n".join([u"\t".join([unicode(token[field]) for field in fields]) for token in sequence]).encode(encoding)
        else:
            seq_str = u"\n".join([u"\t".join([str(token[field]) for field in fields]) for token in sequence]).encode(encoding)
        s = self._wapiti_model.label_sequence(seq_str).decode(encoding)
        return s.strip().split(u"\n")

def main(args):
    for sentence in sem.importers.read_conll():
        fields = ["field-{}".format(i) for i in range(len(sentence[0]))]
        word_field = fields[0]
        break
    
    document = sem.importers.conll_file(args.infile, fields, word_field)
    labeler = SEMModule(args.model, fields)
    exporter = CoNLLExporter()
    
    labeler.process_document(document)
    
    exporter.document_to_file(document, None, args.outfile)
    #sem.wapiti.label(args.infile, args.model, args.outfile)


import sem

_subparsers = sem.argument_subparsers

parser = _subparsers.add_parser(os.path.splitext(os.path.basename(__file__))[0], description='Wrapper for "wapiti label" command.')

parser.add_argument("infile",
                    help="The input file (CoNLL format)")
parser.add_argument("model",
                    help="The name of the model to label data with")
parser.add_argument("outfile",
                    help="The output file")
