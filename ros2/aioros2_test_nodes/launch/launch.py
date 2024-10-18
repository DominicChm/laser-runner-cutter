import os
from aioros2.launch import launch
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription

from aioros2_test_nodes import other_node as ond, talker_node as tnd


def generate_launch_description():

    talker_node = launch(
        tnd,
        output="screen",
        emulate_tty=True, 
        parameters=[
            {"params.amiga_host": "test"}
        ]
    )

    other_node = launch(ond, name="other_node1")
    other_node1 = launch(ond, name="other_node2")

    talker_node.onode = other_node
    talker_node.onode1 = other_node1

    return LaunchDescription([talker_node, other_node, other_node1])
