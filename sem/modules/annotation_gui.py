"""
file: annotation_gui.py

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

import codecs
import re
import logging
import sys
import os

try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk

try:
    import ttk
except ImportError:
    ttk = tk.ttk

from tkFont import Font
import tkFileDialog
import ScrolledText
import tkMessageBox

import sem
from sem.storage.document import Document, SEMCorpus
from sem.storage.annotation import Tag, Annotation
from sem.logger import extended_handler
import sem.importers
from sem.gui.misc import find_potential_separator, find_occurrences, random_color, Adder

annotate_logger = logging.getLogger("sem.annotate")
annotate_logger.addHandler(extended_handler)

LETTERS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'

def update_annotations(document, annotation_name, annotations):
    annots = Annotation(annotation_name)
    annots.annotations = annotations
    try:
        reference = document.annotation(annotation_name).reference
    except:
        reference = None
    document.add_annotation(annots)
    if reference:
        document.set_reference(annotation_name, reference.name)

class AnnotationTool(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        annotate_logger.debug("========== entering method")
        tk.Frame.__init__(self, parent, *args, **kwargs)
        
        self.parent = parent
        
        self.user = None
        self.doc = None
        self.annotations = []
        self.annotations_tick = 0
        
        self.lines_lengths = []
        
        #
        # menu
        #
        self.global_menu = tk.Menu(self.parent)
        # file menu
        self.file_menu = tk.Menu(self.global_menu, tearoff=False)
        self.global_menu.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Open...", command=self.openfile, accelerator="Ctrl+O")
        self.file_menu.add_command(label="Open url...", command=self.openurl, accelerator="Ctrl+Shift+O")
        self.file_menu.add_command(label="Save to...", command=self.save, accelerator="Ctrl+S")
        self.file_menu.entryconfig("Save to...", state=tk.DISABLED)
        # edit menu
        self.edit_menu = tk.Menu(self.global_menu, tearoff=False)
        self.global_menu.add_cascade(label="Edit", menu=self.edit_menu)
        self.edit_menu.add_command(label="Preferences...", command=self.preferences)
        # final
        self.parent.config(menu=self.global_menu)
        
        self.new_type = tk.StringVar()
        self.spare_colors = [{"background":"#FFBB55", "foreground":"#BB5500"}]
        self.spare_colors = []
        self.spare_colors = [{"background":"#FFCCCC", "foreground":"#FF0000"}, {"background":"#CCEEEE", "foreground":"#008888"}, {"background":"#CCCCFF", "foreground":"#0000FF"}, {"background":"#DDFFDD", "foreground":"#008800"}, {"background":"#CCCCCC", "foreground":"#000000"}][::-1]
        
        self.bind_all("<Control-o>", self.openfile)
        self.bind_all("<Control-O>", self.openurl)
        self.bind_all("<Control-s>", self.save)
        self.bind_all("<Control-t>", self.train)
        self.focus_set()
        
        self.bind_all("<Tab>", self.tab)
        self.bind_all("<Shift-Tab>", self.shift_tab)
        
        self.available_chars = [set(u"abcdefghijklmnopqrstuvwxyz")]
        self.SELECT_TYPE = u"-- select type --"
        self.current_selection = None
        self.wish_to_add = []
        
        self.errors = codecs.open(".errors", "a", "utf-8")
        
        self.position2annots = {}
        self.current_annots = []
        
        self.current_annotations = Annotation("CurrentAnnotations")
        
        self.type_hierarchy = [] # types, subtypes, subsubtypes, etc...
        self.current_type_hierarchy_level = 0
        
        self.adders = [{}]

        self.toolbar = ttk.Frame(self)
        self.toolbar.pack(side="top", fill="x")

        self.train_btn = ttk.Button(self.toolbar, text="train", command=self.train)
        self.train_btn.pack(side="left")
        self.train_btn.configure(state=tk.DISABLED)

        self.load_tagset_btn = ttk.Button(self.toolbar, text="load tagset", command=self.load_tagset_gui)
        self.load_tagset_btn.pack(side="left")

        self.type_combos = []
        
        self.add_type_lbls = []
        
        self.annotation_row = ttk.PanedWindow(self, orient="horizontal")
        
        self.corpus_tree = ttk.Treeview(self.annotation_row)
        self.corpus_tree.heading("#0", text="corpus", anchor=tk.W)
        self.corpus_tree.bind("<<TreeviewSelect>>", self.load_document)
        self.corpus_documents = []
        self.corpus_id2doc = {}
        self.corpus_doc2id = {}
        
        self.text = ScrolledText.ScrolledText(self.annotation_row, wrap=tk.WORD, font="Helvetica")
        self.text.configure(state="disabled")
        for adder in self.adders[0].values():
            self.text.bind("<%s>" %adder.shortcut, adder.add)
            self.tree.bind("<%s>" %adder.shortcut, adder.add)
            if adder.shortcut.islower():
                self.text.bind("<%s>" %adder.shortcut.upper(), adder.add_all)
                self.tree.bind("<%s>" %adder.shortcut.upper(), adder.add_all)
        self.text.bind("<Shift-Tab>", self.shift_tab)
        
        self.tree = ttk.Treeview(self.annotation_row)
        self.tree.heading("#0", text="annotation sets", anchor=tk.W)
        self.tree.bind("<<TreeviewSelect>>", self.select_from_tree)
        self.tree_ids = {}
        self.annot2treeitems = {}
        
        self.annotation_row.add(self.corpus_tree)
        self.annotation_row.add(self.text)
        self.annotation_row.add(self.tree)
        self.annotation_row.pack(side="left", fill="both", expand=True)
        
        self.text.bind("<Button-1>", self.click)
        self.text.bind("<Delete>", self.delete)
        self.text.bind("<Shift-Delete>", self.delete_all)
        self.text.bind("<Escape>", self.unselect)
        
        self.tree.bind("<Delete>", self.delete)
        self.tree.bind("<Shift-Delete>", self.delete_all)
        
        ## configuring a tag called BOLD
        bold_font = Font(self.text)
        bold_font.configure(weight="bold")
        self.text.tag_configure("BOLD", font=bold_font)
        
        self.workflow = None
        
        self.tree_ids = {}
        self.annot2treeitems = {}
        self.ner2history = {}
        
        #skip_auth=> self.auth()
    
    def auth(self, event=None):
        annotate_logger.debug("========== entering method")
        authTop = tk.Toplevel()
        authTop.grab_set()
        auth_login = tk.StringVar(authTop, value="admin")
        auth_pw = tk.StringVar(authTop, value="")
        
        def close():
            sys.exit(0)
        
        authTop.protocol('WM_DELETE_WINDOW', close)
        
        def check_auth():
            import time, hashlib
            pwd = auth_pw.get()
            if pwd == "":
                print "Please enter non empty password"
            try:
                content = open(".users").read()
                if "d033e22ae348aeb5660fc2140aec35850c4da997aee5aca44055f2cd2f2ce4266909b69a5d96dad2\n" not in content:
                    print "Something fishy about your .user file, rewriting it with admin user only."
                    with codecs.open(".users", "w") as O:
                        O.write("d033e22ae348aeb5660fc2140aec35850c4da997aee5aca44055f2cd2f2ce4266909b69a5d96dad2\n")
                    time.sleep(5.0)
                    sys.exit(1)
                h = hashlib.sha1()
                h.update(auth_login.get())
                login = h.hexdigest()
                h = hashlib.sha1()
                h.update(pwd)
                pw = h.hexdigest()
                checked = login + pw in content
                if checked:
                    self.user = auth_login.get()[:]
                    tkMessageBox.showinfo("Login success","Logged succesfuly as %s" %self.user)
                    
                    if self.user == "admin":
                        self.add_user_btn = ttk.Button(self.toolbar, text="add user", command=self.add_user)
                        self.add_user_btn.pack(side="left")
                    
                    authTop.destroy()
                else:
                    tkMessageBox.showerror("Login error", "Wrong login/password")
            except IOError:
                with codecs.open(".users", "w") as O:
                    O.write("d033e22ae348aeb5660fc2140aec35850c4da997aee5aca44055f2cd2f2ce4266909b69a5d96dad2\n")
                print "Could not find .user file, rewriting it with admin user only."
        
        authLabel = tk.Label(authTop, text="Enter credentials:")
        authLabel.grid(row=0, column=0, sticky=tk.W+tk.E, columnspan=2)
        
        tk.Label(authTop, text='login').grid(row=1, column=0, sticky=tk.W)
        auth_login_entry = tk.Entry(authTop, textvariable=auth_login)
        auth_login_entry.grid(row=1, column=1, sticky=tk.W)
        tk.Label(authTop, text='password').grid(row=2, column=0, sticky=tk.W)
        auth_pw_entry = tk.Entry(authTop, textvariable=auth_pw, show="*")
        auth_pw_entry.grid(row=2, column=1, sticky=tk.W)
        
        login_btn = ttk.Button(authTop, text="login", command=check_auth)
        login_btn.grid(row=3, column=0, sticky=tk.W+tk.E, columnspan=2)
        
    def add_user(self, event=None):
        annotate_logger.debug("========== entering method")
        authTop = tk.Toplevel()
        authTop.grab_set()
        auth_login = tk.StringVar(authTop, value="admin")
        auth_pw = tk.StringVar(authTop, value="")
        
        def check_auth():
            import hashlib
            pwd = auth_pw.get()
            if pwd == "":
                print "Please enter non empty password"
                return
            try:
                lines = [line.strip() for line in open(".users").readlines()]
                if "d033e22ae348aeb5660fc2140aec35850c4da997aee5aca44055f2cd2f2ce4266909b69a5d96dad2" not in lines:
                    print "Something fishy about your .user file, rewriting it with admin user only."
                    with codecs.open(".users", "w") as O:
                        O.write("d033e22ae348aeb5660fc2140aec35850c4da997aee5aca44055f2cd2f2ce4266909b69a5d96dad2\n")
                h = hashlib.sha1()
                h.update(auth_login.get())
                login = h.hexdigest()
                h = hashlib.sha1()
                h.update(auth_pw.get())
                pw = h.hexdigest()
                for line in lines:
                    if line.startswith(login):
                        tkMessageBox.showerror("Cannot add user", "User %s already exists" %(auth_login.get()))
                        return
                
                with codecs.open(".users", "a") as O:
                    O.write("%s%s\n" %(login, pw))
                tkMessageBox.showinfo("New user","Succesfuly added user %s" %auth_login.get())
                authTop.destroy()
            except IOError:
                with codecs.open(".users", "w") as O:
                    O.write("d033e22ae348aeb5660fc2140aec35850c4da997aee5aca44055f2cd2f2ce4266909b69a5d96dad2\n")
                print "Could not find .user file, rewriting it with admin user only."
        
        authLabel = tk.Label(authTop, text="Enter credentials:")
        authLabel.grid(row=0, column=0, sticky=tk.W+tk.E, columnspan=2)
        
        tk.Label(authTop, text='login').grid(row=1, column=0, sticky=tk.W)
        auth_login_entry = tk.Entry(authTop, textvariable=auth_login)
        auth_login_entry.grid(row=1, column=1, sticky=tk.W)
        tk.Label(authTop, text='password').grid(row=2, column=0, sticky=tk.W)
        auth_pw_entry = tk.Entry(authTop, textvariable=auth_pw, show="*")
        auth_pw_entry.grid(row=2, column=1, sticky=tk.W)
        
        login_btn = ttk.Button(authTop, text="login", command=check_auth)
        login_btn.grid(row=3, column=0, sticky=tk.W+tk.E, columnspan=2)
    
    #
    # file menu methods
    #
    
    def openfile(self, event=None):
        annotate_logger.debug("========== entering method")
        filenames = tkFileDialog.askopenfilenames(filetypes=[("SEM readable files", (".txt", ".sem.xml", ".sem")), ("text files", ".txt"), ("SEM XML files", ("*.sem.xml", ".sem")), ("All files", ".*")])
        if filenames == []: return
        
        documents = []
        for filename in filenames:
            if filename.endswith(".sem.xml") or filename.endswith(".sem"):
                try:
                    documents.append(Document.from_xml(filename, chunks_to_load=["NER"], load_subtypes=True))
                except:
                    documents.extend(SEMCorpus.from_xml(filename, chunks_to_load=["NER"], load_subtypes=True).documents)
            else:
                documents.append(sem.importers.load(filename, encoding="utf-8"))
        
        if documents == []: return
        
        added = False
        for document in documents:
            tmp = self.add_document(document)
            added = added or tmp
        if not added:
            return
        
        self.load_document(document)
        
        self.train_btn.configure(state=tk.NORMAL)
        self.file_menu.entryconfig("Save to...", state=tk.NORMAL)
        self.current_type_hierarchy_level = 0
        self.update_level()
    
    def openurl(self, event=None):
        annotate_logger.debug("========== entering method")
        import urllib
        toplevel = tk.Toplevel()
        
        self.url = tk.StringVar()
        
        def cancel(event=None):
            self.url.set("")
            toplevel.destroy()
        def ok(event=None):
            document = sem.importers.from_url(self.url.get(), wikinews_format=True)
            if document is None: return
        
            added = self.add_document(document)
            if not added: return
            
            self.load_document(document)
            
            self.train_btn.configure(state=tk.NORMAL)
            self.file_menu.entryconfig("Save to...", state=tk.NORMAL)
            cancel()
        
        label1 = tk.Label(toplevel, text="enter url:")
        label1.pack()
        
        text = ttk.Entry(toplevel, textvariable=self.url)
        text.pack()
        text.focus_set()
        
        toolbar = ttk.Frame(toplevel)
        toolbar.pack(side="top", fill="x")
        ok_btn = ttk.Button(toolbar, text="OK", command=ok)
        ok_btn.pack(side="left")
        cancel_btn = ttk.Button(toolbar, text="cancel", command=cancel)
        cancel_btn.pack(side="left")
        toplevel.bind('<Return>', ok)
        toplevel.bind('<Escape>', cancel)
        
        toolbar.pack()
    
    def add_tag(self, value, start, end):
        annotate_logger.debug("========== entering method")
        if type(start) == int:
            start_pos = self.charindex2position(start)
        else:
            start_pos = start
        if type(end) == int:
            end_pos = self.charindex2position(end)
        else:
            end_pos = end
        
        pos = (start, end)
        self.position2annots[pos] = self.position2annots.get(pos, set())
        
        if value not in self.position2annots[pos]:
            self.text.tag_add(value, start_pos, end_pos)
            self.position2annots[pos].add(value)
    
    def save(self, event=None):
        annotate_logger.debug("========== entering method")
        filename = tkFileDialog.asksaveasfilename(defaultextension=".sem.xml")
        if filename == u"": return
        
        update_annotations(self.doc, "NER", self.current_annots)
        
        corpus = SEMCorpus(documents=self.corpus_documents)
        with codecs.open(filename, "w", "utf-8") as O:
            corpus.write(O)
    
    #
    # Edit menu methods
    #
    
    def preferences(self, event=None):
        annotate_logger.debug("========== entering method")
        preferenceTop = tk.Toplevel()
        preferenceTop.focus_set()
        
        tkLabel = tk.Label(preferenceTop, text="Ain't nobody here but us chickens.")
        tkLabel.pack()
    
    #
    # global methods
    #
    
    def train(self, event=None):
        from sem.gui.components import SemTkMasterSelector
        annotate_logger.debug("========== entering method")
        trainTop = tk.Toplevel()
        trainTop.focus_set()
        vars_workflow = tk.StringVar(trainTop, value=r"C:\Users\Yoann\programmation\python\SEM-master\resources\master\fr\NER1-train.xml")
        CRF_algorithmString = tk.StringVar(trainTop, value="rprop")
        CRF_l1String = tk.StringVar(trainTop, value="0.5")
        CRF_l2String = tk.StringVar(trainTop, value="0.0001")
        
        varsFrame = ttk.LabelFrame(trainTop, text="Global variables")
        master_selector = SemTkMasterSelector(varsFrame, os.path.join(sem.SEM_HOME, "resources"))
        
        def trainCRF(event=None):
            from sem.modules.tagger import load_master, main as tagger
            from sem.storage.holder import Holder
            import sem.wapiti, sem.exporters.conll
            
            exporter = sem.exporters.conll.Exporter()
            alg = CRF_algorithmString.get()
            l1 = CRF_l1String.get()
            l2 = CRF_l2String.get()
            
            masterfile = os.path.join(sem.SEM_HOME, "resources", "master", master_selector.lang(), master_selector.workflow())
            if self.workflow is None or self.workflow != masterfile:
                self.workflow = masterfile
                pipeline, workflow_options, exporter, couples = load_master(masterfile)
                args = Holder(**{"infile":self.doc, "pipeline":pipeline, "options":workflow_options, "exporter":None, "couples":None})
                tagger(args)
            
            update_annotations(self.doc, "NER", self.current_annots)
            
            self.doc.set_reference("NER", "tokens", add_to_corpus=True)
            with codecs.open("_train/input.txt", "w", "utf-8") as O:
                O.write(unicode(self.doc.corpus))
            
            sem.wapiti.train("_train/input.txt", pattern="_train/pattern.txt", output="_train/model.txt", algorithm=alg, rho1=l1, rho2=l2)
            
            trainTop.destroy()
        
        
        varsFrame.pack(fill="both", expand="yes")
        vars_cur_row = 0
        vars_cur_row, _ = master_selector.grid(row=vars_cur_row, column=0)
        
        for _ in range(5):
            ttk.Separator(trainTop,orient=tk.HORIZONTAL).pack()
        
        algsFrame = ttk.LabelFrame(trainTop, text="Algorithm-specific variables")
        algsFrame.pack(fill="both", expand="yes")
        
        notebook = ttk.Notebook(algsFrame)
        frame1 = ttk.Frame(notebook)
        frame2 = ttk.Frame(notebook)
        notebook.add(frame1, text='CRF')
        notebook.add(frame2, text='NN')
        notebook.pack()
        
        crf_cur_row = 0
        
        tk.Label(frame1, text='algotirhm').grid(row=0, column=0, sticky=tk.W)
        CRF_algorithmValue = ttk.Combobox(frame1, textvariable=CRF_algorithmString, state="disabled")
        CRF_algorithmValue["values"] = [u"rprop", u"l-bfgs", u"sgd-l1", u"bcd", u"rprop+", u"rprop-"]
        CRF_algorithmValue.current(0)
        CRF_algorithmValue.grid(row=crf_cur_row, column=1)
        crf_cur_row += 1
        
        tk.Label(frame1, text='l1').grid(row=crf_cur_row, column=0, sticky=tk.W)
        CRF_algorithmValue = tk.Entry(frame1, textvariable=CRF_l1String)
        CRF_algorithmValue.grid(row=crf_cur_row, column=1)
        crf_cur_row += 1
        
        tk.Label(frame1, text='l2').grid(row=crf_cur_row, column=0, sticky=tk.W)
        CRF_algorithmValue = tk.Entry(frame1, textvariable=CRF_l2String)
        CRF_algorithmValue.grid(row=crf_cur_row, column=1)
        crf_cur_row += 1
        
        CRF_trainButton = tk.Button(frame1, text="train", command=trainCRF)
        CRF_trainButton.grid(row=crf_cur_row, column=0)
        crf_cur_row += 1
        
        tkLabel = tk.Label(frame2, text="Ain't nobody here but us chickens.")
        tkLabel.pack()
    
    def add_annotation(self, event, remove_focus=True):
        annotate_logger.debug("========== entering method")
        cur_type = Adder.label2type(self.type_combos[self.current_type_hierarchy_level].get(), self.current_type_hierarchy_level, self.SELECT_TYPE)
        if cur_type != self.SELECT_TYPE:
            first = "sel.first"
            last = "sel.last"
            value = self.adders[0][cur_type].type
        elif self.wish_to_add is not None:
            value, first, last = self.wish_to_add
        else:
            return
        
        text_select = False
        try:
            text_select = True
            if first == "sel.first":
                print "first", first,
                first = self.text.index("sel.first")
                print first
            if last == "sel.last":
                last = self.text.index("sel.last")
            
        except tk.TclError:
            print "error"
            return # no selection
        
        if self.current_type_hierarchy_level == 0:
            pos = (self.position2charindex(first), self.position2charindex(last))
            greater = [annot for annot in self.current_annots if annot.lb<=pos[0] and annot.ub>=pos[1] and value==annot.value]
            tag = Tag(pos[0], pos[1], value)
            tag.levels = [value]
            if tag not in self.current_annots and len(greater)==0:
                self.text.tag_add(value, first, last)
                self.current_selection = tag
                index = 0
                for annot in self.current_annots:
                    if annot.lb > tag.lb:
                        break
                    index += 1
                key = unicode(tag)
                item = self.tree.insert(self.tree_ids["NER"], index, text=u'%s "%s" [%i:%i]' %(value, self.doc.content[pos[0] : pos[1]], pos[0], pos[1]))
                self.treeitem2annot[item] = tag
                self.annot2treeitems["NER"][key] = item
                self.current_annots.insert(index, tag)
                self.current_annotations.add(tag)
                item2 = self.tree.insert(self.tree_ids["history"], 0, text='%s "%s" [%i:%i]' %(value, self.doc.content[pos[0] : pos[1]], pos[0], pos[1]))
                self.treeitem2annot[item2] = tag
                self.annot2treeitems["history"][key] = item2
                self.ner2history[item] = item2
            
            self.text.tag_remove("BOLD",  "1.0", 'end')
            self.type_combos[0].current(0)
        else:
            lb = self.position2charindex(first)
            ub = self.position2charindex(last)
            if self.wish_to_add is not None:
                for annot in self.current_annots:
                    if annot.levels == []:
                        annot.levels = annot.value.split(u".")
                    if annot.getLevel(0) == self.current_selection.getLevel(0) and annot.lb == lb and annot.ub == ub:
                        tree_item_str = self.locate_tree_item()
                        tree_item =  self.tree.item(tree_item_str)
                        annot.setLevel(self.current_type_hierarchy_level, self.wish_to_add[0])
                        new_text = u'%s "%s" [%i:%i]' %(annot.getValue(), self.doc.content[annot.lb : annot.ub], lb, ub)
                        self.tree.item(tree_item_str, text=new_text)
                        prev_item = self.ner2history[tree_item_str]
                        self.tree.delete(prev_item)
                        new_item = self.tree.insert(self.tree_ids["history"], 0, text=new_text)
                        self.ner2history[tree_item_str] = new_item
                        self.treeitem2annot[new_item] = self.treeitem2annot[tree_item_str]
        if remove_focus:
            self.wish_to_add = None
            self.current_selection = None
            self.current_type_hierarchy_level = 0
            self.update_level()
        else:
            self.text.tag_add("BOLD", first, last)
    
    def click(self, event):
        annotate_logger.debug("========== entering method")
        annotate_logger.debug("current_selection=%s" %self.current_selection)
        annotate_logger.debug("wish_to_add=%s" %self.wish_to_add)
        
        self.text.tag_remove("BOLD",  "1.0", 'end')
        prev_selection = self.current_selection
        self.current_selection = None
        self.wish_to_add = None
        index = event.widget.index("@%s,%s" % (event.x, event.y))
        names = list(self.text.tag_names(index))
        charindex = self.position2charindex(index)
        try:
            names.remove("sel")
        except ValueError:
            pass
        
        annotations = [annotation for annotation in self.current_annots if annotation.lb <= charindex and charindex <= annotation.ub]
        
        if annotations != self.annotations:
            self.annotations = annotations
            self.annotations_tick = -1
        self.annotations_tick += 1
        if self.annotations_tick >= len(self.annotations):
            self.annotations_tick = 0
        if len(self.annotations) > 0:
            curr_annot = self.annotations[self.annotations_tick]
            ci2p = self.charindex2position
            self.text.tag_add("BOLD", ci2p(curr_annot.lb), ci2p(curr_annot.ub))
            self.text.tag_remove(curr_annot.value, ci2p(curr_annot.lb), ci2p(curr_annot.ub))
            self.text.tag_add(curr_annot.value, ci2p(curr_annot.lb), ci2p(curr_annot.ub))
            self.current_selection = curr_annot
        
        tree_item = self.locate_tree_item()
        if tree_item is not None:
            annotate_logger.debug("tree_item=%s" %tree_item)
            self.tree.selection_set(tree_item)
            self.tree.focus(tree_item)
            self.select_from_tree()
            self.tree.see(tree_item)
        else:
            self.unselect()
        if len(annotations) == 0 or prev_selection != self.current_selection:
            self.current_type_hierarchy_level = 0
            self.update_level()
        
        annotate_logger.debug("current_selection=%s" %self.current_selection)
        annotate_logger.debug("wish_to_add=%s" %self.wish_to_add)
    
    def locate_tree_item(self):
        annotate_logger.debug("========== entering method")
        if self.current_selection is None:
            return None
        if self.wish_to_add:
            lb = self.position2charindex(self.wish_to_add[1])
            ub = self.position2charindex(self.wish_to_add[2])
        else:
            lb = self.current_selection.lb
            ub = self.current_selection.ub
        ner_root = self.tree.get_children()[0]
        id = None
        value = self.current_selection.value
        bounds = "[%i:%i]" %(lb, ub)
        for child in self.tree.get_children(ner_root):
            text = self.tree.item(child)["text"]
            ok = text.startswith(value) and text.endswith(bounds)
            if ok:
                return child
        return None
    
    def select_from_tree(self, event=None):
        annotate_logger.debug("========== entering method")
        parent = self.tree.parent(self.tree.selection()[0])
        annotate_logger.debug("selection=%s" %self.tree.selection()[0])
        if not parent: return
        
        annot = self.treeitem2annot[self.tree.selection()[0]]
        lb_str = self.charindex2position(annot.lb)
        ub_str = self.charindex2position(annot.ub)
        
        self.text.tag_remove("BOLD", "1.0", 'end')
        self.text.tag_add("BOLD", lb_str, ub_str)
        self.current_selection = annot
        self.wish_to_add = None
        
        self.text.mark_set("insert", ub_str)
        self.text.see("insert")
    
    def unselect(self, event=None):
        annotate_logger.debug("========== entering method")
        cmds = [cmd for cmd in dir(self.text) if u"tag" in cmd]
        l = self.text.tag_ranges("BOLD")
        if len(l) != 0:
            self.text.tag_remove("BOLD",  "1.0", 'end')
            self.wish_to_add = None
            self.current_selection = None
            self.current_type_hierarchy_level = 0
            self.update_level()
    
    def delete(self, event):
        annotate_logger.debug("========== entering method")
        self.text.tag_remove("BOLD",  "1.0", 'end')
        
        if self.current_selection is None: return
        
        value = self.current_selection.value
        lb = self.current_selection.lb
        ub = self.current_selection.ub
        matching = [a for a in self.current_annots if a.lb==lb and a.ub==ub and a.value==value]
        greater = [a for a in self.current_annots if a.lb<=lb and a.ub>=ub and a.value==value]
        try:
            greater.remove(matching[0])
        except:
            pass
        for annotation in matching:
            if len(greater) == 0:
                self.text.tag_remove(value, self.charindex2position(annotation.lb), self.charindex2position(annotation.ub))
            
            tag = Tag(annotation.lb, annotation.ub, value)
            key = unicode(tag)
            for v in self.annot2treeitems.values():
                item = v.get(key, None)
                if item is not None:
                    self.tree.delete(item)
                    if tag in self.current_annots:
                        self.current_annots.remove(tag)
                    del v[key]
                    del self.treeitem2annot[item]
        
        self.current_annotations.remove(self.current_selection)
        self.current_selection = None
        self.current_type_hierarchy_level = 0
        self.update_level()
    
    def delete_all(self, event):
        annotate_logger.debug("========== entering method")
        if self.current_selection is not None:
            value = self.current_selection.value
            start = self.current_selection.lb
            end = self.current_selection.ub
            self.errors.write(u"%s %s\n" %(self.doc.content[start:end], value))
            self.errors.flush()
            for occ in find_occurrences(self.doc.content[start:end], self.doc.content):
                self.current_selection = Tag(occ.start(), occ.end(), value)
                self.delete(event)
        self.current_selection = None
        self.current_type_hierarchy_level = 0
        self.update_level()
        self.text.tag_remove("BOLD",  "1.0", 'end')
    
    def position2charindex(self, position):
        annotate_logger.debug("========== entering method")
        line, index = [int(e) for e in position.split(".")]
        return sum(self.lines_lengths[:line]) + index
    
    def charindex2position(self, charindex):
        annotate_logger.debug("========== entering method")
        lengths = self.lines_lengths
        cur = 0
        line = 1
        while cur+lengths[line] <= charindex:
            cur += lengths[line]
            line += 1
        offset = charindex - cur
        return "%i.%i" %(line, offset)
    
    def tab(self, event=None):
        annotate_logger.debug("========== entering method")
        if self.current_selection is None:
            self.current_type_hierarchy_level = 0
            return
        
        self.current_type_hierarchy_level += 1
        if self.current_type_hierarchy_level == len(self.type_hierarchy):
            self.current_type_hierarchy_level = 0
        self.update_level()
    
    def shift_tab(self, event=None):
        annotate_logger.debug("========== entering method")
        self.current_type_hierarchy_level -= 1
        if self.current_type_hierarchy_level == -1:
            self.current_type_hierarchy_level = len(self.type_hierarchy)-1
        self.update_level()
    
    def update_level(self):
        annotate_logger.debug("========== entering method")
        for letter in LETTERS:
            self.text.unbind(letter)
            self.tree.unbind(letter)
        for adder in self.adders[self.current_type_hierarchy_level].values():
            self.text.bind_all("<%s>" %adder.shortcut, adder.add)
            self.tree.bind("<%s>" %adder.shortcut, adder.add)
            if adder.shortcut.islower():
                self.text.bind_all("<%s>" %adder.shortcut.upper(), adder.add_all)
                self.tree.bind("<%s>" %adder.shortcut.upper(), adder.add_all)
        for i in range(len(self.type_hierarchy)):
            if i != self.current_type_hierarchy_level:
                self.type_combos[i].configure(state=tk.DISABLED)
            else:
                self.type_combos[i].configure(state="readonly")
    
    def add_document(self, document):
        found = self.doc is not None and any([document.name == doc.name for doc in self.corpus_documents])
        if found:
            id = self.corpus_id2doc[self.doc.name]
            self.corpus_tree.selection_set(id)
            self.corpus_tree.focus(id)
            self.corpus_tree.see(id)
        else:
            id = self.corpus_tree.insert("", len(self.corpus_tree.get_children()), text=document.name)
            self.corpus_id2doc[id] = document
            self.corpus_id2doc[document.name] = id
            self.corpus_documents.append(document)
            self.corpus_tree.selection_set(id)
            self.corpus_tree.focus(id)
            self.corpus_tree.see(id)
        return not found
    
    def load_document(self, event=None):
        selection = self.corpus_tree.selection()[0]
        document = self.corpus_id2doc[selection]
        if self.doc is None or document.name != self.doc.name:
            if self.doc is not None and len(self.current_annots) > 0:
                update_annotations(self.doc, "NER", self.current_annots)
            
            self.doc = document
            
            previous_tree = self.tree_ids.get("NER", None)
            if previous_tree:
                self.tree.delete(previous_tree)
            previous_tree = self.tree_ids.get("history", None)
            if previous_tree:
                self.tree.delete(previous_tree)
            
            self.tree_ids["NER"] = self.tree.insert("", len(self.tree_ids)+1, text="NER")
            self.tree_ids["history"] = self.tree.insert("", len(self.tree_ids)+1, text="history")
            self.annot2treeitems["NER"] = {}
            self.annot2treeitems["history"] = {}
            self.treeitem2annot = {}
            self.position2annots = {}
            self.current_annotations = Annotation("CurrentAnnotations")
            self.current_annots = []
            self.current_selection = None
            self.wish_to_add = None
            self.lines_lengths = [0] + [len(line)+1 for line in self.doc.content.split(u"\n")]
            
            self.text.configure(state="normal")
            for tag_name in self.text.tag_names():
                self.text.tag_remove(tag_name, "1.0", "end")
            self.text.delete("1.0", "end")
            self.text.insert("end", self.doc.content)
            self.text.tag_remove("BOLD",  "1.0", 'end')
            self.text.configure(state="disabled")
            
            try:
                annots = self.doc.annotation("NER").get_reference_annotations()
                for nth_annot, annot in enumerate(annots):
                    self.add_tag(annot.value, annot.lb, annot.ub)
                    annot.levels = [annot.value]
                    item = self.tree.insert(self.tree_ids["NER"], len(self.annot2treeitems["NER"])+1, text=u'%s "%s" [%i:%i]' %(annot.value, self.doc.content[annot.lb : annot.ub], annot.lb, annot.ub))
                    self.annot2treeitems["NER"][str(annot)] = item
                    annot.ids["NER"] = item
                    self.treeitem2annot[item] = annot
                    self.current_annots.append(annot)
                    if Adder.type2label(annot.value, 0) is None:
                        separator = find_potential_separator(annot.value)
                        if separator is not None:
                            splitted = annot.value.split(separator)
                            for depth, type_to_add in enumerate(splitted,0):
                                self.doc.annotation("NER")[nth_annot].setLevel(depth, type_to_add)
                        else:
                            self.doc.annotation("NER")[nth_annot].setLevel(0, annot.value)
            except KeyError:
                pass
    
    def load_tagset(self, tagset):
        self.type_hierarchy = [set()]
        self.available_chars = [set(u"abcdefghijklmnopqrstuvwxyz")]
        self.adders = [{}]
        Adder.clear()
        
        for combo in self.type_combos:
            combo.destroy()
        self.type_combos = []
        for add_type_lbl in self.add_type_lbls:
            add_type_lbl.destroy()
        self.add_type_lbls = [ttk.Label(self.toolbar, text="add type:")]
        self.add_type_lbls[0].pack(side="left")
        
        self.type_combos.append(ttk.Combobox(self.toolbar))
        self.type_combos[0]["values"] = [self.SELECT_TYPE]
        self.type_combos[0].bind("<<ComboboxSelected>>", self.add_annotation)
        self.type_combos[0].pack(side="left")
        
        for type_full in tagset:
            splitted = type_full.split(".")
            for depth, type_to_add in enumerate(splitted,0):
                if len(self.type_hierarchy)-1 < depth:
                    self.type_hierarchy.append(set())
                    self.available_chars.append(set(u"abcdefghijklmnopqrstuvwxyz"))
                    self.adders.append({})
                    ## label
                    self.add_type_lbls.append(ttk.Label(self.toolbar, text="add %stype:" %("sub"*(depth))))
                    self.add_type_lbls[depth].pack(side="left")
                    # combobox
                    self.type_combos.append(ttk.Combobox(self.toolbar))
                    self.type_combos[depth]["values"] = [self.SELECT_TYPE]
                    self.type_combos[depth].bind("<<ComboboxSelected>>", self.add_annotation)
                    self.type_combos[depth].pack(side="left")
                self.type_hierarchy[depth].add(type_to_add)
                if type_to_add not in self.adders[depth]:
                    self.adders[depth][type_to_add] = Adder(self, type_to_add, self.available_chars, level=depth)
                    if len(self.type_combos) > 0:
                        self.type_combos[depth]["values"] = [self.SELECT_TYPE] + [self.adders[depth][key].label for key in sorted(self.adders[depth].keys())]
        self.update_level()
    
    def load_tagset_gui(self, event=None):
        filename = tkFileDialog.askopenfilename(filetypes=[("text files", ".txt"), ("All files", ".*")])
        
        if filename == "": return
        
        tagset = []
        with codecs.open(filename, "rU", "utf-8") as I:
            for line in I:
                tagset.append(line.strip())
        tagset = [tag.split(u"#",1)[0] for tag in tagset]
        tagset = [tag for tag in tagset if tag != u""]
        
        self.load_tagset(tagset)

_subparsers = sem.argument_subparsers

parser = _subparsers.add_parser(os.path.splitext(os.path.basename(__file__))[0], description="An annotation tool for SEM.")

parser.add_argument("-l", "--log", dest="log_level", choices=("DEBUG","INFO","WARNING","ERROR","CRITICAL"), default="WARNING",
                    help="Increase log level (default: %(default)s)")


def main(args):
    annotate_logger.setLevel(args.log_level or "WARNING")
    root = tk.Tk()
    AnnotationTool(root).pack(expand=1, fill="both")
    root.mainloop()
