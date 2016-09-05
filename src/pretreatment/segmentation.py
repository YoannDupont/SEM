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

import logging, codecs, time

from datetime import timedelta

from obj.tokenisers.dispatch  import get_tokeniser
from obj.storage.document     import Document
from obj.storage.segmentation import Segmentation
from obj.logger               import default_handler, file_handler

segmentation_logger = logging.getLogger("sem.segmentation")
segmentation_logger.addHandler(default_handler)

def document_segmentation(document, tokeniser,
                          field=u"word",
                          log_level=logging.WARNING, log_file=None):
    """
    Updates a document with various segmentations and creates
    an obj.corpus (CoNLL-formatted data) using field argument as index.
    
    Parameters
    ----------
    document : obj.storage.Document
        the input data. It is a document with only a content
    tokeniser : str or obj.tokenisers.Tokeniser
        the tokeniser to segment content of the document with.
        If tokeniser is a string, it will be looked up with
        get_tokeniser method.
    field : str
        the field to index tokens with
    log_level : str or int
        the logging level
    log_file : str
        if not None, the file to log to (does not remove command-line
        logging).
    """
    
    start = time.time()
    
    if log_file is not None:
        segmentation_logger.addHandler(file_handler(log_file))
    segmentation_logger.setLevel(log_level)
    
    current_tokeniser = None
    if type(tokeniser) in (str, unicode):
        segmentation_logger.info('Getting tokeniser "%s"' %(tokeniser))
        Tokeniser         = get_tokeniser(tokeniser)
        current_tokeniser = Tokeniser()
    else:
        current_tokeniser = tokeniser
    
    content = document.content
    
    segmentation_logger.debug(u'segmenting "%s" content', document.name)
    
    token_spans     = current_tokeniser.bounds2spans(current_tokeniser.word_bounds(content))
    sentence_spans  = current_tokeniser.bounds2spans(current_tokeniser.sentence_bounds(content, token_spans))
    paragraph_spans = current_tokeniser.bounds2spans(current_tokeniser.paragraph_bounds(content, sentence_spans, token_spans))
    
    segmentation_logger.info('segmented "%s" in %i sentences, %i tokens' %(document.name, len(sentence_spans), len(token_spans)))
    
    document.add_segmentation(Segmentation("tokens", spans=token_spans))
    document.add_segmentation(Segmentation("sentences", reference=document.segmentation("tokens"), spans=sentence_spans))
    document.add_segmentation(Segmentation("paragraphs", reference=document.segmentation("sentences"), spans=paragraph_spans))
    document.corpus.from_segmentation(document.content, document.segmentation("tokens"), document.segmentation("sentences"))
    
    laps = time.time() - start
    segmentation_logger.info('in %s' %(timedelta(seconds=laps)))

def segmentation(infile, tokeniser_name, outfile,
                 output_format="vector",
                 ienc="utf-8", oenc="utf-8",
                 log_level=logging.WARNING, log_file=None):
    """
    Takes a "raw text" file and creates a CoNLL-formatted file with
    tokenised text.
    
    Parameters
    ----------
    infile : str
        the input data. It is a document with only a content
    tokeniser : str
        the tokeniser name. It will be looked up with get_tokeniser
        method.
    ienc : str
        the input file encoding
    oenc : str
        the output file encoding
    log_level : str or int
        the logging level
    log_file : str
        if not None, the file to log to (does not remove command-line
        logging).
    """
    
    start = time.time()
    
    document = Document(unicode(infile, errors="replace"), codecs.open(infile, "rU", ienc).read().lstrip(u"\ufeff")) # removing BOM
    document_segmentation(document, tokeniser_name, log_level=log_level, log_file=log_file)
    
    content   = document.content
    tokens    = [content[token.lb : token.ub] for token in document.segmentation("tokens")]
    sentences = [tokens[sentence.lb : sentence.ub] for sentence in document.segmentation("sentences")]
    
    segmentation_logger.info(u'writing to "%s"', outfile)
    
    joiner = (u" " if output_format=="line" else u"\n")
    with codecs.open(outfile, "w", oenc) as O:
        for sentence in sentences:
            O.write(joiner.join(sentence) + u"\n")
            if output_format == "vector":
                O.write(u"\n")
    
    laps = time.time() - start
    segmentation_logger.info('in %s' %(timedelta(seconds=laps)))

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
