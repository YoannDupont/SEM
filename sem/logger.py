# -*- coding: utf-8 -*-

"""
file: logger.py

Description: basic SEM logging utility.

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

import logging

# the SEM logging format(s)
logging_format    = u"%(levelname)s\t%(asctime)s\t%(name)s\t%(funcName)s\t%(message)s"
logging_formatter = logging.Formatter(fmt=logging_format)
extended_logging_format    = u"%(levelname)s\t%(asctime)s\t%(name)s\t%(funcName)s:%(lineno)d\t%(message)s"
extended_logging_formatter = logging.Formatter(fmt=extended_logging_format)

# the default handler used by SEM to log on command-line
default_handler = logging.StreamHandler()
default_handler.setFormatter(logging_formatter)
extended_handler = logging.StreamHandler()
extended_handler.setFormatter(extended_logging_formatter)

# a wrapper of logging.FileHandler that return a logging.FileHandler with the SEM format
def file_handler(filename, mode="a", encoding=None, delay=False):
    handler = logging.FileHandler(filename, mode=mode, encoding=encoding, delay=delay)
    handler.setFormatter(logging_formatter)
    return handler
