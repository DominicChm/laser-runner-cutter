from typing import TypeVar
from ._decorators import RosDirective, NodeInfo
import dataclasses
import rclpy.node
import asyncio
from rclpy.parameter import Parameter
from varname import varname
from ..mappings import dataclass_ros_enum_map

class RosParams(RosDirective):
    # Include these here for typing
    _dclass = None
    _base = None

    def __init__(self, params_dclass, base_name) -> None:
        self._validate_dataclass(params_dclass)

        # https://stackoverflow.com/a/58676807/16238567
        # bypass setattr
        vars(self).update(dict(
            _dclass = params_dclass(),
            _base = base_name,
        ))


    def _validate_dataclass(self, dclass):
        pass

    def __setattr__(self, name: str, value) -> None:
        return setattr(self._dclass, name, value)

    # Returns array of listeners that caller can add to.
    def __getattr__(self, attr):
        return getattr(self._dclass, attr)

    
    def implement_server(self, node: rclpy.node.Node, nodeinfo: type[NodeInfo], loop: asyncio.BaseEventLoop):
        field_names = [(f.name, f.default, f.type) for f in dataclasses.fields(self._dclass)]
    
        for name, default_val, t in field_names:
            param_path = self._base + "." + name
            ros_type = dataclass_ros_enum_map[t]
            default_param = Parameter(param_path, ros_type, default_val)

            # Declare and get current (or default) param value
            node.declare_parameter(param_path, ros_type)
            val = node.get_parameter_or(param_path, default_param).value

            # Update internal dataclass with current val
            setattr(self._dclass, name, val)        

    def implement_client(self, node: rclpy.node.Node, nodeinfo: type[NodeInfo], loop: asyncio.BaseEventLoop):
        pass

T = TypeVar("T")
def params(dataclass_param: T) -> T:
    return RosParams(dataclass_param, varname())