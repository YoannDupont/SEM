# -*- coding: utf-8 -*-

"""
file: lexicon.py

Description: a tagger that uses lexica to annotate text

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
import os.path
import codecs

from . import Annotator as RootAnnotator

from sem.logger import default_handler

from sem.features import MultiwordDictionaryFeature, NUL

from sem.storage.annotation import chunk_annotation_from_sentence

from sem.storage import Trie

def compile_chunks(sentence, column=-1):
    return [[a.value, a.lb, a.ub] for a in chunk_annotation_from_sentence(sentence, column).annotations]

class LexicaFeature(MultiwordDictionaryFeature):
    def __init__(self, path, entry, field, order=".order", input_encoding="utf-8", *args, **kwargs):
        super(LexicaFeature, self).__init__(entry=entry, *args, **kwargs)
        
        self._is_sequence = True
        self._path        = path
        self.order        = []
        self._field       = field
        self._value       = Trie()
        order             = order or ".order"
        names             = os.listdir(self._path)
        
        if order in names:
            for line in open(os.path.join(self._path, order), "rU"):
                line = line.strip()
                if "#" in line:
                    line = line[ : line.index("#")].strip()
                if line:
                    self.order.append(line)
        else:
            self.order = [name for name in names if not name.startswith(".")]
        
        self.order = self.order[::-1]
        
        for name in self.order:
            entries = codecs.open(os.path.join(self._path, name), "rU", input_encoding).read().strip().replace(u"\r",u"").split(u"\n")
            for entry in entries:
                try:
                    entry = entry[ : entry.index(u"#")]
                except:
                    pass
                entry = entry.strip()
                if entry != u"":
                    self._value.add_with_value(entry.split(), name)
    
    def __call__(self, list2dict, *args, **kwargs):
        l           = [u"O" for _ in range(len(list2dict))]
        tmp         = self._value._data
        length      = len(list2dict)
        fst         = 0
        lst         = -1 # last match found
        cur         = 0
        entry       = self._entry
        ckey        = None  # Current KEY
        entities    = []
        value       = None
        while fst < length - 1:
            cont = True
            while cont and (cur < length):
                ckey  = list2dict[cur][entry]
                if l[cur] == "O":
                    if NUL in tmp:
                        lst = cur
                        value = tmp[NUL]
                    tmp   = tmp.get(ckey, {})
                    cont  = len(tmp) != 0
                    cur  += int(cont)
                else:
                    cont = False
            
            if NUL in tmp:
                lst = cur
                value = tmp[NUL]
            
            if lst != -1:
                entities.append([value, fst, lst])
                fst = lst
                cur = fst
                value = None
            else:
                fst += 1
                cur  = fst
            
            tmp = self._value._data
            lst = -1
        
        if NUL in self._value._data.get(list2dict[-1][entry], []):
            entities.append([self._value._data[list2dict[-1][entry]][NUL], len(list2dict)-1, len(list2dict)])
        
        if self._field in list2dict[0]:
            gold = compile_chunks(list2dict, self._field)
            for i in reversed(range(len(entities))):
                e = entities[i]
                for r in gold:
                    if (r[1] == e[1] and r[2] == e[2]) or (r[1] == e[1] and r[2] >= e[2]) or (r[1] <= e[1] and r[2] == e[2]):
                        del entities[i]
                        break
            
            for i in reversed(range(len(gold))):
                r = gold[i]
                for e in entities:
                    if (r[1] >= e[1] and r[2] <= e[2]):
                        del gold[i]
                        break
        else:
            gold = []
        
        for r in gold + entities:
            appendice = u"-" + r[0]
            l[r[1]] = u"B" + appendice
            for i in range(r[1]+1,r[2]):
                l[i] = u"I" + appendice
        
        return l

class Annotator(RootAnnotator):
    def __init__(self, field, location, token_field="word", input_encoding="utf-8", *args, **kwargs):
        super(Annotator, self).__init__(field, location, input_encoding=input_encoding, *args, **kwargs)
        
        self._token_field = token_field
        
        self._feature = LexicaFeature(self._location, self._token_field, self._field, input_encoding=input_encoding)

    def process_document(self, document, annotation_fields=None, *args, **kwargs):
        if annotation_fields is None:
            fields = document.corpus.fields
        else:
            fields = annotation_fields
        
        tags = []
        document.corpus.fields.append(self._field)
        for sequence in document.corpus:
            tags.append(self._feature(sequence)[:])
        
        document.add_annotation_from_tags(tags, self._field, self._field)
