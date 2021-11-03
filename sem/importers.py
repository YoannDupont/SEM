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

import glob
import pathlib
import urllib.parse
import urllib.request
import re
import sys

try:
    from xml.etree import cElementTree as ET
except ImportError:
    from xml.etree import ElementTree as ET

from html.parser import HTMLParser

import sem.logger
import sem.util
from sem.storage import Document, SEMCorpus, Corpus, Sentence
from sem.storage import Tag, AnnotationSet
from sem.storage import Segmentation
from sem.storage import Span
from sem.storage import tag_annotation_from_corpus, chunk_annotation_from_corpus


def load(
    filename,
    encoding="utf-8",
    fields=None,
    word_field=None,
    wikinews_format=False,
    strip_html=False,
    tagset_name=None,
    *args,
    **kwargs,
):
    """
    The swiss-knife loader. Guess the input format and load the file using the
    right importer.
    """

    if type(filename) in (Document, SEMCorpus):
        sem.logger.info("detected format: SEM XML")
        return filename

    filename = str(filename)  # may be Path
    if filename.startswith("http"):
        sem.logger.info("detected format: HTML")
        return from_url(filename, strip_html=strip_html, wikinews_format=wikinews_format)

    if filename.endswith(".xml"):
        xml = ET.parse(filename)
        root_tag = xml.getroot().tag
        if root_tag == "sem":
            sem.logger.info("detected format: SEM XML")
            return sem_corpus_from_xml(xml)
        elif root_tag == "document":
            sem.logger.info("detected format: SEM XML")
            return sem_document_from_xml(xml)
        elif root_tag == "GateDocument":
            sem.logger.info("detected format: GATE XML")
            return gate_data(xml, pathlib.Path(filename).name)

    path = pathlib.Path(filename)
    ext = path.suffix
    no_ext = str(path.parent / path.stem)
    if (ext == ".ann") or (ext == ".txt" and pathlib.Path(no_ext + ".ann").exists()):
        sem.logger.info("detected format: BRAT")
        return brat_file(
            filename,
            encoding=encoding,
            tagset_name=tagset_name,
            discontinuous=kwargs.get("discontinuous", "split")
        )

    if fields is not None and word_field is not None:
        sem.logger.info("No specific format found, trying CoNLL")
        return conll_file(
            filename,
            fields,
            word_field,
            encoding=encoding,
            taggings=kwargs.get('taggings'),
            chunkings=kwargs.get('chunkings')
        )

    sem.logger.info("No specific format found, defaulting to text format")
    # if everything else fails, just load as text document
    return text_file(filename, encoding=encoding)


