# -*- coding: utf-8 -*-

"""
file: text.py

Description: export annotated file to text format

author: Nour El Houda Belhaouane and Yoann Dupont
copyright (c) 2017 Nour El Houda Belhaouane and Yoann Dupont -
all rights reserved

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

try:
    from xml.etree import cElementTree as ET
except ImportError:
    from xml.etree import ElementTree as ET

from sem.exporters.exporter import Exporter as DefaultExporter

class Exporter(DefaultExporter):
    __ext = "gate.xml"
    
    def __init__(self, *args, **kwargs):
        pass
    
    def document_to_unicode(self, document, couples, **kwargs):
        return u'<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n' \
               + ET.tostring(self.document_to_data(document, couples), encoding=encoding)
    
    def corpus_to_unicode(self, corpus, couples, **kwargs):
        raise NotImplementedError("corpus_to_unicode not implemented for TEI exporter.")
    
    def document_to_file(self, document, couples, output, **kwargs):
        gateDocument = self.document_to_data(document, couples=couples)
        if type(output) in (str, unicode):
            with open(output, "w") as O:
                O.write(u'<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n')
                O.write(ET.tostring(gateDocument, encoding="utf-8"))
                #O.write(self.document_to_unicode(document, couples, encoding=encoding, **kwargs))
        else:
            output.write(u'<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n')
            output.write(ET.tostring(gateDocument, encoding="utf-8"))
    
    def document_to_data(self, document, couples, **kwargs):
        gateDocument = ET.Element("GateDocument")
        gateDocument.set("version","3")
        gateDocumentFeatures = ET.SubElement(gateDocument,"GateDocumentFeatures")
        # feature 1 : gate.SourceURL
        feature1 = ET.SubElement(gateDocumentFeatures,"Feature")
        name1 = ET.SubElement(feature1, "Name")
        name1.set("className", "java.lang.String")
        name1.text = "gate.SourceURL"
        value1  = ET.SubElement(feature1, "Value")
        value1.set("className", "java.lang.String")
        value1.text = "created from String"
        # feature 2 : MimeType
        feature2 = ET.SubElement(gateDocumentFeatures,"Feature")
        name2 = ET.SubElement(feature2, "Name")
        name2.set("className", "java.lang.String")
        name2.text = "MimeType"
        value2 = ET.SubElement(feature2, "Value")
        value2.set("className", "java.lang.String")
        value2.text = "text/plain"
        # feature 3 : docNewLineType
        feature3 = ET.SubElement(gateDocumentFeatures,"Feature")
        name3 = ET.SubElement(feature3, "Name")
        name3.set("className", "java.lang.String")
        name3.text = "docNewLineType"
        value3 = ET.SubElement(feature3, "Value")
        value3.set("className", "java.lang.String")
        value3.text = ""
        
        # The text with anchors
        textWithNodes = ET.SubElement(gateDocument, "TextWithNodes")
        content = document.content
        annotations = document.annotation(couples["ner"]).get_reference_annotations()
        boundaries = set()
        for annotation in annotations:
            boundaries.add(annotation.lb)
            boundaries.add(annotation.ub)
        boundaries = sorted(boundaries)
        textWithNodes.text = content[ : boundaries[0]]
        for nth, boundary in enumerate(boundaries[:-1]):
            node = ET.SubElement(textWithNodes, "Node")
            node.set("id", str(boundary))
            node.tail = content[boundary : boundaries[nth+1]]
            previous = boundary
        node = ET.SubElement(textWithNodes, "Node")
        node.set("id", str(boundaries[-1]))
        node.tail = content[boundaries[-1] : len(content)]
        
        id = 1
        typeAnnotationSet = ET.SubElement(gateDocument, "AnnotationSet")
        typeAnnotationSet.set("Name", "NER")
        for annot in annotations:
            annotation = ET.SubElement(typeAnnotationSet, "Annotation")
            annotation.set("Id", str(id))
            annotation.set("Type", annot.value)
            annotation.set("StartNode", str(annot.lb))
            annotation.set("EndNode", str(annot.ub))
            id += 1
        
        return gateDocument
