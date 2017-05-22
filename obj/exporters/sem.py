# -*- coding: utf-8 -*-

"""
file: text.py

Description: export annotated file to text format

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

import codecs

from obj.exporters.exporter import Exporter as DefaultExporter

class Exporter(DefaultExporter):
    __ext = "xml"
    
    def __init__(self, *args, **kwargs):
        pass
    
    def document_to_file(self, document, couples, output, encoding="utf-8", **kwargs):
        document.write(codecs.open(output, "w", encoding), add_header=True)
    
    def corpus_to_unicode(self, corpus, couples, **kwargs):
        raise NotImplementedError("corpus_to_unicode not yet implemented for SEM exporter")
    
    def document_to_data(self, document, couples, **kwargs):
        """
        This is just creating a dictionary from the document.
        Nearly copy-pasta of the Document.unicode method.
        """
        
        return self
