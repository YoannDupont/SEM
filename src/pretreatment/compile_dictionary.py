import codecs, cPickle, logging

from obj.logger       import logging_format
from obj.dictionaries import compile_token, compile_multiword

compile_dictionary_logger = logging.getLogger("sem.compile_dictionary")

_compile = {"token"    :compile_token,
            "multiword":compile_multiword}
_choices = set(_compile.keys())

def compile_dictionary(infile, outfile, kind="token",
                       ienc="UTF-8",
                       log_level=logging.CRITICAL, log_file=None):
    file_mode = u"a"
    if type(log_file) in (str, unicode):
        file_mode = u"w"
    logging.basicConfig(level=log_level, format=logging_format, filename=log_file, filemode=file_mode)
    
    if kind not in _choices:
        raise RuntimeError("Invalid kind: %s" %kind)
    
    compile_dictionary_logger.info(u'compiling %s dictionary from "%s" to "%s"' %(kind, infile, outfile))
    
    compile = _compile[kind]
    cPickle.dump(compile(infile, ienc), open(outfile, "w"))
    
    compile_dictionary_logger.info(u"done")



if __name__ == "__main__":
    import argparse, sys
    
    parser = argparse.ArgumentParser(description="Takes a dictionary and compiles it in a readable format for the enrich module. A dictionary is a text file containing one entry per line. There are two kinds of dictionaries: those that only contain entries which apply to a single token (token), and those who contain entries which may be applied to sequences of tokens (multiword).")
    
    parser.add_argument("infile",
                        help="The input file (one term per line)")
    parser.add_argument("outfile",
                        help="The output file (pickled file)")
    parser.add_argument("-k", "--kind", choices=_choices, dest="kind", default="token",
                        help="The kind of entries that the dictionary contains (default: %(default)s)")
    parser.add_argument("-i", "--input-encoding", dest="ienc", default="utf-8",
                        help="Encoding of the input (default: %(default)s)")
    parser.add_argument("-l", "--log", dest="log_level", action="count",
                        help="Increase log level (default: critical)")
    parser.add_argument("--log-file", dest="log_file",
                        help="The name of the log file")
    
    arguments = (sys.argv[2:] if __package__ else sys.argv)
    parser    = parser.parse_args(arguments)
    
    compile_dictionary(parser.infile, parser.outfile,
                       kind=parser.kind,
                       ienc=parser.ienc,
                       log_level=parser.log_level, log_file=parser.log_file)
    sys.exit(0)
