#! /usr/bin/python
# -*- coding: utf-8 -*-

#-------------------------------------------------------------------------------
#
# file: sem_tagger.py
#
# Description: evaluates the POS tags of a given text file. It may be
# plain text and thus will have to be segmented or may be so already.
# The program then calls a couple of scripts to add informations
# before using the " wapiti label " command.
#
# author: Yoann Dupont
# copyright (c) 2011 Yoann Dupont - all rights reserved
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

from src.pretreatment.segmentation import Segmentation
from src.pretreatment.addInformations import addInformations
from src.pretreatment.lefffExtractPickled import lefffExtract

from src.posttreatment.textualise import textualise

from src.io.corpus import ICorpus, OCorpus

from src import *

import os, time, random, subprocess

def log(msg):
	sys.stdout.write(msg)
	sys.stdout.flush()

def tagger(infile, outdir=None, segment=False,
           lefff_pickled=None, tagfile=None,
           model=None, code=None,
           clean=False,
           input_encoding="UTF-8", output_encoding="UTF-8",
           no_tag = True, quiet=True):
   
    outfile = u""

    #--------------------------------------------------------------------------#
    #                            exception handling                            #
    #--------------------------------------------------------------------------#
    if not os.path.exists(infile):
        raise RuntimeError(u'file not found: %s' %infile)

    if not outdir:
        outdir = u'./'
    elif not outdir.endswith(u'/'):
        outdir += u'/'
    elif not os.path.exists(outdir):
        raise RuntimeError(u'directory not found: %s' %outdir)

    if lefff_pickled:
        if not os.path.exists(lefff_pickled):
            raise RuntimeError(u"Lefff file not found: %s" %lefff_pickled)

    if not tagfile:
        tagfile = u"./ressources/tag_list"

    models = []
    if not model:
        models = [u"./model"] * code.count("+")
    else:
        models = model.split("+")
        for m in models:
            if not os.path.exists(m):
                raise IOError(u"File not found: %s" %m)

    if code is None:
        code = u"POS"

    code = getcode(code)
    
    if code == CHUNK and no_tag: # the CHUNK tagging may not be done without POST
        tag_list = eval(file(tagfile,"r").readline())
        if file(infile, "r").readline().split()[-1] in tag_list:
            raise ValueError(u"Cannot remove POS when chunking alone !")
    #--------------------------------------------------------------------------#
    #                        end of exception handling                         #
    #--------------------------------------------------------------------------#

    outfile = u""

    incorpus = ICorpus(infile, input_encoding)
    segmented_file = infile
    
    # segmentation of the in file if needed
    if segment:
        if not quiet:
            log(u"Segmentation...")

        segmented_file = outdir + os.path.basename(infile) + u".segment"
        temp_outcorpus = OCorpus(segmented_file, output_encoding)
        sequencer = Segmentation(incorpus, temp_outcorpus)
        sequencer.segmentation()
        if not quiet:
            log(u" Done !\n\n")

    postfile = segmented_file

    if (code & POS) == POS:
        informed = outdir + os.path.basename(infile) + u".informed"
        wapiti_in = informed
        wapiti_out = outdir + os.path.basename(infile) + u".wapiti"
        
        # adding basic informations
        addInformations(segmented_file, informed,
                        input_encoding, output_encoding,
                        no_tag, quiet)
        print

        # adding lefff informations if needed
        if lefff_pickled:
            wapiti_in = outdir + os.path.basename(infile) + ".lefff"
            lefffExtract(lefff_pickled,
                         tagfile, no_tag,
                         informed, wapiti_in,
                         output_encoding, output_encoding,
                         quiet)
            print

        # calling wapiti
        prc3 = subprocess.Popen(['wapiti', 'label', '-m', models[0], wapiti_in, wapiti_out])
        prc3.wait()

        if file(wapiti_out).read(1) == "": # nothing was written by Wapiti, meaning an error has occured
            raise RuntimeError(u"Error: Wapiti could not label the file : " + wapiti_in + ". Check the source of this error using Wapiti.")

        wapiti_corpus = ICorpus(wapiti_out, input_encoding)
        postfile = outdir + os.path.basename(infile) + ".POS"
        POSTagging = OCorpus(postfile, output_encoding)
        lines = [] # will stock the paragraph to be written

        # writing the out file containing the words and their matching tags
        for paragraph in wapiti_corpus:
            for line in paragraph:
                temp = line.split('\t')
                if no_tag:
                    lines.append(temp[0]+'\t'+temp[-1])
                else:
                    lines.append(temp[0]+'\t'+temp[-2]+'\t'+temp[-1])
            POSTagging.put(lines)
            del lines[:]

        outfile = postfile

    if (code & CHUNK) == CHUNK:
        index = (0 if code == CHUNK else 1)

        if index == 1:
            outfile = outdir + os.path.basename(outfile) + u".CHUNK"
        else:
            outfile = outdir + os.path.basename(infile) + u".CHUNK"

        # calling wapiti
        prc4 = subprocess.Popen(['wapiti', 'label', '-m', models[index], postfile, outfile])
        prc4.wait()

        if file(outfile).read(1) == "": # nothing was written by Wapiti, meaning an error has occured
            raise RuntimeError(u"Error: Wapiti could not label the file : " + outfile + ". Check the source of this error using Wapiti.")

    textualise(outfile, None,
               output_encoding, output_encoding,
               code, tagfile,
               quiet)

    if not quiet and clean:
        log("Cleaning files...\n")
    if clean:
        os.remove(segmented_file)
        os.remove(informed)
        if os.path.exists(wapiti_in): # this may be equal to informed
            os.remove(wapiti_in)
        os.remove(wapiti_out)
    if not quiet:
        log("All done !\n")

