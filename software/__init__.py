#-*- encoding: utf-8-*-

class Software(object):
    u"""
    This class has the purpose of describing the software's current state.
    For example: current version, latest changes and planned changes.
    """
    
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
    
    _latest_changes = \
u"""List of latest changes:
    - corrected typo in enrich files: endogene / exogene -> endogenous / exogenous.
    - corrected a hard-coded "word" as first entry in files to be enriched.
    - added a pdf manual that is now up to date.
    - added versioning and information about the last revision.
    - some other changes I do not recall..."""
    
    _planned_changes = \
u"""List of planned changes (without any order of priority):
    1/ adding an export function that will allow the user to export the final data to various file formats, it will enumerate token-range information and chunk-range information. In master configuration file it will look like: <export format="FORMAT_NAME" token="RANGES" chunk="RANGES">
        1.1/ remove textualise module. Will be replaced by <export format="text" word="WORD_COLUMN" pos="POS_COLUMN" chunk="CHUNK_COLUMN">
        1.2/ add TEI as an export format.
        1.3/ add Glozz as an export format.
    2/ add lemmatiser.
    3/ add the possibility to work in memory rather than using files (existing proposition by lerela).
    4/ migration to python3 ? (already made for revision 39 by lerela).
    5/ add a Windows port to Wapiti using MinGW (would still require pthreads library).
    6/ translate manual in English.
    7/ Improve enrich speed. Possible way: runtime function generation"""
    
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
