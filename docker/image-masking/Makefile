# Image Segmentation Server Makefile
# Provides targets for building, running, and testing the Docker container

# Variables
IMAGE_NAME = image-segmentation-server
CONTAINER_NAME = image-segmentation-server
PORT = 8000
HOST_PORT = 8000

# Docker build arguments
CUDA_VERSION = cu126

# Default target
.PHONY: help
help:
	@echo "Image Segmentation Server - Available targets:"
	@echo ""
	@echo "  build          - Build the Docker image (GPU-enabled)"
	@echo "  build-cpu      - Build the Docker image (CPU-only)"
	@echo "  run            - Run the container"
	@echo "  run-detached   - Run the container in detached mode"
	@echo "  run-gpu        - Run the container with GPU support"
	@echo "  stop           - Stop the running container"
	@echo "  logs           - Show container logs"
	@echo "  shell          - Open a shell in the running container"
	@echo "  test           - Test the API with a sample request"
	@echo "  clean          - Remove the container and image"
	@echo "  rebuild        - Clean and rebuild the image"
	@echo ""
	@echo "Variables:"
	@echo "  IMAGE_NAME     = $(IMAGE_NAME)"
	@echo "  CONTAINER_NAME = $(CONTAINER_NAME)"
	@echo "  PORT           = $(PORT)"
	@echo "  HOST_PORT      = $(HOST_PORT)"

# Build targets
.PHONY: build
build:
	@echo "Building Docker image with GPU support..."
	docker build \
		--load \
		--build-arg CUDA_VERSION=$(CUDA_VERSION) \
		-t $(IMAGE_NAME) .

.PHONY: build-cpu
build-cpu:
	@echo "Building Docker image with CPU-only support..."
	docker build \
		--load \
		--build-arg CUDA_VERSION=cpu \
		-t $(IMAGE_NAME)-cpu .

# Run targets
.PHONY: run
run:
	@echo "Running container on port $(HOST_PORT)..."
	@mkdir -p ./tmp/huggingface
	docker run --rm -it \
		--name $(CONTAINER_NAME) \
		-p $(HOST_PORT):$(PORT) \
		-v $(PWD)/tmp/huggingface:/app/.cache/huggingface \
		$(IMAGE_NAME)

.PHONY: run-detached
run-detached:
	@echo "Running container in detached mode on port $(HOST_PORT)..."
	@mkdir -p ./tmp/huggingface
	docker run -d \
		--name $(CONTAINER_NAME) \
		-p $(HOST_PORT):$(PORT) \
		-v $(PWD)/tmp/huggingface:/app/.cache/huggingface \
		$(IMAGE_NAME)
	@echo "Container started. Use 'make logs' to view logs or 'make stop' to stop."

.PHONY: run-gpu
run-gpu:
	@echo "Running container with GPU support on port $(HOST_PORT)..."
	@mkdir -p ./tmp/huggingface
	docker run --rm -it \
		--name $(CONTAINER_NAME) \
		--gpus all \
		-p $(HOST_PORT):$(PORT) \
		-v $(PWD)/tmp/huggingface:/app/.cache/huggingface \
		$(IMAGE_NAME)

.PHONY: run-gpu-detached
run-gpu-detached:
	@echo "Running container with GPU support in detached mode on port $(HOST_PORT)..."
	@mkdir -p ./tmp/huggingface
	docker run -d \
		--name $(CONTAINER_NAME) \
		--gpus all \
		-p $(HOST_PORT):$(PORT) \
		-v $(PWD)/tmp/huggingface:/app/.cache/huggingface \
		$(IMAGE_NAME)
	@echo "Container started with GPU support. Use 'make logs' to view logs or 'make stop' to stop."

# Management targets
.PHONY: stop
stop:
	@echo "Stopping container..."
	-docker stop $(CONTAINER_NAME)
	-docker rm $(CONTAINER_NAME)

.PHONY: logs
logs:
	@echo "Showing container logs..."
	docker logs -f $(CONTAINER_NAME)

.PHONY: shell
shell:
	@echo "Opening shell in running container..."
	docker exec -it $(CONTAINER_NAME) /bin/bash

# Testing targets
.PHONY: test
test:
	@echo "Testing the API..."
	@echo "Note: This requires the container to be running and a test image."
	@echo "Usage: make test IMAGE=path/to/image.jpg TARGET='object description'"
	@if [ -z "$(IMAGE)" ] || [ -z "$(TARGET)" ]; then \
		echo "Please specify IMAGE and TARGET variables:"; \
		echo "  make test IMAGE=photo.jpg TARGET='person'"; \
	else \
		echo "Testing with image: $(IMAGE), target: $(TARGET)"; \
		python test_client.py "$(IMAGE)" "$(TARGET)" --server "http://localhost:$(HOST_PORT)"; \
	fi

.PHONY: test-api
test-api:
	@echo "Testing API availability..."
	@curl -s http://localhost:$(HOST_PORT)/ | python -m json.tool || echo "API not available"

# Development targets
.PHONY: dev
dev:
	@echo "Starting development environment..."
	@mkdir -p ./tmp/huggingface
	docker run --rm -it \
		--name $(CONTAINER_NAME)-dev \
		-p $(HOST_PORT):$(PORT) \
		-v $(PWD):/app \
		-v $(PWD)/tmp/huggingface:/app/.cache/huggingface \
		$(IMAGE_NAME) /bin/bash

# Cleanup targets
.PHONY: clean
clean:
	@echo "Cleaning up containers and images..."
	-docker stop $(CONTAINER_NAME)
	-docker rm $(CONTAINER_NAME)
	-docker rmi $(IMAGE_NAME)
	-docker rmi $(IMAGE_NAME)-cpu

.PHONY: clean-all
clean-all: clean
	@echo "Cleaning up all related Docker resources..."
	-docker system prune -f

# Rebuild targets
.PHONY: rebuild
rebuild: clean build

.PHONY: rebuild-cpu
rebuild-cpu: clean build-cpu

# Info targets
.PHONY: info
info:
	@echo "Docker Image Information:"
	@echo "=========================="
	@docker images | grep $(IMAGE_NAME) || echo "No images found"
	@echo ""
	@echo "Running Containers:"
	@echo "==================="
	@docker ps | grep $(CONTAINER_NAME) || echo "No containers running"
	@echo ""
	@echo "Container Logs (last 10 lines):"
	@echo "================================"
	@docker logs --tail 10 $(CONTAINER_NAME) 2>/dev/null || echo "No logs available"

# Quick start target
.PHONY: quickstart
quickstart: build run-detached
	@echo ""
	@echo "🚀 Quick Start Complete!"
	@echo "========================="
	@echo "Server is running at: http://localhost:$(HOST_PORT)"
	@echo ""
	@echo "Test the API:"
	@echo "  curl -X POST -F 'image=@photo.jpg' -F 'target=person' http://localhost:$(HOST_PORT)/segment -o result.png"
	@echo ""
	@echo "Or use the test client:"
	@echo "  make test IMAGE=photo.jpg TARGET='person'"
	@echo ""
	@echo "View logs: make logs"
	@echo "Stop server: make stop"