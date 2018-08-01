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

try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk

try:
    import ttk
except ImportError:
    ttk = tk.ttk

try:
    from xml.etree import cElementTree as ET
except ImportError:
    from xml.etree import ElementTree as ET

from tkFont import Font
import tkFileDialog
import tkMessageBox

import os.path
import multiprocessing
import time
import codecs
import shutil
import logging

import sem
import sem.wapiti, sem.exporters.conll
import sem.importers

from sem.storage import Holder, Document, SEMCorpus
from sem.modules.tagger import load_master, main as tagger
from sem.modules import EnrichModule
from sem.logger import default_handler
from sem.storage.annotation import str2filter
from sem.storage import Annotation
from sem.misc import find_suggestions

class SemTkMasterSelector(ttk.Frame):
    def __init__(self, root, resource_dir, lang="fr"):
        ttk.Frame.__init__(self, root)
        
        self.resource_dir = resource_dir
        self._lang = None
        langs = os.listdir(os.path.join(self.resource_dir, "master"))
        if langs:
            self._lang = (lang if lang in langs else langs[0])
        
        self.items = (os.listdir(os.path.join(self.resource_dir, "master", self._lang)) if self._lang else [])
        self.items.sort(key=lambda x: x.lower())
        max_length = max([len(item) for item in self.items])
        
        self.select_workflow_label = ttk.Label(root, text=u"select workflow:")
        self.masters = tk.Listbox(root, width=max_length+1, height=len(self.items))

        for item in self.items:
            self.masters.insert(tk.END, item)
    
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
        return (x,y)
    
    def workflow(self):
        wf = self.masters.get(tk.ACTIVE)
        return os.path.join(self.resource_dir, "master", self.lang(), wf) or None
    
    def lang(self):
        return self._lang
    
    def set_lang(self, language):
        self._lang = language
        self.items = os.listdir(os.path.join(self.resource_dir, "master", self._lang))
        self.items.sort(key=lambda x: x.lower())
        max_length = max([len(item) for item in self.items] + [0])
        self.masters["height"] = len(self.items)
        
        self.masters.delete(0, tk.END)
        for item in self.items:
            self.masters.insert(tk.END, item)


class SemTkLangSelector(ttk.Frame):
    def __init__(self, root, resource_dir):
        ttk.Frame.__init__(self, root)
        
        self.master_selector = None
        self.resource_dir = resource_dir
        self.items = os.listdir(os.path.join(self.resource_dir, "master"))
        
        self.cur_lang = tk.StringVar()
        self.select_lang_label = ttk.Label(root, text=u"select language:")
        self.langs = ttk.Combobox(root, textvariable=self.cur_lang)
        
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
        return (x,y)
    
    def lang(self):
        return self.cur_lang.get()
    
    def select_lang(self, event):
        self.master_selector.set_lang(self.lang())


class SemTkFileSelector(ttk.Frame):
    def __init__(self, root, main_window, button_opt):
        ttk.Frame.__init__(self, root)
        
        self.root = root
        self.main_window = main_window
        self.current_files = None
        self.button_opt = button_opt
        
        # define options for opening or saving a file
        self.file_opt = options = {}
        options['defaultextension'] = '.txt'
        options['filetypes'] = [('all files', '.*'), ('text files', '.txt')]
        options['initialdir'] = os.path.expanduser("~")
        options['parent'] = root
        options['title'] = 'Select files to annotate.'
        
        self.file_selector_button = ttk.Button(self.root, text=u"select file(s)", command=self.filenames)
        self.label = ttk.Label(self.root, text=u"selected file(s):")
        self.fa_search = tk.PhotoImage(file=os.path.join(self.main_window.resource_dir, "images", "fa_search_24_24.gif"))
        self.file_selector_button.config(image=self.fa_search, compound=tk.LEFT)
        
        self.scrollbar = ttk.Scrollbar(self.root)
        self.selected_files = tk.Listbox(self.root, yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.selected_files.yview)
    
    def pack(self):
        self.file_selector_button.pack(**self.button_opt)
        self.label.pack()
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.selected_files.pack(fill=tk.BOTH, expand=True)
    
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
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.selected_files.grid(row=x, column=y, fill=tk.BOTH, expand=True)
        x += 1
        return (x,y)

    def filenames(self, event=None):
        self.current_files = list(tkFileDialog.askopenfilenames(**self.file_opt))
        self.current_files.sort(key=lambda x:x.lower())
        self.selected_files.delete(0, tk.END)
        if self.current_files:
            for current_file in self.current_files:
                self.selected_files.insert(tk.END, os.path.basename(current_file))
            self.file_opt['initialdir'] = os.path.dirname(self.current_files[0])
    
    def files(self):
        return self.current_files or []


