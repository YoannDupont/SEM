# -*- coding: utf-8 -*-

"""
file: importers.py

Description: import methods to handle file format to SEM format

author: Yoann Dupont
copyright (c) 2016 Yoann Dupont - all rights reserved

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import urllib
import re
import os.path
import codecs

try:
    from xml.etree import cElementTree as ET
except ImportError:
    from xml.etree import ElementTree as ET

try:
    from HTMLParser import HTMLParser
except ImportError:
    from html.parser import HTMLParser

from sem.storage import Corpus
from sem.storage import Document
from sem.storage import Tag, Annotation

def load(filename, encoding="utf-8", fields=None, word_field=None, wikinews_format=False):
    if filename.startswith("http"):
        return from_url(filename, wikinews_format=wikinews_format)
    
    if filename.endswith(".xml"):
        return sem_xml_file(filename)
    
    no_ext, ext = os.path.splitext(filename)
    if (ext == ".ann" and os.path.exists(no_ext+".txt")) or (ext == ".txt" and os.path.exists(no_ext+".ann")):
        return brat_file(filename, encoding=encoding)
    
    if fields is not None and word_field is not None:
        return conll_file(filename, fields, word_field, encoding=encoding)
    
    # this should be the last: if everything fail, just load as text document
    return text_file(filename, encoding=encoding)

def text_file(filename, encoding="utf-8"):
    return Document(os.path.basename(filename), content=codecs.open(filename, "rU", encoding).read().replace("\r",""), encoding=encoding)

def conll_file(filename, fields, word_field, encoding="utf-8"):
    document         = Document(os.path.basename(filename), encoding=encoding)
    document._corpus = Corpus.from_conll(filename, fields, encoding=encoding)
    character_index  = 0
    sentence_index   = 0
    contents         = []
    word_spans       = []
    sentence_spans   = []
    for sentence in document._corpus.sentences:
        contents.append([])
        for token in sentence:
            word = token[word_field]
            contents[-1].append(word)
            word_spans.append(Span(character_index, character_index+len(word)))
            character_index += len(word) + 1
        sentence_spans.append(Span(sentence_index, sentence_index+len(sentence)))
        sentence_index += len(sentence)
    document._content = u"\n".join([u" ".join(content) for content in contents])
    document.add_segmentation(Segmentation("tokens", spans=word_spans))
    document.add_segmentation(Segmentation("sentences", reference=document.segmentation("tokens"), spans=sentence_spans))
    return document

def from_url(url, wikinews_format=False):
    url = url.strip()
    
    if url == u"": return None
    
    charset = re.compile('charset="(.+?)"')
    escaped_url = u"".join([(urllib.quote(c) if ord(c) > 127 else c) for c in url.encode("utf-8")])
    #url = url.decode("iso-8859-1")
    url = url.replace(":","")
    
    content = u""
    f = urllib.urlopen(escaped_url)
    content = f.read()
    f.close()
    encoding = charset.search(content)
    if encoding is not None:
        encoding = encoding.group(1) or "utf-8"
    else:
        encoding = "utf-8"
    content = content.decode(encoding)
    
    regex = re.compile('^.+?[^/]/(?=[^/])', re.M)
    parts = regex.findall(escaped_url)
    base_url = (escaped_url[:]+u"/" if parts == [] else parts[0]).decode("iso-8859-1")
    
    content = content.replace(u'="//', u'="http://')
    content = content.replace(u'="/', u'="%s' %base_url)
    content = content.replace(u'=\\"//', u'=\\"http://')
    content = content.replace(u'=\\"/', u'=\\"%s' %base_url)
    content = content.replace(u'\r', u'')
    content = content.replace(u'</p>', u'</p>\n\n')
    
    hs = re.compile(u"<h[1][^>]*?>.+?</h[0-9]>", re.M + re.U + re.DOTALL)
    paragraphs = re.compile(u"<p.*?>.+?</p>", re.M + re.U + re.DOTALL)
    div_beg = re.compile(u"<div.*?>", re.M + re.U + re.DOTALL)
    div_end = re.compile(u"</div>", re.M + re.U + re.DOTALL)
    lis = re.compile(u"<li.*?>.+?</div>", re.M + re.U + re.DOTALL)
    
    parts = []
    s_e = []
    for finding in hs.finditer(content):
        s_e.append([finding.start(), finding.end()])
    for finding in paragraphs.finditer(content):
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

    non_space = re.compile("[^ \n\r]")
    parts.append(u" " * s_e[0][0])
    for i in range(len(s_e)):
        if i > 0:
            parts.append(non_space.sub(u" ", content[s_e[i-1][1] : s_e[i][0]]))
        parts.append(content[s_e[i][0] : s_e[i][1]])
    new_content = u"".join(parts)
    
    tag = re.compile("<.+?>", re.U + re.M + re.DOTALL)
    def repl(m):
        return u" " * (m.end() - m.start())
    
    new_content = tag.sub(repl, new_content).replace("&nbsp;", u"      ").replace(u"&#160;", u"      ")
    
    spaces = re.compile(" +")
    spaces_begin = re.compile("^ *", re.M)
    spaces_end = re.compile(" *$", re.M)
    newlines = re.compile("\n{2,}")
    cleaned_content = (new_content[ : content.index("<h2>")].strip() if wikinews_format else content)
    cleaned_content = cleaned_content.replace("\r", "")
    cleaned_content = spaces.sub(u" ", cleaned_content)
    cleaned_content = spaces_begin.sub("", cleaned_content)
    cleaned_content = spaces_end.sub("", cleaned_content)
    cleaned_content = newlines.sub("\n\n", cleaned_content)
    
    return Document(name=url, content=cleaned_content)

def sem_xml_file(xml):
    if type(xml) in (str, unicode):
        data = ET.parse(xml)
    elif isinstance(xml, ET.Tree):
        data = xml
    else:
        raise TypeError("Invalid type for loading XML-SEM document: %s" %(type(xml)))
    
    htmlparser = HTMLParser()
    root = data.getroot()
    document = Document(root.attrib.get("name", u"_DOCUMENT_"))
    for element in list(root):
        if element.tag == "metadata":
            document.metadata = element.attrib
        elif element.tag == "content":
            document.content = htmlparser.unescape(element.text)
        elif element.tag == "segmentations":
            for segmentation in list(element):
                spans = [Span(lb=int(span.attrib.get("start", span.attrib["s"])), ub=0, length=int(span.attrib.get("length", span.attrib["l"]))) for span in list(segmentation)]
                reference = segmentation.get(u"reference", None)
                if reference:
                    reference = document.segmentation(reference)
                document.add_segmentation(Segmentation(segmentation.attrib[u"name"], spans=spans, reference=reference))
        elif element.tag == "annotations":
            for annotation in list(element):
                tags = [Tag(lb=int(tag.attrib.get("start", tag.attrib["s"])), ub=0, length=int(tag.attrib.get("length", tag.attrib["l"])), value=tag.attrib.get(u"value",tag.attrib[u"v"])) for tag in list(annotation)]
                reference = annotation.get(u"reference", None)
                if reference:
                    reference = document.segmentation(reference)
                annotation = Annotation(annotation.attrib[u"name"], reference=reference)
                annotation.annotations = tags
                document.add_annotation(annotation)
    
    return document

def brat_file(filename, encoding="utf-8"):
    no_ext, ext = os.path.splitext(filename)
    txt_file = no_ext + ".txt"
    ann_file = no_ext + ".ann"
    if not (os.path.exists(txt_file) and os.path.exists(ann_file)):
        raise ValueError("missing either .ann or .txt file")
    
    document = Document(txt_file, encoding=encoding)
    document.content = codecs.open(txt_file, "rU", encoding).read().replace(u"\r", u"")
    annotations = Annotation("NER")
    for line in codecs.open(ann_file, "rU", encoding):
        line = line.strip()
        if line != u"" and line.startswith(u'T'):
            parts = line.split(u"\t")
            value, lb, ub = parts[1].split()
            lb = int(lb)
            ub = int(ub)
            annotations.append(Tag(lb=lb, ub=ub, value=value))
    document.add_annotation(annotations)
    
    return document