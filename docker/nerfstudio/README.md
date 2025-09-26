# NerfStudio for Jetson Orin

> WARNING: [Dockerfile.jp61](./Dockerfile.jp61) succeeds on building but fails at runtime due to a possible version mismatch issue in the cudnn and cublas for memory allocation when trying to train a Nerf model.

Dusty has nerfstudio available for Docker build. Follow [this image](https://github.com/dusty-nv/jetson-containers/tree/master/packages/3d/nerf/nerfstudio) and run,

```bash
# on https://github.com/dusty-nv/jetson-containers
jetson-containers build nerfstudio:1.1.7
```