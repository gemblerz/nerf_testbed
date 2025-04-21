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