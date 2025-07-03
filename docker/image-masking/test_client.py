#!/usr/bin/env python3
"""
Test script for the image segmentation server
"""

import requests
import argparse
import os

def test_server(image_path, target_text, server_url="http://localhost:8000"):
    """Test the image segmentation server"""
    
    if not os.path.exists(image_path):
        print(f"Error: Image file {image_path} not found")
        return False
    
    try:
        # Prepare the request
        with open(image_path, 'rb') as img_file:
            files = {'image': img_file}
            data = {'target': target_text}
            
            print(f"Sending request to {server_url}/segment...")
            print(f"Target object: {target_text}")
            
            # Make the request
            response = requests.post(f"{server_url}/segment", files=files, data=data)
            
            if response.status_code == 200:
                # Save the result
                output_path = f"segmented_{os.path.basename(image_path)}.png"
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                print(f"Success! Segmented image saved as: {output_path}")
                return True
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return False
                
    except requests.ConnectionError:
        print("Error: Could not connect to server. Is it running?")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Test the image segmentation server')
    parser.add_argument('image_path', help='Path to the input image')
    parser.add_argument('target', help='Target object to segment (e.g., "person", "car", "dog")')
    parser.add_argument('--server', default='http://localhost:8000', help='Server URL')
    
    args = parser.parse_args()
    
    success = test_server(args.image_path, args.target, args.server)
    exit(0 if success else 1)

if __name__ == "__main__":
    main()
