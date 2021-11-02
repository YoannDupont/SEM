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
import functools

from sem.constants import NUL
from sem.storage import (
    AnnotationSet,
    compile_token,
    compile_multiword,
    get_top_level,
    chunks_to_annotation
)


def get(x):
    """The method to automatically get an element in a list with a shift.
    This is useful for features like "previous word starts with uppercase".

    Parameters
    ----------
    x : int
        the shift to apply to an index

    Returns
    -------
    function
        A function that will get the element of a list with a shift of x.
        When no element is found, the method will return empty string.
    """
    def get_sent(lst, index):
        if 0 <= index + x < len(lst):
            return lst[index+x]
        return ""
    return get_sent


def sentence_wrapper(f, x, y):
    """A wrapper for methods that work on a single token (like an str) to make them work
    on a Sentence (list of elements).

    Parameters
    ----------
    f : function
        the function to apply on a sentence.
    x : int
        the shift in position in sentence.
    y : str
        the field to apply f on.

    Returns
    -------
    function
        a mapping function that will map f on a Sentence object.
    """
    getter = get(x)

    def do_map(s):
        features = s.feature(y)
        return [f(getter(features, i)) for i in range(len(s))]
    return do_map


def limited_compose(funs):
    """Minimalistic function composition by messing with `functools.reduce`.
    This method is limited as it requires a single argument, where valid call
    could be no arguments or many. This means that some valid calls will raise
    an exception (the message will also be very obscure if do not know what is
    going on).
    This function is intended to be used as a mean to model sequence features
    is SEM, where multiple functions are called one after the other.

    For real composition, use `funcy.funcs.compose` (https://github.com/Suor/funcy).

    Parameters
    ----------
    funs : list[function]
        The list of one argument functions to compose.

    Returns
    -------
    function
        The composition of functions given in argument.

    Raises
    ------
    ValueError
        There are less than 2 functions to compose.
    """
    if len(funs) < 2:
        raise ValueError("Cannot compose less than 2 functions")
    # `functools.reduce` works using an accumulator that will hold
    # the current value. This accumulator is `x` in the lambda expression,
    # y is the current function in the iterator.
    # We can see why we *need* an argument: if no arguments are given, reduce
    # will assume the first element of the list to be the initializer, meaning
    # the first element will be a function.
    return functools.partial(functools.reduce, lambda x, y: y(x), funs)


def is_upper_at(token, index):
    return token[index].isupper()


def bos(s):
    return [i == 0 for i in range(len(s))]


def eos(s):
    return [i == len(s)-1 for i in range(len(s))]


def matches(s, regexp, y):
    return [regexp.search(token) is not None for token in s.feature(y)]


def subsequence(s, regexp, y, default="#"):
    lst = [regexp.search(token) for token in s.feature(y)]
    return [item.group() if item else default for item in lst]


def token(s, regexp, y, default="#"):
    return [(token if regexp.search(token) else default) for token in s.feature(y)]


def check_some(s, features):
    return [any(feats) for feats in zip(*[f(s) for f in features])]


def check_all(s, features):
    return [all(feats) for feats in zip(*[f(s) for f in features])]


def check_none(s, features):
    return [not any(feats) for feats in zip(*[f(s) for f in features])]


def substitute(string, pattern, repl):
    """Just an interface to make re.sub work with functools.partial"""
    return re.sub(pattern, repl, string)


def boolean_format(fmt):
    if fmt.lower() in ("bo", "b/o"):
        return bo_fmt
    elif fmt.lower() in ("zo", "z/o", "01", "0/1"):
        return zo_fmt
    else:
        raise ValueError(f'unknown boolean feature format: "{fmt}"')


def bo_fmt(value, appendice):
    """Begin/Out format."""
    return ('B{}'.format(appendice) if value else 'O')


def zo_fmt(value, appendice):
    """Zero/One format."""
    return int(value)


def not_op(s, f, fmt=zo_fmt):
    return [fmt(not item, '') for item in f(s)]


def and_op(s, f1, f2, fmt=zo_fmt):
    return [fmt(left and right, '') for left, right in zip(f1(s), f2(s))]


def token_gazetteer(s, gazetteer, y, appendice='', fmt=bo_fmt):
    return [fmt(token in gazetteer, appendice) for token in s.feature(y)]


def multiword_dictionary(s, trie, y, appendice=''):
    length = len(s)
    res = ['O' for _ in range(length)]
    tmp = trie.data
    fst = 0
    lst = -1  # last match found
    cur = 0
    ckey = None  # Current KEY
    tokens = s.feature(y)
    while fst < length - 1:
        cont = True
        while cont and (cur < length):
            ckey = tokens[cur]
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
        tmp = trie.data
        lst = -1
    if NUL in trie.data.get(tokens[-1], []):
        res[-1] = "B{}".format(appendice)
    return res


def directory_feature(s, features):
    data = ["O" for _ in range(len(s))]
    annotation = AnnotationSet("")
    for feat in features:
        for annot in chunks_to_annotation(feat(s)):
            annotation.add(annot)
    tags = get_top_level(annotation)
    for tag in tags:
        data[tag.lb] = "B-{}".format(tag.value)
        for index in range(tag.lb + 1, tag.ub):
            data[index] = "I-{}".format(tag.value)
    return data


