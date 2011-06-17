#! /usr/bin/python
# -*- coding: utf-8 -*-

from corpus import ICorpus, OCorpus
import os, time, random, subprocess

def log(msg):
	sys.stdout.write(msg)
	sys.stdout.flush()

def tagger(infile, outdir=None, segment=False,
           lefff_pickled=None, tagfile=None,
           model=None, clean=False,
           input_encoding="UTF-8", output_encoding="UTF-8",
           quiet=True):

    if not os.path.exists(infile):
        raise RuntimeError(u'file not found: %s' %infile)
    if not outdir:
        outdir = u'./'
    elif not os.path.exists(outdir):
        raise RuntimeError(u'directory not found: %s' %outdir)
    if lefff_pickled:
        if not os.path.exists(lefff_pickled):
            raise RuntimeError(u"Lefff file not found: %s" %lefff_pickled)
    if not tagfile:
        tagfile = u"./tag_list"
    if not model:
        model = u"./model"

    incorpus = ICorpus(infile,input_encoding)
    segmented_file = infile

    # segmentation of the in file if needed
    if segment:
        if not quiet:
            log(u"Segmentation...")
        segmented_file = outdir + os.path.basename(infile) + u"_segment"
        temp_outcorpus = OCorpus(segmented_file, output_encoding)
        segmentation(incorpus, temp_outcorpus)
        if not quiet:
            log(u" Done ! \n")

    informed = outdir + os.path.basename(infile) + u"_informed"
    wapiti_in = informed
    wapiti_out = outdir + u"wapiti_out"

    # adding basic informations
    prc1 = subprocess.Popen(['python', 'addInformations.py', segmented_file, '-o', informed, '--input-encoding', input_encoding, '--output-encoding', output_encoding, '--no-tag', '--quiet'])
    prc1.wait()

    # adding lefff informations if needed
    if lefff_pickled:
        wapiti_in = outdir + os.path.basename(infile) + "_lefff"
        prc2 = subprocess.Popen(['python', 'lefffExtractPickled.py', lefff_pickled, '-i', informed, '-o', wapiti_in, '--tag-list', tagfile, '--encoding', output_encoding, '--no-tag', '--quiet'])
        prc2.wait()

    # calling wapiti
    prc3 = subprocess.Popen(['wapiti', 'label', '-m', model, wapiti_in, wapiti_out])
    prc3.wait()

    wapiti_corpus = ICorpus(wapiti_out, input_encoding)
    outfile = outdir + os.path.basename(infile) + "_out"
    outcorpus = OCorpus(outfile, output_encoding)
    outlines = []

    # writing the out file containing the words and their matching tags
    for paragraph in wapiti_corpus:
        for line in paragraph:
            temp = line.split('\t')
            outlines.append(temp[0]+'\t'+temp[-1])
        outlines.append('')

    outcorpus.put(outlines)

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


