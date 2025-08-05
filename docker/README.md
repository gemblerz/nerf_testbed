# Create Docker Image

Refer to each Dockerfile in the sub-directories for creating a Docker image.

# Docker Swarm

While it is possible to run containers using stanalone Docker, it is easy to perform the same using Docker Swarm. Also, configuring a performance monitoring tool on Swarm is probably easier than doing it with the Docker engine on individual nodes.

```bash
# the address should be the network visible to all nodes that will join the swarm.
docker swarm init --advertise-addr x.x.x.x
```

```bash
# other devices join to the swarm cluster
docker swarm join --token xxxxxxx x.x.x.x:2377
```

```bash
# verify the nodes in the cluster
$ docker node ls
ID                            HOSTNAME                    STATUS    AVAILABILITY   MANAGER STATUS   ENGINE VERSION
gf5b4sm3gmi8kovorevmyh3lz *   theone                      Ready     Active         Leader           26.1.3
sk7n5lncfkjbhexv1pastlpba     wd-agent-0000004E01B02738   Ready     Active                          24.0.2
```

# (Optional) Run Performance Monitoring

First, launch cadvisor in the swarm cluster,
```bash
docker service create --name cadvisor -l prometheus-job=cadvisor \
    --mode=global --publish published=8080,target=8080,mode=host \
    --mount type=bind,src=/var/run/docker.sock,dst=/var/run/docker.sock,ro \
    --mount type=bind,src=/,dst=/rootfs,ro \
    --mount type=bind,src=/var/run,dst=/var/run \
    --mount type=bind,src=/sys,dst=/sys,ro \
    --mount type=bind,src=/var/lib/docker,dst=/var/lib/docker,ro \
    gcr.io/cadvisor/cadvisor -docker_only
```

Then, run the monitoring solution using docker compose,
```bash
docker compose -f docker-compose-monitor.yml up -d
```

# Launch Realsense2 Docker Image on Devices

> NOTE: [Kubernetes YAMLs](../kubernetes/) can be used to run Realsense2 Docker images for testing Nvidia VSLAM. However, it is not trivial to use Nvidia Jetson for the launch because of unsupported DDS in Flannel and the missing kernel module for Cilium on Jetson. This Docker launch is an alternative way of doing the test by utilizing the host network.

## Running a Sender

> NOTE: [The camera system requirement from Nvidia VSLAM](https://nvidia-isaac-ros.github.io/repositories_and_packages/isaac_ros_visual_slam/index.html#camera-system-requirements) demonds 30 FPS at minimum. We may need to set the FPS to 30 from the camera and lower the resolution the process has a bottleneck.

```bash
docker run -ti --rm \
  --name vslam-rtx \
  --runtime nvidia \
  --privileged \
  --network host \
  gemblerz/ros-isaac-realsense2:3.2.0-humble-amd64-cuda \
  /app/launch.sh \
    camera_node_name:=camera \
    camera_rgb_profile:=848x480x30 \
    camera_depth_profile:=640x480x30 \
    image_jitter_threshold:=80.0 \
    enable_image_denoise:=False \
    enable_align_depth:=True
```

## Running a Receiver

```bash
docker run -ti --rm \
  --name vslam-rcv \
  --network host \
  --volume $(pwd):/data \
  --entrypoint /bin/bash \
  gemblerz/ros-isaac-realsense2:humble-amd64 \
  -c 'cd /data; source /opt/ros/humble/setup.bash; \
  ros2 bag record -o test \
  /tf \
  /tf_static \
  /camera/color/camera_info \
  /camera/color/image_raw/compressed \
  /camera/aligned_depth_to_color/image_raw \
  /visual_slam/tracking/odometry'
```