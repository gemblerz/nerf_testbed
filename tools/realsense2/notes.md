# Generating Point Cloud Directly from Realsense2 D455
The [list](https://dev.intelrealsense.com/docs/python2) of Python examples includes generating a pointcloud from the camera.

# Forwarding X11 to the Local from Remote in VScode
1. install xQuartz on the local machine (and reboot the system)
2. ForwardX11 yes in the ssh config
3. 

```bash
docker run -ti --rm --env DISPLAY=$DISPLAY --privileged --volume="$HOME/.Xauthority:/root/.Xauthority:rw" -v /tmp/.X11-unix:/tmp/.X11-unix -v /dev:/dev --entrypoint /bin/bash --network host gemblerz/ros-realsense2:humble
```

# Realsense-ros and Issac on Jetson
A few findings,
- The exact combination of the software libraries between librealsense, realsense-ros, and the device firmware are required (See [this](https://nvidia-isaac-ros.github.io/getting_started/hardware_setup/sensors/realsense_setup.html))
- The Realsense device needs some kernel drivers which are not supported in Jetpack 6 as of now. The recommended Jetpack is 5; confirmed that Orin Jp6 does not recognize the device while Xavier NX Jp 5.4.1 does (See [this](https://support.intelrealsense.com/hc/en-us/community/posts/31576776977427-cannot-connect-D455-on-jetson-agx-orin?page=1#community_comment_31577939626771) and [this](https://github.com/IntelRealSense/realsense_mipi_platform_driver) for details)

To run the Issac-realsense container,

```bash
docker run -ti --rm --privileged --network host --entrypoint /bin/bash -v /dev:/dev gemblerz/ros-issac-realsense2:humble
```

# Dual camera and calibration

```bash
ros2 launch realsense2_camera rs_launch.py serial_no:="'239622301386'" camera_name:='camera1' camera_namespace:='camera1' pointcloud.enable:=true rgb_camera.color_profile:=1280x720x15 depth_module.depth_profile:=848x480x15

ros2 launch realsense2_camera rs_launch.py serial_no:="'235422301960'" camera_name:='camera2' camera_namespace:='camera2' pointcloud.enable:=true rgb_camera.color_profile:=1280x720x15 depth_module.depth_profile:=848x480x15
```

Under the realsense-ros/realsense2_camera/scripts directory,
```bash
python3 set_cams_transforms.py camera1_link camera2_link 0 0 0 0 0 0
```

after calibration
```bash
# This does not seem to work well; the roll-pitch-yaw are not correctly transformed into the space
ros2 launch realsense2_camera rs_dual_camera_launch.py serial_no1:=_239622301386 serial_no2:=_235422301960 tf.translation.x:=0.18 tf.translation.y:=0.42 tf.translation.z:=0.0 tf.rotation.yaw:=-30.95 tf.rotation.pitch:=4.02 tf.rotation.roll:=4.8

# Doing a manual control
ros2 launch realsense2_camera rs_dual_camera_launch.py serial_no1:=_239622301386 serial_no2:=_235422301960 tf.translation.x:=0.18 tf.translation.y:=0.42 tf.translation.z:=0.0 tf.rotation.x:=0.04968284420351226 tf.rotation.y:=0.02260643738575159 tf.rotation.z:=-0.26783531644319325 tf.rotation.w:=0.9619172559250345
```