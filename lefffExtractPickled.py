#! /usr/bin/python

import os, os.path, sys, cPickle, time
from corpus import ICorpus, OCorpus

def log(msg):
    sys.stdout.write(msg)
    sys.stdout.flush()


def lefffExtract(dictionary,
                 tagfile=None, no_tag=False,
                 infile=None, outfile=None,
                 input_encoding="UTF-8", output_encoding="UTF-8",
				quiet=False):
    temps = time.time()
    
    #exceptions handling
    if not dictionary:
        dictionary = 'lefff-ext-3.0.txt'
    if not os.path.exists(dictionary):
        raise RuntimeError(u'File not found: %s' %dictionary)
    if not infile:
        infile = u'informed'
    if not os.path.exists(infile):
        raise RuntimeError(u'File not found: %s' %infile)
    if not tagfile:
        tagfile = u'tag_list'
    if not os.path.exists(tagfile):
        raise RuntimeError(u'File not found: %s' %tagfile)
    if not outfile:
        outfile = 'out'
    
    if not quiet:
        log(u'Creating dictionary...\n')
    
    #creating the dictionary with the lefff file given
    lefff_words = cPickle.load(file(dictionary,"r"))
    if not quiet:
        t1 = time.time()-temps
        log('dictionary of single words created in: %ss\n' %str(t1))
    
    incorpus = ICorpus(infile, input_encoding)
    tag_dict,tag_list = TagDictListCouple(tagfile)
    format = formatFromList(tag_list)
    
    outlines = []
    
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
            outlines.append(u'\t'.join(elts))
        outlines.append(u'')
    
    if not quiet:
        log(u'Writing...\n')
    #writing
    out = OCorpus(outfile,output_encoding)
    out.put(outlines)
    if not quiet:
        log(u'\nDone in %ss !\n' % str(time.time()-temps))
            
    
def reinitialize(myDict):
    for key in myDict.keys():
        myDict[key] = 0
    return myDict


def TagDictListCouple(tagfile):
    tag_dict = {}
    tag_list = eval(file(tagfile,"r").readline())
    
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
        "--tag-list", dest="tagfile", default=None, metavar="STR",
        help="path/basename of the file containing tags (default: ./tag_list)"
        )
    parser.add_option(
        "--no-tag", action="store_true", dest="no_tag", default=False,
        help="no tag will be read from input file"
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
        "--encoding", dest="enc", default="UTF-8", metavar="ENC",
        help="encoding to use for input and output unless overriden (default: UTF-8)"
        )
    parser.add_option(
        "--input-encoding", dest="ienc", default=None, metavar="ENC",
        help="encoding for the input file (the corpus)"
        )
    parser.add_option(
        "--output-encoding", dest="oenc", default="UTF-8", metavar="ENC",
        help="encoding for the output file"
        )
    parser.add_option(
        "--quiet", "-q", action="store_true", dest="quiet", default=False,
        help="write no feedback during processing"
        )

    options, args = parser.parse_args()
    if len(args) != 1:
        raise RuntimeError("expected exactly one positional arguments")
    lefffExtract(args[0],
          tagfile=options.tagfile, no_tag=options.no_tag,
          infile=options.infile, outfile=options.outfile,
          input_encoding=options.ienc or options.enc,
          output_encoding=options.oenc or options.enc,
          quiet=options.quiet)
    sys.exit(0)
