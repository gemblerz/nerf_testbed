import time
import math
import random
import numpy as np
from pymycobot.myarm import MyArm
from iksolver_myarm300 import (
    cartesian_to_angles, 
    forward_kinematics, 
    validate_joint_angles,
    JOINT_LIMITS,
    BASE_HEIGHT,
    LINK1_LENGTH,
    LINK2_LENGTH,
    WRIST_LENGTH
)

# Initialize MyArm
mc = MyArm('/dev/ttyAMA0', 115200)

# Configuration parameters
TARGET_POSITION = [180, 0, 250]  # Target object position in mm [x, y, z] - within reach
SCAN_DISTANCE = 80  # Constant distance from target in mm - reduced for workspace
NUM_SCAN_POINTS = 12  # Number of random scan points
MOVEMENT_SPEED = 30  # Movement speed (0-100)
SLEEP_DURATION = 3  # Sleep time between movements in seconds
MAX_MOVEMENT_TIME = 15  # Maximum time to wait for movement completion in seconds

def wait_for_movement_completion(target_angles, timeout=MAX_MOVEMENT_TIME, angle_tolerance=2.0):
    """
    Wait for the MyArm to complete its movement by monitoring is_moving() status 
    and checking if current angles are close to target angles.
    
    Args:
        target_angles: list of target joint angles in degrees
        timeout: maximum time to wait in seconds
        angle_tolerance: acceptable angle difference in degrees
        
    Returns:
        bool: True if movement completed successfully, False if timeout
    """
    start_time = time.time()
    print(f"Waiting for movement completion (timeout: {timeout}s)...")
    
    # First, give the robot a moment to start moving
    time.sleep(0.5)
    
    while time.time() - start_time < timeout:
        try:
            # Check if robot is still moving
            if hasattr(mc, 'is_moving') and callable(mc.is_moving):
                if not mc.is_moving():
                    # Robot reports it's not moving, but let's verify with angles
                    current_angles = mc.get_angles()
                    if current_angles and len(current_angles) == len(target_angles):
                        # Check if current angles are close to target
                        angle_errors = [abs(target_angles[i] - current_angles[i]) for i in range(len(target_angles))]
                        max_error = max(angle_errors)
                        
                        if max_error <= angle_tolerance:
                            elapsed_time = time.time() - start_time
                            print(f"✓ Movement completed in {elapsed_time:.1f}s (max error: {max_error:.1f}°)")
                            return True
                        else:
                            print(f"Robot stopped but angles not accurate enough (max error: {max_error:.1f}°)")
                    
            # If is_moving() is not available, fall back to angle checking only
            else:
                current_angles = mc.get_angles()
                if current_angles and len(current_angles) == len(target_angles):
                    angle_errors = [abs(target_angles[i] - current_angles[i]) for i in range(len(target_angles))]
                    max_error = max(angle_errors)
                    
                    if max_error <= angle_tolerance:
                        elapsed_time = time.time() - start_time
                        print(f"✓ Movement completed in {elapsed_time:.1f}s (max error: {max_error:.1f}°)")
                        return True
                
            time.sleep(0.1)  # Small delay before checking again
            
        except Exception as e:
            print(f"Warning: Error checking movement status: {e}")
            time.sleep(0.1)
    
    # Timeout reached
    print(f"⚠ Movement timeout after {timeout}s")
    return False

def generate_random_scan_points(target_pos, distance, num_points):
    """
    Generate random points on a sphere around the target position
    at a constant distance from the target.
    
    Args:
        target_pos: [x, y, z] position of target object in mm
        distance: constant distance from target in mm
        num_points: number of random points to generate
    
    Returns:
        list of [x, y, z] positions
    """
    points = []
    
    for i in range(num_points):
        # Generate random spherical coordinates
        # Use uniform distribution for better coverage
        u = random.random()  # [0, 1]
        v = random.random()  # [0, 1]
        
        # Convert to spherical coordinates
        theta = 2 * math.pi * u  # azimuth angle [0, 2π]
        phi = math.acos(2 * v - 1)  # polar angle [0, π]
        
        # Convert to Cartesian coordinates
        x = distance * math.sin(phi) * math.cos(theta)
        y = distance * math.sin(phi) * math.sin(theta)
        z = distance * math.cos(phi)
        
        # Translate to target position
        scan_point = [
            target_pos[0] + x,
            target_pos[1] + y,
            target_pos[2] + z
        ]
        
        points.append(scan_point)
    
    return points

def filter_reachable_points(points):
    """
    Filter out points that are outside the robot's workspace.
    
    Args:
        points: list of [x, y, z] positions
        
    Returns:
        list of reachable [x, y, z] positions
    """
    reachable_points = []
    max_horizontal_reach = LINK1_LENGTH + LINK2_LENGTH - 20  # Leave some margin
    
    for point in points:
        x, y, z = point
        horizontal_distance = math.sqrt(x*x + y*y)
        
        # Check horizontal reach
        if horizontal_distance > max_horizontal_reach:
            print(f"Filtering out point [{x:.1f}, {y:.1f}, {z:.1f}] - "
                  f"horizontal distance {horizontal_distance:.1f}mm > max {max_horizontal_reach}mm")
            continue
            
        # Check height limits (rough estimate based on joint 2 limits)
        min_height = BASE_HEIGHT - 120  # When arm points down
        max_height = BASE_HEIGHT + 250  # When arm points up (limited by joint 2)
        
        if z < min_height or z > max_height:
            print(f"Filtering out point [{x:.1f}, {y:.1f}, {z:.1f}] - "
                  f"height {z:.1f}mm outside range [{min_height:.1f}, {max_height:.1f}]mm")
            continue
            
        reachable_points.append(point)
    
    return reachable_points

