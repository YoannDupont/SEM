from xml.etree.ElementTree import ElementTree
from tree import Tree, EndogeneNodeFromName, ExogeneNodeFromName

class Informations(object):
    def __init__(self, path=None):
        self._bentries  = [] # informations that are before newly added information
        self._aentries  = [] # informations that are after ...
        self._endogenes = []
        self._exogenes  = []
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
        
        if len(children) < 2: raise RuntimeError("Less than 2 fields for configuration file.")
        
        if len(children) == 2:
            if children[0].tag != "entries" or children[1].tag not in ["endogene","exogene"]:
                raise RuntimeError("malformed configuration file: either no base entry or endo/exo gene features.")
        elif len(children) == 3:
            if children[0].tag != "entries" or children[1].tag != "endogene" or children[2].tag != "exogene":
                raise RuntimeError("malformed configuration file: either no base entry or endo/exo gene features.")
        else:
            raise RuntimeError("Invalid length")
        
        entries = children[0].getchildren()
        if len(entries) == 0: raise RuntimeError("At least one entry position should be given in configuration file.")
        if len(entries)  > 2: raise RuntimeError("More than 2 entry positions in configuration file.")
        
        for entry in entries:
            if entry.tag == "before":
                for c in entry.getchildren():
                    name = c.attrib["name"]
                    safe_add(found, name)
                    self._bentries.append(name)
            elif entry.tag == "after":
                for c in entry.getchildren():
                    name = c.attrib["name"]
                    safe_add(found, name)
                    self._aentries.append(name)
        
        self._endogenes = children[1].getchildren()
        self._exogenes  = (children[2].getchildren() if len(children)>2 else [])
        
        for i in xrange(len(self._endogenes)):
            name = self._endogenes[i].attrib["name"]
            safe_add(found, name)
            
            tmp = Tree(EndogeneNodeFromName(self._endogenes[i].tag))
            tmp.parse(self._endogenes[i])
            self._endogenes[i] = tmp
        
        if self._exogenes:
            for i in xrange(len(self._exogenes)):
                tmp = Tree(ExogeneNodeFromName(self._exogenes[i].tag, filename))
                tmp.parse(self._exogenes[i])
                self._exogenes[i] = tmp
    
    def bentries(self):
        return self._bentries
    
    def aentries(self):
        return self._aentries
    
    def endogenes(self):
        return self._endogenes
    
    def exogenes(self):
        return self._exogenes
