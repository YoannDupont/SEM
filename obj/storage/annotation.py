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

from obj.span import Span

class Tag(object):
    def __init__(self, value):
        self._value = value
    
    @property
    def value(self):
        return self._value
    
    def kind(self):
        return u"tagging"

class SpannedTag(Tag):
    def __init__(self, value, span):
        super(SpannedTag, self).__init__(value)
        self._span = span
    
    def __len__(self):
        return len(self._span)
    
    def __str__(self):
        return self.value+","+str(self.span)
    
    @property
    def span(self):
        return self._span
    
    @property
    def start(self):
        return self._span.lb
    
    @property
    def end(self):
        return self._span.ub
    
    def toXML(self):
        return '<tag v="%s" s="%i" l="%s" />' %(self.value, self.lb, self.ub)
    
    def kind(self):
        return u"chunking"
    
class Annotation(object):
    def __init__(self, name, reference=None):
        self._name        = name
        self._reference   = reference
        self._annotations = []
    
    def __len__(self):
        return len(self._annotations)
    
    def __getitem__(self, i):
        return self._annotations[i]
    
    def __iter__(self):
        for annotation in self._annotations:
            yield annotation
    
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
    
    def append(self, annotation):
        self._annotations.append(annotation)
    
    def extend(self, annotations):
        self._annotations.extend(annotations)
    
    def get_reference_annotations(self):
        if self.reference is None:
            return self.annotations
        else:
            reference_spans = self.reference.get_reference_spans()
            return [SpannedTag(element.value, Span(reference_spans[element.start].lb, reference_spans[element.end-1].ub)) for element in self.annotations]
    

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
                annotation.append(SpannedTag(value, Span(start+shift, 0, length=length)))
            value  = ""
            length = 0
        
        elif flag in BEGIN:
            if value != "": # begin after non-empty chunk ==> add annnotation
                annotation.append(SpannedTag(value, Span(start+shift, 0, length=length)))
            value  = tag[2:]
            start  = index
            length = 1
            if index == last: # last token ==> add annotation
                annotation.append(SpannedTag(value, Span(start+shift, 0, length=length)))
        
        elif flag in IN:
            if value != tag[2:] and strict:
                raise ValueError('Got different values for same chunk: "%s" <> "%s"' %(tag[2:], value))
            length += 1
            if index == last: # last token ==> add annotation
                annotation.append(SpannedTag(value, Span(start+shift, 0, length=length)))
        
        elif flag in LAST:
            annotation.append(SpannedTag(value, Span(start+shift, 0, length=length+1)))
            value  = ""
            length = 0
        
        elif flag in SINGLE:
            if value != "": # begin after non-empty chunk ==> add annnotation
                annotation.append(SpannedTag(value, Span(start+shift, 0, length=length)))
                value  = ""
                length = 0
            annotation.append(SpannedTag(tag[2:], Span(index+shift, 0, length=1)))
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
                annotation.append(SpannedTag(value, Span(start+shift, 0, length=length)))
            value  = tag
            start  = index
            length = 1
            if index == last: # last token ==> add annotation
                annotation.append(SpannedTag(value, Span(start+shift, 0, length=length)))
        
        else:
            if value != tag[1:]:
                if strict:
                    raise ValueError('Got different values for same POS: "%s" <> "%s"' %(tag[1:], value))
                else:
                    value = tag[1:] # most probable tag at the end.
            length += 1
            if index == last: # last token ==> add annotation
                annotation.append(SpannedTag(value, Span(start+shift, 0, length=length)))
    return annotation

def tag_annotation_from_corpus(corpus, column, name, reference=None, strict=False):
    """
    Return an annotation from a sentence. The annotation has the following
    scheme:
        add "_" at the beginning of an annotation if it "continues"
        the previous tag. It is the same as BIO, "B-" is replaced by None
        and "I-" by "_".
    """
    
    annotation = Annotation(name, reference=reference, strict=strict)
    shift      = 0
    for nth, sentence in enumerate(corpus): # enumerate for better exception message
        annotation.extend(tag_annotation_from_sentence(sentence, column, shift=shift).annotations)
        shift += len(sentence)
    return annotation
