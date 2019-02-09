#-*- encoding: utf-8 -*-

"""
file: test_segmentation.py

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

import unittest
import codecs, os.path

from sem import SEM_DATA_DIR

import sem.tokenisers
import sem.tokenisers.fr as FrenchTokeniser
import sem.tokenisers.en as EnglishTokeniser

class TestSegmentation(unittest.TestCase):
    def test_fr(self):
        content = codecs.open(os.path.join(SEM_DATA_DIR, "non-regression", "fr", "in", "segmentation.txt"), "rU", "utf-8").read()
        conll   = codecs.open(os.path.join(SEM_DATA_DIR, "non-regression", "fr", "out", "segmentation.txt"), "rU", "utf-8").read().strip()
        
        token_spans     = FrenchTokeniser.word_spans(content)
        sentence_spans  = sem.tokenisers.bounds2spans(FrenchTokeniser.sentence_bounds(content, token_spans))
        paragraph_spans = sem.tokenisers.bounds2spans(FrenchTokeniser.paragraph_bounds(content, sentence_spans, token_spans))
        
        tokens            = [content[s.lb : s.ub] for s in token_spans]
        sentences         = [tokens[s.lb : s.ub] for s in sentence_spans]
        token_content     = u"".join(tokens)
        token_conll       = u"\n\n".join([u"\n".join(tokens) for tokens in sentences])
        spaceless_content = content.replace(u"\r",u"").replace(u"\n",u"").replace(u" ", u"")
        
        self.assertEquals(token_content, spaceless_content) # no lost content
        self.assertEquals(token_conll, conll) # same segmentation
    
    def test_en(self):
        content = codecs.open(os.path.join(SEM_DATA_DIR, "non-regression", "en", "in", "segmentation.txt"), "rU", "utf-8").read()
        
        token_spans     = sem.tokenisers.bounds2spans(EnglishTokeniser.word_bounds(content))
        sentence_spans  = sem.tokenisers.bounds2spans(EnglishTokeniser.sentence_bounds(content, token_spans))
        paragraph_spans = sem.tokenisers.bounds2spans(EnglishTokeniser.paragraph_bounds(content, sentence_spans, token_spans))
        
        token_content     = u"".join([content[s.lb : s.ub] for s in token_spans])
        spaceless_content = content.replace("\r","").replace("\n","").replace(" ", "")
        
        self.assertEquals(token_content, spaceless_content) # no lost content


if __name__ == '__main__':
    unittest.main(verbosity=2)
