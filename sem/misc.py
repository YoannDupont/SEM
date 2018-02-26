# -*- coding: utf-8 -*-

"""
file: misc.py

Description: a file for miscellaneous operations.

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

import re
import os.path
import tarfile

def ranges_to_set(ranges, length, include_zero=False):
    """
    Returns a set of integers based of ranges over a reference list. Ranges are
    inclusive both in the lower and upper bound, unlike in python where they are
    inclusive only in the lower but not the upper bound.
    
    Parameters
    ----------
    ranges : str
        a list of ranges represented by a string. Each range is comma separated.
        A range is a couple of integers colon separated.
        If the index 0 in not present in the list, it is automatically added.
    length : int
        the reference length to use in case of negative indexing.
    """
    result = set()
    
    for current_range in ranges.split(','):
        if ':' in current_range:
            lo, hi = [int(i) for i in current_range.split(":")]
        else:
            lo = int(current_range)
            hi = lo
        
        if (hi < lo): continue
        
        if lo < 0: lo = length + lo
        if hi < 0: hi = length + hi
        
        for i in xrange(lo, hi+1): result.add(i)
    
    if include_zero: result.add(0)
    
    return result

def last_index(s, e):
    try:
        return len(s) - s[::-1].index(e[::-1]) - 1
    except ValueError:
        return -1

def correct_pos_tags(tags):
    corrected   = [[level2 for level2 in level1] for level1 in tags]
    corrections = 0
    for i in range(len(corrected)):
        value = ""
        j     = len(corrected[i])-1
        while j >= 0:
            if value != "":
                if corrected[i][j][0] == "_":
                    if corrected[i][j][1:] != value:
                        corrected[i][j] = u"_" + value
                        corrections += 1
                else:
                    if corrected[i][j][0] != "_" and corrected[i][j] != value:
                        corrected[i][j] = value
                        corrections += 1
                    value = ""
            elif corrected[i][j][0] == "_":
                value = corrected[i][j][1:]
            j -= 1
    return corrected

def is_relative_path(s):
    tmp = s.replace(u"\\", u"/")
    return tmp.startswith(u"../") or tmp.startswith(u"~/") or tmp.startswith(u"./")

def check_model_available(model, logger=None):
    if not os.path.exists(model):
        if os.path.exists(model + ".tar.gz"):
            if logger is not None:
                logger.info("Model not extracted, extracting %s" %(os.path.normpath(model + ".tar.gz")))
            with tarfile.open(model + ".tar.gz", "r:gz") as tar:
                tar.extractall(os.path.dirname(model))
        else:
            raise IOError("Cannot find model file: %s" %model)

def strip_html(html, keep_offsets=False):
    hs = re.compile(u"<h[1][^>]*?>.+?</h[0-9]>", re.M + re.U + re.DOTALL)
    paragraphs = re.compile(u"<p.*?>.+?</p>", re.M + re.U + re.DOTALL)
    # div_beg = re.compile(u"<div.*?>", re.M + re.U + re.DOTALL)
    # div_end = re.compile(u"</div>", re.M + re.U + re.DOTALL)
    # lis = re.compile(u"<li.*?>.+?</div>", re.M + re.U + re.DOTALL)
    
    parts = []
    s_e = []
    for finding in hs.finditer(html):
        s_e.append([finding.start(), finding.end()])
    for finding in paragraphs.finditer(html):
        s_e.append([finding.start(), finding.end()])
    s_e.sort(key=lambda x: (x[0], -x[1]))
    ref = s_e[0]
    i = 1
    while i < len(s_e):
        if ref[0] <= s_e[i][0] and s_e[i][1] <= ref[1]:
            del s_e[i]
            i -= 1
        elif ref[1] <= s_e[i][0]:
            ref = s_e[i]
        i += 1

    if keep_offsets:
        non_space = re.compile("[^ \n\r]")
        parts.append(u" " * s_e[0][0])
    else:
        non_space = re.compile("[^ \n\r]+")
    for i in range(len(s_e)):
        if i > 0:
            parts.append(non_space.sub(u" ", html[s_e[i-1][1] : s_e[i][0]]))
        parts.append(html[s_e[i][0] : s_e[i][1]])
    stripped_html = u"".join(parts)
    
    tag = re.compile("<.+?>", re.U + re.M + re.DOTALL)
    if keep_offsets:
        def repl(m):
            return u" " * (m.end() - m.start())
    else:
        repl = u""
    
    if keep_offsets:
        stripped_html = tag.sub(repl, stripped_html).replace("&nbsp;", u"      ").replace(u"&#160;", u"      ")
    else:
        stripped_html = tag.sub(repl, stripped_html).replace("&nbsp;", u" ").replace(u"&#160;", u" ")
    
    return stripped_html

def str2bool(s):
    s = s.lower()
    res = {"yes":True,"y":True,"true":True, "no":False,"n":False,"false":False}.get(s, None)
    if res is None:
        raise ValueError(u'Cannot convert to boolean: "%s"' %s)
    return res
