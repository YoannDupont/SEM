# -*- coding: utf-8 -*-

"""
file: conll.py

Description: export annotated file to CoNLL format

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

from .exporter import Exporter as DefaultExporter

class Exporter(DefaultExporter):
    __ext = "conll"
    
    def __init__(self, *args, **kwargs):
        pass
    
    def document_to_unicode(self, document, couples, **kwargs):
        logger = kwargs.get("logger", None)
        if len(document.corpus.fields) == 0:
            if logger is not None:
                logger.warn("No fields found for Corpus, cannot create string.")
            return u""
        
        if not couples or (len(couples)==0) or (len(couples)==1 and (couples.keys()[0].lower() in ["word", "token"])):
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
