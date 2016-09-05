# -*- coding: utf-8 -*-

"""
file: setup.py

Description: sniffs for command line callable modules.

author: Yoann Dupont
copyright (c) 2016 Yoann Dupont - all rights reserved

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

import re, os.path
join = os.path.join

def get_modules(path):
    """
    Return the list of modules that can be called from command-line.
    They are sniffed in subdirectories of "src" containing
    an __init__.py file.
    """
    
    def to_module_name(name):
        return re.sub(r"[\\/]", ".", re.sub(r"^[./\\]+", "", elt[:-3], re.MULTILINE))
    
    def get(path):
        ids    = os.listdir(path)
        pathes = []
        
        if "__init__.py" in ids:
            ids    = sorted([module for module in ids if module.endswith(".py") and not module.startswith("_")])
            pathes = [join(path, module) for module in ids]
            ids    = [module[:-3] for module in ids]
            
            dirs   = [join(path, d) for d in os.listdir(path) if os.path.isdir(join(path, d))]
            
            for i in dirs:
                L, R = get(i)
                for i in xrange(len(L)):
                    m = L[i]
                    if m not in ids:
                        ids.append(m)
                    else:
                        raise ValueError("Module indexation crash, module \"" + m + "\" found twice:\n" +
                                         "    " + pathes[ids.index(m)] + "\n" +
                                         "    " + R[i])
                pathes.extend(R)
        else:
            del ids[:]
        
        return [ids, pathes]
    ids, pathes = get(path)
    pathes      = [to_module_name(elt) for elt in pathes]
    
    return [ids,pathes]
