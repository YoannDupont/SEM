# -*- coding: utf-8 -*-

import logging

from xml.etree.ElementTree import ElementTree

class Master(object):
    """
    The object representation of the master configuration file that contains two
    main parts:
        - [mandatory] a pipeline
        - [optional]  a set of global options
    The pipeline is mandatory as it is what the module has to do.
    Global options will affect every runned script.
    """
    
    _allowed_pipes   = set([u"segmentation", u"enrich", u"label", u"clean_info", u"textualise"])
    _allowed_options = set([u"encoding", u"log", u"clean"])
    
    class Process(object):
        """
        Process is just a holder for various informations about the processes to
        launch in the pipeline. The handling of everything is not done here as
        some global options may be given and cannot both be easily accessed here
        and keep the code simple and straightforward.
        """
        
        def __init__(self, identifier, args):
            self._identifier = identifier
            self._args       = args
            
        @property
        def identifier(self):
            return self._identifier
            
        @property
        def args(self):
            return self._args
        
    class Options(object):
        """
        Options is a holder for global options in the "sem tagger" module.
        """
        
        def __init__(self, ienc="utf-8", oenc="utf-8", log_level=logging.CRITICAL, log_file=None, clean=False):
            self._ienc      = ienc
            self._oenc      = oenc
            self._log_level = log_level
            self._log_file  = log_file
            self._clean     = clean
        
        @property
        def ienc(self):
            return self._ienc
        
        @property
        def oenc(self):
            return self._oenc
        
        @property
        def log_level(self):
            return self._log_level
        
        @property
        def log_file(self):
            return self._log_file
        
        @property
        def clean(self):
            return self._clean
        
        def set_ienc(self, ienc):
            self._ienc = ienc
        
        def set_oenc(self, oenc):
            self._oenc = oenc
        
        def set_log_level(self, log_level):
            self._log_level = log_level
        
        def set_log_file(self, log_file):
            self._log_file = log_file
        
        def set_clean(self, clean):
            self._clean = clean
        
    def __init__(self, infile):
        self.pipeline = []
        self.options  = Master.Options()
        
        self._parse(infile)
    
    def _parse(self, infile):
        parsing = ElementTree()
        parsing.parse(infile)
        
        root     = parsing.getroot()
        children = root.getchildren()
        
        assert (root.tag == "master")
        assert (len(children) in [1,2])
        assert (children[0].tag == "pipeline")
        if len(children) == 2:
            assert (children[1].tag == "options")
        
        for child in children[0].getchildren():
            assert (child.tag in Master._allowed_pipes)
            attrib = child.attrib
            self.pipeline.append(Master.Process(child.tag, attrib))
        
        if len(children) > 1:
            for child in children[1].getchildren():
                assert (child.tag in Master._allowed_options)
                
                option = child.tag
                if option == "encoding":
                    self.options.set_ienc(child.attrib["input-encoding"] or "utf-8")
                    self.options.set_oenc(child.attrib["output-encoding"] or "utf-8")
                elif option == "log":
                    self.options.set_log_level(logging._levelNames[child.attrib["level"] if "level" in child.attrib else "CRITICAL"])
                    self.options.set_log_file(child.attrib["file"] if "file" in child.attrib else None)
                elif option == "clean":
                    self.options.set_clean(True)
