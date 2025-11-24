"""
Zoom invariant tests for GraphCanvas.

Validates that the world point under the cursor remains fixed in screen
coordinates after zoom operations, with and without rotation.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


import unittest
import sys
import os

# Ensure project root is on sys.path for "gui" imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


class ZoomInvariantTest(unittest.TestCase):
    def setUp(self):
        try:
            import wx  # noqa: F401
        except Exception as e:
            self.skipTest(f"wxPython not available: {e}")

        import wx
        # Create headless app
        self.app = wx.App(False)

        # Import here to ensure wx is initialized first
        import graph_canvas.presentation.desktop.gui.graph_canvas as m_graph_canvas

        # Create a hidden frame as parent
        self.frame = wx.Frame(None, title="Test Frame", size=(800, 600))
        self.canvas = m_graph_canvas.GraphCanvas(self.frame, graph=None)
        # Ensure a known size for center math and int rounding behavior
        self.canvas.SetSize((800, 600))
        # Start with a neutral view
        self.canvas.zoom = 1.0
        self.canvas.pan_x = 0.0
        self.canvas.pan_y = 0.0
        self.canvas.world_rotation = 0.0

    def tearDown(self):
        try:
            self.frame.Destroy()
            # Destroy app last
            self.app.Destroy()
        except Exception:
            pass

    def _assert_fixed_point(self, sx: int, sy: int, zoom_factor: float, rotation_deg: float = 0.0):
        # Set rotation and read world point at the given screen position
        self.canvas.set_world_rotation(rotation_deg)
        world_before = self.canvas.screen_to_world(sx, sy)

        # Perform zoom-at-point
        import wx
        self.canvas.zoom_at_point(zoom_factor, wx.Point(sx, sy))

        # The same world point should map back to the original screen point
        sx2, sy2 = self.canvas.world_to_screen(world_before[0], world_before[1])
        dx = abs(sx2 - sx)
        dy = abs(sy2 - sy)
        self.assertLessEqual(dx, 1, f"X deviated by {dx} px (rotation={rotation_deg})")
        self.assertLessEqual(dy, 1, f"Y deviated by {dy} px (rotation={rotation_deg})")

    def test_zoom_invariance_basic(self):
        # Center point
        self._assert_fixed_point(400, 300, 1.2, rotation_deg=0.0)
        self._assert_fixed_point(400, 300, 0.8, rotation_deg=0.0)

        # Off-center point
        self._assert_fixed_point(250, 180, 1.2, rotation_deg=0.0)
        self._assert_fixed_point(650, 420, 0.8, rotation_deg=0.0)

    def test_zoom_invariance_with_rotation(self):
        # Center point with rotation
        self._assert_fixed_point(400, 300, 1.2, rotation_deg=15.0)
        self._assert_fixed_point(400, 300, 0.8, rotation_deg=15.0)

        # Off-center points with rotation
        self._assert_fixed_point(100, 100, 1.5, rotation_deg=30.0)
        self._assert_fixed_point(700, 500, 0.7, rotation_deg=45.0)

    def test_sequential_zoom_steps_stability(self):
        import wx
        sx, sy = 350, 260
        self.canvas.set_world_rotation(20.0)
        world_initial = self.canvas.screen_to_world(sx, sy)

        # Apply several small zoom-in steps
        for _ in range(5):
            self.canvas.zoom_at_point(1.1, wx.Point(sx, sy))
            sx2, sy2 = self.canvas.world_to_screen(world_initial[0], world_initial[1])
            self.assertLessEqual(abs(sx2 - sx), 1)
            self.assertLessEqual(abs(sy2 - sy), 1)

        # Apply several small zoom-out steps
        for _ in range(5):
            self.canvas.zoom_at_point(1.0 / 1.1, wx.Point(sx, sy))
            sx2, sy2 = self.canvas.world_to_screen(world_initial[0], world_initial[1])
            self.assertLessEqual(abs(sx2 - sx), 1)
            self.assertLessEqual(abs(sy2 - sy), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)


