from typing import Any, TypeVar
from .util import get_module_ros_directives, duplicate_module
from .AioRos2Exception import AioRos2Exception
from .directives.use_node import RosUseNode
from launch_ros.actions import Node
from .directives import NodeInfo


class Aioros2LaunchDescription(Node):
    __instance = None
    __linkage_params = {}
    __kwargs = {}

    def __init_rclpy_node(self):
        kwargs = {
            # Default node name is node file name.
            "name": self.__instance.__name__.split(".")[-1],
            "namespace": "/",
            # executable name (in setup.py) MUST be name of the file.
            # IE "talker_node = aioros2_test_nodes.talker_node:main"
            "executable": self.__instance.__name__.split(".")[-1],
            "package": self.__instance.__package__,

            # Allow input kwargs to override above but not linkage params 
            **self.__kwargs,
            
            # Merge input parameters with those needed for node linkage.
            # Prioritize node linkage.
            "parameters": self.__kwargs.get("parameters", []) + [self.__linkage_params],
        }

        super().__init__(**kwargs)

    def __init__(self, module, **kwargs):
        directives = get_module_ros_directives(module)

        if len(directives) <= 0:
            raise AioRos2Exception(
                "Cannot launch module - no aioros2 directives found!"
            )

        self.__kwargs = kwargs

        # Load duplicate of module. Remove non-use directives from dict.
        self.__instance = duplicate_module(module)

        self.__init_rclpy_node()

    def __register_link(self, name, node):
        if not isinstance(node, Node):
            raise AttributeError("`use` directives must be linked to an rclpy node.")

        # Add parameters linking the varname of the `use` directive
        # to the name and namespace of the rclpy node.
        self.__linkage_params[name + ".name"] = node._Node__node_name
        self.__linkage_params[name + ".namespace"] = node._Node__node_namespace

        # Reinit rclpy node b/c parameters are updated.
        self.__init_rclpy_node()

    def __setattr__(self, name: str, value: Any) -> None:
        if hasattr(self.__instance, name):
            if isinstance(getattr(self.__instance, name), RosUseNode):
                self.__register_link(name, value)
            else:
                raise AttributeError(
                    f"Cannot set >{name}< in node. Only `use` directives are settable during launch"
                )

        return super().__setattr__(name, value)

    def __getattr__(self, name):
        return getattr(self.__instance, name)


T = TypeVar("T")


def launch(module: T, *args, **kwargs) -> T:
    if len(args) > 0:
        raise TypeError("More positional args passed than expected. Use keyword args.")

    return Aioros2LaunchDescription(module, **kwargs)
