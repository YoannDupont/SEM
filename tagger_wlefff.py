#! /usr/bin/python

from corpus import ICorpus, OCorpus
import time, random, os, subprocess

def log(msg):
	sys.stdout.write(msg)
	sys.stdout.flush()

def tagger(infile,
           lefff_pickled=None, tagfile=None,
           outfile=None, model=None,
           input_encoding="UTF-8", output_encoding="UTF-8",
		  quiet=False):
    
    if not lefff_pickled:
        lefff_pickled = u'lefff_pickled'
    if not os.path.exists(lefff_pickled):
        raise RuntimeError(u'file not found: %s' %lefff_pickled)
    if not tagfile:
        tagfile = u'tag_list'
    if not os.path.exists(tagfile):
        raise RuntimeError(u'file not found: %s' %tagfile)
    if not model:
        model = u'model'
    if not os.path.exists(model):
        raise RuntimeError(u'file not found: %s' %model)
    if not outfile:
        outfile = u'out'

    
    random_name = generateRandomName()
    random_informed = random_name+u"informed"
    random_lefff = random_informed+u"lefff"
    random_out = random_name+u"out"
    
    temp_incorpus1 = ICorpus(infile,input_encoding)
    temp_outcorpus1 = OCorpus(random_name,output_encoding)
    
    segmentation(temp_incorpus1,temp_outcorpus1,input_encoding,output_encoding)
    if not quiet:
        log("Segmentation done successfuly... Preparing the file...\n")
    
    #calling the different processes recquiered
    prc1 = subprocess.Popen(['python', 'addInformations.py',random_name,'-o',random_informed,'--encoding',output_encoding,'--no-tag','--quiet'])
    prc1.wait()
    prc2 = subprocess.Popen(['python', 'lefffExtractPickled.py',lefff_pickled,'-i',random_informed,'-o',random_lefff,'--tag-list',tagfile,'--encoding',output_encoding,'--no-tag','--quiet'])
    prc2.wait()
    prc3 = subprocess.Popen(['wapiti','label','-m',model,random_lefff,random_out])
    prc3.wait()
    
    temp_incorpus2 = ICorpus(random_out,input_encoding)
    temp_outcorpus2 = OCorpus(outfile,output_encoding)
    
    outlines = []
    for paragraph in temp_incorpus2:
        for line in paragraph:
            temp = line.split('\t')
            outlines.append(temp[0]+'\t'+temp[-1])
        outlines.append('')
    
    temp_outcorpus2.put(outlines)
    
    #removing temporary files
    if not quiet:
        log("Cleaning files...\n")
    os.remove(random_name)
    os.remove(random_informed)
    os.remove(random_lefff)
    os.remove(random_out)
    
    if not quiet:
        log("Done!\n")


#self explanatory
def segmentation(incorpus,outcorpus,input_encoding,output_encoding):
    dots = u'...'
    punctStrong = [u'.',u'?',u'!']
    punctWeak = [u',',u':',u';',u'(',u')',u'[',u']']
    apostrophe = u"'"
    cl_long = u'-t-' #"-t-on"...
    cl = [u'-je',u'-tu',u'-il',u'-elle',u'-nous',u'-vous',u'-ils',u'-elles',u'-moi',u'-toi',u'-lui',u'-on',u'-ce',u'-le',u'-la',u'-les']
    temp_list = []
    
    #first for "..."
    for a in incorpus:
        for b in a:
            cut = b.split()
            for elt in cut:
                if dots in elt:
                    temp_list.extend([elt[:-len(dots)],dots,u''])
                else:
                    temp_list.append(elt)
    cut = list(temp_list)
    del temp_list[:]
    
    #then for other strong punctuations
    for punct in punctStrong:
        for elt in cut:
            if not dots in elt:
                if punct in elt:
                    if not punct==elt: #e.g. "word?"
                        temp_list.append(elt[:-len(punct)])
                    temp_list.extend([punct,u'']) #e.g. "word !" or continuing "word?"
                else: #e.g. "word" or ""
                    temp_list.append(elt)
            else: # elt=="..."
                temp_list.append(elt)
        cut = list(temp_list)
        del temp_list[:]
    
    #for weak punctuations
    for punct in punctWeak:
        for word in cut:
            if not punct==word:
                temp = word.split(punct)
                if temp[-1]==u'' and len(temp[0])>1: #e.g. "word,"
                    temp[-1] = punct
                else:
                    if temp[0]==u'' and word!=u'': #e.g. "(word"
                        temp[0]=punct
                temp_list.extend(temp)
            else: #e.g. ";"
                temp_list.append(punct)
        cut = list(temp_list)
        del temp_list[:]
    
    #for apostrophes
    for elt in cut:
        if apostrophe in elt:
            if not elt[-1]==apostrophe and u"_" not in elt: #e.g. "d'accord"
                temp = elt.split(apostrophe)
                temp[0] = temp[0] + apostrophe
                temp_list.extend(list(temp))
                del temp[:]
            else: #e.g. "d'"
                temp_list.append(elt)
        else: #no apostrophe
            temp_list.append(elt)
    cut = list(temp_list)
    del temp_list[:]
    
    #for cl_long
    for elt in cut:
        if cl_long in elt:
            temp = elt.split(cl_long)
            temp[-1] = cl_long + temp[-1]
            temp_list.extend(temp)
            del temp[:]
        else:
            temp_list.append(elt)
    cut = list(temp_list)
    del temp_list[:]
    
    #for cl
    for c in cl:
        for elt in cut:
            if not cl_long in elt:
                if elt.endswith(c):
                    temp_list.extend([elt[:-len(c)],c])
                else:
                    temp_list.append(elt)
            else:
                temp_list.append(elt)
        cut = list(temp_list)
        del temp_list[:]
    
    outcorpus.put(cut)


#generates a random file name, because using a python temporary file is not possible
def generateRandomName():
    random_characters = u"azertyuiopqsdfghjklmwxcvbn0123456789"
    random_length = random.randint(15,50)
    random_name = u""
    for i in range(0,random_length):
        random_name += random_characters[random.randint(0,len(random_characters)-1)]
    return random_name


if __name__ == '__main__':
    import optparse, sys
    parser = optparse.OptionParser(
        usage="usage: %prog [options] FILE"
        )
    parser.add_option(
        "--lefff", '-l', dest="lefff_pickled", default=None, metavar="STR",
        help="path/name of the lefff pickle dumped file (default: lefff_pickled)"
        )
    parser.add_option(
        "--tag-list", dest="tagfile", default=None, metavar="STR",
        help="path/basename of the file containing tags (default: ./tag_list)"
        )
    parser.add_option(
        "--out", '-o', dest="outfile", default=None, metavar="STR",
        help="path/name of the out file (default: out)"
        )
    parser.add_option(
        "--model", '-m', dest="model", default=None, metavar="STR",
        help="path/name of the model file (default: ./model)"
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
    tagger(args[0],
          lefff_pickled=options.lefff_pickled, tagfile=options.tagfile,
          outfile=options.outfile, model=options.model,
          input_encoding=options.ienc or options.enc,
          output_encoding=options.oenc or options.enc,
          quiet=options.quiet)
    sys.exit(0)
