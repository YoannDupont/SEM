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

import tkFileDialog
import tkMessageBox

import os.path
import multiprocessing
import time
import codecs

import sem
import sem.wapiti, sem.exporters.conll
import sem.importers
from sem.storage import Holder
from sem.storage import Document
from sem.modules.tagger import load_master, main as tagger

class SemTkMasterSelector(ttk.Frame):
    def __init__(self, root, resource_dir, lang="fr"):
        ttk.Frame.__init__(self, root)
        
        self._lang = lang
        self.resource_dir = resource_dir
        
        items = os.listdir(os.path.join(self.resource_dir, "master", self._lang))
        items.sort(key=lambda x: x.lower())
        max_length = max([len(item) for item in items])
        
        self.select_workflow_label = ttk.Label(root, text=u"select workflow:")
        self.masters = tk.Listbox(root, width=max_length+1, height=len(items))

        for item in items:
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
        items = os.listdir(os.path.join(self.resource_dir, "master", self._lang))
        max_length = max([len(item) for item in items] + [0])
        self.masters["height"] = len(items)
        
        self.masters.delete(0, tk.END)
        for item in items:
            self.masters.insert(tk.END, item)


class SemTkLangSelector(ttk.Frame):
    def __init__(self, root, resource_dir):
        ttk.Frame.__init__(self, root)
        
        self.master_selector = None
        self.resource_dir = resource_dir
        items = os.listdir(os.path.join(self.resource_dir, "master"))
        
        self.select_lang_label = ttk.Label(root, text=u"select language:")
        self.langs = tk.Listbox(root, height=len(items), selectmode=tk.SINGLE)

        for i, item in enumerate(items):
            self.langs.insert(tk.END, item)
            if item == "fr":
                self.langs.activate(i)
                self.langs.selection_set(i)
        
        self.langs.bind('<<ListboxSelect>>', self.select_lang)
    
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
        return self.langs.get(tk.ACTIVE)
    
    def select_lang(self, event):
        selected = self.langs.curselection()[0]
        self.langs.selection_set(selected)
        self.langs.activate(selected)
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
        self.current_files = tkFileDialog.askopenfilenames(**self.file_opt)
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
    def __init__(self, file_selector, master):
        self.file_selector = file_selector
        self.master = master
        
        self.current_train = os.path.join(sem.SEM_DATA_DIR, "train")
        if not os.path.exists(self.current_train):
            os.makedirs(self.current_train)
        
        self.trainTop = tk.Toplevel()
        self.trainTop.focus_set()
        self.CRF_algorithm_var = tk.StringVar(self.trainTop, value="rprop")
        self.CRF_l1_var = tk.StringVar(self.trainTop, value="0.5")
        self.CRF_l2_var = tk.StringVar(self.trainTop, value="0.0001")
        self.CRF_nprocs_var = tk.StringVar(self.trainTop, value="1")
        self.pattern_label_var = tk.StringVar(self.trainTop, value="")
        self.compact_var = tk.IntVar()
        
        algsFrame = ttk.LabelFrame(self.trainTop, text="Algorithm-specific variables")
        algsFrame.pack(fill="both", expand="yes")
        
        crf_cur_row = 0
        
        ttk.Button(algsFrame, text='pattern (optional)', command=self.select_file).grid(row=crf_cur_row, column=0, sticky=tk.W)
        pattern_label = tk.Label(algsFrame, textvariable=self.pattern_label_var)
        pattern_label.grid(row=crf_cur_row, column=1, sticky=tk.W)
        crf_cur_row += 1
        
        tk.Label(algsFrame, text='algotirhm').grid(row=crf_cur_row, column=0, sticky=tk.W)
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
        options['initialdir'] = os.path.expanduser("~")
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
        self.pattern_label_var.get()
    
    def compact(self):
        return bool(self.compact_var.get())
    
    def trainCRF(self, events=None):
        exporter = sem.exporters.conll.Exporter()
        alg = self.algorithm()
        l1 = self.l1()
        l2 = self.l2()
        nprocs = self.nprocs()
        pattern = self.pattern()
        compact = self.compact()
        masterfile = self.master.workflow()
        export_format = "conll"
        pipeline, workflow_options, exporter, couples = load_master(masterfile, force_format=export_format)
        
        output_dir = os.path.join(self.current_train, time.strftime("%Y%m%d%H%M%S"))
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        train_file = os.path.join(output_dir, "train.conll")
        pattern_file = (pattern if pattern else os.path.join(output_dir, "pattern.txt"))
        model_file = os.path.join(output_dir, "model.txt")
        documents = []
        with codecs.open(train_file, "w", "utf-8") as O:
            for filename in self.file_selector.files():
                document = sem.importers.load(filename, encoding="utf-8")
                args = Holder(**{"infile":document, "pipeline":pipeline, "options":workflow_options, "exporter":None, "couples":None})
                document = tagger(args)
                
                document.set_reference("NER", "tokens", add_to_corpus=True)
                O.write(unicode(document.corpus))
                O.write(u"\n")
                documents.append(document)
        
        if pattern:
            shutil.copy(pattern, output_dir)
        else:
            with codecs.open(pattern_file, "w", "utf-8") as O:
                O.write("u\n\n")
                for i, field in enumerate(documents[0].corpus.fields[:-1]):
                    for shift in range(-2,3):
                        O.write("u:%s %+i=%%x[%i,%i]\n" %(field, shift, shift, i))
                    O.write(u"\n")
                O.write("b\n")
        
        with codecs.open(os.path.join(output_dir, "config.txt"), "w", "utf-8") as O:
            O.write(u"algorithm\t%s\n" %alg)
            O.write(u"l1\t%s\n" %l1)
            O.write(u"l2\t%s\n" %l2)
            O.write(u"number of processors\t%s\n" %nprocs)
            O.write(u"compact\t%s\n" %compact)
        
        sem.wapiti.train(train_file, pattern=pattern_file, output=model_file, algorithm=alg, rho1=l1, rho2=l2, nthreads=nprocs, compact=compact)
        
        tkMessageBox.showinfo("training SEM", "Everything went ok! files are located in: " + output_dir)
        
        self.trainTop.destroy()
