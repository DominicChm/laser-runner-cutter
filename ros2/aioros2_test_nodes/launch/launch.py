
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription

from aioros2_test_nodes import other_node, talker_node

def generate_launch_description():
    parameters_file = os.path.join(
        get_package_share_directory("guidance_brain"),
        "config",
        "params.yaml",
    )

    talker_node = launch(
        other_node,
        name="",
        namespace=""
    )

    # furrow_perc0 = LaunchNode(
    #     furrow_perceiver_node,
    #     name="furrow0",
    #     parameters=[parameters_file],
    # )

    # furrow_perc1 = LaunchNode(
    #     furrow_perceiver_node,
    #     name="furrow1",
    #     parameters=[parameters_file],
    # )

    # rosbridge = IncludeLaunchDescription(
    #     FrontendLaunchDescriptionSource(
    #         [
    #             get_package_share_directory("rosbridge_server"),
    #             "/launch/rosbridge_websocket_launch.xml",
    #         ]
    #     ),
    # )

    # amiga = LaunchNode(
    #     amiga_control_node,
    #     name="amiga0",
    #     parameters=[parameters_file],
    #     output="screen",
    #     emulate_tty=True,
    # )

    # brain = LaunchNode(
    #     guidance_brain_node,
    #     name="brain0",
    #     parameters=[parameters_file],
    #     output="screen",
    #     emulate_tty=True,
    # )

    # video_server = launch_ros.actions.Node(
    #     package="web_video_server", executable="web_video_server", name="wvs"
    # )

    # # Link nodes
    # brain.perceiver_forward.link(furrow_perc0)
    # brain.amiga.link(amiga)

    return LaunchDescription(
        [
            # amiga,
            # brain,
            # rosbridge,
            # video_server,
            # rs_node0,
            # furrow_perc0,
            # rs_node1,
            # furrow_perc1,
        ]
    )
