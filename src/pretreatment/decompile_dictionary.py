import codecs, cPickle, logging

from obj.logger import logging_format

compile_dictionary_logger = logging.getLogger("sem.decompile_dictionary")

# in token dictionaries, one entry = one token
def _entry_token(token):
    return token

# in multiword dictionaries, one entry = multiple tokens
def _entry_multiword(tokens):
    return u" ".join(tokens)

_entry   = {"token"    :_entry_token,
            "multiword":_entry_multiword}
_choices = set(_entry.keys())

def decompile_dictionary(infile, outfile, kind="token",
                         oenc="UTF-8",
                         log_level=logging.CRITICAL, log_file=None):
    file_mode = u"a"
    if type(log_file) in (str, unicode):
        file_mode = u"w"
    logging.basicConfig(level=log_level, format=logging_format, filename=log_file, filemode=file_mode)
    
    if kind not in _choices:
        raise RuntimeError("Invalid kind: %s" %kind)
    
    compile_dictionary_logger.info(u'compiling %s dictionary from "%s" to "%s"' %(kind, infile, outfile))
    
    resource = cPickle.load(open(infile))
    entry    = _entry[kind]
    with codecs.open(outfile, "w", oenc) as O:
        tokens = []
        for token in resource:
            tokens.append(token[:])
        for token in sorted(tokens):
            O.write(entry(token) + u"\n")
    
    compile_dictionary_logger.info(u"done")



if __name__ == "__main__":
    import argparse, sys
    
    parser = argparse.ArgumentParser(description="Takes a dictionary and compiles it in a readable format for the enrich module. A dictionary is a text file containing one entry per line. There are to kinds of dictionaries: those that only contain entries which apply to a single token (token), and those who contain entries which may be applied to sequences of tokens (multiword).")
    
    parser.add_argument("infile",
                        help="The input file (one term per line)")
    parser.add_argument("outfile",
                        help="The output file (pickled file)")
    parser.add_argument("-k", "--kind", choices=_choices, dest="kind", default="token",
                        help="The kind of entries that the dictionary contains (default: %(default)s)")
    parser.add_argument("-o", "--output-encoding", dest="oenc", default="utf-8",
                        help="Encoding of the output (default: %(default)s)")
    parser.add_argument("-l", "--log", dest="log_level", action="count",
                        help="Increase log level (default: critical)")
    parser.add_argument("--log-file", dest="log_file",
                        help="The name of the log file")
    
    arguments = (sys.argv[2:] if __package__ else sys.argv)
    parser    = parser.parse_args(arguments)
    
    decompile_dictionary(parser.infile, parser.outfile,
                         kind=parser.kind,
                         oenc=parser.oenc,
                         log_level=parser.log_level, log_file=parser.log_file)
    sys.exit(0)
