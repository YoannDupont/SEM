#! /usr/bin/python
# -*- coding: utf-8 -*-

import codecs


_keys = set([u"IN_FILE", u"OUT_DIRECTORY", u"SEGMENTATION", u"LEFFF_FILE", u"POS_TAGS", u"CHUNK_TAGS", u"CODE", u"MODELS", u"CLEAN", u"INPUT_ENCODING", u"OUTPUT_ENCODING", u"QUIET", u"HAS_TAGGING"])

_list_args = _keys & set([u"POS_TAGS", u"CHUNK_TAGS"])

US = u"_"
pos_tags = u"POS_TAGS"
Hyphen = u"-"
B, I, O = u"BIO"
_chunks = set([B, I, O]) # the minimum chunk set, used to label a single type of data
chk_tags = u"CHUNK_TAGS"

C, R, W = u"CRW"
# C: Creating a new entry in the config dictionary with its unitary value
# R: Reading values for list arguments
# W: Waiting for a new key

SHARP = u"#"
# comment lines and sub-lines

YN_TO_BOOL = {u"YES":True, u"Y":True, u"TRUE":True,
              u"NO":False, u"N":False, u"FALSE":False}

def valueof(elt):
    if elt.upper() in YN_TO_BOOL.keys():
        return YN_TO_BOOL[elt.upper()]
    else:
        return elt


def indexof(l, elt):
    return (line.index(elt) if elt in l else len(l))


class Config(object):

    def __init__(self, filename):
        self._values = {}
        self._values[u"CHUNK_TAGS"] = _chunks

        self._readfile(filename)

    def __str__(self):
        return str(self._values)

    def __repr__(self):
        repres = u""
        for k in self._values.keys():
            repres += k + ":" + repr(self._values[k]) + "\n"
        return repres

    def _readfile(self, filename):
        f = codecs.open(filename, u"r", u"UTF-8")
        status = W
        value = u""
        s = set()
        
        for l in f:
            line = l.rstrip(u"\n")
            if line == u"":
                if s != set():
                    self._values[value] = list(s)
                    s.clear()
                    self._values[value].sort()
                status = W
            elif line[0] != SHARP:
                if status == W:
                    status = C
                    value = line[0 : indexof(line, SHARP)]
                    if not value in _keys:
                        raise KeyError(u"The key \"%s\" is not valid. Valid keys are %s" %(value, _keys))
                    if value == chk_tags:
                        s = _chunks.copy()
                    else:
                        self._values[value] = None

                elif status == C:
                    if value not in _list_args:
                        if self._values[value] == None:
                            self._values[value] = valueof(line[0 : indexof(line, SHARP)])
                        else:
                            raise ValueError("Unitary value assigned multiple times: %r assigned with %r and then %r" %(value, self._values[value], line))
                    else:
                        for token in line[0 : indexof(line, SHARP)].split():
                            if value == chk_tags:
                                s.add(B + Hyphen + token)
                                s.add(I + Hyphen + token)
#                            elif value == pos_tags:
#                                 s.add(token)
#                                s.add(US + token)
                            else:
                                s.add(token)

                elif status == R:
                    for token in line[0 : indexof(line, SHARP)].split():
                        if value == chk_tags:
                            s.add(B + Hyphen + token)
                            s.add(I + Hyphen + token)
#                        elif value == pos_tags:
#                            s.add(token)
#                            s.add(US + token)
                        else:
                            s.add(token)

    @property
    def chunk_tags(self):
        return self._values[u"CHUNK_TAGS"]

    @property
    def clean(self):
        return self._values[u"CLEAN"]

    @property
    def code(self):
        return self._values[u"CODE"]

    @property
    def in_file(self):
        return self._values[u"IN_FILE"]

    @property
    def input_encoding(self):
        return self._values[u"INPUT_ENCODING"]

    @property
    def lefff_file(self):
        return self._values[u"LEFFF_FILE"]

    @property
    def models(self):
        return self._values[u"MODELS"]

    @property
    def out_directory(self):
        return self._values[u"OUT_DIRECTORY"]

    @property
    def output_encoding(self):
        return self._values[u"OUTPUT_ENCODING"]

    @property
    def pos_tags(self):
        return self._values[u"POS_TAGS"]

    @property
    def quiet(self):
        return self._values[u"QUIET"]

    @property
    def segmentation(self):
        return self._values[u"SEGMENTATION"]

    @property
    def has_tagging(self):
        return self._values[u"HAS_TAGGING"]
