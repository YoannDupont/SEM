#-*- encoding:utf-8 -*-

import re

from obj.misc import last_index

class Index_To_Bound(object):
    def __init__(self):
        self._matches = []
    
    @property
    def matches(self):
        return self._matches
    
    def find(self, element):
        for i,m in enumerate(self._matches):
            if m[-1] < element:
                continue
            elif m[0] > element:
                return (i, False)
            elif element in m:
                return (i, True)
            elif m[0] < element < m[-1]:
                return (i, False)
        return (len(self._matches), False)
    
    def contains(self, element):
        return self.find(element)[-1]
    
    def add(self, element):
        i, found = self.find(element)
        
        if not found:
            if i == len(self._matches):
                self._matches.append([element])
            else:
                m = self._matches[i]
                if m[0] < element < m[-1]:
                    self._matches[i].append(element)
                    self._matches[i].sort()
                else:
                    self._matches = self._matches[:i] + [[element]] + self._matches[i:]
    
    def add_with(self, to_add, present):
        index, found = self.find(present)
        if not found:
            raise ValueError('"%s" was not found in the list' %str(present))
        
        self._matches[index].append(to_add)
        self._matches[index].sort()

def isabbrbeforenoun(token):
    is_abn = re.compile(u"^(dr|me?lles?|mmes?|mr?s?|st|)$", re.U + re.I + re.M)
    return is_abn.match(token) is not None

def getcls(token):
    cls = re.compile(u"^(-je|-tu|-il|-elle|-on|-nous|-vous|-ils|-elles|-t-il|-t-elle|-t-on|-t-ils|-t-elles)", re.U + re.I + re.M)
    return cls.match(token)

def word_tokeniser(s):
    """
    Returns a tokenised version of the sentence.
    That is, a string that contains tokens separated by a space between them.
    
    Parameters
    ----------
    s : str
        the string to tokenise. It is unimportant if s contains several
        sentences or not. They will be inferred later. The only thing this
        function does is separating tokens.
    """
    import time
    start = time.time()
    word_bounds = Index_To_Bound()
    word_bounds.add(0)
    index = 0
    while index < len(s):
        c = s[index]
        if c == u" ":
            word_bounds.add(index)
            word_bounds.add_with(index+1, index)
        elif c == u"," and 0 < index < len(s) and not (s[index-1].isdigit() or s[index+1].isdigit()):
            word_bounds.add(index)
            word_bounds.add(index+1)
        elif c in u"\";:«»()[]*/":
            word_bounds.add(index)
            word_bounds.add(index+1)
        elif c in u"?!":
            if index > 0 and s[index-1] not in "?!":
                word_bounds.add(index)
            if index < len(s)-1 and s[index+1] not in "?!":
                word_bounds.add(index+1)
            if index == len(s)-1:
                word_bounds.add(index+1)
        elif c == u".":
            if index == len(s)-1:
                word_bounds.add(index)
                word_bounds.add(index + 1)
            elif 0 < index < len(s):
                prev = s[word_bounds.matches[-1][-1] : index]
                if not(s[index-1].isdigit() and s[index+1].isdigit() or isabbrbeforenoun(prev)):
                    word_bounds.add(index)
                    word_bounds.add(index + 1)
        elif c in u"0123456789":
            if index > 0 and s[index-1] not in u"0123456789.,-": # unit is before
                if not s[last_index(s[:index], " ") : index].isdigit():
                    word_bounds.add(index)
            elif index < len(s)-1:
                if s[index+1] not in u"0123456789.,-": # unit is after
                    i = -1
                    try:
                        i = index + s[index : ].index(" ")
                    except:
                        pass
                    if not(s[index : i].isdigit() and s[index+1].isdigit()):
                        word_bounds.add(index+1)
                elif s[index+1] in "-":
                    word_bounds.add(index+1)
                    word_bounds.add(index+2)
        elif c in u"'ʼ’":
            word_bounds.add(index+1)
        elif c == u"-":
            i = -1
            try:
                i = index + s[index : ].index(" ")
            except:
                pass
            cls = getcls(s[index : i])
            if cls is not None:
                matched = cls.group()
                word_bounds.add(index)
                index += len(matched) - 1
        index += 1
    # has to be added last, otherwise we cannot be sure that the last token
    # is the one at index -1.
    word_bounds.add(len(s))
    
    laps = time.time() - start
    print "%.2f tokens per second" %(float(len(word_bounds._matches)-1) / laps)
    tokens = []
    for i in range(len(word_bounds.matches)-1):
        tokens.append(s[word_bounds.matches[i][-1] : word_bounds.matches[i+1][0]])
    
    return tokens

def sentence_tokeniser(tokens):
    """
    Returns a list of sentences.
    A sentence being a list of tokens.
    
    Parameters
    ----------
    tokens : list of str
        the tokens to be regrouped in sentences. It is here that sentences
        are inferred so "proper" (meaning awaited) tokenisation should be
        done before hand.
    """
    
    sent_bounds    = Index_To_Bound()
    opening_counts = [0 for i in tokens]
    count          = 0
    for i in range(len(opening_counts)):
        if tokens[i] in u"«([":
            count += 1
        if tokens[i] in u"»)]":
            count -= 1
        opening_counts[i] = count
    
    sent_bounds.add(0)
    for index, token in enumerate(tokens):
        if re.match(u"^[?!]+$", token) or token == u"…" or re.match(u"\.\.+", token):
            sent_bounds.add(index+1)
        if token == u".":
            if opening_counts[index] == 0:
                sent_bounds.add(index+1)
    sent_bounds.add(len(tokens))

    sents = []
    for i in range(len(sent_bounds.matches)-1):
        sents.append(tokens[sent_bounds.matches[i][-1] : sent_bounds.matches[i+1][0]])
    
    return sents
