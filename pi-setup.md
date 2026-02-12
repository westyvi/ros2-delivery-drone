# Raspberry Pi 5 Setup Log

Steps taken to set up a headless Raspberry Pi 5 for the ros2-delivery-drone project.

## Prerequisites

- Raspberry Pi 5 (8GB RAM)
- MicroSD card (64GB) flashed with Raspbian (Bookworm/Trixie) via Raspberry Pi Imager
  - Set hostname: `beerpi`
  - Set username/password
  - Configured WiFi credentials during flashing
- RPi Camera Module connected via CSI ribbon cable
- USB-C cable for power

## 1. Discover the Pi on the Network

From WSL2, mDNS (`.local`) doesn't work across the NAT boundary. Use PowerShell on the Windows host to resolve:

```powershell
Resolve-DnsName beerpi.local
```

This returned `10.0.0.193`.

## 2. Set Up SSH Key Access

Generate a key and copy it to the Pi (one-time interactive step):

```bash
ssh-keygen -t ed25519 -f ~/.ssh/beerpi_key -N ""
ssh-copy-id -i ~/.ssh/beerpi_key.pub beerpi@10.0.0.193
```

After this, connect non-interactively:

```bash
ssh -i ~/.ssh/beerpi_key beerpi@10.0.0.193
```

## 3. Install Docker

```bash
curl -fsSL https://get.docker.com | sh
```

Then add the user to the `docker` group so `docker` commands don't require `sudo`:

```bash
sudo usermod -aG docker $USER
```

> **Note:** You must log out and back in (or start a new SSH session) for the group change to take effect.

## 4. Install Git

```bash
sudo apt-get install -y git
```

(Was already present on this Raspbian image.)

## 5. Clone Repo

```bash
git clone https://github.com/westyvi/ros2-delivery-drone.git
cd ros2-delivery-drone
```

## 6. Build Docker Image Locally

> **Note:** The multi-arch DockerHub image (`westyvi/ros2-delivery-drone:latest`) had amd64
> binaries in the arm64 layer due to GHA cache contamination between the amd64 test build and
> the multi-arch push (shared `cache-from: type=gha`). This was fixed by separating cache
> scopes in the CI workflow. If you still encounter `cannot execute binary file` errors after
> pulling, build locally with `--pull` as shown below.

```bash
docker build --pull -f .devcontainer/Dockerfile -t ros2-drone .
```

**Important:** Use `--pull` to force Docker to fetch the correct arm64 base image from
upstream. Without it, Docker may reuse cached amd64 layers from a previously pulled broken
image.

This takes ~15-20 minutes on the Pi (large base image + pip install mediapipe for arm64).

## 7. Verify Camera

The RPi Camera Module (CSI) appears under the `rp1-cfe` platform device:

```bash
v4l2-ctl --list-devices
```

Key output:
```
rp1-cfe (platform:1f00110000.csi):
    /dev/video0  <-- main capture device
    /dev/video1
    ...
```

## 8. Run the Container

```bash
docker run --privileged --network=host \
  -v ~/ros2-delivery-drone:/workspace \
  -it ros2-drone
```

Inside the container:

```bash
cd /workspace
colcon build --symlink-install
source install/setup.bash

# Run full system (parameters loaded from YAML config files in drone_bringup/config/)
ros2 launch drone_bringup full_system.launch.py

# Or run individual nodes with inline parameter overrides
ros2 run hand_detection palm_detector_node --ros-args \
  -p camera_id:=0 \
  -p publish_debug_frames:=true
```

## 9. View Debug Images from Dev Machine

From a machine with ROS2 on the same network (same `ROS_DOMAIN_ID`, default 0):

```bash
ros2 topic list
ros2 run rqt_image_view rqt_image_view /hand_detection/debug_image
```
