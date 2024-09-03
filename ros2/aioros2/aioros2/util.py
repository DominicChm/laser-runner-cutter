import inspect
import re
import traceback
from types import ModuleType
from rclpy.logging import LoggingSeverity

from aioros2.directives._decorators import RosDirective
# Decorate sync callbacks to catch errors into the specified print function.
def catch(log_fn, return_val=None):
    def _catch(fn):
        def _safe_exec(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            
            except Exception:
                log_fn(traceback.format_exc(), LoggingSeverity.ERROR)
                return return_val

        return _safe_exec

    return _catch


def to_camel_case(snake_str):
    # https://stackoverflow.com/questions/19053707/converting-snake-case-to-lower-camel-case-lowercamelcase
    return "".join(x.capitalize() for x in snake_str.lower().split("_"))


def to_snake(camel_str):
    camel_str = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", camel_str)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", camel_str).lower()

def get_caller_module(skip=0):
    stack = inspect.stack()

    start_idx = 2 + skip # Always omit this function and the calling function from the stack.
    caller_frame = stack[start_idx][0]

    caller_module = inspect.getmodule(caller_frame)

    return caller_module

def get_module_ros_directives(d):
    if isinstance(d, ModuleType):
        d = d.__dict__

    if not isinstance(d, dict):
        return []
    
    return [
        d[k]
        for k in d
        if not k.startswith("__") and isinstance(d[k], RosDirective)
    ]