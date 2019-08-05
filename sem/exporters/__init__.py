"""
file: __init__.py

Description: an __init__ file to allow the use of python sources as modules

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

from sem.exporters.brat import Exporter as BratExporter
from sem.exporters.conll import Exporter as CoNLLExporter
from sem.exporters.gate import Exporter as GateExporter
from sem.exporters.html import Exporter as HTMLExporter
from sem.exporters.jason import Exporter as JSONExporter
from sem.exporters.sem_xml import Exporter as SEMExporter
from sem.exporters.tei_analec import Exporter as AnalecTEIExporter
from sem.exporters.tei_reden import Exporter as REDENTEIExporter
from sem.exporters.tei_np import Exporter as TEINPExporter
from sem.exporters.text import Exporter as TextExporter

try:
    from importlib import import_module
except ImportError:  # backward compatibility for python < 2.7

    def import_module(module_name):
        return __import__(module_name, fromlist=module_name.rsplit(".", 1)[0])


def get_exporter(name):
    module = import_module("sem.exporters.{0}".format(name))
    return module.Exporter
