# ros2-delivery-drone

## Overview

Delivery drone project built on ROS2 Jazzy. The drone navigates to GPS coordinates, detects a person, and releases payload when an open palm is detected by the belly camera. Runs headless on a Raspberry Pi 5.

Three packages:

- **`hand_detection`** — subscribes to camera images from `camera_ros`, runs MediaPipe hand landmark detection, publishes palm-open state as a boolean
- **`servo_control`** — subscribes to Bool commands, drives a servo via GPIO PWM for payload release (auto-falls back to simulation when not on RPi)
- **`drone_bringup`** — launch-only package that brings up the full system with topic remapping

Planned packages: `ardupilot_bridge`, `drone_autonomy`.

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

### hand_detection

`palm_detector_node` handles the vision pipeline:
- Subscribes to camera images from `camera_ros` (no direct camera access)
- Runs MediaPipe HandLandmarker to detect hand keypoints
- Publishes `Bool` on `/openPalm_detection` (true when open palm detected)
- Optionally publishes annotated `Image` on `/hand_detection/debug_image`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `camera_topic` | string | /camera/image_raw | Topic to subscribe to for camera images |
| `publish_debug_frames` | bool | false | Publish annotated image for remote viewing |
| `image_size` | int | 480 | Max dimension for inference resize |

### servo_control

`servo_control_node` drives a servo for payload release:
- Subscribes to `Bool` on `/servo/command` (True = open, False = close)
- Publishes `Bool` on `/servo/state` (current servo state)
- Drives servo via `gpiozero.Servo` on GPIO 18 (hardware PWM0, configurable)
- Auto-detects RPi via `/sys/firmware/devicetree/base/model`; falls back to simulation mode if not on RPi or GPIO init fails

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `gpio_pin` | int | 18 | GPIO pin for servo PWM (BCM numbering) |
| `open_angle` | float | 90.0 | Servo angle for open position (0-180) |
| `closed_angle` | float | 0.0 | Servo angle for closed position (0-180) |
| `simulate` | bool | false | Force simulation mode (no GPIO) |

### drone_bringup

Launch-only package. `full_system.launch.py` starts camera_ros, palm_detector_node, servo_control_node, and foxglove_bridge. Remaps `/servo/command` to `/openPalm_detection` so palm detections directly drive the servo.

YAML config files in `config/` are the single source of truth for all ROS parameters. Per-package launch files load these by default and accept a `params_file` argument for override.

## Setup

Install [Docker](https://docs.docker.com/engine/install/ubuntu/) (recommend via apt for lightweight). You may need to [add your user to the docker group](https://docs.docker.com/engine/install/linux-postinstall/).

### Development (VSCode devcontainer)

Open the project in VSCode and reopen in container (Ctrl+Shift+P > "Reopen in Container"). Requires the Dev Containers extension.

### RPi Deployment

Build and run the Docker container on the Pi:
```bash
docker build --pull -f .devcontainer/Dockerfile -t ros2-drone .
docker run --privileged --network=host -v /run/udev:/run/udev:ro -v ~/ros2-delivery-drone:/workspace -it ros2-drone
```

Verify camera before running:
```bash
rpicam-hello --list-cameras  # on Pi host, outside Docker
```

## Building and Running

```bash
# Build (run from workspace root, inside Docker container)
colcon build --symlink-install
source install/setup.bash

# Run full system (camera + hand detection + servo control + foxglove bridge)
ros2 launch drone_bringup full_system.launch.py

# Or run individual nodes
ros2 run hand_detection palm_detector_node
ros2 run servo_control servo_control_node

# Run with parameters
ros2 run hand_detection palm_detector_node --ros-args \
  -p camera_topic:=/camera/image_raw \
  -p publish_debug_frames:=true

ros2 run servo_control servo_control_node --ros-args \
  -p gpio_pin:=18 \
  -p simulate:=true

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

### Automated tests

```bash
colcon test
colcon test-result --verbose
```

### Manual servo simulation test (host machine or RPi)

On any machine (no camera or GPIO needed):
```bash
# Terminal 1: start servo node in simulation mode
ros2 run servo_control servo_control_node --ros-args -p simulate:=true

# Terminal 2: send open command
ros2 topic pub --once /servo/command std_msgs/msg/Bool '{data: true}'

# Terminal 2: send close command
ros2 topic pub --once /servo/command std_msgs/msg/Bool '{data: false}'

# Terminal 2: monitor servo state
ros2 topic echo /servo/state
```

Expected output from the servo node:
```
[WARN] Simulation mode enabled via parameter
[INFO] [SIMULATE] Servo CLOSED (angle=0.0)
[INFO] Servo control ready (SIMULATE)
[INFO] [SIMULATE] Servo OPEN (angle=90.0)    # after open command
[INFO] [SIMULATE] Servo CLOSED (angle=0.0)   # after close command
```

### Testing on RPi with real servo

On the Raspberry Pi with a servo connected to GPIO 18:
```bash
# Servo will use real GPIO (no simulate parameter needed)
ros2 run servo_control servo_control_node

# Or run the full system (camera + servo)
ros2 launch drone_bringup full_system.launch.py
```

The node auto-detects the RPi and uses hardware GPIO. If GPIO initialization fails for any reason, it automatically falls back to simulation mode.

## Remote Viewing via Foxglove

The launch files include a Foxglove Bridge node (WebSocket on port 8765). This works through NAT (WSL2, WiFi AP) without any DDS configuration.

**Setup:**
1. Install [Foxglove Studio](https://foxglove.dev/download) on your dev machine
2. Connect to `ws://<pi-ip>:8765` (e.g., `ws://10.0.0.193:8765`)
3. Add an Image panel and select `/hand_detection/debug_image` to see the annotated camera feed
4. Add an Indicator panel and select `/openPalm_detection` to see palm detection state
