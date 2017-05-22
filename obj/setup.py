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

import re
import os
import os.path


def get_modules(path, root):
    def to_module_name(path):
        return os.path.splitext(os.path.relpath(path, root))[0].replace(os.path.sep, '.')

    def get(modules_path):
        res = dict()
        for dirpath, _, filenames in os.walk(modules_path):
            if '__init__.py' in filenames:
                modules_path = (f for f in filenames
                                if os.path.splitext(f)[1] == '.py' and not os.path.basename(f).startswith('_'))
                for m in modules_path:
                    m_name, m_path = os.path.splitext(os.path.basename(m))[0], os.path.join(dirpath, m)
                    if m_name in res:
                        raise ValueError('Module indexation crash, module "{m_name}" found twice:\n\t{m_path}\n\t{res_m_name}'.format(m_name=m_name, m_path=m_path, res_m_name=res[m_name]))
                    res[m_name] = m_path

        return res
    modules = get(os.path.join(root, path))
    return {m: to_module_name(p) for m, p in modules.items()}
