# -*- coding: utf-8 -*-

"""
file: wapiti.py

Description: a very simple wrapper for calling wapiti. Provides train
and test procedures.
TODO: add every option for train and test
TODO: add support for other modes, such as dump and update (1.5.0+)

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
along with this program. If not, see GNU official website.
"""

try:
    from xml.etree import cElementTree as ET
except ImportError:
    from xml.etree import ElementTree as ET

import logging

from sem.logger import default_handler

from sem.CRF.model import Model as WapitiModel

wapiti_logger = logging.getLogger("sem.wapiti")
wapiti_logger.addHandler(default_handler)
wapiti_logger.setLevel("INFO")

class Tagger(object):
    def __init__(self, field, model, encoding="utf-8", *atgs, **kwargs):
        self._field = field
        self._model = WapitiModel.from_wapiti_model(model, encoding=encoding)

    def process_document(self, document, annotation_name=None, annotation_fields=None):
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
