import sys, codecs

from obj.IO.columnIO import Reader

from obj.enrich.features.dictionaryfeatures import MultiwordDictionaryFeature, NUL

def compile_chunks(sentence, column=-1):
    entity_chunks = []
    label         = u""
    start         = -1
    for index, token in enumerate(sentence):
        ne = token[column]
        
        if ne == "O":
            if label:
                entity_chunks.append([label, start, index])
                label = u""
                start = -1
        elif ne[0] == "B":
            if label:
                entity_chunks.append([label, start, index])
            start = index
            label = ne[2:]
        elif ne[0] == "I":
            None
        else:
            raise ValueError(ne)
    if label:
        entity_chunks.append([label, start, index])
        label = u""
        start = -1
    
    return entity_chunks

class LabelConsistencyFeature(MultiwordDictionaryFeature):
    def __init__(self, form2entity, ne_entry, *args, **kwargs):
        super(LabelConsistencyFeature, self).__init__(*args, **kwargs)
        self._form2entity = form2entity
        self._ne_entry = ne_entry
    
    def __call__(self, list2dict, *args, **kwargs):
        l           = [t[self._ne_entry][:] for t in list2dict]
        form2entity = self._form2entity
        tmp         = self._value._data
        length      = len(list2dict)
        fst         = 0
        lst         = -1 # last match found
        cur         = 0
        entry       = self._entry
        ckey        = None  # Current KEY
        while fst < length - 1:
            cont = True
            while cont and (cur < length):
                ckey  = list2dict[cur][entry]
                if l[cur] == "O":
                    if NUL in tmp: lst = cur
                    tmp   = tmp.get(ckey, {})
                    cont  = len(tmp) != 0
                    cur  += int(cont)
                else:
                    cont = False
            
            if NUL in tmp: lst = cur
            
            if lst != -1:
                form = u" ".join([list2dict[i][entry] for i in range(fst,lst)])
                appendice = u"-" + form2entity[form]
                l[fst] = u'B' + appendice
                for i in xrange(fst+1, lst):
                    l[i] = u'I' + appendice
                fst = lst
                cur = fst
            else:
                fst += 1
                cur  = fst
            
            tmp = self._value._data
            lst = -1
        
        if NUL in self._value._data.get(list2dict[-1][entry], []) and l[-1] == "O":
            l[-1] = u'B-' + form2entity[list2dict[-1][entry]]
        
        return l

class OverridingLabelConsistencyFeature(LabelConsistencyFeature):
    """
    This is the second label consistency strategy.
    It can change CRF entities if it finds a wider one.
    Gives lower results on FTB
    """
    def __call__(self, list2dict, *args, **kwargs):
        l           = [u"O" for _ in range(len(list2dict))]
        form2entity = self._form2entity
        tmp         = self._value._data
        length      = len(list2dict)
        fst         = 0
        lst         = -1 # last match found
        cur         = 0
        entry       = self._entry
        ckey        = None  # Current KEY
        entities    = []
        while fst < length - 1:
            cont = True
            while cont and (cur < length):
                ckey  = list2dict[cur][entry]
                if l[cur] == "O":
                    if NUL in tmp: lst = cur
                    tmp   = tmp.get(ckey, {})
                    cont  = len(tmp) != 0
                    cur  += int(cont)
                else:
                    cont = False
            
            if NUL in tmp: lst = cur
            
            if lst != -1:
                form = u" ".join([list2dict[i][entry] for i in range(fst, lst)])
                entities.append([form2entity[form], fst, lst])
                fst = lst
                cur = fst
            else:
                fst += 1
                cur  = fst
            
            tmp = self._value._data
            lst = -1
        
        if NUL in self._value._data.get(list2dict[-1][entry], []):
            entities.append([form2entity[list2dict[-1][entry]], len(list2dict)-1, len(list2dict)])
        
        gold = compile_chunks(list2dict, self._ne_entry)
        
        for i in reversed(range(len(entities))):
            e = entities[i]
            for r in gold:
                if (r[1] == e[1] and r[2] == e[2]):
                    del entities[i]
                    continue
        
        for i in reversed(range(len(gold))):
            r = gold[i]
            for e in entities:
                if (r[1] >= e[1] and r[2] <= e[2]):
                    del gold[i]
                    continue
        
        for r in gold + entities:
            appendice = u"-" + r[0]
            l[r[1]] = u"B" + appendice
            for i in range(r[1]+1,r[2]):
                l[i] = u"I" + appendice
        
        return l


