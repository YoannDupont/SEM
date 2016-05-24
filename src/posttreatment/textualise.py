# -*- coding: utf-8 -*-

"""
file: textualise.py

Description: write the output of a wapiti labeled file into sentences.
Each sentence is written on a single line and every sentence is spaced
by an empty line.
At the moment, this program allows to "sentencify" POS and chunking tagged
files. POS tags should be given in a file that is a python evaluable list and
the chunks should have the following construction : B-<<ID>> when the tag
marks the beginning of a chunk and I-<<ID>> when the tag marks the
continuation of the chunk. The end is not marked explicitly as the beginning
of a new chunk is the end of the preceeding one.
However, if another marking is used or even none, each different tag will be
considered as the identifier of a chunk.

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

import logging, os, os.path, sys, string, time

from obj.IO.columnIO import Reader, Writer
from obj.logger import logging_format
from obj.misc   import to_dhms

B = u"B"
I = u"I"
O = u"O0"

textualise_logger = logging.getLogger("sem.textualise")

def textualise(inputfile, outputfile,
               pos_column=0, chunk_column=0,
               ienc="utf-8", oenc="utf-8",
               log_level=logging.CRITICAL, log_file=None):
    start = time.time()
    file_mode = u"a"
    if type(log_file) in (str, unicode):
        file_mode = u"w"
    logging.basicConfig(level=log_level, format=logging_format, filename=log_file, filemode=file_mode)
    
    def join_space(s):
        return u" ".join(s)
    
    assert(pos_column != chunk_column or pos_column == 0)
    
    textualise_logger.info('textualising "%s" into "%s"' %(inputfile, outputfile))
    
    if pos_column != 0:
        textualise_logger.info('POS column is %i' %pos_column)
    if chunk_column != 0:
        textualise_logger.info('chunking column is %i' %chunk_column)
    
    incorpus  = Reader(inputfile, ienc)
    outcorpus = Writer(outputfile, oenc, joiner=join_space)
    
    if pos_column != 0 and chunk_column != 0:
        tokens = get_tokens(incorpus)
        if pos_column != 0:
            add_pos(tokens, incorpus, pos_column)
        if chunk_column != 0:
            add_chunk(tokens, incorpus, chunk_column)
        outcorpus.write([tokens])
    else:
        textualise_logger.warn("POS and chunk not requested, not doing anything")
    
    textualise_logger.info("done in %s", to_dhms(time.time() - start))

def get_tokens(corpus):
    tokens = []
    for sentence in corpus:
        tokens.append([])
        for token in sentence:
            tokens[-1].append(token[0])
    return tokens

def add_pos(tokens, incorpus, poscol):
    for i, sentence in enumerate(incorpus):
        for j, token in enumerate(sentence):
            tokens[i][j] += u"/"+token[poscol]

def add_chunk(tokens, incorpus, chunkcol):
    for i, sentence in enumerate(incorpus):
        for j, token in enumerate(sentence):
            if token[chunkcol][0] == B:
                tokens[i][j] = u"(" + getchunkid(token[chunkcol]) + u" " + tokens[i][j]
            if token[chunkcol][0] in B+I and (j == len(sentence)-1 or sentence[j+1][chunkcol][0] != I):
                tokens[i][j] += u")"

def getchunkid(chunk):
    return (chunk[2:] if (chunk[:2]==(u'B-') or chunk[:2]==(u'I-')) else chunk) # trimming "B-" or "I-" if necessary

if __name__ == '__main__':
    import argparse, sys
    parser = argparse.ArgumentParser(description="Takes a vectorized text (in a file) and outputs an linear text (in a file).")
    
    parser.add_argument("input",
                        help="path/name of the out file. Overwritten if existing.")
    parser.add_argument("output",
                        help="path/name of the out file. Overwritten if existing.")
    parser.add_argument('-p', '--pos-column', dest="pos_column", type=int, default=0,
                        help="The column for POS. If 0, POS information is not added (default: 0)")
    parser.add_argument('-c', '--chunk-column', dest="chunk_column", type=int, default=0,
                        help="The column for chunk. If 0, chunk information is not added (default: 0)")
    parser.add_argument("--input-encoding", dest="ienc",
                        help="Encoding of the input (default: UTF-8)")
    parser.add_argument("--output-encoding", dest="oenc",
                        help="Encoding of the input (default: UTF-8)")
    parser.add_argument("--encoding", dest="enc", default="UTF-8",
                        help="Encoding of both the input and the output (default: UTF-8)")
    parser.add_argument("-l", "--log", dest="log_level", action="count",
                        help="Increase log level (default: critical)")
    parser.add_argument("--log-file", dest="log_file",
                        help="The name of the log file")
    
    arguments = (sys.argv[2:] if __package__ else sys.argv)
    parser    = parser.parse_args(arguments)
    
    textualise(parser.input, parser.output,
               pos_column=parser.pos_column, chunk_column=parser.chunk_column,
               ienc=parser.ienc or parser.enc, oenc=parser.oenc or parser.enc,
               log_level=parser.log_level, log_file=parser.log_file)
    sys.exit(0)
