import functools
from typing import Any, Union

from ..util import catch, idl_to_kwargs
from ._RosDirective import RosDirective
from .topic import RosTopic
from rclpy.expand_topic_name import expand_topic_name
from ..deferrable import Deferrable
import rclpy.node
import asyncio
from ..AioRos2Exception import AioRos2Exception
from inspect import iscoroutinefunction

class RosSubscription(RosDirective):
    def __init__(self, fn, topic: Deferrable, idl=None, qos=10):
        self.topic = topic
        self.idl = idl
        self.qos = qos
        self.fn = fn

    # If implemented from a server node, run the handler.
    def implement_server(self, node: rclpy.node.Node, nodeinfo, loop: asyncio.BaseEventLoop):
        topic = self.topic.resolve()
        idl = self.idl
        qos = self.qos

        # Get IDL, topic, and qos either explicitly or from external
        # topic.
        if type(topic) == str:
            if not self.idl:
                raise AioRos2Exception("An IDL must be provided for string-based subscriptions")

        elif isinstance(topic, RosTopic):
            idl = topic.idl()
            qos = topic.qos()
            topic = topic.get_fully_qualified_path()

        else:
            raise TypeError("Not a topic or string")
        
        @catch(node.get_logger().log)
        def wrap_cb(data):
            kwargs = idl_to_kwargs(data)

            if iscoroutinefunction(self.fn):
                loop.create_task(self.fn(**kwargs))
            else:
                loop.run_in_executor(None, functools.partial(self.fn, **kwargs))

        node.create_subscription(idl, topic, wrap_cb ,qos)

    def implement_client(self, node: rclpy.node.Node, nodeinfo, loop: asyncio.BaseEventLoop):
        return # Don't do anything with subscriptions in client nodes

def subscribe(topic: Union[RosTopic, str], idl: Union[Any, None] = None, qos_queue=10):
    topic = Deferrable(topic)

    def _subscribe(fn):
        return RosSubscription(fn, topic, idl, qos_queue)

    return _subscribe
