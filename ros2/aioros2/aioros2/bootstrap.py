# Wraps an rclpy node singleton everything attaches to.

import rclpy
import asyncio

from rclpy.node import Node

rclpy.init()

node = Node("DEFAULT")

loop = asyncio.get_event_loop()
