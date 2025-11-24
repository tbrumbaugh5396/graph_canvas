#!/usr/bin/env python3
"""
Debug test script to help trace control point button issues.
Run this instead of main.py to see debug output.
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

print("=" * 50)
print("🔍 DEBUG TEST SCRIPT STARTED")
print("=" * 50)

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🚀 Python version:", sys.version)
print("🚀 Current directory:", os.getcwd())
print("🚀 Python path:", sys.path[:3])  # First 3 entries

print("\n🔍 Attempting to import main.py...")
try:
    import main
    print("✅ main.py imported successfully")
    print("🔍 Starting wxPython application...")
    main.main()
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
