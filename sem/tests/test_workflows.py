#-*- encoding: utf-8 -*-

"""
file: test_workflows.py

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

from __future__ import print_function

import unittest
import os.path
import sys

from sem import SEM_RESOURCE_DIR

from sem.storage import Document, Corpus, Holder

import sem.modules.tagger

document = Document("document", "Ceci est un test.")
corpus = Corpus([u"word"], sentences=[[
    {u"word":u"Ceci"},
    {u"word":u"est"},
    {u"word":u"un"},
    {u"word":u"test"},
    {u"word":u"."}
]])
document._corpus = corpus

def launch(path_to_master):
    pipeline, options, exporter, couples = sem.modules.tagger.load_master(
        path_to_master
    )
    
    args = Holder(
        pipeline = pipeline,
        options = options,
        exporter = None,
        couples = couples,
        infiles = [document]
    )
    
    sem.modules.tagger.main(args)

class TestWorkflows(unittest.TestCase):
    def test_pos(self):
        launch(os.path.join(SEM_RESOURCE_DIR, "master", "fr", "pos.xml"))
    
    def test_pos_leff(self):
        launch(os.path.join(SEM_RESOURCE_DIR, "master", "fr", "pos-lefff.xml"))
    
    def test_chunking(self):
        launch(os.path.join(SEM_RESOURCE_DIR, "master", "fr", "chunking.xml"))
    
    def test_no_chunking(self):
        launch(os.path.join(SEM_RESOURCE_DIR, "master", "fr", "np_chunking.xml"))
    
    def test_ner(self):
        launch(os.path.join(SEM_RESOURCE_DIR, "master", "fr", "NER.xml"))

if __name__ == '__main__':
    unittest.main(verbosity=2)
