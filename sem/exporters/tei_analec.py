# -*- coding: utf-8 -*-

"""
file: tei_analec.py

Description: export annotated file to Analec TEI format.

author: Nour El Houda Belhaouane and Yoann Dupont

MIT License

Copyright (c) 2018 Nour El Houda and Yoann Dupont

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

from .exporter import Exporter as DefaultExporter
from sem.storage.annotation import tag_annotation_from_sentence as get_pos, chunk_annotation_from_sentence as get_chunks
from sem.storage import Span
from sem.misc import is_string

def add_text(node, text):
    parts = text.split(u"\n")
    node.text = parts[0]
    for i in range(1, len(parts)):
        br = ET.SubElement(node,"lb")
        br.tail = u"\n" + parts[1]

def add_tail(node, tail):
    parts = tail.split(u"\n")
    node.tail = parts[0]
    for i in range(1, len(parts)):
        br = ET.SubElement(node,"lb")
        br.tail = u"\n" + parts[1]

class Exporter(DefaultExporter):
    __ext = "analec.tei.xml"
    
    def __init__(self, *args, **kwargs):
        pass
    
    def document_to_unicode(self, document, couples, encoding="utf-8", **kwargs):
        return u'<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n' \
               + ET.tostring(self.document_to_data(document, couples), encoding=encoding)
    
    def corpus_to_unicode(self, corpus, couples, **kwargs):
        raise NotImplementedError("corpus_to_unicode not implemented for TEI exporter.")
    
    def document_to_file(self, document, couples, output, encoding="utf-8", **kwargs):
        teiCorpus = self.document_to_data(document, couples=couples)
        content = ET.tostring(teiCorpus, encoding="utf-8").decode("utf-8")
        if is_string(output):
            with open(output, "w") as O:
                O.write(u'<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n')
                O.write(content)
        else:
            output.write(u'<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n')
            output.write(content)
    
    def document_to_data(self, document, couples, **kwargs):
        teiCorpus = ET.Element("teiCorpus")
        teiCorpus.set("xmlns","http://www.tei-c.org/ns/1.0")
        teiHeader = ET.SubElement(teiCorpus,"teiHeader")
        fileDesc = ET.SubElement(teiHeader,"fileDesc")
        titleStmt = ET.SubElement(fileDesc,"titleStmt")
        title = ET.SubElement(titleStmt,"title")
        title.text =""
        respStmt = ET.SubElement(titleStmt,"respStmt")
        resp = ET.SubElement(respStmt,"resp")
        resp.text =""
        name = ET.SubElement(respStmt,"name")
        name.text = ""
        publicationStmt = ET.SubElement(fileDesc,"publicationStmt")
        publisher = ET.SubElement(publicationStmt,"publisher")
        publisher.text =""
        sourceDesc = ET.SubElement(fileDesc,"sourceDesc")
        sourceDesc.text =""
        TEI = ET.SubElement(teiCorpus,"TEI")
        teiHeader = ET.SubElement(TEI,"teiHeader")
        teiHeader.text =""
        titleStmt = ET.SubElement(fileDesc,"titleStmt")
        title = ET.SubElement(titleStmt,"title")
        title.text =""
        respStmt = ET.SubElement(titleStmt,"respStmt")
        resp = ET.SubElement(respStmt,"resp")
        resp.text =""
        name = ET.SubElement(respStmt,"name")
        name.text =""
        publicationStmt = ET.SubElement(fileDesc,"publicationStmt")
        publisher = ET.SubElement(publicationStmt,"publisher")
        publisher.text =""
        sourceDesc = ET.SubElement(fileDesc,"sourceDesc")
        sourceDesc.text =""

        root = ET.SubElement(TEI,"text")
        body = ET.SubElement(root,"body")
        
        lower  = {}
        for field in couples:
            lower[field.lower()] = couples[field]
        annotations = set(document.annotations.keys())
        field = None
        if len(couples) == 1:
            field = lower[sorted(lower.keys())[0]]
        else:
            field = (lower.get("ner", None) if lower.get("ner", None) in annotations else None)
            if field is None:
                field = (lower.get("chunking", None) if lower.get("chunking", None) in annotations else None)
        if field is None:
            raise ValueError("Could not determine the field to use for TEI export.")
        
        content = document.content
        paragraphs = (document.segmentation(u"paragraphs").get_reference_spans() if document.segmentation(u"paragraphs") is not None else [Span(0, len(content))])
        NEs = document.annotation(field).get_reference_annotations()
        values = set([entity.value for entity in NEs])
        
        nth = dict([(value,0) for value in values])
        for paragraph in paragraphs:
            entities = [entity for entity in NEs if entity.lb >= paragraph.lb and entity.ub <= paragraph.ub]
            p = ET.SubElement(body,"p")
            start = paragraph.lb
            if len(entities) == 0:
                p.text = content[paragraph.lb : paragraph.ub]
            else:
                p.text = content[paragraph.lb : entities[0].lb]
                for i,entity in enumerate(entities):
                    nth[entity.value] += 1
                    entity_start = ET.SubElement(p, "anchor", {"xml:id":"u-{0}-{1}-start".format(entity.value, nth[entity.value]), "type":"AnalecDelimiter", "subtype":"UnitStart"})
                    entity_start.tail = content[entity.lb : entity.ub]
                    entity_end = ET.SubElement(p, "anchor", {"xml:id":"u-{0}-{1}-end".format(entity.value, nth[entity.value]), "type":"AnalecDelimiter", "subtype":"UnitEnd"})
                    if i < len(entities)-1:
                        entity_end.tail = content[entity.ub : entities[i+1].lb]
                    else:
                        entity_end.tail = content[entity.ub : paragraph.ub]
        
        back = ET.SubElement(root,"back")
        for value in sorted(values):
            spanGrp = ET.SubElement(back, "spanGrp")
            spanGrp.set("type", "AnalecUnit")
            spanGrp.set("n", value)
            i = 0
            for entity in [ent for ent in NEs if ent.value == value]:
                i += 1
                ET.SubElement(spanGrp, "span", {"xml:id":"u-{0}-{1}".format(value, i), "from":"#u-{0}-{1}-start".format(value, i), "to":"#u-{0}-{1}-end".format(value, i), "ana":"#u-{0}-{1}-fs".format(value, i)})
        
        fvLib = ET.SubElement(back,"fvLib")
        fvLib.set("n","AnalecElementProperties")
        nth = dict([(value,0) for value in values])
        for i, entity in enumerate(NEs):
            nth[entity.value] += 1
            fs = ET.SubElement(fvLib,"fs",{"xml:id": "u-{0}-{1}-fs".format(entity.value, nth[entity.value])})
        
        return teiCorpus
