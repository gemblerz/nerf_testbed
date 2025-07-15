# Enhanced Batch Segmentation Script

The `batch_segment.sh` script has been enhanced to support both CLIPSeg and Rembg models for flexible batch image processing.

## Key Features

- **Dual Model Support**: Choose between CLIPSeg (text-guided) and Rembg (background removal)
- **Batch Processing**: Process single files or entire directories
- **Model Selection**: Multiple Rembg models for different use cases
- **Safe Operation**: Dry-run mode to preview operations
- **Flexible Output**: Converts JPG inputs to PNG outputs with transparency

## Quick Start

### CLIPSeg Examples (Text-Guided Segmentation)

```bash
# Extract people from images
./batch_segment.sh -m clipseg -t "person" /path/to/images/

# Extract specific objects  
./batch_segment.sh -m clipseg -t "red car" /path/to/street_photos/

# Original robot arm use case
./batch_segment.sh -m clipseg -t "robot arm with the white body" /path/to/robot_images/
```

### Rembg Examples (Background Removal)

```bash
# Remove backgrounds with default model
./batch_segment.sh -m rembg /path/to/images/

# Use high-quality general model
./batch_segment.sh -m rembg -r birefnet-general /path/to/images/

# Use portrait-optimized model for headshots
./batch_segment.sh -m rembg -r birefnet-portrait /path/to/portraits/
```

## Model Comparison

| Model | Best For | Input Required | Speed | Quality |
|-------|----------|----------------|-------|---------|
| **CLIPSeg** | Specific object extraction | Image + text description | Slower | Good for targeted objects |
| **Rembg** | Background removal | Image only | Faster | Excellent for backgrounds |

## Available Rembg Models

- **u2net** - General purpose (default)
- **u2netp** - Lightweight version  
- **birefnet-general** - High-quality general background removal
- **birefnet-portrait** - Optimized for human portraits
- **isnet-general-use** - Advanced general segmentation
- **isnet-anime** - Specialized for anime characters

## Command Line Options

```
-m, --model TYPE     Model type: 'clipseg' or 'rembg' (default: clipseg)
-t, --target TEXT    Target object for CLIPSeg (required for CLIPSeg)
-r, --rembg-model M  Rembg model name (default: u2net)
-u, --url URL        API server URL (default: http://localhost:8000)
-v, --verbose        Enable verbose output
-n, --dry-run        Show what would be processed without doing it
-h, --help           Show help message
```

## Safe Testing

Always test with dry-run first:

```bash
# Test CLIPSeg
./batch_segment.sh --dry-run -m clipseg -t "person" /path/to/test_image.jpg

# Test Rembg
./batch_segment.sh --dry-run -m rembg -r birefnet-general /path/to/test_image.jpg
```

## Prerequisites

1. **Start the Image Segmentation Server**:
   ```bash
   cd /path/to/image-masking/
   python image-mask-server.py
   ```

2. **Verify Server is Running**:
   ```bash
   curl http://localhost:8000/
   ```

## Usage Workflow

1. **Choose Your Model**:
   - Use CLIPSeg when you want to extract specific objects
   - Use Rembg when you want to remove backgrounds

2. **Test First**:
   ```bash
   ./batch_segment.sh --dry-run -m [model] [options] /path/to/test/
   ```

3. **Run Processing**:
   ```bash
   ./batch_segment.sh -v -m [model] [options] /path/to/images/
   ```

4. **Results**:
   - Original JPG files are deleted
   - PNG files with transparency are created
   - Same filename, different extension

## Example Workflows

### Portrait Processing
```bash
# Remove backgrounds from portrait photos
./batch_segment.sh -m rembg -r birefnet-portrait -v /path/to/headshots/
```

### Product Photography
```bash
# Remove backgrounds from product photos
./batch_segment.sh -m rembg -r birefnet-general -v /path/to/products/
```

### Object Extraction
```bash
# Extract cars from street photos
./batch_segment.sh -m clipseg -t "car" -v /path/to/street_photos/
```

### Mixed Processing
```bash
# First extract people, then remove backgrounds from remaining images
./batch_segment.sh -m clipseg -t "person" /path/to/mixed_photos/
./batch_segment.sh -m rembg /path/to/remaining_photos/
```

## Troubleshooting

- **"API is not available"**: Ensure the image segmentation server is running
- **"CLIPSeg requires target"**: Add `-t "target object"` for CLIPSeg mode
- **Empty results**: Check image format (only JPG/JPEG supported)
- **Server errors**: Check server logs and ensure models are loaded

## Testing Script

Run the test script to see all available options and examples:

```bash
./test_batch_segment.sh
```
