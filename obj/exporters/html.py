# -*- coding: utf-8 -*-

"""
file: html.py

Description: export annotated file to HTML

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

import os, cgi, codecs

try:
    from xml.etree import cElementTree as ET
except ImportError:
    from xml.etree import ElementTree as ET

from obj.exporters.exporter import Exporter as DefaultExporter

import software

class Exporter(DefaultExporter):
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
    
    #
    # corpus-specific methods
    #
    
    def corpus_to_unicode(self, corpus, couples, document_name=None, token_field=0, encoding="utf-8", **kwargs):
        entry_names = {}
        for entry in couples:
            entry_names[entry.lower()] = couples[entry]
        
        data = []
        for sentence in corpus:
            data.append(sentence[:])
        
        escaped    = self.escape_tokens(data, token_field)
        pos_html   = []
        chunk_html = []
        ner_html   = []
        if entry_names.get("pos", None):
            pos_html = self.add_pos_corpus(escaped, data, entry_names["pos"])
        if entry_names.get("chunking", None):
            chunk_html = self.add_chunking_corpus(escaped, data, entry_names["chunking"])
        if entry_names.get("ner", None):
            ner_html = self.add_chunking_corpus(escaped, data, entry_names["ner"])
        
        return self.makeHTML_corpus(pos_html, chunk_html, ner_html, self._lang, encoding, document_name=document_name, lang_style=self._lang_style)

    def add_pos_corpus(self, escaped, corpus, column):
        to_return = [e[:] for e in escaped]
        for i in range(len(to_return)):
            for j in range(len(to_return[i])):
                if corpus[i][j][column][0] == "_":
                    if (j+1 == len(to_return[i]) or corpus[i][j+1][column][0] != "_"):
                        to_return[i][j] = '%s</span>' %(to_return[i][j])
                else:
                    to_return[i][j] = '<span id="%s" title="%s">%s' %(corpus[i][j][column], corpus[i][j][column], to_return[i][j])
                    if (j+1 == len(to_return[i]) or corpus[i][j+1][column][0] != "_"):
                        to_return[i][j] = '%s</span>' %(to_return[i][j])
        return to_return

    def add_chunking_corpus(self, escaped, corpus, column):
        to_return = [e[:] for e in escaped]
        for i in range(len(to_return)):
            for j in range(len(to_return[i])):
                if corpus[i][j][column][0] == "O": continue
                chunk_name = corpus[i][j][column][2:]
                if corpus[i][j][column][0] == "B":
                    to_return[i][j] = '<span id="%s" title="%s">%s' %(chunk_name, chunk_name, escaped[i][j])
                if corpus[i][j][column][0] in "BI" and (j+1 == len(to_return[i]) or corpus[i][j+1][column][0] != "I"):
                    to_return[i][j] += '</span>'
        return to_return

    def makeHTML_corpus(self, pos, chunk, ner, lang, output_encoding, document_name="", lang_style="default.css"):
        def checked(number):
            """ whether the tab is checked or not """
            if 1 == number:
                return ' checked="true"'
            else:
                return ""
        
        #css_tabs = os.path.join(software.SEM_HOME, "resources", "css", "tabs.css")
        #css_lang = os.path.join(software.SEM_HOME, "resources", "css", lang, lang_style)
        css_tabs = "tabs.css"
        css_lang = lang_style
        
        # header + div that will contain tabs
        html_page = u"""<html>
    <head>
        <meta charset="%s" />
        <title>%s</title>
        <link rel="stylesheet" href="%s" />
        <link rel="stylesheet" href="%s" />
    </head>
    <body>
        <div class="wrapper">
            <h1>%s</h1>
            <div class="tab_container">""" %(output_encoding, document_name, css_tabs, css_lang, document_name)
        
        # the annotations that will be outputted
        nth    = 1
        annots = []
        
        #
        # declaring tabs in HTML. TODO: refactor duped code
        #
        
        if pos != []:
            html_page += (u"""
                <input id="tab%i" type="radio" name="tabs"%s />
                <label for="tab%i">Part-Of-Speech</label>""" %(nth, checked(nth), nth))
            annots.append(u"""
                <section id="content%i" class="tab-content">
%s
                </section>""" %(nth, u"\n".join([u" ".join(pos_token) for pos_token in pos])))
            nth += 1
        
        if chunk != []:
            html_page += (u"""
                <input id="tab%i" type="radio" name="tabs"%s />
                <label for="tab%i">Chunking</label>""" %(nth, checked(nth), nth))
            annots.append(u"""
                <section id="content%i" class="tab-content">