def segmentation(incorpus, outcorpus):

    for line in incorpus:
        the_line = line[0].strip().split() # splitting the line in tokens
        sentence = "" # the sentence to be written
        current_position = 0
        EOL = False # end of line
        opening_char_count = 0

        while not EOL:

            if isOpeningChar(the_line[current_position][0]): # the token starts with an opening character
                opening_char_count += 1
                if isClosingChar(the_line[current_position][-1]): # the token ends with a closing character
                    opening_char_count -= 1
                    sentence += u" " + the_line[current_position][0] + u" " + the_line[current_position][1:-1] + u" " + the_line[current_position][-1]
                elif isChar(the_line[current_position]):
                    sentence += u" " + the_line[current_position]
                else:
                    sentence += u" " + the_line[current_position][0] + u" " + the_line[current_position][1:]

            elif isClosingChar(the_line[current_position][-1]): # the token ends with a closing character
                opening_char_count -= 1
                if isChar(the_line[current_position]):
                    sentence += u" " + the_line[current_position]
                else:
                    sentence += u" " + the_line[current_position][:-1] + u" " + the_line[current_position][-1]

            elif isStrongPunct(the_line[current_position]): # the token ends with a strong punctuation
                sentence += u" " + the_line[current_position]
                if opening_char_count == 0:
                    outcorpus.put(sentence.split())
                    sentence = ""

            elif isWeakPunct(the_line[current_position][-1]): # the token ends with a weak punctuation
                sentence += u" " + the_line[current_position][:-1] + u" " + the_line[current_position][-1]

            elif isUnit(the_line[current_position]) != -1: # the token is a number with an unit at its start or at its end
                index = isUnit(the_line[current_position])
                sentence += u" " + the_line[current_position][0 : index] + u" " + the_line[current_position][index : len(the_line[current_position])]

            elif the_line[current_position][-1] == u".": # the token ends with a dot
                token = the_line[current_position]
                if (isAcronym(token)) or (isAbbreviationBeforeNoun(token)):
                    sentence += u" " + token
                elif not current_position == (len(the_line) - 1): # the token is not the last token of the line
                    next_token = the_line[current_position+1]
                    sentence += u" " + token[:-1] + u" " + token[-1]
                    if next_token[0].isupper(): # the next token starts with an upper case character
                        if opening_char_count == 0:
                            outcorpus.put(sentence.split())
                            sentence = ""
                else: # the dot marks the end of the sentence
                    sentence += u" " + token[:-1] + u" " + token[-1]
                    if opening_char_count == 0:
                        outcorpus.put(sentence.split())
                        sentence = ""

            else: # any other case : the token is added
                #if not opening_char_count > 0:
                #    sentence += u" " + the_line[current_position]
                sentence += u" " + the_line[current_position]

            current_position += 1
            EOL = current_position >= len(the_line)

            if EOL and sentence != u"":
                outcorpus.put(sentence.split())


def isChar(s):
    return len(s) == 1


def isOpeningChar(s):
    opening_chars = u"([{«"
    
    if isChar(s):
        return opening_chars.find(s) != -1
    else:
        return False


def isClosingChar(s):
    closing_chars = u")]}»"
    
    if isChar(s):
        return closing_chars.find(s) != -1
    else:
        return False


# '.' is not considered as a strong punctuation
# because it can be used to other purposes.
def isStrongPunct(s):
    strong_puncts = u"?!…"
    
    if isChar(s):
        return strong_puncts.find(s) != -1
    else:
        return s == u"..."


def isWeakPunct(s):
    weak_puncts = u",:;"
    
    if isChar(s):
        return weak_puncts.find(s) != -1
    else:
        return False


def isAbbreviationBeforeNoun(token):
    abbr_list = [u"mme.", u"mmes.", u"melle.", u"melles.", u"mlle.", u"mlles.", u"m.", u"mr.", u"me.", u"mrs.", u"st."]

    return abbr_list.count(token.lower()) != 0


# A token is a unit if:
#  | it start by letter(s) and ends with number(s)
#  | it start by number(s) and ends with number(s)
#  | and the numbers and letters are not "mixed"
# if the token is not a unit, the returned inex is -1
def isUnit(token):
    left = token.lstrip(u"0123456789")
    right = token.rstrip(u"0123456789")

    if len(left) < len(token):
        for C in left:
            if C.isdigit():
                return -1
        return len(token) - len(left)
    elif len(right) < len(token):
        for C in right:
            if C.isdigit():
                return -1
        return len(right)
    else:
        return -1


def isAcronym(token):
    return token.count(u".") > 1 or token.replace(".","").isupper()


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
        help="path/name of the file containing tags (default: ./tag_list)"
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
        "--quiet", "-q", action="store_true", dest="quiet", default=False,
        help="write no feedback during processing"
        )

    options, args = parser.parse_args()
    if len(args) != 1:
        raise RuntimeError("expected exactly one positional arguments")
    tagger(args[0], outdir=options.outdir, segment=options.segment,
          lefff_pickled=options.lefff_pickled, tagfile=options.tagfile,
          model=options.model, clean=options.clean,
          input_encoding=options.ienc or options.enc,
          output_encoding=options.oenc or options.enc,
          quiet=options.quiet)
    sys.exit(0)
