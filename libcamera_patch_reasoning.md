# RPi libcamera Patch: Why and How

## The core problem

The Raspberry Pi Foundation maintains their own **fork** of the `libcamera` library. The "upstream" (original) `libcamera` is the open-source project maintained by the broader Linux community. The RPi Foundation takes that code, adds RPi-specific features, and publishes their version as `libcamera 0.6.0+rpt` (the `+rpt` means "Raspberry Pi tweaks").

When you install ROS2 Jazzy's camera packages (`ros-jazzy-libcamera`), you get the **upstream** v0.6.0 — the one without RPi-specific code. This is what's inside our Docker container since it's based on `ros:jazzy-perception` (Ubuntu).

On the Pi **host** (outside Docker), Raspbian ships the RPi fork. That's why `rpicam-hello` works fine on the host but `camera_ros` crashes inside the container.

## What are the PiSP patches?

**PiSP** = **Pi** **S**ignal **P**rocessor. It's the image processing hardware built into the RPi5's RP1 chip. When raw data comes off the camera sensor (our ov5647), it's just a grid of single-color pixels (a Bayer pattern). The PiSP hardware converts that into an actual color image — handling demosaicing, white balance, noise reduction, lens shading correction, etc.

The RPi5 uses PiSP. The RPi4 used an older ISP called "vc4". The upstream libcamera doesn't know how to talk to PiSP because it's RPi-proprietary hardware. The RPi fork adds the pipeline handler code that drives PiSP. Without it, libcamera sees the camera sensor but can't set up the processing pipeline, so it reports "no cameras available."

This is why you need this workaround specifically on RPi5. It's a consequence of the RPi Foundation adding custom silicon that the upstream Linux camera stack doesn't support yet. Eventually these patches may land upstream, but they haven't as of v0.6.0.

## What does "ABI-compatible" mean?

**ABI** = **A**pplication **B**inary **I**nterface. It's the contract between a compiled library (`.so` file) and the programs that use it.

Both the upstream and RPi fork expose `libcamera.so.0.6` — same SONAME (the version identifier baked into the shared library). This means any program compiled against upstream v0.6.0 (like `camera_ros`) can load the RPi fork's v0.6.0+rpt without recompilation. The function signatures, data structures, and calling conventions are identical. The RPi fork just *adds* internal pipeline code — it doesn't change the public API.

If the RPi fork were v0.7.0 (different SONAME `libcamera.so.0.7`), the dynamic linker would refuse to load it for `camera_ros`, which was compiled against `libcamera.so.0.6`. This is actually the situation we ran into — the RPi apt repo has already bumped `libcamera-ipa` to v0.7.0, so we had to grab the v0.6.0 `.deb` files directly from the archive pool.

## What are IPA modules and search paths?

**IPA** = **I**mage **P**rocessing **A**lgorithm. These are plugin `.so` files that libcamera loads at runtime to run camera-specific tuning algorithms (auto-exposure, auto-focus, color correction, etc.). They're separate from the main library so different cameras can have different algorithms.

The key IPA modules for RPi are:
- `ipa_rpi_pisp.so` — algorithms for RPi5's PiSP hardware
- `ipa_rpi_vc4.so` — algorithms for RPi4's vc4 hardware

Each IPA module has a paired **tuning file** (like `ov5647.json`) that contains camera-sensor-specific calibration data — how much lens shading to correct, color matrix coefficients, noise profiles, etc.

The **search path** is where libcamera looks for these plugins. The path is compiled into the `.so` at build time. The upstream library looks in `/opt/ros/jazzy/lib/libcamera/ipa` (where ROS installed it). The RPi fork looks in `/usr/lib/aarch64-linux-gnu/libcamera/ipa` (where Debian installed it).

This caused the first test failure — we mounted the RPi `.so` files at the ROS path, but the RPi library was still looking for IPA modules at the *Debian* path and not finding them. The fix was the `LIBCAMERA_IPA_MODULE_PATH` environment variable, which overrides the compiled-in search path.

## What does the udev mount do?

**udev** is Linux's device manager. When hardware is detected (camera plugged in, kernel driver loaded), udev creates device nodes (`/dev/video0`, `/dev/media0`) and stores metadata about each device in a database under `/run/udev/data/`.

libcamera uses this database to discover which `/dev/media*` devices are cameras, what sensor is attached, which ISP to use, etc. With `--privileged`, Docker gives the container access to all `/dev/*` nodes, but **not** the udev database. Without it, libcamera can see the device files but can't identify what they are, so it finds "no cameras."

The `-v /run/udev:/run/udev:ro` mount shares the host's udev database (read-only) with the container. This is a standard pattern for any Docker container that needs to work with hardware devices.

## How the Dockerfile changes map to all of this

Each piece and why it's there:

```dockerfile
ARG RPI_LIBCAMERA_VERSION=0.6.0+rpt20251202-1
```
Pins the exact RPi fork version. This must match the `libcamera.so.0.6` SONAME that `camera_ros` was compiled against.

```dockerfile
RUN if [ "$(dpkg --print-architecture)" = "arm64" ]; then \
```
Only runs on arm64 (RPi). On amd64 (CI/dev machines), there's no RPi camera hardware, so the upstream libcamera is fine.

