import launch
import launch_ros.actions

def generate_launch_description():
    return launch.LaunchDescription([
        launch_ros.actions.Node(
            package='hand_detection',
            executable='palm_detector_node',
            name='palm_detector_node',
            parameters=[{
                'camera_id': 0,
                'publish_debug_frames': False,
                'image_size': 480,
                'capture_fps': 30,
            }]),
    ])
