#-*- coding: utf-8 -*-

"""
file: enrich.py

Description: this program is used to enrich a CoNLL-formatted file with
various features.

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

import time
from datetime import timedelta
import codecs

try:
    from xml.etree.cElementTree import ElementTree, tostring as element2string
except ImportError:
    from xml.etree.ElementTree import ElementTree, tostring as element2string

from .sem_module import SEMModule as RootModule

from sem.features import XML2Feature
from sem.logger import default_handler, file_handler
from sem.misc import is_string
from sem.importers import conll_file
from sem.storage import Entry

from sem.storage import Span, Document, Segmentation
#1. from sem.storage.corpus1 import Corpus
from sem.importers import read_conll

import os.path
enrich_logger = logging.getLogger("sem.{0}".format(os.path.basename(__file__).split(".")[0]))
enrich_logger.addHandler(default_handler)

#1. def conll_file(filename, fields, word_field, encoding="utf-8", taggings=None, chunkings=None):
#1.     """
#1.     Read CoNLL-formatted text from a file.
#1.     """
#1.     name = os.path.basename(filename)
#1.     sents = [sent[:] for sent in read_conll(filename, encoding)]
#1.     return conll_data(name, Corpus(fields, sents), word_field, encoding="utf-8", taggings=None, chunkings=None)
#1. #1. 
#1. def conll_data(name, corpus, word_field, encoding="utf-8", taggings=None, chunkings=None):
#1.     """
#1.     Create a Document from CoNLL-formatted data (SEM Corpus).
#1.     """
#1.     character_index  = 0
#1.     sentence_index   = 0
#1.     contents         = []
#1.     word_spans       = []
#1.     sentence_spans   = []
#1.     word_index       = corpus.f2i[word_field]
#1.     for sentence in corpus.sentences:
#1.         contents.append([])
#1.         for token in sentence:
#1.             word = token[word_index]
#1.             contents[-1].append(word[:])
#1.             word_spans.append(Span(character_index, character_index+len(word)))
#1.             character_index += len(word) + 1
#1.         sentence_spans.append(Span(sentence_index, sentence_index+len(sentence)))
#1.         sentence_index += len(sentence)
#1.     document = Document(name, u"\n".join([u" ".join(content) for content in contents]), encoding)
#1.     document._corpus = corpus # TODO: should not access field with _
#1.     document.add_segmentation(Segmentation("tokens", spans=word_spans))
#1.     document.add_segmentation(Segmentation("sentences", reference=document.segmentation("tokens"), spans=sentence_spans[:]))
#1.     for tagging in (taggings or []):
#1.         document.add_annotation(tag_annotation_from_corpus(document._corpus, tagging, tagging, reference=document.segmentation("tokens"), strict=True))
#1.     for chunking in (chunkings or []):
#1.         document.add_annotation(chunk_annotation_from_corpus(document._corpus, chunking, chunking, reference=document.segmentation("tokens"), strict=True))
#1.     return document

