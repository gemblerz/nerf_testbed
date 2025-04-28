# Recording Realsense2 into ROS2 Bags
Intel Realsense cameras provide RGB images and its IMU measurements. This is a primary input for NerfStudio and NerfBridge. You can create ROS2 bags from the camera recordings and feed the bags to Nerf models later. This tool lets you record a ROS2 bag of realsense camera data.

> NOTE: You may follow the [instructions](https://dev.intelrealsense.com/docs/firmware-releases-d400) to update the camera firmware to up-to-date.

# Realsense Setting for NerfBridge
NerfBride's models require Nvidia VSLAM for camera pose data. 

[Nvidia issac ROS](https://nvidia-isaac-ros.github.io/repositories_and_packages/isaac_ros_visual_slam/isaac_ros_visual_slam/index.html#quickstart)
[Realsense ROS wrapper](https://dev.intelrealsense.com/docs/ros2-wrapper)