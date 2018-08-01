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

#
# Chunking flags.
#
    
BEGIN  = "B"  # begin flags
IN     = "I"  # in flags
LAST   = "LE" # end flags
SINGLE = "US" # single flags
OUT    = "O"

#
# Some useful constants for tries.
#

NUL = u""

#
# Some useful regular expressions.
#

# see: http://www.ietf.org/rfc/rfc1738.txt
# URLs recognition. Validating URL is both hard and all urls may not be
# valid when analysing textual information. Hence, validity checking is
# kept to bare minimum, covering being more important.
protocol = u"(?:http|ftp|news|nntp|telnet|gopher|wais|file|prospero)"
mailto   = u"mailto"
url_body = u"\S+[0-9A-Za-z/]"
url      = u"<?(?:{0}://|{1}:|www\.){2}>?".format(protocol, mailto, url_body)
url_re   = re.compile(url, re.I)

# email addresses recognition. See URLs.
localpart_border = u"[A-Za-z0-9!#$%&'*+\-/=?^_`{|}~]"
localpart_inside = u"[A-Za-z0-9!#$%&'*+\-/=?^_`{|}~.]"
localpart        = u"{0}{1}*".format(localpart_border, localpart_inside)
subdomain_start  = u"[A-Za-z]"
subdomain_inside = u"[A-Za-z0-9\\-]"
subdomain_end    = u"[A-Za-z0-9]"
subdomain        = u"{0}{1}*{2}".format(subdomain_start, subdomain_inside, subdomain_end)
domain           = u"{0}(?:\\.{1})*".format(subdomain, subdomain)
email_str        = u"{0}@{1}".format(localpart, domain)
email_re         = re.compile(email_str)
