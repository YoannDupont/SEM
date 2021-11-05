# -*- coding: utf-8 -*-

"""
file: tagger.py

Description: performs a sequence of operations in a pipeline.

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
import os
import shutil
import multiprocessing
import time
import pathlib
from datetime import timedelta
from functools import partial

import configparser

import sem
import sem.logger
import sem.importers
import sem.pipelines

if sem.ON_WINDOWS:
    sem.logger.warning(
        "multiprocessing not handled on Windows. Documents will be processed sequentially."
    )

__pipeline = None


def process(document, exporter, output_directory, couples, encoding, lang_style):
    """
    The function used to allow multiprocessing of documents.
    Note that multiprocessing will only work on Linux.
    The function is written to work sequentially on Windows to avoid dupe.
    """
    __pipeline.process_document(document)

    if exporter is not None:
        name = document.escaped_name()
        if "html" in exporter.extension:
            shutil.copy(sem.SEM_RESOURCE_DIR / "css" / "tabs.css", output_directory)
            shutil.copy(
                sem.SEM_RESOURCE_DIR / "css" / exporter._lang / lang_style, output_directory
            )

        shortname = pathlib.Path(name).stem
        out_path = output_directory / "{0}.{1}".format(shortname, exporter.extension)
        if exporter.extension == "ann":
            filename = shortname + ".txt"
            with open(output_directory / filename, "w", encoding=encoding) as output_stream:
                output_stream.write(document.content)
        exporter.document_to_file(document, couples, out_path, encoding=encoding)

    return document


def get_option(cfg, section, option, default=None):
    try:
        return cfg.get(section, option)
    except (configparser.NoSectionError, configparser.NoOptionError):
        return default


def get_section(cfg, section):
    try:
        return dict(cfg.items(section))
    except configparser.NoSectionError:
        return {}


def main(argv=None):
    args = parser.parse_args(argv)
    tagger(**vars(args))


def tagger(
    workflow,
    infiles,
    output_directory=".",
    force_format="default",
    n_procs=1,
    pipeline=None,
    options=None,
    exporter=None,
    couples=None
):
    """Return a document after it passed through a pipeline.

    Parameters
    ----------
    workflowfile : str
        the file containing the pipeline and global options
    infiles : list
        the input for the upcoming pipe. Its base value is the list of files to
        treat, it can be either "plain text" or CoNNL-formatted file.
    directory : str
        the directory where every file will be outputted.
    n_procs : int
        the number of processors to use to process documents.
        f n_procs < 0, it will be set to 1, if n_procs == 0 it will be set
        to cpu_count, and n_procs otherwise.
        If n_procs is greater than the number of documents, it will be
        adjusted.
    """

    start = time.time()

    global __pipeline

    output_directory = pathlib.Path(output_directory)

    if pipeline is None or options is None:
        workflow = pathlib.Path(workflow)
        pipeline, options, exporter, couples = sem.pipelines.load_workflow(workflow, force_format)
    __pipeline = pipeline

    if get_option(options, "log", "log_file") is not None:
        sem.logger.addHandler(sem.logger.file_handler(get_option(options, "log", "log_file")))
    sem.logger.setLevel(get_option(options, "log", "log_level", "WARNING"))

    if not output_directory.exists():
        os.makedirs(output_directory)

    oenc = get_option(options, "encoding", "output_encoding", "utf-8")

    file_format = get_option(options, "file", "format", "guess")
    opts = get_section(options, "file")
    opts.update(get_section(options, "encoding"))
    if file_format == "conll":
        opts["fields"] = opts["fields"].split(",")
        opts["taggings"] = [tagging for tagging in opts.get("taggings", "").split(",") if tagging]
        opts["chunkings"] = [
            chunking for chunking in opts.get("chunkings", "").split(",") if chunking
        ]

    documents = sem.importers.documents_from_list(infiles, file_format, **opts)

    n_procs = int(n_procs)
    if n_procs == 0:
        n_procs = multiprocessing.cpu_count()
        sem.logger.info("no processors given, using %s", n_procs)
    else:
        n_procs = min(max(n_procs, 1), multiprocessing.cpu_count())
    if n_procs > len(documents):
        n_procs = len(documents)

    do_process = partial(
        process,
        exporter=exporter,
        output_directory=output_directory,
        couples=couples,
        encoding=oenc,
        lang_style=get_option(options, "export", "lang_style", "default.css"),
    )
    if sem.ON_WINDOWS or n_procs == 1:
        for document in documents:
            do_process(document)
    else:
        pool = multiprocessing.Pool(processes=n_procs)
        dpp = 1 if n_procs < len(documents) * 2 else 2  # documents per processor
        beg = 0
        batch_size = dpp * n_procs
        while beg <= len(documents):
            documents[beg: beg + batch_size] = pool.map(
                do_process, documents[beg: beg + batch_size]
            )
            beg += batch_size
        pool.terminate()

    laps = time.time() - start
    sem.logger.info("done in %s", timedelta(seconds=laps))

    return documents


parser = argparse.ArgumentParser(
    "Performs various operations given in a workflow configuration file that defines a pipeline."
)

parser.add_argument(
    "workflow",
    help="The workflow configuration file."
    " Defines at least the pipeline and may provide some options.",
)
parser.add_argument("infiles", nargs="+", help="The input file(s) for the tagger.")
parser.add_argument(
    "-o",
    "--output-directory",
    dest="output_directory",
    default=".",
    help='The output directory (default: "%(default)s").',
)
parser.add_argument(
    "-f",
    "--force-format",
    default="default",
    help='Force the output format given in "workflow" (default: "%(default)s").',
)
parser.add_argument(
    "-p",
    "--processors",
    dest="n_procs",
    type=int,
    default=1,
    help='The number of processors to use (default: "%(default)s").',
)
