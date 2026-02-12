import os

from ament_index_python.packages import get_package_share_directory
import launch
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
import launch_ros.actions


def generate_launch_description():
    default_params_file = os.path.join(
        get_package_share_directory('drone_bringup'), 'config', 'hand_detection_params.yaml')

    return launch.LaunchDescription([
        DeclareLaunchArgument(
            'params_file',
            default_value=default_params_file,
            description='Path to the hand_detection parameter file'),

        # Camera driver (camera_ros)
        launch_ros.actions.Node(
            package='camera_ros',
            executable='camera_node',
            name='camera',
            parameters=[LaunchConfiguration('params_file')]),

        # Palm detection node
        launch_ros.actions.Node(
            package='hand_detection',
            executable='palm_detector_node',
            name='palm_detector_node',
            parameters=[LaunchConfiguration('params_file')]),

        # Remote viewing bridge
        launch_ros.actions.Node(
            package='foxglove_bridge',
            executable='foxglove_bridge',
            name='foxglove_bridge',
            parameters=[{'port': 8765}]),
    ])
