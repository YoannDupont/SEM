# -*- coding: utf-8 -*-

"""
file: logger.py

Description: basic SEM logging utility.

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

import logging

# the SEM logging format
logging_format    = u"%(levelname)s\t%(asctime)s\t%(name)s\t%(funcName)s\t%(message)s"
logging_formatter = logging.Formatter(fmt=logging_format)

# the default handler used by SEM to log on command-line
default_handler = logging.StreamHandler()
default_handler.setFormatter(logging_formatter)

# a wrapper of logging.FileHandler that return a logging.FileHandler with the SEM format
def file_handler(filename, mode="a", encoding=None, delay=False):
    handler = logging.FileHandler(filename, mode=mode, encoding=encoding, delay=delay)
    handler.setFormatter(logging_formatter)
    return handler
