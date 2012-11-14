#! /usr/bin/python

#-------------------------------------------------------------------------------
#
# file: lefffExtractPickled.py
#
# Description: add informations extracted from a pickle dumped Lefff file
# to a one that is designed to be used by the software wapiti.
# The extracted informations are added as columns which value can either be
# 0 or 1.
# Each value relates to a POS tag. 0 meaning that the tag does not correspond
# to this word. 1 meaning that it may be the matching tag, because there can
# be more than one column having this value.
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

import os, os.path, sys, cPickle, time

from ..config.configParser import *
from ..io.corpus import ICorpus, OCorpus

def log(msg):
    sys.stdout.write(msg)
    sys.stdout.flush()


def lefffExtract(dictionary,
                 infile=None, outfile=None,
                 configfile=None):
    tlaps = time.time()
    
    #exceptions handling
    if not dictionary:
        dictionary = 'lefff-ext-3.0.txt'
    if type(dictionary) in[str, unicode] and not os.path.exists(dictionary):
        raise IOError(u'File not found: %s' %dictionary)
    if not infile:
        infile = u'informed'
    if not os.path.exists(infile):
        raise IOError(u'File not found: %s' %infile)
    if not outfile:
        outfile = 'out'
    if not configfile:
        configfile = u"../../resources/config.default"
    if not os.path.exists(configfile):
        raise IOError(u"File not found : " + configfile)
    C = Config(configfile)

    quiet = C.quiet
    tag_list = C.pos_tags
    input_encoding = C.input_encoding
    output_encoding = C.output_encoding
    no_tag = not C.has_tagging

    # If dictionary is either string or unicode, then it should be loaded here.
    # Else, it means that it is already loaded and was given in parameter.
    lefff_words = None

    if type(dictionary) in[str, unicode]:
        lefff_words = load_lefff(dictionary, quiet)
    elif type(dictionary) == dict:
        lefff_words = dictionary
        if not quiet:
            log("Dictionary already loaded...\n")
    else:
        raise TypeError("Dictionary is neither a path to a file nor a python dictionary.")


    try:
        incorpus = ICorpus(infile, input_encoding)
    except UnicodeDecodeError:
        incorpus = ICorpus(infile, output_encoding)
    tag_dict,tag_list = TagDictListCouple(tag_list)
    format = formatFromList(tag_list)
    lines = []
    out = OCorpus(outfile,output_encoding)
    
    #writing
    if not quiet:
        log(u'Writing...\n')
    
    for paragraph in incorpus:
        for line in paragraph:
            elts = line.split()
            if no_tag:
                position = len(elts)
            else:
                position = -1

            word = elts[0]
            wordl = word.lower()

            if lefff_words.has_key(word):
                for i in lefff_words[word]: #it is supposed that the dictionary has every key
                    tag_dict[i] = 1
            elif lefff_words.has_key(wordl):
                for i in lefff_words[wordl]: #it is supposed that the dictionary has every key
                    tag_dict[i] = 1

            s = (format %tag_dict)
            reinitialize(tag_dict)
            elts.insert(position,s)
            lines.append(u'\t'.join(elts))

        out.put(lines)
        del lines[:]

    if not quiet:
        log(u'\nDone in %ss !\n' % str(time.time()-tlaps))


def load_lefff(dictionary, quiet):
    tlaps = time.time()
    
    if not quiet:
        log(u'Creating dictionary...\n')
    
    #creating the dictionary with the lefff file given
    lefff_words = cPickle.load(file(dictionary,"r"))
    if not quiet:
        t1 = time.time()-tlaps
        log('dictionary of single words created in: %ss\n' %str(t1))

    return lefff_words
    
def reinitialize(myDict):
    for key in myDict.keys():
        myDict[key] = 0

    return myDict


def TagDictListCouple(tag_list):
    tag_dict = {}
    
    #tag_list is supposed to be correct
    for tag in tag_list:
        tag_dict[tag] = 0
    
    tag_list.sort()
    return [tag_dict,tag_list]


def formatFromList(myList):
    format = u''
    
    for elt in myList:
        format += u'%('+elt+')s\t'
    
    return format[:-1]


#Speaks for itself
def extractInformations(word, lefffwords):
    l = None
    wordl = word.lower() #e.g.: word at the beginning of the sentence will not have a proper casing - also fully capitalized words
    if lefffwords.has_key(word):
        l = lefffwords[word]
    elif lefffwords.has_key(wordl):
        l = lefffwords[wordl]
    return l


if __name__ == '__main__':
    import optparse, sys
    parser = optparse.OptionParser(
        usage="usage: %prog [options] LEFFF-PICKLED"
        )
    parser.add_option(
        "--infile", '-i', dest="infile", default=None, metavar="STR",
        help="path/basename of the corpus (default: ./informed)"
        )
    parser.add_option(
        "--out", '-o', dest="outfile", default=None, metavar="STR",
        help="path/name of the out file (default: out)"
        )
    parser.add_option(
        "--config-file", '-c', dest="config", default=None, metavar="STR",
        help="Configuration file."
        )

    options, args = parser.parse_args()
    if len(args) != 1:
        raise RuntimeError("expected exactly one positional arguments")
    lefffExtract(args[0],
          infile=options.infile, outfile=options.outfile,
          config=options.config)
    sys.exit(0)
