# -*- coding: utf-8 -*-

"""
file: stringfeatures.py

Description: features based on "raw" string values.

author: Yoann Dupont
copyright (c) 2016 Yoann Dupont - all rights reserved

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see GNU official website.
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
            l[lo] = "B-%s" %self.name
            for i in range(lo+1, hi):
                l[i] = "I-%s" %self.name
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