#-*- coding: utf-8 -*-

"""
file: compile_dictionary.py

Description: 

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
    
    if __package__:
        args = parser.parse_args(sys.argv[2:])
    else:
        args = parser.parse_args()
    
    compile_dictionary(args.infile, args.outfile,
                       kind=args.kind,
                       ienc=args.ienc,
                       log_level=args.log_level, log_file=args.log_file)
    sys.exit(0)
