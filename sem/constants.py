# -*- coding: utf-8 -*-

"""
file: constants.py

Description: some useful constants that could be of some use in SEM and
beyond.

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
import pathlib

#
# SEM related constants
#

SEM_DATA_DIR = pathlib.Path.home() / "sem_data"
SEM_RESOURCE_DIR = pathlib.Path(SEM_DATA_DIR) / "resources"
SEM_PIPELINE_DIR = SEM_RESOURCE_DIR / "pipelines"
SEM_HOMEPAGE = "http://www.lattice.cnrs.fr/sites/itellier/SEM.html"
SEM_RESOURCE_BASE_URL = (
    "https://raw.githubusercontent.com/YoannDupont/SEM-resources/{branch}/{kind}/{name}{extension}"
)

#
# Chunking flags.
#

BEGIN = "B"  # begin flags
IN = "I"  # in flags
LAST = "LE"  # end flags
SINGLE = "US"  # single flags
OUT = "O"

chunking_schemes = {
    "BIO": {"begin": "B", "in": "I", "last": "I", "single": "B", "out": "O"},
    "BILOU": {"begin": "B", "in": "I", "last": "L", "single": "U", "out": "O"},
    "BIOES": {"begin": "B", "in": "I", "last": "E", "single": "S", "out": "O"},
}

#
# Some useful constants for tries.
#

NUL = ""

#
# Some useful regular expressions.
#

# see: http://www.ietf.org/rfc/rfc1738.txt
# URLs recognition. Validating URL is both hard and all urls may not be
# valid when analysing textual information. Hence, validity checking is
# kept to bare minimum, covering being more important.
protocol = r"(?:http|ftp|news|nntp|telnet|gopher|wais|file|prospero)"
mailto = r"mailto"
url_body = r"\S+[0-9A-Za-z/]"
url = r"<?(?:{0}://|{1}:|www\.){2}>?".format(protocol, mailto, url_body)
url_re = re.compile(url, re.I)

# email addresses recognition. See URLs.
localpart_border = r"[A-Za-z0-9!#$%&'*+\-/=?^_`{|}~]"
localpart_inside = r"[A-Za-z0-9!#$%&'*+\-/=?^_`{|}~.]"
localpart = f"{localpart_border}{localpart_inside}*"
subdomain_start = r"[A-Za-z]"
subdomain_inside = r"[A-Za-z0-9\\-]"
subdomain_end = r"[A-Za-z0-9]"
subdomain = f"{subdomain_start}{subdomain_inside}*{subdomain_end}"
domain = rf"{subdomain}(?:\.{subdomain})*"
email_str = rf"{localpart}@{domain}"
email_re = re.compile(email_str)
