import logging

from xml.etree.ElementTree import ElementTree, tostring as element2string

from obj.enrich.features.xml2feature import XML2Feature
from obj.logger                      import logging_formatter

import os.path

tmp                = os.path.normpath(__file__).split(os.sep)
tmp                = u'.'.join(tmp[tmp.index("obj") : ]).rsplit(".",1)[0]
xml2feature_logger = logging.getLogger("sem.%s" %tmp)
xml2feature_logger.setLevel("WARN")
xml2feature_handler = logging.StreamHandler()
xml2feature_handler.setFormatter(logging_formatter)
xml2feature_logger.addHandler(xml2feature_handler)
del tmp

class Informations(object):
    def __init__(self, path=None):
        self._bentries = [] # informations that are before newly added information
        self._aentries = [] # informations that are after ...
        self._features = [] # informations that are added
        self._x2f      = None # the feature parser, initialised in parse
        
        if path is not None:
            self.parse(path)
    
    def parse(self, filename):
        def safe_add(set, entry):
            if entry in set:
                raise ValueError('Duplicated column name: "' + entry + '"')
            set.add(entry)
        
        parsing = ElementTree()
        parsing.parse(filename)
        found = set() # set of found entries / names. They are nominative and SHOULD NOT be met twice
        
        children = parsing.getroot().getchildren()
        
        if len(children) != 2: raise RuntimeError("Enrichment file requires exactly 2 fields, %i given." %len(children))
        else:
            if children[0].tag != "entries":
                raise RuntimeError('Expected "entries" as first field, got "%s".' %children[0].tag)
            if children[1].tag != "features":
                raise RuntimeError('Expected "features" as second field, got "%s".' %children[1].tag)
        
        entries = list(children[0])
        if len(entries) not in (1,2):
            raise RuntimeError("Entries takes exactly 1 or 2 fields, %i given" %len(entries))
        else:
            entry1 = entries[0].tag.lower()
            entry2 = (entries[1].tag.lower() if len(entries)==2 else None)
            if entry1 not in ("before", "after"):
                raise RuntimeError('For entry position, expected "before" or "after", got "%s".' %entry1)
            if entry2 and entry2 not in ("before", "after"):
                raise RuntimeError('For entry position, expected "before" or "after", got "%s".' %entry2)
            if entry1 == entry2:
                raise RuntimeError('Both entry positions are the same, they should be different')
        
        for entry in entries:
            for c in entry.getchildren():
                name = c.attrib["name"]
                safe_add(found, name)
                if entry.tag == "before":
                        self._bentries.append(name)
                elif entry.tag == "after":
                        self._aentries.append(name)
    
        self._x2f = XML2Feature(self.aentries + self.bentries, path=filename)
        
        features = list(children[1])
        for feature in features:
            self._features.append(self._x2f.parse(feature))
            if self._features[-1].name is None:
                try:
                    raise ValueError("Nameless feature found.")
                except ValueError as exc:
                    for line in element2string(feature).rstrip().split("\n"):
                        xml2feature_logger.error(line.strip())
                    xml2feature_logger.exception(exc)
                    raise
            safe_add(found, self._features[-1].name)
    
    @property
    def bentries(self):
        return self._bentries
    
    @property
    def aentries(self):
        return self._aentries
    
    @property
    def features(self):
        return self._features
