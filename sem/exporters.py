# -*- coding: utf-8 -*-

"""
file: exporters.py

Description: some exporters for SEM documents

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

import html
import json

import sem.storage
from sem.storage import Segmentation
from sem.storage import Span
from sem.storage import (
    tag_annotation_from_sentence as get_pos,
    chunk_annotation_from_sentence as get_chunks,
)
import sem.logger

try:
    from xml.etree import cElementTree as ET
except ImportError:
    from xml.etree import ElementTree as ET


def add_text(node, text):
    parts = text.split("\n")
    node.text = parts[0]
    for i in range(1, len(parts)):
        br = ET.SubElement(node, "lb")
        br.tail = "\n{}".format(parts[1])


def add_tail(node, tail):
    parts = tail.split("\n")
    node.tail = parts[0]
    for i in range(1, len(parts)):
        br = ET.SubElement(node, "lb")
        br.tail = "\n{}".format(parts[1])


class Exporter:
    def __init__(self, *args, **kwargs):
        pass

    def document_to_file(self, document, couples, output, encoding="utf-8", **kwargs):
        """
        write the document to a file in the given export format.

        Parameters
        ----------
            document : Document
                the document to export
            couples : dict (string -> string)
                the "entry name" <=> "entry index" that allows to
                retrieve information to export.
                ex: couples = {"chunking":"C", "NER":"N"}
            output : str
                the name of the file to write into
        """
        to_write = self.document_to_unicode(document, couples, **kwargs)
        try:
            output.write(to_write)
        except AttributeError:
            with open(output, "w", encoding=encoding, newline="") as output_stream:
                output_stream.write(to_write)

    def document_to_data(self, document, couples, **kwargs):
        """
        creates a new variable representing the document in the given
        export format.

        Parameters
        ----------
            document : Document
                the document to export
            couples : dict (string -> string)
                the "entry name" <=> "entry index" that allows to
                retrieve information to export.
                ex: couples = {"chunking":"C", "NER":"N"}
        """
        raise NotImplementedError(
            "export_to_data not implemented for class {}".format(self.__class__)
        )

    def document_to_unicode(self, document, couples, **kwargs):
        raise NotImplementedError(
            'document_to_unicode is not implemented for {}'.format(self.__class__)
        )


class BratExporter(Exporter):
    extension = "ann"

    def __init__(self, *args, **kwargs):
        pass

    def document_to_unicode(self, document, couples, **kwargs):
        lowers = dict([(x.lower(), y) for (x, y) in couples.items()])
        if "ner" not in lowers and "NER" in document.annotationsets:
            lowers["ner"] = "NER"
        if "ner" not in lowers:
            sem.logger.exception("No NER annotation specified for BRAT exporter")
        if not document.annotationset(lowers["ner"]):
            sem.logger.exception("No annotation %s in document", lowers["ner"])
        content = document.content
        parts = []
        for id, annotation in enumerate(
            document.annotationset(lowers["ner"]).get_reference_annotations(), 1
        ):
            parts.append(
                "T{id}\t{annotation.value} {annotation.lb} {annotation.ub}\t{txt}".format(
                    id=id,
                    annotation=annotation,
                    txt=content[annotation.lb: annotation.ub].replace("\r", "").replace("\n", " "),
                )
            )
        return "\n".join(parts)


class CoNLLExporter(Exporter):
    extension = "conll"

    def __init__(self, *args, **kwargs):
        self.scheme = kwargs.get("scheme", "BIO")

    def document_to_unicode(self, document, couples, **kwargs):
        if len(document.corpus.fields) == 0:
            sem.logger.warning("No fields found for Corpus, cannot create string.")
            return ""

        if (
            not couples
            or (len(couples) == 0)
            or (len(couples) == 1 and list(couples.keys())[0].lower() in ["word", "token"])
        ):
            return str(document.corpus)
        else:
            lower = {}
            fields = []
            for field in couples:
                lower[field.lower()] = couples[field]

            if "word" in lower:
                fields.append(lower["word"])
            elif "token" in lower:
                fields.append(lower["token"])
            else:
                all_keys = document.corpus.fields
                field = (
                    "word" if "word" in all_keys
                    else "token" if "token" in all_keys
                    else sorted(document.corpus.fields)[0]
                )
                fields.append(field)

            if "pos" in lower:
                fields.append(lower["pos"])
            if "chunking" in lower:
                fields.append(lower["chunking"])
            if "ner" in lower:
                fields.append(lower["ner"])

            for field in fields:
                if field not in document.corpus:
                    sem.logger.warning('field "%s" not in corpus, adding', field)
                    document.add_to_corpus(field, scheme=self.scheme)

            return document.corpus.unicode(fields)

    def document_to_data(self, document, couples, **kwargs):
        return document.corpus.sentences


class GateExporter(Exporter):
    extension = "gate.xml"

    def __init__(self, *args, **kwargs):
        pass

    def document_to_unicode(self, document, couples, **kwargs):
        return '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n' \
               + ET.tostring(
                   self.document_to_data(document, couples),
                   encoding="utf-8"
                ).decode("utf-8")

    def document_to_data(self, document, couples, **kwargs):
        gateDocument = ET.Element("GateDocument")
        gateDocument.set("version", "3")
        gateDocumentFeatures = ET.SubElement(gateDocument, "GateDocumentFeatures")
        # feature 1 : gate.SourceURL
        feature1 = ET.SubElement(gateDocumentFeatures, "Feature")
        name1 = ET.SubElement(feature1, "Name")
        name1.set("className", "java.lang.String")
        name1.text = "gate.SourceURL"
        value1 = ET.SubElement(feature1, "Value")
        value1.set("className", "java.lang.String")
        value1.text = "created from String"
        # feature 2 : MimeType
        feature2 = ET.SubElement(gateDocumentFeatures, "Feature")
        name2 = ET.SubElement(feature2, "Name")
        name2.set("className", "java.lang.String")
        name2.text = "MimeType"
        value2 = ET.SubElement(feature2, "Value")
        value2.set("className", "java.lang.String")
        value2.text = "text/plain"
        # feature 3 : docNewLineType
        feature3 = ET.SubElement(gateDocumentFeatures, "Feature")
        name3 = ET.SubElement(feature3, "Name")
        name3.set("className", "java.lang.String")
        name3.text = "docNewLineType"
        value3 = ET.SubElement(feature3, "Value")
        value3.set("className", "java.lang.String")
        value3.text = ""

        # The text with anchors
        textWithNodes = ET.SubElement(gateDocument, "TextWithNodes")
        content = document.content
        if "ner" not in couples and "NER" in document.annotationsets:
            couples["ner"] = "NER"
        if "ner" in couples:
            annotationset = document.annotationset(couples["ner"])
            annotations = annotationset.get_reference_annotations()
            boundaries = set()
            for annotation in annotations:
                boundaries.add(annotation.lb)
                boundaries.add(annotation.ub)
            boundaries = sorted(boundaries)
        else:
            annotationset = None
            annotations = []
            boundaries = []

        if boundaries != []:
            textWithNodes.text = content[: boundaries[0]]
            for nth, boundary in enumerate(boundaries[:-1]):
                node = ET.SubElement(textWithNodes, "Node")
                node.set("id", str(boundary))
                node.tail = content[boundary: boundaries[nth+1]]
            node = ET.SubElement(textWithNodes, "Node")
            node.set("id", str(boundaries[-1]))
            node.tail = content[boundaries[-1]: len(content)]
        else:
            textWithNodes.text = content

        if annotations != []:
            id = 1
            typeAnnotationSet = ET.SubElement(gateDocument, "AnnotationSet")
            typeAnnotationSet.set("Name", annotationset.name)
            for annot in annotations:
                annotation = ET.SubElement(typeAnnotationSet, "Annotation")
                annotation.set("Id", str(id))
                annotation.set("Type", annot.value)
                annotation.set("StartNode", str(annot.lb))
                annotation.set("EndNode", str(annot.ub))
                id += 1

        return gateDocument


class HTMLInlineExporter(Exporter):
    extension = "html"

    def __init__(self, lang="fr", lang_style="default.css", *args, **kwargs):
        self._lang = lang
        self._lang_style = lang_style

    def document_to_unicode(self, document, couples, encoding="utf-8", **kwargs):
        entry_names = {}
        for entry in couples:
            entry_names[entry.lower()] = couples[entry]

        key = entry_names.get("ner", None)
        if key is None or document.annotationset(key) is None:
            key = entry_names.get("chunking", None)
        if key is None or document.annotationset(key) is None:
            key = entry_names.get("pos", None)
        if key is None or document.annotationset(key) is None:
            raise KeyError("Cannot find any annotation for export.")

        content = document.original_content[:]

        position2html = {}
        annotations = document.annotationset(key).get_reference_annotations()
        for annotation in reversed(annotations):
            lb = annotation.lb
            ub = annotation.ub
            value = annotation.value

            if ub not in position2html:
                position2html[ub] = []
            position2html[ub].insert(0, "</span>")
            if lb not in position2html:
                position2html[lb] = []
            position2html[lb].append('<span id="{0}" title="{0}">'.format(value))

        for index in reversed(sorted(position2html.keys())):
            content = content[:index] + "".join(position2html[index]) + content[index:]

        content = content.replace(
            "<head>", '<head>\n<link rel="stylesheet" href="{0}" />'.format(self._lang)
        )
        content = content.replace(
            "<head>", '<head>\n<link rel="stylesheet" href="{0}" />'.format(self._lang_style)
        )

        return content


class HTMLExporter(Exporter):
    extension = "html"

    def __init__(self, lang="fr", lang_style="default.css", *args, **kwargs):
        self._lang = lang
        self._lang_style = lang_style

    def escape_tokens(self, corpus, token_entry):
        """
        Returns a list of (HTML-)escaped token given a corpus and
        an entry where to find the tokens.
        """
        escaped = []
        for sentence in corpus:
            escaped.append([])
            for element in sentence:
                escaped[-1].append(html.escape(element[token_entry]))
        return escaped

    def make_escaped_content(self, document):
        content = document.content
        tokens = document.segmentation("tokens")
        escaped_tokens = [html.escape(content[token.lb: token.ub]) for token in tokens]
        escaped_nontokens = [
            html.escape(content[tokens[i].ub: tokens[i + 1].lb]) for i in range(len(tokens) - 1)
        ]
        escaped_nontokens.insert(0, html.escape(content[0: tokens[0].lb]))
        escaped_nontokens.append(html.escape(content[tokens[-1].ub: len(content)]))

        return escaped_tokens, escaped_nontokens

    def document_to_unicode(self, document, couples, encoding="utf-8", **kwargs):
        entry_names = {}
        for entry in couples:
            entry_names[entry.lower()] = couples[entry]

        pos_html = []
        chunk_html = []
        ner_html = []

        current_key = entry_names.get("pos", "POS")
        if current_key and current_key in document.annotationsets:
            pos_html = self.add_annotation_document(document, current_key)
        current_key = entry_names.get("chunking", entry_names.get("chunk", "chunking"))
        if current_key and current_key in document.annotationsets:
            chunk_html = self.add_annotation_document(document, current_key)
        current_key = entry_names.get("ner", "NER")
        if current_key and current_key in document.annotationsets:
            ner_html = self.add_annotation_document(document, current_key)

        return self.makeHTML_document(document, pos_html, chunk_html, ner_html, encoding)

    def add_annotation_document(self, document, column):
        annotations = document.annotationset(column).get_reference_annotations()[::-1]
        content = document.content

        parts = []
        last = len(content)
        for annotation in annotations:
            parts.append(
                html.escape(content[annotation.ub: last])
                .replace("\n", "<br />\n")
                .replace("\r<br />", "<br />\r")
            )
            parts.append("</span>")
            parts.append(
                html.escape(content[annotation.lb: annotation.ub])
                .replace("\n", "<br />\n")
                .replace("\r<br />", "<br />\r")
            )
            parts.append('<span id="{0}" title="{0}">'.format(annotation.value))
            last = annotation.lb
        parts.append(
            html.escape(content[0:last]).replace("\n", "<br />\n").replace("\r<br />", "<br />\r")
        )

        new_content = "".join(parts[::-1])
        return new_content

    def makeHTML_document(self, document, pos, chunk, ner, output_encoding):
        def checked(number):
            # whether the tab is checked or not
            if 1 == number:
                return ' checked="true"'
            else:
                return ""

        css_tabs = "tabs.css"
        css_lang = self._lang_style

        # header + div that will contain tabs
        html_page = [
            """<html>
    <head>
        <meta charset="{0}" />
        <title>{1}</title>
        <link rel="stylesheet" href="{2}" />
        <link rel="stylesheet" href="{3}" />
    </head>
    <body>
        <div class="wrapper">
            <h1>{4}</h1>
            <div class="tab_container">""".format(
                output_encoding, document.name, css_tabs, css_lang, document.name
            )
        ]

        # the annotations that will be outputted
        nth = 1
        annots = []

        #
        # declaring tabs in HTML. TODO: refactor duped code
        #

        if pos != []:
            html_page.append(
                """
                <input id="tab{0}" type="radio" name="tabs"{1} />
                <label for="tab{0}">Part-Of-Speech</label>""".format(
                    nth, checked(nth)
                )
            )
            annots.append(
                """
                <section id="content{0}" class="tab-content">
{1}
                </section>""".format(
                    nth, pos
                )
            )
            nth += 1

        if chunk != []:
            html_page.append(
                """
                <input id="tab{0}" type="radio" name="tabs"{1} />
                <label for="tab{0}">Chunking</label>""".format(
                    nth, checked(nth)
                )
            )
            annots.append(
                """
                <section id="content{0}" class="tab-content">
{1}
                </section>""".format(
                    nth, chunk
                )
            )
            nth += 1

        if ner != []:
            html_page.append(
                """
                <input id="tab{0}" type="radio" name="tabs"{1} />
                <label for="tab{0}">Named Entity</label>""".format(
                    nth, checked(nth)
                )
            )
            annots.append(
                """
                <section id="content{0}" class="tab-content">
{1}
                </section>""".format(
                    nth, ner
                )
            )
            nth += 1

        # annotations are put after the tab declarations
        for annot in annots:
            html_page.append(annot)

        # closing everything that remains to be closed
        html_page.append(
            """
            </div>
        </div>
    </body>
