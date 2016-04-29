# -*- coding: utf-8 -*-

"""
file: export.py

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

import logging, os, os.path, sys, string, time, cgi, codecs

from software import Software

from obj.IO.columnIO import Reader
from obj.logger      import logging_format
from obj.misc        import to_dhms

export_logger = logging.getLogger("sem.export")

def export(inputfile, outputfile,
           document_name=None, lang="fr", lang_style="default.css",
           pos_column=0, chunk_column=0, ner_column=0,
           ienc="utf-8", oenc="utf-8",
           log_level=logging.CRITICAL, log_file=None):
    start = time.time()
    
    file_mode = u"a"
    if type(log_file) in (str, unicode):
        file_mode = u"w"
    logging.basicConfig(level=log_level, format=logging_format, filename=log_file, filemode=file_mode)
    
    if not document_name:
        document_name = os.path.basename(outputfile)
    
    export_logger.info('exporting "%s"' %(inputfile))
    
    if pos_column != 0:
        export_logger.debug('POS column is %i' %pos_column)
    if chunk_column != 0:
        export_logger.debug('chunking column is %i' %chunk_column)
    if ner_column != 0:
        export_logger.debug('NER column is %i' %ner_column)
    
    corpus = []
    for element in Reader(inputfile, ienc):
        corpus.append(element[:])
    
    escaped    = escape_tokens(corpus)
    pos_html   = []
    chunk_html = []
    ner_html   = []
    if pos_column != 0:
        pos_html = add_pos(escaped, corpus, pos_column)
    if chunk_column != 0:
        chunk_html = add_chunking(escaped, corpus, chunk_column)
    if ner_column != 0:
        ner_html = add_chunking(escaped, corpus, ner_column)
    
    export_logger.info('Writing "%s"' %(outputfile))
    
    with codecs.open(outputfile, "w", oenc) as O:
        O.write(makeHTML(pos_html, chunk_html, ner_html, lang, oenc, document_name=document_name, lang_style=lang_style))
    
    export_logger.info("done in %s", to_dhms(time.time() - start))

def escape_tokens(corpus):
    escaped = []
    for sentence in corpus:
        escaped.append([])
        for element in sentence:
            escaped[-1].append(cgi.escape(element[0]))
    return escaped

def add_pos(escaped, corpus, column):
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

def add_chunking(escaped, corpus, column):
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

def makeHTML(pos, chunk, ner, lang, output_encoding, document_name="", lang_style="default.css"):
    def checked(number):
        """ whether the tab is checked or not """
        if 1 == number:
            return " checked"
        else:
            return ""
    
    css_tabs = os.path.join(Software.SEM_HOME, "resources", "css", "tabs.css")
    css_lang = os.path.join(Software.SEM_HOME, "resources", "css", lang, lang_style)
    
    # header + div that will contain tabs
    html_page = u"""<html>
    <head>
        <meta charset="%s" />
        <title>%s</title>
        <link rel="stylesheet" href="%s">
        <link rel="stylesheet" href="%s">
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
                <input id="tab%i" type="radio" name="tabs"%s>
                <label for="tab%i">Part-Of-Speech</label>""" %(nth, checked(nth), nth))
        annots.append(u"""
                <section id="content%i" class="tab-content">
%s
                </section>""" %(nth, u"\n".join([u" ".join(pos_tokens) for pos_tokens in pos])))
        nth += 1
    
    if chunk != []:
        html_page += (u"""
                <input id="tab%i" type="radio" name="tabs"%s>
                <label for="tab%i">Chunking</label>""" %(nth, checked(nth), nth))
        annots.append(u"""
                <section id="content%i" class="tab-content">
%s
                </section>""" %(nth, u"\n".join([u" ".join(chunk_tokens) for chunk_tokens in chunk])))
        nth += 1
    
    if ner != []:
        html_page += (u"""
                <input id="tab%i" type="radio" name="tabs"%s>
                <label for="tab%i">Named Entity</label>""" %(nth, checked(nth), nth))
        annots.append(u"""
                <section id="content%i" class="tab-content">
%s
                </section>""" %(nth, u"\n".join([u" ".join(ner_tokens) for ner_tokens in ner])))
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
    
    return u"""<html>
    <head>
        <meta charset="%s" />
        <title>%s</title>
        <link rel="stylesheet" href="%s">
        <link rel="stylesheet" href="%s">
    </head>
    <body>
        <div class="wrapper">
            <h1>%s</h1>
            <div class="tab_container">
                <input id="tab1" type="radio" name="tabs" checked>
                <label for="tab1">Part-Of-Speech</label>
                <input id="tab2" type="radio" name="tabs">
                <label for="tab2">Chunking</label>
                <input id="tab3" type="radio" name="tabs">
                <label for="tab3">Named Entity</label>
                <section id="content1" class="tab-content">
%s
                </section>
                <section id="content2" class="tab-content">
%s
                </section>
                <section id="content3" class="tab-content">
%s
                </section>
            </div>
        </div>
    </body>
</html>
""" %(output_encoding, document_name, css_tab, css_lang, document_name, u"\n".join([u" ".join(pos_tokens) for pos_tokens in pos]), u"\n".join([u" ".join(chunk_tokens) for chunk_tokens in chunk]), u"\n".join([u" ".join(ner_tokens) for ner_tokens in ner]))

if __name__ == '__main__':
    import argparse, sys
    parser = argparse.ArgumentParser(description="Takes a vectorized text (in a file) and outputs an linear text (in a file).")
    
    parser.add_argument("input",
                        help="path/name of the out file. Overwritten if existing.")
    parser.add_argument("output",
                        help="path/name of the out file. Overwritten if existing.")
    parser.add_argument("-d", "--document-name", dest="document_name",
                        help="The column for POS. If 0, POS information is not added (default: %(default)s)")
    parser.add_argument("--lang", dest="lang", default="fr",
                        help="The language (default: %(default)s)")
    parser.add_argument("--lang-style", dest="lang_style", default="default.css",
                        help="The name of the CSS stylesheet for the given language (default: %(default)s)")
    parser.add_argument("-p", "--pos-column", dest="pos_column", type=int, default=0,
                        help="The column for POS. If 0, POS information is not added (default: %(default)s)")
    parser.add_argument("-c", "--chunk-column", dest="chunk_column", type=int, default=0,
                        help="The column for chunk. If 0, chunk information is not added (default: %(default)s)")
    parser.add_argument("-n", "--ner-column", dest="ner_column", type=int, default=0,
                        help="The column for NER. If 0, chunk information is not added (default: %(default)s)")
    parser.add_argument("--input-encoding", dest="ienc",
                        help="Encoding of the input (default: UTF-8)")
    parser.add_argument("--output-encoding", dest="oenc",
                        help="Encoding of the input (default: UTF-8)")
    parser.add_argument("--encoding", dest="enc", default="UTF-8",
                        help="Encoding of both the input and the output (default: %(default)s)")
    parser.add_argument("-l", "--log", dest="log_level", action="count",
                        help="Increase log level (default: critical)")
    parser.add_argument("--log-file", dest="log_file",
                        help="The name of the log file")
    
    arguments = (sys.argv[2:] if __package__ else sys.argv)
    args      = parser.parse_args(arguments)
    
    export(args.input, args.output,
           document_name=args.document_name, lang=args.lang, lang_style=args.lang_style,
           pos_column=args.pos_column, chunk_column=args.chunk_column, ner_column=args.ner_column,
           ienc=args.ienc or args.enc, oenc=args.oenc or args.enc,
           log_level=args.log_level, log_file=args.log_file)
    sys.exit(0)
