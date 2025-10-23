FROM ros:humble

RUN apt-get update \
  && apt-get install -y \
  wget \
  curl \
  nano \
  dumb-init \
  python3-pip \
  ros-humble-xacro \
  ros-humble-urdf-tutorial \
  ros-humble-rviz2

RUN pip3 install -U pip \
  && pip install pymycobot

# NOTE: Running ROS with root prohibits non-root users
#     to subscribe topics
RUN useradd -m -u 1000 ros \
  && usermod -aG dialout ros

USER ros
RUN mkdir -p /home/ros/colcon_ws/src \
  && cd /home/ros/colcon_ws/src \
  && git clone -b humble --depth 1 https://github.com/elephantrobotics/mycobot_ros2.git

RUN cd /home/ros/colcon_ws \
  && . /opt/ros/humble/setup.sh \
  && colcon build \
  && echo "source /home/ros/colcon_ws/install/setup.bash" >> /home/ros/.bashrc

COPY urdf /home/ros/urdf
COPY *.py /home/ros/

ENTRYPOINT ["/ros_entrypoint.sh"]