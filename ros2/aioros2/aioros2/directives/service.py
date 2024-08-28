import asyncio
import inspect

from aioros2.returnable import marshal_returnable_to_idl
from aioros2.util import catch
from ._decorators import RosDirective, idl_to_kwargs
from rclpy.node import Node

# https://stackoverflow.com/questions/11731136/class-method-decorator-with-self-arguments


class RosService(RosDirective):
    def __init__(self, path, idl, fn):
        if not hasattr(idl, "Request"):
            raise TypeError("Passed object is not a service-compatible IDL object! Make sure it isn't a topic or action IDL.")
        
        if not inspect.iscoroutinefunction(fn):
            raise TypeError("Service handler must be async")
        
        self._check_service_handler_signature(fn, idl)

        self._path = path
        self._idl = idl
        self._fn = fn

    def _check_service_handler_signature(self, fn, srv):
        fn_name = fn.__name__
        fn_inspection = inspect.signature(fn)
        fn_dict = fn_inspection.parameters
        fn_params = set(fn_dict)
        
        idl_dict = srv.Request.get_fields_and_field_types()
        idl_params = set(idl_dict.keys())

        if fn_params != idl_params:
            raise RuntimeError(
                f"PROBLEM WITH SERVICE >{fn_name}<\n"
                f"Service handler parameters do not match those in the IDL format!\n"
                f"Make sure that the function parameter names match those in the IDL!\n"
                f"Handler: {fn_name} -> \t{fn_params if len(fn_params) else 'NO ARGUMENTS'}\n"
                f"    IDL: {fn_name} -> \t{idl_params}"
            )

    def __call__(self, *args: any, **kwds: any) -> any:
        return self._fn(*args, **kwds)
    
    def implement_server(self, node: Node, loop):

        @catch(node.get_logger().log, self._idl.Response())
        def cb(req, result):
            kwargs = idl_to_kwargs(req)
            
            # Call handler function
            user_return = asyncio.run_coroutine_threadsafe(
                self._fn(**kwargs), 
                loop
            ).result()
            
            return marshal_returnable_to_idl(user_return, self._idl.Response)

        node.create_service(self._idl, self._path, cb)
    
    def implement_client(self, node: Node, loop):
        pass

# Decorator
def service(path, srv_idl):
    def _service(fn):
        return RosService(path, srv_idl, fn)

    return _service

