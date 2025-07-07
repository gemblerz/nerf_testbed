#!/bin/bash
# Setup script for PLY viewer

echo "Setting up PLY viewer dependencies..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not found. Please install Python 3."
    exit 1
fi

# Install required packages
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Make the viewer executable
chmod +x ply_viewer.py

echo "Setup complete!"
echo ""
echo "Usage examples:"
echo "  python3 ply_viewer.py --demo                    # View sample files from workspace"
echo "  python3 ply_viewer.py --interactive             # Browse and select file"
echo "  python3 ply_viewer.py /path/to/file.ply        # View specific file"
echo ""
echo "Sample files in your workspace:"
find .. -name "*.ply" -type f 2>/dev/null | head -5 | while read file; do
    echo "  $file"
done
