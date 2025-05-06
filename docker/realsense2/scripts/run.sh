#!/bin/bash

docker rm -f isaac-vslam

docker run -d \
  --name isaac-vslam \
  --privileged \
  --network host \
  --runtime nvidia \
  --volume $(pwd):/data \
  --entrypoint /bin/bash \
  gemblerz/ros-isaac-realsense2:humble \
  -c 'while true; do sleep 1; done'


#!/bin/bash

#   camera_node_namespace:="" \



ros2 launch mylaunch.py \
  camera_node_name:=camera \
  camera_rgb_profile:=848x480x15 \
  camera_depth_profile:=848x480x15 \
  image_jitter_threshold:=66.0 \
  enable_image_denoise:=False \
  enable_align_depth:=True

  # camera_rgb_profile:=848x480x15 \
  # camera_depth_profile:=848x480x15 \

  # camera_rgb_profile:=1280x720x15 \
  # camera_depth_profile:=1280x720x15 \


/app/launch.sh \
  camera_node_name:=camera \
  camera_rgb_profile:=848x480x15 \
  camera_depth_profile:=848x480x15 \
  image_jitter_threshold:=80.0 \
  enable_image_denoise:=False \
  enable_align_depth:=True