# -*- coding: utf-8 -*-

"""
file: corpus.py

Description: defines the Corpus object. It is an object representation
of a CoNLL-formatted corpus.

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

_train_set = set(["train", "eval", "evaluate", "evaluation"])
_train = "train"
_label_set = set(["label", "annotate", "annotation"])
_label = "label"
_modes = _train_set | _label_set
_equivalence = dict([[mode, _train] for mode in _train_set] + [[mode, _label] for mode in _label_set])

class Entry(object):
    """
    The Entry object. It represents a field's identifier in a CoNLL corpus.
    An Entry may be used only in certain circumstances: for example, the
    output tag may only appear in train mode.
    """
    def __init__(self, name, mode="label"):
        if mode not in _modes:
            raise ValueError("Unallowed mode for entry: {0}".format(mode))
        self._name = name
        self._mode = _equivalence[mode]

    def __eq__(self, other):
        return self.name == other.name

    @property
    def name(self):
        return self._name

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, mode):
        self._mode = _equivalence[mode]

    @property
    def is_train(self):
        return self._mode == _train

    @property
    def is_label(self):
        return self._mode == _label

    @staticmethod
    def fromXML(xml_element):
        return Entry(**xml_element.attrib)

    def has_mode(self, mode):
        return self.mode == _equivalence[mode]

class Corpus(object):
    def __init__(self, fields=None, sentences=None):
        if fields:
            self.fields = fields[:]
        else:
            self.fields = []

        if sentences:
            self.sentences = sentences[:]
        else:
            self.sentences = []

    def __contains__(self, item):
        return item in self.fields

    def __len__(self):
        return len(self.sentences)

    def __iter__(self):
        for element in self.iterate_on_sentences():
            yield element

    def __unicode__(self):
        return self.unicode(self.fields)

    def unicode(self, fields, separator="\t"):
        fmt = "\t".join(["{{{0}}}".format(field) for field in fields])
        sentences = []
        for sentence in self:
            sentences.append([])
            for token in sentence:
                sentences[-1].append((fmt.format(**token)) + "\n")
        return "\n".join(["".join(sentence) for sentence in sentences])

    def to_matrix(self, sentence):
        sent = []
        for token in sentence:
            sent.append([token[field] for field in self.fields])
        return sent

    def iterate_on_sentences(self):
        for element in self.sentences:
            yield element

    def is_empty(self):
        return 0 == len(self.sentences)

    def has_key(self, key):
        return key in self.fields

    def append_sentence(self, sentence):
        self.sentences.append(sentence)

    def from_sentences(self, sentences, field_name="word"):
        del self.fields[:]
        del self.sentences[:]

        self.fields = [field_name]
        for sentence in sentences:
            self.sentences.append([])
            for token in sentence:
                self.sentences[-1].append({field_name: token})

    def from_segmentation(self, content, tokens, sentences, field_name="word"):
        self.fields = [field_name]
        for sentence in sentences.spans:
            self.append_sentence([
                {field_name: content[token.lb : token.ub]}
                for token in tokens.spans[sentence.lb : sentence.ub]
            ])

    def write(self, fd, fields=None):
        fmt = "\t".join(["{{{0}}}".format(field) for field in (fields or self.fields)]) + "\n"
        for sentence in self:
            for token in sentence:
                fd.write(fmt.format(**token))
            fd.write("\n")
