#!/usr/bin/env python3
"""
Replay Scan - Playback Recorded Robot Positions

This script replays previously recorded robot positions from a JSON file.
The robot will move through each recorded position with a configurable delay.

Usage:
    python replay_scan.py [filename]
    python replay_scan.py --list  # List available recording files
    
If no filename is provided, the script will use the most recent recording file.
"""

import time
import json
import math
import os
import glob
import sys
from datetime import datetime

# Try to import pymycobot, but allow testing without hardware
try:
    from pymycobot.myarm import MyArm
    HARDWARE_AVAILABLE = True
except ImportError:
    print("Warning: pymycobot module not found. Running in test mode without hardware.")
    HARDWARE_AVAILABLE = False
    
    # Mock MyArm class for testing
    class MyArm:
        def __init__(self, *args, **kwargs):
            print("Mock MyArm initialized")
            
        def send_radians(self, angles, speed=None):
            print(f"Mock send_radians: {[f'{math.degrees(angle):.1f}°' for angle in angles]} at speed {speed}")
            
        def get_radians(self):
            return [0.0] * 7

# Configuration
DEFAULT_SLEEP_DURATION = 5.0  # Default sleep time between movements in seconds
DEFAULT_MOVEMENT_SPEED = 30   # Default movement speed (0-100)
MAX_MOVEMENT_TIME = 15        # Maximum time to wait for movement completion

def find_recording_files():
    """Find all recording files in the current directory"""
    pattern = "recorded_positions_*.json"
    files = glob.glob(pattern)
    return sorted(files, reverse=True)  # Most recent first

def list_recording_files():
    """List all available recording files with details"""
    files = find_recording_files()
    
    if not files:
        print("No recording files found.")
        return
        
    print("Available recording files:")
    print("-" * 80)
    
    for i, filename in enumerate(files, 1):
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                
            metadata = data.get('metadata', {})
            positions_count = metadata.get('total_positions', len(data.get('positions', [])))
            recording_date = metadata.get('recording_date', 'Unknown')
            
            # Parse date for better display
            try:
                date_obj = datetime.fromisoformat(recording_date.replace('Z', '+00:00'))
                date_str = date_obj.strftime("%Y-%m-%d %H:%M:%S")
            except:
                date_str = recording_date
                
            print(f"{i:2d}. {filename}")
            print(f"    Date: {date_str}")
            print(f"    Positions: {positions_count}")
            print()
            
        except Exception as e:
            print(f"{i:2d}. {filename} (Error reading file: {e})")

def load_recording_file(filename):
    """Load and validate a recording file"""
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        
        # Extract positions
        positions = data.get('positions', [])
        metadata = data.get('metadata', {})
        
        if not positions:
            raise ValueError("No positions found in the recording file")
        
        # Validate position data
        for i, pos in enumerate(positions):
            if 'angles_radians' not in pos:
                raise ValueError(f"Position {i+1} missing 'angles_radians' data")
            if len(pos['angles_radians']) != 7:
                raise ValueError(f"Position {i+1} has {len(pos['angles_radians'])} angles, expected 7")
        
        return positions, metadata
        
    except FileNotFoundError:
        raise FileNotFoundError(f"Recording file '{filename}' not found")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in file '{filename}'")

def wait_for_movement_completion(mc, target_angles, timeout=MAX_MOVEMENT_TIME, angle_tolerance=math.radians(10.0)):
    """
    Wait for the MyArm to complete its movement.
    
    Args:
        mc: MyArm instance
        target_angles: list of target joint angles in radians
        timeout: maximum time to wait in seconds
        angle_tolerance: acceptable angle difference in radians
        
    Returns:
        bool: True if movement completed successfully, False if timeout
    """
    start_time = time.time()
    print(f"  Waiting for movement completion (timeout: {timeout}s)...")
    
    # First, give the robot a moment to start moving
    time.sleep(0.5)
    
    while time.time() - start_time < timeout:
        try:
            # Check if robot is still moving (if method exists)
            if hasattr(mc, 'is_moving') and callable(mc.is_moving):
                if not mc.is_moving():
                    # Robot reports it's not moving, verify with angles
                    current_angles = mc.get_radians()
                    if current_angles and len(current_angles) == len(target_angles):
                        angle_errors = [abs(target_angles[i] - current_angles[i]) for i in range(len(target_angles))]
                        max_error = max(angle_errors)
                        
                        if max_error <= angle_tolerance:
                            elapsed_time = time.time() - start_time
                            print(f"  ✓ Movement completed in {elapsed_time:.1f}s (max error: {math.degrees(max_error):.1f}°)")
                            return True
            
            # Fallback: just check angles
            else:
                current_angles = mc.get_radians()
                if current_angles and len(current_angles) == len(target_angles):
                    angle_errors = [abs(target_angles[i] - current_angles[i]) for i in range(len(target_angles))]
                    max_error = max(angle_errors)
                    
                    if max_error <= angle_tolerance:
                        elapsed_time = time.time() - start_time
                        print(f"  ✓ Movement completed in {elapsed_time:.1f}s (max error: {math.degrees(max_error):.1f}°)")
                        return True
                
            time.sleep(0.1)
            
        except Exception as e:
            print(f"  Warning: Error checking movement status: {e}")
            time.sleep(0.1)
    
    print(f"  ⚠ Movement timeout after {timeout}s")
    return False

