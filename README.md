# ros2-delivery-drone

## Overview
This repo contains all code to make my delivery drone work. The drone uses two cameras for perception: one Oak Lite camera facing forward and running a pose estimation neural network to detect human locations, and one rasbperry pi camera facing down to detect an open palm. The drone navigates to specified GPS coordinates, detects a person raising their hand, and enters a hover in front of them. When the belly camera detects an open palm (using google's hand keypoint detector network on an rpi5), the drone releases the payload and returns home. 

## Setup

Install [Docker](https://docs.docker.com/engine/install/ubuntu/) (recommend via apt for lightweight). You may need to [Add your user to the docker group](https://docs.docker.com/engine/install/linux-postinstall/).

Open the project in VSCode and reopen in container. It may prompt you for this, or you can do ctrl+shift+p and search it. Ensure dev containers extension is installed. 

## Building and Running the Project

Once in the container, to build the project:
colcon build
source install/setup.bash
