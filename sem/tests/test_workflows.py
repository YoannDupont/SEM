# -*- encoding: utf-8 -*-

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

import unittest

from sem import SEM_RESOURCE_DIR
from sem.storage import Document
import sem.pipelines


def launch(path_to_workflow):
    document = Document("document", "Ceci est un test.")
    pipeline, options, exporter, couples = sem.pipelines.load_workflow(path_to_workflow)
    pipeline.process_document(document)


class TestWorkflows(unittest.TestCase):
    def test_pos(self):
        path = SEM_RESOURCE_DIR / "workflow" / "fr" / "pos.xml"
        if not path.exists():
            self.skipTest(f"{path.name} workflow not found.")
        launch(path)

    def test_pos_leff(self):
        path = SEM_RESOURCE_DIR / "workflow" / "fr" / "pos-lefff.xml"
        if not path.exists():
            self.skipTest(f"{path.name} workflow not found.")
        launch(path)

    def test_chunking(self):
        path = SEM_RESOURCE_DIR / "workflow" / "fr" / "chunking.xml"
        if not path.exists():
            self.skipTest(f"{path.name} workflow not found.")
        launch(path)

    def test_np_chunking(self):
        path = SEM_RESOURCE_DIR / "workflow" / "fr" / "np_chunking.xml"
        if not path.exists():
            self.skipTest(f"{path.name} workflow not found.")
        launch(path)

    def test_ner(self):
        path = SEM_RESOURCE_DIR / "workflow" / "fr" / "NER.xml"
        if not path.exists():
            self.skipTest(f"{path.name} workflow not found.")
        launch(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
