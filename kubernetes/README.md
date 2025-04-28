# Install K3S



```bash
#   K3S_CONFIG_FILE=/home/theone/k3s-config.yaml \
# Server
curl -sfL https://get.k3s.io | \
  sh -s - \
  --disable traefik \
  --agent-token myagent \
  --bind-address 10.31.82.1 \
  --advertise-address 10.31.82.1
```

```bash
# Jetson NX with JetPack 5.1.2
curl -sfL https://get.k3s.io | \
  K3S_URL=https://10.31.82.1:6443 \
  K3S_TOKEN=myagent \
  K3S_NODE_NAME=nx512 \
  sh -s - \
  --default-runtime nvidia
```

```bash
# Jetson Orin with JetPack 6.1
curl -sfL https://get.k3s.io | \
  K3S_URL=https://10.31.82.1:6443 \
  K3S_TOKEN=myagent \
  K3S_NODE_NAME=orin61 \
  sh -s - \
  --default-runtime nvidia
```

# ROS2 DDS Multicast and Kubernetes Network
Kubernetes CNI may not handle ROS2 discovery packets well some folks created a discovery service in Kubernetes (See [more](https://discourse.ros.org/t/ros-2-fast-dds-discovery-server-with-kubernetes/36086)).

__TODO: We need to figure out how we allow ROS2 nodes in different Pods to be discovered.__

One test case indicates a severy slow down in data collection when sending data over network.
- NX512 runs Nvidia VSLAM and publishes aligned-depto-to-color in a ROS2 topic at 30 Hz.
- When subscribing the ROS2 topic on the same device it reaches about 20 Hz.
- When doing the same on another device (Orin61) it reaches about 5 Hz.

This is because within the same node ROS2 utilizes zero-copy transfer but over the network ROS2 does not. This tells us the importance of processing data at local.

Another use case might be the same configuration but using a desktop machine and edge device.