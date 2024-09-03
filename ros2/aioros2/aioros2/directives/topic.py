from typing import Any, Union
from ._decorators import NodeInfo, RosDirective
import rclpy.node
import asyncio
from rclpy.qos import (
    QoSProfile,
    QoSDurabilityPolicy,
    QoSHistoryPolicy,
)

QOS_LATCHED = QoSProfile(
    depth=1,
    history=QoSHistoryPolicy.KEEP_LAST,
    durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
)

class RosTopic(RosDirective):
    def __init__(
        self, path: str, msg_idl: Any, qos: Union[QoSProfile, int]
    ):
        self._path = path
        self._idl = msg_idl
        self._qos: QoSProfile = qos

        self._nodeInfo = NodeInfo(None, None)

    def implement_server(self, node: rclpy.node.Node, nodeinfo, loop: asyncio.BaseEventLoop):
        self._nodeInfo = nodeinfo

    def implement_client(self, node: rclpy.node.Node, nodeinfo, loop: asyncio.BaseEventLoop):
        self._nodeInfo = nodeinfo

    def name(self):
        return self._nodeinfo.name
    
    def namespace(self):
        return self._nodeinfo.namespace

def topic(namespace: str, idl: Any, qos: Union[QoSProfile, int] = 10):
    return RosTopic(namespace, idl, qos)
