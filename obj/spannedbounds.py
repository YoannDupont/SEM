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
    
    def append(self, i):
        if self.is_forbidden(i): return
        if len(self._bounds) > 0 and self._bounds[-1].ub == i: return
        
        self._bounds.append(Span(i,i))
    
    def add_span(self, span):
        added = False
        for i in range(len(self._bounds)):
            if span.ub <= self._bounds[i]:
                self._bounds.insert(i, span)
                added = True
            if added: break
        if not added:
            self._bounds.append(span)
    
    def add(self, i):
        if self.is_forbidden(i): return
        
        index, found = self.find(i)
        if found:
            return
        else:
            if index == -1:
                self._bounds.append(Span(i,i))
            else:
                self._bounds.insert(index, Span(i,i))
    
    def add_at(self, i, index):
        if i in self._forbidden: return
        
        if i in self._bounds[index]:
            return
        else:
            if i < self._bounds[index].lb:
                self._bounds[index].lb = i
            elif i > self._bounds[index].ub:
                self._bounds[index].ub = i
    
    def add_with(self, i, j):
        if self.is_forbidden(i): return
        
        index, found = self.find(j)
        if not found:
            return
        else:
            if i in self._bounds[index]:
                return
            else:
                if i < self._bounds[index].lb:
                    self._bounds[index].lb = i
                elif i > self._bounds[index].ub:
                    self._bounds[index].ub = i
    
    def add_last(self, i):
        if self.is_forbidden(i): return
        
        if i in self._bounds[-1]:
            return
        else:
            if i == self._bounds[-1].ub+1:
                self._bounds[-1].ub = i
            elif i > self._bounds[-1].ub+1:
                self._bounds.append(Span(i,i))
    
    def is_forbidden(self, i):
        return i in self._forbidden