class SEMModule(RootModule):
    def __init__(self, path=None, bentries=None, aentries=None, features=None, mode=u"label", log_level="WARNING", log_file=None, **kwargs):
        super(SEMModule, self).__init__(log_level=log_level, log_file=log_file, **kwargs)
        
        self._mode     = mode
        self._source   = path
        self._bentries = [] # informations that are before newly added information
        self._aentries = [] # informations that are after ...
        self._features = [] # informations that are added
        self._names    = set()
        self._x2f      = None # the feature parser, initialised in parse
        
        if self._source is not None:
            enrich_logger.info(u'loading %s', self._source)
            self._parse(self._source)
        else:
            self._bentries = ([entry for entry in bentries if entry.has_mode(self._mode)] if bentries else self._bentries)
            self._aentries = ([entry for entry in aentries if entry.has_mode(self._mode)] if aentries else self._aentries)
            self._features = features
            self._names = set([entry.name for entry in self._aentries + self._bentries])
    
    @property
    def informations(self):
        return self._informations
    
    @property
    def mode(self):
        return self._mode
    
    @mode.setter
    def mode(self, mode):
        if not is_string(self._source):
            raise RuntimeError("cannot change mode for Enrich module: source for informations is not a file.")
        self._mode = mode
        enrich_logger.info(u'loading %s', self._source)
        self._parse(self._source)
    
    @property
    def bentries(self):
        return self._bentries
    
    @property
    def aentries(self):
        return self._aentries
    
    @property
    def features(self):
        return self._features
    
    def process_document(self, document, **kwargs):
        """
        Updates the CoNLL-formatted corpus inside a document with various
        features.
        
        Parameters
        ----------
        document : sem.storage.Document
            the input data, contains an object representing CoNLL-formatted
            data. Each token is a dict which works like TSV.
        log_level : str or int
            the logging level
        log_file : str
            if not None, the file to log to (does not remove command-line
            logging).
        """
        
        start = time.time()
        
        if self._log_file is not None:
            enrich_logger.addHandler(file_handler(self._log_file))
        enrich_logger.setLevel(self._log_level)
        
        missing_fields = set([I.name for I in self.bentries + self.aentries]) - set(document.corpus.fields)
        
        if len(missing_fields) > 0:
            raise ValueError("Missing fields in input corpus: {0}".format(u",".join(sorted(missing_fields))))
        
        enrich_logger.info(u'enriching file "%s"', document.name)
        
        new_fields = [feature.name for feature in self.features if feature.display]
        document.corpus.fields += new_fields
        #1. document.corpus.fields = \
        #1.         [entry.name for entry in self.bentries] \
        #1.         + [feature.name for feature in self.features] \
        #1.         + [entry.name for entry in self.aentries]
        nth = 0
        for i, p in enumerate(document.corpus):
            for feature in self.features:
                if feature.is_sequence:
                    for i, value in enumerate(feature(p)):
                        p[i][feature.name] = value
                        #1. p.set(i, feature.name, value)
                else:
                    for i in range(len(p)):
                        p[i][feature.name] = feature(p, i)
                        #1. p.set(i, feature.name, feature(p, i))
                        if feature.is_boolean:
                            p[i][feature.name] = int(p[i][feature.name])
                            #1. p.set(i, feature.name, int(p.get(i, feature.name)))
                        elif p[i][feature.name] is None:
                        #1. elif p.get(i, feature.name) is None:
                            p[i][feature.name] = feature.default()
                            #1. p.set(i, feature.name, feature.default())
            nth += 1
            if (0 == nth % 1000):
                enrich_logger.debug(u'%i sentences enriched', nth)
        enrich_logger.debug(u'%i sentences enriched', nth)
        
        laps = time.time() - start
        enrich_logger.info(u"done in %s", timedelta(seconds=laps))
    
    def _parse(self, filename):
        def check_entry(entry_name):
            if entry_name in self._names:
                raise ValueError('Duplicated column name: "{}"'.format(entry_name))
            else:
                self._names.add(entry_name)
        
        parsing = ElementTree()
        parsing.parse(filename)
        
        children = parsing.getroot().getchildren()
        
        if len(children) != 2: raise RuntimeError("Enrichment file requires exactly 2 fields, {0} given.".format(len(children)))
        else:
            if children[0].tag != "entries":
                raise RuntimeError('Expected "entries" as first field, got "{0}".'.format(children[0].tag))
            if children[1].tag != "features":
                raise RuntimeError('Expected "features" as second field, got "{0}".'.format(children[1].tag))
        
        entries = list(children[0])
        if len(entries) not in (1,2):
            raise RuntimeError("Entries takes exactly 1 or 2 fields, {0} given".format(len(entries)))
        else:
            entry1 = entries[0].tag.lower()
            entry2 = (entries[1].tag.lower() if len(entries)==2 else None)
            if entry1 not in ("before", "after"):
                raise RuntimeError('For entry position, expected "before" or "after", got "{0}".'.format(entry1))
            if entry2 and entry2 not in ("before", "after"):
                raise RuntimeError('For entry position, expected "before" or "after", got "{0}".'.format(entry2))
            if entry1 == entry2:
                raise RuntimeError('Both entry positions are the same, they should be different')
        
        for entry in entries:
            for c in entry.getchildren():
                current_entry = Entry.fromXML(c)
                check_entry(current_entry.name)
                if entry.tag == "before" and current_entry.has_mode(self._mode):
                    self._bentries.append(current_entry)
                elif entry.tag == "after" and current_entry.has_mode(self._mode):
                    self._aentries.append(current_entry)
        
        self._x2f = XML2Feature(self.bentries + self.aentries, path=filename)
        
        features = list(children[1])
        del self._features[:]
        for feature in features:
            self._features.append(self._x2f.parse(feature))
            if self._features[-1].name is None:
                try:
                    raise ValueError("Nameless feature found.")
                except ValueError as exc:
                    for line in element2string(feature).rstrip().split("\n"):
                        xml2feature_logger.error(line.strip())
                    xml2feature_logger.exception(exc)
                    raise
            check_entry(self._features[-1].name)


