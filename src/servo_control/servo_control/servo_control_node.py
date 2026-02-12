#!/usr/bin/env python3
"""Servo control node — drives a servo via GPIO PWM for payload release."""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool


class ServoControlNode(Node):
    def __init__(self):
        super().__init__('servo_control_node')

        # Declare ROS parameters
        self.declare_parameter('gpio_pin', 18)
        self.declare_parameter('open_angle', 90.0)
        self.declare_parameter('closed_angle', 0.0)
        self.declare_parameter('simulate', False)

        # Read parameters
        self.gpio_pin = self.get_parameter('gpio_pin').value
        self.open_angle = self.get_parameter('open_angle').value
        self.closed_angle = self.get_parameter('closed_angle').value
        self.simulate = self.get_parameter('simulate').value

        # Current state
        self.is_open = False
        self.servo = None

        # Initialize GPIO (or fall back to simulation)
        if not self.simulate:
            self._init_gpio()
        else:
            self.get_logger().warn('Simulation mode enabled via parameter')

        # Subscriber and publisher
        self.command_sub = self.create_subscription(
            Bool, '/servo/command', self._command_callback, 10)
        self.state_pub = self.create_publisher(Bool, '/servo/state', 10)

        # Move to closed position on startup
        self._set_servo(False)

        mode = 'SIMULATE' if self.simulate else f'GPIO {self.gpio_pin}'
        self.get_logger().info(f'Servo control ready ({mode})')

    def _init_gpio(self):
        """Try to initialize gpiozero servo; fall back to simulation if unavailable."""
        # Check if running on Raspberry Pi
        try:
            with open('/sys/firmware/devicetree/base/model', 'r') as f:
                model = f.read()
            if 'Raspberry Pi' not in model:
                self.get_logger().warn(
                    f'Not a Raspberry Pi (model: {model.strip()}), '
                    'falling back to simulation mode')
                self.simulate = True
                return
        except FileNotFoundError:
            self.get_logger().warn(
                'Cannot detect board model, falling back to simulation mode')
            self.simulate = True
            return

        # Try to initialize gpiozero
        try:
            from gpiozero import Servo
            from gpiozero.pins.lgpio import LGPIOFactory

            factory = LGPIOFactory()
            # gpiozero Servo expects values -1 to 1; we map angles in _set_servo
            self.servo = Servo(self.gpio_pin, pin_factory=factory)
            self.get_logger().info(
                f'Servo ready on GPIO {self.gpio_pin} — '
                'ensure servo is physically connected')
        except Exception as e:
            self.get_logger().warn(
                f'GPIO init failed ({e}), falling back to simulation mode')
            self.simulate = True

    def _command_callback(self, msg: Bool):
        """Handle servo command: True = open, False = close."""
        self._set_servo(msg.data)

    def _set_servo(self, open_servo: bool):
        """Move servo to open or closed position and publish state."""
        self.is_open = open_servo
        angle = self.open_angle if open_servo else self.closed_angle
        state_str = 'OPEN' if open_servo else 'CLOSED'

        if self.simulate:
            self.get_logger().info(f'[SIMULATE] Servo {state_str} (angle={angle})')
        else:
            # Map angle (0-180) to gpiozero value (-1 to 1)
            value = (angle / 90.0) - 1.0
            value = max(-1.0, min(1.0, value))
            self.servo.value = value
            self.get_logger().info(f'Servo {state_str} (angle={angle})')

        self.state_pub.publish(Bool(data=self.is_open))

    def destroy_node(self):
        if self.servo is not None:
            self.servo.detach()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = ServoControlNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
