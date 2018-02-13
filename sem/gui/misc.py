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

try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk

def find_potential_separator(target):
    regex = re.compile(u"(\W+)", re.U)
    found = list(set(regex.findall(target)))
    if len(found) == 1:
        return found[0]
    return None

def find_occurrences(target, content):
    regex = re.compile(u'((?<=\W)|(?<=^))' + target + u"(?=\W|$)", re.U + re.M)
    for match in regex.finditer(content):
        yield match

def random_color():
    import random, colorsys
    
    red = (random.randrange(0, 256) + 256) / 2.0;
    green = (random.randrange(0, 256) + 256) / 2.0;
    blue = (random.randrange(0, 256) + 256) / 2.0;
    
    def to_hex(i):
        hx = hex(int(i))[2:]
        if len(hx) == 1:
            hx = "0" + hx
        return hx
    def to_color(r,g,b):
        cs = [to_hex(c) for c in [r,g,b]]
        return "#%s%s%s" %(cs[0],cs[1],cs[2])
    def darker(r,g,b):
        h,l,s = colorsys.rgb_to_hls(r/256.0, g/256.0, b/256.0)
        cs = [to_hex(256.0*c) for c in colorsys.hls_to_rgb(h,l/2.5,s)]
        return "#%s%s%s" %(cs[0],cs[1],cs[2])
    
    return {"background":to_color(red,green,blue),"foreground":darker(red,green,blue)}

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
        self.frame = frame
        self.type = the_type[:]
        self.level = level
        self.label = the_type.lower()
        self.shortcut = None
        found = False
        if self.level == 0 and len(self.frame.spare_colors) > 0:
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
                self.label = self.label[:i] + u"[" + self.label[i] + u"]" + self.label[i+1:]
                break
        if not found and len(available[level]) > 0:
            char = sorted(available[level])[0]
            available[level].remove(char)
            self.shortcut = char
            self.label += " [%s]" %char
        if self.level not in Adder.l2t:
            Adder.l2t[self.level] = {}
            Adder.t2l[self.level] = {}
        Adder.l2t[self.level][self.label] = self.type
        Adder.t2l[self.level][self.type] = self.label
    
    def add(self, event, remove_focus=False):
        if self.frame.current_selection is not None:
            f_cs = self.frame.current_selection
            tag = Tag(f_cs.lb, f_cs.ub, self.type)
            first = self.frame.charindex2position(f_cs.lb)
            last = self.frame.charindex2position(f_cs.ub)
            if tag in self.frame.current_annots and self.frame.current_type_hierarchy_level == 0:
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
            regex = re.compile(u'((?<=\W)|(?<=^))' + self.frame.text.get(start, end) + u"(?=\W|$)", re.U + re.M)
            for match in regex.finditer(self.frame.doc.content):
                cur_start, cur_end = self.frame.charindex2position(match.start()), self.frame.charindex2position(match.end())
                #self.frame.text.tag_add(self.type, cur_start, cur_end)
                if Tag(match.start(), match.end(), self.type) not in self.frame.current_annots:
                    self.frame.wish_to_add = [self.type, cur_start, cur_end]
                    self.frame.add_annotation(None, remove_focus=False)
        except tk.TclError:
            raise
        self.frame.type_combos[self.level].current(0)
        self.frame.wish_to_add = None
        self.frame.current_selection = None
        self.frame.current_type_hierarchy_level = 0
        self.frame.update_level()
        self.frame.text.tag_remove("BOLD",  "1.0", 'end')
