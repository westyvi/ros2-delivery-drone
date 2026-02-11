# ros2-delivery-drone

## Overview

Delivery drone project built on ROS2 Jazzy. The drone navigates to GPS coordinates, detects a person, and releases payload when an open palm is detected by the belly camera. Runs headless on a Raspberry Pi 5.

Currently implemented: **hand_detection** package — a single Python node that captures video, runs MediaPipe hand landmark detection, and publishes palm-open state as a boolean.

Planned packages: `ardupilot_bridge`, `servo_control`.

## Architecture

Single node (`palm_detector_node`) handles the full pipeline:
- Opens camera directly via OpenCV (no inter-process image serialization)
- Runs MediaPipe HandLandmarker to detect hand keypoints
- Publishes `Bool` on `/openPalm_detection` (true when open palm detected)
- Optionally publishes annotated `Image` on `/hand_detection/debug_image`

### ROS Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `camera_id` | int | 0 | Video device index (`/dev/video<N>`) |
| `publish_debug_frames` | bool | false | Publish annotated image for remote viewing |
| `image_size` | int | 480 | Max dimension for inference resize |
| `capture_fps` | int | 30 | Timer-driven capture rate |

## Setup

Install [Docker](https://docs.docker.com/engine/install/ubuntu/) (recommend via apt for lightweight). You may need to [add your user to the docker group](https://docs.docker.com/engine/install/linux-postinstall/).

### Development (VSCode devcontainer)

Open the project in VSCode and reopen in container (Ctrl+Shift+P > "Reopen in Container"). Requires the Dev Containers extension.

### RPi Deployment

Build and run the Docker container on the Pi:
```bash
docker build -f .devcontainer/Dockerfile -t ros2-drone .
docker run --privileged --device=/dev/video0 --network=host -v $(pwd):/workspace -it ros2-drone
```

For RPi Camera Module, you may need: `sudo modprobe bcm2835-v4l2`

## Building and Running

```bash
# Build
colcon build --symlink-install
source install/setup.bash

# Run
ros2 run hand_detection palm_detector_node

# Run with parameters
ros2 run hand_detection palm_detector_node --ros-args \
  -p camera_id:=0 \
  -p publish_debug_frames:=true

# Run via launch file
ros2 launch hand_detection hand_detection_launch.py

# Monitor detection output
ros2 topic echo /openPalm_detection
```

## Remote Topic Viewing

From a dev machine with ROS2 installed on the same network (same `ROS_DOMAIN_ID`, default 0):

```bash
# Text topics work over any connection
ros2 topic echo /openPalm_detection

# Debug image viewing (enable publish_debug_frames on the Pi first)
rqt_image_view /hand_detection/debug_image
```
