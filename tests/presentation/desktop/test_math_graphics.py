#!/usr/bin/env python3
"""
Test script for Mathematical Graphics Menu
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

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import wx
    print("✓ wxPython available")
except ImportError as e:
    print(f"✗ wxPython not available: {e}")
    sys.exit(1)

try:
    import numpy as np
    print("✓ NumPy available")
except ImportError as e:
    print(f"✗ NumPy not available: {e}")
    sys.exit(1)

try:
    from graph_canvas.presentation.desktop.gui.sphere_3d import Sphere3DApp
    print("✓ Sphere3D imports successfully")
    
    # Run the application
    print("Starting Sphere3D application with Mathematical Graphics...")
    print("Look for 'Mathematical Graphics' menu in the menu bar!")
    
    app = Sphere3DApp()
    app.MainLoop()
    
except ImportError as e:
    print(f"✗ Sphere3D import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error running Sphere3D: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
