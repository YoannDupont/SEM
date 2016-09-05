#-*- coding:utf-8 -*-

"""
file: export.py

Description: exports an input to a given format.

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

import logging, codecs

# measuring time laps
import time
from datetime import timedelta

from obj.IO.columnIO        import Reader
from obj.storage.document   import Document
from obj.exporters.dispatch import get_exporter
from obj.logger             import default_handler, file_handler

export_logger = logging.getLogger("sem.exportation")
export_logger.addHandler(default_handler)

def export(infile, exporter_name, outfile,
           pos_column=0, chunk_column=0, ner_column=0,
           lang="fr", lang_style="fr",
           ienc="utf-8", oenc="utf-8",
           log_level=logging.WARNING, log_file=None):
    
    start = time.time()
    
    if log_file is not None:
        export_logger.addHandler(file_handler(log_file))
    export_logger.setLevel(log_level)
    
    infile_is_str = type(infile) in (str, unicode)
    
    export_logger.info('getting exporter %s' %(exporter_name))
    
    Exporter = get_exporter(exporter_name)
    exporter = Exporter(lang=lang, lang_style=lang_style)
    
    export_logger.debug('setting name/column couples for exportation')
    
    corpus = None
    if infile_is_str:
        corpus = []
        for element in Reader(infile, ienc):
            corpus.append(element[:])
        couples = {"word":0}
    else:
        couples = {}
        if "word" in infile.corpus.fields:
            couples["token"] = "word"
        elif "token" in infile.corpus.fields:
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
    
    if infile_is_str:
        export_logger.debug('exporting corpus %s' %infile)
        exporter.corpus_to_file(corpus, couples, outfile, encoding=oenc)
    else:
        export_logger.debug('exporting document %s' %infile.name)
        exporter.document_to_file(infile, couples, outfile, encoding=oenc)
    
    laps = time.time() - start
    export_logger.info('done in %s' %(timedelta(seconds=laps)))
    

if __name__ == "__main__":
    import argparse, os.path, sys

    parser = argparse.ArgumentParser(description="Segments the textual content of a sentence into tokens. They can either be outputted line per line or in a vectorised format")
    
    parser.add_argument("infile",
                        help="The input file")
    parser.add_argument("exporter_name",
                        help="The name of the exporter to use")
    parser.add_argument("outfile",
                        help="The output file")
    parser.add_argument("-p", "--pos-column", dest="pos_column", type=int, default=0,
                        help="The column for POS. If 0, POS information is not added (default: %(default)s)")
    parser.add_argument("-c", "--chunk-column", dest="chunk_column", type=int, default=0,
                        help="The column for chunk. If 0, chunk information is not added (default: %(default)s)")
    parser.add_argument("-n", "--ner-column", dest="ner_column", type=int, default=0,
                        help="The column for NER. If 0, chunk information is not added (default: %(default)s)")
    parser.add_argument("--lang", dest="lang", default="fr",
                        help="The language of the text (default: %(default)s)")
    parser.add_argument("-s", "--lang-style", dest="lang_style", default="default.css",
                        help="The style to use, if applicable (default: %(default)s)")
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

    if __package__:
        args = parser.parse_args(sys.argv[2:])
    else:
        args = parser.parse_args()
    
    export(args.infile, args.exporter_name, args.outfile,
           pos_column=args.pos_column, chunk_column=args.chunk_column, ner_column=args.ner_column,
           lang=args.lang, lang_style=args.lang_style,
           ienc=args.ienc or args.enc, oenc=args.oenc or args.enc,
           log_level=args.log_level, log_file=args.log_file)
    sys.exit(0)
