from obj.tree        import Tree, BooleanNode, ListNode
from obj.information import Informations
from obj.corpus      import ICorpus, OCorpus
from obj.logger      import log

def enrich(infile, infofile, outfile,
           ienc="UTF-8", oenc="UTF-8", verbose=False):
    info    = Informations(infofile)
    icorpus = ICorpus(infile, ienc)
    ocorpus = OCorpus(outfile, oenc)
    
    if verbose:
        log('Enriching file "%s"...\n' %infile)

    l   = mkentry(icorpus, info.bentries() + info.aentries())
    fmt = "\t".join(["%(" + entry + ")s" for entry in info.bentries()])

    if verbose:
        log("Loading endogene traits...")
    for endo in info.endogenes():
        l    = add(l, endo)
        fmt += "\t%(" + endo.get_name() + ")s"
    if verbose:
        log(" Done.\n")

    if verbose:
        log("Loading exogene traits...")
    for exo in info.exogenes():
        l    = add(l, exo)
        fmt += "\t%(" + endo.get_name() + ")s"
    if verbose:
        log(" Done.\n")
    
    if info.aentries() != []:
        fmt += "\t" + "\t".join(["%(" + entry + ")s" for entry in info.aentries()])

    if verbose:
        log("Outputting...")
    for sent in l:
        ocorpus.putformat(sent, fmt)
    if verbose:
        log(" Done.\n")

def add(corpus, endo):
    def to_pseudo_boolean_if_possible(string):
        s = string.lower()
        return ("1" if s=="true" else "0" if s=="false" else string)

    name = endo.get_name()
    for sent in corpus:
        token = []
        for i in xrange(len(sent)):
            enriched = dict(sent[i])
            enriched[name] = to_pseudo_boolean_if_possible(endo.eval(sent, i))
            token.append(enriched)
        yield token

def addSequence(corpus, trait):
    """
    multi-words dictionaries are "recursive" dictionaries which form a prefix
    tree. Each word is a key of the dictionary and the depth of the tree is the
    nth word in the multi-word entity.
    There is a match when the empty string key is found. Currently, the shortest
    matching entity is used.
    """
    
    name     = trait.get_name()
    resource = trait.value()
    NUL      = u""
    
    if not resource:
        for sent in it:
            l = []
            for token in sent:
                y = dict(token)
                y[name] = u'O'
                l.append(y)
            yield l
    
    for sent in it:
        tmp       = resource
        l         = [dict(elt) for elt in sent]
        length    = len(sent)
        fst       = 0
        cur       = 0
        criterion = False
        ckey      = None

        while not criterion:
            cont = True
            while cont and (cur < length):
                if (NUL not in tmp):
                    ckey = sent[cur][u"Word"]
                    
                    if (ckey in tmp):
                        tmp = tmp[ckey]
                        cur += 1
                    else:
                        cont = False
                else:
                    cont = False
            
            if NUL in tmp:
                l[fst][name] = u'B-' + tmp[NUL]
                for i in xrange(fst+1, cur):
                    l[i][name] = u'I-' + tmp[NUL]
                fst = cur
            else:
                l[fst][name] = u'O'
                fst += 1
                cur = fst
            tmp = resource

            criterion = fst >= length - 1

        if not name in l[-1].keys():
            l[-1][name] = u'O'
        yield l

def mkentry(it, cols):
    for x in it:
        lines = []
        for l in x:
            l2 = {}
            for c,v in zip(cols, l.split()):
                l2[c] = v
            lines.append(l2)
        yield lines
    



if __name__ == "__main__":
    import argparse, sys

    parser = argparse.ArgumentParser(description="Adds information to a file using and XML-styled configuration file.")

    parser.add_argument("infile",
                        help="The input file (CoNLL format)")
    parser.add_argument("infofile",
                        help="The information file (XML format)")
    parser.add_argument("outfile",
                        help="The output file (CoNLL format)")
    parser.add_argument("--input-encoding", dest="ienc",
                        help="Encoding of the input (default: UTF-8)")
    parser.add_argument("--output-encoding", dest="oenc",
                        help="Encoding of the input (default: UTF-8)")
    parser.add_argument("--encoding", dest="enc", default="UTF-8",
                        help="Encoding of both the input and the output (default: UTF-8)")
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true",
                        help="Basic feedback for user (default: False).")
    
    arguments = (sys.argv[2:] if __package__ else sys.argv)
    parser    = parser.parse_args(arguments)
    
    enrich(parser.infile, parser.infofile, parser.outfile,
           ienc=parser.ienc or parser.enc, oenc=parser.oenc or parser.enc, verbose=parser.verbose)
    sys.exit(0)
