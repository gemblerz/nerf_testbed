#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CompressedImage
from nav_msgs.msg import Odometry
from message_filters import ApproximateTimeSynchronizer, Subscriber

class SimpleSyncDemo(Node):
    def __init__(self):
        super().__init__('simple_sync_demo')
        
        # Create subscribers for different topics
        self.image_sub = Subscriber(self, CompressedImage, '/camera/color/image_raw/compressed_republished')
        self.odom_sub = Subscriber(self, Odometry, '/visual_slam/tracking/odometry')
        self.depth_sub = Subscriber(self, Image, '/camera/aligned_depth_to_color/image_raw_republished')
        
        # Set up ApproximateTimeSynchronizer
        # Parameters: [subscribers], queue_size, slop_time_seconds
        self.sync = ApproximateTimeSynchronizer(
            [self.image_sub, self.odom_sub, self.depth_sub], 
            queue_size=40, 
            slop=0.1  # Allow 0.1 seconds difference between messages
        )
        
        # Register the callback function
        self.sync.registerCallback(self.synchronized_callback)
        
        self.get_logger().info('SimpleSyncDemo node started. Waiting for synchronized messages...')
    
    def synchronized_callback(self, image_msg, odom_msg, depth_msg):
        """
        Callback function that receives synchronized messages
        """
        image_time = image_msg.header.stamp.sec + image_msg.header.stamp.nanosec * 1e-9
        odom_time = odom_msg.header.stamp.sec + odom_msg.header.stamp.nanosec * 1e-9
        depth_time = depth_msg.header.stamp.sec + depth_msg.header.stamp.nanosec * 1e-9
        
        print(f"\n--- Synchronized Messages Received ---")
        print(f"Compressed Image timestamp: {image_time:.6f}")
        print(f"Image format: {image_msg.format}")
        print(f"Image data size: {len(image_msg.data)} bytes")
        
        print(f"Odometry timestamp: {odom_time:.6f}")
        print(f"Position: x={odom_msg.pose.pose.position.x:.3f}, "
              f"y={odom_msg.pose.pose.position.y:.3f}, "
              f"z={odom_msg.pose.pose.position.z:.3f}")
        
        print(f"Depth Image timestamp: {depth_time:.6f}")
        print(f"Depth size: {depth_msg.width} x {depth_msg.height}")
        print(f"Depth encoding: {depth_msg.encoding}")
        
        max_time = max(image_time, odom_time, depth_time)
        min_time = min(image_time, odom_time, depth_time)
        print(f"Max time difference: {max_time - min_time:.6f} seconds")
        print("---------------------------------------")

def main(args=None):
    rclpy.init(args=args)
    
    try:
        node = SimpleSyncDemo()
        rclpy.spin(node)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        rclpy.shutdown()

if __name__ == '__main__':
    main()