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
from src.pretreatment.lefffExtractPickled import lefffExtract, load_lefff

from src.posttreatment.textualise import textualise

from src.io.corpus import ICorpus, OCorpus

from src.config.configParser import *

from src import *

import os, time, random, subprocess, codecs, cPickle

def log(msg):
	sys.stdout.write(msg)
	sys.stdout.flush()

def tagger(configfile):

    C = Config(configfile)

    clean = C.clean
    code = C.code
    in_file = C.in_file
    input_encoding = C.input_encoding
    output_encoding = C.output_encoding
    lefff_pickled = C.lefff_file
    model = C.models
    no_tag = not C.has_tagging
    outdir = C.out_directory
    pos_tags = C.pos_tags
    quiet = C.quiet
    segment = C.segmentation

    #--------------------------------------------------------------------------#
    #                            exception handling                            #
    #--------------------------------------------------------------------------#
    if not os.path.exists(in_file):
        raise RuntimeError(u'file not found: %s' %in_file)

    if not outdir:
        outdir = u'./'
    elif not outdir.endswith(u'/'):
        outdir += u'/'
    elif not os.path.exists(outdir):
        raise RuntimeError(u'directory not found: %s' %outdir)

    if lefff_pickled:
        if not os.path.exists(lefff_pickled):
            raise RuntimeError(u"Lefff file not found: %s" %lefff_pickled)

    if code is None:
        code = u"POS"
    code = getcode(code)

    if ((code & POS) == POS and not no_tag) and (not pos_tags or pos_tags == []):
        raise RuntimeError(u"No POS tags given in requiering context.")

    models = []
    if not model:
        raise RuntimeError("No model given in configuration file !")
    else:
        models = model.split("+")
        for m in models:
            if not os.path.exists(m):
                raise IOError(u"File not found: %s" %m)

    # here we check whether it is needed to load the dictionary before-hand.
    # It is the case if the file given in parameter is a directory.
    if os.path.isdir(in_file):
        folder = (C.in_file + u"/" if C.in_file[-1] != u"/" else C.in_file)
        in_file = os.listdir(folder)
        in_file.sort()
        in_file[:] = [folder + elt for elt in in_file]

        if (code & POS) == POS and C.lefff_file is not None:
            lefff_pickled = load_lefff(C.lefff_file, quiet)
    else:
        in_file = [in_file]
    
    if code == CHUNK:
        line = file(in_file[0], "r").readline()
        # the CHUNK tagging may not be done without POST
        if no_tag:
            found = False
            for token in line.split()[1:]:
                if token in pos_tags:
                    found = True
                    break
            if not found:
                raise ValueError(u"Invalid POS tags or file format.")
        else:
            if line.split()[-2] not in pos_tags:
                raise ValueError(u"Invalid POS tags or file format.")
    #--------------------------------------------------------------------------#
    #                        end of exception handling                         #
    #--------------------------------------------------------------------------#

    segmented_file = u""
    informed = u""
    wapiti_in = u""
    wapiti_out = u""
    postfile = u""
    outfile = u""

    for infile in in_file:
        incorpus = ICorpus(infile, input_encoding)
        
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
        else:
            segmented_file = infile

        if (code & POS) == POS:
            informed = outdir + os.path.basename(infile) + u".informed"
            wapiti_in = informed
            wapiti_out = outdir + os.path.basename(infile) + u".wapiti"
            
            # adding basic informations
            addInformations(segmented_file, informed,
                            input_encoding, output_encoding,
                            no_tag, quiet)
            if not quiet:
                print

            # adding lefff informations if needed
            if lefff_pickled:
                wapiti_in = outdir + os.path.basename(infile) + ".lefff"
                lefffExtract(lefff_pickled,
                             informed, wapiti_in,
                             configfile)
                if not quiet:
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

            if index == 0:
                postfile = infile

            if index == 1:
                outfile = outdir + os.path.basename(outfile) + u".CHUNK"
            else:
                outfile = outdir + os.path.basename(infile) + u".CHUNK"

            # calling wapiti
            prc4 = subprocess.Popen(['wapiti', 'label', '-m', models[index], postfile, outfile])
            prc4.wait()

            if no_tag and False:
                temp = outfile + ".TEMP"
                f = codecs.open(temp, "w", output_encoding)
                for line in codecs.open(outfile, "r", output_encoding):
                    l = line.split()
                    f.write(u"\t".join(l[:-2] + l[-1:]))
                    f.write(os.linesep)
                f.close()
                os.rename(temp, outfile)

            if file(outfile).read(1) == "": # nothing was written by Wapiti, meaning an error has occured
                raise RuntimeError(u"Error: Wapiti could not label the file : " + outfile + ". Check the source of this error using Wapiti.")

        textualise(outfile, None,
                   configfile)

        if not quiet and clean:
            log("Cleaning files...\n")
        if clean:
            if os.path.exists(segmented_file) and segmented_file != infile:
                os.remove(segmented_file)
            if os.path.exists(informed):
                os.remove(informed)
            if os.path.exists(wapiti_in):
                os.remove(wapiti_in)
            if os.path.exists(wapiti_out):
                os.remove(wapiti_out)
        if not quiet:
            log("All done !\n")




if __name__ == '__main__':
    import optparse, sys
    parser = optparse.OptionParser(
        usage="usage: %prog CONFIGURATION_FILE"
        )
    options, args = parser.parse_args()
    if len(args) != 1:
        raise RuntimeError("expected exactly one positional arguments")
    tagger(args[0])
    sys.exit(0)
