# -*- coding: utf-8 -*-
from corpus import ICorpus, OCorpus

class Segmentation(object):

    def __init__(self,
                 in_corpus, out_corpus,
                 opening_characters = u"([{«", closing_characters = u")]}»",
                 strong_puncts = u"?!…", weak_puncts = u",:;",
                 apostrophes = True):
        self.in_corpus = in_corpus
        self.out_corpus = out_corpus
        self.opening_chars = opening_characters
        self.closing_chars = closing_characters
        self.strong_puncts = strong_puncts
        self.weak_puncts = weak_puncts
        self.apostrophes = apostrophes

        self.opening_char_count = 0
        self.sentence = u"" # the sentence to be written

    def isChar(self, s):
        return len(s) == 1

    def isCharIn(self, token, characters):
        if self.isChar(token):
            return characters.find(token) != -1
        else:
            return False

        return str_buffer

    def isOpeningChar(self, s): 
      return self.isCharIn(s, self.opening_chars)

    def isClosingChar(self, s):
        return self	.isCharIn(s, self.closing_chars)

    # '.' should not be considered as a strong punctuation
    # because it can be used to other purposes.
    def isStrongPunct(self, s):
        b = self.isCharIn(s, self.strong_puncts)
        b = b or (u'...'.find(s) != -1)
        return b

    def isWeakPunct(self, s):
        return isCharIn(s, self.weak_puncts)

    def isSentenceDot(self, the_line, token, current_position):
        EOS = False # End Of Sentence
        if not current_position >= (len(the_line) - 2): # the token is not in the two last tokens of the line
            next_token = the_line[current_position+1]
            if next_token[0].isupper() or (not next_token.isalpha()):
                EOS = True
        else: # the dot may be followed by a double-quote or a closing char
            EOS = False
        return EOS

    def isAcronym(self, token):
        return token.count(u".") > 1 or token.replace(".","").isupper()

    def isAbbreviationBeforeNoun(self, token):
        abbr_list = [u"mme.", u"mmes.", u"melle.", u"melles.", u"mlle.", u"mlles.", u"m.", u"mr.", u"me.", u"mrs.", u"st."]
        return abbr_list.count(token.lower()) != 0

    # A token is a unit if:
    #  | it start by letter(s) and ends with number(s)
    #  | it start by number(s) and ends with number(s)
    #  | and the numbers and letters are not "mixed"
    # if the token is not a unit, the returned inex is -1
    def isUnit(self, token):
        left = token.lstrip(u"0123456789")
        right = token.rstrip(u"0123456789")
        which = None

        if len(left) < len(token):
            which = left
        elif len(right) < len(token):
            which = right
        else:
            return -1
        for C in which:
            if C.isdigit():
                return -1
        return len(token) - len(left)

    def cut(self, token):
        if self.isChar(token):
            res = token
        else:
            res = self.cutByOpeningChars(token)
            res = self.cutByClosingChars(res)
            res = self.cutByStrongPuncts(res)
            res = self.cutByWeakPuncts(res)
            res = self.cutByClitics(res)
            if self.apostrophes:
                res = self.separate(res, u"'", False)
        return res

    def separate(self, token, separating_chars, Before):
        str_buffer = token

        for S_C in separating_chars:
            if Before:
                str_buffer = str_buffer.replace(S_C, u' '+S_C)
            else:
                str_buffer = str_buffer.replace(S_C, S_C+u' ')
        return str_buffer

    def cutByOpeningChars(self, token):
        return self.separate(token, self.opening_chars, False)

    def cutByClosingChars(self, token):
        return self.separate(token, self.closing_chars, True)

    def cutByStrongPuncts(self, token):
        s = self.separate(token, self.strong_puncts, True)
        return s.replace(u'...', u' ...')

    def cutByWeakPuncts(self, token):
        return self.separate(token, self.weak_puncts, True)

    def cutByClitics(self, token):
        cl = [u'-je',u'-tu',u'-il',u'-elle',u'-nous',u'-vous',u'-ils',u'-elles',u'-moi',u'-toi',u'-lui',u'-on',u'-ce',u'-le',u'-la',u'-les']
        return self.separate(token, cl, True)

    def handleChar(self, token, current_position):
        if self.isOpeningChar(token):
            self.opening_char_count += 1
        if self.isClosingChar(token):
            self.opening_char_count -= 1
        if current_position == 0:
            self.sentence += token
        else:
            self.sentence += u' '+token
        if self.isStrongPunct(token) and self.opening_char_count == 0:
            self.out_corpus.put(self.sentence.split())
            self.sentence = u""

    # when the token ends with a dot
    # it has to be treated in the current line which is not modified in the process
    def handleTerminatingDot(self, the_line, token, current_position):
        if (self.isAcronym(token)) or (self.isAbbreviationBeforeNoun(token)):
            self.sentence += u" " + token
        else:
            self.sentence += u" " + token[:-1] + u" " + token[-1]
            if self.isSentenceDot(the_line, token, current_position) and (self.opening_char_count == 0):
                self.out_corpus.put(self.sentence.split())
                self.sentence = u""


    def seg(self):
        for paragraph in self.in_corpus:
            for line in paragraph:
                self.out_corpus.put(line)

    def segmentation(self):
        the_line = u""
        current_position = 0
        EOL = False # end of line

        for paragraph in self.in_corpus:
            for line in paragraph:
                the_line = self.cut(line).strip().split() # splitting the line in tokens
                current_position = 0
                EOL = False

                while not EOL:
                    token = the_line[current_position]

                    if self.isChar(token):
                        self.handleChar(token, current_position)
                    elif self.isUnit(token) != -1: # the token is a number with an unit at its start or at its end
                        index = self.isUnit(token)
                        self.sentence += u" " + token[0 : index] + u" " + token[index : len(token)]
                    elif token[-1] == u".": # the token ends with a dot
                        self.handleTerminatingDot(the_line, token, current_position)
                    else: # any other case : the token is added
                        self.sentence += u" " + the_line[current_position]

                    current_position += 1
                    EOL = current_position >= len(the_line)

                    if EOL and self.sentence != u"":
                        self.out_corpus.put(self.sentence.split())
                        self.sentence = u""
