import codecs, cPickle

from obj.trie import Trie

NUL = u""

def compile_token(infile, encoding):
    tokens = set()
    for line in codecs.open(infile, "rU", encoding):
        line = line.strip()
        if line != "":
            tokens.add(line)
    return tokens

def compile_multiword(infile, encoding):
    trie = Trie()
    for line in codecs.open(infile, "rU", encoding):
        seq = line.strip().split()
        trie.add(seq)
    return trie