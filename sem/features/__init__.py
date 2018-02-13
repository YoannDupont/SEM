"""
file: __init__.py

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

from feature import Feature
from getterfeatures import DEFAULT_GETTER, IdentityFeature, DictGetterFeature, FindForwardFeature, FindBackwardFeature
from arityfeatures import ArityFeature, UnaryFeature, BinaryFeature, BOSFeature, EOSFeature, LowerFeature, SubstringFeature, IsUpperFeature, SubstitutionFeature, SequencerFeature
from booleanfeatures import NotFeature, AndFeature, OrFeature
from dictionaryfeatures import TokenDictionaryFeature, MultiwordDictionaryFeature, MapperFeature, NUL
from listfeatures import ListFeature, SomeFeature, AllFeature, NoneFeature
from matcherfeatures import MatchFeature, CheckFeature, SubsequenceFeature, TokenFeature
from rulefeatures import RuleFeature, OrRuleFeature
from stringfeatures import EqualFeature, EqualCaselessFeature
from triggeredfeatures import TriggeredFeature
from directoryfeatures import DirectoryFeature, FillerFeature

from xml2feature import XML2Feature
