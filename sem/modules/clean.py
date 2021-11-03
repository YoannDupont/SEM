# -*- coding: utf-8 -*-

"""
file: clean.py

Description: remove unwanted fields from a CoNLL-formatted input.

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

import argparse

from sem.util import ranges_to_set
import sem.logger


def main(argv=None):
    clean(**vars(parser.parse_args(argv)))


def clean(
    infile, outfile, ranges, ienc=None, oenc=None, enc="utf-8", log_level="WARNING", log_file=None
):
    """
    Cleans a CoNLL-formatted file, removing fields at given indices.

    Parameters
    ----------
    infile : str
        the name of the file to clean.
    outfile : str
        the name of the output file, where some columns have been removed.
    ranges : str
        the fields to remove. Fields is a coma-separated list of indices
        or ranges of indices using a python format (ie: "lo:hi").
    """

    if log_file is not None:
        sem.logger.addHandler(sem.logger.file_handler(log_file))
    sem.logger.setLevel(log_level)

    ienc = ienc or enc
    oenc = oenc or enc

    allowed = ranges_to_set(
        ranges,
        len(open(infile, "rU", encoding=ienc).readline().strip().split()),
        include_zero=True,
    )
    max_abs = 0
    for element in allowed:
        element = abs(element) + (1 if element > 0 else 0)
        max_abs = max(max_abs, element)
    nelts = len(open(infile, "rU", encoding=ienc).readline().strip().split())

    if nelts < max_abs:
        sem.logger.error(
            'asked to keep up to {0} field(s), yet only {1} are present in the "{2}"'.format(
                max_abs, nelts, infile
            )
        )
        raise RuntimeError(
            'asked to keep up to {0} field(s), yet only {1} are present in the "{2}"'.format(
                max_abs, nelts, infile
            )
        )

    sem.logger.info('cleaning "{0}"'.format(infile))
    sem.logger.info(
        "keeping columns: {0}".format(", ".join([str(s) for s in sorted(allowed)]))
    )
    sem.logger.info('writing "{0}"'.format(outfile))

    with open(outfile, "w", encoding=oenc) as output_stream:
        for line in open(infile, "rU", encoding=ienc):
            line = line.strip().split()
            if line != []:
                tokens = [line[i] for i in range(len(line)) if i in allowed]
                output_stream.write("\t".join(tokens))
            output_stream.write("\n")

    sem.logger.info("done")


parser = argparse.ArgumentParser("Remove unwanted columns from CoNLL-formatted file.")

parser.add_argument("infile", help="The input file")
parser.add_argument("outfile", help="The output file ")
parser.add_argument("ranges", help="The ranges of indexes to keep in the file.")
parser.add_argument("--input-encoding", dest="ienc", help="Encoding of the input (default: UTF-8)")
parser.add_argument("--output-encoding", dest="oenc", help="Encoding of the input (default: UTF-8)")
parser.add_argument(
    "--encoding",
    dest="enc",
    default="UTF-8",
    help="Encoding of both the input and the output (default: UTF-8)",
)
parser.add_argument(
    "-l",
    "--log",
    dest="log_level",
    choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
    default="WARNING",
    help="Increase log level (default: critical)",
)
parser.add_argument("--log-file", dest="log_file", help="The name of the log file")
