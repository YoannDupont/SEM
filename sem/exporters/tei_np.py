# -*- coding: utf-8 -*-

"""
file: tei_np.py

Description: export annotated file to a TEI format. This exporter is
adapted for NP chunking

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

import logging
from sem.logger import logging_format, default_handler

from sem.span import Span

from sem.exporters.exporter import Exporter as DefaultExporter
from sem.storage.annotation import tag_annotation_from_sentence as get_pos, chunk_annotation_from_sentence as get_chunks

tei_np_logger = logging.getLogger("sem.tagger")
tei_np_logger.addHandler(default_handler)

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
    __ext = "tei.xml"
    
    def __init__(self, *args, **kwargs):
        pass
    
    def document_to_unicode(self, document, couples, encoding="utf-8", **kwargs):
        return u'<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n' \
               + ET.tostring(self.document_to_data(document, couples), encoding=encoding)
    
    def corpus_to_unicode(self, corpus, couples, **kwargs):
        raise NotImplementedError("corpus_to_unicode not implemented for TEI exporter.")
    
    def document_to_file(self, document, couples, output, encoding="utf-8", **kwargs):
        teiCorpus = self.document_to_data(document, couples=couples)
        with open(output, "w") as O:
            O.write(u'<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n')
            O.write(ET.tostring(teiCorpus, encoding="utf-8"))
            #O.write(self.document_to_unicode(document, couples, encoding=encoding, **kwargs))
    
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
        chunking_field = None
        try:
            chunking_field = lower["chunking"]
        except KeyError:
            message = 'No "chunking" field was found, please check you have chunking information in your pipeline.'
            tei_np_logger.exception(message)
            raise KeyError(message)
        
        content = document.content
        possessives = set([u"son", u"sa", u"ses"])
        pronoun2analec = {u"CL":u"PR_CL", u"CLO":u"PR_CL_O", u"CLR":u"PR_CL_R", u"CLS":u"PR_CL_S", u"PRO":u"PR_PRO", u"PROREL":u"PR_REL", u"PROWH":u"PR_WH", u"P+PRO":u"PR_PP"}
        words = document.segmentation(u"tokens").get_reference_spans()
        paragraphs = document.segmentation(u"paragraphs").get_reference_spans() or Span(0, len(content))
        np_chunks = [annotation for annotation in document.annotation(chunking_field) if annotation.value == u"NP"]
        pos_tags = document.annotation(lower["pos"])[:]
        pos = []
        for i in range(len(np_chunks)):
            chunk = np_chunks[i]
            pos.append([annot for annot in pos_tags if annot.lb >= chunk.lb and annot.ub <= chunk.ub])
        
        for i in range(len(np_chunks)):
            np_chunks[i].ub = words[np_chunks[i].ub-1].ub
            np_chunks[i].lb = words[np_chunks[i].lb].lb
        
        nth = 0
        for paragraph in paragraphs:
            nps = [chunk for chunk in np_chunks if chunk.lb >= paragraph.lb and chunk.ub <= paragraph.ub]
            p = ET.SubElement(body,"p")
            start = paragraph.lb
            if len(nps) == 0:
                p.text = content[paragraph.lb : paragraph.ub]
                #add_text(p, content[paragraph.lb : paragraph.ub])
            else:
                p.text = content[paragraph.lb : nps[0].lb]
                #add_text(p, content[paragraph.lb : nps[0].lb])
                for i,np in enumerate(nps):
                    nth += 1
                    np_start = ET.SubElement(p,"anchor",{"xml:id":"u-MENTION-%i-start" %nth, "type":"AnalecDelimiter", "subtype":"UnitStart"})
                    np_start.tail = content[np.lb : np.ub]
                    #add_tail(np_start, content[np.lb : np.ub])
                    np_end = ET.SubElement(p,"anchor",{"xml:id":"u-MENTION-%i-end" %nth, "type":"AnalecDelimiter", "subtype":"UnitEnd"})
                    if i < len(nps)-1:
                        np_end.tail = content[np.ub : nps[i+1].lb]
                        #add_tail(np_end, content[np.ub : nps[i+1].lb])
                    else:
                        np_end.tail = content[np.ub : paragraph.ub]
                        #add_tail(np_end, content[np.ub : paragraph.ub])
        
        back = ET.SubElement(root,"back")
        spanGrp = ET.SubElement(back, "spanGrp")
        spanGrp.set("type", "AnalecUnit")
        spanGrp.set("n","MENTION")
        for i, np in enumerate(np_chunks):
            ET.SubElement(spanGrp, "span", {"xml:id":"u-MENTION-%i"%(i+1), "from":"#u-MENTION-%i-start"%(i+1), "to":"#u-MENTION-%i-end"%(i+1), "ana":"#u-MENTION-%i-fs"%(i+1)})
        
        fvLib = ET.SubElement(back,"fvLib")
        fvLib.set("n","AnalecElementProperties")
        for i, np in enumerate(np_chunks):
            value = pronoun2analec.get(pos[i][0].value, u"GN")
            
            fs = ET.SubElement(fvLib,"fs",{"xml:id": "u-MENTION-%i-fs" %(i+1)})
            f = ET.SubElement(fs,"f")
            f.set("name","REF")
            ET.SubElement(f,"string")
            
            f = ET.SubElement(fs,"f")
            f.set("name","CODE_SEM")
            fstring = ET.SubElement(f,"string")
            fstring.text = value
            
            f = ET.SubElement(fs,"f")
            f.set("name","CATEGORIE")
            fstring = ET.SubElement(f,"string")
            fstring.text = value
        
        return teiCorpus
