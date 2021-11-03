# -*- encoding: utf-8 -*-

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
import re

import sem.tokenisers


FR_TEXT = """18 mai j'ai en effet un p, porte-serviette qui est 1,2% plus cool que m. Trucmuche et mme. Machinchose.

Test: un mot qui finit par m, zoom. Et on regarde s'il est bien segmenté!

test2.

I
Vérification qu'une fin de ligne sans ponctuation est considérée comme une fin de phrase ou non.

Des     espaces multiples d'   orgines nombreuses.

Un test de ponctuation... Un autre test de ponctuation… Et une fin de ligne sans ponctuation

St-Jean peut causer des soucis de segmentation.

Vous pouvez m'écrire à yoa.dupont@gmail.com pour des questions au sujet de SEM, n'hésitez pas à visiter la page : http://www.lattice.cnrs.fr/sites/itellier/SEM.html!
"""  # noqa: E501
FR_TOKENS = [
    "18", "mai", "j'", "ai", "en", "effet", "un", "p", ",", "porte-serviette", "qui", "est", "1,2",
    "%", "plus", "cool", "que", "m.", "Trucmuche", "et", "mme.", "Machinchose", ".", "Test", ":",
    "un", "mot", "qui", "finit", "par", "m", ",", "zoom", ".", "Et", "on", "regarde", "s'", "il",
    "est", "bien", "segmenté", "!", "test", "2", ".", "I", "Vérification", "qu'", "une", "fin",
    "de", "ligne", "sans", "ponctuation", "est", "considérée", "comme", "une", "fin", "de",
    "phrase", "ou", "non", ".", "Des", "espaces", "multiples", "d'", "orgines", "nombreuses", ".",
    "Un", "test", "de", "ponctuation", "...", "Un", "autre", "test", "de", "ponctuation", "…",
    "Et", "une", "fin", "de", "ligne", "sans", "ponctuation", "St-Jean", "peut", "causer", "des",
    "soucis", "de", "segmentation", ".", "Vous", "pouvez", "m'", "écrire", "à",
    "yoa.dupont@gmail.com", "pour", "des", "questions", "au", "sujet", "de", "SEM", ",", "n'",
    "hésitez", "pas", "à", "visiter", "la", "page", ":",
    "http://www.lattice.cnrs.fr/sites/itellier/SEM.html", "!"
]
EN_TEXT = """I,  I've tried to improve Bob's coolness by 1.2%.
Test

test2.

I am
just checking if a newline is considered as an end of sentence or not.
"""


class TestSegmentation(unittest.TestCase):
    def test_get(self):
        default = sem.tokenisers.get_tokeniser("default")()  # noqa: F841
        fr = sem.tokenisers.get_tokeniser("fr")()  # noqa: F841
        en = sem.tokenisers.get_tokeniser("en")()  # noqa: F841

    def test_fr(self):
        content = FR_TEXT
        tokens_reference = FR_TOKENS[:]
        tokeniser = sem.tokenisers.FrenchTokeniser()
        token_spans = tokeniser.word_spans(content)
        tokens_guess = [content[s.lb: s.ub] for s in token_spans]

        self.assertEquals(tokens_guess, tokens_reference)

    def test_en(self):
        content = EN_TEXT
        tokeniser = sem.tokenisers.EnglishTokeniser()
        token_spans = tokeniser.word_spans(content)
        token_content = "".join([content[s.lb: s.ub] for s in token_spans])
        spaceless_content = re.sub(r"\s+", "", content)

        self.assertEquals(token_content, spaceless_content)  # no lost content


if __name__ == "__main__":
    unittest.main(verbosity=2)
