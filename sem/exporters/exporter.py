# -*- coding: utf-8 -*-

"""
file: exporter.py

Description: root type for exporter objects.

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

import codecs
import os.path

class Exporter(object):
    __ext = None
    
    def __init__(self, *args, **kwargs):
        pass
    
    @classmethod
    def extension(cls):
        return cls.__ext
    
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
        raise NotImplementedError("export_to_string not implemented for class " + self.__class__)
    
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
        raise NotImplementedError("export_to_string not implemented for class " + self.__class__)
    
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
        if type(output) in (str, unicode):
            with codecs.open(output, "w", encoding) as O:
                O.write(self.document_to_unicode(document, couples, **kwargs))
        else:
            output.write(self.document_to_unicode(document, couples, **kwargs))
    
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
        raise NotImplementedError("export_to_data not implemented for class " + self.__class__)
