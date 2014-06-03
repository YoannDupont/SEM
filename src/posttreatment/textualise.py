#! /usr/bin/python
# -*- coding: utf-8 -*-

#-------------------------------------------------------------------------------
#
# file: textualise.py
#
# Description: write the output of a wapiti labeled file into sentences.
# Each sentence is written on a single line and every sentence is spaced
# by an empty line.
# At the moment, this program allows to "sentencify" POS and chunking tagged
# files. POS tags should be given in a file that is a python evaluable list and
# the chunks should have the following construction : B-<<ID>> when the tag
# marks the beginning of a chunk and I-<<ID>> when the tag marks the
# continuation of the chunk. The end is not marked explicitly as the beginning
# of a new chunk is the end of the preceeding one.
# However, if another marking is used or even none, each different tag will be
# considered as the identifier of a chunk.
#
# author: Yoann Dupont
# copyright (c) 2012 Yoann Dupont - all rights reserved
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#-------------------------------------------------------------------------------

import os, os.path, sys, string, time

from obj.corpus import ICorpus, OCorpus
from obj.logger import log

B = u"B"
I = u"I"
O = u"O0"

def textualise(inputfile, outputfile,
               pos_column=0, chunk_column=0,
               ienc="utf-8", oenc="utf-8", verbose=False):
    
    assert(pos_column != chunk_column or pos_column == 0)
    
    if verbose:
        log('Textualising "%s"...' %inputfile)
    
    incorpus = ICorpus(inputfile)
    outcorpus = OCorpus(outputfile)
    
    if pos_column != 0 and chunk_column != 0:   # doing both POS and CHUNKING
        textualise_posandchunk(incorpus, outcorpus, pos_column, chunk_column)
    elif pos_column != 0:                   # doing only POS
        textualise_pos(incorpus, outcorpus, 1)
    elif chunk_column != 0:               # doing only chunk
        textualise_chunk(incorpus, outcorpus, 1)
    else:
        log("\n/!\ Both POS and chunk are 0, not doing anything...\n")
    
    if verbose:
        log(' Done.\n')

def textualise_pos(incorpus, outc, poscol):
    for paragraph in incorpus:
        outc.put_concise( [u" ".join( [u"/".join( [line.split()[0]] + [line.split()[poscol]] ) for line in paragraph] )])

def textualise_chunk(incorpus, outc, chunkcol):
    chkid = u""
    result = u""
    tokens = []
    for paragraph in incorpus:
        chkid = getchunkid(paragraph[0].split()[chunkcol])
        for line in paragraph:
            informations = line.split()
            chunk        = informations[chunkcol]
            if (getchunkid(chunk) == chkid) or (getchunkid(chunk) == I and chkid in [B,I]):
                tokens.append(informations[0])
            else:
                result += (u"" if result == u"" else u" ") + to_string(tokens, chkid)
                del tokens[:]
                tokens.append(informations[0])
                chkid = getchunkid(chunk)
        if line == paragraph[-1]:
            result += u" " + to_string(tokens, chkid)
            del tokens[:]
        outc.put([result])
        result = u""

def textualise_posandchunk(incorpus, outc, poscol, chunkcol):
    chkid   = u""
    result  = u""
    tokens  = []
    POS_seq = []
    for paragraph in incorpus:
        chkid = getchunkid(paragraph[0].split()[chunkcol])
        for line in paragraph:
            informations = line.split()
            pos          = informations[poscol]
            chunk        = informations[chunkcol]
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
        if line == paragraph[-1]:
            result += u" " + to_string_POS(tokens, POS_seq, chkid)
            del tokens[:]
            del POS_seq[:]
        outc.put([result])
        result = u""

def getchunkid(chunk):
    return (chunk[2:] if (chunk[0:2]==(u'B-') or chunk[0:2]==(u'I-')) else chunk) # trimming "B-" or "I-" if necessary

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
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true",
                        help="Basic feedback for user (default: False).")

    if not __package__:
        parser = parser.parse_args()
    else:
        parser = parser.parse_args(sys.argv[2:])
    
    textualise(parser.input, parser.output,
               pos_column=parser.pos_column, chunk_column=parser.chunk_column,
               ienc=parser.ienc or parser.enc, oenc=parser.oenc or parser.enc,
               verbose=parser.verbose)
    sys.exit(0)
