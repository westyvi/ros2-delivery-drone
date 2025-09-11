# Use the official ROS 2 Jazzy image as the base
FROM ros:jazzy-perception

SHELL ["/bin/bash", "-c"]

# Install additional tools and dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-venv \ 
    x11-apps \
    && rm -rf /var/lib/apt/lists/*
    
# Create a directory for the virtual environment and set it up
# system site packages gives venv access to system (jazzy) packages necessary for ros2
RUN python3 -m venv --system-site-packages /opt/venv && \ 
    source /opt/venv/bin/activate && \
    python3 -m pip install mediapipe numpy
    
# Set up the workspace
WORKDIR /workspace

# Source the ROS 2 setup file in every new shell
RUN echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc

# Set the entrypoint
ENTRYPOINT ["/bin/bash"]
