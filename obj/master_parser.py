# -*- coding: utf-8 -*-

"""
file: master_parser.py

Description: an object to parse SEM pipeline files.

author: Yoann Dupont
copyright (c) 2016 Yoann Dupont - all rights reserved

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

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
    
    Attributes
    ----------
    _allowed_pipes : set of string
        the set of allowed processes names
    _allowed_options : set of string
        the set of allowed option names
    """
    
    _allowed_pipes   = set([u"segmentation", u"enrich", u"label", u"clean_info", u"export"])
    _allowed_options = set([u"encoding", u"log", u"clean"])
    
    class Process(object):
        """
        Process is just a holder for various informations about the processes to
        launch in the pipeline. The handling of everything is not done here as
        some global options may be given and cannot both be easily accessed here
        and keep the code simple and straightforward.
        
        Attributes
        ----------
        _identifier : str
            the identifier (name) of the process
        _args : dict(str -> str)
            the arguments of the process (name -> value)
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
        
        Attributes
        ----------
        _ienc : str
            The input's encoding.
        _oenc : str
            The output's encoding.
        _log_level : str
            The logging level.
        _log_file : str
            The file to log to.
        _clean : boolean
            Are temporary files cleaned up at the end of the process ?
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
            if child.tag not in Master._allowed_pipes:
                raise ValueError('"%s" is not a valid module.' %(child.tag))
            attrib = child.attrib
            self.pipeline.append(Master.Process(child.tag, attrib))
        
        if len(children) > 1:
            for child in children[1].getchildren():
                if child.tag not in Master._allowed_options:
                    raise ValueError('"%s" is not a valid option.' %(child.tag))
                
                option = child.tag
                if option == "encoding":
                    self.options.set_ienc(child.attrib.get("input-encoding", "utf-8"))
                    self.options.set_oenc(child.attrib.get("output-encoding", "utf-8"))
                elif option == "log":
                    self.options.set_log_level(child.attrib.get("level", "WARN"))
                    self.options.set_log_file(child.attrib.get("file", None))
                elif option == "clean":
                    self.options.set_clean(True)
