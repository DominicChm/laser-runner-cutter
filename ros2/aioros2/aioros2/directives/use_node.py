import importlib
from types import ModuleType
from typing import Optional, TypeVar

from ..util import get_module_ros_directives, duplicate_module
from ._decorators import NodeInfo, RosDirective
import rclpy.node
import asyncio
from varname import varname
uses = {}

class RosUseNode(RosDirective):    
    def __init__(
        self,
        module,
        param,
        node_name: Optional[str] = None,
        node_namespace: Optional[str] = None,
    ):
        # Access dict to bypass setattr.
        self.__dict__["_param_base"] = param # Defines parameter where name and ns are looked for.
        self.__dict__["_module"] = module
        self.__dict__["_node_name"] = node_name
        self.__dict__["_node_namespace"] = node_namespace
        self.__dict__["_instance"] = None


    def __getattr__(self, name):
        if self._instance:
            return getattr(self._instance, name)
        else:
            return getattr(self._module, name)
    
    def __setattr__(self, name: str, value: rclpy.node.Any) -> None:
        if self._instance:
            return setattr(self._instance, name, value)
        else:
            return setattr(self._module, name, value)
    
    def implement_server(self, node: rclpy.node.Node, nodeinfo, loop: asyncio.BaseEventLoop):
        clone = duplicate_module(self._module)
        self.__dict__["_instance"] = clone

        # Initialize instance.
        directives = get_module_ros_directives(clone)

        name = node.get_parameter_or(self._param_base + "/name", None)
        namespace = node.get_parameter_or(self._param_base + "/ns", None)

        if not name:
            print(f"CAN'T USE {self._param_base} BECAUSE A PARAMETER NAME WAS NOT SPECIFIED.")
            return
        
        print("USE", self._param_base, name.value, namespace.value)

        for d in directives:
            d.implement_server(node, NodeInfo(name, namespace), loop)

    def implement_client(self, node: rclpy.node.Node, nodeinfo, loop: asyncio.BaseEventLoop):
        return self._module


U = TypeVar('U')
def use(
    module: U,
    node_name: Optional[str] = None, # Will be overidden by parameters 
    node_namespace: Optional[str] = None, # Will be overidden by parameters 
) -> U:
    return RosUseNode(module, varname(), node_name, node_namespace)