class SemTkExportSelector(ttk.Frame):
    def __init__(self, root):
        ttk.Frame.__init__(self, root)
        
        self.root = root
        self.label = ttk.Label(self.root, text=u"select output format:")
        
        self.export_formats = ["default"] + [exporter[:-3] for exporter in os.listdir(os.path.join(sem.SEM_HOME, "exporters")) if (exporter.endswith(".py") and not exporter.startswith("_") and not exporter == "exporter.py")]
        self.export_combobox = ttk.Combobox(self.root)
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
        return (x,y)
    
    def export_format(self):
        return self.export_combobox.get()


class SEMTkWapitiTrain(ttk.Frame):
    def __init__(self, file_selector, master, annotation_name, annotation_level=None, top=None, main_frame=None, text="Algorithm-specific variables", log_level="INFO"):
        if top:
            self.trainTop = top
        else:
            self.trainTop = tk.Toplevel()
        
        
        self.file_selector = file_selector
        self.master = master
        self.annotation_name = annotation_name
        self.annotation_level = annotation_level or tk.StringVar(self.trainTop, value="top level")
        self.log_level = log_level
        self.wapiti_train_logger = logging.getLogger("sem.wapiti_train")
        self.wapiti_train_logger.addHandler(default_handler)
        self.wapiti_train_logger.setLevel(self.log_level)
        
        self.current_train = os.path.join(sem.SEM_DATA_DIR, "train")
        if not os.path.exists(self.current_train):
            os.makedirs(self.current_train)
        
        self.main_frame = main_frame or self.trainTop
        self.trainTop.focus_set()
        self.CRF_algorithm_var = tk.StringVar(self.trainTop, value="rprop")
        self.CRF_l1_var = tk.StringVar(self.trainTop, value="0.5")
        self.CRF_l2_var = tk.StringVar(self.trainTop, value="0.0001")
        self.CRF_nprocs_var = tk.StringVar(self.trainTop, value="1")
        self.pattern_label_var = tk.StringVar(self.trainTop, value="")
        self.compact_var = tk.IntVar()
        self.compact_var.set(1)
        
        algsFrame = ttk.LabelFrame(self.trainTop, text=text)
        algsFrame.pack(fill="both", expand="yes")
        
        crf_cur_row = 0
        
        ttk.Button(algsFrame, text='pattern (optional)', command=self.select_file).grid(row=crf_cur_row, column=0, sticky=tk.W)
        self.pattern_label = tk.Label(algsFrame, textvariable=self.pattern_label_var)
        self.pattern_label.grid(row=crf_cur_row, column=1, sticky=tk.W)
        crf_cur_row += 1
        
        tk.Label(algsFrame, text='algorithm').grid(row=crf_cur_row, column=0, sticky=tk.W)
        CRF_algorithmValue = ttk.Combobox(algsFrame, textvariable=self.CRF_algorithm_var)
        CRF_algorithmValue["values"] = [u"rprop", u"l-bfgs", u"sgd-l1", u"bcd", u"rprop+", u"rprop-"]
        CRF_algorithmValue.current(0)
        CRF_algorithmValue.grid(row=crf_cur_row, column=1)
        crf_cur_row += 1
        
        tk.Label(algsFrame, text='l1').grid(row=crf_cur_row, column=0, sticky=tk.W)
        CRF_algorithmValue = tk.Entry(algsFrame, textvariable=self.CRF_l1_var)
        CRF_algorithmValue.grid(row=crf_cur_row, column=1)
        crf_cur_row += 1
        
        tk.Label(algsFrame, text='l2').grid(row=crf_cur_row, column=0, sticky=tk.W)
        CRF_algorithmValue = tk.Entry(algsFrame, textvariable=self.CRF_l2_var)
        CRF_algorithmValue.grid(row=crf_cur_row, column=1)
        crf_cur_row += 1
        
        tk.Label(algsFrame, text='number of processors').grid(row=crf_cur_row, column=0, sticky=tk.W)
        CRF_nprocsValue = ttk.Combobox(algsFrame, textvariable=self.CRF_nprocs_var)
        CRF_nprocsValue["values"] = range(1, multiprocessing.cpu_count()+1)
        CRF_nprocsValue.current(0)
        CRF_nprocsValue.grid(row=crf_cur_row, column=1)
        crf_cur_row += 1
        
        compact_btn = ttk.Checkbutton(algsFrame, text="compact model", variable=self.compact_var).grid(row=crf_cur_row, column=0, sticky=tk.W)
        crf_cur_row += 1
        
        CRF_trainButton = tk.Button(algsFrame, text="train", command=self.trainCRF)
        CRF_trainButton.grid(row=crf_cur_row, column=0)
        crf_cur_row += 1
    
    def select_file(self, event=None):
        options = {}
        options['defaultextension'] = '.txt'
        options['filetypes'] = [('all files', '.*'), ('text files', '.txt')]
        options['initialdir'] = os.path.join(sem.SEM_DATA_DIR, "resources", "patterns")
        options['parent'] = self.trainTop
        options['title'] = 'Select pattern file.'
        pattern = tkFileDialog.askopenfilename(**options)
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
        pipeline, workflow_options, exporter, couples = load_master(masterfile, force_format=export_format)
        annotation_level = str2filter[self.annotation_level.get()]
        
        paren, name = os.path.split(masterfile)
        paren1, lang = os.path.split(paren)
        rootdir = os.path.dirname(paren1)
        mod_dir = os.path.join(rootdir, "models", lang)
        mod_subdirs = os.listdir(mod_dir)
        suggestions = find_suggestions(name, mod_subdirs, case_sensitive=False)
        out_dir = None
        if suggestions != []:
            out_dir = os.path.join(mod_dir, suggestions[0])
        
        pipes = [pipe for pipe in pipeline]
        for pipe in reversed(pipes):
            if isinstance(pipe, EnrichModule):
                pipe.mode = "train"
                self.annotation_name = pipe.informations.aentries[-1].name
                pipe.mode = "label"
                break
        
        timestamp = time.strftime("%Y%m%d%H%M%S")
        output_dir = os.path.join(self.current_train, timestamp)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        train_file = os.path.join(output_dir, "train.conll")
        model_file = os.path.join(output_dir, "model.txt")
        try:
            files = self.file_selector.files()
        except:
            files = self.file_selector
        fields = []
        names = set()
        with codecs.open(train_file, "w", "utf-8") as O:
            for filename in files:
                document = sem.importers.load(filename, encoding="utf-8")
                args = Holder(**{"infile":document, "pipeline":pipeline, "options":workflow_options, "exporter":None, "couples":None})
                if isinstance(document, SEMCorpus):
                    for doc in document:
                        if doc.name in names:
                            continue
                        args.infile = doc
                        doc = tagger(args)
                        
                        if self.annotation_name is not None:
                            doc.add_to_corpus(self.annotation_name, filter=annotation_level)
                            O.write(unicode(doc.corpus))
                            O.write(u"\n")
                        if not fields:
                            fields = doc.corpus.fields[:-1]
                else:
                    document = tagger(args)
                    if document.name in names:
                        continue
                    
                    if self.annotation_name is not None:
                        document.add_to_corpus(self.annotation_name, filter=annotation_level)
                        O.write(unicode(document.corpus))
                        O.write(u"\n")
                        if not fields:
                            fields = document.corpus.fields[:-1]
        
        pattern_file = os.path.join(output_dir, "pattern.txt")
        if pattern:
            shutil.copy(pattern, pattern_file)
        else:
            with codecs.open(os.path.join(output_dir, "pattern.txt"), "w", "utf-8") as O:
                O.write("u\n\n")
                for i, field in enumerate(fields):
                    for shift in range(-2,3):
                        O.write("u:{0} {1:+d}=%x[{1},{2}]\n".format(field, shift, i))
                    O.write(u"\n")
                O.write("b\n")
        
        with codecs.open(os.path.join(output_dir, "config.txt"), "w", "utf-8") as O:
            O.write(u"algorithm\t{0}\n".format(alg))
            O.write(u"l1\t{0}\n".format(l1))
            O.write(u"l2\t{0}\n".format(l2))
            O.write(u"number of processors\t{0}\n".format(nprocs))
            O.write(u"compact\t{0}\n".format(compact))
        
        sem.wapiti.train(train_file, pattern=pattern_file, output=model_file, algorithm=alg, rho1=l1, rho2=l2, nthreads=nprocs, compact=compact)
        
        model_update_message = "\n\nNo candidate location found, model update has to be done manually"
        if out_dir:
            model_out = os.path.join(out_dir, "model.txt")
            if os.path.exists(model_out):
                backup_name = "model.backup-{0}.txt".format(timestamp)
                dest = os.path.join(out_dir, backup_name)
                self.wapiti_train_logger.info('creating backup file before moving: %s', dest)
                shutil.move(model_out, dest)
            self.wapiti_train_logger.info('trained model moved to: %s', out_dir)
            model_update_message = "\n\nTrained model moved to: {0}".format(out_dir)
            shutil.copy(model_file, model_out)
        
        self.wapiti_train_logger.info("files are located in: " + output_dir)
        tkMessageBox.showinfo("training SEM", "Everything went ok! files are located in: {0}{1}".format(output_dir, model_update_message))
        
        if self.main_frame:
            self.main_frame.destroy()
        else:
            self.trainTop.destroy()


