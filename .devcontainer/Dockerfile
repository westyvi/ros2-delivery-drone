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

WORKDIR /workspace

RUN echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc

ENTRYPOINT ["/bin/bash"]
