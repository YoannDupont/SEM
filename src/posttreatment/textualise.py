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

from ..io.corpus import ICorpus, OCorpus

from ..config.configParser import *

from .. import *

B = u"B"
I = u"I"
O = u"O0"

def log(msg):
	sys.stdout.write(msg)
	sys.stdout.flush()

def textualise(inc, outcorpus=None,
               configfile=None):

    #--------------------------------------------------------------------------#
    #                            exception handling                            #
    #--------------------------------------------------------------------------#
    if not os.path.exists(inc):
        raise IOError(u"File not found : " + inc)

    if not configfile:
        configfile = u"../../resources/config.default"
    if not os.path.exists(configfile):
        raise IOError(u"File not found : " + configfile)
    C = Config(configfile)

    if outcorpus is None:
        outcorpus = inc + u".textualised"
    outcorpus = OCorpus(outcorpus)

    code = getcode(C.code)
    tag_list = C.pos_tags

    inc = ICorpus(inc)
    index, found = getposcol(inc, tag_list)
    
    if not found:
        raise RuntimeError(u"None of the tags in " + tagfile + " were found.")
    #--------------------------------------------------------------------------#
    #                        end of exception handling                         #
    #--------------------------------------------------------------------------#
    
    if (code & (POS | CHUNK)) == POS + CHUNK:   # doing both POS and CHUNKING
        textualize_posandchunk(inc, outcorpus)
    elif (code & POS) == POS:                   # doing only POS
        textualize_pos(inc, outcorpus, 1)
    elif (code & CHUNK) == CHUNK:               # doing only chunk
        textualize_chunk(inc, outcorpus, 1)

def textualize_pos(inc, outc, poscol):
    for paragraph in inc:
        outc.put_concise( [u" ".join( [u"/".join( [line.split()[0]] + [line.split()[poscol]] ) for line in paragraph] )])

def textualize_chunk(inc, outc, poscol):
    chkid = u""
    result = u""
    tokens = []
    for paragraph in inc:
        chkid = getchunkid(paragraph[0].split()[-1])
        for line in paragraph:
            if (getchunkid(line.split()[-1]) == chkid) or (getchunkid(line.split()[-1]) == I and chkid in [B,I]):
                tokens.append(line.split()[0])
            else:
                result += (u"" if result == u"" else u" ") + to_string(tokens, chkid)
                del tokens[:]
                tokens.append(line.split()[0])
                chkid = getchunkid(line.split()[-1])
        if line == paragraph[-1]:
            result += u" " + to_string(tokens, chkid)
            del tokens[:]
        outc.put([result])
        result = u""

def textualize_posandchunk(inc, outc):
    chkid = u""
    result = u""
    tokens = []
    POS = []
    for paragraph in inc:
        chkid = getchunkid(paragraph[0].split()[-1])
        for line in paragraph:
            if (getchunkid(line.split()[-1]) == chkid) or (getchunkid(line.split()[-1]) == I and chkid in [B,I]):
                tokens.append(line.split()[0])
                POS.append(line.split()[-2])
            else:
                result += (u"" if result == u"" else u" ") + to_string_POS(tokens, POS, chkid)
                del tokens[:]
                del POS[:]
                tokens.append(line.split()[0])
                POS.append(line.split()[-2])
                chkid = getchunkid(line.split()[-1])
        if line == paragraph[-1]:
            result += u" " + to_string_POS(tokens, POS, chkid)
            del tokens[:]
            del POS[:]
        outc.put([result])
        result = u""

# get the POS column as it may not be the last
def getposcol(inc, taglist):
    index = -1
    found = False
    for paragraph in inc:
        for elt in paragraph[0].split():
            index += 1
            if elt in taglist:
                found = True
                break
        break

    inc = ICorpus(inc.filename, inc.encoding)
    return [index, found]

def getchunkid(chunk):
    return (chunk[2:] if (chunk[0:2]==(u'B-') or chunk[0:2]==(u'I-')) else chunk) # trimming "B-" or "I-" if necessary

def to_string(tokens, chkid):
    res = u" ".join(tokens)
    if chkid in O:
        return res
    else:
        res = u"(" + res + u")"
        if chkid not in [B,I]:
            res += chkid
        return res

def to_string_POS(tokens, POS, chkid):
    res = u" ".join([token + u"/" + tag for token,tag in zip(tokens,POS)])
    if chkid in O:
        return res
    else:
        res = u"(" + res + u")"
        if chkid not in [B,I]:
            res += chkid
        return res

if __name__ == '__main__':
    import optparse, sys
    parser = optparse.OptionParser(
        usage="usage: %prog [options] FILENAME"
        )
    parser.add_option(
        "--out", '-o', dest="outcorpus", default=None, metavar="STR",
        help="path/name of the out file (default: FILENAME.textualised). Overwritten if existing."
        )
    parser.add_option(
        "--config-file", '-c', dest="config", default=None, metavar="STR",
        help="Configuration file."
        )

    options, args = parser.parse_args()
    if len(args) != 1:
        raise RuntimeError("expected exactly one positional argument")
    textualise(args[0], outcorpus=options.outcorpus,
               config=options.config)
    sys.exit(0)
