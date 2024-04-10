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
Please note that this is still a manual step to get a series of images from the simulator as Gazebo's Python wrapper is not straight forward to follow.

First, create a meta information about objects in the simulator. We assume the camera objects are not moving so that taking a few messages on the meta information is enough.

```bash
# Please follow printed instructions,
# i.e. you will need to run the command and
# press control + C a couple of seconds later
./create_meta.sh
```
Please make sure you have info.bag file created that contains orientation and position of the cameras.

Then, run the following to receive frames.

```bash
python3 subscribe.py -t camera1 -t camera2 -t camera3 -t camera4
```

Finally, run the simulator from the Gazebo GUI and stop the simulator and the above Pytyhon command after collecting a reasonable amount of frames.

## Converting frames into Nerf dataset
After getting some frames, each .bag will have JSON blobs containing frames. Please refer to the [notebook](notebook.ipynb) to produce dataset with meta information about the camera, e.g. world coordination, image resolution, etc.