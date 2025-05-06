# Install K3S with Cilium Network Backend

ROS2 uses network DDS to exchange messages, and the default network, Flannel, does not support this network layer (See [more](https://discourse.ros.org/t/ros-2-dds-flying-in-cloud-with-cilium-kubernetes/36845)). We install K3S with Cilium to support the layer and allow Pods to run ROS pub/sub.

```bash
#   K3S_CONFIG_FILE=/home/theone/k3s-config.yaml \
# Server
curl -sfL https://get.k3s.io | \
  sh -s - \
  --disable traefik \
  --agent-token myagent \
  --bind-address 10.31.82.1 \
  --advertise-address 10.31.82.1 \
  --flannel-backend=none \
  --disable-network-policy
```

Install Cilium (See [the installation](https://docs.cilium.io/en/stable/installation/k3s/)).
```bash
CILIUM_CLI_VERSION=$(curl -s https://raw.githubusercontent.com/cilium/cilium-cli/main/stable.txt)
CLI_ARCH=amd64
if [ "$(uname -m)" = "aarch64" ]; then CLI_ARCH=arm64; fi
curl -L --fail --remote-name-all https://github.com/cilium/cilium-cli/releases/download/${CILIUM_CLI_VERSION}/cilium-linux-${CLI_ARCH}.tar.gz{,.sha256sum}
sha256sum --check cilium-linux-${CLI_ARCH}.tar.gz.sha256sum
sudo tar xzvfC cilium-linux-${CLI_ARCH}.tar.gz /usr/local/bin
rm cilium-linux-${CLI_ARCH}.tar.gz{,.sha256sum}
```

We then need to enable multicast in Cilium (See [more](https://github.com/fujitatomoya/ros_k8s/blob/main/docs/Setup_Kubernetes_Cluster.md#enable-multicast)).

```bash
# Jetson NX with JetPack 5.1.2
curl -sfL https://get.k3s.io | \
  K3S_URL=https://10.31.82.1:6443 \
  K3S_TOKEN=myagent \
  K3S_NODE_NAME=nx512 \
  sh -s - \
  --default-runtime nvidia
```

> Jetpack 5 does not come with `CONFIG_NF_TABLES` being set, which causes it to fail in setting iptables. A dead-end.

```bash
# Jetson Orin with JetPack 6.1
curl -sfL https://get.k3s.io | \
  K3S_URL=https://10.31.82.1:6443 \
  K3S_TOKEN=myagent \
  K3S_NODE_NAME=orin61 \
  sh -s - \
  --default-runtime nvidia
```

# Desktop with RTX2080
curl -sfL https://get.k3s.io | \
  K3S_URL=https://10.31.82.1:6443 \
  K3S_TOKEN=myagent \
  K3S_NODE_NAME=rtx2080 \
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