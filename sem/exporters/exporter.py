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


class Exporter(object):
    __ext = None

    def __init__(self, *args, **kwargs):
        pass

    @classmethod
    def extension(cls):
        return cls.__ext

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
                ex: couples = {"chunking":"C", "NER":"N"}
            output : str
                the name of the file to write into
        """
        to_write = self.document_to_unicode(document, couples, **kwargs)
        try:
            output.write(to_write)
        except AttributeError:
            with open(output, "w", encoding=encoding, newline="") as output_stream:
                output_stream.write(to_write)

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
                ex: couples = {"chunking":"C", "NER":"N"}
        """
        raise NotImplementedError(
            "export_to_data not implemented for class {}".format(self.__class__)
        )
