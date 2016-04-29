#-*- coding:utf-8 -*-

"""
file: segmentation.py

Description: performs text segmentation according to given tokeniser.
It is searched in "obj/tokenisers", a valid name to give to this
script is the basename (without extension) of any .py file that can be
found in this directory.

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

import logging, codecs

from obj.tokenisers.dispatch import get_tokeniser
from obj.logger              import logging_format

segmentation_logger = logging.getLogger("sem.segmentation")

def segmentation(infile, tokeniser_name, outfile,
                 output_format="vector",
                 ienc="utf-8", oenc="utf-8",
                 log_level=logging.WARNING, log_file=None):
    file_mode = u"a"
    
    segmentation_logger.setLevel(log_level)
    
    segmentation_logger.debug('Getting tokeniser "%s"' %(tokeniser_name))
    
    Tokeniser           = get_tokeniser(tokeniser_name)
    tokeniser           = Tokeniser()
    number_of_tokens    = 0
    number_of_sentences = 0
    
    with codecs.open(outfile, "w", oenc) as O:
        segmentation_logger.debug(u'segmenting "%s" content to "%s"', unicode(infile, errors="replace"), unicode(outfile, errors="replace"))
        joiner = (u" " if output_format=="line" else u"\n")
        for line in codecs.open(infile, "rU", ienc):
            line   = line.lstrip(u"\ufeff") # BOM
            line   = line.strip()
            tokens = tokeniser.tokenise(line, tokeniser.word_bounds(line))
            for sentence in tokeniser.tokenise(tokens, tokeniser.sentence_bounds(tokens)):
                number_of_sentences += 1
                number_of_tokens    += len(sentence)
                O.write(joiner.join(sentence) + u"\n")
                if output_format == "vector":
                    O.write(u"\n")
        segmentation_logger.info('segmented "%s" in %i sentences, %i tokens' %(unicode(infile, errors="replace"), number_of_sentences, number_of_tokens))

if __name__ == "__main__":
    import argparse, os.path, sys

    parser = argparse.ArgumentParser(description="Segments the textual content of a sentence into tokens. They can either be outputted line per line or in a vectorised format")
    
    parser.add_argument("infile",
                        help="The input file (raw text)")
    parser.add_argument("tokeniser_name",
                        help="The name of the tokeniser to import")
    parser.add_argument("outfile",
                        help="The output file")
    parser.add_argument("--output-format", dest="output_format", choices=("line", "vector"), default="vector",
                        help="The output format (default: %(default)s)")
    parser.add_argument("--input-encoding", dest="ienc",
                        help="Encoding of the input (default: UTF-8)")
    parser.add_argument("--output-encoding", dest="oenc",
                        help="Encoding of the input (default: UTF-8)")
    parser.add_argument("--encoding", dest="enc", default="UTF-8",
                        help="Encoding of both the input and the output (default: UTF-8)")
    parser.add_argument("-l", "--log", dest="log_level", choices=("DEBUG","INFO","WARNING","ERROR","CRITICAL"), default="WARNING",
                        help="Increase log level (default: %(default)s)")
    parser.add_argument("--log-file", dest="log_file",
                        help="The name of the log file")

    if __package__:
        args = parser.parse_args(sys.argv[2:])
    else:
        args = parser.parse_args()
    
    segmentation(args.infile, args.tokeniser_name, args.outfile,
                 output_format=args.output_format,
                 ienc=args.ienc or args.enc, oenc=args.oenc or args.enc,
                 log_level=args.log_level, log_file=args.log_file)
    sys.exit(0)
