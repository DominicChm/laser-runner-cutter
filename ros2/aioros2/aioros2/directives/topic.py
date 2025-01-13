from typing import Any, Union
from ._RosDirective import NodeInfo, RosDirective
import rclpy.node
import asyncio
from rclpy.expand_topic_name import expand_topic_name
from ..util import marshal_to_idl

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
    def __init__(self, path: str, msg_idl: Any, qos: Union[QoSProfile, int]):
        self._path = path
        self._idl = msg_idl
        self._qos: QoSProfile = qos

        self._loop = None
        self._node = None
        self._publisher = None
        self._nodeInfo = NodeInfo(None, None)

    def pub(self, *args, **kwargs):
        """Publishes to this topic without blocking."""
        self._loop.create_task(self.pub_async(*args, **kwargs))

    async def pub_async(self, *args, **kwargs):
        """Allows caller to wait"""
        p = self._get_publisher()
        idl = marshal_to_idl(self._idl, *args, **kwargs)
        await self._loop.run_in_executor(None, p.publish, idl)

    def get_fully_qualified_path(self):
        return expand_topic_name(
            self._path, self._nodeInfo.name, self._nodeInfo.namespace
        )

    def idl(self):
        return self._idl

    def qos(self):
        return self._qos

    def _get_publisher(self):
        if not self._publisher:
            self._publisher = self._node.create_publisher(
                self._idl, self.get_fully_qualified_path(), self._qos
            )

        return self._publisher

    def implement_server(
        self, node: rclpy.node.Node, nodeinfo, loop: asyncio.BaseEventLoop
    ):
        self._nodeInfo = nodeinfo
        self._node = node
        self._loop = loop

    def implement_client(
        self, node: rclpy.node.Node, nodeinfo, loop: asyncio.BaseEventLoop
    ):
        self._nodeInfo = nodeinfo
        self._node = node
        self._loop = loop


def topic(namespace: str, idl: Any, qos: Union[QoSProfile, int] = 10):
    return RosTopic(namespace, idl, qos)