if __name__ == '__main__':
    import optparse, sys
    parser = optparse.OptionParser(
        usage="usage: %prog [options] FILE"
        )
    parser.add_option(
        "--out", '-o', dest="outdir", default=None, metavar="DIR",
        help="path of the out directory (default: ./)"
        )
    parser.add_option(
        "--segment", '-s', action="store_true", dest="segment", default=False,
        help="segment the given in file"
        )
    parser.add_option(
        "--lefff", '-l', dest="lefff_pickled", default=None, metavar="STR",
        help="path/name of the lefff pickle dumped file. If not given, it is assumed that the lefff is not used"
        )
    parser.add_option(
        "--tag-list", dest="tagfile", default=None, metavar="STR",
        help="path/name of the file containing tags (default: ./ressources/tag_list)"
        )
    parser.add_option(
        "--tag-code", "-t", dest="code", default=None,
        help="POS, CHUNK, etc... Elements should be concatenated with a + if more than one is wanted. ex: POS+CHUNK (default: POS)"
        )
    parser.add_option(
        "--model", '-m', dest="model", default=None, metavar="STR",
        help="path/name of the model file (default: ./model)"
        )
    parser.add_option(
        "--clean", "-c", action="store_true", dest="clean", default=False,
        help="clean all out files except the result"
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
        "--output-encoding", dest="oenc", default="UTF-8", metavar="ENC",
        help="encoding for the output file (the corpus)"
        )
    parser.add_option(
        "--no-tag", action="store_true", dest="no_tag", default=False,
        help="no tag will be read from input file"
        )
    parser.add_option(
        "--quiet", "-q", action="store_true", dest="quiet", default=False,
        help="write no feedback during processing"
        )

    options, args = parser.parse_args()
    if len(args) != 1:
        raise RuntimeError("expected exactly one positional arguments")
    tagger(args[0], outdir=options.outdir, segment=options.segment,
          lefff_pickled=options.lefff_pickled, tagfile=options.tagfile,
          model=options.model, code=options.code,
          clean=options.clean,
          input_encoding=options.ienc or options.enc,
          output_encoding=options.oenc or options.enc,
          no_tag = options.no_tag, quiet=options.quiet)
    sys.exit(0)
