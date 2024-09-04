import importlib
import traceback
from types import ModuleType
from typing import Optional, TypeVar

from ..util import get_module_ros_directives, duplicate_module
from ._decorators import NodeInfo, RosDirective
import rclpy.node
from rclpy.parameter import Parameter
from rclpy.exceptions import ParameterUninitializedException
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
        self.__dict__["_instance"] = module


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

        try:
            # Load name and namespace of referenced node from parameters
            name_param = self._param_base + ".name"
            namespace_param = self._param_base + ".namespace"

            node.declare_parameter(name_param, Parameter.Type.STRING)
            node.declare_parameter(namespace_param, Parameter.Type.STRING)
            
            name = node.get_parameter(name_param).value
            namespace = node.get_parameter(namespace_param).value

            # Reinstantiate the module to get independant funcs and vars.
            clone = duplicate_module(self._module)
            self.__dict__["_instance"] = clone

            # Initialize the instance as a client.
            directives = get_module_ros_directives(clone)

            for d in directives:
                d.implement_client(node, NodeInfo(namespace, name), loop)

        except ParameterUninitializedException: 
            node.get_logger().error(f"Could not link {self._param_base}"
                                    f" because `{self._param_base}.namespace` "
                                    f"or `{self._param_base}.name` params were "
                                    f"uninitialized")

    def implement_client(self, node: rclpy.node.Node, nodeinfo, loop: asyncio.BaseEventLoop):
        return self._module


U = TypeVar('U')
def use(
    module: U,
    node_name: Optional[str] = None, # Will be overidden by parameters 
    node_namespace: Optional[str] = None, # Will be overidden by parameters 
) -> U:
    return RosUseNode(module, varname(), node_name, node_namespace)