def sem_document_from_xml(xml, chunks_to_load=None, load_subtypes=True, type_separator="."):
    if isinstance(xml, str):
        data = ET.parse(xml)
    elif isinstance(xml, ET.ElementTree):
        data = xml
    elif isinstance(xml, type(ET.Element("a"))):  # did not ind a better way to do this
        data = xml
    else:
        raise TypeError("Invalid type for loading XML-SEM document: {0}".format(type(xml)))

    if isinstance(data, ET.ElementTree):
        root = data.getroot()
    elif isinstance(data, type(ET.Element("a"))):
        root = data

    if root.tag == "sem":
        root = list(root)[0]
    elif root.tag != "document":
        raise TypeError("Invalid XML document type for XML-SEM document: {0}".format(root.tag))

    htmlparser = HTMLParser()
    document = Document(root.attrib.get("name", "_DOCUMENT_"))
    for element in list(root):
        if element.tag == "metadata":
            document._metadatas = element.attrib
        elif element.tag == "content":
            document.content = htmlparser.unescape(element.text)
        elif element.tag == "segmentations":
            for segmentation in list(element):
                spans = [
                    Span(
                        lb=int(span.attrib.get("start", span.attrib["s"])),
                        ub=0,
                        length=int(span.attrib.get("length", span.attrib["l"])),
                    )
                    for span in list(segmentation)
                ]
                reference = segmentation.get("reference", None)
                if reference:
                    reference = document.segmentation(reference)
                document.add_segmentation(
                    Segmentation(segmentation.attrib["name"], spans=spans, reference=reference)
                )
        elif element.tag == "annotations":
            for annotation in list(element):
                tags = []
                for tag in list(annotation):
                    value = tag.attrib.get("value", tag.attrib["v"])
                    if not load_subtypes:
                        value = value.strip(type_separator).split(type_separator)[0]
                    tags.append(
                        Tag(
                            value=value,
                            lb=int(tag.attrib.get("start", tag.attrib["s"])),
                            ub=0,
                            length=int(tag.attrib.get("length", tag.attrib["l"])),
                        )
                    )
                reference = annotation.get("reference", None)
                if reference:
                    reference = document.segmentation(reference)
                annotation = AnnotationSet(annotation.attrib["name"], reference=reference)
                annotation.annotations = tags
                document.add_annotationset(annotation)

    if document.segmentation("tokens") and document.segmentation("sentences"):
        document.corpus.from_segmentation(
            document.content,
            document.segmentation("tokens"),
            document.segmentation("sentences"),
        )

        if chunks_to_load is not None:
            for chunk_to_load in chunks_to_load:
                cur_annot = document.annotationset(chunk_to_load)
                if cur_annot and cur_annot.reference is None:
                    document.set_reference(cur_annot.name, "tokens")
                i = 0
                sent_iter = iter(document.corpus)
                shift = 0
                present = set([(a.lb, a.ub) for a in cur_annot])
                for sentence in document.segmentation("sentences"):
                    sent = next(sent_iter)
                    annots = []
                    while i < len(cur_annot) and cur_annot[i].ub <= sentence.ub:
                        annots.append(cur_annot[i])
                        if tuple([cur_annot[i].lb, cur_annot[i].ub]) not in present:
                            raise Exception
                        i += 1
                    l1 = ["O" for _ in range(len(sentence))]
                    for annot in annots:
                        l1[annot.lb - shift] = "B-{0}".format(annot.value)
                        for j in range(annot.lb + 1 - shift, annot.ub - shift):
                            l1[j] = "I-{}".format(annot.value)
                    for j in range(len(l1)):
                        sent[j]["NER"] = l1[j]
                    shift += len(sentence)
                document.corpus.fields.append(chunk_to_load)

    return document


def sem_corpus_from_xml(xml, chunks_to_load=None, load_subtypes=True, type_separator="."):
    if isinstance(xml, str):
        data = ET.parse(xml)
    elif isinstance(xml, ET.ElementTree):
        data = xml
    elif isinstance(xml, type(ET.Element("a"))):  # did not ind a better way to do this
        data = xml
    else:
        raise TypeError("Invalid type for loading XML-SEM document: {0}".format(type(xml)))

    root = data.getroot()
    if root.tag != "sem":
        raise ValueError("Not sem xml file type: '{0}'".format(root.tag))
    doc_list = []
    for document in list(root):
        doc_list.append(Document.from_xml(document))
    return SEMCorpus(doc_list)


def add_document(self, document):
    ok = not any([d.name == document.name for d in self.documents])
    if ok:
        self._documents.append(document)


def text_file(filename, encoding="utf-8"):
    """
    Read a text file.
    """
    with open(filename, "r", encoding=encoding, newline="") as input_stream:
        content = input_stream.read().replace("\r", "")

    return Document(
        pathlib.Path(filename).name,
        content=content,
        encoding=encoding,
    )


