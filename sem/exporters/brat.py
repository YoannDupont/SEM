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
    __ext = "ann"
    
    def __init__(self, *args, **kwargs):
        pass
    
    def document_to_unicode(self, document, couples, **kwargs):
        if "ner" not in couples:
            return u""
        content = document.content
        parts = []
        for id, annotation in enumerate(document.annotation(couples["ner"]).get_reference_annotations(), 1):
            parts.append(u"T%i\t%s %i %i\t%s" %(id, annotation.value, annotation.lb, annotation.ub, content[annotation.lb : annotation.ub].replace(u"\r",u"").replace(u"\n",u" ")))
        return u"\n".join(parts)
    
    def corpus_to_unicode(self, corpus, couples, **kwargs):
        raise NotImplementedError("corpus_to_unicode not implemented for TEI exporter.")
    