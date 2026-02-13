FROM ros:jazzy-perception

SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get install -y python3-pip && rm -rf /var/lib/apt/lists/*

# Copy package.xml files for rosdep to resolve dependencies
COPY src/hand_detection/package.xml /tmp/hand_detection/package.xml
COPY src/servo_control/package.xml /tmp/servo_control/package.xml
COPY src/drone_bringup/package.xml /tmp/drone_bringup/package.xml

# Install dependencies: rosdep handles apt packages, pip handles mediapipe.
# --skip-keys excludes pip deps from rosdep (we install them directly below).
# --break-system-packages is safe in Docker (container is the system).
# numpy<2 prevents pip from trying to replace apt's numpy (no RECORD file).
RUN apt-get update && \
    rosdep update && \
    rosdep install --from-paths /tmp/hand_detection /tmp/servo_control /tmp/drone_bringup --ignore-src -r -y --skip-keys="python3-mediapipe-pip" && \
    pip3 install --break-system-packages "numpy<2" mediapipe && \
    rm -rf /var/lib/apt/lists/* /tmp/hand_detection /tmp/servo_control /tmp/drone_bringup

# On arm64 (RPi): overlay RPi-patched libcamera for PiSP camera support.
# ros-jazzy-libcamera is upstream v0.6.0, which lacks RPi5 PiSP patches.
# The RPi fork (v0.6.0+rpt) is ABI-compatible, so we extract the .deb files
# and overlay the patched libraries, IPA modules, and tuning data.
# Requires: docker run -v /run/udev:/run/udev:ro for camera enumeration.
ARG RPI_LIBCAMERA_VERSION=0.6.0+rpt20251202-1
RUN if [ "$(dpkg --print-architecture)" = "arm64" ]; then \
      cd /tmp && \
      curl -fsSL "http://archive.raspberrypi.com/debian/pool/main/libc/libcamera/libcamera0.6_${RPI_LIBCAMERA_VERSION}_arm64.deb" -o libcamera0.6.deb && \
      curl -fsSL "http://archive.raspberrypi.com/debian/pool/main/libc/libcamera/libcamera-ipa_${RPI_LIBCAMERA_VERSION}_arm64.deb" -o libcamera-ipa.deb && \
      mkdir rpi-cam && dpkg -x libcamera0.6.deb rpi-cam/ && dpkg -x libcamera-ipa.deb rpi-cam/ && \
      cp rpi-cam/usr/lib/aarch64-linux-gnu/libcamera.so.0.6.0 /opt/ros/jazzy/lib/ && \
      cp rpi-cam/usr/lib/aarch64-linux-gnu/libcamera-base.so.0.6.0 /opt/ros/jazzy/lib/ && \
      cp -f rpi-cam/usr/lib/aarch64-linux-gnu/libcamera/ipa/* /opt/ros/jazzy/lib/libcamera/ipa/ && \
      cp rpi-cam/usr/libexec/aarch64-linux-gnu/libcamera/* /opt/ros/jazzy/lib/libcamera/ && \
      cp -r rpi-cam/usr/share/libcamera/* /opt/ros/jazzy/share/libcamera/ && \
      rm -rf /tmp/rpi-cam /tmp/libcamera*.deb; \
    fi

# Point libcamera at the ROS install paths for IPA modules, proxies, and tuning data
ENV LIBCAMERA_IPA_MODULE_PATH=/opt/ros/jazzy/lib/libcamera/ipa
ENV LIBCAMERA_IPA_PROXY_PATH=/opt/ros/jazzy/lib/libcamera
ENV LIBCAMERA_IPA_CONFIG_PATH=/opt/ros/jazzy/share/libcamera/ipa

WORKDIR /workspace

RUN echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc

ENTRYPOINT ["/bin/bash"]
