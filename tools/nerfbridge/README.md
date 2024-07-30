# Nerfbridge

[Nerf_bridge](https://github.com/javieryu/nerf_bridge) introduces ROS2 communication to Nerfstudio to stream images from ROS2 topics to train and visualize the rosnerfacto model in Nerfstudio.

To build a container for nerfbridge,

```bash
git clone https://github.com/javieryu/nerf_bridge.git
cp Dockerfile nerf_bridge/
cd nerf_bridge
docker build -t gemblerz/nerfbridge:cu118-ros2humble .
```