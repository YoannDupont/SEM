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

_version_minor = 4
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
                            u"supported export formats: CoNLL, text, HTML (from plain text)",
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

_latest_changes = [
                    [u"Wapiti changes", 
                        [
                            u'now SEM only uses a local version of Wapiti (available in ext) that needs to be compiled.'
                        ]
                    ],
                    [u"export module changes", 
                        [
                            u"export now behaves like segmentation: different export modules are available in obj/exporters",
                            u'export "flavours" are in obj/exporters'
                        ]
                    ],
                    [u"tokeniser changes",
                        [
                            u"updated French tokeniser",
                            u"updated English tokeniser",
                            u"added support for urls and emails in obj/constants.py"
                        ]
                    ],
                    [u"Software module changes",
                        [
                            u'removed object oriented "Software" object. Replaced by global variables and methods',
                            u"SEM information now generated in MarkDown format."
                        ]
                    ],
                    [u"unit tests",
                        [
                            u'first unit tests added.'
                        ]
                    ],
                    [u"correction: added is_boolean switch to list features.", []
                    ]
                  ]

_planned_changes = [
                        [u"redo triggered features and sequence features.", []],
                        [u"add lemmatiser.", []],
                        [u"migration to python3 ? (already made for revision 39 by lerela).", []],
                        [u"translate manual in English.", []],
                        [u"update manual.", []],
                        [u'improve pipeline: allow calling a pipeline within a pipeline.', []],
                        [u'make SEM callable modules the same way segmenters and exporters. This would allow better integration in a pipeline.', []],
                        [u'have more unit tests', []],
                        [u'handle CoNLL-formatted input files for tagger module', []],
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
                        ],
                        ["make module objects using the same principle as for tokenisers or exporters.", []]
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
[SEM (Segmenteur-Étiqueteur Markovien)](%s) is a free NLP tool relying on Machine Learning technologies, especially CRFs. SEM provides powerful and configurable preprocessing and postprocessing.

## Main SEM features
%s

## latest changes (2.3.4 > %s)
%s

## planned changes (no priority)
%s""" %(full_name(), SEM_HOMEPAGE, make_md(_main_features), version(), make_md(_latest_changes), make_md(_planned_changes))
