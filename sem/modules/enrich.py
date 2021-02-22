# -*- coding: utf-8 -*-

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

import argparse
import time
from datetime import timedelta

try:
    from xml.etree.cElementTree import ElementTree, tostring as element2string
except ImportError:
    from xml.etree.ElementTree import ElementTree, tostring as element2string

from sem.modules.sem_module import SEMModule as RootModule

from sem.features import xml2feat
import sem.logger
from sem.importers import conll_file
from sem.storage import Entry

# import pathlib


class SEMModule(RootModule):
    def __init__(
        self,
        path=None,
        bentries=None,
        aentries=None,
        features=None,
        mode="label",
        **kwargs,
    ):
        super(SEMModule, self).__init__(**kwargs)

        self._mode = mode
        self._source = path
        self._bentries = []  # informations that are before newly added information
        self._aentries = []  # informations that are after ...
        self._features = []  # informations that are added
        self._names = set()
        self._temporary = set()  # features that will be deleted at the end of process
        self._x2f = None  # the feature parser, initialised in parse

        if self._source is not None:
            sem.logger.info("loading %s", self._source)
            self._parse(self._source)
        else:
            self._bentries = (
                [entry for entry in bentries if entry.has_mode(self._mode)]
                if bentries
                else self._bentries
            )
            self._aentries = (
                [entry for entry in aentries if entry.has_mode(self._mode)]
                if aentries
                else self._aentries
            )
            self._features = features
            self._names = set([entry.name for entry in self._aentries + self._bentries])

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, mode):
        if not isinstance(self._source, str):
            raise RuntimeError(
                "cannot change mode for Enrich module: source for informations is not a file."
            )
        self._mode = mode
        sem.logger.info("loading %s", self._source)
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

    def fields(self):
        fields = [entry.name for entry in self._bentries]
        fields += [name for (feature, name) in self.features if name not in self._temporary]
        fields += [entry.name for entry in self._aentries]
        return fields

    def process_document(self, document, **kwargs):
        """
        Updates the CoNLL-formatted corpus inside a document with various
        features.

        Parameters
        ----------
        document : sem.storage.Document
            the input data, contains an object representing CoNLL-formatted
            data. Each token is a dict which works like TSV.
        """

        start = time.time()

        missing_fields = set([I.name for I in self.bentries + self.aentries]) - set(
            document.corpus.fields
        )

        if len(missing_fields) > 0:
            raise ValueError(
                "Missing fields in input corpus: {0}".format(",".join(sorted(missing_fields)))
            )

        sem.logger.info('enriching file "%s"', document.name)

        fields = self.fields()
        nth = 0
        for i, p in enumerate(document.corpus):
            p.update(self.features)
            for tmp in self._temporary:
                p.remove(tmp)
            nth += 1
            if 0 == nth % 1000:
                sem.logger.debug("%i sentences enriched", nth)
        sem.logger.debug("%i sentences enriched", nth)
        document.corpus.fields = fields[:]

        laps = time.time() - start
        sem.logger.info("done in %s", timedelta(seconds=laps))

    def _parse(self, filename):
        def check_entry(entry_name):
            if entry_name in self._names:
                raise ValueError('Duplicated column name: "{}"'.format(entry_name))
            else:
                self._names.add(entry_name)

        parsing = ElementTree()
        parsing.parse(filename)

        children = parsing.getroot().getchildren()

        if len(children) != 2:
            raise RuntimeError(
                "Enrichment file requires exactly 2 fields, {0} given.".format(len(children))
            )
        else:
            if children[0].tag != "entries":
                raise RuntimeError(
                    'Expected "entries" as first field, got "{0}".'.format(children[0].tag)
                )
            if children[1].tag != "features":
                raise RuntimeError(
                    'Expected "features" as second field, got "{0}".'.format(children[1].tag)
                )

        entries = list(children[0])
        if len(entries) not in (1, 2):
            raise RuntimeError(
                "Entries takes exactly 1 or 2 fields, {0} given".format(len(entries))
            )
        else:
            entry1 = entries[0].tag.lower()
            entry2 = entries[1].tag.lower() if len(entries) == 2 else None
            if entry1 not in ("before", "after"):
                raise RuntimeError(
                    'For entry position, expected "before" or "after", got "{0}".'.format(entry1)
                )
            if entry2 and entry2 not in ("before", "after"):
                raise RuntimeError(
                    'For entry position, expected "before" or "after", got "{0}".'.format(entry2)
                )
            if entry1 == entry2:
                raise RuntimeError("Both entry positions are the same, they should be different")

        for entry in entries:
            for c in entry.getchildren():
                current_entry = Entry.fromXML(c)
                check_entry(current_entry.name)
                if entry.tag == "before" and current_entry.has_mode(self._mode):
                    self._bentries.append(current_entry)
                elif entry.tag == "after" and current_entry.has_mode(self._mode):
                    self._aentries.append(current_entry)

        features = list(children[1])
        del self._features[:]
        for feature in features:
            feature_name = feature.attrib.get("name")
            if not sem.misc.str2bool(feature.attrib.get("display", "yes")):
                self._temporary.add(feature_name)
            self._features.append((xml2feat(feature, path=filename), feature_name))
            if not feature_name:
                try:
                    raise ValueError("Nameless feature found.")
                except ValueError as exc:
                    for line in element2string(feature).rstrip().split("\n"):
                        sem.logger.error(line.strip())
                    sem.logger.exception(exc)
                    raise
            check_entry(feature_name)


def main(argv=None):
    enrich(parser.parse_args(argv))


def enrich(args):
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
        sem.logger.addHandler(sem.logger.file_handler(args.log_file))
    sem.logger.setLevel(args.log_level)
    sem.logger.info('parsing enrichment file "%s"', args.infofile)

    processor = SEMModule(path=args.infofile, mode=args.mode)

    sem.logger.debug('enriching file "%s"', args.infile)

    bentries = [entry.name for entry in processor.bentries]
    aentries = [entry.name for entry in processor.aentries]
    document = conll_file(
        args.infile, bentries + aentries, (bentries + aentries)[0], encoding=args.ienc or args.enc
    )

    processor.process_document(document)
    fields = processor.fields()
    with open(args.outfile, "w", encoding=args.oenc or args.enc) as output_stream:
        for sentence in document.corpus:
            output_stream.write(sentence.conll(fields))
            output_stream.write("\n\n")

    laps = time.time() - start
    sem.logger.info("done in %s", timedelta(seconds=laps))


parser = argparse.ArgumentParser(
    "Adds information to a file using and XML-styled configuration file."
)

parser.add_argument("infile", help="The input file (CoNLL format)")
parser.add_argument("infofile", help="The information file (XML format)")
parser.add_argument("outfile", help="The output file (CoNLL format)")
parser.add_argument(
    "-m",
    "--mode",
    dest="mode",
    default="train",
    choices=("train", "label", "annotate", "annotation"),
    help="The mode for enrichment. May make entries vary (default: %(default)s)",
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
    help="Increase log level (default: critical)",
)
parser.add_argument("--log-file", dest="log_file", help="The name of the log file")
