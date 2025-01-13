import asyncio
from aioros2.util import catch
from ._RosDirective import RosDirective
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup, ReentrantCallbackGroup
import rclpy.node
import asyncio
from inspect import iscoroutinefunction
from ..AioRos2Exception import AioRos2Exception


class RosTimer(RosDirective):
    """
    Uses a ROS timer to execute the decorated function when the node is run as a server
    """

    def __init__(self, interval, allow_concurrent_execution, fn) -> None:
        if not iscoroutinefunction(fn):
            raise AioRos2Exception("Timer functions MUST be async.")

        self.fn = fn
        self.interval = interval
        self.allow_concurrent_execution = allow_concurrent_execution

    def __call__(self, *args: any, **kwds: any) -> any:
        return self.fn(*args, **kwds)

    def implement_server(
        self, node: rclpy.node.Node, nodeinfo, loop: asyncio.BaseEventLoop
    ):
        # To prevent concurrent exec, use ros2 callback groups
        if self.allow_concurrent_execution:
            cbg = ReentrantCallbackGroup()
        else:
            cbg = MutuallyExclusiveCallbackGroup()

        @catch(node.get_logger().log)
        def _timer_callback():
            asyncio.run_coroutine_threadsafe(self.fn(), loop).result()

        node.create_timer(self.interval, _timer_callback, callback_group=cbg)

    # Don't run server-specific code on clients.
    def implement_client(self, node, nodeinfo, loop):
        pass


def timer(interval, allow_concurrent_execution=True):
    def _timer(fn):
        return RosTimer(interval, allow_concurrent_execution, fn)

    return _timer