class SearchFrame(ttk.Frame):
    def __init__(self, text, regexp=False, nocase=False):
        self.text = text
        self.pattern = tk.StringVar()
        self.regexp = tk.IntVar(int(regexp))
        self.nocase = tk.IntVar(int(nocase))
        self.prev_pattern = ""
        self.prev_regexp = regexp
        self.prev_nocase = nocase
        self.findings = []
        self.current = -1
        self.text.tag_config("search", background='yellow', foreground="black")
        bold_font = Font(self.text)
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
        find_in_text_top = tk.Toplevel()
        find_in_text_top.title("search")
        find_in_text_top.focus_set()
        matchesVar = tk.StringVar()
        
        def nxt(event=None):
            pattern = self.pattern.get()
            regexp = self.regexp.get()
            nocase = self.nocase.get()
            if pattern != self.prev_pattern or regexp != self.prev_regexp or nocase != self.prev_nocase:
                self.clear_tags()
                self.prev_pattern = pattern
                self.prev_regexp = regexp
                self.prev_nocase = nocase
                del self.findings[:]
                start = 1.0
                countVar = tk.StringVar()
                pos = self.text.search(pattern, start, stopindex="end", count=countVar, regexp=self.regexp.get(), nocase=self.nocase.get())
                while pos:
                    end = "{0} + {1}c".format(pos, countVar.get())
                    self.text.tag_add("search", pos, end)
                    self.findings.append((pos, end))
                    start = end
                    pos = self.text.search(pattern, start, stopindex="end", count=countVar, regexp=self.regexp.get(), nocase=self.nocase.get())
                self.current = 1
            elif self.findings:
                prev = self.findings[self.current-1]
                self.current = (self.current+1 if self.current < len(self.findings) else 1)
                self.text.tag_remove("search_current",  prev[0],  prev[1])
            
            if self.findings:
                self.text.tag_add("search_current", self.findings[self.current-1][0], self.findings[self.current-1][1])
                matchesVar.set("match {0} out of {1}".format(self.current, len(self.findings)))
                self.text.mark_set("insert", self.findings[self.current-1][1])
                self.text.see("insert")
            else:
                matchesVar.set("no matches found")
        
        def cancel(event=None):
            self.clear()
            find_in_text_top.destroy()
        
        label1 = tk.Label(find_in_text_top, text="search for:")
        
        text = ttk.Entry(find_in_text_top, textvariable=self.pattern)
        
        next_btn = ttk.Button(find_in_text_top, text="next", command=nxt)
        cancel_btn = ttk.Button(find_in_text_top, text="cancel", command=cancel)
        matches_found_lbl = tk.Label(find_in_text_top, textvariable=matchesVar)
        regexp_btn = ttk.Checkbutton(find_in_text_top, text="regular expression", variable=self.regexp)
        nocase_btn = ttk.Checkbutton(find_in_text_top, text="ignore case", variable=self.nocase)
        label1.grid(row=0, column=0)
        text.grid(row=0, column=1)
        regexp_btn.grid(row=1, column=0)
        nocase_btn.grid(row=1, column=1)
        next_btn.grid(row=2, column=0)
        cancel_btn.grid(row=2, column=1)
        matches_found_lbl.grid(row=3, column=0, columnspan=2)
        text.focus_set()
        
        find_in_text_top.bind('<Return>', nxt)
        find_in_text_top.bind('<Escape>', cancel)
        find_in_text_top.protocol("WM_DELETE_WINDOW", cancel)
