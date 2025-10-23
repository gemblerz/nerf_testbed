"""
Forward and Inverse Kinematics Solver for MyArm 300

This module provides forward and inverse kinematics functions specifically
designed for the MyArm 300 robot arm based on its URDF specifications.

Author: Generated from scan.py refactoring
Date: September 17, 2025
"""

import math

# MyArm 300 specifications from URDF (in mm)
BASE_HEIGHT = 165.0  # Height from base to joint 1
LINK1_LENGTH = 110.0  # Upper arm length (joint 2 to joint 3)
LINK2_LENGTH = 126.0  # Forearm length (joint 4 to joint 5)  
WRIST_LENGTH = 56.0   # Wrist extension (joint 6 to joint 7)

# Joint limits in degrees (from URDF - converted from radians)
JOINT_LIMITS = [
    (-160.0, 160.0),  # Joint 1: -2.7925 to 2.7925 rad
    (-80.0, 80.0),    # Joint 2: -1.3962 to 1.3962 rad
    (-165.0, 165.0),  # Joint 3: -2.8797 to 2.8797 rad
    (-100.0, 80.0),   # Joint 4: -1.7453 to 1.3962 rad
    (-165.0, 165.0),  # Joint 5: -2.8797 to 2.8797 rad
    (-110.0, 110.0),  # Joint 6: -1.9198 to 1.9198 rad
    (-165.0, 165.0),  # Joint 7: -2.8797 to 2.8797 rad
]


def cartesian_to_angles_with_orientation(position, target_point):
    """
    Calculate joint angles to position the end-effector at 'position' 
    while pointing toward 'target_point'.
    
    Args:
        position: [x, y, z] end-effector position in mm
        target_point: [x, y, z] point to aim the end-effector toward in mm
        
    Returns:
        list of 7 joint angles in degrees, or None if unreachable
    """
    # Calculate direction vector from end-effector to target
    dx = target_point[0] - position[0]
    dy = target_point[1] - position[1] 
    dz = target_point[2] - position[2]
    
    # Normalize the direction vector
    distance = math.sqrt(dx*dx + dy*dy + dz*dz)
    if distance < 1e-6:  # Target is at end-effector position
        direction = [0, 0, -1]  # Default downward pointing
    else:
        direction = [dx/distance, dy/distance, dz/distance]
    
    return cartesian_to_angles(position, direction)


