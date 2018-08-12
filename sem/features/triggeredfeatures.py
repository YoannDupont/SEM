# -*- coding: utf-8 -*-

"""
file: triggeredfeatures.py

Description: defines features that will only be extracted when
a given condition is met (when it is triggered).

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

from .feature        import Feature
from .getterfeatures import DEFAULT_GETTER

class TriggeredFeature(Feature):
    def __init__(self, trigger, operation, default="_untriggered_", *args, **kwargs):
        super(TriggeredFeature, self).__init__(self, *args, **kwargs)
        
        self.trigger   = trigger
        self.operation = operation
        self.default   = default
        
        if not self.trigger.is_boolean:
            raise ValueError("Trigger for {0} is not boolean.".format(self.name))
        
        self._is_boolean = self.operation._is_boolean
    
    def __call__(self, *args, **kwargs):
        if self.trigger(*args, **kwargs):
            return self.operation(*args, **kwargs)
        else:
            return self.default
