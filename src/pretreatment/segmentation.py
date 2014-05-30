from obj.segmentation import Segmentation
from obj.corpus       import ICorpus, OCorpus
from obj.logger       import log

def segmentation(infile, outfile, verbose=False):
    segmenter = Segmentation(ICorpus(infile), OCorpus(outfile))
    
    if verbose:
        log('Segmenting "%s"...' %infile)
    
    segmenter.segmentation()
    
    if verbose:
        log('done.\n')
    

if __name__ == '__main__':
    import sys, argparse
    
    parser = argparse.ArgumentParser(description=u"Segments a text into tokens and separates sentences.")
    
    parser.add_argument("infile", type=str, help="the input file.")
    parser.add_argument("outfile", type=str, help="the output file.")
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true",
                        help="Basic feedback for user (default: False).")
    
    arguments = (sys.argv[2:] if __package__ else sys.argv)
    parser    = parser.parse_args(arguments)
    segmentation(parser.infile, parser.outfile, verbose=parser.verbose)
    sys.exit(0)
