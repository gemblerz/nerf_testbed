# SPDX-FileCopyrightText: NVIDIA CORPORATION & AFFILIATES
# Copyright (c) 2021-2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

import launch
from launch_ros.actions import ComposableNodeContainer, Node
from launch_ros.descriptions import ComposableNode

from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    camera_node_name = LaunchConfiguration('camera_node_name')
    camera_node_namespace = LaunchConfiguration('camera_node_namespace')
    camera_rgb_profile = LaunchConfiguration('camera_rgb_profile')
    camera_depth_profile = LaunchConfiguration('camera_depth_profile')
    image_jitter_threshold = LaunchConfiguration('image_jitter_threshold')
    enable_image_denoise = LaunchConfiguration('enable_image_denoise')
    enable_align_depth = LaunchConfiguration('enable_align_depth')

    camera_node_name_arg = DeclareLaunchArgument(
        'camera_node_name',
        default_value='camera',
        description='Name of the camera ROS2 node (default: "camera")'
    )
    camera_node_namespace_arg = DeclareLaunchArgument(
        'camera_node_namespace',
        default_value='',
        description='Namespace for the camera ROS2 node (default: "")'
    )
    camera_rgb_profile_arg = DeclareLaunchArgument(
        'camera_rgb_profile',
        default_value='848x480x15',
        description='Camera RGB profile (default: "848x480x15")'
    )
    camera_depth_profile_arg = DeclareLaunchArgument(
        'camera_depth_profile',
        default_value='848x480x15',
        description='Camera depth profile (default: "848x480x15")'
    )
    image_jitter_threshold_arg = DeclareLaunchArgument(
        'image_jitter_threshold',
        default_value='22.00',
        description='Image jitter threshold in ms (default: 22.00)'
    )
    enable_image_denoise_arg = DeclareLaunchArgument(
        'enable_image_denoise',
        default_value='False',
        description='Enable image denoising (default: False)'
    )
    enable_align_depth_arg = DeclareLaunchArgument(
        'enable_align_depth',
        default_value='True',
        description='Enable depth alignment (default: True)'
    )

    """Launch file which brings up visual slam node configured for RealSense."""
    realsense_camera_node = Node(
        name=camera_node_name,
        namespace=camera_node_namespace,
        package='realsense2_camera',
        executable='realsense2_camera_node',
        parameters=[{
            'enable_infra1': True,
            'enable_infra2': True,
            'enable_color': True,
            'enable_depth': True,
            'align_depth.enable': enable_align_depth,
            'depth_module.emitter_enabled': 0,
            'rgb_camera.color_profile': camera_rgb_profile,
            'depth_module.depth_profile': camera_depth_profile,
            'depth_module.infra_profile': camera_depth_profile,
            'enable_gyro': True,
            'enable_accel': True,
            'gyro_fps': 200,
            'accel_fps': 200,
            'unite_imu_method': 2,
        }]
    )

    visual_slam_node = ComposableNode(
        name='visual_slam_node',
        package='isaac_ros_visual_slam',
        plugin='nvidia::isaac_ros::visual_slam::VisualSlamNode',
        parameters=[{
            'enable_image_denoising': enable_image_denoise,
            'rectified_images': True,
            'enable_imu_fusion': True,
            'gyro_noise_density': 0.000244,
            'gyro_random_walk': 0.000019393,
            'accel_noise_density': 0.001862,
            'accel_random_walk': 0.003,
            'calibration_frequency': 200.0,
            'image_jitter_threshold_ms': image_jitter_threshold,
            'base_frame': 'camera_link',
            'imu_frame': 'camera_gyro_optical_frame',
            'enable_slam_visualization': True,
            'enable_landmarks_view': True,
            'enable_observations_view': True,
            'camera_optical_frames': [
                'camera_infra1_optical_frame',
                'camera_infra2_optical_frame',
            ],
        }],
        remappings=[
            ('visual_slam/image_0', 'camera/infra1/image_rect_raw'),
            ('visual_slam/camera_info_0', 'camera/infra1/camera_info'),
            ('visual_slam/image_1', 'camera/infra2/image_rect_raw'),
            ('visual_slam/camera_info_1', 'camera/infra2/camera_info'),
            ('visual_slam/imu', 'camera/imu'),
        ],
    )

    visual_slam_launch_container = ComposableNodeContainer(
        name='visual_slam_launch_container',
        namespace='',
        package='rclcpp_components',
        executable='component_container',
        composable_node_descriptions=[visual_slam_node],
        output='screen',
    )

    return launch.LaunchDescription([
        camera_node_name_arg,
        camera_node_namespace_arg,
        camera_rgb_profile_arg,
        camera_depth_profile_arg,
        image_jitter_threshold_arg,
        enable_image_denoise_arg,
        enable_align_depth_arg,
        visual_slam_launch_container,
        realsense_camera_node
    ])