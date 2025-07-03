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

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageSegmentationHandler(BaseHTTPRequestHandler):
    """HTTP request handler for image segmentation"""
    
    def __init__(self, *args, **kwargs):
        # Initialize the segmentation model
        self.processor = None
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")
        super().__init__(*args, **kwargs)
    
    def _load_model(self):
        """Load the CLIPSeg model for image segmentation"""
        if self.processor is None or self.model is None:
            logger.info("Loading CLIPSeg model...")
            try:
                self.processor = CLIPSegProcessor.from_pretrained("CIDAS/clipseg-rd64-refined")
                self.model = CLIPSegForImageSegmentation.from_pretrained("CIDAS/clipseg-rd64-refined")
                self.model.to(self.device)
                logger.info("Model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                raise
    
    def _segment_image(self, image: Image.Image, target_text: str) -> Image.Image:
        """
        Segment the image to extract the target object
        
        Args:
            image: PIL Image to segment
            target_text: Text description of the target object
            
        Returns:
            PIL Image containing only the segmented object
        """
        try:
            # Ensure model is loaded
            self._load_model()
            
            # Prepare inputs
            inputs = self.processor(
                text=[target_text], 
                images=[image], 
                padding="max_length", 
                return_tensors="pt"
            ).to(self.device)
            
            # Generate segmentation mask
            with torch.no_grad():
                outputs = self.model(**inputs)
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
            logger.error(f"Error during segmentation: {e}")
            raise
    
    def _parse_multipart_form(self) -> Tuple[Optional[Image.Image], Optional[str]]:
        """Parse multipart form data to extract image and target text"""
        try:
            content_type = self.headers.get('Content-Type', '')
            if not content_type.startswith('multipart/form-data'):
                return None, None
            
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
            
            # Extract image file
            if 'image' in form:
                image_field = form['image']
                if image_field.file:
                    image_data = image_field.file.read()
                    image = Image.open(io.BytesIO(image_data))
            
            # Extract target text
            if 'target' in form:
                target_text = form['target'].value
            
            return image, target_text
            
        except Exception as e:
            logger.error(f"Error parsing form data: {e}")
            return None, None
    
    def do_POST(self):
        """Handle POST requests for image segmentation"""
        try:
            if self.path == '/segment':
                # Parse form data
                image, target_text = self._parse_multipart_form()
                
                if image is None or target_text is None:
                    self.send_error(400, "Missing required fields: 'image' and 'target'")
                    return
                
                logger.info(f"Processing segmentation request for target: '{target_text}'")
                
                # Perform segmentation
                segmented_image = self._segment_image(image, target_text)
                
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
                "message": "Image Segmentation API using CLIPSeg",
                "model": "CIDAS/clipseg-rd64-refined",
                "endpoints": {
                    "POST /segment": {
                        "description": "Segment an image to extract target object",
                        "parameters": {
                            "image": "Image file (multipart/form-data)",
                            "target": "Text description of target object to segment"
                        },
                        "response": "PNG image with segmented object"
                    }
                },
                "features": [
                    "Zero-shot segmentation with arbitrary text descriptions",
                    "No predefined classes - works with any object description",
                    "Supports custom labels and specific object descriptions",
                    "Examples: 'red car', 'person wearing hat', 'wooden table', 'blue sky'"
                ],
                "usage": "curl -X POST -F 'image=@image.jpg' -F 'target=red car' http://localhost:8000/segment -o result.png"
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
    
    server_address = (host, port)
    httpd = HTTPServer(server_address, ImageSegmentationHandler)
    
    try:
        logger.info(f"Server running at http://{host}:{port}")
        logger.info("Send POST requests to /segment with 'image' file and 'target' text")
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