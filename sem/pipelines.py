# -*- coding: utf-8 -*-

"""
file: pipeline.py

Description: a file for basic stuff related to pipelines. This file was
created to workaround a cycle dependency between 'sem.util' and 'sem.processors'
when trying to move the 'load_workflow' method in the 'sem.util' module.

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
import dill
import configparser
import warnings

try:
    from xml.etree import cElementTree as ET
except ImportError:
    from xml.etree import ElementTree as ET

import sem.logger
import sem.processors
from sem.util import check_model_available


class Pipeline(sem.processors.Processor):
    """A pipeline. It will basically chain processors. We will consider that a
    pipeline is a kind of processor since it will do basically the same job.
    It will make everything more pluggable.
    """

    def __init__(self, pipes, pipeline_mode="all", **kwargs):
        super(Pipeline, self).__init__(**kwargs)

        self._pipes = pipes
        self.pipeline_mode = pipeline_mode

    def __iter__(self):
        for pipe in self._pipes:
            yield pipe

    def __len__(self):
        return len(self._pipes)

    def __getitem__(self, index):
        return self._pipes[index]

    @property
    def pipes(self):
        return self._pipes

    def append(self, pipe):
        self._pipes.append(pipe)

    def remove(self, pipe):
        self._pipes.remove(pipe)

    def process_document(self, document, **kwargs):
        for pipe in self._pipes:
            if pipe.check_mode(self.pipeline_mode):
                pipe.process_document(document, **kwargs)
            else:
                sem.logger.info("pipe %s not executed", pipe)
        return document  # allows multiprocessing


def load_workflow(workflow, force_format="default", pipeline_mode="all"):
    """Load a SEM workflow from a file.

    Parameters
    ----------
    workflow : str
        the path to the file.
    force_format : str ["default"]
        if "default", use the normal format defined in workflow file. Otherwise,
        use force_format.
    """

    tree = ET.parse(str(pathlib.Path(workflow).resolve()))
    root = tree.getroot()
    xmlpipes, xmloptions = list(root)

    options = configparser.RawConfigParser()
    exporter = None
    couples = {}
    for xmloption in xmloptions:
        section = xmloption.tag
        options.add_section(section)
        attribs = {}
        for key, val in xmloption.attrib.items():
            key = key.replace("-", "_")
            try:
                attribs[key] = sem.util.str2bool(val)
            except ValueError:
                attribs[key] = val
        for key, val in attribs.items():
            options.set(section, key, val)
        if xmloption.tag == "export":
            couples = dict(options.items("export"))
            export_format = couples["format"]
            if force_format is not None and force_format != "default":
                sem.logger.info("using forced format: {0}".format(force_format))
                export_format = force_format
            exporter = sem.exporters.get_exporter(export_format)(**couples)

    pipes = []
    for xmlpipe in xmlpipes:
        if xmlpipe.tag == "export":
            continue

        arguments = {}
        arguments["expected_mode"] = pipeline_mode
        for key, value in xmlpipe.attrib.items():
            path = pathlib.Path(value)
            user_path = path.expanduser()
            if path != user_path:  # path startswith "~"
                value = str(user_path)
            elif str(path).startswith("../") or str(path).startswith("./"):
                value = str((pathlib.Path(workflow).parent / path).resolve())
            arguments[key.replace("-", "_")] = value
        if list(xmlpipe):
            subpipes = list(xmlpipe)
            for pipe in subpipes:
                path = pipe.attrib.get("path")
                if path and path.startswith("../") or path.startswith("./"):
                    pipe.attrib["path"] = str((pathlib.Path(workflow).parent / path).resolve())
                if pipe.attrib.get("priority", "top-down") == "top-down":
                    subpipes = subpipes[::-1]
            arguments["xmllist"] = subpipes
        for section in options.sections():
            if section == "export":
                continue
            for key, value in options.items(section):
                if key not in arguments:
                    arguments[key] = value
                else:
                    sem.logger.warning("Not adding already existing option: {0}".format(key))
        sem.logger.info("loading {0}".format(xmlpipe.tag))
        pipes.append(sem.processors.build_processor(xmlpipe.tag, **arguments))
    pipeline = Pipeline(pipes, pipeline_mode=pipeline_mode)

    return pipeline, options, exporter, couples


def load_pipeline(path, auto_download=True):
    warnings.filterwarnings("always", category=DeprecationWarning)
    warnings.warn("'load_pipeline' is deprecated, use 'load' instead", DeprecationWarning)
    warnings.filterwarnings("default", category=DeprecationWarning)
    return load(path, auto_download=auto_download)


def load(path, auto_download=True):
    """Load a serialized (potentially .tar.gz) pipeline.
    Pipelines are serialized using dill.
    If the pipeline does not exist and auto_download is set to True,
    SEM will attempt to download the pipeline and load it.

    Parameters
    ----------
    path : str or pathlib.Path
        The path (relative or absolute) to the pipeline.
        SEM will look for the file in the following folders:
        "." and sem.PIPELINE_DIR (defined in sem.__init__.py)
    auto_download : Boolean (default: True)
        Download the pipeline if not found on the computer.

    Returns
    -------
    sem.pipeline.Pipeline
        A SEM pipeline ready to process some documents.
    """
    def download_pipeline(path):
        import os
        import urllib.request

        outfile_path = sem.SEM_PIPELINE_DIR / path.with_suffix(".tar.gz")
        url = sem.SEM_RESOURCE_BASE_URL.format(
            branch="main", kind="pipelines", name=str(path), extension=".tar.gz"
        )
        sem.logger.info("downloading %s...", url)
        response = urllib.request.urlopen(url)
        data = response.read()
        try:
            os.makedirs(outfile_path.parent)
        except FileExistsError:
            pass
        with open(outfile_path, "wb") as output_stream:
            output_stream.write(data)

    path = pathlib.Path(path)
    pipeline = None
    for folder in [pathlib.Path(), sem.SEM_PIPELINE_DIR]:
        actual_path = folder / path
        try:
            check_model_available(actual_path)
            sem.logger.info("Loading %s", str(actual_path))
            with open(actual_path, "rb") as input_stream:
                pipeline = dill.load(input_stream)
        except FileNotFoundError:
            pass

    if pipeline is None:
        if auto_download:
            download_pipeline(path)
            actual_path = sem.SEM_PIPELINE_DIR / path
            check_model_available(actual_path)  # extract if need be
            sem.logger.info("Loading %s", str(actual_path))
            with open(actual_path, "rb") as input_stream:
                pipeline = dill.load(input_stream)
        else:
            raise FileNotFoundError("Could not find pipeline {}".format(path))

    return pipeline


def save(pipeline, path, mode="w"):
    with open(path, f"{mode}b") as output_stream:
        dill.dump(pipeline, output_stream)


def save_pipeline(pipeline, path):
    warnings.filterwarnings("always", category=DeprecationWarning)
    warnings.warn("'save_pipeline' is deprecated, use 'save' instead", DeprecationWarning)
    warnings.filterwarnings("default", category=DeprecationWarning)
    save(pipeline, path)
