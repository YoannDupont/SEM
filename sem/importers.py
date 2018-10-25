# -*- coding: utf-8 -*-

"""
file: importers.py

Description: import methods to handle file format to SEM format

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

import urllib
import re
import os.path
import codecs
import sys

try:
    from xml.etree import cElementTree as ET
except ImportError:
    from xml.etree import ElementTree as ET

try:
    from HTMLParser import HTMLParser
except ImportError:
    from html.parser import HTMLParser

import sem.logger
import sem.misc
from sem.storage import Corpus
from sem.storage import Document, SEMCorpus
from sem.storage import Tag, Annotation
from sem.storage import Segmentation
from sem.storage import Span

def load(filename, encoding="utf-8", fields=None, word_field=None, wikinews_format=False, logger=None, strip_html=False, tagset_name=None, *args, **kwargs):
    if type(filename) in (Document, SEMCorpus):
        if logger is not None:
            logger.info(u"detected format: SEM XML")
        return filename
    
    try:
        filename = filename.decode(sys.getfilesystemencoding())
    except UnicodeDecodeError:
        pass
    except AttributeError: # AttributeError raised in python3 as it will be str
        pass
    
    if filename.startswith("http"):
        if logger is not None:
            logger.info(u"detected format: HTML")
        return from_url(filename, strip_html=strip_html, wikinews_format=wikinews_format)
    
    if filename.endswith(".xml"):
        xml = ET.parse(filename)
        root_tag = xml.getroot().tag
        if root_tag == "sem":
            if logger is not None:
                logger.info(u"detected format: SEM XML")
            return SEMCorpus.from_xml(xml)
        elif root_tag == "document":
            if logger is not None:
                logger.info(u"detected format: SEM XML")
            return Document.from_xml(xml)
        elif root_tag == "GateDocument":
            if logger is not None:
                logger.info(u"detected format: GATE XML")
            return gate_data(xml, os.path.basename(filename))
    
    no_ext, ext = os.path.splitext(filename)
    if (ext == ".ann") or (ext == ".txt" and os.path.exists(no_ext+".ann")):
        if logger is not None:
            logger.info(u"detected format: BRAT")
        return brat_file(filename, encoding=encoding, tagset_name=tagset_name)
    
    if fields is not None and word_field is not None:
        if logger is not None:
            logger.info(u"No specific format found, defaulting to text format")
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

def from_url(url, strip_html=False, wikinews_format=False):
    url = url.strip()
    
    if url == u"": return None
    
    try:
        url = url.decode(sys.getfilesystemencoding())
    except:
        pass
    
    strip_html |= wikinews_format # wikinews format is always stripped
    
    charset = re.compile('charset="(.+?)"')
    escaped_url = u"".join([(urllib.quote(c) if ord(c) > 127 else c) for c in url.encode("utf-8")])
    escaped_url = escaped_url.replace(u"%2525", u"%25")
    #url = url.decode("iso-8859-1")
    #url = url.replace(":","")
    
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
    content = content.replace(u'="/', u'="{0}'.format(base_url))
    content = content.replace(u'=\\"//', u'=\\"http://')
    content = content.replace(u'=\\"/', u'=\\"{0}'.format(base_url))
    content = content.replace(u'\r', u'')
    content = content.replace(u'</p>', u'</p>\n\n')
    
    if strip_html:
        new_content = sem.misc.strip_html(content, keep_offsets=True)
    else:
        new_content = content
    
    if wikinews_format:
        cleaned_content = new_content[ : content.index("<h2>")].strip()
    else:
        cleaned_content = new_content
    
    if strip_html:
        h = HTMLParser()
        empty_line = re.compile("\n[ \t]+")
        spaces = re.compile("[ \t]+")
        newlines = re.compile("\n{2,}")
        cleaned_content = h.unescape(cleaned_content)
        cleaned_content = empty_line.sub(u"\n", cleaned_content)
        cleaned_content = spaces.sub(u" ", cleaned_content)
        cleaned_content = newlines.sub("\n\n", cleaned_content)
    
    spaces_begin = re.compile("^[ \t]+", re.M)
    spaces_end = re.compile("[ \t]+$", re.M)
    cleaned_content = spaces_begin.sub("", cleaned_content)
    cleaned_content = spaces_end.sub("", cleaned_content)
    
    mime_type = ("text/plain" if strip_html else "text/html")
    return Document(name=url, content=cleaned_content, original_content=content, mime_type=mime_type)

def brat_file(filename, encoding="utf-8", tagset_name=None):
    tagset_name = tagset_name or "NER"
    no_ext, ext = os.path.splitext(filename)
    txt_file = no_ext + ".txt"
    ann_file = no_ext + ".ann"
    if not (os.path.exists(txt_file) and os.path.exists(ann_file)):
        raise ValueError("missing either .ann or .txt file")
    
    document = Document(os.path.basename(txt_file), encoding=encoding, mime_type="text/plain")
    document.content = codecs.open(txt_file, "rU", encoding).read().replace(u"\r", u"")
    annotations = Annotation(tagset_name)
    for line in codecs.open(ann_file, "rU", encoding):
        line = line.strip()
        if line != u"" and line.startswith(u'T'):
            parts = line.split(u"\t")
            value, bounds = parts[1].split(" ", 1)
            for bound in bounds.split(";"):
                lb, ub = bound.split()
                lb = int(lb)
                ub = int(ub)
                annotations.append(Tag(value=value, lb=lb, ub=ub))
    annotations.sort()
    document.add_annotation(annotations)
    
    return document

def gate_file(filename):
    data = ET.parse(filename)
    return gate_data(data, name=os.path.basename(filename))

def gate_data(data, name=None):
    document = Document(name or "__DOCUMENT__", mime_type="text/plain")
    
    textwithnodes = data.findall("TextWithNodes")[0]
    annotation_sets = data.findall("AnnotationSet")
    
    text_parts = [textwithnodes.text or u""]
    nodes = {}
    for node in list(textwithnodes):
        nodes[int(node.attrib["id"])] = sum([len(part) for part in text_parts])
        text_parts.append(node.tail or u"")
    document.content = u"".join(text_parts)
    
    annotations = []
    for annotation_set in annotation_sets:
        annotation_name = annotation_set.attrib["Name"]
        sem_annotation = Annotation(annotation_name)
        for annotation in annotation_set:
            lb = nodes[int(annotation.attrib["StartNode"])]
            ub = nodes[int(annotation.attrib["EndNode"])]
            sem_annotation.append(Tag(annotation.attrib["Type"], lb, ub))
        document.add_annotation(sem_annotation)
    
    return document

def json_data(data):
    document = Document(data.get(u"name", u"_DOCUMENT_"), content=data.get(u"content", u""))
    for key, value in data.get(u"metadatas", {}).items():
        document.add_metadata(key, value)
    
    for segmentation_name in data.get(u"segmentations", {}):
        d = data[u"segmentations"][segmentation_name]
        spans = [Span(lb=span[u"s"], ub=0, length=span[u"l"]) for span in d[u"spans"]]
        segmentation = Segmentation(segmentation_name, spans=spans, reference=d.get(u"reference", None))
        document.add_segmentation(segmentation)
    for segmentation in document.segmentations:
        if segmentation.reference is not None:
            segmentation.reference = document.segmentation(segmentation.reference)
    
    for annotation_name in data.get(u"annotations", {}):
        d = data[u"annotations"][annotation_name]
        annotations = [Tag(value=annotation[u"v"], lb=annotation[u"s"], ub=0, length=annotation[u"l"]) for annotation in d[u"annotations"]]
        annotation = Annotation(annotation_name, reference=document.segmentation(d[u"reference"]), annotations=annotations)
        document.add_annotation(annotation)
