#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
file: __main__.py

Description: the entry point to SEM.

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

import pathlib
import unittest
import sys

import sem
import sem.modules
from sem.util import find_suggestions
from sem.tests import (test_features, test_processors, test_segmentation, test_workflows)


def main(argv=None):
    def banter():
        def username():
            import os

            return os.environ.get("USERNAME", os.environ.get("USER", pathlib.Path.home().name))

        import random

        banters = [
            "Do thou mockest me?",
            "Try again?",
            "I'm sorry {0}, I'm afraid I can't do that.".format(username()),
            "The greatest trick this module ever pulled was convincing the users it did not exist.",
            "It's just a typo.",
        ]
        return random.choice(banters)

    modules = {}
    for modulename in sem.modules.names():
        module = sem.modules.get_module(modulename)
        if hasattr(module, "main"):
            modules[modulename] = module
    name = pathlib.Path(sys.argv[0]).name
    operation = sys.argv[1] if len(sys.argv) > 1 else "-h"

    if operation in modules:
        module = modules[operation]
        module.main(sys.argv[2:])
    elif operation in ["-h", "--help"]:
        print("Usage: {0} <module> [module arguments]\n".format(name))
        print("Module list:")
        for module in sorted(modules):
            print("\t{0}".format(module))
        print()
        print("for SEM's current version: -v or --version\n")
        print("for informations about SEM: see readme.md")
        print("for playing all tests: --test")
    elif operation in ["-v", "--version"]:
        print(sem.full_name())
    elif operation == "--test":
        loader = unittest.TestLoader()
        testsuite = loader.loadTestsFromModule(test_features)
        testsuite.addTests(loader.loadTestsFromModule(test_processors))
        testsuite.addTests(loader.loadTestsFromModule(test_segmentation))
        testsuite.addTests(loader.loadTestsFromModule(test_workflows))
        unittest.TextTestRunner(verbosity=2).run(testsuite)
    else:
        print("Module not found: {}".format(operation))
        suggestions = find_suggestions(operation, modules)
        if len(suggestions) > 0:
            print("Did you mean one of the following?")
            for suggestion in suggestions:
                print("\t{0}".format(suggestion))
        else:
            print("No suggestions found...", banter())


if __name__ == "__main__":
    main()
