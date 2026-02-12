#!/usr/bin/env python3
"""Single node combining camera capture, hand landmark detection, and palm-open publishing."""

import os
import time

import cv2
import mediapipe as mp
import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Bool


class PalmDetectorNode(Node):
    def __init__(self):
        super().__init__('palm_detector_node')

        # Declare ROS parameters
        self.declare_parameter('camera_id', 0)
        self.declare_parameter('publish_debug_frames', False)
        self.declare_parameter('image_size', 480)
        self.declare_parameter('capture_fps', 30)

        # Read parameters
        self.camera_id = self.get_parameter('camera_id').value
        self.publish_debug = self.get_parameter('publish_debug_frames').value
        self.image_size = self.get_parameter('image_size').value
        capture_fps = self.get_parameter('capture_fps').value

        # Publishers
        self.bool_publisher = self.create_publisher(Bool, '/openPalm_detection', 10)
        if self.publish_debug:
            self.img_publisher = self.create_publisher(Image, '/hand_detection/debug_image', 10)
            self.bridge = CvBridge()

        # Open camera
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            self.get_logger().error(f'Failed to open camera {self.camera_id}')

        # MediaPipe HandLandmarker setup
        package_path = os.path.dirname(__file__)
        model_path = os.path.join(package_path, 'resources', 'hand_landmarker.task')

        BaseOptions = mp.tasks.BaseOptions
        HandLandmarker = mp.tasks.vision.HandLandmarker
        HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
        VisionRunningMode = mp.tasks.vision.RunningMode
        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            num_hands=1,
            running_mode=VisionRunningMode.VIDEO)
        self.detector = HandLandmarker.create_from_options(options)

        # FPS tracking
        self.processing_times = []
        self.last_fps_report = time.time()

        # Timer-driven capture at configured FPS
        timer_period = 1.0 / capture_fps
        self.timer = self.create_timer(timer_period, self.timer_callback)

        self.get_logger().info(
            f'Palm detector started: camera={self.camera_id}, '
            f'fps={capture_fps}, debug_frames={self.publish_debug}')

    def timer_callback(self):
        if not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        if not ret:
            self.get_logger().error('Failed to read frame from camera', throttle_duration_sec=5.0)
            return

        start_time = time.time()

        # Convert BGR -> RGB and resize
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_rgb_resized = self._resize_image(frame_rgb)

        # Run MediaPipe detection
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb_resized)
        timestamp_ms = int(time.time() * 1e3)
        detection_result = self.detector.detect_for_video(mp_image, timestamp_ms)

        # Determine palm state and publish
        palm_open = self._is_palm_open(detection_result)
        self.bool_publisher.publish(Bool(data=palm_open))

        # Optionally publish debug image
        if self.publish_debug:
            annotated = self._draw_landmarks(mp_image.numpy_view(), detection_result)
            cv2_img = cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR)
            self.img_publisher.publish(self.bridge.cv2_to_imgmsg(cv2_img, 'bgr8'))

        # FPS reporting
        processing_time = time.time() - start_time
        self.processing_times.append(processing_time)
        if time.time() - self.last_fps_report > 5.0:
            avg_time = np.mean(self.processing_times[-50:])
            fps = 1.0 / avg_time if avg_time > 0 else 0
            self.get_logger().info(f'Average FPS: {fps:.1f}, Processing time: {avg_time*1000:.1f}ms')
            self.last_fps_report = time.time()

    def _is_palm_open(self, detection_result):
        if len(detection_result.hand_landmarks) < 1:
            return False

        keypoints = np.zeros((3, len(detection_result.hand_landmarks[0])))
        for i, keypoint in enumerate(detection_result.hand_landmarks[0]):
            keypoints[:, i] = np.array([keypoint.x, keypoint.y, keypoint.z])

        palm_indices = [5, 9, 13, 17]
        finger_indices = [8, 12, 16, 20]
        finger_extended_cutoff = 0.5
        for i, fidx in enumerate(finger_indices):
            pidx = palm_indices[i]
            finger_vector = keypoints[:, pidx] - keypoints[:, fidx]
            wrist2palm_vector = keypoints[:, 0] - keypoints[:, pidx]
            val = np.inner(finger_vector, wrist2palm_vector) / np.inner(wrist2palm_vector, wrist2palm_vector)
            if val < finger_extended_cutoff:
                return False
        return True

    def _resize_image(self, frame):
        height, width = frame.shape[:2]
        if max(height, width) > self.image_size:
            scale = self.image_size / max(height, width)
            return cv2.resize(frame, (int(width * scale), int(height * scale)))
        return frame

    def _draw_landmarks(self, rgb_image, detection_result):
        annotated_image = np.copy(rgb_image)
        drawing_utils = mp.tasks.vision.drawing_utils
        drawing_styles = mp.tasks.vision.drawing_styles
        hand_connections = mp.tasks.vision.HandLandmarksConnections.HAND_CONNECTIONS

        for idx in range(len(detection_result.hand_landmarks)):
            hand_landmarks = detection_result.hand_landmarks[idx]
            handedness = detection_result.handedness[idx]

            drawing_utils.draw_landmarks(
                annotated_image,
                hand_landmarks,
                hand_connections,
                drawing_styles.get_default_hand_landmarks_style(),
                drawing_styles.get_default_hand_connections_style())

            height, width, _ = annotated_image.shape
            x_coordinates = [lm.x for lm in hand_landmarks]
            y_coordinates = [lm.y for lm in hand_landmarks]
            text_x = int(min(x_coordinates) * width)
            text_y = int(min(y_coordinates) * height) - 10
            cv2.putText(annotated_image, f"{handedness[0].category_name}",
                        (text_x, text_y), cv2.FONT_HERSHEY_DUPLEX,
                        1, (88, 205, 54), 1, cv2.LINE_AA)

        return annotated_image

    def destroy_node(self):
        if self.cap.isOpened():
            self.cap.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = PalmDetectorNode()
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
