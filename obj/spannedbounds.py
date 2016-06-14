#-*- encoding:utf-8 -*-

from obj.span import Span

class SpannedBounds(object):
    def __init__(self):
        self._bounds    = []
        self._forbidden = set()
    
    def __iter__(self):
        for e in self._bounds:
            yield e
    
    def __getitem__(self, i):
        return self._bounds[i]
    
    def __len__(self):
        return len(self._bounds)
    
    def add_forbiddens_regex(self, regex, s):
        for match in regex.finditer(s):
            for index in range(match.start()+1, match.end()):
                self._forbidden.add(index)
    
    def force_regex(self, regex, s):
        for match in regex.finditer(s):
            self.add(match.start())
            self.add(match.end())
    
    def find(self, i):
        for nth, span in enumerate(self._bounds):
            if i < span.lb:
                return (nth, False)
            elif i > span.ub:
                continue
            elif i in span:
                return (nth, True)
        return (-1, False)
    
    def append(self, span):
        if self.is_forbidden(span.lb): return
        if len(self._bounds) > 0:
            if span in self._bounds[-1] or span == self._bounds[-1]: return
        
        self._bounds.append(span)
    
    def add(self, span):
        if self.is_forbidden(span.lb): return
        
        index, found = self.find(span.lb)
        if found:
            return
        else:
            if index == -1:
                self._bounds.append(span)
            else:
                self._bounds.insert(index, span)
    
    def add_last(self, span):
        if self.is_forbidden(span.lb): return
        if span in self._bounds[-1]: return
        
        if self._bounds[-1].ub == span.lb:
            self._bounds[-1].expand_ub(span.ub - self._bounds[-1].ub)
    
    def is_forbidden(self, i):
        return i in self._forbidden