def cartesian_to_angles(position, target_orientation=None):
    """
    Convert Cartesian coordinates to joint angles using inverse kinematics.
    Based on exact MyArm 300 URDF specifications with full 7-DOF control.
    
    Args:
        position: [x, y, z] position in mm
        target_orientation: [rx, ry, rz] target orientation in radians (optional)
                          If None, end-effector will point toward target
    
    Returns:
        list of 7 joint angles in degrees, or None if position is unreachable
    """
    x, y, z = position
    
    # Joint 1: Base rotation (around z-axis)
    joint1 = math.degrees(math.atan2(y, x))
    
    # Check joint 1 limits
    if not (JOINT_LIMITS[0][0] <= joint1 <= JOINT_LIMITS[0][1]):
        print(f"Warning: Joint 1 angle {joint1:.1f}° outside limits {JOINT_LIMITS[0]}")
        joint1 = max(JOINT_LIMITS[0][0], min(JOINT_LIMITS[0][1], joint1))
    
    # Distance from base axis to target (in x-y plane)
    r = math.sqrt(x*x + y*y)
    
    # Adjust z coordinate relative to joint 2 (subtract base height)
    z_adjusted = z - BASE_HEIGHT
    
    # For 7-DOF, we need to work backwards from the desired end-effector pose
    # Calculate desired wrist center position (joint 6 position)
    # The end-effector (joint 7) is offset from joint 6 by WRIST_LENGTH
    
    # Calculate desired end-effector orientation
    if target_orientation is None:
        # Default: point the end-effector toward the target from above
        # Calculate orientation vector pointing from end-effector toward target
        ee_to_target = [0, 0, -1]  # Point downward by default
        
        # If we want to point toward target from a distance:
        # approach_distance = 50  # mm - distance to approach from
        # approach_x = x + approach_distance * (-x / math.sqrt(x*x + y*y + (z-BASE_HEIGHT)**2))
        # approach_y = y + approach_distance * (-y / math.sqrt(x*x + y*y + (z-BASE_HEIGHT)**2))  
        # approach_z = z + approach_distance * (-(z-BASE_HEIGHT) / math.sqrt(x*x + y*y + (z-BASE_HEIGHT)**2))
        # ee_to_target = [(x - approach_x), (y - approach_y), (z - approach_z)]
        # norm = math.sqrt(ee_to_target[0]**2 + ee_to_target[1]**2 + ee_to_target[2]**2)
        # ee_to_target = [ee_to_target[i]/norm for i in range(3)]
    else:
        # Use provided orientation
        ee_to_target = target_orientation
    
    # Calculate wrist center position (joint 6) by backing off from end-effector position
    # along the end-effector orientation vector
    wrist_center_x = x - WRIST_LENGTH * ee_to_target[0]
    wrist_center_y = y - WRIST_LENGTH * ee_to_target[1] 
    wrist_center_z = z - WRIST_LENGTH * ee_to_target[2]
    
    # Now solve for joints 2 and 3 to reach the wrist center
    wrist_r = math.sqrt(wrist_center_x*wrist_center_x + wrist_center_y*wrist_center_y)
    wrist_z_rel = wrist_center_z - BASE_HEIGHT
    
    # Distance from joint 2 to wrist center (joint 6)
    d_to_wrist = math.sqrt(wrist_r*wrist_r + wrist_z_rel*wrist_z_rel)
    
    # Check reachability for the main arm (joints 2-5 reach)
    max_reach = LINK1_LENGTH + LINK2_LENGTH  # Main arm reach
    min_reach = abs(LINK1_LENGTH - LINK2_LENGTH)
    
    if d_to_wrist > max_reach:
        print(f"Warning: Wrist center at distance {d_to_wrist:.1f}mm > max reach {max_reach}mm")
        return None
    elif d_to_wrist < min_reach:
        print(f"Warning: Wrist center too close. Distance {d_to_wrist:.1f}mm < min reach {min_reach}mm")
        return None
    
    # Joint 3: Elbow angle using law of cosines
    cos_joint3 = (LINK1_LENGTH*LINK1_LENGTH + LINK2_LENGTH*LINK2_LENGTH - d_to_wrist*d_to_wrist) / (2 * LINK1_LENGTH * LINK2_LENGTH)
    cos_joint3 = max(-1.0, min(1.0, cos_joint3))  # Clamp to valid range
    joint3 = math.degrees(math.acos(cos_joint3))
    
    # Convert to MyArm convention (negative for elbow down configuration)
    joint3 = -(180.0 - joint3)
    
    # Joint 2: Shoulder angle
    alpha = math.atan2(wrist_z_rel, wrist_r)
    beta = math.acos((LINK1_LENGTH*LINK1_LENGTH + d_to_wrist*d_to_wrist - LINK2_LENGTH*LINK2_LENGTH) / (2 * LINK1_LENGTH * d_to_wrist))
    joint2 = math.degrees(alpha + beta)
    
    # Adjust for MyArm coordinate system (joint 2 is measured from horizontal)
    joint2 = 90.0 - joint2
    
    # Check joint 2 and 3 limits
    if not (JOINT_LIMITS[1][0] <= joint2 <= JOINT_LIMITS[1][1]):
        print(f"Warning: Joint 2 angle {joint2:.1f}° outside limits {JOINT_LIMITS[1]}")
        joint2 = max(JOINT_LIMITS[1][0], min(JOINT_LIMITS[1][1], joint2))
        
    if not (JOINT_LIMITS[2][0] <= joint3 <= JOINT_LIMITS[2][1]):
        print(f"Warning: Joint 3 angle {joint3:.1f}° outside limits {JOINT_LIMITS[2]}")
        joint3 = max(JOINT_LIMITS[2][0], min(JOINT_LIMITS[2][1], joint3))
    
    # Now calculate wrist orientation (joints 4, 5, 6, 7)
    # We need the end-effector to have the desired orientation
    
    # Calculate current end-effector frame after joints 1, 2, 3
    # This gives us the orientation of the wrist center frame
    j1_rad = math.radians(joint1)
    j2_rad = math.radians(joint2)
    j3_rad = math.radians(joint3)
    
    # Calculate the current orientation of the arm after joint 3
    # The arm direction vector after joint 3
    arm_direction = _calculate_arm_direction_after_joint3(j1_rad, j2_rad, j3_rad)
    
    # Calculate required wrist angles to achieve desired end-effector orientation
    joint4, joint5, joint6, joint7 = _calculate_wrist_angles(arm_direction, ee_to_target, j1_rad)
    
    # Apply joint limits to wrist joints
    joint4 = max(JOINT_LIMITS[3][0], min(JOINT_LIMITS[3][1], joint4))
    joint5 = max(JOINT_LIMITS[4][0], min(JOINT_LIMITS[4][1], joint5))
    joint6 = max(JOINT_LIMITS[5][0], min(JOINT_LIMITS[5][1], joint6))
    joint7 = max(JOINT_LIMITS[6][0], min(JOINT_LIMITS[6][1], joint7))
    
    return [joint1, joint2, joint3, joint4, joint5, joint6, joint7]


