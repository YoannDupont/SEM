#-*- encoding:utf-8 -*-

class Span(object):
    def __init__(self, lb, ub):
        self._lb = min(lb, ub)
        self._ub = max(lb, ub)
    
    def __eq__(self, span):
        return self.lb == span.lb and self.ub == span.ub
    
    def __contains__(self, i):
        return i >= self._lb and i <= self.ub
    
    def __len__(self):
        return self._ub - self._lb
    
    def __str__(self):
        return "[%i:%i]" %(self._lb, self._ub)
    
    @property
    def lb(self):
        return self._lb
    
    @property
    def ub(self):
        return self._ub
    
    @lb.setter
    def lb(self, lb):
        self._lb = min(lb, self._ub)
    
    @ub.setter
    def ub(self, ub):
        self._ub = max(ub, self._lb)
    
    def strictly_contains(self, i):
        return i > self._lb and i < self.ub
    
    def expand_lb(self, length):
        self._lb -= length
    
    def expand_ub(self, length):
        self._ub += length
