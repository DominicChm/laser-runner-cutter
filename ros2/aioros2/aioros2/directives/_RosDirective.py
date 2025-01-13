import rclpy.node
import asyncio
from collections import namedtuple

NodeInfo = namedtuple("NodeInfo", ["namespace", "name"])

class RosDirective:
    """
    Common base class for all aioros2 decorations. Used to discover aioros2
    implementations when instantiating drivers

    """

    def implement_server(self, node: rclpy.node.Node, nodeinfo: type[NodeInfo], loop: asyncio.BaseEventLoop):
        """
        Called when loading a ROS node as a server.
        """
        raise NotImplementedError("Server implementation not available.")

    def implement_client(self, node: rclpy.node.Node, nodeinfo: type[NodeInfo], loop: asyncio.BaseEventLoop):
        """
        Called when loading a ROS node API through a `use` directive
        """
        raise NotImplementedError("Client implementation not available.")

