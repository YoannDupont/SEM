#-*- coding: utf-8 -*-

"""
file: compile_dictionary.py

Description: serialize a dictionary written in a file. A dictionary file
is a file where every entry is on one line. There are two kinds of
dictionaries: token and multiword. A token dictionary will apply itself
on single tokens. A multiword dictionary will apply itself on sequences
of tokens.

author: Yoann Dupont
copyright (c) 2016 Yoann Dupont - all rights reserved

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import codecs, cPickle, logging

from obj.logger       import default_handler, file_handler
from obj.dictionaries import compile_token, compile_multiword

compile_dictionary_logger = logging.getLogger("sem.compile_dictionary")
compile_dictionary_logger.addHandler(default_handler)

_compile = {"token"    :compile_token,
            "multiword":compile_multiword}
_choices = set(_compile.keys())

def compile_dictionary(infile, outfile, kind="token",
                       ienc="UTF-8",
                       log_level=logging.CRITICAL, log_file=None):
    if log_file is not None:
        compile_dictionary_logger.addHandler(file_handler(log_file))
    compile_dictionary_logger.setLevel(log_level)
    
    if kind not in _choices:
        raise RuntimeError("Invalid kind: %s" %kind)
    
    compile_dictionary_logger.info(u'compiling %s dictionary from "%s" to "%s"' %(kind, infile, outfile))
    
    try:
        dictionary_compile = _compile[kind]
    except KeyError: # invalid kind asked
        compile_dictionary_logger.exception("Invalid kind: %s. Should be in: %s" %(kind, u", ".join(_compile.keys())))
        raise
    
    cPickle.dump(dictionary_compile(infile, ienc), open(outfile, "w"))
    
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
    
    if __package__:
        args = parser.parse_args(sys.argv[2:])
    else:
        args = parser.parse_args()
    
    compile_dictionary(args.infile, args.outfile,
                       kind=args.kind,
                       ienc=args.ienc,
                       log_level=args.log_level, log_file=args.log_file)
    sys.exit(0)
