#!/usr/bin/env python3
"""
Record Scan - Manual Robot Position Recording

This script allows a user to manually move the MyArm 300 robot by releasing all servos.
The user can record joint positions by pressing Enter, and the recorded positions
are saved to a JSON file for later replay.

Usage:
    python record_scan.py

Controls:
    - Press Enter to record current joint angles
    - Type 'q' and press Enter to quit and save
"""

import time
import json
import math
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
            self._mock_angles = [0.0] * 7
            
        def release_all_servos(self):
            print("Mock release_all_servos: All servos released")
            
        def get_radians(self):
            # Simulate some variation in mock angles
            import random
            self._mock_angles = [angle + random.uniform(-0.1, 0.1) for angle in self._mock_angles]
            return self._mock_angles[:]
            
        def get_angles(self):
            radians = self.get_radians()
            return [math.degrees(angle) for angle in radians]

def main():
    """Main recording loop"""
    print("=" * 60)
    print("MyArm 300 Manual Position Recorder")
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
            return
    
    # Release all servos so user can move the robot freely
    try:
        print("\n🔓 Releasing all servos...")
        mc.release_all_servos()
        print("✓ All servos released. You can now move the robot manually.")
    except AttributeError:
        print("⚠ release_all_servos() method not available. Trying alternative...")
        try:
            # Alternative method if release_all_servos doesn't exist
            if hasattr(mc, 'set_free_mode'):
                mc.set_free_mode(1)
                print("✓ Free mode enabled. You can now move the robot manually.")
            else:
                print("⚠ Could not release servos. Manual movement may not work.")
        except Exception as e:
            print(f"⚠ Could not enable free mode: {e}")
    except Exception as e:
        print(f"⚠ Error releasing servos: {e}")
    
    recorded_positions = []
    position_count = 0
    
    print("\n📋 Instructions:")
    print("  - Manually move the robot to desired positions")
    print("  - Press Enter to record current joint angles")
    print("  - Type 'q' and press Enter to quit and save")
    print("  - Type 'show' and press Enter to display current angles")
    print("\n" + "-" * 40)
    
    try:
        while True:
            user_input = input(f"\nPosition #{position_count + 1} - Press Enter to record (or 'q' to quit, 'show' to display): ").strip()
            
            if user_input.lower() == 'q':
                break
            elif user_input.lower() == 'show':
                # Display current angles without recording
                try:
                    current_angles_rad = mc.get_radians()
                    if current_angles_rad:
                        current_angles_deg = [math.degrees(angle) for angle in current_angles_rad]
                        print(f"\n📐 Current joint angles:")
                        for i, angle in enumerate(current_angles_deg):
                            print(f"  Joint {i+1}: {angle:6.1f}° ({current_angles_rad[i]:6.3f} rad)")
                    else:
                        print("❌ Could not read current angles")
                except Exception as e:
                    print(f"❌ Error reading angles: {e}")
                continue
            elif user_input == "":
                # Record current position
                try:
                    current_angles_rad = mc.get_radians()
                    if current_angles_rad:
                        current_angles_deg = [math.degrees(angle) for angle in current_angles_rad]
                        
                        # Create position record
                        position_record = {
                            'position_id': position_count + 1,
                            'timestamp': datetime.now().isoformat(),
                            'angles_radians': current_angles_rad,
                            'angles_degrees': current_angles_deg
                        }
                        
                        recorded_positions.append(position_record)
                        position_count += 1
                        
                        print(f"✅ Position #{position_count} recorded:")
                        for i, angle in enumerate(current_angles_deg):
                            print(f"  Joint {i+1}: {angle:6.1f}° ({current_angles_rad[i]:6.3f} rad)")
                        
                    else:
                        print("❌ Could not read current angles. Position not recorded.")
                        
                except Exception as e:
                    print(f"❌ Error recording position: {e}")
            else:
                print("Invalid input. Press Enter to record, 'show' to display, or 'q' to quit.")
    
    except KeyboardInterrupt:
        print("\n\n⚠ Recording interrupted by user (Ctrl+C)")
    
    # Save recorded positions to file
    if recorded_positions:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recorded_positions_{timestamp}.json"
        
        # Create complete record with metadata
        complete_record = {
            'metadata': {
                'recording_date': datetime.now().isoformat(),
                'total_positions': len(recorded_positions),
                'robot_model': 'MyArm 300',
                'angle_units': 'radians and degrees'
            },
            'positions': recorded_positions
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(complete_record, f, indent=2)
            
            print(f"\n💾 Recorded {len(recorded_positions)} positions saved to: {filename}")
            print(f"📊 Summary:")
            print(f"  • Total positions: {len(recorded_positions)}")
            print(f"  • Recording duration: {(datetime.fromisoformat(recorded_positions[-1]['timestamp']) - datetime.fromisoformat(recorded_positions[0]['timestamp'])).total_seconds():.1f} seconds" if len(recorded_positions) > 1 else "  • Single position recorded")
            print(f"  • File: {filename}")
            
        except Exception as e:
            print(f"❌ Error saving file: {e}")
            print("📝 Positions recorded in this session:")
            for pos in recorded_positions:
                print(f"  Position {pos['position_id']}: {[f'{angle:.1f}°' for angle in pos['angles_degrees']]}")
    else:
        print("\n📭 No positions recorded.")
    
    print("\n🔒 Re-engaging servos...")
    try:
        # Try to re-engage servos if possible
        if hasattr(mc, 'set_free_mode'):
            mc.set_free_mode(0)
            print("✅ Servos re-engaged")
        else:
            print("⚠ Could not automatically re-engage servos")
    except Exception as e:
        print(f"⚠ Warning: Could not re-engage servos: {e}")
    
    print("\n✨ Recording session complete!")

if __name__ == "__main__":
    main()
