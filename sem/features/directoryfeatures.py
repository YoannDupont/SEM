# -*- coding: utf-8 -*-

"""
file: directoryfeatures.py

Description: defines features related to taxonomies.

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

import os

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

import sem
from . import Feature
from . import DEFAULT_GETTER, DictGetterFeature
from . import MultiwordDictionaryFeature, MapperFeature
from . import TriggeredFeature
from . import SubsequenceFeature
from sem.storage.annotation import Tag, Annotation, get_top_level, chunk_annotation_from_sentence

class DirectoryFeature(Feature):
    def __init__(self, path, x2f, order=".order", ambiguous=False, *args, **kwargs):
        super(DirectoryFeature, self).__init__(self, *args, **kwargs)
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
            if sem.PY2:
                self.features.append(x2f.parse(ET.fromstring(open(os.path.join(self.path, name), "rU").read())))
            else:
                self.features.append(x2f.parse(ET.parse(os.path.join(self.path, name)).getroot()))
            self.features[-1]._name = name
            if not (self.features[-1].is_boolean or self.features[-1].is_sequence or isinstance(self.features[-1], MapperFeature) or (isinstance(self.features[-1], TriggeredFeature) and isinstance(self.features[-1].operation, MapperFeature)) or (isinstance(self.features[-1], SubsequenceFeature))):
                raise ValueError("In {0} feature: {1} is neither boolean nor sequence".format(self.name, name))
            if isinstance(self.features[-1], MultiwordDictionaryFeature):
                self.features[-1]._appendice = self.features[-1]._appendice or u"-{0}".format(name)
    
    def __call__(self, list2dict, *args, **kwargs):
        data = [u"O"]*len(list2dict)
        annotation = Annotation("")
        
        for feature in self.features:
            name = feature.name
            if feature.is_boolean:
                for x in range(len(list2dict)):
                    if feature(list2dict, x):
                        # redone
                        annotation.add(Tag(name, x, x+1))
                        """if not self._ambiguous or data[x] == u"O":
                            data[x] = name
                        else:
                            data[x] += "|"+name"""
            elif feature.is_sequence:
                # redone
                for tag in chunk_annotation_from_sentence([{"tag": tag} for tag in feature(list2dict)], "tag"):
                    annotation.add(tag)
                """for x, element in enumerate(feature(list2dict)):
                    if element != "O":
                        if not self._ambiguous or data[x] == u"O":
                            data[x] = element
                        else:
                            data[x] += "|"+element"""
            #else:
            #    for x in range(len(list2dict)):
            #        data[x] = feature(list2dict, x)
        
        # redone
        if not self._ambiguous:
            tags = get_top_level(annotation)
            for tag in tags:
                data[tag.lb] = u"B-{}".format(tag.value)
                for index in range(tag.lb+1, tag.ub):
                    data[index] = u"I-{}".format(tag.value)
        
        return data

class FillerFeature(Feature):
    def __init__(self, entry, filler_entry, condition, *args, **kwargs):
        super(FillerFeature, self).__init__(self, *args, **kwargs)
        
        self.condition = condition
        self.default   = DictGetterFeature(entry=entry)
        self.filler    = DictGetterFeature(entry=filler_entry)
        
        self.condition._getter.entry = entry
        
        if not self.condition.is_boolean:
            raise ValueError("In {0}: condition is not boolean.".format(self.name))
    
    def __call__(self, *args, **kwargs):
        if self.condition(*args, **kwargs):
            return self.filler(*args, **kwargs)
        else:
            return self.default(*args, **kwargs)
