# -*- coding: utf-8 -*-

"""
file: ontologyfeatures.py

Description: defines features related to taxonomies.

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
along with this program. If not, see GNU official website.
"""

import os

import xml.etree.ElementTree

from feature            import Feature
from . import DEFAULT_GETTER, DictGetterFeature
from . import MultiwordDictionaryFeature, MapperFeature
from . import TriggeredFeature
from . import SubsequenceFeature

class OntologyFeature(Feature):
    def __init__(self, path, x2f, order=".order", ambiguous=False, *args, **kwargs):
        super(OntologyFeature, self).__init__(self, *args, **kwargs)
        self._is_sequence = True
        self._ambiguous   = ambiguous
        
        order = order or ".order"
        
        self.path     = os.path.abspath(os.path.expanduser(path))
        self.order    = []
        self.features = []
        
        names = os.listdir(self.path)
        if order in names:
            for line in open(os.path.join(self.path, order), "rU"):
                line = line.strip()
                if "#" in line:
                    line = line[ : line.index("#")].strip()
                if line:
                    self.order.append(line)
        else:
            self.order = [name for name in names if not name.startswith(".")]
        
        self.order = self.order[::-1]
        
        for name in self.order:
            self.features.append(x2f.parse(xml.etree.ElementTree.fromstring(open(os.path.join(self.path, name), "rU").read())))
            self.features[-1]._name = name
            if not (self.features[-1].is_boolean or self.features[-1].is_sequence or isinstance(self.features[-1], MapperFeature) or (isinstance(self.features[-1], TriggeredFeature) and isinstance(self.features[-1].operation, MapperFeature)) or (isinstance(self.features[-1], SubsequenceFeature))):
                raise ValueError("In %s feature: %s is neither boolean nor sequence" %(self.name, name))
            if isinstance(self.features[-1], MultiwordDictionaryFeature):
                self.features[-1]._appendice = "-%s" %(name)
    
    def __call__(self, list2dict, *args, **kwargs):
        data = ["O"]*len(list2dict)
        
        for feature in self.features:
            name = feature.name
            if feature.is_boolean:
                for x in range(len(list2dict)):
                    if feature(list2dict, x):
                        if not self._ambiguous or data[x] == u"O":
                            data[x] = name
                        else:
                            data[x] += "|"+name
            elif feature.is_sequence:
                for x, element in enumerate(feature(list2dict)):
                    if element != "O":
                        if not self._ambiguous or data[x] == u"O":
                            data[x] = element
                        else:
                            data[x] += "|"+element
            else:
                for x in range(len(list2dict)):
                    data[x] = feature(list2dict, x)
        
        return data

class FillerFeature(Feature):
    def __init__(self, entry, filler_entry, condition, *args, **kwargs):
        super(FillerFeature, self).__init__(self, *args, **kwargs)
        
        self.condition = condition
        self.default   = DictGetterFeature(entry=entry)
        self.filler    = DictGetterFeature(entry=filler_entry)
        
        self.condition._getter.entry = entry
        
        if not self.condition.is_boolean:
            raise ValueError("In %s: condition is not boolean." %self.name)
    
    def __call__(self, *args, **kwargs):
        if self.condition(*args, **kwargs):
            return self.filler(*args, **kwargs)
        else:
            return self.default(*args, **kwargs)