import argparse
import logging
from base64 import b64decode
from pathlib import Path
import json
from typing import Tuple, Union
from types import ModuleType

from scipy.spatial.transform import Rotation as R
import numpy as np
from PIL import Image


def decode_timestamp(stamp: dict) -> float:
    # Returns timestamp from given dict timestamp
    sec = 0.
    if "sec" in stamp:
        sec = int(stamp["sec"])
    return sec + (float(stamp["nsec"]) / 1e9)


def create_image_from_record(d: dict) -> Image:
    # Returns decoded image from a json blob
    raw = b64decode(d["data"])
    pixel_format = d["pixelFormatType"]
    desired_format = "RGB" if pixel_format == "RGB_INT8" else ""
    w = d["width"]
    h = d["height"]
    size = (w, h)
    return Image.frombytes(desired_format, size, raw)


def create_image_from_bag_at_index(bag_path: Path, index: int=0) -> Tuple[ModuleType, str]:
    # Returns an image from given bag at given index
    count = 0
    with open(bag_path, "r") as f:
        for l in f.readlines():
            if count < index:
                count += 1
                continue
            d = json.loads(l)
            img = create_image_from_record(d)

            t = decode_timestamp(d["header"]["stamp"])
            sequence = 0
            for i in d["header"]["data"]:
                if i["key"] == "seq":
                    sequence = int(i["value"][0])
                    break
            return img, f'frame_{bag_path.stem}_{t}.jpg'


def load_camera_intrinsics_from_bag(p: Path) -> dict:
    # Since all the cameras share the same characteristics
    # we return the first record
    # details can be found https://docs.ros.org/en/melodic/api/sensor_msgs/html/msg/CameraInfo.html
    # cameras = {}
    with p.open("r") as file:
        for l in file:
            return json.loads(l)


def generate_matrix_for_nerfstudio(P: dict, O: dict) -> np.ndarray:
    np.set_printoptions(suppress=True)
    # nerfstudio format
    # [+X0 +Y0 +Z0 X]
    # [+X1 +Y1 +Z1 Y]
    # [+X2 +Y2 +Z2 Z]
    # [0.0 0.0 0.0 1]
    pos = np.array([[P["x"], P["y"], P["z"]]], dtype=float).T
    rot = R.from_quat(
        [O["x"], O["y"], O["z"], O["w"]]
        )
    logging.debug(f'rotation in degrees for zyx: {rot.as_euler('zyx', degrees=True)}')
    pos_rot = np.hstack((rot.as_matrix(), pos))
    logging.debug(f'rotation and transformation: {pos_rot}')
    return np.vstack((pos_rot, np.array([0., 0., 0., 1.], dtype=float)))


def load_camera_extrinsics_from_bag(p: Path) -> dict:
    # each line holds the entire information we need
    with p.open("r") as f:
        d = json.loads(f.readline())

    objects = {}
    for e in d["pose"]:
        pos = {
            "x": 0.,
            "y": 0.,
            "z": 0.,
        }
        pos.update(e["position"])
        orientation = {
            "x": 0.,
            "y": 0.,
            "z": 0.,
            "w": 0.,
        }
        orientation.update(e["orientation"])
        logging.debug(f'generating matrix for {e["name"]}.')
        matrix = generate_matrix_for_nerfstudio(pos, orientation)
        objects[e["name"]] = matrix
    return objects


def build_dataset(images: list, intrinsics: dict, extrinsics: dict) -> dict:
    # Intrinsic camera matrix for the raw (distorted) images.
    #     [fx  0 cx]
    # K = [ 0 fy cy]
    #     [ 0  0  1]
    o = {
        "fl_x": intrinsics["intrinsics"]["k"][0],
        "fl_y": intrinsics["intrinsics"]["k"][4],
        "cx": intrinsics["intrinsics"]["k"][2],
        "cy": intrinsics["intrinsics"]["k"][5],
        "w": intrinsics["width"],
        "h": intrinsics["height"],
        "k1": 0.0, # intrinsics["distortion"]["k"][0],
        "k2": 0.0, # intrinsics["distortion"]["k"][1],
        "k3": 0.0,
        "k4": 0.0,
        "p1": 0.0,
        "p2": 0.0,
    }
    frames = []
    for camera_name, file_path in images:
        if camera_name not in extrinsics:
            logging.error(f'no camera extrinsics found for {camera_name}. Skipping')
            continue
        
        e = extrinsics[camera_name]
        logging.debug(f'adding {file_path} to frames')
        frames.append({
            "file_path": f'./{file_path}',
            "transform_matrix": e.tolist()
        })
    o.update({
        "frames": frames
    })
    return o

def main(args):
    output_dir = Path(args.output_dir)
    output_images_subdir = "images"
    output_dir.joinpath(output_images_subdir).mkdir(parents=True, exist_ok=True)
    logging.info(f'Output directory: {output_dir} created.')
    
    input_dir = Path(args.input_dir)
    frames = []
    for bag in input_dir.glob("*.bag"):
        if bag.stem == "camera_info":
            # extract camera intrinsics
            camera_intrinsics = load_camera_intrinsics_from_bag(bag)
        elif bag.stem == "info":
            # extract camera extrinsics
            camera_extrinsics = load_camera_extrinsics_from_bag(bag)
        else:
            img, filename = create_image_from_bag_at_index(bag)
            img.save(output_dir/output_images_subdir/filename)
            frames.append((bag.stem, Path(output_images_subdir).joinpath(filename)))
            logging.info(f'{bag.stem} camera image is created: {Path(output_images_subdir).joinpath(filename)}')

    # NOTE: as Nerf Datasets require one camera intrinsics for frames
    # we will use one of the cameras in the Gazebo simulation for all the frames
    meta = build_dataset(frames, camera_intrinsics, camera_extrinsics)
    logging.debug(json.dumps(meta, indent=4))
    with output_dir.joinpath("transforms.json").open("w") as f:
        f.write(json.dumps(meta, indent=4))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--debug", dest="debug",
        action="store_true",
        help="Enable debugging")
    parser.add_argument(
        "-o", "--output-dir",
        dest="output_dir", required=True,
        action="store",
        help="Path to output directory ")
    parser.add_argument(
        "-i", "--input_dir",
        dest="input_dir", required=True,
        action="store",
        help="Path to input bag files")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%Y/%m/%d %H:%M:%S')
    logging.debug(args)
    exit(main(args))
