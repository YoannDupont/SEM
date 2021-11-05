"""
file: gui_components.py

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

import tkinter
import tkinter.ttk
import tkinter.filedialog
import tkinter.messagebox

import pathlib
import os
import multiprocessing
import time
import shutil
import configparser

import sem
import sem.exporters
import sem.importers
import sem.logger
import sem.pipelines

from sem.constants import NUL
from sem.storage import SEMCorpus, str2filter, str2docfilter, Tag, Trie
from sem.processors import EnrichProcessor, WapitiLabelProcessor
from sem.modules.tagger import tagger

from wapiti.api import Model as WapitiModel


SPARE_COLORS_DEFAULT = [
    {'background': '#FFCCCC', 'foreground': '#FF0000'},
    {'background': '#CCEEEE', 'foreground': '#008888'},
    {'background': '#CCCCFF', 'foreground': '#0000FF'},
    {'background': '#DDFFDD', 'foreground': '#008800'},
    {'foreground': '#6c4c45', 'background': '#e6dad7'},
    {'foreground': '#813058', 'background': '#eecfde'},
    {'foreground': '#8a570d', 'background': '#f4c888'},
    {'foreground': '#1461a1', 'background': '#cce5f9'},
    {'foreground': '#601194', 'background': '#d7a8f6'},
    {'foreground': '#254084', 'background': '#bccaed'},
    {'foreground': '#a22800', 'background': '#ffb299'},
    {'foreground': '#729413', 'background': '#e3f5af'},
    {'foreground': '#0a9b47', 'background': '#a3fac8'},
    {'foreground': '#275a5f', 'background': '#85c6cc'},
    {'foreground': '#886c11', 'background': '#f1da91'},
    {'foreground': '#426722', 'background': '#aad684'},
    {'background': '#C9B297', 'foreground': '#5C4830'},
    {'background': '#C8A9DC', 'foreground': '#542D6E'},
    {'foreground': '#79a602', 'background': '#e7fea8'},
    {'foreground': '#454331', 'background': '#a7a383'},
    {'foreground': '#625e2d', 'background': '#d0cb99'},
    {'foreground': '#4b3054', 'background': '#b28fbf'},
    {'foreground': '#374251', 'background': '#9ca9bc'},
    {'background': '#CCCCCC', 'foreground': '#000000'},
]


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
        pattern = (
            (r"\b" if target[0].isalnum() else r"((?<=\s)|(?<=^))")
            + re.escape(target)
            + (r"\b" if target[-1].isalnum() else r"(?=\s|$)")
        )
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
        h, l, s = colorsys.rgb_to_hls(r / 256.0, g / 256.0, b / 256.0)
        cs = [to_hex(256.0 * c) for c in colorsys.hls_to_rgb(h, l / 2.5, s)]
        return "#{cs[0]}{cs[1]}{cs[2]}".format(cs=cs)

    return {"background": to_color(red, green, blue), "foreground": darker(red, green, blue)}


class Adder:
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
        self.frame.add_annotationset(None, remove_focus)

    def add_all(self, event):
        if self.frame.current_selection is not None:
            start = self.frame.charindex2position(self.frame.current_selection.lb)
            end = self.frame.charindex2position(self.frame.current_selection.ub)
        else:
            start, end = ("sel.first", "sel.last")
        try:
            target = re.escape(self.frame.text.get(start, end).strip())
            pattern = (
                (r"\b" if target[0].isalnum() else r"((?<=\s)|(?<=^))")
                + target
                + (r"\b" if target[-1].isalnum() else r"(?=\s|$)")
            )
            regex = re.compile(pattern, re.U + re.M)
            for match in regex.finditer(self.frame.doc.content):
                cur_start = self.frame.charindex2position(match.start())
                cur_end = self.frame.charindex2position(match.end())
                if Tag(self.type, match.start(), match.end()) not in self.frame.current_annotations:
                    self.frame.wish_to_add = [self.type, cur_start, cur_end]
                    self.frame.add_annotationset(None, remove_focus=False)
        except tkinter.TclError:
            raise
        self.frame.type_combos[self.level].current(0)
        self.frame.wish_to_add = None
        self.frame.current_selection = None
        self.frame.current_type_hierarchy_level = 0
        self.frame.update_level()
        self.frame.text.tag_remove("BOLD", "1.0", "end")


def makemap(tagset, colors):
    dct = {}
    for tag in tagset:
        val = tag.split(".", 1)[0]
        color = (colors.pop(0) if colors else random_color())
        dct[val] = color
    return dct


class Adder2:
    def __init__(self, tagset, levels, shortcut_trie, color=None):
        self.tagset = tagset
        self.levels = levels
        self.shortcut_trie = shortcut_trie
        self.current_annotation = None
        self.current_hierarchy_level = 0
        self.color = color or makemap(self.tagset, SPARE_COLORS_DEFAULT[:])

    def max_depth(self):
        return max([len(lvl) for lvl in self.levels])

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
                self.current_hierarchy_level = self.max_depth() - 1

    def type_from_letter(self, letter):
        if (
            self.current_annotation is not None
            and len(self.current_annotation.levels) < self.current_hierarchy_level
        ):
            return None
        path = (
            self.current_annotation.levels[: self.current_hierarchy_level]
            if self.current_annotation
            else []
        )
        sub = self.shortcut_trie.goto(path)
        for key, val in sub.items():
            if key != NUL and val[NUL] == letter:
                return key


def from_tagset(tagset):
    levels = [tag.split(".") for tag in tagset]
    chars = list("abcdefghijklmnopqrstuvwxyz") + [
        "F1",
        "F2",
        "F3",
        "F4",
        "F5",
        "F6",
        "F7",
        "F8",
        "F9",
        "F10",
        "F11",
        "F12",
        "*",
    ]
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


class SemTkLangSelector(tkinter.ttk.Frame):
    def __init__(self, root, resource_dir):
        tkinter.ttk.Frame.__init__(self, root)

        self.resource_dir = resource_dir
        self.observers = []
        self.items = [resource.name for resource in self.resource_dir.glob("*")]

        self.cur_lang = tkinter.StringVar()
        self.select_lang_label = tkinter.ttk.Label(root, text="select language:")
        self.langs = tkinter.ttk.Combobox(root, textvariable=self.cur_lang)

        self.langs["values"] = self.items

        self.langs.current(0)
        for i, item in enumerate(self.items):
            if item == "fr":
                self.langs.current(i)

        self.langs.bind("<<ComboboxSelected>>", self.select_lang)

    def pack(self):
        self.select_lang_label.pack()
        self.langs.pack()

    def grid(self, row=0, column=0):
        x = row
        y = column
        self.select_lang_label.grid(row=x, column=y)
        x += 1
        self.langs.grid(row=x, column=y)
        x += 1
        return (x, y)

    def lang(self):
        return self.cur_lang.get()

    def register(self, observer):
        self.observers.append(observer)
        observer.set_lang(self.lang())

    def select_lang(self, event):
        for observer in self.observers:
            observer.set_lang(self.lang())


class SemTkResourceSelector(tkinter.ttk.Frame):
    def __init__(self, root, resource_dir, filter=lambda x: True):
        tkinter.ttk.Frame.__init__(self, root)

        self.resource_dir = resource_dir
        self._filter = filter
        self._lang = None
        self._items = []
        self.select_resourse_label = tkinter.ttk.Label(
            root, text=f"select {self.resource_dir.name}:"
        )
        self.resources = tkinter.Listbox(root)

    def pack(self):
        self.select_resourse_label.pack()
        self.resources.pack()

    def grid(self, row=0, column=0):
        x = row
        y = column
        self.select_resourse_label.grid(row=x, column=y)
        x += 1
        self.resources.grid(row=x, column=y)
        x += 1
        return (x, y)

    def resource(self):
        resrc = self.resources.get(tkinter.ACTIVE)
        return self.resource_dir / self.lang() / resrc or None

    def lang(self):
        return self._lang

    def set_lang(self, language):
        self._lang = language
        self.items = [
            path.name for path in (self.resource_dir / self._lang).glob("*") if self._filter(path)
        ]
        self.items.sort(key=lambda x: x.lower())
        self.resources["width"] = max(
            max(len(item) for item in self.items) + 1, self.resources["width"]
        )
        self.resources["height"] = len(self.items)

        self.resources.delete(0, tkinter.END)
        for item in self.items:
            self.resources.insert(tkinter.END, item)


class SemTkFileSelector(tkinter.ttk.Frame):
    def __init__(self, root, main_window, button_opt):
        tkinter.ttk.Frame.__init__(self, root)

        self.root = root
        self.main_window = main_window
        self.current_files = None
        self.button_opt = button_opt

        # define options for opening or saving a file
        self.file_opt = options = {}
        options["defaultextension"] = ".txt"
        options["filetypes"] = [("all files", ".*"), ("text files", ".txt")]
        options["initialdir"] = pathlib.Path("~").expanduser()
        options["parent"] = root
        options["title"] = "Select files to annotate."

        self.file_selector_button = tkinter.ttk.Button(
            self.root, text="select file(s)", command=self.filenames
        )
        self.label = tkinter.ttk.Label(self.root, text="selected file(s):")
        self.fa_search = tkinter.PhotoImage(
            file=self.main_window.resource_dir / "images" / "fa_search_24_24.gif"
        )
        self.file_selector_button.config(image=self.fa_search, compound=tkinter.LEFT)

        self.scrollbar = tkinter.ttk.Scrollbar(self.root)
        self.selected_files = tkinter.Listbox(self.root, yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.selected_files.yview)

    def pack(self):
        self.file_selector_button.pack(**self.button_opt)
        self.label.pack()
        self.scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self.selected_files.pack(fill=tkinter.BOTH, expand=True)

    def grid(self, row=0, column=0):
        """
        TODO: to be tested
        """
        x = row
        y = column
        self.file_selector_button.grid(row=x, column=y, **self.button_opt)
        x += 1
        self.label.grid(row=x, column=y)
        x += 1
        self.scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self.selected_files.grid(row=x, column=y, fill=tkinter.BOTH, expand=True)
        x += 1
        return (x, y)

    def filenames(self, event=None):
        self.current_files = list(tkinter.filedialog.askopenfilenames(**self.file_opt))
        self.current_files.sort(key=lambda x: x.lower())
        self.current_files = [pathlib.Path(path) for path in self.current_files]
        self.selected_files.delete(0, tkinter.END)
        if self.current_files:
            for current_file in self.current_files:
                self.selected_files.insert(tkinter.END, current_file.name)
            self.file_opt["initialdir"] = self.current_files[0].parent

    def files(self):
        return self.current_files or []


class SemTkExportSelector(tkinter.ttk.Frame):
    def __init__(self, root):
        tkinter.ttk.Frame.__init__(self, root)

        self.root = root
        self.label = tkinter.ttk.Label(self.root, text="select output format:")

        self.export_formats = ["default"] + sorted(
            sem.exporters.available_exporters()
        )
        self.export_combobox = tkinter.ttk.Combobox(self.root)
        self.export_combobox["values"] = self.export_formats
        self.export_combobox.current(0)

    def pack(self):
        self.label.pack()
        self.export_combobox.pack()

    def grid(self, row=0, column=0):
        x = row
        y = column
        self.label.grid(row=x, column=y)
        x += 1
        self.export_combobox.grid(row=x, column=y)
        x += 1
        return (x, y)

    def export_format(self):
        return self.export_combobox.get()


class SEMTkWapitiTrain(tkinter.ttk.Frame):
    def __init__(
        self,
        file_selector,
        workflow,
        annotation_name,
        lang,
        annotation_level=None,
        document_filter=None,
        top=None,
        main_frame=None,
        text="Algorithm-specific variables",
    ):
        if top:
            self.trainTop = top
        else:
            self.trainTop = tkinter.Toplevel()

        self.file_selector = file_selector
        self.workflow = workflow
        self.annotation_name = annotation_name
        self.lang = lang
        self.annotation_level = annotation_level or tkinter.StringVar(
            self.trainTop, value="top level"
        )
        self.document_filter = document_filter or tkinter.StringVar(
            self.trainTop, value="all documents"
        )

        self.current_train = sem.SEM_DATA_DIR / "train"
        if not self.current_train.exists():
            os.makedirs(self.current_train)

        self.main_frame = main_frame or self.trainTop
        self.trainTop.focus_set()
        self.CRF_algorithm_var = tkinter.StringVar(self.trainTop, value="rprop")
        self.CRF_l1_var = tkinter.StringVar(self.trainTop, value="0.5")
        self.CRF_l2_var = tkinter.StringVar(self.trainTop, value="0.0001")
        self.CRF_nprocs_var = tkinter.StringVar(self.trainTop, value="1")
        self.pattern_label_var = tkinter.StringVar(self.trainTop, value="")
        self.compact_var = tkinter.IntVar()
        self.compact_var.set(1)

        algsFrame = tkinter.ttk.LabelFrame(self.trainTop, text=text)
        algsFrame.pack(fill="both", expand="yes")

        crf_cur_row = 0

        tkinter.ttk.Button(algsFrame, text="pattern (optional)", command=self.select_file).grid(
            row=crf_cur_row, column=0, sticky=tkinter.W
        )
        self.pattern_label = tkinter.Label(algsFrame, textvariable=self.pattern_label_var)
        self.pattern_label.grid(row=crf_cur_row, column=1, sticky=tkinter.W)
        crf_cur_row += 1

        tkinter.Label(algsFrame, text="algorithm").grid(row=crf_cur_row, column=0, sticky=tkinter.W)
        CRF_algorithmValue = tkinter.ttk.Combobox(algsFrame, textvariable=self.CRF_algorithm_var)
        CRF_algorithmValue["values"] = ["rprop", "l-bfgs", "sgd-l1", "bcd", "rprop+", "rprop-"]
        CRF_algorithmValue.current(0)
        CRF_algorithmValue.grid(row=crf_cur_row, column=1)
        crf_cur_row += 1

        tkinter.Label(algsFrame, text="l1").grid(row=crf_cur_row, column=0, sticky=tkinter.W)
        CRF_algorithmValue = tkinter.Entry(algsFrame, textvariable=self.CRF_l1_var)
        CRF_algorithmValue.grid(row=crf_cur_row, column=1)
        crf_cur_row += 1

        tkinter.Label(algsFrame, text="l2").grid(row=crf_cur_row, column=0, sticky=tkinter.W)
        CRF_algorithmValue = tkinter.Entry(algsFrame, textvariable=self.CRF_l2_var)
        CRF_algorithmValue.grid(row=crf_cur_row, column=1)
        crf_cur_row += 1

        tkinter.Label(algsFrame, text="number of processors").grid(
            row=crf_cur_row, column=0, sticky=tkinter.W
        )
        CRF_nprocsValue = tkinter.ttk.Combobox(algsFrame, textvariable=self.CRF_nprocs_var)
        CRF_nprocsValue["values"] = list(range(1, multiprocessing.cpu_count() + 1))
        CRF_nprocsValue.current(0)
        CRF_nprocsValue.grid(row=crf_cur_row, column=1)
        crf_cur_row += 1

        tkinter.ttk.Checkbutton(
            algsFrame, text="compact model", variable=self.compact_var
        ).grid(row=crf_cur_row, column=0, sticky=tkinter.W)
        crf_cur_row += 1

        CRF_trainButton = tkinter.Button(algsFrame, text="train", command=self.trainCRF)
        CRF_trainButton.grid(row=crf_cur_row, column=0)
        crf_cur_row += 1

    def select_file(self, event=None):
        options = {}
        options["defaultextension"] = ".txt"
        options["filetypes"] = [("all files", ".*"), ("text files", ".txt")]
        options["initialdir"] = sem.SEM_DATA_DIR / "resources" / "patterns"
        options["parent"] = self.trainTop
        options["title"] = "Select pattern file."
        pattern = tkinter.filedialog.askopenfilename(**options)
        self.pattern_label_var.set(pattern)

    def algorithm(self):
        return self.CRF_algorithm_var.get()

    def l1(self):
        return float(self.CRF_l1_var.get())

    def l2(self):
        return float(self.CRF_l2_var.get())

    def nprocs(self):
        return int(self.CRF_nprocs_var.get())

    def pattern(self):
        return self.pattern_label_var.get()

    def compact(self):
        return bool(self.compact_var.get())

    def trainCRF(self, events=None):
        alg = self.algorithm()
        l1 = self.l1()
        l2 = self.l2()
        pattern = self.pattern()
        nprocs = self.nprocs()
        compact = self.compact()
        workflowfile = self.workflow.resource()
        export_format = "conll"
        pipeline, workflow_options, exporter, couples = sem.pipelines.load_workflow(
            workflowfile, force_format=export_format, pipeline_mode="train"
        )
        workflow_options = configparser.RawConfigParser()
        workflow_options.add_section("log")
        workflow_options.set("log", "log_level", "INFO")
        annotation_level = str2filter[self.annotation_level.get()]
        document_filter = str2docfilter[self.document_filter.get()]

        target_model = None
        pipes = [pipe for pipe in pipeline]
        trained_pipe = None
        for pipe in reversed(pipes):
            if isinstance(pipe, EnrichProcessor):
                pipe.mode = "train"
                self.annotation_name = pipe.informations.aentries[-1].name
                pipe.mode = "label"
                break
            elif isinstance(pipe, WapitiLabelProcessor):
                self.annotation_name = pipe.field
                target_model = pathlib.Path(pipe.model)
                trained_pipe = pipe
                break

        out_dir = None
        if target_model:
            out_dir = target_model.parent
            name = target_model.name
            try:
                os.makedirs(out_dir)
            except FileExistsError:
                pass

        timestamp = time.strftime("%Y%m%d%H%M%S")
        output_dir = self.current_train / timestamp
        if not output_dir.exists():
            os.makedirs(output_dir)

        train_file = output_dir / "train.conll"
        model_file = output_dir / "model.txt"
        # files can be selected from GUI or already provided (list)
        try:
            files = self.file_selector.files()
        except AttributeError:
            files = self.file_selector
        fields = []
        names = set()
        with open(train_file, "w", encoding="utf-8") as output_stream:
            for filename in files:
                document = sem.importers.load(
                    filename, encoding="utf-8", tagset_name=self.annotation_name
                )
                args = {
                    "workflow": None,
                    "infiles": [document],
                    "pipeline": pipeline,
                    "options": workflow_options,
                    "exporter": None,
                    "couples": None,
                }
                if isinstance(document, SEMCorpus):
                    for doc in document:
                        if doc.name in names:
                            sem.logger.warning("document %s already found, skipping", doc.name)
                            continue
                        elif not document_filter(doc, self.annotation_name):
                            sem.logger.warning("document %s has no annotations, skipping", doc.name)
                            continue
                        args["infiles"] = [doc]
                        doc = tagger(**args)[0]

                        if self.annotation_name is not None:
                            doc.add_to_corpus(self.annotation_name, filter=annotation_level)
                            doc.corpus.write(output_stream)
                        if not fields:
                            fields = doc.corpus.fields[:-1]
                else:
                    if document.name in names:
                        sem.logger.warning("document %s already found, skipping", document.name)
                        continue
                    elif not document_filter(document, self.annotation_name):
                        sem.logger.warning(
                            "document %s has no annotations, skipping", document.name
                        )
                        continue

                    document = tagger(**args)[0]

                    if self.annotation_name is not None:
                        document.add_to_corpus(self.annotation_name, filter=annotation_level)
                        document.corpus.write(output_stream)
                        if not fields:
                            fields = document.corpus.fields[:-1]

        pattern_file = output_dir / "pattern.txt"
        if pattern:
            shutil.copy(pattern, pattern_file)
        else:
            with open(pattern_file, "w", encoding="utf-8") as output_stream:
                output_stream.write("u\n\n")
                for i, field in enumerate(fields):
                    for shift in range(-2, 3):
                        output_stream.write("u:{0} {1:+d}=%x[{1},{2}]\n".format(field, shift, i))
                    output_stream.write("\n")
                output_stream.write("b\n")

        with open(output_dir / "config.txt", "w", encoding="utf-8") as output_stream:
            output_stream.write("algorithm\t{0}\n".format(alg))
            output_stream.write("l1\t{0}\n".format(l1))
            output_stream.write("l2\t{0}\n".format(l2))
            output_stream.write("number of processors\t{0}\n".format(nprocs))
            output_stream.write("compact\t{0}\n".format(compact))

        with open(pattern_file, "r") as input_stream:
            patterns = input_stream.read()
        model = WapitiModel(
            patterns=patterns, algo=alg, rho1=l1, rho2=l2, nthreads=nprocs, compact=compact
        )
        sequences = []
        for sequence in sem.importers.read_conll(train_file, "utf-8"):
            sequences.append(bytes(sequence.conll(range(len(sequence.keys()))) + "\n", "utf-8"))
        model.train(sequences)
        model.save(str(model_file))
        del model

        model_update_message = (
            "\n\nNo candidate location found, model update has to be done manually"
        )
        output_pipeline = sem.SEM_RESOURCE_DIR / "pipelines" / self.lang / workflowfile.stem
        try:
            output_pipeline.parent.mkdir(parents=True)
        except FileExistsError:
            pass
        if target_model:
            if target_model.exists():
                bname = pathlib.Path(name).stem
                ext = pathlib.Path(name).suffix
                backup_name = "{}.backup-{}{}".format(bname, timestamp, ext)
                dest = out_dir / backup_name
                sem.logger.info("creating backup file before moving: %s", dest)
                shutil.move(target_model, dest)
            sem.logger.info("trained model moved to: %s", str(out_dir))
            model_update_message = "\n\nTrained model moved to: {0}".format(out_dir)
            shutil.copy(model_file, target_model)
            pipeline.pipeline_mode = "label"
            trained_pipe.model = target_model
            sem.pipelines.save(pipeline, output_pipeline)
            pipeline.pipeline_mode = "train"
            pipeline_update_message = "\n\nPipeline saved to: {0}".format(output_pipeline)

        sem.logger.info("files are located in: %s", str(output_dir))
        tkinter.messagebox.showinfo(
            "training SEM",
            "Everything went ok!\n\nfiles are located in: {0}{1}{2}".format(
                output_dir, model_update_message, pipeline_update_message
            ),
        )

        if self.main_frame:
            self.main_frame.destroy()
        else:
            self.trainTop.destroy()


class SEMTkTrainInterface(tkinter.ttk.Frame):
    def __init__(self, documents, lang=None, workflow=None):
        self.documents = documents
        self._lang = lang
        self._workflow = workflow
        if not (workflow and lang):
            self._workflow = None
            self._lang = None
        self.workflow_selector = None
        self.lang_selector = None

        trainTop = tkinter.Toplevel()
        trainTop.focus_set()

        varsFrame = tkinter.ttk.LabelFrame(trainTop, text="Global variables")

        document_filter_label = tkinter.ttk.Label(varsFrame, text="document filter:")
        document_filter_var = tkinter.StringVar(varsFrame, value="all documents")
        document_filter = tkinter.ttk.Combobox(varsFrame, textvariable=document_filter_var)
        document_filter["values"] = sorted(str2docfilter.keys())
        document_filter.current(sorted(str2docfilter.keys()).index("all documents"))

        annotation_level_label = tkinter.ttk.Label(varsFrame, text="annotation level:")
        annotation_level_var = tkinter.StringVar(varsFrame, value="top level")
        annotation_level = tkinter.ttk.Combobox(varsFrame, textvariable=annotation_level_var)
        annotation_level["values"] = sorted(str2filter.keys())
        annotation_level.current(sorted(str2filter.keys()).index("top level"))

        directory = sem.SEM_DATA_DIR / "resources" / "workflow"
        if not self._workflow:
            self.workflow_selector = SemTkResourceSelector(
                varsFrame, directory, filter=lambda x: pathlib.Path(x).suffix == ".xml"
            )
        if not self._lang:
            self.lang_selector = SemTkLangSelector(varsFrame, directory)
            self.lang_selector.register(self.workflow_selector)

        algsFrame = tkinter.ttk.LabelFrame(trainTop, text="Algorithm-specific variables")

        notebook = tkinter.ttk.Notebook(algsFrame)
        frame1 = tkinter.ttk.Frame(notebook)
        frame2 = tkinter.ttk.Frame(notebook)
        notebook.add(frame1, text="CRF")
        notebook.add(frame2, text="NN")
        frame1.resource_dir = sem.SEM_DATA_DIR / "resources"

        varsFrame.pack(fill="both", expand="yes")
        vars_cur_row = 0
        document_filter_label.grid(row=vars_cur_row, column=0)
        vars_cur_row += 1
        document_filter.grid(row=vars_cur_row, column=0)
        vars_cur_row += 1
        annotation_level_label.grid(row=vars_cur_row, column=0)
        vars_cur_row += 1
        annotation_level.grid(row=vars_cur_row, column=0)
        vars_cur_row += 1
        if self.lang_selector:
            vars_cur_row, _ = self.lang_selector.grid(row=vars_cur_row, column=0)
        if self.workflow_selector:
            vars_cur_row, _ = self.workflow_selector.grid(row=vars_cur_row, column=0)

        for _ in range(5):
            tkinter.ttk.Separator(trainTop, orient=tkinter.HORIZONTAL).pack()

        algsFrame.pack(fill="both", expand="yes")

        notebook.pack()

        SEMTkWapitiTrain(
            self.documents,
            self.workflow,
            None,
            lang=self.lang,
            annotation_level=annotation_level_var,
            document_filter=document_filter_var,
            top=frame1,
            main_frame=trainTop,
            text="CRF-specific variables",
        )

    @property
    def workflow(self):
        return self._workflow or self.workflow_selector

    @property
    def lang(self):
        return self._lang or self.lang_selector.lang()


class SearchFrame(tkinter.ttk.Frame):
    def __init__(self, text, regexp=False, nocase=False):
        self.text = text
        self.pattern = tkinter.StringVar()
        self.regexp = tkinter.IntVar(int(regexp))
        self.nocase = tkinter.IntVar(int(nocase))
        self.prev_pattern = ""
        self.prev_regexp = regexp
        self.prev_nocase = nocase
        self.findings = []
        self.current = -1
        self.text.tag_config("search", background="yellow", foreground="black")
        bold_font = tkinter.font.Font(self.text)
        bold_font.configure(weight="bold")
        self.text.tag_config("search_current", font=bold_font)

    def clear_tags(self):
        self.text.tag_remove("search", "1.0", "end")
        self.text.tag_remove("search_current", "1.0", "end")

    def clear(self):
        self.clear_tags()
        self.prev_pattern = ""
        self.prev_regexp = self.regexp.get()
        self.prev_nocase = self.nocase.get()
        self.current = -1
        del self.findings[:]

    def find_in_text(self, event=None):
        find_in_text_top = tkinter.Toplevel()
        find_in_text_top.title("search")
        find_in_text_top.focus_set()
        matchesVar = tkinter.StringVar()

        def nxt(event=None):
            pattern = self.pattern.get()
            regexp = self.regexp.get()
            nocase = self.nocase.get()
            if (
                pattern != self.prev_pattern
                or regexp != self.prev_regexp
                or nocase != self.prev_nocase
            ):
                self.clear_tags()
                self.prev_pattern = pattern
                self.prev_regexp = regexp
                self.prev_nocase = nocase
                del self.findings[:]
                start = 1.0
                countVar = tkinter.StringVar()
                pos = self.text.search(
                    pattern,
                    start,
                    stopindex="end",
                    count=countVar,
                    regexp=self.regexp.get(),
                    nocase=self.nocase.get(),
                )
                while pos:
                    end = "{0} + {1}c".format(pos, countVar.get())
                    self.text.tag_add("search", pos, end)
                    self.findings.append((pos, end))
                    start = end
                    pos = self.text.search(
                        pattern,
                        start,
                        stopindex="end",
                        count=countVar,
                        regexp=self.regexp.get(),
                        nocase=self.nocase.get(),
                    )
                self.current = 1
            elif self.findings:
                prev = self.findings[self.current - 1]
                self.current = self.current + 1 if self.current < len(self.findings) else 1
                self.text.tag_remove("search_current", prev[0], prev[1])

            if self.findings:
                self.text.tag_add(
                    "search_current",
                    self.findings[self.current - 1][0],
                    self.findings[self.current - 1][1],
                )
                matchesVar.set("match {0} out of {1}".format(self.current, len(self.findings)))
                self.text.mark_set("insert", self.findings[self.current - 1][1])
                self.text.see("insert")
            else:
                matchesVar.set("no matches found")

        def cancel(event=None):
            self.clear()
            find_in_text_top.destroy()

        label1 = tkinter.Label(find_in_text_top, text="search for:")

        text = tkinter.ttk.Entry(find_in_text_top, textvariable=self.pattern)

        next_btn = tkinter.ttk.Button(find_in_text_top, text="next", command=nxt)
        cancel_btn = tkinter.ttk.Button(find_in_text_top, text="cancel", command=cancel)
        matches_found_lbl = tkinter.Label(find_in_text_top, textvariable=matchesVar)
        regexp_btn = tkinter.ttk.Checkbutton(
            find_in_text_top, text="regular expression", variable=self.regexp
        )
        nocase_btn = tkinter.ttk.Checkbutton(
            find_in_text_top, text="ignore case", variable=self.nocase
        )
        label1.grid(row=0, column=0)
        text.grid(row=0, column=1)
        regexp_btn.grid(row=1, column=0)
        nocase_btn.grid(row=1, column=1)
        next_btn.grid(row=2, column=0)
        cancel_btn.grid(row=2, column=1)
        matches_found_lbl.grid(row=3, column=0, columnspan=2)
        text.focus_set()

        find_in_text_top.bind("<Return>", nxt)
        find_in_text_top.bind("<Escape>", cancel)
        find_in_text_top.protocol("WM_DELETE_WINDOW", cancel)
