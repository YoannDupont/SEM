"""
file: augment_wapiti_model.py

author: Yoann Dupont

MIT License

Copyright (c) 2021 Yoann Dupont

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

import argparse
import json


__DEFAULT_PREFIXES = ("u:WordId_", "u:word ")


# This class allows to have a minimal CRF object that allows to easily augment the features.
# Unlike sem.CRF.Model, which was more made to load a Wapiti model that is not meant to be modified.
# Maybe later, this class will be replaced by sem.CRF.Model.
class CRF:
    def __init__(self):
        self.model_type = -1
        self.maxcol = -1
        self.autouni = 0
        self.patterns = []
        self.labels = []
        self.features = []
        self.theta = []
        self.offset = {}

    def weightsperfeat(self, feat):
        nlabels = len(self.labels)
        d = {b"u": nlabels, b"b": nlabels**2, b"*": nlabels+nlabels**2}
        return d[bytes([feat[0]])]

    def write(self, stream):
        nact = sum(f != 0.0 for f in self.theta)
        stream.write(b"#mdl#%i#%i\n" %(self.model_type, nact))

        stream.write(b"#rdr#%i/%i/%i\n" %(len(self.patterns), self.maxcol, self.autouni))
        for pattern in self.patterns:
            stream.write(b"%i:%s,\n" %(len(pattern), pattern))

        stream.write(b"#qrk#%i\n" %(len(self.labels)))
        for label in self.labels:
            stream.write(b"%i:%s,\n" %(len(label), label))

        stream.write(b"#qrk#%i\n" %(len(self.features)))
        for feature in self.features:
            stream.write(b"%i:%s,\n" %(len(feature), feature))

        for i, w in enumerate(self.theta):
            if w == 0.0:
                continue
            stream.write(b"%i=%s\n" %(i, bytes(float.hex(w), "utf-8")))

    @staticmethod
    def read(path):
        model = CRF()
        with open(path, "rb") as input_stream:
            header = next(input_stream).strip().split(b"#")
            model.model_type = int(header[2])
            nact = int(header[-1])

            header = next(input_stream).strip().split(b"#")
            npat, maxcol, autouni = header[-1].split(b"/")
            npat = int(npat)
            model.maxcol = int(maxcol)
            model.autouni = int(autouni)
            for i in range(npat):
                line = next(input_stream).strip().split(b":", 1)[1][:-1]
                model.patterns.append(line)

            header = next(input_stream).strip().split(b"#")
            nlabels = int(header[-1])
            for i in range(nlabels):
                line = next(input_stream).strip().split(b":", 1)[1][:-1]
                model.labels.append(line)

            header = next(input_stream).strip().split(b"#")
            nfeats = int(header[-1])
            numweights = 0
            weightsperfeat = {b"u": nlabels, b"b": nlabels**2, b"*": nlabels+nlabels**2}
            for i in range(nfeats):
                line = next(input_stream).strip().split(b":", 1)[1][:-1]
                model.features.append(line)
                model.offset[line] = numweights
                numweights += weightsperfeat[bytes([line[0]])]

            model.theta = [0.0 for _ in range(numweights)]
            for i in range(nact):
                line = next(input_stream).strip()
                idx, val = line.split(b"=", 1)
                idx = int(idx)
                model.theta[idx] = float.fromhex(val.decode("utf8"))
        return model


def main(argv=None):
    augment_wapiti_model(**vars(parser.parse_args(argv)))


def augment_wapiti_model(
    inputfile, configfile, outputfile, encoding="utf-8", substitution_prefixes=None
):
    mdl = CRF.read(inputfile)
    mdlfeats = set(mdl.features)
    prefixes = list(substitution_prefixes or __DEFAULT_PREFIXES)
    prefixes = [bytes(p, encoding) for p in prefixes]

    with open(configfile, encoding=encoding) as input_stream:
        config = json.load(input_stream)
    config["substitutions"] = [
        [bytes(p, encoding), bytes(r, encoding)] for p, r in config["substitutions"]
    ]
    config["additions"] = [
        [bytes(f, encoding), bytes(l, encoding), w] for f, l, w in config["additions"]
    ]

    add_feats = []
    for pattern, repl in config["substitutions"]:
        for feat in mdl.features:
            if not any(feat.startswith(prefix) for prefix in prefixes):
                continue
            if pattern not in feat:
                continue
            off1 = mdl.offset[feat]
            addition = feat.replace(pattern, repl)
            if addition in mdlfeats:
                continue
            add_feats.append(addition)
            mdl.offset[addition] = len(mdl.theta)
            mdl.theta.extend(mdl.theta[off1: off1+mdl.weightsperfeat(feat)])
    for feat, label, weight in config["additions"]:
        if feat in mdlfeats:
            continue
        weights = [0.0 for _ in range(mdl.weightsperfeat(feat))]
        weights[mdl.labels.index(label)] = weight
        add_feats.append(feat)
        mdl.offset[feat] = len(mdl.theta)
        mdl.theta.extend(weights)
    mdl.features.extend(add_feats)

    with open(outputfile, "wb") as output_stream:
        mdl.write(output_stream)


parser = argparse.ArgumentParser(
    'Add more features in a model by substitution or adding entirely new features.'
    ' This is specially useful when one wants to add features for words that were not seen or for'
    ' handling special characters.\n'
    '\n'
    'The configuration file is a json file with two keys: substitutions and additions.'
    ' Here is an example of such a json:\n'
    '\n'
    '{\n'
    '    "substitutions": [\n'
    '        ["\'", "ʼ"],\n'
    '        ["\'", "’"]\n'
    '    ],\n'
    '    "additions": [\n'
    '        ["u:WordId_+0=«", "PONCT", 32.0],\n'
    '        ["u:WordId_+0=»", "PONCT", 32.0],\n'
    '        ["u:WordId_+0=–", "PONCT", 32.0],\n'
    '        ["u:WordId_+0=—", "PONCT", 32.0],\n'
    '        ["u:WordId_+0=•", "PONCT", 32.0]\n'
    '    ]\n'
    '}\n'
)
parser.add_argument("inputfile", help="The input wapiti model to augment.")
parser.add_argument("configfile", help="The json file where substitutions and additions are given.")
parser.add_argument("outputfile", help="The output (augmented) wapiti model.")
parser.add_argument(
    "-e", "--encoding", default="utf-8", help="The encoding of configfile. (default: %(default)s)"
)
parser.add_argument(
    "--substitution-prefixes",
    nargs="*",
    default=__DEFAULT_PREFIXES,
    help="The allowed feature prefixes for substitutions. (default: %(default)s)"
)
