#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
file: sem

Description: a wrapper for every module available in sem.

author: Yoann Dupont
copyright (c) 2013 Yoann Dupont - all rights reserved

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import logging
import os.path
import unittest
import sys

import sem
import sem.modules

from sem.logger import logging_format

sem_logger = logging.getLogger("sem")

def valid_module(m):
    return m.endswith(".py") and not (m.startswith(u"_") or m in ["sem_module.py", "pipeline.py"])

def find_suggestions(operation, ids):
    suggestions = []
    for name in ids:
        shortest = (name if len(name) < len(operation) else operation)
        longest  = (operation if shortest == name else name)
        if shortest in longest:
            suggestions.append(name)
    return suggestions

def main(args=None):
    modules = {}
    for element in os.listdir(os.path.join(sem.SEM_HOME, "modules")):
        m = element[:-3]
        if valid_module(element):
            modules[m] = sem.modules.get_package(m)
    #modules   = [element[:-3] for element in os.listdir(os.path.join(sem.SEM_HOME, "modules")) if valid_module(element)]
    name      = os.path.basename(sys.argv[0])
    operation = (sys.argv[1] if len(sys.argv) > 1 else "-h")

    if operation in modules:
        module = modules[operation]
        module.main(sem.argument_parser.parse_args())
    elif operation in ["-h", "--help"]:
        print "Usage: %s <module> [module arguments]\n" %name
        print "Module list:"
        for module in modules:
            print "\t%s" %module
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
            print "Did you mean one of the following ?"
            for suggestion in suggestions:
                print "\t%s" %suggestion
        else:
            print "No suggestions found... Try again?"

if __name__ == "__main__":
    main()