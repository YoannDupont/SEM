#-------------------------------------------------------------------------------
#
# file: __init__.py
#
# Description: an __init__ file to allow the use of python sources as modules
#
# author: Yoann Dupont
# copyright (c) 2016 Yoann Dupont - all rights reserved
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#-------------------------------------------------------------------------------

from brat import Exporter as BratExporter
from conll import Exporter as CoNLLExporter
from gate import Exporter as GateExporter
from html import Exporter as HTMLExporter
from jason import Exporter as JSONExporter
from sem_xml import Exporter as SEMExporter
from tei import Exporter as TEIExporter
from tei_np import Exporter as TEINPExporter
from text import Exporter as TextExporter

try:
    from importlib import import_module
except ImportError: # backward compatibility for python < 2.7
    def import_module(module_name):
        return __import__(module_name, fromlist=module_name.rsplit(".", 1)[0])

def get_exporter(name):
    module = import_module("sem.exporters.%s" %name)
    return module.Exporter
    """try:
        module = import_module("sem.exporters.%s" %name)
        return module.Exporter
    except ImportError, e:
        raise ImportError('Could import exporter "%s": %s' %(name,e))"""