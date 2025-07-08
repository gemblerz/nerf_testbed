#!/usr/bin/env python3
"""
PLY Point Cloud Viewer

A Python-based tool for visualizing .ply files containing point clouds.
Supports multiple rendering modes for local and remote (SSH) environments.

Usage:
    python ply_viewer.py <path_to_ply_file>
    python ply_viewer.py --interactive  # Browse and select file
    python ply_viewer.py --demo         # View sample files from the workspace
    python ply_viewer.py --mode screenshot  # Generate screenshots for remote viewing
    python ply_viewer.py --mode web     # Generate web export
"""

import argparse
import os
import sys
from pathlib import Path

# Make tkinter optional for headless environments
try:
    from tkinter import filedialog
    import tkinter as tk
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False

try:
    import open3d as o3d
    import numpy as np
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
except ImportError as e:
    print(f"Missing required package: {e}")
    print("Please install with: pip install open3d numpy matplotlib")
    sys.exit(1)


class PLYViewer:
    def __init__(self):
        self.workspace_root = Path(__file__).parent.parent
        
    def load_ply_file(self, file_path):
        """Load a PLY file and return the point cloud object."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PLY file not found: {file_path}")
        
        print(f"Loading PLY file: {file_path}")
        
        # Try to load as point cloud first
        pcd = o3d.io.read_point_cloud(file_path)
        
        if len(pcd.points) == 0:
            # If no points, try loading as mesh
            print("No points found, trying to load as mesh...")
            mesh = o3d.io.read_triangle_mesh(file_path)
            if len(mesh.vertices) > 0:
                # Convert mesh to point cloud
                pcd = mesh.sample_points_uniformly(number_of_points=10000)
                print(f"Converted mesh to point cloud with {len(pcd.points)} points")
            else:
                raise ValueError("Could not load PLY file as point cloud or mesh")
        
        print(f"Loaded point cloud with {len(pcd.points)} points")
        return pcd
    
    def enhance_visualization(self, pcd):
        """Enhance the point cloud for better visualization."""
        # Estimate normals if not present
        if not pcd.has_normals():
            print("Computing normals...")
            pcd.estimate_normals()
            pcd.orient_normals_consistent_tangent_plane(30)
        
        # Color the point cloud if no colors are present
        if not pcd.has_colors():
            print("Adding colors based on height...")
            points = np.asarray(pcd.points)
            # Color based on Z coordinate (height)
            z_coords = points[:, 2]
            z_normalized = (z_coords - z_coords.min()) / (z_coords.max() - z_coords.min())
            
            # Create a color map (blue to red based on height)
            colors = np.zeros((len(points), 3))
            colors[:, 0] = z_normalized  # Red channel
            colors[:, 2] = 1 - z_normalized  # Blue channel
            pcd.colors = o3d.utility.Vector3dVector(colors)
        
        return pcd
    
    def is_remote_environment(self):
        """Detect if we're running in a remote environment."""
        # Check for SSH connection
        if 'SSH_CONNECTION' in os.environ or 'SSH_CLIENT' in os.environ:
            return True
        
        # Check for DISPLAY variable (X11 forwarding)
        if 'DISPLAY' not in os.environ:
            return True
            
        # Check if tkinter is available
        if not TKINTER_AVAILABLE:
            return True
            
        # Check if we can create a display
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            root.destroy()
            return False
        except:
            return True
    
    def save_screenshots(self, pcd, file_path, output_dir="screenshots"):
        """Save multiple view screenshots of the point cloud."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        base_name = Path(file_path).stem
        
        try:
            # Create visualizer for headless rendering
            vis = o3d.visualization.Visualizer()
            vis.create_window(visible=False, width=800, height=600)  # Headless mode
            vis.add_geometry(pcd)
            
            # Get view control
            ctr = vis.get_view_control()
            
            if ctr is None:
                print("Warning: Could not create view control for screenshots. Using matplotlib fallback.")
                vis.destroy_window()
                return [self.matplotlib_view(pcd, file_path)]
            
            # Different viewing angles
            views = [
                ("front", [0, 0, -1]),
                ("back", [0, 0, 1]),
                ("left", [-1, 0, 0]),
                ("right", [1, 0, 0]),
                ("top", [0, -1, 0]),
                ("bottom", [0, 1, 0]),
                ("isometric", [1, 1, 1])
            ]
            
            screenshots = []
            for view_name, direction in views:
                # Set camera direction
                ctr.set_front(direction)
                ctr.set_up([0, 1, 0] if direction != [0, 1, 0] and direction != [0, -1, 0] else [0, 0, 1])
                
                # Fit view
                vis.poll_events()
                vis.update_renderer()
                
                # Capture screenshot
                screenshot_path = output_path / f"{base_name}_{view_name}.png"
                vis.capture_screen_image(str(screenshot_path))
                screenshots.append(screenshot_path)
                print(f"Saved {view_name} view: {screenshot_path}")
            
            vis.destroy_window()
            return screenshots
            
        except Exception as e:
            print(f"Screenshot mode failed ({e}). Using matplotlib fallback.")
            try:
                vis.destroy_window()
            except:
                pass
            return [self.matplotlib_view(pcd, file_path)]

    def matplotlib_view(self, pcd, file_path):
        """Create matplotlib visualization for remote viewing."""
        points = np.asarray(pcd.points)
        
        if len(points) > 50000:
            # Subsample for performance
            indices = np.random.choice(len(points), 50000, replace=False)
            points = points[indices]
            print(f"Subsampled to 50,000 points for matplotlib visualization")
        
        fig = plt.figure(figsize=(15, 10))
        
        # Create subplots for different views
        views = [
            (221, "3D View", None),
            (222, "XY Plane (Top)", "xy"),
            (223, "XZ Plane (Front)", "xz"),
            (224, "YZ Plane (Side)", "yz")
        ]
        
        for subplot_pos, title, plane in views:
            ax = fig.add_subplot(subplot_pos, projection='3d' if plane is None else None)
            
            if plane is None:
                # 3D scatter plot
                ax.scatter(points[:, 0], points[:, 1], points[:, 2], 
                          c=points[:, 2], cmap='viridis', s=0.5, alpha=0.6)
                ax.set_xlabel('X')
                ax.set_ylabel('Y')
                ax.set_zlabel('Z')
            elif plane == "xy":
                ax.scatter(points[:, 0], points[:, 1], c=points[:, 2], cmap='viridis', s=0.5, alpha=0.6)
                ax.set_xlabel('X')
                ax.set_ylabel('Y')
            elif plane == "xz":
                ax.scatter(points[:, 0], points[:, 2], c=points[:, 1], cmap='viridis', s=0.5, alpha=0.6)
                ax.set_xlabel('X')
                ax.set_ylabel('Z')
            elif plane == "yz":
                ax.scatter(points[:, 1], points[:, 2], c=points[:, 0], cmap='viridis', s=0.5, alpha=0.6)
                ax.set_xlabel('Y')
                ax.set_ylabel('Z')
            
            ax.set_title(title)
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save the plot
        output_path = Path("screenshots")
        output_path.mkdir(exist_ok=True)
        base_name = Path(file_path).stem
        plot_path = output_path / f"{base_name}_matplotlib.png"
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"Matplotlib visualization saved: {plot_path}")
        return plot_path

    def web_export(self, pcd, file_path, max_points=None):
        """Export point cloud as HTML for web viewing."""
        points = np.asarray(pcd.points)
        original_count = len(points)
        
        # Determine max points - use parameter, or smart defaults based on size
        if max_points is None:
            if original_count <= 50000:
                max_points = original_count  # Keep all points for smaller clouds
            elif original_count <= 200000:
                max_points = 100000  # Medium clouds: use 100k points
            elif original_count <= 500000:
                max_points = 200000  # Large clouds: use 200k points
            else:
                max_points = 300000  # Very large clouds: use 300k points
        elif max_points <= 0:
            max_points = original_count  # Use all points when explicitly set to 0 or negative
        
        # Subsample if needed
        if len(points) > max_points:
            indices = np.random.choice(len(points), max_points, replace=False)
            points = points[indices]
            print(f"Subsampled from {original_count:,} to {max_points:,} points for web export")
        else:
            print(f"Using all {original_count:,} points for web export")
            indices = None
        
        # Get colors
        if pcd.has_colors():
            colors = np.asarray(pcd.colors)
            if len(colors) > len(points):
                colors = colors[indices] if 'indices' in locals() else colors[:len(points)]
        else:
            # Create height-based colors
            z_coords = points[:, 2]
            z_normalized = (z_coords - z_coords.min()) / (z_coords.max() - z_coords.min())
            colors = plt.cm.viridis(z_normalized)[:, :3]
        
        # Calculate bounding box
        min_bounds = points.min(axis=0)
        max_bounds = points.max(axis=0)
        center = (min_bounds + max_bounds) / 2
        size = max_bounds - min_bounds
        max_dim = np.max(size)
        
        # Create simplified HTML with reliable CDN
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>PLY Viewer - {Path(file_path).name}</title>
    <style>
        body {{ margin: 0; font-family: Arial, sans-serif; background: #f0f0f0; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .info {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .viewer {{ background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        canvas {{ border: 1px solid #ddd; border-radius: 4px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-top: 15px; }}
        .stat {{ background: #f8f9fa; padding: 10px; border-radius: 4px; text-align: center; }}
        .controls {{ background: #e3f2fd; padding: 15px; border-radius: 4px; margin-top: 15px; }}
        .debug {{ background: #fff3e0; padding: 10px; border-radius: 4px; margin-top: 10px; font-family: monospace; font-size: 12px; max-height: 150px; overflow-y: auto; }}
        .error {{ background: #ffebee; color: #c62828; padding: 10px; border-radius: 4px; margin-top: 10px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="info">
            <h1>PLY Point Cloud Viewer</h1>
            <h2>{Path(file_path).name}</h2>
            <div class="stats">
                <div class="stat">
                    <strong>Points:</strong><br>{len(points):,}{f' of {original_count:,}' if len(points) != original_count else ''}
                </div>
                <div class="stat">
                    <strong>X Range:</strong><br>{min_bounds[0]:.3f} to {max_bounds[0]:.3f}
                </div>
                <div class="stat">
                    <strong>Y Range:</strong><br>{min_bounds[1]:.3f} to {max_bounds[1]:.3f}
                </div>
                <div class="stat">
                    <strong>Z Range:</strong><br>{min_bounds[2]:.3f} to {max_bounds[2]:.3f}
                </div>
            </div>
            <div class="controls">
                <strong>Mouse Controls:</strong> Left click + drag to rotate freely in 3D | Right click + drag to pan | Scroll to zoom | Middle click + drag for constrained rotation<br>
                <strong>Keyboard:</strong> 'R' to reset view | '+/-' to change point size | Arrow keys for fine rotation | Shift+arrows for panning | 1,2,3,7 for preset views<br>
                <strong>Point Size:</strong> <input type="range" id="pointSize" min="0.01" max="10" step="0.01" value="0.05"> 
                <span id="pointSizeValue">0.05</span> | 
                <button onclick="resetPointSize()">Reset Size</button> | 
                <button onclick="resetCamera()">Reset View</button>
            </div>
            <div class="debug" id="debug">Initializing...</div>
            <div class="error" id="error" style="display: none;"></div>
        </div>
        
        <div class="viewer">
            <div id="viewer" style="width: 100%; height: 600px;"></div>
        </div>
    </div>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    
    <script>
        function log(message) {{
            const debug = document.getElementById('debug');
            debug.innerHTML += message + '<br>';
            debug.scrollTop = debug.scrollHeight;
            console.log(message);
        }}
        
        function error(message) {{
            const errorDiv = document.getElementById('error');
            errorDiv.innerHTML = message;
            errorDiv.style.display = 'block';
            console.error(message);
        }}
        
        try {{
            log('Starting PLY viewer...');
            
            // Check if Three.js loaded
            if (typeof THREE === 'undefined') {{
                throw new Error('Three.js failed to load from CDN');
            }}
            log('Three.js loaded successfully (revision: ' + THREE.REVISION + ')');
            
            // Scene setup
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x202020);
            
            const container = document.getElementById('viewer');
            const camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.001, 1000);
            const renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize(container.clientWidth, container.clientHeight);
            renderer.setPixelRatio(window.devicePixelRatio);
            container.appendChild(renderer.domElement);
            
            log('Scene, camera, and renderer created');
            
            // Point cloud data
            const pointPositions = [
{', '.join([f'{p[0]:.4f}, {p[1]:.4f}, {p[2]:.4f}' for p in points])}
            ];
            
            const pointColors = [
{', '.join([f'{c[0]:.3f}, {c[1]:.3f}, {c[2]:.3f}' for c in colors])}
            ];
            
            log('Point data prepared: ' + pointPositions.length/3 + ' points');
            
            // Create geometry
            const geometry = new THREE.BufferGeometry();
            const positions = new Float32Array(pointPositions);
            const colors = new Float32Array(pointColors);
            
            geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
            geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
            
            log('Geometry created with ' + positions.length/3 + ' vertices');
            
            // Create enhanced material for better rendering
            const material = new THREE.PointsMaterial({{
                size: 0.05,
                vertexColors: true,
                sizeAttenuation: false,
                alphaTest: 0.5,
                transparent: false
            }});
            
            // Create point cloud
            const pointCloud = new THREE.Points(geometry, material);
            scene.add(pointCloud);
            
            log('Point cloud added to scene with enhanced material');
            
            // Set up camera with better initial positioning
            const center = new THREE.Vector3({center[0]:.4f}, {center[1]:.4f}, {center[2]:.4f});
            const maxDim = {max_dim:.4f};
            
            // Position camera at a good initial angle for 3D viewing
            const distance = maxDim * 2.0;
            camera.position.set(
                center.x + distance * 0.7,
                center.y + distance * 0.7,
                center.z + distance * 0.7
            );
            camera.lookAt(center);
            
            // Set appropriate near/far planes for the point cloud scale
            camera.near = maxDim * 0.01;
            camera.far = maxDim * 20;
            camera.updateProjectionMatrix();
            
            log('Camera positioned at: ' + camera.position.x.toFixed(3) + ', ' + camera.position.y.toFixed(3) + ', ' + camera.position.z.toFixed(3));
            
            // Add enhanced controls
            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.target.copy(center);
            
            // Enhanced control settings for better 3D manipulation
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            controls.screenSpacePanning = false; // Keep panning in world space
            
            // Enable full rotation freedom
            controls.minAzimuthAngle = -Infinity; // No limit on horizontal rotation
            controls.maxAzimuthAngle = Infinity;
            controls.minPolarAngle = 0; // Allow full vertical rotation
            controls.maxPolarAngle = Math.PI;
            
            // Enhanced zoom and distance controls
            controls.minDistance = maxDim * 0.1;
            controls.maxDistance = maxDim * 10;
            controls.zoomSpeed = 1.0;
            controls.rotateSpeed = 1.0;
            controls.panSpeed = 0.8;
            
            // Enable all mouse buttons
            controls.mouseButtons = {{
                LEFT: THREE.MOUSE.ROTATE,
                MIDDLE: THREE.MOUSE.DOLLY,
                RIGHT: THREE.MOUSE.PAN
            }};
            
            // Enable touch controls for mobile
            controls.touches = {{
                ONE: THREE.TOUCH.ROTATE,
                TWO: THREE.TOUCH.DOLLY_PAN
            }};
            
            controls.update();
            
            log('Enhanced orbit controls initialized with full 3D rotation');
            
            // Add lighting
            const ambientLight = new THREE.AmbientLight(0x404040, 0.8);
            scene.add(ambientLight);
            
            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.6);
            directionalLight.position.set(1, 1, 1);
            scene.add(directionalLight);
            
            log('Lighting added');
            
            // Add reference helpers
            const axesHelper = new THREE.AxesHelper(maxDim * 0.3);
            axesHelper.position.copy(center);
            scene.add(axesHelper);
            
            log('Reference helpers added');
            
            // Render loop
            let frameCount = 0;
            function animate() {{
                requestAnimationFrame(animate);
                controls.update();
                renderer.render(scene, camera);
                
                // Log first few frames
                if (frameCount < 5) {{
                    frameCount++;
                    if (frameCount === 1) log('First frame rendered successfully');
                    if (frameCount === 5) log('Animation loop running smoothly');
                }}
            }}
            
            animate();
            log('Animation started');
            
            // Handle window resize
            window.addEventListener('resize', () => {{
                camera.aspect = container.clientWidth / container.clientHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(container.clientWidth, container.clientHeight);
            }});
            
            // Enhanced keyboard controls
            window.addEventListener('keydown', (event) => {{
                const moveSpeed = maxDim * 0.1;
                const rotateSpeed = 0.1;
                
                // Reset camera
                if (event.key === 'r' || event.key === 'R') {{
                    const distance = maxDim * 2.0;
                    camera.position.set(
                        center.x + distance * 0.7,
                        center.y + distance * 0.7,
                        center.z + distance * 0.7
                    );
                    camera.lookAt(center);
                    controls.target.copy(center);
                    controls.update();
                    log('Camera reset to initial position');
                }}
                
                // Arrow keys for fine rotation
                if (event.shiftKey) {{
                    // Shift + arrows for panning
                    if (event.key === 'ArrowLeft') {{
                        controls.target.x -= moveSpeed;
                        camera.position.x -= moveSpeed;
                    }} else if (event.key === 'ArrowRight') {{
                        controls.target.x += moveSpeed;
                        camera.position.x += moveSpeed;
                    }} else if (event.key === 'ArrowUp') {{
                        controls.target.y += moveSpeed;
                        camera.position.y += moveSpeed;
                    }} else if (event.key === 'ArrowDown') {{
                        controls.target.y -= moveSpeed;
                        camera.position.y -= moveSpeed;
                    }}
                    controls.update();
                    event.preventDefault();
                }} else {{
                    // Arrow keys for rotation
                    if (event.key === 'ArrowLeft') {{
                        const spherical = new THREE.Spherical();
                        spherical.setFromVector3(camera.position.clone().sub(controls.target));
                        spherical.theta -= rotateSpeed;
                        camera.position.copy(new THREE.Vector3().setFromSpherical(spherical).add(controls.target));
                        camera.lookAt(controls.target);
                        event.preventDefault();
                    }} else if (event.key === 'ArrowRight') {{
                        const spherical = new THREE.Spherical();
                        spherical.setFromVector3(camera.position.clone().sub(controls.target));
                        spherical.theta += rotateSpeed;
                        camera.position.copy(new THREE.Vector3().setFromSpherical(spherical).add(controls.target));
                        camera.lookAt(controls.target);
                        event.preventDefault();
                    }} else if (event.key === 'ArrowUp') {{
                        const spherical = new THREE.Spherical();
                        spherical.setFromVector3(camera.position.clone().sub(controls.target));
                        spherical.phi = Math.max(0.1, spherical.phi - rotateSpeed);
                        camera.position.copy(new THREE.Vector3().setFromSpherical(spherical).add(controls.target));
                        camera.lookAt(controls.target);
                        event.preventDefault();
                    }} else if (event.key === 'ArrowDown') {{
                        const spherical = new THREE.Spherical();
                        spherical.setFromVector3(camera.position.clone().sub(controls.target));
                        spherical.phi = Math.min(Math.PI - 0.1, spherical.phi + rotateSpeed);
                        camera.position.copy(new THREE.Vector3().setFromSpherical(spherical).add(controls.target));
                        camera.lookAt(controls.target);
                        event.preventDefault();
                    }}
                    controls.update();
                }}
                
                // Point size keyboard shortcuts
                if (event.key === '+' || event.key === '=') {{
                    const currentSize = material.size;
                    const newSize = Math.min(currentSize + 0.01, 10);
                    material.size = newSize;
                    pointSizeSlider.value = newSize;
                    pointSizeValue.textContent = newSize.toFixed(2);
                    log('Point size increased to: ' + newSize.toFixed(2));
                    event.preventDefault();
                }}
                
                if (event.key === '-' || event.key === '_') {{
                    const currentSize = material.size;
                    const newSize = Math.max(currentSize - 0.01, 0.01);
                    material.size = newSize;
                    pointSizeSlider.value = newSize;
                    pointSizeValue.textContent = newSize.toFixed(2);
                    log('Point size decreased to: ' + newSize.toFixed(2));
                    event.preventDefault();
                }}
                
                // Additional view presets
                if (event.key === '1') {{
                    // Front view
                    camera.position.set(center.x, center.y, center.z + maxDim * 2);
                    camera.lookAt(center);
                    controls.target.copy(center);
                    controls.update();
                    log('Switched to front view');
                }} else if (event.key === '2') {{
                    // Right view
                    camera.position.set(center.x + maxDim * 2, center.y, center.z);
                    camera.lookAt(center);
                    controls.target.copy(center);
                    controls.update();
                    log('Switched to right view');
                }} else if (event.key === '3') {{
                    // Top view
                    camera.position.set(center.x, center.y + maxDim * 2, center.z);
                    camera.lookAt(center);
                    controls.target.copy(center);
                    controls.update();
                    log('Switched to top view');
                }} else if (event.key === '7') {{
                    // Isometric view
                    const distance = maxDim * 2.0;
                    camera.position.set(
                        center.x + distance * 0.7,
                        center.y + distance * 0.7,
                        center.z + distance * 0.7
                    );
                    camera.lookAt(center);
                    controls.target.copy(center);
                    controls.update();
                    log('Switched to isometric view');
                }}
            }});
            
            log('Setup complete! You should see the point cloud now.');
            
            // Point size control functionality
            const pointSizeSlider = document.getElementById('pointSize');
            const pointSizeValue = document.getElementById('pointSizeValue');
            
            pointSizeSlider.addEventListener('input', (event) => {{
                const newSize = parseFloat(event.target.value);
                material.size = newSize;
                pointSizeValue.textContent = newSize.toFixed(2);
                log('Point size changed to: ' + newSize.toFixed(2));
            }});
            
            // Reset point size function
            window.resetPointSize = function() {{
                const defaultSize = 0.05;
                pointSizeSlider.value = defaultSize;
                material.size = defaultSize;
                pointSizeValue.textContent = defaultSize.toFixed(2);
                log('Point size reset to default: ' + defaultSize);
            }};
            
            // Reset camera function
            window.resetCamera = function() {{
                const distance = maxDim * 2.0;
                camera.position.set(
                    center.x + distance * 0.7,
                    center.y + distance * 0.7,
                    center.z + distance * 0.7
                );
                camera.lookAt(center);
                controls.target.copy(center);
                controls.update();
                log('Camera reset to initial position');
            }};
            
            log('Point size and camera controls initialized');
            
        }} catch (err) {{
            error('Error initializing viewer: ' + err.message);
            log('Full error: ' + err.stack);
        }}
    </script>
</body>
</html>"""
        
        # Save HTML file
        output_path = Path("web_export")
        output_path.mkdir(exist_ok=True)
        base_name = Path(file_path).stem
        html_path = output_path / f"{base_name}.html"
        
        with open(html_path, 'w') as f:
            f.write(html_content)
        
        print(f"Web export saved: {html_path}")
        print(f"Open in VS Code and use 'Live Server' extension or copy to local machine")
        return html_path

    def visualize_ply(self, file_path, enhance=True, mode="auto", max_points=None):
        """Visualize a PLY file with different modes for remote/local viewing."""
        try:
            pcd = self.load_ply_file(file_path)
            
            if enhance:
                pcd = self.enhance_visualization(pcd)
            
            # Print point cloud info
            print(f"Point cloud bounds:")
            print(f"  Min: {pcd.get_min_bound()}")
            print(f"  Max: {pcd.get_max_bound()}")
            print(f"  Center: {pcd.get_center()}")
            print(f"  Total points: {len(pcd.points):,}")
            
            # Detect if we're in a remote environment
            is_remote = self.is_remote_environment()
            
            if mode == "auto":
                if is_remote:
                    print("Remote environment detected. Using screenshot mode.")
                    mode = "screenshot"
                else:
                    mode = "window"
            
            if mode == "window":
                # Traditional window mode (local only)
                print("Opening visualization window...")
                print("Controls:")
                print("  - Mouse: Rotate view")
                print("  - Mouse wheel: Zoom")
                print("  - Ctrl+Mouse: Pan")
                print("  - Press 'q' or close window to exit")
                
                o3d.visualization.draw_geometries(
                    [pcd],
                    window_name=f"PLY Viewer - {os.path.basename(file_path)}",
                    width=1200,
                    height=800,
                    left=50,
                    top=50
                )
                
            elif mode == "screenshot":
                # Screenshot mode for remote viewing
                print("Generating screenshots for remote viewing...")
                screenshots = self.save_screenshots(pcd, file_path)
                print(f"Generated {len(screenshots)} screenshots")
                print("View the screenshots in VS Code or download them to your local machine")
                
            elif mode == "matplotlib":
                # Matplotlib mode
                print("Generating matplotlib visualization...")
                plot_path = self.matplotlib_view(pcd, file_path)
                print(f"Matplotlib plot saved: {plot_path}")
                
            elif mode == "web":
                # Web export mode
                print("Generating web export...")
                html_path = self.web_export(pcd, file_path, max_points=max_points)
                print(f"Web export saved: {html_path}")
                
            else:
                print(f"Unknown mode: {mode}")
                return False
                
        except Exception as e:
            print(f"Error visualizing PLY file: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return True
    
    def browse_file(self):
        """Open a file browser to select a PLY file."""
        if not TKINTER_AVAILABLE:
            print("GUI file browser not available in this environment (tkinter not installed).")
            return None
            
        try:
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            
            file_path = filedialog.askopenfilename(
                title="Select PLY file",
                filetypes=[("PLY files", "*.ply"), ("All files", "*.*")],
                initialdir=str(self.workspace_root)
            )
            
            root.destroy()
            return file_path
        except Exception as e:
            print(f"GUI file browser not available: {e}")
            return None
    
    def find_sample_ply_files(self):
        """Find sample PLY files in the workspace."""
        sample_files = []
        
        # Look in common directories
        search_dirs = [
            self.workspace_root / "tmp" / "exports" / "pcd",
            self.workspace_root / "tmp" / "data" / "nerfstudio",
            self.workspace_root / "outputs",
        ]
        
        for search_dir in search_dirs:
            if search_dir.exists():
                for ply_file in search_dir.rglob("*.ply"):
                    sample_files.append(ply_file)
        
        return sample_files
    
    def demo_mode(self, max_points=None):
        """Run demo mode with sample files from the workspace."""
        sample_files = self.find_sample_ply_files()
        
        if not sample_files:
            print("No PLY files found in the workspace.")
            print("Searched in:")
            print("  - tmp/exports/pcd/")
            print("  - tmp/data/nerfstudio/")
            print("  - outputs/")
            return False
        
        print("Found PLY files:")
        for i, file_path in enumerate(sample_files, 1):
            rel_path = file_path.relative_to(self.workspace_root)
            file_size = file_path.stat().st_size / (1024 * 1024)  # MB
            print(f"  {i}. {rel_path} ({file_size:.1f} MB)")
        
        while True:
            try:
                choice = input(f"\\nSelect a file to view (1-{len(sample_files)}) or 'q' to quit: ")
                if choice.lower() == 'q':
                    break
                
                idx = int(choice) - 1
                if 0 <= idx < len(sample_files):
                    # Ask for visualization mode
                    print("\\nVisualization modes:")
                    print("  1. Auto (detect environment)")
                    print("  2. Screenshots (PNG files)")
                    print("  3. Matplotlib (single PNG)")
                    print("  4. Web export (HTML)")
                    
                    mode_choice = input("Select mode (1-4): ")
                    mode_map = {"1": "auto", "2": "screenshot", "3": "matplotlib", "4": "web"}
                    mode = mode_map.get(mode_choice, "auto")
                    
                    self.visualize_ply(str(sample_files[idx]), mode=mode, max_points=max_points)
                else:
                    print("Invalid selection.")
                    
            except ValueError:
                print("Please enter a valid number or 'q'.")
            except KeyboardInterrupt:
                break
        
        return True


def main():
    parser = argparse.ArgumentParser(description="Visualize PLY point cloud files")
    parser.add_argument("file", nargs="?", help="Path to PLY file")
    parser.add_argument("--interactive", "-i", action="store_true", 
                       help="Open file browser to select PLY file")
    parser.add_argument("--demo", "-d", action="store_true",
                       help="Demo mode with sample files from workspace")
    parser.add_argument("--mode", "-m", choices=["auto", "window", "screenshot", "matplotlib", "web"],
                       default="auto", help="Visualization mode")
    parser.add_argument("--no-enhance", action="store_true",
                       help="Skip enhancement (normals, colors)")
    parser.add_argument("--max-points", type=int, 
                       help="Maximum number of points to render (for web mode). Use 0 for all points.")
    
    args = parser.parse_args()
    
    # Handle max_points argument
    max_points = args.max_points
    # Don't convert 0 to None here - let the web_export method handle it
    
    viewer = PLYViewer()
    
    if args.demo:
        viewer.demo_mode(max_points=max_points)
    elif args.interactive:
        file_path = viewer.browse_file()
        if file_path:
            viewer.visualize_ply(file_path, enhance=not args.no_enhance, mode=args.mode, max_points=max_points)
        else:
            print("No file selected.")
    elif args.file:
        if not args.file.endswith('.ply'):
            print("Warning: File doesn't have .ply extension")
        viewer.visualize_ply(args.file, enhance=not args.no_enhance, mode=args.mode, max_points=max_points)
    else:
        print("PLY Point Cloud Viewer")
        print("Usage examples:")
        print("  python3 ply_viewer.py /path/to/file.ply")
        print("  python3 ply_viewer.py --demo")
        print("  python3 ply_viewer.py --interactive")
        print("  python3 ply_viewer.py --mode screenshot /path/to/file.ply")
        print("  python3 ply_viewer.py --mode web /path/to/file.ply")
        print("  python3 ply_viewer.py --mode web --max-points 1000000 /path/to/file.ply  # Use 1M points")
        print("  python3 ply_viewer.py --mode web --max-points 0 /path/to/file.ply  # Use ALL points")
        print("")
        print("Point control options:")
        print("  --max-points 50000   # Use up to 50,000 points")
        print("  --max-points 500000  # Use up to 500,000 points")
        print("  --max-points 0       # Use ALL points (may be slow)")
        print("")
        print("For remote SSH environments, use:")
        print("  --mode screenshot  # Generate multiple view PNG files")
        print("  --mode matplotlib  # Generate single matplotlib PNG")
        print("  --mode web         # Generate interactive HTML file")
        print("")
        print("Runtime controls (web mode):")
        print("  - Slider: Adjust point size dynamically")
        print("  - Keyboard: +/- keys to increase/decrease point size")
        print("  - Button: Reset to default point size")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
