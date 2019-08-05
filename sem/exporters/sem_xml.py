# -*- coding: utf-8 -*-

"""
file: sem_xml.py

Description: export annotated file to the SEM XML format.

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

from sem.exporters.exporter import Exporter as DefaultExporter
import sem.storage.document


class Exporter(DefaultExporter):
    __ext = "sem.xml"

    def __init__(self, *args, **kwargs):
        pass

    def document_to_file(
        self, document: sem.storage.document.Document, couples, output, encoding="utf-8", **kwargs
    ):
        document.write(open(output, "w", encoding=encoding), add_header=True)

    def document_to_data(self, document, couples, **kwargs):
        """
        This is just creating a dictionary from the document.
        Nearly copy-pasta of the Document.unicode method.
        """

        return document
