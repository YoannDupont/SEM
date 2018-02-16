# -*- coding: utf-8 -*-

"""
file: information.py

Description: an object to represent which features to add and where to
add them in a CoNLL corpus.

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

from xml.etree.ElementTree import ElementTree, tostring as element2string

from sem.features import XML2Feature
from sem.logger import default_handler

import os.path

tmp                = os.path.normpath(__file__).split(os.sep)
tmp                = u'.'.join(tmp[tmp.index("sem") : ]).rsplit(".",1)[0]
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
    
    @property
    def is_train(self):
        return self._mode in _train
    
    @property
    def is_label(self):
        return self._mode in _label
    
    @staticmethod
    def fromXML(xml_element):
        return Entry(**xml_element.attrib)
    
    def has_mode(self, mode):
        if len(_label & _equivalence[self._mode]) != 0: return True
        return len(_equivalence[self._mode] & _equivalence[mode]) != 0

class Informations(object):
    def __init__(self, path=None, bentries=None, aentries=None, features=None, mode=u"label"):
        self._mode     = mode
        self._bentries = [] # informations that are before newly added information
        self._aentries = [] # informations that are after ...
        self._features = [] # informations that are added
        self._names    = set()
        self._x2f      = None # the feature parser, initialised in parse
        
        if path is not None:
            self.parse(path)
        else:
            self._bentries = ([entry for entry in bentries if entry.has_mode(self._mode)] if bentries else self._bentries)
            self._aentries = ([entry for entry in aentries if entry.has_mode(self._mode)] if aentries else self._aentries)
            self._features = features
            self._names = set([entry.name for entry in self._aentries + self._bentries])
    
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
                    self._bentries.append(current_entry)
                elif entry.tag == "after" and current_entry.has_mode(self._mode):
                    self._aentries.append(current_entry)
        
        self._x2f = XML2Feature(self.bentries + self.aentries, path=filename)
        
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
    
    def enrich(self, keycorpus):
        """
        An iterator to enrich a corpus. It will go through the data and
        generate features, one feature at a time. If the feature has the
        is_sequence property, it be called once and enrich the whole
        sentence. If a feature does not have the is_sequence property, it
        will be called at each and every token.
        
        Parameters
        ----------
        keycorpus : list of list of dict / sem.storage.Corpus
            the input data, contains an object representing CoNLL-formatted
            data. Each token is a dict which works like TSV.
        
        Yields
        ------
        list of dict
            the current sentence enriched with informations
        """
        
        for p in keycorpus:
            for feature in self.features:
                if feature.is_sequence:
                    for i, value in enumerate(feature(p)):
                        p[i][feature.name] = value
                else:
                    for i in range(len(p)):
                        p[i][feature.name] = feature(p, i)
                        if feature.is_boolean:
                            p[i][feature.name] = int(p[i][feature.name])
                        elif p[i][feature.name] is None:
                            p[i][feature.name] = feature.default()
            yield p
    
    @property
    def bentries(self):
        return self._bentries
    
    @property
    def aentries(self):
        return self._aentries
    
    @property
    def features(self):
        return self._features
