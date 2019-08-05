# -*- coding: utf-8 -*-

"""
file: gate.py

Description: export annotated file to GATE format

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

from sem.exporters.exporter import Exporter as DefaultExporter


class Exporter(DefaultExporter):
    __ext = "gate.xml"

    def __init__(self, *args, **kwargs):
        pass

    def document_to_unicode(self, document, couples, **kwargs):
        return '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n' \
               + ET.tostring(
                   self.document_to_data(document, couples),
                   encoding="utf-8"
                ).decode("utf-8")

    def document_to_data(self, document, couples, **kwargs):
        gateDocument = ET.Element("GateDocument")
        gateDocument.set("version", "3")
        gateDocumentFeatures = ET.SubElement(gateDocument, "GateDocumentFeatures")
        # feature 1 : gate.SourceURL
        feature1 = ET.SubElement(gateDocumentFeatures, "Feature")
        name1 = ET.SubElement(feature1, "Name")
        name1.set("className", "java.lang.String")
        name1.text = "gate.SourceURL"
        value1 = ET.SubElement(feature1, "Value")
        value1.set("className", "java.lang.String")
        value1.text = "created from String"
        # feature 2 : MimeType
        feature2 = ET.SubElement(gateDocumentFeatures, "Feature")
        name2 = ET.SubElement(feature2, "Name")
        name2.set("className", "java.lang.String")
        name2.text = "MimeType"
        value2 = ET.SubElement(feature2, "Value")
        value2.set("className", "java.lang.String")
        value2.text = "text/plain"
        # feature 3 : docNewLineType
        feature3 = ET.SubElement(gateDocumentFeatures, "Feature")
        name3 = ET.SubElement(feature3, "Name")
        name3.set("className", "java.lang.String")
        name3.text = "docNewLineType"
        value3 = ET.SubElement(feature3, "Value")
        value3.set("className", "java.lang.String")
        value3.text = ""

        # The text with anchors
        textWithNodes = ET.SubElement(gateDocument, "TextWithNodes")
        content = document.content
        if "ner" in couples:
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
            textWithNodes.text = content[: boundaries[0]]
            for nth, boundary in enumerate(boundaries[:-1]):
                node = ET.SubElement(textWithNodes, "Node")
                node.set("id", str(boundary))
                node.tail = content[boundary: boundaries[nth+1]]
            node = ET.SubElement(textWithNodes, "Node")
            node.set("id", str(boundaries[-1]))
            node.tail = content[boundaries[-1]: len(content)]
        else:
            textWithNodes.text = content

        if annotations != []:
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