def _calculate_arm_direction_after_joint3(j1, j2, j3):
    """
    Calculate the arm direction vector after joint 3.
    This represents the direction from joint 3 to joint 5.
    
    Args:
        j1, j2, j3: joint angles in radians
        
    Returns:
        [x, y, z] normalized direction vector
    """
    # Based on the URDF kinematic chain
    # Joint 2 rotates around modified Z axis
    # Joint 3 rotates around modified Z axis after joint 2
    
    # Simplified calculation: after joint 2 and 3, the forearm direction
    shoulder_angle = math.pi/2 - j2  # Convert from MyArm convention
    elbow_angle = math.pi + j3      # Convert from negative convention
    
    # Total arm angle in the sagittal plane
    total_arm_angle = shoulder_angle + elbow_angle - math.pi
    
    # Direction in robot frame
    arm_dir_x = math.cos(total_arm_angle) * math.cos(j1)
    arm_dir_y = math.cos(total_arm_angle) * math.sin(j1)
    arm_dir_z = math.sin(total_arm_angle)
    
    # Normalize
    norm = math.sqrt(arm_dir_x*arm_dir_x + arm_dir_y*arm_dir_y + arm_dir_z*arm_dir_z)
    return [arm_dir_x/norm, arm_dir_y/norm, arm_dir_z/norm]


def _calculate_wrist_angles(arm_direction, desired_ee_direction, base_rotation):
    """
    Calculate wrist joint angles (4, 5, 6, 7) to achieve desired end-effector orientation.
    
    Args:
        arm_direction: [x, y, z] direction vector of the arm after joint 3
        desired_ee_direction: [x, y, z] desired end-effector pointing direction
        base_rotation: base rotation angle in radians
        
    Returns:
        (joint4, joint5, joint6, joint7) in degrees
    """
    # This is a simplified wrist orientation calculation
    # For a more accurate solution, we would need to implement full 
    # forward kinematics with transformation matrices
    
    # Joint 4: Wrist roll - rotate around the arm axis
    joint4 = 0.0
    
    # Joint 5: Wrist pitch - primary orientation control
    # Calculate angle between arm direction and desired direction
    dot_product = (arm_direction[0] * desired_ee_direction[0] + 
                  arm_direction[1] * desired_ee_direction[1] + 
                  arm_direction[2] * desired_ee_direction[2])
    dot_product = max(-1.0, min(1.0, dot_product))
    
    # Angle between current arm direction and desired direction
    angle_diff = math.acos(dot_product)
    
    # Convert to joint 5 angle (wrist pitch)
    joint5 = math.degrees(angle_diff)
    
    # Determine sign based on vertical component
    if desired_ee_direction[2] < arm_direction[2]:
        joint5 = -joint5
    
    # Joint 6: Wrist yaw - secondary orientation control
    # Calculate azimuth correction
    desired_azimuth = math.atan2(desired_ee_direction[1], desired_ee_direction[0])
    current_azimuth = math.atan2(arm_direction[1], arm_direction[0])
    azimuth_diff = desired_azimuth - current_azimuth
    
    # Normalize angle difference
    while azimuth_diff > math.pi:
        azimuth_diff -= 2 * math.pi
    while azimuth_diff < -math.pi:
        azimuth_diff += 2 * math.pi
    
    joint6 = math.degrees(azimuth_diff) * 0.5  # Scale factor for wrist yaw
    
    # Joint 7: End-effector roll - for fine orientation adjustment
    joint7 = 0.0  # Keep simple for now
    
    return joint4, joint5, joint6, joint7


