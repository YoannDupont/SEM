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
import ConfigParser

try:
    from xml.etree import cElementTree as ET
except importError:
    from xml.etree import ElementTree as ET

# measuring time laps
import time
from datetime import timedelta

import os.path

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

def get_option(cfg, section, option, default=None):
    try:
        return cfg.get(section, option)
    except:
        return default

def get_section(cfg, section):
    try:
        return dict(cfg.items(section))
    except ConfigParser.NoSectionError:
        return {}

def load_master(master, force_format="default"):
    tree = ET.parse(master)
    root = tree.getroot()
    xmlpipes, xmloptions = list(root)
    
    options = ConfigParser.RawConfigParser()
    exporter = None
    couples = {}
    for xmloption in xmloptions:
        if xmloption.tag != "export":
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
        else:
            couples = dict(xmloption.attrib.items())
            export_format = couples.pop("format")
            if force_format is not None and force_format != "default":
                sem_tagger_logger.info("using forced format: %s" %force_format)
                export_format = force_format
            exporter = sem.exporters.get_exporter(export_format)(**couples)
    
    if get_option(options, "log", "log_file") is not None:
        sem_tagger_logger.addHandler(file_handler(get_option(options, "log", "log_file")))
    sem_tagger_logger.setLevel(get_option(options, "log", "level", "WARNING"))
    
    classes = {}
    pipes = []
    for xmlpipe in xmlpipes:
        if xmlpipe.tag == "export": continue
        
        Class = classes.get(xmlpipe.tag, None)
        if Class is None:
            Class = get_module(xmlpipe.tag)
            classes[xmlpipe.tag] = Class
        arguments = {}
        for key, value in xmlpipe.attrib.items():
            if value.startswith(u"~/"):
                value = os.path.expanduser(value)
            elif sem.misc.is_relative_path(value):
                value = os.path.abspath(os.path.join(os.path.dirname(master), value))
            arguments[key.replace(u"-", u"_")] = value
        for section in options.sections():
            for key, value in options.items(section):
                if key not in arguments:
                    arguments[key] = value
                else:
                    sem_tagger_logger.warn('Not adding already existing option: %s' %(key))
        sem_tagger_logger.info("loading %s" %xmlpipe.tag)
        pipes.append(Class(**arguments))
    pipeline = sem.modules.pipeline.Pipeline(pipes)
    
    return pipeline, options, exporter, couples

def main(args):
    """
    Return a document after it passed through a pipeline.
    
    Parameters
    ----------
    masterfile : str
        the file containing the pipeline and global options
    infile : str
        the input for the upcoming pipe. Its base value is the file to
        treat, it can be either "plain text" or CoNNL-formatted file.
    directory : str
        the directory where every file will be outputted.
    """
    
    start = time.time()
    
    infile = args.infile
    
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
    
    if get_option(options, "log", "log_file") is not None:
        sem_tagger_logger.addHandler(file_handler(get_option(options, "log", "log_file")))
    sem_tagger_logger.setLevel(get_option(options, "log", "log_level", "WARNING"))
    
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    exports = {} # keeping track of already done exports
    
    nth = 1
    ienc = get_option(options, "encoding", "input_encoding", "utf-8")
    oenc = get_option(options, "encoding", "output_encoding", "utf-8")
    
    current_fields = None
    # the fields at the current state (depends on enrichments and
    # info cleaning). They will be used for wapiti
    
    sem_tagger_logger.info("Reading %s" %(infile))
    
    if isinstance(infile, Document):
        document = infile
    else:
        file_shortname, _ = os.path.splitext(os.path.basename(infile))
        export_name = os.path.join(output_directory, file_shortname)
        file_format = get_option(options, "file", "format", "guess")
        opts = get_section(options, "file")
        opts.update(get_section(options, "encoding"))
        if file_format == "text":
            document = Document(os.path.basename(infile), content=codecs.open(infile, "rU", ienc).read().replace(u"\r", u""), **opts)
        elif file_format == "conll":
            document = Document.from_conll(infile, **opts)
        elif file_format == "guess":
            document = sem.importers.load(infile, logger=sem_tagger_logger, **opts)
        else:
            raise ValueError(u"unknown format: %s" %file_format)
    
    pipeline.process_document(document)
    
    if exporter is not None:
        name = document.name
        if u"/" in name:
            name = name.rsplit(u"/", 1)[1]
        if exporter.extension() == "html":
            shutil.copy(os.path.join(sem.SEM_RESOURCE_DIR, "css", get_option(options, "export", "lang", "tabs.css")), output_directory)
            shutil.copy(os.path.join(sem.SEM_RESOURCE_DIR, "css", exporter._lang, get_option(options, "export", "lang_style", "default.css")), output_directory)
        
        if exporter.extension() == "ann":
            out_path = os.path.join(output_directory, "%s.%s" %(os.path.splitext(name)[0], exporter.extension()))
            with codecs.open(os.path.join(output_directory, name), "w", oenc) as O:
                O.write(document.content)
        else:
            out_path = os.path.join(output_directory, "%s.%s" %(name, exporter.extension()))
        exporter.document_to_file(document, couples, out_path, encoding=oenc)
    
    laps = time.time() - start
    sem_tagger_logger.info('done in %s' %(timedelta(seconds=laps)))
    
    return document


import sem

_subparsers = sem.argument_subparsers

parser = _subparsers.add_parser(os.path.splitext(os.path.basename(__file__))[0], description="Performs various operations given in a master configuration file that defines a pipeline.")

parser.add_argument("master",
                    help="The master configuration file. Defines at least the pipeline and may provide some options.")
parser.add_argument("infile",
                    help="The input file for the tagger.")
parser.add_argument("-o", "--output-directory", dest="output_directory", default=".",
                    help='The output directory (default: "%(default)s").')
parser.add_argument("-f", "--force-format", dest="force_format", default="default",
                    help='Force the output format given in "master", default otherwise (default: "%(default)s").')
