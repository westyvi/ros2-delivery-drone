# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ROS2 (Jazzy) delivery drone project targeting headless Raspberry Pi 5 deployment. Single package (`hand_detection`) with one Python node (`palm_detector_node`) that captures video, runs MediaPipe hand landmark detection, and publishes palm-open state for payload release.

## Build & Run

```bash
# Build (run from workspace root)
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

## Testing

```bash
colcon test
colcon test-result --verbose
```

## Architecture

**Package:** `hand_detection` — pure `ament_python` package in `src/hand_detection/`.

**Single node: `palm_detector_node`**
- Opens camera directly via OpenCV (`camera_id` parameter, default 0)
- Timer-driven at configurable FPS (no inter-process image serialization)
- Runs MediaPipe HandLandmarker in VIDEO mode
- Publishes `std_msgs/Bool` on `/openPalm_detection` (always)
- Publishes `sensor_msgs/Image` on `/hand_detection/debug_image` (only when `publish_debug_frames=true`)

**ROS Parameters:** `camera_id` (int), `publish_debug_frames` (bool), `image_size` (int), `capture_fps` (int)

**Key implementation details:**
- Python source in `src/hand_detection/hand_detection/`
- MediaPipe model file at `src/hand_detection/hand_detection/resources/hand_landmarker.task` (installed via `package_data` in setup.py)
- Palm detection logic: checks if all 4 fingertip landmarks extend beyond palm base using distance ratio (cutoff: 0.5)
- Image resizing: caps longest dimension at `image_size` (default 480px) before inference
- FPS reporting every 5 seconds

## Development Environment

Target platform is RPi5 running headless, developed via SSH. Docker container built on `ros:jazzy-perception` with mediapipe pip-installed. The devcontainer uses `--privileged` + `--device=/dev/video0` + `--network=host`.

## CI/CD

GitHub Actions builds multi-arch Docker images (amd64/arm64) on push to `main` or version tags, pushes to Docker Hub. Requires `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` secrets.
