#-*- coding: utf-8 -*-

"""
file: gui.py

Description: performs a sequence of operations in a pipeline.

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

try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk

try:
    import ttk
except ImportError:
    ttk = tk.ttk

import Tkconstants, tkFileDialog, tkMessageBox

import time

import os.path

from software import SEM_HOME
from src.tagger import tagger
from obj.master_parser import Master

import platform
SYSTEM = platform.system().lower()
ON_WINDOWS = (SYSTEM == "windows")

class TkSemMainWindow(tk.Frame):
    def __init__(self, root):
        """
        create the main window.
        
        Some commented code that should not be of any use, but just in case:
            1. did not work on Linux, did not seem to have an effect on Windows.
            2. using an icon found on the internet (should use something else)
        """
        tk.Frame.__init__(self, root)
        
        self.current_files = None
        self.current_output = os.path.join(SEM_HOME, "outputs")
        if not os.path.exists(self.current_output):
            os.makedirs(self.current_output)
        
        self.master_zone = tk.Frame(root)
        self.master_zone.grid(row=0, column=0, rowspan=2, columnspan=1, sticky="ns")
        self.master_zone.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.file_select_zone = tk.Frame(root)
        #1. self.file_select_zone.grid(row=0, column=1, rowspan=3, columnspan=1, sticky="ew")
        self.file_select_zone.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.launch_zone = tk.Frame(root)
        #1. self.launch_zone.grid(row=0, column=2, rowspan=1, columnspan=1, sticky="ew")
        self.launch_zone.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.select_lang_label = tk.Label(self.master_zone, text=u"select language:")
        self.select_lang_label.pack()
        self.lang_selector = SemTkLangSelector(self.master_zone)
        self.lang_selector.pack()
        self.select_workflow_label = tk.Label(self.master_zone, text=u"select workflow:")
        self.select_workflow_label.pack()
        self.master = SemTkMasterSelector(self.master_zone)
        self.master.pack()
        self.lang_selector.set_workflow(self.master)
        
        # options for buttons
        button_opt = {'fill': Tkconstants.BOTH, 'padx': 5, 'pady': 5}
        
        # define buttons
        self.file_selector = tk.Button(self.file_select_zone, text=u"select file(s)", command=self.filename)
        self.file_selector.pack(**button_opt)
        self.label = tk.Label(self.file_select_zone, text=u"selected file(s):")
        self.fa_search = tk.PhotoImage(file=os.path.join(SEM_HOME, "images", "fa_search_24_24.gif"))
        self.file_selector.config(image=self.fa_search, compound=tk.LEFT)
        self.label.pack()
        
        scrollbar = tk.Scrollbar(self.file_select_zone)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.selected_files = tk.Listbox(self.file_select_zone, yscrollcommand=scrollbar.set)
        self.selected_files.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.selected_files.yview)
        
        self.label = tk.Label(self.launch_zone, text=u"selected output format:")
        self.label.pack()
        
        export_formats = ["default", "conll", "html", "jason", "sem", "tei", "tei_np", "text"]
        export_format = tk.StringVar()
        self.export_combobox = ttk.Combobox(self.launch_zone)#, export_format, *export_formats)
        self.export_combobox["values"] = export_formats
        self.export_combobox.current(0)
        self.export_combobox.pack()
        
        self.launch_button = tk.Button(self.launch_zone, text=u"launch SEM", command=self.launch_tagger)
        self.launch_button.pack(expand=True)
        self.haw = tk.PhotoImage(file=os.path.join(SEM_HOME, "images", "haw_24_24.gif"))
        self.launch_button.config(image=self.haw, compound=tk.LEFT)
        
        # define options for opening or saving a file
        self.file_opt = options = {}
        options['defaultextension'] = '.txt'
        options['filetypes'] = [('all files', '.*'), ('text files', '.txt')]
        options['initialdir'] = SEM_HOME
        options['parent'] = root
        options['title'] = 'This is a title'

    
    def filename(self):
        self.current_files = tkFileDialog.askopenfilenames(**self.file_opt)
        self.selected_files.delete(0, tk.END)
        if self.current_files:
            for current_file in self.current_files:
                self.selected_files.insert(tk.END, os.path.basename(current_file))
            self.file_opt['initialdir'] = os.path.dirname(self.current_files[0])
    
    def launch_tagger(self):
        if not self.current_files:
            tkMessageBox.showwarning("launching SEM", "No files specified.")
            return
        
        workflow = self.master.worklow()
        if not workflow:
            tkMessageBox.showwarning("launching SEM", "No workflow selected.")
            return
        masterfile = os.path.join(SEM_HOME, "resources", "master", self.lang_selector.lang(), workflow)
        
        output_dir = os.path.join(self.current_output, time.strftime("%Y%m%d%H%M%S"))
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        try:
            export_format = self.export_combobox.get()
            for current_file in self.current_files:
                tagger(masterfile, current_file, directory=output_dir, force_format=export_format)
        except Exception,e:
            tkMessageBox.showerror("launching SEM", "Error: " + e.message)
            raise
            return
        tkMessageBox.showinfo("launching SEM", "Everything went ok! files are located in: " + output_dir)
        return

class SemTkMasterSelector(tk.Frame):
    def __init__(self, root, lang="fr"):
        tk.Frame.__init__(self, root)
        
        self._lang = lang
        items = os.listdir(os.path.join(SEM_HOME, "resources", "master", self._lang))
        max_length = max([len(item) for item in items])
        self.masters = tk.Listbox(root, width=max_length+1, height=len(items))
        self.masters.pack()

        for item in items:
            self.masters.insert(tk.END, item)
    
    def worklow(self):
        wf = self.masters.get(tk.ACTIVE)
        return wf or None
    
    def set_lang(self, language):
        self._lang = language
        items = os.listdir(os.path.join(SEM_HOME, "resources", "master", self._lang))
        max_length = max([len(item) for item in items] + [0])
        self.masters["height"] = len(items)
        
        self.masters.delete(0, tk.END)
        for item in items:
            self.masters.insert(tk.END, item)
        

class SemTkLangSelector(tk.Frame):
    def __init__(self, root):
        tk.Frame.__init__(self, root)
        
        self.workflow = None
        items = os.listdir(os.path.join(SEM_HOME, "resources", "master"))
        self.langs = tk.Listbox(root, height=len(items), selectmode=tk.SINGLE)
        self.langs.pack()

        for i, item in enumerate(items):
            self.langs.insert(tk.END, item)
            if item == "fr":
                self.langs.activate(i)
                self.langs.selection_set(i)
        
        self.langs.bind('<<ListboxSelect>>', self.select_lang)
    
    def lang(self):
        return self.langs.get(tk.ACTIVE)
    
    def set_workflow(self, workflow):
        self.workflow = workflow
    
    def select_lang(self, event):
        selected = self.langs.curselection()[0]
        self.langs.selection_set(selected)
        self.langs.activate(selected)
        self.workflow.set_lang(self.langs.get(tk.ACTIVE))


if __name__ == '__main__':
    root = tk.Tk()
    root.title("SEM")
    root.minsize(width=380, height=200)
    #2. root.wm_iconbitmap(os.path.join(SEM_HOME, 'images', 'test-icon.ico'))
    
    TkSemMainWindow(root).pack()
    
    root.mainloop()