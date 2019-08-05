# -*- coding: utf-8 -*-

"""
file: xml2feature.py

Description: defines XML-to-object parsing procedure for each feature.

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

import re

import pathlib

import sem.misc

from sem.storage import Entry

from sem.features import DictGetterFeature, FindForwardFeature, FindBackwardFeature, DEFAULT_GETTER
from sem.features import EqualFeature, EqualCaselessFeature
from sem.features import CheckFeature, SubsequenceFeature, TokenFeature
from sem.features import OrFeature, AndFeature, NotFeature
from sem.features import (
    BOSFeature,
    EOSFeature,
    LowerFeature,
    IsUpperFeature,
    SubstringFeature,
    SubstitutionFeature,
    SequencerFeature,
)
from sem.features import SomeFeature, AllFeature, NoneFeature
from sem.features import TokenDictionaryFeature, MultiwordDictionaryFeature, MapperFeature
from sem.features import DirectoryFeature, FillerFeature
from sem.features import RuleFeature, OrRuleFeature
from sem.features import TriggeredFeature


class XML2Feature(object):
    def __init__(self, entries, path=None):
        self._default_shift = 0

        self._default_entry = None
        self._entries = {}
        for entry in entries:
            if entry.name.lower() == "word":
                self._default_entry = entry.name
            self._entries[entry._name] = entry

        self._features = {}

        if self._default_entry is None:
            self._default_entry = entries[0].name

        self._path = path

    def parse(self, xml, getter=None):
        attrib = xml.attrib

        if getter is None:
            getter = DictGetterFeature(
                entry=attrib.get("entry", self._default_entry),
                shift=attrib.get("shift", self._default_shift),
            )
        if isinstance(getter, DictGetterFeature):
            self.check_entry(getter.entry, attrib)

        if attrib.get("name", None):
            self._features[attrib["name"]] = Entry(attrib["name"], mode="label")

        if xml.tag == "boolean":
            if attrib["action"] == "and":
                children = list(xml)
                assert len(children) == 2
                left = self.parse(children[0])
                right = self.parse(children[1])
                assert left.is_boolean and right.is_boolean
                return AndFeature(left, right, **attrib)
            elif attrib["action"] == "or":
                children = list(xml)
                assert len(children) == 2
                left = self.parse(children[0])
                right = self.parse(children[1])
                assert left.is_boolean and right.is_boolean
                return OrFeature(left, right, **attrib)
            elif attrib["action"] == "not":
                children = list(xml)
                assert len(children) == 1
                element = self.parse(children[0])
                assert element.is_boolean
                return NotFeature(element, **attrib)
            raise RuntimeError

        elif xml.tag == "nullary":
            if attrib["action"].lower() == "bos":
                return BOSFeature(**attrib)
            elif attrib["action"].lower() == "eos":
                return EOSFeature(**attrib)
            elif attrib["action"].lower() == "lower":
                return LowerFeature(getter=getter, **attrib)
            elif attrib["action"].lower() == "substring":
                return SubstringFeature(getter=getter, **attrib)
            raise RuntimeError

        elif xml.tag == "unary":
            if attrib["action"].lower() == "isupper":
                return IsUpperFeature(int(xml.text), getter=getter, **attrib)
            raise RuntimeError

        elif xml.tag == "binary":
            children = list(xml)
            assert len(children) == 2
            if attrib["action"].lower() == "substitute":
                assert children[0].tag == "pattern" and children[1].tag in (
                    "replace",
                    "replacement",
                )
                flags = attrib.pop("flags", re.U + re.M)
                return SubstitutionFeature(
                    children[0].text, children[1].text, flags, getter=getter, **attrib
                )
            raise RuntimeError

        elif xml.tag == "nary":
            if attrib["action"].lower() == "sequencer":
                return SequencerFeature(
                    *[self.parse(list(xml)[0])]
                    + [self.parse(child, getter=DEFAULT_GETTER) for child in list(xml)[1:]],
                    getter=getter,
                    **attrib,
                )
            raise RuntimeError

        elif xml.tag == "regexp":
            flags = re.U + re.M + (re.I * int("i" == xml.attrib.get("casing", "s")))
            if attrib["action"].lower() == "check":
                return CheckFeature(xml.text, flags=flags, getter=getter, **attrib)
            elif attrib["action"].lower() == "subsequence":
                return SubsequenceFeature(xml.text, flags=flags, getter=getter, **attrib)
            elif attrib["action"].lower() == "token":
                return TokenFeature(xml.text, flags=flags, getter=getter, **attrib)
            raise RuntimeError

        elif xml.tag == "string":
            if attrib["action"].lower() == "equal":
                casing = attrib.get("casing", "s").lower()
                if casing in ("s", "sensitive"):
                    return EqualFeature(xml.text, getter=getter, **attrib)
                elif casing in ("i", "insensitive"):
                    return EqualCaselessFeature(xml.text, getter=getter, **attrib)
            raise RuntimeError

        elif xml.tag == "list":
            action = attrib["action"].lower()
            if action == "some":
                return SomeFeature(*[self.parse(element) for element in list(xml)], **attrib)
            elif action == "all":
                return AllFeature(*[self.parse(element) for element in list(xml)], **attrib)
            elif action == "none":
                return NoneFeature(*[self.parse(element) for element in list(xml)], **attrib)
            raise RuntimeError

        elif xml.tag == "find":
            action = attrib["action"].lower()
            if attrib.get("return_entry", None):
                self.check_entry(attrib["return_entry"], attrib)
            if action == "forward":
                return FindForwardFeature(self.parse(list(xml)[0], getter=None), **attrib)
            elif action == "backward":
                return FindBackwardFeature(self.parse(list(xml)[0], getter=None), **attrib)
            raise RuntimeError

        elif xml.tag == "dictionary":
            if "path" in attrib:
                # attrib["path"] = abspath(join(dirname(self._path), xml.attrib["path"]))
                attrib["path"] = (pathlib.Path(self._path).parent / xml.attrib["path"]).resolve()
            elif xml.text:
                attrib["entries"] = xml.text.split("\n")
            else:
                raise ValueError("Dictionary feature should have either a path attribute or text !")

            action = attrib["action"].lower()
            if action == "token":
                return TokenDictionaryFeature(getter=getter, **attrib)
            elif action == "multiword":
                if attrib.get("entry", None) is None:
                    attrib["entry"] = "word"
                return MultiwordDictionaryFeature(**attrib)
            elif action == "map":
                return MapperFeature(getter=getter, **attrib)
            raise RuntimeError

        elif xml.tag == "directory":
            # path = abspath(join(dirname(self._path), attrib.pop("path")))
            path = (pathlib.Path(self._path).parent / attrib.pop("path")).resolve()
            ambiguous = sem.misc.str2bool(attrib.pop("ambiguous", "false"))
            return DirectoryFeature(
                path, self, order=attrib.pop("order", ".order"), ambiguous=ambiguous, **attrib
            )

        elif xml.tag == "fill":
            entry = attrib.pop("entry")
            filler_entry = attrib.get("filler-entry", self._default_entry)
            if "filler-entry" in attrib:
                del attrib["filler-entry"]
            self.check_entry(filler_entry, attrib)
            return FillerFeature(entry, filler_entry, self.parse(list(xml)[0]), **attrib)

        elif xml.tag == "trigger":
            trigger, operation = list(xml)
            return TriggeredFeature(self.parse(trigger), self.parse(operation), **attrib)

        elif xml.tag in ("rule", "orrule"):
            elements = list(xml)
            for e in elements:
                e.attrib["x"] = 0  # forcing current element

            features = [self.parse(e, getter=None) for e in elements]
            for e, f in zip(elements, features):
                card = e.attrib.get("card", "1")
                f.min_match = 0
                f.max_match = 0
                if card == "?":
                    f.min_match = 0
                    f.max_match = 1
                elif card == "*":
                    f.min_match = 0
                    f.max_match = 2 ** 30  # should be long enough
                elif card == "+":
                    f.min_match = 1
                    f.max_match = 2 ** 30  # should be long enough
                elif "," in card:
                    mi, ma = card.split(",")
                    f.min_match = int(mi)
                    f.max_match = int(ma)
                try:
                    f.min_match = int(card)
                    f.max_match = f.min_match
                except Exception:
                    pass
                if f.min_match < 0 or f.max_match <= 0:
                    raise ValueError(
                        'Invalid cardinality for {0} feature: "{1}"'.format(e.tag, card)
                    )
            if xml.tag == "rule":
                return RuleFeature(features, **xml.attrib)
            elif xml.tag == "orrule":
                return OrRuleFeature(features, **xml.attrib)

        else:
            raise ValueError("unknown tag: {0}".format(xml.tag))

    def check_entry(self, entry, attrib):
        used_entry = self._entries.get(entry, None)
        if not used_entry:
            used_entry = self._features.get(entry, None)
        if not used_entry:
            raise ValueError(
                'Node "{0}", entry not found: "{0}"'.format(attrib.get("name", "unnamed"), entry)
            )
        elif used_entry.is_train:
            raise ValueError(
                'Node "{0}" uses train-only entry: "{0}"'.format(
                    attrib.get("name", "unnamed"), used_entry.name
                )
            )
