# -*- encoding: utf-8-*-

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

import platform

from sem.constants import (  # noqa: F401
    SEM_DATA_DIR, SEM_RESOURCE_DIR, SEM_PIPELINE_DIR, SEM_HOMEPAGE, SEM_RESOURCE_BASE_URL
)
from sem.pipelines import (load, save, load_workflow)  # noqa: F401

SYSTEM = platform.system().lower()
ON_WINDOWS = SYSTEM == "windows"

_name = "SEM"

__version__ = "4.0.0-alpha.1"


def name():
    return _name


def version():
    return __version__


def full_name():
    return "{} v{}".format(name(), version())
