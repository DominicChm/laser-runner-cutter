import builtins
import inspect
import threading
from types import ModuleType
from typing import Optional
from .directives._decorators import RosDirective
from aioros2.util import get_caller_module, get_module_ros_directives
from aioros2.AioRos2Exception import AioRos2Exception
import asyncio
from .bootstrap import node, loop
from rclpy.executors import Executor, MultiThreadedExecutor
import rclpy

# pip install -e laser-runner-cutter/ros2/aioros2/ --config-settings editable_mode=strict

# https://stackoverflow.com/questions/338101/python-function-attributes-uses-and-abuses
# https://robotics.stackexchange.com/questions/106026/ros2-multi-nodes-each-on-a-thread-in-same-process


def run(num_threads: Optional[int] = None):
    # Access caller module dict to find directives
    module_dict = inspect.stack()[1].frame.f_globals

    directives = get_module_ros_directives(module_dict)

    if len(directives) <= 0:
        raise AioRos2Exception(
            f"Initialized module {module_dict.__name__} does not have any ROS directives!"
        )

    for d in directives:
        d.implement_server(node, loop)

    loop.create_task(_spin([node], num_threads))

    loop.run_forever()

    rclpy.shutdown()


async def _spin(nodes, num_threads: Optional[int] = None):
    # From https://github.com/mavlink/MAVSDK-Python/issues/419

    executor = MultiThreadedExecutor(num_threads=num_threads)
    for node in nodes:
        executor.add_node(node)

    cancels = [node.create_guard_condition(lambda: None) for node in nodes]

    def spin_inner(
        executor: Executor,
        future: asyncio.Future,
        event_loop: asyncio.AbstractEventLoop,
    ):
        while not future.cancelled():
            executor.spin_once()
        if not future.cancelled():
            event_loop.call_soon_threadsafe(future.set_result, None)

    event_loop = asyncio.get_event_loop()
    spin_task = event_loop.create_future()
    spin_thread = threading.Thread(
        target=spin_inner, args=(executor, spin_task, event_loop)
    )
    spin_thread.start()
    try:
        await spin_task
    except asyncio.CancelledError:
        for cancel in cancels:
            cancel.trigger()
    spin_thread.join()

    for idx, node in enumerate(nodes):
        node.destroy_guard_condition(cancels[idx])


def process_imports(module):
    imports = get_module_ros_imports(module)

    for i in imports:
        print("imports", imports)


def get_module_ros_imports(d):
    if isinstance(d, ModuleType):
        d = d.__dict__

    return [
        d[k]
        for k in d
        if not k.startswith("__")
        and isinstance(d[k], ModuleType)
        and len(get_module_ros_directives(d[k])) > 0
    ]
