#!/usr/bin/env python3
"""
Simple test to verify ray tracing camera follows vector direction
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from graph_canvas.presentation.desktop.gui.sphere_3d import SphereRenderer
import numpy as np

def test_ray_tracing_camera():
    """Test if ray tracing camera follows vector direction"""
    print("=== Ray Tracing Camera Test ===")
    
    # Create a sphere renderer
    sphere = SphereRenderer()
    
    print(f"Initial camera position: {sphere.screen_camera_position}")
    print(f"Initial camera target: {sphere.screen_camera_target}")
    print(f"Initial vector direction: {getattr(sphere, 'vector_direction', 'NOT SET')}")
    
    # Set vector direction to point toward red cube
    sphere.set_vector_direction(1, 0, 1)  # Should point toward cube at (2,0,2)
    
    print(f"After setting vector to (1,0,1):")
    print(f"Vector direction: {sphere.vector_direction}")
    print(f"Camera position: {sphere.screen_camera_position}")
    print(f"Camera target: {sphere.screen_camera_target}")
    
    # Calculate expected camera direction
    camera_dir = sphere.screen_camera_target - sphere.screen_camera_position
    camera_dir = camera_dir / np.linalg.norm(camera_dir)
    print(f"Camera direction: {camera_dir}")
    
    # Expected direction to cube
    cube_pos = np.array([2.0, 0.0, 2.0])
    expected_dir = cube_pos / np.linalg.norm(cube_pos)
    print(f"Expected direction to cube: {expected_dir}")
    
    # Check if they match
    match = np.allclose(camera_dir, expected_dir, atol=0.1)
    print(f"Do camera direction and cube direction match? {match}")
    
    if match:
        print("✅ SUCCESS: Ray tracing camera is following vector direction!")
    else:
        print("❌ FAILURE: Ray tracing camera is NOT following vector direction!")
        print(f"   Camera dir: [{camera_dir[0]:.3f}, {camera_dir[1]:.3f}, {camera_dir[2]:.3f}]")
        print(f"   Expected:   [{expected_dir[0]:.3f}, {expected_dir[1]:.3f}, {expected_dir[2]:.3f}]")
        print(f"   Difference: {np.linalg.norm(camera_dir - expected_dir):.3f}")

if __name__ == "__main__":
    test_ray_tracing_camera()

