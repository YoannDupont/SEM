# -*- coding: utf-8 -*-

"""
file: util.py

Description: a file for utilitarian functionalities.

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

import pathlib
import re
import tarfile

from contextlib import contextmanager
from io import open, StringIO

import sem.logger


def find_suggestions(target, candidates, case_sensitive=True):
    trgt = target if case_sensitive else target.lower()
    suggestions = []
    for candidate in candidates if case_sensitive else [cand.lower() for cand in candidates]:
        shortest = candidate if len(candidate) < len(trgt) else trgt
        longest = trgt if shortest == candidate else candidate
        if shortest in longest:
            suggestions.append(candidate)
    return suggestions


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

    for current_range in ranges.split(","):
        if ":" in current_range:
            lo, hi = [int(i) for i in current_range.split(":")]
        else:
            lo = int(current_range)
            hi = lo

        if hi < lo:
            continue

        if lo < 0:
            lo = length + lo
        if hi < 0:
            hi = length + hi

        for i in range(lo, hi + 1):
            result.add(i)

    if include_zero:
        result.add(0)

    return result


def correct_pos_tags(tags):
    """
    Correct POS tags following the "tag _tag" scheme to remove impossible transitions.
    """
    corrected = [[level2 for level2 in level1] for level1 in tags]
    corrections = 0
    for i in range(len(corrected)):
        value = ""
        j = len(corrected[i]) - 1
        while j >= 0:
            if value != "":
                if corrected[i][j][0] == "_":
                    if corrected[i][j][1:] != value:
                        corrected[i][j] = "_{}".format(value)
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


def check_model_available(model):
    path = pathlib.Path(model)
    if not path.exists():
        targz = pathlib.Path(str(path) + ".tar.gz")
        if targz.exists():
            sem.logger.info("Model not extracted, extracting {0}".format(str(targz.resolve())))
            with tarfile.open(targz, "r:gz") as tar:
                tar.extractall(targz.parent)
        else:
            raise FileNotFoundError("Cannot find model file: {0}".format(model))


def strip_html(html, keep_offsets=False):
    """
    Take an str containing HTML data and strip the HTML markup.

    Parameters
    ----------
    html : str
        the HTML data (str) to strip.
    keep_offsets : bool [False]
        if True, markups are replaced by spaces, otherwise replace by single space.
    """

    def replace_same_size(m):
        return " " * (m.end() - m.start())

    preprocessed_html = html[:]
    to_remove = []
    to_remove.append(re.compile("<script.*?>.+?</script>", re.M + re.U + re.DOTALL))
    to_remove.append(re.compile("<head>.+?</head>", re.M + re.U + re.DOTALL))
    to_remove.append(re.compile("<nav.*?>.+?</nav>", re.M + re.U + re.DOTALL))
    for remove in to_remove:
        preprocessed_html = remove.sub(replace_same_size, preprocessed_html)

    to_keep = []
    to_keep.append(re.compile("<h[1][^>]*?>.+?</h[0-9]>", re.M + re.U + re.DOTALL))
    to_keep.append(re.compile("<p.*?>.+?</p>", re.M + re.U + re.DOTALL))

    parts = []
    s_e = []
    for keep in to_keep:
        for finding in keep.finditer(html):
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
        parts.append(" " * s_e[0][0])
    else:
        non_space = re.compile("[^ \n\r]+")
    for i in range(len(s_e)):
        if i > 0:
            parts.append(non_space.sub(" ", preprocessed_html[s_e[i - 1][1]: s_e[i][0]]))
        parts.append(preprocessed_html[s_e[i][0]: s_e[i][1]])
    stripped_html = "".join(parts)

    tag = re.compile("<.+?>", re.U + re.M + re.DOTALL)
    repl = replace_same_size if keep_offsets else ""
    if keep_offsets:
        stripped_html = (
            tag.sub(repl, stripped_html).replace("&nbsp;", "      ").replace("&#160;", "      ")
        )
    else:
        stripped_html = tag.sub(repl, stripped_html).replace("&nbsp;", " ").replace("&#160;", " ")
        stripped_html = re.sub("\n[ \t]+", "\n", stripped_html)
        stripped_html = re.sub("[ \t]+", " ", stripped_html)
        stripped_html = re.sub("\n{2,}", "\n\n", stripped_html)

    return stripped_html


def str2bool(s):
    """
    Return a boolean value from string.

    Parameters
    ----------
    s : str
        the string value to convert to boolean.
    """

    s = s.lower()
    res = {"yes": True, "y": True, "true": True, "no": False, "n": False, "false": False}.get(
        s, None
    )
    if res is None:
        raise ValueError('Cannot convert to boolean: "{0}"'.format(s))
    return res


def longest_common_substring(a, b, casesensitive=True, lastchance=False):
    """
    A backtrack algorithm to find the best suited match between a long and
    a short form.
    It will generate a list of candidate solutions that have exactly the
    same number of matching tokens as the LCS algorithm found.

    """
    if len(a) < len(b):
        # left should be the longest sequence, but here right is.
        # We invert them so we do not have to deal with the mirroring of the checks.
        # However, in the end, the indexes will be switched between the two tokens,
        # so we put them back in place.
        return [
            [(y, x) for (x, y) in solution]
            for solution in longest_common_substring(b, a, casesensitive)
        ]
    if not casesensitive:
        # simple and dirty python to easily simulate case insensitivity.
        # Even though it works for most cases, it will not for some specific
        # unicode characters which I do not recall.
        return longest_common_substring(a.lower(), b.lower(), casesensitive=True)

    lengths = [[0 for j in range(len(b) + 1)] for i in range(len(a) + 1)]
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            if x == y:
                lengths[i + 1][j + 1] = lengths[i][j] + 1
            else:
                lengths[i + 1][j + 1] = max(lengths[i + 1][j], lengths[i][j + 1])

    solutions = set()

    def bcktrck(x, y, current):
        """
        The recursive algorithm that finds solutions by backtracking
        """
        if x == 0 or y == 0:
            if current == []:  # empty solution
                return
            if len(current) != lengths[-1][-1]:
                return

            z, t = current[0]
            # we start in the middle of a word of the long form
            if z > 0 and a[z - 1].isalpha():
                return
            # we do not take the first character of the short form
            if t != 0:
                return

            solutions.add(tuple(current))
            return
        if a[x - 1] == b[y - 1]:
            try:
                a_x2_ok = a[x - 2].isalpha()
            except Exception:
                a_x2_ok = False

            if current != []:
                if a[current[0][0] - 1].isalpha():
                    bcktrck(x - 1, y, current)
                    return
                # generated more than one token, and splitted one of them
                if " " in a[x - 1: current[0][0]].strip() and a_x2_ok:
                    bcktrck(x - 1, y, current)
                    return
            else:
                # we cut somewhere after a hyphen
                if "-" in a[x - 1:] and not a[x - 1] == "-":
                    if lengths[x - 1][y] == lengths[x][y]:
                        bcktrck(x - 1, y, current)
                    return
                # generated more than one token *and* splitted one of them
                if " " in a[x - 1:].strip() and (x > 1 and a_x2_ok):
                    if lengths[x - 1][y] == lengths[x][y]:
                        bcktrck(x - 1, y, current)
                    return

            bcktrck(x - 1, y - 1, [(x - 1, y - 1)] + current)
            if lengths[x][y] == lengths[x - 1][y]:
                bcktrck(x - 1, y, current)
            if lengths[x][y] == lengths[x][y - 1]:
                bcktrck(x, y - 1, current)
        elif lengths[x][y] == lengths[x - 1][y]:
            bcktrck(x - 1, y, current)
        elif lengths[x][y] == lengths[x][y - 1]:
            bcktrck(x, y - 1, current)

    try:
        bcktrck(len(a), len(b), [])
        return list(solutions)
    except RuntimeError:  # maximum recursion depth
        return []


@contextmanager
def r_open(source, encoding="utf-8"):
    """Open in read mode either a file from the filename or a string."""

    src = None
    try:
        src = open(source, "r", encoding=encoding, newline="")
    except Exception:
        try:
            s = source.decode(encoding)
        except UnicodeDecodeError:
            s = source
        except UnicodeEncodeError:
            s = source
        except AttributeError:
            s = source
        src = StringIO(s)
    finally:
        yield src
        try:
            src.close()
        except AttributeError:
            pass


def read_chunks(source, size=1024, encoding="utf-8"):
    """Read a source by chunks of a given size."""

    with r_open(source, encoding) as input_stream:
        buff = input_stream.read(size)
        while buff:
            yield buff
            buff = input_stream.read(size)
