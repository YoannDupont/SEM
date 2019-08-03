# -*- coding: utf-8 -*-

"""
file: compile_dictionary.py

Description: serialize a dictionary written in a file. A dictionary file
is a file where every entry is on one line. There are two kinds of
dictionaries: token and multiword. A token dictionary will apply itself
on single tokens. A multiword dictionary will apply itself on sequences
of tokens.

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

import logging

try:
    import cPickle as pickle
except ImportError:
    import pickle

from sem.logger import default_handler, file_handler
from sem.storage.dictionaries import compile_token, compile_multiword

compile_dictionary_logger = logging.getLogger("sem.compile_dictionary")
compile_dictionary_logger.addHandler(default_handler)

_compile = {
    "token": compile_token,
    "multiword": compile_multiword
}
_choices = set(_compile.keys())

def compile_dictionary(
    infile,
    outfile,
    kind="token",
    ienc="UTF-8",
    log_level=logging.CRITICAL,
    log_file=None
):
    if log_file is not None:
        compile_dictionary_logger.addHandler(file_handler(log_file))
    compile_dictionary_logger.setLevel(log_level)

    if kind not in _choices:
        raise RuntimeError("Invalid kind: {0}".format(kind))

    compile_dictionary_logger.info(
        'compiling {0} dictionary from "{1}" to "{2}"'.format(kind, infile, outfile)
    )

    try:
        dictionary_compile = _compile[kind]
    except KeyError: # invalid kind asked
        compile_dictionary_logger.exception(
            "Invalid kind: {0}. Should be in: {1}".format(kind, ", ".join(_compile.keys()))
        )
        raise

    pickle.dump(dictionary_compile(infile, ienc), open(outfile, "w"))

    compile_dictionary_logger.info("done")


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Takes a dictionary and compiles it in a readable format for the enrich module."
                    " A dictionary is a text file containing one entry per line."
                    " There are two kinds of dictionaries:"
                    " those that only contain entries which apply to a single token (token),"
                    " and those who contain entries which may be applied to sequences of tokens"
                    " (multiword)."
    )

    parser.add_argument("infile",
                        help="The input file (one term per line)")
    parser.add_argument("outfile",
                        help="The output file (pickled file)")
    parser.add_argument("-k", "--kind", choices=_choices, dest="kind", default="token",
                        help="The kind of entries that the dictionary contains"
                             " (default: %(default)s)")
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

    compile_dictionary(
        args.infile,
        args.outfile,
        kind=args.kind,
        ienc=args.ienc,
        log_level=args.log_level,
        log_file=args.log_file
    )
    sys.exit(0)
