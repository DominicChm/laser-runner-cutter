import rclpy.node
import asyncio

class RosDirective:
    """Common base class for all aioros2 decorations. Used to discover aioros2
    implementations when instantiating drivers"""

    def implement_server(self, node: rclpy.node.Node, loop: asyncio.BaseEventLoop):
        raise NotImplementedError("Server implementation not available.")

    def implement_client(self, node: rclpy.node.Node, loop: asyncio.BaseEventLoop):
        raise NotImplementedError("Client implementation not available.")



def idl_to_kwargs(req):
    msg_keys = req.get_fields_and_field_types().keys()
    return {k: getattr(req, k) for k in msg_keys}
