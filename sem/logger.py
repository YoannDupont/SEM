# -*- coding: utf-8 -*-

"""
file: logger.py

Description: basic logging utility for SEM.

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
logging_format = "%(levelname)s\t%(asctime)s\t%(name)s.%(module)s\t%(funcName)s\t%(message)s"
logging_formatter = logging.Formatter(fmt=logging_format)

default_handler = logging.StreamHandler()
default_handler.setFormatter(logging_formatter)

# The following allows to have only one logger for SEM.

logger = logging.getLogger("sem")
logger.addHandler(default_handler)
logger.setLevel("WARNING")

debug = logger.debug
info = logger.info
warning = logger.warning
error = logger.error
exception = logger.exception
critical = logger.critical
addHandler = logger.addHandler
setLevel = logger.setLevel
level = logger.level


def file_handler(filename, mode="a", encoding=None, delay=False):
    """A wrapper of logging.FileHandler that returns a logging.FileHandler with the SEM format"""
    handler = logging.FileHandler(filename, mode=mode, encoding=encoding, delay=delay)
    handler.setFormatter(logging_formatter)
    return handler
