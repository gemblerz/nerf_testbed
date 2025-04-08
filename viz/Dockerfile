FROM osrf/ros:humble-desktop

COPY data/foxglove-studio-latest-linux-amd64.deb /tmp/foxglove-studio-latest-linux-amd64.deb
RUN apt-get update \
  && apt-get install -y ros-humble-foxglove-bridge \
  && apt-get install -y /tmp/foxglove-studio-latest-linux-amd64.deb


CMD ["foxglove-studio"]