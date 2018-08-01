#-*- coding:utf-8-*-

"""
file: model.py

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

import time, codecs
import itertools

from sem.storage import Coder
from template    import ListPattern

class Model(object):
    def __init__(self, constraints={}):
        self._tagset       = Coder()
        self._templates    = []
        self._observations = Coder()
        self._uoff         = []
        self._boff         = []
        self._weights      = [] # list
        self._max_col      = 0
    
    def __call__(self, x):
        return self.tag_viterbi(x)
    
    @classmethod
    def from_wapiti_model(cls, filename, encoding="utf-8", verbose=True):
        MODEL = 0
        READER = 1
        READ_TEMPLATE = 2
        LABELS = 3
        OBSERVATIONS = 4
        FEATURES = 5
        
        model           = Model()
        n_weights       = -1
        n_patterns      = -1
        n_labels        = -1
        n_observations  = -1
        current_feature = 0
        state           = MODEL
        line_index      = 0
        if encoding is None:
            fd = open(filename, "rU")
        else:
            fd = codecs.open(filename, "rU", encoding)
        lines = [line.strip() for line in fd.readlines()]
        
        n_weights = int(lines[line_index].split(u"#")[-1])
        line_index += 1
        
        n_patterns, max_col, other = lines[line_index].split(u"#")[-1].split(u"/")
        n_patterns = int(n_patterns)
        max_col = int(max_col)
        model._max_col = max_col
        line_index += 1
        
        for line in lines[line_index : line_index+n_patterns]:
            line = line.split(":",1)[1][:-1]
            model._templates.append(ListPattern.from_string(line))
        assert len(model.templates) == n_patterns
        line_index += n_patterns
        state = LABELS
        
        s = time.time()
        n_labels = int(lines[line_index].strip().split("#")[-1])
        line_index += 1
        for line in lines[line_index : line_index+n_labels]:
            line = line.strip()
            model.tagset.add(line[line.index(":")+1 : -1])
        line_index += n_labels
        assert len(model.tagset) == n_labels
        state = OBSERVATIONS
        """if verbose:
            print "labels:", time.time()-s"""
        
        s = time.time()
        n_observations = int(lines[line_index].split("#")[-1])
        line_index += 1
        model._uoff = [-1]*n_observations
        model._boff = [-1]*n_observations
        for line in lines[line_index : line_index+n_observations]:
            obs      = line[line.index(":")+1 : -1]
            n_feats  = (n_labels if obs[0] in "u*" else 0)
            n_feats += (n_labels**2 if obs[0] in "b*" else 0)
            
            model.observations.add(obs)
            if obs[0] in "u*":
                model.uoff[len(model.observations)-1] = current_feature
            if obs[0] in "b*":
                model.boff[len(model.observations)-1] = current_feature + (n_labels if obs[0]==u"*" else 0)
            current_feature += n_feats
        line_index += n_observations
        model._weights = [0.0]*current_feature
        state = FEATURES
        """if verbose:
            print "observations:", time.time()-s"""
        
        s = time.time()
        for line in lines[-n_weights : ]:
            index, weight = line.split("=")
            model.weights[int(index)] = float.fromhex(weight)#(float.fromhex(weight) if "x" in weight else float(weight))
        """if verbose:
            print "features:", time.time()-s"""
        
        return model
    
    @property
    def tagset(self):
        return self._tagset
    
    @property
    def templates(self):
        return self._templates
    
    @property
    def observations(self):
        return self._observations
    
    @property
    def uoff(self):
        """
        Unigram OFFset
        """
        return self._uoff
    
    @property
    def boff(self):
        """
        Bigram OFFset
        """
        return self._boff
    
    @property
    def weights(self):
        return self._weights
    
    def tag_viterbi(self, sentence):
        Y = len(self.tagset)
        T = len(sentence)
        range_Y = range(Y)
        range_T = range(T)
        psi = [[[0.0]*Y for _y1 in range_Y] for _t in range_T]
        back = [[0]*Y for _t in range_T]
        cur = [0.0]*Y
        old = [0.0]*Y
        psc = [0.0]*T
        sc = -2**30
        tag = [u"" for _t in range_T]
        # avoiding dots
        weights_ = self._weights
        obs_encode = self._observations.encode
        templates_ = self._templates
        uoff_ = self._uoff
        boff_ = self._boff
        
        unigrams = []
        bigrams = []
        for t in range_T:
            unigrams.append([])
            bigrams.append([])
            u_append = unigrams[-1].append
            b_append = bigrams[-1].append
            for template in templates_:
                obs = template.instanciate(sentence, t)
                o = obs_encode(obs)
                #if t == 0: print obs, "--", o
                if o != -1:
                    if obs[0] == 'u' and uoff_[o] != -1:
                        #u_append(uoff_[o])
                        u_append(weights_[uoff_[o] : uoff_[o]+Y])
                    if obs[0] == 'b' and boff_[o] != -1:
                        #b_append(boff_[o])
                        b_append(weights_[boff_[o] : boff_[o]+Y*Y])
        
        # compute scores in psi
        for t in range_T:
            unigrams_T = unigrams[t]
            for y in range_Y:
                sum_ = 0.0
                for w in unigrams_T:
                    sum_ += w[y]
                for yp in range_Y:
                    psi[t][yp][y] = sum_
        for t in range(1,T):
            bigrams_T = bigrams[t]
            d = 0
            for yp, y in itertools.product(range_Y, range_Y):
                for w in bigrams_T:
                    psi[t][yp][y] += w[d]
                d += 1
        
        for y in range_Y:
            cur[y] = psi[0][0][y]
        for t in range(1,T):
            for y in range_Y:
                old[y] = cur[y]
            for y in range_Y:
                bst = -2**30
                idx = 0
                for yp in range_Y:
                    val = old[yp] + psi[t][yp][y]
                    if val > bst:
                        bst = val
                        idx = yp
                back[t][y] = idx
                cur[y] = bst
        
        bst = 0
        for y in range(1,Y):
            if cur[y] > cur[bst]:
                bst = y
        sc = cur[bst]
        for t in reversed(range_T):
            yp = (back[t][bst] if t != 0 else 0)
            y = bst
            tag[t] = self._tagset.decode(y)
            psc[t] = psi[t][yp][y]
            bst = yp
        
        return tag, psc, sc
    
    def write(self, filename, encoding="utf-8"):
        with codecs.open(filename, "w", "utf-8") as O:
            O.write("#mdl#2#{0}\n".format(len([w for w in self.weights if w !=0.0])))
            O.write("#rdr#{0}/{1}/0\n".format(len(self._templates), self._max_col))
            for pattern in self._templates:
                uni_pattern = unicode(pattern)
                O.write("{0}:{1},\n".format(len(uni_pattern), uni_pattern))
            O.write(u"#qrk#{0}\n".format(len(self._tagset)))
            for tag in self.tagset:
                O.write(u"{0}:{1}\n".format(len(tag), tag))
            # observations
            O.write(u"#qrk#{0}\n".format(len(self._observations)))
            for obs in self._observations:
                O.write(u"{0}:{1}\n".format(len(obs), obs))
            for index, w in enumerate(self.weights):
                if w != 0.0:
                    O.write(u"{0}={1}\n".format(index, float.hex(w)))
    
    def dump(self, filename):
        ntags = len(self.tagset)
        with codecs.open(filename, "w", "utf-8") as O:
            for i in range(len(self.observations)):
                o = self.observations.decode(i)
                written = False
                if o[0] == u"u":
                    off = self.uoff[i]
                    for y in range(ntags):
                        w = self.weights[off+y]
                        if w != 0:
                            O.write(u"{0}\t{1}\t{2}\t{3:.5f}\n".format(o, u'#', self.tagset.decode(y), w))
                            written = True
                else:
                    off = self.boff[i]
                    d = 0
                    for yp in range(ntags):
                        for y in range(ntags):
                            w = self.weights[off+d]
                            if w != 0:
                                O.write(u"{0}\t{1}\t{2}\t{3:.5f}\n".format(o, self.tagset.decode(yp), self.tagset.decode(y), w))
                                written = True
                            d += 1
                if written:
                    O.write(u"\n")
