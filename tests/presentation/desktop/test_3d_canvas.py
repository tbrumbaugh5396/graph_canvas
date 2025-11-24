#!/usr/bin/env python3
"""
Test script for the 3D Canvas
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
    print("Install NumPy with: pip install numpy")
    sys.exit(1)

try:
    from graph_canvas.presentation.desktop.gui.3d_canvas import Canvas3D, Test3DApp
    print("✓ 3D Canvas imports successfully")
    
    # Run the test application
    print("Starting 3D Canvas test application...")
    app = Test3DApp()
    app.MainLoop()
    
except ImportError as e:
    print(f"✗ 3D Canvas import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error running 3D Canvas: {e}")
    sys.exit(1)
