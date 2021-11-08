# -*- coding: utf-8 -*-

import pathlib
import sys
import sem
from sem.modules.export import SEMModule as ExporterModule
import sem.logger

try:
    path = sys.argv[1]
except IndexError:
    path = input("model? > ")

try:
    inputfile = sys.argv[2]
except IndexError:
    inputfile = None

sem.logger.setLevel("INFO")
p = sem.load(path)

if inputfile:
    with open(inputfile, encoding="utf-8") as input_stream:
        d = sem.storage.Document(name=inputfile, content=input_stream.read())
else:
    d = sem.storage.Document(name="text.txt", content="France : arrivée du président Jean Dupont.")

p.process_document(d)

# Reference_annotations are annotations which span on character offsets in document.
# By default, NER annotations span on token offsets in a document.
for annotation in d.annotation("NER").get_reference_annotations():
    print(annotation, d.content[annotation.lb : annotation.ub])

#
# exporting data to a given output format.
#

exporter = ExporterModule("brat")

with open(pathlib.Path(d.name).stem + ".ann", "w") as output_stream:
    exporter.process_document(d, outfile=output_stream)
