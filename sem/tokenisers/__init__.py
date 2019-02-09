"""
file: __init__.py

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

from sem.storage import Span

try:
    from importlib import import_module
except ImportError: # backward compatibility for python < 2.7
    def import_module(module_name):
        return __import__(module_name, fromlist=module_name.rsplit(".", 1)[0])


def get_tokeniser(name):
    return import_module("sem.tokenisers.{}".format(name))


def bounds2spans(bounds):
    """
    creates spans from bounds
    """
    spans = [Span(bounds[i].ub, bounds[i+1].lb) for i in range(0, len(bounds)-1)]
    spans = [span for span in spans if span.lb != span.ub]
    return spans
