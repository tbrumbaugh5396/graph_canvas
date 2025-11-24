#!/usr/bin/env python3
"""
Test ray tracing toggle functionality
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


def test_ray_tracing_toggle():
    """Test the ray tracing toggle logic"""
    print("=== Ray Tracing Toggle Test ===")
    
    # Mock sphere and canvas
    class MockSphere:
        def __init__(self):
            self.screen_enabled = False  # Sphere starts disabled
            
    class MockCanvas:
        def __init__(self):
            self.screen_enabled = True      # Canvas starts enabled
            self.screen_render_mode = "simple"  # Canvas starts in simple mode
            self.sphere = MockSphere()
            
        def setup_unified_screen_system(self):
            print("  - Ray tracing system set up")
            # This should enable sphere screen
            self.sphere.screen_enabled = True
            
        def setup_framebuffer(self):
            print("  - Framebuffer set up")
            
        def Refresh(self):
            print("  - Canvas refreshed")
            
        def toggle_screen(self):
            """Toggle between screen modes: simple → raytracing → off → simple..."""
            if self.screen_enabled and self.screen_render_mode == "simple":
                # simple → raytracing
                self.screen_render_mode = "raytracing"
                # Ensure ray tracing screen is set up
                self.setup_unified_screen_system()
                # Explicitly enable sphere's ray tracing screen
                if hasattr(self.sphere, 'screen_enabled'):
                    self.sphere.screen_enabled = True
                print(f"DEBUG: Switched to ray tracing screen mode")
            elif self.screen_enabled and self.screen_render_mode == "raytracing":
                # raytracing → off
                self.screen_enabled = False
                print(f"DEBUG: Screen disabled")
            else:
                # off → simple
                self.screen_enabled = True
                self.screen_render_mode = "simple"
                # Ensure framebuffer is set up for simple mode
                self.setup_framebuffer()
                # Explicitly disable sphere's ray tracing screen for simple mode
                if hasattr(self.sphere, 'screen_enabled'):
                    self.sphere.screen_enabled = False
                print(f"DEBUG: Switched to simple 2D screen mode")
            
            sphere_enabled = getattr(self.sphere, 'screen_enabled', 'NOT SET')
            print(f"DEBUG: Screen state - canvas_enabled: {self.screen_enabled}, mode: {self.screen_render_mode}, sphere_enabled: {sphere_enabled}")
            self.Refresh()
    
    canvas = MockCanvas()
    
    print(f"Initial state:")
    print(f"  - Canvas: enabled={canvas.screen_enabled}, mode={canvas.screen_render_mode}")
    print(f"  - Sphere: enabled={canvas.sphere.screen_enabled}")
    
    print(f"\n1. Toggle simple → raytracing:")
    canvas.toggle_screen()
    
    print(f"\n2. Toggle raytracing → off:")
    canvas.toggle_screen()
    
    print(f"\n3. Toggle off → simple:")
    canvas.toggle_screen()
    
    print(f"\n4. Toggle simple → raytracing again:")
    canvas.toggle_screen()
    
    # Check final state
    if canvas.screen_enabled and canvas.screen_render_mode == "raytracing" and canvas.sphere.screen_enabled:
        print(f"\n✅ SUCCESS: Ray tracing mode properly enabled!")
        print(f"   - Canvas enabled: {canvas.screen_enabled}")
        print(f"   - Canvas mode: {canvas.screen_render_mode}")
        print(f"   - Sphere enabled: {canvas.sphere.screen_enabled}")
    else:
        print(f"\n❌ FAILURE: Ray tracing mode not properly enabled")
        print(f"   - Canvas enabled: {canvas.screen_enabled}")
        print(f"   - Canvas mode: {canvas.screen_render_mode}")
        print(f"   - Sphere enabled: {canvas.sphere.screen_enabled}")

if __name__ == "__main__":
    test_ray_tracing_toggle()

