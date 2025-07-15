# Image Segmentation HTTP Server

A powerful HTTP server that provides image segmentation and background removal using both CLIPSeg and Rembg models. Choose between text-guided segmentation or automatic background removal.

## Features

- **Dual Model Support**: CLIPSeg for text-guided segmentation + Rembg for background removal
- **REST API**: Simple multipart/form-data interface
- **GPU Acceleration**: Supports CUDA (falls back to CPU)
- **Multiple Models**: Various Rembg models (u2net, birefnet-general, etc.)
- **Flexible Output**: PNG images with transparency
- **Zero-shot**: CLIPSeg works with any text description

## Model Comparison

| Model | Use Case | Input Required | Best For |
|-------|----------|----------------|----------|
| **CLIPSeg** | Text-guided segmentation | Image + text description | Specific object extraction |
| **Rembg** | Background removal | Image only | General background removal |

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

3. Test the APIs:
```bash
# CLIPSeg: Extract specific objects
curl -X POST -F 'image=@photo.jpg' -F 'model_type=clipseg' -F 'target=person' http://localhost:8000/segment -o clipseg_result.png

# Rembg: Remove background
curl -X POST -F 'image=@photo.jpg' -F 'model_type=rembg' http://localhost:8000/segment -o rembg_result.png
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

Segment an image using either CLIPSeg or Rembg.

**Parameters:**
- `image`: Image file (multipart/form-data) - **REQUIRED**
- `model_type`: Model to use - `"clipseg"` or `"rembg"` (default: clipseg)
- `target`: Text description of target object - **REQUIRED for CLIPSeg**
- `model_name`: Rembg model name (default: u2net) - **Optional for Rembg**

**Response:**
- PNG image with segmented object or background removed

### CLIPSeg Examples:
```bash
# Extract a person from photo
curl -X POST \
  -F 'image=@photo.jpg' \
  -F 'model_type=clipseg' \
  -F 'target=person' \
  http://localhost:8000/segment \
  -o person.png

# Extract a specific object
curl -X POST \
  -F 'image=@street.jpg' \
  -F 'model_type=clipseg' \
  -F 'target=red car' \
  http://localhost:8000/segment \
  -o red_car.png
```

### Rembg Examples:
```bash
# Remove background with default model
curl -X POST \
  -F 'image=@photo.jpg' \
  -F 'model_type=rembg' \
  http://localhost:8000/segment \
  -o no_background.png

# Use specific Rembg model
curl -X POST \
  -F 'image=@portrait.jpg' \
  -F 'model_type=rembg' \
  -F 'model_name=birefnet-portrait' \
  http://localhost:8000/segment \
  -o portrait_no_bg.png
```

### GET /

Get API information, available models, and usage instructions.

## Test Client

Use the enhanced test client to test both models:

```bash
# Test both models
python test_client.py photo.jpg --target "person" --model-type both

# Test only CLIPSeg
python test_client.py photo.jpg --target "car" --model-type clipseg

# Test only Rembg
python test_client.py photo.jpg --model-type rembg --rembg-model birefnet-general

# Show API information
python test_client.py photo.jpg --info
```

## Available Models

### CLIPSeg
- **Model**: `CIDAS/clipseg-rd64-refined`
- **Use Case**: Text-guided object segmentation
- **Strengths**: Works with any text description, precise object targeting

### Rembg Models
- **u2net**: General purpose background removal (default)
- **u2netp**: Lightweight version of u2net
- **birefnet-general**: High-quality general background removal
- **birefnet-portrait**: Optimized for human portraits
- **isnet-general-use**: Advanced general segmentation
- **isnet-anime**: Specialized for anime characters
- **And more**: See full list at [rembg models](https://github.com/danielgatis/rembg#models)

## When to Use Each Model

### Use CLIPSeg when:
- You want to extract specific objects (e.g., "red car", "person wearing hat")
- You need precise control over what gets segmented
- You want to segment multiple different objects from the same image
- You need to target objects by description rather than category

### Use Rembg when:
- You want to remove the entire background
- You need high-quality general background removal
- Speed is important (no text processing needed)
- You're working with portraits, products, or general photography

## Environment Variables

- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `HF_HOME`: Hugging Face cache directory

## Requirements

- Python 3.10+
- PyTorch 2.0+
- Transformers 4.30+
- PIL/Pillow
- rembg 2.0+
- NumPy

## Notes

- First request may be slower due to model downloading
- GPU acceleration is used when available
- Models are cached in `HF_HOME` directory
- Server supports concurrent requests
- Images are processed in RGBA format with transparency

## Acknowledgement
The codes and documents in this directory were created with the support from GitHub Copilot.