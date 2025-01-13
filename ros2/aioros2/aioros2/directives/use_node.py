import importlib
import traceback
from types import ModuleType
from typing import Optional, TypeVar

from ..util import get_module_ros_directives, duplicate_module
from ._RosDirective import NodeInfo, RosDirective
import rclpy.node
from rclpy.parameter import Parameter
from rclpy.exceptions import ParameterUninitializedException
import asyncio
from varname import varname

uses = {}


class RosUseNode(RosDirective):
    """
    aioros2's import. Allows node linkage at launch time and multi-instance imports.

    ```
    import testnodes.talker
    talker_node1 = use(testnodes.talker)
    talker_node2 = use(testnodes.talker)

    @subscribe(talker_node1.topic)
    def handle_topic1():
        ...

    @subscribe(talker_node2.topic)
    def handle_topic2():
        ...
    ```
    """

    # A unique instance of the module this `use` directive wraps
    # All variables, functions, etc within this module are different instances
    # to those accessible through an `import` statement.
    _instance = None

    # The default module, received through an `import` statement .
    _module = None

    # Name of the variable this `use` is assigned to.
    _param_base = None

    def __init__(
        self,
        module,
        param,
    ):
        # Set variables like this to bypass setattr
        vars(self).update(dict(_param_base=param, _module=module, _instance=module))

    def __getattr__(self, name):
        return getattr(self._instance, name)

    def __setattr__(self, name: str, value: rclpy.node.Any) -> None:
        return setattr(self._instance, name, value)

    def implement_server(
        self, node: rclpy.node.Node, nodeinfo, loop: asyncio.BaseEventLoop
    ):
        """
        When loaded by a server node, all use directives have their modules reloaded to create
        unique, independent instances.
        """
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
            node.get_logger().error(
                f"Could not link {self._param_base}"
                f" because `{self._param_base}.namespace` "
                f"or `{self._param_base}.name` params were "
                f"uninitialized"
            )

    def implement_client(
        self, node: rclpy.node.Node, nodeinfo, loop: asyncio.BaseEventLoop
    ):
        # More than 1 level of removal is not supported ATM.
        # IE node clients will not instantiate clients for their `use`d nodes.
        pass


U = TypeVar("U")


def use(
    module: U,
) -> U:
    return RosUseNode(module, varname())
