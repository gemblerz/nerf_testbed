FROM ros:humble

RUN apt-get update \
  && apt-get install -y \
  ros-humble-librealsense2* \
  wget \
  curl \
  nano

RUN apt-get install -y \
  ros-humble-realsense2-* \
  ros-humble-rviz2

ENTRYPOINT ["/ros_entrypoint.sh"]