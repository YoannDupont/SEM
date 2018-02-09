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

import logging, codecs, time, os.path

from datetime import timedelta

from .sem_module import SEMModule as RootModule

from sem.tokenisers           import get_tokeniser
from sem.storage.document     import Document
from sem.storage.segmentation import Segmentation
from sem.logger               import default_handler, file_handler

segmentation_logger = logging.getLogger("sem.segmentation")
segmentation_logger.addHandler(default_handler)

class SEMModule(RootModule):
    def __init__(self, tokeniser, log_level="WARNING", log_file=None, **kwargs):
        super(SEMModule, self).__init__(log_level=log_level, log_file=log_file, **kwargs)
        
        if type(tokeniser) in (str, unicode):
            segmentation_logger.info('Getting tokeniser "%s"' %(tokeniser))
            Tokeniser = get_tokeniser(tokeniser)
            self._tokeniser = Tokeniser()
        else:
            self._tokeniser = tokeniser
    
    def process_document(self, document, **kwargs):
        """
        Updates a document with various segmentations and creates
        an sem.corpus (CoNLL-formatted data) using field argument as index.
        
        Parameters
        ----------
        document : sem.storage.Document
            the input data. It is a document with only a content
        log_level : str or int
            the logging level
        log_file : str
            if not None, the file to log to (does not remove command-line
            logging).
        """
        
        start = time.time()

        if self._log_file is not None:
            segmentation_logger.addHandler(file_handler(self._log_file))
        segmentation_logger.setLevel(self._log_level)

        current_tokeniser = self._tokeniser

        segmentation_logger.debug(u'segmenting "%s" content', document.name)

        content         = document.content
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

def main(args):
    if args.log_file is not None:
        segmentation_logger.addHandler(file_handler(args.log_file))
    segmentation_logger.setLevel(args.log_level)
    
    ienc = args.ienc or args.enc
    oenc = args.oenc or args.enc
    segmenter = SEMModule(args.tokeniser_name)
    document = Document(os.path.basename(args.infile), content=codecs.open(args.infile, "rU", ienc).read().replace(u"\r", u""))
    segmenter.process_document(document, log_level=args.log_level)
    tokens_spans = document.segmentation("tokens")
    sentence_spans = document.segmentation("sentences")
    joiner = (u"\n" if args.output_format == "vector" else u" ")
    content = document.content
    with codecs.open(args.outfile, "w", oenc) as O:
        for sentence in sentence_spans:
            sentence_token_spans = tokens_spans[sentence.lb : sentence.ub]
            sentence_tokens = [content[s.lb : s.ub] for s in sentence_token_spans]
            O.write(joiner.join(sentence_tokens))
            if args.output_format == "vector":
                O.write(u"\n")
            O.write(u"\n")


import sem

_subparsers = sem.argument_subparsers

parser = _subparsers.add_parser(os.path.splitext(os.path.basename(__file__))[0], description="Segments the textual content of a sentence into tokens. They can either be outputted line per line or in a vectorised format.")

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

#args = parser.parse_args()
#main(args)
#
#sys.exit(0)
