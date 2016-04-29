#-*- coding: utf-8 -*-

"""
file: enrich.py

Description: 

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
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import logging, time

from obj.information import Informations
from obj.IO.KeyIO    import KeyReader, KeyWriter
from obj.misc        import to_dhms


import os.path
enrich_logger = logging.getLogger("sem.%s" %os.path.basename(__file__).split(".")[0])

def enrich(keycorpus, informations):
    for p in keycorpus:
        for feature in informations.features:
            if feature.is_sequence:
                for i, value in enumerate(feature(p)):
                    p[i][feature.name] = value
            else:
                for i in range(len(p)):
                    p[i][feature.name] = feature(p, i)
                    if feature.is_boolean:
                        p[i][feature.name] = int(p[i][feature.name])
        yield p

def enrich_file(infile, infofile, outfile,
                ienc="UTF-8", oenc="UTF-8",
                log_level="WARNING", log_file=None):
    start = time.time()
    
    enrich_logger.setLevel(log_level)
    enrich_logger.info('parsing enrichment file "%s"' %infofile)
    
    informations = Informations(infofile)
    
    enrich_logger.debug('enriching file "%s"' %infile)
    
    with KeyWriter(outfile, oenc, informations.bentries + [feature.name for feature in informations.features if feature.display] + informations.aentries) as O:
        nth = 0
        for p in enrich(KeyReader(infile, ienc, informations.bentries + informations.aentries), informations):
            O.write_p(p)
            nth += 1
            if (0 == nth % 1000):
                enrich_logger.debug('%i sentences enriched' %nth)
        enrich_logger.debug('%i sentences enriched' %nth)
    
    enrich_logger.info("done in %s", to_dhms(time.time() - start))



if __name__ == "__main__":
    import argparse, sys

    parser = argparse.ArgumentParser(description="Adds information to a file using and XML-styled configuration file.")

    parser.add_argument("infile",
                        help="The input file (CoNLL format)")
    parser.add_argument("infofile",
                        help="The information file (XML format)")
    parser.add_argument("outfile",
                        help="The output file (CoNLL format)")
    parser.add_argument("--input-encoding", dest="ienc",
                        help="Encoding of the input (default: UTF-8)")
    parser.add_argument("--output-encoding", dest="oenc",
                        help="Encoding of the input (default: UTF-8)")
    parser.add_argument("--encoding", dest="enc", default="UTF-8",
                        help="Encoding of both the input and the output (default: UTF-8)")
    parser.add_argument("-l", "--log", dest="log_level", choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"), default="WARNING",
                        help="Increase log level (default: critical)")
    parser.add_argument("--log-filename", dest="log_filename",
                        help="The name of the log file")
    
    if __package__:
        args = parser.parse_args(sys.argv[2:])
    else:
        args = parser.parse_args()
    
    enrich_file(args.infile, args.infofile, args.outfile,
                ienc=args.ienc or args.enc, oenc=args.oenc or args.enc,
                log_level=args.log_level, log_file=args.log_filename)
    sys.exit(0)
