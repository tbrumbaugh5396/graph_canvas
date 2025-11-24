#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

print("🎯 SIMPLE TEST: This should show debug is working!")
print("🎯 If you see this, Python3 is working and debug prints work.")

# Test if wx is available
try:
    import wx
    print("✅ wxPython is available")
except ImportError as e:
    print(f"❌ wxPython not available: {e}")

# Test if our main file can be imported
try:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import main
    print("✅ main.py can be imported")
except Exception as e:
    print(f"❌ Cannot import main.py: {e}")
    import traceback
    traceback.print_exc()



