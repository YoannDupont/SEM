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

from obj.exporters.exporter import Exporter as DefaultExporter
from obj.storage.annotation import tag_annotation_from_sentence as get_pos, chunk_annotation_from_sentence as get_chunks

class Exporter(DefaultExporter):
    def __init__(self, *args, **kwargs):
        pass
    
    def document_to_unicode(self, document, couples, **kwargs):
        return self.corpus_to_unicode(document.corpus.sentences, couples, **kwargs)
    
    def corpus_to_unicode(self, corpus, couples, **kwargs):
        lower  = {}
        for field in couples:
            lower[field.lower()] = couples[field]
        
        if "word" in lower:
            token_field = lower["word"]
        elif "token" in lower:
            token_field = lower["token"]
        
        data = []
        for sentence in corpus:
            tokens = [token[token_field] for token in sentence]
            
            if "pos" in lower:
                pos = [u"" for _ in range(len(tokens))]
                for annotation in get_pos(sentence, lower["pos"]):
                    tokens[annotation.end-1] += u"/" + annotation.value
                    for i in range(annotation.start, annotation.end-1): # regrouping tokens for tags spanning over >2 tokens
                        tokens[i+1] = tokens[i] + u"_" + tokens[i+1]
                        tokens[i]   = u""
            
            if "chunking" in lower:
                for annotation in get_chunks(sentence, lower["chunking"]):
                    tokens[annotation.start] = "(%s %s" %(annotation.value, tokens[annotation.start])
                    tokens[annotation.end-1] = "%s )" %(tokens[annotation.end-1])
            
            if "ner" in lower:
                for annotation in get_chunks(sentence, lower["ner"]):
                    tokens[annotation.start] = "(%s %s" %(annotation.value, tokens[annotation.start])
                    tokens[annotation.end-1] = "%s )" %(tokens[annotation.end-1])
            
            tokens = [token for token in tokens if token != ""] # if regrouping tokens, some are empty and would generate superfluous spaces
            data.append(u" ".join(tokens[:]))
        return u"\n".join(data)
    
    def document_to_data(self, document, couples, **kwargs):
        return self.document_to_unicode(document, couples).split(u"\n")
