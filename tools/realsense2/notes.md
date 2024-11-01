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