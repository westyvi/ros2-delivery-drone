from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'servo_control'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob(os.path.join('launch', '*launch.[pxy][yma]*'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='root',
    maintainer_email='79417323+westyvi@users.noreply.github.com',
    description='ROS2 servo control for drone payload release',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'servo_control_node = servo_control.servo_control_node:main',
        ],
    },
)
