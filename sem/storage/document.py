# -*- coding: utf-8 -*-

"""
file: document.py

Description: defines the "all purpose" document object. A document is a
holder that will contain various informations, such as a content, a set
of segmentations or annotations.

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

from .holder import Holder

from os.path import basename
import cgi
import codecs
import logging

try:
    from xml.etree import cElementTree as ET
except ImportError:
    from xml.etree import ElementTree as ET

try:
    from HTMLParser import HTMLParser
except ImportError:
    from html.parser import HTMLParser

import sem
from sem.storage.segmentation import Segmentation
from sem.storage.corpus       import Corpus
from sem.storage.annotation   import Tag, Annotation, tag_annotation_from_corpus, chunk_annotation_from_corpus, get_top_level
from sem.span                 import Span
from sem.misc                 import correct_pos_tags
from sem.logger               import default_handler

document_logger = logging.getLogger("sem.storage.document")
document_logger.addHandler(default_handler)
document_logger.setLevel("WARNING")

class Document(Holder):
    def __init__(self, name, content=None, encoding=None, lang=None, mime_type=None, **kwargs):
        super(Document, self).__init__(**kwargs)
        self._name          = name
        self._content       = content
        self._segmentations = {}
        self._annotations   = {}
        self._corpus        = Corpus()
        self._metadatas     = {}
        if encoding is not None:
            self._metadatas["encoding"] = encoding
        if lang is not None:
            self._metadatas["lang"] = lang
        if mime_type is not None:
            self._metadatas["MIME"] = mime_type
    
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
    
    @property
    def metadatas(self):
        return self._metadatas
    
    @classmethod
    def from_file(cls, filename, encoding="utf-8"):
        return Document(basename(filename), content=codecs.open(filename, "rU", encoding).read().replace("\r",""), encoding=encoding)
    
    @classmethod
    def from_conll(cls, filename, fields, word_field, taggings=None, chunkings=None, encoding="utf-8", **kwargs):
        return Document.from_corpus(basename(filename), Corpus.from_conll(filename, fields, encoding=encoding), word_field, taggings=taggings, chunkings=chunkings, encoding=encoding, **kwargs)
    
    @classmethod
    def from_corpus(cls, name, corpus, word_field, taggings=None, chunkings=None, encoding="utf-8", **kwargs):
        document         = Document(name, encoding=encoding)
        document._corpus = corpus
        character_index  = 0
        sentence_index   = 0
        contents         = []
        word_spans       = []
        sentence_spans   = []
        for sentence in document._corpus.sentences:
            contents.append([])
            for token in sentence:
                word = token[word_field]
                contents[-1].append(word[:])
                word_spans.append(Span(character_index, character_index+len(word)))
                character_index += len(word) + 1
            sentence_spans.append(Span(sentence_index, sentence_index+len(sentence)))
            sentence_index += len(sentence)
        document._content = u"\n".join([u" ".join(content) for content in contents])
        document.add_segmentation(Segmentation("tokens", spans=word_spans))
        document.add_segmentation(Segmentation("sentences", reference=document.segmentation("tokens"), spans=sentence_spans[:]))
        for tagging in (taggings or []):
            document.add_annotation(tag_annotation_from_corpus(document._corpus, tagging, tagging, reference=document.segmentation("tokens"), strict=True))
        for chunking in (chunkings or []):
            document.add_annotation(chunk_annotation_from_corpus(document._corpus, chunking, chunking, reference=document.segmentation("tokens"), strict=True))
        return document
    
    @classmethod
    def from_xml(cls, xml, chunks_to_load=None, load_subtypes=True, type_separator=u"."):
        if type(xml) in (str, unicode):
            data = ET.parse(xml)
        elif isinstance(xml, ET.ElementTree):
            data = xml
        elif isinstance(xml, type(ET.Element("a"))): # did not ind a better way to do this
            data = xml
        else:
            raise TypeError("Invalid type for loading XML-SEM document: %s" %(type(xml)))
        
        if isinstance(data, ET.ElementTree):
            root = data.getroot()
        elif isinstance(data, type(ET.Element("a"))):
            root = data
        
        if root.tag == "sem":
            root = list(root)[0]
        elif root.tag != "document":
            raise TypeError("Invalid XML document type for XML-SEM document: %s" %(root.tag))
        
        htmlparser = HTMLParser()
        document = Document(root.attrib.get("name", u"_DOCUMENT_"))
        for element in list(root):
            if element.tag == "metadata":
                document._metadatas = element.attrib
            elif element.tag == "content":
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
                    tags = []
                    for tag in list(annotation):
                        value = tag.attrib.get(u"value",tag.attrib[u"v"])
                        if not load_subtypes:
                            value = value.strip(type_separator).split(type_separator)[0]
                        tags.append(Tag(lb=int(tag.attrib.get("start", tag.attrib["s"])), ub=0, length=int(tag.attrib.get("length", tag.attrib["l"])), value=value))
                    reference = annotation.get(u"reference", None)
                    if reference:
                        reference = document.segmentation(reference)
                    annotation = Annotation(annotation.attrib[u"name"], reference=reference)
                    annotation.annotations = tags
                    document.add_annotation(annotation)
        
        if document.segmentation("tokens") and document.segmentation("sentences"):
            document.corpus.from_segmentation(document.content, document.segmentation("tokens"), document.segmentation("sentences"))
        
            if chunks_to_load is not None:
                for chunk_to_load in chunks_to_load:
                    cur_annot = document.annotation(chunk_to_load)
                    if cur_annot and cur_annot.reference is None:
                        document.set_reference(cur_annot.name, "tokens")
                    i = 0
                    sent_iter = iter(document.corpus)
                    shift = 0
                    present = set([(a.lb,a.ub) for a in cur_annot])
                    for sentence in document.segmentation("sentences"):
                        sent = next(sent_iter)
                        annots = []
                        while i<len(cur_annot) and cur_annot[i].ub <= sentence.ub:
                            annots.append(cur_annot[i])
                            if tuple([cur_annot[i].lb, cur_annot[i].ub]) not in present:
                                raise Exception
                            i += 1
                        l = [u"O" for _ in range(len(sentence))]
                        for annot in annots:
                            l[annot.lb-shift] = u"B-%s" %annot.value
                            for j in range(annot.lb+1-shift, annot.ub-shift):
                                l[j] = u"I-%s" %annot.value
                        for j in range(len(l)):
                            sent[j]["NER"] = l[j]
                        shift += len(sentence)
                    document.corpus.fields.append(chunk_to_load)
        
        return document
    
    def escaped_name(self):
        name = basename(self._name)
        if sem.ON_WINDOWS:
            return name.replace(u":", u"").replace(u"\\", u"").replace(u"?", u"").replace(u'"', u"").replace(u"<", u"").replace(u">", u"").replace(u"|", u"")
        else:
            return name
    
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
        return self._annotations.get(name, None)
    
    def add_metadata(self, key, value):
        self._metadatas[key] = value
    
    def metadata(self, name):
        return self._metadatas.get(name, None)
    
    def mime_type(self):
        return self.metadata("MIME")
    
    def write(self, f, depth=0, indent=4, add_header=False):
        if add_header:
            f.write(u'<?xml version="1.0" encoding="%s" ?>\n' %(f.encoding or u"ASCII"))
        f.write(u'%s<document name="%s">\n' %(depth*indent*u" ", self.name))
        depth += 1
        f.write(u'%s<metadata' %(depth*indent*" "))
        for metakey, metavalue in sorted(self._metadatas.items()):
            f.write(u' %s="%s"' %(metakey, metavalue))
        f.write(u' />\n')
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
                    f.write(u'%s<tag v="%s" s="%i" l="%i"/>\n' %(depth*indent*" ", tag.getValue(), tag.lb, len(tag)))
                depth -= 1
                f.write(u'%s</annotation>\n' %(depth*indent*" "))
                depth -= 1
            f.write(u'%s</annotations>\n' %(depth*indent*" "))
        
        depth -= 1
        f.write(u'%s</document>\n' %(depth*indent*" "))
    
    def set_reference(self, annotation_name, reference_name, add_to_corpus=False, filter=get_top_level):
        annot = self.annotation(annotation_name)
        
        if annot is not None and (annot.reference is None or annot.reference.name != reference_name):
            spans = self.segmentation(reference_name).get_reference_spans()
            begin = 0
            i = 0
            for j, annotation in enumerate(annot):
                start = annotation.lb
                end   = annotation.ub
                while not(spans[i].lb <= start and start < spans[i].ub):
                    i += 1
                begin = i
                while spans[i].ub < end:
                    i += 1
                annotation.lb = begin
                annotation.ub = i + 1
                i = max(begin-1, 0)
                begin = 0
            annot._reference = self.segmentation(reference_name)
        
        if add_to_corpus:
            self.add_to_corpus(annotation_name, filter=filter)
    
    def add_to_corpus(self, annotation_name, filter=get_top_level):
        annotations = self.annotation(annotation_name).get_reference_annotations()
        
        spans = self.segmentation("tokens").get_reference_spans()
        begin = 0
        i = 0
        to_remove = [] # annotations that cannot be aligned with tokens will be removed
        for j, annotation in enumerate(annotations):
            start = annotation.lb
            end   = annotation.ub
            while (i > 0) and start < spans[i].lb:
                i -= 1
            while (i < len(spans)) and not(spans[i].lb <= start < spans[i].ub):
                i += 1
            if i < len(spans):
                begin = i
                while spans[i].ub < end:
                    i += 1
                annotation.lb = begin
                annotation.ub = i + 1
            else:
                document_logger.warn("cannot add annotation %s" %(annotation))
                to_remove.append(j)
            i = max(begin, 0)
            begin = 0
        for i in to_remove[::-1]:
            del annotations[i]
        
        if filter:
            annotations = filter(annotations)
        sentence_spans = iter(self.segmentation("sentences"))
        annot_index = 0
        if len(annotations) == 0:
            annots = []
            cur_annot = None
        else:
            annots = annotations
            cur_annot = annots[annot_index]
        shift = 0
        for sentence in self.corpus.sentences:
            span = next(sentence_spans)
            for token in sentence:
                token[annotation_name] = u"O"
            while cur_annot is not None and cur_annot.lb >= span.lb and cur_annot.ub <= span.ub:
                sentence[cur_annot.lb -shift][annotation_name] = u"B-%s" %cur_annot.value
                for k in range(cur_annot.lb+1, cur_annot.ub):
                    sentence[k - shift][annotation_name] = u"I-%s" %cur_annot.value
                try:
                    annot_index += 1
                    cur_annot = annots[annot_index]
                except IndexError:
                    cur_annot = None
            if cur_annot is not None and ((span.lb <= cur_annot.lb < span.ub) and cur_annot.ub > span.ub): # annotation spans over at least two sentences
                document_logger.warn("Annotation %s spans over multiple sentences, ignoring" %(cur_annot))
                try:
                    annot_index += 1
                    cur_annot = annots[annot_index]
                except IndexError:
                    cur_annot = None
            shift += len(sentence)
        self.corpus.fields.append(annotation_name)
    
    def add_annotation_from_tags(self, tags, field, annotation_name):
        BIO = all([tag[0] in u"BIO" for tag in tags[0]])
        if self._annotations.get(annotation_name, None):
            del self._annotations[annotation_name]._annotations[:]
        if BIO:
            self.add_chunking(tags, field, annotation_name)
        else:
            self.add_tagging(correct_pos_tags(tags), field, annotation_name)
        if not self.corpus.has_key(field):
            self.corpus.fields.append(field)
    
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
        


class SEMCorpus(Holder):
    def __init__(self, documents=None, **kwargs):
        super(SEMCorpus, self).__init__(**kwargs)
        
        if documents is None:
            self._documents = []
        else:
            self._documents = documents
    
    def __len__(self):
        return len(self._documents)
    
    def __iter__(self):
        return iter(self._documents)
    
    @property
    def documents(self):
        return self._documents
    
    @classmethod
    def from_xml(cls, xml, chunks_to_load=None, load_subtypes=True, type_separator=u"."):
        if type(xml) in (str, unicode):
            data = ET.parse(xml)
        elif isinstance(xml, ET.ElementTree):
            data = xml
        elif isinstance(xml, type(ET.Element("a"))): # did not ind a better way to do this
            data = xml
        else:
            raise TypeError("Invalid type for loading XML-SEM document: %s" %(type(xml)))
        
        root = data.getroot()
        if root.tag != "sem":
            raise ValueError("Not sem xml file type: '%s'" %root.tag)
        doc_list = []
        for document in list(root):
            doc_list.append(Document.from_xml(document))
        return SEMCorpus(doc_list)
    
    def add_document(self, document):
        ok = not any([d.name == document.name for d in self.documents])
        if ok:
            self._documents.append(document)
    
    def write(self, f, indent=4):
        f.write(u'<?xml version="1.0" encoding="%s" ?>\n' %(f.encoding or "ASCII"))
        f.write(u"<sem>\n")
        for document in self._documents:
            document.write(f, depth=1, indent=indent, add_header=False)
        f.write(u"</sem>")
