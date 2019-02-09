# -*- coding: utf-8 -*-

"""
file: html.py

Description: export annotated file to HTML

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

import os, cgi, codecs

try:
    from xml.etree import cElementTree as ET
except ImportError:
    from xml.etree import ElementTree as ET

from .exporter import Exporter as DefaultExporter

class Exporter(DefaultExporter):
    __ext = "html"
    
    def __init__(self, lang="fr", lang_style="default.css", *args, **kwargs):
        self._lang       = lang
        self._lang_style = lang_style

    def escape_tokens(self, corpus, token_entry):
        """
        Returns a list of (HTML-)escaped token given a corpus and
        an entry where to find the tokens.
        """
        escaped = []
        for sentence in corpus:
            escaped.append([])
            for element in sentence:
                escaped[-1].append(cgi.escape(element[token_entry]))
        return escaped
    
    def make_escaped_content(self, document):
        content           = document.content
        tokens            = document.segmentation("tokens")
        escaped_tokens    = [cgi.escape(content[token.lb : token.ub]) for token in tokens]
        escaped_nontokens = [cgi.escape(content[tokens[i].ub : tokens[i+1].lb]) for i in range(len(tokens)-1)]
        escaped_nontokens.insert(0, cgi.escape(content[0 : tokens[0].lb]))
        escaped_nontokens.append(cgi.escape(content[tokens[-1].ub : len(content)]))
        
        return escaped_tokens, escaped_nontokens
    
    def document_to_unicode(self, document, couples, encoding="utf-8", **kwargs):
        entry_names = {}
        for entry in couples:
            entry_names[entry.lower()] = couples[entry]
        
        pos_html   = []
        chunk_html = []
        ner_html   = []
        
        current_key = entry_names.get("pos", None)
        if current_key and current_key in document.annotations:
            pos_html = self.add_annotation_document(document, entry_names["pos"])
        current_key = entry_names.get("chunking", None)
        if current_key and current_key in document.annotations:
            chunk_html = self.add_annotation_document(document, entry_names.get("chunk", entry_names["chunking"]))
        current_key = entry_names.get("ner", None)
        if current_key and current_key in document.annotations:
            ner_html = self.add_annotation_document(document, entry_names["ner"])
        
        return self.makeHTML_document(document, pos_html, chunk_html, ner_html, encoding)
    
    def add_annotation_document(self, document, column):
        annotations = document.annotation(column).get_reference_annotations()[::-1]
        content = document.content
        
        parts = []
        last = len(content)
        for annotation in annotations:
            parts.append(cgi.escape(content[annotation.ub : last]).replace(u"\n", u"<br />\n").replace(u"\r<br />", u"<br />\r"))
            parts.append(u'</span>')
            parts.append(cgi.escape(content[annotation.lb : annotation.ub]).replace(u"\n", u"<br />\n").replace(u"\r<br />", u"<br />\r"))
            parts.append(u'<span id="{0}" title="{0}">'.format(annotation.value))
            last = annotation.lb
        parts.append(cgi.escape(content[0:last]).replace(u"\n", u"<br />\n").replace(u"\r<br />", u"<br />\r"))
        
        new_content = u"".join(parts[::-1])
        return new_content

    def makeHTML_document(self, document, pos, chunk, ner, output_encoding):
        def checked(number):
            # whether the tab is checked or not
            if 1 == number:
                return ' checked="true"'
            else:
                return ""
        
        css_tabs = "tabs.css"
        css_lang = self._lang_style
        
        # header + div that will contain tabs
        html_page = [u"""<html>
    <head>
        <meta charset="{0}" />
        <title>{1}</title>
        <link rel="stylesheet" href="{2}" />
        <link rel="stylesheet" href="{3}" />
    </head>
    <body>
        <div class="wrapper">
            <h1>{4}</h1>
            <div class="tab_container">""".format(output_encoding, document.name, css_tabs, css_lang, document.name)]
        
        # the annotations that will be outputted
        nth    = 1
        annots = []
        
        #
        # declaring tabs in HTML. TODO: refactor duped code
        #
        
        if pos != []:
            html_page.append(u"""
                <input id="tab{0}" type="radio" name="tabs"{1} />
                <label for="tab{0}">Part-Of-Speech</label>""".format(nth, checked(nth)))
            annots.append(u"""
                <section id="content{0}" class="tab-content">
{1}
                </section>""".format(nth, pos))
            nth += 1
        
        if chunk != []:
            html_page.append(u"""
                <input id="tab{0}" type="radio" name="tabs"{1} />
                <label for="tab{0}">Chunking</label>""".format(nth, checked(nth)))
            annots.append(u"""
                <section id="content{0}" class="tab-content">
{1}
                </section>""".format(nth, chunk))
            nth += 1
        
        if ner != []:
            html_page.append(u"""
                <input id="tab{0}" type="radio" name="tabs"{1} />
                <label for="tab{0}">Named Entity</label>""".format(nth, checked(nth)))
            annots.append(u"""
                <section id="content{0}" class="tab-content">
{1}
                </section>""".format(nth, ner))
            nth += 1
        
        # annotations are put after the tab declarations
        for annot in annots:
            html_page.append(annot)
        
        # closing everything that remains to be closed
        html_page.append(u"""
            </div>
        </div>
    </body>
</html>
""")
        
        return u"".join(html_page)
    
    def document_to_data(self, document, couples, **kwargs):
        """
        returns an ElementTree object (ATM) of the HTML page.
        """
        return ET.ElementTree(ET.fromstring(self.document_to_unicode(document, couples, encoding=kwargs.pop("encoding", "utf-8"), **kwargs)))
