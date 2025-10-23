# Makefile for er-myarm300 Docker container and URDF visualization

# Variables
DOCKER_IMAGE = er-myarm300
DOCKER_TAG = latest
CONTAINER_NAME = er-myarm300-urdf
DOCKERFILE_PATH = .
URDF_PATH = /home/ros/urdf/myarm_300_pi.urdf

# Default target
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  build       - Build the Docker image"
	@echo "  run-urdf    - Run container and launch URDF tutorial"
	@echo "  run-shell   - Run container with interactive shell"
	@echo "  clean       - Remove Docker image and stop containers"
	@echo "  stop        - Stop running containers"
	@echo "  logs        - Show container logs"

# Build the Docker image
.PHONY: build
build:
	@echo "Building Docker image $(DOCKER_IMAGE):$(DOCKER_TAG)..."
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) $(DOCKERFILE_PATH)

# Run container and launch URDF tutorial
.PHONY: run-urdf
run-urdf: build
	@echo "Launching URDF tutorial for myarm300..."
	@echo "Make sure X11 forwarding is enabled on your host system"
	docker run -it --rm \
		--name $(CONTAINER_NAME) \
		--env="DISPLAY=$$DISPLAY" \
		--volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
		--net=host \
		$(DOCKER_IMAGE):$(DOCKER_TAG) \
		bash -c "source /opt/ros/humble/setup.bash && source /home/ros/colcon_ws/install/setup.bash && ros2 launch urdf_tutorial display.launch.py model:=$(URDF_PATH)"

# Run container with interactive shell for debugging
.PHONY: run-shell
run-shell: build
	@echo "Starting interactive shell in container..."
	docker run -it --rm \
		--name $(CONTAINER_NAME)-shell \
		--env="DISPLAY=$$DISPLAY" \
		--volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
		--net=host \
		$(DOCKER_IMAGE):$(DOCKER_TAG) \
		bash

# Run container in background (headless mode)
.PHONY: run-headless
run-headless: build
	@echo "Running container in headless mode..."
	docker run -d \
		--name $(CONTAINER_NAME)-headless \
		--net=host \
		$(DOCKER_IMAGE):$(DOCKER_TAG) \
		bash -c "source /opt/ros/humble/setup.bash && source /home/ros/colcon_ws/install/setup.bash && sleep infinity"

# Stop running containers
.PHONY: stop
stop:
	@echo "Stopping containers..."
	-docker stop $(CONTAINER_NAME) 2>/dev/null || true
	-docker stop $(CONTAINER_NAME)-shell 2>/dev/null || true
	-docker stop $(CONTAINER_NAME)-headless 2>/dev/null || true
	-docker rm $(CONTAINER_NAME) 2>/dev/null || true
	-docker rm $(CONTAINER_NAME)-shell 2>/dev/null || true
	-docker rm $(CONTAINER_NAME)-headless 2>/dev/null || true

# Show container logs
.PHONY: logs
logs:
	docker logs -f $(CONTAINER_NAME) 2>/dev/null || docker logs -f $(CONTAINER_NAME)-headless 2>/dev/null || echo "No running containers found"

# Clean up Docker image and containers
.PHONY: clean
clean: stop
	@echo "Cleaning up Docker image and containers..."
	-docker rmi $(DOCKER_IMAGE):$(DOCKER_TAG) 2>/dev/null || true

# Test URDF file exists in container
.PHONY: test-urdf
test-urdf: build
	@echo "Testing if URDF file exists in container..."
	docker run --rm $(DOCKER_IMAGE):$(DOCKER_TAG) \
		bash -c "if [ -f $(URDF_PATH) ]; then echo 'URDF file found at $(URDF_PATH)'; cat $(URDF_PATH) | head -5; else echo 'URDF file not found!'; fi"

# Show ROS2 packages available in container
.PHONY: test-ros
test-ros: build
	@echo "Testing ROS2 setup in container..."
	docker run --rm $(DOCKER_IMAGE):$(DOCKER_TAG) \
		bash -c "source /opt/ros/humble/setup.bash && source /home/ros/colcon_ws/install/setup.bash && ros2 pkg list | grep -E '(urdf|robot_state|joint_state|rviz)'"