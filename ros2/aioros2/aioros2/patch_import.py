import importlib
import inspect
import re
from aioros2.util import get_module_ros_directives
import sys
import builtins
from .bootstrap import node

default_import = __import__

sys.dont_write_bytecode = True


# Will eventually come from parameters
def get_server_import_linkage(as_name):
    # ROS: return parameters.get(as_name + "/ns"), parameters.get(as_name + "/name")
    return (
        node.get_parameter(as_name + "/ns") or "/",
        node.get_parameter(as_name + "/name"),
    )  


def get_client_import_linkage(ns, name, as_name):
    return (None, None)


def iw(name: str, globals=None, locals=None, fromlist=(), level=0):
    module = default_import(name, globals, locals, fromlist, level)
    
    if fromlist and len(fromlist) > 0 and fromlist[0] == "other_node":
        print(getattr(module, fromlist[0]))

    # if ROS module, Re-import module to get a fresh, independant, instance.
    if len(get_module_ros_directives(module)) > 0:
        as_name = get_import_as_name()
        module = resolve_ros_import(module, name, as_name)

    return module


print("PATCH")
builtins.__import__ = iw


def get_import_as_name(skip=0):
    """Returns >name< from `import as >name<` in the caller module"""
    import_src = inspect.stack()[2 + skip].code_context[0]
    r = re.search(" as (.*)", import_src)

    if r:
        return r.group(1)


def resolve_ros_import(module, name, as_name):
    print("IMPORTING ROS MODULE", name, as_name)

    linkage = get_server_import_linkage(as_name)
    print(linkage)

    # Don't know where this module leads. Return the default loaded version of this module.
    if linkage[0] is None and linkage[1] is None:
        print("IMPORT DEFAULT", linkage)
        return module

    # Check if this node has already loaded.
    if linkage in sys.modules:
        print("IMPORT CACHED", linkage)
        return sys.modules[linkage]

    print("CREATE NEW", linkage)

    # Re-import to get a module with an independant dict
    spec = importlib.util.find_spec(name)
    new_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(new_module)

    new_module.__ros_ns__ = linkage[0]
    new_module.__ros_name__ = linkage[1]

    sys.modules[linkage] = new_module

    return new_module
