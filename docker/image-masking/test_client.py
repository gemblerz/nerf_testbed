#!/usr/bin/env python3
"""
Test client for the Image Segmentation HTTP Server
Demonstrates both CLIPSeg and Rembg models
"""

import requests
import argparse
import os
from pathlib import Path

def test_clipseg(server_url, image_path, target_text, output_path):
    """Test CLIPSeg text-guided segmentation"""
    print(f"Testing CLIPSeg with target: '{target_text}'")
    
    with open(image_path, 'rb') as f:
        files = {'image': f}
        data = {
            'model_type': 'clipseg',
            'target': target_text
        }
        
        response = requests.post(f"{server_url}/segment", files=files, data=data)
    
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print(f"CLIPSeg result saved to: {output_path}")
        return True
    else:
        print(f"CLIPSeg failed: {response.status_code} - {response.text}")
        return False

def test_rembg(server_url, image_path, model_name, output_path):
    """Test Rembg background removal"""
    print(f"Testing Rembg with model: '{model_name}'")
    
    with open(image_path, 'rb') as f:
        files = {'image': f}
        data = {
            'model_type': 'rembg',
            'model_name': model_name
        }
        
        response = requests.post(f"{server_url}/segment", files=files, data=data)
    
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print(f"Rembg result saved to: {output_path}")
        return True
    else:
        print(f"Rembg failed: {response.status_code} - {response.text}")
        return False

def test_api_info(server_url):
    """Test API information endpoint"""
    print("Getting API information...")
    
    response = requests.get(server_url)
    
    if response.status_code == 200:
        print("API Info:")
        import json
        print(json.dumps(response.json(), indent=2))
        return True
    else:
        print(f"API info failed: {response.status_code} - {response.text}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Test the image segmentation server with both CLIPSeg and Rembg')
    parser.add_argument('image_path', help='Path to the input image')
    parser.add_argument('--target', help='Target object for CLIPSeg (e.g., "person", "car", "dog")')
    parser.add_argument('--model-type', choices=['clipseg', 'rembg', 'both'], default='both', 
                       help='Which model to test (default: both)')
    parser.add_argument('--rembg-model', default='u2net', 
                       help='Rembg model name (default: u2net)')
    parser.add_argument('--server', default='http://localhost:8000', help='Server URL')
    parser.add_argument('--info', action='store_true', help='Show API information')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.image_path):
        print(f"Error: Image file {args.image_path} not found")
        return 1
    
    image_path = Path(args.image_path)
    server_url = args.server
    
    print(f"Testing with image: {image_path}")
    print(f"Server URL: {server_url}")
    print("-" * 50)
    
    # Show API info if requested
    if args.info:
        test_api_info(server_url)
        print("-" * 50)
    
    success_count = 0
    total_tests = 0
    
    # Test CLIPSeg
    if args.model_type in ['clipseg', 'both']:
        if args.target:
            total_tests += 1
            output_path = f"clipseg_{args.target}_{image_path.stem}.png"
            if test_clipseg(server_url, image_path, args.target, output_path):
                success_count += 1
                print(f"✓ CLIPSeg test passed")
            else:
                print(f"✗ CLIPSeg test failed")
        else:
            print("⚠ Skipping CLIPSeg test: --target required for CLIPSeg")
        print()
    
    # Test Rembg
    if args.model_type in ['rembg', 'both']:
        total_tests += 1
        output_path = f"rembg_{args.rembg_model}_{image_path.stem}.png"
        if test_rembg(server_url, image_path, args.rembg_model, output_path):
            success_count += 1
            print(f"✓ Rembg test passed")
        else:
            print(f"✗ Rembg test failed")
        print()
    
    print("-" * 50)
    print(f"Testing complete! {success_count}/{total_tests} tests passed")
    
    return 0 if success_count == total_tests else 1

if __name__ == "__main__":
    exit(main())
