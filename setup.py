# -*- coding: utf-8 -*-

"""
file: setup.py

Description: setup file for SEM.

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

from setuptools import setup, find_packages
from filecmp import dircmp
import os
import pathlib
import shutil
import platform
import sem

SYSTEM = platform.system().lower()
ON_WINDOWS = SYSTEM == "windows"


def diff_files(dcmp):
    def diff_files_rec(dcmp, missing, differents):
        right_only = dcmp.right_only
        diff_files = dcmp.diff_files
        for ro in right_only or []:
            missing.append(pathlib.Path(dcmp.right) / ro)
        for df in diff_files or []:
            differents.append(pathlib.Path(dcmp.right) / df)
        for sub_dcmp in dcmp.subdirs.values():
            diff_files_rec(sub_dcmp, missing, differents)

    missing = []
    differents = []
    diff_files_rec(dcmp, missing, differents)
    return missing, differents


validity = {"y": True, "ye": True, "yes": True, "n": False, "no": False}

#
# preparing SEM data
#

# overriding SEM data, if the user is OK with it.
usr_sem_data = pathlib.Path.home() / "sem_data"
already_exists = usr_sem_data.exists()
override = False
if already_exists:
    answer = input("\nsem_data already exists, override? [y/N] ").lower()
    override = validity.get(answer, False)

if override:
    try:
        shutil.rmtree(pathlib.Path.home() / "sem_data")
    except FileNotFoundError:
        pass

try:
    os.makedirs(pathlib.Path.home() / "sem_data")
except FileExistsError:
    pass

if override or not already_exists:
    try:
        shutil.copytree("./resources", pathlib.Path.home() / "sem_data" / "resources")
    except FileExistsError:
        pass
    try:
        shutil.copytree("./images", pathlib.Path.home() / "sem_data" / "resources" / "images")
    except FileExistsError:
        pass
    try:
        shutil.copytree("./non-regression", pathlib.Path.home() / "sem_data" / "non-regression")
    except FileExistsError:
        pass
else:
    # even if sem_data already exists, there may be some new files
    # the user would like to have.
    missing, differents = diff_files(dircmp(usr_sem_data / "resources", "resources"))
    if missing:
        print()
        print("The following files are missing:")
        print("\t" + " ".join(missing))
        answer = input("add missing files? [Y/n] ").lower()
        add_missing = validity.get(answer, True)
        if add_missing:
            for filename in missing:
                dest = usr_sem_data / filename
                if pathlib.Path(filename).is_dir():
                    shutil.copytree(filename, dest)
                else:
                    shutil.copy(filename, dest)
    if differents:
        print()
        print("The following files are differents:")
        print("\t" + " ".join(str(diff) for diff in differents))
        answer = input("overwritte different files? [Y/n] ").lower()
        overwritte = validity.get(answer, True)
        if overwritte:
            for filename in differents:
                dest = usr_sem_data / filename
                if pathlib.Path(filename).is_dir():
                    shutil.copytree(filename, dest)
                else:
                    shutil.copy(filename, dest)

#
# launching setup
#

setup(
    name="SEM",
    description="SEM tool for text annotation",
    long_description="SEM is a free NLP tool relying on Machine Learning technologies,"
    " especially CRFs."
    " SEM provides powerful and configurable preprocessing and postprocessing.",
    license="MIT",
    author="Yoann Dupont",
    author_email="yoa.dupont@gmail.com",
    maintainer="Yoann Dupont",
    maintainer_email="yoa.dupont@gmail.com",
    version=sem.version(),
    keywords=[
        "natural language processing",
        "machine learning",
        "tagging",
        "part-of-speech tagging",
        "chunking",
        "named entity recognition",
    ],
    packages=find_packages(),
    include_package_data=True,
    entry_points={"console_scripts": ["sem = sem.__main__:main"]},
)
