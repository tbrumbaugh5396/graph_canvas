#!/usr/bin/env python3
"""
Test script for the 3D Sphere visualization.
Run this to see the 3D sphere with all its features.
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

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph_canvas.presentation.desktop.gui.sphere_3d import Sphere3DApp

if __name__ == "__main__":
    print("Starting 3D Sphere Visualization...")
    print("\nControls:")
    print("- Left mouse drag: Rotate camera around sphere")
    print("- Mouse wheel: Zoom in/out")
    print("- Arrow keys: Move camera left/right/up/down in 3D space")
    print("- I key: Move camera forward (into the screen)")
    print("- O key: Move camera backward (out of the screen)")
    print("- Menu bar: Access all sphere and grid controls")
    print("\nFeatures:")
    print("- Sphere transformations (position, rotation, scale)")
    print("- Color and transparency controls")
    print("- Multiple grid systems:")
    print("  * Longitude/Latitude grids")
    print("  * Concentric circles")
    print("  * Dot particles (Fibonacci spiral distribution)")
    print("  * Neon-style lines with glow effects")
    print("  * Wireframe mode")
    print("- Customizable grid colors")
    print("- Grid parameter adjustments")
    print("- Adjustable wireframe density")
    print("- Proper transparency rendering (shows back side and grids)")
    print("- Toggleable lighting system")
    print("- Configurable 3D vector from sphere center with arrow head")
    print("- Toggleable cone section with configurable angle and length (or infinite length)")
    print("- Toggleable 4-sided pyramid with dual angle control (or infinite length)")
    print("- Toggleable rectangular cuboid with configurable length, width, and height (or infinite length)")
    print("- Near plane cutting system that converts shapes to truncated versions:")
    print("  * Pyramid becomes hexahedron (truncated pyramid)")
    print("  * Cone becomes truncated cone")
    print("  * Cuboid becomes smaller cuboid")
    print("- Sphere intersection display shows where shapes intersect sphere surface")
    print("  * Cone creates circular cap on sphere")
    print("  * Pyramid creates rectangular patch on sphere")
    print("  * Cuboid creates rectangular patch on sphere")
    print("- Normal ray visualization shows surface normal vectors")
    print("  * Rays extend orthogonally from sphere surface")
    print("  * Configurable length, density, color, and thickness")
    print("- Intersection normal rays show normals only on intersection surfaces")
    print("  * Focused normal rays on cone, pyramid, and cuboid intersections")
    print("  * Separate color and properties from general normal rays")
    print("- Truncation normal rays show normals on near plane cut surfaces")
    print("  * Normal rays extending from truncated flat surfaces of shapes")
    print("  * Visualizes the tangent plane orientation on cutting planes")
    print("- 2D Ray Tracing Screen system with advanced rendering")
    print("  * Ray tracing, path tracing, PBR, and ray marching rendering modes")
    print("  * Virtual camera with configurable position and target")
    print("  * Real-time ray-traced image displayed on 3D screen")
    print("  * Adjustable screen position, rotation, and size in 3D space")
    print("  * Configurable resolution, update rate, and anti-aliasing")
    print("  * Multiple ray bounces for realistic reflections")
    print("\nTry the menu options to explore all features!")
    print("\nVisual Tips:")
    print("- Set transparency to 0-50% to see grids through the sphere")
    print("- Grids will be visible on both sides when sphere is transparent")
    print("- Adjust wireframe density in Grids > Grid Parameters menu")
    print("- Toggle lighting in View menu for flat vs 3D shaded appearance")
    print("- Enable vector in Vector menu and try preset directions")
    print("- Vector is great for showing normals, axes, or reference directions")
    print("- Enable cone to visualize field of view, light cones, or angular regions")
    print("- Cone follows vector direction - perfect for spotlight or radar visualization")
    print("- Pyramid offers rectangular coverage with independent horizontal/vertical angles")
    print("- Perfect for camera sensors, rectangular beams, or asymmetric coverage areas")
    print("- Cuboid creates solid rectangular volumes - ideal for collision boxes, building blocks")
    print("- All shapes align with vector direction for coherent directional visualization")
    print("- Enable infinite length for shapes to extend beyond normal boundaries")
    print("- Use Near Plane to create truncated shapes - perfect for sectional views")
    print("- Near plane distance is adjustable to control how much gets cut off")
    print("- Enable Sphere Intersections to see exactly where shapes touch the sphere surface")
    print("- Intersection areas are highlighted with bright colors for clear visibility")
    print("- Enable Normal Rays in View menu to see surface normal vectors")
    print("- Normal rays help visualize the tangent plane orientation at each point")
    print("- Enable Intersection Normals to see normals only on shape intersection areas")
    print("- Intersection normals highlight the surface orientation where shapes intersect sphere")
    print("- Enable Truncation Normals to see normals on near plane cut surfaces")
    print("- Truncation normals show the tangent plane orientation on flat cutting planes")
    print("- Enable Ray Tracing Screen in Screen menu for advanced visualization")
    print("- Screen shows ray-traced image of the scene from a virtual camera perspective")
    print("- Try different render modes: Ray Tracing (fast), Ray Marching (accurate), Path Tracing (reflections), PBR (realistic)")
    print("- Position the virtual camera around the scene to get different viewpoints")
    print("- Adjust screen position and rotation to view the ray-traced image from different angles")
    print("- Lower resolution for faster updates, higher resolution for better quality")
    print("- Click on the 3D view to enable keyboard navigation")
    print("- Use arrow keys to fly around the scene in any direction")
    print("- Press I to move forward and O to move backward for complete 3D freedom")
    print("- Combine mouse rotation with keyboard movement for cinematic camera control")
    
    app = Sphere3DApp()
    app.MainLoop()
