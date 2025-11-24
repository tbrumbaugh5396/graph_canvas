"""
Graph canvas for drawing and interacting with graphs.
"""


import wx
import math
from typing import Optional, List, Tuple, Callable, Set, TYPE_CHECKING
from functools import partial
#if TYPE_CHECKING:

# Handle imports for both module and direct execution
import sys
import os

# Add the parent directory to the path for direct execution
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Try relative imports first (when running as module)
    from . import drawer as m_drawer
    from . import signal as m_signal
    from ..models import graph as m_graph
    from ..models import node as m_node
    from ..models import edge as m_edge
    from ..utils import commands as m_commands
    from .graph_canvas_property_notifier import GraphCanvasPropertyNotifierMixin
except ImportError:
    # Fall back to absolute imports (when running directly)
    import graph_canvas.presentation.desktop.gui.drawer as m_drawer
    import graph_canvas.presentation.desktop.gui.signal as m_signal
    import graph_canvas.presentation.desktop.models.graph as m_graph
    import graph_canvas.presentation.desktop.models.node as m_node
    import graph_canvas.presentation.desktop.models.edge as m_edge
    import graph_canvas.presentation.desktop.utils.commands as m_commands
    from graph_canvas.presentation.desktop.gui.graph_canvas_property_notifier import GraphCanvasPropertyNotifierMixin


class GraphCanvas(wx.Panel, GraphCanvasPropertyNotifierMixin):
    """Canvas for drawing and interacting with graphs."""

    def __init__(self, parent, graph: m_graph.Graph, undo_redo_manager=None):
        super().__init__(parent)

        self.graph = graph
        self.undo_redo_manager = undo_redo_manager

        # Graph restrictions
        self.no_loops = False  # Allow loops by default
        self.no_multigraphs = False  # Allow multiple edges by default
        self.graph_type_restriction = 0  # 0=No Restrictions, 1=Directed only, 2=Undirected only

        # Graph type and background
        self.selected_graph_type = 2  # Default to "Graph"
        self.checkerboard_background = False  # Default to no checkboard

        # Checkboard colors (will be set by main window)
        self.checker_color1 = wx.Colour(240, 240, 240)  # Light gray
        self.checker_color2 = wx.Colour(
            255, 255, 255)  # White (will be set to background color)

        # View state
        self.zoom = 1.0
        # Base factor used for per-step zooming; lower => smoother
        self.zoom_base = 1.12

        # Grid and snapping
        self.grid_style = "grid"  # "none", "grid", "dots"
        self.grid_spacing = 50
        self.snap_to_grid = True  # Default to enabled
        self.dot_size = 2  # Base size for grid dots

        # Background
        from graph_canvas.presentation.desktop.utils.managers.background_manager import BackgroundManager
        self.background_manager = BackgroundManager(self)
        self.min_zoom = 0.01  # max zoom out
        self.max_zoom = 30.0  # max zoom in
        self.pan_x = 0
        self.pan_y = 0

        # Interaction state
        self.tool = "select"  # select, node, edge
        self.dragging = False
        self.dragging_canvas = False
        self.drag_start_pos = None
        self.drag_offset = {}  # node_id -> (dx, dy)
        self.drag_original_positions = {
        }  # node_id -> (original_x, original_y) for undo
        self.edge_start_node = None
        self.edge_start_connection = None  # (edge, point_type) for hyperedge connections
        self.selection_rect = None
        self.selection_start = None

        # Edge endpoint dragging state
        self.dragging_edge_endpoint = False
        self.dragging_edge = None
        self.dragging_endpoint = None  # 'source', 'target', 'from', 'to'

        # Freeform edge state
        self.temp_edge = None  # For temporary edge during creation
        self.temp_path_points = [
        ]  # For storing freeform path points during edge creation

        # Freeform composite segment state
        self.drawing_composite_segment = False
        self.composite_segment_edge = None  # Edge being edited

        # Move tool state
        self.move_sensitivity_x = 1.0
        self.move_sensitivity_y = 1.0
        self.move_inverted = False
        self.dragging_canvas = False
        self.drag_start_pos = None
        self.right_button_down = False  # Track right button state for move world

        # Zoom sensitivity
        self.zoom_sensitivity = 1.0

        # Current mouse position for zoom centering
        self.current_mouse_pos = wx.Point(0, 0)

        # Fixed zoom center tracking (world position that stays fixed during zooming)
        self.zoom_center_world_pos = None  # (x, y) world coordinates of fixed zoom center
        self.zoom_center_screen_pos = None  # (x, y) screen coordinates of fixed zoom center
        self.zoom_center_locked = False  # Whether zoom center is currently locked

        # Zoom event handling state to prevent conflicts
        self.zoom_event_in_progress = False
        self.zoom_event_counter = 0
        self.zoom_active = False  # True while handling a zoom gesture (wheel/magnify)
        self._zoom_active_timer_ms = 150  # slightly longer suppression window to block pan during zoom
        self.zoom_gesture_sign = 0  # +1/-1 during a zoom gesture to debounce direction
        self._zoom_direction_epsilon = 0.02  # deadzone around no zoom (wider to prevent jitter)
        self.pan_suppressed = False  # Flag to suppress all pan modifications during zoom

        # Stable zoom anchor for a gesture
        self._zoom_anchor_screen = None  # (x, y) screen position captured at gesture start
        self._zoom_anchor_world = None  # (x, y) world position corresponding to anchor screen

        # Accumulated zoom in log space for smooth, coalesced application
        self._zoom_accum_ln = 0.0
        self._zoom_apply_scheduled = False
        self._zoom_apply_delay_ms = 12  # small delay to batch multiple wheel ticks

        # Edge scrolling state
        self.edge_scroll_zone = 50  # Pixels from edge where scrolling starts
        self.edge_scroll_speed = 5.0  # Base scroll speed multiplier
        self.last_cursor_pos = None  # For calculating ghost movement

        # Center zoom toggle state
        self.center_zoom_enabled = False  # Whether to zoom to center or mouse position
        self.center_zoom_factor = 2.0  # Zoom multiplier for center zoom

        # World rotation
        self.world_rotation = 0.0  # Rotation angle in degrees

        # Custom default view settings
        self.custom_origin_x = 0  # Custom origin pan_x
        self.custom_origin_y = 0  # Custom origin pan_y
        self.custom_default_rotation = 0.0  # Custom default rotation
        self.custom_default_zoom = 1.0  # Custom default zoom

        # Rotation tool state
        self.dragging_rotation = False
        self.rotation_start_pos = None
        self.rotation_start_angle = 0.0
        self.initial_world_rotation = 0.0
        self.show_rotation_center = False  # Show center dot only during active rotation
        self.rotation_center_color = (255, 0, 0)  # Default to red
        self.rotation_center_pos = None  # Position of rotation center in world coordinates

        # Element rotation state
        self.dragging_element_rotation = False
        self.rotating_element = None  # The node being rotated
        self.element_rotation_start_pos = None
        self.element_rotation_start_angle = 0.0
        self.element_initial_rotation = 0.0
        self.element_pivot_world = None  # Optional custom pivot for element rotation (world coords)
        self.element_initial_offset_world = None  # Node center offset from pivot at start
        self.show_element_rotation_center = False  # Show red dot at element center during rotation

        # Auto-readable nodes
        self.auto_readable_nodes = False

        # Show nested edges toggle
        self.show_nested_edges = True

        # Nested edge indicators
        self.show_nested_edge_indicators = True

        # Grid snapping
        self.grid_snapping_enabled = True  # Enable by default for easier testing
        self.snap_anchor = "center"  # center, upper_left, upper_right, etc.

        # Edge rendering options
        self.edge_rendering_type = "bspline"  # straight, curved, bspline, bezier, cubic_spline, nurbs, polyline
        self.prevent_edge_overlap = False
        self.control_points_enabled = True  # Enable by default to match UI checkbox
        self.relative_control_points = True  # Keep control points relative to nodes when moving

        # Edge anchor settings
        self.edge_anchor_mode = "nearest_face"  # free, center, nearest_face, left_center, etc.
        self.show_anchor_points = False  # Show pink anchor points on nodes

        # Control point interaction state
        self.dragging_control_point = False
        self.dragging_control_point_edge = None
        self.dragging_control_point_index = -1

        # Arrow position control state
        self.dragging_arrow_position = False
        self.dragging_arrow_position_edge = None
        # Selected uberedge segment context
        self.selected_uber_segment_kind = None  # 'edge' or 'node'
        self.selected_uber_segment_edge_id = None
        self.selected_uber_segment_other_edge_id = None
        self.selected_uber_segment_node_id = None

        # Edge endpoint dragging state
        self.dragging_edge_endpoint = False
        self.dragging_edge = None
        self.dragging_endpoint = None  # 'source', 'target', 'from', 'to'

        # B-spline editing state
        self.bspline_editing_mode = False
        self.bspline_editing_edge = None
        self.adding_bspline_control_point = False

        # Containment tool state
        self.dragging_into_container = False
        self.container_target = None  # Target container node
        self.dragging_selection = [
        ]  # Nodes/edges being dragged into container

        # Visual state
        self.grid_style = "grid"  # "none", "grid", or "dots"
        self.grid_spacing = 50.0  # Default spacing between grid lines or dots
        self.show_node_labels = True
        self.show_edge_labels = True
        self.antialias = True
        # Store colors as RGB tuples to avoid wx.Colour issues
        self.background_color = (250, 250, 250)  # Default background
        self.grid_color = (100, 100, 100
                           )  # Darker grid color for better visibility

        print(
            f"DEBUG: Canvas initialized with grid_style='{self.grid_style}', spacing={self.grid_spacing}"
        )
        print(
            f"DEBUG: Grid color: {self.grid_color}, Background: {self.background_color}"
        )

        # Signals
        self.selection_changed = m_signal.Signal()
        self.graph_modified = m_signal.Signal()

        # Set up canvas
        self.SetBackgroundColour(
            wx.Colour(*self.background_color))  # Use RGB tuple
        self.SetDoubleBuffered(True)

        # Bind events
        self.Bind(wx.EVT_PAINT, partial(m_drawer.on_paint, self))
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        self.Bind(wx.EVT_RIGHT_DOWN, self.on_right_down)
        # Also support system context menu events (e.g., ctrl-click, long-press)
        self.Bind(wx.EVT_CONTEXT_MENU, self.on_context_menu)
        self.Bind(wx.EVT_RIGHT_UP, self.on_right_up)
        self.Bind(wx.EVT_MOTION, self.on_motion)
        self.Bind(wx.EVT_MOUSEWHEEL, self.on_mousewheel)
        self._wheel_bound = True

        # Try to bind magnify event - may not be supported on all systems
        try:
            self.Bind(wx.EVT_MAGNIFY, self.on_magnify)
            self._magnify_bound = True
            print("DEBUG: wx.EVT_MAGNIFY binding successful")
        except (AttributeError, TypeError):
            self._magnify_bound = False
            print("DEBUG: wx.EVT_MAGNIFY not supported on this system")

        # Try additional gesture events
        try:
            if hasattr(wx, 'EVT_GESTURE_ZOOM'):
                self.Bind(wx.EVT_GESTURE_ZOOM, self.on_gesture_zoom)
                print("DEBUG: wx.EVT_GESTURE_ZOOM binding successful")
        except (AttributeError, TypeError):
            print("DEBUG: wx.EVT_GESTURE_ZOOM not available")

        try:
            if hasattr(wx, 'EVT_GESTURE_PAN'):
                self.Bind(wx.EVT_GESTURE_PAN, self.on_gesture_pan)
                print("DEBUG: wx.EVT_GESTURE_PAN binding successful")
        except (AttributeError, TypeError):
            print("DEBUG: wx.EVT_GESTURE_PAN not available")

        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.Bind(wx.EVT_LEFT_DCLICK, self.on_double_click)

        # Make sure we can receive keyboard events
        self.SetCanFocus(True)

        # Debug: Show wxPython version and available events (only once)
        print(f"DEBUG: wxPython version: {wx.version()}")
        print(
            f"DEBUG: Zoom controls: Trackpad scroll, +/- keys, Arrow keys for pan"
        )

    def on_mousewheel(self, event):
        """Handle mouse wheel events for zooming."""
        # Enforce exclusivity: respect canvas.zoom_input_mode if present (kept in sync by MVU)
        mode = getattr(self, 'zoom_input_mode', None)
        if mode is None:
            try:
                if hasattr(self, 'main_window') and hasattr(
                        self.main_window, 'mvu_adapter'):
                    mode = getattr(self.main_window.mvu_adapter.model,
                                   'zoom_input_mode', 'wheel')
            except Exception:
                mode = 'wheel'
        if mode == 'touchpad':
            print(
                f"DEBUG: Ignoring mouse wheel zoom because zoom_input_mode={mode}"
            )
            event.Skip()
            return
        # In 'both' mode, allow wheel to proceed
        self.zoom_event_counter += 1
        print(
            f"DEBUG: ===== MOUSE WHEEL EVENT #{self.zoom_event_counter} START ====="
        )

        if self.zoom_event_in_progress:
            print(
                f"DEBUG: Skipping mousewheel #{self.zoom_event_counter} - zoom event already in progress"
            )
            return

        self.zoom_event_in_progress = True
        self.zoom_active = True
        # Suppress any panning during the zoom gesture to avoid boomerang
        self.pan_suppressed = True
        try:
            rotation = event.GetWheelRotation()
            delta = event.GetWheelDelta(
            ) or 120  # Fallback to common notch value

            print(f"DEBUG: rotation: {rotation}, delta: {delta}")
            print(f"DEBUG: zoom_sensitivity: {self.zoom_sensitivity}")

            # Calculate a continuous zoom factor using fractional wheel steps for smoothness
            # One wheel 'notch' corresponds to rotation == delta. Use fractional exponent with sensitivity.
            frac_steps = (rotation / float(delta))
            base_factor = getattr(self, 'zoom_base', 1.12)
            # Use separate sensitivity for zoom-out to avoid oscillation from high-res wheels
            direction = 1.0 if frac_steps >= 0 else -1.0
            smoothing_scale = 0.6  # smaller => smoother
            effective_sensitivity = (self.zoom_sensitivity * smoothing_scale
                                     ) * (0.9 if direction < 0 else 1.0)
            exponent = frac_steps * effective_sensitivity

            print(f"DEBUG: abs(rotation): {abs(rotation)}")
            print(
                f"DEBUG: frac_steps: {frac_steps:.3f}, exponent: {exponent:.3f}, base_factor: {base_factor:.3f}"
            )

            zoom_factor = pow(base_factor, exponent)
            # Guard against numeric jitter: if |exponent| is extremely small, snap to 1.0
            if abs(exponent) < 1e-4:
                zoom_factor = 1.0

            # Debounce zoom direction within a gesture to avoid in/out flicker
            # Determine current sign from exponent
            cur_sign = 1 if exponent > self._zoom_direction_epsilon else (
                -1 if exponent < -self._zoom_direction_epsilon else 0)
            if self.zoom_active:
                if self.zoom_gesture_sign == 0 and cur_sign != 0:
                    self.zoom_gesture_sign = cur_sign
                    print(
                        f"DEBUG: Zoom gesture start sign={self.zoom_gesture_sign}"
                    )
                elif cur_sign != 0 and cur_sign != self.zoom_gesture_sign:
                    # Opposite tiny step? suppress it
                    if abs(exponent) < 0.08:
                        print(
                            "DEBUG: Suppressing opposite tiny wheel step to prevent direction flip"
                        )
                        zoom_factor = 1.0
                        cur_sign = 0
                    else:
                        # Significant reversal: accept and update sign
                        self.zoom_gesture_sign = cur_sign
                        print(
                            f"DEBUG: Zoom gesture sign updated to {self.zoom_gesture_sign}"
                        )
            print(
                f"DEBUG: zoom factor: pow({base_factor:.3f}, {exponent:.3f}) = {zoom_factor:.6f}"
            )

            print(f"DEBUG: final zoom_factor: {zoom_factor}")

            # DEBUG: Mouse button/modifier state during wheel
            try:
                left_down = event.LeftIsDown()
                middle_down = event.MiddleIsDown()
                right_down = event.RightIsDown()
                ctrl = event.ControlDown()
                shift = event.ShiftDown()
                alt = event.AltDown()
                print(
                    f"DEBUG: 🖱️ Mouse state L={left_down} M={middle_down} R={right_down} | Ctrl={ctrl} Shift={shift} Alt={alt}"
                )
            except Exception:
                pass

            # Get mouse position and update current_mouse_pos for accurate zoom centering
            mouse_pos = event.GetPosition()
            self.current_mouse_pos = mouse_pos
            print(
                f"DEBUG: mouse_pos from event: ({mouse_pos.x}, {mouse_pos.y})")
            print(
                f"DEBUG: Updated current_mouse_pos: ({self.current_mouse_pos.x}, {self.current_mouse_pos.y})"
            )

            # Establish stable zoom anchor at gesture start
            if self._zoom_anchor_screen is None:
                self._zoom_anchor_screen = (mouse_pos.x, mouse_pos.y)
                self._zoom_anchor_world = self.screen_to_world(
                    mouse_pos.x, mouse_pos.y)
                print(
                    f"DEBUG: 📌 Captured zoom anchor: screen={self._zoom_anchor_screen}, world=({self._zoom_anchor_world[0]:.3f}, {self._zoom_anchor_world[1]:.3f})"
                )

            # Accumulate zoom in log space and schedule a single apply to avoid jitter/boomerang
            self._zoom_accum_ln += math.log(max(1e-6, zoom_factor))
            print(f"DEBUG: 🧮 Accumulated ln-zoom: {self._zoom_accum_ln:.6f}")
            if not self._zoom_apply_scheduled:
                self._zoom_apply_scheduled = True
                wx.CallLater(self._zoom_apply_delay_ms,
                             self._apply_accumulated_zoom)

        finally:
            self.zoom_event_in_progress = False
            # Keep zoom_active briefly to suppress interleaved pan/gesture events
            wx.CallLater(self._zoom_active_timer_ms, self._clear_zoom_active)
            # Re-enable panning after the zoom gesture completes
            self.pan_suppressed = False
            print(
                f"DEBUG: ===== MOUSE WHEEL EVENT #{self.zoom_event_counter} END ====="
            )
            print()

    def on_magnify(self, event):
        """Handle trackpad magnify events for zooming."""
        self.zoom_event_counter += 1
        print(
            f"DEBUG: ===== MAGNIFY EVENT #{self.zoom_event_counter} START ====="
        )

        # Enforce exclusivity: respect canvas.zoom_input_mode if present (kept in sync by MVU)
        mode = getattr(self, 'zoom_input_mode', None)
        if mode is None:
            try:
                if hasattr(self, 'main_window') and hasattr(
                        self.main_window, 'mvu_adapter'):
                    mode = getattr(self.main_window.mvu_adapter.model,
                                   'zoom_input_mode', 'wheel')
            except Exception:
                mode = 'wheel'
        if mode == 'wheel':
            print(
                f"DEBUG: Ignoring magnify zoom because zoom_input_mode={mode}")
            event.Skip()
            return
        # In 'both' mode, allow magnify to proceed

        if self.zoom_event_in_progress:
            print(
                f"DEBUG: Skipping magnify #{self.zoom_event_counter} - zoom event already in progress"
            )
            return

        self.zoom_event_in_progress = True
        self.zoom_active = True
        try:
            magnification = event.GetMagnification()
            print(f"DEBUG: Magnify event - raw magnification: {magnification}")
            # Suppress panning during magnify zoom gesture
            self.pan_suppressed = True

            # Use same base and sensitivity mapping as wheel to match behavior
            base_factor = getattr(self, 'zoom_base', 1.12)
            # Heuristic: Some platforms emit a small delta (e.g., ±0.02) vs factor (>1 in, <1 out)
            if -0.3 <= magnification <= 0.3:
                # Map tiny magnification deltas to "fractional steps" similar to wheel notches
                # Choose k so that a typical delta (0.05) ≈ 1 step -> exponent ≈ 1 * sensitivity
                k = 12.0
                frac_steps = magnification * k
                direction = 1.0 if frac_steps >= 0 else -1.0
                smoothing_scale = 0.6
                effective_sensitivity = (self.zoom_sensitivity *
                                         smoothing_scale) * (0.9 if direction
                                                             < 0 else 1.0)
                exponent = frac_steps * effective_sensitivity
                zoom_factor = pow(base_factor, exponent)
                mode = "delta"
            else:
                # magnification represents a factor (>=1 in, <1 out). Convert to wheel-equivalent exponent
                if magnification <= 0:
                    zoom_factor = 1.0
                else:
                    # exponent such that base_factor^exponent == magnification
                    try:
                        raw_exp = math.log(magnification) / math.log(
                            base_factor)
                    except Exception:
                        raw_exp = 0.0
                    direction = 1.0 if raw_exp >= 0 else -1.0
                    effective_sensitivity = self.zoom_sensitivity * (
                        0.85 if direction < 0 else 1.0)
                    exponent = raw_exp * effective_sensitivity
                    zoom_factor = pow(base_factor, exponent)
                mode = "factor"

            # Clamp to avoid extreme jumps
            zoom_factor = max(0.01, min(100.0, zoom_factor))
            print(
                f"DEBUG: Magnify -> mode={mode}, computed zoom_factor={zoom_factor:.6f}"
            )

            # Debounce zoom direction within a gesture to avoid in/out flicker
            cur_sign = 1 if zoom_factor > 1.0 + self._zoom_direction_epsilon else (
                -1 if zoom_factor < 1.0 - self._zoom_direction_epsilon else 0)
            if self.zoom_active:
                if self.zoom_gesture_sign == 0 and cur_sign != 0:
                    self.zoom_gesture_sign = cur_sign
                    print(
                        f"DEBUG: Magnify gesture start sign={self.zoom_gesture_sign}"
                    )
                elif cur_sign != 0 and cur_sign != self.zoom_gesture_sign:
                    # Opposite tiny step? suppress it by snapping to 1.0
                    # Use log distance from 1 as magnitude proxy
                    mag_strength = abs(zoom_factor - 1.0)
                    if mag_strength < 0.02:
                        print(
                            "DEBUG: Suppressing opposite tiny magnify step to prevent direction flip"
                        )
                        zoom_factor = 1.0
                        cur_sign = 0
                    else:
                        self.zoom_gesture_sign = cur_sign
                        print(
                            f"DEBUG: Magnify gesture sign updated to {self.zoom_gesture_sign}"
                        )

            # DEBUG: Mouse button/modifier state during magnify
            try:
                left_down = event.LeftIsDown()
                middle_down = event.MiddleIsDown()
                right_down = event.RightIsDown()
                ctrl = event.ControlDown()
                shift = event.ShiftDown()
                alt = event.AltDown()
                print(
                    f"DEBUG: 🖱️ Mouse state L={left_down} M={middle_down} R={right_down} | Ctrl={ctrl} Shift={shift} Alt={alt}"
                )
            except Exception:
                pass

            # Get mouse position from the magnify event and update current_mouse_pos
            mouse_pos = event.GetPosition()
            self.current_mouse_pos = mouse_pos
            print(
                f"DEBUG: 🖱️ Magnify zoom at mouse position ({self.current_mouse_pos.x}, {self.current_mouse_pos.y}) with factor {magnification:.3f}"
            )

            # Establish stable zoom anchor at gesture start
            if self._zoom_anchor_screen is None:
                self._zoom_anchor_screen = (mouse_pos.x, mouse_pos.y)
                self._zoom_anchor_world = self.screen_to_world(
                    mouse_pos.x, mouse_pos.y)
                print(
                    f"DEBUG: 📌 Captured zoom anchor: screen={self._zoom_anchor_screen}, world=({self._zoom_anchor_world[0]:.3f}, {self._zoom_anchor_world[1]:.3f})"
                )

            # Accumulate zoom in log space and schedule a single apply to avoid jitter/boomerang
            self._zoom_accum_ln += math.log(max(1e-6, zoom_factor))
            print(f"DEBUG: 🧮 Accumulated ln-zoom: {self._zoom_accum_ln:.6f}")
            if not self._zoom_apply_scheduled:
                self._zoom_apply_scheduled = True
                wx.CallLater(self._zoom_apply_delay_ms,
                             self._apply_accumulated_zoom)
        finally:
            self.zoom_event_in_progress = False
            # Keep zoom_active briefly to suppress interleaved pan/gesture events
            wx.CallLater(self._zoom_active_timer_ms, self._clear_zoom_active)

        # Do not propagate magnify; we handled zoom here to avoid duplicate zoom from parent bindings
        return

    def unlock_zoom_center(self):
        """Deprecated: no-op, always zoom at current cursor."""
        return

    def on_mouse_motion(self, event):
        """Handle mouse motion events."""
        # No center locking; nothing to do here

        # Call the original mouse motion handler if it exists
        if hasattr(super(), 'on_mouse_motion'):
            super().on_mouse_motion(event)
        else:
            event.Skip()

    def on_gesture_zoom(self, event):
        """Handle gesture zoom events."""
        if self.zoom_event_in_progress:
            print(
                "DEBUG: Skipping gesture zoom - zoom event already in progress"
            )
            event.Skip()
            return

        if hasattr(event, 'GetZoomFactor'):
            self.zoom_event_in_progress = True
            try:
                zoom_factor = event.GetZoomFactor()
                print(f"DEBUG: Gesture zoom - factor: {zoom_factor}")
                # Suppress panning during gesture zoom
                self.pan_suppressed = True

                # Use current_mouse_pos for consistent zoom behavior
                print(
                    f"DEBUG: 🖱️ Gesture zoom at current_mouse_pos ({self.current_mouse_pos.x}, {self.current_mouse_pos.y}) with factor {zoom_factor:.3f}"
                )

                # Use the unified zoom_at_point method with cursor position
                self.zoom_at_point(zoom_factor, self.current_mouse_pos)
            finally:
                self.zoom_event_in_progress = False

        event.Skip()

    def on_gesture_pan(self, event):
        """Handle gesture pan events."""

        if hasattr(event, 'GetDelta'):
            # Ignore gesture pan while a zoom event is active or suppressed
            if getattr(self, 'zoom_event_in_progress', False) or getattr(
                    self, 'zoom_active', False) or getattr(
                        self, 'pan_suppressed', False):
                print("DEBUG: Ignoring gesture pan during active zoom event")
                event.Skip()
                return
            delta = event.GetDelta()
            print(f"DEBUG: Gesture pan - delta: {delta}")

            # Apply pan
            self.pan_x += delta.x
            self.pan_y += delta.y

            self.Refresh()
        event.Skip()

    def on_key_down(self, event):
        """Handle keyboard events for navigation."""

        key_code = event.GetKeyCode()
        pan_speed = 50  # pixels per key press

        # Arrow keys and WASD for navigation
        if (key_code == wx.WXK_LEFT
                or key_code == ord('A')) and not self.pan_suppressed:
            self.pan_x += pan_speed
            self.Refresh()
        elif (key_code == wx.WXK_RIGHT
              or key_code == ord('D')) and not self.pan_suppressed:
            self.pan_x -= pan_speed
            self.Refresh()
        elif (key_code == wx.WXK_UP
              or key_code == ord('W')) and not self.pan_suppressed:
            self.pan_y += pan_speed
            self.Refresh()
        elif (key_code == wx.WXK_DOWN
              or key_code == ord('S')) and not self.pan_suppressed:
            self.pan_y -= pan_speed
            self.Refresh()
        # Zoom with + and - keys
        elif key_code == ord('+') or key_code == ord('='):
            if self.center_zoom_enabled:
                # Use center-based zooming
                self.zoom_to_world_center_smooth(zoom_in=True)
                print(f"DEBUG: 🔍 Keyboard center zoom in")
            else:
                # Use cursor-based zooming (original behavior)
                self.zoom_at_point(1.0 + (0.2 * self.zoom_sensitivity),
                                   self.current_mouse_pos)
                print(
                    f"DEBUG: 🖱️ Keyboard zoom in at mouse position ({self.current_mouse_pos.x}, {self.current_mouse_pos.y})"
                )
        elif key_code == ord('-'):
            if self.center_zoom_enabled:
                # Use center-based zooming
                self.zoom_to_world_center_smooth(zoom_in=False)
                print(f"DEBUG: 🔍 Keyboard center zoom out")
            else:
                # Use cursor-based zooming (original behavior)
                self.zoom_at_point(1.0 - (0.2 * self.zoom_sensitivity),
                                   self.current_mouse_pos)
                print(
                    f"DEBUG: 🖱️ Keyboard zoom out at mouse position ({self.current_mouse_pos.x}, {self.current_mouse_pos.y})"
                )
        # Reset zoom and pan with R key
        elif key_code == ord('R'):
            self.zoom = 1.0
            self.pan_x = 0
            self.pan_y = 0
            print("DEBUG: Reset zoom and pan")
            self.Refresh()
        else:
            event.Skip()

    def set_graph(self, graph: m_graph.Graph, emit_signal: bool = True):
        """Set a new graph for the canvas.

        Args:
            graph: The new graph to display
            emit_signal: Whether to emit the graph_modified signal (default: True)
        """
        self.graph = graph

        # Clear any selection or interaction state
        self.edge_start_node = None
        self.selection_rect = None
        self.selection_start = None
        self.dragging = False
        self.dragging_canvas = False

        # Emit signal only if requested (to prevent recursion)
        if emit_signal:
            self.graph_modified.emit()

        self.Refresh()

    def set_tool(self, tool: str):
        """Set the current tool."""

        self.tool = tool
        self.edge_start_node = None
        self.edge_start_connection = None
        # Re-sync MVU model rotation on tool change
        try:
            mw = self.GetParent().GetParent()
            if hasattr(mw, 'mvu_adapter'):
                from mvc_mvu.messages import make_message
                import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
                # Always push current canvas rotation to model on tool switch to avoid stale resets
                mw.mvu_adapter.dispatch(
                    make_message(m_main_mvu.Msg.SET_ROTATION,
                                 angle=self.world_rotation))
        except Exception:
            pass

    def set_move_sensitivity(self, x_sensitivity: float, y_sensitivity: float,
                             inverted: bool):
        """Set move tool sensitivity and inversion settings."""

        self.move_sensitivity_x = x_sensitivity
        self.move_sensitivity_y = y_sensitivity
        self.move_inverted = inverted
        print(
            f"DEBUG: Move sensitivity set to X:{x_sensitivity}, Y:{y_sensitivity}, Inverted:{inverted}"
        )

    def set_zoom_sensitivity(self, zoom_sensitivity: float):
        """Set zoom sensitivity."""

        self.zoom_sensitivity = zoom_sensitivity
        print(f"DEBUG: Zoom sensitivity set to {zoom_sensitivity}")

    def _apply_accumulated_zoom(self):
        """Apply accumulated ln-zoom once per event loop cycle to avoid jitter/boomerang."""
        try:
            if self._zoom_anchor_screen is None or abs(
                    self._zoom_accum_ln) < 1e-6:
                print("DEBUG: _apply_accumulated_zoom: nothing to apply")
                return
            # Compute single zoom factor from accumulated ln, clamp extreme values
            zoom_factor = math.exp(self._zoom_accum_ln)
            zoom_factor = max(0.01, min(100.0, zoom_factor))
            anchor_point = wx.Point(self._zoom_anchor_screen[0],
                                    self._zoom_anchor_screen[1])
            print(
                f"DEBUG: 🚀 Applying accumulated zoom: ln={self._zoom_accum_ln:.6f}, factor={zoom_factor:.6f} at anchor=({anchor_point.x},{anchor_point.y})"
            )
            # Reset accumulator before applying to coalesce bursts properly
            self._zoom_accum_ln = 0.0
            self._zoom_apply_scheduled = False
            self.zoom_at_point(zoom_factor, anchor_point)
            # Re-sync MVU model rotation after zoom apply
            try:
                mw = self.GetParent().GetParent()
                if hasattr(mw, 'mvu_adapter'):
                    from mvc_mvu.messages import make_message
                    import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
                    mw.mvu_adapter.dispatch(
                        make_message(m_main_mvu.Msg.SET_ROTATION,
                                     angle=self.world_rotation))
            except Exception:
                pass
        except Exception as e:
            print(f"DEBUG: _apply_accumulated_zoom error: {e}")
            self._zoom_accum_ln = 0.0
            self._zoom_apply_scheduled = False

    def zoom_at_point(self, zoom_factor: float, point: wx.Point):
        """Zoom in/out while keeping the specified point fixed in world space."""

        print(f"DEBUG: ===== ZOOM AT POINT START =====")
        print(f"DEBUG: zoom_factor: {zoom_factor}")
        print(f"DEBUG: point: ({point.x}, {point.y})")
        print(f"DEBUG: current zoom: {self.zoom}")
        print(f"DEBUG: current pan: ({self.pan_x}, {self.pan_y})")
        print(f"DEBUG: world_rotation: {self.world_rotation}")

        # Suppress all pan modifications during zoom
        self.pan_suppressed = True

        if not point:
            # If no point provided, zoom at center
            size = self.GetSize()
            point = wx.Point(size.width // 2, size.height // 2)
            print(
                f"DEBUG: No point provided, using center: ({point.x}, {point.y})"
            )

        # INVARIANT CHECK: Screen -> World -> Screen transformation before zoom
        print(f"DEBUG: ===== INVARIANT CHECK: BEFORE ZOOM =====")
        # Always use provided point (mouse or center) for anchor
        world_point = self.screen_to_world(point.x, point.y)
        print(
            f"DEBUG: 1. screen_to_world({point.x}, {point.y}) = ({world_point[0]:.3f}, {world_point[1]:.3f})"
        )

        # Verify the reverse transformation works before zoom
        check_screen_x, check_screen_y = self.world_to_screen(
            world_point[0], world_point[1])
        pre_zoom_error_x = abs(point.x - check_screen_x)
        pre_zoom_error_y = abs(point.y - check_screen_y)
        print(
            f"DEBUG: 2. world_to_screen({world_point[0]:.3f}, {world_point[1]:.3f}) = ({check_screen_x}, {check_screen_y})"
        )
        print(
            f"DEBUG: 3. Pre-zoom round-trip error: ({pre_zoom_error_x}, {pre_zoom_error_y})"
        )

        if pre_zoom_error_x > 1 or pre_zoom_error_y > 1:
            print(
                f"DEBUG: ⚠️  WARNING: Pre-zoom coordinate transformation has errors!"
            )
        else:
            print(f"DEBUG: ✅ Pre-zoom coordinate transformation is accurate")

        # Early return if zoom factor is 1.0 (no change requested)
        if abs(zoom_factor - 1.0) < 0.001:
            print(
                "DEBUG: Zoom factor is 1.0 - no zoom change requested, returning early"
            )
            return

        # Calculate and apply new zoom level with limits
        old_zoom = self.zoom
        new_zoom = max(self.min_zoom, min(self.max_zoom,
                                          old_zoom * zoom_factor))
        print(f"DEBUG: zoom change: {old_zoom:.3f} -> {new_zoom:.3f}")

        # If zoom would be out of bounds, don't change anything
        if new_zoom == old_zoom:
            print("DEBUG: Zoom unchanged (hit limits)")
            return

        # Apply new zoom
        self.zoom = new_zoom
        print(f"DEBUG: Applied new zoom: {self.zoom}")

        # CORRECT APPROACH: Keep the chosen world point fixed
        # Use the world position we already calculated before zoom
        world_x, world_y = world_point[0], world_point[1]

        print(
            f"DEBUG: Mouse world position (must stay fixed): ({world_x:.3f}, {world_y:.3f})"
        )

        # New mouse-centered zoom with center+offset pipeline
        size = self.GetSize()
        cx = size.width / 2.0
        cy = size.height / 2.0
        # Compute mouse delta from canvas center in screen space
        dx = point.x - cx
        dy = point.y - cy
        # Compute S'/S
        ratio = new_zoom / old_zoom if old_zoom != 0 else 1.0
        # Update pan so that the anchor remains fixed visually under rotation too
        # Derivation: screen = center + pan + R(S*world). Keep screen constant when S->S':
        # pan' = pan + R(S*world) - R(S'*world). Using dx,dy = pan + R(S*world):
        # pan' = r*pan + (1 - r)*(dx,dy), where r = S'/S
        new_pan_x = self.pan_x * ratio + (1.0 - ratio) * dx
        new_pan_y = self.pan_y * ratio + (1.0 - ratio) * dy

        print(
            f"DEBUG: Required new pan to keep point fixed: ({new_pan_x:.3f}, {new_pan_y:.3f})"
        )

        # EXTRA DEBUG: After applying zoom and proposed pan, verify forward transform matches anchor
        pre_sx = world_x * self.zoom
        pre_sy = world_y * self.zoom
        if self.world_rotation != 0.0:
            theta_chk = math.radians(self.world_rotation)
            cos_chk = math.cos(theta_chk)
            sin_chk = math.sin(theta_chk)
            rx_chk = pre_sx * cos_chk - pre_sy * sin_chk
            ry_chk = pre_sx * sin_chk + pre_sy * cos_chk
        else:
            rx_chk, ry_chk = pre_sx, pre_sy
        precheck_x = rx_chk + cx + new_pan_x
        precheck_y = ry_chk + cy + new_pan_y
        anchor_err_x = point.x - precheck_x
        anchor_err_y = point.y - precheck_y
        print(
            f"DEBUG: 🔁 Forward-check: world_to_screen(world_point) = ({precheck_x:.3f}, {precheck_y:.3f}), anchor=({point.x}, {point.y}), err=({anchor_err_x:.3f}, {anchor_err_y:.3f})"
        )

        # If zoom center is locked, ensure crosshair is fixed at screen center
        if hasattr(self, 'zoom_center_locked') and self.zoom_center_locked:
            size = self.GetSize()
            center_x = int(size.width / 2)
            center_y = int(size.height / 2)
            self.zoom_center_world_pos = (world_x, world_y)
            self.zoom_center_screen_pos = (center_x, center_y)

        # Set pan directly to avoid incremental accumulation error
        old_pan_x, old_pan_y = self.pan_x, self.pan_y
        self.pan_x = new_pan_x
        self.pan_y = new_pan_y
        print(
            f"DEBUG: pan set: ({old_pan_x:.3f}, {old_pan_y:.3f}) -> ({self.pan_x:.3f}, {self.pan_y:.3f})"
        )

        # EXTRA DEBUG: After setting pan, confirm with world_to_screen function
        final_screen_x, final_screen_y = self.world_to_screen(world_x, world_y)
        final_err_x = point.x - final_screen_x
        final_err_y = point.y - final_screen_y
        print(
            f"DEBUG: 🔎 world_to_screen(post): ({final_screen_x}, {final_screen_y}) vs anchor=({point.x}, {point.y}) -> err=({final_err_x}, {final_err_y})"
        )

        # No post-zoom correction: the direct pan computation above should exactly
        # keep the world point fixed. Removing the incremental correction avoids
        # oscillations/boomerang from overcompensation between successive events.

        # DEBUG: Check if the point is still at the same world position after zoom
        world_after = self.screen_to_world(point.x, point.y)
        world_error_x = abs(world_x - world_after[0])
        world_error_y = abs(world_y - world_after[1])
        print(
            f"DEBUG: World position after zoom: ({world_after[0]:.3f}, {world_after[1]:.3f})"
        )
        print(
            f"DEBUG: World position error: ({world_error_x:.3f}, {world_error_y:.3f})"
        )

        if world_error_x > 0.1 or world_error_y > 0.1:
            print(f"DEBUG: ⚠️  WARNING: Zoom is not keeping the point fixed!")
            print(f"DEBUG: 🔍 FIXED POINT VERIFICATION FAILED!")
            print(f"DEBUG: 🔍 Screen position: ({point.x}, {point.y})")
            print(f"DEBUG: 🔍 World before: ({world_x:.3f}, {world_y:.3f})")
            print(
                f"DEBUG: 🔍 World after: ({world_after[0]:.3f}, {world_after[1]:.3f})"
            )
            print(
                f"DEBUG: 🔍 Error: ({world_error_x:.3f}, {world_error_y:.3f})")
        else:
            print(f"DEBUG: ✅ Zoom is keeping the point fixed")
            print(f"DEBUG: 🔍 FIXED POINT VERIFICATION PASSED!")

        # DEBUG: Check crosshair position if locked
        if hasattr(self, 'zoom_center_locked') and self.zoom_center_locked:
            print(f"DEBUG: ===== CROSSHAIR POSITION CHECK =====")
            print(f"DEBUG: Zoom center locked: {self.zoom_center_locked}")
            print(
                f"DEBUG: Zoom center world pos: {self.zoom_center_world_pos}")
            print(
                f"DEBUG: Zoom center screen pos: {self.zoom_center_screen_pos}"
            )

            # Check if the crosshair world position is the same as our fixed point
            if self.zoom_center_world_pos:
                crosshair_world_x, crosshair_world_y = self.zoom_center_world_pos
                crosshair_error_x = abs(crosshair_world_x - world_x)
                crosshair_error_y = abs(crosshair_world_y - world_y)
                print(
                    f"DEBUG: Crosshair world position: ({crosshair_world_x:.3f}, {crosshair_world_y:.3f})"
                )
                print(
                    f"DEBUG: Fixed point world position: ({world_x:.3f}, {world_y:.3f})"
                )
                print(
                    f"DEBUG: Crosshair vs fixed point error: ({crosshair_error_x:.3f}, {crosshair_error_y:.3f})"
                )

                if crosshair_error_x > 0.1 or crosshair_error_y > 0.1:
                    print(
                        f"DEBUG: ⚠️  WARNING: Crosshair world position doesn't match fixed point!"
                    )
                else:
                    print(
                        f"DEBUG: ✅ Crosshair world position matches fixed point!"
                    )

            # Check if the crosshair screen position is the same as our point
            if self.zoom_center_screen_pos:
                crosshair_screen_x, crosshair_screen_y = self.zoom_center_screen_pos
                screen_error_x = abs(crosshair_screen_x - point.x)
                screen_error_y = abs(crosshair_screen_y - point.y)
                print(
                    f"DEBUG: Crosshair screen position: ({crosshair_screen_x}, {crosshair_screen_y})"
                )
                print(
                    f"DEBUG: Zoom point screen position: ({point.x}, {point.y})"
                )
                print(
                    f"DEBUG: Crosshair vs zoom point screen error: ({screen_error_x}, {screen_error_y})"
                )

                if screen_error_x > 1 or screen_error_y > 1:
                    print(
                        f"DEBUG: ⚠️  WARNING: Crosshair screen position doesn't match zoom point!"
                    )
                else:
                    print(
                        f"DEBUG: ✅ Crosshair screen position matches zoom point!"
                    )

        # Update canvas information display
        if hasattr(self, 'main_window') and hasattr(self.main_window,
                                                    'update_canvas_info'):
            self.main_window.update_canvas_info()

        # Force immediate refresh to show zoom effect
        self.Refresh()

        # INVARIANT CHECK: Complete zoom transformation verification
        print(f"DEBUG: ===== INVARIANT CHECK: AFTER ZOOM =====")
        print(f"DEBUG: Original screen point: ({point.x}, {point.y})")
        print(
            f"DEBUG: World point (should be unchanged): ({world_point[0]:.3f}, {world_point[1]:.3f})"
        )
        print(f"DEBUG: Old zoom: {old_zoom:.3f}, New zoom: {self.zoom:.3f}")
        print(
            f"DEBUG: Old pan: ({old_pan_x:.3f}, {old_pan_y:.3f}), New pan: ({self.pan_x:.3f}, {self.pan_y:.3f})"
        )

        # The world point should now map back to the original screen position
        final_screen_x, final_screen_y = self.world_to_screen(
            world_point[0], world_point[1])
        final_error_x = abs(point.x - final_screen_x)
        final_error_y = abs(point.y - final_screen_y)

        print(
            f"DEBUG: world_to_screen({world_point[0]:.3f}, {world_point[1]:.3f}) = ({final_screen_x}, {final_screen_y})"
        )
        print(
            f"DEBUG: Final transformation error: ({final_error_x}, {final_error_y})"
        )

        # Also check against current_mouse_pos for comparison
        mouse_error_x = abs(self.current_mouse_pos.x - final_screen_x)
        mouse_error_y = abs(self.current_mouse_pos.y - final_screen_y)
        print(
            f"DEBUG: Error vs current_mouse_pos ({self.current_mouse_pos.x}, {self.current_mouse_pos.y}): ({mouse_error_x}, {mouse_error_y})"
        )

        if final_error_x > 1 or final_error_y > 1:
            print(
                f"DEBUG: ⚠️  INVARIANT VIOLATION: World point doesn't map back to original screen position!"
            )
            print(f"DEBUG: This is the source of the boomerang effect!")
        else:
            print(
                f"DEBUG: ✅ INVARIANT SATISFIED: Zoom-at-point working correctly"
            )

        print(f"DEBUG: ===== ZOOM AT POINT END =====")

        # Re-enable pan modifications after zoom
        self.pan_suppressed = False
        # Stabilize the stored current_mouse_pos to the anchor point for this zoom
        # so subsequent computations use the invariant anchor during gesture bursts
        self.current_mouse_pos = wx.Point(int(point.x), int(point.y))

        self.Refresh()

    def zoom_in_at_mouse(self):
        """Zoom in at current mouse position."""

        base = getattr(self, 'zoom_base', 1.12)
        self.zoom_at_point(base, self.current_mouse_pos)

    def zoom_out_at_mouse(self):
        """Zoom out at current mouse position."""

        base = getattr(self, 'zoom_base', 1.12)
        self.zoom_at_point(1.0 / base, self.current_mouse_pos)

    def reset_view(self):
        """Reset view to the saved default state (saved center, rotation, and zoom)."""

        # Use saved default zoom if set, otherwise use 1.0
        self.zoom = getattr(self, 'custom_default_zoom', 1.0)

        # Use saved origin if set, otherwise use (0,0)
        self.pan_x = getattr(self, 'custom_origin_x', 0.0)
        self.pan_y = getattr(self, 'custom_origin_y', 0.0)

        # Use saved default rotation if set, otherwise use 0.0
        self.world_rotation = getattr(self, 'custom_default_rotation', 0.0)

        print(
            f"DEBUG: View reset to saved defaults: zoom={self.zoom}, pan=({self.pan_x}, {self.pan_y}), rotation={self.world_rotation}°"
        )
        self.Refresh()

    def force_grid_visible(self):
        """Force grid to be visible with high contrast for debugging."""
        print("DEBUG: Forcing grid to be visible")
        self.grid_style = "grid"
        self.grid_spacing = 50.0
        self.grid_color = (0, 0, 0)  # Black grid for maximum contrast
        self.background_color = (255, 255, 255)  # White background
        print(
            f"DEBUG: Grid forced - style: {self.grid_style}, spacing: {self.grid_spacing}"
        )
        print(
            f"DEBUG: Colors - grid: {self.grid_color}, background: {self.background_color}"
        )
        self.Refresh()

    def create_test_background(self):
        """Create a test background image for debugging."""
        print("DEBUG: Creating test background image")

        # Create a simple test image programmatically
        test_image = wx.Image(200, 200)
        test_image.SetRGB(wx.Rect(0, 0, 200, 200), 100, 150, 200)  # Light blue
        test_image.SetRGB(wx.Rect(50, 50, 100, 100), 200, 100,
                          100)  # Light red square

        # Create bitmap from image
        test_bitmap = wx.Bitmap(test_image)

        # Add a background layer
        layer = self.background_manager.add_layer("Test Background")
        layer.bitmap = test_bitmap
        from graph_canvas.presentation.desktop.models.background_layer import BackgroundMode
        layer.mode = BackgroundMode.POSITIONED  # Use positioned mode for world coordinates
        layer.visible = True
        layer.stretch = False
        layer.fixed_position = False  # Let it move with world

        # Add a position for the image at world center
        layer.add_position(0, 0, 1.0, 0.0, 0.5)  # Semi-transparent

        print("DEBUG: Test background created and added")
        self.Refresh()

    def set_custom_origin(self):
        """Set the current center of screen as the custom origin."""

        # Current pan represents the offset from world origin to screen center
        # Store current pan as the new custom origin
        self.custom_origin_x = self.pan_x
        self.custom_origin_y = self.pan_y
        print(
            f"DEBUG: Custom origin set to pan=({self.custom_origin_x}, {self.custom_origin_y})"
        )

    def set_custom_default_rotation(self):
        """Set the current rotation as the custom default rotation."""

        self.custom_default_rotation = self.world_rotation
        print(
            f"DEBUG: Custom default rotation set to {self.custom_default_rotation}°"
        )

    def set_custom_default_zoom(self):
        """Set the current zoom level as the custom default zoom."""

        self.custom_default_zoom = self.zoom
        print(f"DEBUG: Custom default zoom set to {self.custom_default_zoom}x")

    def zoom_to_fit(self, padding=50):
        """Zoom and pan to fit all nodes and edges in view with padding."""

        all_nodes = self.graph.get_all_nodes()
        if not all_nodes:
            print("DEBUG: No nodes to fit, resetting view")
            self.reset_view()
            return

        # Calculate bounding box of all nodes with their full dimensions
        min_x = float('inf')
        max_x = float('-inf')
        min_y = float('inf')
        max_y = float('-inf')

        for node in all_nodes:
            # Consider node dimensions and rotation
            corners = self._get_node_corners(node)
            for x, y in corners:
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)

        # Also consider edges for a more complete bounding box
        all_edges = self.graph.get_all_edges()
        for edge in all_edges:
            source_node = self.graph.get_node(edge.source_id)
            target_node = self.graph.get_node(edge.target_id)
            if source_node and target_node:
                # Include edge control points in bounding box
                points = self._get_edge_points(edge, source_node, target_node)
                for x, y in points:
                    min_x = min(min_x, x)
                    max_x = max(max_x, x)
                    min_y = min(min_y, y)
                    max_y = max(max_y, y)

        if min_x == float('inf') or max_x == float('-inf'):
            print("DEBUG: No valid bounds found, resetting view")
            self.reset_view()
            return

        # Calculate content dimensions
        content_width = max_x - min_x
        content_height = max_y - min_y

        # Calculate dynamic padding based on content size
        dynamic_padding = max(content_width,
                              content_height) * 0.1  # 10% of content size
        total_padding = max(padding, dynamic_padding)

        # Get canvas dimensions
        canvas_size = self.GetSize()
        available_width = canvas_size.width - 2 * total_padding
        available_height = canvas_size.height - 2 * total_padding

        if content_width <= 0 or content_height <= 0:
            print("DEBUG: Content has no dimensions, resetting view")
            self.reset_view()
            return

        # Calculate zoom to fit both width and height
        zoom_x = available_width / content_width
        zoom_y = available_height / content_height
        new_zoom = min(zoom_x, zoom_y)

        # Apply zoom limits
        new_zoom = max(self.min_zoom, min(new_zoom, self.max_zoom))

        # Calculate center of content
        content_center_x = (min_x + max_x) / 2
        content_center_y = (min_y + max_y) / 2

        # Calculate pan to center content
        canvas_center_x = canvas_size.width / 2
        canvas_center_y = canvas_size.height / 2

        new_pan_x = canvas_center_x - content_center_x * new_zoom
        new_pan_y = canvas_center_y - content_center_y * new_zoom

        # Apply new values
        self.zoom = new_zoom
        self.pan_x = new_pan_x
        self.pan_y = new_pan_y

        print(
            f"DEBUG: Zoom to fit - Content bounds: ({min_x:.1f}, {min_y:.1f}) to ({max_x:.1f}, {max_y:.1f})"
        )
        print(
            f"DEBUG: Zoom to fit - Zoom: {new_zoom:.2f}, Pan: ({new_pan_x:.1f}, {new_pan_y:.1f})"
        )

        self.Refresh()

    def _get_node_corners(self, node) -> List[Tuple[float, float]]:
        """Get the corners of a node considering its rotation."""
        # Calculate node corners
        half_width = node.width / 2
        half_height = node.height / 2
        corners = [(node.x - half_width, node.y - half_height),
                   (node.x + half_width, node.y - half_height),
                   (node.x + half_width, node.y + half_height),
                   (node.x - half_width, node.y + half_height)]

        # Apply node rotation if any
        if hasattr(node, 'rotation') and node.rotation != 0:
            rotation_rad = math.radians(node.rotation)
            cos_rot = math.cos(rotation_rad)
            sin_rot = math.sin(rotation_rad)
            rotated_corners = []
            for x, y in corners:
                dx = x - node.x
                dy = y - node.y
                rotated_x = node.x + dx * cos_rot - dy * sin_rot
                rotated_y = node.y + dx * sin_rot + dy * cos_rot
                rotated_corners.append((rotated_x, rotated_y))
            return rotated_corners
        return corners

    def _get_edge_points(self, edge, source_node,
                         target_node) -> List[Tuple[float, float]]:
        """Get all points that define an edge's path."""
        points = []

        # Add source and target points
        points.append((source_node.x, source_node.y))
        points.append((target_node.x, target_node.y))

        # Add control points if any
        if hasattr(edge, 'control_points') and edge.control_points:
            for cp in edge.control_points:
                points.append((cp[0], cp[1]))

        # Add any additional path points
        if hasattr(edge, 'path_points') and edge.path_points:
            for pp in edge.path_points:
                points.append((pp[0], pp[1]))

        return points

    def set_world_rotation(self, angle: float):
        """Set world rotation angle in degrees."""

        self.world_rotation = angle % 360
        print(f"DEBUG: World rotation set to {self.world_rotation}°")
        self.Refresh()

    def world_to_screen(self, x: float, y: float) -> Tuple[int, int]:
        """Convert world coordinates to screen coordinates (Translate(center+offset) -> Scale -> Rotate)."""

        size = self.GetSize()
        cx = size.width / 2.0
        cy = size.height / 2.0

        # Apply Scale then Rotate around origin, then translate by center+offset in screen space
        sx = x
        sy = y
        # Scale
        sx *= self.zoom
        sy *= self.zoom
        # Rotate
        if self.world_rotation != 0.0:
            theta = math.radians(self.world_rotation)
            cos_t = math.cos(theta)
            sin_t = math.sin(theta)
            rx = sx * cos_t - sy * sin_t
            ry = sx * sin_t + sy * cos_t
            sx, sy = rx, ry
        # Translate by center + offset
        sx += cx + self.pan_x
        sy += cy + self.pan_y
        return (int(sx), int(sy))

    def transform_direction_world_to_screen(self, dx: float,
                                            dy: float) -> Tuple[float, float]:
        """Transform a direction vector from world space to screen space, accounting for zoom and rotation."""

        # Apply zoom to direction vector (directions scale with zoom)
        screen_dx = dx * self.zoom
        screen_dy = dy * self.zoom

        # Apply world rotation to direction vector if any
        if self.world_rotation != 0.0:
            # Convert rotation to radians
            rotation_rad = math.radians(self.world_rotation)
            cos_angle = math.cos(rotation_rad)
            sin_angle = math.sin(rotation_rad)

            # Apply rotation to direction vector
            rotated_dx = screen_dx * cos_angle - screen_dy * sin_angle
            rotated_dy = screen_dx * sin_angle + screen_dy * cos_angle

            screen_dx = rotated_dx
            screen_dy = rotated_dy

        return (screen_dx, screen_dy)

    def screen_to_world(self, x: int, y: int) -> Tuple[float, float]:
        """Convert screen coordinates to world coordinates (inverse of Translate->Scale->Rotate)."""

        size = self.GetSize()
        cx = size.width / 2.0
        cy = size.height / 2.0

        # Inverse translate by center + offset
        sx = x - (cx + self.pan_x)
        sy = y - (cy + self.pan_y)
        # Inverse rotate
        if self.world_rotation != 0.0:
            theta = -math.radians(self.world_rotation)
            cos_t = math.cos(theta)
            sin_t = math.sin(theta)
            rx = sx * cos_t - sy * sin_t
            ry = sx * sin_t + sy * cos_t
            sx, sy = rx, ry
        # Inverse scale
        if self.zoom != 0:
            sx /= self.zoom
            sy /= self.zoom
        return (sx, sy)

    def _screen_delta_to_pan_delta(self, dx: float,
                                   dy: float) -> Tuple[float, float]:
        """Map screen drag delta to pan delta under current view pipeline.

        With Translate(center+offset) -> Scale -> Rotate, offset is in screen space
        and applied before scale/rotate. So pan delta equals the screen delta directly.
        """
        return dx, dy

    def _clear_zoom_active(self):
        """Clear the transient zoom_active flag after a zoom gesture completes."""
        self.zoom_active = False
        self.zoom_gesture_sign = 0
        self.pan_suppressed = False
        self._zoom_anchor_screen = None
        self._zoom_anchor_world = None
        self._zoom_accum_ln = 0.0
        self._zoom_apply_scheduled = False

    def screen_to_world_delta(self, screen_dx: int,
                              screen_dy: int) -> Tuple[float, float]:
        """Convert screen coordinate deltas to world coordinate deltas."""

        # Apply inverse zoom
        world_dx = screen_dx / self.zoom
        world_dy = screen_dy / self.zoom

        # Apply inverse rotation if needed
        if self.world_rotation != 0.0:
            rotation_rad = -math.radians(
                self.world_rotation)  # Negative for inverse
            cos_angle = math.cos(rotation_rad)
            sin_angle = math.sin(rotation_rad)

            temp_dx = world_dx
            temp_dy = world_dy
            world_dx = temp_dx * cos_angle - temp_dy * sin_angle
            world_dy = temp_dx * sin_angle + temp_dy * cos_angle

        return (world_dx, world_dy)

    def handle_edge_scrolling_and_cursor_mirror(self,
                                                current_pos,
                                                is_world_drag=False):
        """Handle edge scrolling and cursor position mirroring under rotation.
        
        Returns the effective position to use for dragging operations.
        If cursor mirroring is active, applies inverse rotation transformation.
        If edge scrolling is needed, continues movement proportionally.
        """

        size = self.GetSize()

        # Apply inverse rotation to get the cursor position in pre-rotated space for consistent dragging
        effective_pos = current_pos
        if self.world_rotation != 0.0 and not is_world_drag:
            center_x = size.width // 2
            center_y = size.height // 2

            # Apply inverse rotation for cursor mirroring
            rotation_rad = -math.radians(self.world_rotation)
            cos_angle = math.cos(rotation_rad)
            sin_angle = math.sin(rotation_rad)

            temp_x = current_pos.x - center_x
            temp_y = current_pos.y - center_y

            mirrored_x = temp_x * cos_angle - temp_y * sin_angle + center_x
            mirrored_y = temp_x * sin_angle + temp_y * cos_angle + center_y

            effective_pos = wx.Point(int(mirrored_x), int(mirrored_y))
            print(
                f"DEBUG: 🎮 Cursor mirroring: actual({current_pos.x}, {current_pos.y}) -> effective({effective_pos.x}, {effective_pos.y})"
            )

        # Check for edge scrolling
        edge_scroll_x = 0
        edge_scroll_y = 0

        # Left edge
        if current_pos.x < self.edge_scroll_zone:
            edge_scroll_x = -(self.edge_scroll_zone -
                              current_pos.x) * self.edge_scroll_speed
        # Right edge
        elif current_pos.x > size.width - self.edge_scroll_zone:
            edge_scroll_x = (
                current_pos.x -
                (size.width - self.edge_scroll_zone)) * self.edge_scroll_speed

        # Top edge
        if current_pos.y < self.edge_scroll_zone:
            edge_scroll_y = -(self.edge_scroll_zone -
                              current_pos.y) * self.edge_scroll_speed
        # Bottom edge
        elif current_pos.y > size.height - self.edge_scroll_zone:
            edge_scroll_y = (
                current_pos.y -
                (size.height - self.edge_scroll_zone)) * self.edge_scroll_speed

        # Apply edge scrolling
        if edge_scroll_x != 0 or edge_scroll_y != 0:
            print(
                f"DEBUG: 📏 Edge scrolling: ({edge_scroll_x:.1f}, {edge_scroll_y:.1f})"
            )

            if is_world_drag and not self.pan_suppressed:
                # For world dragging, apply scrolling to pan
                self.pan_x += edge_scroll_x
                self.pan_y += edge_scroll_y
            else:
                # For object dragging, simulate cursor movement beyond edge
                virtual_x = effective_pos.x + edge_scroll_x
                virtual_y = effective_pos.y + edge_scroll_y
                effective_pos = wx.Point(int(virtual_x), int(virtual_y))

            self.Refresh()

        return effective_pos

    def zoom_to_world_center(self, zoom_in=True):
        """Zoom in or out to the center of the world view."""

        if zoom_in:
            zoom_factor = self.center_zoom_factor
        else:
            zoom_factor = 1.0 / self.center_zoom_factor

        # Get current canvas center
        canvas_size = self.GetSize()
        canvas_center_x = canvas_size.width / 2
        canvas_center_y = canvas_size.height / 2

        # Convert current canvas center to world coordinates
        world_center_x = (canvas_center_x - self.pan_x) / self.zoom
        world_center_y = (canvas_center_y - self.pan_y) / self.zoom

        # Apply zoom
        old_zoom = self.zoom
        new_zoom = max(self.min_zoom,
                       min(self.max_zoom, self.zoom * zoom_factor))
        self.zoom = new_zoom

        # Adjust pan to keep the world center fixed at canvas center
        self.pan_x = canvas_center_x - world_center_x * self.zoom
        self.pan_y = canvas_center_y - world_center_y * self.zoom

        print(
            f"DEBUG: 🔍 Center zoom: {old_zoom:.2f} -> {new_zoom:.2f}, {'in' if zoom_in else 'out'}"
        )
        self.Refresh()

    def zoom_to_world_center_smooth(self, zoom_in=True):
        """Smooth zoom in or out to the center of the world view (for mouse wheel)."""

        # Use smooth zoom increment like mouse wheel
        base_zoom = 0.1 * self.zoom_sensitivity
        if zoom_in:
            zoom_factor = 1.0 + base_zoom
        else:
            zoom_factor = 1.0 - base_zoom

        # Get current canvas center
        canvas_size = self.GetSize()
        canvas_center_x = canvas_size.width / 2
        canvas_center_y = canvas_size.height / 2

        # Convert current canvas center to world coordinates
        world_center_x = (canvas_center_x - self.pan_x) / self.zoom
        world_center_y = (canvas_center_y - self.pan_y) / self.zoom

        # Apply smooth zoom
        old_zoom = self.zoom
        new_zoom = max(self.min_zoom,
                       min(self.max_zoom, self.zoom * zoom_factor))
        self.zoom = new_zoom

        # Adjust pan to keep the world center fixed at canvas center
        self.pan_x = canvas_center_x - world_center_x * self.zoom
        self.pan_y = canvas_center_y - world_center_y * self.zoom

        # No debug print here to avoid spam during smooth scrolling

    def zoom_to_world_center_magnify(self, magnification):
        """Zoom to the center of the world view using trackpad magnification factor."""

        # Get current canvas center
        canvas_size = self.GetSize()
        canvas_center_x = canvas_size.width / 2
        canvas_center_y = canvas_size.height / 2

        # Convert current canvas center to world coordinates
        world_center_x = (canvas_center_x - self.pan_x) / self.zoom
        world_center_y = (canvas_center_y - self.pan_y) / self.zoom

        # Apply magnification-based zoom
        old_zoom = self.zoom
        new_zoom = max(self.min_zoom,
                       min(self.max_zoom, self.zoom * magnification))
        self.zoom = new_zoom

        # Adjust pan to keep the world center fixed at canvas center
        self.pan_x = canvas_center_x - world_center_x * self.zoom
        self.pan_y = canvas_center_y - world_center_y * self.zoom

    def snap_to_grid(self,
                     x: float,
                     y: float,
                     node_width: float = 50.0,
                     node_height: float = 30.0) -> Tuple[float, float]:
        """Snap position to grid based on the current snap anchor setting."""

        if not self.grid_snapping_enabled:
            return x, y

        # Use the configured grid spacing
        grid_size = self.grid_spacing

        # Calculate anchor point offset from node center
        if self.snap_anchor == "upper_left":
            anchor_offset_x = -node_width / 2
            anchor_offset_y = -node_height / 2
        elif self.snap_anchor == "upper_center":
            anchor_offset_x = 0
            anchor_offset_y = -node_height / 2
        elif self.snap_anchor == "upper_right":
            anchor_offset_x = node_width / 2
            anchor_offset_y = -node_height / 2
        elif self.snap_anchor == "left_center":
            anchor_offset_x = -node_width / 2
            anchor_offset_y = 0
        elif self.snap_anchor == "center":
            anchor_offset_x = 0
            anchor_offset_y = 0
        elif self.snap_anchor == "right_center":
            anchor_offset_x = node_width / 2
            anchor_offset_y = 0
        elif self.snap_anchor == "bottom_left":
            anchor_offset_x = -node_width / 2
            anchor_offset_y = node_height / 2
        elif self.snap_anchor == "bottom_center":
            anchor_offset_x = 0
            anchor_offset_y = node_height / 2
        elif self.snap_anchor == "bottom_right":
            anchor_offset_x = node_width / 2
            anchor_offset_y = node_height / 2
        else:
            # Default to center
            anchor_offset_x = 0
            anchor_offset_y = 0

        # Calculate the anchor point position in world coordinates
        anchor_x = x + anchor_offset_x
        anchor_y = y + anchor_offset_y

        # Snap the anchor point to the nearest grid intersection (multiples of 20)
        snapped_anchor_x = round(anchor_x / grid_size) * grid_size
        snapped_anchor_y = round(anchor_y / grid_size) * grid_size

        # Calculate the final node center position
        snapped_x = snapped_anchor_x - anchor_offset_x
        snapped_y = snapped_anchor_y - anchor_offset_y

        print(
            f"DEBUG: 🔗 GRID SNAP: node_center ({x:.1f}, {y:.1f}) -> ({snapped_x:.1f}, {snapped_y:.1f})"
        )
        print(
            f"DEBUG: 🔗 GRID SNAP: anchor '{self.snap_anchor}' at ({anchor_x:.1f}, {anchor_y:.1f}) -> snapped to ({snapped_anchor_x:.1f}, {snapped_anchor_y:.1f})"
        )
        print(
            f"DEBUG: 🔗 GRID SNAP: grid intersections: ...,-40,-20,0,20,40,60,... (spacing={grid_size})"
        )

        return snapped_x, snapped_y

    def get_node_at_position(self, screen_x: int,
                             screen_y: int) -> Optional[m_node.Node]:
        """Get the node at the given screen position using unified world_to_screen transform."""

        print(
            f"DEBUG: get_node_at_position: screen({screen_x}, {screen_y}), world_rotation={self.world_rotation}°"
        )

        # Iterate in reverse order to pick topmost node on overlaps
        nodes = self.graph.get_all_nodes()
        for node in reversed(nodes):
            if not node.visible:
                continue

            # Use the same pipeline as drawing for the node center
            cx, cy = self.world_to_screen(node.x, node.y)

            # Hit test in screen space; scale node bounds by zoom; enforce a small min size for usability
            half_w = max(6.0, (node.width * self.zoom) / 2.0)
            half_h = max(6.0, (node.height * self.zoom) / 2.0)

            dx = float(screen_x - cx)
            dy = float(screen_y - cy)

            # Undo node-local rotation in screen space if present
            node_rot = float(getattr(node, 'rotation', 0.0) or 0.0)
            if abs(node_rot) > 1e-6:
                rot_rad = -math.radians(node_rot)
                cos_r = math.cos(rot_rad)
                sin_r = math.sin(rot_rad)
                rdx = dx * cos_r - dy * sin_r
                rdy = dx * sin_r + dy * cos_r
                dx, dy = rdx, rdy

            inside = (-half_w <= dx <= half_w) and (-half_h <= dy <= half_h)
            if inside:
                print(
                    f"DEBUG: ✅ Found node '{node.text}' at visual position ({cx:.1f},{cy:.1f})"
                )
                return node
            else:
                print(
                    f"DEBUG: Node '{node.text}' miss: center=({cx:.1f},{cy:.1f}), dxdy=({dx:.1f},{dy:.1f}), half=({half_w:.1f},{half_h:.1f}), mouse=({screen_x},{screen_y})"
                )

        print("DEBUG: ❌ No visible node found at position")
        return None

    def get_edge_at_position(self, screen_x: int,
                             screen_y: int) -> Optional[m_edge.Edge]:
        """Get the edge at the given screen position, checking against actual curve paths with anchor endpoints."""

        world_x, world_y = self.screen_to_world(screen_x, screen_y)
        tolerance = max(
            10.0, 15.0 / self.zoom
        )  # Click tolerance in world coordinates, scales with zoom

        for edge in self.graph.get_all_edges():
            source_node = self.graph.get_node(edge.source_id)
            target_node = self.graph.get_node(edge.target_id)

            if not source_node or not target_node:
                continue

            # Prefer anchor endpoints (connection points) for better hit-testing alignment
            if hasattr(self, 'get_edge_anchor_endpoints_world'):
                try:
                    src_anchor, tgt_anchor = self.get_edge_anchor_endpoints_world(
                        edge, source_node, target_node)
                except Exception:
                    src_anchor = (source_node.x, source_node.y)
                    tgt_anchor = (target_node.x, target_node.y)
            else:
                src_anchor = (source_node.x, source_node.y)
                tgt_anchor = (target_node.x, target_node.y)

            # Check if point is near the actual curve path
            if self.point_near_curve(world_x, world_y, edge, source_node,
                                     target_node, tolerance):
                return edge
        return None

    def point_near_curve(self, px, py, edge, source_node, target_node,
                         tolerance):
        """Check if a point is near the curve path of an edge."""

        rendering_type = edge.rendering_type if edge.rendering_type else self.edge_rendering_type

        print(
            f"DEBUG: 🎯 Checking if point ({px:.1f}, {py:.1f}) is near edge {edge.id} (type: {rendering_type}, tolerance: {tolerance:.1f})"
        )

        # Sample the curve at multiple points and check distance to each segment
        samples = 50  # Number of curve samples to check

        prev_point = None
        min_distance = float('inf')

        for i in range(samples + 1):
            t = i / samples
            curve_point = self.calculate_position_on_curve(
                edge, source_node, target_node, t)

            if curve_point:
                if prev_point:
                    # Check distance to line segment between prev_point and curve_point
                    distance = self._point_to_line_segment_distance(
                        px, py, prev_point, curve_point)
                    min_distance = min(min_distance, distance)
                    if distance <= tolerance:
                        print(
                            f"DEBUG: 🎯 Point is within tolerance! Distance: {distance:.1f} <= {tolerance:.1f}"
                        )
                        return True
                prev_point = curve_point

        print(
            f"DEBUG: 🎯 Point not near edge {edge.id}. Min distance: {min_distance:.1f}"
        )
        return False

    def _point_to_line_segment_distance(self, px, py, p1, p2):
        """Calculate the distance from a point to a line segment."""

        x1, y1 = p1
        x2, y2 = p2

        # Calculate line length squared
        line_length_sq = (x2 - x1)**2 + (y2 - y1)**2

        if line_length_sq == 0:
            # Degenerate line (point)
            return math.sqrt((px - x1)**2 + (py - y1)**2)

        # Calculate the parameter t for the closest point on the line
        t = max(
            0,
            min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) /
                line_length_sq))

        # Find the closest point on the line segment
        closest_x = x1 + t * (x2 - x1)
        closest_y = y1 + t * (y2 - y1)

        # Return distance to the closest point
        return math.sqrt((px - closest_x)**2 + (py - closest_y)**2)

    def calculate_anchor_position(self, node, mouse_world_pos, anchor_mode):
        """Calculate the anchor position based on the mode and mouse position, accounting for node rotation."""

        # Check if the node has rotation
        has_individual_rotation = hasattr(node,
                                          'rotation') and node.rotation != 0.0
        has_auto_readable = self.auto_readable_nodes and self.world_rotation != 0.0

        effective_rotation = 0.0
        if has_individual_rotation:
            effective_rotation += node.rotation
        if has_auto_readable:
            effective_rotation -= self.world_rotation

        def rotate_point_around_node(px, py):
            """Rotate a point around the node center by the effective rotation."""

            if effective_rotation == 0.0:
                return px, py

            # Translate to origin (node center)
            dx = px - node.x
            dy = py - node.y

            # Apply rotation
            cos_rot = math.cos(math.radians(effective_rotation))
            sin_rot = math.sin(math.radians(effective_rotation))

            rotated_x = dx * cos_rot - dy * sin_rot
            rotated_y = dx * sin_rot + dy * cos_rot

            # Translate back
            return node.x + rotated_x, node.y + rotated_y

        if anchor_mode == "free":
            # Constrain to node boundary
            # For rotated nodes, we need to work in the node's local coordinate system
            if effective_rotation != 0.0:
                # Rotate mouse position to node's local coordinates
                dx = mouse_world_pos[0] - node.x
                dy = mouse_world_pos[1] - node.y

                cos_rot = math.cos(
                    math.radians(-effective_rotation))  # Inverse rotation
                sin_rot = math.sin(math.radians(-effective_rotation))

                local_dx = dx * cos_rot - dy * sin_rot
                local_dy = dx * sin_rot + dy * cos_rot
            else:
                local_dx = mouse_world_pos[0] - node.x
                local_dy = mouse_world_pos[1] - node.y

            # Calculate the half dimensions
            half_width = node.width / 2
            half_height = node.height / 2

            # Clamp to node boundary in local coordinates
            if abs(local_dx) > half_width:
                local_dx = half_width if local_dx > 0 else -half_width
            if abs(local_dy) > half_height:
                local_dy = half_height if local_dy > 0 else -half_height

            # Convert back to world coordinates
            return rotate_point_around_node(node.x + local_dx,
                                            node.y + local_dy)

        elif anchor_mode == "center":
            return (node.x, node.y)

        elif anchor_mode == "nearest_face":
            # Find the nearest face based on mouse position
            # For rotated nodes, work in local coordinates
            if effective_rotation != 0.0:
                dx = mouse_world_pos[0] - node.x
                dy = mouse_world_pos[1] - node.y

                cos_rot = math.cos(
                    math.radians(-effective_rotation))  # Inverse rotation
                sin_rot = math.sin(math.radians(-effective_rotation))

                local_dx = dx * cos_rot - dy * sin_rot
                local_dy = dx * sin_rot + dy * cos_rot
            else:
                local_dx = mouse_world_pos[0] - node.x
                local_dy = mouse_world_pos[1] - node.y

            half_width = node.width / 2
            half_height = node.height / 2

            # Determine which face is closest in local coordinates
            abs_dx = abs(local_dx)
            abs_dy = abs(local_dy)

            if abs_dx > abs_dy:
                # Left or right face
                if local_dx > 0:
                    local_pos = (node.x + half_width, node.y)  # Right face
                else:
                    local_pos = (node.x - half_width, node.y)  # Left face
            else:
                # Top or bottom face
                if local_dy > 0:
                    local_pos = (node.x, node.y + half_height)  # Bottom face
                else:
                    local_pos = (node.x, node.y - half_height)  # Top face

            return rotate_point_around_node(local_pos[0], local_pos[1])

        else:
            # Specific anchor points
            half_width = node.width / 2
            half_height = node.height / 2

            anchor_positions = {
                "left_center": (node.x - half_width, node.y),
                "right_center": (node.x + half_width, node.y),
                "top_center": (node.x, node.y - half_height),
                "bottom_center": (node.x, node.y + half_height),
                "top_left": (node.x - half_width, node.y - half_height),
                "top_right": (node.x + half_width, node.y - half_height),
                "bottom_left": (node.x - half_width, node.y + half_height),
                "bottom_right": (node.x + half_width, node.y + half_height),
            }

            base_pos = anchor_positions.get(anchor_mode, (node.x, node.y))
            return rotate_point_around_node(base_pos[0], base_pos[1])

    def update_custom_endpoints_for_moved_nodes(self, old_positions):
        """Update custom edge endpoints when their associated nodes are moved."""

        for edge in self.graph.get_all_edges():
            if not hasattr(edge,
                           'custom_endpoints') or not edge.custom_endpoints:
                continue

            source_node = self.graph.get_node(edge.source_id)
            target_node = self.graph.get_node(edge.target_id)

            if not source_node or not target_node:
                continue

            # Check if source node was moved and has custom endpoint
            if edge.source_id in old_positions and 'source' in edge.custom_endpoints:
                old_node_pos = old_positions[edge.source_id]
                new_node_pos = (source_node.x, source_node.y)
                old_endpoint = edge.custom_endpoints['source']

                # Calculate the offset from old node position to old endpoint
                offset_x = old_endpoint[0] - old_node_pos[0]
                offset_y = old_endpoint[1] - old_node_pos[1]

                # Apply the same offset to new node position
                new_endpoint = (new_node_pos[0] + offset_x,
                                new_node_pos[1] + offset_y)
                edge.custom_endpoints['source'] = new_endpoint

                print(
                    f"DEBUG: 🔗 Updated source endpoint for edge {edge.id}: {old_endpoint} -> {new_endpoint}"
                )

            # Check if target node was moved and has custom endpoint
            if edge.target_id in old_positions and 'target' in edge.custom_endpoints:
                old_node_pos = old_positions[edge.target_id]
                new_node_pos = (target_node.x, target_node.y)
                old_endpoint = edge.custom_endpoints['target']

                # Calculate the offset from old node position to old endpoint
                offset_x = old_endpoint[0] - old_node_pos[0]
                offset_y = old_endpoint[1] - old_node_pos[1]

                # Apply the same offset to new node position
                new_endpoint = (new_node_pos[0] + offset_x,
                                new_node_pos[1] + offset_y)
                edge.custom_endpoints['target'] = new_endpoint

                print(
                    f"DEBUG: 🔗 Updated target endpoint for edge {edge.id}: {old_endpoint} -> {new_endpoint}"
                )

    def update_control_points_for_moved_nodes(self, old_positions):
        """Update edge control points when their associated nodes are moved."""

        for edge in self.graph.get_all_edges():
            if not hasattr(edge, 'control_points') or not edge.control_points:
                continue

            source_node = self.graph.get_node(edge.source_id)
            target_node = self.graph.get_node(edge.target_id)

            if not source_node or not target_node:
                continue

            # Check if this is a self-loop
            is_self_loop = source_node.id == target_node.id

            # For self-loops, we only need to check if the node was moved
            if is_self_loop and edge.source_id in old_positions:
                old_node_pos = old_positions[edge.source_id]
                new_node_pos = (source_node.x, source_node.y)

                # Calculate node movement offset
                dx = new_node_pos[0] - old_node_pos[0]
                dy = new_node_pos[1] - old_node_pos[1]

                # Move all control points by the same offset
                new_control_points = []
                for cp in edge.control_points:
                    if len(cp
                           ) >= 2:  # Ensure we have at least x, y coordinates
                        new_cp = (cp[0] + dx, cp[1] + dy)
                        if len(cp) > 2:  # Preserve z coordinate if present
                            new_cp = new_cp + (cp[2], )
                        new_control_points.append(new_cp)

                edge.control_points = new_control_points
                print(
                    f"DEBUG: 🎛️ Updated {len(new_control_points)} control points for self-loop edge {edge.id}"
                )

            # For edges between different nodes
            elif not is_self_loop and (edge.source_id in old_positions
                                       or edge.target_id in old_positions):
                source_moved = edge.source_id in old_positions
                target_moved = edge.target_id in old_positions

                if source_moved and target_moved:
                    # Both nodes moved - calculate average movement to preserve edge shape
                    old_source_pos = old_positions[edge.source_id]
                    old_target_pos = old_positions[edge.target_id]
                    new_source_pos = (source_node.x, source_node.y)
                    new_target_pos = (target_node.x, target_node.y)

                    # Calculate movement of both endpoints
                    source_dx = new_source_pos[0] - old_source_pos[0]
                    source_dy = new_source_pos[1] - old_source_pos[1]
                    target_dx = new_target_pos[0] - old_target_pos[0]
                    target_dy = new_target_pos[1] - old_target_pos[1]

                    # Move control points based on their relative position between source and target
                    new_control_points = []
                    for cp in edge.control_points:
                        if len(cp) >= 2:
                            # Calculate relative position of control point between old source and target
                            old_edge_dx = old_target_pos[0] - old_source_pos[0]
                            old_edge_dy = old_target_pos[1] - old_source_pos[1]

                            if abs(old_edge_dx) > 0.1 or abs(
                                    old_edge_dy
                            ) > 0.1:  # Avoid division by zero
                                # Find position along old edge (0 = source, 1 = target)
                                t = 0.5  # Default to middle if calculation fails
                                if abs(old_edge_dx) > abs(old_edge_dy):
                                    t = (
                                        cp[0] - old_source_pos[0]
                                    ) / old_edge_dx if old_edge_dx != 0 else 0.5
                                else:
                                    t = (
                                        cp[1] - old_source_pos[1]
                                    ) / old_edge_dy if old_edge_dy != 0 else 0.5
                                t = max(0, min(1, t))  # Clamp between 0 and 1

                                # Interpolate movement based on position
                                move_dx = source_dx * (1 - t) + target_dx * t
                                move_dy = source_dy * (1 - t) + target_dy * t
                            else:
                                # Fallback: average movement
                                move_dx = (source_dx + target_dx) / 2
                                move_dy = (source_dy + target_dy) / 2

                            new_cp = (cp[0] + move_dx, cp[1] + move_dy)
                            if len(cp) > 2:  # Preserve z coordinate if present
                                new_cp = new_cp + (cp[2], )
                            new_control_points.append(new_cp)

                    edge.control_points = new_control_points
                    print(
                        f"DEBUG: 🎛️ Updated {len(new_control_points)} control points for edge {edge.id} (both nodes moved)"
                    )

                elif source_moved or target_moved:
                    # Only one node moved - move control points proportionally
                    moved_node_id = edge.source_id if source_moved else edge.target_id
                    old_moved_pos = old_positions[moved_node_id]
                    new_moved_pos = (source_node.x,
                                     source_node.y) if source_moved else (
                                         target_node.x, target_node.y)

                    # Calculate movement offset
                    dx = new_moved_pos[0] - old_moved_pos[0]
                    dy = new_moved_pos[1] - old_moved_pos[1]

                    # Move control points by a fraction of the movement to maintain edge shape
                    # The fraction depends on which node moved (source vs target)
                    fraction = 0.5  # Move control points halfway with the moved node

                    new_control_points = []
                    for cp in edge.control_points:
                        if len(cp) >= 2:
                            new_cp = (cp[0] + dx * fraction,
                                      cp[1] + dy * fraction)
                            if len(cp) > 2:  # Preserve z coordinate if present
                                new_cp = new_cp + (cp[2], )
                            new_control_points.append(new_cp)

                    edge.control_points = new_control_points
                    print(
                        f"DEBUG: 🎛️ Updated {len(new_control_points)} control points for edge {edge.id} ({'source' if source_moved else 'target'} moved)"
                    )

    def graham_scan(self, points):
        """Compute the convex hull of a set of points using Graham's scan algorithm."""

        def orientation(p, q, r):
            val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
            if val == 0:
                return 0
            return 1 if val > 0 else 2

        n = len(points)
        if n < 3:
            return points

        # Find the bottommost point (and leftmost if tied)
        bottom_idx = 0
        for i in range(1, n):
            if (points[i][1] < points[bottom_idx][1]
                    or (points[i][1] == points[bottom_idx][1]
                        and points[i][0] < points[bottom_idx][0])):
                bottom_idx = i

        # Swap the bottommost point to position 0
        points[0], points[bottom_idx] = points[bottom_idx], points[0]

        # Sort points by polar angle and distance from points[0]
        p0 = points[0]
        sorted_points = sorted(points[1:],
                               key=lambda p:
                               (math.atan2(p[1] - p0[1], p[0] - p0[0]),
                                (p[0] - p0[0])**2 + (p[1] - p0[1])**2))
        sorted_points = [p0] + sorted_points

        # Build convex hull
        stack = [sorted_points[0], sorted_points[1]]
        for i in range(2, len(sorted_points)):
            while len(stack) > 1 and orientation(stack[-2], stack[-1],
                                                 sorted_points[i]) != 2:
                stack.pop()
            stack.append(sorted_points[i])

        return stack

    def evaluate_bspline(self, control_points, t):
        """Evaluate B-spline curve at parameter t."""

        # Simple B-spline evaluation for 4 control points
        if len(control_points) != 4:
            return control_points[0] if control_points else (0, 0)

        # Basis functions for cubic B-spline
        b0 = (1 - t)**3 / 6
        b1 = (3 * t**3 - 6 * t**2 + 4) / 6
        b2 = (-3 * t**3 + 3 * t**2 + 3 * t + 1) / 6
        b3 = t**3 / 6

        x = (b0 * control_points[0][0] + b1 * control_points[1][0] +
             b2 * control_points[2][0] + b3 * control_points[3][0])
        y = (b0 * control_points[0][1] + b1 * control_points[1][1] +
             b2 * control_points[2][1] + b3 * control_points[3][1])

        return x, y

    def evaluate_bspline_variable(self, control_points, t):
        """Evaluate B-spline curve with variable number of control points using De Boor-like algorithm."""

        if len(control_points) < 2:
            return control_points[0] if control_points else (0, 0)

        # For simplicity, we'll use a uniform B-spline approach
        # This is a simplified version that works reasonably well for visualization
        n = len(control_points) - 1  # Number of intervals

        if n == 1:
            # Linear interpolation between two points
            p1, p2 = control_points[0], control_points[1]
            x = (1 - t) * p1[0] + t * p2[0]
            y = (1 - t) * p1[1] + t * p2[1]
            return x, y

        elif n == 2:
            # Quadratic B-spline
            return self.evaluate_quadratic_bspline(control_points, t)

        elif n >= 3:
            # Cubic or higher order B-spline - use approximation
            return self.evaluate_cubic_bspline_approximation(control_points, t)

        # Fallback for any missed cases
        return control_points[0] if control_points else (0, 0)

    def evaluate_quadratic_bspline(self, control_points, t):
        """Evaluate quadratic B-spline with 3 control points."""

        if len(control_points) != 3:
            return control_points[0]

        p0, p1, p2 = control_points

        # Quadratic B-spline basis functions
        b0 = (1 - t)**2 / 2
        b1 = (-2 * t**2 + 2 * t + 1) / 2
        b2 = t**2 / 2

        x = b0 * p0[0] + b1 * p1[0] + b2 * p2[0]
        y = b0 * p0[1] + b1 * p1[1] + b2 * p2[1]

        return x, y

    def evaluate_quadratic_bezier_curve(self, control_points, t):
        """Evaluate a quadratic Bézier curve at parameter t with 3 control points."""

        if len(control_points) != 3:
            return control_points[0] if control_points else (0, 0)

        p0, p1, p2 = control_points

        # Quadratic Bézier formula: (1-t)²*P0 + 2*(1-t)*t*P1 + t²*P2
        t2 = t * t
        one_minus_t = 1 - t
        one_minus_t2 = one_minus_t * one_minus_t

        x = one_minus_t2 * p0[0] + 2 * one_minus_t * t * p1[0] + t2 * p2[0]
        y = one_minus_t2 * p0[1] + 2 * one_minus_t * t * p1[1] + t2 * p2[1]

        return x, y

    def evaluate_polyline_curve(self, segment_points, t):
        """Evaluate a polyline curve at parameter t by finding the appropriate segment."""

        if not segment_points or len(segment_points) < 2:
            return segment_points[0] if segment_points else (0, 0)

        if len(segment_points) == 2:
            # Simple linear interpolation between two points
            p1, p2 = segment_points[0], segment_points[1]
            x = (1 - t) * p1[0] + t * p2[0]
            y = (1 - t) * p1[1] + t * p2[1]
            return x, y

        # Multiple segments - find which segment contains parameter t
        num_segments = len(segment_points) - 1
        segment_length = 1.0 / num_segments
        segment_index = min(int(t * num_segments), num_segments - 1)

        # Calculate local t within the segment (0.0 to 1.0)
        segment_start_t = segment_index * segment_length
        segment_end_t = (segment_index + 1) * segment_length

        if segment_end_t - segment_start_t > 0:
            local_t = (t - segment_start_t) / (segment_end_t - segment_start_t)
        else:
            local_t = 0.0

        # Linear interpolation within the segment
        p1 = segment_points[segment_index]
        p2 = segment_points[segment_index + 1]

        x = (1 - local_t) * p1[0] + local_t * p2[0]
        y = (1 - local_t) * p1[1] + local_t * p2[1]

        return x, y

    def evaluate_rational_bezier_curve(self, weighted_points, t):
        """Evaluate a rational Bézier curve (NURBS) at parameter t with weighted control points."""

        if not weighted_points:
            return (0, 0)

        if len(weighted_points) == 1:
            return (weighted_points[0][0], weighted_points[0][1])

        # Extract points and weights
        points = [(p[0], p[1]) for p in weighted_points]
        weights = [p[2] if len(p) > 2 else 1.0 for p in weighted_points]

        # Calculate weighted Bézier curve
        n = len(points) - 1
        x_num = y_num = w_denom = 0

        for i in range(n + 1):
            # Bernstein basis function
            binom_coeff = self.binomial_coefficient(n, i)
            basis = binom_coeff * ((1 - t)**(n - i)) * (t**i)

            # Weighted contribution
            weighted_basis = basis * weights[i]
            x_num += weighted_basis * points[i][0]
            y_num += weighted_basis * points[i][1]
            w_denom += weighted_basis

        # Avoid division by zero
        if abs(w_denom) < 1e-10:
            return points[0]

        return x_num / w_denom, y_num / w_denom

    def binomial_coefficient(self, n, k):
        """Calculate binomial coefficient C(n,k) = n! / (k! * (n-k)!)"""

        if k > n or k < 0:
            return 0
        if k == 0 or k == n:
            return 1

        # Use the multiplicative formula to avoid large factorials
        result = 1
        for i in range(min(k, n - k)):
            result = result * (n - i) // (i + 1)
        return result

    def evaluate_cubic_bspline_approximation(self, control_points, t):
        """Approximate higher-order B-spline using piecewise cubic segments."""

        n = len(control_points) - 1

        # Determine which segment we're in
        segment_t = t * (n - 2)  # Scale to number of cubic segments
        segment_index = int(segment_t)
        local_t = segment_t - segment_index

        # Clamp to valid range
        segment_index = max(0, min(segment_index, n - 3))

        # Use 4 consecutive control points for cubic B-spline segment
        p0 = control_points[segment_index]
        p1 = control_points[segment_index + 1]
        p2 = control_points[segment_index + 2]
        p3 = control_points[segment_index + 3]

        # Cubic B-spline basis functions
        t2 = local_t * local_t
        t3 = t2 * local_t

        b0 = (1 - 3 * local_t + 3 * t2 - t3) / 6
        b1 = (4 - 6 * t2 + 3 * t3) / 6
        b2 = (1 + 3 * local_t + 3 * t2 - 3 * t3) / 6
        b3 = t3 / 6

        x = b0 * p0[0] + b1 * p1[0] + b2 * p2[0] + b3 * p3[0]
        y = b0 * p0[1] + b1 * p1[1] + b2 * p2[1] + b3 * p3[1]

        return x, y

    def evaluate_interpolating_spline(self, points, t):
        """Evaluate an interpolating spline that passes through all given points."""

        if len(points) < 2:
            return points[0] if points else (0, 0)

        n = len(points) - 1  # Number of segments

        if n == 1:
            # Linear interpolation between two points
            p1, p2 = points[0], points[1]
            x = (1 - t) * p1[0] + t * p2[0]
            y = (1 - t) * p1[1] + t * p2[1]
            return x, y

        # For multiple points, use piecewise interpolation
        # Scale t to the number of segments
        segment_t = t * n
        segment_index = min(int(segment_t), n - 1)
        local_t = segment_t - segment_index

        # Get the current segment points
        p0 = points[segment_index]
        p1 = points[segment_index + 1]

        # Add curvature using adjacent points if available
        if len(points) >= 3:
            # Use Catmull-Rom spline for smooth interpolation
            # Get control points for smooth curve
            if segment_index > 0:
                p_prev = points[segment_index - 1]
            else:
                p_prev = p0  # Use current point if at start

            if segment_index < n - 1:
                p_next = points[segment_index + 2]
            else:
                p_next = p1  # Use current point if at end

            # Catmull-Rom spline evaluation
            t2 = local_t * local_t
            t3 = t2 * local_t

            # Catmull-Rom basis functions
            x = 0.5 * (
                (2 * p0[0]) + (-p_prev[0] + p1[0]) * local_t +
                (2 * p_prev[0] - 5 * p0[0] + 4 * p1[0] - p_next[0]) * t2 +
                (-p_prev[0] + 3 * p0[0] - 3 * p1[0] + p_next[0]) * t3)

            y = 0.5 * (
                (2 * p0[1]) + (-p_prev[1] + p1[1]) * local_t +
                (2 * p_prev[1] - 5 * p0[1] + 4 * p1[1] - p_next[1]) * t2 +
                (-p_prev[1] + 3 * p0[1] - 3 * p1[1] + p_next[1]) * t3)

            return x, y
        else:
            # Simple linear interpolation for only 2 points
            x = (1 - local_t) * p0[0] + local_t * p1[0]
            y = (1 - local_t) * p0[1] + local_t * p1[1]
            return x, y

    def evaluate_rational_bezier(self, control_points, t):
        """Evaluate rational Bézier curve at parameter t."""

        if len(control_points) != 4:
            return control_points[0][:2] if control_points else (0, 0)

        # Rational Bézier curve evaluation
        t2 = t * t
        t3 = t2 * t

        # Basis functions for cubic Bézier
        b0 = (1 - t)**3
        b1 = 3 * (1 - t)**2 * t
        b2 = 3 * (1 - t) * t2
        b3 = t3

        # Weighted sum
        wx = (b0 * control_points[0][0] * control_points[0][2] +
              b1 * control_points[1][0] * control_points[1][2] +
              b2 * control_points[2][0] * control_points[2][2] +
              b3 * control_points[3][0] * control_points[3][2])

        wy = (b0 * control_points[0][1] * control_points[0][2] +
              b1 * control_points[1][1] * control_points[1][2] +
              b2 * control_points[2][1] * control_points[2][2] +
              b3 * control_points[3][1] * control_points[3][2])

        w = (b0 * control_points[0][2] + b1 * control_points[1][2] +
             b2 * control_points[2][2] + b3 * control_points[3][2])

        # Avoid division by zero
        if abs(w) < 1e-10:
            w = 1e-10

        return wx / w, wy / w

    def evaluate_rational_bezier_variable(self, control_points, t):
        """Evaluate general rational Bézier curve at parameter t with variable control points."""

        if not control_points:
            return (0, 0)

        if len(control_points) == 1:
            return control_points[0][:2]

        n = len(control_points) - 1  # Degree of the curve

        # Calculate binomial coefficients and basis functions
        def binomial(n, k):
            if k > n or k < 0:
                return 0
            if k == 0 or k == n:
                return 1
            result = 1
            for i in range(min(k, n - k)):
                result = result * (n - i) // (i + 1)
            return result

        # Calculate weighted sum
        wx = wy = w = 0
        for i, cp in enumerate(control_points):
            # Bernstein basis function
            basis = binomial(n, i) * (t**i) * ((1 - t)**(n - i))
            weight = cp[2] if len(
                cp) > 2 else 1.0  # Use weight if provided, otherwise 1.0

            wx += basis * cp[0] * weight
            wy += basis * cp[1] * weight
            w += basis * weight

        # Avoid division by zero
        if abs(w) < 1e-10:
            w = 1e-10

        return wx / w, wy / w

    def evaluate_bezier_curve(self, control_points, t):
        """Evaluate general Bézier curve at parameter t using De Casteljau's algorithm."""

        if not control_points:
            return (0, 0)

        if len(control_points) == 1:
            return control_points[0]

        # De Casteljau's algorithm for stable evaluation
        points = [(p[0], p[1]) for p in control_points
                  ]  # Ensure we only use x,y coordinates

        while len(points) > 1:
            new_points = []
            for i in range(len(points) - 1):
                x = (1 - t) * points[i][0] + t * points[i + 1][0]
                y = (1 - t) * points[i][1] + t * points[i + 1][1]
                new_points.append((x, y))
            points = new_points

        return points[0]

    # B-spline control points list is now managed via the sidebar properties panel

    def initialize_control_points(self, edge, source_node, target_node):
        """Initialize default control points for an edge based on its type."""

        # Skip control point initialization for freeform edges
        rendering_type = edge.rendering_type if edge.rendering_type else self.edge_rendering_type
        if rendering_type == "freeform":
            edge.control_points = []
            edge.custom_position = False
            return

        dx = target_node.x - source_node.x
        dy = target_node.y - source_node.y

        # Check if this is a self-loop (same source and target)
        is_self_loop = source_node.id == target_node.id

        if rendering_type == "straight":
            # No control points needed for straight lines, but self-loops need at least one
            if is_self_loop:
                # Create a simple loop above the node - use 3D coordinates
                edge.control_points = [(source_node.x, source_node.y - 40, 0.0)
                                       ]
            else:
                edge.control_points = []
        elif rendering_type == "curved":
            if is_self_loop:
                # Single control point for self-loop - create a curved loop - use 3D coordinates
                edge.control_points = [(source_node.x + 30, source_node.y - 50,
                                        0.0)]
            else:
                # Single control point for quadratic curve - use 3D coordinates
                mid_x = (source_node.x + target_node.x) / 2
                mid_y = (source_node.y + target_node.y) / 2
                # Offset perpendicular to the line
                length = max(1, math.sqrt(dx * dx + dy * dy))
                offset = length * 0.25
                perp_x = -dy / length * offset
                perp_y = dx / length * offset
                edge.control_points = [(mid_x + perp_x, mid_y + perp_y, 0.0)]
        elif rendering_type == "bezier":
            if is_self_loop:
                # Two control points for self-loop bezier - create a nice loop shape - use 3D coordinates
                edge.control_points = [
                    (source_node.x + 40, source_node.y - 30,
                     0.0),  # First control point
                    (source_node.x - 40, source_node.y - 30, 0.0
                     )  # Second control point
                ]
            else:
                # Start with 0 control points - user can add them manually
                edge.control_points = []
        elif rendering_type == "cubic_spline":
            if is_self_loop:
                # Three control points for self-loop cubic spline - create a flowing loop - use 3D coordinates
                edge.control_points = [
                    (source_node.x + 50, source_node.y - 20,
                     0.0),  # Right and up
                    (source_node.x + 20, source_node.y - 60, 0.0),  # Above
                    (source_node.x - 30, source_node.y - 20, 0.0
                     )  # Left and up
                ]
            else:
                # Start with 0 control points - user can add them manually
                edge.control_points = []
        elif rendering_type == "nurbs":
            if is_self_loop:
                # Four control points for self-loop NURBS - create a complex loop - use 3D coordinates
                edge.control_points = [
                    (source_node.x + 60, source_node.y - 10, 0.0),  # Right
                    (source_node.x + 40, source_node.y - 70, 0.0),  # Up-right
                    (source_node.x - 40, source_node.y - 70, 0.0),  # Up-left
                    (source_node.x - 60, source_node.y - 10, 0.0)  # Left
                ]
            else:
                # Start with 0 control points - user can add them manually
                edge.control_points = []
        elif rendering_type == "bspline":
            if is_self_loop:
                # Two intermediate control points for self-loop B-spline - use 3D coordinates
                edge.control_points = [
                    (source_node.x + 35, source_node.y - 45, 0.0),  # Up-right
                    (source_node.x - 35, source_node.y - 45, 0.0)  # Up-left
                ]
            else:
                # Start with 0 control points - user can add them manually
                edge.control_points = []
        elif rendering_type == "polyline":
            if is_self_loop:
                # Multiple control points for self-loop polyline - create a zigzag loop - use 3D coordinates
                edge.control_points = [
                    (source_node.x + 30, source_node.y - 25, 0.0),  # Right-up
                    (source_node.x + 10, source_node.y - 55, 0.0),  # Center-up
                    (source_node.x - 30, source_node.y - 25, 0.0)  # Left-up
                ]
            else:
                # Start with 0 control points - user can add them manually
                edge.control_points = []
        elif rendering_type == "composite":
            # No regular control points for composite curves - control is through segments
            edge.control_points = []
            # Initialize composite segments if not already set
            if not getattr(edge, 'is_composite', False):
                edge.is_composite = True
            if not getattr(edge, 'curve_segments', None):
                # Initialize with absolute world coordinates
                cp1_x = source_node.x + dx * 0.3
                cp1_y = source_node.y + dy * 0.3 - 30
                cp2_x = source_node.x + dx * 0.7
                cp2_y = source_node.y + dy * 0.7 + 30
                edge.curve_segments = [{
                    "type":
                    "bezier",
                    "control_points": [(cp1_x, cp1_y), (cp2_x, cp2_y)],
                    "weight":
                    1.0
                }]

        edge.custom_position = len(edge.control_points) > 0
        print(
            f"DEBUG: 🎛️ Initialized {len(edge.control_points)} control points for edge {edge.id} (type: {rendering_type}): {edge.control_points}"
        )

    # Removed duplicate function - the real implementation is below

    def get_control_point_at_position(self, screen_x, screen_y):
        """Check if position is over a control point. Returns (edge, control_point_index) or None."""

        if not self.control_points_enabled:
            print(
                f"DEBUG: 🎛️ Control points disabled, not checking hit detection"
            )
            return None

        control_radius = max(10, int(
            8 * self.zoom))  # Increased radius and better scaling
        print(
            f"DEBUG: 🎛️ Hit testing control points at screen({screen_x}, {screen_y}) with radius {control_radius}"
        )

        # Apply inverse rotation to get coordinates in the same space as drawing
        test_x, test_y = screen_x, screen_y

        try:
            if self.world_rotation != 0.0:
                size = self.GetSize()
                center_x = size.width // 2
                center_y = size.height // 2

                rotation_rad = -math.radians(
                    self.world_rotation)  # Negative for inverse
                cos_angle = math.cos(rotation_rad)
                sin_angle = math.sin(rotation_rad)

                temp_x = screen_x - center_x
                temp_y = screen_y - center_y

                test_x = temp_x * cos_angle - temp_y * sin_angle + center_x
                test_y = temp_x * sin_angle + temp_y * cos_angle + center_y

            # If a specific ubergraph segment is selected, check that segment's control points first
            try:
                if getattr(self, 'selected_uber_segment_kind', None) and getattr(self, 'selected_uber_segment_edge_id', None):
                    sedge = self.graph.get_edge(self.selected_uber_segment_edge_id)
                    if sedge and getattr(sedge, 'is_hyperedge', False) and getattr(sedge, 'hyperedge_visualization', '') == 'ubergraph':
                        cp_list = []
                        if self.selected_uber_segment_kind == 'node' and getattr(self, 'selected_uber_segment_node_id', None):
                            cp_map = (sedge.metadata or {}).get('segment_cp_nodes', {}) if hasattr(sedge, 'metadata') else {}
                            cp_list = cp_map.get(str(self.selected_uber_segment_node_id), []) or []
                        elif self.selected_uber_segment_kind == 'edge' and getattr(self, 'selected_uber_segment_other_edge_id', None):
                            cp_map = (sedge.metadata or {}).get('segment_cp_edges', {}) if hasattr(sedge, 'metadata') else {}
                            cp_list = cp_map.get(str(self.selected_uber_segment_other_edge_id), []) or []
                        for i, cp in enumerate(cp_list):
                            cp_screen = self.world_to_screen(cp[0], cp[1])
                            dist = math.sqrt((test_x - cp_screen[0])**2 + (test_y - cp_screen[1])**2)
                            if dist <= control_radius:
                                return (sedge, i)
            except Exception:
                pass

            # Check each edge's control points
            for edge in self.graph.get_all_edges():
                if not edge.selected or not hasattr(edge, 'control_points'):
                    continue

                for i, control_point in enumerate(edge.control_points):
                    if not control_point:
                        continue

                    screen_pos = self.world_to_screen(control_point[0],
                                                      control_point[1])
                    distance = math.sqrt((test_x - screen_pos[0])**2 +
                                         (test_y - screen_pos[1])**2)

                    if distance <= control_radius:
                        print(
                            f"DEBUG: 🎛️ Hit control point {i} of edge {edge.id} at distance {distance:.1f}"
                        )
                        return (edge, i)

            return None

        except Exception as e:
            print(f"DEBUG: 🎛️ Error in control point hit detection: {e}")
            return None

        for edge in self.graph.get_all_edges():
            if not edge.selected:
                continue

            # Get the appropriate control points for this edge type
            control_points_to_check = []
            rendering_type = edge.rendering_type if edge.rendering_type else self.edge_rendering_type
            print(
                f"DEBUG: 🎛️ Checking edge {edge.id} (type: {rendering_type})")

            if rendering_type == "composite" and getattr(
                    edge, 'is_composite', False):
                # For composite curves, check control points of the currently selected segment
                segment_index = getattr(self, 'current_composite_segment', 0)
                if hasattr(edge, 'curve_segments') and segment_index < len(
                        edge.curve_segments):
                    segment = edge.curve_segments[segment_index]
                    control_points_to_check = segment.get("control_points", [])
                    print(
                        f"DEBUG: 🔗 Hit testing {len(control_points_to_check)} composite segment {segment_index} control points"
                    )
                    for i, cp in enumerate(control_points_to_check):
                        cp_screen = self.world_to_screen(cp[0], cp[1])
                        dist = math.sqrt((test_x - cp_screen[0])**2 +
                                         (test_y - cp_screen[1])**2)
                        print(
                            f"DEBUG: 🔗 Composite CP {i}: world({cp[0]:.1f}, {cp[1]:.1f}) -> screen({cp_screen[0]:.1f}, {cp_screen[1]:.1f}), distance: {dist:.1f}"
                        )
                        if dist <= control_radius:
                            print(
                                f"DEBUG: 🎛️ ✅ HIT composite control point {i} of edge {edge.id}"
                            )
                            return (edge, i)
            else:
                # For regular curves, use the edge's control points
                control_points_to_check = edge.control_points if hasattr(
                    edge, 'control_points') else []
                print(
                    f"DEBUG: 🎛️ Edge {edge.id} has {len(control_points_to_check)} control points: {control_points_to_check}"
                )

                for i, control_point in enumerate(control_points_to_check):
                    screen_pos = self.world_to_screen(control_point[0],
                                                      control_point[1])

                    # Check if mouse is within control point bounds (using inverse-rotated coordinates)
                    dx = test_x - screen_pos[0]
                    dy = test_y - screen_pos[1]
                    distance = math.sqrt(dx * dx + dy * dy)

                    print(
                        f"DEBUG: 🎛️ CP {i}: world({control_point[0]:.1f}, {control_point[1]:.1f}) -> screen({screen_pos[0]:.1f}, {screen_pos[1]:.1f}), distance: {distance:.1f}"
                    )

                    if distance <= control_radius:
                        print(
                            f"DEBUG: 🎛️ ✅ HIT control point {i} of {rendering_type} edge {edge.id} at distance {distance:.1f}"
                        )
                        return (edge, i)

        print(f"DEBUG: 🎛️ ❌ No control point hit found")
        return None

    def get_arrow_position_control_at_position(self, screen_x, screen_y):
        """Check if position is over an arrow position control dot. Returns edge or None."""

        if not self.control_points_enabled:
            return None

        control_radius = max(8, int(6 * self.zoom))

        # Apply inverse rotation to get coordinates in the same space as drawing
        test_x, test_y = screen_x, screen_y
        if self.world_rotation != 0.0:
            size = self.GetSize()
            center_x = size.width // 2
            center_y = size.height // 2

            rotation_rad = -math.radians(
                self.world_rotation)  # Negative for inverse
            cos_angle = math.cos(rotation_rad)
            sin_angle = math.sin(rotation_rad)

            temp_x = screen_x - center_x
            temp_y = screen_y - center_y

            test_x = temp_x * cos_angle - temp_y * sin_angle + center_x
            test_y = temp_x * sin_angle + temp_y * cos_angle + center_y

        for edge in self.graph.get_all_edges():
            if not edge.selected:
                continue

            source_node = self.graph.get_node(edge.source_id)
            target_node = self.graph.get_node(edge.target_id)

            if not source_node or not target_node:
                continue

            # Get screen positions
            source_screen = self.world_to_screen(source_node.x, source_node.y)
            target_screen = self.world_to_screen(target_node.x, target_node.y)

            # Calculate adjusted edge endpoints (same as in draw_edge)
            source_adjusted = self.calculate_line_endpoint(
                source_node, target_node, source_screen, target_screen, True,
                edge)
            target_adjusted = self.calculate_line_endpoint(
                target_node, source_node, target_screen, source_screen, False,
                edge)

            if edge.is_hyperedge and getattr(edge, 'hyperedge_visualization',
                                             '') == 'ubergraph':
                # 1) Hit-test yellow dots on uberedge↔node segments
                try:
                    tmap = (edge.metadata
                            or {}).get('arrow_pos_nodes', {}) if hasattr(
                                edge, 'metadata') else {}
                except Exception:
                    tmap = {}
                # Build list of node ids connected
                node_ids = []
                if getattr(edge, 'source_id', None):
                    node_ids.append(edge.source_id)
                for nid in getattr(edge, 'source_ids', []) or []:
                    node_ids.append(nid)
                if getattr(edge, 'target_id', None):
                    node_ids.append(edge.target_id)
                for nid in getattr(edge, 'target_ids', []) or []:
                    node_ids.append(nid)
                # Test each node segment
                ex, ey = self.world_to_screen(edge.uber_x, edge.uber_y)
                for nid in node_ids:
                    node = self.graph.get_node(nid)
                    if not node:
                        continue
                    nx, ny = self.world_to_screen(node.x, node.y)
                    t_val = float(tmap.get(str(nid), 0.5)) if tmap else 0.5
                    t_val = max(0.0, min(1.0, t_val))
                    dot_x = ex + (nx - ex) * t_val
                    dot_y = ey + (ny - ey) * t_val
                    dxp = test_x - dot_x
                    dyp = test_y - dot_y
                    if math.hypot(dxp, dyp) <= control_radius:
                        # Store drag context and return the edge
                        self.dragging_arrow_position_kind = 'node'
                        self.dragging_arrow_node_id = nid
                        self.dragging_arrow_other_edge_id = None
                        return edge
                # 2) Hit-test yellow dots on uberedge↔uberedge link segments
                try:
                    explicit_list = list((edge.metadata or {}).get(
                        'connected_uberedges', [])) if hasattr(
                            edge, 'metadata') else []
                    tmap_edges = (edge.metadata or {}).get(
                        'arrow_pos_edges', {}) if hasattr(edge,
                                                          'metadata') else {}
                except Exception:
                    explicit_list = []
                    tmap_edges = {}
                for target_edge_id in explicit_list:
                    other = self.graph.get_edge(target_edge_id) if hasattr(
                        self.graph, 'get_edge') else None
                    if not other or not other.is_hyperedge:
                        continue
                    ox, oy = self.world_to_screen(other.uber_x, other.uber_y)
                    t_val = float(tmap_edges.get(str(target_edge_id),
                                                 0.5)) if tmap_edges else 0.5
                    t_val = max(0.0, min(1.0, t_val))
                    dot_x = ex + (ox - ex) * t_val
                    dot_y = ey + (oy - ey) * t_val
                    dxp = test_x - dot_x
                    dyp = test_y - dot_y
                    if math.hypot(dxp, dyp) <= control_radius:
                        self.dragging_arrow_position_kind = 'edge'
                        self.dragging_arrow_node_id = None
                        self.dragging_arrow_other_edge_id = target_edge_id
                        return edge
                # 3) TODO: self-loop ellipse handle (optional)
                continue
            elif edge.is_hyperedge:
                # Calculate arrow position based on the main segment (non-ubergraph)
                dx = target_adjusted[0] - source_adjusted[0]
                dy = target_adjusted[1] - source_adjusted[1]
                from_x = source_adjusted[0] + dx * edge.from_connection_point
                from_y = source_adjusted[1] + dy * edge.from_connection_point
                to_x = source_adjusted[0] + dx * edge.to_connection_point
                to_y = source_adjusted[1] + dy * edge.to_connection_point
                segment_dx = to_x - from_x
                segment_dy = to_y - from_y
                arrow_x = from_x + segment_dx * edge.arrow_position
                arrow_y = from_y + segment_dy * edge.arrow_position
            else:
                # Calculate arrow position for regular edge
                dx = target_adjusted[0] - source_adjusted[0]
                dy = target_adjusted[1] - source_adjusted[1]
                arrow_x = source_adjusted[0] + dx * edge.arrow_position
                arrow_y = source_adjusted[1] + dy * edge.arrow_position

            # Check if mouse is within control point bounds (using inverse-rotated coordinates)
            dx = test_x - arrow_x
            dy = test_y - arrow_y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance <= control_radius:
                # For non-ubergraph cases, simple return
                self.dragging_arrow_position_kind = 'main'
                self.dragging_arrow_node_id = None
                self.dragging_arrow_other_edge_id = None
                return edge

        return None

    def calculate_curve_tangent_at_target(self, edge, source_node,
                                          target_node):
        """Calculate the tangent direction at the target point for curved edges."""

        if not edge.control_points:
            # Fallback to straight line direction
            return target_node.x - source_node.x, target_node.y - source_node.y

        # Use edge-specific rendering type if set, otherwise use global
        rendering_type = edge.rendering_type if edge.rendering_type else self.edge_rendering_type

        try:
            if rendering_type == "curved" and len(edge.control_points) >= 1:
                # Quadratic Bézier tangent at t=1: 2(1-t)(P₁-P₀) + 2t(P₂-P₁) = 2(P₂-P₁) at t=1
                control_point = edge.control_points[0]
                dx = target_node.x - control_point[0]
                dy = target_node.y - control_point[1]
                return dx, dy

            elif rendering_type in ["bezier", "cubic_spline", "nurbs"] and len(
                    edge.control_points) >= 2:
                # Cubic Bézier tangent at t=1: 3(P₃-P₂)
                control_point = edge.control_points[-1]  # Last control point
                dx = target_node.x - control_point[0]
                dy = target_node.y - control_point[1]
                return dx, dy

            elif rendering_type == "bspline" and len(edge.control_points) >= 1:
                # B-spline tangent approximation using last control point
                control_point = edge.control_points[-1]
                dx = target_node.x - control_point[0]
                dy = target_node.y - control_point[1]
                return dx, dy

            elif rendering_type == "polyline" and len(
                    edge.control_points) >= 1:
                # Use direction from last control point to target
                control_point = edge.control_points[-1]
                dx = target_node.x - control_point[0]
                dy = target_node.y - control_point[1]
                return dx, dy
        except (IndexError, TypeError, ValueError) as e:
            print(
                f"DEBUG: ⚠️ Error calculating curve tangent at target: {e}, using fallback"
            )

            # Fallback to straight line direction
            return target_node.x - source_node.x, target_node.y - source_node.y

    def calculate_curve_tangent_at_position(self, edge, source_node,
                                            target_node, t):
        """Calculate the tangent direction at any position t along the curve."""

        rendering_type = edge.rendering_type if edge.rendering_type else self.edge_rendering_type
        print(
            f"DEBUG: 🧭 Calculating tangent for {rendering_type} edge {edge.id} at t={t:.3f}"
        )

        if rendering_type == "straight" or not edge.control_points:
            # Constant direction for straight lines
            dx, dy = target_node.x - source_node.x, target_node.y - source_node.y
            print(f"DEBUG: 🧭 Straight line tangent: ({dx:.2f}, {dy:.2f})")
            return dx, dy

        elif rendering_type == "curved":
            # Quadratic Bézier derivative: B'(t) = 2(1-t)(P₁-P₀) + 2t(P₂-P₁)
            if (hasattr(edge, 'control_points') and edge.control_points
                    and isinstance(edge.control_points, list)
                    and len(edge.control_points) >= 1):
                try:
                    cp = edge.control_points[0]
                    cp_x, cp_y = cp[0], cp[1]
                    dx = 2 * (1 - t) * (cp_x - source_node.x) + 2 * t * (
                        target_node.x - cp_x)
                    dy = 2 * (1 - t) * (cp_y - source_node.y) + 2 * t * (
                        target_node.y - cp_y)
                    print(
                        f"DEBUG: 🧭 Curved tangent using CP({cp_x:.1f}, {cp_y:.1f}): ({dx:.2f}, {dy:.2f})"
                    )
                    return dx, dy
                except (IndexError, TypeError, ValueError) as e:
                    print(
                        f"DEBUG: ⚠️ Error accessing curved control point: {e}, falling back to straight line"
                    )

                    # Fallback to straight line if no valid control point
                    print(
                        f"DEBUG: 🧭 Curved edge has no valid control points, using straight line tangent"
                    )
                    dx, dy = target_node.x - source_node.x, target_node.y - source_node.y
                    print(
                        f"DEBUG: 🧭 Straight line fallback tangent: ({dx:.2f}, {dy:.2f})"
                    )
            return dx, dy

        elif rendering_type in ["bezier", "cubic_spline", "nurbs"]:
            # Use actual control points for tangent calculation if available
            if (hasattr(edge, 'control_points') and edge.control_points
                    and isinstance(edge.control_points, list)
                    and len(edge.control_points) >= 2):
                try:
                    ctrl1_x, ctrl1_y = edge.control_points[0][
                        0], edge.control_points[0][1]
                    ctrl2_x, ctrl2_y = edge.control_points[1][
                        0], edge.control_points[1][1]
                    print(
                        f"DEBUG: 🧭 Using actual control points: CP1({ctrl1_x:.1f}, {ctrl1_y:.1f}), CP2({ctrl2_x:.1f}, {ctrl2_y:.1f})"
                    )
                except (IndexError, TypeError, ValueError) as e:
                    print(
                        f"DEBUG: ⚠️ Error accessing control points: {e}, falling back to defaults"
                    )
                    # Fallback to default control points
                    dx = target_node.x - source_node.x
                    dy = target_node.y - source_node.y
                    ctrl1_x = source_node.x + dx * 0.3
                    ctrl1_y = source_node.y + dy * 0.3 - 30
                    ctrl2_x = source_node.x + dx * 0.7
                    ctrl2_y = source_node.y + dy * 0.7 + 30
            else:
                # Fallback to default control points when insufficient control points
                print(
                    f"DEBUG: 🧭 Insufficient control points (has {len(edge.control_points) if hasattr(edge, 'control_points') and edge.control_points else 0}), using defaults"
                )
                dx = target_node.x - source_node.x
                dy = target_node.y - source_node.y
                ctrl1_x = source_node.x + dx * 0.3
                ctrl1_y = source_node.y + dy * 0.3 - 30
                ctrl2_x = source_node.x + dx * 0.7
                ctrl2_y = source_node.y + dy * 0.7 + 30

            # Cubic Bézier derivative: B'(t) = 3(1-t)²(P₁-P₀) + 6(1-t)t(P₂-P₁) + 3t²(P₃-P₂)
            dx = (3 * (1 - t)**2 * (ctrl1_x - source_node.x) + 6 *
                  (1 - t) * t * (ctrl2_x - ctrl1_x) + 3 * t**2 *
                  (target_node.x - ctrl2_x))
            dy = (3 * (1 - t)**2 * (ctrl1_y - source_node.y) + 6 *
                  (1 - t) * t * (ctrl2_y - ctrl1_y) + 3 * t**2 *
                  (target_node.y - ctrl2_y))
            print(
                f"DEBUG: 🧭 {rendering_type} tangent using CPs({ctrl1_x:.1f}, {ctrl1_y:.1f}), ({ctrl2_x:.1f}, {ctrl2_y:.1f}): ({dx:.2f}, {dy:.2f})"
            )
            return dx, dy

        elif rendering_type == "bspline":
            # For B-spline, approximate tangent by sampling nearby points
            epsilon = 0.01
            t1 = max(0, t - epsilon)
            t2 = min(1, t + epsilon)

            p1 = self.calculate_position_on_curve(edge, source_node,
                                                  target_node, t1)
            p2 = self.calculate_position_on_curve(edge, source_node,
                                                  target_node, t2)

            if p1 and p2:
                return p2[0] - p1[0], p2[1] - p1[1]
            else:
                return target_node.x - source_node.x, target_node.y - source_node.y

        elif rendering_type == "polyline":
            # For polyline, calculate direction of the current segment
            if edge.control_points:
                # Create points list: source -> control points -> target
                points = [
                    (source_node.x, source_node.y)
                ] + edge.control_points + [(target_node.x, target_node.y)]
                total_segments = len(points) - 1

                # Find which segment we're on
                segment_t = t * total_segments
                segment_index = min(int(segment_t), total_segments - 1)
                local_t = segment_t - segment_index

                # Get segment start and end points
                if segment_index < len(points) - 1:
                    start_point = points[segment_index]
                    end_point = points[segment_index + 1]

                    # Direction for this specific segment
                    dx = end_point[0] - start_point[0]
                    dy = end_point[1] - start_point[1]
                    return dx, dy

            # Fallback to overall direction
            return target_node.x - source_node.x, target_node.y - source_node.y

        elif rendering_type == "composite" or getattr(edge, 'is_composite',
                                                      False):
            # For composite curves, approximate tangent by sampling nearby points
            epsilon = 0.01
            t1 = max(0, t - epsilon)
            t2 = min(1, t + epsilon)

            p1 = self.calculate_position_on_curve(edge, source_node,
                                                  target_node, t1)
            p2 = self.calculate_position_on_curve(edge, source_node,
                                                  target_node, t2)

            if p1 and p2:
                return p2[0] - p1[0], p2[1] - p1[1]
            else:
                return target_node.x - source_node.x, target_node.y - source_node.y

        else:
            # Fallback to straight line direction
            return target_node.x - source_node.x, target_node.y - source_node.y

    def set_edge_curve_type(self, edge, curve_type):
        """Set the curve type for a specific edge."""

        edge.rendering_type = curve_type

        # Only clear existing control points if the user hasn't manually added any
        # or if switching to a curve type that requires specific initialization
        preserve_custom = getattr(edge, 'custom_position', False)
        requires_specific_init = curve_type in [
            "curved"
        ]  # Only arcs require specific control points

        if not preserve_custom or requires_specific_init:
            print(
                f"DEBUG: 🔄 Clearing control points for curve type change to {curve_type} (preserve_custom: {preserve_custom}, requires_specific: {requires_specific_init})"
            )
        edge.control_points = []
        edge.custom_position = False

        # Immediately regenerate control points for the new type
        source_node = self.graph.get_node(edge.source_id)
        target_node = self.graph.get_node(edge.target_id)
        if source_node and target_node:
            self.initialize_control_points(edge, source_node, target_node)
        else:
            print(
                f"DEBUG: 🔄 PRESERVING {len(edge.control_points)} custom control points when changing to {curve_type}"
            )
            print(
                f"DEBUG: 🎛️ Re-initialized control points for edge {edge.id} with type {curve_type}: {edge.control_points}"
            )

        # Emit signals and refresh
        self.graph_modified.emit()
        self.Refresh()

    def enter_bspline_editing_mode(self, edge):
        """Enter B-spline editing mode for the specified edge."""

        if edge.rendering_type != "bspline" and self.edge_rendering_type != "bspline":
            return

        self.bspline_editing_mode = True
        self.bspline_editing_edge = edge
        self.adding_bspline_control_point = False
        print(f"DEBUG: 🌊 Entered B-spline editing mode for edge {edge.id}")
        self.Refresh()

    def exit_bspline_editing_mode(self):
        """Exit B-spline editing mode."""

        self.bspline_editing_mode = False
        self.bspline_editing_edge = None
        self.adding_bspline_control_point = False
        print(f"DEBUG: 🌊 Exited B-spline editing mode")
        self.Refresh()

    def add_curve_control_point(self, world_x, world_y, insert_index=None):
        """Add a new control point to the current curve (B-spline or Bézier) at the specified position."""

        print(
            f"DEBUG: 🌊 add_curve_control_point called with ({world_x}, {world_y}), editing_edge = {self.bspline_editing_edge}"
        )
        if not self.bspline_editing_edge:  # Using same variable for both curve types
            print(f"DEBUG: 🌊 No bspline_editing_edge set - returning early")
            return

        # Check if control_points is initialized
        if not hasattr(self.bspline_editing_edge, 'control_points'):
            print(
                f"DEBUG: 🌊 Edge {self.bspline_editing_edge.id} has no control_points attribute - initializing"
            )
            self.bspline_editing_edge.control_points = []

        print(
            f"DEBUG: 🌊 Edge {self.bspline_editing_edge.id} currently has {len(self.bspline_editing_edge.control_points)} control points"
        )

        if insert_index is None:
            # Add at the end - use 3D coordinates (x, y, z) as expected by Edge model
            self.bspline_editing_edge.control_points.append(
                (world_x, world_y, 0.0))
            print(f"DEBUG: 🌊 Appended control point to end")
        else:
            # Insert at specific position - use 3D coordinates (x, y, z) as expected by Edge model
            self.bspline_editing_edge.control_points.insert(
                insert_index, (world_x, world_y, 0.0))

        self.bspline_editing_edge.custom_position = True

        # Get curve type for logging
        curve_type = getattr(self.bspline_editing_edge, 'rendering_type',
                             None) or self.edge_rendering_type
        print(
            f"DEBUG: 🌊 Added {curve_type} control point at ({world_x:.1f}, {world_y:.1f})"
        )
        print(
            f"DEBUG: 🌊 {curve_type} now has {len(self.bspline_editing_edge.control_points)} control points"
        )

        self.graph_modified.emit()
        # Update the main window's curve list if it exists
        print(f"DEBUG: 🌊 Triggering UI update after adding control point")
        if hasattr(self.GetParent(), 'update_curve_list'):
            print(f"DEBUG: 🌊 Calling update_curve_list")
            wx.CallAfter(self.GetParent().update_curve_list)
        elif hasattr(self.GetParent(),
                     'update_bspline_list'):  # Fallback for compatibility
            print(f"DEBUG: 🌊 Calling update_bspline_list")
            wx.CallAfter(self.GetParent().update_bspline_list)
        self.Refresh()

    def add_bspline_control_point(self, world_x, world_y, insert_index=None):
        """Legacy method - forwards to add_curve_control_point for compatibility."""

        return self.add_curve_control_point(world_x, world_y, insert_index)

    def delete_bspline_control_point(self, index):
        """Delete a control point from the B-spline."""

        if not self.bspline_editing_edge or index < 0 or index >= len(
                self.bspline_editing_edge.control_points):
            return

        deleted_point = self.bspline_editing_edge.control_points.pop(index)
        self.bspline_editing_edge.custom_position = True
        print(
            f"DEBUG: 🌊 Deleted B-spline control point at index {index}: {deleted_point}"
        )
        self.graph_modified.emit()
        # Update the main window's B-spline list if it exists
        if hasattr(self.GetParent(), 'update_bspline_list'):
            wx.CallAfter(self.GetParent().update_bspline_list)
        self.Refresh()

    def move_bspline_control_point(self, from_index, to_index):
        """Reorder a B-spline control point."""

        if not self.bspline_editing_edge or from_index < 0 or to_index < 0:
            return
        if from_index >= len(
                self.bspline_editing_edge.control_points) or to_index >= len(
                    self.bspline_editing_edge.control_points):
            return

        # Move the control point
        control_point = self.bspline_editing_edge.control_points.pop(
            from_index)
        self.bspline_editing_edge.control_points.insert(
            to_index, control_point)
        self.bspline_editing_edge.custom_position = True
        print(
            f"DEBUG: 🌊 Moved B-spline control point from index {from_index} to {to_index}"
        )
        self.graph_modified.emit()
        # Update the main window's B-spline list if it exists
        if hasattr(self.GetParent(), 'update_bspline_list'):
            wx.CallAfter(self.GetParent().update_bspline_list)
        self.Refresh()

    def start_adding_bspline_control_point(self):
        """Start the mode for adding B-spline control points by clicking."""

        if not self.bspline_editing_edge:
            return

        self.adding_bspline_control_point = True
        print(
            f"DEBUG: 🌊 Started adding B-spline control point mode - click to add points"
        )
        # Change cursor to indicate adding mode
        self.SetCursor(wx.Cursor(wx.CURSOR_CROSS))

    def show_bspline_control_points_dialog(self, edge):
        """Show a dialog to list and manage B-spline control points."""

        if not edge or not edge.control_points:
            wx.MessageBox("No control points to display.",
                          "B-spline Control Points",
                          wx.OK | wx.ICON_INFORMATION)
            return

        # Create a simple dialog showing control points
        dialog = wx.Dialog(self,
                           title=f"B-spline Control Points (Edge {edge.id})",
                           size=(400, 300))
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Instructions
        instructions = wx.StaticText(
            dialog,
            label="Control Points (excluding source and target nodes):")
        sizer.Add(instructions, 0, wx.ALL, 10)

        # List control points
        list_ctrl = wx.ListCtrl(dialog, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        list_ctrl.AppendColumn("Index", width=60)
        list_ctrl.AppendColumn("X", width=100)
        list_ctrl.AppendColumn("Y", width=100)
        list_ctrl.AppendColumn("Actions", width=100)

        for i, (x, y) in enumerate(edge.control_points):
            index = list_ctrl.InsertItem(i, str(i))
            list_ctrl.SetItem(index, 1, f"{x:.1f}")
            list_ctrl.SetItem(index, 2, f"{y:.1f}")
            list_ctrl.SetItem(index, 3, "Edit/Delete")

        sizer.Add(list_ctrl, 1, wx.EXPAND | wx.ALL, 10)

        # Buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        add_btn = wx.Button(dialog, label="Add Point")
        delete_btn = wx.Button(dialog, label="Delete Selected")
        close_btn = wx.Button(dialog, wx.ID_CLOSE, "Close")

        button_sizer.Add(add_btn, 0, wx.ALL, 5)
        button_sizer.Add(delete_btn, 0, wx.ALL, 5)
        button_sizer.Add(close_btn, 0, wx.ALL, 5)

        sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        def on_add_point(evt):
            # Simple dialog to get coordinates
            coord_dialog = wx.TextEntryDialog(dialog,
                                              "Enter coordinates (x,y):",
                                              "Add Control Point", "0,0")
            if coord_dialog.ShowModal() == wx.ID_OK:
                try:
                    coords = coord_dialog.GetValue().split(',')
                    if len(coords) == 2:
                        x, y = float(coords[0].strip()), float(
                            coords[1].strip())
                        self.add_curve_control_point(x, y)
                        dialog.EndModal(wx.ID_OK)  # Close dialog to refresh
                except ValueError:
                    wx.MessageBox("Invalid coordinates format. Use: x,y",
                                  "Error", wx.OK | wx.ICON_ERROR)
            coord_dialog.Destroy()

        def on_delete_point(evt):
            selected = list_ctrl.GetFirstSelected()
            if selected >= 0:
                self.delete_bspline_control_point(selected)
                dialog.EndModal(wx.ID_OK)  # Close dialog to refresh
            else:
                wx.MessageBox("Please select a control point to delete.",
                              "No Selection", wx.OK | wx.ICON_WARNING)

        add_btn.Bind(wx.EVT_BUTTON, on_add_point)
        delete_btn.Bind(wx.EVT_BUTTON, on_delete_point)
        close_btn.Bind(wx.EVT_BUTTON, lambda evt: dialog.EndModal(wx.ID_CLOSE))

        dialog.SetSizer(sizer)
        dialog.ShowModal()
        dialog.Destroy()

    def calculate_position_on_curve(self, edge, source_node, target_node, t):
        """Calculate position along curve at parameter t (0.0 = source, 1.0 = target)."""

        rendering_type = edge.rendering_type if edge.rendering_type else self.edge_rendering_type

        # Determine connection-point anchors (not node centers) for endpoints
        try:
            if hasattr(self, 'get_edge_anchor_endpoints_world'):
                src_anchor, tgt_anchor = self.get_edge_anchor_endpoints_world(
                    edge, source_node, target_node)
                src_x, src_y = src_anchor
                tgt_x, tgt_y = tgt_anchor
            else:
                # Fallback: compute adjusted endpoints in screen space and convert back to world
                src_screen = self.world_to_screen(source_node.x, source_node.y)
                tgt_screen = self.world_to_screen(target_node.x, target_node.y)
                src_adj = self.calculate_line_endpoint(source_node,
                                                       target_node, src_screen,
                                                       tgt_screen, True, edge)
                tgt_adj = self.calculate_line_endpoint(target_node,
                                                       source_node, tgt_screen,
                                                       src_screen, False, edge)
                src_x, src_y = self.screen_to_world(src_adj[0], src_adj[1])
                tgt_x, tgt_y = self.screen_to_world(tgt_adj[0], tgt_adj[1])
        except Exception:
            src_x, src_y = source_node.x, source_node.y
            tgt_x, tgt_y = target_node.x, target_node.y

        # Initialize control points if they don't exist (but preserve user preference for 0 control points)
        if not hasattr(edge, 'control_points'):
            edge.control_points = []

        # Don't auto-initialize control points - let curves start with 0 and user can add them
        # Only initialize if explicitly needed for specific curve types that require control points
        needs_init = (
            (rendering_type == "curved" and len(edge.control_points) == 0)
            or  # Arcs need 1 control point
            (source_node.id == target_node.id and len(edge.control_points) == 0
             )  # Self-loops need control points
        )
        if needs_init:
            print(
                f"DEBUG: 🎛️ Auto-initializing control points for {rendering_type} edge (self-loop: {source_node.id == target_node.id})"
            )
            self.initialize_control_points(edge, source_node, target_node)

        if rendering_type == "straight":
            # Linear interpolation between connection anchors
            x = src_x + t * (tgt_x - src_x)
            y = src_y + t * (tgt_y - src_y)
            return (x, y)

        elif rendering_type == "curved":
            # For curved edges, use control point if available, otherwise calculate default
            if edge.control_points and len(edge.control_points) >= 1:
                cp = edge.control_points[0]
            else:
                # Calculate default control point
                dx = tgt_x - src_x
                dy = tgt_y - src_y
                length = max(1, math.sqrt(dx * dx + dy * dy))
                offset = length * 0.25
                perp_x = -dy / length * offset
                perp_y = dx / length * offset
                mid_x = (src_x + tgt_x) / 2
                mid_y = (src_y + tgt_y) / 2
                cp = (mid_x + perp_x, mid_y + perp_y)
            # Quadratic Bézier evaluation: B(t) = (1-t)²P₀ + 2(1-t)tP₁ + t²P₂
            x = (1 - t)**2 * src_x + 2 * (1 - t) * t * cp[0] + t**2 * tgt_x
            y = (1 - t)**2 * src_y + 2 * (1 - t) * t * cp[1] + t**2 * tgt_y
            return (x, y)

        elif rendering_type == "bezier":
            # For Bézier curves, use the new multi-point evaluation
            if edge.control_points and len(edge.control_points) >= 1:
                control_points = [(src_x, src_y)
                                  ] + edge.control_points + [(tgt_x, tgt_y)]
            else:
                # Calculate default control points for cubic Bézier
                dx = tgt_x - src_x
                dy = tgt_y - src_y
                ctrl1 = (src_x + dx * 0.3, src_y + dy * 0.3 - 30)
                ctrl2 = (src_x + dx * 0.7, src_y + dy * 0.7 + 30)
                control_points = [(src_x, src_y), ctrl1, ctrl2, (tgt_x, tgt_y)]

            return self.evaluate_bezier_curve(control_points, t)

        elif rendering_type == "cubic_spline":
            # For cubic splines, use interpolating spline through all control points
            if (hasattr(edge, 'control_points') and edge.control_points
                    and isinstance(edge.control_points, list)
                    and len(edge.control_points) >= 1):
                try:
                    # Create points list: anchors -> control points -> anchor
                    points = [(src_x, src_y)
                              ] + edge.control_points + [(tgt_x, tgt_y)]
                    return self.evaluate_interpolating_spline(points, t)
                except (IndexError, TypeError, ValueError) as e:
                    print(
                        f"DEBUG: ⚠️ Error evaluating cubic spline position: {e}, using linear interpolation"
                    )

                # Fallback to linear interpolation
                x = src_x + t * (tgt_x - src_x)
                y = src_y + t * (tgt_y - src_y)
                return (x, y)

        elif rendering_type == "freeform":
            # For freeform edges, interpolate along the path points
            if edge.freeform_points and len(edge.freeform_points) >= 2:
                # Calculate total path length and segment lengths
                total_length = 0
                segment_lengths = []
                for i in range(len(edge.freeform_points) - 1):
                    p1 = edge.freeform_points[i]
                    p2 = edge.freeform_points[i + 1]
                    dx = p2[0] - p1[0]
                    dy = p2[1] - p1[1]
                    length = math.sqrt(dx * dx + dy * dy)
                    total_length += length
                    segment_lengths.append(length)

                # Find the segment where t falls
                target_distance = total_length * t
                current_distance = 0

                for i in range(len(segment_lengths)):
                    if current_distance + segment_lengths[i] >= target_distance:
                        # Found the segment - calculate exact position
                        p1 = edge.freeform_points[i]
                        p2 = edge.freeform_points[i + 1]
                        segment_t = (target_distance -
                                     current_distance) / segment_lengths[i]

                        # Linear interpolation within the segment
                        x = p1[0] + (p2[0] - p1[0]) * segment_t
                        y = p1[1] + (p2[1] - p1[1]) * segment_t
                        return (x, y)
                    current_distance += segment_lengths[i]

                # If we reach here, return the last point
                last_point = edge.freeform_points[-1]
                return (last_point[0], last_point[1])
            else:
                # Fallback to linear interpolation
                x = src_x + t * (tgt_x - src_x)
                y = src_y + t * (tgt_y - src_y)
                return (x, y)

        elif rendering_type == "nurbs":
            # For NURBS, use rational Bézier evaluation
            if edge.control_points and len(edge.control_points) >= 1:
                # Create weighted control points: source -> edge control points -> target
                ctrl_points = [(src_x, src_y, 1.0)]
                for cp in edge.control_points:
                    ctrl_points.append(
                        (cp[0], cp[1],
                         3.0))  # Higher weight for control points
                ctrl_points.append((tgt_x, tgt_y, 1.0))

                return self.evaluate_rational_bezier_variable(ctrl_points, t)
            else:
                # Fallback to linear interpolation
                x = src_x + t * (tgt_x - src_x)
                y = src_y + t * (tgt_y - src_y)
                return (x, y)

        elif rendering_type == "polyline":
            # For polyline, use control points if available
            if edge.control_points and len(edge.control_points) >= 1:
                # Create points list: source -> control_points -> target
                points = [type('Point', (), {
                    'x': src_x,
                    'y': src_y
                })()] + [
                    type('Point', (), {
                        'x': cp[0],
                        'y': cp[1]
                    })() for cp in edge.control_points
                ] + [type('Point', (), {
                    'x': tgt_x,
                    'y': tgt_y
                })()]
                num_segments = len(points) - 1

                if num_segments == 0:
                    return (source_node.x, source_node.y)

                # Find which segment we're in
                segment_t = t * num_segments
                segment_index = min(int(segment_t), num_segments - 1)
                local_t = segment_t - segment_index

                # Linear interpolation within the segment
                p0, p1 = points[segment_index], points[segment_index + 1]
                x = p0.x + local_t * (p1.x - p0.x)
                y = p0.y + local_t * (p1.y - p0.y)
                return (x, y)
            else:
                # Use default polyline algorithm between anchors
                dx = tgt_x - src_x
                dy = tgt_y - src_y
                segments = 5

                # Find which segment we're in
                segment_t = t * segments
                segment_index = min(int(segment_t), segments - 1)
                local_t = segment_t - segment_index

                # Linear interpolation with offset for middle segments
                base_x = src_x + t * dx
                base_y = src_y + t * dy

                # Add offset for segments in the middle
                if 0 < segment_index < segments - 1:
                    offset = 10 * math.sin(segment_index * math.pi / segments)
                    base_x += offset * math.cos(
                        math.atan2(dy, dx) + math.pi / 2)
                    base_y += offset * math.sin(
                        math.atan2(dy, dx) + math.pi / 2)

                return (base_x, base_y)

        elif rendering_type == "bspline":
            # For B-spline, use interpolating spline through all points between connection anchors
            if edge.control_points:
                # Create interpolation points: anchors -> control points -> anchor
                interpolation_points = [
                    (src_x, src_y)
                ] + edge.control_points + [(tgt_x, tgt_y)]
                return self.evaluate_interpolating_spline(
                    interpolation_points, t)
            else:
                # Use default interpolation based on anchors
                dx = tgt_x - src_x
                dy = tgt_y - src_y
                interpolation_points = [
                    (src_x, src_y),
                    (src_x + dx * 0.33, src_y + dy * 0.33 - 20),
                    (src_x + dx * 0.67, src_y + dy * 0.67 + 20), (tgt_x, tgt_y)
                ]
                return self.evaluate_interpolating_spline(
                    interpolation_points, t)

        elif rendering_type == "composite" or getattr(edge, 'is_composite',
                                                      False):
            # For composite curves, calculate position along the multi-segment path
            if not getattr(edge, 'curve_segments', None):
                # Fallback if no segments defined
                x = source_node.x + t * (target_node.x - source_node.x)
                y = source_node.y + t * (target_node.y - source_node.y)
                return (x, y)

            # Calculate intermediate points for each segment
            num_segments = len(edge.curve_segments)
            segment_points = [(source_node.x, source_node.y)
                              ]  # Start with source

            # Calculate intermediate points between segments
            for i in range(1, num_segments):
                segment_t = i / num_segments
                x = source_node.x + segment_t * (target_node.x - source_node.x)
                y = source_node.y + segment_t * (target_node.y - source_node.y)
                segment_points.append((x, y))

            segment_points.append(
                (target_node.x, target_node.y))  # End with target

            # Find which segment we're in
            global_t = t * num_segments
            segment_index = min(int(global_t), num_segments - 1)
            local_t = global_t - segment_index

            # Get the segment and evaluate its curve
            segment = edge.curve_segments[segment_index]
            start_pos = segment_points[segment_index]
            end_pos = segment_points[segment_index + 1]

            # Evaluate the specific segment type
            return self.calculate_segment_position(segment, start_pos, end_pos,
                                                   local_t)

        else:
            # Fallback to linear interpolation
            x = source_node.x + t * (target_node.x - source_node.x)
            y = source_node.y + t * (target_node.y - source_node.y)
            return (x, y)

    def calculate_segment_position(self, segment, start_pos, end_pos, t):
        """Calculate position along a single composite curve segment at parameter t."""

        segment_type = segment.get("type", "straight")
        control_points = segment.get("control_points", [])
        weight = segment.get("weight", 1.0)

        if segment_type == "straight":
            # Linear interpolation
            x = start_pos[0] + t * (end_pos[0] - start_pos[0])
            y = start_pos[1] + t * (end_pos[1] - start_pos[1])
            return (x, y)

        elif segment_type == "curved":
            # Quadratic Bézier with one control point
            if control_points and len(control_points) >= 1:
                cp = control_points[0]
            else:
                # Default control point
                mid_x = (start_pos[0] + end_pos[0]) / 2
                mid_y = (start_pos[1] + end_pos[1]) / 2
                dx = end_pos[0] - start_pos[0]
                dy = end_pos[1] - start_pos[1]
                length = max(1, math.sqrt(dx * dx + dy * dy))
                offset = length * 0.25
                perp_x = -dy / length * offset
                perp_y = dx / length * offset
                cp = (mid_x + perp_x, mid_y + perp_y)

            # Quadratic Bézier: B(t) = (1-t)²P₀ + 2(1-t)tP₁ + t²P₂
            x = (1 - t)**2 * start_pos[0] + 2 * (
                1 - t) * t * cp[0] + t**2 * end_pos[0]
            y = (1 - t)**2 * start_pos[1] + 2 * (
                1 - t) * t * cp[1] + t**2 * end_pos[1]
            return (x, y)

        elif segment_type == "bezier":
            # Multi-point Bézier
            if control_points and len(control_points) >= 1:
                full_control_points = [start_pos] + control_points + [end_pos]
            else:
                # Default cubic Bézier
                dx = end_pos[0] - start_pos[0]
                dy = end_pos[1] - start_pos[1]
                ctrl1 = (start_pos[0] + dx * 0.3, start_pos[1] + dy * 0.3 - 20)
                ctrl2 = (start_pos[0] + dx * 0.7, start_pos[1] + dy * 0.7 + 20)
                full_control_points = [start_pos, ctrl1, ctrl2, end_pos]

            return self.evaluate_bezier_curve(full_control_points, t)

        elif segment_type == "bspline":
            # B-spline through control points
            if control_points and len(control_points) >= 1:
                points = [start_pos] + control_points + [end_pos]
            else:
                # Default B-spline
                dx = end_pos[0] - start_pos[0]
                dy = end_pos[1] - start_pos[1]
                ctrl1 = (start_pos[0] + dx * 0.33,
                         start_pos[1] + dy * 0.33 - 15)
                ctrl2 = (start_pos[0] + dx * 0.67,
                         start_pos[1] + dy * 0.67 + 15)
                points = [start_pos, ctrl1, ctrl2, end_pos]

            return self.evaluate_interpolating_spline(points, t)

        elif segment_type == "nurbs":
            # NURBS with weighted control points
            if control_points and len(control_points) >= 1:
                ctrl_points = [(start_pos[0], start_pos[1], 1.0)]
                for cp in control_points:
                    ctrl_points.append((cp[0], cp[1], weight * 3.0))
                ctrl_points.append((end_pos[0], end_pos[1], 1.0))
            else:
                # Default NURBS
                dx = end_pos[0] - start_pos[0]
                dy = end_pos[1] - start_pos[1]
                ctrl_points = [(start_pos[0], start_pos[1], 1.0),
                               (start_pos[0] + dx * 0.3,
                                start_pos[1] + dy * 0.3 - 25, weight * 3.0),
                               (start_pos[0] + dx * 0.7,
                                start_pos[1] + dy * 0.7 + 25, weight * 3.0),
                               (end_pos[0], end_pos[1], 1.0)]

            try:
                return self.evaluate_rational_bezier_variable(ctrl_points, t)
            except:
                # Fallback to linear
                x = start_pos[0] + t * (end_pos[0] - start_pos[0])
                y = start_pos[1] + t * (end_pos[1] - start_pos[1])
                return (x, y)

        elif segment_type == "polyline":
            # Polyline with intermediate points
            if control_points and len(control_points) >= 1:
                points = [start_pos] + control_points + [end_pos]
            else:
                # Default polyline
                dx = end_pos[0] - start_pos[0]
                dy = end_pos[1] - start_pos[1]
                points = [
                    start_pos,
                    (start_pos[0] + dx * 0.33, start_pos[1] + dy * 0.33 + 10),
                    (start_pos[0] + dx * 0.67, start_pos[1] + dy * 0.67 - 10),
                    end_pos
                ]

            # Find segment within polyline
            num_sub_segments = len(points) - 1
            if num_sub_segments == 0:
                return start_pos

            segment_t = t * num_sub_segments
            sub_segment_index = min(int(segment_t), num_sub_segments - 1)
            local_t = segment_t - sub_segment_index

            # Linear interpolation within sub-segment
            p0, p1 = points[sub_segment_index], points[sub_segment_index + 1]
            x = p0[0] + local_t * (p1[0] - p0[0])
            y = p0[1] + local_t * (p1[1] - p0[1])
            return (x, y)

        else:
            # Fallback to linear interpolation
            x = start_pos[0] + t * (end_pos[0] - start_pos[0])
            y = start_pos[1] + t * (end_pos[1] - start_pos[1])
            return (x, y)

    def find_nearest_curve_parameter(self, edge, source_node, target_node,
                                     target_point):
        """Find the curve parameter t that produces a point closest to target_point using anchor points."""

        # Get proper anchor endpoints for accurate curve sampling
        source_anchor_world, target_anchor_world = self.get_edge_anchor_endpoints_world(
            edge, source_node, target_node)
        print(
            f"DEBUG: 🟡 Finding nearest curve parameter using anchor endpoints: source {source_anchor_world}, target {target_anchor_world}"
        )

        # Simple approach: sample the curve at many points and find the closest one
        best_t = 0.5
        best_distance = float('inf')

        # Sample the curve at 100 points using anchor-based calculation
        for i in range(101):
            t = i / 100.0
            curve_point = self.calculate_position_on_curve_with_anchors(
                edge, source_anchor_world, target_anchor_world, t)

            if curve_point:
                dx = curve_point[0] - target_point[0]
                dy = curve_point[1] - target_point[1]
                distance = math.sqrt(dx * dx + dy * dy)

                if distance < best_distance:
                    best_distance = distance
                    best_t = t

        print(
            f"DEBUG: 🟡 Found nearest curve parameter t={best_t:.3f} at distance {best_distance:.1f}"
        )
        return best_t

    def _point_to_line_distance(self, px: float, py: float, p1: tuple,
                                p2: tuple) -> float:
        """Calculate the distance from a point to a line segment."""

        x1, y1 = p1
        x2, y2 = p2

        # Calculate line length squared
        line_length_sq = (x2 - x1)**2 + (y2 - y1)**2

        if line_length_sq == 0:
            # Point case
            return math.sqrt((px - x1)**2 + (py - y1)**2)

        # Calculate projection parameter
        t = max(
            0,
            min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) /
                line_length_sq))

        # Calculate projection point
        projection_x = x1 + t * (x2 - x1)
        projection_y = y1 + t * (y2 - y1)

        # Return distance to projection
        return math.sqrt((px - projection_x)**2 + (py - projection_y)**2)

    def get_edge_at_position(self, screen_x, screen_y):
        """Check if position is over an edge using the same coordinate system as drawing."""

        click_tolerance = max(10, int(8 * self.zoom))

        print(
            f"DEBUG: 🎯 Edge hit test at screen({screen_x}, {screen_y}) with tolerance {click_tolerance} (rotation: {self.world_rotation}°)"
        )

        # If world is rotated, we need to "undo" the graphics context rotation
        # to get coordinates in the same space as the drawing operations
        test_x, test_y = screen_x, screen_y
        if self.world_rotation != 0.0:
            size = self.GetSize()
            center_x = size.width // 2
            center_y = size.height // 2

            # Apply inverse rotation to get coordinates in the pre-rotated space
            rotation_rad = -math.radians(
                self.world_rotation)  # Negative for inverse
            cos_angle = math.cos(rotation_rad)
            sin_angle = math.sin(rotation_rad)

            # Translate to origin
            temp_x = screen_x - center_x
            temp_y = screen_y - center_y

            # Apply inverse rotation
            test_x = temp_x * cos_angle - temp_y * sin_angle + center_x
            test_y = temp_x * sin_angle + temp_y * cos_angle + center_y

        # First check for ubergraph edges - they take precedence since they're like nodes
        for edge in self.graph.get_all_edges():
            if edge.is_hyperedge and edge.hyperedge_visualization == "ubergraph":
                # Convert edge's ubergraph position to screen coordinates
                edge_screen_x, edge_screen_y = self.world_to_screen(
                    edge.uber_x, edge.uber_y)

                # Check if click is within the edge's bounds
                half_width = (edge.uber_width * self.zoom) / 2.0
                half_height = (edge.uber_height * self.zoom) / 2.0

                if (abs(test_x - edge_screen_x) <= half_width
                        and abs(test_y - edge_screen_y) <= half_height):
                    print(f"DEBUG: 🎯 Hit ubergraph edge {edge.id}")
                    return edge

            print(
                f"DEBUG: 🎯 Inverse rotation: screen({screen_x}, {screen_y}) -> pre-rotation({test_x:.1f}, {test_y:.1f})"
            )

        # Next, check clicks on ubergraph link paths (line_graph view) and node↔uberedge segments
        for edge in self.graph.get_all_edges():
            if not (edge.is_hyperedge
                    and edge.hyperedge_visualization == "ubergraph"):
                continue
            view = getattr(edge, 'hyperedge_view', 'standard') or 'standard'
            # Build target list including explicit connections (allow duplicates for parallel links)
            explicit_list = []
            try:
                explicit_list = list((edge.metadata or {}).get(
                    'connected_uberedges', [])) if hasattr(edge,
                                                           'metadata') else []
            except Exception:
                explicit_list = []
            # Compute screen position of this edge
            ex, ey = self.world_to_screen(edge.uber_x, edge.uber_y)
            # For each explicit connection entry, test distance to segment in screen space
            for target_edge_id in explicit_list:
                other = self.graph.get_edge(target_edge_id) if hasattr(
                    self.graph, 'get_edge') else None
                if not other:
                    # Fallback: search by id
                    for oe in self.graph.get_all_edges():
                        if oe.id == target_edge_id:
                            other = oe
                            break
                if not other or not other.is_hyperedge:
                    continue
                ox, oy = self.world_to_screen(other.uber_x, other.uber_y)
                # Point-to-segment distance in screen space
                x1, y1, x2, y2 = float(ex), float(ey), float(ox), float(oy)
                vx, vy = x2 - x1, y2 - y1
                wx, wy = test_x - x1, test_y - y1
                seg_len_sq = vx * vx + vy * vy
                t = 0.0 if seg_len_sq == 0 else max(
                    0.0, min(1.0, (wx * vx + wy * vy) / seg_len_sq))
                proj_x = x1 + t * vx
                proj_y = y1 + t * vy
                dist = math.hypot(test_x - proj_x, test_y - proj_y)
                if dist <= click_tolerance:
                    print(
                        f"DEBUG: 🎯 Hit ubergraph link path of edge {edge.id} -> {other.id}"
                    )
                    # Record selection context for segment operations
                    self.selected_uber_segment_kind = 'edge'
                    self.selected_uber_segment_edge_id = edge.id
                    self.selected_uber_segment_other_edge_id = other.id
                    self.selected_uber_segment_node_id = None
                    try:
                        self.graph.clear_selection()
                        self.graph.select_edge(edge.id)
                        self.selection_changed.emit()
                    except Exception:
                        pass
                    return edge

            # Also allow selection by clicking node↔uberedge connection segments
            node_ids = []
            if getattr(edge, 'source_id', None):
                node_ids.append(edge.source_id)
            for nid in getattr(edge, 'source_ids', []) or []:
                node_ids.append(nid)
            if getattr(edge, 'target_id', None):
                node_ids.append(edge.target_id)
            for nid in getattr(edge, 'target_ids', []) or []:
                node_ids.append(nid)
            for nid in node_ids:
                node = self.graph.get_node(nid)
                if not node:
                    continue
                nx, ny = self.world_to_screen(node.x, node.y)
                x1, y1, x2, y2 = float(ex), float(ey), float(nx), float(ny)
                vx, vy = x2 - x1, y2 - y1
                wx, wy = test_x - x1, test_y - y1
                seg_len_sq = vx * vx + vy * vy
                t = 0.0 if seg_len_sq == 0 else max(
                    0.0, min(1.0, (wx * vx + wy * vy) / seg_len_sq))
                proj_x = x1 + t * vx
                proj_y = y1 + t * vy
                dist = math.hypot(test_x - proj_x, test_y - proj_y)
                if dist <= click_tolerance:
                    print(
                        f"DEBUG: 🎯 Hit ubergraph node-link path of edge {edge.id} -> node {nid}"
                    )
                    self.selected_uber_segment_kind = 'node'
                    self.selected_uber_segment_edge_id = edge.id
                    self.selected_uber_segment_node_id = nid
                    self.selected_uber_segment_other_edge_id = None
                    try:
                        self.graph.clear_selection()
                        self.graph.select_edge(edge.id)
                        self.selection_changed.emit()
                    except Exception:
                        pass
                    return edge

        best_edge = None
        best_distance = float('inf')

        # Check all edges
        for edge in self.graph.get_all_edges():
            if not edge.visible:
                continue

            source_node = self.graph.get_node(edge.source_id)
            target_node = self.graph.get_node(edge.target_id)

            if not source_node or not target_node:
                continue

            # Get screen positions for main nodes
            source_screen = self.world_to_screen(source_node.x, source_node.y)
            target_screen = self.world_to_screen(target_node.x, target_node.y)
            source_adjusted = self.calculate_line_endpoint(
                source_node, target_node, source_screen, target_screen, True,
                edge)
            target_adjusted = self.calculate_line_endpoint(
                target_node, source_node, target_screen, source_screen, False,
                edge)

            if edge.is_hyperedge:
                # Calculate connection points
                dx = target_adjusted[0] - source_adjusted[0]
                dy = target_adjusted[1] - source_adjusted[1]
                from_point = (source_adjusted[0] +
                              dx * edge.from_connection_point,
                              source_adjusted[1] +
                              dy * edge.from_connection_point)
                to_point = (source_adjusted[0] + dx * edge.to_connection_point,
                            source_adjusted[1] + dy * edge.to_connection_point)

                # Check source node connections
                for node in [source_node] + [
                        self.graph.get_node(nid) for nid in edge.source_ids
                ]:
                    if not node:
                        continue
                    node_screen = self.world_to_screen(node.x, node.y)
                    node_adjusted = self.calculate_line_endpoint(
                        node, source_node, node_screen, source_screen, True,
                        edge)
                    dist = self._point_to_line_distance(
                        test_x, test_y, node_adjusted, from_point)
                    if dist <= click_tolerance and dist < best_distance:
                        best_distance = dist
                        best_edge = edge

                # Check target node connections
                for node in [target_node] + [
                        self.graph.get_node(nid) for nid in edge.target_ids
                ]:
                    if not node:
                        continue
                    node_screen = self.world_to_screen(node.x, node.y)
                    node_adjusted = self.calculate_line_endpoint(
                        node, target_node, node_screen, target_screen, True,
                        edge)
                    dist = self._point_to_line_distance(
                        test_x, test_y, node_adjusted, to_point)
                    if dist <= click_tolerance and dist < best_distance:
                        best_distance = dist
                        best_edge = edge

                # Check main segment
                dist = self._point_to_line_distance(test_x, test_y, from_point,
                                                    to_point)
                if dist <= click_tolerance and dist < best_distance:
                    best_distance = dist
                    best_edge = edge
            else:
                # Regular edge - check the main line
                dist = self._point_to_line_distance(test_x, test_y,
                                                    source_adjusted,
                                                    target_adjusted)
                if dist <= click_tolerance and dist < best_distance:
                    best_distance = dist
                    best_edge = edge

        for edge in self.graph.get_all_edges():
            if not hasattr(edge, 'visible') or edge.visible:
                source_node = self.graph.get_node(edge.source_id)
                target_node = self.graph.get_node(edge.target_id)

                if not source_node or not target_node:
                    continue

                # Use the exact same positioning as draw_edge()
                source_screen = self.world_to_screen(source_node.x,
                                                     source_node.y)
                target_screen = self.world_to_screen(target_node.x,
                                                     target_node.y)

                # Calculate the same line endpoints as in draw_edge()
                source_adjusted = self.calculate_line_endpoint(
                    source_node, target_node, source_screen, target_screen,
                    True, edge)
                target_adjusted = self.calculate_line_endpoint(
                    target_node, source_node, target_screen, source_screen,
                    False, edge)

                # Sample points along the edge in the same coordinate space as drawing
                min_distance = float('inf')

                # For freeform edges, check against the actual path points
                if edge.rendering_type == "freeform" and edge.freeform_points and len(
                        edge.freeform_points) >= 2:
                    for i in range(len(edge.freeform_points) - 1):
                        p1 = edge.freeform_points[i]
                        p2 = edge.freeform_points[i + 1]
                        p1_screen = self.world_to_screen(p1[0], p1[1])
                        p2_screen = self.world_to_screen(p2[0], p2[1])

                        # Calculate distance to line segment
                        dx = p2_screen[0] - p1_screen[0]
                        dy = p2_screen[1] - p1_screen[1]
                        length_sq = dx * dx + dy * dy

                        if length_sq == 0:
                            # Point case
                            distance = math.sqrt((test_x - p1_screen[0])**2 +
                                                 (test_y - p1_screen[1])**2)
                        else:
                            # Calculate projection parameter
                            t = max(
                                0,
                                min(1, ((test_x - p1_screen[0]) * dx +
                                        (test_y - p1_screen[1]) * dy) /
                                    length_sq))

                            # Calculate projection point
                            proj_x = p1_screen[0] + t * dx
                            proj_y = p1_screen[1] + t * dy

                            # Calculate distance to projection
                            distance = math.sqrt((test_x - proj_x)**2 +
                                                 (test_y - proj_y)**2)

                        min_distance = min(min_distance, distance)
                else:
                    # For other edge types, sample points along the edge
                    min_distance = float('inf')

                for i in range(20):  # Sample at 20 points along the curve
                    t = i / 19.0 if i < 19 else 1.0

                    # For curved edges, get the actual curve position using same method as drawing
                    if hasattr(edge, 'control_points') and hasattr(
                            edge, 'rendering_type'):
                        rendering_type = edge.rendering_type if edge.rendering_type else self.edge_rendering_type
                        if rendering_type != 'straight' and edge.control_points:
                            # Use the same curve calculation as the drawing code
                            source_anchor_world, target_anchor_world = self.get_edge_anchor_endpoints_world(
                                edge, source_node, target_node)
                            curve_world = self.calculate_position_on_curve_with_anchors(
                                edge, source_anchor_world, target_anchor_world,
                                t)
                            if curve_world:
                                curve_screen = self.world_to_screen(
                                    curve_world[0], curve_world[1])
                                curve_x, curve_y = curve_screen[
                                    0], curve_screen[1]
                            else:
                                # Fallback to straight line
                                curve_x = source_adjusted[0] + t * (
                                    target_adjusted[0] - source_adjusted[0])
                                curve_y = source_adjusted[1] + t * (
                                    target_adjusted[1] - source_adjusted[1])
                        else:
                            # Straight line case
                            curve_x = source_adjusted[0] + t * (
                                target_adjusted[0] - source_adjusted[0])
                            curve_y = source_adjusted[1] + t * (
                                target_adjusted[1] - source_adjusted[1])
                    else:
                        # Straight line case
                        curve_x = source_adjusted[0] + t * (
                            target_adjusted[0] - source_adjusted[0])
                        curve_y = source_adjusted[1] + t * (
                            target_adjusted[1] - source_adjusted[1])

                    # Calculate distance from test point to curve point (same coordinate space)
                    dx = curve_x - test_x
                    dy = curve_y - test_y
                    distance = math.sqrt(dx * dx + dy * dy)

                    if distance < min_distance:
                        min_distance = distance

                if min_distance < click_tolerance and min_distance < best_distance:
                    best_edge = edge
                    best_distance = min_distance
                    print(
                        f"DEBUG: 🎯 Edge {edge.id} hit at distance {min_distance:.1f} pixels"
                    )

        if best_edge:
            print(
                f"DEBUG: 🎯 ✅ Selected edge {best_edge.id} at distance {best_distance:.1f}"
            )
            return best_edge
        else:
            print(f"DEBUG: 🎯 ❌ No edge hit")
            return None

    def get_edge_endpoint_at_position(self, screen_x, screen_y):
        """Check if position is over an edge endpoint dot. Returns (edge, endpoint_type) or None.
        
        endpoint_type can be: 'source', 'target', 'from', 'to', 'source_N', 'target_N' (where N is the index)
        """

        dot_radius = max(6, int(4 * self.zoom))

        # Apply inverse rotation to get coordinates in the same space as drawing
        test_x, test_y = screen_x, screen_y
        if self.world_rotation != 0.0:
            size = self.GetSize()
            center_x = size.width // 2
            center_y = size.height // 2

            rotation_rad = -math.radians(
                self.world_rotation)  # Negative for inverse
            cos_angle = math.cos(rotation_rad)
            sin_angle = math.sin(rotation_rad)

            temp_x = screen_x - center_x
            temp_y = screen_y - center_y

            test_x = temp_x * cos_angle - temp_y * sin_angle + center_x
            test_y = temp_x * sin_angle + temp_y * cos_angle + center_y

        for edge in self.graph.get_all_edges():
            if not edge.selected:
                continue

            source_node = self.graph.get_node(edge.source_id)
            target_node = self.graph.get_node(edge.target_id)

            if not source_node or not target_node:
                continue

            # Get screen positions
            source_screen = self.world_to_screen(source_node.x, source_node.y)
            target_screen = self.world_to_screen(target_node.x, target_node.y)

            # Calculate adjusted edge endpoints (same as in draw_edge)
            source_adjusted = self.calculate_line_endpoint(
                source_node, target_node, source_screen, target_screen, True,
                edge)
            target_adjusted = self.calculate_line_endpoint(
                target_node, source_node, target_screen, source_screen, False,
                edge)

            if edge.is_hyperedge:
                # Check source node connections
                for i, node in enumerate(
                    [source_node] +
                    [self.graph.get_node(nid) for nid in edge.source_ids]):
                    if not node:
                        continue
                    node_screen = self.world_to_screen(node.x, node.y)
                    node_adjusted = self.calculate_line_endpoint(
                        node, source_node, node_screen, source_screen, True,
                        edge)
                    dist = math.sqrt((test_x - node_adjusted[0])**2 +
                                     (test_y - node_adjusted[1])**2)
                    if dist <= dot_radius:
                        return (edge, f'source_{i}')

                # Check target node connections
                for i, node in enumerate(
                    [target_node] +
                    [self.graph.get_node(nid) for nid in edge.target_ids]):
                    if not node:
                        continue
                    node_screen = self.world_to_screen(node.x, node.y)
                    node_adjusted = self.calculate_line_endpoint(
                        node, target_node, node_screen, target_screen, True,
                        edge)
                    dist = math.sqrt((test_x - node_adjusted[0])**2 +
                                     (test_y - node_adjusted[1])**2)
                    if dist <= dot_radius:
                        return (edge, f'target_{i}')
            else:
                # Check source dot (using inverse-rotated coordinates)
                source_dist = math.sqrt((test_x - source_adjusted[0])**2 +
                                        (test_y - source_adjusted[1])**2)
                if source_dist <= dot_radius:
                    return (edge, 'source')

                # Check target dot (using inverse-rotated coordinates)
                target_dist = math.sqrt((test_x - target_adjusted[0])**2 +
                                        (test_y - target_adjusted[1])**2)
                if target_dist <= dot_radius:
                    return (edge, 'target')

                # Calculate edge direction
                dx = target_adjusted[0] - source_adjusted[0]
                dy = target_adjusted[1] - source_adjusted[1]

                # Check cyan (from) connection point
                from_x = source_adjusted[0] + dx * edge.from_connection_point
                from_y = source_adjusted[1] + dy * edge.from_connection_point
                from_dist = math.sqrt((test_x - from_x)**2 +
                                      (test_y - from_y)**2)
                if from_dist <= dot_radius:
                    return (edge, 'from')

                # Check purple (to) connection point
                to_x = source_adjusted[0] + dx * edge.to_connection_point
                to_y = source_adjusted[1] + dy * edge.to_connection_point
                to_dist = math.sqrt((test_x - to_x)**2 + (test_y - to_y)**2)
                if to_dist <= dot_radius:
                    return (edge, 'to')

        return None

    def calculate_line_endpoint(self,
                                node,
                                other_node,
                                node_screen,
                                other_screen,
                                is_source,
                                edge=None):
        """Calculate the proper endpoint for a line to avoid overlapping with the node."""
        # Check for custom endpoint position first
        if edge and hasattr(edge, 'custom_endpoints'):
            endpoint_key = 'source' if is_source else 'target'
            if endpoint_key in edge.custom_endpoints:
                custom_world_pos = edge.custom_endpoints[endpoint_key]
                custom_screen_pos = self.world_to_screen(
                    custom_world_pos[0], custom_world_pos[1])
                return (int(custom_screen_pos[0]), int(custom_screen_pos[1]))

        # Perform endpoint computation in WORLD coordinates so rotation does not distort anchors
        node_cx_w, node_cy_w = node.x, node.y
        other_cx_w, other_cy_w = other_node.x, other_node.y

        # Direction vector in world space
        dx_w = other_cx_w - node_cx_w
        dy_w = other_cy_w - node_cy_w
        length_w = math.sqrt(dx_w * dx_w + dy_w * dy_w)
        if length_w == 0:
            # Fallback: return passed-in center in screen coords
            return node_screen

        # Normalize direction in world space
        dx_w /= length_w
        dy_w /= length_w

        # Node dimensions in WORLD units (unscaled); world transform will scale uniformly
        node_width_w = float(node.width)
        node_height_w = float(node.height)

        # Distance from center to rectangle edges along the ray in world space
        if abs(dx_w) > 0.001:
            dist_to_vertical_edge_w = (node_width_w / 2.0) / abs(dx_w)
        else:
            dist_to_vertical_edge_w = float('inf')

        if abs(dy_w) > 0.001:
            dist_to_horizontal_edge_w = (node_height_w / 2.0) / abs(dy_w)
        else:
            dist_to_horizontal_edge_w = float('inf')

        edge_distance_w = min(dist_to_vertical_edge_w,
                              dist_to_horizontal_edge_w)

        endpoint_x_w = node_cx_w + dx_w * edge_distance_w
        endpoint_y_w = node_cy_w + dy_w * edge_distance_w

        # Convert back to screen coordinates for drawing/UI
        endpoint_screen = self.world_to_screen(endpoint_x_w, endpoint_y_w)
        return (int(endpoint_screen[0]), int(endpoint_screen[1]))

    def get_edge_anchor_endpoints_world(self, edge, source_node, target_node):
        """Get the actual anchor endpoints in world coordinates for proper curve calculations."""

        # Get screen positions of node centers
        source_screen = self.world_to_screen(source_node.x, source_node.y)
        target_screen = self.world_to_screen(target_node.x, target_node.y)

        # Calculate adjusted edge endpoints (anchor points) in screen coordinates
        source_adjusted_screen = self.calculate_line_endpoint(
            source_node, target_node, source_screen, target_screen, True, edge)
        target_adjusted_screen = self.calculate_line_endpoint(
            target_node, source_node, target_screen, source_screen, False,
            edge)

        # Convert back to world coordinates
        source_anchor_world = self.screen_to_world(source_adjusted_screen[0],
                                                   source_adjusted_screen[1])
        target_anchor_world = self.screen_to_world(target_adjusted_screen[0],
                                                   target_adjusted_screen[1])

        return source_anchor_world, target_anchor_world

    def debug_check_node_visibility(self, context=""):
        """Debug function to check if any nodes have become invisible."""

        invisible_nodes = []
        for node in self.graph.get_all_nodes():
            if not node.visible:
                invisible_nodes.append(node.text)

        if invisible_nodes:
            print(
                f"DEBUG: 👻 {context} - Found invisible nodes: {invisible_nodes}"
            )
        else:
            print(f"DEBUG: 👁️ {context} - All nodes visible")

    def force_all_nodes_visible(self):
        """Force all nodes to be visible - useful for debugging disappearing node issues."""

        restored_count = 0
        for node in self.graph.get_all_nodes():
            if not node.visible:
                print(f"DEBUG: 🔧 Restoring visibility to node '{node.text}'")
                node.visible = True
                restored_count += 1

        if restored_count > 0:
            print(f"DEBUG: 🔧 Restored visibility to {restored_count} nodes")
            self.Refresh()
        else:
            print(f"DEBUG: 🔧 All nodes were already visible")

    def calculate_position_on_curve_with_anchors(self, edge, source_anchor,
                                                 target_anchor, t):
        """Calculate position along curve at parameter t using anchor endpoints instead of node centers."""

        rendering_type = edge.rendering_type if edge.rendering_type else self.edge_rendering_type

        # Initialize control points if they don't exist (but preserve user preference for 0 control points)
        if not hasattr(edge, 'control_points'):
            edge.control_points = []

        if rendering_type == "freeform" and edge.freeform_points and len(
                edge.freeform_points) >= 2:
            # For freeform edges, interpolate along the path points
            total_length = 0
            segment_lengths = []
            for i in range(len(edge.freeform_points) - 1):
                p1 = edge.freeform_points[i]
                p2 = edge.freeform_points[i + 1]
                dx = p2[0] - p1[0]
                dy = p2[1] - p1[1]
                length = math.sqrt(dx * dx + dy * dy)
                total_length += length
                segment_lengths.append(length)

            # Find the segment where t falls
            target_distance = total_length * t
            current_distance = 0

            for i in range(len(segment_lengths)):
                if current_distance + segment_lengths[i] >= target_distance:
                    # Found the segment - calculate exact position
                    p1 = edge.freeform_points[i]
                    p2 = edge.freeform_points[i + 1]
                    segment_t = (target_distance -
                                 current_distance) / segment_lengths[i]

                    # Linear interpolation within the segment
                    x = p1[0] + (p2[0] - p1[0]) * segment_t
                    y = p1[1] + (p2[1] - p1[1]) * segment_t
                    return (x, y)
                current_distance += segment_lengths[i]

            # If we reach here, return the last point
            last_point = edge.freeform_points[-1]
            return (last_point[0], last_point[1])

        elif rendering_type == "straight":
            # Linear interpolation for straight lines using anchor points
            x = source_anchor[0] + t * (target_anchor[0] - source_anchor[0])
            y = source_anchor[1] + t * (target_anchor[1] - source_anchor[1])
            return (x, y)

        elif rendering_type == "curved":
            # For curved edges, use control point if available, otherwise calculate default
            if (hasattr(edge, 'control_points') and edge.control_points
                    and isinstance(edge.control_points, list)
                    and len(edge.control_points) >= 1):
                try:
                    # Quadratic Bézier with anchor endpoints
                    control_point = edge.control_points[0]
                    return self.evaluate_quadratic_bezier_curve([
                        source_anchor,
                        (control_point[0], control_point[1]), target_anchor
                    ], t)
                except (IndexError, TypeError, ValueError):
                    pass

            # Default arc calculation using anchor points
            cx = (source_anchor[0] + target_anchor[0]) / 2
            cy = (source_anchor[1] + target_anchor[1]) / 2

            # Create arc control point offset from midpoint
            dx = target_anchor[0] - source_anchor[0]
            dy = target_anchor[1] - source_anchor[1]
            length = math.sqrt(dx * dx + dy * dy)
            if length > 0:
                offset = length * 0.3  # 30% offset perpendicular
                perpendicular_x = -dy / length * offset
                perpendicular_y = dx / length * offset
                control_point = (cx + perpendicular_x, cy + perpendicular_y)
                return self.evaluate_quadratic_bezier_curve(
                    [source_anchor, control_point, target_anchor], t)
            else:
                return source_anchor  # Fallback for zero-length edge

        elif rendering_type == "bspline":
            # B-spline calculation using anchor endpoints
            if (hasattr(edge, 'control_points') and edge.control_points
                    and isinstance(edge.control_points, list)
                    and len(edge.control_points) >= 1):
                try:
                    # Create knot points: source anchor -> control points -> target anchor
                    knot_points = [source_anchor
                                   ] + edge.control_points + [target_anchor]
                    return self.evaluate_bspline_variable(knot_points, t)
                except (IndexError, TypeError, ValueError):
                    pass

            # Fallback to linear interpolation with anchor points
            x = source_anchor[0] + t * (target_anchor[0] - source_anchor[0])
            y = source_anchor[1] + t * (target_anchor[1] - source_anchor[1])
            return (x, y)

        elif rendering_type == "bezier":
            # Bézier curve using anchor endpoints
            if (hasattr(edge, 'control_points') and edge.control_points
                    and isinstance(edge.control_points, list)
                    and len(edge.control_points) >= 1):
                try:
                    # Create control points list: source anchor -> control points -> target anchor
                    control_points = [source_anchor] + edge.control_points + [
                        target_anchor
                    ]
                    return self.evaluate_bezier_curve(control_points, t)
                except (IndexError, TypeError, ValueError):
                    pass

            # With 0 control points, Bézier should be a straight line (match draw_bezier_edge behavior)
            x = source_anchor[0] + t * (target_anchor[0] - source_anchor[0])
            y = source_anchor[1] + t * (target_anchor[1] - source_anchor[1])
            return (x, y)

        elif rendering_type == "cubic_spline":
            # Cubic spline using anchor endpoints
            if (hasattr(edge, 'control_points') and edge.control_points
                    and isinstance(edge.control_points, list)
                    and len(edge.control_points) >= 1):
                try:
                    # Create points list: source anchor -> control points -> target anchor
                    points = [source_anchor
                              ] + edge.control_points + [target_anchor]
                    return self.evaluate_interpolating_spline(points, t)
                except (IndexError, TypeError, ValueError):
                    pass

            # Fallback to linear interpolation with anchor points
            x = source_anchor[0] + t * (target_anchor[0] - source_anchor[0])
            y = source_anchor[1] + t * (target_anchor[1] - source_anchor[1])
            return (x, y)

        elif rendering_type == "nurbs":
            # NURBS using anchor endpoints
            if (hasattr(edge, 'control_points') and edge.control_points
                    and isinstance(edge.control_points, list)
                    and len(edge.control_points) >= 1):
                try:
                    # Create weighted control points: source anchor -> edge control points -> target anchor
                    weighted_points = [(source_anchor[0], source_anchor[1],
                                        1.0)]
                    for cp in edge.control_points:
                        weighted_points.append((cp[0], cp[1], 1.0))
                    weighted_points.append(
                        (target_anchor[0], target_anchor[1], 1.0))
                    return self.evaluate_rational_bezier_curve(
                        weighted_points, t)
                except (IndexError, TypeError, ValueError):
                    pass

            # Fallback to linear interpolation with anchor points
            x = source_anchor[0] + t * (target_anchor[0] - source_anchor[0])
            y = source_anchor[1] + t * (target_anchor[1] - source_anchor[1])
            return (x, y)

        elif rendering_type == "polyline":
            # Polyline using anchor endpoints
            if (hasattr(edge, 'control_points') and edge.control_points
                    and isinstance(edge.control_points, list)
                    and len(edge.control_points) >= 1):
                try:
                    # Create segment points: source anchor -> control points -> target anchor
                    segment_points = [source_anchor] + edge.control_points + [
                        target_anchor
                    ]
                    return self.evaluate_polyline_curve(segment_points, t)
                except (IndexError, TypeError, ValueError):
                    pass

            # Fallback to linear interpolation with anchor points
            x = source_anchor[0] + t * (target_anchor[0] - source_anchor[0])
            y = source_anchor[1] + t * (target_anchor[1] - source_anchor[1])
            return (x, y)

        elif rendering_type == "composite" or getattr(edge, 'is_composite',
                                                      False):
            # Composite curve using anchor endpoints
            if hasattr(edge, 'curve_segments') and edge.curve_segments:
                try:
                    # Find which segment contains parameter t
                    num_segments = len(edge.curve_segments)
                    segment_length = 1.0 / num_segments
                    segment_index = min(int(t * num_segments),
                                        num_segments - 1)

                    # Calculate local t within the segment (0.0 to 1.0)
                    segment_t = (t * num_segments) - segment_index
                    segment_t = max(0.0, min(1.0, segment_t))

                    segment = edge.curve_segments[segment_index]
                    segment_type = segment.get("type", "bezier")
                    segment_control_points = segment.get("control_points", [])

                    # Calculate segment endpoints
                    segment_start_t = segment_index / num_segments
                    segment_end_t = (segment_index + 1) / num_segments

                    segment_start_x = source_anchor[0] + segment_start_t * (
                        target_anchor[0] - source_anchor[0])
                    segment_start_y = source_anchor[1] + segment_start_t * (
                        target_anchor[1] - source_anchor[1])
                    segment_end_x = source_anchor[0] + segment_end_t * (
                        target_anchor[0] - source_anchor[0])
                    segment_end_y = source_anchor[1] + segment_end_t * (
                        target_anchor[1] - source_anchor[1])

                    segment_start = (segment_start_x, segment_start_y)
                    segment_end = (segment_end_x, segment_end_y)

                    # Calculate position within this segment based on its type
                    if segment_type == "bezier" and len(
                            segment_control_points) >= 1:
                        # Create full control points list for this segment
                        control_points = [
                            segment_start
                        ] + segment_control_points + [segment_end]
                        return self.evaluate_bezier_curve(
                            control_points, segment_t)
                    elif segment_type == "bspline" and len(
                            segment_control_points) >= 1:
                        knot_points = [
                            segment_start
                        ] + segment_control_points + [segment_end]
                        return self.evaluate_bspline_variable(
                            knot_points, segment_t)
                    elif segment_type == "cubic_spline" and len(
                            segment_control_points) >= 1:
                        points = [segment_start
                                  ] + segment_control_points + [segment_end]
                        return self.evaluate_interpolating_spline(
                            points, segment_t)
                    else:
                        # Default to linear interpolation for this segment
                        x = segment_start[0] + segment_t * (segment_end[0] -
                                                            segment_start[0])
                        y = segment_start[1] + segment_t * (segment_end[1] -
                                                            segment_start[1])
                        return (x, y)

                except (IndexError, TypeError, ValueError) as e:
                    print(
                        f"DEBUG: ⚠️ Error calculating composite curve position: {e}"
                    )

            # Fallback to linear interpolation for composite curves
            x = source_anchor[0] + t * (target_anchor[0] - source_anchor[0])
            y = source_anchor[1] + t * (target_anchor[1] - source_anchor[1])
            return (x, y)

        # Default fallback: linear interpolation with anchor points
        x = source_anchor[0] + t * (target_anchor[0] - source_anchor[0])
        y = source_anchor[1] + t * (target_anchor[1] - source_anchor[1])
        return (x, y)

    def calculate_curve_tangent_at_position_with_anchors(
            self, edge, source_anchor, target_anchor, t):
        """Calculate tangent direction at position t using anchor endpoints instead of node centers."""

        rendering_type = edge.rendering_type if edge.rendering_type else self.edge_rendering_type

        # Safety checks for control points
        if not hasattr(edge, 'control_points'):
            edge.control_points = []

        try:
            if rendering_type == "straight":
                # Straight line tangent is constant direction
                dx = target_anchor[0] - source_anchor[0]
                dy = target_anchor[1] - source_anchor[1]
                return (dx, dy)

            elif rendering_type == "curved":
                # Curved arc tangent
                if (hasattr(edge, 'control_points') and edge.control_points
                        and isinstance(edge.control_points, list)
                        and len(edge.control_points) >= 1):
                    try:
                        # Quadratic Bézier tangent with anchor endpoints
                        control_point = edge.control_points[0]
                        p0, p1, p2 = source_anchor, (
                            control_point[0], control_point[1]), target_anchor
                        # Quadratic Bézier tangent: 2*(1-t)*(p1-p0) + 2*t*(p2-p1)
                        dx = 2 * (1 - t) * (p1[0] - p0[0]) + 2 * t * (p2[0] -
                                                                      p1[0])
                        dy = 2 * (1 - t) * (p1[1] - p0[1]) + 2 * t * (p2[1] -
                                                                      p1[1])
                        return (dx, dy)
                    except (IndexError, TypeError, ValueError):
                        pass

                # Default arc tangent using anchor points
                dx = target_anchor[0] - source_anchor[0]
                dy = target_anchor[1] - source_anchor[1]
                return (dx, dy)

            elif rendering_type == "bspline":
                # B-spline tangent using anchor endpoints
                if (hasattr(edge, 'control_points') and edge.control_points
                        and isinstance(edge.control_points, list)
                        and len(edge.control_points) >= 1):
                    try:
                        knot_points = [source_anchor] + edge.control_points + [
                            target_anchor
                        ]
                        # Simple finite difference approximation for B-spline tangent
                        dt = 0.01
                        p1 = self.evaluate_bspline_variable(
                            knot_points, max(0, t - dt / 2))
                        p2 = self.evaluate_bspline_variable(
                            knot_points, min(1, t + dt / 2))
                        dx = (p2[0] - p1[0]) / dt
                        dy = (p2[1] - p1[1]) / dt
                        return (dx, dy)
                    except (IndexError, TypeError, ValueError):
                        pass

                # Fallback to straight line tangent with anchor points
                dx = target_anchor[0] - source_anchor[0]
                dy = target_anchor[1] - source_anchor[1]
                return (dx, dy)

            elif rendering_type == "bezier":
                # Bézier tangent using anchor endpoints
                if (hasattr(edge, 'control_points') and edge.control_points
                        and isinstance(edge.control_points, list)
                        and len(edge.control_points) >= 1):
                    try:
                        control_points = [
                            source_anchor
                        ] + edge.control_points + [target_anchor]
                        n = len(control_points) - 1

                        # Bézier derivative formula
                        dx, dy = 0, 0
                        for i in range(n):
                            coeff = self.binomial_coefficient(n - 1, i) * (
                                (1 - t)**(n - 1 - i)) * (t**i)
                            dx += coeff * (control_points[i + 1][0] -
                                           control_points[i][0])
                            dy += coeff * (control_points[i + 1][1] -
                                           control_points[i][1])

                        return (n * dx, n * dy)
                    except (IndexError, TypeError, ValueError):
                        pass

                # Fallback to straight line tangent with anchor points
                dx = target_anchor[0] - source_anchor[0]
                dy = target_anchor[1] - source_anchor[1]
                return (dx, dy)

            elif rendering_type == "cubic_spline":
                # Cubic spline tangent using anchor endpoints
                if (hasattr(edge, 'control_points') and edge.control_points
                        and isinstance(edge.control_points, list)
                        and len(edge.control_points) >= 1):
                    try:
                        points = [source_anchor
                                  ] + edge.control_points + [target_anchor]
                        # Finite difference approximation for cubic spline tangent
                        dt = 0.01
                        p1 = self.evaluate_interpolating_spline(
                            points, max(0, t - dt / 2))
                        p2 = self.evaluate_interpolating_spline(
                            points, min(1, t + dt / 2))
                        dx = (p2[0] - p1[0]) / dt
                        dy = (p2[1] - p1[1]) / dt
                        return (dx, dy)
                    except (IndexError, TypeError, ValueError):
                        pass

                # Fallback to straight line tangent with anchor points
                dx = target_anchor[0] - source_anchor[0]
                dy = target_anchor[1] - source_anchor[1]
                return (dx, dy)

            elif rendering_type == "composite" or getattr(
                    edge, 'is_composite', False):
                # Composite curve tangent using finite difference
                try:
                    dt = 0.01
                    p1 = self.calculate_position_on_curve_with_anchors(
                        edge, source_anchor, target_anchor, max(0, t - dt / 2))
                    p2 = self.calculate_position_on_curve_with_anchors(
                        edge, source_anchor, target_anchor, min(1, t + dt / 2))
                    dx = (p2[0] - p1[0]) / dt
                    dy = (p2[1] - p1[1]) / dt
                    return (dx, dy)
                except:
                    pass

            # For other curve types (nurbs, polyline), use finite difference approximation
            else:
                try:
                    dt = 0.01
                    p1 = self.calculate_position_on_curve_with_anchors(
                        edge, source_anchor, target_anchor, max(0, t - dt / 2))
                    p2 = self.calculate_position_on_curve_with_anchors(
                        edge, source_anchor, target_anchor, min(1, t + dt / 2))
                    dx = (p2[0] - p1[0]) / dt
                    dy = (p2[1] - p1[1]) / dt
                    return (dx, dy)
                except:
                    pass

        except (IndexError, TypeError, ValueError, ZeroDivisionError) as e:
            print(
                f"DEBUG: ⚠️ Error calculating tangent for {rendering_type}: {e}"
            )

        # Ultimate fallback: straight line tangent with anchor points
        dx = target_anchor[0] - source_anchor[0]
        dy = target_anchor[1] - source_anchor[1]
        return (dx, dy)
        """Draw the selection rectangle in screen coordinates (not affected by world rotation)."""

        if not self.selection_rect:
            return

        # The selection rectangle should be drawn outside the world rotation transformation
        # We need to temporarily restore the transformation state to draw in screen coordinates
        restore_state = False
        if self.world_rotation != 0.0 and hasattr(dc, 'GetGraphicsContext'):
            gc = dc.GetGraphicsContext()
            if gc:
                gc.PopState()  # Temporarily exit the rotated world
                restore_state = True

        # Draw selection rectangle in screen coordinates
        dc.SetPen(wx.Pen(wx.Colour(0, 0, 0), 2,
                         wx.PENSTYLE_DOT))  # Black selection border
        dc.SetBrush(wx.Brush(wx.Colour(100, 150, 255,
                                       80)))  # Blue selection fill
        dc.DrawRectangle(self.selection_rect)

        # Restore the rotation transformation if we temporarily removed it
        if restore_state and hasattr(dc, 'GetGraphicsContext'):
            gc = dc.GetGraphicsContext()
            if gc:
                size = self.GetSize()
                center_x = size.width // 2
                center_y = size.height // 2
                gc.PushState()
                gc.Translate(center_x, center_y)
                gc.Rotate(math.radians(self.world_rotation))
                gc.Translate(-center_x, -center_y)

    def start_freeform_composite_segment(self, edge):
        """Start drawing a freeform segment for a composite edge."""

        self.drawing_composite_segment = True
        self.composite_segment_edge = edge
        self.temp_path_points = []
        # Switch to edge tool temporarily
        self.previous_tool = self.get_tool_from_main_window()
        self.tool = "edge"

    def finish_freeform_composite_segment(self):
        """Finish drawing a freeform segment and add it to the composite edge."""

        if self.composite_segment_edge and self.temp_path_points:
            # Convert screen points to world coordinates
            world_points = []
            for point in self.temp_path_points:
                world_points.append((point[0], point[1], 0.0))

            # Add new segment
            new_segment = {
                "type": "freeform",
                "control_points": world_points,
                "weight": 1.0
            }
            self.composite_segment_edge.curve_segments.append(new_segment)

            # Reset state
            self.drawing_composite_segment = False
            self.composite_segment_edge = None
            self.temp_path_points = []
            # Restore previous tool
            if hasattr(self, 'previous_tool'):
                self.tool = self.previous_tool

            # Update display
            self.Refresh()

    def on_size(self, event):
        """Handle resize events."""

        self.Refresh()
        event.Skip()

    def on_left_down(self, event):
        """Handle left mouse button down."""

        print(f"DEBUG: ⬇️ on_left_down triggered at position")
        self.SetFocus()
        pos = event.GetPosition()
        print(f"DEBUG: ⬇️ Mouse down position: {pos.x}, {pos.y}")

        print(f"DEBUG: ⬇️ Tool detected: '{self.tool}'")

        if self.tool == "select":
            # Check if we're in B-spline control point adding mode
            if self.adding_bspline_control_point:
                world_pos = self.screen_to_world(pos.x, pos.y)
                self.add_curve_control_point(world_pos[0], world_pos[1])
                # Stay in adding mode - user must click "End Click" to exit
                print(
                    f"DEBUG: 🌊 Added control point, staying in click mode (use 'End Click' to exit)"
                )
                return

            print(f"DEBUG: ⬇️ Calling handle_select_down")
            self.handle_select_down(pos)
        elif self.tool == "node":
            print(f"DEBUG: ⬇️ Calling handle_node_creation")
            self.handle_node_creation(pos)
        elif self.tool == "edge":
            print(f"DEBUG: ⬇️ Calling handle_edge_creation_start")
            # Clear selection to avoid selected uberedges influencing edge creation hit-tests
            try:
                self.graph.clear_selection()
                self.selection_changed.emit()
            except Exception:
                pass
            self.handle_edge_creation_start(pos)
        elif self.tool == "move":
            print(f"DEBUG: ⬇️ Calling handle_move_down")
            self.handle_move_down(pos)
        elif self.tool == "rotate":
            print(
                f"DEBUG: 🔄 ROTATE WORLD TOOL DETECTED - calling handle_rotate_down"
            )
            self.handle_rotate_down(pos)
        elif self.tool == "rotate_element":
            print(
                f"DEBUG: 🔄 ROTATE ELEMENT TOOL DETECTED in on_left_down - calling handle_rotate_element_down"
            )
            self.handle_rotate_element_down(pos)
        elif self.tool == "drag_into":
            print(
                f"DEBUG: 📦 ============ DRAG INTO CONTAINER TOOL DETECTED ============"
            )
            print(
                f"DEBUG: 📦 Calling handle_drag_into_down at {pos.x}, {pos.y}")
            self.handle_drag_into_down(pos)
        elif self.tool == "expand":
            print(
                f"DEBUG: 📖 EXPAND TOOL DETECTED - calling handle_expand_down")
            self.handle_expand_down(pos)
        elif self.tool == "collapse":
            print(
                f"DEBUG: 📕 COLLAPSE TOOL DETECTED - calling handle_collapse_down"
            )
            self.handle_collapse_down(pos)
        elif self.tool == "recursive_expand":
            print(
                f"DEBUG: 🔄📖 RECURSIVE EXPAND TOOL DETECTED - calling handle_recursive_expand_down"
            )
            self.handle_recursive_expand_down(pos)
        elif self.tool == "recursive_collapse":
            print(
                f"DEBUG: 🔄📕 RECURSIVE COLLAPSE TOOL DETECTED - calling handle_recursive_collapse_down"
            )
            self.handle_recursive_collapse_down(pos)
        else:
            print(f"DEBUG: ❌ Unknown tool: '{self.tool}'")

        print(f"DEBUG: ⬇️ Mouse down complete with tool: {self.tool}")

    def on_left_up(self, event):
        """Handle left mouse button up."""

        pos = event.GetPosition()

        print(f"DEBUG: 🔧 TOOL DETECTED: '{self.tool}' in on_left_up")

        if self.tool == "select":
            print(
                f"DEBUG: 🔗 Select tool up - dragging: {self.dragging}, drag_offset count: {len(self.drag_offset) if self.drag_offset else 0}"
            )
            # Handle select tool mouse up
            self.handle_select_up(pos)
        elif self.tool == "edge":
            if self.drawing_composite_segment:
                self.finish_freeform_composite_segment()
            else:
                self.handle_edge_creation_end(pos)
        elif self.tool == "move":
            self.handle_move_up(pos)
        elif self.tool == "rotate":
            self.handle_rotate_up(pos)
        elif self.tool == "rotate_element":
            self.handle_rotate_element_up(pos)
        elif self.tool == "drag_into":
            print(
                f"DEBUG: 📦 ============ DRAG INTO CONTAINER UP DETECTED ============"
            )
            print(
                f"DEBUG: 📦 About to call handle_drag_into_up with pos ({pos.x}, {pos.y})"
            )
            self.handle_drag_into_up(pos)
        elif self.tool == "expand":
            # No mouse up handling needed for expand (instant action)
            pass
        elif self.tool == "collapse":
            # No mouse up handling needed for collapse (instant action)
            pass
        elif self.tool == "recursive_expand":
            # No mouse up handling needed for recursive expand (instant action)
            pass
        elif self.tool == "recursive_collapse":
            # No mouse up handling needed for recursive collapse (instant action)
            pass

        print(f"DEBUG: Mouse up with tool: {self.tool}")
        print(
            f"DEBUG: 🔗 MOUSE UP CHECK - dragging: {self.dragging}, drag_offset: {len(self.drag_offset) if self.drag_offset else 0}, grid_snapping_enabled: {self.grid_snapping_enabled}"
        )

        # Apply grid snapping to dragged nodes if dragging was active
        if self.dragging and self.drag_offset:
            print(
                f"DEBUG: 🔗 Applying grid snapping to {len(self.drag_offset)} dragged nodes (enabled: {self.grid_snapping_enabled})"
            )

            # Store old positions for custom endpoint updates
            old_positions = {}
            for node_id in self.drag_offset.keys():
                node = self.graph.get_node(node_id)
                if node:
                    old_positions[node_id] = (node.x, node.y)

            # Apply grid snapping
            for node_id in self.drag_offset.keys():
                node = self.graph.get_node(node_id)
                if node:
                    print(
                        f"DEBUG: 🔗 Node {node_id} before snap: ({node.x:.1f}, {node.y:.1f})"
                    )
                    snapped_pos = self.snap_to_grid(node.x, node.y, node.width,
                                                    node.height)
                    node.set_2d_position(snapped_pos[0], snapped_pos[1])
                    print(
                        f"DEBUG: 🔗 Node {node_id} after snap: ({node.x:.1f}, {node.y:.1f})"
                    )

            # Update custom edge endpoints for moved nodes
            if self.grid_snapping_enabled:
                self.update_custom_endpoints_for_moved_nodes(old_positions)
                self.graph_modified.emit()
                self.Refresh()
            # Send final snapped positions to backend
            try:
                mw = self.GetParent()
                backend = getattr(mw, 'backend', None)
                if backend and getattr(backend, 'is_available', lambda: False)():
                    items = []
                    for node_id in list(self.drag_offset.keys()):
                        node = self.graph.get_node(node_id)
                        if node:
                            items.append((node_id, float(node.x), float(node.y)))
                    if items:
                        backend.patch_node_positions(items)
            except Exception:
                pass

        self.dragging = False
        self.dragging_canvas = False
        self.dragging_edge_endpoint = False
        self.dragging_edge = None
        self.dragging_endpoint = None
        self.dragging_rotation = False
        self.dragging_control_point = False
        self.dragging_control_point_edge = None
        self.dragging_control_point_index = -1
        self.dragging_arrow_position = False
        self.dragging_arrow_position_edge = None
        print(
            f"DEBUG: 📦 FINAL CLEANUP - Clearing drag states in on_left_up - was dragging: {self.dragging_into_container}"
        )
        if self.dragging_into_container:
            print(
                f"DEBUG: 📦 ⚠️ WARNING: Clearing dragging_into_container without completing containment!"
            )
        self.dragging_into_container = False
        self.container_target = None
        self.dragging_selection = []
        self.selection_rect = None
        self.drag_offset.clear()
        self.drag_original_positions.clear()

    def on_right_up(self, event):
        """Handle right mouse button up."""
        pos = event.GetPosition()
        print(f"DEBUG: Right button up at ({pos.x}, {pos.y})")
        event.Skip()

    def _show_context_menu(self, pos):
        """Build and show the context menu at the given client position."""
        print(f"DEBUG: Show context menu at ({pos.x}, {pos.y})")

        node = self.get_node_at_position(pos.x, pos.y)
        edge = self.get_edge_at_position(pos.x, pos.y)

        menu = wx.Menu()

        # Ubergraph segment context actions if a segment is selected
        if hasattr(self, 'selected_uber_segment_kind') and self.selected_uber_segment_kind:
            menu.Append(30, "Delete Segment")
            menu.Append(31, "Delete Uberedge")
            def _delete_segment(_evt):
                self.delete_selected_uber_segment()
                # Clear selection
                self.selected_uber_segment_kind = None
                self.selected_uber_segment_edge_id = None
                self.selected_uber_segment_other_edge_id = None
                self.selected_uber_segment_node_id = None
                self.graph_modified.emit()
                self.Refresh()
            def _delete_uberedge(_evt):
                try:
                    if getattr(self, 'selected_uber_segment_edge_id', None):
                        self.graph.remove_edge(self.selected_uber_segment_edge_id)
                        self.graph_modified.emit(); self.Refresh()
                except Exception:
                    pass
            menu.Bind(wx.EVT_MENU, _delete_segment, id=30)
            menu.Bind(wx.EVT_MENU, _delete_uberedge, id=31)
            menu.AppendSeparator()

        if node:
            menu.Append(1, "Edit Node Properties")
            menu.Append(2, "Delete Node")
            menu.AppendSeparator()
            menu.Append(3, "Copy Node")
            # Bind node menu events
            menu.Bind(wx.EVT_MENU, lambda evt: self.on_delete_node(node), id=2)
            menu.Bind(wx.EVT_MENU,
                      lambda evt: self.on_edit_node_properties(node),
                      id=1)
        elif edge:
            menu.Append(4, "Edit Edge Properties")
            menu.Append(5, "Delete Edge")
            menu.AppendSeparator()

            # Edge curve type submenu
            curve_menu = wx.Menu()
            curve_menu.Append(10, "Straight Line")
            curve_menu.Append(11, "Curved/Arc")
            curve_menu.Append(12, "Bézier Curve")
            curve_menu.Append(13, "B-Spline")
            curve_menu.Append(14, "Cubic Spline")
            curve_menu.Append(15, "NURBS")
            curve_menu.Append(16, "Polyline")
            curve_menu.AppendSeparator()
            curve_menu.Append(17, "Use Global Setting")
            menu.AppendSubMenu(curve_menu, "Curve Type")

            # B-spline specific editing options
            edge_type = edge.rendering_type if edge.rendering_type else self.edge_rendering_type
            if edge_type == "bspline":
                menu.AppendSeparator()
                bspline_menu = wx.Menu()
                bspline_menu.Append(20, "Enter B-spline Edit Mode")
                bspline_menu.Append(21, "Exit B-spline Edit Mode")
                bspline_menu.AppendSeparator()
                bspline_menu.Append(22, "Add Control Point (Click Mode)")
                bspline_menu.Append(23, "List Control Points")
                menu.AppendSubMenu(bspline_menu, "B-spline Editing")

                # Bind B-spline menu events
                menu.Bind(wx.EVT_MENU,
                          lambda evt: self.enter_bspline_editing_mode(edge),
                          id=20)
                menu.Bind(wx.EVT_MENU,
                          lambda evt: self.exit_bspline_editing_mode(),
                          id=21)
                menu.Bind(
                    wx.EVT_MENU,
                    lambda evt: self.start_adding_bspline_control_point(),
                    id=22)
                menu.Bind(
                    wx.EVT_MENU,
                    lambda evt: self.show_bspline_control_points_dialog(edge),
                    id=23)

            menu.AppendSeparator()
            menu.Append(6, "Add Control Point")

            # Bind edge menu events
            menu.Bind(wx.EVT_MENU, lambda evt: self.on_delete_edge(edge), id=5)
            menu.Bind(wx.EVT_MENU,
                      lambda evt: self.on_edit_edge_properties(edge),
                      id=4)
            menu.Bind(wx.EVT_MENU,
                      lambda evt: self.set_edge_curve_type(edge, "straight"),
                      id=10)
            menu.Bind(wx.EVT_MENU,
                      lambda evt: self.set_edge_curve_type(edge, "curved"),
                      id=11)
            menu.Bind(wx.EVT_MENU,
                      lambda evt: self.set_edge_curve_type(edge, "bezier"),
                      id=12)
            menu.Bind(wx.EVT_MENU,
                      lambda evt: self.set_edge_curve_type(edge, "bspline"),
                      id=13)
            menu.Bind(
                wx.EVT_MENU,
                lambda evt: self.set_edge_curve_type(edge, "cubic_spline"),
                id=14)
            menu.Bind(wx.EVT_MENU,
                      lambda evt: self.set_edge_curve_type(edge, "nurbs"),
                      id=15)
            menu.Bind(wx.EVT_MENU,
                      lambda evt: self.set_edge_curve_type(edge, "polyline"),
                      id=16)
            menu.Bind(wx.EVT_MENU,
                      lambda evt: self.set_edge_curve_type(edge, None),
                      id=17)
        else:
            # Check if we have selections to delete
            selected_nodes = self.graph.get_selected_nodes()
            selected_edges = self.graph.get_selected_edges()

            if selected_nodes or selected_edges:
                menu.Append(9, "Delete Selection")
                menu.AppendSeparator()
                # Bind selection delete event
                menu.Bind(wx.EVT_MENU,
                          lambda evt: self.on_delete_selection(),
                          id=9)

            menu.Append(7, "Add Node Here")
            menu.AppendSeparator()
            menu.Append(8, "Paste")
            # Bind general menu events
            menu.Bind(wx.EVT_MENU,
                      lambda evt: self.on_add_node_here(pos),
                      id=7)

        self.PopupMenu(menu)
        menu.Destroy()

    def on_right_down(self, event):
        """Handle right mouse button down."""
        pos = event.GetPosition()
        self._show_context_menu(pos)

    def on_context_menu(self, event):
        """Handle system context menu (ctrl-click, long-press, etc.)."""
        # Try to get event-local position; fallback to current mouse position in client coords
        pos = event.GetPosition()
        try:
            if not pos or (pos.x == wx.DefaultCoord
                           and pos.y == wx.DefaultCoord):
                global_pos = wx.GetMousePosition()
                pos = self.ScreenToClient(global_pos)
        except Exception:
            try:
                global_pos = wx.GetMousePosition()
                pos = self.ScreenToClient(global_pos)
            except Exception:
                pos = wx.Point(0, 0)
        self._show_context_menu(pos)

    def on_edit_node_properties(self, node):
        """Open the full Node Properties dialog for a node (context menu)."""
        try:
            from graph_canvas.presentation.desktop.gui.dialogs import NodePropertiesDialog
        except Exception as _e:
            return
        dialog = NodePropertiesDialog(self, node)
        # Apply theme if available
        try:
            main_window = self.GetParent().GetParent()
            if hasattr(main_window, 'apply_theme_to_dialog'):
                main_window.apply_theme_to_dialog(dialog)
        except Exception:
            pass
        if dialog.ShowModal() == wx.ID_OK:
            # Node was updated by dialog
            self.graph_modified.emit()
            self.Refresh()
        dialog.Destroy()

    def on_edit_edge_properties(self, edge):
        """Open the full Edge Properties dialog for an edge (context menu)."""
        try:
            from graph_canvas.presentation.desktop.gui.dialogs import EdgePropertiesDialog
        except Exception as _e:
            return
        dialog = EdgePropertiesDialog(self, edge)
        # Apply theme if available
        try:
            main_window = self.GetParent().GetParent()
            if hasattr(main_window, 'apply_theme_to_dialog'):
                main_window.apply_theme_to_dialog(dialog)
        except Exception:
            pass
        if dialog.ShowModal() == wx.ID_OK:
            # Edge was updated by dialog
            self.graph_modified.emit()
            self.Refresh()
        dialog.Destroy()

    def on_delete_node(self, node):
        """Delete a specific node from context menu."""

        print(f"DEBUG: Deleting node {node.id} from context menu")

        if self.undo_redo_manager:
            command = m_commands.DeleteNodeCommand(self.graph, node.id)
            self.undo_redo_manager.execute_command(command)
        else:
            # Fallback if no undo manager
            self.graph.remove_node(node.id)

        self.graph_modified.emit()
        self.Refresh()

    def on_delete_edge(self, edge):
        """Delete a specific edge from context menu."""

        print(f"DEBUG: Deleting edge {edge.id} from context menu")

        if self.undo_redo_manager:
            command = m_commands.DeleteEdgeCommand(self.graph, edge.id)
            self.undo_redo_manager.execute_command(command)
        else:
            # Fallback if no undo manager
            self.graph.remove_edge(edge.id)

        self.graph_modified.emit()
        self.Refresh()

    def on_delete_selection(self):
        """Delete all selected items from context menu."""

        print("DEBUG: Deleting selection from context menu")

        # First, if an uberedge segment is selected, remove that segment
        try:
            if hasattr(self, 'selected_uber_segment_kind') and self.selected_uber_segment_kind:
                self.delete_selected_uber_segment()
                # Clear segment selection and refresh
                self.selected_uber_segment_kind = None
                self.selected_uber_segment_edge_id = None
                self.selected_uber_segment_node_id = None
                self.selected_uber_segment_other_edge_id = None
                self.graph_modified.emit()
                self.Refresh()
                return
        except Exception as _e:
            print(f"DEBUG: ⚠️ Error deleting selected uber segment: {_e}")

        if self.undo_redo_manager:
            # Create composite command for multiple deletions
            commands = []

            # Add delete commands for selected nodes (do edges first to avoid orphaned edges)
            selected_edges = self.graph.get_selected_edges()
            for edge in selected_edges:
                commands.append(
                    m_commands.DeleteEdgeCommand(self.graph, edge.id))

            selected_nodes = self.graph.get_selected_nodes()
            for node in selected_nodes:
                commands.append(
                    m_commands.DeleteNodeCommand(self.graph, node.id))

            if commands:
                composite_command = m_commands.CompositeCommand(
                    "Delete Selection", commands)
                self.undo_redo_manager.execute_command(composite_command)
        else:
            # Fallback if no undo manager
            self.graph.delete_selected()

        self.graph_modified.emit()
        self.Refresh()

    def delete_selected_uber_segment(self):
        """Delete the currently selected uberedge segment (edge↔edge or node↔edge)."""
        try:
            kind = getattr(self, 'selected_uber_segment_kind', None)
            if not kind:
                return
            eid = getattr(self, 'selected_uber_segment_edge_id', None)
            if not eid:
                return
            edge = self.graph.get_edge(eid)
            if not edge or not getattr(edge, 'is_hyperedge', False):
                return
            if kind == 'edge':
                other_id = getattr(self, 'selected_uber_segment_other_edge_id', None)
                if not other_id:
                    return
                if hasattr(edge, 'metadata') and isinstance(edge.metadata, dict):
                    lst = edge.metadata.get('connected_uberedges') or []
                    edge.metadata['connected_uberedges'] = [x for x in lst if x != other_id]
                    amap = edge.metadata.get('arrow_pos_edges') or {}
                    if other_id in amap:
                        del amap[other_id]
                    if str(other_id) in amap:
                        del amap[str(other_id)]
                    edge.metadata['arrow_pos_edges'] = amap
            elif kind == 'node':
                node_id = getattr(self, 'selected_uber_segment_node_id', None)
                if not node_id:
                    return
                # Remove from source_ids/target_ids if present
                if hasattr(edge, 'source_ids') and isinstance(edge.source_ids, list):
                    edge.source_ids = [nid for nid in edge.source_ids if nid != node_id]
                if hasattr(edge, 'target_ids') and isinstance(edge.target_ids, list):
                    edge.target_ids = [nid for nid in edge.target_ids if nid != node_id]
                # Also clear single source_id/target_id if they match
                if getattr(edge, 'source_id', None) == node_id:
                    edge.source_id = None
                if getattr(edge, 'target_id', None) == node_id:
                    edge.target_id = None
                # Remove any per-node arrow position
                if hasattr(edge, 'metadata') and isinstance(edge.metadata, dict):
                    nmap = edge.metadata.get('arrow_pos_nodes') or {}
                    if node_id in nmap:
                        del nmap[node_id]
                    if str(node_id) in nmap:
                        del nmap[str(node_id)]
                    edge.metadata['arrow_pos_nodes'] = nmap
        except Exception as _e:
            print(f"DEBUG: ⚠️ Error deleting uber segment: {_e}")

    def handle_node_creation(self, pos):
        """Handle node creation when node tool is selected."""

        print(f"DEBUG: 🆕 handle_node_creation called at pos {pos.x}, {pos.y}")

        # Always use the cursor's world position for node placement (independent of zoom center lock)
        world_pos = self.screen_to_world(pos.x, pos.y)
        print(
            f"DEBUG: 🖱️ MOUSE NODE PLACEMENT: screen=({pos.x}, {pos.y}) -> world={world_pos}"
        )

        print(f"DEBUG: 🌍 World pos before snap: {world_pos}")

        # Apply grid snapping if enabled (respect the unified grid_snapping_enabled flag)
        if getattr(self, 'grid_snapping_enabled', False):
            world_pos = self.snap_to_grid_position(world_pos[0], world_pos[1])
            print(f"DEBUG: 📍 After snapping: {world_pos}")

        # Create node locally
        node = m_node.Node(x=world_pos[0], y=world_pos[1], text="New Node")

        if self.undo_redo_manager:
            command = m_commands.AddNodeCommand(self.graph, node)
            self.undo_redo_manager.execute_command(command)
        else:
            # Fallback if no undo manager
            self.graph.add_node(node)

        # Try to create node in backend, ignoring errors for offline mode
        try:
            mw = self.GetParent()
            backend = getattr(mw, 'backend', None)
            if backend and getattr(backend, 'is_available', lambda: False)():
                backend.create_node(float(node.x), float(node.y), node.text)
        except Exception:
            pass
        print(f"DEBUG: Created new node {node.id} at position {world_pos} with node tool")
        self.graph_modified.emit()
        self.Refresh()

    def on_add_node_here(self, pos):
        """Add a new node at the specified position."""

        world_pos = self.screen_to_world(pos.x, pos.y)

        # Apply grid snapping if enabled
        print(
            f"DEBUG: 📍 Add node here at world_pos: {world_pos}, grid_snapping_enabled: {self.grid_snapping_enabled}"
        )
        if getattr(self, 'grid_snapping_enabled', False):
            snapped_pos = self.snap_to_grid_position(world_pos[0],
                                                     world_pos[1])
        else:
            snapped_pos = world_pos
        print(f"DEBUG: 📍 After snapping: {snapped_pos}")

        # Create node locally
        node = m_node.Node(x=snapped_pos[0], y=snapped_pos[1], text="New Node")

        if self.undo_redo_manager:
            command = m_commands.AddNodeCommand(self.graph, node)
            self.undo_redo_manager.execute_command(command)
        else:
            # Fallback if no undo manager
            self.graph.add_node(node)

        # Try to create node in backend
        try:
            mw = self.GetParent()
            backend = getattr(mw, 'backend', None)
            if backend and getattr(backend, 'is_available', lambda: False)():
                backend.create_node(float(node.x), float(node.y), node.text)
        except Exception:
            pass
        print(f"DEBUG: Added new node {node.id} at position {world_pos}")
        self.graph_modified.emit()
        self.Refresh()

    def get_tool_from_main_window(self):
        """Get current tool from main window."""

        try:
            # GraphCanvas -> main_panel -> MainWindow
            main_window = self.GetParent().GetParent()
            if hasattr(main_window,
                       'tool_select') and main_window.tool_select.GetValue():
                return "select"
            elif hasattr(main_window,
                         'tool_node') and main_window.tool_node.GetValue():
                return "node"
            elif hasattr(main_window,
                         'tool_edge') and main_window.tool_edge.GetValue():
                return "edge"
            elif hasattr(main_window,
                         'tool_move') and main_window.tool_move.GetValue():
                return "move"
            elif hasattr(main_window,
                         'tool_rotate') and main_window.tool_rotate.GetValue():
                print(f"DEBUG: 🎯 ROTATE WORLD TOOL IS SELECTED!")
                return "rotate"
            elif hasattr(main_window, 'tool_rotate_element'
                         ) and main_window.tool_rotate_element.GetValue():
                print(f"DEBUG: 🎯 ROTATE ELEMENT TOOL IS SELECTED!")
                return "rotate_element"
            elif hasattr(main_window, 'tool_drag_into'
                         ) and main_window.tool_drag_into.GetValue():
                print(f"DEBUG: 📦 DRAG INTO CONTAINER TOOL IS SELECTED!")
                return "drag_into"
            elif hasattr(main_window,
                         'tool_expand') and main_window.tool_expand.GetValue():
                print(f"DEBUG: 📖 EXPAND TOOL IS SELECTED!")
                return "expand"
            elif hasattr(
                    main_window,
                    'tool_collapse') and main_window.tool_collapse.GetValue():
                print(f"DEBUG: 📕 COLLAPSE TOOL IS SELECTED!")
                return "collapse"
            elif hasattr(main_window, 'tool_recursive_expand'
                         ) and main_window.tool_recursive_expand.GetValue():
                print(f"DEBUG: 🔄📖 RECURSIVE EXPAND TOOL IS SELECTED!")
                return "recursive_expand"
            elif hasattr(main_window, 'tool_recursive_collapse'
                         ) and main_window.tool_recursive_collapse.GetValue():
                print(f"DEBUG: 🔄📕 RECURSIVE COLLAPSE TOOL IS SELECTED!")
                return "recursive_collapse"
        except Exception as e:
            print(f"DEBUG: Error getting tool from main window: {e}")
            return "select"  # Default fallback

    def on_motion(self, event):
        """Handle mouse motion."""

        pos = event.GetPosition()

        # Track current mouse position for zoom centering
        self.current_mouse_pos = pos

        if self.tool == "select":
            self.handle_select_motion(pos)
        elif self.tool == "edge":
            if self.drawing_composite_segment:
                # Add point to composite segment path
                world_pos = self.screen_to_world(pos.x, pos.y)
                self.temp_path_points.append((world_pos[0], world_pos[1], 0.0))
            elif self.edge_start_node:
                if self.edge_rendering_type == "freeform" and self.temp_edge:
                    # Convert screen coordinates to world coordinates
                    world_pos = self.screen_to_world(pos.x, pos.y)
                    # Add point to path
                    self.temp_path_points.append(
                        (world_pos[0], world_pos[1], 0.0))
                    self.temp_edge.freeform_points = self.temp_path_points
            self.Refresh()  # Refresh to update temporary edge
        elif self.tool == "move":
            self.handle_move_motion(pos)
        elif self.tool == "rotate":
            print(
                f"DEBUG: 🔄 ROTATE WORLD MOTION - calling handle_rotate_motion at {pos.x}, {pos.y}"
            )
            self.handle_rotate_motion(pos)
        elif self.tool == "rotate_element":
            print(
                f"DEBUG: 🔄 ROTATE ELEMENT MOTION - calling handle_rotate_element_motion at {pos.x}, {pos.y}"
            )
            self.handle_rotate_element_motion(pos)
        elif self.tool == "drag_into":
            print(f"DEBUG: 📦 DRAG INTO MOTION at {pos.x}, {pos.y}")
            self.handle_drag_into_motion(pos)

    def on_right_down(self, event):
        """Handle right mouse button down events."""

        pos = event.GetPosition()
        print(f"DEBUG: Right click at ({pos.x}, {pos.y})")

        # Check if we clicked on a node or edge
        clicked_node = self.get_node_at_position(pos.x, pos.y)
        clicked_edge = self.get_edge_at_position(pos.x, pos.y)

        # Create context menu
        menu = wx.Menu()

        # Add view information submenu
        view_menu = wx.Menu()

        # Get canvas size and center
        size = self.GetSize()
        center_x = size.width / 2
        center_y = size.height / 2

        # Convert screen center to world coordinates
        world_center_x = (center_x - self.pan_x) / self.zoom
        world_center_y = (center_y - self.pan_y) / self.zoom

        # Calculate world dimensions
        world_width = size.width / self.zoom
        world_height = size.height / self.zoom

        # Add view information items
        view_menu.Append(
            wx.ID_ANY, f"Center: ({world_center_x:.1f}, {world_center_y:.1f})")
        view_menu.Append(
            wx.ID_ANY, f"World Size: {world_width:.1f} x {world_height:.1f}")
        view_menu.Append(wx.ID_ANY,
                         f"Screen Size: {size.width} x {size.height}")
        view_menu.Append(wx.ID_ANY, f"Zoom: {self.zoom:.2f}x")
        # If clicking on an item, show its ID for quick reference
        if clicked_node and hasattr(clicked_node, 'id'):
            view_menu.Append(wx.ID_ANY, f"Node ID: {clicked_node.id}")
        if clicked_edge and hasattr(clicked_edge, 'id'):
            view_menu.Append(wx.ID_ANY, f"Edge ID: {clicked_edge.id}")
        menu.AppendSubMenu(view_menu, "View Information")
        menu.AppendSeparator()

        # Add hyperedge options if applicable
        if clicked_edge and clicked_edge.is_hyperedge:
            # Split arrows toggle
            split_arrows_item = menu.AppendCheckItem(wx.ID_ANY, "Split Arrows")
            split_arrows_item.Check(clicked_edge.split_arrows)

            def on_toggle_split(event):
                clicked_edge.split_arrows = not clicked_edge.split_arrows
                self.Refresh()

            self.Bind(wx.EVT_MENU, on_toggle_split, split_arrows_item)
            menu.AppendSeparator()

        if clicked_node:
            print(f"DEBUG: Right-clicked on node: {clicked_node.text}")
            # Node context menu
            edit_node_id = wx.NewId()
            delete_node_id = wx.NewId()
            menu.Append(edit_node_id, "Edit Node Properties")
            menu.Append(delete_node_id, "Delete Node")
            self.Bind(wx.EVT_MENU,
                      lambda evt: self.on_edit_node_properties(clicked_node),
                      id=edit_node_id)
            self.Bind(
                wx.EVT_MENU,
                lambda evt: self.delete_node_context_menu(clicked_node.id),
                id=delete_node_id)

        elif clicked_edge:
            print(f"DEBUG: Right-clicked on edge")
            # Edge context menu
            edit_edge_id = wx.NewId()
            delete_edge_id = wx.NewId()
            menu.Append(edit_edge_id, "Edit Edge Properties")
            menu.Append(delete_edge_id, "Delete Edge")
            self.Bind(wx.EVT_MENU,
                      lambda evt: self.on_edit_edge_properties(clicked_edge),
                      id=edit_edge_id)
            self.Bind(
                wx.EVT_MENU,
                lambda evt: self.delete_edge_context_menu(clicked_edge.id),
                id=delete_edge_id)

        else:
            print(f"DEBUG: Right-clicked on empty space")
            # General context menu
            if self.has_selected_items():
                delete_selected_id = wx.NewId()
                menu.Append(delete_selected_id, "Delete Selected Items")
                self.Bind(wx.EVT_MENU,
                          lambda evt: self.delete_selected_context_menu(),
                          id=delete_selected_id)

        # Only show menu if it has items
        if menu.GetMenuItemCount() > 0:
            # Important: Don't call event.Skip() to prevent any additional event handling
            # that might interfere with zoom
            self.PopupMenu(menu, pos)
            menu.Destroy()
        else:
            # If no menu items, still consume the event to prevent weird behavior
            pass

        # Explicitly do NOT call event.Skip() here to prevent the right-click
        # from causing any unwanted side effects

    def delete_node_context_menu(self, node_id):
        """Delete a node via context menu."""

        print(f"DEBUG: Deleting node {node_id} via context menu")
        if self.undo_redo_manager:
            command = m_commands.DeleteNodeCommand(self.graph, node_id)
            self.undo_redo_manager.execute_command(command)
        else:
            # Fallback if no undo manager
            self.graph.remove_node(node_id)
            self.graph_modified.emit()
        self.Refresh()

    def delete_edge_context_menu(self, edge_id):
        """Delete an edge via context menu."""

        print(f"DEBUG: Deleting edge {edge_id} via context menu")
        if self.undo_redo_manager:
            command = m_commands.DeleteEdgeCommand(self.graph, edge_id)
            self.undo_redo_manager.execute_command(command)
        else:
            # Fallback if no undo manager
            self.graph.remove_edge(edge_id)
            self.graph_modified.emit()
        self.Refresh()

    def delete_selected_context_menu(self):
        """Delete all selected items via context menu."""

        print(f"DEBUG: Deleting selected items via context menu")
        selected_nodes = [
            node for node in self.graph.get_all_nodes() if node.selected
        ]
        selected_edges = [
            edge for edge in self.graph.get_all_edges() if edge.selected
        ]

        if selected_nodes or selected_edges:
            commands = []

            # Add delete commands for selected edges first
            for edge in selected_edges:
                commands.append(
                    m_commands.DeleteEdgeCommand(self.graph, edge.id))

            # Add delete commands for selected nodes
            for node in selected_nodes:
                commands.append(
                    m_commands.DeleteNodeCommand(self.graph, node.id))

            if commands and self.undo_redo_manager:
                composite_command = m_commands.CompositeCommand(
                    "Delete Selection", commands)
                self.undo_redo_manager.execute_command(composite_command)
            else:
                # Fallback if no undo manager
                for edge in selected_edges:
                    self.graph.remove_edge(edge.id)
                for node in selected_nodes:
                    self.graph.remove_node(node.id)
                self.graph_modified.emit()

        self.Refresh()

    def has_selected_items(self):
        """Check if there are any selected items."""

        return any(node.selected for node in self.graph.get_all_nodes()) or \
               any(edge.selected for edge in self.graph.get_all_edges())

    def on_key_down(self, event):
        """Handle key down events."""

        keycode = event.GetKeyCode()

        if keycode == wx.WXK_DELETE:
            self.graph.delete_selected()
            self.graph_modified.emit()
            self.Refresh()
        elif keycode == wx.WXK_ESCAPE:
            self.graph.clear_selection()
            self.selection_changed.emit()
            self.Refresh()

        event.Skip()

    def on_double_click(self, event):
        """Handle double click events."""

        pos = event.GetPosition()
        node = self.get_node_at_position(pos.x, pos.y)

        if node:
            # Open text editing dialog
            dialog = wx.TextEntryDialog(self, "Enter node text:", "Edit Node",
                                        node.text)
            if dialog.ShowModal() == wx.ID_OK:
                new_text = dialog.GetValue()
                old_text = node.text

                # Use undo system for text changes
                if self.undo_redo_manager and new_text != old_text:
                    command = m_commands.EditPropertiesCommand(
                        node, {'text': old_text}, {'text': new_text},
                        f"Edit Node Text")
                    self.undo_redo_manager.execute_command(command)
                else:
                    # Fallback if no undo manager
                    node.set_text(new_text)

                self.graph.modified = True
                self.graph_modified.emit()
                self.Refresh()
            dialog.Destroy()
        else:
            # Double-click on empty space - create a new node
            world_pos = self.screen_to_world(pos.x, pos.y)

            # Create node using command pattern
            from graph_canvas.presentation.desktop.models.node import Node
            node = m_node.Node(x=world_pos[0], y=world_pos[1], text="New Node")

            if self.undo_redo_manager:
                command = m_commands.AddNodeCommand(self.graph, node)
                self.undo_redo_manager.execute_command(command)
            else:
                # Fallback if no undo manager
                self.graph.add_node(node)

            print(
                f"DEBUG: Created new node {node.id} at position {world_pos} via double-click"
            )
            self.graph_modified.emit()
            self.Refresh()

    def handle_select_down(self, pos):
        """Handle select tool mouse down."""

        # First check if clicking on arrow position control point
        arrow_control_edge = self.get_arrow_position_control_at_position(
            pos.x, pos.y)
        if arrow_control_edge:
            print(
                f"DEBUG: 🟡 Starting to drag arrow position control of edge {arrow_control_edge.id}"
            )
            self.dragging_arrow_position = True
            self.dragging_arrow_position_edge = arrow_control_edge
            self.drag_start_pos = pos
            return

        # Check for control point dragging
        control_info = self.get_control_point_at_position(pos.x, pos.y)
        if control_info is not None:  # Explicitly check for None
            try:
                edge, control_index = control_info
                if edge is not None and control_index is not None:  # Make sure we have valid info
                    print(
                        f"DEBUG: 🎛️ Starting to drag control point {control_index} of edge {edge.id}"
                    )
                    self.dragging_control_point = True
                    self.dragging_control_point_edge = edge
                    self.dragging_control_point_index = control_index
                    self.drag_start_pos = pos
                    return
            except (TypeError, ValueError) as e:
                print(f"DEBUG: ❌ Error unpacking control point info: {e}")
                # Continue with other checks if control point handling fails

        # Check for edge endpoint dragging
        endpoint_info = self.get_edge_endpoint_at_position(pos.x, pos.y)
        if endpoint_info:
            edge, endpoint = endpoint_info
            print(
                f"DEBUG: Starting to drag {endpoint} endpoint of edge {edge.id}"
            )
            self.dragging_edge_endpoint = True
            self.dragging_edge = edge
            self.dragging_endpoint = endpoint
            self.drag_start_pos = pos
            return

        # Check for node or edge selection
        node = self.get_node_at_position(pos.x, pos.y)
        edge = self.get_edge_at_position(pos.x, pos.y)

        if node:
            # Node selection/dragging
            if not wx.GetKeyState(wx.WXK_CONTROL):
                if not node.selected:
                    self.graph.clear_selection()
                    self.graph.select_node(node.id)
                    self.selection_changed.emit()
            else:
                # Toggle selection
                if node.selected:
                    self.graph.deselect_node(node.id)
                else:
                    self.graph.select_node(node.id)
                self.selection_changed.emit()

            # Defer grid snapping until mouse-up; keep drag smooth and cursor-following

            # Start dragging (node(s))
            self.dragging = True
            self.drag_start_pos = pos
            world_pos = self.screen_to_world(pos.x, pos.y)
            # Anchor the node under the cursor so it follows the cursor directly
            anchor_node = self.get_node_at_position(pos.x, pos.y)
            self.drag_anchor_node_id = anchor_node.id if anchor_node else None
            self.drag_offset.clear()
            self.drag_original_positions.clear()
            for selected_node in self.graph.get_selected_nodes():
                if getattr(self, 'drag_anchor_node_id',
                           None) == selected_node.id:
                    # No offset for the node under the cursor: center follows cursor
                    self.drag_offset[selected_node.id] = (0.0, 0.0)
                else:
                    self.drag_offset[selected_node.id] = (selected_node.x -
                                                          world_pos[0],
                                                          selected_node.y -
                                                          world_pos[1])
                    self.drag_original_positions[selected_node.id] = (
                        selected_node.x, selected_node.y)
            print(f"DEBUG: Starting drag with {len(self.drag_offset)} nodes")
            # Clear any in-progress selection rectangle when starting a drag
            self.selection_start = None
            self.selection_rect = None
            # Capture mouse to ensure we receive move/up even if cursor leaves canvas
            try:
                if not self.HasCapture():
                    self.CaptureMouse()
            except Exception:
                pass
            self.Refresh()
            return
        elif edge:
            # Edge selection
            print(f"DEBUG: Clicking on edge {edge.id}")
            if not wx.GetKeyState(wx.WXK_CONTROL):
                print("DEBUG: Clearing selection (no Ctrl held)")
                self.graph.clear_selection()

            # Find all connected hyperedges
            connected_edges = set()
            if edge.is_hyperedge:
                for other_edge in self.graph.get_all_edges():
                    if other_edge.is_hyperedge and edge.shares_nodes_with(
                            other_edge):
                        connected_edges.add(other_edge)

            if edge.selected:
                print(f"DEBUG: Deselecting edge {edge.id} and connected edges")
                self.graph.deselect_edge(edge.id)
                for connected_edge in connected_edges:
                    self.graph.deselect_edge(connected_edge.id)
            else:
                print(f"DEBUG: Selecting edge {edge.id} and connected edges")
                self.graph.select_edge(edge.id)
                for connected_edge in connected_edges:
                    self.graph.select_edge(connected_edge.id)
            self.selection_changed.emit()
        else:
            # Start selection rectangle or canvas panning
            if wx.GetKeyState(wx.WXK_SPACE):
                self.dragging_canvas = True
                self.drag_start_pos = pos
            else:
                if not wx.GetKeyState(wx.WXK_CONTROL):
                    print(
                        "DEBUG: Clicking on empty space - clearing selection")
                    self.graph.clear_selection()
                    self.selection_changed.emit()

                self.selection_start = pos
                self.selection_rect = wx.Rect(pos.x, pos.y, 0, 0)

        # Then check if clicking on edge endpoint dot
        endpoint_info = self.get_edge_endpoint_at_position(pos.x, pos.y)
        if endpoint_info:
            edge, endpoint = endpoint_info
            print(
                f"DEBUG: Starting to drag {endpoint} endpoint of edge {edge.id}"
            )
            self.dragging_edge_endpoint = True
            self.dragging_edge = edge
            self.dragging_endpoint = endpoint
            self.drag_start_pos = pos
            return

        node = self.get_node_at_position(pos.x, pos.y)
        edge = self.get_edge_at_position(pos.x, pos.y)

        if node:
            # Node selection/dragging
            ctrl = wx.GetKeyState(wx.WXK_CONTROL)
            if not ctrl:
                if not node.selected:
                    self.graph.clear_selection()
                    self.graph.select_node(node.id)
                    self.selection_changed.emit()
            else:
                # Toggle selection
                if node.selected:
                    self.graph.deselect_node(node.id)
                else:
                    self.graph.select_node(node.id)
                self.selection_changed.emit()

            # Start dragging (node)
            self.dragging = True
            self.drag_start_pos = pos

            # Calculate drag offsets and store original positions for all selected nodes
            world_pos = self.screen_to_world(pos.x, pos.y)
            anchor_node = self.get_node_at_position(pos.x, pos.y)
            self.drag_anchor_node_id = anchor_node.id if anchor_node else None
            self.drag_offset.clear()
            self.drag_original_positions.clear()

            for selected_node in self.graph.get_selected_nodes():
                if getattr(self, 'drag_anchor_node_id',
                           None) == selected_node.id:
                    self.drag_offset[selected_node.id] = (0.0, 0.0)
                else:
                    self.drag_offset[selected_node.id] = (selected_node.x -
                                                          world_pos[0],
                                                          selected_node.y -
                                                          world_pos[1])
                    self.drag_original_positions[selected_node.id] = (
                        selected_node.x, selected_node.y)
            try:
                if not self.HasCapture():
                    self.CaptureMouse()
            except Exception:
                pass

        elif edge:
            # Edge selection
            print(f"DEBUG: Clicking on edge {edge.id}")
            if not wx.GetKeyState(wx.WXK_CONTROL):
                print("DEBUG: Clearing selection (no Ctrl held)")
                self.graph.clear_selection()

            # Find all connected hyperedges
            connected_edges = set()
            if edge.is_hyperedge:
                for other_edge in self.graph.get_all_edges():
                    if other_edge.is_hyperedge and edge.shares_nodes_with(
                            other_edge):
                        connected_edges.add(other_edge)

            if edge.selected:
                print(f"DEBUG: Deselecting edge {edge.id} and connected edges")
                self.graph.deselect_edge(edge.id)
                for connected_edge in connected_edges:
                    self.graph.deselect_edge(connected_edge.id)
            else:
                print(f"DEBUG: Selecting edge {edge.id} and connected edges")
                self.graph.select_edge(edge.id)
                for connected_edge in connected_edges:
                    self.graph.select_edge(connected_edge.id)
            self.selection_changed.emit()

            # Start dragging (edge)
            self.dragging = True
            self.dragging_edge = edge
            self.drag_start_pos = pos
            # Cancel rectangle selection
            self.selection_start = None
            self.selection_rect = None
            try:
                if not self.HasCapture():
                    self.CaptureMouse()
            except Exception:
                pass

            # For ubergraph edges, also start endpoint dragging to enable movement
            if edge.is_hyperedge and edge.hyperedge_visualization == "ubergraph":
                self.dragging_edge_endpoint = True
                self.dragging_endpoint = "ubergraph"  # Special case for ubergraph movement

        else:
            # Start selection rectangle or canvas panning or group drag
            if wx.GetKeyState(wx.WXK_SPACE):
                self.dragging_canvas = True
                self.drag_start_pos = pos
            else:
                # If clicking inside the bounding box of the current selection, start a group drag
                selected_nodes = list(self.graph.get_selected_nodes())
                if selected_nodes:
                    min_x = min_y = float('inf')
                    max_x = max_y = float('-inf')
                    for n in selected_nodes:
                        sx, sy = self.world_to_screen(n.x, n.y)
                        if sx < min_x: min_x = sx
                        if sy < min_y: min_y = sy
                        if sx > max_x: max_x = sx
                        if sy > max_y: max_y = sy
                    # Add a small margin
                    margin = 8
                    min_x -= margin
                    min_y -= margin
                    max_x += margin
                    max_y += margin
                    if min_x <= pos.x <= max_x and min_y <= pos.y <= max_y:
                        # Begin group drag for all selected nodes
                        self.dragging = True
                        self.drag_start_pos = pos
                        world_pos = self.screen_to_world(pos.x, pos.y)
                        self.drag_anchor_node_id = None
                        self.drag_offset.clear()
                        self.drag_original_positions.clear()
                        for sn in selected_nodes:
                            self.drag_offset[sn.id] = (sn.x - world_pos[0],
                                                       sn.y - world_pos[1])
                            self.drag_original_positions[sn.id] = (sn.x, sn.y)
                        # Cancel any selection rectangle
                        self.selection_start = None
                        self.selection_rect = None
                        try:
                            if not self.HasCapture():
                                self.CaptureMouse()
                        except Exception:
                            pass
                        self.Refresh()
                        return

                if not wx.GetKeyState(wx.WXK_CONTROL):
                    print(
                        "DEBUG: Clicking on empty space - clearing selection")
                    self.graph.clear_selection()
                    self.selection_changed.emit()

                self.selection_start = pos
                self.selection_rect = wx.Rect(pos.x, pos.y, 0, 0)

        self.Refresh()

    def handle_select_up(self, pos):
        """Handle select tool mouse up."""

        # Handle selection rectangle
        if self.selection_rect and self.selection_start:
            # Only select items if the user actually dragged to create a meaningful rectangle
            if self.selection_rect.width > 5 or self.selection_rect.height > 5:
                print(
                    f"DEBUG: Rectangle selection with size {self.selection_rect.width}x{self.selection_rect.height}"
                )
                # Select nodes and edges within rectangle
                self.select_items_in_rect(self.selection_rect)
            else:
                print(
                    f"DEBUG: Single click detected (rectangle too small: {self.selection_rect.width}x{self.selection_rect.height})"
                )

            # Clear selection rectangle
            self.selection_rect = None
            self.selection_start = None
            self.Refresh()
            return

        # Handle edge endpoint reconnection
        if self.dragging_edge_endpoint and self.dragging_edge:
            target_node = self.get_node_at_position(pos.x, pos.y)
            if target_node:
                print(
                    f"DEBUG: Reconnecting {self.dragging_endpoint} of edge {self.dragging_edge.id} to node {target_node.id}"
                )

                if self.dragging_endpoint in ['from', 'to']:
                    # Handle hyperedge connection point
                    if self.dragging_endpoint == 'from':
                        self.dragging_edge.add_from_node(target_node.id)
                    else:  # 'to'
                        self.dragging_edge.add_to_node(target_node.id)

                    self.graph.modified = True
                    self.graph_modified.emit()
                elif self.dragging_endpoint.startswith(
                        'source_') or self.dragging_endpoint.startswith(
                            'target_'):
                    # Handle hyperedge anchor point
                    try:
                        index = int(self.dragging_endpoint.split('_')[1])
                        if self.dragging_endpoint.startswith('source_'):
                            # Update source node
                            if index == 0:
                                # Main source node
                                old_source_id = self.dragging_edge.source_id
                                self.dragging_edge.source_id = target_node.id
                                # Update source_ids list if it contains the old source
                                if old_source_id in self.dragging_edge.source_ids:
                                    self.dragging_edge.source_ids[
                                        self.dragging_edge.source_ids.index(
                                            old_source_id)] = target_node.id
                            elif index - 1 < len(
                                    self.dragging_edge.source_ids):
                                # Additional source node
                                self.dragging_edge.source_ids[
                                    index - 1] = target_node.id
                        else:  # target_N
                            # Update target node
                            if index == 0:
                                # Main target node
                                old_target_id = self.dragging_edge.target_id
                                self.dragging_edge.target_id = target_node.id
                                # Update target_ids list if it contains the old target
                                if old_target_id in self.dragging_edge.target_ids:
                                    self.dragging_edge.target_ids[
                                        self.dragging_edge.target_ids.index(
                                            old_target_id)] = target_node.id
                            elif index - 1 < len(
                                    self.dragging_edge.target_ids):
                                # Additional target node
                                self.dragging_edge.target_ids[
                                    index - 1] = target_node.id

                        self.graph.modified = True
                        self.graph_modified.emit()
                    except (ValueError, IndexError):
                        print(
                            f"DEBUG: Invalid hyperedge endpoint index: {self.dragging_endpoint}"
                        )
                else:
                    # Handle regular endpoint reconnection
                    # Store old connection for undo
                    old_source_id = self.dragging_edge.source_id
                    old_target_id = self.dragging_edge.target_id

                # Determine new connection
                if self.dragging_endpoint == 'source':
                    new_source_id = target_node.id
                    new_target_id = old_target_id
                    print(
                        f"DEBUG: Changed source from {old_source_id} to {new_source_id}"
                    )
                else:  # target
                    new_source_id = old_source_id
                    new_target_id = target_node.id
                    print(
                        f"DEBUG: Changed target from {old_target_id} to {new_target_id}"
                    )

                # Use undo system for edge reconnection
                if self.undo_redo_manager and (new_source_id != old_source_id
                                               or new_target_id
                                               != old_target_id):
                    command = m_commands.ChangeEdgeConnectionCommand(
                        self.graph, self.dragging_edge.id, old_source_id,
                        old_target_id, new_source_id, new_target_id)
                    self.undo_redo_manager.execute_command(command)
                else:
                    # Fallback if no undo manager
                    self.dragging_edge.source_id = new_source_id
                    self.dragging_edge.target_id = new_target_id

                self.graph.modified = True
                self.graph_modified.emit()
            else:
                print(
                    "DEBUG: No node found at drop position, edge reconnection cancelled"
                )

        # Handle end of node dragging
        if self.dragging and self.drag_original_positions:
            # Create move commands for all nodes that were dragged
            if self.undo_redo_manager:
                commands = []
                for node_id, original_pos in self.drag_original_positions.items(
                ):
                    node = self.graph.get_node(node_id)
                    if node:
                        current_pos = (node.x, node.y)
                        if original_pos != current_pos:  # Only create command if position actually changed
                            command = m_commands.MoveNodeCommand(
                                self.graph, node_id, original_pos, current_pos)
                            commands.append(command)

                if commands:
                    if len(commands) == 1:
                        self.undo_redo_manager.execute_command(commands[0])
                    else:
                        composite_command = m_commands.CompositeCommand(
                            "Move Nodes", commands)
                        self.undo_redo_manager.execute_command(
                            composite_command)

                    print(
                        f"DEBUG: Created move command(s) for {len(commands)} node(s)"
                    )

        # Snap selected nodes on release (after drag completes)
        if self.dragging and self.snap_to_grid and self.drag_original_positions:
            for node_id in list(self.drag_original_positions.keys()):
                node = self.graph.get_node(node_id)
                if node:
                    sx, sy = self.snap_to_grid_position(node.x, node.y)
                    node.x, node.y = sx, sy
            self.graph.modified = True
            self.graph_modified.emit()

        if self.selection_rect:
            # Only select items if the user actually dragged to create a meaningful rectangle
            # (not just a single click which creates a 0x0 rectangle)
            if self.selection_rect.width > 5 or self.selection_rect.height > 5:
                print(
                    f"DEBUG: Rectangle selection with size {self.selection_rect.width}x{self.selection_rect.height}"
                )
                # Select nodes and edges within rectangle
                self.select_items_in_rect(self.selection_rect)
            else:
                print(
                    f"DEBUG: Single click detected (rectangle too small: {self.selection_rect.width}x{self.selection_rect.height})"
                )
                # For single clicks on empty space, selection was already cleared in handle_select_down
            self.selection_changed.emit()
            self.selection_rect = None

        # Clear all dragging states
        self.dragging = False
        self.dragging_edge_endpoint = False
        self.dragging_edge = None
        self.dragging_endpoint = None
        self.dragging_arrow_position = False
        self.dragging_arrow_position_edge = None
        self.dragging_control_point = False
        self.dragging_control_point_edge = None
        self.dragging_control_point_index = -1
        self.drag_offset.clear()
        self.drag_original_positions.clear()

        # Clear selection states
        self.selection_rect = None
        self.selection_start = None
        # Release mouse capture if held
        try:
            if self.HasCapture():
                self.ReleaseMouse()
        except Exception:
            pass

        self.Refresh()

    def handle_auto_pan(self, pos):
        """Handle auto-panning when dragging near screen edges."""
        size = self.GetSize()
        edge_margin = 50  # pixels from edge to trigger panning
        pan_speed = 10  # pixels per update

        # Check each edge and pan if needed
        pan_x = pan_y = 0

        # Left edge
        if pos.x < edge_margin:
            pan_x = pan_speed
        # Right edge
        elif pos.x > size.width - edge_margin:
            pan_x = -pan_speed
        # Top edge
        if pos.y < edge_margin:
            pan_y = pan_speed
        # Bottom edge
        elif pos.y > size.height - edge_margin:
            pan_y = -pan_speed

        # Apply panning if needed
        if pan_x != 0 or pan_y != 0:
            if not self.pan_suppressed:
                self.pan_x += pan_x
                self.pan_y += pan_y
                self.Refresh()
            return True

        return False

    def handle_select_motion(self, pos):
        """Handle select tool mouse motion."""
        # Ensure we keep mouse capture during drags to avoid "stuck" behavior
        try:
            if self.dragging and not self.HasCapture():
                self.CaptureMouse()
        except Exception:
            pass
        # Lazy-init a node drag if mouse-down was missed but button is held
        try:
            if not self.dragging and not self.dragging_canvas:
                ms = wx.GetMouseState()
                if ms.LeftIsDown():
                    anchor = self.get_node_at_position(pos.x, pos.y)
                    if anchor and anchor.selected:
                        self.dragging = True
                        self.drag_start_pos = pos
                        world_pos = self.screen_to_world(pos.x, pos.y)
                        self.drag_anchor_node_id = anchor.id
                        self.drag_offset.clear()
                        self.drag_original_positions.clear()
                        for selected_node in self.graph.get_selected_nodes():
                            if selected_node.id == self.drag_anchor_node_id:
                                self.drag_offset[selected_node.id] = (0.0, 0.0)
                            else:
                                self.drag_offset[selected_node.id] = (
                                    selected_node.x - world_pos[0],
                                    selected_node.y - world_pos[1])
                                self.drag_original_positions[
                                    selected_node.id] = (selected_node.x,
                                                         selected_node.y)
                        # Cancel any selection rectangle once dragging starts
                        self.selection_start = None
                        self.selection_rect = None
                        try:
                            if not self.HasCapture():
                                self.CaptureMouse()
                        except Exception:
                            pass
        except Exception:
            pass

        # Handle auto-panning when dragging near edges
        if self.dragging and not self.dragging_canvas:
            self.handle_auto_pan(pos)

        if self.dragging_edge_endpoint and self.dragging_edge:
            if self.dragging_edge.is_hyperedge and self.dragging_edge.hyperedge_visualization == "ubergraph":
                # Move the ubergraph edge itself
                world_pos = self.screen_to_world(pos.x, pos.y)
                if self.drag_start_pos:
                    dx = pos.x - self.drag_start_pos.x
                    dy = pos.y - self.drag_start_pos.y
                    world_dx, world_dy = self.screen_to_world_delta(dx, dy)
                    self.dragging_edge.uber_x += world_dx
                    self.dragging_edge.uber_y += world_dy
                    self.drag_start_pos = pos
                    self.Refresh()
                return
            elif self.dragging_endpoint in ['from', 'to']:
                # Update hyperedge connection point position
                source_node = self.graph.get_node(self.dragging_edge.source_id)
                target_node = self.graph.get_node(self.dragging_edge.target_id)

                if source_node and target_node:
                    # Get screen positions
                    source_screen = self.world_to_screen(
                        source_node.x, source_node.y)
                    target_screen = self.world_to_screen(
                        target_node.x, target_node.y)

                # Calculate adjusted edge endpoints
                source_adjusted = self.calculate_line_endpoint(
                    source_node, target_node, source_screen, target_screen,
                    True, self.dragging_edge)
                target_adjusted = self.calculate_line_endpoint(
                    target_node, source_node, target_screen, source_screen,
                    False, self.dragging_edge)

                # Calculate the closest point on the edge line to the mouse position
                dx = target_adjusted[0] - source_adjusted[0]
                dy = target_adjusted[1] - source_adjusted[1]
                length_sq = dx * dx + dy * dy

                if length_sq > 0:
                    # Calculate projection of mouse point onto edge line
                    t = ((pos.x - source_adjusted[0]) * dx +
                         (pos.y - source_adjusted[1]) * dy) / length_sq
                    t = max(0.0, min(1.0, t))  # Clamp to [0, 1]

                    # Update the appropriate connection point
                    if self.dragging_endpoint == 'from':
                        self.dragging_edge.from_connection_point = t
                    else:  # 'to'
                        self.dragging_edge.to_connection_point = t

                    self.graph.modified = True
                    self.graph_modified.emit()
                    self.Refresh()
        elif self.dragging:
            # Update node positions (no snapping during drag so the node follows the cursor smoothly)
            if self.drag_start_pos and self.drag_offset:
                world_pos = self.screen_to_world(pos.x, pos.y)
                # Update all selected nodes
                for node_id, (dx, dy) in self.drag_offset.items():
                    node = self.graph.get_node(node_id)
                    if node:
                        new_x = world_pos[0] + dx
                        new_y = world_pos[1] + dy
                        node.x = new_x
                        node.y = new_y
                        print(
                            f"DEBUG: Moving node {node_id} to ({new_x:.1f}, {new_y:.1f}) (no snap during drag)"
                        )
                self.graph.modified = True
                self.graph_modified.emit()
                self.Refresh()
            # elif self.dragging:
            #     print("DEBUG: Dragging but no drag_start_pos or drag_offset")
        elif self.dragging_canvas:
            # Pan the canvas
            if self.drag_start_pos:
                dx = pos.x - self.drag_start_pos.x
                dy = pos.y - self.drag_start_pos.y
                # Rotate the drag vector into pre-rotation space so pan feels intuitive
                if not self.pan_suppressed:
                    pan_dx, pan_dy = self._screen_delta_to_pan_delta(dx, dy)
                    self.pan_x += pan_dx
                    self.pan_y += pan_dy
                self.drag_start_pos = pos
                self.Refresh()
        elif self.selection_start and self.selection_rect:
            # Update selection rectangle
            # Convert points to screen coordinates
            start_x = min(self.selection_start.x, pos.x)
            start_y = min(self.selection_start.y, pos.y)
            end_x = max(self.selection_start.x, pos.x)
            end_y = max(self.selection_start.y, pos.y)

            # Update rectangle
            self.selection_rect.SetLeft(start_x)
            self.selection_rect.SetTop(start_y)
            self.selection_rect.SetRight(end_x)
            self.selection_rect.SetBottom(end_y)
            self.Refresh()
        elif self.dragging_arrow_position:
            # Update arrow control along segments
            if self.dragging_arrow_position_edge:
                edge = self.dragging_arrow_position_edge
                effective_pos = self.handle_edge_scrolling_and_cursor_mirror(
                    pos, is_world_drag=False)
                # Ubergraph segment dragging
                if edge.is_hyperedge and getattr(
                        edge, 'hyperedge_visualization', '') == 'ubergraph':
                    # Node segment
                    if getattr(self, 'dragging_arrow_position_kind',
                               None) == 'node' and getattr(
                                   self, 'dragging_arrow_node_id',
                                   None) is not None:
                        node = self.graph.get_node(self.dragging_arrow_node_id)
                        if node:
                            ex, ey = self.world_to_screen(
                                edge.uber_x, edge.uber_y)
                            nx, ny = self.world_to_screen(node.x, node.y)
                            vx = nx - ex
                            vy = ny - ey
                            seg_len_sq = vx * vx + vy * vy
                            if seg_len_sq > 0:
                                t = ((effective_pos.x - ex) * vx +
                                     (effective_pos.y - ey) * vy) / seg_len_sq
                                t = max(0.0, min(1.0, t))
                                if not hasattr(
                                        edge,
                                        'metadata') or edge.metadata is None:
                                    edge.metadata = {}
                                amap = edge.metadata.get(
                                    'arrow_pos_nodes') or {}
                                amap[str(self.dragging_arrow_node_id)] = t
                                edge.metadata['arrow_pos_nodes'] = amap
                                self.graph_modified.emit()
                                self.Refresh()
                                return
                    # Edge↔edge segment
                    if getattr(self, 'dragging_arrow_position_kind',
                               None) == 'edge' and getattr(
                                   self, 'dragging_arrow_other_edge_id',
                                   None) is not None:
                        other = self.graph.get_edge(
                            self.dragging_arrow_other_edge_id)
                        if other and other.is_hyperedge:
                            ex, ey = self.world_to_screen(
                                edge.uber_x, edge.uber_y)
                            ox, oy = self.world_to_screen(
                                other.uber_x, other.uber_y)
                            vx = ox - ex
                            vy = oy - ey
                            seg_len_sq = vx * vx + vy * vy
                            if seg_len_sq > 0:
                                t = ((effective_pos.x - ex) * vx +
                                     (effective_pos.y - ey) * vy) / seg_len_sq
                                t = max(0.0, min(1.0, t))
                                if not hasattr(
                                        edge,
                                        'metadata') or edge.metadata is None:
                                    edge.metadata = {}
                                amap = edge.metadata.get(
                                    'arrow_pos_edges') or {}
                                amap[str(
                                    self.dragging_arrow_other_edge_id)] = t
                                edge.metadata['arrow_pos_edges'] = amap
                                self.graph_modified.emit()
                                self.Refresh()
                                return
                    return
                # Non-ubergraph fallback (main segment)
                source_node = self.graph.get_node(edge.source_id)
                target_node = self.graph.get_node(edge.target_id)
                if source_node and target_node:
                    source_screen = self.world_to_screen(
                        source_node.x, source_node.y)
                    target_screen = self.world_to_screen(
                        target_node.x, target_node.y)
                    source_adjusted = self.calculate_line_endpoint(
                        source_node, target_node, source_screen, target_screen,
                        True, edge)
                    target_adjusted = self.calculate_line_endpoint(
                        target_node, source_node, target_screen, source_screen,
                        False, edge)
                    dx = target_adjusted[0] - source_adjusted[0]
                    dy = target_adjusted[1] - source_adjusted[1]
                    edge_len_sq = dx * dx + dy * dy
                    if edge_len_sq > 0:
                        t = ((effective_pos.x - source_adjusted[0]) * dx +
                             (effective_pos.y - source_adjusted[1]) *
                             dy) / edge_len_sq
                        t = max(0.0, min(1.0, t))
                        edge.arrow_position = max(0.1, min(0.9, t))
                        main_window = self.GetParent()
                        if hasattr(main_window,
                                   'arrow_position_slider') and hasattr(
                                       main_window, 'arrow_position_text'):
                            wx.CallAfter(
                                main_window.arrow_position_slider.SetValue,
                                int(edge.arrow_position * 100))
                            wx.CallAfter(
                                main_window.arrow_position_text.SetValue,
                                f"{edge.arrow_position:.2f}")
                        self.graph_modified.emit()
                        self.Refresh()
            return

        if self.dragging_control_point:
            # Update control point position with edge scrolling and cursor mirroring
            edge = self.dragging_control_point_edge
            index = self.dragging_control_point_index

            if edge:
                effective_pos = self.handle_edge_scrolling_and_cursor_mirror(
                    pos, is_world_drag=False)
                world_pos = self.screen_to_world(effective_pos.x,
                                                 effective_pos.y)
                print(
                    f"DEBUG: 🎮 Moving control point: screen ({pos.x}, {pos.y}) -> effective ({effective_pos.x}, {effective_pos.y}) -> world {world_pos} (rotation: {self.world_rotation}°)"
                )
                rendering_type = edge.rendering_type if edge.rendering_type else self.edge_rendering_type

                # Segment-specific control points for selected ubergraph segment
                if getattr(edge, 'is_hyperedge', False) and getattr(edge, 'hyperedge_visualization', '') == 'ubergraph' and getattr(self, 'selected_uber_segment_kind', None):
                    try:
                        if not hasattr(edge, 'metadata') or edge.metadata is None:
                            edge.metadata = {}
                        if self.selected_uber_segment_kind == 'node' and getattr(self, 'selected_uber_segment_node_id', None) is not None:
                            nid = str(self.selected_uber_segment_node_id)
                            cp_map = edge.metadata.get('segment_cp_nodes') or {}
                            arr = cp_map.get(nid) or []
                            while len(arr) <= index:
                                arr.append((world_pos[0], world_pos[1]))
                            old_point = arr[index] if index < len(arr) else None
                            arr[index] = (world_pos[0], world_pos[1])
                            cp_map[nid] = arr
                            edge.metadata['segment_cp_nodes'] = cp_map
                            print(f"DEBUG: 🎯 Updated node-segment CP[{index}] from {old_point} to {arr[index]} for edge {edge.id} node {nid}")
                            self.graph_modified.emit(); self.Refresh(); return
                        elif self.selected_uber_segment_kind == 'edge' and getattr(self, 'selected_uber_segment_other_edge_id', None) is not None:
                            oid = str(self.selected_uber_segment_other_edge_id)
                            cp_map = edge.metadata.get('segment_cp_edges') or {}
                            arr = cp_map.get(oid) or []
                            while len(arr) <= index:
                                arr.append((world_pos[0], world_pos[1]))
                            old_point = arr[index] if index < len(arr) else None
                            arr[index] = (world_pos[0], world_pos[1])
                            cp_map[oid] = arr
                            edge.metadata['segment_cp_edges'] = cp_map
                            print(f"DEBUG: 🎯 Updated edge-segment CP[{index}] from {old_point} to {arr[index]} for edge {edge.id} other {oid}")
                            self.graph_modified.emit(); self.Refresh(); return
                    except Exception as _e:
                        print(f"DEBUG: ⚠️ Error updating ubergraph segment CP: {_e}")

                if rendering_type == "composite" and getattr(
                        edge, 'is_composite', False):
                    # Handle composite curve control points
                    segment_index = getattr(self, 'current_composite_segment',
                                            0)
                    if (hasattr(edge, 'curve_segments')
                            and segment_index < len(edge.curve_segments)
                            and 0 <= index < len(
                                edge.curve_segments[segment_index].get(
                                    "control_points", []))):

                        segment = edge.curve_segments[segment_index]
                        old_point = segment["control_points"][index]
                        segment["control_points"][index] = (world_pos[0],
                                                            world_pos[1])
                        print(
                            f"DEBUG: 🔗 Moving composite segment {segment_index} control point {index} from {old_point} to {world_pos}"
                        )
                        print(
                            f"DEBUG: 🔗 Segment now has control points: {segment['control_points']}"
                        )

                        # Update the main window's control list
                        main_window = self.GetParent()
                        if hasattr(main_window, 'update_curve_list'):
                            wx.CallAfter(main_window.update_curve_list)

                        self.graph_modified.emit()
                        self.Refresh()
                else:
                    # Handle regular curve control points
                    if (hasattr(edge, 'control_points')
                            and 0 <= index < len(edge.control_points)):
                        old_point = edge.control_points[index]
                        edge.control_points[index] = (world_pos[0],
                                                      world_pos[1])
                        edge.custom_position = True  # Mark as having custom control points
                        print(
                            f"DEBUG: 🎛️ Moving {rendering_type} control point {index} from {old_point} to {world_pos}"
                        )
                        print(
                            f"DEBUG: 🎛️ Edge {edge.id} control_points now: {edge.control_points}"
                        )

                        # Update the main window's control list
                        main_window = self.GetParent()
                        if hasattr(main_window, 'update_curve_list'):
                            wx.CallAfter(main_window.update_curve_list)

                        self.graph_modified.emit()
                        self.Refresh()
            return

        if self.dragging_edge_endpoint:
            # Update edge endpoint based on anchor mode
            if self.dragging_edge and self.dragging_endpoint:
                world_pos = self.screen_to_world(pos.x, pos.y)

                # Find the target node for the endpoint being dragged
                if self.dragging_endpoint == 'source':
                    target_node = self.graph.get_node(
                        self.dragging_edge.source_id)
                else:
                    target_node = self.graph.get_node(
                        self.dragging_edge.target_id)

                if target_node:
                    # Calculate new anchor position based on mode
                    new_anchor = self.calculate_anchor_position(
                        target_node, world_pos, self.edge_anchor_mode)

                    # Store custom endpoint position on the edge
                    if not hasattr(self.dragging_edge, 'custom_endpoints'):
                        self.dragging_edge.custom_endpoints = {}

                    self.dragging_edge.custom_endpoints[
                        self.dragging_endpoint] = new_anchor
                    print(
                        f"DEBUG: 🔗 Updated {self.dragging_endpoint} endpoint to {new_anchor} (mode: {self.edge_anchor_mode})"
                    )

                    self.graph_modified.emit()
            self.Refresh()
        elif self.dragging and self.drag_offset:
            # Drag selected nodes with edge scrolling and cursor mirroring
            effective_pos = self.handle_edge_scrolling_and_cursor_mirror(
                pos, is_world_drag=False)
            world_pos = self.screen_to_world(effective_pos.x, effective_pos.y)

            # Store old positions for custom endpoint updates
            old_positions = {}
            for node_id, offset in self.drag_offset.items():
                node = self.graph.get_node(node_id)
                if node:
                    old_positions[node_id] = (node.x, node.y)

            # Update node positions
            for node_id, offset in self.drag_offset.items():
                node = self.graph.get_node(node_id)
                if node:
                    node.set_2d_position(world_pos[0] + offset[0],
                                         world_pos[1] + offset[1])

            # Update custom edge endpoints for moved nodes
            self.update_custom_endpoints_for_moved_nodes(old_positions)

            # Update control points for moved nodes if setting is enabled
            if self.relative_control_points:
                self.update_control_points_for_moved_nodes(old_positions)

            self.graph.modified = True
            self.graph_modified.emit()
            self.Refresh()
            # Push live position updates to backend if available
            try:
                mw = self.GetParent()
                backend = getattr(mw, 'backend', None)
                if backend and getattr(backend, 'is_available', lambda: False)():
                    items = []
                    for node_id, offset in self.drag_offset.items():
                        node = self.graph.get_node(node_id)
                        if node:
                            items.append((node_id, float(node.x), float(node.y)))
                    if items:
                        backend.patch_node_positions(items)
            except Exception:
                pass

        elif self.dragging_canvas:
            # Pan canvas with edge scrolling and cursor mirroring
            if self.drag_start_pos:
                effective_pos = self.handle_edge_scrolling_and_cursor_mirror(
                    pos, is_world_drag=True)
                dx = effective_pos.x - self.drag_start_pos.x
                dy = effective_pos.y - self.drag_start_pos.y
                if not self.pan_suppressed:
                    pan_dx, pan_dy = self._screen_delta_to_pan_delta(dx, dy)
                    self.pan_x += pan_dx
                    self.pan_y += pan_dy
                self.drag_start_pos = effective_pos
                self.Refresh()

        elif self.selection_rect:
            # Update selection rectangle
            start_x = min(self.selection_start.x, pos.x)
            start_y = min(self.selection_start.y, pos.y)
            width = abs(pos.x - self.selection_start.x)
            height = abs(pos.y - self.selection_start.y)

            self.selection_rect = wx.Rect(start_x, start_y, width, height)
            self.Refresh()

    def handle_move_down(self, pos):
        """Handle move tool mouse down."""

        print(f"DEBUG: Move tool down at {pos.x}, {pos.y}")
        # Start move world behavior
        self.dragging_canvas = True
        self.drag_start_pos = pos

    def handle_move_up(self, pos):
        """Handle move tool mouse up."""

        print(f"DEBUG: Move tool up at {pos.x}, {pos.y}")
        # Re-sync MVU model rotation after move completes
        try:
            mw = self.GetParent().GetParent()
            if hasattr(mw, 'mvu_adapter'):
                from mvc_mvu.messages import make_message
                import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
                mw.mvu_adapter.dispatch(
                    make_message(m_main_mvu.Msg.SET_ROTATION,
                                 angle=self.world_rotation))
        except Exception:
            pass

    def move_world(self):
        """Move the world based on mouse drag."""
        # This method is called by the hotkey manager when in move mode
        # The actual movement is handled by handle_move_motion
        pass

    def snap_to_grid_position(self, x: float, y: float) -> Tuple[float, float]:
        """Snap a position to the nearest grid point if snap to grid is enabled."""
        if not self.snap_to_grid:
            return (x, y)

        # Round to nearest grid spacing
        snapped_x = round(x / self.grid_spacing) * self.grid_spacing
        snapped_y = round(y / self.grid_spacing) * self.grid_spacing

        return (snapped_x, snapped_y)

    def handle_move_motion(self, pos):
        """Handle move tool mouse motion - drags the entire world (grid, nodes, edges)."""
        if not self.dragging_canvas:
            return

        if not hasattr(self, 'drag_start_pos') or self.drag_start_pos is None:
            self.drag_start_pos = pos
            return

        # Calculate movement delta
        dx = pos.x - self.drag_start_pos.x
        dy = pos.y - self.drag_start_pos.y

        print(
            f"DEBUG: 🌐 Move world - Raw mouse delta: dx={dx:.1f}, dy={dy:.1f}")

        # Apply sensitivity scaling
        dx *= self.move_sensitivity_x
        dy *= self.move_sensitivity_y

        print(
            f"DEBUG: 🌐 Move world - After sensitivity: dx={dx:.1f}, dy={dy:.1f}"
        )

        # Apply inversion if enabled
        if self.move_inverted:
            print(f"DEBUG: 🌐 Move world - Applying inversion")
            dx = -dx
            dy = -dy

        print(f"DEBUG: 🌐 Move world - Final delta: dx={dx:.1f}, dy={dy:.1f}")

        # Update pan position (apply inverse rotation so movement is intuitive with world rotation)
        if not self.pan_suppressed:
            pan_dx, pan_dy = self._screen_delta_to_pan_delta(dx, dy)
            self.pan_x += pan_dx
            self.pan_y += pan_dy

        # Update drag start position for next delta calculation
        self.drag_start_pos = pos

        print(
            f"DEBUG: 🌐 Move world - New pan position: ({self.pan_x:.1f}, {self.pan_y:.1f})"
        )

        # Update canvas information display
        if hasattr(self, 'main_window') and hasattr(self.main_window,
                                                    'update_canvas_info'):
            self.main_window.update_canvas_info()

        # Refresh the canvas to show the moved world
        self.Refresh()

    def handle_rotate_down(self, pos):
        """Handle rotate tool mouse down."""

        print(f"DEBUG: 🎯 Rotate tool clicked at {pos.x}, {pos.y}")
        self.dragging_rotation = True
        self.rotation_start_pos = pos
        self.initial_world_rotation = self.world_rotation
        self.show_rotation_center = True  # Show center dot

        # For world rotation, always use screen center as rotation point
        size = self.GetSize()
        center_x = size.width / 2.0  # Use float for precision
        center_y = size.height / 2.0  # Use float for precision

        # Calculate initial angle from click position to screen center
        self.rotation_start_angle = math.atan2(pos.y - center_y,
                                               pos.x - center_x)

        print(
            f"DEBUG: Starting rotation from {self.initial_world_rotation:.1f}°"
        )
        print(
            f"DEBUG: Click at ({pos.x}, {pos.y}), Screen center at ({center_x}, {center_y})"
        )
        print(
            f"DEBUG: Initial angle: {math.degrees(self.rotation_start_angle):.1f}°"
        )
        self.Refresh()  # Refresh to show center dot

    def handle_rotate_up(self, pos):
        """Handle rotate tool mouse up."""

        final_rotation = getattr(self, 'world_rotation', 0.0) or 0.0
        print(
            f"DEBUG: ✅ Rotate tool released at {pos.x}, {pos.y} - Final rotation: {final_rotation:.1f}°"
        )
        print(
            f"DEBUG: 🔴 Hiding rotation center dot (show_rotation_center = False)"
        )
        self.dragging_rotation = False
        self.show_rotation_center = False  # Hide center dot

        # Update the rotation field in the main window if available
        try:
            main_window = self.GetParent().GetParent()
            if hasattr(main_window, 'rotation_field'):
                main_window.rotation_field.SetValue(final_rotation)
                print(
                    f"DEBUG: ✅ Final rotation UI update: {final_rotation:.1f}°"
                )
            else:
                print(
                    f"DEBUG: ❌ rotation_field not found in main window during release"
                )
            # Ensure MVU model stores the final rotation so subsequent renders keep it
            if hasattr(main_window, 'mvu_adapter'):
                try:
                    from mvc_mvu.messages import make_message as _mmake
                    import graph_canvas.presentation.desktop.mvu.main_mvu as _m_main
                    main_window.mvu_adapter.dispatch(
                        _mmake(_m_main.Msg.SET_ROTATION, angle=final_rotation))
                    print(
                        f"DEBUG: 📤 Dispatched MVU SET_ROTATION final {final_rotation:.1f}° on release"
                    )
                except Exception as _e:
                    print(
                        f"DEBUG: ❌ Failed to dispatch MVU final rotation: {_e}"
                    )
            # Set a brief cooldown to prevent MVU applying stale model rotation (e.g., 0°) immediately
            try:
                setattr(self, 'rotation_sync_skip_frames', 2)
            except Exception:
                pass
        except Exception as e:
            print(f"DEBUG: ❌ Error updating final rotation field: {e}")

        self.Refresh()  # Refresh to hide center dot

    def handle_rotate_motion(self, pos):
        """Handle rotate tool mouse motion."""

        print(
            f"DEBUG: 🔄 handle_rotate_motion called with dragging_rotation={getattr(self, 'dragging_rotation', False)}"
        )

        if hasattr(self,
                   'dragging_rotation') and self.dragging_rotation and hasattr(
                       self, 'rotation_start_angle'):
            # For world rotation, ALWAYS use screen center as rotation point
            size = self.GetSize()
            center_x = size.width / 2.0  # Use float for precision
            center_y = size.height / 2.0  # Use float for precision

            # Calculate current angle from mouse position to screen center
            current_angle = math.atan2(pos.y - center_y, pos.x - center_x)

            # Calculate angle difference from initial click
            angle_delta = current_angle - self.rotation_start_angle
            angle_delta_degrees = math.degrees(angle_delta)

            # Apply new rotation based on initial rotation + angle delta
            new_rotation = (self.initial_world_rotation +
                            angle_delta_degrees) % 360
            if new_rotation < 0:
                new_rotation += 360

            print(
                f"DEBUG: 🔄 Mouse at ({pos.x}, {pos.y}), Center at ({center_x}, {center_y})"
            )
            print(
                f"DEBUG: 🔄 Current angle: {math.degrees(current_angle):.1f}°, Start angle: {math.degrees(self.rotation_start_angle):.1f}°"
            )
            print(
                f"DEBUG: 🔄 Angle delta: {angle_delta_degrees:.1f}° → New rotation: {new_rotation:.1f}°"
            )

            # Apply the rotation immediately for smooth feedback
            self.set_world_rotation(new_rotation)

            # Update the UI field immediately for visual feedback
            try:
                main_window = self.GetParent().GetParent()
                if hasattr(main_window, 'rotation_field'):
                    main_window.rotation_field.SetValue(new_rotation)
                    print(
                        f"DEBUG: 🔄 Updated UI rotation field to {new_rotation:.1f}°"
                    )
                else:
                    print(f"DEBUG: ❌ rotation_field not found in main window")
                # Also sync MVU model so all paths see the same rotation
                if hasattr(main_window, 'mvu_adapter'):
                    try:
                        from mvc_mvu.messages import make_message as _mmake
                        import graph_canvas.presentation.desktop.mvu.main_mvu as _m_main
                        main_window.mvu_adapter.dispatch(
                            _mmake(_m_main.Msg.SET_ROTATION,
                                   angle=new_rotation))
                        print(
                            f"DEBUG: 📤 Dispatched MVU SET_ROTATION {new_rotation:.1f}°"
                        )
                    except Exception as _e:
                        print(
                            f"DEBUG: ❌ Failed to dispatch MVU rotation: {_e}")
            except Exception as e:
                print(f"DEBUG: ❌ Error updating rotation field: {e}")
        else:
            print(f"DEBUG: ❌ Not dragging rotation - conditions not met")

    def handle_rotate_element_down(self, pos):
        """Handle rotate element tool mouse down."""

        print(f"DEBUG: 🎯🎯🎯 Rotate element tool clicked at {pos.x}, {pos.y}")

        # Find node at click position
        world_pos = self.screen_to_world(pos.x, pos.y)
        node = self.get_node_at_position(pos.x, pos.y)

        if node:
            print(
                f"DEBUG: 🎯 Selected node {node.id} for rotation at ({world_pos[0]:.1f}, {world_pos[1]:.1f})"
            )
            # Ensure selection of the clicked node
            if not node.selected:
                self.graph.clear_selection()
                self.graph.select_node(node.id)
                self.selection_changed.emit()
            self.dragging_element_rotation = True
            self.rotating_element = node
            self.element_rotation_start_pos = pos
            self.element_initial_rotation = node.rotation
            # Set pivot to the node center to ensure rotation about the visual center
            self.element_pivot_world = (node.x, node.y)
            # Offset from pivot to node center is zero for center-based rotation
            self.element_initial_offset_world = (0.0, 0.0)
            # Compute initial mouse angle around pivot (node center) in world space
            pivot_wx, pivot_wy = self.element_pivot_world
            start_mouse_world = self.screen_to_world(pos.x, pos.y)
            self.element_rotation_start_angle = math.atan2(
                start_mouse_world[1] - pivot_wy,
                start_mouse_world[0] - pivot_wx)
            self.show_element_rotation_center = True
            print(
                f"DEBUG: 🎯 Element rotation pivot (world): {self.element_pivot_world}, start_angle: {math.degrees(self.element_rotation_start_angle):.1f}°"
            )
        else:
            print(f"DEBUG: ❌ No node found at click position")

        self.Refresh()

    def handle_rotate_element_up(self, pos):
        """Handle rotate element tool mouse up."""

        print(f"DEBUG: 🔄 Element rotation up at {pos.x}, {pos.y}")

        if self.dragging_element_rotation and self.rotating_element:
            print(
                f"DEBUG: 🔄 Ending element rotation - final rotation: {self.rotating_element.rotation:.1f}°"
            )

            # Update edge endpoints for the rotated node
            rotated_node = self.rotating_element
            print(
                f"DEBUG: 🔄 Element rotation completed for node {rotated_node.id}"
            )

            # Update all edges connected to this node
            for edge in self.graph.get_all_edges():
                needs_update = False

                if edge.source_id == rotated_node.id or edge.target_id == rotated_node.id:
                    # Check if this edge has custom endpoints
                    if hasattr(edge,
                               'custom_endpoints') and edge.custom_endpoints:
                        # Recalculate custom endpoints based on the node's new rotation
                        if edge.source_id == rotated_node.id and 'source' in edge.custom_endpoints:
                            needs_update = True
                        if edge.target_id == rotated_node.id and 'target' in edge.custom_endpoints:
                            needs_update = True
                    else:
                        # For edges without custom endpoints, determine the best anchor point
                        needs_update = True

                if needs_update:
                    print(
                        f"DEBUG: 🔄 Updating edge {edge.id} endpoints after node rotation"
                    )
                    self.update_edge_endpoints_for_rotated_node(
                        edge, rotated_node)

            self.graph_modified.emit()

        # Reset element rotation state
        self.dragging_element_rotation = False
        self.rotating_element = None
        self.show_element_rotation_center = False
        self.element_rotation_start_pos = None
        self.element_pivot_world = None
        self.element_initial_offset_world = None
        self.Refresh()

    def handle_rotate_element_motion(self, pos):
        """Handle rotate element tool mouse motion."""

        print(
            f"DEBUG: 🔄🔄 Element rotation motion check - dragging: {self.dragging_element_rotation}, element: {self.rotating_element is not None}, has_angle: {hasattr(self, 'element_rotation_start_angle')}"
        )
        # Lazy-init: if mouse is down and we have no rotating element, try to start on the fly
        try:
            if (not self.dragging_element_rotation
                    or not self.rotating_element):
                mouse_state = wx.GetMouseState()
                if mouse_state.LeftIsDown():
                    print(
                        f"DEBUG: 🔄 Lazy-init rotate element on motion at {pos.x},{pos.y}"
                    )
                    self.handle_rotate_element_down(pos)
        except Exception as e:
            print(f"DEBUG: ❌ Lazy-init rotate element failed: {e}")
        if self.dragging_element_rotation and self.rotating_element and hasattr(
                self, 'element_rotation_start_angle'):
            # Compute current mouse angle around pivot in world space
            pivot = self.element_pivot_world if self.element_pivot_world else (
                self.rotating_element.x, self.rotating_element.y)
            pivot_wx, pivot_wy = pivot
            mouse_world = self.screen_to_world(pos.x, pos.y)
            current_angle = math.atan2(mouse_world[1] - pivot_wy,
                                       mouse_world[0] - pivot_wx)

            # Angle delta and new rotation
            angle_delta = current_angle - self.element_rotation_start_angle
            angle_delta_degrees = math.degrees(angle_delta)
            new_rotation = (self.element_initial_rotation +
                            angle_delta_degrees) % 360
            if new_rotation < 0:
                new_rotation += 360

            # If pivot differs from node center (non-zero offset), update position; otherwise keep center fixed
            if self.element_initial_offset_world is not None:
                ox, oy = self.element_initial_offset_world
                if abs(ox) > 1e-6 or abs(oy) > 1e-6:
                    cos_a = math.cos(angle_delta)
                    sin_a = math.sin(angle_delta)
                    rx = ox * cos_a - oy * sin_a
                    ry = ox * sin_a + oy * cos_a
                    new_cx = pivot_wx + rx
                    new_cy = pivot_wy + ry
                    self.rotating_element.x = new_cx
                    self.rotating_element.y = new_cy

            self.rotating_element.rotation = new_rotation
            print(
                f"DEBUG: 🔄 Element pivot rotate: Δ={angle_delta_degrees:.1f}°, new rot={new_rotation:.1f}°, new center=({self.rotating_element.x:.1f},{self.rotating_element.y:.1f})"
            )
            self.Refresh()
        else:
            print(
                f"DEBUG: ❌ Not dragging element rotation - conditions not met")

    # Containment tool handlers
    def handle_drag_into_down(self, pos):
        """Handle mouse down for drag-into-container tool."""

        print(f"DEBUG: 📦 Drag into container down at {pos.x}, {pos.y}")

        # Check if we clicked on selected nodes/edges
        selected_nodes = self.graph.get_selected_nodes()
        selected_edges = self.graph.get_selected_edges()

        print(
            f"DEBUG: 📦 Found {len(selected_nodes)} selected nodes and {len(selected_edges)} selected edges"
        )

        if selected_nodes or selected_edges:
            # Start dragging the selected items regardless of where clicked
            # This makes the tool more intuitive - if items are selected, dragging starts
            self.dragging_into_container = True
            self.dragging_selection = list(selected_nodes) + list(
                selected_edges)
            print(
                f"DEBUG: 📦 Starting drag of {len(selected_nodes)} nodes and {len(selected_edges)} edges"
            )
            print(
                f"DEBUG: 📦 Selected node names: {[node.text for node in selected_nodes]}"
            )
            print(f"DEBUG: 📦 Selected edge count: {len(selected_edges)}")
        else:
            print(f"DEBUG: 📦 No selection to drag - select items first")
            # Show instructional message for users
            import wx
            wx.MessageBox(
                "No items selected to drag into container.\n\nTo use this tool:\n1. First select some nodes/edges\n2. Then click and drag to a target node",
                "Select Items First", wx.OK | wx.ICON_INFORMATION)

    def handle_drag_into_motion(self, pos):
        """Handle mouse motion for drag-into-container tool."""

        if self.dragging_into_container:
            # Find potential container target under mouse
            target_node = self.get_node_at_position(pos.x, pos.y)
            print(
                f"DEBUG: 📦 Motion over target: {target_node.text if target_node else 'None'}"
            )

            # Don't allow dragging into selected nodes (can't contain yourself)
            nodes_being_dragged = [
                item for item in self.dragging_selection
                if hasattr(item, 'text')
            ]
            if target_node and target_node not in nodes_being_dragged:
                self.container_target = target_node
                print(f"DEBUG: 📦 Valid motion target: {target_node.text}")
            else:
                if target_node and target_node in nodes_being_dragged:
                    print(
                        f"DEBUG: 📦 Invalid motion target - node is being dragged"
                    )
                self.container_target = None

            self.Refresh()  # Update visual feedback

    def handle_drag_into_up(self, pos):
        """Handle mouse up for drag-into-container tool."""

        print(f"DEBUG: 📦 ========== DRAG INTO CONTAINER UP ==========")
        print(f"DEBUG: 📦 Mouse release at {pos.x}, {pos.y}")
        print(
            f"DEBUG: 📦 dragging_into_container: {self.dragging_into_container}"
        )
        print(
            f"DEBUG: 📦 dragging_selection: {len(self.dragging_selection)} items"
        )
        print(
            f"DEBUG: 📦 container_target: {self.container_target.text if self.container_target else 'None'}"
        )

        if self.dragging_into_container:
            # Find the target node under the mouse at release point
            target_node = self.get_node_at_position(pos.x, pos.y)
            print(
                f"DEBUG: 📦 Target node found at release: {target_node.text if target_node else 'None'}"
            )

            # List all nodes near the mouse position for debugging
            world_pos = self.screen_to_world(pos.x, pos.y)
            print(f"DEBUG: 📦 World position: {world_pos}")
            print(f"DEBUG: 📦 All nodes:")
            for node in self.graph.get_all_nodes():
                distance = ((node.x - world_pos[0])**2 +
                            (node.y - world_pos[1])**2)**0.5
                print(
                    f"DEBUG: 📦 Node '{node.text}' at ({node.x:.1f}, {node.y:.1f}), distance: {distance:.1f}, visible: {node.visible}"
                )

            # Check if target is valid (not one of the selected nodes being dragged)
            if target_node:
                nodes_being_dragged = [
                    item for item in self.dragging_selection
                    if hasattr(item, 'text')
                ]
                print(
                    f"DEBUG: 📦 Nodes being dragged: {[n.text for n in nodes_being_dragged]}"
                )
                if target_node not in nodes_being_dragged:
                    self.container_target = target_node
                    print(
                        f"DEBUG: 📦 ✅ Valid container target: {target_node.text}"
                    )
                else:
                    print(
                        f"DEBUG: 📦 ❌ Invalid target - cannot contain selected node in itself"
                    )
                    self.container_target = None
            else:
                print(f"DEBUG: 📦 ❌ No target node found under mouse")
                self.container_target = None

        print(
            f"DEBUG: 📦 Final check - dragging: {self.dragging_into_container}, target: {self.container_target.text if self.container_target else 'None'}"
        )

        if self.dragging_into_container and self.container_target:
            # Perform the containment operation
            container_node = self.container_target

            nodes_to_contain = [
                item for item in self.dragging_selection
                if hasattr(item, 'text')
            ]
            edges_to_contain = [
                item for item in self.dragging_selection
                if hasattr(item, 'source_id')
            ]

            print(f"DEBUG: 📦 🎯 PERFORMING CONTAINMENT!")
            print(
                f"DEBUG: 📦 Containing {len(nodes_to_contain)} nodes and {len(edges_to_contain)} edges in {container_node.text}"
            )

            # Add children to container
            node_ids_being_contained = set()
            for node in nodes_to_contain:
                if node.id != container_node.id:  # Don't contain self
                    container_node.add_child(node.id)
                    node.parent_id = container_node.id
                    node_ids_being_contained.add(node.id)

            # Only mark edges as contained if BOTH endpoints are being contained
            # Edges with one external endpoint should remain external for redirection
            print(
                f"DEBUG: 📦 Node IDs being contained: {node_ids_being_contained}"
            )
            for edge in edges_to_contain:
                source_contained = edge.source_id in node_ids_being_contained
                target_contained = edge.target_id in node_ids_being_contained

                if source_contained and target_contained:
                    # Both endpoints are internal - this is a truly internal edge
                    print(
                        f"DEBUG: 📦 Edge {edge.id} is internal ({edge.source_id} -> {edge.target_id}), adding to contained_edges"
                    )
                    container_node.add_contained_edge(edge.id)
                else:
                    # At least one endpoint is external - leave as external edge for redirection
                    print(
                        f"DEBUG: 📦 Edge {edge.id} is external ({edge.source_id} -> {edge.target_id}), leaving for redirection"
                    )
                    print(
                        f"DEBUG: 📦   Source contained: {source_contained}, Target contained: {target_contained}"
                    )

            # Hide contained items if container is collapsed
            if not container_node.is_expanded:
                for node in nodes_to_contain:
                    print(
                        f"DEBUG: 📦 Hiding node '{node.text}' due to containment collapse"
                    )
                    node.visible = False
                for edge in edges_to_contain:
                    edge.visible = False

            # Clear selection
            self.graph.clear_selection()

            # Mark graph as modified
            if hasattr(self, 'graph_modified'):
                self.graph_modified.emit()

            print(f"DEBUG: 📦 Containment completed")

            # Show success message
            import wx
            wx.MessageBox(
                f"Successfully contained {len(nodes_to_contain)} nodes and {len(edges_to_contain)} edges in '{container_node.text}'",
                "Containment Successful", wx.OK | wx.ICON_INFORMATION)

        else:
            print(f"DEBUG: 📦 ❌ CONTAINMENT FAILED!")
            print(
                f"DEBUG: 📦 dragging_into_container: {self.dragging_into_container}"
            )
            print(f"DEBUG: 📦 container_target: {self.container_target}")
            print(
                f"DEBUG: 📦 No valid container target found for drop operation")

            # Show user feedback for failed drag operation
            if self.dragging_into_container:
                import wx
                wx.MessageBox(
                    "Drop failed: No valid container target found.\n\nTo use Drag Into Container:\n1. Select nodes/edges to contain\n2. Switch to 'Drag Into Container' tool\n3. Click and drag to an unselected target node\n4. Release mouse over target to contain items",
                    "Drag Into Container", wx.OK | wx.ICON_INFORMATION)

        # Reset state
        self.dragging_into_container = False
        self.container_target = None
        self.dragging_selection = []
        self.Refresh()

    def handle_expand_down(self, pos):
        """Handle expand tool click."""

        print(f"DEBUG: 📖 Expand tool click at {pos.x}, {pos.y}")

        # Find node under mouse
        target_node = self.get_node_at_position(pos.x, pos.y)

        if target_node and target_node.is_container:
            print(f"DEBUG: 📖 Expanding container {target_node.text}")

            # Expand the container
            target_node.is_expanded = True

            # Show all contained nodes and edges
            for child_id in target_node.child_ids:
                child_node = self.graph.get_node(child_id)
                if child_node:
                    child_node.visible = True

            for edge_id in target_node.contained_edge_ids:
                edge = self.graph.get_edge(edge_id)
                if edge:
                    edge.visible = True

            # Restore redirected edges to their original nodes
            print(f"DEBUG: 📖 Restoring redirected edges from container")
            edges_restored = 0
            redirected_edges = target_node.get_redirected_edges()

            for edge_id, original_node_id in redirected_edges.items():
                edge = self.graph.get_edge(edge_id)
                if edge:
                    # Determine if this was a source or target redirection
                    if edge.source_id == target_node.id:
                        # Restore source
                        print(
                            f"DEBUG: 📖 Restoring edge {edge_id} source from {target_node.text} to {original_node_id}"
                        )
                        edge.source_id = original_node_id
                        edges_restored += 1
                    elif edge.target_id == target_node.id:
                        # Restore target
                        print(
                            f"DEBUG: 📖 Restoring edge {edge_id} target from {target_node.text} to {original_node_id}"
                        )
                        edge.target_id = original_node_id
                        edges_restored += 1

                    # Remove the redirection record
                    target_node.remove_redirected_edge(edge_id)

            print(f"DEBUG: 📖 Restored {edges_restored} edges from container")

            # Mark graph as modified
            if hasattr(self, 'graph_modified'):
                self.graph_modified.emit()
            # Notify MVU of updated counts
            try:
                mw = self.GetParent().GetParent()
                if hasattr(mw, 'mvu_adapter'):
                    from mvc_mvu.messages import make_message
                    import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
                    all_nodes = len(self.graph.get_all_nodes())
                    all_edges = len(self.graph.get_all_edges())
                    mw.mvu_adapter.dispatch(
                        make_message(m_main_mvu.Msg.SET_COUNTS,
                                     nodes=all_nodes,
                                     edges=all_edges))
            except Exception:
                pass

            self.Refresh()
            print(
                f"DEBUG: 📖 Container expanded with {edges_restored} edges restored"
            )
        else:
            print(f"DEBUG: 📖 No container found or not a container")

    def handle_collapse_down(self, pos):
        """Handle collapse tool click."""

        print(f"DEBUG: 📕 Collapse tool click at {pos.x}, {pos.y}")

        # Find node under mouse
        target_node = self.get_node_at_position(pos.x, pos.y)

        if target_node and target_node.is_container:
            print(f"DEBUG: 📕 Collapsing container {target_node.text}")

            # Collapse the container
            target_node.is_expanded = False

            # Hide all contained nodes and edges
            for child_id in target_node.child_ids:
                child_node = self.graph.get_node(child_id)
                if child_node:
                    child_node.visible = False

            for edge_id in target_node.contained_edge_ids:
                edge = self.graph.get_edge(edge_id)
                if edge:
                    edge.visible = False

            # Redirect edges from internal nodes to the container
            print(
                f"DEBUG: 📕 Redirecting edges from internal nodes to container")
            edges_redirected = 0

            for edge in self.graph.get_all_edges():
                if not edge.visible:  # Skip already hidden internal edges
                    continue

                # Check if edge connects to any internal node
                source_node = self.graph.get_node(edge.source_id)
                target_edge_node = self.graph.get_node(edge.target_id)

                if source_node and source_node.id in target_node.child_ids:
                    # Source is internal - redirect source to container
                    print(
                        f"DEBUG: 📕 Redirecting edge {edge.id} source from {source_node.text} to {target_node.text}"
                    )
                    target_node.add_redirected_edge(edge.id, edge.source_id)
                    edge.source_id = target_node.id
                    edges_redirected += 1

                elif target_edge_node and target_edge_node.id in target_node.child_ids:
                    # Target is internal - redirect target to container
                    print(
                        f"DEBUG: 📕 Redirecting edge {edge.id} target from {target_edge_node.text} to {target_node.text}"
                    )
                    target_node.add_redirected_edge(edge.id, edge.target_id)
                    edge.target_id = target_node.id
                    edges_redirected += 1

            print(f"DEBUG: 📕 Redirected {edges_redirected} edges to container")

            # Mark graph as modified
            if hasattr(self, 'graph_modified'):
                self.graph_modified.emit()
            # Notify MVU of updated counts
            try:
                mw = self.GetParent().GetParent()
                if hasattr(mw, 'mvu_adapter'):
                    from mvc_mvu.messages import make_message
                    import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
                    all_nodes = len(self.graph.get_all_nodes())
                    all_edges = len(self.graph.get_all_edges())
                    mw.mvu_adapter.dispatch(
                        make_message(m_main_mvu.Msg.SET_COUNTS,
                                     nodes=all_nodes,
                                     edges=all_edges))
            except Exception:
                pass

            self.Refresh()
            print(
                f"DEBUG: 📕 Container collapsed with {edges_redirected} edges redirected"
            )
        else:
            print(f"DEBUG: 📕 No container found or not a container")

    def handle_recursive_expand_down(self, pos):
        """Handle recursive expand tool click."""

        print(f"DEBUG: 🔄📖 Recursive expand tool click at {pos.x}, {pos.y}")

        # Find node under mouse
        target_node = self.get_node_at_position(pos.x, pos.y)

        if target_node and target_node.is_container:
            print(
                f"DEBUG: 🔄📖 Starting recursive expand from container {target_node.text}"
            )
            expanded_count = self.recursive_expand_node(target_node)

            # Mark graph as modified
            if hasattr(self, 'graph_modified'):
                self.graph_modified.emit()
            # Notify MVU of updated counts
            try:
                mw = self.GetParent().GetParent()
                if hasattr(mw, 'mvu_adapter'):
                    from mvc_mvu.messages import make_message
                    import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
                    all_nodes = len(self.graph.get_all_nodes())
                    all_edges = len(self.graph.get_all_edges())
                    mw.mvu_adapter.dispatch(
                        make_message(m_main_mvu.Msg.SET_COUNTS,
                                     nodes=all_nodes,
                                     edges=all_edges))
            except Exception:
                pass

            self.Refresh()
            print(
                f"DEBUG: 🔄📖 Recursive expand completed - expanded {expanded_count} containers"
            )

            # Show feedback message
            import wx
            wx.MessageBox(
                f"Recursively expanded {expanded_count} containers starting from '{target_node.text}'",
                "Recursive Expand", wx.OK | wx.ICON_INFORMATION)
        else:
            print(f"DEBUG: 🔄📖 No container found or not a container")

    def handle_recursive_collapse_down(self, pos):
        """Handle recursive collapse tool click."""

        print(f"DEBUG: 🔄📕 Recursive collapse tool click at {pos.x}, {pos.y}")

        # Find node under mouse
        target_node = self.get_node_at_position(pos.x, pos.y)

        if target_node and target_node.is_container:
            print(
                f"DEBUG: 🔄📕 Starting recursive collapse from container {target_node.text}"
            )
            collapsed_count = self.recursive_collapse_node(target_node)

            # Mark graph as modified
            if hasattr(self, 'graph_modified'):
                self.graph_modified.emit()
            # Notify MVU of updated counts
            try:
                mw = self.GetParent().GetParent()
                if hasattr(mw, 'mvu_adapter'):
                    from mvc_mvu.messages import make_message
                    import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
                    all_nodes = len(self.graph.get_all_nodes())
                    all_edges = len(self.graph.get_all_edges())
                    mw.mvu_adapter.dispatch(
                        make_message(m_main_mvu.Msg.SET_COUNTS,
                                     nodes=all_nodes,
                                     edges=all_edges))
            except Exception:
                pass

            self.Refresh()
            print(
                f"DEBUG: 🔄📕 Recursive collapse completed - collapsed {collapsed_count} containers"
            )

            # Show feedback message
            import wx
            wx.MessageBox(
                f"Recursively collapsed {collapsed_count} containers starting from '{target_node.text}'",
                "Recursive Collapse", wx.OK | wx.ICON_INFORMATION)
        else:
            print(f"DEBUG: 🔄📕 No container found or not a container")

    def recursive_expand_node(self, container_node):
        """Recursively expand a container node and all its child containers."""

        if not container_node.is_container:
            return 0

        expanded_count = 0

        # First, expand this container if it's collapsed
        if not container_node.is_expanded:
            print(f"DEBUG: 🔄📖 Expanding container {container_node.text}")

            # Expand the container
            container_node.is_expanded = True

            # Show all contained nodes and edges
            for child_id in container_node.child_ids:
                child_node = self.graph.get_node(child_id)
                if child_node:
                    child_node.visible = True

            for edge_id in container_node.contained_edge_ids:
                edge = self.graph.get_edge(edge_id)
                if edge:
                    edge.visible = True

            # Restore redirected edges to their original nodes
            print(
                f"DEBUG: 🔄📖 Restoring redirected edges from container {container_node.text}"
            )
            redirected_edges = container_node.get_redirected_edges()

            for edge_id, original_node_id in redirected_edges.items():
                edge = self.graph.get_edge(edge_id)
                if edge:
                    # Determine if this was a source or target redirection
                    if edge.source_id == container_node.id:
                        # Restore source
                        print(
                            f"DEBUG: 🔄📖 Restoring edge {edge_id} source from {container_node.text} to {original_node_id}"
                        )
                        edge.source_id = original_node_id
                    elif edge.target_id == container_node.id:
                        # Restore target
                        print(
                            f"DEBUG: 🔄📖 Restoring edge {edge_id} target from {container_node.text} to {original_node_id}"
                        )
                        edge.target_id = original_node_id

                    # Remove the redirection record
                    container_node.remove_redirected_edge(edge_id)

            expanded_count += 1

        # Then recursively expand all child containers
        for child_id in container_node.child_ids:
            child_node = self.graph.get_node(child_id)
            if child_node and child_node.is_container:
                expanded_count += self.recursive_expand_node(child_node)

        return expanded_count

    def is_edge_redirected(self, edge):
        """Check if an edge has been redirected due to container collapse."""

        # Check all container nodes to see if any have this edge in their redirected_edges
        for node in self.graph.get_all_nodes():
            if node.is_container and hasattr(node, 'redirected_edges'):
                if edge.id in node.redirected_edges:
                    return True
        return False

    def recursive_collapse_node(self, container_node):
        """Recursively collapse a container node and all its child containers."""

        if not container_node.is_container:
            return 0

        collapsed_count = 0

        # First, recursively collapse all child containers
        for child_id in container_node.child_ids:
            child_node = self.graph.get_node(child_id)
            if child_node and child_node.is_container:
                collapsed_count += self.recursive_collapse_node(child_node)

        # Then collapse this container if it's expanded
        if container_node.is_expanded:
            print(f"DEBUG: 🔄📕 Collapsing container {container_node.text}")

            # Collapse the container
            container_node.is_expanded = False

            # Hide all contained nodes and edges
            for child_id in container_node.child_ids:
                child_node = self.graph.get_node(child_id)
                if child_node:
                    child_node.visible = False

            for edge_id in container_node.contained_edge_ids:
                edge = self.graph.get_edge(edge_id)
                if edge:
                    edge.visible = False

            # Redirect edges from internal nodes to the container
            print(
                f"DEBUG: 🔄📕 Redirecting edges from internal nodes to container {container_node.text}"
            )
            edges_redirected = 0

            for edge in self.graph.get_all_edges():
                if not edge.visible:  # Skip already hidden internal edges
                    continue

                # Check if edge connects to any internal node
                source_node = self.graph.get_node(edge.source_id)
                target_edge_node = self.graph.get_node(edge.target_id)

                if source_node and source_node.id in container_node.child_ids:
                    # Source is internal - redirect source to container
                    print(
                        f"DEBUG: 🔄📕 Redirecting edge {edge.id} source from {source_node.text} to {container_node.text}"
                    )
                    container_node.add_redirected_edge(edge.id, edge.source_id)
                    edge.source_id = container_node.id
                    edges_redirected += 1

                elif target_edge_node and target_edge_node.id in container_node.child_ids:
                    # Target is internal - redirect target to container
                    print(
                        f"DEBUG: 🔄📕 Redirecting edge {edge.id} target from {target_edge_node.text} to {container_node.text}"
                    )
                    container_node.add_redirected_edge(edge.id, edge.target_id)
                    edge.target_id = container_node.id
                    edges_redirected += 1

            print(
                f"DEBUG: 🔄📕 Redirected {edges_redirected} edges to container {container_node.text}"
            )
            collapsed_count += 1

        return collapsed_count

    def draw_container_target_feedback(self, dc):
        """Draw visual feedback for potential container target."""

        if not self.container_target:
            return

        # Get screen position of target container
        screen_pos = self.world_to_screen(self.container_target.x,
                                          self.container_target.y)

        # Apply world rotation to get visual position
        if self.world_rotation != 0.0:
            size = self.GetSize()
            center_x = size.width // 2
            center_y = size.height // 2

            rotation_rad = math.radians(self.world_rotation)
            cos_angle = math.cos(rotation_rad)
            sin_angle = math.sin(rotation_rad)

            temp_x = screen_pos[0] - center_x
            temp_y = screen_pos[1] - center_y

            rotated_x = temp_x * cos_angle - temp_y * sin_angle
            rotated_y = temp_x * sin_angle + temp_y * cos_angle

            visual_x = rotated_x + center_x
            visual_y = rotated_y + center_y
        else:
            visual_x, visual_y = screen_pos

        # Draw highlight around container target
        dc.SetPen(wx.Pen(wx.Colour(0, 255, 0), 3))  # Green highlight
        dc.SetBrush(wx.Brush(wx.Colour(0, 255, 0,
                                       50)))  # Semi-transparent green

        width = int(self.container_target.width * self.zoom)
        height = int(self.container_target.height * self.zoom)

        highlight_rect = wx.Rect(int(visual_x - width // 2 - 5),
                                 int(visual_y - height // 2 - 5), width + 10,
                                 height + 10)
        dc.DrawRoundedRectangle(highlight_rect, 8)

    def draw_drag_into_feedback(self, dc):
        """Draw visual feedback while dragging selection into container."""

        if not self.dragging_selection:
            return

        # Draw semi-transparent overlay on dragged items
        dc.SetPen(wx.Pen(wx.Colour(255, 165, 0), 2))  # Orange outline
        dc.SetBrush(wx.Brush(wx.Colour(255, 165, 0,
                                       80)))  # Semi-transparent orange

        for item in self.dragging_selection:
            if hasattr(item, 'text'):  # It's a node
                screen_pos = self.world_to_screen(item.x, item.y)

                # Apply world rotation for visual position
                if self.world_rotation != 0.0:
                    size = self.GetSize()
                    center_x = size.width // 2
                    center_y = size.height // 2

                    rotation_rad = math.radians(self.world_rotation)
                    cos_angle = math.cos(rotation_rad)
                    sin_angle = math.sin(rotation_rad)

                    temp_x = screen_pos[0] - center_x
                    temp_y = screen_pos[1] - center_y

                    rotated_x = temp_x * cos_angle - temp_y * sin_angle
                    rotated_y = temp_x * sin_angle + temp_y * cos_angle

                    visual_x = rotated_x + center_x
                    visual_y = rotated_y + center_y
                else:
                    visual_x, visual_y = screen_pos

                width = int(item.width * self.zoom)
                height = int(item.height * self.zoom)

                drag_rect = wx.Rect(int(visual_x - width // 2),
                                    int(visual_y - height // 2), width, height)
                dc.DrawRoundedRectangle(drag_rect, 5)

    def handle_node_creation_old(self, pos):
        """Old handle node creation - now redirects to new method."""

        # Redirect to the new method that uses undo system
        self.handle_node_creation(pos)

    def get_connection_point_at_position(self, screen_x, screen_y):
        """Check if position is over a connection point. Returns (edge, point_type, node_id) or None.
        point_type can be 'from' or 'to'
        """

        dot_radius = max(6, int(4 * self.zoom))

        # Apply inverse rotation to get coordinates in the same space as drawing
        test_x, test_y = screen_x, screen_y
        if self.world_rotation != 0.0:
            size = self.GetSize()
            center_x = size.width // 2
            center_y = size.height // 2

            rotation_rad = -math.radians(
                self.world_rotation)  # Negative for inverse
            cos_angle = math.cos(rotation_rad)
            sin_angle = math.sin(rotation_rad)

            temp_x = screen_x - center_x
            temp_y = screen_y - center_y

            test_x = temp_x * cos_angle - temp_y * sin_angle + center_x
            test_y = temp_x * sin_angle + temp_y * cos_angle + center_y

        for edge in self.graph.get_all_edges():
            # Skip ubergraph hyperedges: they don't expose cyan/magenta connection dots
            try:
                if getattr(edge, 'is_hyperedge', False) and getattr(
                        edge, 'hyperedge_visualization', '') == 'ubergraph':
                    continue
            except Exception:
                pass
            source_node = self.graph.get_node(edge.source_id)
            target_node = self.graph.get_node(edge.target_id)

            if not source_node or not target_node:
                continue

            # Get screen positions
            source_screen = self.world_to_screen(source_node.x, source_node.y)
            target_screen = self.world_to_screen(target_node.x, target_node.y)

            # Calculate adjusted edge endpoints
            source_adjusted = self.calculate_line_endpoint(
                source_node, target_node, source_screen, target_screen, True,
                edge)
            target_adjusted = self.calculate_line_endpoint(
                target_node, source_node, target_screen, source_screen, False,
                edge)

            # Calculate positions along the edge
            dx = target_adjusted[0] - source_adjusted[0]
            dy = target_adjusted[1] - source_adjusted[1]

            # Check cyan (from) connection point
            from_x = source_adjusted[0] + dx * edge.from_connection_point
            from_y = source_adjusted[1] + dy * edge.from_connection_point
            from_dist = math.sqrt((test_x - from_x)**2 + (test_y - from_y)**2)
            if from_dist <= dot_radius:
                return (edge, 'from', edge.source_id)

            # Check purple (to) connection point
            to_x = source_adjusted[0] + dx * edge.to_connection_point
            to_y = source_adjusted[1] + dy * edge.to_connection_point
            to_dist = math.sqrt((test_x - to_x)**2 + (test_y - to_y)**2)
            if to_dist <= dot_radius:
                return (edge, 'to', edge.target_id)

        return None

    def handle_edge_creation_start(self, pos):
        """Handle edge creation start."""

        print(f"DEBUG: 🟢 handle_edge_creation_start at ({pos.x}, {pos.y})")
        # First check if we're starting from a connection point
        connection_info = self.get_connection_point_at_position(pos.x, pos.y)
        if connection_info:
            edge, point_type, node_id = connection_info
            self.edge_start_node = self.graph.get_node(node_id)
            self.edge_start_connection = (edge, point_type)
            print(
                f"DEBUG: 🟢 start from connection point on node {node_id} ({point_type})"
            )
        else:
            # If not a connection point, check if starting on an edge body to support edge→edge linking (uberedge)
            start_edge = self.get_edge_at_position(pos.x, pos.y)
            if start_edge:
                self.edge_start_node = None
                self.edge_start_connection = None
                self.edge_start_uberedge = start_edge
                print(
                    f"DEBUG: 🟢 start from edge body (edge→edge link) {start_edge.id}"
                )
                return
            # Regular edge creation
            node = self.get_node_at_position(pos.x, pos.y)
        if node:
            self.edge_start_node = node
            self.edge_start_connection = None
            print(f"DEBUG: 🟢 start from node {node.id}")
            if self.edge_rendering_type == "freeform":
                # Create temporary edge for preview
                self.temp_edge = m_edge.Edge(source_id=node.id,
                                             target_id=node.id)
                self.temp_edge.rendering_type = "freeform"
                # Convert screen coordinates to world coordinates for start point
                world_pos = self.screen_to_world(pos.x, pos.y)
                self.temp_path_points = [(world_pos[0], world_pos[1], 0.0)
                                         ]  # Start point
        else:
            print("DEBUG: 🟡 No start node under cursor for edge start")

    def handle_edge_creation_end(self, pos):
        """Handle edge creation end."""

        # Uberedge flows (handle first): starting from an uberedge square
        if hasattr(self, 'edge_start_uberedge') and self.edge_start_uberedge:
            end_edge = self.get_edge_at_position(pos.x, pos.y)
            if end_edge:
                e1 = self.edge_start_uberedge
                e2 = end_edge
                # Ensure both edges are ubergraph hyperedges
                try:
                    if getattr(e1, 'source_id',
                               None) and e1.source_id not in e1.source_ids:
                        e1.source_ids.append(e1.source_id)
                    if getattr(e1, 'target_id',
                               None) and e1.target_id not in e1.target_ids:
                        e1.target_ids.append(e1.target_id)
                    e1.is_hyperedge = True
                    e1.hyperedge_visualization = 'ubergraph'
                    e1.hyperedge_view = 'line_graph'
                    # Ensure default dimensions
                    if not getattr(e1, 'uber_width', None):
                        e1.uber_width = 60.0
                    if not getattr(e1, 'uber_height', None):
                        e1.uber_height = 40.0
                    if not getattr(e1, 'uber_shape', None):
                        e1.uber_shape = 'rectangle'
                    # Seed uber position if needed
                    try:
                        s = self.graph.get_node(e1.source_id)
                        t = self.graph.get_node(e1.target_id)
                        if s and t:
                            e1.uber_x = (s.x + t.x) / 2.0
                            e1.uber_y = (s.y + t.y) / 2.0
                    except Exception:
                        pass

                    if getattr(e2, 'source_id',
                               None) and e2.source_id not in e2.source_ids:
                        e2.source_ids.append(e2.source_id)
                    if getattr(e2, 'target_id',
                               None) and e2.target_id not in e2.target_ids:
                        e2.target_ids.append(e2.target_id)
                    e2.is_hyperedge = True
                    e2.hyperedge_visualization = 'ubergraph'
                    e2.hyperedge_view = 'line_graph'
                    if not getattr(e2, 'uber_width', None):
                        e2.uber_width = 60.0
                    if not getattr(e2, 'uber_height', None):
                        e2.uber_height = 40.0
                    if not getattr(e2, 'uber_shape', None):
                        e2.uber_shape = 'rectangle'
                    try:
                        s = self.graph.get_node(e2.source_id)
                        t = self.graph.get_node(e2.target_id)
                        if s and t:
                            e2.uber_x = (s.x + t.x) / 2.0
                            e2.uber_y = (s.y + t.y) / 2.0
                    except Exception:
                        pass

                    # Record an explicit edge-to-edge connection so line_graph view draws a link
                    lst = e1.metadata.get('connected_uberedges') if hasattr(
                        e1, 'metadata') else None
                    if lst is None:
                        e1.metadata['connected_uberedges'] = []
                        lst = e1.metadata['connected_uberedges']
                    # Allow duplicates to represent parallel uberedges
                    lst.append(e2.id)
                    # Directionality control: hold 'Shift' to reverse (second as source of first), else second is target of first
                    try:
                        reverse = False
                        try:
                            reverse = wx.GetKeyState(wx.WXK_SHIFT)
                        except Exception:
                            reverse = False
                        dir_map = e1.metadata.get(
                            'connected_uberedges_dir') or {}
                        dir_map[str(e2.id)] = 'from' if reverse else 'to'
                        e1.metadata['connected_uberedges_dir'] = dir_map
                        e1.directed = True
                    except Exception:
                        pass
                    self.graph_modified.emit()
                    self.Refresh()
                except Exception as _e:
                    pass
                # Clear state
                self.edge_start_uberedge = None
                return

            # If not ending on an uberedge, allow ending on a node to create uberedge↔node segment
            end_node = self.get_node_at_position(pos.x, pos.y)
            if end_node:
                e1 = self.edge_start_uberedge
                try:
                    e1.is_hyperedge = True
                    e1.hyperedge_visualization = 'ubergraph'
                    e1.hyperedge_view = 'line_graph'
                    if not getattr(e1, 'uber_width', None):
                        e1.uber_width = 60.0
                    if not getattr(e1, 'uber_height', None):
                        e1.uber_height = 40.0
                    if not getattr(e1, 'uber_shape', None):
                        e1.uber_shape = 'rectangle'
                    # Default: add node as a target connection
                    if not hasattr(e1, 'target_ids') or e1.target_ids is None:
                        e1.target_ids = []
                    if end_node.id not in e1.target_ids and end_node.id != getattr(
                            e1, 'target_id', None):
                        e1.target_ids.append(end_node.id)
                    self.graph_modified.emit()
                    self.Refresh()
                except Exception:
                    pass
                # Clear state
                self.edge_start_uberedge = None
                return

            # No valid end target; clear and exit
            self.edge_start_uberedge = None
            return

        # Fallback: if start node was not captured on mouse down, try to latch it on mouse up
        if not self.edge_start_node:
            start_node = self.get_node_at_position(pos.x, pos.y)
            if start_node:
                self.edge_start_node = start_node
                self.edge_start_connection = None
                # If freeform, seed a temp edge and starting point in world coordinates
                if self.edge_rendering_type == "freeform":
                    self.temp_edge = m_edge.Edge(source_id=start_node.id,
                                                 target_id=start_node.id)
                    self.temp_edge.rendering_type = "freeform"
                    world_pos = self.screen_to_world(pos.x, pos.y)
                    self.temp_path_points = [(world_pos[0], world_pos[1], 0.0)]
                print(
                    f"DEBUG: 🟡 Edge start latched on mouse up at node {start_node.id}"
                )
                return
            # In Ubergraph mode, clicking empty space should create a standalone uberedge box
            try:
                if getattr(self, 'selected_graph_type', 3) in (6, 7):
                    if not self.get_node_at_position(
                            pos.x, pos.y) and not self.get_edge_at_position(
                                pos.x, pos.y):
                        world_pos = self.screen_to_world(pos.x, pos.y)
                        new_e = m_edge.Edge(source_id=None, target_id=None)
                        new_e.is_hyperedge = True
                        new_e.hyperedge_visualization = 'ubergraph'
                        new_e.hyperedge_view = 'line_graph'
                        new_e.uber_x = world_pos[0]
                        new_e.uber_y = world_pos[1]
                        # Standardize default uberedge box to match connected creation
                        new_e.uber_width = 60.0
                        new_e.uber_height = 40.0
                        new_e.uber_shape = 'rectangle'
                        # visual parity with connected uberedges: ensure text and style defaults
                        try:
                            new_e.width = getattr(new_e, 'width', 2)
                            new_e.line_style = getattr(new_e, 'line_style', 'solid')
                            if not getattr(new_e, 'color', None):
                                new_e.color = (50, 50, 50)
                        except Exception:
                            pass
                        new_e.directed = True
                        # Make it self-referential so it passes add_edge validation
                        new_e.source_id = new_e.id
                        new_e.target_id = new_e.id
                        # Bypass undo; add directly
                        try:
                            self.graph.edges[new_e.id] = new_e
                            self.graph.modified = True
                        except Exception:
                            pass
                        self.graph_modified.emit()
                        self.Refresh()
                        print(
                            "DEBUG: 🆕 Created standalone uberedge box on empty space"
                        )
                        return
            except Exception as _e:
                print(f"DEBUG: ⚠️ Failed creating standalone uberedge: {_e}")
            print(
                "DEBUG: 🟡 Edge start not found on mouse up - click directly on a node to start"
            )
            return

        if self.edge_start_node:
            # Check if we're ending on a connection point
            connection_info = self.get_connection_point_at_position(
                pos.x, pos.y)
            if connection_info:
                # Ending on a connection point
                edge, point_type, node_id = connection_info
                print(
                    f"DEBUG: 🔵 end on connection point for node {node_id} ({point_type})"
                )
                if point_type == 'from':
                    edge.add_from_node(self.edge_start_node.id)
                else:  # 'to'
                    edge.add_to_node(self.edge_start_node.id)
                self.graph.modified = True
                self.graph_modified.emit()
                # Clear temporary edge state
                self.temp_edge = None
                self.temp_path_points = []
                self.edge_start_node = None
                self.edge_start_connection = None
                return
            else:
                # Ending on an uberedge square: attach node to that uberedge (Ubergraph)
                end_edge_square = self.get_edge_at_position(pos.x, pos.y)
                if end_edge_square and getattr(
                        end_edge_square, 'is_hyperedge', False) and getattr(
                            end_edge_square, 'hyperedge_visualization',
                            '') == 'ubergraph':
                    print(
                        f"DEBUG: 🔵 end on uberedge square {end_edge_square.id} from node {self.edge_start_node.id}"
                    )
                    try:
                        # Ensure ubergraph defaults
                        end_edge_square.is_hyperedge = True
                        end_edge_square.hyperedge_visualization = 'ubergraph'
                        if not getattr(end_edge_square, 'uber_width', None):
                            end_edge_square.uber_width = 60.0
                        if not getattr(end_edge_square, 'uber_height', None):
                            end_edge_square.uber_height = 40.0
                        # Attach node as a target by default
                        if not hasattr(end_edge_square, 'target_ids'
                                       ) or end_edge_square.target_ids is None:
                            end_edge_square.target_ids = []
                        if self.edge_start_node.id not in end_edge_square.target_ids and self.edge_start_node.id != getattr(
                                end_edge_square, 'target_id', None):
                            end_edge_square.target_ids.append(
                                self.edge_start_node.id)
                        self.graph.modified = True
                        self.graph_modified.emit()
                    except Exception as _e:
                        print(
                            f"DEBUG: ⚠️ Error attaching node to uberedge: {_e}"
                        )
                    # Clear temporary edge state
                    self.temp_edge = None
                    self.temp_path_points = []
                    self.edge_start_node = None
                    self.edge_start_connection = None
                    return
                # Check if we're starting from a connection point
                target_node = self.get_node_at_position(pos.x, pos.y)
            if target_node:  # Allow self-loops by removing the != check
                print(f"DEBUG: 🔵 end on node {target_node.id}")
                if self.edge_start_connection:
                    # Starting from a connection point
                    edge, point_type = self.edge_start_connection
                    if point_type == 'from':
                        edge.add_from_node(target_node.id)
                    else:  # 'to'
                        edge.add_to_node(target_node.id)
                    self.graph.modified = True
                    self.graph_modified.emit()
                    # Clear temporary edge state
                    self.temp_edge = None
                    self.temp_path_points = []
                    self.edge_start_node = None
                    self.edge_start_connection = None
                    return
                else:
                    # Regular edge creation
                    # Check graph restrictions before creating edge
                    if not self.check_edge_restrictions(
                            self.edge_start_node, target_node):
                        self.temp_edge = None
                        self.temp_path_points = []
                        return

                # Create edge using command pattern
                from graph_canvas.presentation.desktop.models.edge import Edge

                # Create the edge
                edge = m_edge.Edge(source_id=self.edge_start_node.id,
                                   target_id=target_node.id)
                # If graph type is Ubergraph, create as uberedge with defaults
                try:
                    if getattr(self, 'selected_graph_type', 3) in (6, 7):
                        edge.is_hyperedge = True
                        edge.hyperedge_visualization = 'ubergraph'
                        edge.hyperedge_view = 'line_graph'
                        if not getattr(edge, 'uber_width', None):
                            edge.uber_width = 60.0
                        if not getattr(edge, 'uber_height', None):
                            edge.uber_height = 40.0
                        if not getattr(edge, 'uber_shape', None):
                            edge.uber_shape = 'rectangle'
                        # Seed uber position near midpoint of endpoints
                        edge.uber_x = (self.edge_start_node.x +
                                       target_node.x) / 2.0
                        edge.uber_y = (self.edge_start_node.y +
                                       target_node.y) / 2.0
                except Exception:
                    pass
                if self.edge_rendering_type == "freeform" and self.temp_edge:
                    # Use the collected path points for the new edge
                    edge.rendering_type = "freeform"
                    edge.freeform_points = self.temp_path_points.copy(
                    )  # Make a copy to avoid reference issues
                    # Replace the last point with target node position to ensure clean connection
                    target_pos = (target_node.x, target_node.y, 0.0)
                    if len(edge.freeform_points) > 0:
                        edge.freeform_points[-1] = target_pos
                    else:
                        edge.freeform_points.append(target_pos)
                    # Ensure the edge is not treated as composite
                    edge.is_composite = False
                    edge.curve_segments = []
                    self.temp_edge = None
                    self.temp_path_points = []

                # Set default arrow position to 50%
                edge.arrow_position = 0.5

                # Set direction based on UI setting
                try:
                    # GraphCanvas -> main_panel -> MainWindow
                    main_window = self.GetParent().GetParent()
                    if hasattr(main_window, 'edge_directed_cb'):
                        directed_value = main_window.edge_directed_cb.GetValue(
                        )
                        edge.directed = directed_value
                        print(
                            f"DEBUG: Created edge with directed={directed_value} from UI checkbox"
                        )
                    else:
                        print(
                            "DEBUG: Could not find edge_directed_cb, using default directed=True"
                        )
                        edge.directed = True
                except Exception as e:
                    print(
                        f"DEBUG: Error accessing MainWindow, using default directed=True: {e}"
                    )
                    edge.directed = True

                # Initialize control points for the new edge
                self.initialize_control_points(edge, self.edge_start_node,
                                               target_node)
                print(
                    f"DEBUG: ✅ Created edge {edge.id} from {self.edge_start_node.id} to {target_node.id}"
                )

                # Execute command
                if self.undo_redo_manager:
                    command = m_commands.AddEdgeCommand(self.graph, edge)
                    self.undo_redo_manager.execute_command(command)
                else:
                    # Fallback if no undo manager
                    self.graph.add_edge(edge)

                # Best-effort mirror to backend
                try:
                    mw = self.GetParent()
                    backend = getattr(mw, 'backend', None)
                    if backend and getattr(backend, 'is_available', lambda: False)():
                        backend.create_edge(edge.source_id, edge.target_id, edge.text)
                except Exception:
                    pass

                self.graph_modified.emit()
                self.Refresh()
            else:
                print("DEBUG: 🟡 No target node under cursor for edge end")

        self.edge_start_node = None

    def check_edge_restrictions(self, source_node, target_node):
        """Check if creating an edge between source and target nodes violates any restrictions."""

        # Check for loops restriction
        if self.no_loops and source_node.id == target_node.id:
            wx.MessageBox(
                "Cannot create self-loop: No loops restriction is enabled.",
                "Graph Restriction", wx.OK | wx.ICON_WARNING)
            print(
                f"DEBUG: 🔒 Blocked self-loop creation due to no_loops restriction"
            )
            return False

        # Check for multigraph restriction (skip in Ubergraph/Typed Ubergraph so multiple uberedges are allowed)
        is_ubergraph = False
        try:
            is_ubergraph = getattr(self, 'selected_graph_type', 3) in (6, 7)
        except Exception:
            is_ubergraph = False
        if self.no_multigraphs and not is_ubergraph:
            # Check if an edge already exists between these nodes (in either direction)
            existing_edges = self.graph.get_all_edges()
            for edge in existing_edges:
                if ((edge.source_id == source_node.id
                     and edge.target_id == target_node.id)
                        or (edge.source_id == target_node.id
                            and edge.target_id == source_node.id)):
                    wx.MessageBox(
                        f"Cannot create multiple edges between the same nodes: No multigraphs restriction is enabled.",
                        "Graph Restriction", wx.OK | wx.ICON_WARNING)
                    print(
                        f"DEBUG: 🔒 Blocked multiple edge creation due to no_multigraphs restriction"
                    )
                    return False

        # Check graph type restriction
        if self.graph_type_restriction != 0:  # Not "No Restrictions"
            try:
                # Get the current directed setting from the UI
                main_window = self.GetParent().GetParent()
                if hasattr(main_window, 'edge_directed_cb'):
                    is_directed = main_window.edge_directed_cb.GetValue()

                    if self.graph_type_restriction == 1:  # Require Directed Graph
                        if not is_directed:
                            wx.MessageBox(
                                "Cannot create undirected edge: Graph requires all edges to be directed.",
                                "Graph Restriction", wx.OK | wx.ICON_WARNING)
                            print(
                                f"DEBUG: 🔒 Blocked undirected edge creation due to directed-only restriction"
                            )
                            return False

                    elif self.graph_type_restriction == 2:  # Require Undirected Graph
                        if is_directed:
                            wx.MessageBox(
                                "Cannot create directed edge: Graph requires all edges to be undirected.",
                                "Graph Restriction", wx.OK | wx.ICON_WARNING)
                            print(
                                f"DEBUG: 🔒 Blocked directed edge creation due to undirected-only restriction"
                            )
                            return False

            except Exception as e:
                print(f"DEBUG: 🔒 Error checking graph type restriction: {e}")

        return True  # All restrictions passed

    def select_items_in_rect(self, rect):
        """Select all nodes and edges within the given rectangle.

        The rectangle is provided in SCREEN coordinates. We convert its corners to WORLD
        coordinates (accounting for zoom/pan/rotation) and perform selection entirely in
        WORLD space using polygon intersection tests. This guarantees correct behavior
        regardless of rotation.
        """

        print(
            f"DEBUG: Selecting items in screen rect: {rect.x}, {rect.y}, {rect.width}, {rect.height}"
        )
        print(f"DEBUG: World rotation: {self.world_rotation}°")

        # Build world-space polygon from the screen-space selection rectangle
        screen_corners = [(rect.x, rect.y), (rect.x + rect.width, rect.y),
                          (rect.x + rect.width, rect.y + rect.height),
                          (rect.x, rect.y + rect.height)]
        world_poly = [
            self.screen_to_world(int(px), int(py))
            for (px, py) in screen_corners
        ]
        print(f"DEBUG: World selection polygon: {world_poly}")

        def point_in_polygon(point, polygon):
            x, y = point
            inside = False
            n = len(polygon)
            for i in range(n):
                x1, y1 = polygon[i]
                x2, y2 = polygon[(i + 1) % n]
                if ((y1 > y) != (y2 > y)):
                    xinters = (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1
                    if x < xinters:
                        inside = not inside
            return inside

        def polygons_intersect(poly1, poly2):
            # Any edge intersection?
            for i in range(len(poly1)):
                p1 = poly1[i]
                p2 = poly1[(i + 1) % len(poly1)]
                for j in range(len(poly2)):
                    q1 = poly2[j]
                    q2 = poly2[(j + 1) % len(poly2)]
                    if self.line_segments_intersect(p1, p2, q1, q2):
                        return True
            # One contains the other?
            if point_in_polygon(poly1[0], poly2):
                return True
            if point_in_polygon(poly2[0], poly1):
                return True
            return False

        # Select nodes within world polygon
        nodes_selected = 0
        for node in self.graph.get_all_nodes():
            if not node.visible:
                continue

            node_poly = self._get_node_corners(
                node)  # world corners with node rotation

            if polygons_intersect(node_poly, world_poly) or point_in_polygon(
                (node.x, node.y), world_poly):
                self.graph.select_node(node.id)
                nodes_selected += 1
                print(
                    f"DEBUG: ✅ Selected node '{node.text}' via world polygon intersection"
                )
            else:
                print(
                    f"DEBUG: ❌ Node '{node.text}' not intersecting world selection polygon"
                )

        # Select edges that intersect world polygon
        edges_selected = 0
        for edge in self.graph.get_all_edges():
            if self.edge_intersects_world_polygon(edge, world_poly):
                self.graph.select_edge(edge.id)
                edges_selected += 1

        print(
            f"DEBUG: World polygon selection found {nodes_selected} nodes and {edges_selected} edges"
        )

    def edge_intersects_world_polygon(self, edge, world_polygon):
        """Check if an edge (including curves) intersects with a world-space polygon."""

        source_node = self.graph.get_node(edge.source_id)
        target_node = self.graph.get_node(edge.target_id)

        if not source_node or not target_node:
            return False

        # Sample the curve at multiple world points and test point-in-polygon and segment intersection
        samples = 50

        def point_in_polygon(point, polygon):
            x, y = point
            inside = False
            n = len(polygon)
            for i in range(n):
                x1, y1 = polygon[i]
                x2, y2 = polygon[(i + 1) % n]
                if ((y1 > y) != (y2 > y)):
                    xinters = (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1
                    if x < xinters:
                        inside = not inside
            return inside

        prev_world_point = None
        for i in range(samples + 1):
            t = i / samples
            curve_world_point = self.calculate_position_on_curve(
                edge, source_node, target_node, t)

            if curve_world_point:
                # Check if this world point lies inside polygon
                if point_in_polygon(curve_world_point, world_polygon):
                    return True

                # Check if the world segment intersects the polygon edges
                if prev_world_point:
                    for j in range(len(world_polygon)):
                        q1 = world_polygon[j]
                        q2 = world_polygon[(j + 1) % len(world_polygon)]
                        if self.line_segments_intersect(
                                prev_world_point, curve_world_point, q1, q2):
                            return True

                prev_world_point = curve_world_point

        return False

    def line_segment_intersects_rect(self, p1, p2, rect):
        """Check if a line segment intersects with a rectangle."""

        # Rectangle corners
        rect_left = rect.x
        rect_right = rect.x + rect.width
        rect_top = rect.y
        rect_bottom = rect.y + rect.height

        # Check intersection with each rectangle edge
        rect_edges = [
            ((rect_left, rect_top), (rect_right, rect_top)),  # Top edge
            ((rect_right, rect_top), (rect_right,
                                      rect_bottom)),  # Right edge  
            ((rect_right, rect_bottom), (rect_left,
                                         rect_bottom)),  # Bottom edge
            ((rect_left, rect_bottom), (rect_left, rect_top))  # Left edge
        ]

        for rect_edge in rect_edges:
            if self.line_segments_intersect(p1, p2, rect_edge[0],
                                            rect_edge[1]):
                return True

        return False

    def line_segments_intersect(self, p1, p2, p3, p4):
        """Check if two line segments intersect."""

        def ccw(A, B, C):
            return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] -
                                                                    A[0])

        return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(
            p1, p2, p4)

        # Layout algorithms
        # Removed duplicate set_graph method
        self.dragging_edge_endpoint = False
        self.dragging_edge = None
        self.dragging_endpoint = None
        self.rotating_element = None
        self.dragging_element_rotation = False
        self.dragging_control_point = False
        self.dragging_control_point_edge = None
        self.dragging_control_point_index = -1
        self.dragging_arrow_position = False
        self.dragging_arrow_position_edge = None

        # Clear drag state
        self.drag_offset.clear()
        self.drag_original_positions.clear()

        # Reset view if needed (optional - you might want to preserve the current view)
        # self.zoom = 1.0
        # self.pan_x = 0
        # self.pan_y = 0
        # self.world_rotation = 0.0

        # Emit signals and refresh
        self.selection_changed.emit()
        self.graph_modified.emit()
        self.Refresh()

    def update_edge_endpoints_for_rotated_node(self, edge, rotated_node):
        """Update edge endpoints when a connected node is rotated."""

        source_node = self.graph.get_node(edge.source_id)
        target_node = self.graph.get_node(edge.target_id)

        if not source_node or not target_node:
            return

        # Determine which endpoint needs updating
        if edge.source_id == rotated_node.id:
            # Update source endpoint
            if hasattr(
                    edge,
                    'custom_endpoints') and 'source' in edge.custom_endpoints:
                # For custom endpoints, recalculate the position based on the node's rotation
                # This maintains the relative position on the rotated node
                old_endpoint = edge.custom_endpoints['source']
                # TODO: Apply rotation transformation to the custom endpoint
                print(
                    f"DEBUG: 🔄 Would update custom source endpoint: {old_endpoint}"
                )
            else:
                # For automatic endpoints, select the best anchor point based on edge direction
                world_target_pos = (target_node.x, target_node.y)
                best_anchor = self.calculate_anchor_position(
                    rotated_node, world_target_pos, "nearest_face")
                if not hasattr(edge, 'custom_endpoints'):
                    edge.custom_endpoints = {}
                edge.custom_endpoints['source'] = best_anchor
                print(f"DEBUG: 🔄 Set new source anchor: {best_anchor}")

        if edge.target_id == rotated_node.id:
            # Update target endpoint
            if hasattr(
                    edge,
                    'custom_endpoints') and 'target' in edge.custom_endpoints:
                # For custom endpoints, recalculate the position based on the node's rotation
                old_endpoint = edge.custom_endpoints['target']
                # TODO: Apply rotation transformation to the custom endpoint
                print(
                    f"DEBUG: 🔄 Would update custom target endpoint: {old_endpoint}"
                )
            else:
                # For automatic endpoints, select the best anchor point based on edge direction
                world_source_pos = (source_node.x, source_node.y)
                best_anchor = self.calculate_anchor_position(
                    rotated_node, world_source_pos, "nearest_face")
                if not hasattr(edge, 'custom_endpoints'):
                    edge.custom_endpoints = {}
                edge.custom_endpoints['target'] = best_anchor
                print(f"DEBUG: 🔄 Set new target anchor: {best_anchor}")

    def on_auto_readable_changed(self, event):
        """Handle auto-readable nodes checkbox change."""

        value = self.auto_readable_cb.GetValue()
        print(f"DEBUG: Auto-readable nodes toggled: {value}")
        if hasattr(self.canvas, 'auto_readable_nodes'):
            self.canvas.auto_readable_nodes = value
            self.canvas.Refresh()

    def on_show_nested_edges_changed(self, event):
        """Handle show nested edges checkbox change."""

        value = self.show_nested_edges_cb.GetValue()
        print(f"DEBUG: Show nested edges toggled: {value}")
        if hasattr(self.canvas, 'show_nested_edges'):
            self.canvas.show_nested_edges = value
            self.canvas.Refresh()

    # View control event handlers
    def on_snap_to_original(self, event):
        """Snap to original view (reset zoom and pan)."""

        print("DEBUG: Snapping to original view")
        # Call reset_view directly since we're already in the canvas
        self.reset_view()
        # Also reset the rotation field in the UI to match the saved rotation
        if hasattr(self, 'rotation_field'):
            self.rotation_field.SetValue(self.world_rotation)
        # Update canvas information display
        if hasattr(self, 'main_window') and hasattr(self.main_window,
                                                    'update_canvas_info'):
            self.main_window.update_canvas_info()
