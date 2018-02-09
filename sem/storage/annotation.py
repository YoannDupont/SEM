# -*- coding: utf-8 -*-

"""
file: annotation.py

Description: defines multiple objects used for annotation. An annotation
is a set of values positioned using a segmentation.

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

from sem.span import Span

class Tag(Span):
    def __init__(self, lb, ub, value, length=-1):
        super(Tag, self).__init__(lb, ub, length=length)
        self._value = value
        self.levels = []
        self.ids = {}
    
    @property
    def value(self):
        return self._value
    
    def __eq__(self, tag):
        return self.value == tag.value and self.lb == tag.lb and self.ub == tag.ub
    
    def __str__(self):
        return "%s,%s" %(self.value, super(Tag,self).__str__())
    
    def toXML(self):
        return '<tag v="%s" s="%i" l="%s" />' %(self.value, self.lb, self.ub)
    
    def kind(self):
        return u"chunking"
    
    def getLevel(self, nth):
        while nth >= len(self.levels):
            self.levels.append("")
        return self.levels[nth]
    
    def setLevel(self, nth, value):
        while nth >= len(self.levels):
            self.levels.append("")
        self.levels[nth] = value
        for i in range(nth+1, len(self.levels)):
            self.levels[i] = ""
    
    def getValue(self):
        values = []
        do_it = True
        i = -1
        while do_it:
            i += 1
            value = self.getLevel(i)
            do_it = value != ""
            if do_it:
                values.append(value)
        return u".".join(values)
    
class Annotation(object):
    def __init__(self, name, reference=None, annotations=None):
        self._name        = name
        self._reference   = reference
        if annotations is None:
            self._annotations = []
        else:
            self._annotations = annotations
    
    def __len__(self):
        return len(self._annotations)
    
    def __getitem__(self, i):
        return self._annotations[i]
    
    def __iter__(self):
        return iter(self._annotations)
    
    @property
    def name(self):
        return self._name
    
    @property
    def reference(self):
        return self._reference
    
    @property
    def annotations(self):
        return self._annotations
    
    @annotations.setter
    def annotations(self, annotations):
        self._annotations = annotations
    
    def add(self, annotation, after=None):
        i = 0
        if after is None:
            while i < len(self._annotations):
                if annotation.lb > self._annotations[i].lb:
                    None
                elif annotation.lb > self._annotations[i].ub:
                    break
                elif annotation.lb == self._annotations[i].lb:
                    if self._annotations[i].ub <= annotation.ub:
                        break
                i += 1
        else:
            while i < len(self._annotations):
                if self._annotations[i] == after:
                    i += 1
                    break
                i += 1
        if i == len(self._annotations):
            self._annotations.append(annotation)
        else:
            self._annotations.insert(i, annotation)
    
    def append(self, annotation):
        self._annotations.append(annotation)
    
    def extend(self, annotations):
        self._annotations.extend(annotations)
    
    def remove(self, annotation):
        try:
            self._annotations.remove(annotation)
        except ValueError: # annotation not in annotations
            pass
    
    def sort(self):
        self._annotations.sort(key= lambda x: (x.lb, -x.ub, x.value))
    
    def get_reference_annotations(self):
        if self.reference is None:
            return self.annotations
        else:
            reference_spans = self.reference.get_reference_spans()
            return [Tag(reference_spans[element.lb].lb, reference_spans[element.ub-1].ub, element.value) for element in self.annotations]
    

def chunk_annotation_from_sentence(sentence, column, shift=0, strict=False):
    BEGIN  = "B"  # begin flags
    IN     = "I"  # in flags
    LAST   = "LE" # end flags
    SINGLE = "US" # single flags
    OUT    = "O"
    
    annotation = Annotation("")
    start      = 0
    length     = 0
    value      = ""
    last       = len(sentence)-1
    for index, element in enumerate(sentence):
        tag  = element[column]
        flag = tag[0]
        
        if tag in OUT:
            if value != "": # we just got out of a chunk
                annotation.append(Tag(start+shift, 0, value, length=length))
            value  = ""
            length = 0
        
        elif flag in BEGIN:
            if value != "": # begin after non-empty chunk ==> add annnotation
                annotation.append(Tag(start+shift, 0, value, length=length))
            value  = tag[2:]
            start  = index
            length = 1
            if index == last: # last token ==> add annotation
                annotation.append(Tag(start+shift, 0, value, length=length))
        
        elif flag in IN:
            if value != tag[2:] and strict:
                raise ValueError('Got different values for same chunk: "%s" <> "%s"' %(tag[2:], value))
            length += 1
            if index == last: # last token ==> add annotation
                annotation.append(Tag(start+shift, 0, value, length=length))
        
        elif flag in LAST:
            annotation.append(Tag(start+shift, 0, value, length=length+1))
            value  = ""
            length = 0
        
        elif flag in SINGLE:
            if value != "": # begin after non-empty chunk ==> add annnotation
                annotation.append(Tag(value, start+shift, 0, length=length))
                value  = ""
                length = 0
            annotation.append(Tag(index+shift, 0, tag[2:], length=1))
    return annotation

def chunk_annotation_from_corpus(corpus, column, name, reference=None, strict=False):
    """
    Return an annotation from a sentence. The annotation has to have one
    of the following tagging schemes:
       - BIO (Begin In Out)
       - BILOU (Begin In Last Out Unit-length)
       - BIOES (Begin In Out End Single)
    
    we define a general approach to handle the three at the same time.
    """
    
    BEGIN  = "B"  # begin flags
    IN     = "I"  # in flags
    LAST   = "LE" # end flags
    SINGLE = "US" # single flags
    OUT    = "O"
    
    annotation = Annotation(name, reference=reference)
    shift      = 0
    for nth, sentence in enumerate(corpus): # enumerate for better exception message
        annotation.extend(chunk_annotation_from_sentence(sentence, column, shift=shift, strict=strict).annotations)
        shift += len(sentence)
    return annotation

def tag_annotation_from_sentence(sentence, column, shift=0, strict=False):
    def is_begin(tag):
        return tag[0] != "_"
    
    annotation = Annotation("")
    start      = 0
    length     = 0
    value      = ""
    last       = len(sentence)-1
    for index, element in enumerate(sentence):
        tag  = element[column]
        flag = tag[0]
        
        if is_begin(tag):
            if value != "": # begin after non-empty chunk ==> add annnotation
                annotation.append(Tag(start+shift, 0, value, length=length))
            value  = tag
            start  = index
            length = 1
            if index == last: # last token ==> add annotation
                annotation.append(Tag(start+shift, 0, value, length=length))
        
        else:
            if value != tag[1:]:
                if strict:
                    raise ValueError('Got different values for same POS: "%s" <> "%s"' %(tag[1:], value))
                else:
                    value = tag[1:] # most probable tag at the end.
            length += 1
            if index == last: # last token ==> add annotation
                annotation.append(Tag(start+shift, 0, value, length=length))
    return annotation

def tag_annotation_from_corpus(corpus, column, name, reference=None, strict=False):
    """
    Return an annotation from a sentence. The annotation has the following
    scheme:
        add "_" at the beginning of an annotation if it "continues"
        the previous tag. It is the same as BIO, "B-" is replaced by None
        and "I-" by "_".
    """
    
    annotation = Annotation(name, reference=reference)
    shift      = 0
    for nth, sentence in enumerate(corpus): # enumerate for better exception message
        annotation.extend(tag_annotation_from_sentence(sentence, column, shift=shift, strict=strict).annotations)
        shift += len(sentence)
    return annotation
