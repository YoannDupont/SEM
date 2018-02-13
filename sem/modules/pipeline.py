#-*- coding: utf-8 -*-

"""
file: pipeline.py

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
