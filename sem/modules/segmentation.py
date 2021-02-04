# -*- coding:utf-8 -*-

"""
file: segmentation.py

Description: performs text segmentation according to given tokeniser.

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

import time
import pathlib
from datetime import timedelta

from sem.modules.sem_module import SEMModule as RootModule
from sem.misc import (strip_html, read_chunks)
from sem.tokenisers import (get_tokeniser, bounds2spans)
from sem.storage import (Document, Segmentation, Span)
import sem.logger


def token_spans_buffered(tokeniser, content):
    """Return the token spans of content.
    This does the same as tokeniser.word_spans, but this method buffers
    the input to allow a quicker processing of large content.
    """
    rem = ""  # remainder of unsegmented tokens
    shift = 0
    token_spans = []
    for chunk in read_chunks(content):
        chnk = rem + chunk
        spans = tokeniser.word_spans(chnk)
        if not spans:
            rem = chnk
            continue
        elif spans[-1].ub < len(chnk):
            rem = chnk[spans[-1].ub:]
        elif spans[-1].ub == len(chnk):
            rem = chnk[spans[-1].lb:]
            del spans[-1]
        else:
            rem = ""
        token_spans.extend([Span(shift + s.lb, shift + s.ub) for s in spans])
        shift += len(chnk) - len(rem)
        del spans[:]

    if rem:
        spans = tokeniser.word_spans(rem) or [Span(0, len(rem))]
        token_spans.extend([Span(shift + s.lb, shift + s.ub) for s in spans])
    if not content[token_spans[-1].lb: token_spans[-1].ub].strip():
        del token_spans[-1]

    return token_spans


class SEMModule(RootModule):
    def __init__(self, tokeniser, **kwargs):
        super(SEMModule, self).__init__(**kwargs)

        if isinstance(tokeniser, str):
            sem.logger.info('Getting tokeniser "{0}"'.format(tokeniser))
            self._tokeniser = get_tokeniser(tokeniser)()
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
        """

        start = time.time()

        current_tokeniser = self._tokeniser

        sem.logger.debug('segmenting "%s" content', document.name)

        content = document.content
        if document.metadata("MIME") == "text/html":
            content = strip_html(content, keep_offsets=True)

        do_segmentation = (
            document.segmentation("tokens") is None
            or document.segmentation("sentences") is None
            or document.segmentation("paragraphs") is None
        )
        if do_segmentation:
            token_spans = token_spans_buffered(current_tokeniser, document.content)
            sentence_spans = bounds2spans(current_tokeniser.sentence_bounds(content, token_spans))
            paragraph_spans = bounds2spans(
                current_tokeniser.paragraph_bounds(content, sentence_spans, token_spans)
            )
        else:
            sem.logger.info(
                "{0} already has segmenation, not computing".format(document.name)
            )
            token_spans = document.segmentation("tokens").spans
            sentence_spans = document.segmentation("sentences").spans
            paragraph_spans = document.segmentation("paragraphs").spans
        sem.logger.info(
            '"{0}" segmented in {1} sentences, {2} tokens'.format(
                document.name, len(sentence_spans), len(token_spans)
            )
        )

        if document.segmentation("tokens") is None:
            document.add_segmentation(Segmentation("tokens", spans=token_spans))
        if document.segmentation("sentences") is None:
            document.add_segmentation(
                Segmentation(
                    "sentences", reference=document.segmentation("tokens"), spans=sentence_spans
                )
            )
        if document.segmentation("paragraphs") is None:
            document.add_segmentation(
                Segmentation(
                    "paragraphs",
                    reference=document.segmentation("sentences"),
                    spans=paragraph_spans,
                )
            )
        if len(document.corpus) == 0:
            document.corpus.from_segmentation(
                document.content,
                document.segmentation("tokens"),
                document.segmentation("sentences"),
            )

        laps = time.time() - start
        sem.logger.info("in {0}".format(timedelta(seconds=laps)))


def main(args):
    if args.log_file is not None:
        sem.logger.addHandler(sem.logger.file_handler(args.log_file))
    sem.logger.setLevel(args.log_level)

    ienc = args.ienc or args.enc
    oenc = args.oenc or args.enc
    segmenter = SEMModule(args.tokeniser_name)
    document = Document(
        pathlib.Path(args.infile).name,
        content=open(args.infile, "rU", encoding=ienc).read().replace("\r", ""),
    )
    segmenter.process_document(document)
    tokens_spans = document.segmentation("tokens")
    sentence_spans = document.segmentation("sentences")
    joiner = "\n" if args.output_format == "vector" else " "
    content = document.content
    with open(args.outfile, "w", encoding=oenc) as output_stream:
        for sentence in sentence_spans:
            sentence_token_spans = tokens_spans[sentence.lb: sentence.ub]
            sentence_tokens = [content[s.lb: s.ub] for s in sentence_token_spans]
            output_stream.write(joiner.join(sentence_tokens))
            if args.output_format == "vector":
                output_stream.write("\n")
            output_stream.write("\n")


import sem

_subparsers = sem.argument_subparsers

parser = _subparsers.add_parser(
    pathlib.Path(__file__).stem,
    description="Segments the textual content of a sentence into tokens."
    " They can either be outputted line per line or in a vectorised format.",
)

parser.add_argument("infile", help="The input file (raw text)")
parser.add_argument("tokeniser_name", help="The name of the tokeniser to import")
parser.add_argument("outfile", help="The output file")
parser.add_argument(
    "--output-format",
    dest="output_format",
    choices=("line", "vector"),
    default="vector",
    help="The output format (default: %(default)s)",
)
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
    help="Increase log level (default: %(default)s)",
)
parser.add_argument("--log-file", dest="log_file", help="The name of the log file")
