# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ROS2 (Jazzy) delivery drone project targeting headless Raspberry Pi 5 deployment. Three packages:

- **`hand_detection`** — subscribes to camera images, runs MediaPipe hand landmark detection, publishes palm-open state
- **`servo_control`** — subscribes to Bool commands, drives a servo via GPIO PWM for payload release (auto-falls back to simulation when not on RPi)
- **`drone_bringup`** — launch-only package that brings up the full system with topic remapping

## Build & Run

```bash
# Build (run from workspace root)
colcon build --symlink-install
source install/setup.bash

# Run individual nodes
ros2 run hand_detection palm_detector_node
ros2 run servo_control servo_control_node

# Run with parameters
ros2 run hand_detection palm_detector_node --ros-args \
  -p camera_topic:=/camera/image_raw \
  -p publish_debug_frames:=true

ros2 run servo_control servo_control_node --ros-args \
  -p gpio_pin:=18 \
  -p simulate:=true

# Run full system (camera + hand detection + servo control + foxglove bridge)
ros2 launch drone_bringup full_system.launch.py

# Run individual launch files (loads YAML config from drone_bringup)
ros2 launch hand_detection hand_detection_launch.py
ros2 launch servo_control servo_control_launch.py

# Override config with a custom YAML file
ros2 launch servo_control servo_control_launch.py params_file:=/path/to/custom.yaml

# Monitor topics
ros2 topic echo /openPalm_detection
ros2 topic echo /servo/state
```

## Testing

```bash
colcon test
colcon test-result --verbose
```

### Manual servo simulation test (no camera or GPIO needed)

```bash
# Terminal 1: start servo in simulation mode
ros2 run servo_control servo_control_node --ros-args -p simulate:=true

# Terminal 2: send commands and observe state
ros2 topic pub --once /servo/command std_msgs/msg/Bool '{data: true}'
ros2 topic pub --once /servo/command std_msgs/msg/Bool '{data: false}'
ros2 topic echo /servo/state
```

On non-RPi hosts, the node auto-falls back to simulation even without `-p simulate:=true`.

## Architecture

```
[camera_ros]                       [hand_detection]                    [servo_control]
  camera_node                        palm_detector_node                  servo_control_node
  pub: /camera/image_raw (Image) --> sub: /camera/image_raw (Image)
                                     pub: /openPalm_detection (Bool) --> sub: /servo/command (Bool)
                                                                         pub: /servo/state (Bool)
                                                                         drives GPIO 18 via gpiozero

[foxglove_bridge]
  WebSocket server on port 8765 for remote viewing via Foxglove Studio

[drone_bringup]
  full_system.launch.py
  - launches camera_ros, palm_detector_node, servo_control_node, foxglove_bridge
  - remaps /servo/command -> /openPalm_detection (temporary direct glue)
```

**Future:** A `drone_autonomy` state machine package will sit between detection and servo. Swap is a launch-file-only change — remove the remap, let `drone_autonomy` subscribe to `/openPalm_detection` and publish to `/servo/command`. Zero code changes to `hand_detection` or `servo_control`.

### Package: `hand_detection`

Pure `ament_python` package in `src/hand_detection/`.

**Node: `palm_detector_node`**
- Subscribes to `sensor_msgs/Image` from `camera_ros` via configurable topic
- Runs MediaPipe HandLandmarker in VIDEO mode
- Publishes `std_msgs/Bool` on `/openPalm_detection` (always)
- Publishes `sensor_msgs/Image` on `/hand_detection/debug_image` (only when `publish_debug_frames=true`)

**ROS Parameters:** `camera_topic` (string), `publish_debug_frames` (bool), `image_size` (int)

**Key implementation details:**
- Python source in `src/hand_detection/hand_detection/`
- MediaPipe model file at `src/hand_detection/hand_detection/resources/hand_landmarker.task` (installed via `package_data` in setup.py)
- Palm detection logic: checks if all 4 fingertip landmarks extend beyond palm base using distance ratio (cutoff: 0.5)
- Image resizing: caps longest dimension at `image_size` (default 480px) before inference
- FPS reporting every 5 seconds

### Package: `servo_control`

Pure `ament_python` package in `src/servo_control/`.

**Node: `servo_control_node`**
- Subscribes to `std_msgs/Bool` on `/servo/command` (True = open, False = close)
- Publishes `std_msgs/Bool` on `/servo/state` (current state)
- Drives servo via `gpiozero.Servo` on GPIO 18 (hardware PWM0, configurable)
- Auto-detects RPi via `/sys/firmware/devicetree/base/model`; falls back to simulation mode if not on RPi or GPIO init fails

**ROS Parameters:** `gpio_pin` (int, default 18), `open_angle` (float, default 90.0), `closed_angle` (float, default 0.0), `simulate` (bool, default False)

**Key implementation details:**
- Python source in `src/servo_control/servo_control/`
- RPi auto-detection reads `/sys/firmware/devicetree/base/model`; three fallback paths: not RPi, file not found, GPIO init failure
- Angle mapping: gpiozero expects -1 to 1, node maps angle via `(angle / 90.0) - 1.0`
- Uses `gpiozero.pins.lgpio.LGPIOFactory` (required for RPi5 — default pigpio factory doesn't work)
- Starts in CLOSED position; publishes state on every command

### Package: `drone_bringup`

Launch-only `ament_python` package in `src/drone_bringup/`. No nodes — just launch files and YAML config.

**Config files** (single source of truth for all ROS parameters):
- `config/hand_detection_params.yaml` — camera_ros and palm_detector_node parameters
- `config/servo_control_params.yaml` — servo_control_node parameters

Launch files and per-package launches load these YAML files. Node `declare_parameter()` defaults remain as last-resort fallbacks. Per-package launch files accept a `params_file` argument for override.

## Development Environment

Target platform is RPi5 running headless, developed via SSH. Docker container built on `ros:jazzy-perception` with mediapipe pip-installed. The devcontainer uses `--privileged` + `--network=host`.

## Remote Viewing

Foxglove Bridge runs on port 8765 inside the container. Connect from any machine using Foxglove Studio (`ws://<pi-ip>:8765`). Works through NAT (WSL2, WiFi AP) without DDS configuration.

## CI/CD

GitHub Actions builds multi-arch Docker images (amd64/arm64) on push to `main` or version tags, pushes to Docker Hub. Requires `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` secrets.
