from xml.etree.ElementTree import ElementTree
from tree                  import Tree, EndogenousNodeFromName, ExogenousNodeFromName

class Informations(object):
    def __init__(self, path=None):
        self._bentries   = [] # informations that are before newly added information
        self._aentries   = [] # informations that are after ...
        self._endogenous = []
        self._exogenous  = []
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
            if children[0].tag != "entries" or children[1].tag not in ["endogenous","exogenous"]:
                raise RuntimeError("malformed configuration file: either no base entry or endo/exo gene features.")
        elif len(children) == 3:
            if children[0].tag != "entries" or children[1].tag != "endogenous" or children[2].tag != "exogenous":
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
                if len(self._bentries) == 0:
                    raise RuntimeError("At least one before entry is required.")
            elif entry.tag == "after":
                for c in entry.getchildren():
                    name = c.attrib["name"]
                    safe_add(found, name)
                    self._aentries.append(name)
        
        self._endogenous = []
        self._exogenous  = []
        n = 1
        if children[n].tag == "endogenous":
            self._endogenous = children[n].getchildren()
            n += 1
        if n < len(children) and children[n].tag == "exogenous":
            self._exogenous  = children[n].getchildren()
        
        for i in xrange(len(self._endogenous)):
            name = self._endogenous[i].attrib["name"]
            safe_add(found, name)
            
            tmp = Tree(EndogenousNodeFromName(self._endogenous[i].tag, self._bentries[0]))
            tmp.parse(self._endogenous[i])
            self._endogenous[i] = tmp
        
        if self._exogenous:
            for i in xrange(len(self._exogenous)):
                tmp = Tree(ExogenousNodeFromName(self._exogenous[i].tag, self._bentries[0], filename))
                tmp.parse(self._exogenous[i])
                self._exogenous[i] = tmp
    
    def bentries(self):
        return self._bentries
    
    def aentries(self):
        return self._aentries
    
    def endogenous(self):
        return self._endogenous
    
    def exogenous(self):
        return self._exogenous
