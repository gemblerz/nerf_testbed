# Recording Realsense2 into ROS2 Bags
Intel Realsense cameras provide RGB images and its IMU measurements. This is a primary input for NerfStudio and NerfBridge. You can create ROS2 bags from the camera recordings and feed the bags to Nerf models later. This tool lets you record a ROS2 bag of realsense camera data.

> NOTE: You may follow the [instructions](https://dev.intelrealsense.com/docs/firmware-releases-d400) to update the camera firmware to up-to-date.

# Realsense Setting for NerfBridge
NerfBride's models require Nvidia VSLAM for camera pose data. 

[Nvidia issac ROS](https://nvidia-isaac-ros.github.io/repositories_and_packages/isaac_ros_visual_slam/isaac_ros_visual_slam/index.html#quickstart)
[Realsense ROS wrapper](https://dev.intelrealsense.com/docs/ros2-wrapper)

# Receiving Data from Realsense2 ROS2 Bags
This section is to demonstrate how to replay a ROS2 bag of Realsense2 data and subscribe ROS messages in Python.

## Download A Realsense2 ROS2 Bag
First, download a ROS2 data you want to replay. Here is an example from [nerfbridge](https://github.com/javieryu/nerf_bridge/blob/main/scripts/download_data.py). First, you download the dataset if you do not have the data.

```bash
mkdir repo
cd repo
git clone https://github.com/javieryu/nerf_bridge.git
cd nerf_bridge/scripts
python3 download_data.py
```

> You may run into the following error.
```bash
Traceback (most recent call last):
  File "/tmp/download_data.py", line 1, in <module>
    import gdown
ModuleNotFoundError: No module named 'gdown'
```

If so, please install the required Python package.
```bash
pip3 install gdown rich
```

## Replaying the ROS2 Bag and Receiving ROS Messages
Open one terminal and cd (change directory) to the directory of this document. Then,

```bash
export ROS_BAG_PATH=$HOME/repo/nerf_bridge/rosbags
docker run -ti --rm \
  --name rosplayer \
  --entrypoint /bin/bash \
  --volume $(pwd)/scripts/receiver.py:/app/receiver.py \
  --volume ${ROS_BAG_PATH}:/data \
  gemblerz/ros-isaac-realsense2:humble-amd64
```

```bash
# you should be inside the container you just ran
source /opt/ros/humble/setup.bash
python3 /app/receiver.py
```

You should see something like this.
```bash
[INFO] [1749579964.922603373] [receiver_node]: Receiver node started, listening to the topics...
```

Now, it is ready for you to play the ROS bag. Open another terminal and follow,
```bash
docker exec -ti rosplayer /bin/bash
```

Then, run the following,
```bash
source /opt/ros/humble/setup.bash
ros2 bag play /data/desk --start-paused
```

Press space on your keyboard to play the bag. The other terminal that is running the ROS receiver should print out messages as it receives from the bag. Now it is up to you to implement what you want from here.