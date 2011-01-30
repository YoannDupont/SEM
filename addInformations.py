#! /usr/bin/python
# -*- coding: utf-8 -*-

import os, os.path, sys, string, time
from corpus import ICorpus, OCorpus

def log(msg):
	sys.stdout.write(msg)
	sys.stdout.flush()

def test(incorpus=None,outcorpus=None,
         input_encoding='utf-8',output_encoding='utf-8',
         no_tag=False,
         quiet=False):
    temps = time.time()
    #gestion des cas particuliers
    if not os.path.exists(incorpus):
        raise RuntimeError(u"file not found: %s" % incorpus)
    if not outcorpus:
        path,name = os.path.split(incorpus)
        outcorpus = os.path.join(path,name+'_informed')
    if incorpus==outcorpus:
        raise RuntimeError(u'Files have to be different from one another!')
    #creation des entrees/sorties
    icorpus = ICorpus(incorpus)
    ocorpus = OCorpus(outcorpus)

    if not quiet:
        log(u'Initializing information adding algorithm')
    #ajout des informations
    l = mkentry(icorpus,['Word','Tag'])
    l = addCommenceParMajuscule(l)
    l = addIsDigit(l)
    l = addIsPunct(l)
    l = addNLasts(l,3)
    
    format = u'%(Word)s\t%(CPMaj)s\t%(IsDigit)s\t%(IsPunct)s\t%(3Lasts)s'
    if not no_tag:
        format += u'\t%(Tag)s'
    for a in l:
        ocorpus.putformat(a,format)
        if not quiet:
            log(u'.')
    if not quiet:
        log(u'\nDone in : %ss !\n' %str(time.time()-temps))

def mkentry(it, cols):
    for x in it:
        lines = []
        for l in x:
            l2 = {}
            for c,v in zip(cols, l.split()):
				l2[c] = v
            lines.append(l2)
        yield lines

def addCommenceParMajuscule(it, name='CPMaj'):
    for liste in it:
        l = []
        for element in liste:
            y = dict(element)
            if element["Word"][0].isupper():
                y[name] = '1'
            else:
                y[name] = '0'
            l.append(y)
        yield l

def addIsDigit(it, name="IsDigit"):
    for liste in it:
        l = []
        for element in liste:
            y = dict(element)
            if element["Word"].isdigit():
                y[name] = '1'
            else:
                y[name] = '0'
            l.append(y)
        yield l

def addIsPunct(it, name="IsPunct"):
    for liste in it:
        l = []
        for element in liste:
            ispunct = True
            y = dict(element)
            for e in element["Word"]:
                if e.isalnum():
                    ispunct = False
                    break
            if ispunct:
                y[name] = '1'
            else:
                y[name] = '0'
            l.append(y)
        yield l

def addNLasts(it, n):
    name=('%sLasts' %n)
    for liste in it:
        l = []
        for element in liste:
            y = dict(element)
            y[name] = element["Word"][-n:]
            l.append(y)
        yield l

if __name__ == '__main__':
    import optparse, sys
    parser = optparse.OptionParser(
        usage="usage: %prog [options] CRF++-READABLE-CORPUS"
        )
    parser.add_option(
        "--out", '-o', dest="outcorpus", default=None, metavar="STR",
        help="path/name of the out file (default: basename_informed)"
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
        "--no-tag", action="store_true", dest="no_tag", default=False,
        help="no tag will be read from input file"
        )
    parser.add_option(
        "--quiet", "-q", action="store_true", dest="quiet", default=False,
        help="write no feedback during processing"
        )

    options, args = parser.parse_args()
    if len(args) != 1:
        raise RuntimeError("expected exactly one positional argument")
    test(args[0], outcorpus=options.outcorpus,
		   input_encoding=options.ienc or options.enc,
		   output_encoding=options.oenc or options.enc,
           no_tag=options.no_tag,
		   quiet=options.quiet)
    sys.exit(0)
