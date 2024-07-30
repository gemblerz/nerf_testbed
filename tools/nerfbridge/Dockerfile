FROM gemblerz/nerfstudio:cu118

RUN locale \
  && sudo apt update && sudo apt install locales \
  && sudo locale-gen en_US en_US.UTF-8 \
  && sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 \
  && echo "export LANG=en_US.UTF-8" \
  && locale

RUN sudo apt-get update \
  && sudo DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get install -y software-properties-common curl tzdata \
  && sudo add-apt-repository universe

RUN sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg \
  && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

RUN sudo apt-get update \
  && sudo apt-get install -y ros-humble-ros-base ros-dev-tools
RUN echo -e '\nsource /opt/ros/humble/setup.bash' >> /home/user/.bashrc


WORKDIR /code
COPY . /code/
# cvbridge3 is required by nerfbridge
RUN sudo pip3 install -U pip setuptools cvbridge3 \
  && sudo pip3 install -e .