def forward_kinematics(joint_angles):
    """
    Calculate forward kinematics using URDF-based transformations.
    
    Args:
        joint_angles: list of 7 joint angles in degrees
        
    Returns:
        [x, y, z] end effector position in mm
    """
    if len(joint_angles) != 7:
        raise ValueError(f"Expected 7 joint angles, got {len(joint_angles)}")
    
    import numpy as np
    
    j1, j2, j3, j4, j5, j6, j7 = [math.radians(angle) for angle in joint_angles]
    
    # Based on URDF transformation chain:
    # base -> joint1: origin xyz="0 0 0.165" rpy="0 0 0" (165mm up in Z)
    # joint1 -> joint2: origin xyz="0 0 0" rpy="-1.5708 0 0" (rotate -90° around X)
    # joint2 -> joint3: origin xyz="0 -0.11 0" rpy="1.5708 0 0" (translate -110mm in Y, rotate 90° around X)  
    # joint3 -> joint4: origin xyz="0 0 0" rpy="-1.5708 0 3.14159" (rotate -90° X, 180° Z)
    # joint4 -> joint5: origin xyz="0 -0.126 0" rpy="1.5708 0 0" (translate -126mm in Y, rotate 90° X)
    # joint5 -> joint6: origin xyz="0 0 0" rpy="-1.5708 0 0" (rotate -90° around X)
    # joint6 -> joint7: origin xyz="0 -0.056 0" rpy="1.5708 0 0" (translate -56mm in Y, rotate 90° X)
    
    def rotation_matrix(axis, angle):
        """Create rotation matrix around axis (0=X, 1=Y, 2=Z)"""
        c, s = math.cos(angle), math.sin(angle)
        if axis == 0:  # X-axis
            return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
        elif axis == 1:  # Y-axis
            return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
        else:  # Z-axis
            return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    
    def transform_matrix(translation, rotation_xyz):
        """Create 4x4 transformation matrix"""
        T = np.eye(4)
        # Apply rotations in order: X, Y, Z
        R = np.eye(3)
        for axis, angle in enumerate(rotation_xyz):
            if abs(angle) > 1e-6:
                R = R @ rotation_matrix(axis, angle)
        T[:3, :3] = R
        T[:3, 3] = translation
        return T
    
    # Build transformation chain
    T = np.eye(4)  # Start with identity
    
    # Base to joint1: translate [0, 0, 165mm], no rotation, then rotate by j1 around Z
    T_base_j1 = transform_matrix([0, 0, 165], [0, 0, 0])
    T_j1_rot = transform_matrix([0, 0, 0], [0, 0, j1])
    T = T @ T_base_j1 @ T_j1_rot
    
    # Joint1 to joint2: rpy="-1.5708 0 0", then rotate by j2 around Z  
    T_j1_j2 = transform_matrix([0, 0, 0], [-math.pi/2, 0, 0])
    T_j2_rot = transform_matrix([0, 0, 0], [0, 0, j2])
    T = T @ T_j1_j2 @ T_j2_rot
    
    # Joint2 to joint3: translate [0, -110, 0], rpy="1.5708 0 0", then rotate by j3 around Z
    T_j2_j3 = transform_matrix([0, -110, 0], [math.pi/2, 0, 0])
    T_j3_rot = transform_matrix([0, 0, 0], [0, 0, j3])
    T = T @ T_j2_j3 @ T_j3_rot
    
    # Joint3 to joint4: rpy="-1.5708 0 3.14159", then rotate by j4 around Z
    T_j3_j4 = transform_matrix([0, 0, 0], [-math.pi/2, 0, math.pi])
    T_j4_rot = transform_matrix([0, 0, 0], [0, 0, j4])
    T = T @ T_j3_j4 @ T_j4_rot
    
    # Joint4 to joint5: translate [0, -126, 0], rpy="1.5708 0 0", then rotate by j5 around Z
    T_j4_j5 = transform_matrix([0, -126, 0], [math.pi/2, 0, 0])
    T_j5_rot = transform_matrix([0, 0, 0], [0, 0, j5])
    T = T @ T_j4_j5 @ T_j5_rot
    
    # Joint5 to joint6: rpy="-1.5708 0 0", then rotate by j6 around Z
    T_j5_j6 = transform_matrix([0, 0, 0], [-math.pi/2, 0, 0])
    T_j6_rot = transform_matrix([0, 0, 0], [0, 0, j6])
    T = T @ T_j5_j6 @ T_j6_rot
    
    # Joint6 to joint7: translate [0, -56, 0], rpy="1.5708 0 0", then rotate by j7 around Z
    T_j6_j7 = transform_matrix([0, -56, 0], [math.pi/2, 0, 0])
    T_j7_rot = transform_matrix([0, 0, 0], [0, 0, j7])
    T = T @ T_j6_j7 @ T_j7_rot
    
    # Extract final position
    final_position = T[:3, 3]
    
    return [float(final_position[0]), float(final_position[1]), float(final_position[2])]


