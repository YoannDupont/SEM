# -*- coding:utf-8 -*-

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

import pathlib
import sys

# measuring time laps
import time
from datetime import timedelta

import sem.importers
from sem.misc import str2bool
from .sem_module import SEMModule as RootModule

from sem.storage import SEMCorpus
from sem.exporters import get_exporter
import sem.logger


class SEMModule(RootModule):
    def __init__(
        self,
        exporter,
        lang="fr",
        lang_style="default.css",
        pos_column=None,
        chunk_column=None,
        ner_column=None,
        **kwargs,
    ):
        super(SEMModule, self).__init__(**kwargs)

        self._lang = lang
        self._lang_style = lang_style
        self._pos_column = pos_column
        self._chunk_column = chunk_column
        self._ner_column = ner_column
        if isinstance(exporter, str):
            sem.logger.info("getting exporter {0}".format(exporter))
            Exporter = get_exporter(exporter)
            self._exporter = Exporter(lang=self._lang, lang_style=self._lang_style)
        else:
            sem.logger.info("using loaded exporter")
            self._exporter = exporter

    def process_document(self, document, outfile=sys.stdout, output_encoding="utf-8", **kwargs):
        start = time.time()

        sem.logger.debug("setting name/column couples for exportation")

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
            sem.logger.debug("POS column is {0}".format(pos_column))
        if chunk_column:
            couples["chunking"] = chunk_column
            sem.logger.debug("chunking column is {0}".format(chunk_column))
        if ner_column:
            couples["ner"] = ner_column
            sem.logger.debug("NER column is {0}".format(ner_column))

        sem.logger.debug("exporting document to {0} format".format(self._exporter.extension))

        self._exporter.document_to_file(document, couples, outfile, encoding=output_encoding)

        laps = time.time() - start
        sem.logger.info("done in %s", timedelta(seconds=laps))


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

    pos_column = args.pos_column
    chunk_column = args.chunk_column
    ner_column = args.ner_column

    exporter = SEMModule(
        exporter_name,
        lang=lang,
        lang_style=lang_style,
        pos_column=pos_column,
        chunk_column=chunk_column,
        ner_column=ner_column,
    )

    if type(import_options) in (list,):  # list from argparse
        options = {}
        for option in import_options:
            key, value = option.split("=", 1)
            try:
                value = str2bool(value)
            except ValueError:
                pass
            if ',' in value:
                try:
                    value = [item for item in value.split(',') if item]
                except AttributeError:
                    pass
            options[key] = value
        options["encoding"] = ienc
    else:
        options = import_options

    infile_is_str = isinstance(infile, str)
    if infile_is_str:
        sem.logger.info("loading input file")
        document = sem.importers.load(infile, **options)
        if isinstance(document, SEMCorpus):
            sem.logger.warn("input file is SEM corpus, only exporting the first document")
            document = document[0]
    else:
        sem.logger.info("using input document")
        document = infile

    sem.logger.debug("exporting document {0}".format(document.name))
    exporter.process_document(document, outfile, encoding=oenc)

    laps = time.time() - start
    sem.logger.info("done in %s", timedelta(seconds=laps))


import sem

_subparsers = sem.argument_subparsers

parser = _subparsers.add_parser(
    pathlib.Path(__file__).stem, description="Export CoNLL-formatted data to specified format."
)

parser.add_argument("infile", help="The input file")
parser.add_argument("exporter_name", help="The name of the exporter to use")
parser.add_argument("outfile", help="The output file")
parser.add_argument(
    "-p", "--pos-column", dest="pos_column", default=None, help="The column for POS."
)
parser.add_argument(
    "-c", "--chunk-column", dest="chunk_column", default=None, help="The column for chunk."
)
parser.add_argument(
    "-n", "--ner-column", dest="ner_column", default=None, help="The column for NER."
)
parser.add_argument(
    "--lang", dest="lang", default="fr", help="The language of the text (default: %(default)s)"
)
parser.add_argument(
    "-s",
    "--lang-style",
    dest="lang_style",
    default="default.css",
    help="The style to use, if applicable (default: %(default)s)",
)
parser.add_argument(
    "--import-options",
    nargs="*",
    dest="import_options",
    help=(
        'Import-specific options. This is a list of "key=value" pairs.'
        'Typical keys for this options are: "fields" (the list of CoNLL fields),'
        '"word_field" (the name of the field where words are), "taggings" (the fields'
        'that contains taggings to load as annotations), "chunkings" (IOB formatted'
        'tags that represent some chunking (syntax or NE).'
    ),
)
parser.add_argument("--input-encoding", dest="ienc", help="Encoding of the input (default: UTF-8)")
parser.add_argument("--output-encoding", dest="oenc", help="Encoding of the input (default: UTF-8)")
parser.add_argument(
    "--encoding",
    dest="enc",
    default="UTF-8",
    help="Encoding of both the input and the output (default: UTF-8)",
)
parser.add_argument(
    "-l",
    "--log",
    dest="log_level",
    choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
    default="WARNING",
    help="Increase log level (default: %(default)s)",
)
parser.add_argument("--log-file", dest="log_file", help="The name of the log file")
