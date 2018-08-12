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

import platform
SYSTEM = platform.system().lower()
ON_WINDOWS = (SYSTEM == "windows")
PY2 = sys.version_info.major == 2

if PY2:
    SEM_HOME = dirname(abspath(__file__)).decode(sys.getfilesystemencoding())
else:
    SEM_HOME = dirname(abspath(__file__))
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

_version_minor = 2
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
                    [u"A GUI for manual annotation (requires TkInter)",
                        [
                            u'from terminal: run ```python -m sem annotation_gui```',
                            u'fast annotation: keyboard shortcuts and document-wide annotation broadcast',
                            u'can load pre-annotated files',
                            u'support for hierarchical tags (dot-separated, eg: "noun.common")',
                            u'handles multiple input format',
                            u'export in different formats'
                        ]
                    ],
                    [u"A GUI for easier use (requires TkInter)",
                        [
                            u'on Linux: double-clic on sem_gui.sh',
                            u'on Windows: double-clic on sem_gui.bat',
                            u'from terminal: run ```python -m sem gui```',
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
                            u"see [install.md](install.md)",
                            u"It will compile Wapiti and create necessary directories. Currently, SEM datas are located in ```~/sem_data```"
                        ],
                    ],
                    [u"run tests",
                        ["run ```python -m sem --test``` in a terminal"]
                    ],
                    [u"run SEM",
                        [
                            'run GUI (see "main features" above) and annotate "non-regression/fr/in/segmentation.txt"',
                            'or run: ```python -m sem tagger resources/master/fr/NER.xml ./non-regression/fr/in/segmentation.txt -o sem_output```'
                        ]
                    ]
                ]

_external_resources = [
                        [u"[French Treebank](http://www.llf.cnrs.fr/fr/Gens/Abeille/French-Treebank-fr.php) by [Abeillé et al. (2003)](http://link.springer.com/chapter/10.1007%2F978-94-010-0201-1_10): corpus used for POS and chunking.", []],
                        [u"NER annotated French Treebank by [Sagot et al. (2012)](https://halshs.archives-ouvertes.fr/file/index/docid/703108/filename/taln12ftbne.pdf): corpus used for NER.", []],
                        [u"[Lexique des Formes Fléchies du Français (LeFFF)](http://alpage.inria.fr/~sagot/lefff.html) by [Clément et al. (2004)](http://www.labri.fr/perso/clement/lefff/public/lrec04ClementLangSagot-1.0.pdf): french lexicon of inflected forms with various informations, such as their POS tag and lemmatization.", []],
                        [u"[Wapiti](http://wapiti.limsi.fr) by [Lavergne et al. (2010)](http://www.aclweb.org/anthology/P10-1052): linear-chain CRF library.", []],
                        [u"[setuptools](https://pypi.python.org/pypi/setuptools): to install SEM.", []],
                        [u"[Tkinter](https://wiki.python.org/moin/TkInter): for GUI modules (they will not be installed if Tkinter is not present).", []],
                        [u"Windows only: [MinGW64](https://sourceforge.net/projects/mingw-w64/?source=navbar): used to compile Wapiti on Windows.", []],
                        [u"Windows only: [POSIX threads for Windows](https://sourceforge.net/p/pthreads4w/wiki/Home/): if you want to multithread Wapiti on Windows.", []],
                        [u"GUI-specific: [TkInter](https://wiki.python.org/moin/TkInter): if you want to launch SEM's GUI.", []]
                      ]

_planned_changes = [
                        [u'Add a tutorial. Some of it done in section "retrain SEM" in manual.', []],
                        [u"add lemmatiser.", []],
                        [u"migration to python3 (already made for revision 39 by lerela).", []],
                        [u'have more unit tests', []],
                        [
                            "improve segmentation",
                            [
                                'handle URLs starting with country indicator (ex: "en.wikipedia.org")',
                                'handle URLs starting with subdomain (ex: "blog.[...]")',
                            ]
                        ]
                   ]