def process_document(document, field, token_column="word",
                     label_consistency="non-overriding",
                     ienc="utf-8", oenc="utf-8",
                     verbose=False):
    
    process_corpus(document.corpus.sentences, field, token_column=token_column,
                   label_consistency=label_consistency,
                   ienc=ienc, oenc=oenc,
                   verbose=verbose)
    tags = [[token[field] for token in sentence] for sentence in document.corpus.sentences]
    document.add_annotation_from_tags(tags, field, field)


def process_corpus(corpus, column, token_column="word",
                   label_consistency="non-overriding",
                   ienc="utf-8", oenc="utf-8",
                   verbose=False):
    
    entities = {}
    counts   = {}
    for p in corpus:
        G = compile_chunks(p, column=column)
        for entity in G:
            id   = entity[0]
            form = u" ".join([p[index][token_column] for index in range(entity[1], entity[2])])
            if form not in counts:
                counts[form] = {}
            if id not in counts[form]:
                counts[form][id] = 0
            counts[form][id] += 1
    
    for form, count in counts.items():
        if len(count) == 1:
            entities[form] = count.keys()[0]
        else:
            best = sorted(count.keys(), key=lambda x: -count[x])[0]
            entities[form] = best
    
    if label_consistency == "non-overriding":
        feature = LabelConsistencyFeature(entities, ne_entry=column, entry=token_column, entries=entities.keys())
    else:
        feature = OverridingLabelConsistencyFeature(entities, ne_entry=column, entry=token_column, entries=entities.keys())
    
    for p in corpus:
        for i, value in enumerate(feature(p)):
            p[i][column] = value


def label_consistency(infile, outfile,
                label_consistency="non-overriding", token_column=0, column=-1,
                ienc="utf-8", oenc="utf-8",
                verbose=False):
    
    entities = {}
    counts   = {}
    for p in Reader(infile, ienc):
        G = compile_chunks(p, column=column)
        for entity in G:
            id   = entity[0]
            form = u" ".join([p[index][token_column] for index in range(entity[1], entity[2])])
            if form not in counts:
                counts[form] = {}
            if id not in counts[form]:
                counts[form][id] = 0
            counts[form][id] += 1
    
    for form, count in counts.items():
        if len(count) == 1:
            entities[form] = count.keys()[0]
        else:
            best = sorted(count.keys(), key=lambda x: -count[x])[0]
            entities[form] = best
    
    if label_consistency == "non-overriding":
        feature = LabelConsistencyFeature(entities, ne_entry=column, entry=token_column, entries=entities.keys())
    else:
        feature = OverridingLabelConsistencyFeature(entities, ne_entry=column, entry=token_column, entries=entities.keys())
    
    with codecs.open(outfile, "w", oenc) as O:
        for p in Reader(infile, ienc):
            for i, value in enumerate(feature(p)):
                p[i][column] = value
                O.write(u"\t".join(p[i]) + u"\n")
            O.write(u"\n")
    
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Get most ambiguous words according to category distribution")

    parser.add_argument("infile",
                        help="The input file (CoNLL format)")
    parser.add_argument("outfile",
                        help="The output file")
    parser.add_argument("-t", "--token-column", dest="token_column", type=int, default=0,
                        help="Form column")
    parser.add_argument("--label-consistency", dest="label_consistency", choices=("non-overriding","overriding"), default="non-overriding",
                        help="Non-overriding leaves CRF's annotation as they are, overriding label_consistency erases them if it finds a longer one.")
    parser.add_argument("--input-encoding", dest="ienc",
                        help="Encoding of the input (default: utf-8)")
    parser.add_argument("--output-encoding", dest="oenc",
                        help="Encoding of the input (default: utf-8)")
    parser.add_argument("-e", "--encoding", dest="enc", default="utf-8",
                        help="Encoding of both the input and the output (default: utf-8)")
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true",
                        help="Writes feedback during process (default: no output)")
    
    if __package__:
        args = parser.parse_args(sys.argv[2:])
    else:
        args = parser.parse_args()
    
    label_consistency(args.infile, args.outfile,
                label_consistency=args.label_consistency, token_column=args.token_column,
                ienc=args.ienc or args.enc, oenc=args.oenc or args.enc,
                verbose=args.verbose)
    sys.exit(0)
