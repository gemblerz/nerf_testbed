# Nerfbridge

[Nerf_bridge](https://github.com/javieryu/nerf_bridge) introduces ROS2 communication to Nerfstudio to stream images from ROS2 topics to train and visualize the rosnerfacto model in Nerfstudio.

To build a container for nerfbridge,

```bash
git clone https://github.com/javieryu/nerf_bridge.git
cp Dockerfile nerf_bridge/
cd nerf_bridge
docker build -t gemblerz/nerfbridge:cu118-ros2humble .
```

## Training
By default, the training runs for 30K iterations, with a fixed number of images (10?). If new images come from the ROS2 topic, those images get updated while the training is using them.

## Viewer
It is necessary to disable showing the training image because they don't exist (and they are from the ROS2 bag),

```bash
ns-viewer \
  --viewer.max-num-display-images 0 \
  --load-config outputs/configs/ros-depth-nerfacto/2024-09-06_180515/config.yml
```