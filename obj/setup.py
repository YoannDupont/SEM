#!/usr/bin/python

import re, os.path
join = os.path.join

#module_directory = ".\\src"

def get_modules(path):
    def to_module_name(name):
        return re.sub(r"[\\/]", ".", re.sub(r"^[./\\]+", "", elt[:-3], re.MULTILINE))
    
    def get(path):
        ids    = os.listdir(path)
        pathes = []
        
        if "__init__.py" in ids:
            ids    = sorted([module for module in ids if module.endswith(".py") and not module.startswith("_")])
            pathes = [join(path, module) for module in ids]
            ids    = [module[:-3] for module in ids]
            
            dirs   = [join(path, d) for d in os.listdir(path) if os.path.isdir(join(path, d))]
            
            for i in dirs:
                L, R = get(i)
                for i in xrange(len(L)):
                    m = L[i]
                    if m not in ids:
                        ids.append(m)
                    else:
                        raise ValueError("Module indexation crash, module \"" + m + "\" found twice:\n" +
                                         "    " + pathes[ids.index(m)] + "\n" +
                                         "    " + R[i])
                pathes.extend(R)
        else:
            del ids[:]
        
        return [ids, pathes]
    ids, pathes = get(path)
    pathes      = [to_module_name(elt) for elt in pathes]
    
    return [ids,pathes]
