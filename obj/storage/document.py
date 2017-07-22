# -*- coding: utf-8 -*-

"""
file: document.py

Description: defines the "all purpose" document object. A document is a
holder that will contain various informations, such as a content, a set
of segmentations or annotations.

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

from holder import Holder

from os.path import basename
import cgi

try:
    from xml.etree import cElementTree as ET
except ImportError:
    from xml.etree import ElementTree as ET

try:
    from HTMLParser import HTMLParser
except ImportError:
    from html.parser import HTMLParser

from obj.storage.segmentation import Segmentation
from obj.storage.corpus       import Corpus
from obj.storage.annotation   import Tag, Annotation, chunk_annotation_from_corpus
from obj.span                 import Span
from obj.misc                 import correct_pos_tags

class Document(Holder):
    def __init__(self, name, content=None, **kwargs):
        super(Document, self).__init__(**kwargs)
        self._name          = name
        self._content       = content
        self._segmentations = {}
        self._annotations   = {}
        self._corpus        = Corpus()
    
    @property
    def name(self):
        return self._name
    
    @property
    def content(self):
        return self._content
    
    @property
    def corpus(self):
        return self._corpus
    
    @content.setter
    def content(self, content):
        self._content = content
    
    @property
    def segmentations(self):
        return self._segmentations
    
    @property
    def annotations(self):
        return self._annotations
    
    @classmethod
    def from_file(cls, filename, encoding="utf-8"):
        return Document(basename(filename), content=codecs.open(filename, "rU", encoding).read())
    
    @classmethod
    def from_conll(cls, filename, fields, word_field, encoding="utf-8"):
        document         = Document(basename(filename))
        document._corpus = Corpus.from_conll(filename, fields, encoding=encoding)
        character_index  = 0
        sentence_index   = 0
        contents         = []
        word_spans       = []
        sentence_spans   = []
        for sentence in document._corpus.sentences:
            contents.append([])
            for token in sentence:
                word = token[word_field]
                contents[-1].append(word)
                word_spans.append(Span(character_index, character_index+len(word)))
                character_index += len(word) + 1
            sentence_spans.append(Span(sentence_index, sentence_index+len(sentence)))
            sentence_index += len(sentence)
        document._content = u"\n".join([u" ".join(content) for content in contents])
        document.add_segmentation(Segmentation("tokens", spans=word_spans))
        document.add_segmentation(Segmentation("sentences", reference=document.segmentation("tokens"), spans=sentence_spans))
        return document
    
    @classmethod
    def from_xml(cls, xml):
        if type(xml) in (str, unicode):
            data = ET.parse(xml)
        elif isinstance(xml, ET.Tree):
            data = xml
        else:
            raise TypeError("Invalid type for loading XML-SEM document: %s" %(type(xml)))
        
        htmlparser = HTMLParser()
        root = data.getroot()
        document = Document(root.attrib.get("name", u"_DOCUMENT_"))
        for element in list(root):
            if element.tag == "content":
                document.content = htmlparser.unescape(element.text)
            elif element.tag == "segmentations":
                for segmentation in list(element):
                    spans = [Span(lb=int(span.attrib.get("start", span.attrib["s"])), ub=0, length=int(span.attrib.get("length", span.attrib["l"]))) for span in list(segmentation)]
                    reference = segmentation.get(u"reference", None)
                    if reference:
                        reference = document.segmentation(reference)
                    document.add_segmentation(Segmentation(segmentation.attrib[u"name"], spans=spans, reference=reference))
            elif element.tag == "annotations":
                for annotation in list(element):
                    tags = [Tag(lb=int(tag.attrib.get("start", tag.attrib["s"])), ub=0, length=int(tag.attrib.get("length", tag.attrib["l"])), value=tag.attrib.get(u"value",tag.attrib[u"v"])) for tag in list(annotation)]
                    reference = annotation.get(u"reference", None)
                    if reference:
                        reference = document.segmentation(reference)
                    annotation = Annotation(annotation.attrib[u"name"], reference=reference)
                    annotation.annotations = tags
                    document.add_annotation(annotation)
        
        return document
    
    def get_tokens(self):
        tokens  = []
        content = self.content
        for span in self.segmentation("tokens"):
            tokens.append(content[span.lb : span.ub])
        return tokens
    
    def set_content(self, content):
        self._content = content
    
    def add_segmentation(self, segmentation):
        self._segmentations[segmentation.name]           = segmentation
        self._segmentations[segmentation.name]._document = self
    
    def segmentation(self, name):
        return self._segmentations.get(name, None)
    
    def add_annotation(self, annotation):
        self._annotations[annotation.name]           = annotation
        self._annotations[annotation.name]._document = self
    
    def annotation(self, name):
        return self._annotations[name]
    
    def write(self, f, depth=0, indent=4, add_header=False):
        if add_header:
            f.write(u'<?xml version="1.0" encoding="%s" ?>\n' %(f.encoding or "ASCII"))
        f.write(u'%s<document name="%s">\n' %(depth*indent*" ", self.name))
        depth += 1
        f.write(u'%s<content>%s</content>\n' %(depth*indent*" ", cgi.escape(self.content)))
        
        if len(self.segmentations) > 0:
            f.write(u'%s<segmentations>\n' %(depth*indent*" "))
            refs = [seg.reference for seg in self.segmentations.values() if seg.reference]
            for seg in sorted(self.segmentations.values(), key=lambda x: (x.reference and x.reference.reference in refs, x.name)): # TODO: create a sort_segmentations method to order them in terms of reference.
                depth += 1
                ref     = (seg.reference.name if isinstance(seg.reference, Segmentation) else seg.reference)
                ref_str = ("" if ref is None else ' reference="%s"'%ref)
                f.write(u'%s<segmentation name="%s"%s>' %(depth*indent*" ", seg.name, ref_str))
                depth += 1
                for i, element in enumerate(seg):
                    lf = i == 0 or (i % 5 == 0)
                    if lf:
                        f.write(u'\n%s' %(depth*indent*" "))
                    f.write(u'%s<s s="%i" l="%i" />' %(("" if lf else " "), element.lb, len(element)))
                f.write(u"\n")
                depth -= 1
                f.write(u'%s</segmentation>\n' %(depth*indent*" "))
                depth -= 1
            f.write(u'%s</segmentations>\n' %(depth*indent*" "))
        
        if len(self.annotations) > 0:
            f.write(u'%s<annotations>\n' %(depth*indent*" "))
            for annotation in self.annotations.values():
                depth += 1
                reference = ("" if not annotation.reference else u' reference="%s"' %(annotation.reference if type(annotation.reference) in (str, unicode) else annotation.reference.name))
                f.write(u'%s<annotation name="%s"%s>\n' %(depth*indent*" ", annotation.name, reference))
                depth += 1
                for tag in annotation:
                    f.write(u'%s<tag v="%s" s="%i" l="%i"/>\n' %(depth*indent*" ", tag.value, tag.lb, len(tag)))
                depth -= 1
                f.write(u'%s</annotation>\n' %(depth*indent*" "))
                depth -= 1
            f.write(u'%s</annotations>\n' %(depth*indent*" "))
            depth -= 1
        
        f.write(u'%s</document>\n' %(depth*indent*" "))
    
    def add_annotation_from_tags(self, tags, field, annotation_name):
        BIO = all([tag[0] in u"BIO" for tag in tags[0]])
        if self._annotations.get(annotation_name, None):
            del self._annotations[annotation_name]._annotations[:]
        if BIO:
            self.add_chunking(tags, field, annotation_name)
        else:
            self.add_tagging(correct_pos_tags(tags), field, annotation_name)
    
    def add_tagging(self, sentence_tags, field, annotation_name):
        nth_token  = 0
        annotation = []
        
        for nth_sentence, tags in enumerate(sentence_tags):
            if tags[0][0] == u"_":
                tags[0] = tags[0].lstrip(u"_")
            
            index = len(annotation)
            i = len(tags)-1
            n = 0
            current = None # current tag value (for multiword tags)
            while i >= 0:
                change = not(current is None or tags[i].lstrip(u"_") == current)
                
                if tags[i][0] != u"_":
                    if change:
                        tags[i] = current
                    
                    annotation.insert(index, Tag(nth_token+i, 0, tags[i], length=n+1))
                    current = None
                    n       = 0
                else:
                    if current is None:
                        current = tags[i].lstrip(u"_")
                        n = 0
                    if change:
                        tags[i] = u"_" + current
                    n += 1
                
                """if i == len(tags)-1:
                    annotation.append(SpannedTag(tags[i].lstrip("_"), Span(nth_token, nth_token+n+1)))
                    nth_token = nth_token+n+1
                    n = 0
                else:
                    if tags[i][0] == u"_":
                        if tags[i+1] == tags[i]:
                            n += 1
                        else:
                            annotation.append(SpannedTag(tags[i].lstrip("_"), Span(nth_token, nth_token+n+1)))
                            nth_token = nth_token+n+1
                            n = 0
                    else:
                        if tags[i+1][0] == u"_":
                            n += 1
                        else:
                            annotation.append(SpannedTag(tags[i].lstrip("_"), Span(nth_token, nth_token+1)))
                            nth_token = nth_token+1
                            n = 0"""
                self.corpus.sentences[nth_sentence][i][field] = tags[i]
                i -= 1
            nth_token += len(tags)
        self._annotations[annotation_name] = Annotation(annotation_name, reference=self.segmentation("tokens"))
        self._annotations[annotation_name].annotations = annotation[:]
    
    def add_chunking(self, sentence_tags, field, annotation_name):
        nth_token  = 0
        annotation = []
        
        for nth_sentence, tags in enumerate(sentence_tags):
            for i in range(len(tags)):
                self.corpus.sentences[nth_sentence][i][field] = tags[i]
        self._annotations[annotation_name] = chunk_annotation_from_corpus(self.corpus, field, annotation_name, reference=self.segmentation("tokens"))
        
