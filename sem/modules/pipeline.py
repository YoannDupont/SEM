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

from .sem_module import SEMModule

class Pipeline(SEMModule):
    def __init__(self, pipes, log_level="WARNING", log_file=None, **kwargs):
        super(Pipeline, self).__init__(log_level=log_level, log_file=log_file, **kwargs)
        
        self._pipes = pipes
    
    def process_document(self, document, **kwargs):
        for pipe in self._pipes:
            pipe.process_document(document, **kwargs)
    
    @classmethod
    def from_xml(cls, xmlpipes):
        classes = {}
        pipes = []
        for xmlpipe in xmlpipes:
            if xmlpipe.tag == "export": continue
            
            Class = classes.get(xmlpipe.tag, None)
            if Class is None:
                Class = get_module(xmlpipe.tag)
                classes[xmlpipe.tag] = Class
            arguments = {}
            for key, value in xmlpipe.attrib.items():
                if value.startswith(u"~/"):
                    value = os.path.expanduser(value)
                elif sem.misc.is_relative_path(value):
                    value = os.path.abspath(os.path.join(os.path.dirname(master), value))
                arguments[key.replace(u"-", u"_")] = value
            for key, value in options.items():
                if key not in arguments:
                    arguments[key] = value
            pipes.append(Class(**arguments))
        pipeline = sem.modules.pipeline.Pipeline(pipes)