def replay_positions(positions, metadata, sleep_duration=DEFAULT_SLEEP_DURATION, movement_speed=DEFAULT_MOVEMENT_SPEED):
    """Replay the recorded positions"""
    
    print("=" * 60)
    print("MyArm 300 Position Replay")
    print("=" * 60)
    
    # Initialize MyArm
    try:
        mc = MyArm('/dev/ttyAMA0', 115200)
        print("✓ MyArm initialized")
    except Exception as e:
        print(f"✗ Failed to initialize MyArm: {e}")
        if not HARDWARE_AVAILABLE:
            print("Running in mock mode...")
            mc = MyArm()
        else:
            return False
    
    print(f"\n📊 Replay Settings:")
    print(f"  • Total positions: {len(positions)}")
    print(f"  • Sleep duration: {sleep_duration}s between movements")
    print(f"  • Movement speed: {movement_speed}")
    print(f"  • Recording date: {metadata.get('recording_date', 'Unknown')}")
    
    # Safety check - get current position
    try:
        current_angles = mc.get_radians()
        if current_angles:
            current_degrees = [math.degrees(angle) for angle in current_angles]
            print(f"\n📍 Current position: {[f'{angle:.1f}°' for angle in current_degrees]}")
        else:
            print("\n⚠ Could not read current robot position")
    except Exception as e:
        print(f"\n⚠ Error reading current position: {e}")
    
    # Confirmation prompt
    response = input(f"\n🤖 Ready to replay {len(positions)} positions. Continue? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("Replay cancelled.")
        return False
    
    print(f"\n🎬 Starting replay in 3 seconds...")
    for i in range(3, 0, -1):
        print(f"   {i}...")
        time.sleep(1)
    print("   GO!")
    
    successful_moves = 0
    failed_moves = 0
    
    try:
        for i, position in enumerate(positions, 1):
            print(f"\n[{i}/{len(positions)}] Moving to recorded position {position.get('position_id', i)}:")
            
            # Get target angles
            target_angles = position['angles_radians']
            target_degrees = [math.degrees(angle) for angle in target_angles]
            
            # Display target position
            print(f"  Target: {[f'{angle:.1f}°' for angle in target_degrees]}")
            
            try:
                # Send movement command
                mc.send_radians(target_angles, movement_speed)
                
                # Wait for completion
                if wait_for_movement_completion(mc, target_angles):
                    successful_moves += 1
                    print(f"  ✅ Successfully reached position {i}")
                else:
                    failed_moves += 1
                    print(f"  ⚠ Movement to position {i} may not have completed properly")
                
                # Sleep before next movement (except for last position)
                if i < len(positions):
                    print(f"  💤 Waiting {sleep_duration}s before next movement...")
                    time.sleep(sleep_duration)
                
            except Exception as e:
                failed_moves += 1
                print(f"  ❌ Error moving to position {i}: {e}")
                
                # Ask user if they want to continue
                if i < len(positions):
                    response = input("    Continue with next position? (Y/n): ").strip().lower()
                    if response in ['n', 'no']:
                        print("    Replay stopped by user.")
                        break
    
    except KeyboardInterrupt:
        print("\n\n⚠ Replay interrupted by user (Ctrl+C)")
    
    # Summary
    print(f"\n📈 Replay Summary:")
    print(f"  • Successful moves: {successful_moves}/{len(positions)}")
    print(f"  • Failed moves: {failed_moves}/{len(positions)}")
    print(f"  • Success rate: {(successful_moves/len(positions)*100):.1f}%")
    
    # Final position hold
    if successful_moves > 0:
        print(f"\n🔒 Holding final position for 3 seconds...")
        time.sleep(3)
    
    print("\n✨ Replay complete!")
    return True

def main():
    """Main function"""
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--list':
            list_recording_files()
            return
        elif sys.argv[1] == '--help' or sys.argv[1] == '-h':
            print(__doc__)
            return
        else:
            filename = sys.argv[1]
    else:
        # Find most recent recording file
        files = find_recording_files()
        if not files:
            print("❌ No recording files found.")
            print("   Run 'record_scan.py' first to create recordings.")
            print("   Or use 'python replay_scan.py --list' to see available files.")
            return
        
        filename = files[0]  # Most recent file
        print(f"📁 Using most recent recording: {filename}")
    
    # Load the recording file
    try:
        positions, metadata = load_recording_file(filename)
        print(f"✅ Loaded recording with {len(positions)} positions")
    except Exception as e:
        print(f"❌ Error loading recording file: {e}")
        return
    
    # Optional: Allow user to customize settings
    print(f"\n⚙️  Replay Settings (press Enter for defaults):")
    
    # Sleep duration
    sleep_input = input(f"  Sleep duration between moves [{DEFAULT_SLEEP_DURATION}s]: ").strip()
    try:
        sleep_duration = float(sleep_input) if sleep_input else DEFAULT_SLEEP_DURATION
        sleep_duration = max(0.1, sleep_duration)  # Minimum 0.1 second
    except ValueError:
        sleep_duration = DEFAULT_SLEEP_DURATION
    
    # Movement speed
    speed_input = input(f"  Movement speed (1-100) [{DEFAULT_MOVEMENT_SPEED}]: ").strip()
    try:
        movement_speed = int(speed_input) if speed_input else DEFAULT_MOVEMENT_SPEED
        movement_speed = max(1, min(100, movement_speed))  # Clamp to 1-100
    except ValueError:
        movement_speed = DEFAULT_MOVEMENT_SPEED
    
    # Start replay
    replay_positions(positions, metadata, sleep_duration, movement_speed)

if __name__ == "__main__":
    main()
