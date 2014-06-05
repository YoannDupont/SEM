from obj.misc   import ranges_to_set
from obj.logger import log

import codecs

def clean_info(infile, outfile, ranges,
               ienc="utf-8", oenc="utf-8", verbose=False):
    allowed = ranges_to_set(ranges, codecs.open(infile, "rU", ienc).readline().strip().split())
    
    if verbose:
        log('Cleaning "%s"...' %infile)
        
    with codecs.open(outfile, "w", oenc) as O:
        for line in codecs.open(infile, "rU", ienc):
            line = line.strip().split()
            if line != []:
                tokens = [line[i] for i in xrange(len(line)) if i in allowed]
                O.write(u"\t".join(tokens))
            O.write(u"\n")
    
    if verbose:
        log(' Done.\n')

if __name__ == "__main__":
    import argparse, sys

    parser = argparse.ArgumentParser(description="...")

    parser.add_argument("infile",
                        help="The input file")
    parser.add_argument("outfile",
                        help="The output file ")
    parser.add_argument("ranges",
                        help="The ranges of indexes to keep in the file.")
    parser.add_argument("--input-encoding", dest="ienc",
                        help="Encoding of the input (default: UTF-8)")
    parser.add_argument("--output-encoding", dest="oenc",
                        help="Encoding of the input (default: UTF-8)")
    parser.add_argument("--encoding", dest="enc", default="UTF-8",
                        help="Encoding of both the input and the output (default: UTF-8)")
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true",
                        help="Basic feedback for user (default: False).")
    
    arguments = (sys.argv[2:] if __package__ else sys.argv)
    parser    = parser.parse_args(arguments)
    
    clean_info(parser.infile, parser.outfile, parser.ranges,
               ienc=parser.ienc or parser.enc, oenc=parser.oenc or parser.enc, verbose=parser.verbose)
    sys.exit(0)
