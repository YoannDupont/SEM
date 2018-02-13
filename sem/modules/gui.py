#-*- coding: utf-8 -*-

"""
file: gui.py

Description: performs a sequence of operations in a pipeline.

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

import Tkconstants, tkMessageBox

import time

import os.path

import sem
from sem.modules.tagger import load_master, main as tagger
from sem.storage.holder import Holder
from sem.gui.components import SemTkMasterSelector, SemTkLangSelector, SemTkFileSelector, SemTkExportSelector, SEMTkWapitiTrain

import platform
SYSTEM = platform.system().lower()
ON_WINDOWS = (SYSTEM == "windows")

class SemTkMainWindow(ttk.Frame):
    def __init__(self, root, resource_dir):
        """
        create the main window.
        """
        
        ttk.Frame.__init__(self, root)
        
        self.resource_dir = resource_dir
        self.loaded_master = {}
        
        self.current_files = None
        self.current_output = os.path.join(sem.SEM_DATA_DIR, "outputs")
        if not os.path.exists(self.current_output):
            os.makedirs(self.current_output)
        
        self.master_zone = ttk.Frame(root)
        self.master_zone.grid(row=0, column=0, rowspan=2, columnspan=1, sticky="ns")
        self.master_zone.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.file_select_zone = ttk.Frame(root)
        self.file_select_zone.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.launch_zone = ttk.Frame(root)
        self.launch_zone.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.lang_selector = SemTkLangSelector(self.master_zone, self.resource_dir)
        self.master = SemTkMasterSelector(self.master_zone, self.resource_dir)
        self.lang_selector.master_selector = self.master
        self.lang_selector.pack()
        self.master.pack()
        
        self.file_selector = SemTkFileSelector(self.file_select_zone, self, button_opt={'fill': Tkconstants.BOTH, 'padx': 5, 'pady': 5})
        self.file_selector.pack()
        root.bind("<Control-o>", self.file_selector.filenames)
        
        self.export_format_selector = SemTkExportSelector(self.launch_zone)
        self.export_format_selector.pack()
        
        self.launch_button = ttk.Button(self.launch_zone, text=u"launch SEM", command=self.launch_tagger)
        self.launch_button.pack(expand=True)
        self.haw = tk.PhotoImage(file=os.path.join(self.resource_dir, "images", "haw_24_24.gif"))
        self.launch_button.config(image=self.haw, compound=tk.LEFT)
        
        self.train_button = ttk.Button(self.launch_zone, text=u"train SEM", command=self.train_tagger)
        self.train_button.pack(expand=True)
        self.university = tk.PhotoImage(file=os.path.join(self.resource_dir, "images", "fa_university_24_24.gif"))
        self.train_button.config(image=self.university, compound=tk.LEFT)
    
    def launch_tagger(self):
        current_files = self.file_selector.files()
        if not current_files:
            tkMessageBox.showwarning("launching SEM", "No files specified.")
            return
        
        workflow = self.master.workflow()
        if not workflow:
            tkMessageBox.showwarning("launching SEM", "No workflow selected.")
            return
        masterfile = os.path.join(self.resource_dir, "master", self.lang_selector.lang(), workflow)
        
        output_dir = os.path.join(self.current_output, time.strftime("%Y%m%d%H%M%S"))
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        try:
            print "="*64
            export_format = self.export_format_selector.export_format()
            if masterfile in self.loaded_master:
                pipeline, workflow_options, exporter, couples = self.loaded_master[masterfile]
            else:
                self.loaded_master.clear()
                pipeline, workflow_options, exporter, couples = load_master(masterfile, force_format=export_format)
                self.loaded_master[masterfile] = [pipeline, workflow_options, exporter, couples]
            for current_file in current_files:
                args = Holder(**{"infile":current_file, "output_directory":output_dir, "pipeline":pipeline, "options":workflow_options, "exporter":exporter, "couples":couples})
                tagger(args)
        except Exception,e:
            tkMessageBox.showerror("launching SEM", "Error: " + e.message)
            raise
            return
        tkMessageBox.showinfo("launching SEM", "Everything went ok! files are located in: " + output_dir)
        return
    
    def train_tagger(self, event=None):
        current_files = self.file_selector.files()
        if not current_files:
            tkMessageBox.showwarning("launching SEM", "No files specified.")
            return
        
        workflow = self.master.workflow()
        if not workflow:
            tkMessageBox.showwarning("launching SEM", "No workflow selected.")
            return
        
        wt = SEMTkWapitiTrain(self.file_selector, self.master)


import sem

_subparsers = sem.argument_subparsers

parser = _subparsers.add_parser(os.path.splitext(os.path.basename(__file__))[0], description="Launched GUI for SEM for tagging documents and training new models.")

parser.add_argument("resources", nargs="?", default=os.path.join(sem.SEM_RESOURCE_DIR),
                    help="The directory where resources are. If not provided, will use current installation's resources.")

def main(args):
    root = tk.Tk()
    root.title("SEM")
    root.minsize(width=380, height=200)
    
    SemTkMainWindow(root, args.resources).pack()
    
    root.mainloop()