def read_conll(name, encoding, fields=None, cleaner=str.strip, splitter=str.split):
    """
    Iterate through a CoNLL-formatted file and provide sentences represented as
    either a list of list (if fields is None) or a list of dict (otherwise).
    """
    clean = cleaner or (lambda x: x)
    split = splitter or (lambda x: x)
    if fields:
        def to_data(x, y): return {key: val for key, val in zip(y, x)}
    else:
        def to_data(x, y): return {index: item for index, item in enumerate(x)}

    with open(name, "r", encoding=encoding, newline="") as input_stream:
        paragraph = []
        for line in input_stream:
            line = clean(line)
            if line != "":
                paragraph.append(split(line))
            elif paragraph != []:
                paragraph = [list(item) for item in zip(*paragraph)]
                yield Sentence(to_data(paragraph, fields))
                del paragraph[:]
        if paragraph != []:
            paragraph = [list(item) for item in zip(*paragraph)]
            yield Sentence(to_data(paragraph, fields))


def conll_file(filename, fields, word_field, encoding="utf-8", taggings=None, chunkings=None):
    """
    Read CoNLL-formatted text from a file.
    """
    name = pathlib.Path(filename).name
    sents = [sent for sent in read_conll(filename, encoding, fields)]
    fields = fields or sorted(sents[0].keys())  # no fields = we infer a "list" (dict with 0-index)
    if word_field is None:
        word_field = fields[0]
    return conll_data(
        name,
        Corpus(fields=fields, sentences=sents),
        word_field,
        encoding="utf-8",
        taggings=taggings,
        chunkings=chunkings
    )


def conll_data(name, corpus, word_field, encoding="utf-8", taggings=None, chunkings=None):
    """
    Create a Document from CoNLL-formatted data (SEM Corpus).
    """
    character_index = 0
    sentence_index = 0
    contents = []
    word_spans = []
    sentence_spans = []
    for sentence in corpus.sentences:
        contents.append(sentence.feature(word_field))
        for word in contents[-1]:
            word_spans.append(Span(character_index, character_index + len(word)))
            character_index += len(word) + 1
        sentence_spans.append(Span(sentence_index, sentence_index + len(sentence)))
        sentence_index += len(sentence)
    document = Document(
        name,
        content="\n".join([" ".join(content) for content in contents]),
        encoding=encoding,
        corpus=corpus
    )
    document.add_segmentation(Segmentation("tokens", spans=word_spans))
    document.add_segmentation(
        Segmentation(
            "sentences", reference=document.segmentation("tokens"), spans=sentence_spans[:]
        )
    )
    for tagging in taggings or []:
        document.add_annotationset(
            tag_annotation_from_corpus(
                document._corpus,
                tagging,
                tagging,
                reference=document.segmentation("tokens"),
                strict=True,
            )
        )
    for chunking in chunkings or []:
        document.add_annotationset(
            chunk_annotation_from_corpus(
                document._corpus,
                chunking,
                chunking,
                reference=document.segmentation("tokens"),
                strict=True,
            )
        )
    return document


