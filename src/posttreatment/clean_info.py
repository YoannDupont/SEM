import logging, codecs

from obj.misc   import ranges_to_set
from obj.logger import logging_format

clean_info_logger = logging.getLogger("sem.clean_info")

def clean_info(infile, outfile, ranges,
               ienc="utf-8", oenc="utf-8",
               log_level=logging.CRITICAL, log_file=None):
    file_mode = u"a"
    if type(log_file) in (str, unicode):
        file_mode = u"w"
    logging.basicConfig(level=log_level, format=logging_format, filename=log_file, filemode=file_mode)
    
    allowed = ranges_to_set(ranges, len(codecs.open(infile, "rU", ienc).readline().strip().split()), include_zero=True)
    max_abs = 0
    for element in allowed:
        element = abs(element) + (1 if element > 0 else 0)
        max_abs = max(max_abs, element)
    nelts = len(codecs.open(infile, "rU", ienc).readline().strip().split())
    
    if nelts < max_abs:
        clean_info_logger.error(u'asked to keep up to %i field(s), yet only %i are present in the "%s"' %(max_abs, nelts, infile))
        raise runtimeError(u'asked to keep up to %i field(s), yet only %i are present in the "%s"' %(max_abs, nelts, infile))
    
    clean_info_logger.info(u'cleaning "%s" to "%s"' %(infile,outfile))
    clean_info_logger.info(u'keeping columns: %s' %(u", ".join([str(s) for s in sorted(allowed)])))
        
    with codecs.open(outfile, "w", oenc) as O:
        for line in codecs.open(infile, "rU", ienc):
            line = line.strip().split()
            if line != []:
                tokens = [line[i] for i in xrange(len(line)) if i in allowed]
                O.write(u"\t".join(tokens))
            O.write(u"\n")
    
    clean_info_logger.info(u'done')

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
    parser.add_argument("-l", "--log", dest="log_level", action="count",
                        help="Increase log level (default: critical)")
    parser.add_argument("--log-file", dest="log_file",
                        help="The name of the log file")
    
    arguments = (sys.argv[2:] if __package__ else sys.argv)
    parser    = parser.parse_args(arguments)
    
    clean_info(parser.infile, parser.outfile, parser.ranges,
               ienc=parser.ienc or parser.enc, oenc=parser.oenc or parser.enc,
               log_level=parser.log_level, log_file=parser.log_file)
    sys.exit(0)
