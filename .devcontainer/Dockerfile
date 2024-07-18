# Use the official ROS 2 Jazzy image as the base
FROM ros:jazzy

SHELL ["/bin/bash", "-c"]

ARG DEBIAN_FRONTEND=noninteractive
ARG USER_UID=1000
ARG USER_GID=1000

# Install additional tools and dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-colcon-common-extensions \
    git \
    vim \
    bash-completion \
    && rm -rf /var/lib/apt/lists/*

# Set up the workspace
WORKDIR /workspace

# Source the ROS 2 setup file in every new shell
RUN echo "source /opt/ros/jazzy/setup.bash" >> /etc/bash.bashrc

# Set the entrypoint
ENTRYPOINT ["/bin/bash"]
