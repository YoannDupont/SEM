"""
Wrapper to Wapiti. Provides the train and label procedures.
TODO: add every option for train and test
TODO: add support for other modes, such as dump and update (1.5.0+)

The way things "should" be done here : every method should be a class method,
so that they can be called the following way: Wapiti.<method>
"""

import subprocess

class Wapiti(object):
    
    @staticmethod
    def exe():
        """
        returns the executable of Wapiti.
        
        This supposes that wapiti is installed on your computer.
        """
        
        return "wapiti"

    @staticmethod
    def train(input, pattern=None, output=None, algorithm=None, nthreads=1, maxiter=None, rho1=None, rho2=None, model=None):
        """
        The train command of Wapiti.
        """
        
        cmd = [Wapiti.exe(), "train"]
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

    @staticmethod
    def label(input, model, output=None, nbest=None):
        """
        The label command of Wapiti.
        """
        
        cmd = [Wapiti.exe(), "label", "-m", str(model)]
        
        if nbest is not None: cmd.extend(["-n", str(nbest)])
        
        cmd.append(input)
        if output is not None: cmd.append(str(output))
        
        exit_status = subprocess.call(cmd)
        
        if exit_status != 0:
            if output is None: output = "*stdout"
            raise RuntimeError("Wapiti exited with status %i.\n\tmodel: %s\n\tinput: %s\n\toutput: %s" %(exit_status, model, input, output))
