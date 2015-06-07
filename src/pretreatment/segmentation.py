import logging, codecs

from obj.tokeniser import Index_To_Bound, word_tokeniser, sentence_tokeniser
from obj.logger    import logging_format

segmentation_logger = logging.getLogger("sem.segmentation")

def segmentation(infile, outfile,
                 output_format="text",
                 ienc="utf-8", oenc="utf-8",
                 log_level=logging.CRITICAL, log_file=None):
    file_mode = u"a"
    if type(log_file) in (str, unicode):
        file_mode = u"w"
    
    logging.basicConfig(level=log_level, format=logging_format, filename=log_file, filemode=file_mode)
    
    number_of_tokens    = 0
    number_of_sentences = 0
    
    with codecs.open(outfile, "w", oenc) as O:
        segmentation_logger.info('segmenting "%s" content to "%s"', infile, outfile)
        joiner = (u" " if output_format=="line" else u"\n")
        for line in codecs.open(infile, "rU", ienc):
            line = line.lstrip(u"\ufeff") # BOM
            line = line.strip()
            for sentence in sentence_tokeniser(word_tokeniser(line)):
                number_of_sentences += 1
                number_of_tokens    += len(sentence)
                O.write(joiner.join(sentence) + u"\n")
                if output_format == "vector":
                    O.write(u"\n")
        segmentation_logger.info('segmented "%s" in %i sentences, %i tokens' %(infile, number_of_sentences, number_of_tokens))

if __name__ == "__main__":
    import argparse, os.path, sys

    parser = argparse.ArgumentParser(description="Segments the textual content of a sentence into tokens. They can either be outputted line per line or in a vectorised format")
    
    parser.add_argument("infile",
                        help="The input file (raw text)")
    parser.add_argument("outfile",
                        help="The output file")
    parser.add_argument("--output-format", dest="output_format", choices=("line", "vector"), default="line",
                        help="The output format (default: %(default)s)")
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

    if __package__:
        parser = parser.parse_args(sys.argv[2:])
    else:
        parser = parser.parse_args()
    
    if parser.log_level is None: parser.log_level = 0
    parser.log_level = min(parser.log_level, 5) * 10
    parser.log_level = 50 - parser.log_level
    
    segmentation(parser.infile, parser.outfile,
                 output_format=parser.output_format,
                 ienc=parser.ienc or parser.enc, oenc=parser.oenc or parser.enc,
                 log_level=parser.log_level, log_file=parser.log_file)
    sys.exit(0)