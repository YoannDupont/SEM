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

from src.pretreatment.segmentation import segmentation
from src.pretreatment.enrich       import enrich
from src.pretreatment.clean_info   import clean_info

import os.path
join     = os.path.join
basename = os.path.basename
dirname  = os.path.dirname

def tagger(masterfile):
    MASTER    = Master(masterfile)
    pipeline  = MASTER.pipeline
    options   = MASTER.options
    directory = MASTER.output_directory
    
    file_history   = []                # the files generated so far in the pipeline
    current_input  = MASTER.input_file # the current input in the pipeline
    current_output = u""               # the current output in the pipeline

    nth  = 1
    ienc = options.ienc
    oenc = options.oenc
    
    if pipeline[0].identifier == u"segmentation":
        current_output = join(directory, basename(current_input) + ".segmentation")
        
        segmentation(current_input, current_output)
        
        current_input  = current_output
        nth           += 1
        pipeline       = pipeline[1:]
    
    for process in pipeline:
        # segmentation may only be first. If we are in this loop, a segmentation
        # cannot occur as it was handled before.
        if process.identifier == u"segmentation":
            raise RuntimeError(u"Segmentation can only be performed first. Asked as process number %d" %nth)
            
        elif process.identifier == u"enrich":
            information    = join(dirname(masterfile), process.args["config"])
            current_output = join(directory, basename(current_input) + "." + basename(information[:-4]))
            
            enrich(current_input, information, current_output, ienc=ienc, oenc=oenc)
            
        elif process.identifier == u"label":
            model          = join(dirname(masterfile), process.args["model"])
            current_output = join(directory, basename(current_input) + "." + basename(model))
            
            Wapiti.label(current_input, model, output=current_output)
            
        elif process.identifier == u"clean_info":
            current_output = join(directory, basename(current_input) + ".clean")
            clean_info(current_input, current_output, process.args["to-keep"], ienc=ienc, oenc=oenc)
            
        else:
            raise RuntimeError(u'Unknown process "%s"' %process.identifier)
        
        if nth > 1:      file_history.append(current_input)
        if ienc != oenc: ienc = oenc
        current_input  = current_output
        current_output = None
        
        nth += 1
    
    if options.clean:
        for filename in file_history:
            os.remove(filename)


if __name__ == '__main__':
    import argparse, sys
    parser = argparse.ArgumentParser(description="Performs various operations given in a master configuration file that defines a pipeline.")
    
    parser.add_argument("master",
                        help="The master configuration file. Defines at least the pipeline and may provide some options.")
    
    if not __package__:
        parser = parser.parse_args()
    else:
        parser = parser.parse_args(sys.argv[2:])
    
    tagger(parser.master)
    sys.exit(0)
