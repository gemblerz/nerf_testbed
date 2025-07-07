# Visualization Tools

This directory contains tools for visualizing point clouds and 3D data from the NeRF testbed.

## PLY Viewer

A Python-based tool for viewing .ply point cloud files using Open3D. **Supports both local and remote SSH environments.**

### Setup

1. Run the setup script to install dependencies:
   ```bash
   cd viz
   ./setup.sh
   ```

2. Or install manually:
   ```bash
   pip3 install -r requirements.txt
   ```

### Usage for Remote SSH (VS Code)

When using VS Code with SSH, the viewer automatically detects the remote environment and switches to screenshot mode:

**Demo mode** (view sample files from workspace):
```bash
python3 ply_viewer.py --demo
```

**Screenshot mode** (generates PNG files you can view in VS Code):
```bash
python3 ply_viewer.py --mode screenshot ../tmp/exports/pcd/process_output.ply
```

**Web export** (generates interactive HTML file):
```bash
python3 ply_viewer.py --mode web ../tmp/exports/pcd/process_output.ply
```

**Matplotlib mode** (single comprehensive PNG):
```bash
python3 ply_viewer.py --mode matplotlib ../tmp/exports/pcd/process_output.ply
```

### Remote Viewing Modes

1. **Screenshot Mode** (`--mode screenshot`):
   - Generates 7 PNG images from different angles (front, back, left, right, top, bottom, isometric)
   - Files saved to `screenshots/` directory
   - Best for detailed inspection from multiple angles

2. **Web Export Mode** (`--mode web`):
   - Creates an interactive HTML file with Three.js
   - Supports rotation, zoom, and pan controls
   - Open the HTML file in VS Code or copy to your local machine
   - Install "Live Server" extension in VS Code for best experience

3. **Matplotlib Mode** (`--mode matplotlib`):
   - Single PNG with 4 views (3D, XY plane, XZ plane, YZ plane)
   - Good for quick overview and 2D projections

### Local Usage (Direct Display)

If running locally (not via SSH):

**Interactive mode** (file browser):
```bash
python3 ply_viewer.py --interactive
```

**Direct file viewing**:
```bash
python3 ply_viewer.py /path/to/your/file.ply
```

### Examples with Your Data

```bash
# View the processed output (auto-detects remote environment)
python3 ply_viewer.py ../tmp/exports/pcd/process_output.ply

# Generate screenshots for detailed inspection
python3 ply_viewer.py --mode screenshot ../tmp/exports/pcd/robot_arm_from_masked_images.ply

# Create interactive web viewer
python3 ply_viewer.py --mode web ../tmp/exports/pcd/process_output.ply
```

### Features

- **Remote environment detection**: Automatically switches to appropriate mode for SSH
- **Multiple output formats**: Screenshots, web export, matplotlib plots
- **Automatic enhancement**: Adds colors and normals if missing
- **Smart subsampling**: Reduces point count for large files to improve performance
- **Interactive controls** (web mode): 
  - Left click + drag: Rotate view
  - Right click + drag: Pan
  - Scroll: Zoom
- **Workspace integration**: Automatically finds PLY files in your project

### Viewing Generated Files

**In VS Code (SSH):**
- Screenshots: View directly in the file explorer
- Web exports: Right-click HTML file → "Open with Live Server" (if extension installed)
- Matplotlib plots: View directly in VS Code

**Copy to local machine:**
```bash
# From your local machine, copy the generated files
scp user@remote:/path/to/nerf_testbed/viz/screenshots/* ./
scp user@remote:/path/to/nerf_testbed/viz/web_export/* ./
```

### Troubleshooting

**For SSH/Remote environments:**
1. **No display available**: This is expected - use `--mode screenshot` or `--mode web`
2. **Large files**: The script automatically subsamples large point clouds
3. **Missing screenshots**: Check the `screenshots/` directory in the viz folder

**For local environments:**
1. **Import errors**: Make sure Open3D is installed: `pip3 install open3d`
2. **Display issues**: Try `export DISPLAY=:0` or use remote modes

### Dependencies

- Python 3.7+
- Open3D (3D visualization and screenshots)
- NumPy (numerical operations)
- Matplotlib (2D plotting)
- tkinter (file browser, usually included with Python)

## Other Visualization Options

For additional visualization needs, consider:

- **CloudCompare**: Professional point cloud software (GUI)
- **MeshLab**: 3D mesh processing (GUI)
- **ParaView**: Scientific visualization for large datasets (GUI)
