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

import pathlib

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from sem.features.feature import Feature
from sem.features.getterfeatures import DictGetterFeature
from sem.features.dictionaryfeatures import MultiwordDictionaryFeature, MapperFeature
from sem.features.triggeredfeatures import TriggeredFeature
from sem.features.matcherfeatures import SubsequenceFeature
from sem.storage.annotation import Tag, Annotation, get_top_level, chunk_annotation_from_sentence

class DirectoryFeature(Feature):
    def __init__(self, path, x2f, order=".order", ambiguous=False, *args, **kwargs):
        super(DirectoryFeature, self).__init__(self, *args, **kwargs)
        self._is_sequence = True
        self._ambiguous = ambiguous

        order = order or ".order"

        self.path = pathlib.Path(path).expanduser().absolute().resolve()
        self.order = []
        self.features = []

        names = [p.name for p in self.path.glob("*")]
        if order in names:
            for line in open(self.path / order, "rU"):
                line = line.strip()
                if "#" in line:
                    line = line[ : line.index("#")].strip()
                if line:
                    self.order.append(line)
        else:
            self.order = [name for name in names if not name.startswith(".")]

        self.order = self.order[::-1]

        for name in self.order:
            self.features.append(x2f.parse(ET.parse(self.path / name).getroot()))
            self.features[-1]._name = name
            if (
                not (
                    self.features[-1].is_boolean
                    or self.features[-1].is_sequence
                    or isinstance(self.features[-1], MapperFeature)
                    or (
                        isinstance(self.features[-1], TriggeredFeature)
                        and isinstance(self.features[-1].operation, MapperFeature)
                    )
                    or (isinstance(self.features[-1], SubsequenceFeature))
                )
            ):
                raise ValueError("In {0} feature: {1} is neither boolean nor sequence".format(
                    self.name,
                    name
                ))
            if isinstance(self.features[-1], MultiwordDictionaryFeature):
                self.features[-1]._appendice = self.features[-1]._appendice or "-{0}".format(name)

    def __call__(self, list2dict, *args, **kwargs):
        data = ["O"]*len(list2dict)
        annotation = Annotation("")

        for feature in self.features:
            name = feature.name
            if feature.is_boolean:
                for x in range(len(list2dict)):
                    if feature(list2dict, x):
                        annotation.add(Tag(name, x, x+1))
            elif feature.is_sequence:
                for tag in chunk_annotation_from_sentence(
                    [{"tag": tag} for tag in feature(list2dict)],
                    "tag"
                ):
                    annotation.add(tag)

        if not self._ambiguous:
            tags = get_top_level(annotation)
            for tag in tags:
                data[tag.lb] = "B-{}".format(tag.value)
                for index in range(tag.lb+1, tag.ub):
                    data[index] = "I-{}".format(tag.value)

        return data

class FillerFeature(Feature):
    def __init__(self, entry, filler_entry, condition, *args, **kwargs):
        super(FillerFeature, self).__init__(self, *args, **kwargs)

        self.condition = condition
        self.default = DictGetterFeature(entry=entry)
        self.filler = DictGetterFeature(entry=filler_entry)
        self.condition._getter.entry = entry

        if not self.condition.is_boolean:
            raise ValueError("In {0}: condition is not boolean.".format(self.name))

    def __call__(self, *args, **kwargs):
        if self.condition(*args, **kwargs):
            return self.filler(*args, **kwargs)
        else:
            return self.default(*args, **kwargs)
