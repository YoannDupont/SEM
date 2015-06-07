import logging, time

from obj.tree         import Tree, BooleanNode, ListNode, TokenNode, MultiWordNode
from obj.information  import Informations
from obj.corpus       import ICorpus, OCorpus
from obj.logger       import logging_format
from obj.dictionaries import NUL
from obj.misc         import to_dhms

enrich_logger = logging.getLogger("sem.enrich")

def enrich(infile, infofile, outfile,
           ienc="UTF-8", oenc="UTF-8",
           log_level=50, log_file=None):
    start = time.time()
    
    logging.basicConfig(level=log_level, format=logging_format, filename=log_file)
    
    enrich_logger.info('parsing enrichment file "%s"' %infofile)
    
    info    = Informations(infofile)
    icorpus = ICorpus(infile, ienc)
    ocorpus = OCorpus(outfile, oenc)
    
    enrich_logger.info('enriching file "%s"' %infile)

    l   = mkentry(icorpus, info.bentries() + info.aentries(), infile, infofile)
    fmt = "\t".join(["%(" + entry + ")s" for entry in info.bentries()])

    enrich_logger.info("loading endogenous traits")
    for endo in info.endogenous():
        l    = add(l, endo)
        fmt += "\t%(" + endo.get_name() + ")s"
    enrich_logger.info("done")

    enrich_logger.info("loading exogenous traits")
    for exo in info.exogenous():
        if isinstance(exo.root, TokenNode):
            l = add(l, exo)
        elif isinstance(exo.root, MultiWordNode):
            #l = addSequence(l, exo)
            l = addSequenceLongest(l, exo, exo.root.entry)
        else:
            raise RuntimeError('Unknown node type "%s"...' %exo.__class__.__name__)
        fmt += "\t%(" + exo.get_name() + ")s"
    enrich_logger.info("done")
    
    if info.aentries() != []:
        fmt += "\t" + "\t".join(["%(" + entry + ")s" for entry in info.aentries()])

    enrich_logger.info("outputting")
    for sent in l:
        ocorpus.putformat(sent, fmt)
    enrich_logger.info("done in %s", to_dhms(time.time() - start))

def add(corpus, trait):
    def to_pseudo_boolean_if_possible(string):
        if type(string) == bool:
            return unicode(int(string))
        else:
            return string

    name = trait.get_name()
    for sent in corpus:
        token = []
        for i in xrange(len(sent)):
            enriched = dict(sent[i])
            enriched[name] = to_pseudo_boolean_if_possible(trait.eval(sent, i))
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
    resource = trait.root.value
    
    if not resource:
        for sent in corpus:
            l = []
            for token in sent:
                y = dict(token)
                y[name] = u'O'
                l.append(y)
            yield l
    
    for sent in corpus:
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
                    ckey = sent[cur][u"word"]
                    
                    if (ckey in tmp):
                        tmp = tmp[ckey]
                        cur += 1
                    else:
                        cont = False
                else:
                    cont = False
            
            if NUL in tmp:
                l[fst][name] = u'B'
                for i in xrange(fst+1, cur):
                    l[i][name] = u'I'
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

def addSequenceLongest(corpus, trait, column):
    """
    multi-words dictionaries are "recursive" dictionaries which form a prefix
    tree. Each word is a key of the dictionary and the depth of the tree is the
    nth word in the multi-word entity.
    There is a match when the empty string key is found. The longest matching
    entity is used.
    """
    
    name      = trait.get_name()
    resource  = trait.root.value.data
    appendice = trait.root.appendice
    
    if not resource:
        for sent in corpus:
            l = []
            for token in sent:
                y = dict(token)
                y[name] = u'O'
                l.append(y)
            yield l
    
    for sent in corpus:
        tmp       = resource
        l         = [dict(elt) for elt in sent]
        length    = len(sent)
        fst       = 0
        lst       = -1 # last match found
        cur       = 0
        criterion = False # stop criterion
        ckey      = None  # Current KEY
        while not criterion:
            cont = True
            while cont and (cur < length):
                ckey = sent[cur][column]
                if (NUL not in tmp):
                    if (ckey in tmp):
                        tmp  = tmp[ckey]
                        cur += 1
                    else:
                        cont = False
                else:
                    lst  = cur
                    cont = ckey in tmp
                    if cont:
                        tmp  = tmp[ckey]
                        cur += 1
            
            if NUL in tmp:
                l[fst][name] = u'B' + appendice
                for i in xrange(fst+1, cur):
                    l[i][name] = u'I' + appendice
                fst = cur
            elif lst != -1:
                l[fst][name] = u'B' + appendice
                for i in xrange(fst+1, lst):
                    l[i][name] = u'I' + appendice
                fst = lst
            else:
                l[fst][name] = u'O'
                fst += 1
                cur  = fst
            
            tmp       = resource
            lst       = -1
            criterion = fst >= length - 1
        
        if name not in l[-1].keys():
            l[-1][name] = u'O'
        if NUL in resource.get(sent[-1][column], []):
            l[-1][name] = u'B' + appendice
        yield l

def mkentry(it, cols, inputname=None, infoname=None):
    for x in it:
        for l in x:
            fields = l.split()
            break
        break
    if len(fields) < len(cols):
        enrich_logger.error(u'"%s" has %i field(s), yet %i were asked in "%s".' %(inputname, len(fields), len(cols), infoname))
    elif len(fields) > len(cols):
        enrich_logger.warn('in "%s", %i field(s) will be ignored.' %(inputname, len(fields) - len(cols)))
    del fields # the only purpose of this variable is to be able to warn / error, it should not be kept afterwards
    
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
    parser.add_argument("-l", "--log", dest="log_level", action="count",
                        help="Increase log level (default: critical)")
    parser.add_argument("--log-file", dest="log_file",
                        help="The name of the log file")
    
    arguments = (sys.argv[2:] if __package__ else sys.argv)
    parser    = parser.parse_args(arguments)
    
    enrich(parser.infile, parser.infofile, parser.outfile,
           ienc=parser.ienc or parser.enc, oenc=parser.oenc or parser.enc,
           log_level=parser.log_level, log_file=parser.log_file)
    sys.exit(0)
