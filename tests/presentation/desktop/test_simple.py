#!/usr/bin/env python3
"""
Simple test for the 3D sphere app
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
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from graph_canvas.presentation.desktop.gui.sphere_3d import Sphere3DApp
    print("Import successful!")
    
    app = Sphere3DApp()
    print("App created successfully!")
    
    # Try to create the frame but don't show it yet
    frame = app.GetTopWindow()
    if frame is None:
        # Create frame manually if needed
        from graph_canvas.presentation.desktop.gui.sphere_3d import Sphere3DFrame
        frame = Sphere3DFrame()
        print("Frame created successfully!")
    
    # Now test the color dialog specifically
    print("Testing cone color dialog...")
    try:
        frame.set_cone_color()
        print("Cone color dialog test completed")
    except Exception as e:
        print(f"Error in cone color dialog: {e}")
    
    print("Testing pyramid color dialog...")
    try:
        frame.set_pyramid_color()
        print("Pyramid color dialog test completed")
    except Exception as e:
        print(f"Error in pyramid color dialog: {e}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
