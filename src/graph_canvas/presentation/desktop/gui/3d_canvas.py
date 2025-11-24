"""
3D Canvas with advanced camera system supporting perspective/orthographic projection,
view limits, and full 3D navigation controls.
"""

import wx
import math
import numpy as np
from typing import Tuple, Optional, List
from enum import Enum


class ProjectionMode(Enum):
    """Camera projection modes."""

    PERSPECTIVE = "perspective"
    ORTHOGRAPHIC = "orthographic"


class Camera3D:
    """3D Camera with perspective/orthographic projection and view limits."""
    
    def __init__(self):
        # Camera position
        self.position = np.array([0.0, 0.0, 5.0])  # x, y, z
        
        # Camera orientation (Euler angles in degrees)
        self.rotation = np.array([0.0, 0.0, 0.0])  # pitch, yaw, roll
        
        # Camera target (look-at point)
        self.target = np.array([0.0, 0.0, 0.0])
        
        # Camera vectors
        self.up = np.array([0.0, 1.0, 0.0])
        self.forward = np.array([0.0, 0.0, -1.0])
        self.right = np.array([1.0, 0.0, 0.0])
        
        # Projection settings
        self.projection_mode = ProjectionMode.PERSPECTIVE
        self.fov = 60.0  # Field of view in degrees (for perspective)
        self.near_plane = 0.1
        self.far_plane = 1000.0
        self.ortho_size = 10.0  # Size for orthographic projection
        
        # View limits (optional culling bounds)
        self.use_view_limits = False
        self.view_limits = {
            'x_min': -10.0, 'x_max': 10.0,
            'y_min': -10.0, 'y_max': 10.0,
            'z_min': -10.0, 'z_max': 10.0
        }
        
        # Movement speeds
        self.move_speed = 1.0
        self.rotation_speed = 45.0  # degrees per unit
        self.zoom_speed = 1.0
        
    def update_vectors(self):
        """Update camera vectors based on rotation."""

        # Convert rotation to radians
        pitch = math.radians(self.rotation[0])
        yaw = math.radians(self.rotation[1])
        roll = math.radians(self.rotation[2])
        
        # Calculate forward vector
        self.forward[0] = math.cos(yaw) * math.cos(pitch)
        self.forward[1] = math.sin(pitch)
        self.forward[2] = math.sin(yaw) * math.cos(pitch)
        self.forward = self.forward / np.linalg.norm(self.forward)
        
        # Calculate right vector
        world_up = np.array([0.0, 1.0, 0.0])
        self.right = np.cross(self.forward, world_up)
        self.right = self.right / np.linalg.norm(self.right)
        
        # Calculate up vector
        self.up = np.cross(self.right, self.forward)
        self.up = self.up / np.linalg.norm(self.up)
        
        # Apply roll rotation to up and right vectors
        if roll != 0:
            cos_roll = math.cos(roll)
            sin_roll = math.sin(roll)
            
            new_up = self.up * cos_roll + self.right * sin_roll
            new_right = self.right * cos_roll - self.up * sin_roll
            
            self.up = new_up
            self.right = new_right
    
    def get_view_matrix(self):
        """Get the view matrix for the camera."""

        self.update_vectors()
        
        # Create view matrix using look-at
        eye = self.position
        target = self.position + self.forward
        up = self.up
        
        # Calculate view matrix
        f = (target - eye)
        f = f / np.linalg.norm(f)
        
        s = np.cross(f, up)
        s = s / np.linalg.norm(s)
        
        u = np.cross(s, f)
        
        view_matrix = np.array([
            [s[0], u[0], -f[0], 0],
            [s[1], u[1], -f[1], 0],
            [s[2], u[2], -f[2], 0],
            [-np.dot(s, eye), -np.dot(u, eye), np.dot(f, eye), 1]
        ])
        
        return view_matrix
    
    def get_projection_matrix(self, aspect_ratio: float):
        """Get the projection matrix based on current mode."""

        if self.projection_mode == ProjectionMode.PERSPECTIVE:
            return self._get_perspective_matrix(aspect_ratio)
        else:
            return self._get_orthographic_matrix(aspect_ratio)
    
    def _get_perspective_matrix(self, aspect_ratio: float):
        """Get perspective projection matrix."""

        fov_rad = math.radians(self.fov)
        f = 1.0 / math.tan(fov_rad / 2.0)
        
        return np.array([
            [f / aspect_ratio, 0, 0, 0],
            [0, f, 0, 0],
            [0, 0, (self.far_plane + self.near_plane) / (self.near_plane - self.far_plane), 
             (2 * self.far_plane * self.near_plane) / (self.near_plane - self.far_plane)],
            [0, 0, -1, 0]
        ])
    
    def _get_orthographic_matrix(self, aspect_ratio: float):
        """Get orthographic projection matrix."""

        width = self.ortho_size * aspect_ratio
        height = self.ortho_size
        
        return np.array([
            [2.0 / width, 0, 0, 0],
            [0, 2.0 / height, 0, 0],
            [0, 0, -2.0 / (self.far_plane - self.near_plane), 
             -(self.far_plane + self.near_plane) / (self.far_plane - self.near_plane)],
            [0, 0, 0, 1]
        ])
    
    def move_forward(self, amount: float):
        """Move camera forward/backward."""

        self.position += self.forward * amount * self.move_speed
    
    def move_right(self, amount: float):
        """Move camera right/left."""

        self.position += self.right * amount * self.move_speed
    
    def move_up(self, amount: float):
        """Move camera up/down."""

        self.position += self.up * amount * self.move_speed
    
    def rotate_pitch(self, amount: float):
        """Rotate camera pitch (up/down)."""

        self.rotation[0] += amount * self.rotation_speed
        # Clamp pitch to prevent gimbal lock
        self.rotation[0] = max(-89.0, min(89.0, self.rotation[0]))
    
    def rotate_yaw(self, amount: float):
        """Rotate camera yaw (left/right)."""

        self.rotation[1] += amount * self.rotation_speed
        # Keep yaw in 0-360 range
        self.rotation[1] = self.rotation[1] % 360.0
    
    def rotate_roll(self, amount: float):
        """Rotate camera roll."""

        self.rotation[2] += amount * self.rotation_speed
        # Keep roll in -180 to 180 range
        self.rotation[2] = ((self.rotation[2] + 180.0) % 360.0) - 180.0
    
    def zoom(self, amount: float):
        """Zoom camera (change FOV for perspective, size for orthographic)."""

        if self.projection_mode == ProjectionMode.PERSPECTIVE:
            self.fov -= amount * self.zoom_speed
            self.fov = max(10.0, min(120.0, self.fov))  # Clamp FOV
        else:
            self.ortho_size -= amount * self.zoom_speed * 0.1
            self.ortho_size = max(0.1, self.ortho_size)  # Prevent negative size
    
    def point_in_view_limits(self, point: np.array) -> bool:
        """Check if a 3D point is within view limits."""

        if not self.use_view_limits:
            return True
        
        return (self.view_limits['x_min'] <= point[0] <= self.view_limits['x_max'] and
                self.view_limits['y_min'] <= point[1] <= self.view_limits['y_max'] and
                self.view_limits['z_min'] <= point[2] <= self.view_limits['z_max'])


