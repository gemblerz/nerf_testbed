#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage, Image
import time
import argparse


class TopicRepublisher(Node):
    def __init__(self, republish_rate=1.0):
        super().__init__('topic_republisher')
        
        # Configuration
        self.republish_rate = republish_rate
        self.rate_interval = 1.0 / republish_rate  # Convert Hz to seconds
        
        # Topics to republish
        self.topics = {
            '/camera/color/image_raw/compressed': CompressedImage,
            '/camera/aligned_depth_to_color/image_raw': Image
        }
        
        # Track last publish times
        self.last_publish_times = {}
        
        # Setup subscribers and publishers
        self.topic_subscribers = {}
        self.topic_publishers = {}
        
        for topic_name, msg_type in self.topics.items():
            # Initialize last publish time
            self.last_publish_times[topic_name] = 0
            
            # Create subscriber for original topic
            self.topic_subscribers[topic_name] = self.create_subscription(
                msg_type,
                topic_name,
                lambda msg, topic=topic_name: self._rate_limited_callback(msg, topic),
                10
            )
            
            # Create publisher for republished topic
            republished_topic = f"{topic_name}_republished"
            self.topic_publishers[topic_name] = self.create_publisher(
                msg_type,
                republished_topic,
                10
            )
            
            self.get_logger().info(f'Setup republishing: {topic_name} -> {republished_topic} at {republish_rate} Hz')
        
        self.get_logger().info(f'Topic republisher initialized at {republish_rate} Hz')

    def _rate_limited_callback(self, msg, topic_name):
        """Callback that republishes messages at the specified rate"""
        current_time = time.time()
        last_time = self.last_publish_times.get(topic_name, 0)
        
        if current_time - last_time >= self.rate_interval:
            if topic_name in self.topic_publishers:
                self.topic_publishers[topic_name].publish(msg)
                self.last_publish_times[topic_name] = current_time
                self.get_logger().debug(f'Republished message for {topic_name}')


def main(args=None):
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='ROS2 Topic Republisher')
    parser.add_argument('--rate', type=float, default=1.0, 
                       help='Republish rate in Hz (default: 1.0)')
    
    # Parse known args to avoid conflicts with ROS2 args
    parsed_args, unknown = parser.parse_known_args()
    
    rclpy.init(args=unknown)
    
    republisher_node = TopicRepublisher(republish_rate=parsed_args.rate)
    
    try:
        print(f"Republishing topics at {parsed_args.rate} Hz... Press Ctrl+C to stop")
        rclpy.spin(republisher_node)
    except KeyboardInterrupt:
        print("\nStopping republisher...")
    finally:
        republisher_node.destroy_node()
        rclpy.shutdown()
        print("Republisher stopped!")


if __name__ == '__main__':
    main()