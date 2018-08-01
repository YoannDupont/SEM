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

import logging
import os.path
import unittest
import sys

import sem
import sem.modules

from sem.logger import logging_format
from sem.misc import find_suggestions

sem_logger = logging.getLogger("sem")

def valid_module(m):
    return m.endswith(".py") and not (m.startswith(u"_") or m in ["sem_module.py", "pipeline.py"])

def main(args=None):
    def banter():
        def username():
            import os
            return os.environ.get("USERNAME", os.environ.get("USER", os.path.split(os.path.expanduser(u"~"))[-1]))
        import random
        l = [
            u"Do thou mockest me?",
            u"Try again?",
            u"I'm sorry {0}, I'm afraid I can't do that.".format(username()),
            u'The greatest trick this module ever pulled what convincing the users it did not exist.',
            u"It's just a typo."
        ]
        random.shuffle(l)
        return l[0]
        
    modules = {}
    for element in os.listdir(os.path.join(sem.SEM_HOME, "modules")):
        m = element[:-3]
        if valid_module(element):
            modules[m] = sem.modules.get_package(m)
    name = os.path.basename(sys.argv[0])
    operation = (sys.argv[1] if len(sys.argv) > 1 else "-h")

    if operation in modules:
        module = modules[operation]
        module.main(sem.argument_parser.parse_args())
    elif operation in ["-h", "--help"]:
        print "Usage: {0} <module> [module arguments]\n".format(name)
        print "Module list:"
        for module in modules:
            print "\t{0}".format(module)
        print
        print "for SEM's current version: -v or --version\n"
        print "for informations about the last revision: -i or --informations"
        print "for playing all tests: --test"
    elif operation in ["-v", "--version"]:
        print sem.full_name()
    elif operation in ["-i", "--informations"]:
        informations = sem.informations()
        try:
            print informations
        except UnicodeEncodeError:
            print informations.encode(sys.getfilesystemencoding(), errors="replace")
    elif operation == "--test":
        testsuite = unittest.TestLoader().discover(os.path.join(sem.SEM_HOME, "tests"))
        unittest.TextTestRunner(verbosity=2).run(testsuite)
    else:
        print "Module not found: " + operation
        suggestions = find_suggestions(operation, modules)
        if len(suggestions) > 0:
            print "Did you mean one of the following?"
            for suggestion in suggestions:
                print "\t{0}".format(suggestion)
        else:
            print "No suggestions found...", banter()

if __name__ == "__main__":
    main()
