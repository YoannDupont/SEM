#-*- coding:utf-8 -*-

"""
file: export.py

Description: exports an input to a given format.

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

import sys
import logging, codecs

# measuring time laps
import time
from datetime import timedelta

import sem.importers
import sem.misc
from .sem_module import SEMModule as RootModule

from sem.IO.columnIO      import Reader
from sem.storage.document import Document
from sem.exporters        import get_exporter
from sem.logger           import default_handler, file_handler

export_logger = logging.getLogger("sem.exportation")
export_logger.addHandler(default_handler)

class SEMModule(RootModule):
    def __init__(self, exporter, log_level="WARNING", log_file=None, lang="fr", lang_style="default.css", pos_column=None, chunk_column=None, ner_column=None, **kwargs):
        super(SEMModule, self).__init__(log_level=log_level, log_file=log_file, **kwargs)
        
        self._lang = lang
        self._lang_style = lang_style
        self._pos_column = pos_column
        self._chunk_column = chunk_column
        self._ner_column = ner_column
        if type(exporter) in (str, unicode):
            export_logger.info('getting exporter %s' %(exporter))
            Exporter = get_exporter(exporter)
            self._exporter = Exporter(lang=self._lang, lang_style=self._lang_style)
        else:
            export_logger.info('using loaded exporter')
            self._exporter = exporter
        
    
    def process_document(self, document, outfile=sys.stdout, output_encoding="utf-8", **kwargs):
        start = time.time()
        
        if self._log_file is not None:
            export_logger.addHandler(file_handler(self._log_file))
        export_logger.setLevel(self._log_level)
        
        export_logger.debug('setting name/column couples for exportation')
        
        oenc = kwargs.get("output-encoding", "utf-8")
        pos_column = self._pos_column
        chunk_column = self._chunk_column
        ner_column = self._ner_column
        
        couples = {}
        if "word" in document.corpus.fields:
            couples["token"] = "word"
        elif "token" in document.corpus.fields:
            couples["token"] = "token"
    
        if pos_column:
            couples["pos"] = pos_column
            export_logger.debug('POS column is %s' %pos_column)
        if chunk_column:
            couples["chunking"] = chunk_column
            export_logger.debug('chunking column is %s' %chunk_column)
        if ner_column:
            couples["ner"] = ner_column
            export_logger.debug('NER column is %s' %ner_column)
        
        export_logger.debug('exporting document to %s format' %self._exporter.extension)
        
        self._exporter.document_to_file(document, couples, outfile, encoding=output_encoding)
        
        laps = time.time() - start
        export_logger.info('done in %s' %(timedelta(seconds=laps)))

def main(args):
    start = time.time()
    
    infile = args.infile
    outfile = args.outfile
    exporter_name = args.exporter_name
    lang = args.lang
    lang_style = args.lang_style
    import_options = args.import_options or {}
    ienc = args.ienc or args.enc
    oenc = args.oenc or args.enc
    log_file = args.log_file
    log_level = args.log_level
    
    pos_column = args.pos_column
    chunk_column = args.chunk_column
    ner_column = args.ner_column
    couples = {}
    if pos_column:
        couples["pos"] = pos_column
        export_logger.debug('POS column is %s' %pos_column)
    if chunk_column:
        couples["chunking"] = chunk_column
        export_logger.debug('chunking column is %s' %chunk_column)
    if ner_column:
        couples["ner"] = ner_column
        export_logger.debug('NER column is %s' %ner_column)
    
    if log_file is not None:
        export_logger.addHandler(file_handler(log_file))
    export_logger.setLevel(log_level)
    
    if type(exporter_name) in (str, unicode):
        export_logger.info('getting exporter %s' %(exporter_name))
        Exporter = get_exporter(exporter_name)
        exporter = Exporter(lang=lang, lang_style=lang_style)
    else:
        export_logger.info('using loaded exporter')
        exporter = exporter_name
    
    if type(import_options) in (list,): # list from argparse
        options = {}
        for option in import_options:
            key, value = option.split(u"=", 1)
            try:
                value = sem.misc.str2bool(value)
            except ValueError:
                pass
            options[key] = value
        options["encoding"] = ienc
    else:
        options = import_options
    
    infile_is_str = type(infile) in (str, unicode)
    if infile_is_str:
        export_logger.info('loading input file')
        document = sem.importers.load(infile, logger=export_logger, **options)
    else:
        export_logger.info('using input document')
        document = infile
    
    export_logger.debug('exporting document %s' %document.name)
    exporter.document_to_file(document, couples, outfile, encoding=oenc, logger=export_logger)
    
    laps = time.time() - start
    export_logger.info('done in %s' %(timedelta(seconds=laps)))


import os.path
import sem

_subparsers = sem.argument_subparsers

parser = _subparsers.add_parser(os.path.splitext(os.path.basename(__file__))[0], description="Export CoNLL-formatted data to specified format.")

parser.add_argument("infile",
                    help="The input file")
parser.add_argument("exporter_name",
                    help="The name of the exporter to use")
parser.add_argument("outfile",
                    help="The output file")
parser.add_argument("-p", "--pos-column", dest="pos_column", default=None,
                    help="The column for POS.")
parser.add_argument("-c", "--chunk-column", dest="chunk_column", default=None,
                    help="The column for chunk.")
parser.add_argument("-n", "--ner-column", dest="ner_column", default=None,
                    help="The column for NER.")
parser.add_argument("--lang", dest="lang", default="fr",
                    help="The language of the text (default: %(default)s)")
parser.add_argument("-s", "--lang-style", dest="lang_style", default="default.css",
                    help="The style to use, if applicable (default: %(default)s)")
parser.add_argument("--import-options", nargs="*", dest="import_options",
                    help='Import-specific options. This is a list of "key=value" pairs.')
parser.add_argument("--input-encoding", dest="ienc",
                    help="Encoding of the input (default: UTF-8)")
parser.add_argument("--output-encoding", dest="oenc",
                    help="Encoding of the input (default: UTF-8)")
parser.add_argument("--encoding", dest="enc", default="UTF-8",
                    help="Encoding of both the input and the output (default: UTF-8)")
parser.add_argument("-l", "--log", dest="log_level", choices=("DEBUG","INFO","WARNING","ERROR","CRITICAL"), default="WARNING",
                    help="Increase log level (default: %(default)s)")
parser.add_argument("--log-file", dest="log_file",
                    help="The name of the log file")

