"""
file: workflow_to_pipeline.py

author: Yoann Dupont

MIT License

Copyright (c) 2021 Yoann Dupont

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

import argparse
from sem.pipelines import (load_workflow, save)


def main(argv=None):
    workflow_to_pipeline(**vars(parser.parse_args(argv)))


def workflow_to_pipeline(inputfile, outputfile, force=False):
    outputmode = ("w" if force else "x")
    p, _, _, _ = load_workflow(inputfile)
    save(p, outputfile, outputmode)


parser = argparse.ArgumentParser("Create a serialized pipeline file from a workflow file.")
parser.add_argument("inputfile", help="The input workflow file (XML).")
parser.add_argument("outputfile", help="The output pipeline file (binary).")
parser.add_argument("-f", "--force", action="store_true", help="Overwrite outputfile if it exists.")
