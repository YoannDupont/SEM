#-*- coding: utf-8 -*-

"""
file: decompile_dictionary.py

Description: creates a dictionary file from a serialized dictionary.
A dictionary file is a file where every entry is on one line. There are
two kinds of dictionaries: token and multiword. A token dictionary will
apply itself on single tokens. A multiword dictionary will apply itself
on sequences of tokens.

author: Yoann Dupont

MIT License

Copyright (c) 2018 Yoann Dupont

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import codecs, cPickle, logging

from sem.logger import default_handler

decompile_dictionary_logger = logging.getLogger("sem.decompile_dictionary")
decompile_dictionary_logger.addHandler(default_handler)

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
    if log_file is not None:
        decompile_dictionary_logger.addHandler(file_handler(log_file))
    decompile_dictionary_logger.setLevel(log_level)
    
    if kind not in _choices:
        raise RuntimeError("Invalid kind: {0}".format(kind))
    
    compile_dictionary_logger.info(u'compiling {0} dictionary from "{1}" to "{2}"'.format(kind, infile, outfile))
    
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
    
    if __package__:
        args = parser.parse_args(sys.argv[2:])
    else:
        args = parser.parse_args()
    
    decompile_dictionary(args.infile, args.outfile,
                         kind=args.kind,
                         oenc=args.oenc,
                         log_level=args.log_level, log_file=args.log_file)
    sys.exit(0)
