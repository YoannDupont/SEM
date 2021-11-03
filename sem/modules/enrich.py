# -*- coding: utf-8 -*-

"""
file: enrich.py

Description: this program is used to enrich a CoNLL-formatted file with
various features.

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

import argparse
import time
from datetime import timedelta

from sem.processors import EnrichProcessor

import sem.util
import sem.logger
from sem.importers import conll_file


def main(argv=None):
    enrich(**vars(parser.parse_args(argv)))


def enrich(
    infile,
    infofile,
    outfile,
    mode="train",
    ienc=None,
    oenc=None,
    enc="utf-8",
    log_level="WARNING",
    log_file=None
):
    """
    Takes a CoNLL-formatted file and write another CoNLL-formatted file
    with additional features in it.

    Parameters
    ----------
    infile : str
        the CoNLL-formatted input file.
    infofile : str
        the XML file containing the different features.
    mode : str
        the mode to use for infofile. Some inputs may only be present in
        a particular mode. For example, the output tag is only available
        in "train" mode.
    log_level : str or int
        the logging level.
    log_file : str
        if not None, the file to log to (does not remove command-line
        logging).
    """

    start = time.time()

    if log_file is not None:
        sem.logger.addHandler(sem.logger.file_handler(log_file))
    sem.logger.setLevel(log_level)
    sem.logger.info('parsing enrichment file "%s"', infofile)

    processor = EnrichProcessor(path=infofile, mode=mode)

    sem.logger.debug('enriching file "%s"', infile)

    bentries = [entry.name for entry in processor.bentries]
    aentries = [entry.name for entry in processor.aentries]
    document = conll_file(
        infile, bentries + aentries, (bentries + aentries)[0], encoding=ienc or enc
    )

    processor.process_document(document)
    fields = processor.fields()
    with open(outfile, "w", encoding=oenc or enc) as output_stream:
        for sentence in document.corpus:
            output_stream.write(sentence.conll(fields))
            output_stream.write("\n\n")

    laps = time.time() - start
    sem.logger.info("done in %s", timedelta(seconds=laps))


parser = argparse.ArgumentParser(
    "Adds information to a file using and XML-styled configuration file."
)

parser.add_argument("infile", help="The input file (CoNLL format)")
parser.add_argument("infofile", help="The information file (XML format)")
parser.add_argument("outfile", help="The output file (CoNLL format)")
parser.add_argument(
    "-m",
    "--mode",
    dest="mode",
    default="train",
    choices=("train", "label", "annotate", "annotation"),
    help="The mode for enrichment. May make entries vary (default: %(default)s)",
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
    help="Increase log level (default: critical)",
)
parser.add_argument("--log-file", dest="log_file", help="The name of the log file")
