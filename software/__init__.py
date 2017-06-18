#-*- encoding: utf-8-*-

import sys

from os.path import dirname, abspath

SEM_HOME     = dirname(dirname(abspath(__file__))).decode(sys.getfilesystemencoding())
SEM_HOMEPAGE = u"http://www.lattice.cnrs.fr/sites/itellier/SEM.html"

_name = u"SEM"
u"""
The name of the software. Obviously, it is SEM.
"""

_version_major = 2
u"""
The major version number.
Is only incremented when deep changes (that usually lead to a change of how the whole software is used) are made to the program.
Such changes include various feature additions / deletions / modifications, source code reorganisation and so on.
On a more NLP side, such changes could also include a change in corpora used in learning (if going from proprietary to free for example).
If this number is incremented, _version_minor and _version_patch are to be reseted to 0.
"""

_version_minor = 5
u"""
The minor version number.
Is only incremented when medium changes are made to the program.
Such changes include feature addition / deletion, creation of a new language entry for manual.
If this number is incremented, _version_patch is to be reseted to 0.
"""

_version_patch = 2
u"""
The patch version number.
Is only incremented when shallow changes are made to the program.
Such changes include bug correction, typo correction and any modification to existing manual(s) are made.
On a more NLP side, such changes would also include model changes.
"""

_main_features = [
                    [u"A GUI for easier use (requires TkInter)",
                        [
                            u'On Linux: double-clic on sem_gui.sh (or launch "bash ./sem_gui.sh" in a terminal)',
                            u'On Windows: double-clic on sem_gui.bat (or launch ".\\sem_gui.bat" in a terminal)'
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
                    [u"make Wapiti",
                        [
                            u"uncompress ext/wapitiXXX.tar.gz (where XXX is an optional version number)",
                            u"open a terminal in ext/wapiti",
                            u'type "make" (".\\make.bat wapiti" on Windows) without quotes. Note for Windows: if compilation fails, check you use the right gcc (see in make.bat)',
                            u"note: on Windows, either install [POSIX threads for Windows](https://sourceforge.net/p/pthreads4w/wiki/Home/) or disable them as explained in ext/src/wapiti.h"
                        ],
                    ],
                    [u"run tests",
                        ["python sem --test"]
                    ],
                    [u"run SEM",
                        [
                            'run GUI (see "main features" above) and annotate "non-regression/fr/in/segmentation.txt"',
                            'OR: run ```python sem tagger resources/master/fr/NER.xml ./non-regression/fr/in/segmentation.txt -o sem_output```'
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
                    [u"Corrected bug in text exporter. It required all POS, chunking and NER fields. It is no longer the case",[]],
                    [u"Added a GUI",
                        [
                            u'On Linux: double-clic on sem_gui.sh (or launch "bash ./sem_gui.sh" in a terminal)',
                            u'On Windows: double-clic on sem_gui.bat (or launch ".\\sem_gui.bat" in a terminal)'
                        ]
                    ],
                    [u"Improved model for NER",[]],
                    [u"Models are now automatically extracted using tagger module", []],
                    [u"Output directory now automatically created for tagger module", []],
                    [u'Added "ontology" feature',
                        [
                            u'an ontology is just a set of dictionaries that will all be matched on the same column.'
                        ]
                    ],
                    [u"Improved readme.md", 
                        [
                            u"more details left and right."
                        ]
                    ],
                    [u"tagger module now handles CoNLL-like files again! Hooray!",
                        [
                            u'in master file, within the options section: ```<file format="conll" fields="your,fields,separated,by,commas,the_field_where_words_are_supposed_to_be" word_field="the_field_where_words_are_supposed_to_be">```'
                        ]
                    ],
                    [u"chunking_fscore module created to evaluate tasks like named entities.",
                        [
                            u'only works for IOB tagging scheme for now.'
                        ]
                    ]
                  ]

_planned_changes = [
                        [u"Add a tutorial.", []],
                        [u"redo triggered features and sequence features.", []],
                        [u"add lemmatiser.", []],
                        [u"migration to python3 ? (already made for revision 39 by lerela).", []],
                        [u"translate manual in English.", []],
                        [u"update manual.", []],
                        [u'improve pipeline: allow calling a pipeline within a pipeline.', []],
                        [u'make SEM callable modules the same way segmenters and exporters. This would allow better integration in a pipeline.', []],
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

## First steps before using SEM
%s

## External resources used by SEM
%s

## Latest changes (2.4.0 > %s)
%s

## Planned changes (no priority)
%s

## SEM references (with task[s] of interest)
%s""" %(full_name(), SEM_HOMEPAGE, make_md(_main_features), make_md(_first_steps), make_md(_external_resources), version(), make_md(_latest_changes), make_md(_planned_changes), make_md(_references))
