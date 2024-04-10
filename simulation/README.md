# Simulation setup using Gazebo

## Install
Please follow https://gazebosim.org/docs/harmonic/install

## Run
Run Gazebo server,
```bash
gz sim -s world.sdf
```

On another terminal run a Gazebo GUI,
__NOTE: on Linux both server and gui can run in one command, but need to be separated for Mac__
```bash
gz sim -g
```

## Getting images from the simulator
Please note that this is still a manual step to get a series of images from the simulator as Gazebo's Python wrapper is not straight forward to follow. On each terminal you have to subscribe each camera topic to receive frames,

```bash
# for the topic /camera1
gz topic -t /camera1 -e --json-output > camera1.bag
```

After getting some frames, each .bag will have JSON blobs containing frames. Please refer to the [notebook](notebook.ipynb) to produce dataset with meta information about the camera, e.g. world coordination, image resolution, etc.