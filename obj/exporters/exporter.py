# -*- coding: utf-8 -*-

"""
file: exporter.py

Description: root type for exporter objects.

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

class Exporter(object):
    def __init__(self, *args, **kwargs):
        pass
    
    def corpus_to_unicode(self, corpus, couples, **kwargs):
        """
        returns a unicode representation of the corpus for the given
        export format.
        
        Parameters
        ----------
            corpus : list of list of dict (string -> string)
                the input corpus to export. It is more or less a CoNLL
                representation of the corpus.
            couples : dict (string -> string)
                the "entry name" <=> "entry index" that allows to
                retrieve information to export.
                ex: couples = {u"chunking":u"C", u"NER":u"N"}
        """
        raise RuntimeError("export_to_string not implemented for class " + self.__class__)
    
    def corpus_to_file(self, corpus, couples, output, encoding="utf-8", **kwargs):
        """
        write the document to a file in the given export format.
        
        Parameters
        ----------
            corpus : list
                the corpus to export
            couples : dict (string -> string)
                the "entry name" <=> "entry index" that allows to
                retrieve information to export.
                ex: couples = {u"chunking":u"C", u"NER":u"N"}
            output : str
                the name of the file to write into
        """
        with codecs.open(output, "w", encoding) as O:
            O.write(self.corpus_to_unicode(corpus, couples, **kwargs))
    
    def document_to_unicode(document, couples, **kwargs):
        """
        returns a unicode representation of the document for the given
        export format.
        
        Parameters
        ----------
            document : Document
                the input document to export
            couples : dict (string -> string)
                the "entry name" <=> "entry index" that allows to
                retrieve information to export.
                ex: couples = {u"chunking":u"C", u"NER":u"N"}
        """
        raise RuntimeError("export_to_string not implemented for class " + self.__class__)
    
    def document_to_file(self, document, couples, output, encoding="utf-8", **kwargs):
        """
        write the document to a file in the given export format.
        
        Parameters
        ----------
            document : Document
                the document to export
            couples : dict (string -> string)
                the "entry name" <=> "entry index" that allows to
                retrieve information to export.
                ex: couples = {u"chunking":u"C", u"NER":u"N"}
            output : str
                the name of the file to write into
        """
        with codecs.open(output, "w", encoding) as O:
            O.write(self.document_to_unicode(document, couples, **kwargs))
    
    def document_to_data(self, document, couples, **kwargs):
        """
        creates a new variable representing the document in the given
        export format.
        
        Parameters
        ----------
            document : Document
                the document to export
            couples : dict (string -> string)
                the "entry name" <=> "entry index" that allows to
                retrieve information to export.
                ex: couples = {u"chunking":u"C", u"NER":u"N"}
        """
        raise RuntimeError("export_to_data not implemented for class " + self.__class__)