</html>
"""
        )

        return "".join(html_page)

    def document_to_data(self, document, couples, **kwargs):
        """
        returns an ElementTree object (ATM) of the HTML page.
        """
        return ET.ElementTree(
            ET.fromstring(
                self.document_to_unicode(
                    document, couples, encoding=kwargs.pop("encoding", "utf-8"), **kwargs
                )
            )
        )


class JSONExporter(Exporter):
    extension = "json"

    def __init__(self, *args, **kwargs):
        pass

    def document_to_unicode(self, document, couples, **kwargs):
        return json.dumps(
            self.document_to_data(document, couples, **kwargs), indent=2, ensure_ascii=False
        )

    def document_to_data(self, document, couples, **kwargs):
        """
        This is just creating a dictionary from the document.
        Nearly copy-pasta of the Document.unicode method.
        """

        json_dict = {}
        json_dict["name"] = document.name
        json_dict["content"] = document.content
        json_dict["metadatas"] = document.metadatas

        json_dict["segmentations"] = {}
        for seg in document.segmentations.values():
            json_dict["segmentations"][seg.name] = {}
            ref = seg.reference.name if isinstance(seg.reference, Segmentation) else seg.reference
            if ref:
                json_dict["segmentations"][seg.name]["reference"] = ref
            json_dict["segmentations"][seg.name]["spans"] = [
                {"s": span.lb, "l": len(span)} for span in seg.spans
            ]

        json_dict["annotations"] = {}
        for annotation in document.annotationsets.values():
            json_dict["annotations"][annotation.name] = {}
            reference = (
                ""
                if not annotation.reference
                else (
                    annotation.reference
                    if isinstance(annotation.reference, str)
                    else annotation.reference.name
                )
            )
            if reference:
                json_dict["annotations"][annotation.name]["reference"] = reference
            json_dict["annotations"][annotation.name]["annotations"] = [
                {"v": tag.value, "s": tag.lb, "l": len(tag)} for tag in annotation
            ]

        return json_dict


class SEMExporter(Exporter):
    extension = "sem.xml"

    def __init__(self, *args, **kwargs):
        pass

    def document_to_file(self, document, couples, output, encoding="utf-8", **kwargs):
        with open(output, "w", encoding=encoding) as output_stream:
            # both SEM documents and SEM corpora have their write method,
            # this allows to have only one exporter for both
            document.write(output_stream, add_header=True)

    def document_to_data(self, document, couples, **kwargs):
        """
        This is just creating a dictionary from the document.
        Nearly copy-pasta of the Document.unicode method.
        """

        return document


class AnalecTEIExporter(Exporter):
    extension = "analec.tei.xml"

    def __init__(self, *args, **kwargs):
        pass

    def document_to_unicode(self, document, couples, **kwargs):
        return '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n' + ET.tostring(
            self.document_to_data(document, couples), encoding="utf-8"
        ).decode("utf-8")

    def document_to_data(self, document, couples, **kwargs):
        teiCorpus = ET.Element("teiCorpus")
        teiCorpus.set("xmlns", "http://www.tei-c.org/ns/1.0")
        teiHeader = ET.SubElement(teiCorpus, "teiHeader")
        fileDesc = ET.SubElement(teiHeader, "fileDesc")
        titleStmt = ET.SubElement(fileDesc, "titleStmt")
        title = ET.SubElement(titleStmt, "title")
        title.text = ""
        respStmt = ET.SubElement(titleStmt, "respStmt")
        resp = ET.SubElement(respStmt, "resp")
        resp.text = ""
        name = ET.SubElement(respStmt, "name")
        name.text = ""
        publicationStmt = ET.SubElement(fileDesc, "publicationStmt")
        publisher = ET.SubElement(publicationStmt, "publisher")
        publisher.text = ""
        sourceDesc = ET.SubElement(fileDesc, "sourceDesc")
        sourceDesc.text = ""
        TEI = ET.SubElement(teiCorpus, "TEI")
        teiHeader = ET.SubElement(TEI, "teiHeader")
        teiHeader.text = ""
        titleStmt = ET.SubElement(fileDesc, "titleStmt")
        title = ET.SubElement(titleStmt, "title")
        title.text = ""
        respStmt = ET.SubElement(titleStmt, "respStmt")
        resp = ET.SubElement(respStmt, "resp")
        resp.text = ""
        name = ET.SubElement(respStmt, "name")
        name.text = ""
        publicationStmt = ET.SubElement(fileDesc, "publicationStmt")
        publisher = ET.SubElement(publicationStmt, "publisher")
        publisher.text = ""
        sourceDesc = ET.SubElement(fileDesc, "sourceDesc")
        sourceDesc.text = ""

        root = ET.SubElement(TEI, "text")
        body = ET.SubElement(root, "body")

        lower = {}
        for field in couples:
            lower[field.lower()] = couples[field]
        annotations = set(document.annotationsets.keys())
        field = None
        if len(couples) == 1:
            field = lower[sorted(lower.keys())[0]]
        else:
            field = lower.get("ner", None) if lower.get("ner", None) in annotations else None
            if field is None:
                field = (
                    lower.get("chunking", None)
                    if lower.get("chunking", None) in annotations
                    else None
                )
        if field is None:
            raise ValueError("Could not determine the field to use for TEI export.")

        content = document.content
        paragraphs = (
            document.segmentation("paragraphs").get_reference_spans()
            if document.segmentation("paragraphs") is not None
            else [Span(0, len(content))]
        )
        NEs = document.annotationset(field).get_reference_annotations()
        values = set([entity.value for entity in NEs])

        nth = dict([(value, 0) for value in values])
        for paragraph in paragraphs:
            entities = [
                entity for entity in NEs if entity.lb >= paragraph.lb and entity.ub <= paragraph.ub
            ]
            p = ET.SubElement(body, "p")
            if len(entities) == 0:
                p.text = content[paragraph.lb: paragraph.ub]
            else:
                p.text = content[paragraph.lb: entities[0].lb]
                for i, entity in enumerate(entities):
                    nth[entity.value] += 1
                    entity_start = ET.SubElement(
                        p,
                        "anchor",
                        {
                            "xml:id": "u-{0}-{1}-start".format(entity.value, nth[entity.value]),
                            "type": "AnalecDelimiter",
                            "subtype": "UnitStart",
                        },
                    )
                    entity_start.tail = content[entity.lb: entity.ub]
                    entity_end = ET.SubElement(
                        p,
                        "anchor",
                        {
                            "xml:id": "u-{0}-{1}-end".format(entity.value, nth[entity.value]),
                            "type": "AnalecDelimiter",
                            "subtype": "UnitEnd",
                        },
                    )
                    if i < len(entities) - 1:
                        entity_end.tail = content[entity.ub: entities[i + 1].lb]
                    else:
                        entity_end.tail = content[entity.ub: paragraph.ub]

        back = ET.SubElement(root, "back")
        for value in sorted(values):
            spanGrp = ET.SubElement(back, "spanGrp")
            spanGrp.set("type", "AnalecUnit")
            spanGrp.set("n", value)
            i = 0
            for entity in [ent for ent in NEs if ent.value == value]:
                i += 1
                ET.SubElement(
                    spanGrp,
                    "span",
                    {
                        "xml:id": "u-{0}-{1}".format(value, i),
                        "from": "#u-{0}-{1}-start".format(value, i),
                        "to": "#u-{0}-{1}-end".format(value, i),
                        "ana": "#u-{0}-{1}-fs".format(value, i),
                    },
                )

        fvLib = ET.SubElement(back, "fvLib")
        fvLib.set("n", "AnalecElementProperties")
        nth = dict([(value, 0) for value in values])
        for i, entity in enumerate(NEs):
            nth[entity.value] += 1
            ET.SubElement(
                fvLib, "fs", {"xml:id": "u-{0}-{1}-fs".format(entity.value, nth[entity.value])}
            )

        return teiCorpus


class TEINPExporter(Exporter):
    extension = "analec.tei.xml"

    def __init__(self, *args, **kwargs):
        pass

    def document_to_unicode(self, document, couples, encoding="utf-8", **kwargs):
        return '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n' + ET.tostring(
            self.document_to_data(document, couples), encoding="utf-8"
        ).decode("utf-8")

    def document_to_data(self, document, couples, **kwargs):
        teiCorpus = ET.Element("teiCorpus")
        teiCorpus.set("xmlns", "http://www.tei-c.org/ns/1.0")
        teiHeader = ET.SubElement(teiCorpus, "teiHeader")
        fileDesc = ET.SubElement(teiHeader, "fileDesc")
        titleStmt = ET.SubElement(fileDesc, "titleStmt")
        title = ET.SubElement(titleStmt, "title")
        title.text = ""
        respStmt = ET.SubElement(titleStmt, "respStmt")
        resp = ET.SubElement(respStmt, "resp")
        resp.text = ""
        name = ET.SubElement(respStmt, "name")
        name.text = ""
        publicationStmt = ET.SubElement(fileDesc, "publicationStmt")
        publisher = ET.SubElement(publicationStmt, "publisher")
        publisher.text = ""
        sourceDesc = ET.SubElement(fileDesc, "sourceDesc")
        sourceDesc.text = ""
        TEI = ET.SubElement(teiCorpus, "TEI")
        teiHeader = ET.SubElement(TEI, "teiHeader")
        teiHeader.text = ""
        titleStmt = ET.SubElement(fileDesc, "titleStmt")
        title = ET.SubElement(titleStmt, "title")
        title.text = ""
        respStmt = ET.SubElement(titleStmt, "respStmt")
        resp = ET.SubElement(respStmt, "resp")
        resp.text = ""
        name = ET.SubElement(respStmt, "name")
        name.text = ""
        publicationStmt = ET.SubElement(fileDesc, "publicationStmt")
        publisher = ET.SubElement(publicationStmt, "publisher")
        publisher.text = ""
        sourceDesc = ET.SubElement(fileDesc, "sourceDesc")
        sourceDesc.text = ""

        root = ET.SubElement(TEI, "text")
        body = ET.SubElement(root, "body")

        lower = {}
        for field in couples:
            lower[field.lower()] = couples[field]
        chunking_field = None
        try:
            chunking_field = lower["chunking"]
        except KeyError:
            message = (
                'No "chunking" field was found, please check you have'
                " chunking information in your pipeline."
            )
            sem.logger.exception(message)
            raise KeyError(message)

        content = document.content
        pronoun2analec = {
            "CL": "PR_CL",
            "CLO": "PR_CL_O",
            "CLR": "PR_CL_R",
            "CLS": "PR_CL_S",
            "PRO": "PR_PRO",
            "PROREL": "PR_REL",
            "PROWH": "PR_WH",
            "P+PRO": "PR_PP",
        }
        words = document.segmentation("tokens").get_reference_spans()
        paragraphs = document.segmentation("paragraphs").get_reference_spans() or Span(
            0, len(content)
        )
        np_chunks = [
            annotation
            for annotation in document.annotationset(chunking_field)
            if annotation.value == "NP"
        ]
        pos_tags = document.annotationset(lower["pos"])[:]
        pos = []
        for i in range(len(np_chunks)):
            chunk = np_chunks[i]
            pos.append(
                [annot for annot in pos_tags if annot.lb >= chunk.lb and annot.ub <= chunk.ub]
            )

        for i in range(len(np_chunks)):
            np_chunks[i].ub = words[np_chunks[i].ub - 1].ub
            np_chunks[i].lb = words[np_chunks[i].lb].lb

        nth = 0
        for paragraph in paragraphs:
            nps = [
                chunk
                for chunk in np_chunks
                if chunk.lb >= paragraph.lb and chunk.ub <= paragraph.ub
            ]
            p = ET.SubElement(body, "p")
            if len(nps) == 0:
                p.text = content[paragraph.lb: paragraph.ub]
            else:
                p.text = content[paragraph.lb: nps[0].lb]
                for i, np in enumerate(nps):
                    nth += 1
                    np_start = ET.SubElement(
                        p,
                        "anchor",
                        {
                            "xml:id": "u-MENTION-{0}-start".format(nth),
                            "type": "AnalecDelimiter",
                            "subtype": "UnitStart",
                        },
                    )
                    np_start.tail = content[np.lb: np.ub]
                    np_end = ET.SubElement(
                        p,
                        "anchor",
                        {
                            "xml:id": "u-MENTION-{0}-end".format(nth),
                            "type": "AnalecDelimiter",
                            "subtype": "UnitEnd",
                        },
                    )
                    if i < len(nps) - 1:
                        np_end.tail = content[np.ub: nps[i + 1].lb]
                    else:
                        np_end.tail = content[np.ub: paragraph.ub]

        back = ET.SubElement(root, "back")
        spanGrp = ET.SubElement(back, "spanGrp")
        spanGrp.set("type", "AnalecUnit")
        spanGrp.set("n", "MENTION")
        for i, np in enumerate(np_chunks):
            ET.SubElement(
                spanGrp,
                "span",
                {
                    "xml:id": "u-MENTION-{0}".format(i + 1),
                    "from": "#u-MENTION-{0}-start".format(i + 1),
                    "to": "#u-MENTION-{0}-end".format(i + 1),
                    "ana": "#u-MENTION-{0}-fs".format(i + 1),
                },
            )

        fvLib = ET.SubElement(back, "fvLib")
        fvLib.set("n", "AnalecElementProperties")
        for i, np in enumerate(np_chunks):
            value = pronoun2analec.get(pos[i][0].value, "GN")

            fs = ET.SubElement(fvLib, "fs", {"xml:id": "u-MENTION-{0}-fs".format(i + 1)})
            f = ET.SubElement(fs, "f")
            f.set("name", "REF")
            ET.SubElement(f, "string")

            f = ET.SubElement(fs, "f")
            f.set("name", "CODE_SEM")
            fstring = ET.SubElement(f, "string")
            fstring.text = value

            f = ET.SubElement(fs, "f")
            f.set("name", "CATEGORIE")
            fstring = ET.SubElement(f, "string")
            fstring.text = value

        return teiCorpus


class REDENTEIExporter(Exporter):
    extension = "reden.tei.xml"

    def __init__(self, *args, **kwargs):
        pass

    def document_to_unicode(self, document, couples, **kwargs):
        return '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n' + ET.tostring(
            self.document_to_data(document, couples), encoding="utf-8"
        ).decode("utf-8")

    def document_to_data(self, document, couples, **kwargs):
        TEI = ET.Element("TEI")
        TEI.set("xmlns", "http://www.tei-c.org/ns/1.0")
        lang = document.metadata("lang")
        if lang is not None:
            TEI.set("xml:lang", lang)
        teiHeader = ET.SubElement(TEI, "teiHeader")
        fileDesc = ET.SubElement(teiHeader, "fileDesc")
        titleStmt = ET.SubElement(fileDesc, "titleStmt")
        title = ET.SubElement(titleStmt, "title")
        title.text = ""
        respStmt = ET.SubElement(titleStmt, "respStmt")
        resp = ET.SubElement(respStmt, "resp")
        resp.text = ""
        name = ET.SubElement(respStmt, "name")
        name.text = ""
        publicationStmt = ET.SubElement(fileDesc, "publicationStmt")
        publisher = ET.SubElement(publicationStmt, "publisher")
        publisher.text = ""
        sourceDesc = ET.SubElement(fileDesc, "sourceDesc")
        sourceDesc.text = ""
        titleStmt = ET.SubElement(fileDesc, "titleStmt")
        title = ET.SubElement(titleStmt, "title")
        title.text = ""
        respStmt = ET.SubElement(titleStmt, "respStmt")
        resp = ET.SubElement(respStmt, "resp")
        resp.text = ""
        name = ET.SubElement(respStmt, "name")
        name.text = ""
        publicationStmt = ET.SubElement(fileDesc, "publicationStmt")
        publisher = ET.SubElement(publicationStmt, "publisher")
        publisher.text = ""
        sourceDesc = ET.SubElement(fileDesc, "sourceDesc")
        sourceDesc.text = ""

        root = ET.SubElement(TEI, "text")
        body = ET.SubElement(root, "body")
        div = ET.SubElement(body, "div")

        lower = {}
        for field in couples:
            lower[field.lower()] = couples[field]
        annotations = set(document.annotationsets.keys())
        field = None
        if len(couples) == 1:
            field = lower[sorted(lower.keys())[0]]
        else:
            field = lower.get("ner", None) if lower.get("ner", None) in annotations else None
            if field is None:
                field = (
                    lower.get("chunking", None)
                    if lower.get("chunking", None) in annotations
                    else None
                )
        if field is None:
            raise ValueError("Could not determine the field to use for TEI export.")

        content = document.content
        paragraphs = (
            document.segmentation("paragraphs").get_reference_spans()
            if document.segmentation("paragraphs") is not None
            else [Span(0, len(content))]
        )
        NEs = document.annotationset(field).get_reference_annotations()

        for paragraph in paragraphs:
            entities = [
                entity for entity in NEs if entity.lb >= paragraph.lb and entity.ub <= paragraph.ub
            ]
            p = ET.SubElement(div, "p")
            if len(entities) == 0:
                p.text = content[paragraph.lb: paragraph.ub]
            else:
                p.text = content[paragraph.lb: entities[0].lb]
                for i, entity in enumerate(entities):
                    entity_xml = ET.SubElement(p, entity.value)
                    entity_xml.text = content[entity.lb: entity.ub]
                    if i < len(entities) - 1:
                        entity_xml.tail = content[entity.ub: entities[i + 1].lb]
                    else:
                        entity_xml.tail = content[entity.ub: paragraph.ub]

        return TEI


class TextExporter(Exporter):
    extension = "txt"

    def __init__(self, *args, **kwargs):
        pass

    def document_to_unicode(self, document, couples, **kwargs):
        corpus = document.corpus

        lower = {}
        for field in couples:
            lower[field.lower()] = couples[field]

        if "word" in lower:
            token_field = lower["word"]
        elif "token" in lower:
            token_field = lower["token"]
        elif "word" in corpus:
            token_field = "word"
        elif "token" in corpus:
            token_field = "token"
        else:
            raise RuntimeError("Cannot find token field")

        data = []
        for sentence in corpus:
            tokens = sentence.feature(token_field)

            if "pos" in lower and lower["pos"] in corpus:
                for annotation in get_pos(sentence, lower["pos"]):
                    tokens[annotation.ub - 1] += "/{}".format(annotation.value)
                    # regrouping tokens for tags spanning over >2 tokens
                    for i in range(annotation.lb, annotation.ub - 1):
                        tokens[i + 1] = "{}{}{}".format(tokens[i], "_", tokens[i + 1])
                        tokens[i] = ""

            if "chunking" in lower and lower["chunking"] in corpus:
                for annotation in get_chunks(sentence, lower["chunking"]):
                    tokens[annotation.lb] = "({0} {1}".format(
                        annotation.value, tokens[annotation.lb]
                    )
                    tokens[annotation.ub - 1] = "{0} )".format(tokens[annotation.ub - 1])

            if "ner" in lower and lower["ner"] in corpus:
                for annotation in get_chunks(sentence, lower["ner"]):
                    tokens[annotation.lb] = "({0} {1}".format(
                        annotation.value, tokens[annotation.lb]
                    )
                    tokens[annotation.ub - 1] = "{0} )".format(tokens[annotation.ub - 1])

            # if regrouping tokens, some are empty and would generate superfluous spaces
            tokens = [token for token in tokens if token != ""]
            data.append(" ".join(tokens[:]))
        return "\n".join(data)

    def document_to_data(self, document, couples, **kwargs):
        return self.document_to_unicode(document, couples).split("\n")


__exporters = {
    "brat": BratExporter,
    "conll": CoNLLExporter,
    "gate": GateExporter,
    "html": HTMLExporter,
    "html_inline": HTMLInlineExporter,
    "jason": JSONExporter,
    "sem_xml": SEMExporter,
    "tei_analec": AnalecTEIExporter,
    "tei_reden": REDENTEIExporter,
    "tei_np": TEINPExporter,
    "text": TextExporter
}


def get_exporter(name):
    return __exporters[name.lower()]


def available_exporters():
    return sorted(__exporters.keys())
