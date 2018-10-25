#-*- coding: utf-8 -*-

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

import codecs
import logging
import os
import shutil
import multiprocessing

try:
    import ConfigParser as configparser
except ImportError:
    import configparser

try:
    from xml.etree import cElementTree as ET
except importError:
    from xml.etree import ElementTree as ET

# measuring time laps
import time
import os.path
from datetime import timedelta
from functools import partial

import sem

from sem.logger import logging_format, default_handler
from sem.storage import Document

from sem.modules import get_module
import sem.modules.pipeline
import sem.modules.export
import sem.exporters
import sem.exporters.conll
import sem.importers
import sem.misc

sem_tagger_logger = logging.getLogger("sem.tagger")
sem_tagger_logger.addHandler(default_handler)
if sem.ON_WINDOWS:
    sem_tagger_logger.warn("multiprocessing not handled on Windows. Documents will be processed sequentially.")

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
        if u"html" in exporter.extension():
            shutil.copy(os.path.join(sem.SEM_RESOURCE_DIR, u"css", u"tabs.css"), output_directory)
            shutil.copy(os.path.join(sem.SEM_RESOURCE_DIR, u"css", exporter._lang, lang_style), output_directory)
        
        shortname, ext = os.path.splitext(name)
        out_path = os.path.join(output_directory, u"{0}.{1}".format(shortname, exporter.extension()))
        if exporter.extension() == u"ann":
            filename = shortname + u".txt"
            with codecs.open(os.path.join(output_directory, filename), "w", encoding) as O:
                O.write(document.content)
        exporter.document_to_file(document, couples, out_path, encoding=encoding)
        
    return document
    
def get_option(cfg, section, option, default=None):
    try:
        return cfg.get(section, option)
    except:
        return default

def get_section(cfg, section):
    try:
        return dict(cfg.items(section))
    except configparser.NoSectionError:
        return {}

def load_master(master, force_format="default", pipeline_mode="all"):
    try:
        tree = ET.parse(os.path.abspath(master))
        root = tree.getroot()
    except IOError:
        root = ET.fromstring(master)
    xmlpipes, xmloptions = list(root)
    
    options = configparser.RawConfigParser()
    exporter = None
    couples = {}
    for xmloption in xmloptions:
        section = xmloption.tag
        options.add_section(section)
        attribs = {}
        for key, val in xmloption.attrib.items():
            key = key.replace(u"-", u"_")
            try:
                attribs[key] = sem.misc.str2bool(val)
            except ValueError:
                attribs[key] = val
        for key, val in attribs.items():
            options.set(section, key, val)
        if xmloption.tag == "export":
            couples = dict(options.items("export"))
            export_format = couples["format"]
            if force_format is not None and force_format != "default":
                sem_tagger_logger.info("using forced format: {0}".format(force_format))
                export_format = force_format
            exporter = sem.exporters.get_exporter(export_format)(**couples)
    
    if get_option(options, "log", "log_file") is not None:
        sem_tagger_logger.addHandler(file_handler(get_option(options, "log", "log_file")))
    sem_tagger_logger.setLevel(get_option(options, "log", "log_level", "WARNING"))
    
    classes = {}
    pipes = []
    for xmlpipe in xmlpipes:
        if xmlpipe.tag == "export": continue
        
        Class = classes.get(xmlpipe.tag, None)
        if Class is None:
            Class = get_module(xmlpipe.tag)
            classes[xmlpipe.tag] = Class
        arguments = {}
        arguments["expected_mode"] = pipeline_mode
        for key, value in xmlpipe.attrib.items():
            if value.startswith(u"~/"):
                value = os.path.expanduser(value)
            elif sem.misc.is_relative_path(value):
                value = os.path.abspath(os.path.join(os.path.dirname(master), value))
            arguments[key.replace(u"-", u"_")] = value
        for section in options.sections():
            if section == "export": continue
            for key, value in options.items(section):
                if key not in arguments:
                    arguments[key] = value
                else:
                    sem_tagger_logger.warn('Not adding already existing option: {0}'.format(key))
        sem_tagger_logger.info("loading {0}".format(xmlpipe.tag))
        pipes.append(Class(**arguments))
    pipeline = sem.modules.pipeline.Pipeline(pipes, pipeline_mode=pipeline_mode)
    
    return pipeline, options, exporter, couples

def main(args):
    """
    Return a document after it passed through a pipeline.
    
    Parameters
    ----------
    masterfile : str
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
    
    try:
        output_directory = args.output_directory
    except AttributeError:
        output_directory = u"."
    try:
        force_format = args.force_format
    except AttributeError:
        force_format = "default"
    
    try:
        pipeline = args.pipeline
        options = args.options
        exporter = args.exporter
        couples = args.couples
    except AttributeError:
        pipeline, options, exporter, couples = load_master(args.master, force_format)
    __pipeline = pipeline
    
    if get_option(options, "log", "log_file") is not None:
        sem_tagger_logger.addHandler(file_handler(get_option(options, "log", "log_file")))
    sem_tagger_logger.setLevel(get_option(options, "log", "log_level", "WARNING"))
    
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    exports = {} # keeping track of already done exports
    
    nth = 1
    ienc = get_option(options, "encoding", "input_encoding", "utf-8")
    oenc = get_option(options, "encoding", "output_encoding", "utf-8")
    
    file_format = get_option(options, "file", "format", "guess")
    opts = get_section(options, "file")
    opts.update(get_section(options, "encoding"))
    if file_format == "conll":
        opts["fields"] = opts["fields"].split(u",")
        opts["taggings"] = [tagging for tagging in opts.get("taggings", u"").split(u",") if tagging]
        opts["chunkings"] = [chunking for chunking in opts.get("chunkings", u"").split(u",") if chunking]
    
    documents = sem.misc.documents_from_list(args.infiles, file_format, **opts)
    
    n_procs = getattr(args, "n_procs", 1)
    if n_procs == 0:
        n_procs = multiprocessing.cpu_count()
        sem_tagger_logger.info("no processors given, using %s", n_procs)
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
        lang_style=get_option(options, "export", "lang_style", "default.css")
    )
    if sem.ON_WINDOWS:
        for document in documents:
            do_process(document)
    else:
        pool = multiprocessing.Pool(processes=n_procs)
        dpp = (1 if n_procs < len(documents)*2 else 2) # documents per processor
        beg = 0
        batch_size = dpp * n_procs
        while beg <= len(documents):
            documents[beg : beg + batch_size] = pool.map(do_process, documents[beg : beg + batch_size])
            beg += batch_size
        pool.terminate()
    
    laps = time.time() - start
    sem_tagger_logger.info('done in %s', timedelta(seconds=laps))
    
    return documents


import sem

_subparsers = sem.argument_subparsers

parser = _subparsers.add_parser(os.path.splitext(os.path.basename(__file__))[0], description="Performs various operations given in a master configuration file that defines a pipeline.")

parser.add_argument("master",
                    help="The master configuration file. Defines at least the pipeline and may provide some options.")
parser.add_argument("infiles", nargs="+",
                    help="The input file(s) for the tagger.")
parser.add_argument("-o", "--output-directory", dest="output_directory", default=".",
                    help='The output directory (default: "%(default)s").')
parser.add_argument("-f", "--force-format", dest="force_format", default="default",
                    help='Force the output format given in "master", default otherwise (default: "%(default)s").')
parser.add_argument("-p", "--processors", dest="n_procs", type=int, default=1,
                    help='The number of processors to use (default: "%(default)s").')
