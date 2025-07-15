#!/usr/bin/env python3
"""
Image Segmentation HTTP Server

A simple HTTP server that accepts POST requests with an image file and target object text,
performs image segmentation using Hugging Face models, and returns the segmented image.
"""

import os
import io
import json
import logging
from typing import Optional, Tuple
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import cgi

import torch
from PIL import Image
import numpy as np
from transformers import pipeline, CLIPSegProcessor, CLIPSegForImageSegmentation
from rembg import remove, new_session

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageSegmentationHandler(BaseHTTPRequestHandler):
    """HTTP request handler for image segmentation"""
    
    # Class-level variables to store the models (shared across all instances)
    _clipseg_processor = None
    _clipseg_model = None
    _rembg_session = None
    _device = "cuda" if torch.cuda.is_available() else "cpu"
    _clipseg_loaded = False
    _rembg_loaded = False
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    @classmethod
    def _load_clipseg_model(cls):
        """Load the CLIPSeg model for text-guided image segmentation"""
        if not cls._clipseg_loaded:
            logger.info(f"Loading CLIPSeg model on device: {cls._device}")
            try:
                cls._clipseg_processor = CLIPSegProcessor.from_pretrained("CIDAS/clipseg-rd64-refined")
                cls._clipseg_model = CLIPSegForImageSegmentation.from_pretrained("CIDAS/clipseg-rd64-refined")
                cls._clipseg_model.to(cls._device)
                cls._clipseg_loaded = True
                logger.info("CLIPSeg model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load CLIPSeg model: {e}")
                raise
    
    @classmethod
    def _load_rembg_model(cls):
        """Load the Rembg model for background removal"""
        if not cls._rembg_loaded:
            logger.info("Loading Rembg model")
            try:
                cls._rembg_session = new_session()
                cls._rembg_loaded = True
                logger.info("Rembg model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load Rembg model: {e}")
                raise
    
    def _segment_image_clipseg(self, image: Image.Image, target_text: str) -> Image.Image:
        """
        Segment the image to extract the target object using CLIPSeg
        
        Args:
            image: PIL Image to segment
            target_text: Text description of the target object
            
        Returns:
            PIL Image containing only the segmented object
        """
        try:
            # Ensure model is loaded
            self._load_clipseg_model()
            
            # Prepare inputs
            inputs = self._clipseg_processor(
                text=[target_text], 
                images=[image], 
                padding="max_length", 
                return_tensors="pt"
            ).to(self._device)
            
            # Generate segmentation mask
            with torch.no_grad():
                outputs = self._clipseg_model(**inputs)
                logits = outputs.logits
                
            # Process the logits to create a mask
            # Resize to match original image size
            mask = torch.nn.functional.interpolate(
                logits.unsqueeze(1), 
                size=image.size[::-1], 
                mode='bilinear', 
                align_corners=False
            ).squeeze()
            
            # Convert to numpy and normalize
            mask = mask.cpu().numpy()
            mask = (mask - mask.min()) / (mask.max() - mask.min())
            
            # Apply threshold to create binary mask
            binary_mask = (mask > 0.5).astype(np.uint8) * 255
            
            # Convert image to RGBA for transparency
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            # Create PIL mask
            mask_image = Image.fromarray(binary_mask, mode='L')
            
            # Apply mask to image
            image_array = np.array(image)
            mask_array = np.array(mask_image)
            
            # Set alpha channel based on mask
            image_array[:, :, 3] = mask_array
            
            # Create final segmented image
            segmented_image = Image.fromarray(image_array, 'RGBA')
            
            return segmented_image
            
        except Exception as e:
            logger.error(f"Error during CLIPSeg segmentation: {e}")
            raise
    
    def _segment_image_rembg(self, image: Image.Image, model_name: str = "u2net") -> Image.Image:
        """
        Remove background from image using Rembg
        
        Args:
            image: PIL Image to process
            model_name: Rembg model to use (u2net, u2netp, birefnet-general, etc.)
            
        Returns:
            PIL Image with background removed
        """
        try:
            # Ensure model is loaded
            self._load_rembg_model()
            
            # Remove background
            if model_name != "u2net":
                # Create session with specific model
                session = new_session(model_name)
                output = remove(image, session=session)
            else:
                # Use default session
                output = remove(image, session=self._rembg_session)
            
            return output
            
        except Exception as e:
            logger.error(f"Error during Rembg background removal: {e}")
            raise
    
    def _parse_multipart_form(self) -> Tuple[Optional[Image.Image], Optional[str], Optional[str], Optional[str]]:
        """Parse multipart form data to extract image, target text, model type, and model name"""
        try:
            content_type = self.headers.get('Content-Type', '')
            if not content_type.startswith('multipart/form-data'):
                return None, None, None, None
            
            # Parse multipart form data
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    'REQUEST_METHOD': 'POST',
                    'CONTENT_TYPE': content_type,
                }
            )
            
            image = None
            target_text = None
            model_type = "clipseg"  # default
            model_name = "u2net"   # default for rembg
            
            # Extract image file
            if 'image' in form:
                image_field = form['image']
                if image_field.file:
                    image_data = image_field.file.read()
                    image = Image.open(io.BytesIO(image_data))
            
            # Extract target text (required for CLIPSeg)
            if 'target' in form:
                target_text = form['target'].value
            
            # Extract model type (clipseg or rembg)
            if 'model_type' in form:
                model_type = form['model_type'].value.lower()
            
            # Extract model name (for rembg models)
            if 'model_name' in form:
                model_name = form['model_name'].value
            
            return image, target_text, model_type, model_name
            
        except Exception as e:
            logger.error(f"Error parsing form data: {e}")
            return None, None, None, None
    
    def do_POST(self):
        """Handle POST requests for image segmentation"""
        try:
            if self.path == '/segment':
                # Parse form data
                image, target_text, model_type, model_name = self._parse_multipart_form()
                
                if image is None:
                    self.send_error(400, "Missing required field: 'image'")
                    return
                
                # Validate model type and required parameters
                if model_type == "clipseg":
                    if target_text is None:
                        self.send_error(400, "CLIPSeg requires 'target' text description")
                        return
                    logger.info(f"Processing CLIPSeg segmentation for target: '{target_text}'")
                    segmented_image = self._segment_image_clipseg(image, target_text)
                    
                elif model_type == "rembg":
                    logger.info(f"Processing Rembg background removal with model: '{model_name}'")
                    segmented_image = self._segment_image_rembg(image, model_name)
                    
                else:
                    self.send_error(400, f"Invalid model_type: '{model_type}'. Use 'clipseg' or 'rembg'")
                    return
                
                # Convert image to bytes
                img_buffer = io.BytesIO()
                segmented_image.save(img_buffer, format='PNG')
                img_data = img_buffer.getvalue()
                
                # Send response
                self.send_response(200)
                self.send_header('Content-Type', 'image/png')
                self.send_header('Content-Length', str(len(img_data)))
                self.end_headers()
                self.wfile.write(img_data)
                
                logger.info("Segmentation completed successfully")
                
            else:
                self.send_error(404, "Endpoint not found")
                
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def do_GET(self):
        """Handle GET requests - provide API information"""
        if self.path == '/':
            response = {
                "message": "Image Segmentation API with CLIPSeg and Rembg",
                "models": {
                    "clipseg": "CIDAS/clipseg-rd64-refined",
                    "rembg": "Multiple models available (u2net, birefnet-general, etc.)"
                },
                "endpoints": {
                    "POST /segment": {
                        "description": "Segment an image using CLIPSeg or remove background using Rembg",
                        "parameters": {
                            "image": "Image file (multipart/form-data) - REQUIRED",
                            "model_type": "Model type: 'clipseg' or 'rembg' (default: clipseg)",
                            "target": "Text description of target object (REQUIRED for CLIPSeg)",
                            "model_name": "Rembg model name (default: u2net, options: u2netp, birefnet-general, birefnet-portrait, isnet-general-use, etc.)"
                        },
                        "response": "PNG image with segmented object or background removed"
                    }
                },
                "model_comparison": {
                    "clipseg": {
                        "use_case": "Text-guided segmentation for specific objects",
                        "requires": "Text description of target object",
                        "examples": "'red car', 'person wearing hat', 'wooden table'"
                    },
                    "rembg": {
                        "use_case": "General background removal",
                        "requires": "No text input needed",
                        "models": ["u2net", "u2netp", "birefnet-general", "birefnet-portrait", "isnet-general-use", "isnet-anime"]
                    }
                },
                "usage_examples": {
                    "clipseg": "curl -X POST -F 'image=@image.jpg' -F 'model_type=clipseg' -F 'target=red car' http://localhost:8000/segment -o result.png",
                    "rembg_default": "curl -X POST -F 'image=@image.jpg' -F 'model_type=rembg' http://localhost:8000/segment -o result.png",
                    "rembg_custom_model": "curl -X POST -F 'image=@image.jpg' -F 'model_type=rembg' -F 'model_name=birefnet-general' http://localhost:8000/segment -o result.png"
                }
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response, indent=2).encode())
        else:
            self.send_error(404, "Not found")
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(f"{self.address_string()} - {format % args}")


def run_server(host='0.0.0.0', port=8000):
    """Run the HTTP server"""
    logger.info(f"Starting Image Segmentation Server on {host}:{port}")
    
    # Load the CLIPSeg model once at startup
    logger.info("Loading CLIPSeg model at startup...")
    ImageSegmentationHandler._load_clipseg_model()
    
    # Rembg models are loaded on-demand for better memory efficiency
    logger.info("Rembg models will be loaded on-demand")
    
    server_address = (host, port)
    httpd = HTTPServer(server_address, ImageSegmentationHandler)
    
    try:
        logger.info(f"Server running at http://{host}:{port}")
        logger.info("Send POST requests to /segment with 'image' file and 'model_type' (clipseg/rembg)")
        logger.info("For CLIPSeg: include 'target' text. For Rembg: optionally include 'model_name'")
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    # Get host and port from environment variables
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 8000))
    
    run_server(host, port)