from typing import Any, Union
from ._decorators import RosDirective
from .topic import RosTopic
from rclpy.expand_topic_name import expand_topic_name
from ..deferrable import Deferrable
import rclpy.node
import asyncio

class RosSubscription(RosDirective):
    def __init__(self, fn, topic: Deferrable, idl=None, qos=10):
        self.topic = topic
        self.idl = idl
        self.qos = qos
        self.fn = fn

    def implement_server(self, node: rclpy.node.Node, nodeinfo, loop: asyncio.BaseEventLoop):
        t = self.topic.resolve()

        if type(t) == str:
            print("STRING TOPIC")
        elif isinstance(t, RosTopic):
            print("ROS TOPIC", t)
        else:
            raise TypeError("Not a topic or string")
        
    def implement_client(self, node: rclpy.node.Node, nodeinfo, loop: asyncio.BaseEventLoop):
        return

def subscribe(topic: Union[RosTopic, str], idl: Union[Any, None] = None, qos_queue=10):
    topic = Deferrable(topic)

    def _subscribe(fn):
        return RosSubscription(fn, topic, idl, qos_queue)


    return _subscribe
