#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from sensor_msgs.msg import CompressedImage
from sensor_msgs.msg import CameraInfo
from nav_msgs.msg import Odometry


class ReceiverNode(Node):
    def __init__(self):
        super().__init__('receiver_node')
        topic_camera_info = "/camera/color/camera_info"
        topic_camera_raw_compressed = "/camera/color/image_raw/compressed"
        topic_camera_depth_aligned = "/camera/aligned_depth_to_color/image_raw"
        topic_camera_odometry = "/visual_slam/tracking/odometry"

        self.sub_a = self.create_subscription(
            CameraInfo, topic_camera_info, self.callback_camera_info, 10)
        self.sub_b = self.create_subscription(
            CompressedImage, topic_camera_raw_compressed, self.callback_camera_raw_compressed, 10)
        self.sub_c = self.create_subscription(
            Image, topic_camera_depth_aligned, self.callback_camera_depth_aligned, 10)
        self.sub_d = self.create_subscription(
            Odometry, topic_camera_odometry, self.callback_camera_odometry, 10)

        self.get_logger().info("Receiver node started, listening to the topics...")

    def callback_camera_info(self, msg):
        self.get_logger().info(f"Received: camera info width {msg.width}, height {msg.height}")

    def callback_camera_raw_compressed(self, msg):
        self.get_logger().info(f"Received: raw compressed image with format {msg.format}")

    def callback_camera_depth_aligned(self, msg):
        self.get_logger().info(f"Received: camera image width {msg.width}, height {msg.height}, encoding {msg.encoding}")

    def callback_camera_odometry(self, msg):
        self.get_logger().info(f"Received: camera pose {msg.pose}, twist {msg.twist}")

def main():
    rclpy.init()
    node = ReceiverNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down receiver node...")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
