# -*- coding:utf-8 -*-

"""file: map_annotations.py

Description: Map annotations according to a mapping. If no mapping is provided
for a given type, it will remain unchanged. If an empty mapping is provided,
every annotation of that type will be discarded. This module only affects
annotations, not CoNLL Corpus.

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
import argparse
from datetime import timedelta

from sem.modules.sem_module import SEMModule as RootModule
from sem.storage import Annotation, Tag
import sem.logger
from sem.storage import compile_map


class SEMModule(RootModule):
    def __init__(self, mapping, annotation_name, **kwargs):
        super(SEMModule, self).__init__(**kwargs)

        if isinstance(mapping, str):
            with open(mapping, 'r', encoding="utf-8") as input_stream:
                self._mapping = compile_map(input_stream)
        else:
            self._mapping = mapping

        self._annotation_name = annotation_name

    def process_document(self, document, **kwargs):
        """Updates a document with various segmentations and creates
        an sem.corpus (CoNLL-formatted data) using field argument as index.

        Parameters
        ----------
        document : sem.storage.Document
            the input data. It is a document with only a content
        """

        start = time.time()

        ref_annotation = document.annotation(self._annotation_name)
        ref_annotations = ref_annotation.annotations
        new_annotations = [
            Tag(self._mapping.get(annotation.value, annotation.value), annotation.lb, annotation.ub)
            for annotation in ref_annotations
            if self._mapping.get(annotation.value, None) != ""
        ]

        document.add_annotation(
            Annotation(
                self._annotation_name,
                reference=ref_annotation.reference,
                annotations=new_annotations,
            )
        )

        laps = time.time() - start
        sem.logger.info("in %s", timedelta(seconds=laps))


parser = argparse.ArgumentParser(
    "Map annotations according to a mapping."
    " If no mapping is provided for a given type,"
    " it will remain unchanged."
    " If an empty mapping is provided,"
    " every annotation of that type will be discarded.",
)

parser.add_argument("infile", help="The input file (CoNLL format)")
parser.add_argument("mapping", help="The mapping file")
parser.add_argument("outfile", help="The output file")
parser.add_argument(
    "-c", "--column", type=int, default=-1, help="The column to map (default: %(default)s)"
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
