# -*- coding: utf-8 -*-

"""
file: html_inline.py

Description: export annotated file to HTML (only inline annotations)

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

class Exporter(DefaultExporter):
    __ext = "html"

    def __init__(self, lang="fr", lang_style="default.css", *args, **kwargs):
        self._lang = lang
        self._lang_style = lang_style

    def document_to_unicode(self, document, couples, encoding="utf-8", **kwargs):
        entry_names = {}
        for entry in couples:
            entry_names[entry.lower()] = couples[entry]

        key = entry_names.get("ner", None)
        if key is None or document.annotation(key) is None:
            key = entry_names.get("chunking", None)
        if key is None or document.annotation(key) is None:
            key = entry_names.get("pos", None)
        if key is None or document.annotation(key) is None:
            raise KeyError("Cannot find any annotation for export.")

        content = document.content[:]

        position2html = {}
        annotations = document.annotation(key).get_reference_annotations()
        for annotation in reversed(annotations):
            lb = annotation.lb
            ub = annotation.ub
            value = annotation.value

            if ub not in position2html:
                position2html[ub] = []
            position2html[ub].insert(0, '</span>')
            if lb not in position2html:
                position2html[lb] = []
            position2html[lb].append('<span id="{0}" title="{0}">'.format(value))

        for index in reversed(sorted(position2html.keys())):
            content = content[:index] + "".join(position2html[index]) + content[index:]

        content = content.replace("<head>", '<head>\n<link rel="stylesheet" href="{0}" />'.format(
            self._lang
        ))
        content = content.replace("<head>", '<head>\n<link rel="stylesheet" href="{0}" />'.format(
            self._lang_style
        ))

        return content
