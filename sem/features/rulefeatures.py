# -*- coding: utf-8 -*-

"""
file: rulefeatures.py

Description: rule-based features.

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

from feature        import Feature
from getterfeatures import DEFAULT_GETTER

class RuleFeature(Feature):
    def __init__(self, features, *args, **kwargs):
        super(RuleFeature, self).__init__(self, *args, **kwargs)
        self._is_boolean  = False
        self._is_sequence = True
        self._features = features
    
    def __call__(self, list2dict, *args, **kwargs):
        l = ["O"]*len(list2dict)
        pos_beg = 0
        pos_cur = 0
        feat_index = 0
        feat = self._features[feat_index]
        remain_min = feat.min_match
        remain_max = feat.max_match
        matches = []
        func = (feat.__call__ if feat.is_boolean else feat.step)
        while pos_beg < len(list2dict)-1:
            while remain_min <= 0 and not pos_cur >= len(list2dict) and not func(list2dict, pos_cur) and feat_index < len(self._features)-1:
                feat_index += 1
                feat = self._features[feat_index]
                func = (feat.__call__ if feat.is_boolean else feat.step)
                remain_min = feat.min_match
                remain_max = feat.max_match
            if feat_index >= len(self._features) or pos_cur >= len(list2dict):
                pos_beg += 1
                pos_cur = pos_beg
                feat_index = 0
                feat = self._features[feat_index]
                func = (feat.__call__ if feat.is_boolean else feat.step)
                remain_min = feat.min_match
                remain_max = feat.max_match
                continue
            if func(list2dict, pos_cur):
                N = int(func(list2dict, pos_cur))
                pos_cur += N
                remain_min -= 1
                remain_max -= 1
            elif remain_min <= 0:
                if feat_index < len(self._features)-1:
                    feat_index += 1
                else:
                    matches.append([pos_beg, pos_cur])
                    pos_beg = pos_cur
                    pos_cur = pos_beg
                    feat_index = 0
                feat = self._features[feat_index]
                func = (feat.__call__ if feat.is_boolean else feat.step)
                remain_min = feat.min_match
                remain_max = feat.max_match
            elif remain_max >= 0:
                pos_beg += 1
                pos_cur = pos_beg
                feat_index = 0
                feat = self._features[feat_index]
                func = (feat.__call__ if feat.is_boolean else feat.step)
                remain_min = feat.min_match
                remain_max = feat.max_match
            if remain_max == 0:
                if feat_index < len(self._features)-1:
                    feat_index += 1
                else:
                    feat_index = 0
                    matches.append([pos_beg, pos_cur])
                    pos_beg = pos_cur
                    pos_cur = pos_beg
                feat = self._features[feat_index]
                func = (feat.__call__ if feat.is_boolean else feat.step)
                remain_min = feat.min_match
                remain_max = feat.max_match
        for lo,hi in matches:
            l[lo] = "B-{0}".format(self.name)
            for i in range(lo+1, hi):
                l[i] = "I-{0}".format(self.name)
        return l
    
    def step(self, list2dict, i):
        pos_beg = i
        pos_cur = pos_beg
        feat_index = 0
        feat = self._features[feat_index]
        remain_min = feat.min_match
        remain_max = feat.max_match
        matches = []
        func = (feat.__call__ if feat.is_boolean else feat.step)
        while pos_beg < len(list2dict)-1:
            while remain_min <= 0 and not func(list2dict, pos_cur) and feat_index < len(self._features)-1:
                feat_index += 1
                feat = self._features[feat_index]
                func = (feat.__call__ if feat.is_boolean else feat.step)
                remain_min = feat.min_match
                remain_max = feat.max_match
            if feat_index >= len(self._features):
                return 0
            if func(list2dict, pos_cur):
                N = int(func(list2dict, pos_cur))
                pos_cur += N
                remain_min -= 1
                remain_max -= 1
            elif remain_min <= 0:
                if feat_index < len(self._features)-1:
                    feat_index += 1
                else:
                    return pos_cur - pos_beg
                feat = self._features[feat_index]
                func = (feat.__call__ if feat.is_boolean else feat.step)
                remain_min = feat.min_match
                remain_max = feat.max_match
            elif remain_max >= 0:
                return 0
            if remain_max == 0:
                if feat_index < len(self._features)-1:
                    feat_index += 1
                else:
                    return pos_cur - pos_beg
                feat = self._features[feat_index]
                func = (feat.__call__ if feat.is_boolean else feat.step)
                remain_min = feat.min_match
                remain_max = feat.max_match
        return 0

class OrRuleFeature(Feature):
    def __init__(self, features, *args, **kwargs):
        super(OrRuleFeature, self).__init__(self, *args, **kwargs)
        self._is_boolean  = False
        self._is_sequence = True
        self._features = features
    
    def step(self, list2dict, i):
        pos_beg = i
        pos_cur = pos_beg
        feat_index = 0
        feat = self._features[feat_index]
        remain_min = feat.min_match
        remain_max = feat.max_match
        matches = []
        best_end = -1
        for feat in self._features:
            func = (feat.__call__ if feat.is_boolean else feat.step)
            best_end = max(best_end, int(func(list2dict, pos_beg)))
        return best_end
