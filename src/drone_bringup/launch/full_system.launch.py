import os

from ament_index_python.packages import get_package_share_directory
import launch
import launch_ros.actions


def generate_launch_description():
    bringup_dir = get_package_share_directory('drone_bringup')

    hand_detection_config = os.path.join(bringup_dir, 'config', 'hand_detection_params.yaml')
    servo_control_config = os.path.join(bringup_dir, 'config', 'servo_control_params.yaml')

    return launch.LaunchDescription([
        # Palm detection node
        launch_ros.actions.Node(
            package='hand_detection',
            executable='palm_detector_node',
            name='palm_detector_node',
            parameters=[hand_detection_config]),

        # Servo control node — remap /servo/command to /openPalm_detection
        # so palm detections directly drive the servo.
        # When drone_autonomy is added, remove this remap and let the
        # state machine sit between detection and servo.
        launch_ros.actions.Node(
            package='servo_control',
            executable='servo_control_node',
            name='servo_control_node',
            parameters=[servo_control_config],
            remappings=[
                ('/servo/command', '/openPalm_detection'),
            ]),
    ])
