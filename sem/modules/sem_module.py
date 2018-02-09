#-*- coding: utf-8 -*-

"""
file: compile_dictionary.py

Description: serialize a dictionary written in a file. A dictionary file
is a file where every entry is on one line. There are two kinds of
dictionaries: token and multiword. A token dictionary will apply itself
on single tokens. A multiword dictionary will apply itself on sequences
of tokens.

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
from sem.storage.holder import Holder

class SEMModule(Holder):
    def __init__(self, log_level="WARNING", log_file=None, **kwargs):
        super(SEMModule, self).__init__(**kwargs)
        
        self._log_level = log_level
        self._log_file = log_file
    
    def process_document(self, document, **kwargs):
        raise NotImplementedError("process_document not implemented for root type " + self.__class__)