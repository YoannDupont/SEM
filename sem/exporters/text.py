# -*- coding: utf-8 -*-

"""
file: text.py

Description: export annotated file to text format

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

from sem.exporters.exporter import Exporter as DefaultExporter
from sem.storage.annotation import tag_annotation_from_sentence as get_pos, chunk_annotation_from_sentence as get_chunks

class Exporter(DefaultExporter):
    __ext = "txt"
    
    def __init__(self, *args, **kwargs):
        pass
    
    def document_to_unicode(self, document, couples, **kwargs):
        return self.corpus_to_unicode(document.corpus, couples, **kwargs)
    
    def corpus_to_unicode(self, corpus, couples, **kwargs):
        lower  = {}
        for field in couples:
            lower[field.lower()] = couples[field]
        
        if "word" in lower:
            token_field = lower["word"]
        elif "token" in lower:
            token_field = lower["token"]
        elif corpus.has_key(u"word"):
            token_field = u"word"
        elif corpus.has_key(u"token"):
            token_field = u"token"
        else:
            raise RuntimeError("Cannot find token field")
        
        data = []
        for sentence in corpus:
            tokens = [token[token_field] for token in sentence]
            
            if "pos" in lower and corpus.has_key(lower["pos"]):
                pos = [u"" for _ in range(len(tokens))]
                for annotation in get_pos(sentence, lower["pos"]):
                    tokens[annotation.ub-1] += u"/" + annotation.value
                    for i in range(annotation.lb, annotation.ub-1): # regrouping tokens for tags spanning over >2 tokens
                        tokens[i+1] = tokens[i] + u"_" + tokens[i+1]
                        tokens[i]   = u""
            
            if "chunking" in lower and corpus.has_key(lower["chunking"]):
                for annotation in get_chunks(sentence, lower["chunking"]):
                    tokens[annotation.lb] = "({0} {1}".format(annotation.value, tokens[annotation.lb])
                    tokens[annotation.ub-1] = "{0} )".format(tokens[annotation.ub-1])
            
            if "ner" in lower and corpus.has_key(lower["ner"]):
                for annotation in get_chunks(sentence, lower["ner"]):
                    tokens[annotation.lb] = "({0} {1}".format(annotation.value, tokens[annotation.lb])
                    tokens[annotation.ub-1] = "{0} )".format(tokens[annotation.ub-1])
            
            tokens = [token for token in tokens if token != ""] # if regrouping tokens, some are empty and would generate superfluous spaces
            data.append(u" ".join(tokens[:]))
        return u"\n".join(data)
    
    def document_to_data(self, document, couples, **kwargs):
        return self.document_to_unicode(document, couples).split(u"\n")
