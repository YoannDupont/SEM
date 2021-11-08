# -*- coding: utf-8 -*-

import dill
import pathlib
import sys
import sem

try:
    path = sys.argv[1]
except IndexError:
    path = input("master? > ")
path = pathlib.Path(path)

try:
    output_file = sys.argv[2]
except IndexError:
    output_file = path.stem


p, _, _, _ = sem.load_workflow(path)

p.couples = {"pos": "POS", "chunking": "chunking", "ner": "NER"}
p.license = (
    "This SEM pipeline is provided for research, teaching and personal use only"
    ", it may not be used for any other reason."
)

sem.save(p, output_file)
