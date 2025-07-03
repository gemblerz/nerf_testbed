# Image Segmentation HTTP Server

A simple HTTP server that performs image segmentation using Hugging Face's CLIPSeg model. Send an image and target object description, get back a segmented image containing only the target object.

## Features

- REST API for image segmentation
- Uses CLIPSeg model for zero-shot segmentation
- Supports GPU acceleration (falls back to CPU)
- Returns PNG images with transparency
- Simple multipart/form-data interface

## Quick Start

### Using Docker

1. Build the image:
```bash
docker build -t image-segmentation-server .
```

2. Run the server:
```bash
docker run -p 8000:8000 image-segmentation-server
```

3. Test the API:
```bash
curl -X POST -F 'image=@your_image.jpg' -F 'target=person' http://localhost:8000/segment -o result.png
```

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
python image-mask-server.py
```

## API Usage

### POST /segment

Segment an image to extract a target object.

**Parameters:**
- `image`: Image file (multipart/form-data)
- `target`: Text description of the target object to segment

**Response:**
- PNG image with the segmented object (transparent background)

**Example:**
```bash
curl -X POST \
  -F 'image=@photo.jpg' \
  -F 'target=dog' \
  http://localhost:8000/segment \
  -o segmented_dog.png
```

### GET /

Get API information and usage instructions.

## Test Client

Use the provided test client:

```bash
python test_client.py path/to/image.jpg "target object"
```

Examples:
```bash
python test_client.py photo.jpg "person"
python test_client.py street.jpg "car"
python test_client.py garden.jpg "flower"
```

## Supported Target Objects

The CLIPSeg model can segment a wide variety of objects described in natural language:
- People: "person", "man", "woman", "child"
- Animals: "dog", "cat", "bird", "horse"
- Vehicles: "car", "truck", "bicycle", "motorcycle"
- Objects: "chair", "table", "phone", "laptop"
- Nature: "tree", "flower", "grass", "sky"
- And many more!

## Model Information

This server uses the CLIPSeg model (`CIDAS/clipseg-rd64-refined`) which:
- Performs zero-shot image segmentation
- Accepts natural language descriptions
- Works with arbitrary object categories
- Provides good quality segmentation masks

## Environment Variables

- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `HF_HOME`: Hugging Face cache directory

## Docker Build Arguments

- `TORCH_VERSION`: PyTorch version (default: cu118)
- `TORCH_INDEX_URL`: PyTorch index URL (default: CUDA 11.8)

For CPU-only builds:
```bash
docker build --build-arg TORCH_VERSION=cpu --build-arg TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu -t image-segmentation-server .
```

## Requirements

- Python 3.10+
- PyTorch 2.0+
- Transformers 4.30+
- PIL/Pillow
- NumPy

## Notes

- First request may be slower due to model downloading
- GPU acceleration is used when available
- Models are cached in `HF_HOME` directory
- Server supports concurrent requests
- Images are processed in RGBA format with transparency

## Acknowledgement
The codes and documents in this directory were created with the support from GitHub Copilot.