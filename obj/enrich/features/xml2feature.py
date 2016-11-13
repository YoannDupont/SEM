# -*- coding: utf-8 -*-

"""
file: xml2feature.py

Description: defines XML-to-object parsing procedure for each feature.

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

import re

from os.path import abspath, dirname, join

from obj.enrich.features.feature            import Feature
from obj.enrich.features.getterfeatures     import IdentityFeature, DictGetterFeature, FindForwardFeature, FindBackwardFeature, DEFAULT_GETTER
from obj.enrich.features.stringfeatures     import EqualFeature, EqualCaselessFeature
from obj.enrich.features.matcherfeatures    import MatchFeature, CheckFeature, SubsequenceFeature, TokenFeature
from obj.enrich.features.booleanfeatures    import OrFeature, AndFeature, NotFeature
from obj.enrich.features.arityfeatures      import ArityFeature, UnaryFeature, BOSFeature, EOSFeature, LowerFeature, IsUpperFeature, SubstringFeature, SubstitutionFeature, SequencerFeature
from obj.enrich.features.listfeatures       import ListFeature, SomeFeature, AllFeature, NoneFeature
from obj.enrich.features.dictionaryfeatures import TokenDictionaryFeature, MultiwordDictionaryFeature

class XML2Feature(object):
    def __init__(self, entries, path=None):
        self._default_shift = 0
        
        self._default_entry = None
        for entry in entries:
            if entry.lower() == "word":
                self._default_entry = entry
        
        if self._default_entry is None:
            self._default_entry = entries[0]
        
        self._path = path
    
    def parse(self, xml, getter=None):
        attrib = xml.attrib
        
        if getter is None:
            getter = DictGetterFeature(entry=attrib.get("entry", self._default_entry), shift=attrib.get("shift", self._default_shift))
        
        if xml.tag == "boolean":
            if attrib["action"] == "and":
                children = list(xml)
                assert len(children) == 2
                left  = self.parse(children[0])
                right = self.parse(children[1])
                assert left.is_boolean and right.is_boolean
                return AndFeature(left, right, **attrib)
            elif attrib["action"] == "or":
                children = list(xml)
                assert len(children) == 2
                left  = self.parse(children[0])
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
                assert children[0].tag == "pattern" and children[1].tag in ("replace", "replacement")
                return SubstitutionFeature(children[0].text, children[1].text, re.U + re.M, getter=getter, **attrib)
            raise RuntimeError
        
        elif xml.tag == "nary":
            if attrib["action"].lower() == "sequencer":
                return SequencerFeature(*[self.parse(list(xml)[0])]+[self.parse(child, getter=DEFAULT_GETTER) for child in list(xml)[1:]], getter=getter, **attrib)
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
            if action == "forward":
                return FindForwardFeature(self.parse(list(xml)[0], getter=None), **attrib)
            elif action == "backward":
                return FindBackwardFeature(self.parse(list(xml)[0], getter=None), **attrib)
            raise RuntimeError
        
        elif xml.tag == "dictionary":
            attrib["path"] = abspath(join(dirname(self._path), xml.attrib["path"]))
            action = attrib["action"].lower()
            if action == "token":
                return TokenDictionaryFeature(getter=getter, **attrib)
            elif action == "multiword":
                if attrib.get("entry", None) is None:
                    attrib["entry"] = "word"
                return MultiwordDictionaryFeature(**attrib)
            raise RuntimeError
        
        else:
            raise ValueError("unknown tag: %s" %(xml.tag))
