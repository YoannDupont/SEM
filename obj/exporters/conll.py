# -*- coding: utf-8 -*-

"""
file: conll.py

Description: export annotated file to CoNLL format

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

from obj.exporters.exporter import Exporter as DefaultExporter

class Exporter(DefaultExporter):
    def __init__(self, *args, **kwargs):
        pass
    
    def document_to_unicode(self, document, couples, **kwargs):
        return unicode(document.corpus)
        if not couples or (len(couples)==1 and (couples.keys()[0].lower() in ["word", "token"])):
            return unicode(document.corpus)
        else:
            lower  = {}
            fields = []
            for field in couples:
                lower[field.lower()] = couples[field]
            
            if "word" in lower:    fields.append(lower["word"])
            elif "token" in lower: fields.append(lower["token"])
            else:                  fields.append(document.corpus.fields[0])
            
            if "pos" in lower:      fields.append(lower["pos"])
            if "chunking" in lower: fields.append(lower["chunking"])
            if "ner" in lower:      fields.append(lower["ner"])
            
            return document.corpus.unicode(fields)
    
    def corpus_to_unicode(self, corpus, couples, **kwargs):
        values = couples.values()
        return u"\n\n".join([u"\n".join([u"\t".join([fields for i,fields in enumerate(token) if i in values]) for token in sentence]) for sentence in corpus])
    
    def document_to_data(self, document, couples, **kwargs):
        return document.corpus.sentences
