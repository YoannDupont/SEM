#-*- coding:utf-8 -*-

class Coder(object):
    def __init__(self):
        self._encoder = {}
        self._decoder = []
    
    def __len__(self):
        return len(self._decoder)
    
    def __iter__(self):
        return iter(self._decoder[:])
    
    def __contains__(self, element):
        return element in self._encoder
    
    def keys(self):
        return self._decoder[:]
    
    @classmethod
    def fromlist(cls, elements):
        coder = Coder()
        for element in elements:
            coder.add(element)
        return coder
    
    def add(self, element, strict=False):
        if element not in self._encoder:
            self._encoder[element] = len(self)
            self._decoder.append(element)
        elif strict:
            raise KeyError("'{0}' already in coder".format(element))
    
    def insert(self, index, element):
        if element not in self._encoder:
            self._decoder.insert(index, element)
            self._encoder[element] = index
            for nth in range(index+1, len(self._encoder)):
                self._encoder[self._decoder[nth]] = nth
    
    def encode(self, element):
        return self._encoder.get(element, -1)
    
    def decode(self, integer):
        try:
            return self._decoder[integer]
        except:
            return None