def apply_mapping(s, mapping, y, default="O"):
    return [mapping.get(item, default) or default for item in s.feature(y)]


def fill(s, condition, entry, filler):
    l1 = s.feature(entry)
    l2 = s.feature(filler)
    cond = condition(s)
    return [(filling if c else data) for (data, filling, c) in zip(l1, l2, cond)]


def search_forward(s, condition, entry, default='#'):
    tokens = s.feature(entry)
    matches = condition(s)
    lst = []
    to_add = default
    for i, item in reversed(list(enumerate(matches))):
        lst.append(to_add)
        if item:
            to_add = tokens[i]
    return lst[::-1]


def search_backward(s, condition, entry, default='#'):
    tokens = s.feature(entry)
    matches = condition(s)
    lst = []
    to_add = default
    for i, item in enumerate(matches):
        lst.append(to_add)
        if item:
            to_add = tokens[i]
    return lst


def xml2feat(xml, default_entry="word", default_shift=0, path=None):
    attrib = xml.attrib
    action = attrib.get("action")
    y = attrib.get("entry", default_entry)
    x = attrib.get("shift", default_shift)

    if xml.tag == "boolean":
        fmt = boolean_format(attrib.get("format", "0/1"))
        if action.lower() == "and":
            left, right = list(xml)
            return functools.partial(and_op, f1=xml2feat(left), f2=xml2feat(right), fmt=fmt)
        elif action.lower() == "not":
            return functools.partial(not_op, f=xml2feat(list(xml)[0]), fmt=fmt)

    if xml.tag == "string":
        if action.lower() == "equal":
            casing = attrib.get("casing", "s").lower()
            if casing in ("s", "sensitive"):
                return sentence_wrapper(functools.partial(str.__eq__, xml.text), x=x, y=y)
            elif casing in ("i", "insensitive"):
                return sentence_wrapper(
                    limited_compose([str.lower, functools.partial(str.__eq__, xml.text.lower())]),
                    x=x,
                    y=y
                )
        else:
            raise ValueError("Invalid string action: {}".format(action))

    elif xml.tag == "nullary":
        if action.lower() == "lower":
            return sentence_wrapper(str.lower, x=x, y=y)
        elif action.lower() == "bos":
            return bos
        else:
            raise ValueError("Invalid nullary action: {}".format(action))

    elif xml.tag == "unary":
        if action.lower() == "isupper":
            return sentence_wrapper(
                functools.partial(is_upper_at, index=int(xml.text)), x=x, y=y
            )
        else:
            return ValueError("Invalid unaty action: {}".format(action))

    elif xml.tag == "directory":
        children = list(xml)
        if children:
            features = []
            for child in reversed(children):
                features.append(xml2feat(child, path=path))
            return functools.partial(directory_feature, features=features)

    elif xml.tag == "dictionary":
        if "path" in attrib:
            if path:
                the_path = pathlib.Path(path).parent / xml.attrib["path"]
            else:
                the_path = xml.attrib["path"]
            with open(the_path) as input_stream:
                entries = input_stream.readlines()
            appendice = "-{}".format(pathlib.Path(xml.attrib["path"]).stem)
        elif xml.text:
            entries = xml.text.split("\n")
        else:
            raise ValueError("Dictionary feature should have either a path attribute or text.")

        action = attrib["action"].lower()
        entry = attrib.get("entry", "word")
        if action == "token":
            appendice = attrib.get("appendice", appendice)
            fmt = boolean_format(attrib.get("format", "B/O"))
            data = compile_token(entries)
            return functools.partial(
                token_gazetteer, gazetteer=data, y=entry, appendice=appendice, fmt=fmt
            )
        elif action == "multiword":
            appendice = attrib.get("appendice", appendice)
            data = compile_multiword(entries)
            return functools.partial(multiword_dictionary, trie=data, y=entry, appendice=appendice)
        else:
            raise ValueError("Invalid action for dictionary: {}".format(action))

    elif xml.tag == "fill":
        entry = attrib.pop("entry")
        filler_entry = attrib.pop("filler-entry", default_entry)
        condition = xml2feat(list(xml)[0])
        return functools.partial(fill, condition=condition, entry=entry, filler=filler_entry)

    elif xml.tag == "find":
        action = attrib["action"].lower()
        default = attrib.get("default", "#")
        if action == "forward":
            condition = xml2feat(list(xml)[0])
            return functools.partial(search_forward, condition=condition, entry=y, default=default)
        elif action == "backward":
            condition = xml2feat(list(xml)[0])
            return functools.partial(search_backward, condition=condition, entry=y, default=default)
        else:
            raise ValueError("Invalid action for find: {}".format(action))

    elif xml.tag == "regexp":
        flags = re.U + re.M + (re.I * int("i" == xml.attrib.get("casing", "s")))
        if attrib["action"].lower() == "check":
            return functools.partial(matches, regexp=re.compile(xml.text, flags=flags), y=y)
        raise RuntimeError

    else:
        raise ValueError("Invalid feature kind: {}".format(xml.tag))