_references = [
                [u'[DUPONT, Yoann et PLANCQ, Clément. Un étiqueteur en ligne du Français. session démonstration de TALN-RECITAL, 2017, p. 15.](http://taln2017.cnrs.fr/wp-content/uploads/2017/06/actes_TALN_2017-vol3.pdf#page=25)',
                    [
                        u"Online interface"
                    ]
                ],
                [u'(best RECITAL paper award) [DUPONT, Yoann. Exploration de traits pour la reconnaissance d’entités nommées du Français par apprentissage automatique. RECITAL, 2017, p. 42.](http://taln2017.cnrs.fr/wp-content/uploads/2017/06/actes_RECITAL_2017.pdf#page=52)',
                    [
                        u"Named Entity Recognition (new, please use this one)"
                    ]
                ],
                [u"[TELLIER, Isabelle, DUCHIER, Denys, ESHKOL, Iris, et al. Apprentissage automatique d'un chunker pour le français. In : TALN2012. 2012. p. 431–438.](https://hal.archives-ouvertes.fr/hal-01174591/document)",
                    [
                        "Chunking"
                    ]
                ],
                [u"[TELLIER, Isabelle, DUPONT, Yoann, et COURMET, Arnaud. Un segmenteur-étiqueteur et un chunker pour le français. JEP-TALN-RECITAL 2012](http://anthology.aclweb.org/F/F12/F12-5.pdf#page=27)",
                    [
                        u"Part-Of-Speech Tagging",
                        u"chunking"
                    ]
                ],
                [u"[DUPONT, Yoann et TELLIER, Isabelle. Un reconnaisseur d’entités nommées du Français. session démonstration de TALN, 2014, p. 40.](http://www.aclweb.org/anthology/F/F14/F14-3.pdf#page=42)",
                    [
                        u"Named Entity Recognition (old, please do not use)"
                    ]
                ],
]

_bibtex = [
                [u"""\n```latex
@inproceedings{dupont2017etiqueteur,
    title={Un {\'e}tiqueteur en ligne du fran{\c{c}}ais},
    author={Dupont, Yoann and Plancq, Cl{\'e}ment},
    booktitle={24e Conf{\'e}rence sur le Traitement Automatique des Langues Naturelles (TALN)},
    pages={15--16},
    year={2017}
}
```""", []
                ],
                [u"""\n```latex
@inproceedings{dupont2018exploration,
  title={Exploration de traits pour la reconnaissance d’entit{\'e}s nomm{\'e}es du Fran{\c{c}}ais par apprentissage automatique},
  author={Dupont, Yoann},
  booktitle={24e Conf{\'e}rence sur le Traitement Automatique des Langues Naturelles (TALN)},
  pages={42},
  year={2018}
}
```""", []
                ],
                [u"""\n```latex
@inproceedings{tellier2012apprentissage,
  title={Apprentissage automatique d'un chunker pour le fran{\c{c}}ais},
  author={Tellier, Isabelle and Duchier, Denys and Eshkol, Iris and Courmet, Arnaud and Martinet, Mathieu},
  booktitle={TALN2012},
  volume={2},
  pages={431--438},
  year={2012}
}
```""", []
                ],
                [u"""\n```latex
@inproceedings{tellier2012segmenteur,
  title={Un segmenteur-{\'e}tiqueteur et un chunker pour le fran{\c{c}}ais (A Segmenter-POS Labeller and a Chunker for French)[in French]},
  author={Tellier, Isabelle and Dupont, Yoann and Courmet, Arnaud},
  booktitle={Proceedings of the Joint Conference JEP-TALN-RECITAL 2012, volume 5: Software Demonstrations},
  pages={7--8},
  year={2012}
}
```""", []
                ],
                [u"""\n```latex
@article{dupont2014reconnaisseur,
  title={Un reconnaisseur d’entit{\'e}s nomm{\'e}es du Fran{\c{c}}ais (A Named Entity recognizer for French)[in French]},
  author={Dupont, Yoann and Tellier, Isabelle},
  journal={Proceedings of TALN 2014 (Volume 3: System Demonstrations)},
  volume={3},
  pages={40--41},
  year={2014}
}
```""", []
                ],
]

def name():
    return _name

def version():
    return u".".join([str(x) for x in [_version_major, _version_minor, _version_patch]])

def full_name():
    return u"{0} v{1}".format(name(), version())

def informations():
    def make_md(element_list):
        accumulator = []
        for i_index, element in enumerate(element_list, 1):
            accumulator.append(u"{0}. {1}".format(i_index, element[0]))
            for ii_index, subelement in enumerate(element[1], 1):
                accumulator.append(u"   {0}. {1}".format(ii_index, subelement))
        return u"\n".join(accumulator)
        
    return u"""# {0}
[SEM (Segmenteur-Étiqueteur Markovien)]({1}) is a free NLP tool relying on Machine Learning technologies, especially CRFs. SEM provides powerful and configurable preprocessing and postprocessing. [SEM also has an online version](http://apps.lattice.cnrs.fr/sem/index).

## Main SEM features
{2}

## First steps with SEM
{3}

## External resources used by SEM
{4}

## Planned changes (for latest changes, see changelog.md)
{5}

## SEM references (with task[s] of interest)
{6}

## SEM references (bibtex format)
{7}""".format(full_name(), SEM_HOMEPAGE, make_md(_main_features), make_md(_first_steps), make_md(_external_resources), make_md(_planned_changes), make_md(_references), make_md(_bibtex))
