# Use the official ROS 2 Jazzy image as the base
FROM ros:jazzy

SHELL ["/bin/bash", "-c"]

#ARG DEBIAN_FRONTEND=noninteractive
#ARG USER_UID=1000
#ARG USER_GID=1000

# Install additional tools and dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-colcon-common-extensions \
    python3-venv \
    git \
    vim \
    bash-completion \
    ros-jazzy-cv-bridge \
    python-is-python3 \
    python3-dev \
    python3-tk \
    # install lots of dependencies for matplotlib
    libfreetype6-dev \
    libpng-dev \
    libxft-dev \
    libjpeg-dev \
    zlib1g-dev \
    libblas-dev \
    liblapack-dev \
    gfortran \
    # end matplotlib dependencies
    # ping utility to test docker container internet connectivity
    iputils-ping \
    && rm -rf /var/lib/apt/lists/* \
    && ping -c 4 google.com

# Set up a virtual environment
#RUN python3 -m venv /opt/venv
#ENV PATH="/opt/venv/bin:$PATH"
#RUN mkdir -p ~/coclon_venv/src \ 
 #   cd ~/coclon_venv/src \
  #  virtualenv -p python3 ./venv \ 
   # source ./venv/bin/activate \
    #touch ./venv/COLCON_IGNORE

# Set up a virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip
#RUN pip install --user --no-cache-dir matplotlib
RUN pip install --no-cache-dir numpy
RUN pip install --no-cache-dir mediapipe

#RUN pip install --user --no-cache-dir matplotlib numpy mediapipe
ENV PATH="home/developer/local/bin:${PATH}"

# Set up the workspace
WORKDIR /workspace

# Source the ROS 2 setup file in every new shell
RUN echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc

# Set the entrypoint
ENTRYPOINT ["/bin/bash"]
