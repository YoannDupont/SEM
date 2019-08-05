"""
file: components.py

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

import tkinter
import tkinter.ttk
import tkinter.filedialog
import tkinter.messagebox

import pathlib
import os
import multiprocessing
import time
import shutil
import logging

import sem
import sem.exporters.conll
import sem.importers
from sem.storage import Holder, SEMCorpus
from sem.modules.tagger import load_master, main as tagger
from sem.modules import EnrichModule, WapitiLabelModule
from sem.logger import default_handler
from sem.storage.annotation import str2filter
from sem.storage.document import str2docfilter

from wapiti.api import Model as WapitiModel


class SemTkMasterSelector(tkinter.ttk.Frame):
    def __init__(self, root, resource_dir, lang="fr"):
        tkinter.ttk.Frame.__init__(self, root)

        self.resource_dir = resource_dir
        self._lang = None
        langs = [path.name for path in (self.resource_dir / "master").glob("*")]
        if langs:
            self._lang = lang if lang in langs else langs[0]

        self.items = []
        if self._lang:
            self.items = [
                item.name for item in (self.resource_dir / "master" / self._lang).glob("*")
            ]
        self.items.sort(key=lambda x: x.lower())
        max_length = max([len(item) for item in self.items])

        self.select_workflow_label = tkinter.ttk.Label(root, text="select workflow:")
        self.masters = tkinter.Listbox(root, width=max_length + 1, height=len(self.items))

        for item in self.items:
            self.masters.insert(tkinter.END, item)

    def pack(self):
        self.select_workflow_label.pack()
        self.masters.pack()

    def grid(self, row=0, column=0):
        x = row
        y = column
        self.select_workflow_label.grid(row=x, column=y)
        x += 1
        self.masters.grid(row=x, column=y)
        x += 1
        return (x, y)

    def workflow(self):
        wf = self.masters.get(tkinter.ACTIVE)
        return self.resource_dir / "master" / self.lang() / wf or None

    def lang(self):
        return self._lang

    def set_lang(self, language):
        self._lang = language
        self.items = [path.name for path in (self.resource_dir / "master" / self._lang).glob("*")]
        self.items.sort(key=lambda x: x.lower())
        self.masters["height"] = len(self.items)

        self.masters.delete(0, tkinter.END)
        for item in self.items:
            self.masters.insert(tkinter.END, item)


class SemTkLangSelector(tkinter.ttk.Frame):
    def __init__(self, root, resource_dir):
        tkinter.ttk.Frame.__init__(self, root)

        self.master_selector = None
        self.resource_dir = resource_dir
        self.items = [master.name for master in (self.resource_dir / "master").glob("*")]

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

    def select_lang(self, event):
        self.master_selector.set_lang(self.lang())


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
            exporter.stem
            for exporter in (sem.SEM_HOME / "exporters").glob("*")
            if (
                exporter.name.endswith(".py")
                and not exporter.name.startswith("_")
                and not exporter.name == "exporter.py"
            )
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
        master,
        annotation_name,
        annotation_level=None,
        document_filter=None,
        top=None,
        main_frame=None,
        text="Algorithm-specific variables",
        log_level="INFO",
    ):
        if top:
            self.trainTop = top
        else:
            self.trainTop = tkinter.Toplevel()

        self.file_selector = file_selector
        self.master = master
        self.annotation_name = annotation_name
        self.annotation_level = annotation_level or tkinter.StringVar(
            self.trainTop, value="top level"
        )
        self.document_filter = document_filter or tkinter.StringVar(
            self.trainTop, value="all documents"
        )
        self.log_level = log_level
        self.wapiti_train_logger = logging.getLogger("sem.wapiti_train")
        self.wapiti_train_logger.addHandler(default_handler)
        self.wapiti_train_logger.setLevel(self.log_level)

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

        compact_btn = tkinter.ttk.Checkbutton(
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
        exporter = sem.exporters.conll.Exporter()
        alg = self.algorithm()
        l1 = self.l1()
        l2 = self.l2()
        pattern = self.pattern()
        nprocs = self.nprocs()
        compact = self.compact()
        masterfile = self.master.workflow()
        export_format = "conll"
        pipeline, workflow_options, exporter, couples = load_master(
            masterfile, force_format=export_format, pipeline_mode="train"
        )
        annotation_level = str2filter[self.annotation_level.get()]
        document_filter = str2docfilter[self.document_filter.get()]

        target_model = None
        pipes = [pipe for pipe in pipeline]
        for pipe in reversed(pipes):
            if isinstance(pipe, EnrichModule):
                pipe.mode = "train"
                self.annotation_name = pipe.informations.aentries[-1].name
                pipe.mode = "label"
                break
            elif isinstance(pipe, WapitiLabelModule):
                self.annotation_name = pipe.field
                target_model = pathlib.Path(pipe.model)
                break

        out_dir = None
        if target_model:
            out_dir = target_model.parent
            name = target_model.name
            try:
                os.makedirs(out_dir)
            except FileExistsError:  # python3
                pass

        timestamp = time.strftime("%Y%m%d%H%M%S")
        output_dir = self.current_train / timestamp
        if not output_dir.exists():
            os.makedirs(output_dir)

        train_file = output_dir / "train.conll"
        model_file = output_dir / "model.txt"
        try:
            files = self.file_selector.files()
        except Exception:
            files = self.file_selector
        fields = []
        names = set()
        with open(train_file, "w", encoding="utf-8") as output_stream:
            for filename in files:
                document = sem.importers.load(
                    filename, encoding="utf-8", tagset_name=self.annotation_name
                )
                args = Holder(
                    **{
                        "infiles": [document],
                        "pipeline": pipeline,
                        "options": workflow_options,
                        "exporter": None,
                        "couples": None,
                    }
                )
                if isinstance(document, SEMCorpus):
                    for doc in document:
                        if doc.name in names:
                            self.wapiti_train_logger.warn(
                                "document %s already found, skipping", doc.name
                            )
                            continue
                        elif not document_filter(doc, self.annotation_name):
                            self.wapiti_train_logger.warn(
                                "document %s has no annotations, skipping", doc.name
                            )
                            continue
                        args.infiles = [doc]
                        doc = tagger(args)[0]

                        if self.annotation_name is not None:
                            doc.add_to_corpus(self.annotation_name, filter=annotation_level)
                            doc.corpus.write(output_stream)
                        if not fields:
                            fields = doc.corpus.fields[:-1]
                else:
                    if document.name in names:
                        self.wapiti_train_logger.warn(
                            "document %s already found, skipping", document.name
                        )
                        continue
                    elif not document_filter(document, self.annotation_name):
                        self.wapiti_train_logger.warn(
                            "document %s has no annotations, skipping", document.name
                        )
                        continue

                    document = tagger(args)[0]

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
            sequences.append(bytes("\n".join("\t".join(seq) for seq in sequence) + "\n", "utf-8"))
        model.train(sequences)
        model.save(str(model_file))
        del model

        model_update_message = (
            "\n\nNo candidate location found," " model update has to be done manually"
        )
        if target_model:
            if target_model.exists():
                bname = pathlib.Path(name).stem
                ext = pathlib.Path(name).suffix
                backup_name = "{}.backup-{}{}".format(bname, timestamp, ext)
                dest = out_dir / backup_name
                self.wapiti_train_logger.info("creating backup file before moving: %s", dest)
                shutil.move(target_model, dest)
            self.wapiti_train_logger.info("trained model moved to: %s", str(out_dir))
            model_update_message = "\n\nTrained model moved to: {0}".format(out_dir)
            shutil.copy(model_file, target_model)

        self.wapiti_train_logger.info("files are located in: %s", str(output_dir))
        tkinter.messagebox.showinfo(
            "training SEM",
            "Everything went ok! files are located in: {0}{1}".format(
                output_dir, model_update_message
            ),
        )

        if self.main_frame:
            self.main_frame.destroy()
        else:
            self.trainTop.destroy()


class SEMTkTrainInterface(tkinter.ttk.Frame):
    def __init__(self, documents, lang=None, master=None):
        self.documents = documents
        self._lang = lang
        self._master = master
        if not (master and lang):
            self._master = None
            self._lang = None
        self.master_selector = None
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

        if not self._master:
            self.master_selector = SemTkMasterSelector(varsFrame, sem.SEM_DATA_DIR / "resources")
        if not self._lang:
            self.lang_selector = SemTkLangSelector(varsFrame, sem.SEM_DATA_DIR / "resources")
            self.lang_selector.master_selector = self.master_selector

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
        if self.master_selector:
            vars_cur_row, _ = self.master_selector.grid(row=vars_cur_row, column=0)

        for _ in range(5):
            tkinter.ttk.Separator(trainTop, orient=tkinter.HORIZONTAL).pack()

        algsFrame.pack(fill="both", expand="yes")

        notebook.pack()

        crf_cur_row = 0

        crf_train = SEMTkWapitiTrain(
            self.documents,
            self.master,
            None,
            annotation_level=annotation_level_var,
            document_filter=document_filter_var,
            top=frame1,
            main_frame=trainTop,
            text="CRF-specific variables",
        )

    @property
    def master(self):
        return self._master or self.master_selector

    @property
    def lang(self):
        return self._lang or self.lang_selector


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
