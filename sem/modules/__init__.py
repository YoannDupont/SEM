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

from importlib import import_module as _import_module
import warnings as _warnings


__all__ = [
    "annotate",
    "augment_wapiti_model",
    "annotation_gui",
    "clean",
    "download",
    "enrich",
    "evaluate",
    "export",
    "gui",
    "label_consistency",
    "map_annotations",
    "pymorphy",
    "segmentation",
    "tagger",
    "wapiti_label",
    "workflow_to_pipeline",
]


def names():
    return __all__[:]


def get_module(name):
    module = _import_module("sem.modules.{0}".format(name))
    return module


def get_package(name):
    _warnings.filterwarnings("always", category=DeprecationWarning)
    _warnings.warn("'get_package' is deprecated, use 'get_module' instead", DeprecationWarning)
    _warnings.filterwarnings("default", category=DeprecationWarning)
    return get_module(name)
