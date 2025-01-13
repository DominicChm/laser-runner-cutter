import inspect
import asyncio
from ._RosDirective import RosDirective

class RosStart(RosDirective):
    """
    Starts the decorated function when the node is run as a server
    """
    def __init__(self, fn) -> None:
        if not inspect.iscoroutinefunction(fn):
            # Todo: support sync functions using executors
            raise TypeError("Start functions must be async")

        self.fn = fn

    def __call__(self, *args: any, **kwds: any) -> any:
        return self.fn(*args, **kwds)

    def implement_server(self, node, nodeinfo, loop):
        loop.create_task(self.fn())

    def implement_client(self, node, nodeinfo, loop):
        pass


def start(fn):
    return RosStart(fn)
