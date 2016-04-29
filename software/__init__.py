#-*- encoding: utf-8-*-

import sys

from os.path import dirname, abspath

class Software(object):
    u"""
    This class has the purpose of describing the software's current state.
    For example: current version, latest changes and planned changes.
    """
    
    SEM_HOME = dirname(dirname(abspath(__file__))).decode(sys.getfilesystemencoding())
    
    _name          = u"SEM"
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
    
    _version_minor = 3
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
    
    _latest_changes = \
u"""List of latest changes:
    1/ Added the export module that exports file to HTML
    2/ Added MinGW (Windows) support for wapiti (still requires pthreads)
    2/ simplified feature generation XML file
    3/ transformed the ugly "tree.py" where every feature was coded to a feature library
    4/ added some first step to multiple languages handling
    5/ changed french tokeniser
    6/ no more triggered features and sequence features (for now)"""
    
    _planned_changes = \
u"""List of planned changes (without any order of priority):
    1/ redo triggered features and sequence features.
    2/ add lemmatiser.
    3/ add the possibility to work in memory rather than using files:
        3.1/ existing proposition by lerela.
        3.2/ use subprocess.Popen, subprocess.PIPE and subprocess.communicate to put wapiti output to a string.
    4/ migration to python3 ? (already made for revision 39 by lerela).
    5/ translate manual in English.
    6/ add paragraph segmentation
    7/ update manual"""
    
    @classmethod
    def name(cls):
        return cls._name
    
    @classmethod
    def version(cls):
        return u".".join([unicode(x) for x in [cls._version_major, cls._version_minor, cls._version_patch]])
    
    @classmethod
    def full_name(cls):
        return "%s v%s" %(cls.name(), cls.version())
    
    @classmethod
    def informations(cls):
        return "%s\n\n%s\n\n%s" %(cls.full_name(), cls._latest_changes, cls._planned_changes)
