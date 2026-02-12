import os

from ament_index_python.packages import get_package_share_directory
import launch
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
import launch_ros.actions


def generate_launch_description():
    default_params_file = os.path.join(
        get_package_share_directory('drone_bringup'), 'config', 'servo_control_params.yaml')

    return launch.LaunchDescription([
        DeclareLaunchArgument(
            'params_file',
            default_value=default_params_file,
            description='Path to the servo_control parameter file'),

        launch_ros.actions.Node(
            package='servo_control',
            executable='servo_control_node',
            name='servo_control_node',
            parameters=[LaunchConfiguration('params_file')]),
    ])
