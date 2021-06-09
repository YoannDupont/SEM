# -*- coding: utf-8 -*-

"""
file: sem_module.py

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

import sem.logger


DEFAULT_LICENSE = (
    "No license provided.\n"
    "Unless you find contradictory information from an official source,"
    " this is provided for research, teaching and personal use only,"
    " it may not be used for any other purpose."
)


class SEMModule:
    def __init__(self, pipeline_mode="all", license=None, **kwargs):
        super(SEMModule, self).__init__(**kwargs)

        self._pipeline_mode = pipeline_mode
        self._license = license or DEFAULT_LICENSE

    @property
    def pipeline_mode(self):
        return self._pipeline_mode

    @property
    def license(self):
        return self._license

    @license.setter
    def license(self, license):
        if self._license and self._license != DEFAULT_LICENSE:
            sem.logger.warning("changing non default license.")
        self._license = license

    def check_mode(self, expected_mode):
        pass

    def process_document(self, document, **kwargs):
        raise NotImplementedError(
            "process_document not implemented for root type {}".format(self.__class__)
        )
