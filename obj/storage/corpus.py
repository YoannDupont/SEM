# -*- coding: utf-8 -*-

"""
file: corpus.py

Description: defines the Corpus object. It is an object representation
of a CoNLL-formatted corpus.

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
from obj.IO.KeyIO import KeyReader

class Corpus(object):
    def __init__(self, fields=None, sentences=None):
        if fields:
            self.fields = fields[:]
        else:
            self.fields = []
        
        if sentences:
            self.sentences = sentences[:]
        else:
            self.sentences = []
    
    def __iter__(self):
        for element in self.iterate_on_sentences():
            yield element
    
    def __unicode__(self):
        return self.unicode(self.fields)
    
    @classmethod
    def from_conll(cls, filename, fields, encoding="utf-8"):
        corpus = Corpus(fields)
        for sentence in KeyReader(filename, encoding, fields):
            corpus.append_sentence([token.copy() for token in sentence])
        return corpus
    
    def unicode(self, fields, separator=u"\t"):
        fmt       = u"\t".join([u"%%(%s)s" %field for field in fields])
        sentences = []
        for sentence in self:
            sentences.append([])
            for token in sentence:
                sentences[-1].append((fmt %token) + u"\n")
        return u"\n".join([u"".join(sentence) for sentence in sentences])
    
    def iterate_on_sentences(self):
        for element in self.sentences:
            yield element
    
    def is_empty(self):
        return 0 == len(sentences)
    
    def append_sentence(self, sentence):
        self.sentences.append(sentence)
    
    def from_sentences(self, sentences, field_name=u"word"):
        del self.fields[:]
        del self.sentences[:]
        
        self.fields = [field_name]
        for sentence in sentences:
            self.sentences.append([])
            for token in sentence:
                self.sentences[-1].append({field_name : token})
    
    def from_segmentation(self, content, tokens, sentences, field_name=u"word"):
        self.fields = [field_name]
        for sentence in sentences.spans:
            sentence_tokens = []
            self.append_sentence([{field_name:content[token.lb : token.ub]} for token in tokens.spans[sentence.lb : sentence.ub]])
