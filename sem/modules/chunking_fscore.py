import sys, codecs

from sem.IO.columnIO import Reader

from sem.features import MultiwordDictionaryFeature, NUL

def compile_chunks(sentence, column=-1):
    entity_chunks = set()
    label         = u""
    start         = -1
    for index, token in enumerate(sentence):
        ne = token[column]
        
        if ne == "O":
            if label:
                entity_chunks.add(tuple([label, start, index]))
                label = u""
                start = -1
        elif ne[0] == "B":
            if label:
                entity_chunks.add(tuple([label, start, index]))
            start = index
            label = ne[2:]
        elif ne[0] == "I":
            None
        else:
            raise ValueError(ne)
    if label:
        entity_chunks.add(tuple([label, start, index]))
        label = u""
        start = -1
    
    return entity_chunks


def float2spreadsheet(f):
    """
    For spreadsheets, dots should be replaced by commas.
    """
    return (u"%.2f" %f).replace(u".",u",")


def main(args):
    infile = args.infile
    reference_column = args.reference_column
    tagging_column = args.tagging_column
    ienc = args.ienc or args.enc
    oenc = args.oenc or args.enc
    verbose = args.verbose
    
    counts = {}
    prf = {}
    for p in Reader(infile, ienc):
        reference = compile_chunks(p, column=reference_column)
        tagging = compile_chunks(p, column=tagging_column)
        ok = reference & tagging
        silence = reference - ok
        noise = tagging - ok
        for e in ok:
            label = e[0]
            if label not in counts:
                counts[label] = {"ok":0.0, "gold":0.0, "guess":0.0}
            counts[label]["ok"] += 1.0
            counts[label]["gold"] += 1.0
            counts[label]["guess"] += 1.0
        for e in silence:
            label = e[0]
            if label not in counts:
                counts[label] = {"ok":0.0, "gold":0.0, "guess":0.0}
            counts[label]["gold"] += 1.0
        for e in noise:
            label = e[0]
            if label not in counts:
                counts[label] = {"ok":0.0, "gold":0.0, "guess":0.0}
            counts[label]["guess"] += 1.0
    counts[""] = {"ok":0.0, "gold":0.0, "guess":0.0}
    for label in counts:
        if label == "": continue
        counts[""]["ok"] += counts[label]["ok"]
        counts[""]["gold"] += counts[label]["gold"]
        counts[""]["guess"] += counts[label]["guess"]
    
    for label in counts:
        lbl_c = counts[label]
        ok = lbl_c["ok"]
        gold = lbl_c["gold"]
        guess = lbl_c["guess"]
        
        prf[label] = {"p":0.0, "r":0.0, "f":0.0}
        if guess != 0.0:
            prf[label]["p"] = 100.0 * ok / guess
        if gold != 0.0:
            prf[label]["r"] = 100.0 * ok / gold
        if prf[label]["p"] + prf[label]["r"] != 0.0:
            prf[label]["f"] = 2.0 * ((prf[label]["p"] * prf[label]["r"]) / (prf[label]["p"] + prf[label]["r"]))
    
    print "entity\tprecision\trecall\tf-measure"
    entities = set(prf.keys())
    entities.discard("")
    entities = sorted(entities)
    for entity in entities:
        e_prf = prf[entity]
        print "%s\t%s\t%s\t%s" %(entity, float2spreadsheet(e_prf["p"]), float2spreadsheet(e_prf["r"]), float2spreadsheet(e_prf["f"]))
    ma_p = sum([prf[entity]["p"] for entity in entities]) / (len(entities))
    ma_r = sum([prf[entity]["r"] for entity in entities]) / (len(entities))
    ma_f = 2.0 * (ma_p * ma_r) / (ma_p + ma_r)
    print
    print "%s\t%s\t%s\t%s" %("micro-average", float2spreadsheet(prf[""]["p"]), float2spreadsheet(prf[""]["r"]), float2spreadsheet(prf[""]["f"]))
    print "%s\t%s\t%s\t%s" %("macro-average", float2spreadsheet(ma_p), float2spreadsheet(ma_r), float2spreadsheet(ma_f))


import os.path
import sem

_subparsers = sem.argument_subparsers

parser = _subparsers.add_parser(os.path.splitext(os.path.basename(__file__))[0], description="Get F1-score for BIO chunks.")

parser.add_argument("infile",
                    help="The input file (CoNLL format)")
parser.add_argument("-r", "--reference-column", dest="reference_column", type=int, default=-2,
                    help="Column for reference output (default: %(default)s)")
parser.add_argument("-t", "--tagging-column", dest="tagging_column", type=int, default=-1,
                    help="Column for CRF output (default: %(default)s)")
parser.add_argument("--input-encoding", dest="ienc",
                    help="Encoding of the input (default: utf-8)")
parser.add_argument("--output-encoding", dest="oenc",
                    help="Encoding of the input (default: utf-8)")
parser.add_argument("-e", "--encoding", dest="enc", default="utf-8",
                    help="Encoding of both the input and the output (default: utf-8)")
parser.add_argument("-v", "--verbose", dest="verbose", action="store_true",
                    help="Writes feedback during process (default: no output)")
