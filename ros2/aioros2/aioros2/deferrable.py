from typing import Any
from varname import argname
import inspect 

class Deferrable:
    def __init__(self, var):
        v = argname("var")
        self.aname = argname(v, frame=2, vars_only=False)        
        self.globals = inspect.stack()[2].frame.f_globals

        print(self.aname)
    
    def resolve(self):
        return eval(self.aname, self.globals)
    