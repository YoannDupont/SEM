# -*- coding: utf-8 -*-

"""
file: clean_info.py

Description: remove unwanted fields from a CoNLL-formatted input.

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
along with this program. If not, see GNU official website.
"""

import logging, codecs

# measuring time laps
import time
from datetime import timedelta

from obj.misc   import ranges_to_set
from obj.logger import default_handler, file_handler

clean_info_logger = logging.getLogger("sem.clean_info")
clean_info_logger.addHandler(default_handler)

def document_clean(document, ranges,
                   log_level="CRITICAL", log_file=None):
    """
    Cleans the obj.storage.corpus of a document, removing unwanted fields.
    
    Parameters
    ----------
    document : obj.storage.Document
        the document containing the corpus to clean.
    ranges : str or list of int or list of str
        if str: fields to remove will be induced
        if list of int: each element in the list is the index of a field
        to remove in corpus.fields
        if list of string: the list of fields to remove
    """
    
    start = time.time()
    
    if log_file is not None:
        clean_info_logger.addHandler(file_handler(log_file))
    clean_info_logger.setLevel(log_level)
    
    clean_info_logger.info(u'cleaning document')
    
    fields  = None
    allowed = None
    if type(ranges) in (str, unicode):
        try:
            allowed = sorted(ranges_to_set(ranges, len(document.corpus.fields), include_zero=True)) # comma-separated numbers or number ranges
        except:
            allowed = ranges.split(u",") # comma-separated named fields
    else:
        allowed = ranges
    
    if len(allowed) == 0:
        raise RuntimeError("No more data after cleaning !")
    
    if type(allowed[0]) in (int, long):
        fields = [document.corpus.fields[i] for i in allowed]
    else:
        fields = allowed
    
    to_remove = [field for field in document.corpus.fields if field not in fields]
    document.corpus.fields = fields
    
    for i in range(len(document.corpus.sentences)):
        for j in range(len(document.corpus.sentences[i])):
            for field in to_remove:
                del document.corpus.sentences[i][j][field]
    
    laps = time.time() - start
    clean_info_logger.info(u'done in %s' %timedelta(seconds=laps))

def clean_info(infile, outfile, ranges,
               ienc="utf-8", oenc="utf-8",
               log_level="CRITICAL", log_file=None):
    """
    Cleans a CoNLL-formatted file, removing fields at given indices.
    
    Parameters
    ----------
    infile : str
        the name of the file to clean.
    ranges : str
        the fields to remove. Fields is a coma-separated list of indices
        or ranges of indices using a python format (ie: "lo:hi").
    """
    
    if log_file is not None:
        clean_info_logger.addHandler(file_handler(log_file))
    clean_info_logger.setLevel(log_level)
    
    allowed = ranges_to_set(ranges, len(codecs.open(infile, "rU", ienc).readline().strip().split()), include_zero=True)
    max_abs = 0
    for element in allowed:
        element = abs(element) + (1 if element > 0 else 0)
        max_abs = max(max_abs, element)
    nelts = len(codecs.open(infile, "rU", ienc).readline().strip().split())
    
    if nelts < max_abs:
        clean_info_logger.error(u'asked to keep up to %i field(s), yet only %i are present in the "%s"' %(max_abs, nelts, infile))
        raise runtimeError(u'asked to keep up to %i field(s), yet only %i are present in the "%s"' %(max_abs, nelts, infile))
    
    clean_info_logger.info(u'cleaning "%s"' %(infile))
    clean_info_logger.info(u'keeping columns: %s' %(u", ".join([str(s) for s in sorted(allowed)])))
    clean_info_logger.info(u'writing "%s"' %(outfile))
        
    with codecs.open(outfile, "w", oenc) as O:
        for line in codecs.open(infile, "rU", ienc):
            line = line.strip().split()
            if line != []:
                tokens = [line[i] for i in xrange(len(line)) if i in allowed]
                O.write(u"\t".join(tokens))
            O.write(u"\n")
    
    clean_info_logger.info(u'done')

if __name__ == "__main__":
    import argparse, sys

    parser = argparse.ArgumentParser(description="...")

    parser.add_argument("infile",
                        help="The input file")
    parser.add_argument("outfile",
                        help="The output file ")
    parser.add_argument("ranges",
                        help="The ranges of indexes to keep in the file.")
    parser.add_argument("--input-encoding", dest="ienc",
                        help="Encoding of the input (default: UTF-8)")
    parser.add_argument("--output-encoding", dest="oenc",
                        help="Encoding of the input (default: UTF-8)")
    parser.add_argument("--encoding", dest="enc", default="UTF-8",
                        help="Encoding of both the input and the output (default: UTF-8)")
    parser.add_argument("-l", "--log", dest="log_level", choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"), default="WARNING",
                        help="Increase log level (default: critical)")
    parser.add_argument("--log-file", dest="log_file",
                        help="The name of the log file")
    
    arguments = (sys.argv[2:] if __package__ else sys.argv)
    parser    = parser.parse_args(arguments)
    
    clean_info(parser.infile, parser.outfile, parser.ranges,
               ienc=parser.ienc or parser.enc, oenc=parser.oenc or parser.enc,
               log_level=parser.log_level, log_file=parser.log_file)
    sys.exit(0)
