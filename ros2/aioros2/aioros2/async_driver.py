import asyncio
from inspect import getmembers
import traceback
import types
import rclpy
from typing import List

from .decorators import RosDefinition
from .decorators.service import RosService
from .decorators.topic import RosTopic
from .decorators.subscribe import RosSubscription
from .decorators.import_node import RosImport
from .decorators.action import RosAction
from .decorators.timer import RosTimer
from .decorators.params import RosParams
from .decorators.param_subscription import RosParamSubscription
from .decorators.start import RosStart


class AsyncDriver:
    """Base class for all adapters"""

    def __getattr__(self, attr):
        if not hasattr(self._n, attr):
            raise AttributeError(
                f"Attr >{attr}< not found in either driver or definition class"
            )

        value = getattr(self._n, attr)

        # Rebind self-bound definition functions to this driver
        if isinstance(value, types.MethodType):
            value = types.MethodType(value.__func__, self)

        # Cache result for future accesses to bypass this
        # getattr
        setattr(self, attr, value)

        return value

    def __init__(self, async_node, logger):
        self._logger = logger
        self._n = async_node

        # self._n.params = self._attach_params_dataclass(self._n.params)
        self._loop = asyncio.get_running_loop()

    async def run_executor(self, fn, *args, **kwargs):
        """Runs a synchronous function in an executor"""
        return await self._loop.run_in_executor(None, fn, *args, **kwargs)

    def run_coroutine(self, fn, *args, **kwargs):
        """Runs asyncio code from ANOTHER SYNC THREAD"""

        async def _wrap_coro(coro):
            try:
                return await coro
            except Exception:
                self.log_error(traceback.format_exc())

        # https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.call_soon_threadsafe
        return asyncio.run_coroutine_threadsafe(
            _wrap_coro(fn(*args, **kwargs)), self._loop
        )

    def run_coroutine_with_lock(self, fn, lock, *args, **kwargs):
        """Runs asyncio code from ANOTHER SYNC THREAD. Skips if lock is still acquired."""

        async def _wrap_coro(coro, lock):
            try:
                if not lock.locked():
                    async with lock:
                        return await coro
            except Exception:
                self.log_error(traceback.format_exc())

        return asyncio.run_coroutine_threadsafe(
            _wrap_coro(fn(*args, **kwargs), lock), self._loop
        )

    def _get_ros_definitions(self):
        from .decorators.import_node import RosImport

        node = self._n

        a = getmembers(node, lambda v: isinstance(v, RosDefinition))

        # Make sure RosImports are processed first
        a.sort(key=lambda b: type(b[1]) != RosImport)

        # Process topics last to prevent function version from shadowing definition
        a.sort(key=lambda b: type(b[1]) == RosTopic)

        # Process start last as it depends on everything else
        a.sort(key=lambda b: type(b[1]) == RosStart)

        return a

    def log_debug(self, msg: str):
        self._logger.info(msg)

    def log_warn(self, msg: str):
        self._logger.warn(msg)

    def log_error(self, msg: str):
        self._logger.error(msg)

    def log(self, msg: str):
        self._logger.info(msg)

    def _attach(self):
        # Attachers create an implementation for the passed handler which is assigned
        # to that handler's name.
        attachers = {
            # ros_type_e.ACTION: self._attach_action,
            RosService: self._attach_service,
            RosSubscription: self._attach_subscriber,
            RosTopic: self._attach_publisher,
            RosImport: self._process_import,
            RosAction: self._attach_action,
            RosTimer: self._attach_timer,
            RosParams: self._attach_params,
            RosParamSubscription: self._attach_param_subscription,
            RosStart: self._process_start,
        }

        for attr, definition in self._get_ros_definitions():
            setattr(self, attr, attachers[type(definition)](attr, definition))

    def _warn_unimplemented(self, readable_name, fn_name):
        self._logger.warn(
            f"Failed to initialize >{readable_name}< because >{fn_name}< is not implemented in driver >{self.__class__.__qualname__}<"
        )

    def _process_import(self, attr, ros_import: RosImport):
        self._warn_unimplemented("import", "_process_import")

    def _attach_service(self, attr, ros_service: RosService):
        self._warn_unimplemented("service", "_attach_service")

    def _attach_subscriber(self, attr, ros_sub: RosSubscription):
        self._warn_unimplemented("subscriber", "_attach_subscriber")

    def _attach_publisher(self, attr, ros_topic: RosTopic):
        self._warn_unimplemented("topic publisher", "_attach_publisher")

    def _attach_action(self, attr, ros_action: RosAction):
        self._warn_unimplemented("action", "_attach_action")

    def _attach_timer(self, attr, ros_timer: RosTimer):
        self._warn_unimplemented("timer", "_attach_timer")

    def _attach_params(self, attr, ros_params: RosParams):
        self._warn_unimplemented("params", "_attach_params")

    def _attach_param_subscription(self, attr, ros_param_sub: RosParamSubscription):
        self._warn_unimplemented("param subscription", "_attach_param_subscription")

    def _process_start(self, attr, ros_start: RosStart):
        self._warn_unimplemented("start", "_process_start")


# Maps python types to a ROS parameter integer enum
dataclass_ros_map = {
    bool: 1,
    int: 2,
    float: 3,
    str: 4,
    bytes: 5,
    List[bool]: 6,
    List[int]: 7,
    List[float]: 8,
    List[str]: 9,
}

# Maps python types to a ROS parameter enum
dataclass_ros_enum_map = {
    bool: rclpy.Parameter.Type.BOOL,
    int: rclpy.Parameter.Type.INTEGER,
    float: rclpy.Parameter.Type.DOUBLE,
    str: rclpy.Parameter.Type.STRING,
    bytes: rclpy.Parameter.Type.BYTE_ARRAY,
    List[bool]: rclpy.Parameter.Type.BOOL_ARRAY,
    List[int]: rclpy.Parameter.Type.INTEGER_ARRAY,
    List[float]: rclpy.Parameter.Type.DOUBLE_ARRAY,
    List[str]: rclpy.Parameter.Type.STRING_ARRAY,
}

# Maps ROS types to a corresponding attribute containing the
# typed value
ros_type_getter_map = {
    1: "bool_value",
    2: "integer_value",
    3: "double_value",
    4: "string_value",
    5: "byte_array_value",
    6: "bool_array_value",
    7: "integer_array_value",
    8: "double_array_value",
    9: "string_array_value",
}
