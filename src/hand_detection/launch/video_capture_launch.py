import launch
import launch_ros.actions

def generate_launch_description():
    return launch.LaunchDescription([
        launch_ros.actions.Node(
            package='hand_detection',
            executable='video_capture_node',
            name='video_capture_node'),
  ])