class Canvas3D(wx.Panel):
    """Advanced 3D Canvas with camera system and world/camera controls."""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        # Camera system
        self.camera = Camera3D()
        
        # World transformation
        self.world_position = np.array([0.0, 0.0, 0.0])
        self.world_rotation = np.array([0.0, 0.0, 0.0])  # pitch, yaw, roll
        self.world_scale = np.array([1.0, 1.0, 1.0])
        
        # Control state
        self.control_mode = "camera"  # "camera" or "world"
        self.mouse_sensitivity = 0.5
        self.key_sensitivity = 0.1
        
        # Movement behavior settings
        self.invert_mouse_x = False
        self.invert_mouse_y = False
        self.invert_movement = False
        self.smooth_movement = True
        
        # Speed settings
        self.mouse_rotation_speed = 1.0
        self.mouse_pan_speed = 1.0
        self.keyboard_move_speed = 1.0
        self.zoom_speed = 1.0
        
        # Mouse interaction state
        self.mouse_pos = wx.Point(0, 0)
        self.last_mouse_pos = wx.Point(0, 0)
        self.left_mouse_down = False
        self.right_mouse_down = False
        self.middle_mouse_down = False
        
        # 3D objects to render (for testing)
        self.objects = []
        self._create_test_objects()
        
        # Rendering settings
        self.show_grid = True
        self.show_axes = True
        self.grid_size = 10
        self.grid_spacing = 1.0
        self.background_color = (50, 50, 50)
        
        # Grid colors for X, Y, Z axes
        self.grid_color_x = (100, 100, 100)  # Gray for X-parallel lines
        self.grid_color_y = (80, 80, 80)     # Darker gray for Y-parallel lines
        self.grid_color_z = (120, 120, 120)  # Lighter gray for Z-parallel lines
        
        # Bind events
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        self.Bind(wx.EVT_RIGHT_DOWN, self.on_right_down)
        self.Bind(wx.EVT_RIGHT_UP, self.on_right_up)
        self.Bind(wx.EVT_MIDDLE_DOWN, self.on_middle_down)
        self.Bind(wx.EVT_MIDDLE_UP, self.on_middle_up)
        self.Bind(wx.EVT_MOTION, self.on_motion)
        self.Bind(wx.EVT_MOUSEWHEEL, self.on_mousewheel)
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.Bind(wx.EVT_KEY_UP, self.on_key_up)
        
        # Make sure the panel can receive keyboard events
        self.SetCanFocus(True)
        
        print("DEBUG: 3D Canvas initialized")
    
    def _create_test_objects(self):
        """Create some test 3D objects for demonstration."""

        # Cube vertices
        cube_vertices = np.array([
            [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],  # Back face
            [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]       # Front face
        ])
        
        # Cube edges (indices)
        cube_edges = [
            [0, 1], [1, 2], [2, 3], [3, 0],  # Back face
            [4, 5], [5, 6], [6, 7], [7, 4],  # Front face
            [0, 4], [1, 5], [2, 6], [3, 7]   # Connecting edges
        ]
        
        self.objects.append({
            'type': 'wireframe',
            'vertices': cube_vertices,
            'edges': cube_edges,
            'position': np.array([0, 0, 0]),
            'color': (255, 255, 255)
        })
        
        # Add coordinate axes
        axes_vertices = np.array([
            [0, 0, 0], [2, 0, 0],  # X axis
            [0, 0, 0], [0, 2, 0],  # Y axis
            [0, 0, 0], [0, 0, 2]   # Z axis
        ])
        
        axes_edges = [[0, 1], [2, 3], [4, 5]]
        axes_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]  # Red, Green, Blue
        
        for i, color in enumerate(axes_colors):
            self.objects.append({
                'type': 'line',
                'vertices': axes_vertices[i*2:(i*2)+2],
                'edges': [[0, 1]],
                'position': np.array([0, 0, 0]),
                'color': color
            })
    
    def get_world_matrix(self):
        """Get the world transformation matrix."""

        # Translation matrix
        T = np.array([
            [1, 0, 0, self.world_position[0]],
            [0, 1, 0, self.world_position[1]],
            [0, 0, 1, self.world_position[2]],
            [0, 0, 0, 1]
        ])
        
        # Rotation matrices
        rx = math.radians(self.world_rotation[0])
        ry = math.radians(self.world_rotation[1])
        rz = math.radians(self.world_rotation[2])
        
        Rx = np.array([
            [1, 0, 0, 0],
            [0, math.cos(rx), -math.sin(rx), 0],
            [0, math.sin(rx), math.cos(rx), 0],
            [0, 0, 0, 1]
        ])
        
        Ry = np.array([
            [math.cos(ry), 0, math.sin(ry), 0],
            [0, 1, 0, 0],
            [-math.sin(ry), 0, math.cos(ry), 0],
            [0, 0, 0, 1]
        ])
        
        Rz = np.array([
            [math.cos(rz), -math.sin(rz), 0, 0],
            [math.sin(rz), math.cos(rz), 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
        
        # Scale matrix
        S = np.array([
            [self.world_scale[0], 0, 0, 0],
            [0, self.world_scale[1], 0, 0],
            [0, 0, self.world_scale[2], 0],
            [0, 0, 0, 1]
        ])
        
        # Combine transformations: T * Rz * Ry * Rx * S
        return T @ Rz @ Ry @ Rx @ S
    
    def project_point(self, point_3d: np.array) -> Tuple[int, int, float]:
        """Project a 3D point to 2D screen coordinates."""

        # Apply world transformation
        world_matrix = self.get_world_matrix()
        point_4d = np.append(point_3d, 1.0)
        world_point = world_matrix @ point_4d
        
        # Apply view transformation
        view_matrix = self.camera.get_view_matrix()
        view_point = view_matrix @ world_point
        
        # Apply projection transformation
        size = self.GetSize()
        aspect_ratio = size.width / size.height if size.height > 0 else 1.0
        projection_matrix = self.camera.get_projection_matrix(aspect_ratio)
        clip_point = projection_matrix @ view_point
        
        # Perspective divide with safety checks
        if abs(clip_point[3]) < 1e-6:
            # Point is at or very close to camera plane, return far offscreen
            return -999999, -999999, -1.0
        
        ndc_point = clip_point[:3] / clip_point[3]
        
        # Clamp NDC coordinates to reasonable range to prevent overflow
        ndc_point[0] = np.clip(ndc_point[0], -10.0, 10.0)
        ndc_point[1] = np.clip(ndc_point[1], -10.0, 10.0)
        
        # Convert to screen coordinates with bounds checking
        screen_x = (ndc_point[0] + 1.0) * 0.5 * size.width
        screen_y = (1.0 - ndc_point[1]) * 0.5 * size.height
        
        # Clamp to reasonable screen coordinate range
        max_coord = 32767  # Safe maximum for screen coordinates
        screen_x = int(np.clip(screen_x, -max_coord, max_coord))
        screen_y = int(np.clip(screen_y, -max_coord, max_coord))
        
        depth = ndc_point[2]
        
        return screen_x, screen_y, depth
    
    def safe_draw_line(self, dc, start_screen, end_screen):
        """Safely draw a line with coordinate validation."""
        # Check if coordinates are valid and in front of camera
        if (start_screen[2] > 0 and end_screen[2] > 0 and
            abs(start_screen[0]) < 32767 and abs(start_screen[1]) < 32767 and
            abs(end_screen[0]) < 32767 and abs(end_screen[1]) < 32767):
            try:
                dc.DrawLine(start_screen[0], start_screen[1], 
                           end_screen[0], end_screen[1])
            except (OverflowError, ValueError) as e:
                # Silently skip lines that cause drawing errors
                pass
    
    def draw_grid(self, dc):
        """Draw a 3D grid with separate colors for X and Z parallel lines."""

        if not self.show_grid:
            return
        
        # Draw grid in XZ plane
        for i in range(-self.grid_size, self.grid_size + 1):
            pos = i * self.grid_spacing
            
            # Lines parallel to X axis (running along Z direction) - use Z color
            dc.SetPen(wx.Pen(wx.Colour(*self.grid_color_z), 1))
            start_point = np.array([pos, 0, -self.grid_size * self.grid_spacing])
            end_point = np.array([pos, 0, self.grid_size * self.grid_spacing])
            
            if (self.camera.point_in_view_limits(start_point) or 
                self.camera.point_in_view_limits(end_point)):
                start_screen = self.project_point(start_point)
                end_screen = self.project_point(end_point)
                self.safe_draw_line(dc, start_screen, end_screen)
            
            # Lines parallel to Z axis (running along X direction) - use X color
            dc.SetPen(wx.Pen(wx.Colour(*self.grid_color_x), 1))
            start_point = np.array([-self.grid_size * self.grid_spacing, 0, pos])
            end_point = np.array([self.grid_size * self.grid_spacing, 0, pos])
            
            if (self.camera.point_in_view_limits(start_point) or 
                self.camera.point_in_view_limits(end_point)):
                start_screen = self.project_point(start_point)
                end_screen = self.project_point(end_point)
                self.safe_draw_line(dc, start_screen, end_screen)
    
    def draw_axes(self, dc):
        """Draw coordinate axes."""

        if not self.show_axes:
            return
        
        origin = np.array([0, 0, 0])
        x_axis = np.array([3, 0, 0])
        y_axis = np.array([0, 3, 0])
        z_axis = np.array([0, 0, 3])
        
        # Check view limits
        if not (self.camera.point_in_view_limits(origin) or
                self.camera.point_in_view_limits(x_axis) or
                self.camera.point_in_view_limits(y_axis) or
                self.camera.point_in_view_limits(z_axis)):
            return
        
        origin_screen = self.project_point(origin)
        
        # X axis (red)
        dc.SetPen(wx.Pen(wx.Colour(255, 0, 0), 3))
        x_screen = self.project_point(x_axis)
        self.safe_draw_line(dc, origin_screen, x_screen)
        
        # Y axis (green)
        dc.SetPen(wx.Pen(wx.Colour(0, 255, 0), 3))
        y_screen = self.project_point(y_axis)
        self.safe_draw_line(dc, origin_screen, y_screen)
        
        # Z axis (blue)
        dc.SetPen(wx.Pen(wx.Colour(0, 0, 255), 3))
        z_screen = self.project_point(z_axis)
        self.safe_draw_line(dc, origin_screen, z_screen)
    
    def draw_objects(self, dc):
        """Draw all 3D objects."""

        for obj in self.objects:
            if obj['type'] == 'wireframe':
                self.draw_wireframe_object(dc, obj)
            elif obj['type'] == 'line':
                self.draw_line_object(dc, obj)
    
    def draw_wireframe_object(self, dc, obj):
        """Draw a wireframe object."""

        dc.SetPen(wx.Pen(wx.Colour(*obj['color']), 1))
        
        vertices = obj['vertices'] + obj['position']
        
        for edge in obj['edges']:
            start_vertex = vertices[edge[0]]
            end_vertex = vertices[edge[1]]
            
            # Check view limits
            if (self.camera.point_in_view_limits(start_vertex) or
                self.camera.point_in_view_limits(end_vertex)):
                
                start_screen = self.project_point(start_vertex)
                end_screen = self.project_point(end_vertex)
                self.safe_draw_line(dc, start_screen, end_screen)
    
    def draw_line_object(self, dc, obj):
        """Draw a line object."""

        dc.SetPen(wx.Pen(wx.Colour(*obj['color']), 2))
        
        vertices = obj['vertices'] + obj['position']
        
        for edge in obj['edges']:
            start_vertex = vertices[edge[0]]
            end_vertex = vertices[edge[1]]
            
            # Check view limits
            if (self.camera.point_in_view_limits(start_vertex) or
                self.camera.point_in_view_limits(end_vertex)):
                
                start_screen = self.project_point(start_vertex)
                end_screen = self.project_point(end_vertex)
                self.safe_draw_line(dc, start_screen, end_screen)
    
    def draw_info(self, dc):
        """Draw camera and world information."""

        dc.SetTextForeground(wx.Colour(255, 255, 255))
        dc.SetFont(wx.Font(10, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        
        # Calculate vanish point for display
        vanish_point = self.get_vanish_point_screen_coords()
        vanish_text = f"({vanish_point[0]:.0f}, {vanish_point[1]:.0f})" if vanish_point else "N/A (Orthographic)"
        
        info_lines = [
            f"Control Mode: {self.control_mode.upper()}",
            f"Camera Pos: ({self.camera.position[0]:.1f}, {self.camera.position[1]:.1f}, {self.camera.position[2]:.1f})",
            f"Camera Rot: ({self.camera.rotation[0]:.1f}°, {self.camera.rotation[1]:.1f}°, {self.camera.rotation[2]:.1f}°)",
            f"World Pos: ({self.world_position[0]:.1f}, {self.world_position[1]:.1f}, {self.world_position[2]:.1f})",
            f"World Rot: ({self.world_rotation[0]:.1f}°, {self.world_rotation[1]:.1f}°, {self.world_rotation[2]:.1f}°)",
            "",
            "Camera Settings:",
            f"Projection: {self.camera.projection_mode.value}",
            f"FOV: {self.camera.fov:.1f}° | Ortho Size: {self.camera.ortho_size:.1f}",
            f"Near: {self.camera.near_plane:.2f} | Far: {self.camera.far_plane:.1f}",
            f"View Limits: {'ON' if self.camera.use_view_limits else 'OFF'}",
            f"Limit XYZ: ({self.camera.view_limits['x_max']:.1f}, {self.camera.view_limits['y_max']:.1f}, {self.camera.view_limits['z_max']:.1f})",
            f"Vanish Point: {vanish_text}",
            f"Grid Colors: X{self.grid_color_x} Y{self.grid_color_y} Z{self.grid_color_z}",
            "",
            "Movement Settings:",
            f"Mouse X Invert: {'ON' if self.invert_mouse_x else 'OFF'}",
            f"Mouse Y Invert: {'ON' if self.invert_mouse_y else 'OFF'}",
            f"Movement Invert: {'ON' if self.invert_movement else 'OFF'}",
            f"Rotation Speed: {self.mouse_rotation_speed:.1f}x",
            f"Pan Speed: {self.mouse_pan_speed:.1f}x",
            f"Move Speed: {self.keyboard_move_speed:.1f}x",
            f"Zoom Speed: {self.zoom_speed:.1f}x",
            "",
            "Controls:",
            "WASD: Move camera/world",
            "Mouse: Look around",
            "Scroll: Zoom",
            "TAB: Toggle camera/world mode",
            "P: Toggle projection mode",
            "L: Toggle view limits",
            "G: Toggle grid",
            "A: Toggle axes"
        ]
        
        y_pos = 10
        for line in info_lines:
            dc.DrawText(line, 10, y_pos)
            y_pos += 15
    
    def on_paint(self, event):
        """Handle paint events."""

        dc = wx.PaintDC(self)
        self.draw(dc)
    
    def draw(self, dc):
        """Main drawing function."""

        # Clear background
        dc.SetBackground(wx.Brush(wx.Colour(*self.background_color)))
        dc.Clear()
        
        # Draw 3D elements
        self.draw_grid(dc)
        self.draw_axes(dc)
        self.draw_objects(dc)
        
        # Draw UI info
        self.draw_info(dc)
    
    def on_size(self, event):
        """Handle resize events."""

        self.Refresh()
        event.Skip()
    
    def on_left_down(self, event):
        """Handle left mouse button down."""

        self.left_mouse_down = True
        self.last_mouse_pos = event.GetPosition()
        self.CaptureMouse()
        self.SetFocus()
        event.Skip()
    
    def on_left_up(self, event):
        """Handle left mouse button up."""

        self.left_mouse_down = False
        if self.HasCapture():
            self.ReleaseMouse()
        event.Skip()
    
    def on_right_down(self, event):
        """Handle right mouse button down."""

        self.right_mouse_down = True
        self.last_mouse_pos = event.GetPosition()
        self.CaptureMouse()
        self.SetFocus()
        event.Skip()
    
    def on_right_up(self, event):
        """Handle right mouse button up."""

        self.right_mouse_down = False
        if self.HasCapture():
            self.ReleaseMouse()
        event.Skip()
    
    def on_middle_down(self, event):
        """Handle middle mouse button down."""

        self.middle_mouse_down = True
        self.last_mouse_pos = event.GetPosition()
        self.CaptureMouse()
        self.SetFocus()
        event.Skip()
    
    def on_middle_up(self, event):
        """Handle middle mouse button up."""

        self.middle_mouse_down = False
        if self.HasCapture():
            self.ReleaseMouse()
        event.Skip()
    
    def on_motion(self, event):
        """Handle mouse motion."""

        current_pos = event.GetPosition()
        
        if self.left_mouse_down or self.right_mouse_down:
            dx = current_pos.x - self.last_mouse_pos.x
            dy = current_pos.y - self.last_mouse_pos.y
            
            # Apply mouse inversion settings
            if self.invert_mouse_x:
                dx = -dx
            if self.invert_mouse_y:
                dy = -dy
            
            if self.control_mode == "camera":
                # Rotate camera with speed setting
                self.camera.rotate_yaw(-dx * self.mouse_sensitivity * self.mouse_rotation_speed * 0.5)
                self.camera.rotate_pitch(-dy * self.mouse_sensitivity * self.mouse_rotation_speed * 0.5)
            else:
                # Rotate world with speed setting
                self.world_rotation[1] += dx * self.mouse_sensitivity * self.mouse_rotation_speed
                self.world_rotation[0] += dy * self.mouse_sensitivity * self.mouse_rotation_speed
            
            self.Refresh()
        
        elif self.middle_mouse_down:
            dx = current_pos.x - self.last_mouse_pos.x
            dy = current_pos.y - self.last_mouse_pos.y
            
            # Apply mouse inversion for panning
            if self.invert_mouse_x:
                dx = -dx
            if self.invert_mouse_y:
                dy = -dy
            
            if self.control_mode == "camera":
                # Pan camera with speed setting
                self.camera.move_right(dx * self.mouse_sensitivity * self.mouse_pan_speed * 0.01)
                self.camera.move_up(-dy * self.mouse_sensitivity * self.mouse_pan_speed * 0.01)
            else:
                # Pan world with speed setting
                self.world_position[0] += dx * self.mouse_sensitivity * self.mouse_pan_speed * 0.01
                self.world_position[1] -= dy * self.mouse_sensitivity * self.mouse_pan_speed * 0.01
            
            self.Refresh()
        
        self.last_mouse_pos = current_pos
        self.mouse_pos = current_pos
        event.Skip()
    
    def on_mousewheel(self, event):
        """Handle mouse wheel events."""

        rotation = event.GetWheelRotation()
        
        if self.control_mode == "camera":
            # Zoom camera with speed setting
            self.camera.zoom(rotation / 1200.0 * self.zoom_speed)
        else:
            # Scale world with speed setting
            scale_factor = 1.0 + (rotation / 1200.0 * self.zoom_speed)
            self.world_scale *= scale_factor
            self.world_scale = np.clip(self.world_scale, 0.1, 10.0)
        
        self.Refresh()
        event.Skip()
    
    def on_key_down(self, event):
        """Handle key press events."""

        key_code = event.GetKeyCode()
        
        # Movement keys with speed and inversion settings
        move_amount = self.key_sensitivity * self.keyboard_move_speed
        invert_multiplier = -1 if self.invert_movement else 1
        
        if key_code == ord('W'):
            if self.control_mode == "camera":
                self.camera.move_forward(move_amount * invert_multiplier)
            else:
                self.world_position[2] -= move_amount * invert_multiplier
        elif key_code == ord('S'):
            if self.control_mode == "camera":
                self.camera.move_forward(-move_amount * invert_multiplier)
            else:
                self.world_position[2] += move_amount * invert_multiplier
        elif key_code == ord('A'):
            if self.control_mode == "camera":
                self.camera.move_right(-move_amount * invert_multiplier)
            else:
                self.world_position[0] -= move_amount * invert_multiplier
        elif key_code == ord('D'):
            if self.control_mode == "camera":
                self.camera.move_right(move_amount * invert_multiplier)
            else:
                self.world_position[0] += move_amount * invert_multiplier
        elif key_code == ord('Q'):
            if self.control_mode == "camera":
                self.camera.move_up(move_amount * invert_multiplier)
            else:
                self.world_position[1] += move_amount * invert_multiplier
        elif key_code == ord('E'):
            if self.control_mode == "camera":
                self.camera.move_up(-move_amount * invert_multiplier)
            else:
                self.world_position[1] -= move_amount * invert_multiplier
        
        # Toggle keys
        elif key_code == wx.WXK_TAB:
            self.control_mode = "world" if self.control_mode == "camera" else "camera"
            print(f"DEBUG: Switched to {self.control_mode} control mode")
        elif key_code == ord('P'):
            self.camera.projection_mode = (ProjectionMode.ORTHOGRAPHIC 
                                         if self.camera.projection_mode == ProjectionMode.PERSPECTIVE 
                                         else ProjectionMode.PERSPECTIVE)
            print(f"DEBUG: Switched to {self.camera.projection_mode.value} projection")
        elif key_code == ord('L'):
            self.camera.use_view_limits = not self.camera.use_view_limits
            print(f"DEBUG: View limits {'enabled' if self.camera.use_view_limits else 'disabled'}")
        elif key_code == ord('G'):
            self.show_grid = not self.show_grid
            print(f"DEBUG: Grid {'enabled' if self.show_grid else 'disabled'}")
        elif key_code == wx.WXK_F1:  # Changed from 'A' to F1 to avoid conflict
            self.show_axes = not self.show_axes
            print(f"DEBUG: Axes {'enabled' if self.show_axes else 'disabled'}")
        
        self.Refresh()
        event.Skip()
    
    def on_key_up(self, event):
        """Handle key release events."""

        event.Skip()
    
    def reset_camera(self):
        """Reset camera to default position."""

        self.camera.position = np.array([0.0, 0.0, 5.0])
        self.camera.rotation = np.array([0.0, 0.0, 0.0])
        self.camera.fov = 60.0
        self.camera.ortho_size = 10.0
        self.Refresh()
        print("DEBUG: Camera reset to default position")
    
    def reset_world(self):
        """Reset world transformation to default."""

        self.world_position = np.array([0.0, 0.0, 0.0])
        self.world_rotation = np.array([0.0, 0.0, 0.0])
        self.world_scale = np.array([1.0, 1.0, 1.0])
        self.Refresh()
        print("DEBUG: World transformation reset to default")
    
    def set_view_limits(self, x_range: Tuple[float, float], 
                       y_range: Tuple[float, float], 
                       z_range: Tuple[float, float]):
        """Set view limits for culling."""

        self.camera.view_limits.update({
            'x_min': x_range[0], 'x_max': x_range[1],
            'y_min': y_range[0], 'y_max': y_range[1],
            'z_min': z_range[0], 'z_max': z_range[1]
        })
        self.camera.use_view_limits = True
        self.Refresh()
        print(f"DEBUG: View limits set to X:{x_range}, Y:{y_range}, Z:{z_range}")
    
    def set_grid_color_x(self, color: Tuple[int, int, int]):
        """Set the color for X-direction grid lines."""
        self.grid_color_x = color
        self.Refresh()
        print(f"DEBUG: X grid color set to {color}")
    
    def set_grid_color_y(self, color: Tuple[int, int, int]):
        """Set the color for Y-direction grid lines."""
        self.grid_color_y = color
        self.Refresh()
        print(f"DEBUG: Y grid color set to {color}")
    
    def set_grid_color_z(self, color: Tuple[int, int, int]):
        """Set the color for Z-direction grid lines."""
        self.grid_color_z = color
        self.Refresh()
        print(f"DEBUG: Z grid color set to {color}")
    
    def get_grid_colors(self) -> Tuple[Tuple[int, int, int], Tuple[int, int, int], Tuple[int, int, int]]:
        """Get current grid colors for X, Y, Z axes."""
        return self.grid_color_x, self.grid_color_y, self.grid_color_z
    
    # Movement behavior configuration methods
    def toggle_mouse_x_invert(self):
        """Toggle X-axis mouse inversion."""
        self.invert_mouse_x = not self.invert_mouse_x
        print(f"DEBUG: Mouse X invert: {self.invert_mouse_x}")
    
    def toggle_mouse_y_invert(self):
        """Toggle Y-axis mouse inversion."""
        self.invert_mouse_y = not self.invert_mouse_y
        print(f"DEBUG: Mouse Y invert: {self.invert_mouse_y}")
    
    def toggle_movement_invert(self):
        """Toggle keyboard movement inversion."""
        self.invert_movement = not self.invert_movement
        print(f"DEBUG: Movement invert: {self.invert_movement}")
    
    def toggle_smooth_movement(self):
        """Toggle smooth movement (placeholder for future implementation)."""
        self.smooth_movement = not self.smooth_movement
        print(f"DEBUG: Smooth movement: {self.smooth_movement}")
    
    def set_mouse_rotation_speed(self, speed: float):
        """Set mouse rotation speed multiplier."""
        self.mouse_rotation_speed = max(0.1, min(10.0, speed))
        print(f"DEBUG: Mouse rotation speed set to {self.mouse_rotation_speed}")
    
    def set_mouse_pan_speed(self, speed: float):
        """Set mouse pan speed multiplier."""
        self.mouse_pan_speed = max(0.1, min(10.0, speed))
        print(f"DEBUG: Mouse pan speed set to {self.mouse_pan_speed}")
    
    def set_keyboard_move_speed(self, speed: float):
        """Set keyboard movement speed multiplier."""
        self.keyboard_move_speed = max(0.1, min(10.0, speed))
        print(f"DEBUG: Keyboard move speed set to {self.keyboard_move_speed}")
    
    def set_zoom_speed(self, speed: float):
        """Set zoom speed multiplier."""
        self.zoom_speed = max(0.1, min(10.0, speed))
        print(f"DEBUG: Zoom speed set to {self.zoom_speed}")
    
    def get_movement_settings(self):
        """Get current movement behavior settings."""
        return {
            'invert_mouse_x': self.invert_mouse_x,
            'invert_mouse_y': self.invert_mouse_y,
            'invert_movement': self.invert_movement,
            'smooth_movement': self.smooth_movement,
            'mouse_rotation_speed': self.mouse_rotation_speed,
            'mouse_pan_speed': self.mouse_pan_speed,
            'keyboard_move_speed': self.keyboard_move_speed,
            'zoom_speed': self.zoom_speed
        }
    
    # Camera configuration methods
    def set_field_of_view(self, fov_degrees: float):
        """Set camera field of view (perspective mode)."""
        self.camera.fov = max(10.0, min(170.0, fov_degrees))
        self.Refresh()
        print(f"DEBUG: FOV set to {self.camera.fov:.1f}°")
    
    def set_orthographic_size(self, size: float):
        """Set orthographic view size."""
        self.camera.ortho_size = max(0.1, min(100.0, size))
        self.Refresh()
        print(f"DEBUG: Orthographic size set to {self.camera.ortho_size:.1f}")
    
    def set_near_plane(self, near: float):
        """Set camera near clipping plane."""
        # Ensure near is positive and less than far
        near = max(0.01, min(self.camera.far_plane - 0.1, near))
        self.camera.near_plane = near
        self.Refresh()
        print(f"DEBUG: Near plane set to {self.camera.near_plane:.2f}")
    
    def set_far_plane(self, far: float):
        """Set camera far clipping plane."""
        # Ensure far is greater than near
        far = max(self.camera.near_plane + 0.1, min(10000.0, far))
        self.camera.far_plane = far
        self.Refresh()
        print(f"DEBUG: Far plane set to {self.camera.far_plane:.1f}")
    
    def set_camera_position(self, x: float, y: float, z: float):
        """Set camera position directly."""
        self.camera.position = np.array([x, y, z])
        self.Refresh()
        print(f"DEBUG: Camera position set to ({x:.1f}, {y:.1f}, {z:.1f})")
    
    def set_camera_rotation(self, pitch: float, yaw: float, roll: float):
        """Set camera rotation directly (in degrees)."""
        self.camera.rotation[0] = pitch
        self.camera.rotation[1] = yaw
        self.camera.rotation[2] = roll
        self.camera.update_vectors()  # Update camera vectors after rotation change
        self.Refresh()
        print(f"DEBUG: Camera rotation set to ({pitch:.1f}°, {yaw:.1f}°, {roll:.1f}°)")
    
    def toggle_view_limits(self):
        """Toggle view distance limits."""
        self.camera.use_view_limits = not self.camera.use_view_limits
        self.Refresh()
        print(f"DEBUG: View limits: {'ON' if self.camera.use_view_limits else 'OFF'}")
    
    def set_view_limits(self, x_limit: float, y_limit: float, z_limit: float):
        """Set view distance limits."""
        x_limit = max(1.0, x_limit)
        y_limit = max(1.0, y_limit)
        z_limit = max(1.0, z_limit)
        
        self.camera.view_limits['x_min'] = -x_limit
        self.camera.view_limits['x_max'] = x_limit
        self.camera.view_limits['y_min'] = -y_limit
        self.camera.view_limits['y_max'] = y_limit
        self.camera.view_limits['z_min'] = -z_limit
        self.camera.view_limits['z_max'] = z_limit
        
        self.Refresh()
        print(f"DEBUG: View limits set to ({x_limit:.1f}, {y_limit:.1f}, {z_limit:.1f})")
    
    def toggle_projection_mode(self):
        """Toggle between perspective and orthographic projection."""
        if self.camera.projection_mode == ProjectionMode.PERSPECTIVE:
            self.camera.projection_mode = ProjectionMode.ORTHOGRAPHIC
        else:
            self.camera.projection_mode = ProjectionMode.PERSPECTIVE
        self.Refresh()
        print(f"DEBUG: Projection mode: {self.camera.projection_mode.value}")
    
    def get_camera_settings(self):
        """Get current camera settings."""
        return {
            'position': self.camera.position.copy(),
            'pitch': self.camera.rotation[0],
            'yaw': self.camera.rotation[1],
            'roll': self.camera.rotation[2],
            'fov': self.camera.fov,
            'ortho_size': self.camera.ortho_size,
            'near_plane': self.camera.near_plane,
            'far_plane': self.camera.far_plane,
            'projection_mode': self.camera.projection_mode.value,
            'use_view_limits': self.camera.use_view_limits,
            'view_limit_x': self.camera.view_limits['x_max'],
            'view_limit_y': self.camera.view_limits['y_max'],
            'view_limit_z': self.camera.view_limits['z_max']
        }
    
    def get_vanish_point_screen_coords(self):
        """Calculate vanish point in screen coordinates for perspective projection."""
        if self.camera.projection_mode != ProjectionMode.PERSPECTIVE:
            return None
        
        # The vanish point is where parallel lines converge
        # In perspective projection, this is typically the screen center
        # but can be offset based on camera orientation
        
        size = self.GetSize()
        screen_center_x = size.width / 2.0
        screen_center_y = size.height / 2.0
        
        # For a centered perspective projection, vanish point is at screen center
        # This could be enhanced to calculate actual vanish point based on camera direction
        return (screen_center_x, screen_center_y)


# Test application
class Test3DFrame(wx.Frame):
    """Test frame with 3D canvas and menubar."""
    
    def __init__(self):
        super().__init__(None, title="3D Canvas Test with Grid Colors", size=(1024, 768))
        
        # Create 3D canvas
        self.canvas = Canvas3D(self)
        
        # Set some visible grid colors
        self.canvas.set_grid_color_x((255, 100, 100))  # Red-ish
        self.canvas.set_grid_color_z((100, 100, 255))  # Blue-ish
        
        # Create layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Add instructions
        instructions = wx.StaticText(self, label="🔍 Look at TOP OF SCREEN for menubar (macOS) | Use View menu for grid colors")
        instructions.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(instructions, 0, wx.EXPAND | wx.ALL, 5)
        
        sizer.Add(self.canvas, 1, wx.EXPAND)
        self.SetSizer(sizer)
        
        # Create menubar
        self.create_menubar()
        
        # Center
        self.Center()
    
    def create_menubar(self):
        """Create menubar with grid color options."""
        menubar = wx.MenuBar()
        
        # File menu
        file_menu = wx.Menu()
        file_menu.Append(wx.ID_NEW, "&New\tCmd+N", "Reset view")
        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_EXIT, "&Quit\tCmd+Q", "Quit")
        
        # View menu
        view_menu = wx.Menu()
        
        # Grid colors
        self.ID_X_GRID = wx.NewIdRef()
        self.ID_Y_GRID = wx.NewIdRef()
        self.ID_Z_GRID = wx.NewIdRef()
        self.ID_TOGGLE_GRID = wx.NewIdRef()
        self.ID_TOGGLE_AXES = wx.NewIdRef()
        
        view_menu.Append(self.ID_X_GRID, "🔴 X Grid Color...", "Change X grid color")
        view_menu.Append(self.ID_Y_GRID, "🟡 Y Grid Color...", "Change Y grid color")
        view_menu.Append(self.ID_Z_GRID, "🔵 Z Grid Color...", "Change Z grid color")
        view_menu.AppendSeparator()
        view_menu.Append(self.ID_TOGGLE_GRID, "Toggle Grid\tG", "Toggle grid visibility")
        view_menu.Append(self.ID_TOGGLE_AXES, "Toggle Axes\tA", "Toggle axes visibility")
        
        # Controls menu
        controls_menu = wx.Menu()
        
        # Movement behavior toggles
        self.ID_INVERT_MOUSE_X = wx.NewIdRef()
        self.ID_INVERT_MOUSE_Y = wx.NewIdRef()
        self.ID_INVERT_MOVEMENT = wx.NewIdRef()
        self.ID_SMOOTH_MOVEMENT = wx.NewIdRef()
        
        controls_menu.Append(self.ID_INVERT_MOUSE_X, "Invert Mouse X", "Invert horizontal mouse movement")
        controls_menu.Append(self.ID_INVERT_MOUSE_Y, "Invert Mouse Y", "Invert vertical mouse movement")
        controls_menu.Append(self.ID_INVERT_MOVEMENT, "Invert Keyboard Movement", "Invert WASD movement")
        controls_menu.Append(self.ID_SMOOTH_MOVEMENT, "Smooth Movement", "Enable smooth movement")
        
        controls_menu.AppendSeparator()
        
        # Speed settings
        self.ID_ROTATION_SPEED = wx.NewIdRef()
        self.ID_PAN_SPEED = wx.NewIdRef()
        self.ID_MOVE_SPEED = wx.NewIdRef()
        self.ID_ZOOM_SPEED = wx.NewIdRef()
        
        controls_menu.Append(self.ID_ROTATION_SPEED, "Mouse Rotation Speed...", "Set mouse rotation speed")
        controls_menu.Append(self.ID_PAN_SPEED, "Mouse Pan Speed...", "Set mouse pan speed")
        controls_menu.Append(self.ID_MOVE_SPEED, "Keyboard Move Speed...", "Set keyboard movement speed")
        controls_menu.Append(self.ID_ZOOM_SPEED, "Zoom Speed...", "Set zoom speed")
        
        # Camera menu
        camera_menu = wx.Menu()
        
        # Projection settings
        self.ID_TOGGLE_PROJECTION = wx.NewIdRef()
        self.ID_SET_FOV = wx.NewIdRef()
        self.ID_SET_ORTHO_SIZE = wx.NewIdRef()
        
        camera_menu.Append(self.ID_TOGGLE_PROJECTION, "Toggle Projection\tP", "Switch perspective/orthographic")
        camera_menu.AppendSeparator()
        camera_menu.Append(self.ID_SET_FOV, "Field of View...", "Set perspective FOV (10°-170°)")
        camera_menu.Append(self.ID_SET_ORTHO_SIZE, "Orthographic Size...", "Set orthographic view size")
        
        camera_menu.AppendSeparator()
        
        # Clipping planes
        self.ID_SET_NEAR_PLANE = wx.NewIdRef()
        self.ID_SET_FAR_PLANE = wx.NewIdRef()
        
        camera_menu.Append(self.ID_SET_NEAR_PLANE, "Near Clipping Plane...", "Set near clipping distance")
        camera_menu.Append(self.ID_SET_FAR_PLANE, "Far Clipping Plane...", "Set far clipping distance")
        
        camera_menu.AppendSeparator()
        
        # View limits
        self.ID_TOGGLE_VIEW_LIMITS = wx.NewIdRef()
        self.ID_SET_VIEW_LIMITS = wx.NewIdRef()
        
        camera_menu.Append(self.ID_TOGGLE_VIEW_LIMITS, "Toggle View Limits\tL", "Enable/disable view distance limits")
        camera_menu.Append(self.ID_SET_VIEW_LIMITS, "Set View Limits...", "Configure view distance limits")
        
        camera_menu.AppendSeparator()
        
        # Camera position and rotation
        self.ID_SET_CAMERA_POS = wx.NewIdRef()
        self.ID_SET_CAMERA_ROT = wx.NewIdRef()
        self.ID_RESET_CAMERA = wx.NewIdRef()
        
        camera_menu.Append(self.ID_SET_CAMERA_POS, "Set Camera Position...", "Set camera position directly")
        camera_menu.Append(self.ID_SET_CAMERA_ROT, "Set Camera Rotation...", "Set camera rotation directly")
        camera_menu.AppendSeparator()
        camera_menu.Append(self.ID_RESET_CAMERA, "Reset Camera\tR", "Reset camera to default position")
        
        # Vanish point info
        camera_menu.AppendSeparator()
        self.ID_SHOW_VANISH_POINT = wx.NewIdRef()
        camera_menu.Append(self.ID_SHOW_VANISH_POINT, "Show Vanish Point Info", "Display vanish point information")
        
        # Help menu
        help_menu = wx.Menu()
        help_menu.Append(wx.ID_ABOUT, "&About", "About")
        
        # Add to menubar
        menubar.Append(file_menu, "&File")
        menubar.Append(view_menu, "&View")
        menubar.Append(controls_menu, "&Controls")
        menubar.Append(camera_menu, "&Camera")
        menubar.Append(help_menu, "&Help")
        
        # Set menubar
        self.SetMenuBar(menubar)
        
        # Bind events
        self.Bind(wx.EVT_MENU, self.on_quit, id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.on_new, id=wx.ID_NEW)
        self.Bind(wx.EVT_MENU, self.on_about, id=wx.ID_ABOUT)
        
        # View menu events
        self.Bind(wx.EVT_MENU, self.on_x_grid, id=self.ID_X_GRID)
        self.Bind(wx.EVT_MENU, self.on_y_grid, id=self.ID_Y_GRID)
        self.Bind(wx.EVT_MENU, self.on_z_grid, id=self.ID_Z_GRID)
        self.Bind(wx.EVT_MENU, self.on_toggle_grid, id=self.ID_TOGGLE_GRID)
        self.Bind(wx.EVT_MENU, self.on_toggle_axes, id=self.ID_TOGGLE_AXES)
        
        # Controls menu events
        self.Bind(wx.EVT_MENU, self.on_invert_mouse_x, id=self.ID_INVERT_MOUSE_X)
        self.Bind(wx.EVT_MENU, self.on_invert_mouse_y, id=self.ID_INVERT_MOUSE_Y)
        self.Bind(wx.EVT_MENU, self.on_invert_movement, id=self.ID_INVERT_MOVEMENT)
        self.Bind(wx.EVT_MENU, self.on_smooth_movement, id=self.ID_SMOOTH_MOVEMENT)
        self.Bind(wx.EVT_MENU, self.on_rotation_speed, id=self.ID_ROTATION_SPEED)
        self.Bind(wx.EVT_MENU, self.on_pan_speed, id=self.ID_PAN_SPEED)
        self.Bind(wx.EVT_MENU, self.on_move_speed, id=self.ID_MOVE_SPEED)
        self.Bind(wx.EVT_MENU, self.on_zoom_speed, id=self.ID_ZOOM_SPEED)
        
        # Camera menu events
        self.Bind(wx.EVT_MENU, self.on_toggle_projection, id=self.ID_TOGGLE_PROJECTION)
        self.Bind(wx.EVT_MENU, self.on_set_fov, id=self.ID_SET_FOV)
        self.Bind(wx.EVT_MENU, self.on_set_ortho_size, id=self.ID_SET_ORTHO_SIZE)
        self.Bind(wx.EVT_MENU, self.on_set_near_plane, id=self.ID_SET_NEAR_PLANE)
        self.Bind(wx.EVT_MENU, self.on_set_far_plane, id=self.ID_SET_FAR_PLANE)
        self.Bind(wx.EVT_MENU, self.on_toggle_view_limits, id=self.ID_TOGGLE_VIEW_LIMITS)
        self.Bind(wx.EVT_MENU, self.on_set_view_limits, id=self.ID_SET_VIEW_LIMITS)
        self.Bind(wx.EVT_MENU, self.on_set_camera_pos, id=self.ID_SET_CAMERA_POS)
        self.Bind(wx.EVT_MENU, self.on_set_camera_rot, id=self.ID_SET_CAMERA_ROT)
        self.Bind(wx.EVT_MENU, self.on_reset_camera, id=self.ID_RESET_CAMERA)
        self.Bind(wx.EVT_MENU, self.on_show_vanish_point, id=self.ID_SHOW_VANISH_POINT)
    
    def on_quit(self, event):
        self.Close()
    
    def on_new(self, event):
        self.canvas.reset_camera()
        self.canvas.reset_world()
    
    def on_about(self, event):
        wx.MessageBox("3D Canvas Test\n\nUse View menu to change grid colors!", "About", wx.OK | wx.ICON_INFORMATION)
    
    def on_x_grid(self, event):
        current_colors = self.canvas.get_grid_colors()
        data = wx.ColourData()
        data.SetColour(wx.Colour(*current_colors[0]))
        
        with wx.ColourDialog(self, data) as dialog:
            dialog.SetTitle("X Grid Color")
            if dialog.ShowModal() == wx.ID_OK:
                color = dialog.GetColourData().GetColour()
                rgb = (color.Red(), color.Green(), color.Blue())
                self.canvas.set_grid_color_x(rgb)
    
    def on_y_grid(self, event):
        wx.MessageBox("Y Grid Color (not yet implemented)", "Y Grid", wx.OK | wx.ICON_INFORMATION)
    
    def on_z_grid(self, event):
        current_colors = self.canvas.get_grid_colors()
        data = wx.ColourData()
        data.SetColour(wx.Colour(*current_colors[2]))
        
        with wx.ColourDialog(self, data) as dialog:
            dialog.SetTitle("Z Grid Color")
            if dialog.ShowModal() == wx.ID_OK:
                color = dialog.GetColourData().GetColour()
                rgb = (color.Red(), color.Green(), color.Blue())
                self.canvas.set_grid_color_z(rgb)
    
    def on_toggle_grid(self, event):
        self.canvas.show_grid = not self.canvas.show_grid
        self.canvas.Refresh()
    
    def on_toggle_axes(self, event):
        self.canvas.show_axes = not self.canvas.show_axes
        self.canvas.Refresh()
    
    # Controls menu event handlers
    def on_invert_mouse_x(self, event):
        self.canvas.toggle_mouse_x_invert()
    
    def on_invert_mouse_y(self, event):
        self.canvas.toggle_mouse_y_invert()
    
    def on_invert_movement(self, event):
        self.canvas.toggle_movement_invert()
    
    def on_smooth_movement(self, event):
        self.canvas.toggle_smooth_movement()
    
    def on_rotation_speed(self, event):
        current_speed = self.canvas.mouse_rotation_speed
        dialog = wx.NumberEntryDialog(self, 
                                    "Enter mouse rotation speed (0.1 - 10.0):",
                                    "Rotation Speed:",
                                    "Mouse Rotation Speed",
                                    current_speed, 0.1, 10.0)
        if dialog.ShowModal() == wx.ID_OK:
            new_speed = dialog.GetValue()
            self.canvas.set_mouse_rotation_speed(new_speed)
        dialog.Destroy()
    
    def on_pan_speed(self, event):
        current_speed = self.canvas.mouse_pan_speed
        dialog = wx.NumberEntryDialog(self,
                                    "Enter mouse pan speed (0.1 - 10.0):",
                                    "Pan Speed:",
                                    "Mouse Pan Speed",
                                    current_speed, 0.1, 10.0)
        if dialog.ShowModal() == wx.ID_OK:
            new_speed = dialog.GetValue()
            self.canvas.set_mouse_pan_speed(new_speed)
        dialog.Destroy()
    
    def on_move_speed(self, event):
        current_speed = self.canvas.keyboard_move_speed
        dialog = wx.NumberEntryDialog(self,
                                    "Enter keyboard movement speed (0.1 - 10.0):",
                                    "Move Speed:",
                                    "Keyboard Movement Speed",
                                    current_speed, 0.1, 10.0)
        if dialog.ShowModal() == wx.ID_OK:
            new_speed = dialog.GetValue()
            self.canvas.set_keyboard_move_speed(new_speed)
        dialog.Destroy()
    
    def on_zoom_speed(self, event):
        current_speed = self.canvas.zoom_speed
        dialog = wx.NumberEntryDialog(self,
                                    "Enter zoom speed (0.1 - 10.0):",
                                    "Zoom Speed:",
                                    "Zoom Speed",
                                    current_speed, 0.1, 10.0)
        if dialog.ShowModal() == wx.ID_OK:
            new_speed = dialog.GetValue()
            self.canvas.set_zoom_speed(new_speed)
        dialog.Destroy()
    
    # Camera menu event handlers
    def on_toggle_projection(self, event):
        self.canvas.toggle_projection_mode()
    
    def on_set_fov(self, event):
        current_fov = self.canvas.camera.fov
        dialog = wx.NumberEntryDialog(self,
                                    "Enter field of view in degrees (10° - 170°):",
                                    "FOV:",
                                    "Field of View",
                                    current_fov, 10.0, 170.0)
        if dialog.ShowModal() == wx.ID_OK:
            new_fov = dialog.GetValue()
            self.canvas.set_field_of_view(new_fov)
        dialog.Destroy()
    
    def on_set_ortho_size(self, event):
        current_size = self.canvas.camera.ortho_size
        dialog = wx.NumberEntryDialog(self,
                                    "Enter orthographic view size (0.1 - 100.0):",
                                    "Size:",
                                    "Orthographic Size",
                                    current_size, 0.1, 100.0)
        if dialog.ShowModal() == wx.ID_OK:
            new_size = dialog.GetValue()
            self.canvas.set_orthographic_size(new_size)
        dialog.Destroy()
    
    def on_set_near_plane(self, event):
        current_near = self.canvas.camera.near_plane
        max_near = self.canvas.camera.far_plane - 0.1
        dialog = wx.NumberEntryDialog(self,
                                    f"Enter near clipping plane (0.01 - {max_near:.2f}):",
                                    "Near:",
                                    "Near Clipping Plane",
                                    current_near, 0.01, max_near)
        if dialog.ShowModal() == wx.ID_OK:
            new_near = dialog.GetValue()
            self.canvas.set_near_plane(new_near)
        dialog.Destroy()
    
    def on_set_far_plane(self, event):
        current_far = self.canvas.camera.far_plane
        min_far = self.canvas.camera.near_plane + 0.1
        dialog = wx.NumberEntryDialog(self,
                                    f"Enter far clipping plane ({min_far:.2f} - 10000.0):",
                                    "Far:",
                                    "Far Clipping Plane",
                                    current_far, min_far, 10000.0)
        if dialog.ShowModal() == wx.ID_OK:
            new_far = dialog.GetValue()
            self.canvas.set_far_plane(new_far)
        dialog.Destroy()
    
    def on_toggle_view_limits(self, event):
        self.canvas.toggle_view_limits()
    
    def on_set_view_limits(self, event):
        current_limits = (self.canvas.camera.view_limits['x_max'], 
                         self.canvas.camera.view_limits['y_max'], 
                         self.canvas.camera.view_limits['z_max'])
        
        # Simple dialog for view limits
        dialog_text = f"""Current view limits: X={current_limits[0]:.1f}, Y={current_limits[1]:.1f}, Z={current_limits[2]:.1f}

Enter new X limit (1.0 - 1000.0):"""
        
        x_dialog = wx.NumberEntryDialog(self, dialog_text, "X Limit:", "View Limits X", 
                                       current_limits[0], 1.0, 1000.0)
        if x_dialog.ShowModal() == wx.ID_OK:
            x_limit = x_dialog.GetValue()
            
            y_dialog = wx.NumberEntryDialog(self, "Enter Y limit (1.0 - 1000.0):", "Y Limit:", 
                                           "View Limits Y", current_limits[1], 1.0, 1000.0)
            if y_dialog.ShowModal() == wx.ID_OK:
                y_limit = y_dialog.GetValue()
                
                z_dialog = wx.NumberEntryDialog(self, "Enter Z limit (1.0 - 1000.0):", "Z Limit:", 
                                               "View Limits Z", current_limits[2], 1.0, 1000.0)
                if z_dialog.ShowModal() == wx.ID_OK:
                    z_limit = z_dialog.GetValue()
                    self.canvas.set_view_limits(x_limit, y_limit, z_limit)
                z_dialog.Destroy()
            y_dialog.Destroy()
        x_dialog.Destroy()
    
    def on_set_camera_pos(self, event):
        current_pos = self.canvas.camera.position
        
        # Simple sequential dialogs for camera position
        x_dialog = wx.NumberEntryDialog(self, 
                                       f"Current position: ({current_pos[0]:.1f}, {current_pos[1]:.1f}, {current_pos[2]:.1f})\n\nEnter X position (-1000.0 to 1000.0):",
                                       "X Position:", "Camera Position X", 
                                       current_pos[0], -1000.0, 1000.0)
        if x_dialog.ShowModal() == wx.ID_OK:
            x = x_dialog.GetValue()
            
            y_dialog = wx.NumberEntryDialog(self, "Enter Y position (-1000.0 to 1000.0):", "Y Position:", 
                                           "Camera Position Y", current_pos[1], -1000.0, 1000.0)
            if y_dialog.ShowModal() == wx.ID_OK:
                y = y_dialog.GetValue()
                
                z_dialog = wx.NumberEntryDialog(self, "Enter Z position (-1000.0 to 1000.0):", "Z Position:", 
                                               "Camera Position Z", current_pos[2], -1000.0, 1000.0)
                if z_dialog.ShowModal() == wx.ID_OK:
                    z = z_dialog.GetValue()
                    self.canvas.set_camera_position(x, y, z)
                z_dialog.Destroy()
            y_dialog.Destroy()
        x_dialog.Destroy()
    
    def on_set_camera_rot(self, event):
        current_rot = (self.canvas.camera.rotation[0],
                      self.canvas.camera.rotation[1],
                      self.canvas.camera.rotation[2])
        
        # Simple sequential dialogs for camera rotation
        pitch_dialog = wx.NumberEntryDialog(self, 
                                           f"Current rotation: ({current_rot[0]:.1f}°, {current_rot[1]:.1f}°, {current_rot[2]:.1f}°)\n\nEnter pitch (-180° to 180°):",
                                           "Pitch:", "Camera Rotation Pitch", 
                                           current_rot[0], -180.0, 180.0)
        if pitch_dialog.ShowModal() == wx.ID_OK:
            pitch = pitch_dialog.GetValue()
            
            yaw_dialog = wx.NumberEntryDialog(self, "Enter yaw (-180° to 180°):", "Yaw:", 
                                             "Camera Rotation Yaw", current_rot[1], -180.0, 180.0)
            if yaw_dialog.ShowModal() == wx.ID_OK:
                yaw = yaw_dialog.GetValue()
                
                roll_dialog = wx.NumberEntryDialog(self, "Enter roll (-180° to 180°):", "Roll:", 
                                                  "Camera Rotation Roll", current_rot[2], -180.0, 180.0)
                if roll_dialog.ShowModal() == wx.ID_OK:
                    roll = roll_dialog.GetValue()
                    self.canvas.set_camera_rotation(pitch, yaw, roll)
                roll_dialog.Destroy()
            yaw_dialog.Destroy()
        pitch_dialog.Destroy()
    
    def on_reset_camera(self, event):
        self.canvas.reset_camera()
    
    def on_show_vanish_point(self, event):
        vanish_point = self.canvas.get_vanish_point_screen_coords()
        camera_settings = self.canvas.get_camera_settings()
        
        if vanish_point:
            info_text = f"""Vanish Point Information:

SCREEN COORDINATES:
X: {vanish_point[0]:.1f} pixels
Y: {vanish_point[1]:.1f} pixels

CAMERA SETTINGS:
Projection: {camera_settings['projection_mode']}
Field of View: {camera_settings['fov']:.1f}°
Camera Position: ({camera_settings['position'][0]:.1f}, {camera_settings['position'][1]:.1f}, {camera_settings['position'][2]:.1f})
Camera Rotation: ({camera_settings['pitch']:.1f}°, {camera_settings['yaw']:.1f}°, {camera_settings['roll']:.1f}°)

CLIPPING PLANES:
Near: {camera_settings['near_plane']:.2f}
Far: {camera_settings['far_plane']:.1f}

VIEW LIMITS:
Enabled: {camera_settings['use_view_limits']}
X/Y/Z Limits: ({camera_settings['view_limit_x']:.1f}, {camera_settings['view_limit_y']:.1f}, {camera_settings['view_limit_z']:.1f})

NOTE: The vanish point is where parallel lines appear to converge in perspective projection.
In a centered perspective view, this is typically at the screen center.
"""
        else:
            info_text = """Vanish Point Information:

ORTHOGRAPHIC PROJECTION:
No vanish point in orthographic projection.
Parallel lines remain parallel and do not converge.

Switch to perspective projection (Camera → Toggle Projection) to see vanish point behavior.

CURRENT CAMERA SETTINGS:
""" + f"""Projection: {camera_settings['projection_mode']}
Orthographic Size: {camera_settings['ortho_size']:.1f}
Camera Position: ({camera_settings['position'][0]:.1f}, {camera_settings['position'][1]:.1f}, {camera_settings['position'][2]:.1f})
"""
        
        wx.MessageDialog(self, info_text, "Vanish Point Information", wx.OK | wx.ICON_INFORMATION).ShowModal()


class Test3DApp(wx.App):
    """Test application for the 3D canvas."""
    
    def OnInit(self):
        # Set app properties for proper macOS menubar
        self.SetAppName("3D Canvas Test")
        self.SetAppDisplayName("3D Canvas with Grid Colors")
        
        frame = Test3DFrame()
        frame.Show()
        
        # Force activation for macOS menubar
        frame.Raise()
        frame.SetFocus()
        
        if wx.Platform == '__WXMAC__':
            frame.RequestUserAttention(wx.USER_ATTENTION_INFO)
        
        return True


if __name__ == "__main__":
    app = Test3DApp()
    app.MainLoop()