def perform_scan():
    """
    Perform the scanning motion by moving to each generated point
    """
    print(f"Starting scan around target at {TARGET_POSITION}")
    print(f"Scan distance: {SCAN_DISTANCE}mm")
    print(f"Number of scan points: {NUM_SCAN_POINTS}")
    
    # Generate random scan points
    scan_points = generate_random_scan_points(TARGET_POSITION, SCAN_DISTANCE, NUM_SCAN_POINTS)
    
    # Filter out unreachable points
    scan_points = filter_reachable_points(scan_points)
    
    if len(scan_points) == 0:
        print("ERROR: No reachable scan points generated. Try reducing SCAN_DISTANCE or moving TARGET_POSITION closer.")
        return
        
    print(f"Generated {len(scan_points)} reachable scan points:")
    for i, point in enumerate(scan_points):
        horizontal_dist = math.sqrt(point[0]**2 + point[1]**2)
        print(f"  Point {i+1}: [{point[0]:.1f}, {point[1]:.1f}, {point[2]:.1f}] (dist: {horizontal_dist:.1f}mm)")
    
    # Move to home position first
    home_angles = [0, 0, 0, 0, 0, 0, 0]
    print(f"\nMoving to home position: {home_angles}")
    mc.send_angles(home_angles, MOVEMENT_SPEED)
    wait_for_movement_completion(home_angles)
    
    # Move to each scan point
    for i, point in enumerate(scan_points):
        print(f"\nMoving to scan point {i+1}/{NUM_SCAN_POINTS}: [{point[0]:.1f}, {point[1]:.1f}, {point[2]:.1f}]")
        
        # Convert Cartesian coordinates to joint angles
        try:
            joint_angles = cartesian_to_angles(point)
            
            if joint_angles is None:
                print(f"Skipping unreachable point {i+1}")
                continue
                
            if not validate_joint_angles(joint_angles):
                print(f"Skipping point {i+1} due to joint limit violations")
                continue
                
            print(f"Joint angles: {[f'{angle:.1f}°' for angle in joint_angles]}")
            
            # Verify with forward kinematics
            calculated_pos = forward_kinematics(joint_angles)
            error = [abs(point[i] - calculated_pos[i]) for i in range(3)]
            print(f"FK verification - Target: [{point[0]:.1f}, {point[1]:.1f}, {point[2]:.1f}], "
                  f"Calculated: [{calculated_pos[0]:.1f}, {calculated_pos[1]:.1f}, {calculated_pos[2]:.1f}], "
                  f"Error: [{error[0]:.1f}, {error[1]:.1f}, {error[2]:.1f}] mm")
            
            # Send angles to MyArm
            mc.send_angles(joint_angles, MOVEMENT_SPEED)
            
            # Wait for movement to complete
            movement_success = wait_for_movement_completion(joint_angles)
            
            if not movement_success:
                print(f"Warning: Movement to point {i+1} may not have completed properly")
            
            # Get current position for verification
            current_angles = mc.get_angles()
            if current_angles:
                print(f"Actual angles: {[f'{angle:.1f}°' for angle in current_angles]}")
                
                # Show angle differences
                angle_diffs = [abs(joint_angles[j] - current_angles[j]) for j in range(len(joint_angles))]
                max_diff = max(angle_diffs)
                print(f"Angle differences: {[f'{diff:.1f}°' for diff in angle_diffs]} (max: {max_diff:.1f}°)")
            
        except Exception as e:
            print(f"Error moving to point {i+1}: {e}")
            continue
    
    # Return to home position
    print(f"\nReturning to home position")
    mc.send_angles(home_angles, MOVEMENT_SPEED)
    wait_for_movement_completion(home_angles)
    
    print("Scan complete!")

if __name__ == "__main__":
    import sys
    
    # Check command line arguments for test mode
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("Running inverse kinematics test mode...")
        from iksolver_myarm300 import test_inverse_kinematics
        test_inverse_kinematics()
        sys.exit(0)
    
    try:
        # Check if MyArm is connected
        print("Checking MyArm connection...")
        angles = mc.get_angles()
        if angles is None:
            print("Warning: Could not get current angles. MyArm may not be connected properly.")
            print("You can still run in test mode with: python scan.py --test")
        else:
            print(f"MyArm connected. Current angles: {angles}")
        
        # Perform the scanning motion
        perform_scan()
        
    except KeyboardInterrupt:
        print("\nScan interrupted by user")
    except Exception as e:
        print(f"Error during scan: {e}")
    finally:
        # Ensure we end in a safe position
        try:
            print("Ensuring safe final position...")
            safe_angles = [0, 0, 0, 0, 0, 0, 0]
            mc.send_angles(safe_angles, MOVEMENT_SPEED)
            wait_for_movement_completion(safe_angles, timeout=10)
        except Exception as e:
            print(f"Warning: Could not move to safe position: {e}")
            try:
                # Alternative: just stop the robot
                if hasattr(mc, 'stop'):
                    mc.stop()
                    # Wait for robot to stop moving
                    timeout_count = 0
                    while timeout_count < 50:  # 5 second timeout
                        if hasattr(mc, 'is_moving') and not mc.is_moving():
                            break
                        time.sleep(0.1)
                        timeout_count += 1
            except:
                pass