def from_url(url, strip_html=False, wikinews_format=False, keep_offsets=True, **kwargs):
    """
    Load a SEM Document using an URL.

    Parameters
    ----------
    url : str
        The URL to use.
    strip_html : boolean [False]
        Do we strip the HTML from the document's content?
    wikinews_format : boolean [False]
        Do we use the wikinews format?
    **kwargs : kwargs
        other arguments
    """
    url = url.strip()

    if not url:
        return None

    strip_html |= wikinews_format  # wikinews format is always stripped
    keep_offsets &= not wikinews_format  # wikinews format never keeps offsets

    charset = re.compile(b'charset="(.+?)"')
    escaped_url = "".join([(urllib.parse.quote(c) if ord(c) > 127 else c) for c in url])
    escaped_url = escaped_url.replace("%2525", "%25")
    escaped_url = escaped_url.replace('"', "&quot;")

    content = ""
    f = urllib.request.urlopen(escaped_url)
    content = f.read()
    f.close()
    match = charset.search(content)
    if match is not None:
        encoding = match.group(1).decode("utf-8") or "utf-8"
    else:
        encoding = "utf-8"
    content = content.decode(encoding)

    regex = re.compile("^.+?[^/]/(?=[^/])", re.M)
    parts = regex.findall(escaped_url)
    base_url = (escaped_url[:] + "/" if parts == [] else parts[0])

    content = content.replace('="//', '="http://')
    content = content.replace('="/', '="{0}'.format(base_url))
    content = content.replace('=\\"//', '=\\"http://')
    content = content.replace('=\\"/', '=\\"{0}'.format(base_url))
    content = content.replace("\r", "")
    content = content.replace("</p>", "</p>\n\n")

    if strip_html:
        new_content = sem.util.strip_html(content, keep_offsets=keep_offsets)
    else:
        new_content = content

    if wikinews_format:
        cleaned_content = new_content[: content.index("<h2>")].strip()
    else:
        cleaned_content = new_content

    """if strip_html:
        h = HTMLParser()
        empty_line = re.compile("\n[ \t]+")
        spaces = re.compile("[ \t]+")
        newlines = re.compile("\n{2,}")
        cleaned_content = h.unescape(cleaned_content)
        cleaned_content = empty_line.sub("\n", cleaned_content)
        cleaned_content = spaces.sub(" ", cleaned_content)
        cleaned_content = newlines.sub("\n\n", cleaned_content)

    spaces_begin = re.compile("^[ \t]+", re.M)
    spaces_end = re.compile("[ \t]+$", re.M)
    cleaned_content = spaces_begin.sub("", cleaned_content)
    cleaned_content = spaces_end.sub("", cleaned_content)"""

    mime_type = "text/plain" if strip_html else "text/html"
    return Document(
        name=url, content=cleaned_content, original_content=content, mime_type=mime_type
    )


def brat_file(filename, encoding="utf-8", tagset_name=None, discontinuous="split"):
    """
    Load a BRAT file couple. A BRAT file couple is a ".txt" and a ".ann" file.
    If no name is provided for the annotation set, NER is used instead.

    Parameters
    ----------
    filename : str
        the path to the file.
    encoding : str ["utf-8"]
        the encoding of the file.
    tagset_name : str [None]
        the name of the annotation set to load.
    """
    tagset_name = tagset_name or "NER"
    path = pathlib.Path(filename)
    no_ext = str(path.parent / path.stem)
    txt_file = no_ext + ".txt"
    ann_file = no_ext + ".ann"
    if not (pathlib.Path(txt_file).exists() and pathlib.Path(ann_file).exists()):
        raise ValueError("missing either .ann or .txt file")

    document = Document(pathlib.Path(txt_file).name, encoding=encoding, mime_type="text/plain")
    document.content = open(txt_file, "r", encoding=encoding).read().replace("\r", "\n")
    annotations = AnnotationSet(tagset_name)
    for line in open(ann_file, "r", encoding=encoding, newline=""):
        line = line.strip()
        if line != "" and line.startswith("T"):
            parts = line.split("\t")
            value, bounds = parts[1].split(" ", 1)
            if discontinuous == "split":
                for bound in bounds.split(";"):
                    lb, ub = bound.split()
                    lb = int(lb)
                    ub = int(ub)
                    annotations.append(Tag(value=value, lb=lb, ub=ub))
            elif discontinuous == "merge":
                parts = bounds.split()
                lb = int(parts[0])
                ub = int(parts[-1])
                annotations.append(Tag(value=value, lb=lb, ub=ub))
            else:
                raise ValueError(
                    f'Invalid discontinuous annotation handling: "{discontinuous}" (split, merge)'
                )
    annotations.sort()
    document.add_annotationset(annotations)

    return document


def gate_file(filename):
    """
    Load a GATE-formatted file.

    Parameters
    ----------
    filename : str
        the path to the file to load.
    """
    data = ET.parse(filename)
    return gate_data(data, name=pathlib.Path(filename).name)