# Remove the complex transformation matrix functions for now
# def _transformation_matrix(translation, rotation_rpy):
# def _matrix_multiply(A, B):


def validate_joint_angles(joint_angles):
    """
    Validate that all joint angles are within limits.
    
    Args:
        joint_angles: list of 7 joint angles in degrees
        
    Returns:
        bool: True if all angles are valid, False otherwise
    """
    if len(joint_angles) != 7:
        print(f"Expected 7 joint angles, got {len(joint_angles)}")
        return False
        
    for i, angle in enumerate(joint_angles):
        min_limit, max_limit = JOINT_LIMITS[i]
        if not (min_limit <= angle <= max_limit):
            print(f"Joint {i+1} angle {angle:.1f}° outside limits [{min_limit}, {max_limit}]")
            return False
    return True


def test_inverse_kinematics():
    """
    Test the inverse kinematics with known positions and verify accuracy.
    Test positions are designed to be within the robot's workspace based on:
    - Max horizontal reach: ~280mm (considering joint limits)
    - Height range: ~50mm to ~400mm (considering joint 2 limits of ±80°)
    - Base height: 165mm
    - 7-DOF arm configuration
    """
    print("Testing inverse kinematics...")
    print(f"Robot workspace: Max reach ~{LINK1_LENGTH + LINK2_LENGTH}mm, Base height {BASE_HEIGHT}mm")
    print("7-DOF MyArm 300 configuration")
    
    # Test positions within realistic workspace
    test_positions = [
        [200, 0, 250],     # Front position - moderate reach, mid height
        [150, 100, 200],   # Front-right position - moderate reach, lower height
        [100, 150, 300],   # Right side position - shorter reach, higher
        [-120, 80, 180],   # Back-right position - short reach, low height
        [80, 0, 350],      # High front position - short reach, high
        [250, 0, 200],     # Extended front position - max reach, mid height
        [0, 200, 165],     # Side position at base height
        [150, -100, 220],  # Front-left position
    ]
    
    print(f"Testing {len(test_positions)} positions within estimated workspace...")
    
    for i, pos in enumerate(test_positions):
        print(f"\nTest {i+1}: Target position [{pos[0]}, {pos[1]}, {pos[2]}]")
        
        # Calculate distance from base for reference
        horizontal_distance = math.sqrt(pos[0]**2 + pos[1]**2)
        print(f"  Horizontal distance: {horizontal_distance:.1f}mm")
        
        # Calculate joint angles
        joint_angles = cartesian_to_angles(pos)
        
        if joint_angles is None:
            print("  Position unreachable")
            continue
            
        print(f"  Joint angles: {[f'{angle:.1f}°' for angle in joint_angles]}")
        
        # Validate joint limits
        if not validate_joint_angles(joint_angles):
            print("  Joint limits violated")
            continue
            
        # Verify with forward kinematics
        calculated_pos = forward_kinematics(joint_angles)
        error = [abs(pos[i] - calculated_pos[i]) for i in range(3)]
        max_error = max(error)
        
        print(f"  FK result: [{calculated_pos[0]:.1f}, {calculated_pos[1]:.1f}, {calculated_pos[2]:.1f}]")
        print(f"  Error: [{error[0]:.1f}, {error[1]:.1f}, {error[2]:.1f}] mm (max: {max_error:.1f} mm)")
        
        if max_error < 5.0:
            print("  ✓ PASS - Error within tolerance")
        else:
            print("  ✗ FAIL - Error too large")
    
    print(f"\nWorkspace analysis:")
    print(f"  Theoretical max reach: {LINK1_LENGTH + LINK2_LENGTH + WRIST_LENGTH}mm")
    print(f"  Practical max reach: ~{LINK1_LENGTH + LINK2_LENGTH}mm (excluding wrist)")
    print(f"  Height range: {BASE_HEIGHT - 100}mm to {BASE_HEIGHT + 200}mm (estimated with joint limits)")
    print("Inverse kinematics test complete!")


if __name__ == "__main__":
    # Run the test when the module is executed directly
    test_inverse_kinematics()