def main(args):
    """
    Takes a CoNLL-formatted file and write another CoNLL-formatted file
    with additional features in it.
    
    Parameters
    ----------
    infile : str
        the CoNLL-formatted input file.
    infofile : str
        the XML file containing the different features.
    mode : str
        the mode to use for infofile. Some inputs may only be present in
        a particular mode. For example, the output tag is only available
        in "train" mode.
    log_level : str or int
        the logging level.
    log_file : str
        if not None, the file to log to (does not remove command-line
        logging).
    """
    
    start = time.time()
    
    if args.log_file is not None:
        enrich_logger.addHandler(file_handler(args.log_file))
    enrich_logger.setLevel(args.log_level)
    enrich_logger.info(u'parsing enrichment file "%s"', args.infofile)
    
    processor = SEMModule(path=args.infofile, mode=args.mode)
    
    enrich_logger.debug(u'enriching file "%s"', args.infile)
    
    bentries = [entry.name for entry in processor.bentries]
    aentries = [entry.name for entry in processor.aentries]
    features = [feature.name for feature in processor.features if feature.display]
    document = conll_file(args.infile, bentries + aentries, (bentries + aentries)[0], encoding=args.ienc or args.enc)
    
    processor.process_document(document)
    str_format = u"\t".join([u"{{{}}}".format(field) for field in bentries + features + aentries]) + u"\n"
    with codecs.open(args.outfile, "w", args.oenc or args.enc) as output_stream:
        for sentence in document.corpus:
            for token in sentence:
                output_stream.write(str_format.format(**token))
            output_stream.write(u"\n")
    
    laps = time.time() - start
    enrich_logger.info(u"done in %s", timedelta(seconds=laps))



import sem
import argparse, sys

_subparsers = sem.argument_subparsers

parser = _subparsers.add_parser(os.path.splitext(os.path.basename(__file__))[0], description="Adds information to a file using and XML-styled configuration file.")

parser.add_argument("infile",
                    help="The input file (CoNLL format)")
parser.add_argument("infofile",
                    help="The information file (XML format)")
parser.add_argument("outfile",
                    help="The output file (CoNLL format)")
parser.add_argument("-m", "--mode", dest="mode", default=u"train", choices=(u"train", u"label", u"annotate", u"annotation"),
                    help="The mode for enrichment. May make entries vary (default: %(default)s)")
parser.add_argument("--input-encoding", dest="ienc",
                    help="Encoding of the input (default: UTF-8)")
parser.add_argument("--output-encoding", dest="oenc",
                    help="Encoding of the input (default: UTF-8)")
parser.add_argument("--encoding", dest="enc", default="UTF-8",
                    help="Encoding of both the input and the output (default: UTF-8)")
parser.add_argument("-l", "--log", dest="log_level", choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"), default="WARNING",
                    help="Increase log level (default: critical)")
parser.add_argument("--log-file", dest="log_file",
                    help="The name of the log file")
