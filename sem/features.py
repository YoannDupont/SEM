# -*- coding: utf-8 -*-

"""
file: features.py

Description: SEM features for Corpus type.

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

from sem.constants import NUL
from sem.storage import Trie
from sem.storage import (
    compile_token,
    compile_multiword,
    compile_map,
    Entry,
    Tag,
    Annotation,
    get_top_level,
    chunk_annotation_from_sentence
)
from sem.misc import str2bool

try:
    import cPickle as pickle
except ImportError:
    import pickle

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


class Feature:
    def __init__(self, *args, **kwargs):
        self._is_boolean = False
        self._is_sequence = False
        self._name = kwargs.pop("name", None)
        self._display = kwargs.pop("display", "yes").lower()

        self._display = str2bool(self._display)

    def __call__(self, *args, **kwargs):
        raise TypeError("Cannot call {0} object".format(self.__class__.__name__))

    @property
    def is_boolean(self):
        return self._is_boolean

    @property
    def is_sequence(self):
        return self._is_sequence

    @property
    def name(self):
        return self._name

    @property
    def display(self):
        return self._display

    def default(self):
        return "#"


class GetterFeature(Feature):
    def __init__(self, *args, **kwargs):
        super(GetterFeature, self).__init__(*args, **kwargs)


class IdentityFeature(GetterFeature):
    """
    A getter that return the argument as it is.
    This allows to call features on strings as well as a local position
    in a sentence. This may cause performance issue, but it is the only
    way currently known to have an "feature package" that is consistent.
    """

    def __init__(self, *args, **kwargs):
        super(IdentityFeature, self).__init__(*args, **kwargs)

    def __call__(self, element, *args, **kwargs):
        return element


DEFAULT_GETTER = IdentityFeature()


class DictGetterFeature(GetterFeature):
    def __init__(self, *args, **kwargs):
        super(DictGetterFeature, self).__init__(*args, **kwargs)
        self.entry = kwargs.get("entry", "word")
        self.shift = int(kwargs.get("shift", 0))

    def __call__(self, list2dict, position, *args, **kwargs):
        current_position = position + self.shift

        if not (0 <= current_position < len(list2dict)):
            return None

        return list2dict[current_position].get(self.entry, None)


class SentenceGetterFeature(GetterFeature):
    def __init__(self, *args, **kwargs):
        super(SentenceGetterFeature, self).__init__(*args, **kwargs)
        self.entry = kwargs.get("entry", "word")
        self.shift = int(kwargs.get("shift", 0))

    def __call__(self, list2dict, position, *args, **kwargs):
        current_position = position + self.shift

        if not (0 <= current_position < len(list2dict)):
            return None

        return list2dict.get(current_position, self.entry)


class FindFeature(GetterFeature):
    def __init__(self, *args, **kwargs):
        super(FindFeature, self).__init__(*args, **kwargs)
        self._matcher = args[0]
        self._return_entry = kwargs.get("return_entry", "word")
        assert (
            self._matcher is not None and self._matcher.is_boolean
        ), "Matcher field in FindFeature does not return a boolean."


class FindForwardFeature(FindFeature):
    def __init__(self, *args, **kwargs):
        super(FindForwardFeature, self).__init__(*args, **kwargs)

    def __call__(self, list2dict, position, *args, **kwargs):
        for X in range(position + 1, len(list2dict)):
            if self._matcher(list2dict, X):
                return list2dict[X][self._return_entry]
        return None


class FindBackwardFeature(FindFeature):
    def __init__(self, *args, **kwargs):
        super(FindBackwardFeature, self).__init__(*args, **kwargs)

    def __call__(self, list2dict, position, *args, **kwargs):
        for X in reversed(range(0, position)):
            if self._matcher(list2dict, X):
                return list2dict[X][self._return_entry]
        return None


class ListGetterFeature(GetterFeature):
    def __init__(self, *args, **kwargs):
        super(ListGetterFeature, self).__init__(*args, **kwargs)
        self.index = kwargs.get("index", 0)
        self.shift = int(kwargs.get("shift", 0))

    def __call__(self, list2dict, position, *args, **kwargs):
        current_position = position + self.shift

        if not (0 <= current_position < len(list2dict)):
            return None

        return list2dict[current_position][self.index]


class StringFeature(Feature):
    def __init__(self, reference, getter=DEFAULT_GETTER, *args, **kwargs):
        super(StringFeature, self).__init__(self, reference, *args, **kwargs)
        self._reference = reference
        self._getter = getter


class EqualFeature(StringFeature):
    def __init__(self, reference, *args, **kwargs):
        super(EqualFeature, self).__init__(reference, *args, **kwargs)
        self._is_boolean = True

    def __call__(self, *args, **kwargs):
        return self._reference == self._getter(*args, **kwargs)


class EqualCaselessFeature(StringFeature):
    def __init__(self, reference, *args, **kwargs):
        super(EqualCaselessFeature, self).__init__(reference, *args, **kwargs)
        self._is_boolean = True
        self._reference = self._reference.lower()

    def __call__(self, *args, **kwargs):
        return self._reference == self._getter(*args, **kwargs).lower()


class ArityFeature(Feature):
    def __init__(self, *args, **kwargs):
        super(ArityFeature, self).__init__(*args, **kwargs)
        self._getter = kwargs.pop("getter", DEFAULT_GETTER)


class NullaryFeature(ArityFeature):
    def __init__(self, *args, **kwargs):
        super(NullaryFeature, self).__init__(*args, **kwargs)


class BOSFeature(NullaryFeature):
    def __init__(self, *args, **kwargs):
        super(BOSFeature, self).__init__(*args, **kwargs)
        self._is_boolean = True

    def __call__(self, list2dict, position, *args, **kwargs):
        return position == 0


class EOSFeature(NullaryFeature):
    def __init__(self, *args, **kwargs):
        super(EOSFeature, self).__init__(*args, **kwargs)
        self._is_boolean = True

    def __call__(self, list2dict, position, *args, **kwargs):
        return position == len(list2dict) - 1


class LowerFeature(NullaryFeature):
    def __init__(self, *args, **kwargs):
        super(LowerFeature, self).__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        return self._getter(*args, **kwargs).lower()


class SubstringFeature(NullaryFeature):
    def __init__(self, from_index=0, to_index=2 ** 31, *args, **kwargs):
        super(SubstringFeature, self).__init__(from_index, to_index, *args, **kwargs)
        self._default = kwargs.pop("default", '""')
        self._from_index = int(from_index)
        self._to_index = int(to_index)

    def __call__(self, *args, **kwargs):
        s = self._getter(*args, **kwargs)[self._from_index: self._to_index]
        if s:
            return s
        else:
            return self._default


class UnaryFeature(ArityFeature):
    def __init__(self, element, *args, **kwargs):
        super(UnaryFeature, self).__init__(*args, **kwargs)
        self._is_boolean = False
        self._element = element


class IsUpperFeature(UnaryFeature):
    def __init__(self, index, *args, **kwargs):
        super(IsUpperFeature, self).__init__(index, *args, **kwargs)
        self._is_boolean = True
        self._index = self._element

    def __call__(self, *args, **kwargs):
        return self._getter(*args, **kwargs)[self._index].isupper()


class BinaryFeature(ArityFeature):
    def __init__(self, element1, element2, *args, **kwargs):
        super(BinaryFeature, self).__init__(*args, **kwargs)
        self._element1 = element1
        self._element2 = element2


class SubstitutionFeature(BinaryFeature):
    def __init__(self, pattern, replacement, *args, **kwargs):
        super(SubstitutionFeature, self).__init__(pattern, replacement, *args, **kwargs)
        flags = kwargs.pop("flags", 0)
        self._replacer = re.compile(pattern, flags)
        self._replacement = replacement

    def __call__(self, *args, **kwargs):
        return self._replacer.sub(self._replacement, self._getter(*args, **kwargs))


class NaryFeature(ArityFeature):
    def __init__(self, *args, **kwargs):
        super(NaryFeature, self).__init__(self, *args, **kwargs)


class SequencerFeature(NaryFeature):
    def __init__(self, *args, **kwargs):
        super(SequencerFeature, self).__init__(*args, **kwargs)

        if len(args) == 0:
            raise ValueError("{0} cannot have less than 1 feature".format(self.__class__.__name__))

        self._features = args
        # ensuring that we can call the different features sequentially
        for i in range(1, len(self._features)):
            self._features[i]._getter = DEFAULT_GETTER

    def __call__(self, *args, **kwargs):
        current = self._features[0](*args, **kwargs)
        for feature in self._features[1:]:
            current = feature(current, *args, **kwargs)
        return current


class BooleanFeature(Feature):
    def __init__(self, *args, **kwargs):
        super(BooleanFeature, self).__init__(*args, **kwargs)
        self._is_boolean = True


class NotFeature(BooleanFeature):
    def __init__(self, element, *args, **kwargs):
        super(NotFeature, self).__init__(element, *args, **kwargs)
        self.element = element

    def __call__(self, *args, **kwargs):
        return not self.element(*args, **kwargs)


class AndFeature(BooleanFeature):
    def __init__(self, left, right, *args, **kwargs):
        super(AndFeature, self).__init__(left, right, *args, **kwargs)
        self.left = left
        self.right = right

    def __call__(self, *args, **kwargs):
        return self.left(*args, **kwargs) and self.right(*args, **kwargs)


class OrFeature(BooleanFeature):
    def __init__(self, left, right, *args, **kwargs):
        super(OrFeature, self).__init__(left, right, *args, **kwargs)
        self.left = left
        self.right = right

    def __call__(self, *args, **kwargs):
        return self.left(*args, **kwargs) or self.right(*args, **kwargs)


class ListFeature(Feature):
    def __init__(self, *args, **kwargs):
        super(ListFeature, self).__init__(*args, **kwargs)
        self._elements = args
        self._is_boolean = True

        for element in self._elements:
            if not element.is_boolean:
                raise TypeError(
                    "Non boolean element in list node: {0}".format(element.__class__.__name__)
                )


class SomeFeature(ListFeature):
    def __init__(self, *args, **kwargs):
        super(SomeFeature, self).__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        for element in self._elements:
            if element(*args, **kwargs):
                return True
        return False


class AllFeature(ListFeature):
    def __init__(self, *args, **kwargs):
        super(AllFeature, self).__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        for element in self._elements:
            if not element(*args, **kwargs):
                return False
        return True


class NoneFeature(ListFeature):
    def __init__(self, *args, **kwargs):
        super(NoneFeature, self).__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        for element in self._elements:
            if element(*args, **kwargs):
                return False
        return True


class MatchFeature(Feature):
    def __init__(self, pattern, flags=0, getter=DEFAULT_GETTER, default="#", *args, **kwargs):
        super(MatchFeature, self).__init__(pattern, *args, flags=flags, getter=getter, **kwargs)
        self._regexp = re.compile(pattern, flags)
        self._getter = getter
        self._default = default

    def __call__(self, *args, **kwargs):
        return self._regexp.search(self._getter(*args, **kwargs))


class CheckFeature(MatchFeature):
    def __init__(self, pattern, flags=0, getter=DEFAULT_GETTER, *args, **kwargs):
        super(CheckFeature, self).__init__(pattern, flags=flags, getter=getter, *args, **kwargs)
        self._is_boolean = True

    def __call__(self, *args, **kwargs):
        return super(CheckFeature, self).__call__(*args, **kwargs) is not None


class SubsequenceFeature(MatchFeature):
    def __call__(self, *args, **kwargs):
        matcher = super(SubsequenceFeature, self).__call__(*args, **kwargs)
        if matcher is None:
            if self._default:
                return self._default
            else:
                return self._getter(*args, **kwargs)
        else:
            return matcher.group()


class TokenFeature(MatchFeature):
    def __call__(self, *args, **kwargs):
        matcher = super(TokenFeature, self).__call__(*args, **kwargs)
        if matcher is None:
            if self._default:
                return self._default
            else:
                return self._getter(*args, **kwargs)
        else:
            return matcher.string


class RuleFeature(Feature):
    def __init__(self, features, *args, **kwargs):
        super(RuleFeature, self).__init__(self, *args, **kwargs)
        self._is_boolean = False
        self._is_sequence = True
        self._features = features

    def __call__(self, list2dict, *args, **kwargs):
        res = ["O"] * len(list2dict)
        pos_beg = 0
        pos_cur = 0
        feat_index = 0
        feat = self._features[feat_index]
        remain_min = feat.min_match
        remain_max = feat.max_match
        matches = []
        func = feat.__call__ if feat.is_boolean else feat.step
        while pos_beg < len(list2dict) - 1:
            while (
                remain_min <= 0
                and not pos_cur >= len(list2dict)
                and not func(list2dict, pos_cur)
                and feat_index < len(self._features) - 1
            ):
                feat_index += 1
                feat = self._features[feat_index]
                func = feat.__call__ if feat.is_boolean else feat.step
                remain_min = feat.min_match
                remain_max = feat.max_match
            if feat_index >= len(self._features) or pos_cur >= len(list2dict):
                pos_beg += 1
                pos_cur = pos_beg
                feat_index = 0
                feat = self._features[feat_index]
                func = feat.__call__ if feat.is_boolean else feat.step
                remain_min = feat.min_match
                remain_max = feat.max_match
                continue
            if func(list2dict, pos_cur):
                N = int(func(list2dict, pos_cur))
                pos_cur += N
                remain_min -= 1
                remain_max -= 1
            elif remain_min <= 0:
                if feat_index < len(self._features) - 1:
                    feat_index += 1
                else:
                    matches.append([pos_beg, pos_cur])
                    pos_beg = pos_cur
                    pos_cur = pos_beg
                    feat_index = 0
                feat = self._features[feat_index]
                func = feat.__call__ if feat.is_boolean else feat.step
                remain_min = feat.min_match
                remain_max = feat.max_match
            elif remain_max >= 0:
                pos_beg += 1
                pos_cur = pos_beg
                feat_index = 0
                feat = self._features[feat_index]
                func = feat.__call__ if feat.is_boolean else feat.step
                remain_min = feat.min_match
                remain_max = feat.max_match
            if remain_max == 0:
                if feat_index < len(self._features) - 1:
                    feat_index += 1
                else:
                    feat_index = 0
                    matches.append([pos_beg, pos_cur])
                    pos_beg = pos_cur
                    pos_cur = pos_beg
                feat = self._features[feat_index]
                func = feat.__call__ if feat.is_boolean else feat.step
                remain_min = feat.min_match
                remain_max = feat.max_match
        for lo, hi in matches:
            res[lo] = "B-{0}".format(self.name)
            for i in range(lo + 1, hi):
                res[i] = "I-{0}".format(self.name)
        return res

    def step(self, list2dict, i):
        pos_beg = i
        pos_cur = pos_beg
        feat_index = 0
        feat = self._features[feat_index]
        remain_min = feat.min_match
        remain_max = feat.max_match
        func = feat.__call__ if feat.is_boolean else feat.step
        while pos_beg < len(list2dict) - 1:
            while (
                remain_min <= 0
                and not func(list2dict, pos_cur)
                and feat_index < len(self._features) - 1
            ):
                feat_index += 1
                feat = self._features[feat_index]
                func = feat.__call__ if feat.is_boolean else feat.step
                remain_min = feat.min_match
                remain_max = feat.max_match
            if feat_index >= len(self._features):
                return 0
            if func(list2dict, pos_cur):
                N = int(func(list2dict, pos_cur))
                pos_cur += N
                remain_min -= 1
                remain_max -= 1
            elif remain_min <= 0:
                if feat_index < len(self._features) - 1:
                    feat_index += 1
                else:
                    return pos_cur - pos_beg
                feat = self._features[feat_index]
                func = feat.__call__ if feat.is_boolean else feat.step
                remain_min = feat.min_match
                remain_max = feat.max_match
            elif remain_max >= 0:
                return 0
            if remain_max == 0:
                if feat_index < len(self._features) - 1:
                    feat_index += 1
                else:
                    return pos_cur - pos_beg
                feat = self._features[feat_index]
                func = feat.__call__ if feat.is_boolean else feat.step
                remain_min = feat.min_match
                remain_max = feat.max_match
        return 0


class OrRuleFeature(Feature):
    def __init__(self, features, *args, **kwargs):
        super(OrRuleFeature, self).__init__(self, *args, **kwargs)
        self._is_boolean = False
        self._is_sequence = True
        self._features = features

    def step(self, list2dict, i):
        pos_beg = i
        feat_index = 0
        feat = self._features[feat_index]
        best_end = -1
        for feat in self._features:
            func = feat.__call__ if feat.is_boolean else feat.step
            best_end = max(best_end, int(func(list2dict, pos_beg)))
        return best_end


class TriggeredFeature(Feature):
    def __init__(self, trigger, operation, default="_untriggered_", *args, **kwargs):
        super(TriggeredFeature, self).__init__(self, *args, **kwargs)

        self.trigger = trigger
        self.operation = operation
        self.default = default

        if not self.trigger.is_boolean:
            raise ValueError("Trigger for {0} is not boolean.".format(self.name))

        self._is_boolean = self.operation._is_boolean

    def __call__(self, *args, **kwargs):
        if self.trigger(*args, **kwargs):
            return self.operation(*args, **kwargs)
        else:
            return self.default


class DictionaryFeature(Feature):
    def __init__(self, path=None, value=None, entries=None, getter=DEFAULT_GETTER, *args, **kwargs):
        super(DictionaryFeature, self).__init__(*args, **kwargs)
        self._path = path
        if path is not None:
            self._path = pathlib.Path(path).expanduser().resolve()
        self._value = value
        self._getter = getter
        self._entries = entries


class TokenDictionaryFeature(DictionaryFeature):
    def __init__(self, getter=DEFAULT_GETTER, *args, **kwargs):
        super(TokenDictionaryFeature, self).__init__(getter=getter, *args, **kwargs)
        self._is_boolean = True

        if self._path is not None:
            try:
                self._value = pickle.load(open(self._path))
            except (pickle.UnpicklingError, ImportError, EOFError, IndexError, TypeError):
                self._value = compile_token(self._path, "utf-8")
            self._entries = None
        elif self._entries is not None:
            self._value = set()
            for entry in self._entries:
                entry = entry.strip()
                if entry:
                    self._value.add(entry)

        assert self._value is not None

    def __call__(self, *args, **kwargs):
        return self._getter(*args, **kwargs) in self._value


class MultiwordDictionaryFeature(DictionaryFeature):
    def __init__(self, *args, **kwargs):
        super(MultiwordDictionaryFeature, self).__init__(*args, **kwargs)
        self._is_sequence = True
        self._entry = kwargs["entry"]
        self._appendice = kwargs.get("appendice", "")

        if self._path is not None:
            try:
                self._value = pickle.load(open(self._path))
            except (pickle.UnpicklingError, ImportError, EOFError):
                self._value = compile_multiword(self._path, "utf-8")
            self._entries = None
        elif self._entries:
            self._value = Trie()
            for entry in self._entries:
                entry = entry.strip()
                if entry:
                    self._value.add(entry.split())
        else:
            self._value = Trie()

    def __call__(self, list2dict, *args, **kwargs):
        res = ["O"] * len(list2dict)
        tmp = self._value._data
        length = len(list2dict)
        fst = 0
        lst = -1  # last match found
        cur = 0
        ckey = None  # Current KEY
        entry = self._entry
        appendice = self._appendice
        while fst < length - 1:
            cont = True
            while cont and (cur < length):
                ckey = list2dict[cur][entry]
                if NUL in tmp:
                    lst = cur
                tmp = tmp.get(ckey, {})
                cont = len(tmp) != 0
                cur += int(cont)

            if NUL in tmp:
                lst = cur

            if lst != -1:
                res[fst] = "B{}".format(appendice)
                for i in range(fst + 1, lst):
                    res[i] = "I{}".format(appendice)
                fst = lst
                cur = fst
            else:
                fst += 1
                cur = fst

            tmp = self._value._data
            lst = -1

        if NUL in self._value._data.get(list2dict[-1][entry], []):
            res[-1] = "B{}".format(appendice)

        return res

    def step(self, list2dict, i, *args, **kwargs):
        tmp = self._value._data
        length = len(list2dict)
        fst = i
        lst = -1  # last match found
        cur = fst
        ckey = None  # Current KEY
        entry = self._entry
        while fst < length - 1:
            cont = True
            while cont and (cur < length):
                ckey = list2dict[cur][entry]
                if NUL in tmp:
                    lst = cur
                tmp = tmp.get(ckey, {})
                cont = len(tmp) != 0
                cur += int(cont)

            if NUL in tmp:
                lst = cur

            if lst != -1:
                return lst - fst

            return 0

        if NUL in self._value._data.get(list2dict[-1][entry], []):
            return 1

        return 0


class MapperFeature(DictionaryFeature):
    def __init__(self, getter=DEFAULT_GETTER, default="O", *args, **kwargs):
        super(MapperFeature, self).__init__(getter=getter, *args, **kwargs)

        self._default = default

        if self._path is not None:
            self._value = compile_map(self._path, "utf-8")
            self._entries = None
        elif self._entries is not None:
            self._value = {}
            for entry in self._entries:
                entry = entry.strip()
                if entry:
                    key, value = entry.split("\t")
                    self._value[key] = value

        assert self._value is not None

    def __call__(self, *args, **kwargs):
        return self._value.get(self._getter(*args, **kwargs), self._default)


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
                    line = line[: line.index("#")].strip()
                if line:
                    self.order.append(line)
        else:
            self.order = [name for name in names if not name.startswith(".")]

        self.order = self.order[::-1]

        for name in self.order:
            self.features.append(x2f.parse(ET.parse(self.path / name).getroot()))
            self.features[-1]._name = name
            if not (
                self.features[-1].is_boolean
                or self.features[-1].is_sequence
                or isinstance(self.features[-1], MapperFeature)
                or (
                    isinstance(self.features[-1], TriggeredFeature)
                    and isinstance(self.features[-1].operation, MapperFeature)
                )
                or (isinstance(self.features[-1], SubsequenceFeature))
            ):
                raise ValueError(
                    "In {0} feature: {1} is neither boolean nor sequence".format(self.name, name)
                )
            if isinstance(self.features[-1], MultiwordDictionaryFeature):
                self.features[-1]._appendice = self.features[-1]._appendice or "-{0}".format(name)

    def __call__(self, list2dict, *args, **kwargs):
        data = ["O"] * len(list2dict)
        annotation = Annotation("")

        for feature in self.features:
            name = feature.name
            if feature.is_boolean:
                for x in range(len(list2dict)):
                    if feature(list2dict, x):
                        annotation.add(Tag(name, x, x + 1))
            elif feature.is_sequence:
                for tag in chunk_annotation_from_sentence(
                    [{"tag": tag} for tag in feature(list2dict)], "tag"
                ):
                    annotation.add(tag)

        if not self._ambiguous:
            tags = get_top_level(annotation)
            for tag in tags:
                data[tag.lb] = "B-{}".format(tag.value)
                for index in range(tag.lb + 1, tag.ub):
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
            ambiguous = str2bool(attrib.pop("ambiguous", "false"))
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
