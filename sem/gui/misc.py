"""
file: misc.py

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

from sem.storage.annotation import Tag
from sem.storage import Trie
from sem.constants import NUL

import tkinter

def fill_with(t, value):
    def fill_rec(t1):
        keys = [key for key in t1 if key != NUL]
        for key in keys:
            fill_rec(t1[key])
        t1[NUL] = value[:]
    fill_rec(t.data)

def find_potential_separator(target):
    regex = re.compile(r"(\W+)", re.U)
    found = list(set(regex.findall(target)))
    if len(found) == 1:
        return found[0]
    return None

def find_occurrences(target, content, whole_word=True):
    target = target.strip()
    if whole_word:
        pattern = \
            (r"\b" if target[0].isalnum() else r"((?<=\s)|(?<=^))") \
            + re.escape(target) \
            + (r"\b" if target[-1].isalnum() else r"(?=\s|$)")
    else:
        pattern = re.escape(target)
    regex = re.compile(pattern, re.U + re.M)
    for match in regex.finditer(content):
        yield match

def random_color():
    import random
    import colorsys

    red = (random.randrange(0, 256) + 256) / 2.0
    green = (random.randrange(0, 256) + 256) / 2.0
    blue = (random.randrange(0, 256) + 256) / 2.0

    def to_hex(i):
        hx = hex(int(i))[2:]
        if len(hx) == 1:
            hx = "0{}".format(hx)
        return hx
    def to_color(r, g, b):
        cs = [to_hex(c) for c in [r, g, b]]
        return "#{cs[0]}{cs[1]}{cs[2]}".format(cs=cs)
    def darker(r, g, b):
        h, l, s = colorsys.rgb_to_hls(r/256.0, g/256.0, b/256.0)
        cs = [to_hex(256.0*c) for c in colorsys.hls_to_rgb(h, l/2.5, s)]
        return "#{cs[0]}{cs[1]}{cs[2]}".format(cs=cs)

    return {"background": to_color(red, green, blue), "foreground": darker(red, green, blue)}

class Adder():
    l2t = {}
    t2l = {}

    @classmethod
    def label2type(cls, label, level, default=None):
        return cls.l2t.get(level, {}).get(label, default)

    @classmethod
    def type2label(cls, type, level, default=None):
        return cls.t2l.get(level, {}).get(type, default)

    @classmethod
    def clear(cls):
        cls.l2t.clear()
        cls.t2l.clear()

    def __init__(self, frame, the_type, available, level=0):
        if len(available[level]) == 0:
            raise ValueError("No more available shortcuts!")
        self.frame = frame
        self.type = the_type[:]
        self.level = level
        self.label = the_type.lower()
        self.shortcut = None
        found = False
        if self.level == 0:
            if len(self.frame.spare_colors) > 0:
                self.color = self.frame.spare_colors.pop()
            else:
                self.color = random_color()
            self.frame.text.tag_configure(self.type, **self.color)
        for i in range(len(self.label)):
            target = self.label[i].lower()
            found = target in available[level]
            if found:
                available[level].remove(target)
                self.shortcut = target
                self.label = self.label + " [{0} or Shift+{0}]".format(self.label[i])
                break
        if not found and len(available[level]) > 0:
            char = available[level][0]
            available[level].remove(char)
            self.shortcut = char
            self.label += " [{0} or Shift+{0}]".format(char)
        if self.level not in Adder.l2t:
            Adder.l2t[self.level] = {}
            Adder.t2l[self.level] = {}
        Adder.l2t[self.level][self.label] = self.type
        Adder.t2l[self.level][self.type] = self.label

    def add(self, event, remove_focus=False):
        if self.frame.current_selection is not None:
            f_cs = self.frame.current_selection
            tag = Tag(self.type, f_cs.lb, f_cs.ub)
            first = self.frame.charindex2position(f_cs.lb)
            last = self.frame.charindex2position(f_cs.ub)
            if (
                tag in self.frame.current_annotations
                and self.frame.current_type_hierarchy_level == 0
            ):
                return
        else:
            first = "sel.first"
            last = "sel.last"
        self.frame.wish_to_add = [self.type, first, last]
        self.frame.add_annotation(None, remove_focus)

    def add_all(self, event):
        if self.frame.current_selection is not None:
            start = self.frame.charindex2position(self.frame.current_selection.lb)
            end = self.frame.charindex2position(self.frame.current_selection.ub)
        else:
            start, end = ("sel.first", "sel.last")
        try:
            target = re.escape(self.frame.text.get(start, end).strip())
            pattern = \
                (r"\b" if target[0].isalnum() else r"((?<=\s)|(?<=^))") \
                + target \
                + (r"\b" if target[-1].isalnum() else r"(?=\s|$)")
            regex = re.compile(pattern, re.U + re.M)
            for match in regex.finditer(self.frame.doc.content):
                cur_start = self.frame.charindex2position(match.start())
                cur_end = self.frame.charindex2position(match.end())
                if Tag(self.type, match.start(), match.end()) not in self.frame.current_annotations:
                    self.frame.wish_to_add = [self.type, cur_start, cur_end]
                    self.frame.add_annotation(None, remove_focus=False)
        except tkinter.TclError:
            raise
        self.frame.type_combos[self.level].current(0)
        self.frame.wish_to_add = None
        self.frame.current_selection = None
        self.frame.current_type_hierarchy_level = 0
        self.frame.update_level()
        self.frame.text.tag_remove("BOLD",  "1.0", 'end')


class Adder2(object):
    def __init__(self, tagset, levels, shortcut_trie):
        self.tagset = tagset
        self.levels = levels
        self.shortcut_trie = shortcut_trie
        self.current_annotation = None
        self.current_hierarchy_level = 0

    def max_depth(self):
        return max([len(l) for l in self.levels])

    def up_one_level(self):
        if self.current_annotation is None:
            self.current_hierarchy_level = 0
        else:
            self.current_hierarchy_level += 1
            if self.current_hierarchy_level >= self.max_depth():
                self.current_hierarchy_level = 0

    def down_one_level(self):
        if self.current_annotation is None:
            self.current_hierarchy_level = 0
        else:
            self.current_hierarchy_level -= 1
            if self.current_hierarchy_level < 0:
                self.current_hierarchy_level = self.max_depth()-1

    def type_from_letter(self, letter):
        if (
            self.current_annotation is not None
            and len(self.current_annotation.levels) < self.current_hierarchy_level
        ):
            return None
        path = (
            self.current_annotation.levels[ : self.current_hierarchy_level]
            if self.current_annotation
            else []
        )
        sub = self.shortcut_trie.goto(path)
        for key, val in sub.items():
            if key != NUL and val[NUL] == letter:
                return key

def from_tagset(tagset):
    levels = [tag.split(".") for tag in tagset]
    chars = list("abcdefghijklmnopqrstuvwxyz") \
        + ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12', '*']
    trie = Trie()
    for level in levels:
        trie.add(level)
    fill_with(trie, chars)
    shortcut_trie = Trie()
    for level in levels:
        hierarchy = []
        for depth, sublevel in enumerate(level):
            if hierarchy + [sublevel] in shortcut_trie:
                hierarchy.append(sublevel)
                continue
            sub = trie.goto(hierarchy)
            available = sub[NUL]
            for c in sublevel.lower():
                found = c in available
                if found:
                    available.remove(c)
                    break
            if not found:
                c = available[0]
                available.remove(c)
            hierarchy.append(sublevel)
            shortcut_trie.add_with_value(hierarchy, c)
    return Adder2(tagset, levels, shortcut_trie)
