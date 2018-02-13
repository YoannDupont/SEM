#-*- encoding: utf-8-*-

"""
file: __init__.py

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

import sys
import os.path
import argparse

from os.path import dirname, abspath, join, expanduser

SEM_HOME = dirname(abspath(__file__)).decode(sys.getfilesystemencoding())
SEM_DATA_DIR = join(expanduser(u"~"), u"sem_data")
SEM_RESOURCE_DIR = join(SEM_DATA_DIR, u"resources")
SEM_EXT_DIR = join(SEM_DATA_DIR, u"ext")
SEM_HOMEPAGE = u"http://www.lattice.cnrs.fr/sites/itellier/SEM.html"
argument_parser = argparse.ArgumentParser()
argument_subparsers = argument_parser.add_subparsers()

_name = u"SEM"
u"""
The name of the software. Obviously, it is SEM.
"""

_version_major = 3
u"""
The major version number.
Is only incremented when deep changes (that usually lead to a change of how the whole software is used) are made to the program.
Such changes include various feature additions / deletions / modifications, source code reorganisation and so on.
On a more NLP side, such changes could also include a change in corpora used in learning (if going from proprietary to free for example).
If this number is incremented, _version_minor and _version_patch are to be reseted to 0.
"""

_version_minor = 0
u"""
The minor version number.
Is only incremented when medium changes are made to the program.
Such changes include feature addition / deletion, creation of a new language entry for manual.
If this number is incremented, _version_patch is to be reseted to 0.
"""

_version_patch = 0
u"""
The patch version number.
Is only incremented when shallow changes are made to the program.
Such changes include bug correction, typo correction and any modification to existing manual(s) are made.
On a more NLP side, such changes would also include model changes.
"""

_main_features = [
                    [u"A GUI for easier use (requires TkInter)",
                        [
                            u'on Linux: double-clic on sem_gui.sh',
                            u'on Windows: double-clic on sem_gui.bat',
                            u'from temrinal: run ```python -m sem gui```',
                        ]
                    ],
                    [u"segmentation",
                        [
                            u"segmentation for: French, English",
                            u"easy creation and integration of new tokenisers"
                        ]
                    ],
                    [
                        u"feature generation", 
                        [
                            u"XML file to write features without coding them",
                            u"single-token and multi-token dictionary features",
                            u"Regular expression features",
                            u"sequenced features",
                            u"train/label mode",
                            u"display option for features that are useful for generation, but not needed in output"
                        ]
                    ],
                    [u"exporting output",
                        [
                            u"supported export formats: CoNLL, text, HTML (from plain text), two XML-TEI (one specific to NP-chunks and another one for the rest)",
                            u"easy creation and integration of new exporters"
                        ]
                    ],
                    [u"extension of existing features",
                        [
                            u"automatic integration of new segmenters and exporters",
                            u"semi automatic integration of new feature functions",
                            u"easy creation of new CSS formats for HTML exports"
                        ]
                    ]
                  ]

_first_steps = [
                    [u"install SEM",
                        [
                            u"run ```python setup.py install --user``` to install SEM. It will compile Wapiti and create necessary directories. Currently, SEM datas are located in ```~/sem_data```",
                            u'on Windows, Wapiti compilation may fail. Check you use the right gcc (see in make.bat)',
                            u"note: on Windows, either install [POSIX threads for Windows](https://sourceforge.net/p/pthreads4w/wiki/Home/) or disable them as explained in ext/src/wapiti.h"
                        ],
                    ],
                    [u"run tests",
                        ["run ```python -m sem --test``` in a terminal"]
                    ],
                    [u"run SEM",
                        [
                            'run GUI (see "main features" above) and annotate "non-regression/fr/in/segmentation.txt"',
                            'OR: run ```python -m sem tagger resources/master/fr/NER.xml ./non-regression/fr/in/segmentation.txt -o sem_output```'
                        ]
                    ]
                ]

_external_resources = [
                        [u"[French Treebank](http://www.llf.cnrs.fr/fr/Gens/Abeille/French-Treebank-fr.php) by [Abeillé et al. (2003)](http://link.springer.com/chapter/10.1007%2F978-94-010-0201-1_10): corpus used for POS and chunking.", []],
                        [u"NER annotated French Treebank by [Sagot et al. (2012)](https://halshs.archives-ouvertes.fr/file/index/docid/703108/filename/taln12ftbne.pdf): corpus used for NER.", []],
                        [u"[Lexique des Formes Fléchies du Français (LeFFF)](http://alpage.inria.fr/~sagot/lefff.html) by [Clément et al. (2004)](http://www.labri.fr/perso/clement/lefff/public/lrec04ClementLangSagot-1.0.pdf): french lexicon of inflected forms with various informations, such as their POS tag and lemmatization.", []],
                        [u"[Wapiti](http://wapiti.limsi.fr) by [Lavergne et al. (2010)](http://www.aclweb.org/anthology/P10-1052): linear-chain CRF library.", []],
                        [u"Windows only: [MinGW64](https://sourceforge.net/projects/mingw-w64/?source=navbar): used to compile Wapiti on Windows.", []],
                        [u"Windows only: [POSIX threads for Windows](https://sourceforge.net/p/pthreads4w/wiki/Home/): if you want to multithread Wapiti on Windows.", []],
                        [u"GUI-specific: [TkInter](https://wiki.python.org/moin/TkInter): if you want to launch SEM's GUI.", []]
                      ]

_latest_changes = [
                    [u"improved SEM architecture.",[]],
                    [u"SEM can now be installed.",
                        [
                            u"run ```python setup.py install --user```",
                            u"will compile Wapiti",
                            u"will create a sem_data folder in current user"
                        ],
                    ],
                    [u"imrpoved GUI",
                        [u"SEM can now train a Wapiti model using annotated files."]
                    ],
                    [u"another GUI created for annotating documents.", []],
                    [u"updated manual",[]],
                    [u"new module: __annotate__. allows to call python taggers",
                        [
                            u"python implementation of Wapiti labeling",
                            u"lexica-based tagger"
                        ]
                    ],
                  ]

_planned_changes = [
                        [u"Add a tutorial.", []],
                        [u"redo triggered features and sequence features.", []],
                        [u"add lemmatiser.", []],
                        [u"migration to python3 ? (already made for revision 39 by lerela).", []],
                        [u"translate manual in English.", []],
                        [u'have more unit tests', []],
                        [u'handle HTML input files for tagger module',
                            [
                                "create specific tokeniser",
                                "need to handles cases such as words cut by a HTML tag"
                            ]
                        ],
                        [
                            "improve segmentation",
                            [
                                'handle URLs starting with country indicator (ex: "en.wikipedia.org")',
                                'handle URLs starting with subdomain (ex: "blog.[...]")',
                            ]
                        ]
                   ]

_references = [
                [u"[TELLIER, Isabelle, DUCHIER, Denys, ESHKOL, Iris, et al. Apprentissage automatique d'un chunker pour le français. In : TALN2012. 2012. p. 431–438.](https://hal.archives-ouvertes.fr/hal-01174591/document)", ["Chunking"]],
                [u"[TELLIER, Isabelle, DUPONT, Yoann, et COURMET, Arnaud. Un segmenteur-étiqueteur et un chunker pour le français. JEP-TALN-RECITAL 2012](http://anthology.aclweb.org/F/F12/F12-5.pdf#page=27)",
                    [
                        u"Part-Of-Speech Tagging",
                        u"chunking"
                    ]
                ],
                [u"[DUPONT, Yoann et TELLIER, Isabelle. Un reconnaisseur d’entités nommées du Français. session démonstration de TALN, 2014, p. 40.](http://www.aclweb.org/anthology/F/F14/F14-3.pdf#page=42)", ["Named Entity Recognition"]]
                #[u"[]()", [""]],
              ]

def name():
    return _name

def version():
    return u".".join([unicode(x) for x in [_version_major, _version_minor, _version_patch]])

def full_name():
    return "%s v%s" %(name(), version())

def informations():
    def make_md(element_list):
        accumulator = []
        for i_index, element in enumerate(element_list, 1):
            accumulator.append("%s. %s" %(i_index, element[0]))
            for ii_index, subelement in enumerate(element[1], 1):
                accumulator.append("   %s. %s" %(ii_index, subelement))
        return u"\n".join(accumulator)
        
    return u"""# %s
[SEM (Segmenteur-Étiqueteur Markovien)](%s) is a free NLP tool relying on Machine Learning technologies, especially CRFs. SEM provides powerful and configurable preprocessing and postprocessing. [SEM also has an online version](http://apps.lattice.cnrs.fr/sem/index).

## Main SEM features
%s

## First steps with SEM
%s

## External resources used by SEM
%s

## Latest changes (2.5.4 > %s)
%s

## Planned changes (no priority)
%s

## SEM references (with task[s] of interest)
%s""" %(full_name(), SEM_HOMEPAGE, make_md(_main_features), make_md(_first_steps), make_md(_external_resources), version(), make_md(_latest_changes), make_md(_planned_changes), make_md(_references))
