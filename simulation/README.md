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
./create_info.sh
```
Please make sure you have `info.bag` file created that contains orientation and position of the cameras.

Second, do the same again for obtaining camera intrinsic information

```bash
# Please follow printed instructions,
# i.e. you will need to run the command and
# press control + C a couple of seconds later
./create_camera_info.sh
```

Then, run the following to receive frames.

```bash
python3 subscribe.py -t camera1 -t camera2 -t camera3 -t camera4
```

Finally, run the simulator from the Gazebo GUI and stop the simulator and the above Pytyhon command after collecting a reasonable amount of frames.

## Converting frames into a Nerf dataset
After getting some frames, each .bag will have JSON blobs containing frames.

```bash
python3 to_nerfdataset.py \
  --input-dir /path/to/bags \
  --output-dir /path/to/output
```

In `/path/to/output` a directory with images will be created. And, `transforms.json` will contain camera intrinsic and extrinsic information for each image in the directory. The entire output directory is accepted by Nerfstudio.

__NOTE: details for camera [intrinsics](https://docs.nerf.studio/quickstart/data_conventions.html#camera-intrinsics) and [extrinsics](https://docs.nerf.studio/quickstart/data_conventions.html#camera-extrinsics).__

## Running Nerfstudio using the dataset
When training a Nerf model using the dataset, the default dataset loader does some transformation and scaling (See [Github Issue](https://github.com/nerfstudio-project/nerfstudio/issues/1101).) We will need to disable those calculations because they are not needed (only needed for OpenCV -> OpenCL coordinate conversion, which should happen for datasets generated by Colmap.) Here is the flags when training,

```bash
# you can find more options by 
# ns-train nerfacto nerfstudio-data --help
ns-train nerfacto nerfstudio-data \
  --data data/nerfstudio/guy/ \
  --orientation-method none \
  --center-method none \
  --auto-scale-poses False
```