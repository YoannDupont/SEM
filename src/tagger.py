#-*- coding: utf-8 -*-

"""
file: tagger.py

Description: performs a sequence of operations in a pipeline.

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
along with this program. If not, see GNU official website.
"""

import codecs, logging, os, shutil

# measuring time laps
import time
from datetime import timedelta

from os.path import join, basename, dirname

import software

from obj import wapiti

from obj.master_parser    import Master
from obj.logger           import logging_format, default_handler
from obj.storage.document import Document
from obj.information      import Informations

from src.pretreatment.segmentation import segmentation, document_segmentation
from src.pretreatment.enrich       import enrich_file, document_enrich
from src.posttreatment.clean_info  import clean_info, document_clean
from src.posttreatment.export      import export

sem_tagger_logger = logging.getLogger("sem.tagger")
sem_tagger_logger.addHandler(default_handler)

def tagger(masterfile, file_name, directory="."):
    """
    Return a document after it passed through a pipeline.
    
    Parameters
    ----------
    masterfile : str
        the file containing the pipeline and global options
    file_name : str
        the input for the upcoming pipe. Its base value is the file to
        treat, it can be either "plain text" or CoNNL-formatted file.
    directory : str
        the directory where every file will be outputted.
    """
    
    start = time.time()
    
    MASTER   = Master(masterfile)
    pipeline = MASTER.pipeline
    options  = MASTER.options
    
    if (options.log_file is not None):
        segmentation_logger.addHandler(file_handler(log_file))
    sem_tagger_logger.setLevel(options.log_level)
    
    exports           = {} # keeping track of already done exports
    file_shortname, _ = os.path.splitext(basename(file_name))
    export_name       = os.path.join(directory, file_shortname)
    
    nth  = 1
    ienc = options.ienc
    oenc = options.oenc
    
    sem_tagger_logger.info("Reading %s" %(file_name))
    
    document = Document(basename(file_name), content=codecs.open(file_name, "rU", ienc).read())
    
    if pipeline[0].identifier == u"segmentation":
        document_segmentation(document, pipeline[0].args["name"], log_level=options.log_level, log_file=options.log_file)
        
        nth      += 1
        pipeline  = pipeline[1:]
    
    for process in pipeline:
        # segmentation may only be first. If we are in this loop, a segmentation
        # cannot occur as it was handled before.
        if process.identifier == u"segmentation":
            raise RuntimeError(u"Segmentation can only be performed first. Asked as process number %d" %nth)
            
        elif process.identifier == u"clean_info":
            document_clean(document, process.args["to-keep"], log_level=options.log_level, log_file=options.log_file)
            
        elif process.identifier == u"enrich":
            information = join(dirname(masterfile), process.args["config"])
            
            document_enrich(document, information, log_level=options.log_level, log_file=options.log_file)
            
        elif process.identifier == u"label":
            model = join(dirname(masterfile), process.args["model"])
            field = process.args["field"]
            
            sem_tagger_logger.info("labeling %s with wapiti" %(field))
            label_start = time.clock()
            wapiti.label_document(document, model, field, oenc)
            label_laps  = time.clock() - label_start
            sem_tagger_logger.info("labeled in %s" %(timedelta(seconds=label_laps)))
            
        elif process.identifier == u"textualise":
            poscol   = int(process.args.get("pos", 0))
            chunkcol = int(process.args.get("chunk", 0))
            
            textualise(current_input, current_output, pos_column=poscol, chunk_column=chunkcol, ienc=oenc, oenc=oenc, log_level=options.log_level, log_file=options.log_file)
            
        elif process.identifier == u"export":
            export_format = process.args.get("format", "conll")
            poscol        = process.args.get("pos", None)
            chunkcol      = process.args.get("chunking", None)
            nercol        = process.args.get("ner", None)
            lang          = process.args.get("lang", "fr")
            lang_style    = process.args.get("lang_style", "default.css")
            
            if export_format not in exports:
                exports[export_format] = 0
            exports[export_format] += 1
            current_output = export_name + ".export-%i.%s" %(exports[export_format], export_format)
            
            export(document, export_format, current_output, lang=lang, lang_style=lang_style, pos_column=poscol, chunk_column=chunkcol, ner_column=nercol, ienc=oenc, oenc=oenc, log_level=options.log_level, log_file=options.log_file)
            
            if export_format in ("html"):
                shutil.copy(os.path.join(software.SEM_HOME, "resources", "css", "tabs.css"), directory)
                shutil.copy(os.path.join(software.SEM_HOME, "resources", "css", lang, lang_style), directory)
        else:
            sem_tagger_logger.error(u'unknown process: "%s"' %process.identifier)
            raise RuntimeError(u'unknown process: "%s"' %process.identifier)
        
        if ienc != oenc:
            ienc = oenc
        
        nth += 1
    
    if not any([process.identifier == "export" for process in pipeline]): # no export asked
        if __name__ == "__main__": # we only export something if the module is called from command-line
            sem_tagger_logger.warn("no export in pipeline, exporting to conll by default")
            export(document, "conll", export_name + ".conll", ienc=ienc, oenc=oenc, log_level=options.log_level, log_file=options.log_file)
    
    laps = time.time() - start
    sem_tagger_logger.info('done in %s' %(timedelta(seconds=laps)))
    
    return document


if __name__ == '__main__':
    import argparse, sys
    parser = argparse.ArgumentParser(description="Performs various operations given in a master configuration file that defines a pipeline.")
    
    parser.add_argument("master",
                        help="The master configuration file. Defines at least the pipeline and may provide some options.")
    parser.add_argument("input_file",
                        help="The input file for the tagger.")
    parser.add_argument("-o", "--output-directory", dest="output_directory", default=".",
                        help="The output directory (default: '.')")
    
    if not __package__:
        args = parser.parse_args()
    else:
        args = parser.parse_args(sys.argv[2:])
    
    tagger(args.master, args.input_file,
           directory=args.output_directory)
    sys.exit(0)
