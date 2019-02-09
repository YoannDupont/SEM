#-*- coding:utf-8 -*-

"""
file: coder.py

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
