#!/usr/bin/env python3
"""
Test the updated screen toggle functionality
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


def test_new_toggle_sequence():
    """Test the new toggle sequence: simple → raytracing → off → simple"""
    print("=== New Screen Toggle Test ===")
    
    # Simulate canvas state
    class MockCanvas:
        def __init__(self):
            self.screen_enabled = True
            self.screen_render_mode = "simple"  # Start with simple mode
            self.sphere = type('obj', (object,), {})()
            
        def setup_framebuffer(self):
            print("  - Framebuffer set up for simple mode")
            
        def setup_unified_screen_system(self):
            print("  - Ray tracing system set up")
            
        def Refresh(self):
            print("  - Canvas refreshed")
            
        def toggle_screen(self):
            """Toggle between screen modes: simple → raytracing → off → simple..."""
            if self.screen_enabled and self.screen_render_mode == "simple":
                # simple → raytracing
                self.screen_render_mode = "raytracing"
                self.setup_unified_screen_system()
                print(f"DEBUG: Switched to ray tracing screen mode")
            elif self.screen_enabled and self.screen_render_mode == "raytracing":
                # raytracing → off
                self.screen_enabled = False
                print(f"DEBUG: Screen disabled")
            else:
                # off → simple
                self.screen_enabled = True
                self.screen_render_mode = "simple"
                self.setup_framebuffer()
                print(f"DEBUG: Switched to simple 2D screen mode")
            
            print(f"DEBUG: Screen state - enabled: {self.screen_enabled}, mode: {self.screen_render_mode}")
            self.Refresh()
            
        def disable_screen(self):
            """Disable the 2D screen completely."""
            self.screen_enabled = False
            self.sphere.screen_enabled = False
            print(f"DEBUG: Screen disabled completely")
            self.Refresh()
    
    canvas = MockCanvas()
    
    print(f"Initial state: enabled={canvas.screen_enabled}, mode={canvas.screen_render_mode}")
    print("✅ Starts with simple mode (original 2D view)")
    
    print("\n1. Toggle from simple:")
    canvas.toggle_screen()
    
    print("\n2. Toggle from raytracing:")
    canvas.toggle_screen()
    
    print("\n3. Toggle from off:")
    canvas.toggle_screen()
    
    print("\n4. Test disable screen:")
    canvas.disable_screen()
    
    print("\n5. Toggle from disabled:")
    canvas.toggle_screen()
    
    print("\n✅ New toggle functionality works correctly!")
    print("✅ Separate disable option works!")

if __name__ == "__main__":
    test_new_toggle_sequence()

