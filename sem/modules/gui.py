# -*- coding: utf-8 -*-

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

import tkinter
from tkinter import ttk
import tkinter.messagebox

import time
import os
import argparse

import sem
import sem.importers
from sem.modules.tagger import tagger
from sem.gui_components import (
    SemTkResourceSelector,
    SemTkLangSelector,
    SemTkFileSelector,
    SemTkExportSelector,
    SEMTkTrainInterface,
)
import sem.logger
import sem.pipelines


class SemTkMainWindow(ttk.Frame):
    def __init__(self, root, resource_dir):
        """
        create the main window.
        """

        ttk.Frame.__init__(self, root)

        self.resource_dir = resource_dir

        self.current_files = None
        self.current_output = sem.SEM_DATA_DIR / "outputs"
        if not self.current_output.exists():
            os.makedirs(self.current_output)

        self.workflow_zone = ttk.Frame(root)
        self.workflow_zone.grid(row=0, column=0, rowspan=2, columnspan=1, sticky="ns")
        self.workflow_zone.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)

        self.file_select_zone = ttk.Frame(root)
        self.file_select_zone.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)

        self.launch_zone = ttk.Frame(root)
        self.launch_zone.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)

        self.lang_selector = SemTkLangSelector(self.workflow_zone, self.resource_dir / "workflow")
        self.workflow = SemTkResourceSelector(self.workflow_zone, self.resource_dir / "workflow")
        self.lang_selector.register(self.workflow)
        self.lang_selector.pack()
        self.workflow.pack()

        self.file_selector = SemTkFileSelector(
            self.file_select_zone, self, button_opt={"fill": "both", "padx": 5, "pady": 5}
        )
        self.file_selector.pack()
        root.bind("<Control-o>", self.file_selector.filenames)

        self.export_format_selector = SemTkExportSelector(self.launch_zone)
        self.export_format_selector.pack()

        self.launch_button = ttk.Button(
            self.launch_zone, text="launch SEM", command=self.launch_tagger
        )
        self.launch_button.pack(expand=True)
        self.haw = tkinter.PhotoImage(file=str(self.resource_dir / "images" / "haw_24_24.gif"))
        self.launch_button.config(image=self.haw, compound=tkinter.LEFT)

        self.train_button = ttk.Button(
            self.launch_zone, text="train SEM", command=self.train_tagger
        )
        self.train_button.pack(expand=True)
        self.university = tkinter.PhotoImage(
            file=str(self.resource_dir / "images" / "fa_university_24_24.gif")
        )
        self.train_button.config(image=self.university, compound=tkinter.LEFT)

    def launch_tagger(self):
        current_files = self.file_selector.files()
        if not current_files:
            tkinter.messagebox.showwarning("launching SEM", "No files specified.")
            return

        workflow = self.workflow.resource()
        if not workflow:
            tkinter.messagebox.showwarning("launching SEM", "No workflow selected.")
            return
        workflowfile = self.resource_dir / "workflow" / self.lang_selector.lang() / workflow

        output_dir = self.current_output / time.strftime("%Y%m%d%H%M%S")
        if not output_dir.exists():
            os.makedirs(output_dir)

        try:
            export_format = self.export_format_selector.export_format()
            args = {
                "workflow": workflowfile,
                "infiles": [],
                "output_directory": output_dir,
                "force_format": export_format,
                "n_procs": 0,
            }
            for current_file in current_files:
                corpus = None
                try:
                    corpus = sem.importers.sem_document_from_xml(current_file)
                except Exception:
                    pass
                if corpus is not None:
                    args["infiles"].extend(corpus.documents)
                else:
                    args["infiles"].append(current_file)
            tagger(**args)
        except Exception as e:
            # handling ExpatError from etree
            tkinter.messagebox.showerror("launching SEM", "Error: {}".format(e))
            raise
        sem.logger.info("files are located in: {}".format(output_dir))
        tkinter.messagebox.showinfo(
            "launching SEM", "Everything went ok! files are located in: {}".format(output_dir)
        )
        return

    def train_tagger(self, event=None):
        current_files = self.file_selector.files()
        if not current_files:
            tkinter.messagebox.showwarning("launching SEM", "No files specified.")
            return

        SEMTkTrainInterface(self.file_selector, None, None)


def main(argv=None):
    gui(**vars(parser.parse_args(argv)))


def gui(resources=sem.SEM_RESOURCE_DIR, log_level="INFO"):
    root = tkinter.Tk()
    root.title("SEM")
    root.minsize(width=380, height=200)
    sem.logger.setLevel(log_level)

    SemTkMainWindow(root, resources).pack()

    root.mainloop()


parser = argparse.ArgumentParser(
    "Launch GUI for SEM for tagging documents and training new models."
)

parser.add_argument(
    "resources",
    nargs="?",
    default=sem.SEM_RESOURCE_DIR,
    help="The directory where resources are. If not provided,"
    " will use current installation's resources.",
)
parser.add_argument(
    "-l",
    "--log",
    dest="log_level",
    choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
    default="INFO",
    help="Increase log level (default: %(default)s)",
)
