# -*- coding: utf-8 -*-

"""
file: download.py

Description: Download a SEM resource from GitHub.

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

import argparse
import os
import pathlib
import tarfile
import urllib.request

import sem
import sem.misc
import sem.logger


# __BASE_URL = (
#     "https://raw.githubusercontent.com/YoannDupont/SEM-resources/{branch}/{kind}/{name}{extension}"
# )

__kind2name = {
    "dictionary": "dictionaries",
    "master": "master",
    "model": "models",
    "pipeline": "pipelines",
    "tagset": "tagsets",
}


def main(argv=None):
    download(parser.parse_args(argv))


def download(args):
    """Download a SEM resource from GitHub."""

    log_lvl = sem.logger.level
    sem.logger.setLevel("INFO")

    name = args.name
    kind = __kind2name[args.kind]
    extension = args.extension
    branch = args.branch
    encoding = args.encoding
    output_dir = args.output_dir
    binary_or_text = args.binary_or_text
    extract = args.extract

    relative_path = pathlib.Path(f"{kind}/{name}{extension}")
    outfile_path = pathlib.Path(output_dir) / relative_path

    if outfile_path.exists():
        answer = input(f"{outfile_path} already exists, overwrite? [y/N] ").lower()
        try:
            overwrite = sem.misc.str2bool(answer)
        except ValueError:
            overwrite = False
        if not overwrite:
            return
    else:
        try:
            os.makedirs(outfile_path.parent)
        except FileExistsError:
            pass

    url = sem.SEM_RESOURCE_BASE_URL.format(
        branch=branch, kind=kind, name=name, extension=extension
    )
    sem.logger.info("downloading %s...", url)
    response = urllib.request.urlopen(url)
    data = response.read()
    if binary_or_text == "guess":
        binarytext = ("b" if extension in ["", ".tar.gz"] else "t")
    else:
        binarytext = binary_or_text
    if binarytext == "t":
        data = str(data, encoding)

    with open(outfile_path, "w{}".format(binarytext)) as output_stream:
        output_stream.write(data)

    if extract and extension == ".tar.gz":
        sem.logger.info("extracting %s...", outfile_path)
        with tarfile.open(outfile_path, "r:gz") as tar:
            tar.extractall(outfile_path.parent)

    sem.logger.setLevel(log_lvl)


parser = argparse.ArgumentParser("Download a SEM resource from GitHub.")

parser.add_argument("name", help="The name of the resource (example: fr/FTB-NER)")
parser.add_argument(
    "-k",
    "--kind",
    choices=sorted(__kind2name.keys()),
    default="pipeline",
    help="The kind of resource to download (default: %(default)s)"
)
parser.add_argument(
    "-b",
    "--branch",
    default="main",
    help="The branch from which to download (default: %(default)s)"
)
parser.add_argument(
    "-t",
    "--extension",
    default=".tar.gz",
    help="The extension of the file you want to download (default: %(default)s)"
)
parser.add_argument(
    "-o",
    "--output_dir",
    default=sem.SEM_RESOURCE_DIR,
    help="The base folder where to download the resource (default: %(default)s)"
)
parser.add_argument(
    "-e", "--encoding",
    default="UTF-8",
    help="Encoding of the output file, if non binary (default: %(default)s)",
)
parser.add_argument(
    "--binary-or-text",
    choices=("b", "t", "guess"),
    default="guess",
    help="Is the file a binary, a text or should the program guess? (default: %(default)s)"
)
parser.add_argument(
    "-x",
    "--extract",
    action="store_true",
    help="If the resource is an archive, extract it (default: %(default)s)"
)
