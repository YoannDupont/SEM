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
    
    assert(pos_column != chunk_column or pos_column == 0)
    
    textualise_logger.info('textualising "%s" into "%s"' %(inputfile, outputfile))
    
    if pos_column != 0:
        textualise_logger.info('POS column is %i' %pos_column)
    if chunk_column != 0:
        textualise_logger.info('chunking column is %i' %chunk_column)
    
    incorpus  = Reader(inputfile, ienc)
    outcorpus = Writer(outputfile, oenc)
    
    if pos_column != 0 and chunk_column != 0: # doing both POS and CHUNKING
        textualise_posandchunk(incorpus, outcorpus, pos_column, chunk_column)
    elif pos_column != 0: # doing only POS
        textualise_pos(incorpus, outcorpus, pos_column)
    elif chunk_column != 0: # doing only chunk
        textualise_chunk(incorpus, outcorpus, chunk_column)
    else:
        textualise_logger.info("both POS and chunk are 0, not doing anything")
    
    textualise_logger.info("done in %s", to_dhms(time.time() - start))

def textualise_pos(incorpus, outc, poscol):
    for paragraph in incorpus:
        outc.write_l( [u" ".join( [u"/".join( [line[0], line[poscol]] ) for line in paragraph] )])

def textualise_chunk(incorpus, outc, chunkcol):
    chkid  = u""
    result = u""
    tokens = []
    for paragraph in incorpus:
        chkid = getchunkid(paragraph[0][chunkcol])
        for informations in paragraph:
            chunk = informations[chunkcol]
            if (getchunkid(chunk) == chkid) or (getchunkid(chunk) == I and chkid in [B,I]):
                tokens.append(informations[0])
            else:
                result += (u"" if result == u"" else u" ") + to_string(tokens, chkid)
                del tokens[:]
                tokens.append(informations[0])
                chkid = getchunkid(chunk)
            if informations == paragraph[-1]:
                result += u" " + to_string(tokens, chkid)
                del tokens[:]
        outc.write_l([result.strip()])
        result = u""

def textualise_posandchunk(incorpus, outc, poscol, chunkcol):
    chkid   = u""
    result  = u""
    tokens  = []
    POS_seq = []
    for paragraph in incorpus:
        chkid = getchunkid(paragraph[0][chunkcol])
        for informations in paragraph:
            pos   = informations[poscol]
            chunk = informations[chunkcol]
            if (getchunkid(chunk) == chkid) or (getchunkid(chunk) == I and chkid in [B,I]):
                tokens.append(informations[0])
                POS_seq.append(pos)
            else:
                result += (u"" if result == u"" else u" ") + to_string_POS(tokens, POS_seq, chkid)
                del tokens[:]
                del POS_seq[:]
                tokens.append(informations[0])
                POS_seq.append(pos)
                chkid = getchunkid(chunk)
            if informations == paragraph[-1]:
                result += u" " + to_string_POS(tokens, POS_seq, chkid)
                del tokens[:]
                del POS_seq[:]
        outc.write_l([result.strip()])
        result = u""

def getchunkid(chunk):
    return (chunk[2:] if (chunk[:2]==(u'B-') or chunk[:2]==(u'I-')) else chunk) # trimming "B-" or "I-" if necessary

def to_string(tokens, chkid):
    res = u" ".join(tokens)
    if chkid in O:
        return res
    else:
        pref = u"("
        if chkid not in [B,I]:
            pref += chkid + " "
        res = pref + res + u")"
        return res

def to_string_POS(tokens, POS, chkid):
    res = u" ".join([token + u"/" + tag for token,tag in zip(tokens,POS)])
    if chkid in O:
        return res
    else:
        pref = u"("
        if chkid not in [B,I]:
            pref += chkid + " "
        res = pref + res + u")"
        return res

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
