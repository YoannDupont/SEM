#! /usr/bin/python
#-*- coding: utf-8 -*-

"""
file: tag.py

Description: performs a sequence of operations in a pipe given a configuration
file.

author: Yoann Dupont
copyright (c) 2014 Yoann Dupont - all rights reserved

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

from obj.master_parser import Master
from obj.wapiti        import Wapiti
from obj.logger        import log

from src.pretreatment.segmentation import segmentation
from src.pretreatment.enrich       import enrich

from src.posttreatment.clean_info   import clean_info
from src.posttreatment.textualise   import textualise

import os.path
join     = os.path.join
basename = os.path.basename
dirname  = os.path.dirname

def tagger(masterfile, current_input, directory="."):
    MASTER    = Master(masterfile)
    pipeline  = MASTER.pipeline
    options   = MASTER.options
    
    file_history   = []  # the files generated so far in the pipeline
    current_output = u"" # the current output in the pipeline
    
    nth  = 1
    ienc = options.ienc
    oenc = options.oenc
    
    if pipeline[0].identifier == u"segmentation":
        current_output = join(directory, basename(current_input) + ".segmentation")
        
        segmentation(current_input, current_output, verbose=options.verbose)
        
        current_input  = current_output
        nth           += 1
        pipeline       = pipeline[1:]
        
        if options.verbose:
            log('\n')
    
    for process in pipeline:
        # segmentation may only be first. If we are in this loop, a segmentation
        # cannot occur as it was handled before.
        if process.identifier == u"segmentation":
            raise RuntimeError(u"Segmentation can only be performed first. Asked as process number %d" %nth)
            
        elif process.identifier == u"clean_info":
            current_output = join(directory, basename(current_input) + ".clean")
            clean_info(current_input, current_output, process.args["to-keep"], ienc=ienc, oenc=oenc, verbose=options.verbose)
            
        elif process.identifier == u"enrich":
            information    = join(dirname(masterfile), process.args["config"])
            current_output = join(directory, basename(current_input) + "." + basename(information[:-4]))
            
            enrich(current_input, information, current_output, ienc=ienc, oenc=oenc, verbose=options.verbose)
            
        elif process.identifier == u"label":
            model          = join(dirname(masterfile), process.args["model"])
            current_output = join(directory, basename(current_input) + "." + basename(model))
            
            Wapiti.label(current_input, model, output=current_output)
            
        elif process.identifier == u"textualise":
            poscol         = int(process.args["pos"]) if "pos" in process.args else 0
            chunkcol       = int(process.args["chunk"]) if "chunk" in process.args else 0
            current_output = join(directory, basename(current_input) + ".textualise")
            
            textualise(current_input, current_output, pos_column=poscol, chunk_column=chunkcol, ienc=oenc, oenc=oenc, verbose=options.verbose)
            
        else:
            raise RuntimeError(u'Unknown process "%s"' %process.identifier)
        
        if options.verbose:
            log("\n")
        
        if nth > 1:      file_history.append(current_input)
        if ienc != oenc: ienc = oenc
        current_input  = current_output
        current_output = None
        
        nth += 1
    
    if options.clean:
        if options.verbose:
            log("Cleaning files...")
        for filename in file_history:
            os.remove(filename)
        if options.verbose:
            log(" Done.\n")


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
        parser = parser.parse_args()
    else:
        parser = parser.parse_args(sys.argv[2:])
    
    tagger(parser.master, parser.input_file,
           directory=parser.output_directory)
    sys.exit(0)