%s
                </section>""" %(nth, u"\n".join([u" ".join(chunk_token) for chunk_token in chunk])))
            nth += 1
    
        if ner != []:
            html_page += (u"""
                <input id="tab%i" type="radio" name="tabs"%s />
                <label for="tab%i">Named Entity</label>""" %(nth, checked(nth), nth))
            annots.append(u"""
                <section id="content%i" class="tab-content">
%s
                </section>""" %(nth, u"\n".join([u" ".join(ner_token) for ner_token in ner])))
            nth += 1
        
        # annotations are put after the tab declarations
        for annot in annots:
            html_page += annot
        
        # closing everything that remains to be closed
        html_page += u"""
            </div>
        </div>
    </body>
</html>
"""
        
        return html_page
    
    #
    # document-specific methods
    #
    
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
        
        escaped_tokens, escaped_nontokens = self.make_escaped_content(document)
        pos_html   = []
        chunk_html = []
        ner_html   = []
        if entry_names.get("pos", None):
            pos_html = self.add_annotation_document(document, escaped_tokens[:], escaped_nontokens, entry_names["pos"])
        if entry_names.get("chunk", entry_names.get("chunking", None)):
            chunk_html = self.add_annotation_document(document, escaped_tokens[:], escaped_nontokens, entry_names.get("chunk", entry_names["chunking"]))
        if entry_names.get("ner", None):
            ner_html = self.add_annotation_document(document, escaped_tokens[:], escaped_nontokens, entry_names["ner"])
        
        return self.makeHTML_document(document, pos_html, chunk_html, ner_html, encoding)
    
    def add_annotation_document(self, document, escaped_tokens, escaped_nontokens, column):
        annot = document.annotation(column)
        
        for annotation in annot:
            escaped_tokens[annotation.span.lb]    = '<span id="%s" title="%s">%s' %(annotation.value, annotation.value, escaped_tokens[annotation.span.lb])
            escaped_tokens[annotation.span.ub-1] += '</span>'
        for i in range(len(escaped_nontokens)):
            escaped_tokens.insert(2*i, escaped_nontokens[i])
        
        new_content = u"".join(escaped_tokens)
        new_content = new_content.replace(u"\n", u"<br />\n").replace(u"\r<br />", u"<br />\r")
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
        html_page = u"""<html>
    <head>
        <meta charset="%s" />
        <title>%s</title>
        <link rel="stylesheet" href="%s" />
        <link rel="stylesheet" href="%s" />
    </head>
    <body>
        <div class="wrapper">
            <h1>%s</h1>
            <div class="tab_container">""" %(output_encoding, document.name, css_tabs, css_lang, document.name)
        
        # the annotations that will be outputted
        nth    = 1
        annots = []
        
        #
        # declaring tabs in HTML. TODO: refactor duped code
        #
        
        if pos != []:
            html_page += (u"""
                <input id="tab%i" type="radio" name="tabs"%s />
                <label for="tab%i">Part-Of-Speech</label>""" %(nth, checked(nth), nth))
            annots.append(u"""
                <section id="content%i" class="tab-content">
%s
                </section>""" %(nth, pos))
            nth += 1
        
        if chunk != []:
            html_page += (u"""
                <input id="tab%i" type="radio" name="tabs"%s />
                <label for="tab%i">Chunking</label>""" %(nth, checked(nth), nth))
            annots.append(u"""
                <section id="content%i" class="tab-content">
%s
                </section>""" %(nth, chunk))
            nth += 1
        
        if ner != []:
            html_page += (u"""
                <input id="tab%i" type="radio" name="tabs"%s />
                <label for="tab%i">Named Entity</label>""" %(nth, checked(nth), nth))
            annots.append(u"""
                <section id="content%i" class="tab-content">
%s
                </section>""" %(nth, ner))
            nth += 1
        
        # annotations are put after the tab declarations
        for annot in annots:
            html_page += annot
        
        # closing everything that remains to be closed
        html_page += u"""
            </div>
        </div>
    </body>
</html>
"""
        
        return html_page
    
    def document_to_data(self, document, couples, **kwargs):
        """
        returns an ElementTree object (ATM) of the HTML page.
        """
        return ET.ElementTree(ET.fromstring(self.document_to_unicode(document, couples, encoding=kwargs.pop("encoding", "utf-8"), **kwargs)))