```dockerfile
      curl ... libcamera0.6_...arm64.deb ... libcamera-ipa_...arm64.deb
      dpkg -x ... rpi-cam/
```
Downloads the RPi fork's `.deb` packages directly from the RPi archive and extracts them (without installing via apt, which would conflict with the ROS packages).

```dockerfile
      cp rpi-cam/.../libcamera.so.0.6.0 /opt/ros/jazzy/lib/
      cp rpi-cam/.../libcamera-base.so.0.6.0 /opt/ros/jazzy/lib/
```
Replaces the upstream `.so` files with the RPi fork ones. Since `LD_LIBRARY_PATH` from the ROS setup includes `/opt/ros/jazzy/lib/`, this is where `camera_ros` loads them from. This is the core fix — swapping in the PiSP-capable library.

```dockerfile
      cp -f rpi-cam/.../ipa/* /opt/ros/jazzy/lib/libcamera/ipa/
      cp rpi-cam/.../libcamera/* /opt/ros/jazzy/lib/libcamera/
      cp -r rpi-cam/.../libcamera/* /opt/ros/jazzy/share/libcamera/
```
Copies the RPi IPA plugin modules (`ipa_rpi_pisp.so`, `ipa_rpi_vc4.so`), the IPA proxy executable (`raspberrypi_ipa_proxy`), and tuning data files (`ov5647.json`, etc.) to the ROS paths.

```dockerfile
ENV LIBCAMERA_IPA_MODULE_PATH=/opt/ros/jazzy/lib/libcamera/ipa
ENV LIBCAMERA_IPA_PROXY_PATH=/opt/ros/jazzy/lib/libcamera
ENV LIBCAMERA_IPA_CONFIG_PATH=/opt/ros/jazzy/share/libcamera/ipa
```
Overrides the compiled-in search paths. Without these, the RPi library would look for IPA modules at `/usr/lib/aarch64-linux-gnu/libcamera/ipa` (where it was originally built to look), not find them, and fail with "Failed to load a suitable IPA library."

## Why is this so complicated?

It's the intersection of three ecosystems that don't coordinate:

1. **RPi Foundation** ships their own libcamera fork in Raspbian's apt repos
2. **ROS2** packages upstream libcamera in their own apt repos, installed at `/opt/ros/jazzy/`
3. **Docker** isolates the container from the host, so you can't just use the host's libraries

If RPi's PiSP patches were upstreamed (merged into the official libcamera), the ROS package would work out of the box. But hardware vendors often maintain their own forks, and it takes time for patches to flow upstream. Until then, this overlay approach bridges the gap.

## Alternatives considered

### 1. Use `v4l2_camera` instead of `camera_ros` (bypass libcamera)

**Not viable.** On RPi5, the V4L2 device nodes only output raw Bayer data — the PiSP ISP that converts it to RGB is only accessible through libcamera. There's no `bcm2835-v4l2` legacy module on RPi5 (deprecated, only worked on RPi4 and older). Using `libcamerify` (V4L2 compatibility shim) still requires the RPi libcamera fork internally.

### 2. Switch to a Raspbian/Debian base Docker image

**Doesn't help.** Even on Raspbian, `ros-jazzy-libcamera` installs upstream libcamera to `/opt/ros/jazzy/lib/`, and `camera_ros` links against that path via `LD_LIBRARY_PATH`. You'd still need the overlay. Meanwhile you'd lose Tier 1 ROS2 support, prebuilt packages, and depend on small community repos for ROS2 on Debian.

### 3. Add RPi apt repo and use `apt-get install`

**Broken for our version.** The RPi apt repo's current Packages index only lists `libcamera-ipa` v0.7.0, but `libcamera0.6` requires `libcamera-ipa = 0.6.0+rpt` (exact match). So `apt-get install libcamera0.6` fails with an unresolvable dependency. Even if it could install, the packages go to `/usr/lib/` not `/opt/ros/jazzy/lib/`, so you'd still need the overlay step.

### 4. Build RPi libcamera from source in the Dockerfile

**Viable fallback.** This is what [se1exin/camera_ros-in-docker-rpi5](https://github.com/se1exin/camera_ros-in-docker-rpi5) does. It eliminates the SONAME coupling risk since `camera_ros` is also built from source against the same library. Downsides: ~10-20 min build time on RPi5, larger image (build tools remain), more complex Dockerfile. This is the right fallback if our .deb overlay breaks due to a SONAME bump (e.g., ROS moves to libcamera 0.7).

### Why we chose the .deb overlay approach

- **Fast** (~3s download + extract vs 10-20 min source build)
- **Small** (no build tools left in image)
- **Stable** — the pinned .deb URL points to files in the RPi archive pool, which are never deleted even after leaving the Packages index
- **Clean removal path** — when RPi's PiSP patches land upstream, delete the `RUN` block and the `ENV` lines. The `if [ arm64 ]` guard means amd64 CI is unaffected either way
- **Known fragility** — if ROS bumps `ros-jazzy-libcamera` to a new SONAME (e.g., 0.7), the overlay breaks and we'd need to update `RPI_LIBCAMERA_VERSION` or switch to the source build fallback (option 4)