def gate_data(data, name=None):
    """
    Load a GATE-formatted ElementTree. GATE-formatted data contains the content
    and an annotation set. If no name is provided for the annotation set, NER
    is used instead.

    Parameters
    ----------
    data : str
        the GATE ELementTree to load as a SEM Document.
    name : str [None]
        the name of the annotation set to load.
    """
    document = Document(name or "__DOCUMENT__", mime_type="text/plain")

    textwithnodes = data.findall("TextWithNodes")[0]
    annotation_sets = data.findall("AnnotationSet")

    text_parts = [textwithnodes.text or ""]
    nodes = {}
    for node in list(textwithnodes):
        nodes[int(node.attrib["id"])] = sum([len(part) for part in text_parts])
        text_parts.append(node.tail or "")
    document.content = "".join(text_parts)

    for annotation_set in annotation_sets:
        annotation_name = annotation_set.attrib["Name"]
        sem_annotation = AnnotationSet(annotation_name)
        for annotation in annotation_set:
            lb = nodes[int(annotation.attrib["StartNode"])]
            ub = nodes[int(annotation.attrib["EndNode"])]
            sem_annotation.append(Tag(annotation.attrib["Type"], lb, ub))
        document.add_annotationset(sem_annotation)

    return document


def json_data(data):
    """
    Load Document from json data. The json is just a dict containing the right
    informations.

    Parameters
    ----------
    data : dict
        the json input data
    """
    document = Document(data.get("name", "_DOCUMENT_"), content=data.get("content", ""))
    for key, value in data.get("metadatas", {}).items():
        document.add_metadata(key, value)

    for segmentation_name in data.get("segmentations", {}):
        d = data["segmentations"][segmentation_name]
        spans = [Span(lb=span["s"], ub=0, length=span["l"]) for span in d["spans"]]
        segmentation = Segmentation(
            segmentation_name, spans=spans, reference=d.get("reference", None)
        )
        document.add_segmentation(segmentation)
    for segmentation in document.segmentations:
        if segmentation.reference is not None:
            segmentation.reference = document.segmentation(segmentation.reference)

    for annotation_name in data.get("annotations", {}):
        d = data["annotations"][annotation_name]
        annotations = [
            Tag(value=annotation["v"], lb=annotation["s"], ub=0, length=annotation["l"])
            for annotation in d["annotations"]
        ]
        annotation = AnnotationSet(
            annotation_name,
            reference=document.segmentation(d["reference"]),
            annotations=annotations,
        )
        document.add_annotationset(annotation)


def documents_from_list(name_list, file_format, **opts):
    """
    Create a Document list from a list which may contain either Document objects
    or string objects that need to be globbed.

    Parameters
    ----------
    name_list : list
        the list of "documents". It can be Document object or str with wildcards.
    file_format : str
        The expected file format for documents. Can be "plain", "conll",
        "guess", etc.
    **opts : dict
        options for reading documents.
    """
    documents = []
    names = set()  # document names that were already seen
    for name in name_list:
        if isinstance(name, Document):
            sem.logger.info("Reading %s", name.name)
            if name.name not in names:
                documents.append(name)
                names.add(name.name)
            else:
                sem.logger.info("document %s already found, not adding to the list.", name.name)
        else:
            name = str(name)
            for infile in glob.glob(name) or [name]:
                sem.logger.info("Reading %s", infile)
                if file_format == "text":
                    document = Document(
                        pathlib.Path(infile).name,
                        content=open(infile, "r", encoding="utf-8", newline="")
                        .read()
                        .replace("\r", ""),
                        **opts,
                    )
                elif file_format == "conll":
                    document = conll_file(infile, **opts)
                elif file_format == "html":
                    try:
                        infile = infile.decode(sys.getfilesystemencoding())
                    except Exception:
                        pass
                    document = from_url(infile, **opts)
                elif file_format == "guess":
                    document = load(infile, **opts)
                else:
                    raise ValueError("unknown format: {0}".format(file_format))
                if document.name not in names:
                    documents.append(document)
                    names.add(document.name)
                else:
                    sem.logger.info(
                        "document %s already found, not adding to the list.", document.name
                    )

    return documents
