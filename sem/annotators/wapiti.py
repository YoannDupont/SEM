# -*- coding: utf-8 -*-

"""
file: wapiti.py

Description: a tagger based on python implementation of wapiti.

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

try:
    from xml.etree import cElementTree as ET
except ImportError:
    from xml.etree import ElementTree as ET

import logging

from . import Annotator as RootAnnotator
from sem.logger import default_handler
from sem.CRF.model import Model as WapitiModel

from sem.misc import check_model_available

wapiti_logger = logging.getLogger("sem.annotators.wapiti")
wapiti_logger.addHandler(default_handler)
wapiti_logger.setLevel("INFO")

class Annotator(RootAnnotator):
    def __init__(self, field, location, input_encoding=None, *args, **kwargs):
        super(Annotator, self).__init__(field, location, input_encoding=input_encoding, *args, **kwargs)
        
        check_model_available(self._location, logger=wapiti_logger)
        
        self._model = WapitiModel.from_wapiti_model(self._location, encoding=input_encoding)

    def process_document(self, document, annotation_name=None, annotation_fields=None, *args, **kwargs):
        if annotation_fields is None:
            fields = document.corpus.fields
        else:
            fields = annotation_fields
        
        if annotation_name is None:
            annotation_name = unicode(self._field)
        
        tags = []
        for sequence in document.corpus:
            tagging, _, _ = self._model.tag_viterbi(document.corpus.to_matrix(sequence))
            tags.append(tagging[:])
        
        document.add_annotation_from_tags(tags, self._field, annotation_name)
