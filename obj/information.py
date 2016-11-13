# -*- coding: utf-8 -*-

"""
file: information.py

Description: an object to represent which features to add and where to
add them in a CoNLL corpus.

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

import logging

from xml.etree.ElementTree import ElementTree, tostring as element2string

from obj.enrich.features.xml2feature import XML2Feature
from obj.logger                      import default_handler

import os.path

tmp                = os.path.normpath(__file__).split(os.sep)
tmp                = u'.'.join(tmp[tmp.index("obj") : ]).rsplit(".",1)[0]
xml2feature_logger = logging.getLogger("sem.%s" %tmp)
xml2feature_logger.addHandler(default_handler)
xml2feature_logger.setLevel("WARN")
del tmp

_train = set([u"train", u"eval", u"evaluate", u"evaluation"])
_label = set([u"label", u"annotate", u"annotation"])
_modes = _train | _label
_equivalence = dict([[mode, _train] for mode in _train] + [[mode, _label] for mode in _label])

class Entry(object):
    """
    The Entry object. It represents a field's identifier in a CoNLL corpus.
    An Entry may be used only in certain circumstances: for example, the
    output tag may only appear in train mode.
    """
    def __init__(self, name, mode=u"label"):
        if mode not in _modes:
            raise ValueError("Unallowed mode for entry: %s" %mode)
        self._name = name
        self._mode = mode
    
    def __eq__(self, other):
        return self.name == other.name
    
    @property
    def name(self):
        return self._name
    
    @property
    def mode(self):
        return self._mode
    
    @staticmethod
    def fromXML(xml_element):
        return Entry(**xml_element.attrib)
    
    def has_mode(self, mode):
        if len(_label & _equivalence[self._mode]) != 0: return True
        return len(_equivalence[self._mode] & _equivalence[mode]) != 0

class Informations(object):
    def __init__(self, path=None, mode=u"label"):
        self._mode     = mode
        self._bentries = [] # informations that are before newly added information
        self._aentries = [] # informations that are after ...
        self._features = [] # informations that are added
        self._names    = set()
        self._x2f      = None # the feature parser, initialised in parse
        
        if path is not None:
            self.parse(path)
    
    def parse(self, filename):
        parsing = ElementTree()
        parsing.parse(filename)
        
        children = parsing.getroot().getchildren()
        
        if len(children) != 2: raise RuntimeError("Enrichment file requires exactly 2 fields, %i given." %len(children))
        else:
            if children[0].tag != "entries":
                raise RuntimeError('Expected "entries" as first field, got "%s".' %children[0].tag)
            if children[1].tag != "features":
                raise RuntimeError('Expected "features" as second field, got "%s".' %children[1].tag)
        
        entries = list(children[0])
        if len(entries) not in (1,2):
            raise RuntimeError("Entries takes exactly 1 or 2 fields, %i given" %len(entries))
        else:
            entry1 = entries[0].tag.lower()
            entry2 = (entries[1].tag.lower() if len(entries)==2 else None)
            if entry1 not in ("before", "after"):
                raise RuntimeError('For entry position, expected "before" or "after", got "%s".' %entry1)
            if entry2 and entry2 not in ("before", "after"):
                raise RuntimeError('For entry position, expected "before" or "after", got "%s".' %entry2)
            if entry1 == entry2:
                raise RuntimeError('Both entry positions are the same, they should be different')
        
        for entry in entries:
            for c in entry.getchildren():
                current_entry = Entry.fromXML(c)
                self.check_entry(current_entry.name)
                if entry.tag == "before" and current_entry.has_mode(self._mode):
                    self._bentries.append(current_entry.name)
                elif entry.tag == "after" and current_entry.has_mode(self._mode):
                    self._aentries.append(current_entry.name)
        
        self._x2f = XML2Feature(self.aentries + self.bentries, path=filename)
        
        features = list(children[1])
        for feature in features:
            self._features.append(self._x2f.parse(feature))
            if self._features[-1].name is None:
                try:
                    raise ValueError("Nameless feature found.")
                except ValueError as exc:
                    for line in element2string(feature).rstrip().split("\n"):
                        xml2feature_logger.error(line.strip())
                    xml2feature_logger.exception(exc)
                    raise
            self.check_entry(self._features[-1].name)
    
    def check_entry(self, entry_name):
        if entry_name in self._names:
            raise ValueError('Duplicated column name: "' + entry_name + '"')
        else:
            self._names.add(entry_name)
    
    @property
    def bentries(self):
        return self._bentries
    
    @property
    def aentries(self):
        return self._aentries
    
    @property
    def features(self):
        return self._features
