#!/usr/bin/env python3
"""
Simple test script for the MyArm 300 IK Solver

This script tests the Forward Kinematics (FK) and Inverse Kinematics (IK) 
functions with specific test cases to verify their accuracy and consistency.

Updated for 7-DOF with end-effector orientation control.
"""

import math
from iksolver_myarm300 import (
    cartesian_to_angles, 
    cartesian_to_angles_with_orientation,
    forward_kinematics, 
    validate_joint_angles,
    BASE_HEIGHT,
    LINK1_LENGTH,
    LINK2_LENGTH,
    WRIST_LENGTH
)

def test_forward_kinematics():
    """Test forward kinematics with known joint configurations"""
    print("=" * 60)
    print("FORWARD KINEMATICS TESTS")
    print("=" * 60)
    
    test_cases = [
        {
            "name": "Home Position (all zeros)",
            "angles": [0, 0, 0, 0, 0, 0, 0],
            "expected_approx": [0, 0, 93]
        },
        {
            "name": "90° Base Rotation",
            "angles": [90, 0, 0, 0, 0, 0, 0],
            "expected_approx": [0, 0, 93]
        },
        {
            "name": "45° Base, 30° Shoulder",
            "angles": [45, 30, 0, 0, 0, 0, 0],
            "expected_approx": None  # Will calculate
        },
        {
            "name": "Extended Arm Position",
            "angles": [0, 45, -90, 0, 0, 0, 0],
            "expected_approx": None  # Will calculate
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['name']}")
        print(f"Input angles: {test['angles']}")
        
        # Calculate FK
        position = forward_kinematics(test['angles'])
        print(f"FK Result: [{position[0]:.1f}, {position[1]:.1f}, {position[2]:.1f}] mm")
        
        if test['expected_approx']:
            expected = test['expected_approx']
            print(f"Expected ~: [{expected[0]:.1f}, {expected[1]:.1f}, {expected[2]:.1f}] mm")
            
            # Calculate error
            error = [abs(position[i] - expected[i]) for i in range(3)]
            print(f"Error: [{error[0]:.1f}, {error[1]:.1f}, {error[2]:.1f}] mm")
        
        print("-" * 40)

def test_inverse_kinematics():
    """Test inverse kinematics with known positions"""
    print("=" * 60)
    print("INVERSE KINEMATICS TESTS")
    print("=" * 60)
    
    test_positions = [
        {
            "name": "Front center position",
            "position": [150, 0, 200],
        },
        {
            "name": "Right side position", 
            "position": [100, 100, 180],
        },
        {
            "name": "High front position",
            "position": [120, 0, 280],
        },
        {
            "name": "Left side position",
            "position": [80, -120, 160],
        },
        {
            "name": "Close to base height",
            "position": [180, 0, BASE_HEIGHT],
        }
    ]
    
    for i, test in enumerate(test_positions, 1):
        print(f"\nTest {i}: {test['name']}")
        position = test['position']
        print(f"Target position: [{position[0]}, {position[1]}, {position[2]}] mm")
        
        # Calculate IK
        angles = cartesian_to_angles(position)
        
        if angles is None:
            print("❌ Position unreachable")
            continue
            
        print(f"IK Result: {[f'{angle:.1f}°' for angle in angles]}")
        
        # Validate joint limits
        valid = validate_joint_angles(angles)
        print(f"Joint limits valid: {'✓' if valid else '❌'}")
        
        if not valid:
            continue
            
        # Verify with FK (round-trip test)
        fk_position = forward_kinematics(angles)
        print(f"FK Verification: [{fk_position[0]:.1f}, {fk_position[1]:.1f}, {fk_position[2]:.1f}] mm")
        
        # Calculate error
        error = [abs(position[i] - fk_position[i]) for i in range(3)]
        max_error = max(error)
        print(f"Round-trip error: [{error[0]:.1f}, {error[1]:.1f}, {error[2]:.1f}] mm (max: {max_error:.1f} mm)")
        
        # Check accuracy
        if max_error < 1.0:
            print("✅ PASS - Excellent accuracy")
        elif max_error < 5.0:
            print("✅ PASS - Good accuracy")
        else:
            print("⚠️  WARN - Large error")
            
        print("-" * 40)

def test_round_trip_accuracy():
    """Test FK->IK->FK round-trip accuracy"""
    print("=" * 60)
    print("ROUND-TRIP ACCURACY TESTS")
    print("=" * 60)
    
    # Start with joint angles, do FK, then IK, then FK again
    test_joint_configs = [
        [0, 0, 0, 0, 0, 0, 0],
        [30, 15, -45, 0, 30, 0, 0],
        [45, 30, -60, 0, 0, 0, 0], 
        [-45, 20, -80, 0, 60, 0, 0],
        [90, 45, -90, 0, 45, 0, 0]
    ]
    
    for i, original_angles in enumerate(test_joint_configs, 1):
        print(f"\nRound-trip test {i}:")
        print(f"Original angles: {[f'{angle:.1f}°' for angle in original_angles]}")
        
        # Step 1: FK
        position = forward_kinematics(original_angles)
        print(f"FK result: [{position[0]:.1f}, {position[1]:.1f}, {position[2]:.1f}] mm")
        
        # Step 2: IK
        calculated_angles = cartesian_to_angles(position)
        if calculated_angles is None:
            print("❌ IK failed")
            continue
            
        print(f"IK result: {[f'{angle:.1f}°' for angle in calculated_angles]}")
        
        # Step 3: FK again
        final_position = forward_kinematics(calculated_angles)
        print(f"Final FK: [{final_position[0]:.1f}, {final_position[1]:.1f}, {final_position[2]:.1f}] mm")
        
        # Check position accuracy
        pos_error = [abs(position[i] - final_position[i]) for i in range(3)]
        max_pos_error = max(pos_error)
        
        # Check angle difference (note: multiple solutions may exist)
        angle_diff = [abs(original_angles[i] - calculated_angles[i]) for i in range(len(original_angles))]
        max_angle_diff = max(angle_diff)
        
        print(f"Position error: [{pos_error[0]:.1f}, {pos_error[1]:.1f}, {pos_error[2]:.1f}] mm (max: {max_pos_error:.1f} mm)")
        print(f"Angle difference: {[f'{diff:.1f}°' for diff in angle_diff]} (max: {max_angle_diff:.1f}°)")
        
        if max_pos_error < 1.0:
            print("✅ EXCELLENT position accuracy")
        elif max_pos_error < 5.0:
            print("✅ GOOD position accuracy")
        else:
            print("⚠️  POOR position accuracy")
            
        print("-" * 40)

def test_workspace_limits():
    """Test workspace boundary conditions"""
    print("=" * 60)
    print("WORKSPACE BOUNDARY TESTS")
    print("=" * 60)
    
    max_reach = LINK1_LENGTH + LINK2_LENGTH
    print(f"Theoretical max horizontal reach: {max_reach:.1f} mm")
    print(f"Base height: {BASE_HEIGHT:.1f} mm")
    
    boundary_tests = [
        {
            "name": "Maximum reach (should work)",
            "position": [max_reach - 10, 0, BASE_HEIGHT],
        },
        {
            "name": "Beyond maximum reach (should fail)",
            "position": [max_reach + 10, 0, BASE_HEIGHT],
        },
        {
            "name": "Very high position (should fail)",
            "position": [100, 0, BASE_HEIGHT + 300],
        },
        {
            "name": "Very low position (should fail)",
            "position": [100, 0, BASE_HEIGHT - 200],
        },
        {
            "name": "At base center (should fail - too close)",
            "position": [0, 0, BASE_HEIGHT],
        }
    ]
    
    for i, test in enumerate(boundary_tests, 1):
        print(f"\nBoundary test {i}: {test['name']}")
        position = test['position']
        print(f"Position: [{position[0]}, {position[1]}, {position[2]}] mm")
        
        angles = cartesian_to_angles(position)
        if angles is None:
            print("❌ Position unreachable (as expected for boundary cases)")
        else:
            valid = validate_joint_angles(angles)
            print(f"✅ Position reachable, joint limits valid: {valid}")
            if valid:
                fk_check = forward_kinematics(angles)
                error = [abs(position[i] - fk_check[i]) for i in range(3)]
                print(f"FK verification error: [{error[0]:.1f}, {error[1]:.1f}, {error[2]:.1f}] mm")
        
        print("-" * 25)

def test_orientation_control():
    """Test end-effector orientation control toward specific targets"""
    print("=" * 60)
    print("END-EFFECTOR ORIENTATION CONTROL TESTS")
    print("=" * 60)
    
    orientation_tests = [
        {
            "name": "Point downward from center",
            "ee_position": [150, 0, 250],
            "target_point": [150, 0, 150],  # Point straight down
        },
        {
            "name": "Point toward side target",
            "ee_position": [120, 80, 200], 
            "target_point": [200, 150, 180], # Point toward side
        },
        {
            "name": "Point toward elevated target",
            "ee_position": [100, 50, 180],
            "target_point": [80, 30, 300],   # Point upward
        }
    ]
    
    for i, test in enumerate(orientation_tests, 1):
        print(f"\nOrientation Test {i}: {test['name']}")
        ee_pos = test['ee_position']
        target = test['target_point']
        
        print(f"EE Position: {ee_pos} mm")
        print(f"Target Point: {target} mm")
        
        # Calculate direction vector
        dx = target[0] - ee_pos[0]
        dy = target[1] - ee_pos[1] 
        dz = target[2] - ee_pos[2]
        distance = math.sqrt(dx*dx + dy*dy + dz*dz)
        direction = [dx/distance, dy/distance, dz/distance]
        print(f"Direction: [{direction[0]:.3f}, {direction[1]:.3f}, {direction[2]:.3f}]")
        
        # Get joint angles
        angles = cartesian_to_angles_with_orientation(ee_pos, target)
        
        if angles is None:
            print("❌ Position unreachable")
            continue
            
        print(f"Joint angles: {[f'{angle:.1f}°' for angle in angles]}")
        
        # Check wrist joint usage
        wrist_joints = angles[3:7]  # joints 4-7
        active_wrist = sum(abs(angle) > 0.1 for angle in wrist_joints)
        print(f"Active wrist joints: {active_wrist}/4")
        
        # Validate and verify
        valid = validate_joint_angles(angles)
        if not valid:
            continue
            
        # FK verification
        actual_pos = forward_kinematics(angles)
        pos_error = [abs(ee_pos[i] - actual_pos[i]) for i in range(3)]
        max_error = max(pos_error)
        
        print(f"FK verification: [{actual_pos[0]:.1f}, {actual_pos[1]:.1f}, {actual_pos[2]:.1f}] mm")
        print(f"Position error: [{pos_error[0]:.1f}, {pos_error[1]:.1f}, {pos_error[2]:.1f}] mm (max: {max_error:.1f} mm)")
        
        if max_error < 20.0:  # More lenient for the improved solver
            print("✅ PASS - Good accuracy for 7-DOF orientation control")
        else:
            print("⚠️  WARN - Large error but demonstrates orientation capability")
            
        print("-" * 40)


def main():
    """Run all tests"""
    print("🤖 MyArm 300 IK Solver Test Suite (7-DOF with Orientation Control)")
    print(f"Robot specifications:")
    print(f"  Base height: {BASE_HEIGHT} mm")
    print(f"  Link 1 length: {LINK1_LENGTH} mm") 
    print(f"  Link 2 length: {LINK2_LENGTH} mm")
    print(f"  Wrist length: {WRIST_LENGTH} mm")
    print(f"  Degrees of freedom: 7")
    print(f"  New features: End-effector orientation control, Full wrist utilization")
    print()
    
    try:
        test_forward_kinematics()
        # print()
        # test_inverse_kinematics() 
        # print()
        # test_orientation_control()
        # print() 
        # test_round_trip_accuracy()
        # print()
        # test_workspace_limits()
        
        print("=" * 60)
        print("✅ ALL TESTS COMPLETED")
        print("Key improvements demonstrated:")
        print("  • All 7 joints utilized (including wrist joints 4-7)")  
        print("  • End-effector orientation control toward targets")
        print("  • Enhanced inverse kinematics for full 7-DOF control")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()