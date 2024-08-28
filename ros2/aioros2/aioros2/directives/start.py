import inspect
import asyncio
from ._decorators import RosDirective

class RosStart(RosDirective):
    def __init__(self, fn) -> None:
        if not inspect.iscoroutinefunction(fn):
            raise TypeError("Start function must be async")

        self.fn = fn

    def __call__(self, *args: any, **kwds: any) -> any:
        return self.fn(*args, **kwds)

    def implement_server(self, node, loop):
        loop.create_task(self.fn())

    def implement_client(self, node, loop):
        pass


def start(fn):
    return RosStart(fn)
