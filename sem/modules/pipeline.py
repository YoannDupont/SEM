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

import logging
import multiprocessing
import functools

from .sem_module import SEMModule
from sem.logger import default_handler, file_handler

pipeline_logger = logging.getLogger("sem.pipeline")
pipeline_logger.addHandler(default_handler)

class Pipeline(SEMModule):
    def __init__(self, pipes, log_level="WARNING", log_file=None, pipeline_mode="all", **kwargs):
        super(Pipeline, self).__init__(log_level=log_level, log_file=log_file, **kwargs)
        
        self._pipes = pipes
        self._pipeline_mode = pipeline_mode
    
    def __iter__(self):
        for pipe in self._pipes:
            yield pipe
    
    def __len__(self):
        return len(self._pipes)
    
    @property
    def pipes(self):
        return self._pipes
    
    @property
    def pipeline_mode(self):
        return self._pipeline_mode
    
    @pipeline_mode.setter
    def pipeline_mode(self, mode):
        self.pipeline_mode = mode
        for pipe in self._pipes:
            pipe.check_mode(self.pipeline_mode)
    
    def append(self, pipe):
        self._pipes.append(pipe)
    
    def remove(self, pipe):
        self._pipes.remove(pipe)
    
    def process_document(self, document, **kwargs):
        for pipe in self._pipes:
            if self.pipeline_mode == "all" or pipe.pipeline_mode in ("all", self.pipeline_mode):
                pipe.process_document(document, **kwargs)
            else:
                pipeline_logger.warn(u"pipe %s not executed", pipe)
        return document # allows multiprocessing
