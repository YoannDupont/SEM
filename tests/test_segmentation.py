#-*- encoding: utf-8 -*-

import unittest
import codecs, os.path

import software

from obj.tokenisers.fr import Tokeniser as FrTok
from obj.tokenisers.en import Tokeniser as EnTok

class TestSegmentation(unittest.TestCase):
    def test_fr(self):
        tokeniser = FrTok()
        
        content = codecs.open(os.path.join(software.SEM_HOME, "non-regression", "fr", "in", "segmentation.txt"), "rU", "utf-8").read()
        conll   = codecs.open(os.path.join(software.SEM_HOME, "non-regression", "fr", "out", "segmentation.txt"), "rU", "utf-8").read().strip()
        
        token_spans     = tokeniser.bounds2spans(tokeniser.word_bounds(content))
        sentence_spans  = tokeniser.bounds2spans(tokeniser.sentence_bounds(content, token_spans))
        paragraph_spans = tokeniser.bounds2spans(tokeniser.paragraph_bounds(content, sentence_spans, token_spans))
        
        tokens            = [content[s.lb : s.ub] for s in token_spans]
        sentences         = [tokens[s.lb : s.ub] for s in sentence_spans]
        token_content     = u"".join(tokens)
        token_conll       = u"\n\n".join([u"\n".join(tokens) for tokens in sentences])
        spaceless_content = content.replace("\r","").replace("\n","").replace(" ", "")
        
        self.assertEquals(token_content, spaceless_content) # no lost content
        self.assertEquals(token_conll, conll)               # same segmentation
    
    def test_en(self):
        tokeniser = EnTok()
        
        content = codecs.open(os.path.join(software.SEM_HOME, "non-regression", "en", "in", "segmentation.txt"), "rU", "utf-8").read()
        
        token_spans     = tokeniser.bounds2spans(tokeniser.word_bounds(content))
        sentence_spans  = tokeniser.bounds2spans(tokeniser.sentence_bounds(content, token_spans))
        paragraph_spans = tokeniser.bounds2spans(tokeniser.paragraph_bounds(content, sentence_spans, token_spans))
        
        token_content     = u"".join([content[s.lb : s.ub] for s in token_spans])
        spaceless_content = content.replace("\r","").replace("\n","").replace(" ", "")
        
        self.assertEquals(token_content, spaceless_content) # no lost content


if __name__ == '__main__':
    unittest.main(verbosity=2)
