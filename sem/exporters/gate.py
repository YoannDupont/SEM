# -*- coding: utf-8 -*-

"""
file: gate.py

Description: export annotated file to GATE format

author: Yoann Dupont

MIT License

Copyright (c) 2018 Yoann Dupont

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the u"Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED u"AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
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

import codecs

from .exporter import Exporter as DefaultExporter
from sem.misc import is_string

class Exporter(DefaultExporter):
    __ext = u"gate.xml"
    
    def __init__(self, *args, **kwargs):
        pass
    
    def document_to_unicode(self, document, couples, **kwargs):
        return u'<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n' \
               + ET.tostring(self.document_to_data(document, couples), encoding=encoding)
    
    def corpus_to_unicode(self, corpus, couples, **kwargs):
        raise NotImplementedError(u"corpus_to_unicode not implemented for TEI exporter.")
    
    def document_to_file(self, document, couples, output, encoding="utf-8", **kwargs):
        gateDocument = self.document_to_data(document, couples=couples)
        content = ET.tostring(gateDocument, encoding="utf-8").decode(u"utf-8")
        if is_string(output):
            with codecs.open(output, u"w", encoding) as O:
                O.write(u'<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n')
                O.write(content)
                #O.write(self.document_to_unicode(document, couples, encoding=encoding, **kwargs))
        else:
            output.write(u'<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n')
            output.write(content)
    
    def document_to_data(self, document, couples, **kwargs):
        gateDocument = ET.Element(u"GateDocument")
        gateDocument.set(u"version", u"3")
        gateDocumentFeatures = ET.SubElement(gateDocument, u"GateDocumentFeatures")
        # feature 1 : gate.SourceURL
        feature1 = ET.SubElement(gateDocumentFeatures, u"Feature")
        name1 = ET.SubElement(feature1, u"Name")
        name1.set(u"className", u"java.lang.String")
        name1.text = u"gate.SourceURL"
        value1  = ET.SubElement(feature1, u"Value")
        value1.set(u"className", u"java.lang.String")
        value1.text = u"created from String"
        # feature 2 : MimeType
        feature2 = ET.SubElement(gateDocumentFeatures, u"Feature")
        name2 = ET.SubElement(feature2, u"Name")
        name2.set(u"className", u"java.lang.String")
        name2.text = u"MimeType"
        value2 = ET.SubElement(feature2, u"Value")
        value2.set(u"className", u"java.lang.String")
        value2.text = u"text/plain"
        # feature 3 : docNewLineType
        feature3 = ET.SubElement(gateDocumentFeatures, u"Feature")
        name3 = ET.SubElement(feature3, u"Name")
        name3.set(u"className", u"java.lang.String")
        name3.text = u"docNewLineType"
        value3 = ET.SubElement(feature3, u"Value")
        value3.set(u"className", u"java.lang.String")
        value3.text = u""
        
        # The text with anchors
        textWithNodes = ET.SubElement(gateDocument, u"TextWithNodes")
        content = document.content
        if u"ner" in couples:
            annotations = document.annotation(couples["ner"]).get_reference_annotations()
            boundaries = set()
            for annotation in annotations:
                boundaries.add(annotation.lb)
                boundaries.add(annotation.ub)
            boundaries = sorted(boundaries)
        else:
            annotations = []
            boundaries = []
        
        if boundaries != []:
            textWithNodes.text = content[ : boundaries[0]]
            for nth, boundary in enumerate(boundaries[:-1]):
                node = ET.SubElement(textWithNodes, u"Node")
                node.set(u"id", str(boundary))
                node.tail = content[boundary : boundaries[nth+1]]
                previous = boundary
            node = ET.SubElement(textWithNodes, u"Node")
            node.set(u"id", str(boundaries[-1]))
            node.tail = content[boundaries[-1] : len(content)]
        else:
            textWithNodes.text = content
        
        if annotations != []:
            id = 1
            typeAnnotationSet = ET.SubElement(gateDocument, u"AnnotationSet")
            typeAnnotationSet.set(u"Name", u"NER")
            for annot in annotations:
                annotation = ET.SubElement(typeAnnotationSet, u"Annotation")
                annotation.set(u"Id", str(id))
                annotation.set(u"Type", annot.value)
                annotation.set(u"StartNode", str(annot.lb))
                annotation.set(u"EndNode", str(annot.ub))
                id += 1
        
        return gateDocument
