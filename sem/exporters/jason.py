# -*- coding: utf-8 -*-

"""
file: jason.py

Description: export annotated json format

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

import json

from .exporter import Exporter as DefaultExporter
from sem.storage.annotation import tag_annotation_from_sentence as get_pos, chunk_annotation_from_sentence as get_chunks
from sem.storage.segmentation import Segmentation
from sem.misc import is_string

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
        json_dict[u"name"] = document.name
        json_dict[u"content"] = document.content
        json_dict[u"metadatas"] = document.metadatas
        
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
            reference = ("" if not annotation.reference else (annotation.reference if is_string(annotation.reference) else annotation.reference.name))
            if reference:
                json_dict[u"annotations"][annotation.name][u"reference"] = reference
            json_dict[u"annotations"][annotation.name]["annotations"] = [{u"v":tag.value, u"s":tag.lb, u"l":len(tag)} for tag in annotation]
        
        return json_dict
