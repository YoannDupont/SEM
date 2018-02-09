# -*- coding: utf-8 -*-

"""
file: text.py

Description: export annotated file to text format

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

import json

from sem.exporters.exporter import Exporter as DefaultExporter
from sem.storage.annotation import tag_annotation_from_sentence as get_pos, chunk_annotation_from_sentence as get_chunks
from sem.storage.segmentation import Segmentation

class Exporter(DefaultExporter):
    __ext = "json"
    
    def __init__(self, *args, **kwargs):
        pass
    
    def document_to_unicode(self, document, couples, **kwargs):
        return json.dumps(self.document_to_data(document, couples, **kwargs), indent=2, ensure_ascii=False)
    
    def corpus_to_unicode(self, corpus, couples, **kwargs):
        raise NotImplementedError("corpus_to_unicode not yet implemented for json exporter")
    
    def document_to_data(self, document, couples, **kwargs):
        """
        This is just creating a dictionary from the document.
        Nearly copy-pasta of the Document.unicode method.
        """
        
        json_dict = {}
        json_dict[u"content"] = document.content
        
        json_dict[u"segmentations"] = {}
        refs = [seg.reference for seg in document.segmentations.values() if seg.reference]
        for seg in document.segmentations.values():
            json_dict[u"segmentations"][seg.name] = {}
            ref = (seg.reference.name if isinstance(seg.reference, Segmentation) else seg.reference)
            if ref:
                json_dict[u"segmentations"][seg.name]["reference"] = ref
            json_dict[u"segmentations"][seg.name]["spans"] = [{u"s":span.lb, u"l":len(span)} for span in seg.spans]
        
        json_dict[u"annotations"] = {}
        for annotation in document.annotations.values():
            json_dict[u"annotations"][annotation.name] = {}
            reference = ("" if not annotation.reference else u"%s" %(annotation.reference if type(annotation.reference) in (str, unicode) else annotation.reference.name))
            if reference:
                json_dict[u"annotations"][annotation.name][u"reference"] = reference
            json_dict[u"annotations"][annotation.name]["annotations"] = [{u"v":tag.value, u"s":tag.lb, u"l":len(tag)} for tag in annotation]
        
        return json_dict
