version = 3.2.6
image = gemblerz/ros-isaac-realsense2
data_location ?= $(shell pwd)

# Container name variable (can be overridden)
container_name ?= realsense2-container

# ROS parameters with defaults
camera_node_name ?= camera
camera_rgb_profile ?= 848x480x30
camera_depth_profile ?= 848x480x30
image_jitter_threshold ?= 80.0
enable_image_denoise ?= False
enable_align_depth ?= True

build-amd64:
	docker build -t $(image):$(version)-humble-amd64 -f docker/Dockerfile.amd64 --load docker

build-amd64-cuda:
	docker build -t $(image):$(version)-humble-amd64-cuda -f docker/Dockerfile.amd64_cuda docker

build-jp512:
	docker build -t $(image):$(version)-humble-jp512 -f docker/Dockerfile.jp512 docker

build-jp61:
	docker build -t $(image):$(version)-humble-jp61 -f docker/Dockerfile.jp61 docker

interactive-amd64:
	docker run -ti --rm --privileged --network host --volume $(data_location):/data --entrypoint /bin/bash $(image):$(version)-humble-amd64

interactive-amd64-cuda:
	docker run -ti --rm --privileged --network host --volume $(data_location):/data --runtime nvidia --entrypoint /bin/bash $(image):$(version)-humble-amd64-cuda

interactive-jp512:
	docker run -ti --rm --privileged --network host --volume $(data_location):/data --runtime nvidia --entrypoint /bin/bash $(image):$(version)-humble-jp512

interactive-jp61:
	docker run -ti --rm --privileged --network host --volume $(data_location):/data --runtime nvidia --entrypoint /bin/bash $(image):$(version)-humble-jp61

run-amd64:
	docker run -ti --name $(container_name) --privileged --network host --volume $(data_location):/data \
		$(image):$(version)-humble-amd64 \
		/app/launch.sh \
		camera_node_name:=$(camera_node_name) \
		camera_rgb_profile:=$(camera_rgb_profile) \
		camera_depth_profile:=$(camera_depth_profile) \
		image_jitter_threshold:=$(image_jitter_threshold) \
		enable_image_denoise:=$(enable_image_denoise) \
		enable_align_depth:=$(enable_align_depth)

run-amd64-cuda:
	docker run -ti --name $(container_name) --privileged --network host --volume $(data_location):/data --runtime nvidia \
		$(image):$(version)-humble-amd64-cuda \
		/app/launch.sh \
		camera_node_name:=$(camera_node_name) \
		camera_rgb_profile:=$(camera_rgb_profile) \
		camera_depth_profile:=$(camera_depth_profile) \
		image_jitter_threshold:=$(image_jitter_threshold) \
		enable_image_denoise:=$(enable_image_denoise) \
		enable_align_depth:=$(enable_align_depth)

run-jp512:
	docker run -ti --name $(container_name) --privileged --network host --volume $(data_location):/data --runtime nvidia \
		$(image):$(version)-humble-jp512 \
		/app/launch.sh \
		camera_node_name:=$(camera_node_name) \
		camera_rgb_profile:=$(camera_rgb_profile) \
		camera_depth_profile:=$(camera_depth_profile) \
		image_jitter_threshold:=$(image_jitter_threshold) \
		enable_image_denoise:=$(enable_image_denoise) \
		enable_align_depth:=$(enable_align_depth)

run-jp61:
	docker run -ti --name $(container_name) --privileged --network host --volume $(data_location):/data --runtime nvidia \
		$(image):$(version)-humble-jp61 \
		/app/launch.sh \
		camera_node_name:=$(camera_node_name) \
		camera_rgb_profile:=$(camera_rgb_profile) \
		camera_depth_profile:=$(camera_depth_profile) \
		image_jitter_threshold:=$(image_jitter_threshold) \
		enable_image_denoise:=$(enable_image_denoise) \
		enable_align_depth:=$(enable_align_depth)

exec:
	docker exec -ti $(container_name) /bin/bash

clean:
	docker rm -f $(container_name) 2>/dev/null || true