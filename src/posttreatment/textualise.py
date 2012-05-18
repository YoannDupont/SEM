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

from .. import *

def log(msg):
	sys.stdout.write(msg)
	sys.stdout.flush()

def textualise(inc, outcorpus=None,
               input_encoding="utf-8", output_encoding="utf-8",
               code=None, tagfile=None,
               quiet=False):

    #--------------------------------------------------------------------------#
    #                            exception handling                            #
    #--------------------------------------------------------------------------#
    if not os.path.exists(inc):
        raise IOError(u"File not found : " + inc)

    if outcorpus is None:
        outcorpus = inc + u".textualised"
    outcorpus = OCorpus(outcorpus)

    if tagfile is None:
        tagfile = "./ressources/tag_list"
    if not os.path.exists(tagfile):
        raise IOError(u"File not found : " + tagfile)

    tag_list = eval(file(tagfile,"r").readline())
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
        outc.put( [u" ".join( [u"/".join( [line.split()[0]] + [line.split()[poscol]] ) for line in paragraph] )] )

def textualize_chunk(inc, outc, poscol):
    chkid = u""
    current = u"("
    for paragraph in inc:
        chkid = getchunkid(paragraph[0].split()[-1])
        for line in paragraph:
            if getchunkid(line.split()[-1]) == chkid:
                current += (u" " if len(current)!=1 else u"") + line.split()[0]
            else:
                current += u")" + chkid + u" (" + line.split()[0]
                chkid = getchunkid(line.split()[-1])
                if line == paragraph[-1]:
                    current += ")" + chkid
        outc.put([current])
        current = u"("

def textualize_posandchunk(inc, outc):
    chkid = u""
    current = u"("
    for paragraph in inc:
        chkid = getchunkid(paragraph[0].split()[-1])
        for line in paragraph:
            if getchunkid(line.split()[-1]) == chkid:
                current += (u" " if len(current)!=1 else u"") + u"/".join(getchunkid(line.split()))
            else:
                current += u")" + chkid + u" (" + u"/".join(getchunkid(line.split()))
                chkid = getchunkid(line.split()[-1])
                if line == paragraph[-1]:
                    current += ")" + chkid
        outc.put([current])
        current = u"("

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
        "--code", "-c", dest="code", default=None,
        help="POS, CHUNK, etc... Elements should be concatenated with a + if more than one is wanted (ex: POS+CHUNK)"
        )
    parser.add_option(
        "--tag-list", dest="tagfile", default=None, metavar="STR",
        help="path/basename of the file containing tags (default: ressources/tag_list)"
        )
    parser.add_option(
        "--encoding", dest="enc", default="UTF-8", metavar="ENC",
        help="encoding to use for input and output unless overriden (default: UTF-8)"
        )
    parser.add_option(
        "--input-encoding", dest="ienc", default=None, metavar="ENC",
        help="encoding for the input file (the corpus)"
        )
    parser.add_option(
        "--output-encoding", dest="oenc", default=None, metavar="ENC",
        help="encoding for the output file"
        )
    parser.add_option(
        "--quiet", "-q", action="store_true", dest="quiet", default=False,
        help="write no feedback during processing"
        )

    options, args = parser.parse_args()
    if len(args) != 1:
        raise RuntimeError("expected exactly one positional argument")
    textualise(args[0], outcorpus=options.outcorpus,
		   input_encoding=options.ienc or options.enc,
		   output_encoding=options.oenc or options.enc,
           code=options.code, tagfile=options.tagfile,
		   quiet=options.quiet)
    sys.exit(0)
