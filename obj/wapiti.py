"""
file: wapiti.py

Description: a very simple wrapper for calling wapiti. Provides train
and test procedures.
TODO: use subprocess.PIPE to get wapiti's output
TODO: add every option for train and test
TODO: add support for other modes, such as dump and update (1.5.0+)

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
along with this program. If not, see GNU official website.
"""

import subprocess

def command_name():
    """
    returns the executable name of Wapiti.
    
    This supposes that wapiti is installed on your computer.
    """
    
    return "wapiti"

def train(input, pattern=None, output=None, algorithm=None, nthreads=1, maxiter=None, rho1=None, rho2=None, model=None):
    """
    The train command of Wapiti.
    """
    
    cmd = [command_name(), "train"]
    if pattern is not None:   cmd.extend(["-p", pattern])
    if algorithm is not None: cmd.extend(["-a", str(algorithm)])
    if nthreads > 1:          cmd.extend(["-t", str(nthreads)])
    if maxiter is not None:   cmd.extend(["-i", str(maxiter)])
    if rho1 is not None:      cmd.extend(["-1", str(rho1)])
    if rho2 is not None:      cmd.extend(["-2", str(rho2)])
    if model is not None:     cmd.extend(["-m", str(model)])
    
    cmd.append(str(input))
    if output is not None: cmd.append(str(output))
    
    exit_status = subprocess.call(cmd)
    
    if exit_status != 0:
        if output is None: output = "*stdout"
        raise RuntimeError("Wapiti exited with status %i.\n%10s: %s\n%10s: %s\n%10s: %s" %(exit_status, "input", input, "pattern", pattern, "output", output))

def label(input, model, output=None, only_labels=False, nbest=None):
    """
    The label command of Wapiti.
    """
    
    cmd = [command_name(), "label", "-m", str(model)]
    
    if only_labels:       cmd.extend(["-l"])
    if nbest is not None: cmd.extend(["-n", str(nbest)])
    
    cmd.append(input)
    if output is not None: cmd.append(str(output))
    
    exit_status = subprocess.call(cmd)
    
    if exit_status != 0:
        if output is None: output = "*stdout"
        raise RuntimeError("Wapiti exited with status %i.\n\tmodel: %s\n\tinput: %s\n\toutput: %s" %(exit_status, model, input, output))
