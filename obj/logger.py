import logging

logging_format    = u"%(levelname)s\t%(asctime)s\t%(name)s\t%(funcName)s\t%(message)s"
logging_formatter = logging.Formatter(fmt=logging_format)
