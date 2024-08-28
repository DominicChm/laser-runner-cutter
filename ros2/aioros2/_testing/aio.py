import builtins

oi = builtins.__import__

def iwrap( name: str,
    globals = None,
    locals= None,
    fromlist = (),
    level= 0):

    print("IMPORT")

    return "lel" # oi(name, globals, locals, fromlist, level)

builtins.__import__ = iwrap

import aiohttp

avar = "test"