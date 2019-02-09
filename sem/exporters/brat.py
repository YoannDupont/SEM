# -*- coding: utf-8 -*-

"""
file: brat.py

Description: export annotated file to BRAT format

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

from .exporter import Exporter as DefaultExporter

class Exporter(DefaultExporter):
    __ext = "ann"
    
    def __init__(self, *args, **kwargs):
        pass
    
    def document_to_unicode(self, document, couples, **kwargs):
        lowers = dict([(x.lower(), y) for (x,y) in couples.items()])
        if "ner" not in lowers:
            return u""
        if not document.annotation(lowers["ner"]):
            return u""
        content = document.content
        parts = []
        for id, annotation in enumerate(document.annotation(lowers["ner"]).get_reference_annotations(), 1):
            parts.append(u"T{id}\t{annotation.value} {annotation.lb} {annotation.ub}\t{txt}".format(id=id, annotation=annotation, txt=content[annotation.lb : annotation.ub].replace(u"\r",u"").replace(u"\n",u" ")))
        return u"\n".join(parts)
    
