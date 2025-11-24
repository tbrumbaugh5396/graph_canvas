"""
3D Sphere visualization with advanced grid systems, transformations, and visual controls.Supports longitude/latitude grids, concentric circles, dot particles, and neon-style effects.
"""
import wx
import wx.glcanvas
import math
import numpy as np
from typing import Tuple, Optional, List, Dict
from enum import Enum
import OpenGL.GL as gl
import OpenGL.GLU as glu
from PIL import Image
import time
import json
import os
import uuid
from abc import ABC, abstractmethod
import cv2  # For video playback
import threading
from pathlib import Path
import pygame  # For audio playback
import subprocess  # For FFmpeg video processing

# Global pygame mixer management to prevent conflicts
class AudioManager:
    """Manages pygame mixer globally to prevent conflicts between multiple video screens"""
    _instance = None
    _initialized = False
    _current_screen = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AudioManager, cls).__new__(cls)
        return cls._instance
    
    def initialize(self):
        """Initialize pygame mixer if not already done"""
        if not self._initialized:
            try:
                if pygame.mixer.get_init():
                    pygame.mixer.quit()
                
                pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
                pygame.mixer.init()
                self._initialized = True
                print(f"DEBUG: Global AudioManager initialized")
                return True
            except Exception as e:
                print(f"DEBUG: AudioManager initialization failed: {e}")
                return False
        return True
    
    def set_current_screen(self, screen):
        """Set the currently active audio screen"""
        if self._current_screen and self._current_screen != screen:
            # Stop previous screen's audio
            try:
                pygame.mixer.music.stop()
                print(f"DEBUG: Stopped previous screen audio")
            except:
                pass
        self._current_screen = screen
    
    def is_initialized(self):
        return self._initialized

# Global audio manager instance - initialize lazily to avoid startup conflicts
audio_manager = None

def get_audio_manager():
    """Get or create the global audio manager"""
    global audio_manager
    if audio_manager is None:
        audio_manager = AudioManager()
    return audio_manager
import io  # For BytesIO web image handling
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("WARNING: Selenium not available. Website screens will be disabled.")


class GridType(Enum):
    """Types of grid systems for the sphere."""
    LONGITUDE_LATITUDE = "longitude_latitude"
    CONCENTRIC_CIRCLES = "concentric_circles"
    DOT_PARTICLES = "dot_particles"
    NEON_LINES = "neon_lines"
    WIREFRAME = "wireframe"


class ShapeType(Enum):
    """Types of shapes that can be added to the scene."""
    # 0D shapes
    DOT = "dot"
    POINT = "point"
    
    # 1D shapes
    LINE = "line"
    CURVE = "curve"
    BSPLINE = "bspline"
    BEZIER = "bezier"
    
    # 2D shapes
    PLANE = "plane"
    CIRCLE = "circle"
    RECTANGLE = "rectangle"
    TRIANGLE = "triangle"
    SURFACE = "surface"
    
    # 3D shapes
    CUBE = "cube"
    SPHERE = "sphere"
    CYLINDER = "cylinder"
    CONE = "cone"
    PYRAMID = "pyramid"
    TORUS = "torus"


class CameraType(Enum):
    """Types of cameras available in the scene."""
    MAIN = "main"
    MAIN_CLEAN = "main_clean"  # Main camera without overlays/screens
    CUSTOM = "custom"
    SPHERE_VECTOR = "sphere_vector"


class ScreenType(Enum):
    """Types of screens that can be displayed."""
    SCREEN_2D = "screen_2d"  # Positioned in 3D space
    OVERLAY = "overlay"      # Overlayed on main view

class MediaType(Enum):
    """Types of media that can be displayed on screens."""
    IMAGE = "image"          # Static images (PNG, JPG, etc.)
    VIDEO = "video"          # Video files (MP4, AVI, etc.)
    GIF = "gif"             # Animated GIF files
    WEB = "web"             # Web pages


class Shape(ABC):
    """Base class for all shapes in the 3D scene."""
    
    def __init__(self, shape_id: str = None):
        self.id = shape_id or str(uuid.uuid4())
        self.position = np.array([0.0, 0.0, 0.0])
        self.rotation = np.array([0.0, 0.0, 0.0])  # pitch, yaw, roll
        self.scale = np.array([1.0, 1.0, 1.0])
        self.color = np.array([1.0, 1.0, 1.0, 1.0])  # RGBA
        self.visible = True
        self.name = f"{self.__class__.__name__}_{self.id[:8]}"
    
    @abstractmethod
    def render(self):
        """Render the shape using OpenGL."""
        pass
    
    def apply_transformation(self):
        """Apply position, rotation, and scale transformations."""
        gl.glPushMatrix()
        gl.glTranslatef(self.position[0], self.position[1], self.position[2])
        gl.glRotatef(self.rotation[0], 1, 0, 0)  # Pitch
        gl.glRotatef(self.rotation[1], 0, 1, 0)  # Yaw
        gl.glRotatef(self.rotation[2], 0, 0, 1)  # Roll
        gl.glScalef(self.scale[0], self.scale[1], self.scale[2])
    
    def restore_transformation(self):
        """Restore the previous transformation matrix."""
        gl.glPopMatrix()
    
    def set_position(self, x: float, y: float, z: float):
        """Set the shape's position."""
        self.position = np.array([x, y, z])
    
    def set_rotation(self, pitch: float, yaw: float, roll: float):
        """Set the shape's rotation in degrees."""
        self.rotation = np.array([pitch, yaw, roll])
    
    def set_scale(self, sx: float, sy: float, sz: float):
        """Set the shape's scale."""
        self.scale = np.array([sx, sy, sz])
    
    def set_color(self, r: float, g: float, b: float, a: float = 1.0):
        """Set the shape's color."""
        self.color = np.array([r, g, b, a])
    
    def to_dict(self):
        """Convert shape to dictionary for serialization."""
        return {
            'id': self.id,
            'type': self.__class__.__name__,
            'position': self.position.tolist(),
            'rotation': self.rotation.tolist(),
            'scale': self.scale.tolist(),
            'color': self.color.tolist(),
            'visible': self.visible,
            'name': self.name
        }
    
    def from_dict(self, data: dict):
        """Load shape from dictionary."""
        self.id = data.get('id', self.id)
        self.position = np.array(data.get('position', [0.0, 0.0, 0.0]))
        self.rotation = np.array(data.get('rotation', [0.0, 0.0, 0.0]))
        self.scale = np.array(data.get('scale', [1.0, 1.0, 1.0]))
        self.color = np.array(data.get('color', [1.0, 1.0, 1.0, 1.0]))
        self.visible = data.get('visible', True)
        self.name = data.get('name', self.name)


class Camera:
    """Represents a camera in the 3D scene."""
    
    def __init__(self, camera_id: str = None, camera_type: CameraType = CameraType.CUSTOM):
        self.id = camera_id or str(uuid.uuid4())
        self.type = camera_type
        self.position = np.array([0.0, 0.0, 5.0])
        self.target = np.array([0.0, 0.0, 0.0])
        self.up = np.array([0.0, 1.0, 0.0])
        self.fov = 60.0  # Field of view in degrees
        self.near_plane = 0.1
        self.far_plane = 100.0
        self.name = f"Camera_{self.id[:8]}"
    
    def set_position(self, x: float, y: float, z: float):
        """Set camera position."""
        self.position = np.array([x, y, z])
    
    def set_target(self, x: float, y: float, z: float):
        """Set camera target (what it's looking at)."""
        self.target = np.array([x, y, z])
    
    def set_up_vector(self, x: float, y: float, z: float):
        """Set camera up vector."""
        self.up = np.array([x, y, z])
        self.up = self.up / np.linalg.norm(self.up)  # Normalize
    
    def get_view_direction(self):
        """Get the normalized view direction vector."""
        direction = self.target - self.position
        return direction / np.linalg.norm(direction)
    
    def apply_view(self):
        """Apply this camera's view transformation."""
        glu.gluLookAt(
            self.position[0], self.position[1], self.position[2],
            self.target[0], self.target[1], self.target[2],
            self.up[0], self.up[1], self.up[2]
        )
    
    def to_dict(self):
        """Convert camera to dictionary for serialization."""
        return {
            'id': self.id,
            'type': self.type.value,
            'position': self.position.tolist(),
            'target': self.target.tolist(),
            'up': self.up.tolist(),
            'fov': self.fov,
            'near_plane': self.near_plane,
            'far_plane': self.far_plane,
            'name': self.name
        }
    
    def from_dict(self, data: dict):
        """Load camera from dictionary."""
        self.id = data.get('id', self.id)
        self.type = CameraType(data.get('type', CameraType.CUSTOM.value))
        self.position = np.array(data.get('position', [0.0, 0.0, 5.0]))
        self.target = np.array(data.get('target', [0.0, 0.0, 0.0]))
        self.up = np.array(data.get('up', [0.0, 1.0, 0.0]))
        self.fov = data.get('fov', 60.0)
        self.near_plane = data.get('near_plane', 0.1)
        self.far_plane = data.get('far_plane', 100.0)
        self.name = data.get('name', self.name)


class Screen:
    """Represents a screen that can display camera views."""
    
    def __init__(self, screen_id: str = None, screen_type: ScreenType = ScreenType.SCREEN_2D):
        self.id = screen_id or str(uuid.uuid4())
        self.type = screen_type
        self.position = np.array([0.0, 0.0, 0.0])  # Only used for 2D screens in space
        self.rotation = np.array([0.0, 0.0, 0.0])  # Only used for 2D screens in space
        self.size = np.array([2.0, 1.5])  # Width, Height
        self.camera_id = None  # ID of camera to display
        self.visible = True
        self.name = f"Screen_{self.id[:8]}"
        
        # Overlay-specific properties
        self.overlay_position = np.array([0.1, 0.1])  # Normalized screen coordinates (0-1)
        self.overlay_size = np.array([0.3, 0.3])     # Normalized size (0-1)
        
        # Rendering properties
        self.border_color = np.array([1.0, 1.0, 1.0, 1.0])
        self.border_width = 2.0
        self.background_color = np.array([0.0, 0.0, 0.0, 1.0])
        
        # Texture properties for camera view rendering
        self.texture_id = None
        self.texture_width = 256
        self.texture_height = 192
        self.framebuffer_id = None
        self.renderbuffer_id = None
        self.needs_update = True
    
    def set_position(self, x: float, y: float, z: float):
        """Set screen position (for 2D screens in space)."""
        self.position = np.array([x, y, z])
    
    def set_rotation(self, pitch: float, yaw: float, roll: float):
        """Set screen rotation (for 2D screens in space)."""
        self.rotation = np.array([pitch, yaw, roll])
    
    def set_size(self, width: float, height: float):
        """Set screen size."""
        self.size = np.array([width, height])
    
    def set_overlay_position(self, x: float, y: float):
        """Set overlay position (normalized coordinates 0-1)."""
        self.overlay_position = np.array([x, y])
    
    def set_overlay_size(self, width: float, height: float):
        """Set overlay size (normalized coordinates 0-1)."""
        self.overlay_size = np.array([width, height])
    
    def to_dict(self):
        """Convert screen to dictionary for serialization."""
        return {
            'id': self.id,
            'type': self.type.value,
            'position': self.position.tolist(),
            'rotation': self.rotation.tolist(),
            'size': self.size.tolist(),
            'camera_id': self.camera_id,
            'visible': self.visible,
            'name': self.name,
            'overlay_position': self.overlay_position.tolist(),
            'overlay_size': self.overlay_size.tolist(),
            'border_color': self.border_color.tolist(),
            'border_width': self.border_width,
            'background_color': self.background_color.tolist()
        }
    
    def from_dict(self, data: dict):
        """Load screen from dictionary."""
        self.id = data.get('id', self.id)
        self.type = ScreenType(data.get('type', ScreenType.SCREEN_2D.value))
        self.position = np.array(data.get('position', [0.0, 0.0, 0.0]))
        self.rotation = np.array(data.get('rotation', [0.0, 0.0, 0.0]))
        self.size = np.array(data.get('size', [2.0, 1.5]))
        self.camera_id = data.get('camera_id')
        self.visible = data.get('visible', True)
        self.name = data.get('name', self.name)
        self.overlay_position = np.array(data.get('overlay_position', [0.1, 0.1]))
        self.overlay_size = np.array(data.get('overlay_size', [0.3, 0.3]))
        self.border_color = np.array(data.get('border_color', [1.0, 1.0, 1.0, 1.0]))
        self.border_width = data.get('border_width', 2.0)
        self.background_color = np.array(data.get('background_color', [0.0, 0.0, 0.0, 1.0]))


# Concrete Shape Implementations

class DotShape(Shape):
    """A 0D point/dot shape."""
    
    def __init__(self, shape_id: str = None):
        super().__init__(shape_id)
        self.size = 5.0  # Point size
    
    def render(self):
        if not self.visible:
            return
        
        self.apply_transformation()
        gl.glColor4f(self.color[0], self.color[1], self.color[2], self.color[3])
        gl.glPointSize(self.size)
        
        gl.glBegin(gl.GL_POINTS)
        gl.glVertex3f(0.0, 0.0, 0.0)
        gl.glEnd()
        
        self.restore_transformation()


class LineShape(Shape):
    """A 1D line shape."""
    
    def __init__(self, shape_id: str = None):
        super().__init__(shape_id)
        self.start_point = np.array([0.0, 0.0, 0.0])
        self.end_point = np.array([1.0, 0.0, 0.0])
        self.thickness = 2.0
    
    def set_endpoints(self, start: np.ndarray, end: np.ndarray):
        """Set the line endpoints."""
        self.start_point = start.copy()
        self.end_point = end.copy()
    
    def to_dict(self):
        """Convert shape to dictionary for serialization."""
        data = super().to_dict()
        data.update({
            'start_point': self.start_point.tolist(),
            'end_point': self.end_point.tolist(),
            'thickness': self.thickness
        })
        return data
    
    def render(self):
        if not self.visible:
            return
        
        self.apply_transformation()
        gl.glColor4f(self.color[0], self.color[1], self.color[2], self.color[3])
        gl.glLineWidth(self.thickness)
        
        gl.glBegin(gl.GL_LINES)
        gl.glVertex3f(self.start_point[0], self.start_point[1], self.start_point[2])
        gl.glVertex3f(self.end_point[0], self.end_point[1], self.end_point[2])
        gl.glEnd()
        
        gl.glLineWidth(1.0)  # Reset
        self.restore_transformation()


class BezierCurve(Shape):
    """A 1D Bezier curve shape."""
    
    def __init__(self, shape_id: str = None):
        super().__init__(shape_id)
        self.control_points = [
            np.array([0.0, 0.0, 0.0]),
            np.array([0.33, 1.0, 0.0]),
            np.array([0.67, 1.0, 0.0]),
            np.array([1.0, 0.0, 0.0])
        ]
        self.resolution = 50  # Number of segments
        self.thickness = 2.0
    
    def set_control_points(self, points: List[np.ndarray]):
        """Set the Bezier control points."""
        self.control_points = [p.copy() for p in points]
    
    def to_dict(self):
        """Convert shape to dictionary for serialization."""
        data = super().to_dict()
        data.update({
            'control_points': [pt.tolist() for pt in self.control_points],
            'resolution': self.resolution,
            'thickness': self.thickness
        })
        return data
    
    def evaluate_bezier(self, t: float) -> np.ndarray:
        """Evaluate Bezier curve at parameter t (0-1)."""
        n = len(self.control_points) - 1
        result = np.zeros(3)
        
        for i, point in enumerate(self.control_points):
            # Binomial coefficient
            binom = math.factorial(n) // (math.factorial(i) * math.factorial(n - i))
            # Bernstein polynomial
            bernstein = binom * (t ** i) * ((1 - t) ** (n - i))
            result += bernstein * point
        
        return result
    
    def render(self):
        if not self.visible:
            return
        
        self.apply_transformation()
        gl.glColor4f(self.color[0], self.color[1], self.color[2], self.color[3])
        gl.glLineWidth(self.thickness)
        
        gl.glBegin(gl.GL_LINE_STRIP)
        for i in range(self.resolution + 1):
            t = i / self.resolution
            point = self.evaluate_bezier(t)
            gl.glVertex3f(point[0], point[1], point[2])
        gl.glEnd()
        
        gl.glLineWidth(1.0)  # Reset
        self.restore_transformation()


class PlaneShape(Shape):
    """A 2D plane shape."""
    
    def __init__(self, shape_id: str = None):
        super().__init__(shape_id)
        self.width = 2.0
        self.height = 2.0
        self.wireframe = False
    
    def to_dict(self):
        """Convert shape to dictionary for serialization."""
        data = super().to_dict()
        data.update({
            'width': self.width,
            'height': self.height,
            'wireframe': self.wireframe
        })
        return data
    
    def render(self):
        if not self.visible:
            return
        
        self.apply_transformation()
        gl.glColor4f(self.color[0], self.color[1], self.color[2], self.color[3])
        
        # Enable blending for transparency
        if self.color[3] < 1.0:
            gl.glEnable(gl.GL_BLEND)
            gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        
        half_w = self.width / 2.0
        half_h = self.height / 2.0
        
        if self.wireframe:
            gl.glBegin(gl.GL_LINE_LOOP)
        else:
            gl.glBegin(gl.GL_QUADS)
        
        gl.glNormal3f(0.0, 0.0, 1.0)
        gl.glVertex3f(-half_w, -half_h, 0.0)
        gl.glVertex3f(half_w, -half_h, 0.0)
        gl.glVertex3f(half_w, half_h, 0.0)
        gl.glVertex3f(-half_w, half_h, 0.0)
        gl.glEnd()
        
        if self.color[3] < 1.0:
            gl.glDisable(gl.GL_BLEND)
        
        self.restore_transformation()


class CubeShape(Shape):
    """A 3D cube shape."""
    
    def __init__(self, shape_id: str = None):
        super().__init__(shape_id)
        self.size = 1.0
        self.wireframe = False
    
    def to_dict(self):
        """Convert shape to dictionary for serialization."""
        data = super().to_dict()
        data.update({
            'size': self.size,
            'wireframe': self.wireframe
        })
        return data
    
    def render(self):
        if not self.visible:
            return
        
        self.apply_transformation()
        gl.glColor4f(self.color[0], self.color[1], self.color[2], self.color[3])
        
        # Enable blending for transparency
        if self.color[3] < 1.0:
            gl.glEnable(gl.GL_BLEND)
            gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        
        s = self.size / 2.0
        
        if self.wireframe:
            # Draw wireframe cube
            gl.glBegin(gl.GL_LINES)
            # Bottom face
            gl.glVertex3f(-s, -s, -s); gl.glVertex3f(s, -s, -s)
            gl.glVertex3f(s, -s, -s); gl.glVertex3f(s, s, -s)
            gl.glVertex3f(s, s, -s); gl.glVertex3f(-s, s, -s)
            gl.glVertex3f(-s, s, -s); gl.glVertex3f(-s, -s, -s)
            # Top face
            gl.glVertex3f(-s, -s, s); gl.glVertex3f(s, -s, s)
            gl.glVertex3f(s, -s, s); gl.glVertex3f(s, s, s)
            gl.glVertex3f(s, s, s); gl.glVertex3f(-s, s, s)
            gl.glVertex3f(-s, s, s); gl.glVertex3f(-s, -s, s)
            # Vertical edges
            gl.glVertex3f(-s, -s, -s); gl.glVertex3f(-s, -s, s)
            gl.glVertex3f(s, -s, -s); gl.glVertex3f(s, -s, s)
            gl.glVertex3f(s, s, -s); gl.glVertex3f(s, s, s)
            gl.glVertex3f(-s, s, -s); gl.glVertex3f(-s, s, s)
            gl.glEnd()
        else:
            # Draw solid cube
            gl.glBegin(gl.GL_QUADS)
            # Front face
            gl.glNormal3f(0.0, 0.0, 1.0)
            gl.glVertex3f(-s, -s, s); gl.glVertex3f(s, -s, s); gl.glVertex3f(s, s, s); gl.glVertex3f(-s, s, s)
            # Back face
            gl.glNormal3f(0.0, 0.0, -1.0)
            gl.glVertex3f(-s, -s, -s); gl.glVertex3f(-s, s, -s); gl.glVertex3f(s, s, -s); gl.glVertex3f(s, -s, -s)
            # Top face
            gl.glNormal3f(0.0, 1.0, 0.0)
            gl.glVertex3f(-s, s, -s); gl.glVertex3f(-s, s, s); gl.glVertex3f(s, s, s); gl.glVertex3f(s, s, -s)
            # Bottom face
            gl.glNormal3f(0.0, -1.0, 0.0)
            gl.glVertex3f(-s, -s, -s); gl.glVertex3f(s, -s, -s); gl.glVertex3f(s, -s, s); gl.glVertex3f(-s, -s, s)
            # Right face
            gl.glNormal3f(1.0, 0.0, 0.0)
            gl.glVertex3f(s, -s, -s); gl.glVertex3f(s, s, -s); gl.glVertex3f(s, s, s); gl.glVertex3f(s, -s, s)
            # Left face
            gl.glNormal3f(-1.0, 0.0, 0.0)
            gl.glVertex3f(-s, -s, -s); gl.glVertex3f(-s, -s, s); gl.glVertex3f(-s, s, s); gl.glVertex3f(-s, s, -s)
            gl.glEnd()
        
        if self.color[3] < 1.0:
            gl.glDisable(gl.GL_BLEND)
        
        self.restore_transformation()


class SphereShape(Shape):
    """A 3D sphere shape."""
    
    def __init__(self, shape_id: str = None):
        super().__init__(shape_id)
        self.radius = 0.5
        self.resolution = 16
        self.wireframe = False
    
    def to_dict(self):
        """Convert shape to dictionary for serialization."""
        data = super().to_dict()
        data.update({
            'radius': self.radius,
            'resolution': self.resolution,
            'wireframe': self.wireframe
        })
        return data
    
    def render(self):
        if not self.visible:
            return
        
        self.apply_transformation()
        gl.glColor4f(self.color[0], self.color[1], self.color[2], self.color[3])
        
        # Enable blending for transparency
        if self.color[3] < 1.0:
            gl.glEnable(gl.GL_BLEND)
            gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        
        # Use GLU quadric for sphere rendering
        quadric = glu.gluNewQuadric()
        if self.wireframe:
            glu.gluQuadricDrawStyle(quadric, glu.GLU_LINE)
        else:
            glu.gluQuadricDrawStyle(quadric, glu.GLU_FILL)
        
        glu.gluQuadricNormals(quadric, glu.GLU_SMOOTH)
        glu.gluSphere(quadric, self.radius, self.resolution, self.resolution)
        glu.gluDeleteQuadric(quadric)
        
        if self.color[3] < 1.0:
            gl.glDisable(gl.GL_BLEND)
        
        self.restore_transformation()


class CylinderShape(Shape):
    """A 3D cylinder shape."""
    
    def __init__(self, shape_id: str = None):
        super().__init__(shape_id)
        self.radius = 0.5
        self.height = 2.0
        self.resolution = 16
        self.wireframe = False
    
    def to_dict(self):
        """Convert shape to dictionary for serialization."""
        data = super().to_dict()
        data.update({
            'radius': self.radius,
            'height': self.height,
            'resolution': self.resolution,
            'wireframe': self.wireframe
        })
        return data
    
    def render(self):
        if not self.visible:
            return
        
        self.apply_transformation()
        gl.glColor4f(self.color[0], self.color[1], self.color[2], self.color[3])
        
        # Enable blending for transparency
        if self.color[3] < 1.0:
            gl.glEnable(gl.GL_BLEND)
            gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        
        # Use GLU quadric for cylinder rendering
        quadric = glu.gluNewQuadric()
        if self.wireframe:
            glu.gluQuadricDrawStyle(quadric, glu.GLU_LINE)
        else:
            glu.gluQuadricDrawStyle(quadric, glu.GLU_FILL)
        
        glu.gluQuadricNormals(quadric, glu.GLU_SMOOTH)
        
        # Draw cylinder body
        gl.glPushMatrix()
        gl.glTranslatef(0.0, 0.0, -self.height / 2.0)
        glu.gluCylinder(quadric, self.radius, self.radius, self.height, self.resolution, 1)
        gl.glPopMatrix()
        
        # Draw top and bottom caps if not wireframe
        if not self.wireframe:
            # Bottom cap
            gl.glPushMatrix()
            gl.glTranslatef(0.0, 0.0, -self.height / 2.0)
            gl.glRotatef(180.0, 1.0, 0.0, 0.0)
            glu.gluDisk(quadric, 0.0, self.radius, self.resolution, 1)
            gl.glPopMatrix()
            
            # Top cap
            gl.glPushMatrix()
            gl.glTranslatef(0.0, 0.0, self.height / 2.0)
            glu.gluDisk(quadric, 0.0, self.radius, self.resolution, 1)
            gl.glPopMatrix()
        
        glu.gluDeleteQuadric(quadric)
        
        if self.color[3] < 1.0:
            gl.glDisable(gl.GL_BLEND)
        
        self.restore_transformation()


class MediaScreen(Screen):
    """A screen that displays media content (images, videos, GIFs)."""
    
    def __init__(self, screen_type: ScreenType = ScreenType.SCREEN_2D, media_type: MediaType = None):
        super().__init__(screen_type=screen_type)
        self.media_type = media_type
        self.media_path = None
        self.media_texture_id = None
        self.media_data_loaded = False  # Track if media data is loaded
        self.image_data = None  # Store PIL Image data before OpenGL texture creation
        
        # Video-specific properties
        self.video_capture = None  # Not used - FFmpeg only
        self.video_thread = None
        self.video_playing = False
        self.video_paused = False
        self.video_stopped = False
        self.video_fps = 30.0
        self.current_frame = None
        self.frame_lock = threading.Lock()
        self.video_duration = 0.0
        self.video_position = 0.0
        self.video_frame_count = 0
        self.current_frame_index = 0
        
        # FFmpeg-based video processing
        self.ffmpeg_process = None
        self.frame_cache = []
        self.max_cache_size = 30  # Cache 30 frames (~1 second at 30fps)
        
        # Fallback: use simple frame cycling for problematic videos
        self.use_simple_playback = False
        self.simple_frame_cache = []
        self.simple_cache_loaded = False
        
        # GIF-specific properties
        self.gif_frames = []
        self.gif_frame_index = 0
        self.gif_frame_durations = []
        self.gif_last_frame_time = 0.0
        
        # Web-specific properties
        self.web_url = None
        self.web_driver = None
        self.web_refresh_interval = 30.0  # Refresh every 30 seconds
        self.web_last_refresh_time = 0.0
        self.web_width = 1280
        self.web_height = 720
        self.web_auto_refresh = True
        
        # Audio-specific properties (re-added for video support)
        self.audio_initialized = False
        self.audio_file = None
        self.audio_channel = None
        self.audio_start_time = None
        self.audio_paused_time = 0.0
        
        # Fallback audio system using system commands
        self.use_system_audio = False
        self.system_audio_process = None
        
        # Playback speed control
        self.playback_speed = 1.0  # Normal speed (1.0 = 100%)
        self.speed_adjusted_audio_file = None  # Speed-adjusted audio file
        
        # Frame rate control for video sampling
        self.target_frame_rate = None  # Use original video FPS if None
        self.effective_frame_rate = None  # Calculated effective frame rate
        
    def load_media(self, file_path: str) -> bool:
        """Load media from the specified file path."""
        if not os.path.exists(file_path):
            print(f"DEBUG: Media file not found: {file_path}")
            return False
        
        self.media_path = file_path
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']:
            self.media_type = MediaType.IMAGE
            return self._load_image()
        elif file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
            self.media_type = MediaType.VIDEO
            return self._load_video()
        elif file_ext == '.gif':
            self.media_type = MediaType.GIF
            return self._load_gif()
        else:
            print(f"DEBUG: Unsupported media format: {file_ext}")
            return False
    
    def load_website(self, url: str) -> bool:
        """Load a website URL for display."""
        if not SELENIUM_AVAILABLE:
            print("DEBUG: Selenium not available, cannot load websites")
            return False
        
        try:
            # Validate URL format
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            self.web_url = url
            self.media_type = MediaType.WEB
            print(f"DEBUG: Loading website: {url}")
            
            # Initialize webdriver for screenshot capture
            if not self._init_webdriver():
                return False
            
            # Take initial screenshot
            success = self._capture_website_screenshot()
            if success:
                self.media_data_loaded = True
                print(f"DEBUG: Website loaded successfully: {url}")
                return True
            else:
                print(f"DEBUG: Failed to capture website screenshot: {url}")
                return False
                
        except Exception as e:
            print(f"DEBUG: Exception loading website {url}: {e}")
            return False
    
    def _load_image(self) -> bool:
        """Load a static image."""
        try:
            print(f"DEBUG: Loading image data from {self.media_path}")
            image = Image.open(self.media_path)
            image = image.convert('RGBA')
            
            # Store image data for deferred texture creation
            self.image_data = image
            self.media_data_loaded = True
            
            print(f"DEBUG: Image data loaded successfully for {self.name}, size: {image.size}")
            return True
        except Exception as e:
            print(f"DEBUG: Failed to load image {self.media_path}: {e}")
            return False
    
    def _load_video(self) -> bool:
        """Load a video file with audio support."""
        try:
            print(f"DEBUG: Loading video data from {self.media_path}")
            
            # Check if file exists and is readable
            if not os.path.exists(self.media_path):
                print(f"DEBUG: Video file does not exist: {self.media_path}")
                return False
            
            # Initialize audio support
            print(f"DEBUG: Video loading with audio support")
            
            # Get video properties using FFprobe (safer than OpenCV)
            try:
                result = subprocess.run([
                    'ffprobe', '-v', 'quiet', '-print_format', 'json', 
                    '-show_format', '-show_streams', self.media_path
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    import json
                    data = json.loads(result.stdout)
                    
                    # Find video stream
                    video_stream = None
                    for stream in data.get('streams', []):
                        if stream.get('codec_type') == 'video':
                            video_stream = stream
                            break
                    
                    if video_stream:
                        self.video_fps = float(video_stream.get('r_frame_rate', '30/1').split('/')[0]) / float(video_stream.get('r_frame_rate', '30/1').split('/')[1])
                        self.video_duration = float(data.get('format', {}).get('duration', 0))
                        self.video_frame_count = int(self.video_fps * self.video_duration)
                        print(f"DEBUG: Video FPS: {self.video_fps}, Duration: {self.video_duration}s, Frames: {self.video_frame_count}")
                    else:
                        print(f"DEBUG: No video stream found")
                        return False
                else:
                    print(f"DEBUG: ffprobe failed, falling back to OpenCV")
                    # Fall back to OpenCV
                    return self._load_video_opencv_fallback()
                    
            except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
                print(f"DEBUG: ffprobe not available: {e}, using OpenCV fallback")
                return self._load_video_opencv_fallback()
            
            # Extract audio for synchronized playback
            audio_extraction_success = self._extract_audio()
            if audio_extraction_success:
                print(f"DEBUG: Audio extraction successful")
            else:
                print(f"DEBUG: Audio extraction failed or no audio track found")
            
            # Skip OpenCV entirely - use FFmpeg for frame extraction
            print(f"DEBUG: Skipping OpenCV, will use FFmpeg for frame extraction")
            self.video_capture = None  # Will be handled by FFmpeg
            
            # Mark data as loaded (texture creation deferred)
            self.media_data_loaded = True
            
            # Try to pre-load a few frames for fallback playback
            self._prepare_simple_playback()
            
            print(f"DEBUG: Video data loaded successfully for {self.name} (FPS: {self.video_fps}, Duration: {self.video_duration}s)")
            return True
            
        except Exception as e:
            print(f"DEBUG: Exception in _load_video for {self.media_path}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _load_video_opencv_fallback(self) -> bool:
        """Fallback video loading using only OpenCV."""
        try:
            print(f"DEBUG: Using OpenCV fallback for {self.media_path}")
            self.video_capture = cv2.VideoCapture(self.media_path)
            
            if not self.video_capture.isOpened():
                print(f"DEBUG: OpenCV fallback failed to open video")
                return False
            
            self.video_fps = self.video_capture.get(cv2.CAP_PROP_FPS)
            if self.video_fps <= 0:
                self.video_fps = 30.0
                
            frame_count = self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT)
            if frame_count > 0:
                self.video_duration = frame_count / self.video_fps
            
            self.media_data_loaded = True
            print(f"DEBUG: OpenCV fallback successful (FPS: {self.video_fps})")
            return True
            
        except Exception as e:
            print(f"DEBUG: OpenCV fallback failed: {e}")
            return False
    
    def _load_gif(self) -> bool:
        """Load an animated GIF."""
        try:
            print(f"DEBUG: Starting GIF load for {self.media_path}")
            gif_image = Image.open(self.media_path)
            print(f"DEBUG: Opened GIF image, format: {gif_image.format}")
            
            # Extract all frames from the GIF
            self.gif_frames = []
            self.gif_frame_durations = []
            
            frame_index = 0
            while True:
                try:
                    gif_image.seek(frame_index)
                    frame = gif_image.convert('RGBA')
                    print(f"DEBUG: Processing frame {frame_index}, size: {frame.size}")
                    
                    # Store frame data
                    self.gif_frames.append(frame.tobytes())
                    
                    # Get frame duration (in milliseconds)
                    duration = gif_image.info.get('duration', 100)  # Default 100ms
                    self.gif_frame_durations.append(duration / 1000.0)  # Convert to seconds
                    print(f"DEBUG: Frame {frame_index} duration: {duration}ms")
                    
                    frame_index += 1
                except EOFError:
                    print(f"DEBUG: Reached end of GIF at frame {frame_index}")
                    break
            
            if not self.gif_frames:
                print(f"DEBUG: No frames found in GIF: {self.media_path}")
                return False
            
            print(f"DEBUG: Extracted {len(self.gif_frames)} frames from GIF")
            
            # Store frame dimensions from first frame
            first_frame_img = Image.open(self.media_path)
            self.gif_width = first_frame_img.width
            self.gif_height = first_frame_img.height
            
            # Mark data as loaded (texture creation deferred)
            self.media_data_loaded = True
            print(f"DEBUG: GIF dimensions: {self.gif_width}x{self.gif_height}")
            print(f"DEBUG: Successfully loaded GIF {self.media_path} ({len(self.gif_frames)} frames, {self.gif_width}x{self.gif_height})")
            return True
        except Exception as e:
            print(f"DEBUG: Failed to load GIF {self.media_path}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def start_video_playback(self):
        """Start video playback in a separate thread."""
        print(f"DEBUG: ===== START_VIDEO_PLAYBACK CALLED FOR {self.name} =====")
        print(f"DEBUG: Media type: {self.media_type}")
        print(f"DEBUG: Video playing: {self.video_playing}")
        print(f"DEBUG: Has audio file: {hasattr(self, 'audio_file') and self.audio_file}")
        
        if self.media_type == MediaType.VIDEO and not self.video_playing:
            print(f"DEBUG: Starting video playback for {self.name}")
            
            # Initialize audio synchronously first - ensures consistent behavior
            print(f"DEBUG: About to initialize audio...")
            audio_init_result = self._init_audio()
            print(f"DEBUG: Audio initialization result: {audio_init_result}")
            
            # Set video state
            self.video_playing = True
            self.video_paused = False
            self.video_stopped = False
            self.current_frame_index = 0
            
            # Start video thread
            self.video_thread = threading.Thread(target=self._video_playback_loop, daemon=True)
            self.video_thread.start()
            
            # Start audio slightly after video thread to avoid race conditions
            time.sleep(0.05)  # Small delay for video thread to initialize
            self._start_audio_playback()
            print(f"DEBUG: Video playback thread started for {self.name}")
        elif self.video_playing:
            print(f"DEBUG: Video {self.name} is already playing")
        else:
            print(f"DEBUG: Cannot start video playback for {self.name} - not a video or conditions not met")
    
    def pause_video_playback(self):
        """Toggle pause/resume for video playback."""
        if self.media_type == MediaType.VIDEO and self.video_playing:
            self.video_paused = not self.video_paused
            
            # Handle audio pause/resume
            if self.use_system_audio and self.system_audio_process:
                # System audio doesn't support pause/resume, so restart if needed
                if self.video_paused:
                    self.system_audio_process.terminate()
                    print(f"DEBUG: System audio paused (stopped)")
                else:
                    self._start_system_audio_fallback()
                    print(f"DEBUG: System audio resumed (restarted)")
            else:
                try:
                    if pygame.mixer.get_init():
                        if self.video_paused:
                            # Pause both music and channel audio
                            pygame.mixer.music.pause()
                            if self.audio_channel:
                                self.audio_channel.pause()
                            self.audio_paused_time = time.time()
                            print(f"DEBUG: Pygame audio paused")
                        else:
                            # Resume both music and channel audio
                            pygame.mixer.music.unpause()
                            if self.audio_channel:
                                self.audio_channel.unpause()
                            # Adjust audio timing for pause duration
                            if self.audio_paused_time > 0:
                                pause_duration = time.time() - self.audio_paused_time
                                self.audio_start_time += pause_duration
                                self.audio_paused_time = 0
                            print(f"DEBUG: Pygame audio resumed")
                except pygame.error:
                    print(f"DEBUG: Pygame mixer not available for pause/resume")
            
            print(f"DEBUG: Video {'paused' if self.video_paused else 'resumed'}")
    
    def stop_video_playback(self):
        """Stop video playback."""
        if self.media_type == MediaType.VIDEO:
            self.video_playing = False
            self.video_paused = False
            self.video_stopped = True
            
            # Stop audio playback
            if self.use_system_audio and self.system_audio_process:
                self.system_audio_process.terminate()
                self.system_audio_process = None
                print(f"DEBUG: System audio stopped")
            else:
                try:
                    if pygame.mixer.get_init():
                        pygame.mixer.music.stop()
                        if self.audio_channel:
                            self.audio_channel.stop()
                        self.audio_channel = None
                        print(f"DEBUG: Pygame audio stopped")
                except pygame.error:
                    print(f"DEBUG: Pygame mixer not available for stop")
            
            print(f"DEBUG: Video stopped")
    
    def restart_video_playback(self):
        """Restart video from the beginning."""
        if self.media_type == MediaType.VIDEO:
            self.stop_video_playback()
            
            # Reset video to beginning
            self.current_frame_index = 0
            self.video_position = 0.0
            self.frame_cache.clear()
            print(f"DEBUG: Reset video to beginning")
            
            # Restart playback
            time.sleep(0.1)  # Brief pause
            self.start_video_playback()
    
    
    def _video_playback_loop(self):
        """Video playback loop using FFmpeg for frame extraction with audio sync."""
        # Calculate effective frame rate (target frame rate or original video FPS)
        self.effective_frame_rate = self.target_frame_rate if self.target_frame_rate else self.video_fps
        
        # Calculate frame time for display rate (not necessarily sync timing)
        # This controls how often we check for new frames to display
        display_fps = self.effective_frame_rate
        base_frame_time = 1.0 / display_fps
        
        # Don't adjust frame_time by playback_speed here - that's handled by audio sync
        # The playback speed affects the audio timeline, which drives the video sync
        frame_time = base_frame_time
        
        print(f"DEBUG: Video playback loop started for {self.name}")
        print(f"DEBUG: Original FPS: {self.video_fps}, Target FPS: {self.target_frame_rate}, Effective FPS: {self.effective_frame_rate}")
        print(f"DEBUG: Playback speed: {self.playback_speed}x, Frame time: {frame_time:.4f}s")
        
        # Real-time playback timing synchronized with audio
        playback_start_time = time.time()
        
        while self.video_playing and not self.video_stopped:
            current_time = time.time()
            
            # Handle pause state
            if self.video_paused:
                time.sleep(0.1)  # Sleep briefly while paused
                continue
            
            # Calculate current video position based on real time and playback speed
            if self.audio_start_time:
                # Use audio time as master clock for perfect sync
                audio_elapsed = current_time - self.audio_start_time
                
                # The audio is already speed-adjusted, so audio_elapsed represents 
                # the actual video timeline position we should be at
                video_timeline_position = audio_elapsed
                
                # Calculate which original video frame corresponds to this timeline position
                original_frame_index = int(video_timeline_position * self.video_fps)
                
                # If we have a custom target frame rate, we need to decide which frame to show
                # The target frame rate affects display smoothness, not sync timing
                if self.target_frame_rate and self.target_frame_rate != self.video_fps:
                    # Map the timeline position to our target frame rate for display
                    # This allows us to show fewer/more frames while staying synced
                    display_frame_index = int(video_timeline_position * self.target_frame_rate)
                    
                    # But we still need to extract the correct frame from the original video
                    # Map display frame back to original video frame
                    frame_ratio = self.video_fps / self.target_frame_rate
                    target_frame_index = int(display_frame_index * frame_ratio)
                    
                    # Debug sync info every 30 frames
                    if target_frame_index % 30 == 0:
                        print(f"DEBUG: Sync - Audio time: {video_timeline_position:.2f}s, "
                              f"Original frame: {original_frame_index}, Display frame: {display_frame_index}, "
                              f"Target frame: {target_frame_index}, Speed: {self.playback_speed}x")
                else:
                    # Use original frame rate
                    target_frame_index = original_frame_index
                    
            else:
                # Fallback to system time if no audio
                elapsed = current_time - playback_start_time
                # Apply playback speed to elapsed time, then calculate frame
                speed_adjusted_elapsed = elapsed * self.playback_speed
                target_frame_index = int(speed_adjusted_elapsed * self.effective_frame_rate)
            
            # Only update frame if we need to advance
            if target_frame_index > self.current_frame_index:
                # Get current frame using FFmpeg or simple fallback
                if self.use_simple_playback:
                    frame = self._get_simple_frame(target_frame_index)
                else:
                    frame = self._get_video_frame(target_frame_index)
                    # If FFmpeg fails, switch to simple playback
                    if frame is None and self.simple_cache_loaded:
                        print(f"DEBUG: FFmpeg frame extraction failed, switching to simple playback")
                        self.use_simple_playback = True
                        frame = self._get_simple_frame(target_frame_index)
                
                if frame is not None:
                    with self.frame_lock:
                        self.current_frame = frame
                        self.current_frame_index = target_frame_index
                        self.video_position = self.current_frame_index / self.video_fps
                    
                    # Log timing every 30 frames for debugging
                    if self.current_frame_index % 30 == 0:
                        if self.audio_start_time:
                            audio_pos = current_time - self.audio_start_time
                            video_pos = self.current_frame_index / self.video_fps
                            sync_diff = abs(audio_pos - video_pos)
                            print(f"DEBUG: Frame {self.current_frame_index}, audio: {audio_pos:.2f}s, video: {video_pos:.2f}s, sync diff: {sync_diff:.3f}s")
                        else:
                            elapsed = current_time - playback_start_time
                            expected = self.current_frame_index / self.video_fps
                            print(f"DEBUG: Frame {self.current_frame_index}, elapsed: {elapsed:.2f}s, expected: {expected:.2f}s")
                    
                    # Loop video if we reach the end
                    if self.current_frame_index >= self.video_frame_count:
                        print(f"DEBUG: End of video reached, restarting loop")
                        
                        # Stop current audio cleanly
                        try:
                            if pygame.mixer.get_init():
                                pygame.mixer.music.stop()
                                if self.audio_channel:
                                    self.audio_channel.stop()
                        except pygame.error:
                            pass  # Mixer not initialized, skip pygame cleanup
                        
                        # Stop system audio if using fallback
                        if self.use_system_audio and self.system_audio_process:
                            self.system_audio_process.terminate()
                            self.system_audio_process = None
                            self.use_system_audio = False
                        
                        # Reset frame position and timing for seamless loop
                        self.current_frame_index = 0
                        playback_start_time = time.time()
                        
                        # Brief pause to ensure clean restart
                        time.sleep(0.02)
                        
                        # Restart audio playback in sync with new loop
                        self._start_audio_playback()
                        
                else:
                    print(f"DEBUG: Failed to get frame {target_frame_index}")
                    self.current_frame_index = target_frame_index  # Skip frame but keep position
            
            # Sleep for optimal timing based on target frame rate
            # Use shorter sleep for higher frame rates, longer for lower frame rates
            optimal_sleep = min(0.010, max(0.001, frame_time * 0.1))  # 10% of frame time, clamped between 1-10ms
            time.sleep(optimal_sleep)
    
    def _get_video_frame(self, frame_index):
        """Extract a specific frame from video using FFmpeg."""
        try:
            # Calculate timestamp for this frame
            timestamp = frame_index / self.video_fps
            
            # Only log every 30th frame to reduce debug spam
            if frame_index % 30 == 0:
                print(f"DEBUG: Extracting frame {frame_index} at timestamp {timestamp:.3f}s")
            
            # Use FFmpeg to extract frame at specific timestamp with explicit dimensions
            # First get the video dimensions if we don't have them
            if not hasattr(self, 'video_width') or not hasattr(self, 'video_height'):
                # Get video dimensions from FFprobe
                probe_result = subprocess.run([
                    'ffprobe', '-v', 'quiet', '-print_format', 'json', 
                    '-show_streams', self.media_path
                ], capture_output=True, text=True, timeout=5)
                
                if probe_result.returncode == 0:
                    import json
                    data = json.loads(probe_result.stdout)
                    for stream in data.get('streams', []):
                        if stream.get('codec_type') == 'video':
                            self.video_width = stream.get('width', 640)
                            self.video_height = stream.get('height', 480)
                            break
                else:
                    # Default dimensions if probe fails
                    self.video_width = 640
                    self.video_height = 480
                    
                print(f"DEBUG: Video dimensions: {self.video_width}x{self.video_height}")
            
            # Extract frame with known dimensions using faster seeking
            result = subprocess.run([
                'ffmpeg', '-ss', str(timestamp), '-i', self.media_path,
                '-vframes', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                '-s', f'{self.video_width}x{self.video_height}',
                '-an',  # No audio
                '-loglevel', 'error',  # Reduce noise
                '-'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
            
            if result.returncode == 0:
                frame_data = result.stdout
                expected_size = self.video_width * self.video_height * 3
                
                if len(frame_data) == expected_size:
                    frame = np.frombuffer(frame_data, dtype=np.uint8)
                    frame = frame.reshape((self.video_height, self.video_width, 3))
                    # Flip frame vertically to correct OpenGL orientation
                    frame = np.flipud(frame)
                    # Only log every 30th frame to reduce debug spam
                    if frame_index % 30 == 0:
                        print(f"DEBUG: Successfully extracted and flipped frame {frame_index}")
                    return frame
                else:
                    print(f"DEBUG: Frame data size mismatch: got {len(frame_data)}, expected {expected_size}")
            else:
                print(f"DEBUG: FFmpeg failed with return code {result.returncode}")
                if result.stderr:
                    stderr_msg = result.stderr.decode()
                    print(f"DEBUG: FFmpeg error: {stderr_msg}")
                    # Only print first few lines of error to avoid spam
                    if len(stderr_msg.split('\n')) > 3:
                        temp = stderr_msg.split('\n')[:3]
                        print(f"DEBUG: FFmpeg error (truncated): {temp}")
            
            return None
            
        except (subprocess.TimeoutExpired, Exception) as e:
            print(f"DEBUG: Failed to extract frame {frame_index}: {e}")
            return None
    
    def _prepare_simple_playback(self):
        """Pre-extract a few frames for simple playback fallback."""
        try:
            print(f"DEBUG: Preparing simple playback for {self.name}")
            # Extract fewer frames but at more even intervals for better representation
            num_frames_to_extract = min(8, max(3, self.video_frame_count // 30))  # 3-8 frames
            frame_interval = max(1, self.video_frame_count // num_frames_to_extract)
            
            print(f"DEBUG: Extracting {num_frames_to_extract} frames at interval {frame_interval}")
            
            for i in range(0, min(self.video_frame_count, num_frames_to_extract * frame_interval), frame_interval):
                frame = self._get_video_frame(i)
                if frame is not None:
                    self.simple_frame_cache.append(frame)
                    print(f"DEBUG: Extracted frame {i} for simple cache")
                    if len(self.simple_frame_cache) >= num_frames_to_extract:
                        break
                else:
                    print(f"DEBUG: Failed to extract frame {i}, stopping")
                    break  # Stop if we can't get frames
            
            if len(self.simple_frame_cache) > 0:
                self.simple_cache_loaded = True
                print(f"DEBUG: Simple playback prepared with {len(self.simple_frame_cache)} frames")
                # Don't auto-enable simple playback, let real-time try first
                self.use_simple_playback = False  
            else:
                print(f"DEBUG: Failed to prepare simple playback - no frames extracted")
                
        except Exception as e:
            print(f"DEBUG: Exception preparing simple playback: {e}")
    
    def _get_simple_frame(self, frame_index):
        """Get frame from simple cache for fallback playback."""
        if not self.simple_cache_loaded or len(self.simple_frame_cache) == 0:
            return None
        
        # Map the current frame index to the cached frames proportionally
        # This ensures even distribution across the video duration
        if self.video_frame_count > 0:
            # Calculate proportional position in video (0.0 to 1.0)
            video_progress = (frame_index % self.video_frame_count) / self.video_frame_count
            # Map to cache index
            cache_index = int(video_progress * len(self.simple_frame_cache)) % len(self.simple_frame_cache)
        else:
            cache_index = frame_index % len(self.simple_frame_cache)
        
        return self.simple_frame_cache[cache_index]
    
    def _extract_audio(self) -> bool:
        """Extract audio from video file for synchronized playback."""
        try:
            import tempfile
            import os
            
            # Create temporary audio file
            audio_temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            self.audio_file = audio_temp_file.name
            audio_temp_file.close()
            
            print(f"DEBUG: Extracting audio to {self.audio_file}")
            
            # First check if video has audio streams
            probe_result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_streams', self.media_path
            ], capture_output=True, text=True, timeout=10)
            
            if probe_result.returncode == 0:
                import json
                data = json.loads(probe_result.stdout)
                audio_streams = [s for s in data.get('streams', []) if s.get('codec_type') == 'audio']
                
                if not audio_streams:
                    print(f"DEBUG: No audio streams found in video file")
                    return False
                    
                print(f"DEBUG: Found {len(audio_streams)} audio stream(s)")
            else:
                print(f"DEBUG: Could not probe audio streams, attempting extraction anyway")
            
            # Extract audio using FFmpeg with better error handling
            result = subprocess.run([
                'ffmpeg', '-i', self.media_path,
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # PCM 16-bit little endian
                '-ar', '44100',  # 44.1kHz sample rate
                '-ac', '2',  # Stereo
                '-y',  # Overwrite output file
                '-loglevel', 'error',  # Reduce FFmpeg output noise
                self.audio_file
            ], capture_output=True, timeout=60)
            
            if result.returncode == 0 and os.path.exists(self.audio_file):
                audio_size = os.path.getsize(self.audio_file)
                if audio_size > 0:
                    print(f"DEBUG: Audio extraction successful - {audio_size} bytes")
                return True
            else:
                    print(f"DEBUG: Audio extraction produced empty file")
                    os.unlink(self.audio_file)
                    self.audio_file = None
                    return False
            error_msg = result.stderr.decode() if result.stderr else "Unknown error"
            print(f"DEBUG: Audio extraction failed: {error_msg}")
            # Clean up failed audio file
            if os.path.exists(self.audio_file):
                os.unlink(self.audio_file)
            self.audio_file = None
            return False
                
        except subprocess.TimeoutExpired:
            print(f"DEBUG: Audio extraction timed out")
            if hasattr(self, 'audio_file') and self.audio_file and os.path.exists(self.audio_file):
                os.unlink(self.audio_file)
            self.audio_file = None
            return False
        except Exception as e:
            print(f"DEBUG: Exception during audio extraction: {e}")
            import traceback
            traceback.print_exc()
            if hasattr(self, 'audio_file') and self.audio_file and os.path.exists(self.audio_file):
                os.unlink(self.audio_file)
            self.audio_file = None
            return False
    
    def _init_audio(self):
        """Initialize audio system for video playback."""
        try:
            if not self.audio_file or not os.path.exists(self.audio_file):
                print(f"DEBUG: No audio file available for {self.name}")
                return False
            
            audio_size = os.path.getsize(self.audio_file)
            print(f"DEBUG: Audio file exists: {self.audio_file}, size: {audio_size} bytes")
            
            if audio_size == 0:
                print(f"DEBUG: Audio file is empty, skipping audio initialization")
                return False
            
            if not self.audio_initialized:
                try:
                    # Use global audio manager to prevent conflicts
                    manager = get_audio_manager()
                    if not manager.initialize():
                        print(f"DEBUG: Global audio manager initialization failed")
                        return False
                    
                    # Set this screen as the current audio screen
                    manager.set_current_screen(self)
                    self.audio_initialized = True
                    
                    # Check mixer status
                    mixer_info = pygame.mixer.get_init()
                    if mixer_info:
                        print(f"DEBUG: Audio system ready - settings: {mixer_info}")
                    else:
                        print(f"DEBUG: Audio mixer not available")
                        return False
                        
                    # Verify we can load the audio file
                    try:
                        test_sound = pygame.mixer.Sound(self.audio_file)
                        duration = test_sound.get_length()
                        print(f"DEBUG: Audio file verified - duration: {duration:.2f}s")
                        del test_sound  # Clean up test
                    except pygame.error as e:
                        print(f"DEBUG: Cannot load audio file with pygame: {e}")
                        return False
                        
                except pygame.error as e:
                    print(f"DEBUG: Pygame mixer initialization failed: {e}")
                    self.audio_initialized = False
                    return False
            
            return True
            
        except Exception as e:
            print(f"DEBUG: Failed to initialize audio: {e}")
            import traceback
            traceback.print_exc()
            self.audio_initialized = False
            return False
    
    def _start_audio_playback(self):
        """Start audio playback synchronized with video."""
        print(f"DEBUG: ===== _start_audio_playback() called for {self.name} =====")
        print(f"DEBUG: Audio file: {self.audio_file}")
        print(f"DEBUG: Speed adjusted audio: {getattr(self, 'speed_adjusted_audio_file', None)}")
        
        try:
            if not self.audio_file or not os.path.exists(self.audio_file):
                print(f"DEBUG: No audio file to play")
                return
            
            if not self.audio_initialized:
                if not self._init_audio():
                    print(f"DEBUG: Audio initialization failed, skipping audio")
                    return
            
            # Set this screen as the active audio screen
            manager = get_audio_manager()
            manager.set_current_screen(self)
            
            # Determine which audio file to use (speed-adjusted or original)
            audio_file_to_use = self.speed_adjusted_audio_file if self.speed_adjusted_audio_file else self.audio_file
            print(f"DEBUG: Starting audio playback: {audio_file_to_use}")
            if self.playback_speed != 1.0:
                print(f"DEBUG: Using {self.playback_speed:.1f}x speed-adjusted audio")
            
            # Stop any existing audio first
            try:
                if pygame.mixer.get_init():
                    pygame.mixer.music.stop()
                    if hasattr(self, 'audio_channel') and self.audio_channel:
                        self.audio_channel.stop()
            except pygame.error:
                print(f"DEBUG: Pygame mixer not available, will use system audio")
                self._start_system_audio_fallback()
                return
            
            # Load and verify audio file
            try:
                sound = pygame.mixer.Sound(audio_file_to_use)
                sound_length = sound.get_length()
                print(f"DEBUG: Audio loaded successfully - duration: {sound_length:.2f}s")
                
                if sound_length <= 0:
                    print(f"DEBUG: Invalid audio duration: {sound_length}")
                    return
                    
            except pygame.error as e:
                print(f"DEBUG: Failed to load audio file: {e}")
                return
            
            # Try music-based playback first (more reliable for longer files)
            try:
                pygame.mixer.music.load(audio_file_to_use)
                
                # Set volume and verify
                pygame.mixer.music.set_volume(1.0)  # Full volume
                current_volume = pygame.mixer.music.get_volume()
                print(f"DEBUG: Music volume set to: {current_volume}")
                
                pygame.mixer.music.play(0)  # Play once, no looping
                
                # Record start time for synchronization
                self.audio_start_time = time.time()
                
                # Longer delay to ensure audio starts properly
                time.sleep(0.2)
                
                # Verify audio started
                if pygame.mixer.music.get_busy():
                    print(f"DEBUG: ✅ Audio playback started successfully using music mixer")
                    print(f"DEBUG: 🔊 AUDIO SHOULD BE PLAYING NOW - Check your speakers/volume!")
                    
                    # Also try channel-based as backup (in case music fails mid-stream)
                    try:
                        self.audio_channel = pygame.mixer.Channel(0)
                        if not self.audio_channel.get_busy():
                            # Don't start channel if music is working, keep as backup
                            print(f"DEBUG: Channel backup prepared")
                    except Exception:
                        pass  # Channel backup not critical
                        
                else:
                    # Fallback to channel-based playback
                    print(f"DEBUG: Music mixer failed, trying channel-based playback")
                    self.audio_channel = pygame.mixer.Channel(0)
                    self.audio_channel.set_volume(1.0)  # Full volume for channel too
                    self.audio_channel.play(sound)
                    
                    if self.audio_channel.get_busy():
                        print(f"DEBUG: ✅ Audio playback started using channel mixer")
                        print(f"DEBUG: 🔊 CHANNEL AUDIO SHOULD BE PLAYING NOW!")
                    else:
                        print(f"DEBUG: ❌ ERROR: Both music and channel audio playback failed")
                        self.audio_start_time = None
                        return
                
                # Final verification with more details
                music_busy = pygame.mixer.music.get_busy()
                channel_busy = self.audio_channel and self.audio_channel.get_busy()
                audio_playing = music_busy or channel_busy
                
                print(f"DEBUG: Audio status - Music: {music_busy}, Channel: {channel_busy}")
                
                if audio_playing:
                    print(f"DEBUG: ✅ Audio playback confirmed and synchronized")
                    print(f"DEBUG: 🎵 If you don't hear anything, check:")
                    print(f"DEBUG:    - System volume is up")
                    print(f"DEBUG:    - Application isn't muted")
                    print(f"DEBUG:    - Speakers/headphones are connected")
                else:
                    print(f"DEBUG: ❌ WARNING: Audio playback verification failed")
                    
            except pygame.error as e:
                print(f"DEBUG: Pygame audio error: {e}")
                print(f"DEBUG: Falling back to system audio...")
                self._start_system_audio_fallback()
            
        except Exception as e:
            print(f"DEBUG: Failed to start audio playback: {e}")
            print(f"DEBUG: Trying system audio fallback...")
            self._start_system_audio_fallback()
    
    def _start_system_audio_fallback(self):
        """Fallback audio system using macOS afplay command"""
        try:
            # Determine which audio file to use (speed-adjusted or original)
            audio_file_to_use = self.speed_adjusted_audio_file if self.speed_adjusted_audio_file else self.audio_file
            
            if not audio_file_to_use or not os.path.exists(audio_file_to_use):
                print(f"DEBUG: No audio file for system fallback")
                return
            
            print(f"DEBUG: Starting system audio fallback with afplay...")
            if self.playback_speed != 1.0:
                print(f"DEBUG: Using {self.playback_speed:.1f}x speed-adjusted audio for system fallback")
            
            # Use afplay (macOS built-in audio player)
            self.system_audio_process = subprocess.Popen([
                'afplay', audio_file_to_use
            ])
            
            self.use_system_audio = True
            self.audio_start_time = time.time()
            
            print(f"DEBUG: ✅ System audio fallback started successfully!")
            print(f"DEBUG: 🔊 SYSTEM AUDIO SHOULD BE PLAYING NOW!")
            
        except Exception as e:
            print(f"DEBUG: System audio fallback also failed: {e}")
            self.audio_start_time = None
    
    def _create_speed_adjusted_audio(self, speed: float) -> str:
        """Create speed-adjusted audio file using FFmpeg"""
        try:
            if not self.audio_file or not os.path.exists(self.audio_file):
                print(f"DEBUG: No base audio file for speed adjustment")
                return None
            
            import tempfile
            
            # Create temporary speed-adjusted audio file
            speed_audio_temp = tempfile.NamedTemporaryFile(suffix=f'_speed_{speed:.1f}x.wav', delete=False)
            speed_audio_path = speed_audio_temp.name
            speed_audio_temp.close()
            
            print(f"DEBUG: Creating {speed:.1f}x speed audio: {speed_audio_path}")
            
            # Use FFmpeg atempo filter for speed adjustment
            # atempo can only handle 0.5-2.0x, so we may need to chain filters
            atempo_filters = []
            remaining_speed = speed
            
            # Chain atempo filters if speed is outside 0.5-2.0 range
            while remaining_speed > 2.0:
                atempo_filters.append("atempo=2.0")
                remaining_speed /= 2.0
            while remaining_speed < 0.5:
                atempo_filters.append("atempo=0.5")
                remaining_speed /= 0.5
            
            # Add final atempo filter
            if remaining_speed != 1.0:
                atempo_filters.append(f"atempo={remaining_speed:.3f}")
            
            if not atempo_filters:
                # No speed change needed, use original file
                return self.audio_file
            
            # Build FFmpeg command with chained atempo filters
            filter_chain = ",".join(atempo_filters)
            
            result = subprocess.run([
                'ffmpeg', '-i', self.audio_file,
                '-filter:a', filter_chain,
                '-y',  # Overwrite output file
                '-loglevel', 'error',
                speed_audio_path
            ], capture_output=True, timeout=60)
            
            if result.returncode == 0 and os.path.exists(speed_audio_path):
                audio_size = os.path.getsize(speed_audio_path)
                if audio_size > 0:
                    print(f"DEBUG: Speed-adjusted audio created successfully - {audio_size} bytes")
                    return speed_audio_path
                else:
                    print(f"DEBUG: Speed-adjusted audio file is empty")
                    os.unlink(speed_audio_path)
                    return None
            else:
                error_msg = result.stderr.decode() if result.stderr else "Unknown error"
                print(f"DEBUG: Speed audio adjustment failed: {error_msg}")
                if os.path.exists(speed_audio_path):
                    os.unlink(speed_audio_path)
                return None
                
        except Exception as e:
            print(f"DEBUG: Exception during speed audio adjustment: {e}")
            return None
    
    def set_playback_speed(self, speed: float):
        """Set video playback speed and adjust audio accordingly"""
        if speed <= 0:
            print(f"DEBUG: Invalid playback speed: {speed}")
            return False
        
        print(f"DEBUG: Setting playback speed to {speed:.1f}x")
        
        # Store the new speed
        old_speed = self.playback_speed
        self.playback_speed = speed
        
        # If video is currently playing, we need to restart with new speed
        if self.video_playing and self.media_type == MediaType.VIDEO:
            print(f"DEBUG: Video is playing, restarting with new speed")
            
            # Remember current position (in original time)
            current_position = self.video_position if hasattr(self, 'video_position') else 0.0
            
            # Stop current playback
            was_paused = self.video_paused
            self.stop_video_playback()
            
            # Create speed-adjusted audio if we have audio
            if self.audio_file:
                if speed != 1.0:
                    print(f"DEBUG: Creating speed-adjusted audio for {speed:.1f}x playback")
                    self.speed_adjusted_audio_file = self._create_speed_adjusted_audio(speed)
                    
                    if not self.speed_adjusted_audio_file:
                        print(f"DEBUG: Failed to create speed-adjusted audio, using original")
                        self.speed_adjusted_audio_file = self.audio_file
                else:
                    # Normal speed, use original audio
                    self.speed_adjusted_audio_file = self.audio_file
            
            # Restart playback
            self.start_video_playback()
            
            # Restore pause state if needed
            if was_paused:
                self.pause_video_playback()
            
            print(f"DEBUG: Playback speed changed from {old_speed:.1f}x to {speed:.1f}x")
            return True
        else:
            # Video not playing, just store the speed for next playback
            print(f"DEBUG: Speed set to {speed:.1f}x for next playback")
            return True
    
    def set_frame_rate(self, fps: float):
        """Set the target frame rate for video sampling."""
        if fps is not None and fps <= 0:
            print(f"DEBUG: Invalid frame rate: {fps}")
            return False
            
        print(f"DEBUG: Setting target frame rate to {fps} FPS for {self.name}")
        
        # Store the new frame rate
        old_fps = self.target_frame_rate
        self.target_frame_rate = fps
        
        # Restart playback if currently playing to apply new frame rate
        if self.video_playing and self.media_type == MediaType.VIDEO:
            print(f"DEBUG: Video is playing, restarting with new frame rate")
            
            # Stop current playback
            was_paused = self.video_paused
            self.stop_video_playback()
            
            # Brief pause to ensure clean restart
            time.sleep(0.1)
            
            # Restart playback
            self.start_video_playback()
            
            # Restore pause state if needed
            if was_paused:
                self.pause_video_playback()
            
            effective_fps = fps if fps else self.video_fps
            print(f"DEBUG: Frame rate changed from {old_fps} to {fps} (effective: {effective_fps} FPS)")
            return True
        else:
            # Video not playing, just store the frame rate for next playback
            effective_fps = fps if fps else self.video_fps
            print(f"DEBUG: Frame rate set to {fps} (effective: {effective_fps} FPS) for next playback")
            return True
    
    def reset_frame_rate(self):
        """Reset to use the original video frame rate."""
        print(f"DEBUG: Resetting to original frame rate ({self.video_fps} FPS) for {self.name}")
        return self.set_frame_rate(None)
    
    def _init_webdriver(self) -> bool:
        """Initialize Chrome webdriver for website screenshots."""
        try:
            if not SELENIUM_AVAILABLE:
                return False
            
            print(f"DEBUG: Initializing Chrome webdriver")
            chrome_options = ChromeOptions()
            chrome_options.add_argument('--headless')  # Run in background
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1280,720')
            chrome_options.add_argument('--hide-scrollbars')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            
            self.web_driver = webdriver.Chrome(options=chrome_options)
            self.web_driver.set_window_size(self.web_width, self.web_height)
            print(f"DEBUG: Chrome webdriver initialized successfully")
            return True
            
        except Exception as e:
            print(f"DEBUG: Failed to initialize webdriver: {e}")
            return False
    
    def _capture_website_screenshot(self) -> bool:
        """Capture a screenshot of the website."""
        try:
            if not self.web_driver or not self.web_url:
                return False
            
            print(f"DEBUG: Capturing screenshot of {self.web_url}")
            
            # Navigate to the website
            self.web_driver.get(self.web_url)
            
            # Wait for page to load
            WebDriverWait(self.web_driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # Take screenshot
            screenshot_data = self.web_driver.get_screenshot_as_png()
            
            # Convert to PIL Image
            screenshot_image = Image.open(io.BytesIO(screenshot_data))
            screenshot_image = screenshot_image.convert('RGBA')
            
            # Flip image vertically to correct OpenGL orientation (like video frames)
            screenshot_image = screenshot_image.transpose(Image.FLIP_TOP_BOTTOM)
            
            # Store image data for texture creation
            self.image_data = screenshot_image
            self.web_last_refresh_time = time.time()
            
            print(f"DEBUG: Website screenshot captured successfully: {screenshot_image.size}")
            return True
            
        except Exception as e:
            print(f"DEBUG: Failed to capture website screenshot: {e}")
            return False
    
    def _create_opengl_texture(self):
        """Create OpenGL texture from loaded media data."""
        if not self.media_data_loaded:
            print(f"DEBUG: No media data loaded for {self.name}")
            return
        
        try:
            if (self.media_type == MediaType.IMAGE or self.media_type == MediaType.WEB) and self.image_data:
                print(f"DEBUG: Creating OpenGL texture for {self.media_type.value} {self.name}")
                # Generate OpenGL texture for image
                self.media_texture_id = gl.glGenTextures(1)
                gl.glBindTexture(gl.GL_TEXTURE_2D, self.media_texture_id)
                
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
                
                gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, self.image_data.width, self.image_data.height, 
                               0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, self.image_data.tobytes())
                
                print(f"DEBUG: Created image texture {self.media_texture_id} for {self.name}")
                
            elif self.media_type == MediaType.GIF and self.gif_frames:
                print(f"DEBUG: Creating OpenGL texture for GIF {self.name}")
                # Generate OpenGL texture for GIF
                self.media_texture_id = gl.glGenTextures(1)
                gl.glBindTexture(gl.GL_TEXTURE_2D, self.media_texture_id)
                
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
                gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
                
                # Initialize with first frame
                gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, self.gif_width, self.gif_height,
                               0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, self.gif_frames[0])
                
                print(f"DEBUG: Created GIF texture {self.media_texture_id} for {self.name}")
                
            elif self.media_type == MediaType.VIDEO:
                print(f"DEBUG: Creating OpenGL texture for video {self.name}")
                try:
                    # Generate OpenGL texture for video
                    print(f"DEBUG: Generating OpenGL texture...")
                    self.media_texture_id = gl.glGenTextures(1)
                    print(f"DEBUG: Generated texture ID: {self.media_texture_id}")
                    
                    gl.glBindTexture(gl.GL_TEXTURE_2D, self.media_texture_id)
                    
                    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
                    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
                    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
                    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
                    
                    # Get first frame using FFmpeg to initialize texture
                    print(f"DEBUG: Getting first frame from video using FFmpeg...")
                    frame = self._get_video_frame(0)
                    
                    if frame is not None:
                        height, width = frame.shape[:2]
                        print(f"DEBUG: Frame dimensions: {width}x{height}")
                        
                        # Add alpha channel
                        print(f"DEBUG: Adding alpha channel...")
                        frame_rgba = np.dstack([frame, np.full((height, width), 255, dtype=np.uint8)])
                        
                        print(f"DEBUG: Creating OpenGL texture with frame data...")
                        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, width, height,
                                       0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, frame_rgba.tobytes())
                        
                        print(f"DEBUG: Created video texture {self.media_texture_id} for {self.name} ({width}x{height})")
                    else:
                        print(f"DEBUG: Failed to get first frame from video {self.name}")
                        return
                    
                    print(f"DEBUG: Successfully created video texture {self.media_texture_id} for {self.name}")
                except Exception as video_texture_error:
                    print(f"DEBUG: Exception creating video texture: {video_texture_error}")
                    import traceback
                    traceback.print_exc()
                    return
                
            gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
            
        except Exception as e:
            print(f"DEBUG: Failed to create OpenGL texture for {self.name}: {e}")
            import traceback
            traceback.print_exc()
    
    def update_media_texture(self):
        """Update the media texture with current frame/animation state."""
        # Initialize texture if not already done (deferred until OpenGL context is available)
        if not self.media_texture_id and (self.media_path or self.media_type == MediaType.WEB):
            print(f"DEBUG: Initializing deferred media texture for {self.name} (type: {self.media_type})")
            self._create_opengl_texture()
        
        if not self.media_texture_id:
            print(f"DEBUG: No media texture ID for {self.name}")
            return
        
        current_time = time.time()
        
        if self.media_type == MediaType.VIDEO and self.current_frame is not None:
            with self.frame_lock:
                frame = self.current_frame.copy()
            
            # Convert to RGBA
            if len(frame.shape) == 3 and frame.shape[2] == 3:
                height, width = frame.shape[:2]
                # Add alpha channel
                frame_rgba = np.dstack([frame, np.full((height, width), 255, dtype=np.uint8)])
            else:
                frame_rgba = frame
                height, width = frame.shape[:2]
            
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.media_texture_id)
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, width, height,
                           0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, frame_rgba.tobytes())
        
        elif self.media_type == MediaType.GIF and self.gif_frames:
            # Check if it's time to advance to next frame
            frame_duration = self.gif_frame_durations[self.gif_frame_index]
            if current_time - self.gif_last_frame_time >= frame_duration:
                old_index = self.gif_frame_index
                self.gif_frame_index = (self.gif_frame_index + 1) % len(self.gif_frames)
                self.gif_last_frame_time = current_time
                print(f"DEBUG: GIF frame advanced from {old_index} to {self.gif_frame_index}")
            
            # Update texture with current frame
            frame_data = self.gif_frames[self.gif_frame_index]
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.media_texture_id)
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, self.gif_width, self.gif_height,
                           0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, frame_data)
        
        elif self.media_type == MediaType.WEB and self.web_auto_refresh:
            # Check if it's time to refresh the website
            if current_time - self.web_last_refresh_time >= self.web_refresh_interval:
                print(f"DEBUG: Refreshing website: {self.web_url}")
                if self._capture_website_screenshot() and self.image_data:
                    # Update texture with new screenshot
                    gl.glBindTexture(gl.GL_TEXTURE_2D, self.media_texture_id)
                    gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, self.image_data.width, self.image_data.height, 
                                   0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, self.image_data.tobytes())
                    print(f"DEBUG: Website texture updated")
    
    def cleanup(self):
        """Clean up media resources."""
        self.stop_video_playback()
        
        # Clean up web driver
        if self.web_driver:
            try:
                self.web_driver.quit()
                print(f"DEBUG: Web driver closed for {self.name}")
            except Exception as e:
                print(f"DEBUG: Error closing web driver: {e}")
            self.web_driver = None
        
        # Clean up audio
        pygame.mixer.music.stop()
        if self.audio_channel:
            self.audio_channel.stop()
            self.audio_channel = None
        
        if self.audio_file and os.path.exists(self.audio_file):
            try:
                os.unlink(self.audio_file)
                print(f"DEBUG: Temporary audio file cleaned up")
            except Exception as e:
                print(f"DEBUG: Error cleaning up audio file: {e}")
            self.audio_file = None
        
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None
        
        if self.media_texture_id:
            gl.glDeleteTextures([self.media_texture_id])
            self.media_texture_id = None
    
    def to_dict(self):
        """Serialize media screen to dictionary."""
        data = super().to_dict()
        data.update({
            'media_type': self.media_type.value if self.media_type else None,
            'media_path': self.media_path
        })
        return data
    
    def from_dict(self, data: dict):
        """Deserialize media screen from dictionary."""
        super().from_dict(data)
        
        media_type_str = data.get('media_type')
        if media_type_str:
            self.media_type = MediaType(media_type_str)
        
        media_path = data.get('media_path')
        if media_path and os.path.exists(media_path):
            self.load_media(media_path)


class SphereRenderer:
    """Handles 3D sphere rendering with various grid systems."""
    
    def __init__(self):
        # Sphere properties
        self.radius = 1.0
        self.resolution = 32  # Number of subdivisions
        self.wireframe_resolution = 16  # Separate resolution for wireframe
        self.position = np.array([0.0, 0.0, 0.0])
        self.rotation = np.array([0.0, 0.0, 0.0])  # pitch, yaw, roll
        self.scale = np.array([1.0, 1.0, 1.0])
        
        # Visual properties
        self.sphere_color = np.array([0.2, 0.5, 1.0, 0.7])  # RGBA
        self.transparency = 0.7
        self.wireframe_mode = False
        self.lighting_enabled = True
        
        # Vector properties
        self.vector_enabled = True  # Set vector as visible by default
        self.vector_direction = np.array([1.0, 0.0, 0.0])  # Default: X-axis
        self.vector_length = 2.0  # Length relative to sphere radius
        self.vector_color = np.array([1.0, 0.0, 0.0, 1.0])  # Red RGBA
        self.vector_thickness = 3.0
        
        # Vector orientation properties
        self.vector_roll = 0.0  # Roll rotation around the vector axis (camera orientation)
        self.vector_orientation_enabled = False  # Show orientation vector at tail of main vector
        self.vector_orientation_length = 0.8  # Length of orientation vector relative to main vector
        self.vector_orientation_color = np.array([0.0, 1.0, 0.0, 1.0])  # Green RGBA
        self.vector_orientation_thickness = 2.0
        
        # Cone properties
        self.cone_enabled = False
        self.cone_length = 3.0  # Length relative to sphere radius
        self.cone_infinite = False  # Whether cone extends infinitely
        self.cone_angle = 30.0  # Cone half-angle in degrees
        self.cone_color = np.array([1.0, 1.0, 0.0, 0.3])  # Yellow with transparency
        self.cone_resolution = 16  # Number of sides for cone base
        
        # Pyramid properties
        self.pyramid_enabled = False
        self.pyramid_length = 3.0  # Length relative to sphere radius
        self.pyramid_infinite = False  # Whether pyramid extends infinitely
        self.pyramid_angle_horizontal = 25.0  # Horizontal half-angle in degrees
        self.pyramid_angle_vertical = 20.0  # Vertical half-angle in degrees
        self.pyramid_color = np.array([0.0, 1.0, 1.0, 0.3])  # Cyan with transparency
        
        # Cuboid properties
        self.cuboid_enabled = False
        self.cuboid_length = 2.0   # Along vector direction
        self.cuboid_infinite = False  # Whether cuboid extends infinitely
        self.cuboid_width = 1.0    # Perpendicular to vector
        self.cuboid_height = 0.8   # Perpendicular to vector and width
        self.cuboid_color = np.array([1.0, 0.5, 0.0, 0.3])  # Orange with transparency
        
        # Near plane properties (for truncating shapes)
        self.near_plane_enabled = False
        self.near_plane_distance = 0.5  # Distance from sphere center along vector (0 = at center, 1 = at sphere surface)
        
        # Sphere intersection properties (show where shapes intersect sphere surface)
        self.sphere_intersection_enabled = False
        self.sphere_intersection_color = np.array([1.0, 1.0, 0.0, 0.8])  # Bright yellow with some transparency
        
        # Normal ray properties (show surface normal vectors)
        self.normal_rays_enabled = False
        self.normal_rays_length = 0.5  # Length of normal rays relative to sphere radius
        self.normal_rays_density = 8   # Number of rays per latitude/longitude division
        self.normal_rays_color = np.array([0.0, 1.0, 1.0, 1.0])  # Cyan color
        self.normal_rays_thickness = 2.0
        
        # Intersection normal ray properties (show normals only on intersection surfaces)
        self.intersection_normals_enabled = False
        self.intersection_normals_length = 0.3  # Length of intersection normal rays
        self.intersection_normals_density = 12  # Higher density for intersection areas
        self.intersection_normals_color = np.array([1.0, 0.0, 1.0, 1.0])  # Magenta color
        self.intersection_normals_thickness = 2.5
        
        # Truncation normal ray properties (show normals on near plane cut surfaces)
        self.truncation_normals_enabled = False
        self.truncation_normals_length = 0.4  # Length of truncation normal rays
        self.truncation_normals_density = 8   # Density for truncation surfaces
        self.truncation_normals_color = np.array([1.0, 1.0, 1.0, 1.0])  # White color
        self.truncation_normals_thickness = 3.0
        
        # Grid properties
        self.active_grids = set()
        self.grid_colors = {
        GridType.LONGITUDE_LATITUDE: np.array([0.0, 1.0, 1.0, 1.0]),  # Cyan
        GridType.CONCENTRIC_CIRCLES: np.array([1.0, 0.0, 1.0, 1.0]),  # Magenta
        GridType.DOT_PARTICLES: np.array([0.0, 1.0, 0.0, 1.0]),       # Green
        GridType.NEON_LINES: np.array([0.0, 0.5, 1.0, 1.0]),          # Neon blue
        GridType.WIREFRAME: np.array([1.0, 1.0, 1.0, 1.0])            # White
        }
        
        # Grid parameters
        self.longitude_lines = 16
        self.latitude_lines = 12
        self.concentric_rings = 8
        self.dot_density = 200
        self.neon_intensity = 1.0
        
        # 2D Screen properties for ray tracing
        self.screen_enabled = False
        self.screen_width = 3.0  # Width in 3D space (bigger for better visibility)
        self.screen_height = 2.25  # Height in 3D space (bigger for better visibility)
        self.screen_position = np.array([0.0, 0.0, 4.0])  # Position in front of sphere
        self.screen_rotation = np.array([0.0, 0.0, 0.0])  # Screen facing -Z direction (toward camera)
        self.screen_resolution = (128, 96)  # Lower resolution for better performance
        self.screen_render_mode = "simple"  # Start with simple mode, can switch to "ray_tracing", "path_tracing", "pbr", "ray_marching"
        self.screen_camera_position = np.array([0.0, 0.0, 0.0])  # Virtual camera position (sphere center)
        self.screen_camera_target = np.array([1.0, 0.0, 1.0])  # Virtual camera target (toward red-orange-yellow-green-blue-purple cube)
        self.screen_samples = 1  # Lower samples for better performance
        self.screen_max_bounces = 1  # Fewer bounces for better performance
        self.screen_update_rate = 0.2  # Update every 0.2 seconds
        self.screen_last_update = 0.0
        self.screen_texture_id = None
        self.screen_texture_data = None
        self.screen_needs_update = True  # Force initial update
        
        # Geometry data
        self.vertices = []
        self.indices = []
        self.normals = []
        self.texture_coords = []
        
        # Shape and screen management
        self.shapes = {}  # Dictionary of shape_id -> Shape
        self.cameras = {}  # Dictionary of camera_id -> Camera
        self.screens = {}  # Dictionary of screen_id -> Screen
        
        # Create default main camera
        main_camera = Camera(camera_type=CameraType.MAIN)
        main_camera.name = "Main Camera"
        self.cameras[main_camera.id] = main_camera
        self.main_camera_id = main_camera.id
        
        # Create clean main camera (mirrors main camera but without overlays/screens)
        main_clean_camera = Camera(camera_type=CameraType.MAIN_CLEAN)
        main_clean_camera.name = "Main Camera (No Overlays)"
        self.cameras[main_clean_camera.id] = main_clean_camera
        self.main_clean_camera_id = main_clean_camera.id
        
        # Create sphere vector camera (follows sphere's vector direction)
        sphere_vector_camera = Camera(camera_type=CameraType.SPHERE_VECTOR)
        sphere_vector_camera.name = "Sphere Vector Camera"
        self.cameras[sphere_vector_camera.id] = sphere_vector_camera
        self.sphere_vector_camera_id = sphere_vector_camera.id
        
        # Reference to the original screen (will be set during initialization)
        self.original_screen_id = None
        
        # Generate initial geometry
        self.generate_sphere_geometry()
        self.generate_wireframe_geometry()
        
        # Initialize sphere vector camera position
        self.update_sphere_vector_camera()
        
        # Register the original 2D screen as a proper screen object
        self._register_original_2d_screen()
    
    def generate_sphere_geometry(self):
        """Generate sphere vertices, indices, and normals."""
        self.vertices = []
        self.indices = []
        self.normals = []
        self.texture_coords = []
        
        # Generate vertices
        for i in range(self.resolution + 1):
            lat = math.pi * (-0.5 + float(i) / self.resolution)
            sin_lat = math.sin(lat)
            cos_lat = math.cos(lat)
            
            for j in range(self.resolution + 1):
                lon = 2 * math.pi * float(j) / self.resolution
                sin_lon = math.sin(lon)
                cos_lon = math.cos(lon)
                
                # Vertex position
                x = cos_lat * cos_lon * self.radius
                y = sin_lat * self.radius
                z = cos_lat * sin_lon * self.radius
                
                self.vertices.extend([x, y, z])
                
                # Normal (same as normalized position for sphere)
                self.normals.extend([cos_lat * cos_lon, sin_lat, cos_lat * sin_lon])
                
                # Texture coordinates
                u = float(j) / self.resolution
                v = float(i) / self.resolution
                self.texture_coords.extend([u, v])
        
        # Generate indices for triangles
        for i in range(self.resolution):
            for j in range(self.resolution):
                first = i * (self.resolution + 1) + j
                second = first + self.resolution + 1
                
                # First triangle
                self.indices.extend([first, second, first + 1])
                # Second triangle
                self.indices.extend([second, second + 1, first + 1])
    
    def generate_wireframe_geometry(self):
        """Generate separate geometry for wireframe with adjustable density."""
        self.wireframe_vertices = []
        self.wireframe_indices = []
        
        # Generate vertices for wireframe
        for i in range(self.wireframe_resolution + 1):
            lat = math.pi * (-0.5 + float(i) / self.wireframe_resolution)
            sin_lat = math.sin(lat)
            cos_lat = math.cos(lat)
            
            for j in range(self.wireframe_resolution + 1):
                lon = 2 * math.pi * float(j) / self.wireframe_resolution
                sin_lon = math.sin(lon)
                cos_lon = math.cos(lon)
                
                # Vertex position
                x = cos_lat * cos_lon * self.radius
                y = sin_lat * self.radius
                z = cos_lat * sin_lon * self.radius
                
                self.wireframe_vertices.extend([x, y, z])
        
        # Generate indices for wireframe triangles
        for i in range(self.wireframe_resolution):
            for j in range(self.wireframe_resolution):
                first = i * (self.wireframe_resolution + 1) + j
                second = first + self.wireframe_resolution + 1
                
                # First triangle
                self.wireframe_indices.extend([first, second, first + 1])
                # Second triangle
                self.wireframe_indices.extend([second, second + 1, first + 
1])
    
    # ==================== RAY TRACING SYSTEM ====================
    
    def ray_sphere_intersection(self, ray_origin, ray_direction):
        """Calculate ray-sphere intersection. Returns (hit, distance, point, normal)."""
        # Sphere at origin with radius
        oc = ray_origin - self.position
        a = np.dot(ray_direction, ray_direction)
        b = 2.0 * np.dot(oc, ray_direction)
        c = np.dot(oc, oc) - self.radius * self.radius
        
        discriminant = b * b - 4 * a * c
        if discriminant < 0:
            return False, float('inf'), None, None
        
        # Get the closest intersection
        sqrt_discriminant = math.sqrt(discriminant)
        t1 = (-b - sqrt_discriminant) / (2.0 * a)
        t2 = (-b + sqrt_discriminant) / (2.0 * a)
        
        t = t1 if t1 > 0.001 else t2  # Use epsilon to avoid self-intersection
        if t <= 0.001:
            return False, float('inf'), None, None
        
        hit_point = ray_origin + t * ray_direction
        normal = (hit_point - self.position) / self.radius
        return True, t, hit_point, normal
    
    def ray_cone_intersection(self, ray_origin, ray_direction):
        """Calculate ray-cone intersection."""
        if not self.cone_enabled:
            return False, float('inf'), None, None
        
        # Simplified cone intersection (infinite cone from origin)
        direction = self.vector_direction / np.linalg.norm(self.vector_direction)
        cone_angle_rad = math.radians(self.cone_angle)
        cos_angle = math.cos(cone_angle_rad)
        cos_angle_sq = cos_angle * cos_angle
        
        # Transform ray to cone space (cone axis along Z)
        # For simplicity, assume cone along positive vector direction
        oc = ray_origin
        
        # Cone equation: (x² + y²) = (z * tan(angle))²
        # This is a simplified implementation
        a = ray_direction[0] * ray_direction[0] + ray_direction[1] * ray_direction[1] - \
            (ray_direction[2] * ray_direction[2]) * (1 - cos_angle_sq) / cos_angle_sq
        b = 2.0 * (oc[0] * ray_direction[0] + oc[1] * ray_direction[1] - \
                   (oc[2] * ray_direction[2]) * (1 - cos_angle_sq) / cos_angle_sq)
        c = oc[0] * oc[0] + oc[1] * oc[1] - (oc[2] * oc[2]) * (1 - cos_angle_sq) / cos_angle_sq
        
        discriminant = b * b - 4 * a * c
        if discriminant < 0:
            return False, float('inf'), None, None
        
        sqrt_discriminant = math.sqrt(discriminant)
        t1 = (-b - sqrt_discriminant) / (2.0 * a)
        t2 = (-b + sqrt_discriminant) / (2.0 * a)
        
        t = t1 if t1 > 0.001 else t2
        if t <= 0.001:
            return False, float('inf'), None, None
        
        hit_point = ray_origin + t * ray_direction
        
        # Check if hit is within cone bounds (if not infinite)
        if not self.cone_infinite:
            dist_along_axis = np.dot(hit_point, direction)
            # Use fixed base radius so cone size is independent of sphere scale
            base_radius = 1.0
            if dist_along_axis < 0 or dist_along_axis > self.cone_length * base_radius:
                return False, float('inf'), None, None
        
        # Calculate normal (simplified)
        normal = np.array([hit_point[0], hit_point[1], 0.0])
        if np.linalg.norm(normal) > 0:
            normal = normal / np.linalg.norm(normal)
        
        return True, t, hit_point, normal
    
    def ray_box_intersection(self, ray_origin, ray_direction, box_center, box_size):
        """Check ray intersection with an axis-aligned box using proper slab method."""
        # Calculate box bounds (slab method)
        box_min = box_center - box_size
        box_max = box_center + box_size
        
        # Debug flag - enable detailed debugging for specific rays
        debug_this_ray = False
        if np.allclose(ray_origin, [0, 0, 0], atol=0.01) and np.allclose(box_center, [2, 0, 2], atol=0.01):
            ray_dir_norm = ray_direction / np.linalg.norm(ray_direction)
            ideal_dir = np.array([0.707, 0, 0.707])
            if np.dot(ray_dir_norm, ideal_dir) > 0.9:
                debug_this_ray = True
                print(f"DEBUG RAY-BOX INTERSECTION:")
                print(f"  - Ray origin: {ray_origin}")
                print(f"  - Ray direction: {ray_direction}")
                print(f"  - Box center: {box_center}")
                print(f"  - Box size: {box_size}")
                print(f"  - Box min: {box_min}")
                print(f"  - Box max: {box_max}")
        
        # Handle near-zero direction components
        ray_dir = np.where(np.abs(ray_direction) < 1e-8, 
                          np.sign(ray_direction) * 1e-8, 
                          ray_direction)
        
        if debug_this_ray:
            print(f"  - Adjusted ray dir: {ray_dir}")
        
        # Calculate t values for each slab
        t1 = (box_min - ray_origin) / ray_dir
        t2 = (box_max - ray_origin) / ray_dir
        
        if debug_this_ray:
            print(f"  - t1 (to box_min): {t1}")
            print(f"  - t2 (to box_max): {t2}")
        
        # Ensure t1 <= t2 for each dimension
        t_min_vals = np.minimum(t1, t2)
        t_max_vals = np.maximum(t1, t2)
        
        if debug_this_ray:
            print(f"  - t_min_vals: {t_min_vals}")
            print(f"  - t_max_vals: {t_max_vals}")
        
        # Find the intersection interval
        t_near = np.max(t_min_vals)
        t_far = np.min(t_max_vals)
        
        if debug_this_ray:
            print(f"  - t_near: {t_near}")
            print(f"  - t_far: {t_far}")
            print(f"  - t_near > t_far? {t_near > t_far}")
            print(f"  - t_far < 0? {t_far < 0}")
        
        # Check for intersection
        if t_near > t_far:
            if debug_this_ray:
                print(f"  - FAIL: t_near > t_far")
            return False, 0, None, None
        
        # We want the closest positive intersection
        if t_far < 0:
            if debug_this_ray:
                print(f"  - FAIL: t_far < 0 (ray pointing away)")
            return False, 0, None, None
        
        # Choose the intersection point
        t = t_near if t_near > 0 else t_far
        
        if debug_this_ray:
            print(f"  - Chosen t: {t}")
        
        # Calculate hit point
        hit_point = ray_origin + t * ray_direction
        
        if debug_this_ray:
            print(f"  - Hit point: {hit_point}")
            print(f"  - SUCCESS: Ray hits box!")
        
        # Calculate normal - find which face was hit
        # Check which axis the hit point is closest to the box boundary
        rel_pos = hit_point - box_center
        
        # Determine which face by finding the component closest to the box boundary
        normalized_pos = rel_pos / box_size
        abs_normalized = np.abs(normalized_pos)
        max_component = np.argmax(abs_normalized)
        
        normal = np.zeros(3)
        normal[max_component] = 1.0 if rel_pos[max_component] > 0 else -1.0
        
        return True, t, hit_point, normal
    
    def ray_rotated_box_intersection(self, ray_origin, ray_direction, box_center, box_size, rotation_degrees):
        """Check ray intersection with a rotated box by transforming ray to box's local space."""
        import math
        
        # Debug: Check if we have any rotation
        has_rotation = np.any(np.abs(rotation_degrees) > 0.1)
        if has_rotation:
            print(f"DEBUG: ray_rotated_box_intersection called with rotation: {rotation_degrees}")
            print(f"DEBUG: Box center: {box_center}, Box size: {box_size}")
            print(f"DEBUG: Ray origin: {ray_origin}, Ray direction: {ray_direction}")
        
        # Convert rotation from degrees to radians
        rotation_rad = np.radians(rotation_degrees)
        
        # Create rotation matrices to match OpenGL's glRotatef order: X, Y, Z
        # Use positive angles (no negation) to match OpenGL behavior
        cos_x, sin_x = math.cos(rotation_rad[0]), math.sin(rotation_rad[0])
        cos_y, sin_y = math.cos(rotation_rad[1]), math.sin(rotation_rad[1])
        cos_z, sin_z = math.cos(rotation_rad[2]), math.sin(rotation_rad[2])
        
        # Rotation matrix X (pitch) - matches glRotatef(angle, 1, 0, 0)
        R_x = np.array([
            [1, 0, 0],
            [0, cos_x, -sin_x],
            [0, sin_x, cos_x]
        ])
        
        # Rotation matrix Y (yaw) - matches glRotatef(angle, 0, 1, 0)
        R_y = np.array([
            [cos_y, 0, sin_y],
            [0, 1, 0],
            [-sin_y, 0, cos_y]
        ])
        
        # Rotation matrix Z (roll) - matches glRotatef(angle, 0, 0, 1)
        R_z = np.array([
            [cos_z, -sin_z, 0],
            [sin_z, cos_z, 0],
            [0, 0, 1]
        ])
        
        # Combined rotation matrix - apply in same order as OpenGL: X, then Y, then Z
        R_forward = R_z @ R_y @ R_x  # Forward transformation (local to world)
        R_inverse = R_forward.T      # Inverse transformation (world to local)
        
        # Transform ray to box's local coordinate system (world to local)
        local_ray_origin = R_inverse @ (ray_origin - box_center)
        local_ray_direction = R_inverse @ ray_direction
        
        # Test intersection with axis-aligned box in local space
        hit, t, local_hit_point, local_normal = self.ray_box_intersection(
            local_ray_origin, local_ray_direction, np.array([0, 0, 0]), box_size
        )
        
        if hit:
            # Transform hit point and normal back to world space (local to world)
            world_hit_point = R_forward @ local_hit_point + box_center
            world_normal = R_forward @ local_normal
            
            if has_rotation:
                print(f"DEBUG: ✅ ROTATED BOX HIT!")
                print(f"DEBUG: Hit at local: {local_hit_point}, world: {world_hit_point}")
                print(f"DEBUG: Normal local: {local_normal}, world: {world_normal}")
                # Test color selection with this normal
                test_color = self.get_cube_face_color(world_normal)
                print(f"DEBUG: Color for this normal: {test_color}")
            
            return True, t, world_hit_point, world_normal
        
        if has_rotation:
            print(f"DEBUG: ❌ ROTATED BOX MISS - no intersection found")
        
        return False, float('inf'), None, None
    
    def get_cube_face_color(self, normal):
        """Get the color for a cube face based on its normal vector."""
        # Normalize the normal vector to ensure it's unit length
        normal = normal / np.linalg.norm(normal)
        
        # Use a larger tolerance for rotated cubes and find the closest face
        tolerance = 0.1
        
        # Define face normals and colors
        face_data = [
            ([0, 0, 1],   [1.0, 0.0, 0.0]),    # Front face (+Z) - RED
            ([0, 0, -1],  [0.0, 0.0, 1.0]),    # Back face (-Z) - BLUE  
            ([0, 1, 0],   [0.0, 1.0, 0.0]),    # Top face (+Y) - GREEN
            ([0, -1, 0],  [1.0, 1.0, 0.0]),    # Bottom face (-Y) - YELLOW
            ([1, 0, 0],   [1.0, 0.5, 0.0]),    # Right face (+X) - ORANGE
            ([-1, 0, 0],  [0.5, 0.0, 1.0])     # Left face (-X) - PURPLE
        ]
        
        # Find the face with the most similar normal (highest dot product)
        best_match = None
        best_dot = -1.0
        
        for face_normal, face_color in face_data:
            face_normal = np.array(face_normal)
            dot_product = np.dot(normal, face_normal)
            if dot_product > best_dot:
                best_dot = dot_product
                best_match = face_color
        
        # Debug output for face color selection
        if best_dot < 0.99:  # Show debug for any non-perfect match
            face_names = ["Front(+Z)", "Back(-Z)", "Top(+Y)", 
"Bottom(-Y)", "Right(+X)", "Left(-X)"]
            colors = ["RED", "BLUE", "GREEN", "YELLOW", "ORANGE", 
"PURPLE"]
            best_face_idx = -1
            for i, (face_normal, face_color) in enumerate(face_data):
                if np.array_equal(face_color, best_match):
                    best_face_idx = i
                    break
            face_name = face_names[best_face_idx] if best_face_idx >= 0 else "UNKNOWN"
            color_name = colors[best_face_idx] if best_face_idx >= 0 else "UNKNOWN"
            print(f"DEBUG: Face {face_name} detected, color {color_name}, normal={normal}, dot={best_dot:.3f}")
        
        return np.array(best_match) if best_match is not None else np.array([1.0, 0.0, 0.0])
    
    def trace_ray(self, ray_origin, ray_direction, depth=0):
        """Trace a ray through the scene and return color."""
        if depth > self.screen_max_bounces:
            return np.array([0.0, 0.0, 0.0])  # Black
        
        closest_t = float('inf')
        closest_hit = None
        closest_normal = None
        closest_material = None
        
        # Test sphere intersection - DISABLED for ray tracing (camera is inside sphere)
        # hit, t, hit_point, normal = self.ray_sphere_intersection(ray_origin, ray_direction)
        # if hit and t < closest_t:
        #     closest_t = t
        #     closest_hit = hit_point
        #     closest_normal = normal
        #     closest_material = "sphere"
        
        # Test cone intersection - DISABLED for ray tracing (camera is inside cone at origin)
        # if self.cone_enabled:
        #     hit, t, hit_point, normal = self.ray_cone_intersection(ray_origin, ray_direction)
        #     if hit and t < closest_t:
        #         closest_t = t
        #         closest_hit = hit_point
        #         closest_normal = normal
        #         closest_material = "cone"
        
        # Test red cube intersection - match simple mode size, position AND rotation
        if hasattr(self, '_canvas_ref') and self._canvas_ref and hasattr(self._canvas_ref, 'rainbow_cube_position'):
            rainbow_cube_pos = self._canvas_ref.rainbow_cube_position.copy()
        else:
            rainbow_cube_pos = np.array([2.0, 0.0, 2.0])  # Fallback position
        # Use the same size as simple mode to ensure visual consistency
        if hasattr(self, '_canvas_ref') and self._canvas_ref and hasattr(self._canvas_ref, 'rainbow_cube_size'):
            cube_size = self._canvas_ref.rainbow_cube_size
            rainbow_cube_size = np.array([cube_size, cube_size, cube_size])
        else:
            rainbow_cube_size = np.array([0.3, 0.3, 0.3])  # Fallback to match simple mode default
        
        # Get cube rotation to match simple mode rendering
        if hasattr(self, '_canvas_ref') and self._canvas_ref and hasattr(self._canvas_ref, 'object_rotations'):
            cube_rotation = self._canvas_ref.object_rotations.get("cube", np.array([0.0, 0.0, 0.0]))
        else:
            cube_rotation = np.array([0.0, 0.0, 0.0])
        
        # Debug cube rotation and render mode
        if depth == 0:  # Only print for primary rays
            print(f"DEBUG: ===== CUBE ROTATION DEBUG =====")
            print(f"DEBUG: Cube rotation from canvas: {cube_rotation}")
            if hasattr(self, '_canvas_ref') and self._canvas_ref:
                canvas_cube_rot = self._canvas_ref.object_rotations.get("cube", "NOT_FOUND")
                print(f"DEBUG: Canvas object_rotations['cube']: {canvas_cube_rot}")
            
            if np.any(np.abs(cube_rotation) > 0.1):  # Only print if there's significant rotation
                print(f"DEBUG: ⚠️ SIGNIFICANT CUBE ROTATION DETECTED: [{cube_rotation[0]:.1f}°, {cube_rotation[1]:.1f}°, {cube_rotation[2]:.1f}°]")
                print(f"DEBUG: Will use rotated box intersection method")
            else:
                print(f"DEBUG: No significant rotation, will use standard box intersection")
            print(f"DEBUG: =====================================")
            
            # Also debug render mode to make sure we're in ray tracing
            print(f"DEBUG: Sphere render mode: '{self.screen_render_mode}', Canvas render mode:'{getattr(self._canvas_ref, 'screen_render_mode', 'unknown') if self._canvas_ref else 'no_canvas'}')")
        
        # Apply rotation to ray intersection (transform ray to cube's local space)
        hit, t, hit_point, normal = self.ray_rotated_box_intersection(ray_origin, ray_direction, rainbow_cube_pos, rainbow_cube_size, cube_rotation)
        
        # Debug red cube intersection - more detailed
        if depth == 0:  # Only print for primary rays to avoid spam
            ray_dir_normalized = ray_direction / np.linalg.norm(ray_direction)
            cube_direction = rainbow_cube_pos / np.linalg.norm(rainbow_cube_pos)
            dot_to_cube = np.dot(ray_dir_normalized, cube_direction)
            
            # Test if we're close to the ideal ray that should hit dead center
            ideal_ray = rainbow_cube_pos / np.linalg.norm(rainbow_cube_pos)  # (0.707, 0, 0.707)
            dot_to_ideal = np.dot(ray_dir_normalized, ideal_ray)
            
            if dot_to_ideal > 0.95:  # Close to ideal ray (lowered threshold)
                print(f"DEBUG IDEAL Ray-Cube Test: origin={ray_origin}")
                print(f"  - Ray dir: {ray_direction}")
                print(f"  - Ray normalized: {ray_dir_normalized}")
                print(f"  - Ideal direction: {ideal_ray}")
                print(f"  - Dot with ideal: {dot_to_ideal:.6f}")
                print(f"  - Hit: {hit}, t: {t:.3f}")
                if hit:
                    print(f"  - Hit point: {hit_point}")
                    print(f"  - Normal: {normal}")
                else:
                    print(f"  - NO HIT - debugging intersection...")
                    # Debug the intersection calculation step by step
                    box_min = rainbow_cube_pos - rainbow_cube_size
                    box_max = rainbow_cube_pos + rainbow_cube_size
                    print(f"  - Box bounds: min={box_min}, max={box_max}")
                    
                    # Test if ray passes through the box bounds
                    ray_end = ray_origin + ray_direction * 10.0  # Extend ray
                    print(f"  - Ray extended to: {ray_end}")
                    
                print(f"  - Cube bounds: [{rainbow_cube_pos - rainbow_cube_size}] to [{rainbow_cube_pos + rainbow_cube_size}]")
        
            if hit and t < closest_t:
                closest_t = t
                closest_hit = hit_point
                closest_normal = normal
            closest_material = "rainbow_cube"
        
        # No intersection - return background color (match main 3D scene)
        if closest_hit is None:
            # Match the main 3D scene background: gl.glClearColor(0.1, 0.1, 0.1, 1.0)
            bg_color = np.array([0.1, 0.1, 0.1])
            
            # Debug background rays occasionally
            if depth == 0 and abs(ray_direction[0] - 0.707) < 0.01 and abs(ray_direction[2] - 0.707) < 0.01:
                print(f"DEBUG BACKGROUND: ray={ray_direction}, color={bg_color}")
            
            return bg_color
        
        # Calculate lighting
        light_dir = np.array([1.0, 1.0, 1.0])  # Light direction
        light_dir = light_dir / np.linalg.norm(light_dir)
        
        # Diffuse lighting
        diffuse = max(0.0, np.dot(closest_normal, light_dir))
        
        # Material colors
        if closest_material == "sphere":
            base_color = self.sphere_color[:3]
        elif closest_material == "cone":
            base_color = self.cone_color[:3]
        elif closest_material == "rainbow_cube":
            base_color = self.get_cube_face_color(closest_normal)  # Multicolored cube faces
        else:
            base_color = np.array([0.8, 0.8, 0.8])
        
        # Simple lighting model
        ambient = 0.3
        color = base_color * (ambient + diffuse * 0.7)
        
        # Debug color calculation (reduced spam)
        if depth == 0 and closest_material == "rainbow_cube" and np.random.random() < 0.01:  # Only 1% of hits
            print(f"DEBUG RED CUBE HIT!")
            print(f"  - Material: {closest_material}")
            print(f"  - Base color: {base_color}")
            print(f"  - Diffuse: {diffuse:.3f}")
            print(f"  - Final color: {color}")
            print(f"  - Hit point: {closest_hit}")
        
        # Debug if we're getting white colors from non-background sources
        if depth == 0 and np.all(color > 0.9):
            print(f"DEBUG WHITE HIT: material={closest_material}, color={color}, base={base_color}")
        
        # Reflection (simplified)
        if depth < self.screen_max_bounces and self.screen_render_mode in ["path_tracing", "pbr"]:
            reflect_dir = ray_direction - 2.0 * np.dot(ray_direction, closest_normal) * closest_normal
            reflect_color = self.trace_ray(closest_hit + 0.001 * closest_normal, reflect_dir, depth + 1)
            color = 0.7 * color + 0.3 * reflect_color
        
        return np.clip(color, 0.0, 1.0)
    
    # ==================== RAY MARCHING (SDF) SYSTEM ====================
    
    def sdf_sphere(self, point, center, radius):
        """Signed distance function for a sphere."""
        return np.linalg.norm(point - center) - radius
    
    def sdf_box(self, point, center, size):
        """Signed distance function for a box."""
        q = np.abs(point - center) - size
        return np.linalg.norm(np.maximum(q, 0.0)) + min(max(q[0], max(q[1], q[2])), 0.0)
    
    def sdf_cone(self, point, tip, axis, angle, height):
        """Signed distance function for a cone."""
        # Transform point to cone space
        local_point = point - tip
        
        # Project onto cone axis
        axis_projection = np.dot(local_point, axis)
        
        # If outside height range, return distance to caps
        if axis_projection < 0:
            return np.linalg.norm(local_point)
        if axis_projection > height:
            return np.linalg.norm(local_point - axis * height)
        
        # Distance from axis
        radial_vec = local_point - axis * axis_projection
        radial_dist = np.linalg.norm(radial_vec)
        
        # Cone radius at this height
        cone_radius = axis_projection * math.tan(angle)
        
        return radial_dist - cone_radius
    
    def sdf_pyramid(self, point, tip, axis, width, height, length):
        """Signed distance function for a 4-sided pyramid."""
        # Simplified pyramid SDF - treat as scaled box for now
        local_point = point - tip
        axis_projection = np.dot(local_point, axis)
        
        if axis_projection < 0:
            return np.linalg.norm(local_point)
        if axis_projection > length:
            return np.linalg.norm(local_point - axis * length)
        
        # Create a tapered box
        scale = axis_projection / length
        box_size = np.array([width * scale / 2, height * scale / 2, 0.1])
        
        # Get perpendicular vectors (simplified)
        perp1 = np.array([1.0, 0.0, 0.0]) if abs(axis[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
        perp2 = np.cross(axis, perp1)
        perp1 = np.cross(perp2, axis)
        
        # Transform to local box space
        radial_vec = local_point - axis * axis_projection
        local_x = np.dot(radial_vec, perp1)
        local_y = np.dot(radial_vec, perp2)
        local_box_point = np.array([local_x, local_y, 0.0])
        
        return self.sdf_box(local_box_point, np.array([0.0, 0.0, 0.0]), box_size)
    
    def scene_sdf(self, point):
        """Combined SDF for the entire scene."""
        min_dist = float('inf')
        closest_material = "background"
        
        # Sphere SDF - DISABLED for ray tracing (camera is inside sphere)
        # sphere_dist = self.sdf_sphere(point, self.position, self.radius)
        # if sphere_dist < min_dist:
        #     min_dist = sphere_dist
        #     closest_material = "sphere"
        
        # Cone SDF - DISABLED for ray tracing (camera is inside cone at origin)
        # if self.cone_enabled:
        #     direction = self.vector_direction / np.linalg.norm(self.vector_direction)
        #     cone_angle_rad = math.radians(self.cone_angle)
        #     cone_height = self.cone_length * self.radius if not self.cone_infinite else 1000.0
        #     cone_dist = self.sdf_cone(point, np.array([0.0, 0.0, 0.0]), direction, cone_angle_rad, cone_height)
        #     if cone_dist < min_dist:
        #         min_dist = cone_dist
        #         closest_material = "cone"
        
        # Pyramid SDF - DISABLED for ray tracing (camera is inside pyramid at origin)
        # if self.pyramid_enabled:
        #     direction = self.vector_direction / np.linalg.norm(self.vector_direction)
        #     pyramid_length = self.pyramid_length * self.radius if not self.pyramid_infinite else 1000.0
        #     pyramid_width = pyramid_length * math.tan(math.radians(self.pyramid_angle_horizontal))
        #     pyramid_height = pyramid_length * math.tan(math.radians(self.pyramid_angle_vertical))
        #     pyramid_dist = self.sdf_pyramid(point, np.array([0.0, 0.0, 0.0]), direction, 
        #                                   pyramid_width, pyramid_height, pyramid_length)
        #     if pyramid_dist < min_dist:
        #         min_dist = pyramid_dist
        #         closest_material = "pyramid"
        
        # Cuboid SDF - DISABLED for ray tracing (camera is inside cuboid area)
        # if self.cuboid_enabled:
        #     direction = self.vector_direction / np.linalg.norm(self.vector_direction)
        #     
        #     # Calculate cuboid center and size
        #     if self.cuboid_infinite:
        #         # For infinite cuboid, make it very long
        #         cuboid_length = 1000.0
        #     else:
        #         cuboid_length = self.cuboid_length * self.radius
        #     
        #     cuboid_center = direction * (cuboid_length / 2.0)
        #     cuboid_size = np.array([
        #         cuboid_length / 2.0,
        #         self.cuboid_width * self.radius / 2.0,
        #         self.cuboid_height * self.radius / 2.0
        #     ])
        #     
        #     # Transform point to cuboid local space (simplified - assumes axis-aligned)
        #     cuboid_dist = self.sdf_box(point, cuboid_center, cuboid_size)
        #     if cuboid_dist < min_dist:
        #         min_dist = cuboid_dist
        #         closest_material = "cuboid"
        
        # Add the red cube to the ray tracing scene - match simple mode size and position
        if hasattr(self, '_canvas_ref') and self._canvas_ref and hasattr(self._canvas_ref, 'rainbow_cube_position'):
            rainbow_cube_pos = self._canvas_ref.rainbow_cube_position.copy()
        else:
            rainbow_cube_pos = np.array([2.0, 0.0, 2.0])  # Fallback position
        # Use the same size as simple mode to ensure visual consistency
        if hasattr(self, '_canvas_ref') and self._canvas_ref and hasattr(self._canvas_ref, 'rainbow_cube_size'):
            cube_size = self._canvas_ref.rainbow_cube_size
            rainbow_cube_size = np.array([cube_size, cube_size, cube_size])
        else:
            rainbow_cube_size = np.array([0.3, 0.3, 0.3])  # Fallback to match simple mode default
        
        rainbow_cube_dist = self.sdf_box(point, rainbow_cube_pos, rainbow_cube_size)
        if rainbow_cube_dist < min_dist:
            min_dist = rainbow_cube_dist
            closest_material = "rainbow_cube"
        
        return min_dist, closest_material
    
    def calculate_normal_sdf(self, point, epsilon=0.001):
        """Calculate normal using SDF gradient."""
        grad_x = self.scene_sdf(point + np.array([epsilon, 0.0, 0.0]))[0] - self.scene_sdf(point - np.array([epsilon, 0.0, 0.0]))[0]
        grad_y = self.scene_sdf(point + np.array([0.0, epsilon, 0.0]))[0] - self.scene_sdf(point - np.array([0.0, epsilon, 0.0]))[0]
        grad_z = self.scene_sdf(point + np.array([0.0, 0.0, epsilon]))[0] - self.scene_sdf(point - np.array([0.0, 0.0, epsilon]))[0]
        
        normal = np.array([grad_x, grad_y, grad_z])
        norm = np.linalg.norm(normal)
        return normal / norm if norm > 0 else np.array([0.0, 1.0, 0.0])
    
    def ray_march(self, ray_origin, ray_direction, max_steps=64, max_distance=20.0, epsilon=0.001):
        """Ray marching using signed distance functions."""
        total_distance = 0.0
        
        for step in range(max_steps):
            current_point = ray_origin + ray_direction * total_distance
            
            distance, material = self.scene_sdf(current_point)
            
            # Hit surface
            if distance < epsilon:
                normal = self.calculate_normal_sdf(current_point, epsilon)
                return True, total_distance, current_point, normal, material
            
            # Ray escaped
            if total_distance > max_distance:
                break
            
            # March forward
            total_distance += distance
        
        return False, float('inf'), None, None, "background"
    
    def trace_ray_marching(self, ray_origin, ray_direction, depth=0):
        """Ray marching version of ray tracing."""
        if depth > self.screen_max_bounces:
            return np.array([0.0, 0.0, 0.0])  # Black
        
        hit, distance, hit_point, normal, material = self.ray_march(ray_origin, ray_direction)
        
        # No intersection - return background color (match main 3D scene)
        if not hit:
            # Match the main 3D scene background: gl.glClearColor(0.1, 0.1, 0.1, 1.0)
            return np.array([0.1, 0.1, 0.1])
        
        # Calculate lighting
        light_dir = np.array([1.0, 1.0, 1.0])  # Light direction
        light_dir = light_dir / np.linalg.norm(light_dir)
        
        # Diffuse lighting
        diffuse = max(0.0, np.dot(normal, light_dir))
        
        # Material colors
        if material == "sphere":
            base_color = self.sphere_color[:3]
        elif material == "cone":
            base_color = self.cone_color[:3]
        elif material == "pyramid":
            base_color = self.pyramid_color[:3]
        elif material == "cuboid":
            base_color = self.cuboid_color[:3]
        elif material == "rainbow_cube":
            base_color = self.get_cube_face_color(normal)  # Multicolored cube faces
        else:
            base_color = np.array([0.8, 0.8, 0.8])
        
        # Enhanced lighting model for ray marching
        ambient = 0.2
        specular_strength = 0.3
        
        # Specular highlight
        view_dir = -ray_direction
        reflect_dir = 2.0 * np.dot(normal, light_dir) * normal - light_dir
        specular = specular_strength * pow(max(0.0, np.dot(view_dir, reflect_dir)), 32)
        
        color = base_color * (ambient + diffuse * 0.7) + np.array([1.0, 1.0, 1.0]) * specular
        
        # Reflection for ray marching
        if depth < self.screen_max_bounces:
            reflect_dir = ray_direction - 2.0 * np.dot(ray_direction, normal) * normal
            reflect_color = self.trace_ray_marching(hit_point + 0.01 * normal, reflect_dir, depth + 1)
            color = 0.8 * color + 0.2 * reflect_color
        
        return np.clip(color, 0.0, 1.0)
    
    # ==================== END RAY MARCHING SYSTEM ====================
    
    def render_screen_texture(self):
        """Generate ray-traced image for the 2D screen (optimized)."""
        if not self.screen_enabled:
            return
        
        print(f"DEBUG: Rendering ray tracing screen texture, mode: {self.screen_render_mode}")
        print(f"DEBUG: Screen resolution: {self.screen_resolution}x{self.screen_resolution}")
        
        current_time = time.time()
        # Always update if screen_needs_update is True (user interaction)
        if not self.screen_needs_update and current_time - self.screen_last_update < self.screen_update_rate:
            return  # Don't update too frequently for automatic updates only
        
        self.screen_last_update = current_time
        self.screen_needs_update = False
        
        width, height = self.screen_resolution
        
        # Fast mode: Use even lower resolution for real-time updates
        # Check both sphere and canvas render modes for ray tracing
        is_ray_tracing = (self.screen_render_mode == "ray_tracing" or 
                         (hasattr(self, '_canvas_ref') and self._canvas_ref and 
                          getattr(self._canvas_ref, 'screen_render_mode', '') == "raytracing"))
        
        if is_ray_tracing:
            render_width = width // 2  # Quarter resolution for speed
            render_height = height // 2
        else:
            render_width = width // 4  # Even lower for path tracing
            render_height = height // 4
        
        image_data = np.zeros((render_height, render_width, 3), dtype=np.uint8)
        
        # Set up virtual camera - match simple mode camera setup exactly
        camera_pos = self.position.copy()  # Actual sphere center
        
        # Use EXACT SAME camera setup as simple mode
        if hasattr(self, '_canvas_ref') and self._canvas_ref and hasattr(self._canvas_ref, 'view_vector'):
            view_dir = self._canvas_ref.view_vector.copy()  # Same as simple mode
            print(f"DEBUG: Using canvas view_vector: {view_dir}")
        else:
            # Fallback: use sphere's vector direction
            view_dir = self.vector_direction / np.linalg.norm(self.vector_direction)
            print(f"DEBUG: Using sphere vector_direction (fallback): {view_dir}")
        
        print(f"DEBUG: ===== RAY TRACING CAMERA SETUP (MATCHING SIMPLE MODE) =====")
        print(f"DEBUG: Camera position (sphere center): {camera_pos}")
        print(f"DEBUG: View direction: {view_dir}")
        
        # Check if camera is pointing toward red cube (for debugging)
        cube_pos = np.array([2.0, 0.0, 2.0])
        cube_dir = cube_pos - camera_pos
        cube_dir = cube_dir / np.linalg.norm(cube_dir)
        dot_product = np.dot(view_dir, cube_dir)
        angle_to_cube = math.degrees(math.acos(np.clip(dot_product, -1.0, 1.0)))
        print(f"DEBUG: Direction to cube: {cube_dir}")
        print(f"DEBUG: Angle to cube: {angle_to_cube:.1f}° (should be close to 0°)")
        print(f"DEBUG: Are we looking toward cube? {angle_to_cube < 30}")
        
        # Compare with simple mode
        print(f"DEBUG: Ray tracing should match simple mode exactly")
        print(f"DEBUG: Both should show view from sphere toward cube")
        
        # EXACT SAME camera coordinate system as simple mode
        world_up = np.array([0.0, 1.0, 0.0])
        right = np.cross(view_dir, world_up)  # EXACT SAME as simple mode
        if np.linalg.norm(right) < 0.001:
            right = np.array([1.0, 0.0, 0.0])
        right = right / np.linalg.norm(right)
        up = np.cross(right, view_dir)  # EXACT SAME as simple mode
        up = -up / np.linalg.norm(up)  # Negate up vector to match simple mode fix
        
        # EXACT SAME roll rotation as simple mode
        roll_angle = math.radians(self.vector_roll if hasattr(self, 'vector_roll') else 0.0)
        cos_roll = math.cos(roll_angle)
        sin_roll = math.sin(roll_angle)
        
        # EXACT SAME 2D rotation as simple mode
        new_right = cos_roll * right + sin_roll * up
        new_up = -sin_roll * right + cos_roll * up
        
        right = new_right / np.linalg.norm(new_right)
        up = new_up / np.linalg.norm(new_up)
        
        # Apply the same up vector flip as simple mode to match exactly
        up = -up  # Match simple mode's flipped_up = -up
        
        # For ray tracing: camera_dir is the view direction
        camera_dir = view_dir
        
        print(f"DEBUG: Final camera vectors (should match simple mode):")
        print(f"  - camera_dir: {camera_dir}")
        print(f"  - up: {up}")
        print(f"  - right: {right}")
        print(f"  - roll_angle: {math.degrees(roll_angle):.1f}°")
        
        # Verify vectors are orthogonal and properly oriented
        print(f"DEBUG: Vector orthogonality check:")
        print(f"  - camera·up: {np.dot(camera_dir, up):.6f} (should be ~0)")
        print(f"  - camera·right: {np.dot(camera_dir, right):.6f} (should be ~0)")
        print(f"  - up·right: {np.dot(up, right):.6f} (should be ~0)")
        
        # Check if vectors are pointing in expected directions
        print(f"DEBUG: Vector direction check:")
        print(f"  - right should be perpendicular to camera and roughly horizontal")
        print(f"  - up should be perpendicular to camera and roughly vertical")
        print(f"  - Expected camera direction toward cube: [0.707, 0, 0.707]")
        print(f"  - Actual camera direction: {camera_dir}")
        print(f"  - Match? {np.allclose(camera_dir, [0.707, 0, 0.707], atol=0.1)}")
        
        
        # Screen plane - match 2D screen projection mode
        if hasattr(self, '_canvas_ref') and self._canvas_ref and self._canvas_ref.screen_projection == "orthographic":
            # Orthographic projection for 2D screen - rays are parallel
            print(f"DEBUG: Using orthographic ray tracing for 2D screen")
            # Calculate orthographic bounds based on distance and FOV (match simple mode)
            fov = self.cone_angle * 2.0
            aspect_ratio = render_width / render_height
            distance_to_target = 10.0  # Same distance as simple mode look_at calculation
            half_height = distance_to_target * math.tan(math.radians(fov) / 2.0)
            half_width = half_height * aspect_ratio
            is_orthographic = True
        else:
            # Perspective projection for 2D screen - rays converge at camera point
            print(f"DEBUG: Using perspective ray tracing for 2D screen")
            fov = self.cone_angle * 2.0  # Use same FOV as 2D viewing (cone_angle * 2)
            aspect_ratio = render_width / render_height
            half_height = math.tan(math.radians(fov) / 2.0)
            half_width = half_height * aspect_ratio
            is_orthographic = False
        
        # Optimized ray tracing - skip pixels for speed
        step = 2 if self.screen_render_mode == "ray_tracing" else 4
        
        total_rays = 0
        rainbow_cube_hits = 0
        background_hits = 0
        
        print(f"DEBUG: Starting ray trace with step={step}, resolution={render_width}x{render_height}")
        
        # MANUAL TEST: Test perfect ray toward cube
        test_origin = np.array([0.0, 0.0, 0.0])
        test_direction = np.array([0.70710678, 0.0, 0.70710678])  # Perfect direction to cube
        cube_pos = np.array([2.0, 0.0, 2.0])
        # Use the same size as simple mode for consistency
        if hasattr(self, '_canvas_ref') and self._canvas_ref and hasattr(self._canvas_ref, 'rainbow_cube_size'):
            cube_size = self._canvas_ref.rainbow_cube_size
            cube_size = np.array([cube_size, cube_size, cube_size])
        else:
            cube_size = np.array([0.3, 0.3, 0.3])  # Match simple mode default
        
        print(f"DEBUG: MANUAL RAY TEST:")
        print(f"  - Test ray origin: {test_origin}")
        print(f"  - Test ray direction: {test_direction}")
        print(f"  - Cube position: {cube_pos}")
        print(f"  - Cube size: {cube_size}")
        
        # Test the intersection
        hit, t, hit_point, normal = self.ray_box_intersection(test_origin, test_direction, cube_pos, cube_size)
        print(f"  - Manual test result: hit={hit}")
        if hit:
            print(f"  - Manual test t: {t:.3f}")
            print(f"  - Manual test hit point: {hit_point}")
            print(f"  - Manual test normal: {normal}")
            
            # Test the color we'd get
            test_color = self.trace_ray(test_origin, test_direction)
            print(f"  - Manual test color: {test_color}")
        else:
            print(f"  - Manual test FAILED - no intersection detected!")
            
        # Also test why the camera rays have Y-components
        print(f"DEBUG: Camera ray analysis:")
        print(f"  - Camera direction should be: [0.707, 0, 0.707]")
        print(f"  - Actual camera direction: {camera_dir}")
        print(f"  - Camera right vector: {right}")
        print(f"  - Camera up vector: {up}")
        print(f"  - Problem: Camera not aligned with XZ plane!")
        
        for y in range(0, render_height, step):
            for x in range(0, render_width, step):
                total_rays += 1
                # Calculate ray direction
                u = (x + 0.5) / render_width
                v = (y + 0.5) / render_height
                
                # Convert to [-1, 1] range with center offset adjustment
                u = 2.0 * u - 1.0  # Standard U coordinate
                v = 2.0 * v - 1.0  # Standard V coordinate
                
                if is_orthographic:
                    # Orthographic projection - parallel rays
                    # Ray origin varies, ray direction is constant
                    ray_origin_offset = u * half_width * right + v * half_height * up  # up vector already flipped above
                    ray_origin = camera_pos + ray_origin_offset
                    ray_dir = camera_dir  # All rays have same direction
                else:
                    # Perspective projection - rays converge at camera point
                    ray_origin = camera_pos
                    ray_dir = camera_dir + u * half_width * right + v * half_height * up  # up vector already flipped above
                ray_dir = ray_dir / np.linalg.norm(ray_dir)
                
                # Debug ray directions to see if they're perpendicular to camera direction
                if total_rays <= 10:  # Debug first few rays
                    dot_with_camera = np.dot(ray_dir, camera_dir)
                    print(f"DEBUG: Ray {total_rays} at pixel ({x},{y})")
                    print(f"  - Camera direction: {camera_dir}")
                    print(f"  - Ray direction: {ray_dir}")
                    print(f"  - Dot with camera: {dot_with_camera:.6f} (should be close to 1.0 for center rays)")
                    print(f"  - u={u:.3f}, v={v:.3f}")
                    print(f"  - right component: {u * half_width}")
                    print(f"  - up component: {v * half_height}")
                
                # Also check center ray specifically
                if abs(u) < 0.1 and abs(v) < 0.1:  # Near center
                    dot_with_camera = np.dot(ray_dir, camera_dir)
                    print(f"DEBUG: CENTER RAY - should match camera direction closely")
                    print(f"  - Camera direction: {camera_dir}")
                    print(f"  - Center ray direction: {ray_dir}")
                    print(f"  - Dot product: {dot_with_camera:.6f} (should be ~1.0)")
                    if dot_with_camera < 0.9:
                        print(f"  - ⚠️ CENTER RAY IS NOT ALIGNED WITH CAMERA!")
                
                # Choose rendering method based on mode
                if self.screen_render_mode == "ray_marching":
                    color = self.trace_ray_marching(ray_origin, ray_dir)
                else:
                    color = self.trace_ray(ray_origin, ray_dir)
                
                    # Count hits for debugging - fix the color detection
                    if np.any(color > 0.4) and color[0] > color[1] and color[0] > color[2]:  # Red-ish color (cube hit)
                        rainbow_cube_hits += 1
                    elif np.allclose(color, [0.1, 0.1, 0.1], atol=0.05):  
                        # Background color
                        background_hits += 1
                
                # Convert to 8-bit
                pixel_color = (color * 255).astype(np.uint8)
                
                # Debug color conversion for non-background pixels
                if not np.allclose(color, [0.1, 0.1, 0.1], atol=0.05) and total_rays <= 10:
                    print(f"DEBUG COLOR: pixel({x},{y}) - float_color={color}, uint8_color={pixel_color}")
                
                # Fill a block of pixels for speed
                for dy in range(step):
                    for dx in range(step):
                        py = min(y + dy, render_height - 1)
                        px = min(x + dx, render_width - 1)
                        image_data[py, px] = pixel_color  # Fixed: Remove Y flip to match simple mode
        
        # Store the low-res image data for now (we could upscale later if needed)
        self.screen_current_size = (render_width, render_height)
        
        print(f"DEBUG: ===== RAY TRACING TEXTURE COMPLETED =====")
        print(f"DEBUG: Ray tracing statistics:")
        print(f"  - Total rays cast: {total_rays}")
        print(f"  - Red cube hits: {rainbow_cube_hits}")
        print(f"  - Background hits: {background_hits}")
        print(f"  - Other hits: {total_rays - rainbow_cube_hits - background_hits}")
        print(f"  - Cube hit percentage: {(rainbow_cube_hits/total_rays*100):.2f}%")
        
        if rainbow_cube_hits == 0:
            print(f"DEBUG: ⚠️  NO CUBE HITS DETECTED!")
            print(f"DEBUG: This suggests the camera is not pointing toward the cube")
            print(f"DEBUG: Camera direction: {camera_dir}")
            print(f"DEBUG: Expected direction to cube: {cube_dir}")
            print(f"DEBUG: Angle between them: {angle_to_cube:.1f}°")
        print(f"DEBUG: Ray tracing texture updated successfully!")
        print(f"DEBUG: ==============================================")
        
        # Store the image data
        self.screen_texture_data = image_data
        
        # Create OpenGL texture
        if self.screen_texture_id is None:
            self.screen_texture_id = gl.glGenTextures(1)
        
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.screen_texture_id)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, render_width, render_height, 0, 
                       gl.GL_RGB, gl.GL_UNSIGNED_BYTE, image_data)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)  # Nearest for pixelated look
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
    
    def create_placeholder_texture(self):
        """Create a simple placeholder texture for the screen."""
        width, height = 64, 48  # Small placeholder
        # Create a simple pattern: blue background with "RAY TRACING" text simulation
        image_data = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Blue background
        image_data[:, :] = [0, 100, 200]
        
        # Add some simple pattern lines to indicate it's loading
        for y in range(0, height, 8):
            image_data[y:y+2, :] = [255, 255, 255]  # White horizontal lines
        
        # Create texture
        if self.screen_texture_id is None:
            self.screen_texture_id = gl.glGenTextures(1)
        
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.screen_texture_id)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, width, height, 0, 
                       gl.GL_RGB, gl.GL_UNSIGNED_BYTE, image_data)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
    
    def render_screen_geometry(self):
        """Render the 2D screen as a textured rectangle in 3D space."""
        if not self.screen_enabled:
            return
        
        # Update texture if needed
        self.render_screen_texture()
        
        # Create a placeholder texture if ray tracing isn't ready
        if self.screen_texture_id is None:
            self.create_placeholder_texture()
        
        gl.glPushMatrix()
        
        # Apply screen transformations
        gl.glTranslatef(self.screen_position[0], self.screen_position[1], self.screen_position[2])
        
        # Apply screen rotation from object_rotations to match simple mode behavior
        if hasattr(self, '_canvas_ref') and self._canvas_ref and hasattr(self._canvas_ref, 'object_rotations'):
            screen_rot = self._canvas_ref.object_rotations.get("screen", np.array([0.0, 0.0, 0.0]))
            gl.glRotatef(screen_rot[0], 1.0, 0.0, 0.0)  # Pitch (X rotation)
            gl.glRotatef(screen_rot[1], 0.0, 1.0, 0.0)  # Yaw (Y rotation)
            gl.glRotatef(screen_rot[2], 0.0, 0.0, 1.0)  # Roll (Z rotation)
        else:
            # Fallback to internal screen rotation
            gl.glRotatef(self.screen_rotation[0], 1.0, 0.0, 0.0)  # Pitch
            gl.glRotatef(self.screen_rotation[1], 0.0, 1.0, 0.0)  # Yaw
            gl.glRotatef(self.screen_rotation[2], 0.0, 0.0, 1.0)  # Roll
        
        # Enable texturing
        gl.glEnable(gl.GL_TEXTURE_2D)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.screen_texture_id)
        
        # Disable lighting for screen
        lighting_was_enabled = gl.glIsEnabled(gl.GL_LIGHTING)
        if lighting_was_enabled:
            gl.glDisable(gl.GL_LIGHTING)
        
        # Draw screen rectangle
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)  # White color
        gl.glBegin(gl.GL_QUADS)
        
        half_width = self.screen_width / 2.0
        half_height = self.screen_height / 2.0
        
        # Front face
        gl.glTexCoord2f(0.0, 0.0)
        gl.glVertex3f(-half_width, -half_height, 0.0)
        
        gl.glTexCoord2f(1.0, 0.0)
        gl.glVertex3f(half_width, -half_height, 0.0)
        
        gl.glTexCoord2f(1.0, 1.0)
        gl.glVertex3f(half_width, half_height, 0.0)
        
        gl.glTexCoord2f(0.0, 1.0)
        gl.glVertex3f(-half_width, half_height, 0.0)
        
        gl.glEnd()
        
        # Disable texturing for border
        gl.glDisable(gl.GL_TEXTURE_2D)
        
        # Draw screen border for better visibility
        gl.glColor4f(0.8, 0.8, 0.8, 1.0)  # Light gray border
        gl.glLineWidth(3.0)
        gl.glBegin(gl.GL_LINE_LOOP)
        
        border_width = half_width + 0.05
        border_height = half_height + 0.05
        
        gl.glVertex3f(-border_width, -border_height, 0.001)  # Slightly in front
        gl.glVertex3f(border_width, -border_height, 0.001)
        gl.glVertex3f(border_width, border_height, 0.001)
        gl.glVertex3f(-border_width, border_height, 0.001)
        
        gl.glEnd()
        gl.glLineWidth(1.0)  # Reset line width
        
        # Re-enable lighting if it was enabled
        if lighting_was_enabled:
            gl.glEnable(gl.GL_LIGHTING)
        
        gl.glPopMatrix()
    
    # ==================== END RAY TRACING SYSTEM ====================
    
    def toggle_screen(self):
        """Toggle the 2D screen visibility."""
        self.screen_enabled = not self.screen_enabled
        if self.screen_enabled:
            self.screen_needs_update = True  # Force immediate update when enabled
    
    def set_screen_render_mode(self, mode):
        """Set the screen rendering mode."""
        if mode in ["ray_tracing", "path_tracing", "pbr", "ray_marching"]:
            self.screen_render_mode = mode
            # Force screen update on mode change
            self.screen_needs_update = True
    
    def set_screen_position(self, x, y, z):
        """Set the screen 3D position."""
        self.screen_position = np.array([x, y, z])
    
    def set_screen_rotation(self, pitch, yaw, roll):
        """Set the screen rotation."""
        self.screen_rotation = np.array([pitch, yaw, roll])
    
    def set_screen_size(self, width, height):
        """Set the screen size."""
        self.screen_width = width
        self.screen_height = height
    
    def set_screen_resolution(self, width, height):
        """Set the screen texture resolution."""
        self.screen_resolution = (width, height)
        # Clear existing texture to force regeneration
        if self.screen_texture_id is not None:
            gl.glDeleteTextures(1, [self.screen_texture_id])
            self.screen_texture_id = None
    
    def set_camera_position(self, x, y, z):
        """Set the virtual camera position."""
        self.screen_camera_position = np.array([x, y, z])
        self.screen_needs_update = True  # Force update
    
    def set_camera_target(self, x, y, z):
        """Set the virtual camera target."""
        self.screen_camera_target = np.array([x, y, z])
        self.screen_needs_update = True  # Force update
    
    def set_screen_update_rate(self, rate):
        """Set the screen update rate."""
        self.screen_update_rate = max(0.1, rate)  # Minimum 0.1 seconds
    
    def set_screen_samples(self, samples):
        """Set the anti-aliasing samples."""
        self.screen_samples = max(1, samples)
        self.screen_needs_update = True  # Force update
    
    def set_screen_max_bounces(self, bounces):
        """Set the maximum ray bounces."""
        self.screen_max_bounces = max(0, bounces)
        self.screen_needs_update = True  # Force update
    
    def apply_transformation_matrix(self):
        """Apply transformation matrix (translation, rotation, scale)."""
        gl.glPushMatrix()
        
        # Apply translation
        gl.glTranslatef(self.position[0], self.position[1], self.position[2])
        
        # Apply rotation
        gl.glRotatef(self.rotation[0], 1, 0, 0)  # Pitch
        gl.glRotatef(self.rotation[1], 0, 1, 0)  # Yaw
        gl.glRotatef(self.rotation[2], 0, 0, 1)  # Roll
        
        # Apply scale
        gl.glScalef(self.scale[0], self.scale[1], self.scale[2])
    
    def render_sphere_surface(self):
        """Render the main sphere surface with proper transparency."""
        # Set sphere color with transparency
        color = self.sphere_color.copy()
        color[3] = self.transparency
        
        if self.wireframe_mode:
            # Render sphere as wireframe using main sphere geometry
            gl.glColor4f(*color)
            gl.glLineWidth(1.0)
            gl.glDisable(gl.GL_CULL_FACE)  # Show all wireframe lines
            
            # Render triangle edges
            gl.glBegin(gl.GL_LINES)
            for i in range(0, len(self.indices), 3):
                # Draw three edges of each triangle
                for j in range(3):
                    idx1 = self.indices[i + j] * 3
                    idx2 = self.indices[i + ((j + 1) % 3)] * 3
                    
                    gl.glVertex3f(self.vertices[idx1], self.vertices[idx1 + 1], self.vertices[idx1 + 2])
                    gl.glVertex3f(self.vertices[idx2], self.vertices[idx2 + 1], self.vertices[idx2 + 2])
            gl.glEnd()
            gl.glEnable(gl.GL_CULL_FACE)
        else:
            # Render solid sphere surface
            # If transparent, disable face culling to see both sides
            if self.transparency < 1.0:
                gl.glDisable(gl.GL_CULL_FACE)
                gl.glEnable(gl.GL_BLEND)
                gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
                gl.glDepthMask(gl.GL_FALSE)  # Don't write to depth buffer for transparent objects
            else:
                gl.glEnable(gl.GL_CULL_FACE)
                gl.glDisable(gl.GL_BLEND)
                gl.glDepthMask(gl.GL_TRUE)
            
            gl.glColor4f(*color)
            
            # Enable lighting if enabled
            if self.lighting_enabled:
                gl.glEnable(gl.GL_LIGHTING)
                gl.glEnable(gl.GL_LIGHT0)
                
                # Set material properties
                gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT_AND_DIFFUSE, color)
                gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
                gl.glMaterialf(gl.GL_FRONT_AND_BACK, gl.GL_SHININESS, 50.0)
            else:
                gl.glDisable(gl.GL_LIGHTING)
            
            # Render triangles
            gl.glBegin(gl.GL_TRIANGLES)
            for i in range(0, len(self.indices), 3):
                for j in range(3):
                    idx = self.indices[i + j] * 3
                    gl.glNormal3f(self.normals[idx], self.normals[idx + 1], self.normals[idx + 2])
                    gl.glVertex3f(self.vertices[idx], self.vertices[idx + 1], self.vertices[idx + 2])
            gl.glEnd()
            
            if self.lighting_enabled:
                gl.glDisable(gl.GL_LIGHTING)
                
            # Restore depth writing
            if self.transparency < 1.0:
                gl.glDepthMask(gl.GL_TRUE)
                gl.glEnable(gl.GL_CULL_FACE)
                gl.glDisable(gl.GL_BLEND)
    
    def render_longitude_latitude_grid(self):
        """Render longitude and latitude grid lines."""
        if GridType.LONGITUDE_LATITUDE not in self.active_grids:
            return
        
        gl.glColor4f(*self.grid_colors[GridType.LONGITUDE_LATITUDE])
        gl.glLineWidth(2.0)
        
        # Longitude lines (meridians)
        for i in range(self.longitude_lines):
            angle = 2 * math.pi * i / self.longitude_lines
            gl.glBegin(gl.GL_LINE_STRIP)
            for j in range(self.resolution + 1):
                lat = math.pi * (-0.5 + float(j) / self.resolution)
                x = math.cos(lat) * math.cos(angle) * self.radius
                y = math.sin(lat) * self.radius
                z = math.cos(lat) * math.sin(angle) * self.radius
                gl.glVertex3f(x, y, z)
            gl.glEnd()
        
        # Latitude lines (parallels)
        for i in range(self.latitude_lines + 1):
            lat = math.pi * (-0.5 + float(i) / self.latitude_lines)
            gl.glBegin(gl.GL_LINE_LOOP)
            for j in range(self.resolution):
                lon = 2 * math.pi * j / self.resolution
                x = math.cos(lat) * math.cos(lon) * self.radius
                y = math.sin(lat) * self.radius
                z = math.cos(lat) * math.sin(lon) * self.radius
                gl.glVertex3f(x, y, z)
            gl.glEnd()
    
    def render_concentric_circles(self):
        """Render concentric circles on sphere surface."""
        if GridType.CONCENTRIC_CIRCLES not in self.active_grids:
            return
        
        gl.glColor4f(*self.grid_colors[GridType.CONCENTRIC_CIRCLES])
        gl.glLineWidth(2.0)
        
        # Render circles at different latitudes
        for i in range(self.concentric_rings):
            lat = math.pi * (-0.4 + 0.8 * i / (self.concentric_rings - 1))
            radius_at_lat = math.cos(lat) * self.radius
            y = math.sin(lat) * self.radius
            
            gl.glBegin(gl.GL_LINE_LOOP)
            for j in range(64):  # Higher resolution for smooth circles
                angle = 2 * math.pi * j / 64
                x = radius_at_lat * math.cos(angle)
                z = radius_at_lat * math.sin(angle)
                gl.glVertex3f(x, y, z)
            gl.glEnd()
    
    def render_dot_particles(self):
        """Render dot particles distributed on sphere surface."""
        if GridType.DOT_PARTICLES not in self.active_grids:
            return
        
        gl.glColor4f(*self.grid_colors[GridType.DOT_PARTICLES])
        gl.glPointSize(3.0)
    
        gl.glBegin(gl.GL_POINTS)
        
        # Generate pseudo-random points using Fibonacci spiral
        golden_ratio = (1 + math.sqrt(5)) / 2
        for i in range(self.dot_density):
            # Fibonacci spiral distribution
            theta = 2 * math.pi * i / golden_ratio
            phi = math.acos(1 - 2 * (i + 0.5) / self.dot_density)
            
            x = math.sin(phi) * math.cos(theta) * self.radius
            y = math.cos(phi) * self.radius
            z = math.sin(phi) * math.sin(theta) * self.radius
            
            gl.glVertex3f(x, y, z)
        
        gl.glEnd()
    
    def render_neon_lines(self):
        """Render neon-style grid lines with glow effect."""
        if GridType.NEON_LINES not in self.active_grids:
            return
        
        # Enable blending for glow effect
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE)
    
        color = self.grid_colors[GridType.NEON_LINES]
        
        # Render multiple passes for glow effect
        for pass_num in range(3):
            alpha = (3 - pass_num) * 0.3 * self.neon_intensity
            line_width = (pass_num + 1) * 2.0
            
            gl.glColor4f(color[0], color[1], color[2], alpha)
            gl.glLineWidth(line_width)
            
            # Render grid pattern similar to the reference image
            # Horizontal rings
            for i in range(8):
                lat = math.pi * (-0.4 + 0.8 * i / 7)
                radius_at_lat = math.cos(lat) * self.radius
                y = math.sin(lat) * self.radius
                
                gl.glBegin(gl.GL_LINE_LOOP)
                for j in range(64):
                    angle = 2 * math.pi * j / 64
                    x = radius_at_lat * math.cos(angle)
                    z = radius_at_lat * math.sin(angle)
                    gl.glVertex3f(x, y, z)
                gl.glEnd()
            
            # Vertical meridians
            for i in range(12):
                angle = 2 * math.pi * i / 12
                gl.glBegin(gl.GL_LINE_STRIP)
                for j in range(32):
                    lat = math.pi * (-0.5 + float(j) / 31)
                    x = math.cos(lat) * math.cos(angle) * self.radius
                    y = math.sin(lat) * self.radius
                    z = math.cos(lat) * math.sin(angle) * self.radius
                    gl.glVertex3f(x, y, z)
                gl.glEnd()
        
        gl.glDisable(gl.GL_BLEND)
    
    def render_wireframe(self):
        """Render wireframe representation of the sphere with adjustable density."""
        if GridType.WIREFRAME not in self.active_grids:
            return
        
        gl.glColor4f(*self.grid_colors[GridType.WIREFRAME])
        gl.glLineWidth(1.0)
        
        # Disable face culling for wireframe to see all lines
        gl.glDisable(gl.GL_CULL_FACE)
        
        # Render triangle edges using wireframe geometry
        gl.glBegin(gl.GL_LINES)
        for i in range(0, len(self.wireframe_indices), 3):
            # Draw three edges of each triangle
            for j in range(3):
                idx1 = self.wireframe_indices[i + j] * 3
                idx2 = self.wireframe_indices[i + ((j + 1) % 3)] * 3
                
                gl.glVertex3f(self.wireframe_vertices[idx1], self.wireframe_vertices[idx1 + 1], self.wireframe_vertices[idx1 + 2])
                gl.glVertex3f(self.wireframe_vertices[idx2], self.wireframe_vertices[idx2 + 1], self.wireframe_vertices[idx2 + 2])
        gl.glEnd()
        
        # Re-enable face culling
        gl.glEnable(gl.GL_CULL_FACE)
    
    def render_vector(self):
        """Render 3D vector from sphere center with arrow head."""
        if not self.vector_enabled:
            return
        
        # Normalize the direction vector
        direction = self.vector_direction / np.linalg.norm(self.vector_direction)
        
        # Calculate vector end point - use fixed size regardless of sphere scale
        base_radius = 1.0  # Use fixed base radius so vector size is independent of sphere scale
        vector_end = direction * self.vector_length * base_radius
        
        # Set vector color
        gl.glColor4f(*self.vector_color)
        gl.glLineWidth(self.vector_thickness)
        
        # Disable lighting for vector (we want solid colors)
        gl.glDisable(gl.GL_LIGHTING)
        
        # Draw main vector line
        gl.glBegin(gl.GL_LINES)
        gl.glVertex3f(0.0, 0.0, 0.0)  # Start at sphere center
        gl.glVertex3f(vector_end[0], vector_end[1], vector_end[2])  # End point
        gl.glEnd()
        
        # Draw arrow head
        self.render_arrow_head(vector_end, direction)
        
        # Re-enable lighting if it was enabled
        if self.lighting_enabled:
            gl.glEnable(gl.GL_LIGHTING)
        
        # Render orientation vector if enabled
        if self.vector_orientation_enabled:
            self.render_vector_orientation()
    
    def render_vector_orientation(self):
        """Render orientation vector showing the 'up' direction at the tail of the main vector."""
        if not self.vector_enabled or not self.vector_orientation_enabled:
            return
        
        # Normalize the main vector direction
        direction = self.vector_direction / np.linalg.norm(self.vector_direction)
        
        # Calculate the up vector based on roll rotation (same logic as camera system)
        world_up = np.array([0.0, 1.0, 0.0])
        right = np.cross(direction, world_up)
        if np.linalg.norm(right) < 0.001:
            # If vector is pointing up/down, use right vector as reference
            right = np.array([1.0, 0.0, 0.0])
        right = right / np.linalg.norm(right)
        up = np.cross(right, direction)
        up = up / np.linalg.norm(up)
        
        # Apply roll rotation around the vector direction (same method as camera system)
        roll_angle = math.radians(self.vector_roll)
        cos_roll = math.cos(roll_angle)
        sin_roll = math.sin(roll_angle)
        
        # Debug: Print roll angle to verify it's being used
        print(f"DEBUG: Orientation vector roll angle: {self.vector_roll:.1f}° (radians: {roll_angle:.3f})")
        
        # Apply 2D rotation to the up and right vectors in their plane (same as camera system)
        new_right = cos_roll * right + sin_roll * up
        new_up = -sin_roll * right + cos_roll * up
        
        right = new_right / np.linalg.norm(new_right)
        up_rotated = new_up / np.linalg.norm(new_up)
        
        # Debug: Print vectors to verify rotation
        print(f"DEBUG: Original up: {up}")
        print(f"DEBUG: Rotated up: {up_rotated}")
        print(f"DEBUG: Angle between them: {math.degrees(math.acos(np.clip(np.dot(up, up_rotated), -1.0, 1.0))):.1f}°")
        
        # Calculate orientation vector end point (from sphere center)
        base_radius = 1.0  # Use fixed base radius so orientation vector size is independent of sphere scale
        orientation_end = up_rotated * self.vector_orientation_length * base_radius
        
        # Set orientation vector color and thickness
        gl.glColor4f(*self.vector_orientation_color)
        gl.glLineWidth(self.vector_orientation_thickness)
        
        # Disable lighting for orientation vector (we want solid colors)
        lighting_was_enabled = self.lighting_enabled
        if lighting_was_enabled:
            gl.glDisable(gl.GL_LIGHTING)
        
        # Draw orientation vector line from sphere center
        gl.glBegin(gl.GL_LINES)
        gl.glVertex3f(0.0, 0.0, 0.0)  # Start at sphere center (tail of main vector)
        gl.glVertex3f(orientation_end[0], orientation_end[1], orientation_end[2])  # End point
        gl.glEnd()
        
        # Draw small arrow head for orientation vector
        self.render_orientation_arrow_head(orientation_end, up_rotated)
        
        # Re-enable lighting if it was enabled
        if lighting_was_enabled:
            gl.glEnable(gl.GL_LIGHTING)
    
    def render_orientation_arrow_head(self, tip_position, direction):
        """Render small arrow head at the tip of the orientation vector."""
        # Create a smaller arrow head than the main vector
        arrow_length = 0.1  # Smaller than main vector arrow
        arrow_width = 0.05
        
        # Create perpendicular vectors for arrow head
        if abs(direction[0]) < 0.9:
            perp1 = np.array([0.0, direction[2], -direction[1]])
        else:
            perp1 = np.array([-direction[2], 0.0, direction[0]])
        perp1 = perp1 / np.linalg.norm(perp1)
        
        perp2 = np.cross(direction, perp1)
        perp2 = perp2 / np.linalg.norm(perp2)
        
        # Calculate arrow base position
        arrow_base = tip_position - direction * arrow_length
        
        # Draw arrow head as triangular faces
        gl.glBegin(gl.GL_TRIANGLES)
        
        # Create 4 triangular faces for a 3D arrow head
        for i in range(4):
            angle = 2 * math.pi * i / 4
            cos_angle = math.cos(angle)
            sin_angle = math.sin(angle)
            
            # Point on the base circle
            base_point = arrow_base + (perp1 * cos_angle + perp2 * sin_angle) * arrow_width
            
            # Next point on the base circle
            next_angle = 2 * math.pi * (i + 1) / 4
            next_cos = math.cos(next_angle)
            next_sin = math.sin(next_angle)
            next_base_point = arrow_base + (perp1 * next_cos + perp2 * next_sin) * arrow_width
            
            # Triangle from tip to base edge
            gl.glVertex3f(tip_position[0], tip_position[1], tip_position[2])
            gl.glVertex3f(base_point[0], base_point[1], base_point[2])
            gl.glVertex3f(next_base_point[0], next_base_point[1], next_base_point[2])
        
        gl.glEnd()
    
    def render_arrow_head(self, tip_position, direction):
        """Render arrow head at the tip of the vector."""
        # Arrow head parameters
        head_length = 0.3 * self.radius
        head_radius = 0.1 * self.radius
        
        # Calculate arrow head base position
        base_position = tip_position - direction * head_length
        
        # Create perpendicular vectors for arrow head
        # Find a vector perpendicular to direction
        if abs(direction[0]) < 0.9:
            perp1 = np.array([0.0, direction[2], -direction[1]])
        else:
            perp1 = np.array([-direction[2], 0.0, direction[0]])
        
        perp1 = perp1 / np.linalg.norm(perp1) * head_radius
        
        # Second perpendicular vector
        perp2 = np.cross(direction, perp1)
        perp2 = perp2 / np.linalg.norm(perp2) * head_radius
        
        # Draw arrow head as lines from tip to base circle
        gl.glBegin(gl.GL_LINES)
        
        # Draw 8 lines from tip to points around the base circle
        for i in range(8):
            angle = 2 * math.pi * i / 8
            base_point = (base_position +
            perp1 * math.cos(angle) +
            perp2 * math.sin(angle))
            
            # Line from tip to base point
            gl.glVertex3f(tip_position[0], tip_position[1], tip_position[2])
            gl.glVertex3f(base_point[0], base_point[1], base_point[2])
        
        # Draw base circle
        for i in range(8):
            angle1 = 2 * math.pi * i / 8
            angle2 = 2 * math.pi * ((i + 1) % 8) / 8
                
            point1 = (base_position +
            perp1 * math.cos(angle1) +
            perp2 * math.sin(angle1))
            point2 = (base_position +
            perp1 * math.cos(angle2) +
            perp2 * math.sin(angle2))
            
            gl.glVertex3f(point1[0], point1[1], point1[2])
            gl.glVertex3f(point2[0], point2[1], point2[2])
        
        gl.glEnd()
    
    def render_cone(self, manage_blend=True):
        """Render cone section or truncated cone with tip at sphere center pointing along vector direction."""
        if not self.cone_enabled:
            return
        
        # Use vector direction for cone axis
        direction = self.vector_direction / np.linalg.norm(self.vector_direction)
        
        # Calculate cone end point and base radius - use fixed size regardless of sphere scale
        base_radius = 1.0  # Use fixed base radius so cone size is independent of sphere scale
        if self.cone_infinite:
            # Use a very large length for infinite cone rendering to cover entire screen
            effective_length = 1000.0 * base_radius
            cone_end = direction * effective_length
            cone_base_radius = effective_length * math.tan(math.radians(self.cone_angle))
        else:
            cone_end = direction * self.cone_length * base_radius
            cone_base_radius = self.cone_length * base_radius * math.tan(math.radians(self.cone_angle))
        
        # Create perpendicular vectors for cone base
        if abs(direction[0]) < 0.9:
            perp1 = np.array([0.0, direction[2], -direction[1]])
        else:
            perp1 = np.array([-direction[2], 0.0, direction[0]])
            
            perp1 = perp1 / np.linalg.norm(perp1)
        
        # Second perpendicular vector
        perp2 = np.cross(direction, perp1)
        perp2 = perp2 / np.linalg.norm(perp2)
        
        # Set cone color and enable blending for transparency (only if managing blend state)
        if manage_blend:
            gl.glEnable(gl.GL_BLEND)
            gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
            gl.glColor4f(*self.cone_color)
        
        # Disable lighting for cone (we want uniform color)
        lighting_was_enabled = self.lighting_enabled
        if lighting_was_enabled:
            gl.glDisable(gl.GL_LIGHTING)
        
        if self.near_plane_enabled and self.near_plane_distance > 0:
            # Create a truncated cone
            self._render_truncated_cone(direction, cone_end, perp1, perp2, cone_base_radius)
        else:
            # Render full cone
            self._render_full_cone(cone_end, perp1, perp2, cone_base_radius)
        
        # Re-enable lighting if it was enabled
        if lighting_was_enabled:
            gl.glEnable(gl.GL_LIGHTING)
        
        # Disable blend only if we enabled it
        if manage_blend:
            gl.glDisable(gl.GL_BLEND)
    
    def _render_full_cone(self, cone_end, perp1, perp2, cone_base_radius):
        """Render full cone with tip at center."""
        # Scale perpendicular vectors by base radius
        perp1_scaled = perp1 * cone_base_radius
        perp2_scaled = perp2 * cone_base_radius
        
        if self.cone_infinite:
            # For infinite cone, only render the edge rays, not the surface
            gl.glBegin(gl.GL_LINES)
            
            for i in range(self.cone_resolution):
                angle = 2 * math.pi * i / self.cone_resolution
                
                # Point on the cone base circle
                base_point = (cone_end +
                             perp1_scaled * math.cos(angle) +
                             perp2_scaled * math.sin(angle))
                
                # Ray from tip to infinite distance
                gl.glVertex3f(0.0, 0.0, 0.0)  # Tip at sphere center
                gl.glVertex3f(base_point[0], base_point[1], base_point[2])
            
            gl.glEnd()
        else:
            # Render cone surface as triangles
            gl.glBegin(gl.GL_TRIANGLES)
            
            for i in range(self.cone_resolution):
                angle1 = 2 * math.pi * i / self.cone_resolution
                angle2 = 2 * math.pi * ((i + 1) % self.cone_resolution) / self.cone_resolution
                
                # Points on the cone base circle
                base_point1 = (cone_end +
                              perp1_scaled * math.cos(angle1) +
                              perp2_scaled * math.sin(angle1))
                base_point2 = (cone_end +
                              perp1_scaled * math.cos(angle2) +
                              perp2_scaled * math.sin(angle2))
                
                # Triangle from tip to base edge
                gl.glVertex3f(0.0, 0.0, 0.0)  # Tip at sphere center
                gl.glVertex3f(base_point1[0], base_point1[1], base_point1[2])
                gl.glVertex3f(base_point2[0], base_point2[1], base_point2[2])
            
            gl.glEnd()
        
        # Render cone outline wireframe for better visibility
        gl.glColor4f(self.cone_color[0], self.cone_color[1], self.cone_color[2], 1.0)
        gl.glLineWidth(2.0)
        
        # Draw lines from tip to base circle
        gl.glBegin(gl.GL_LINES)
        for i in range(0, self.cone_resolution, 2):  # Every other line to avoid clutter
            angle = 2 * math.pi * i / self.cone_resolution
            base_point = (cone_end +
            perp1_scaled * math.cos(angle) +
            perp2_scaled * math.sin(angle))
            
            gl.glVertex3f(0.0, 0.0, 0.0)  # From tip
            gl.glVertex3f(base_point[0], base_point[1], base_point[2])  # To base
        
        # Draw base circle outline
        for i in range(self.cone_resolution):
            angle1 = 2 * math.pi * i / self.cone_resolution
            angle2 = 2 * math.pi * ((i + 1) % self.cone_resolution) / self.cone_resolution
            
            point1 = (cone_end +
                     perp1_scaled * math.cos(angle1) +
                     perp2_scaled * math.sin(angle1))
            point2 = (cone_end +
                     perp1_scaled * math.cos(angle2) +
                     perp2_scaled * math.sin(angle2))
            
            gl.glVertex3f(point1[0], point1[1], point1[2])
            gl.glVertex3f(point2[0], point2[1], point2[2])
        
        gl.glEnd()
        
    def _render_truncated_cone(self, direction, cone_end, perp1, perp2, cone_base_radius):
        """Render truncated cone by cutting at near plane."""
        # For proper truncation, interpolate along the cone's existing surface
        # The cone goes from tip (0,0,0) to base circle at cone_end
        
        # Use fixed base radius so cone size is independent of sphere scale
        base_radius = 1.0
        full_length = self.cone_length * base_radius
        if self.near_plane_distance >= full_length:
            # Near plane is beyond the cone, render nothing
            return
        
        # Calculate interpolation factor (0 = at tip, 1 = at base)
        t = self.near_plane_distance / full_length
        
        # Calculate near plane position and radius by interpolating along cone surface
        near_plane_pos = t * cone_end  # Position along cone axis
        near_radius = t * cone_base_radius  # Radius scales linearly from tip
        
        # Scale perpendicular vectors
        perp1_near = perp1 * near_radius
        perp2_near = perp2 * near_radius
        perp1_base = perp1 * cone_base_radius
        perp2_base = perp2 * cone_base_radius
        
        # Render truncated cone surface as triangles
        gl.glBegin(gl.GL_TRIANGLES)
        
        for i in range(self.cone_resolution):
            angle1 = 2 * math.pi * i / self.cone_resolution
            angle2 = 2 * math.pi * ((i + 1) % self.cone_resolution) / self.cone_resolution
            
            # Points on the near plane circle (smaller)
            near_point1 = (near_plane_pos +
            perp1_near * math.cos(angle1) +
            perp2_near * math.sin(angle1))
            near_point2 = (near_plane_pos +
            perp1_near * math.cos(angle2) +
            perp2_near * math.sin(angle2))
            
            # Points on the base circle (larger)
            base_point1 = (cone_end +
            perp1_base * math.cos(angle1) +
            perp2_base * math.sin(angle1))
            base_point2 = (cone_end +
            perp1_base * math.cos(angle2) +
            perp2_base * math.sin(angle2))
            
            # Two triangles to form a quad strip between circles
            # Triangle 1: near1 -> near2 -> base2
            gl.glVertex3f(near_point1[0], near_point1[1], near_point1[2])
            gl.glVertex3f(near_point2[0], near_point2[1], near_point2[2])
            gl.glVertex3f(base_point2[0], base_point2[1], base_point2[2])
            
            # Triangle 2: near1 -> base2 -> base1
            gl.glVertex3f(near_point1[0], near_point1[1], near_point1[2])
            gl.glVertex3f(base_point2[0], base_point2[1], base_point2[2])
            gl.glVertex3f(base_point1[0], base_point1[1], base_point1[2])
        
        # Render near plane circle (cap)
        center_near = near_plane_pos
        for i in range(self.cone_resolution):
            angle1 = 2 * math.pi * i / self.cone_resolution
            angle2 = 2 * math.pi * ((i + 1) % self.cone_resolution) / self.cone_resolution
            
            near_point1 = (near_plane_pos +
            perp1_near * math.cos(angle1) +
            perp2_near * math.sin(angle1))
            near_point2 = (near_plane_pos +
            perp1_near * math.cos(angle2) +
            perp2_near * math.sin(angle2))
            
            # Triangle from center to edge
            gl.glVertex3f(center_near[0], center_near[1], center_near[2])
            gl.glVertex3f(near_point1[0], near_point1[1], near_point1[2])
            gl.glVertex3f(near_point2[0], near_point2[1], near_point2[2])
        
        # Render base circle (cap)
        center_base = cone_end
        for i in range(self.cone_resolution):
            angle1 = 2 * math.pi * i / self.cone_resolution
            angle2 = 2 * math.pi * ((i + 1) % self.cone_resolution) / self.cone_resolution
            
            base_point1 = (cone_end +
            perp1_base * math.cos(angle1) +
            perp2_base * math.sin(angle1))
            base_point2 = (cone_end +
            perp1_base * math.cos(angle2) +
            perp2_base * math.sin(angle2))
            
            # Triangle from center to edge
            gl.glVertex3f(center_base[0], center_base[1], center_base[2])
            gl.glVertex3f(base_point1[0], base_point1[1], base_point1[2])
            gl.glVertex3f(base_point2[0], base_point2[1], base_point2[2])
        
        gl.glEnd()
        
        # Render truncated cone outline wireframe
        gl.glColor4f(self.cone_color[0], self.cone_color[1], self.cone_color[2], 1.0)
        gl.glLineWidth(2.0)
    
        gl.glBegin(gl.GL_LINES)
        
        # Draw near plane circle outline
        for i in range(self.cone_resolution):
            angle1 = 2 * math.pi * i / self.cone_resolution
            angle2 = 2 * math.pi * ((i + 1) % self.cone_resolution) / self.cone_resolution
            
            point1 = (near_plane_pos +
            perp1_near * math.cos(angle1) +
            perp2_near * math.sin(angle1))
            point2 = (near_plane_pos +
            perp1_near * math.cos(angle2) +
            perp2_near * math.sin(angle2))
            
            gl.glVertex3f(point1[0], point1[1], point1[2])
            gl.glVertex3f(point2[0], point2[1], point2[2])
        
        # Draw base circle outline
        for i in range(self.cone_resolution):
            angle1 = 2 * math.pi * i / self.cone_resolution
            angle2 = 2 * math.pi * ((i + 1) % self.cone_resolution) / self.cone_resolution
            
            point1 = (cone_end +
            perp1_base * math.cos(angle1) +
            perp2_base * math.sin(angle1))
            point2 = (cone_end +
            perp1_base * math.cos(angle2) +
            perp2_base * math.sin(angle2))
            
            gl.glVertex3f(point1[0], point1[1], point1[2])
            gl.glVertex3f(point2[0], point2[1], point2[2])
        
        # Draw connecting lines between circles
        for i in range(0, self.cone_resolution, 2):  # Every other line to avoid clutter
            angle = 2 * math.pi * i / self.cone_resolution
            
            near_point = (near_plane_pos +
            perp1_near * math.cos(angle) +
            perp2_near * math.sin(angle))
            base_point = (cone_end +
            perp1_base * math.cos(angle) +
            perp2_base * math.sin(angle))
            
            gl.glVertex3f(near_point[0], near_point[1], near_point[2])
            gl.glVertex3f(base_point[0], base_point[1], base_point[2])
        
        gl.glEnd()
    
    def render_pyramid(self, manage_blend=True):
        """Render 4-sided pyramid or hexahedron (truncated pyramid) with tip at sphere center."""
        if not self.pyramid_enabled:
            return
        
        # Use vector direction for pyramid axis
        direction = self.vector_direction / np.linalg.norm(self.vector_direction)
        
        # Calculate pyramid end point - use fixed size regardless of sphere scale
        base_radius = 1.0  # Use fixed base radius so pyramid size is independent of sphere scale
        if self.pyramid_infinite:
            # Use a very large length for infinite pyramid rendering to cover entire screen
            effective_length = 1000.0 * base_radius
            pyramid_end = direction * effective_length
        else:
            pyramid_end = direction * self.pyramid_length * base_radius
        
        # Create orthogonal coordinate system at the pyramid base
        # Find a vector perpendicular to direction for horizontal axis
        if abs(direction[0]) < 0.9:
            horizontal = np.array([0.0, direction[2], -direction[1]])
        else:
            horizontal = np.array([-direction[2], 0.0, direction[0]])
            
        horizontal = horizontal / np.linalg.norm(horizontal)
        
        # Vertical axis is perpendicular to both direction and horizontal
        vertical = np.cross(direction, horizontal)
        vertical = vertical / np.linalg.norm(vertical)
        
        # Calculate half-dimensions of rectangular base
        if self.pyramid_infinite:
            half_width = effective_length * math.tan(math.radians(self.pyramid_angle_horizontal))
            half_height = effective_length * math.tan(math.radians(self.pyramid_angle_vertical))
        else:
            half_width = self.pyramid_length * base_radius * math.tan(math.radians(self.pyramid_angle_horizontal))
            half_height = self.pyramid_length * base_radius * math.tan(math.radians(self.pyramid_angle_vertical))
        
        # Calculate the four corners of the pyramid base
        base_corners = [
        pyramid_end + horizontal * half_width + vertical * half_height,    
# Top-right
        pyramid_end - horizontal * half_width + vertical * half_height,    
# Top-left
        pyramid_end - horizontal * half_width - vertical * half_height,    
# Bottom-left
        pyramid_end + horizontal * half_width - vertical * half_height     
# Bottom-right
        ]
        
        # Set pyramid color and enable blending for transparency (only if managing blend state)
        if manage_blend:
            gl.glEnable(gl.GL_BLEND)
            gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
            gl.glColor4f(*self.pyramid_color)
        
        # Disable lighting for pyramid (we want uniform color)
        lighting_was_enabled = self.lighting_enabled
        if lighting_was_enabled:
            gl.glDisable(gl.GL_LIGHTING)
        
        if self.near_plane_enabled and self.near_plane_distance > 0:
            # Create a hexahedron (truncated pyramid)
            self._render_hexahedron(direction, horizontal, vertical, base_corners)
        else:
            # Render full pyramid
            self._render_full_pyramid(base_corners)
        
        # Re-enable lighting if it was enabled
        if lighting_was_enabled:
            gl.glEnable(gl.GL_LIGHTING)
        
        # Disable blend only if we enabled it
        if manage_blend:
            gl.glDisable(gl.GL_BLEND)
    
    def _render_full_pyramid(self, base_corners):
        """Render full pyramid with tip at center."""
        if self.pyramid_infinite:
            # For infinite pyramid, only render the edge rays, not the surface
            gl.glBegin(gl.GL_LINES)
            
            # Four edge rays from tip to infinite distance
            for i in range(4):
                gl.glVertex3f(0.0, 0.0, 0.0)  # Tip at sphere center
                gl.glVertex3f(base_corners[i][0], base_corners[i][1], base_corners[i][2])
            
            gl.glEnd()
        else:
            # Render pyramid faces as triangles
            gl.glBegin(gl.GL_TRIANGLES)
            
            # Four triangular faces from tip to each edge of the base
            for i in range(4):
                corner1 = base_corners[i]
                corner2 = base_corners[(i + 1) % 4]
                
                # Triangle from tip to base edge
                gl.glVertex3f(0.0, 0.0, 0.0)  # Tip at sphere center
                gl.glVertex3f(corner1[0], corner1[1], corner1[2])
                gl.glVertex3f(corner2[0], corner2[1], corner2[2])
            
            # Base triangles (split rectangle into two triangles)
            # Triangle 1: corners 0, 1, 2
            gl.glVertex3f(base_corners[0][0], base_corners[0][1], base_corners[0][2])
            gl.glVertex3f(base_corners[1][0], base_corners[1][1], base_corners[1][2])
            gl.glVertex3f(base_corners[2][0], base_corners[2][1], base_corners[2][2])
            
            # Triangle 2: corners 0, 2, 3
            gl.glVertex3f(base_corners[0][0], base_corners[0][1], base_corners[0][2])
            gl.glVertex3f(base_corners[2][0], base_corners[2][1], base_corners[2][2])
            gl.glVertex3f(base_corners[3][0], base_corners[3][1], base_corners[3][2])
            
            gl.glEnd()
        
        # Render pyramid outline wireframe for better visibility
        gl.glColor4f(self.pyramid_color[0], self.pyramid_color[1], self.pyramid_color[2], 1.0)
        gl.glLineWidth(2.0)
    
        gl.glBegin(gl.GL_LINES)
        
        # Draw lines from tip to each corner of the base
        for corner in base_corners:
            gl.glVertex3f(0.0, 0.0, 0.0)  # From tip
            gl.glVertex3f(corner[0], corner[1], corner[2])  # To corner
        
        # Draw base rectangle outline
        for i in range(4):
            corner1 = base_corners[i]
            corner2 = base_corners[(i + 1) % 4]
            
            gl.glVertex3f(corner1[0], corner1[1], corner1[2])
            gl.glVertex3f(corner2[0], corner2[1], corner2[2])
        
        gl.glEnd()
    
    def _render_hexahedron(self, direction, horizontal, vertical, base_corners):
        """Render hexahedron (truncated pyramid) by cutting at near plane."""
        # Calculate near plane position
        near_plane_pos = direction * self.near_plane_distance * self.radius
        
        # For proper truncation, interpolate along the pyramid's existing edges
        # The pyramid goes from tip (0,0,0) to base_corners
        # Near plane cuts at distance near_plane_distance along the pyramid length
        
        # Use fixed base radius so pyramid size is independent of sphere scale
        base_radius = 1.0
        full_length = self.pyramid_length * base_radius
        if self.near_plane_distance >= full_length:
            # Near plane is beyond the pyramid, render nothing
            return
        
        # Calculate interpolation factor (0 = at tip, 1 = at base)
        t = self.near_plane_distance / full_length
        
        # Calculate the four corners of the near plane by interpolating from tip to each base corner
        near_corners = []
        for base_corner in base_corners:
            # Interpolate from tip (0,0,0) to base_corner
            near_corner = t * base_corner  # t=0 gives tip, t=1 gives base_corner
            near_corners.append(near_corner)
        
        # Render hexahedron faces as triangles
        gl.glBegin(gl.GL_TRIANGLES)
        
        # Four trapezoidal faces (each split into 2 triangles)
        for i in range(4):
            next_i = (i + 1) % 4
            
            # Bottom triangle of trapezoid (near plane)
            gl.glVertex3f(near_corners[i][0], near_corners[i][1], near_corners[i][2])
            gl.glVertex3f(near_corners[next_i][0], near_corners[next_i][1], near_corners[next_i][2])
            gl.glVertex3f(base_corners[next_i][0], base_corners[next_i][1], base_corners[next_i][2])
            
            # Top triangle of trapezoid
            gl.glVertex3f(near_corners[i][0], near_corners[i][1], near_corners[i][2])
            gl.glVertex3f(base_corners[next_i][0], base_corners[next_i][1], base_corners[next_i][2])
            gl.glVertex3f(base_corners[i][0], base_corners[i][1], base_corners[i][2])
        
        # Near plane (smaller rectangle) - split into two triangles
        # Triangle 1: corners 0, 1, 2
        gl.glVertex3f(near_corners[0][0], near_corners[0][1], near_corners[0][2])
        gl.glVertex3f(near_corners[1][0], near_corners[1][1], near_corners[1][2])
        gl.glVertex3f(near_corners[2][0], near_corners[2][1], near_corners[2][2])
        
        # Triangle 2: corners 0, 2, 3
        gl.glVertex3f(near_corners[0][0], near_corners[0][1], near_corners[0][2])
        gl.glVertex3f(near_corners[2][0], near_corners[2][1], near_corners[2][2])
        gl.glVertex3f(near_corners[3][0], near_corners[3][1], near_corners[3][2])
        
        # Base (larger rectangle) - split into two triangles
        # Triangle 1: corners 0, 1, 2
        gl.glVertex3f(base_corners[0][0], base_corners[0][1], base_corners[0][2])
        gl.glVertex3f(base_corners[1][0], base_corners[1][1], base_corners[1][2])
        gl.glVertex3f(base_corners[2][0], base_corners[2][1], base_corners[2][2])
        
        # Triangle 2: corners 0, 2, 3
        gl.glVertex3f(base_corners[0][0], base_corners[0][1], base_corners[0][2])
        gl.glVertex3f(base_corners[2][0], base_corners[2][1], base_corners[2][2])
        gl.glVertex3f(base_corners[3][0], base_corners[3][1], base_corners[3][2])
    
        gl.glEnd()
        
        # Render hexahedron outline wireframe
        gl.glColor4f(self.pyramid_color[0], self.pyramid_color[1], self.pyramid_color[2], 1.0)
        gl.glLineWidth(2.0)
    
        gl.glBegin(gl.GL_LINES)
        
        # Draw near plane rectangle outline
        for i in range(4):
            corner1 = near_corners[i]
            corner2 = near_corners[(i + 1) % 4]
            gl.glVertex3f(corner1[0], corner1[1], corner1[2])
            gl.glVertex3f(corner2[0], corner2[1], corner2[2])
        
        # Draw base rectangle outline
        for i in range(4):
            corner1 = base_corners[i]
            corner2 = base_corners[(i + 1) % 4]
            gl.glVertex3f(corner1[0], corner1[1], corner1[2])
            gl.glVertex3f(corner2[0], corner2[1], corner2[2])
        
        # Draw connecting lines between near and base planes
        for i in range(4):
            gl.glVertex3f(near_corners[i][0], near_corners[i][1], near_corners[i][2])
            gl.glVertex3f(base_corners[i][0], base_corners[i][1], base_corners[i][2])
        
        gl.glEnd()
    
    def render_cuboid(self, manage_blend=True):
        """Render rectangular cuboid or smaller cuboid when near plane cuts it."""
        if not self.cuboid_enabled:
            return
        
        # Use vector direction for cuboid central axis
        direction = self.vector_direction / np.linalg.norm(self.vector_direction)
        
        # Create orthogonal coordinate system
        # Find a vector perpendicular to direction for width axis
        if abs(direction[0]) < 0.9:
            width_axis = np.array([0.0, direction[2], -direction[1]])
        else:
            width_axis = np.array([-direction[2], 0.0, direction[0]])
        
        width_axis = width_axis / np.linalg.norm(width_axis)
        
        # Height axis is perpendicular to both direction and width
        height_axis = np.cross(direction, width_axis)
        height_axis = height_axis / np.linalg.norm(height_axis)
        
        # Set cuboid color and enable blending for transparency (only if managing blend state)
        if manage_blend:
            gl.glEnable(gl.GL_BLEND)
            gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
            gl.glColor4f(*self.cuboid_color)
        
        # Disable lighting for cuboid (we want uniform color)
        lighting_was_enabled = self.lighting_enabled
        if lighting_was_enabled:
            gl.glDisable(gl.GL_LIGHTING)
        
        if self.near_plane_enabled and self.near_plane_distance > 0:
            # Create a smaller cuboid starting from near plane
            self._render_truncated_cuboid(direction, width_axis, height_axis)
        else:
            # Render full cuboid
            self._render_full_cuboid(direction, width_axis, height_axis)
        
        # Re-enable lighting if it was enabled
        if lighting_was_enabled:
            gl.glEnable(gl.GL_LIGHTING)
        
        # Disable blend only if we enabled it
        if manage_blend:
            gl.glDisable(gl.GL_BLEND)
    
    def _render_full_cuboid(self, direction, width_axis, height_axis):
        """Render full cuboid centered on sphere."""
        if self.cuboid_infinite:
            # For infinite cuboid, render as 4-sided pyramid (far face vanishes)
            self._render_infinite_cuboid_as_pyramid(direction, width_axis, height_axis)
            return
        
        # Calculate half-dimensions for finite cuboid - use fixed size regardless of sphere scale
        base_radius = 1.0  # Use fixed base radius so cuboid size is independent of sphere scale
        half_length = (self.cuboid_length * base_radius) / 2.0
        half_width = (self.cuboid_width * base_radius) / 2.0
        half_height = (self.cuboid_height * base_radius) / 2.0
        
        # Calculate the 8 corners of the cuboid
        # Center the cuboid so it extends from sphere center along vector direction
        center_offset = direction * half_length
        
        corners = []
        for length_sign in [-1, 1]:
            for width_sign in [-1, 1]:
                for height_sign in [-1, 1]:
                    corner = (center_offset +
                             direction * (length_sign * half_length) +
                             width_axis * (width_sign * half_width) +
                             height_axis * (height_sign * half_height))
                    corners.append(corner)
        
        self._render_cuboid_geometry(corners)
    
    def _render_truncated_cuboid(self, direction, width_axis, height_axis):
        """Render smaller cuboid starting from near plane."""
        # Calculate near plane position
        # Calculate near plane position - use fixed base size regardless of sphere scale
        base_radius = 1.0
        near_plane_pos = direction * self.near_plane_distance * base_radius
        
        # Calculate remaining length after near plane cut
        if self.cuboid_infinite:
            # For infinite cuboid, always render from near plane to a large distance
            full_length = 50.0 * base_radius
            remaining_length = full_length - self.near_plane_distance * base_radius
        else:
            full_length = self.cuboid_length * base_radius
            remaining_length = full_length - self.near_plane_distance * base_radius
        
        if remaining_length <= 0:
            # Near plane cuts beyond the cuboid, nothing to render
            return
        
        # Use same width and height as original cuboid
        half_width = (self.cuboid_width * base_radius) / 2.0
        half_height = (self.cuboid_height * base_radius) / 2.0
        
        # Calculate center of the smaller cuboid
        smaller_center = near_plane_pos + direction * (remaining_length / 
2.0)
        half_remaining_length = remaining_length / 2.0
        
        # Calculate the 8 corners of the smaller cuboid
        corners = []
        for length_sign in [-1, 1]:
            for width_sign in [-1, 1]:
                for height_sign in [-1, 1]:
                    corner = (smaller_center +
                             direction * (length_sign * half_remaining_length) +
                             width_axis * (width_sign * half_width) +
                             height_axis * (height_sign * half_height))
                    corners.append(corner)
        
        self._render_cuboid_geometry(corners)
    
    def _render_cuboid_geometry(self, corners):
        """Render cuboid geometry given 8 corner vertices."""
        # Define the 6 faces of the cuboid (each face is 2 triangles)
        # Face indices for the 8 corners arranged as:
        # 0: (-length, -width, -height), 1: (+length, -width, -height)
        # 2: (-length, +width, -height), 3: (+length, +width, -height)
        # 4: (-length, -width, +height), 5: (+length, -width, +height)
        # 6: (-length, +width, +height), 7: (+length, +width, +height)
        
        faces = [
                # Front face (positive length)
        [1, 3, 7, 5],
                # Back face (negative length)
        [0, 4, 6, 2],
                # Right face (positive width)
        [2, 6, 7, 3],
                # Left face (negative width)
        [0, 1, 5, 4],
                # Top face (positive height)
        [4, 5, 7, 6],
                # Bottom face (negative height)
        [0, 2, 3, 1]
        ]
        
        # Render cuboid faces as triangles
        gl.glBegin(gl.GL_TRIANGLES)
        
        for face in faces:
            # Split each quad face into two triangles
            # Triangle 1: corners 0, 1, 2
            for i in [0, 1, 2]:
                corner = corners[face[i]]
                gl.glVertex3f(corner[0], corner[1], corner[2])
                
            # Triangle 2: corners 0, 2, 3
            for i in [0, 2, 3]:
                corner = corners[face[i]]
                gl.glVertex3f(corner[0], corner[1], corner[2])
        
        gl.glEnd()
        
        # Render cuboid wireframe outline for better visibility
        gl.glColor4f(self.cuboid_color[0], self.cuboid_color[1], self.cuboid_color[2], 1.0)
        gl.glLineWidth(1.0)
    
        gl.glBegin(gl.GL_LINES)
        
        # Draw the 12 edges of the cuboid
        edges = [
        # Bottom face edges
        [0, 1], [1, 3], [3, 2], [2, 0],
        # Top face edges  
        [4, 5], [5, 7], [7, 6], [6, 4],
        # Vertical edges
        [0, 4], [1, 5], [2, 6], [3, 7]
        ]
        
        for edge in edges:
            for vertex_idx in edge:
                corner = corners[vertex_idx]
                gl.glVertex3f(corner[0], corner[1], corner[2])
        
        gl.glEnd()
    
    def _render_infinite_cuboid_as_pyramid(self, direction, width_axis, height_axis):
        """Render infinite cuboid with normal size at center and infinite extension."""
        # Calculate the dimensions for the central cuboid - use fixed size regardless of sphere scale
        base_radius = 1.0  # Use fixed base radius so cuboid size is independent of sphere scale
        half_length = (self.cuboid_length * base_radius) / 2.0
        half_width = (self.cuboid_width * base_radius) / 2.0
        half_height = (self.cuboid_height * base_radius) / 2.0
        
        # First, render the normal-sized cuboid at the center
        center_offset = direction * half_length
        
        # Calculate the 8 corners of the central cuboid
        corners = []
        for length_sign in [-1, 1]:
            for width_sign in [-1, 1]:
                for height_sign in [-1, 1]:
                    corner = (center_offset +
                             direction * (length_sign * half_length) +
                             width_axis * (width_sign * half_width) +
                             height_axis * (height_sign * half_height))
                    corners.append(corner)
        
        # Render the central cuboid geometry
        self._render_cuboid_geometry(corners)
        
        # Now render the infinite extension rays from the far face
        # Use a large distance for the "infinite" end - use fixed size regardless of sphere scale
        infinite_distance = 50.0 * base_radius
        
        # Get the four corners of the far face (where the cuboid ends)
        far_face_center = direction * (half_length * 2)  # Far end of the central cuboid
        far_face_corners = [
            far_face_center + width_axis * half_width + height_axis * half_height,    # Top-right
            far_face_center - width_axis * half_width + height_axis * half_height,    # Top-left
            far_face_center - width_axis * half_width - height_axis * half_height,    # Bottom-left
            far_face_center + width_axis * half_width - height_axis * half_height     # Bottom-right
        ]
        
        # Calculate infinite extension points
        infinite_corners = []
        for corner in far_face_corners:
            # Extend from the far face corner to infinity in the same direction
            infinite_point = corner + direction * infinite_distance
            infinite_corners.append(infinite_point)
        
        # Render infinite extension rays
        gl.glBegin(gl.GL_LINES)
        for i in range(4):
            # Line from far face corner to infinite distance
            gl.glVertex3f(far_face_corners[i][0], far_face_corners[i][1], far_face_corners[i][2])
            gl.glVertex3f(infinite_corners[i][0], infinite_corners[i][1], infinite_corners[i][2])
        
        gl.glEnd()
    
    def render(self):
        """Render the complete sphere with all active grid systems."""
        self.apply_transformation_matrix()
        
        # For proper transparency, render in back-to-front order
        if self.transparency < 1.0 and not self.wireframe_mode:
            # First render grids (they're behind the transparent sphere)
            self.render_longitude_latitude_grid()
            self.render_concentric_circles()
            self.render_dot_particles()
            self.render_neon_lines()
            self.render_wireframe()
            
            # Then render transparent sphere surface
            self.render_sphere_surface()
        else:
            # Always render sphere surface (solid or wireframe)
            self.render_sphere_surface()
            
            # Render all active grid systems (but not the wireframe grid if we're in wireframe mode)
            self.render_longitude_latitude_grid()
            self.render_concentric_circles()
            self.render_dot_particles()
            self.render_neon_lines()
            
        # Only render wireframe grid if not in wireframe mode (to avoid double wireframe)
        if not self.wireframe_mode:
            self.render_wireframe()
        
        gl.glPopMatrix()  # End sphere transformation matrix (position, rotation, scale)
        
        # Render shapes OUTSIDE the sphere's scale transformation
        # Apply only sphere position and rotation, but NOT scale
        gl.glPushMatrix()
        gl.glTranslatef(self.position[0], self.position[1], self.position[2])
        gl.glRotatef(self.rotation[0], 1, 0, 0)  # Pitch
        gl.glRotatef(self.rotation[1], 0, 1, 0)  # Yaw
        gl.glRotatef(self.rotation[2], 0, 0, 1)  # Roll
        # NOTE: No glScalef here - shapes maintain their own size regardless of sphere scale
        
        # Render shapes with proper transparency handling
        # For transparent objects, disable depth writes and render back-to-front
        
        # Check if any shapes are transparent
        shapes_transparent = (
            (self.cone_enabled and self.cone_color[3] < 1.0) or
            (self.pyramid_enabled and self.pyramid_color[3] < 1.0) or
            (self.cuboid_enabled and self.cuboid_color[3] < 1.0)
        )
        
        if shapes_transparent:
            # Disable depth writing for transparent shapes
            gl.glDepthMask(gl.GL_FALSE)
            gl.glEnable(gl.GL_BLEND)
            gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
            
            # Render shapes back-to-front (roughly ordered by distance from center)
            # Cuboid is closest to center, then pyramid, then cone (extends furthest)
            if self.cuboid_enabled:
                self.render_cuboid(manage_blend=False)
            if self.pyramid_enabled:
                self.render_pyramid(manage_blend=False)
            if self.cone_enabled:
                self.render_cone(manage_blend=False)
            
            # Re-enable depth writing
            gl.glDepthMask(gl.GL_TRUE)
            gl.glDisable(gl.GL_BLEND)
        else:
            # Render shapes normally (opaque)
            if self.cone_enabled:
                self.render_cone()
            if self.pyramid_enabled:
                self.render_pyramid()
            if self.cuboid_enabled:
                self.render_cuboid()
        
        # Render sphere intersections if enabled (on sphere surface)
        if self.sphere_intersection_enabled:
            self.render_sphere_intersections()
        
        # Render normal rays if enabled
        if self.normal_rays_enabled:
            self.render_normal_rays()
        
        # Render intersection normal rays if enabled
        if self.intersection_normals_enabled:
            self.render_intersection_normal_rays()
        
        # Render truncation normal rays if enabled
        if self.truncation_normals_enabled:
            self.render_truncation_normal_rays()
        
        # Always render vector last (on top of everything)
        # Render vector if enabled (but not when stepped into a screen to avoid obstruction)
        if self.vector_enabled and not self._is_stepped_into_screen():
            self.render_vector()
        
        # Render custom shapes (outside sphere transformation)
        self.render_shapes()
        
        gl.glPopMatrix()  # End shapes transformation matrix
        
        # Render 2D screen with ray-traced image (outside transformation matrix)
        # Only render if canvas is in raytracing mode and screen is enabled
        if hasattr(self, '_canvas_ref') and self._canvas_ref:
            canvas_enabled = self._canvas_ref.screen_enabled
            canvas_mode = self._canvas_ref.screen_render_mode
            # Check for ray tracing in either canvas or sphere mode
            is_ray_tracing_mode = (canvas_mode == "raytracing" or self.screen_render_mode == "ray_tracing")
            should_render = canvas_enabled and is_ray_tracing_mode
            # Debug the render mode mismatch
            print(f"DEBUG: Canvas mode: '{canvas_mode}', Sphere mode: '{self.screen_render_mode}'")
            sphere_enabled = self.screen_enabled
            print(f"DEBUG: Sphere screen render check - canvas_enabled: {canvas_enabled}, canvas_mode: {canvas_mode}, sphere_enabled: {sphere_enabled}, should_render: {should_render}")
            if should_render:
                print(f"DEBUG: Sphere rendering ray tracing screen")
                self.render_screen_geometry()
            else:
                print(f"DEBUG: Sphere skipping screen render (canvas mode: {canvas_mode})")
        else:
            # Fallback: render if screen is enabled (for backward compatibility)
            if self.screen_enabled:
                print(f"DEBUG: Sphere rendering screen (fallback mode)")
                self.render_screen_geometry()
            else:
                print(f"DEBUG: Sphere screen disabled (fallback mode)")
    
    def render_sphere_intersections(self):
        """Render sphere surface areas where shapes intersect the sphere."""
        # Set intersection color and enable blending
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glColor4f(*self.sphere_intersection_color)
        
        # Disable lighting for intersection areas (we want uniform color)
        lighting_was_enabled = self.lighting_enabled
        if lighting_was_enabled:
            gl.glDisable(gl.GL_LIGHTING)
        
        # Render intersection areas for each enabled shape
        if self.cone_enabled:
            self._render_sphere_cone_intersection()
        if self.pyramid_enabled:
            self._render_sphere_pyramid_intersection()
        if self.cuboid_enabled:
            self._render_sphere_cuboid_intersection()
        
        # Re-enable lighting if it was enabled
        if lighting_was_enabled:
            gl.glEnable(gl.GL_LIGHTING)
        
        gl.glDisable(gl.GL_BLEND)
    
    def render_normal_rays(self):
        """Render normal rays (surface normals) extending from sphere surface."""
        # Set normal ray color and properties
        gl.glColor4f(*self.normal_rays_color)
        gl.glLineWidth(self.normal_rays_thickness)
        
        # Disable lighting for rays (we want uniform color)
        lighting_was_enabled = self.lighting_enabled
        if lighting_was_enabled:
            gl.glDisable(gl.GL_LIGHTING)
        
        # Calculate ray length - use fixed base radius so ray length is independent of sphere scale
        base_radius = 1.0
        ray_length = self.normal_rays_length * base_radius
        
        gl.glBegin(gl.GL_LINES)
        
        # Generate rays using spherical coordinates
        density = self.normal_rays_density
        
        # Create rays at regular intervals across the sphere surface
        for i in range(density):
            for j in range(density):
                # Spherical coordinates (theta = azimuth, phi = polar angle)
                theta = 2 * math.pi * i / density  # 0 to 2π
                phi = math.pi * j / density        # 0 to π
                        
                # Skip poles to avoid degenerate cases
                if j == 0 or j == density - 1:
                    continue
                
                # Point on sphere surface
                x = self.radius * math.sin(phi) * math.cos(theta)
                y = self.radius * math.sin(phi) * math.sin(theta)
                z = self.radius * math.cos(phi)
                sphere_point = np.array([x, y, z])
                    
                # Normal vector at this point (for a sphere, normal = position / radius)
                normal_vector = sphere_point / self.radius
                
                # End point of the ray
                ray_end = sphere_point + normal_vector * ray_length
                
                # Draw the ray
                gl.glVertex3f(sphere_point[0], sphere_point[1], sphere_point[2])
                gl.glVertex3f(ray_end[0], ray_end[1], ray_end[2])
            
        gl.glEnd()
        
        # Re-enable lighting if it was enabled
        if lighting_was_enabled:
            gl.glEnable(gl.GL_LIGHTING)
        
        gl.glLineWidth(1.0)  # Reset line width
    
    def render_intersection_normal_rays(self):
        """Render normal rays only on sphere intersection surfaces."""
        # Set intersection normal ray color and properties
        gl.glColor4f(*self.intersection_normals_color)
        gl.glLineWidth(self.intersection_normals_thickness)
        
        # Disable lighting for rays (we want uniform color)
        lighting_was_enabled = self.lighting_enabled
        if lighting_was_enabled:
            gl.glDisable(gl.GL_LIGHTING)
        
        # Calculate ray length - use fixed base radius so ray length is independent of sphere scale
        base_radius = 1.0
        ray_length = self.intersection_normals_length * base_radius
    
        gl.glBegin(gl.GL_LINES)
        
        # Render normals for each enabled shape intersection
        if self.cone_enabled:
            self._render_cone_intersection_normals(ray_length)
        if self.pyramid_enabled:
            self._render_pyramid_intersection_normals(ray_length)
        if self.cuboid_enabled:
            self._render_cuboid_intersection_normals(ray_length)
        
        gl.glEnd()
        
        # Re-enable lighting if it was enabled
        if lighting_was_enabled:
            gl.glEnable(gl.GL_LIGHTING)
        
        gl.glLineWidth(1.0)  # Reset line width
    
    def render_truncation_normal_rays(self):
        """Render normal rays on truncation surfaces (near plane cuts)."""
        # Only render if near plane is enabled and at least one shape is enabled
        if not self.near_plane_enabled or self.near_plane_distance <= 0:
            return
        
        # Set truncation normal ray color and properties
        gl.glColor4f(*self.truncation_normals_color)
        gl.glLineWidth(self.truncation_normals_thickness)
        
        # Disable lighting for rays (we want uniform color)
        lighting_was_enabled = self.lighting_enabled
        if lighting_was_enabled:
            gl.glDisable(gl.GL_LIGHTING)
        
        # Calculate ray length - use fixed base radius so ray length is independent of sphere scale
        base_radius = 1.0
        ray_length = self.truncation_normals_length * base_radius
    
        gl.glBegin(gl.GL_LINES)
        
        # Render normals for each enabled shape's truncation surface
        if self.cone_enabled:
            self._render_cone_truncation_normals(ray_length)
        if self.pyramid_enabled:
            self._render_pyramid_truncation_normals(ray_length)
        if self.cuboid_enabled:
            self._render_cuboid_truncation_normals(ray_length)
        
        gl.glEnd()
        
        # Re-enable lighting if it was enabled
        if lighting_was_enabled:
            gl.glEnable(gl.GL_LIGHTING)
        
            gl.glLineWidth(1.0)  # Reset line width
    
    def _render_cone_truncation_normals(self, ray_length):
        """Render normal rays on cone truncation surface."""
        # Get vector direction and near plane parameters
        direction = self.vector_direction / np.linalg.norm(self.vector_direction)
        
        # Near plane position along the vector - use fixed base radius so position is independent of sphere scale
        base_radius = 1.0
        near_plane_position = self.near_plane_distance * base_radius
        near_plane_center = direction * near_plane_position
        
        # The normal to the truncation plane is the vector direction
        plane_normal = direction
        
        # Create perpendicular vectors for circular pattern
        if abs(direction[0]) < 0.9:
            perp1 = np.array([0.0, direction[2], -direction[1]])
        else:
            perp1 = np.array([-direction[2], 0.0, direction[0]])
        
        perp1 = perp1 / np.linalg.norm(perp1)
        perp2 = np.cross(direction, perp1)
        perp2 = perp2 / np.linalg.norm(perp2)
        
        # Calculate cone radius at truncation plane
        cone_angle_rad = math.radians(self.cone_angle)
        truncation_radius = near_plane_position * math.tan(cone_angle_rad)
        
        # Generate normal rays on the circular truncation surface
        density = self.truncation_normals_density
        
        # Center ray
        ray_start = near_plane_center
        ray_end = ray_start + plane_normal * ray_length
        gl.glVertex3f(ray_start[0], ray_start[1], ray_start[2])
        gl.glVertex3f(ray_end[0], ray_end[1], ray_end[2])
        
        # Circular pattern of rays
        for i in range(density):
            for j in range(2):  # Two rings
                angle = 2 * math.pi * i / density
                radius = truncation_radius * (j + 1) / 2  # Inner and outer ring
                
                # Point on truncation surface
                surface_point = (near_plane_center +
                perp1 * (radius * math.cos(angle)) +
                perp2 * (radius * math.sin(angle)))
                
                # Normal ray from this point
                ray_start = surface_point
                ray_end = ray_start + plane_normal * ray_length
                
                gl.glVertex3f(ray_start[0], ray_start[1], ray_start[2])
                gl.glVertex3f(ray_end[0], ray_end[1], ray_end[2])
    
    def _render_pyramid_truncation_normals(self, ray_length):
        """Render normal rays on pyramid truncation surface."""
        # Get vector direction and near plane parameters
        direction = self.vector_direction / np.linalg.norm(self.vector_direction)
        
        # Create orthogonal coordinate system
        if abs(direction[0]) < 0.9:
            horizontal = np.array([0.0, direction[2], -direction[1]])
        else:
            horizontal = np.array([-direction[2], 0.0, direction[0]])
            
        horizontal = horizontal / np.linalg.norm(horizontal)
        vertical = np.cross(direction, horizontal)
        vertical = vertical / np.linalg.norm(vertical)
        
        # Near plane position along the vector - use fixed base radius so position is independent of sphere scale
        base_radius = 1.0
        near_plane_position = self.near_plane_distance * base_radius
        near_plane_center = direction * near_plane_position
        
        # The normal to the truncation plane is the vector direction
        plane_normal = direction
        
        # Calculate pyramid dimensions at truncation plane
        h_angle_rad = math.radians(self.pyramid_angle_horizontal)
        v_angle_rad = math.radians(self.pyramid_angle_vertical)
        half_width = near_plane_position * math.tan(h_angle_rad)
        half_height = near_plane_position * math.tan(v_angle_rad)
        
        # Generate normal rays on the rectangular truncation surface
        density = self.truncation_normals_density
        
        for i in range(density):
            for j in range(density):
                # Parametric coordinates on truncation surface (-1 to 1)
                u = (i / (density - 1) - 0.5) * 2 if density > 1 else 0
                v = (j / (density - 1) - 0.5) * 2 if density > 1 else 0
                
                # Point on truncation surface
                surface_point = (near_plane_center +
                horizontal * (u * half_width) +
                vertical * (v * half_height))
                
                # Normal ray from this point
                ray_start = surface_point
                ray_end = ray_start + plane_normal * ray_length
                    
                gl.glVertex3f(ray_start[0], ray_start[1], ray_start[2])
                gl.glVertex3f(ray_end[0], ray_end[1], ray_end[2])
    
    def _render_cuboid_truncation_normals(self, ray_length):
        """Render normal rays on cuboid truncation surface."""
        # Get vector direction and near plane parameters
        direction = self.vector_direction / np.linalg.norm(self.vector_direction)
        
        # Create orthogonal coordinate system
        if abs(direction[0]) < 0.9:
            width_axis = np.array([0.0, direction[2], -direction[1]])
        else:
            width_axis = np.array([-direction[2], 0.0, direction[0]])
        
        width_axis = width_axis / np.linalg.norm(width_axis)
        height_axis = np.cross(direction, width_axis)
        height_axis = height_axis / np.linalg.norm(height_axis)
        
        # Near plane position along the vector - use fixed base radius so position is independent of sphere scale
        base_radius = 1.0
        near_plane_position = self.near_plane_distance * base_radius
        near_plane_center = direction * near_plane_position
        
        # The normal to the truncation plane is the vector direction
        plane_normal = direction
        
        # Cuboid dimensions (constant along its length)
        half_width = self.cuboid_width / 2.0
        half_height = self.cuboid_height / 2.0
        
        # Generate normal rays on the rectangular truncation surface
        density = self.truncation_normals_density
        
        for i in range(density):
            for j in range(density):
                # Parametric coordinates on truncation surface (-1 to 1)
                u = (i / (density - 1) - 0.5) * 2 if density > 1 else 0
                v = (j / (density - 1) - 0.5) * 2 if density > 1 else 0
                
                # Point on truncation surface
                surface_point = (near_plane_center +
                width_axis * (u * half_width) +
                height_axis * (v * half_height))
                
                # Normal ray from this point
                ray_start = surface_point
                ray_end = ray_start + plane_normal * ray_length
                
                gl.glVertex3f(ray_start[0], ray_start[1], ray_start[2])
                gl.glVertex3f(ray_end[0], ray_end[1], ray_end[2])
    
    def _render_cone_intersection_normals(self, ray_length):
        """Render normal rays on cone intersection surface."""
        # Get vector direction and cone parameters
        direction = self.vector_direction / np.linalg.norm(self.vector_direction)
        cone_angle_rad = math.radians(self.cone_angle)
        
        # Create perpendicular vectors
        if abs(direction[0]) < 0.9:
            perp1 = np.array([0.0, direction[2], -direction[1]])
        else:
            perp1 = np.array([-direction[2], 0.0, direction[0]])
        
        perp1 = perp1 / np.linalg.norm(perp1)
        perp2 = np.cross(direction, perp1)
        perp2 = perp2 / np.linalg.norm(perp2)
        
        # Generate normal rays on the spherical cap
        density = self.intersection_normals_density
        
        for i in range(density):
            for j in range(int(density * cone_angle_rad / math.pi)):  # Scale by cone angle
                angle = 2 * math.pi * i / density
                ring_angle = cone_angle_rad * j / int(density * cone_angle_rad / math.pi)
                
                # Point on sphere surface within cone
                sphere_direction = (direction * math.cos(ring_angle) +
                (perp1 * math.cos(angle) + perp2 * math.sin(angle)) * math.sin(ring_angle))
                sphere_point = sphere_direction / np.linalg.norm(sphere_direction) * self.radius
                
                # Normal vector (same as position for sphere)
                normal_vector = sphere_point / self.radius
                ray_end = sphere_point + normal_vector * ray_length
                
                # Draw the ray
                gl.glVertex3f(sphere_point[0], sphere_point[1], sphere_point[2])
                gl.glVertex3f(ray_end[0], ray_end[1], ray_end[2])
    
    def _render_pyramid_intersection_normals(self, ray_length):
        """Render normal rays on pyramid intersection surface."""
        # Get vector direction and pyramid parameters
        direction = self.vector_direction / np.linalg.norm(self.vector_direction)
        
        # Create orthogonal coordinate system
        if abs(direction[0]) < 0.9:
            horizontal = np.array([0.0, direction[2], -direction[1]])
        else:
            horizontal = np.array([-direction[2], 0.0, direction[0]])
        
        horizontal = horizontal / np.linalg.norm(horizontal)
        vertical = np.cross(direction, horizontal)
        vertical = vertical / np.linalg.norm(vertical)
        
        # Calculate pyramid angles
        h_angle_rad = math.radians(self.pyramid_angle_horizontal)
        v_angle_rad = math.radians(self.pyramid_angle_vertical)
        # Use fixed base radius so pyramid size is independent of sphere scale
        base_radius = 1.0
        pyramid_length = self.pyramid_length * base_radius
        
        # Generate normal rays within pyramid bounds
        density = self.intersection_normals_density
        
        for i in range(density):
            for j in range(density):
                # Map to angular coordinates within pyramid bounds
                angle_u = (i / density - 0.5) * 2 * h_angle_rad
                angle_v = (j / density - 0.5) * 2 * v_angle_rad
                
                # Create direction vector from angles
                point_direction = (direction +
                horizontal * math.tan(angle_u) +
                vertical * math.tan(angle_v))
                
                # Normalize to get point on sphere surface
                direction_length = np.linalg.norm(point_direction)
                if direction_length > 0:
                    sphere_point = point_direction / direction_length * self.radius
                    
                    # Verify this point is within the pyramid bounds
                    length_proj = np.dot(sphere_point, direction)
                    width_proj = np.dot(sphere_point, horizontal)
                    height_proj = np.dot(sphere_point, vertical)
                    
                    # Check if within pyramid
                    if length_proj > 0 and length_proj <= pyramid_length:
                        pyramid_half_width = length_proj * math.tan(h_angle_rad)
                        pyramid_half_height = length_proj * math.tan(v_angle_rad)
                                        
                        if (abs(width_proj) <= pyramid_half_width and
                        abs(height_proj) <= pyramid_half_height):
                            
                            # Normal vector (same as position for sphere)
                            normal_vector = sphere_point / self.radius
                            ray_end = sphere_point + normal_vector * ray_length
                            
                            # Draw the ray
                            gl.glVertex3f(sphere_point[0], sphere_point[1], sphere_point[2])
                            gl.glVertex3f(ray_end[0], ray_end[1], ray_end[2])
    
    def _render_cuboid_intersection_normals(self, ray_length):
        """Render normal rays on cuboid intersection surface."""
        # Get vector direction and cuboid parameters
        direction = self.vector_direction / np.linalg.norm(self.vector_direction)
        
        # Create orthogonal coordinate system
        if abs(direction[0]) < 0.9:
            width_axis = np.array([0.0, direction[2], -direction[1]])
        else:
            width_axis = np.array([-direction[2], 0.0, direction[0]])
        
        width_axis = width_axis / np.linalg.norm(width_axis)
        height_axis = np.cross(direction, width_axis)
        height_axis = height_axis / np.linalg.norm(height_axis)
        
        # Calculate the cuboid's dimensions
        half_width = self.cuboid_width / 2.0
        half_height = self.cuboid_height / 2.0
        # Use fixed base radius so cuboid size is independent of sphere scale
        base_radius = 1.0
        if self.cuboid_infinite:
            cuboid_length = 50.0 * base_radius
        else:
            cuboid_length = self.cuboid_length * base_radius
        
        # Generate normal rays within cuboid bounds
        density = self.intersection_normals_density
        
        for i in range(density):
            for j in range(density):
                # Parametric coordinates
                u = (i / density - 0.5) * 2  # -1 to 1
                v = (j / density - 0.5) * 2  # -1 to 1
                
                # Map to cuboid coordinates (sample at middle of cuboid length)
                length = cuboid_length * 0.5
                width = half_width * u
                height = half_height * v
                
                # Point in 3D space
                cuboid_point = (direction * length +
                width_axis * width +
                height_axis * height)
                
                # Project to sphere surface
                distance = np.linalg.norm(cuboid_point)
                if distance > 0:
                    sphere_point = cuboid_point / distance * self.radius
                            
                    # Check if within cuboid bounds
                    length_proj = np.dot(sphere_point, direction)
                    width_proj = np.dot(sphere_point, width_axis)
                    height_proj = np.dot(sphere_point, height_axis)
                            
                    inside = (0 <= length_proj <= cuboid_length and
                    -half_width <= width_proj <= half_width and
                    -half_height <= height_proj <= half_height)
                            
                if inside:
                    # Normal vector (same as position for sphere)
                    normal_vector = sphere_point / self.radius
                    ray_end = sphere_point + normal_vector * ray_length
                                
                    # Draw the ray
                    gl.glVertex3f(sphere_point[0], sphere_point[1], sphere_point[2])
                    gl.glVertex3f(ray_end[0], ray_end[1], ray_end[2])
    
    def _render_sphere_cone_intersection(self):
        """Render the spherical cap surface that's inside the cone."""
        # Disable face culling to ensure visibility from all angles
        gl.glDisable(gl.GL_CULL_FACE)
        
        # Get vector direction
        direction = self.vector_direction / np.linalg.norm(self.vector_direction)
        
        # For a cone with half-angle, we want to show the spherical cap that's inside the cone
        cone_angle_rad = math.radians(self.cone_angle)
        
        # Create perpendicular vectors for the circular intersection
        if abs(direction[0]) < 0.9:
            perp1 = np.array([0.0, direction[2], -direction[1]])
        else:
            perp1 = np.array([-direction[2], 0.0, direction[0]])
        
        perp1 = perp1 / np.linalg.norm(perp1)
        perp2 = np.cross(direction, perp1)
        perp2 = perp2 / np.linalg.norm(perp2)
        
        # The spherical cap extends from the sphere center along the vector direction
        # up to the cone boundary angle
        resolution = self.cone_resolution
        
        # Render the spherical cap as triangular segments
        gl.glBegin(gl.GL_TRIANGLES)
        
        # Center point on sphere surface along vector direction
        center_point = direction * self.radius
        
        for i in range(resolution):
            angle1 = 2 * math.pi * i / resolution
            angle2 = 2 * math.pi * ((i + 1) % resolution) / resolution
            
            # Create rings from center to cone boundary
            num_rings = 8
            for ring in range(num_rings):
                # Current and next ring angles (from center to cone boundary)
                ring_angle1 = cone_angle_rad * ring / num_rings
                ring_angle2 = cone_angle_rad * (ring + 1) / num_rings
                
                # Points on sphere surface at these angles - these are already normalized unit vectors
                # pointing in the right direction, so we just multiply by radius
                direction1 = (direction * math.cos(ring_angle1) +
                (perp1 * math.cos(angle1) + perp2 * math.sin(angle1)) * math.sin(ring_angle1))
                direction2 = (direction * math.cos(ring_angle1) +
                (perp1 * math.cos(angle2) + perp2 * math.sin(angle2)) * math.sin(ring_angle1))
                direction3 = (direction * math.cos(ring_angle2) +
                (perp1 * math.cos(angle1) + perp2 * math.sin(angle1)) * math.sin(ring_angle2))
                direction4 = (direction * math.cos(ring_angle2) +
                (perp1 * math.cos(angle2) + perp2 * math.sin(angle2)) * math.sin(ring_angle2))
                
                # Ensure these are unit vectors and scale to sphere radius
                point1 = direction1 / np.linalg.norm(direction1) * self.radius
                point2 = direction2 / np.linalg.norm(direction2) * self.radius
                point3 = direction3 / np.linalg.norm(direction3) * self.radius
                point4 = direction4 / np.linalg.norm(direction4) * self.radius
                
                # Two triangles to form the quad with consistent winding order
                # First triangle (counter-clockwise when viewed from outside sphere)
                gl.glVertex3f(point1[0], point1[1], point1[2])
                gl.glVertex3f(point2[0], point2[1], point2[2])
                gl.glVertex3f(point3[0], point3[1], point3[2])
                
                # Second triangle (counter-clockwise when viewed from outside sphere)
                gl.glVertex3f(point2[0], point2[1], point2[2])
                gl.glVertex3f(point4[0], point4[1], point4[2])
                gl.glVertex3f(point3[0], point3[1], point3[2])
                
                # Also render the triangles with opposite winding for double-sided visibility
                gl.glVertex3f(point1[0], point1[1], point1[2])
                gl.glVertex3f(point3[0], point3[1], point3[2])
                gl.glVertex3f(point2[0], point2[1], point2[2])
                    
                gl.glVertex3f(point2[0], point2[1], point2[2])
                gl.glVertex3f(point3[0], point3[1], point3[2])
                gl.glVertex3f(point4[0], point4[1], point4[2])
        
        gl.glEnd()
        
        # Re-enable face culling if it was enabled before
        gl.glEnable(gl.GL_CULL_FACE)
    
    def _render_sphere_pyramid_intersection(self):
        """Render the sphere surface area that's inside the pyramid."""
        # Disable face culling for better visibility
        gl.glDisable(gl.GL_CULL_FACE)
        
        # Get vector direction and pyramid parameters
        direction = self.vector_direction / np.linalg.norm(self.vector_direction)
        
        # Create orthogonal coordinate system
        if abs(direction[0]) < 0.9:
            horizontal = np.array([0.0, direction[2], -direction[1]])
        else:
            horizontal = np.array([-direction[2], 0.0, direction[0]])
        
        horizontal = horizontal / np.linalg.norm(horizontal)
        vertical = np.cross(direction, horizontal)
        vertical = vertical / np.linalg.norm(vertical)
        
        # Calculate pyramid angles
        h_angle_rad = math.radians(self.pyramid_angle_horizontal)
        v_angle_rad = math.radians(self.pyramid_angle_vertical)
        # Use fixed base radius so pyramid size is independent of sphere scale
        base_radius = 1.0
        pyramid_length = self.pyramid_length * base_radius
        
        # Create smooth pyramid intersection surface using proper parametric mapping
        resolution = 32  # Higher resolution for smoother surface
    
        gl.glBegin(gl.GL_TRIANGLES)
        
        # Map the pyramid volume to sphere surface using angular coordinates
        for i in range(resolution):
            for j in range(resolution):
                # Parametric coordinates (0 to 1)
                u1 = i / resolution
                v1 = j / resolution
                u2 = (i + 1) / resolution
                v2 = (j + 1) / resolution
                
                # Map to angular coordinates within pyramid bounds
                # Convert from [0,1] to [-1,1] for symmetric mapping
                angle_u1 = (u1 * 2 - 1) * h_angle_rad  # Horizontal angle
                angle_v1 = (v1 * 2 - 1) * v_angle_rad  # Vertical angle
                angle_u2 = (u2 * 2 - 1) * h_angle_rad
                angle_v2 = (v2 * 2 - 1) * v_angle_rad
                
                # Create four points for this patch
                points = []
                for angle_u, angle_v in [(angle_u1, angle_v1), (angle_u2, angle_v1),
                (angle_u2, angle_v2), (angle_u1, angle_v2)]:
                    
                    # Create direction vector from angles
                    # This creates a smooth mapping from pyramid volume to sphere surface
                    point_direction = (direction +
                    horizontal * math.tan(angle_u) +
                    vertical * math.tan(angle_v))
                    
                    # Normalize to get point on sphere surface
                    direction_length = np.linalg.norm(point_direction)
                    if direction_length > 0:
                        sphere_point = point_direction / direction_length * self.radius
                        
                        # Verify this point is within the pyramid bounds
                        length_proj = np.dot(sphere_point, direction)
                        width_proj = np.dot(sphere_point, horizontal)
                        height_proj = np.dot(sphere_point, vertical)
                        
                        # Check if within pyramid (pyramid extends from origin)
                        if length_proj > 0 and length_proj <= pyramid_length:
                            # Calculate pyramid bounds at this distance
                            pyramid_half_width = length_proj * math.tan(h_angle_rad)
                            pyramid_half_height = length_proj * math.tan(v_angle_rad)
                                                
                            inside = (abs(width_proj) <= pyramid_half_width and
                            abs(height_proj) <= pyramid_half_height)
                                                
                            if inside:
                                points.append(sphere_point)
                
                # Render triangles with proper winding
                if len(points) >= 4:
                    p1, p2, p3, p4 = points[:4]
                    
                    # Two triangles with consistent winding order
                    # First triangle
                    gl.glVertex3f(p1[0], p1[1], p1[2])
                    gl.glVertex3f(p2[0], p2[1], p2[2])
                    gl.glVertex3f(p3[0], p3[1], p3[2])
                    
                    # Second triangle
                    gl.glVertex3f(p1[0], p1[1], p1[2])
                    gl.glVertex3f(p3[0], p3[1], p3[2])
                    gl.glVertex3f(p4[0], p4[1], p4[2])
                    
                    # Double-sided rendering for better visibility
                    gl.glVertex3f(p1[0], p1[1], p1[2])
                    gl.glVertex3f(p3[0], p3[1], p3[2])
                    gl.glVertex3f(p2[0], p2[1], p2[2])
                            
                    gl.glVertex3f(p1[0], p1[1], p1[2])
                    gl.glVertex3f(p4[0], p4[1], p4[2])
                    gl.glVertex3f(p3[0], p3[1], p3[2])
                            
                elif len(points) == 3:
                    p1, p2, p3 = points
                    gl.glVertex3f(p1[0], p1[1], p1[2])
                    gl.glVertex3f(p2[0], p2[1], p2[2])
                    gl.glVertex3f(p3[0], p3[1], p3[2])
                    
                    # Double-sided
                    gl.glVertex3f(p1[0], p1[1], p1[2])
                    gl.glVertex3f(p3[0], p3[1], p3[2])
                    gl.glVertex3f(p2[0], p2[1], p2[2])
                
        gl.glEnd()
        
        # Re-enable face culling
        gl.glEnable(gl.GL_CULL_FACE)
    
    def _render_sphere_cuboid_intersection(self):
        """Render the sphere surface area that's inside the cuboid, aligned with cuboid faces."""
        # Get vector direction and cuboid parameters
        direction = self.vector_direction / np.linalg.norm(self.vector_direction)
        
        # Create orthogonal coordinate system
        if abs(direction[0]) < 0.9:
            width_axis = np.array([0.0, direction[2], -direction[1]])
        else:
            width_axis = np.array([-direction[2], 0.0, direction[0]])
        
        width_axis = width_axis / np.linalg.norm(width_axis)
        height_axis = np.cross(direction, width_axis)
        height_axis = height_axis / np.linalg.norm(height_axis)
        
        # Calculate the cuboid's dimensions
        half_width = self.cuboid_width / 2.0
        half_height = self.cuboid_height / 2.0
        # Use fixed base radius so cuboid size is independent of sphere scale
        base_radius = 1.0
        if self.cuboid_infinite:
            cuboid_length = 50.0 * base_radius
        else:
            cuboid_length = self.cuboid_length * base_radius
        
        # Create the intersection surface by mapping the cuboid face onto the sphere
        # We'll create a grid that follows the cuboid's rectangular shape
        resolution = 32
    
        gl.glBegin(gl.GL_TRIANGLES)
        
        # Create a rectangular grid in cuboid coordinate space, then project to sphere
        for i in range(resolution):
            for j in range(resolution):
                # Parametric coordinates for the rectangular patch (0 to 1)
                u1 = i / resolution
                v1 = j / resolution
                u2 = (i + 1) / resolution
                v2 = (j + 1) / resolution
                
                # Convert to cuboid face coordinates
                # Map from [0,1] to cuboid bounds
                length_coords = [cuboid_length * 0.1, cuboid_length * 0.9]  
# Stay within cuboid bounds
                width_coords = [half_width * (2 * u1 - 1), half_width * (2 
* u2 - 1)]  # -half_width to +half_width
                height_coords = [half_height * (2 * v1 - 1), half_height * (2 * v2 - 1)]  # -half_height to +half_height
                        
                quad_points = []
                quad_valid = []
                
                # Generate the four corners of this patch
                for length_coord in length_coords:
                    for width_coord in width_coords[:1]:  # Only use first width coord for this iteration
                        for height_coord in height_coords[:1]:  # Only use first height coord for this iteration
                            # Point in cuboid coordinate system
                            cuboid_point = (direction * length_coord +
                            width_axis * width_coord +
                            height_axis * height_coord)
                            
                            # Project onto sphere surface
                            distance = np.linalg.norm(cuboid_point)
                            if distance > 0:
                                sphere_point = cuboid_point / distance * self.radius
                                                    
                                # Verify this point is actually inside the cuboid bounds
                                length_proj = np.dot(sphere_point, direction)
                                width_proj = np.dot(sphere_point, width_axis)
                                height_proj = np.dot(sphere_point, height_axis)
                                                    
                                inside = (0 <= length_proj <= cuboid_length and
                                -half_width <= width_proj <= half_width and
                                -half_height <= height_proj <= half_height)
                                                    
                                quad_points.append(sphere_point)
                                quad_valid.append(inside)
                
                # Create points for the rectangular patch corners
                points = []
                for u, v in [(u1, v1), (u2, v1), (u2, v2), (u1, v2)]:
                    # Map to cuboid coordinates
                    length = cuboid_length * 0.5  # Middle of cuboid length
                    width = half_width * (2 * u - 1)
                    height = half_height * (2 * v - 1)
                    
                    # Point in 3D space
                    cuboid_point = (direction * length +
                    width_axis * width +
                    height_axis * height)
                    
                    # Project to sphere surface
                    distance = np.linalg.norm(cuboid_point)
                    if distance > 0:
                        sphere_point = cuboid_point / distance * self.radius
                                    
                                    # Check if within cuboid bounds
                        length_proj = np.dot(sphere_point, direction)
                        width_proj = np.dot(sphere_point, width_axis)
                        height_proj = np.dot(sphere_point, height_axis)
                                    
                        inside = (0 <= length_proj <= cuboid_length and
                        -half_width <= width_proj <= half_width and
                        -half_height <= height_proj <= half_height)
                            
                        if inside:
                            points.append(sphere_point)
                
                # Render triangles if we have enough valid points
                if len(points) >= 4:
                    p1, p2, p3, p4 = points[:4]
                    
                    # Two triangles to form the quad
                    gl.glVertex3f(p1[0], p1[1], p1[2])
                    gl.glVertex3f(p2[0], p2[1], p2[2])
                    gl.glVertex3f(p3[0], p3[1], p3[2])
                            
                    gl.glVertex3f(p1[0], p1[1], p1[2])
                    gl.glVertex3f(p3[0], p3[1], p3[2])
                    gl.glVertex3f(p4[0], p4[1], p4[2])
                elif len(points) == 3:
                    p1, p2, p3 = points
                    gl.glVertex3f(p1[0], p1[1], p1[2])
                    gl.glVertex3f(p2[0], p2[1], p2[2])
                    gl.glVertex3f(p3[0], p3[1], p3[2])
        
        gl.glEnd()
    
    def set_sphere_color(self, color: Tuple[float, float, float]):
        """Set the sphere's base color (RGB values 0-1)."""
        self.sphere_color[:3] = color
    
    def set_transparency(self, alpha: float):
        """Set sphere transparency (0.0 = transparent, 1.0 = opaque)."""
        self.transparency = max(0.0, min(1.0, alpha))
        self.sphere_color[3] = self.transparency
    
    def set_grid_color(self, grid_type: GridType, color: Tuple[float, float, float, float]):
        """Set color for a specific grid type."""
        self.grid_colors[grid_type] = np.array(color)
    
    def toggle_grid(self, grid_type: GridType):
        """Toggle a grid system on/off."""
        if grid_type in self.active_grids:
            self.active_grids.remove(grid_type)
        else:
            self.active_grids.add(grid_type)
    
    def set_position(self, x: float, y: float, z: float):
        """Set sphere position."""
        old_pos = self.position.copy()
        self.position = np.array([x, y, z])
        
        # Update sphere vector camera to reflect new position
        self.update_sphere_vector_camera()
        
        # Notify canvas if it has the update method
        if hasattr(self, '_canvas_ref') and self._canvas_ref and hasattr(self._canvas_ref, 'update_screen_position_for_sphere_move'):
            self._canvas_ref.update_screen_position_for_sphere_move(old_pos, self.position)
    
    def set_rotation(self, pitch: float, yaw: float, roll: float):
        """Set sphere rotation in degrees."""
        self.rotation = np.array([pitch, yaw, roll])
    
    def set_scale(self, sx: float, sy: float, sz: float):
        """Set sphere scale factors."""
        self.scale = np.array([sx, sy, sz])
    
    def rotate(self, dpitch: float, dyaw: float, droll: float):
        """Apply relative rotation."""
        self.rotation += np.array([dpitch, dyaw, droll])
    
    def translate(self, dx: float, dy: float, dz: float):
        """Apply relative translation."""
        self.position += np.array([dx, dy, dz])
    
    def scale_by(self, factor: float):
        """Apply uniform scaling."""
        self.scale *= factor
    
    def set_wireframe_resolution(self, resolution: int):
        """Set wireframe resolution and regenerate geometry."""
        self.wireframe_resolution = max(4, min(64, resolution))
        self.generate_wireframe_geometry()
    
    def toggle_lighting(self):
        """Toggle lighting on/off."""
        self.lighting_enabled = not self.lighting_enabled
    
    def set_lighting(self, enabled: bool):
        """Set lighting state."""
        self.lighting_enabled = enabled
    
    def toggle_vector(self):
        """Toggle vector visibility."""
        self.vector_enabled = not self.vector_enabled
    
    def set_vector_enabled(self, enabled: bool):
        """Set vector visibility state."""
        self.vector_enabled = enabled
    
    def toggle_vector_orientation(self):
        """Toggle vector orientation visibility."""
        self.vector_orientation_enabled = not self.vector_orientation_enabled
    
    def set_vector_orientation_enabled(self, enabled: bool):
        """Set vector orientation visibility state."""
        self.vector_orientation_enabled = enabled
    
    def set_vector_orientation_length(self, length: float):
        """Set vector orientation length."""
        self.vector_orientation_length = max(0.1, min(2.0, length))
    
    def set_vector_orientation_color(self, r: float, g: float, b: float, a: float = 1.0):
        """Set vector orientation color."""
        self.vector_orientation_color = np.array([r, g, b, a])
    
    def set_vector_orientation_thickness(self, thickness: float):
        """Set vector orientation line thickness."""
        self.vector_orientation_thickness = max(1.0, min(10.0, thickness))
    
    def set_vector_direction(self, x: float, y: float, z: float):
        """Set vector direction (will be normalized)."""
        direction = np.array([x, y, z])
        if np.linalg.norm(direction) > 0:
            self.vector_direction = direction
            
            # Update sphere vector camera to follow new direction
            self.update_sphere_vector_camera()
            
            # Force ray tracing screen update when vector changes
            if hasattr(self, 'screen_needs_update'):
                self.screen_needs_update = True
                print(f"DEBUG: Vector direction changed to {direction}, forcing screen update")
            
            # Notify canvas to update ray tracing camera
            if hasattr(self, '_canvas_ref') and self._canvas_ref:
                self._canvas_ref.update_sphere_view_vector()
                # Force immediate screen refresh
                self._canvas_ref.Refresh()
                print(f"DEBUG: Notified canvas of vector direction change and forced refresh")
    
    def set_vector_length(self, length: float):
        """Set vector length relative to sphere radius."""
        self.vector_length = max(0.1, length)
    
    def set_vector_color(self, color: Tuple[float, float, float, float]):
        """Set vector color (RGBA)."""
        self.vector_color = np.array(color)
    
    def set_vector_thickness(self, thickness: float):
        """Set vector line thickness."""
        self.vector_thickness = max(1.0, thickness)
    
    def set_vector_roll(self, roll_degrees: float):
        """Set vector roll rotation (camera orientation around the vector axis)."""
        self.vector_roll = roll_degrees % 360.0
        
        # Update sphere vector camera to reflect new roll orientation
        self.update_sphere_vector_camera()
        
        # Force ray tracing screen update when roll changes
        if hasattr(self, 'screen_needs_update'):
            self.screen_needs_update = True
        
        # Notify canvas to update ray tracing camera
        if hasattr(self, '_canvas_ref') and self._canvas_ref:
            self._canvas_ref.update_sphere_view_vector()
            # Force immediate screen refresh
            self._canvas_ref.Refresh()
    
    def rotate_vector_roll(self, degrees: float):
        """Rotate vector roll (camera orientation around the vector axis)."""
        self.vector_roll = (self.vector_roll + degrees) % 360.0
        self.set_vector_roll(self.vector_roll)
    
    def toggle_cone(self):
        """Toggle cone visibility."""
        self.cone_enabled = not self.cone_enabled
    
    def set_cone_enabled(self, enabled: bool):
        """Set cone visibility state."""
        self.cone_enabled = enabled
    
    def set_cone_length(self, length: float):
        """Set cone length relative to sphere radius."""
        self.cone_length = max(0.5, length)
    
    def set_cone_angle(self, angle: float):
        """Set cone half-angle in degrees."""
        self.cone_angle = max(5.0, min(89.0, angle))
    
    def set_cone_color(self, color: Tuple[float, float, float, float]):
        """Set cone color (RGBA)."""
        self.cone_color = np.array(color)
    
    def set_cone_resolution(self, resolution: int):
        """Set cone base circle resolution."""
        self.cone_resolution = max(6, min(32, resolution))
    
    def toggle_cone_infinite(self):
        """Toggle cone infinite length."""
        self.cone_infinite = not self.cone_infinite
    
    def set_cone_infinite(self, infinite: bool):
        """Set cone infinite length state."""
        self.cone_infinite = infinite
    
    def toggle_pyramid(self):
        """Toggle pyramid visibility."""
        self.pyramid_enabled = not self.pyramid_enabled
    
    def set_pyramid_enabled(self, enabled: bool):
        """Set pyramid visibility state."""
        self.pyramid_enabled = enabled
    
    def set_pyramid_length(self, length: float):
        """Set pyramid length relative to sphere radius."""
        self.pyramid_length = max(0.5, length)
    
    def set_pyramid_angle_horizontal(self, angle: float):
        """Set pyramid horizontal half-angle in degrees."""
        self.pyramid_angle_horizontal = max(5.0, min(89.0, angle))
    
    def set_pyramid_angle_vertical(self, angle: float):
        """Set pyramid vertical half-angle in degrees."""
        self.pyramid_angle_vertical = max(5.0, min(89.0, angle))
    
    def set_pyramid_color(self, color: Tuple[float, float, float, float]):
        """Set pyramid color (RGBA)."""
        self.pyramid_color = np.array(color)
    
    def toggle_pyramid_infinite(self):
        """Toggle pyramid infinite length."""
        self.pyramid_infinite = not self.pyramid_infinite
    
    def set_pyramid_infinite(self, infinite: bool):
        """Set pyramid infinite length state."""
        self.pyramid_infinite = infinite
    
    # Cuboid control methods
    def toggle_cuboid(self):
        """Toggle cuboid visibility."""
        self.cuboid_enabled = not self.cuboid_enabled
    
    def set_cuboid_enabled(self, enabled: bool):
        """Set cuboid visibility state."""
        self.cuboid_enabled = enabled
    
    def set_cuboid_length(self, length: float):
        """Set cuboid length along vector direction relative to sphere radius."""
        self.cuboid_length = max(0.1, length)
    
    def set_cuboid_width(self, width: float):
        """Set cuboid width perpendicular to vector relative to sphere radius."""
        self.cuboid_width = max(0.1, width)
    
    def set_cuboid_height(self, height: float):
        """Set cuboid height perpendicular to vector relative to sphere radius."""
        self.cuboid_height = max(0.1, height)
    
    def set_cuboid_color(self, color: Tuple[float, float, float, float]):
        """Set cuboid color (RGBA)."""
        self.cuboid_color = np.array(color)
    
    def toggle_cuboid_infinite(self):
        """Toggle cuboid infinite length."""
        self.cuboid_infinite = not self.cuboid_infinite
    
    def set_cuboid_infinite(self, infinite: bool):
        """Set cuboid infinite length state."""
        self.cuboid_infinite = infinite
    
    # Near plane control methods
    def toggle_near_plane(self):
        """Toggle near plane visibility."""
        self.near_plane_enabled = not self.near_plane_enabled
    
    def set_near_plane_enabled(self, enabled: bool):
        """Set near plane visibility state."""
        self.near_plane_enabled = enabled
    
    def set_near_plane_distance(self, distance: float):
        """Set near plane distance from sphere center along vector (0-1 range)."""
        self.near_plane_distance = max(0.0, min(3.0, distance))  # Allow up to 3 radius units
    
    # Sphere intersection control methods
    def toggle_sphere_intersection(self):
        """Toggle sphere intersection visibility."""
        self.sphere_intersection_enabled = not self.sphere_intersection_enabled
    
    def set_sphere_intersection_enabled(self, enabled: bool):
        """Set sphere intersection visibility state."""
        self.sphere_intersection_enabled = enabled
    
    def set_sphere_intersection_color(self, color: Tuple[float, float, float, float]):
        """Set sphere intersection color (RGBA)."""
        self.sphere_intersection_color = np.array(color)
    
    # Normal ray control methods
    def toggle_normal_rays(self):
        """Toggle normal ray visibility."""
        self.normal_rays_enabled = not self.normal_rays_enabled
    
    def set_normal_rays_enabled(self, enabled: bool):
        """Set normal ray visibility state."""
        self.normal_rays_enabled = enabled
    
    def set_normal_rays_length(self, length: float):
        """Set normal ray length relative to sphere radius."""
        self.normal_rays_length = max(0.1, min(2.0, length))
    
    def set_normal_rays_density(self, density: int):
        """Set normal ray density (rays per division)."""
        self.normal_rays_density = max(4, min(20, density))
    
    def set_normal_rays_color(self, color: Tuple[float, float, float, float]):
        """Set normal ray color (RGBA)."""
        self.normal_rays_color = np.array(color)
    
    def set_normal_rays_thickness(self, thickness: float):
        """Set normal ray line thickness."""
        self.normal_rays_thickness = max(1.0, min(5.0, thickness))
    
    # Intersection normal ray control methods
    def toggle_intersection_normals(self):
        """Toggle intersection normal ray visibility."""
        self.intersection_normals_enabled = not self.intersection_normals_enabled
    
    def set_intersection_normals_enabled(self, enabled: bool):
        """Set intersection normal ray visibility state."""
        self.intersection_normals_enabled = enabled
    
    def set_intersection_normals_length(self, length: float):
        """Set intersection normal ray length relative to sphere radius."""
        self.intersection_normals_length = max(0.1, min(2.0, length))
    
    def set_intersection_normals_density(self, density: int):
        """Set intersection normal ray density (rays per division)."""
        self.intersection_normals_density = max(4, min(24, density))
    
    def set_intersection_normals_color(self, color: Tuple[float, float, float, float]):
        """Set intersection normal ray color (RGBA)."""
        self.intersection_normals_color = np.array(color)
    
    def set_intersection_normals_thickness(self, thickness: float):
        """Set intersection normal ray line thickness."""
        self.intersection_normals_thickness = max(1.0, min(5.0, thickness))
    
    # Truncation normal ray control methods
    def toggle_truncation_normals(self):
        """Toggle truncation normal ray visibility."""
        self.truncation_normals_enabled = not self.truncation_normals_enabled
    
    def set_truncation_normals_enabled(self, enabled: bool):
        """Set truncation normal ray visibility state."""
        self.truncation_normals_enabled = enabled
    
    def set_truncation_normals_length(self, length: float):
        """Set truncation normal ray length relative to sphere radius."""
        self.truncation_normals_length = max(0.1, min(2.0, length))
    
    def set_truncation_normals_density(self, density: int):
        """Set truncation normal ray density (rays per division)."""
        self.truncation_normals_density = max(3, min(16, density))
    
    def set_truncation_normals_color(self, color: Tuple[float, float, float, float]):
        """Set truncation normal ray color (RGBA)."""
        self.truncation_normals_color = np.array(color)
    
    def set_truncation_normals_thickness(self, thickness: float):
        """Set truncation normal ray line thickness."""
        self.truncation_normals_thickness = max(1.0, min(5.0, thickness))
    
    def save_scene_to_dict(self) -> dict:
        """Save all sphere properties to a dictionary for serialization."""
        scene_data = {
            "version": "1.0",
            "sphere": {
                "radius": float(self.radius),
                "position": self.position.tolist(),
                "rotation": self.rotation.tolist(),
                "scale": self.scale.tolist(),
                "color": self.sphere_color.tolist(),
                "transparency": float(self.transparency),
                "wireframe_mode": bool(self.wireframe_mode),
                "lighting_enabled": bool(self.lighting_enabled),
                "resolution": int(self.resolution),
                "wireframe_resolution": int(self.wireframe_resolution)
            },
            "vector": {
                "enabled": bool(self.vector_enabled),
                "direction": self.vector_direction.tolist(),
                "length": float(self.vector_length),
                "color": self.vector_color.tolist(),
                "thickness": float(self.vector_thickness),
                "roll": float(self.vector_roll),
                "orientation_enabled": bool(self.vector_orientation_enabled),
                "orientation_length": float(self.vector_orientation_length),
                "orientation_color": self.vector_orientation_color.tolist(),
                "orientation_thickness": float(self.vector_orientation_thickness)
            },
            "cone": {
                "enabled": bool(self.cone_enabled),
                "length": float(self.cone_length),
                "infinite": bool(self.cone_infinite),
                "angle": float(self.cone_angle),
                "color": self.cone_color.tolist(),
                "resolution": int(self.cone_resolution)
            },
            "pyramid": {
                "enabled": bool(self.pyramid_enabled),
                "length": float(self.pyramid_length),
                "infinite": bool(self.pyramid_infinite),
                "angle_horizontal": float(self.pyramid_angle_horizontal),
                "angle_vertical": float(self.pyramid_angle_vertical),
                "color": self.pyramid_color.tolist()
            },
            "cuboid": {
                "enabled": bool(self.cuboid_enabled),
                "length": float(self.cuboid_length),
                "width": float(self.cuboid_width),
                "height": float(self.cuboid_height),
                "infinite": bool(self.cuboid_infinite),
                "color": self.cuboid_color.tolist()
            },
            "grids": {
                "active_grids": list(self.active_grids),
                "grid_colors": {str(k): v.tolist() for k, v in self.grid_colors.items()},
                "longitude_lines": int(self.longitude_lines),
                "latitude_lines": int(self.latitude_lines),
                "concentric_rings": int(self.concentric_rings),
                "dot_density": int(self.dot_density),
                "neon_intensity": float(self.neon_intensity)
            },
            "screen": {
                "enabled": bool(self.screen_enabled),
                "render_mode": str(self.screen_render_mode),
                "position": self.screen_position.tolist(),
                "rotation": self.screen_rotation.tolist(),
                "width": float(self.screen_width),
                "height": float(self.screen_height),
                "resolution": list(self.screen_resolution),
                "update_rate": float(self.screen_update_rate),
                "samples": int(self.screen_samples),
                "max_bounces": int(self.screen_max_bounces)
            },
            "near_plane": {
                "enabled": bool(self.near_plane_enabled),
                "distance": float(self.near_plane_distance)
            },
            "sphere_intersection": {
                "enabled": bool(self.sphere_intersection_enabled),
                "color": self.sphere_intersection_color.tolist()
            },
            "normal_rays": {
                "enabled": bool(self.normal_rays_enabled),
                "length": float(self.normal_rays_length),
                "density": int(self.normal_rays_density),
                "color": self.normal_rays_color.tolist(),
                "thickness": float(self.normal_rays_thickness)
            },
            "intersection_normals": {
                "enabled": bool(self.intersection_normals_enabled),
                "length": float(self.intersection_normals_length),
                "density": int(self.intersection_normals_density),
                "color": self.intersection_normals_color.tolist(),
                "thickness": float(self.intersection_normals_thickness)
            },
            "truncation_normals": {
                "enabled": bool(self.truncation_normals_enabled),
                "length": float(self.truncation_normals_length),
                "density": int(self.truncation_normals_density),
                "color": self.truncation_normals_color.tolist(),
                "thickness": float(self.truncation_normals_thickness)
            }
        }
        return scene_data
    
    def load_scene_from_dict(self, scene_data: dict):
        """Load all sphere properties from a dictionary."""
        try:
            # Sphere properties
            if "sphere" in scene_data:
                s = scene_data["sphere"]
                self.radius = s.get("radius", 1.0)
                self.position = np.array(s.get("position", [0.0, 0.0, 
0.0]))
                self.rotation = np.array(s.get("rotation", [0.0, 0.0, 
0.0]))
                self.scale = np.array(s.get("scale", [1.0, 1.0, 1.0]))
                self.sphere_color = np.array(s.get("color", [0.2, 0.5, 
1.0, 0.7]))
                self.transparency = s.get("transparency", 0.7)
                self.wireframe_mode = s.get("wireframe_mode", False)
                self.lighting_enabled = s.get("lighting_enabled", True)
                self.resolution = s.get("resolution", 32)
                self.wireframe_resolution = s.get("wireframe_resolution", 
16)
            
            # Vector properties
            if "vector" in scene_data:
                v = scene_data["vector"]
                self.vector_enabled = v.get("enabled", True)
                self.vector_direction = np.array(v.get("direction", [1.0, 
0.0, 0.0]))
                self.vector_length = v.get("length", 2.0)
                self.vector_color = np.array(v.get("color", [1.0, 0.0, 
0.0, 1.0]))
                self.vector_thickness = v.get("thickness", 3.0)
                self.vector_roll = v.get("roll", 0.0)
                self.vector_orientation_enabled = v.get("orientation_enabled", False)
                self.vector_orientation_length = v.get("orientation_length", 0.8)
                self.vector_orientation_color = np.array(v.get("orientation_color", [0.0, 1.0, 0.0, 1.0]))
                self.vector_orientation_thickness = v.get("orientation_thickness", 2.0)
            
            # Cone properties
            if "cone" in scene_data:
                c = scene_data["cone"]
                self.cone_enabled = c.get("enabled", False)
                self.cone_length = c.get("length", 3.0)
                self.cone_infinite = c.get("infinite", False)
                self.cone_angle = c.get("angle", 30.0)
                self.cone_color = np.array(c.get("color", [1.0, 1.0, 0.0, 
0.3]))
                self.cone_resolution = c.get("resolution", 16)
            
            # Pyramid properties
            if "pyramid" in scene_data:
                p = scene_data["pyramid"]
                self.pyramid_enabled = p.get("enabled", False)
                self.pyramid_length = p.get("length", 3.0)
                self.pyramid_infinite = p.get("infinite", False)
                self.pyramid_angle_horizontal = p.get("angle_horizontal", 
25.0)
                self.pyramid_angle_vertical = p.get("angle_vertical", 
20.0)
                self.pyramid_color = np.array(p.get("color", [0.0, 1.0, 
1.0, 0.3]))
            
            # Cuboid properties
            if "cuboid" in scene_data:
                cb = scene_data["cuboid"]
                self.cuboid_enabled = cb.get("enabled", False)
                self.cuboid_length = cb.get("length", 2.0)
                self.cuboid_width = cb.get("width", 1.0)
                self.cuboid_height = cb.get("height", 0.8)
                self.cuboid_infinite = cb.get("infinite", False)
                self.cuboid_color = np.array(cb.get("color", [1.0, 0.0, 
1.0, 0.3]))
            
            # Grid properties
            if "grids" in scene_data:
                g = scene_data["grids"]
                self.active_grids = set(g.get("active_grids", []))
                if "grid_colors" in g:
                    for k, v in g["grid_colors"].items():
                        self.grid_colors[k] = np.array(v)
                self.longitude_lines = g.get("longitude_lines", 12)
                self.latitude_lines = g.get("latitude_lines", 8)
                self.concentric_rings = g.get("concentric_rings", 5)
                self.dot_density = g.get("dot_density", 100)
                self.neon_intensity = g.get("neon_intensity", 1.0)
            
            # Screen properties
            if "screen" in scene_data:
                sc = scene_data["screen"]
                self.screen_enabled = sc.get("enabled", True)
                self.screen_render_mode = sc.get("render_mode", "simple")
                self.screen_position = np.array(sc.get("position", [0.0, 
0.0, -3.0]))
                self.screen_rotation = np.array(sc.get("rotation", [0.0, 
0.0, 0.0]))
                self.screen_width = sc.get("width", 2.0)
                self.screen_height = sc.get("height", 1.5)
                self.screen_resolution = tuple(sc.get("resolution", [128, 
96]))
                self.screen_update_rate = sc.get("update_rate", 0.1)
                self.screen_samples = sc.get("samples", 1)
                self.screen_max_bounces = sc.get("max_bounces", 3)
            
            # Near plane properties
            if "near_plane" in scene_data:
                np_data = scene_data["near_plane"]
                self.near_plane_enabled = np_data.get("enabled", False)
                self.near_plane_distance = np_data.get("distance", 1.0)
            
            # Sphere intersection properties
            if "sphere_intersection" in scene_data:
                si = scene_data["sphere_intersection"]
                self.sphere_intersection_enabled = si.get("enabled", False)
                self.sphere_intersection_color = np.array(si.get("color", 
[1.0, 0.5, 0.0, 0.8]))
            
            # Normal rays properties
            if "normal_rays" in scene_data:
                nr = scene_data["normal_rays"]
                self.normal_rays_enabled = nr.get("enabled", False)
                self.normal_rays_length = nr.get("length", 0.5)
                self.normal_rays_density = nr.get("density", 8)
                self.normal_rays_color = np.array(nr.get("color", [0.0, 
1.0, 0.0, 1.0]))
                self.normal_rays_thickness = nr.get("thickness", 1.0)
            
            # Intersection normals properties
            if "intersection_normals" in scene_data:
                inr = scene_data["intersection_normals"]
                self.intersection_normals_enabled = inr.get("enabled", False)
                self.intersection_normals_length = inr.get("length", 0.3)
                self.intersection_normals_density = inr.get("density", 6)
                self.intersection_normals_color = np.array(inr.get("color", [1.0, 1.0, 0.0, 1.0]))
                self.intersection_normals_thickness = inr.get("thickness", 
1.0)
            
            # Truncation normals properties
            if "truncation_normals" in scene_data:
                tn = scene_data["truncation_normals"]
                self.truncation_normals_enabled = tn.get("enabled", False)
                self.truncation_normals_length = tn.get("length", 0.4)
                self.truncation_normals_density = tn.get("density", 5)
                self.truncation_normals_color = np.array(tn.get("color", 
[1.0, 0.0, 1.0, 1.0]))
                self.truncation_normals_thickness = tn.get("thickness", 
1.0)
            
            # Regenerate geometry after loading
            self.generate_sphere_geometry()
            self.generate_wireframe_geometry()
            
            print("Scene loaded successfully")
            
        except Exception as e:
            print(f"Error loading scene: {e}")
            raise
    
    # Shape Management Methods
    
    def add_shape(self, shape: Shape) -> str:
        """Add a shape to the scene."""
        self.shapes[shape.id] = shape
        return shape.id
    
    def remove_shape(self, shape_id: str) -> bool:
        """Remove a shape from the scene."""
        if shape_id in self.shapes:
            del self.shapes[shape_id]
            return True
        return False
    
    def get_shape(self, shape_id: str) -> Optional[Shape]:
        """Get a shape by ID."""
        return self.shapes.get(shape_id)
    
    def get_all_shapes(self) -> List[Shape]:
        """Get all shapes in the scene."""
        return list(self.shapes.values())
    
    def create_dot(self, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> str:
        """Create a dot shape at the specified position."""
        dot = DotShape()
        dot.set_position(x, y, z)
        return self.add_shape(dot)
    
    def create_line(self, start: np.ndarray, end: np.ndarray) -> str:
        """Create a line shape between two points."""
        line = LineShape()
        line.set_endpoints(start, end)
        return self.add_shape(line)
    
    def create_bezier_curve(self, control_points: List[np.ndarray]) -> str:
        """Create a Bezier curve with the given control points."""
        curve = BezierCurve()
        curve.set_control_points(control_points)
        return self.add_shape(curve)
    
    def create_plane(self, x: float = 0.0, y: float = 0.0, z: float = 0.0, 
                    width: float = 2.0, height: float = 2.0) -> str:
        """Create a plane shape."""
        plane = PlaneShape()
        plane.set_position(x, y, z)
        plane.width = width
        plane.height = height
        return self.add_shape(plane)
    
    def create_cube(self, x: float = 0.0, y: float = 0.0, z: float = 0.0, 
                   size: float = 1.0) -> str:
        """Create a cube shape."""
        cube = CubeShape()
        cube.set_position(x, y, z)
        cube.size = size
        return self.add_shape(cube)
    
    def create_sphere_shape(self, x: float = 0.0, y: float = 0.0, z: float = 0.0, 
                           radius: float = 0.5) -> str:
        """Create a sphere shape (different from the main sphere)."""
        sphere = SphereShape()
        sphere.set_position(x, y, z)
        sphere.radius = radius
        return self.add_shape(sphere)
    
    def create_cylinder(self, x: float = 0.0, y: float = 0.0, z: float = 0.0, 
                       radius: float = 0.5, height: float = 2.0) -> str:
        """Create a cylinder shape."""
        cylinder = CylinderShape()
        cylinder.set_position(x, y, z)
        cylinder.radius = radius
        cylinder.height = height
        return self.add_shape(cylinder)
    
    # Camera Management Methods
    
    def add_camera(self, camera: Camera) -> str:
        """Add a camera to the scene."""
        self.cameras[camera.id] = camera
        return camera.id

    def _register_original_2d_screen(self):
        """Register the original 2D screen as a proper screen object."""
        # Create a screen for the original 2D unified screen
        original_screen = Screen(screen_type=ScreenType.SCREEN_2D)
        original_screen.name = "Original 2D Screen"
        original_screen.set_position(-3.0, 0.0, 0.0)  # Position to the left of the sphere
        original_screen.set_size(2.0, 1.5)  # Default size
        original_screen.camera_id = self.sphere_vector_camera_id  # Use sphere vector camera by default
        
        # Add to screens collection
        screen_id = self.add_screen(original_screen)
        
        # Store reference for canvas integration
        self.original_screen_id = screen_id
        
        print(f"DEBUG: Registered original 2D screen as {original_screen.name} with ID {screen_id}")
        return screen_id

    def _is_stepped_into_screen(self):
        """Check if we're currently stepped into a screen (to hide vector arrow)."""
        # Check if canvas reference exists and is stepped into a screen
        if hasattr(self, '_canvas_ref') and self._canvas_ref:
            return self._canvas_ref.stepped_in_screen_id is not None
        return False
    
    def remove_camera(self, camera_id: str) -> bool:
        """Remove a camera from the scene."""
        if camera_id in self.cameras and camera_id not in [self.main_camera_id, self.sphere_vector_camera_id]:
            del self.cameras[camera_id]
            return True
        return False
    
    def get_camera(self, camera_id: str) -> Optional[Camera]:
        """Get a camera by ID."""
        return self.cameras.get(camera_id)
    
    def get_all_cameras(self) -> List[Camera]:
        """Get all cameras in the scene."""
        return list(self.cameras.values())
    
    def create_camera(self, x: float = 0.0, y: float = 0.0, z: float = 5.0,
                     target_x: float = 0.0, target_y: float = 0.0, target_z: float = 0.0) -> str:
        """Create a new camera."""
        camera = Camera()
        camera.set_position(x, y, z)
        camera.set_target(target_x, target_y, target_z)
        return self.add_camera(camera)
    
    def update_sphere_vector_camera(self):
        """Update the sphere vector camera to follow the sphere's vector direction."""
        if self.sphere_vector_camera_id in self.cameras:
            camera = self.cameras[self.sphere_vector_camera_id]
            
            # Normalize the vector direction
            vector_dir = self.vector_direction / np.linalg.norm(self.vector_direction)
            
            # Position camera at the sphere surface in the direction of the vector
            # This puts the camera at the point where the vector exits the sphere
            camera_position = self.position + vector_dir * self.radius
            camera.set_position(camera_position[0], camera_position[1], camera_position[2])
            
            # Set target far along the vector direction (what the camera is looking at)
            target = camera_position + vector_dir * self.vector_length * 5.0  # Look far ahead
            camera.set_target(target[0], target[1], target[2])
            
            # Calculate up vector based on vector roll orientation
            # Start with world up vector
            world_up = np.array([0.0, 1.0, 0.0])
            
            # Get the forward direction (normalized vector direction)
            forward = self.vector_direction / np.linalg.norm(self.vector_direction)
            
            # Calculate right vector (cross product of forward and world up)
            right = np.cross(forward, world_up)
            if np.linalg.norm(right) < 0.001:  # Handle case where forward is parallel to up
                # Use world right as fallback
                right = np.array([1.0, 0.0, 0.0])
            else:
                right = right / np.linalg.norm(right)
            
            # Calculate proper up vector (cross product of right and forward)
            up = np.cross(right, forward)
            up = up / np.linalg.norm(up)
            
            # Apply roll rotation around the forward vector
            if abs(self.vector_roll) > 0.001:
                roll_rad = math.radians(self.vector_roll)
                cos_roll = math.cos(roll_rad)
                sin_roll = math.sin(roll_rad)
                
                # Rotate up and right vectors around forward vector
                new_up = up * cos_roll + right * sin_roll
                camera.set_up_vector(new_up[0], new_up[1], new_up[2])
            else:
                camera.set_up_vector(up[0], up[1], up[2])
    
    def update_main_cameras(self, canvas_ref=None):
        """Update both main camera and clean main camera to mirror the canvas camera system."""
        if not canvas_ref:
            return
            
        # The canvas uses this exact transformation sequence:
        # 1. glTranslatef(0, 0, -camera_distance)
        # 2. glRotatef(camera_rotation_x, 1, 0, 0) 
        # 3. glRotatef(camera_rotation_y, 0, 1, 0)
        # 4. glTranslatef(-camera_position)
        #
        # To match this exactly, we need to reverse the transformations:
        
        # Start at origin, apply transformations in reverse order:
        
        # First: apply camera_position offset
        position = np.array([0.0, 0.0, 0.0]) + canvas_ref.camera_position
        
        # Second: apply inverse rotations
        rot_x_rad = math.radians(-canvas_ref.camera_rotation_x)  # Negative for inverse
        rot_y_rad = math.radians(-canvas_ref.camera_rotation_y)  # Negative for inverse
        
        # Apply Y rotation first (inverse order)
        cos_y, sin_y = math.cos(rot_y_rad), math.sin(rot_y_rad)
        rotation_y = np.array([
            [cos_y, 0, sin_y],
            [0, 1, 0],
            [-sin_y, 0, cos_y]
        ])
        
        # Apply X rotation second  
        cos_x, sin_x = math.cos(rot_x_rad), math.sin(rot_x_rad)
        rotation_x = np.array([
            [1, 0, 0],
            [0, cos_x, -sin_x],
            [0, sin_x, cos_x]
        ])
        
        # Combined rotation matrix (X then Y, since we're doing inverse)
        rotation_matrix = rotation_y @ rotation_x
        
        # Apply rotation to position
        position = rotation_matrix @ position
        
        # Third: apply distance offset (move camera back by distance)
        position[2] += canvas_ref.camera_distance
        
        # The target is at the origin (where the world center is rendered)
        target = np.array([0.0, 0.0, 0.0])
        
        # Update the main camera
        if self.main_camera_id in self.cameras:
            main_camera = self.cameras[self.main_camera_id]
            main_camera.set_position(position[0], position[1], position[2])
            main_camera.set_target(target[0], target[1], target[2])
            main_camera.set_up_vector(0.0, 1.0, 0.0)
        
        # Update the clean main camera
        if self.main_clean_camera_id in self.cameras:
            clean_camera = self.cameras[self.main_clean_camera_id]
            clean_camera.set_position(position[0], position[1], position[2])
            clean_camera.set_target(target[0], target[1], target[2])
            clean_camera.set_up_vector(0.0, 1.0, 0.0)
            
        print(f"DEBUG: Updated main cameras - pos: {position}, target: {target}, distance: {canvas_ref.camera_distance}, rotations: [{canvas_ref.camera_rotation_x}, {canvas_ref.camera_rotation_y}]")
    
    def update_main_clean_camera(self, canvas_ref=None):
        """Legacy method - now calls update_main_cameras for compatibility."""
        self.update_main_cameras(canvas_ref)
    
    # Screen Management Methods
    
    def add_screen(self, screen: Screen) -> str:
        """Add a screen to the scene."""
        self.screens[screen.id] = screen
        print(f"DEBUG: Added screen {screen.name} (type: {type(screen).__name__}) with ID {screen.id}")
        
        # Start video playback if it's a video media screen
        if isinstance(screen, MediaScreen):
            print(f"DEBUG: ===== SPHERE ADD_SCREEN: MediaScreen added =====")
            print(f"DEBUG: Screen name: {screen.name}")
            print(f"DEBUG: Screen media_type: {screen.media_type}")
            print(f"DEBUG: MediaType.VIDEO: {MediaType.VIDEO}")
            print(f"DEBUG: Is VIDEO type? {screen.media_type == MediaType.VIDEO}")
            
            if screen.media_type == MediaType.VIDEO:
                print(f"DEBUG: ===== SPHERE CALLING START_VIDEO_PLAYBACK =====")
                screen.start_video_playback()
                print(f"DEBUG: ===== SPHERE START_VIDEO_PLAYBACK COMPLETED =====")
            else:
                print(f"DEBUG: Not starting video playback - media_type is {screen.media_type}, not VIDEO")
        
        return screen.id
    
    def remove_screen(self, screen_id: str) -> bool:
        """Remove a screen from the scene."""
        if screen_id in self.screens:
            del self.screens[screen_id]
            return True
        return False
    
    def get_screen(self, screen_id: str) -> Optional[Screen]:
        """Get a screen by ID."""
        return self.screens.get(screen_id)
    
    def get_all_screens(self) -> List[Screen]:
        """Get all screens in the scene."""
        return list(self.screens.values())
    
    def create_2d_screen(self, x: float = 0.0, y: float = 0.0, z: float = 0.0,
                        width: float = 2.0, height: float = 1.5, camera_id: str = None) -> str:
        """Create a 2D screen positioned in 3D space."""
        screen = Screen(screen_type=ScreenType.SCREEN_2D)
        screen.set_position(x, y, z)
        screen.set_size(width, height)
        screen.camera_id = camera_id or self.main_camera_id
        screen_id = self.add_screen(screen)
        print(f"DEBUG: Created 2D screen {screen.name} at position {screen.position} with camera {screen.camera_id[:8]}")
        return screen_id
    
    def create_overlay_screen(self, x: float = 0.1, y: float = 0.1,
                             width: float = 0.3, height: float = 0.3, camera_id: str = None) -> str:
        """Create an overlay screen on the main view."""
        screen = Screen(screen_type=ScreenType.OVERLAY)
        screen.set_overlay_position(x, y)
        screen.set_overlay_size(width, height)
        screen.camera_id = camera_id or self.sphere_vector_camera_id
        return self.add_screen(screen)
    
    def step_into_screen(self, screen_id: str, canvas_ref=None) -> bool:
        """Step into a screen - change main view to match the screen's camera."""
        screen = self.get_screen(screen_id)
        if not screen or not screen.camera_id:
            return False
        
        camera = self.get_camera(screen.camera_id)
        if not camera:
            return False
        
        # Update canvas camera to match screen's camera
        if canvas_ref and hasattr(canvas_ref, 'camera_distance'):
            # Calculate distance from camera position to target
            direction = camera.target - camera.position
            distance = np.linalg.norm(direction)
            canvas_ref.camera_distance = distance
            
            # Calculate rotation angles to match camera direction
            direction_norm = direction / distance if distance > 0 else np.array([0, 0, -1])
            
            # Calculate pitch (rotation around X axis)
            pitch = math.degrees(math.asin(-direction_norm[1]))
            
            # Calculate yaw (rotation around Y axis)
            yaw = math.degrees(math.atan2(direction_norm[0], -direction_norm[2]))
            
            canvas_ref.camera_rotation_x = pitch
            canvas_ref.camera_rotation_y = yaw
            
            # Set camera position offset
            canvas_ref.camera_position = -camera.position
            
            # Refresh the view
            canvas_ref.Refresh()
        
        return True
    
    def render_shapes(self):
        """Render all visible shapes in the scene."""
        for shape in self.shapes.values():
            if shape.visible:
                shape.render()
    
    def render_screens(self, canvas_ref=None):
        """Render all visible screens."""
        if len(self.screens) > 0:
            print(f"DEBUG: Rendering {len(self.screens)} screens")
        
        for screen in self.screens.values():
            if not screen.visible:
                print(f"DEBUG: Skipping invisible screen {screen.name}")
                continue
            
            print(f"DEBUG: Rendering screen {screen.name} of type {screen.type.value}")
            if screen.type == ScreenType.SCREEN_2D:
                self.render_2d_screen(screen, canvas_ref)
            elif screen.type == ScreenType.OVERLAY:
                self.render_overlay_screen(screen, canvas_ref)
    
    def render_2d_screen(self, screen: Screen, canvas_ref=None):
        """Render a 2D screen positioned in 3D space with camera view."""
        
        # Handle MediaScreens differently - they display content directly, not camera views
        if isinstance(screen, MediaScreen):
            # MediaScreens render their content directly through _render_screen_quad
            self._render_screen_quad(screen)
            return
        
        if not screen.camera_id or screen.camera_id not in self.cameras:
            return
        
        camera = self.cameras[screen.camera_id]
        
        # Update cameras based on type
        if camera.type == CameraType.SPHERE_VECTOR:
            self.update_sphere_vector_camera()
        elif camera.type in [CameraType.MAIN, CameraType.MAIN_CLEAN]:
            # Update main cameras to sync with canvas
            self.update_main_cameras(canvas_ref)
        
        # Render camera view to texture
        self._render_camera_to_texture(screen, camera, canvas_ref)
        
        # Apply screen transformation
        gl.glPushMatrix()
        gl.glTranslatef(screen.position[0], screen.position[1], screen.position[2])
        gl.glRotatef(screen.rotation[0], 1, 0, 0)
        gl.glRotatef(screen.rotation[1], 0, 1, 0)
        gl.glRotatef(screen.rotation[2], 0, 0, 1)
        
        half_w = screen.size[0] / 2.0
        half_h = screen.size[1] / 2.0
        
        # Enable texturing
        gl.glEnable(gl.GL_TEXTURE_2D)
        if screen.texture_id:
            gl.glBindTexture(gl.GL_TEXTURE_2D, screen.texture_id)
        
        # Draw textured quad
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)  # White to show texture properly
        gl.glBegin(gl.GL_QUADS)
        gl.glTexCoord2f(0.0, 0.0); gl.glVertex3f(-half_w, -half_h, 0.0)
        gl.glTexCoord2f(1.0, 0.0); gl.glVertex3f(half_w, -half_h, 0.0)
        gl.glTexCoord2f(1.0, 1.0); gl.glVertex3f(half_w, half_h, 0.0)
        gl.glTexCoord2f(0.0, 1.0); gl.glVertex3f(-half_w, half_h, 0.0)
        gl.glEnd()
        
        gl.glDisable(gl.GL_TEXTURE_2D)
        
        # Draw screen border
        gl.glColor4f(screen.border_color[0], screen.border_color[1], 
                    screen.border_color[2], screen.border_color[3])
        gl.glLineWidth(screen.border_width)
        
        gl.glBegin(gl.GL_LINE_LOOP)
        gl.glVertex3f(-half_w, -half_h, 0.0)
        gl.glVertex3f(half_w, -half_h, 0.0)
        gl.glVertex3f(half_w, half_h, 0.0)
        gl.glVertex3f(-half_w, half_h, 0.0)
        gl.glEnd()
        
        gl.glLineWidth(1.0)
        gl.glPopMatrix()
    
    def render_overlay_screen(self, screen: Screen, canvas_ref=None):
        """Render an overlay screen on the main view with camera content."""
        if not canvas_ref or not screen.camera_id or screen.camera_id not in self.cameras:
            return
        
        camera = self.cameras[screen.camera_id]
        
        # Update cameras based on type
        if camera.type == CameraType.SPHERE_VECTOR:
            self.update_sphere_vector_camera()
        elif camera.type in [CameraType.MAIN, CameraType.MAIN_CLEAN]:
            # Update main cameras to sync with canvas
            self.update_main_cameras(canvas_ref)
        
        # Render camera view to texture
        self._render_camera_to_texture(screen, camera, canvas_ref)
        
        # Save current matrices
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPushMatrix()
        gl.glLoadIdentity()
        
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glLoadIdentity()
        
        # Set up orthographic projection for 2D overlay
        gl.glOrtho(0, 1, 0, 1, -1, 1)
        
        # Disable depth testing for overlay
        gl.glDisable(gl.GL_DEPTH_TEST)
        
        # Calculate screen coordinates
        x = screen.overlay_position[0]
        y = screen.overlay_position[1]
        w = screen.overlay_size[0]
        h = screen.overlay_size[1]
        
        # Enable texturing and draw camera view
        gl.glEnable(gl.GL_TEXTURE_2D)
        if screen.texture_id:
            gl.glBindTexture(gl.GL_TEXTURE_2D, screen.texture_id)
        
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)  # White to show texture properly
        gl.glBegin(gl.GL_QUADS)
        gl.glTexCoord2f(0.0, 0.0); gl.glVertex2f(x, y)
        gl.glTexCoord2f(1.0, 0.0); gl.glVertex2f(x + w, y)
        gl.glTexCoord2f(1.0, 1.0); gl.glVertex2f(x + w, y + h)
        gl.glTexCoord2f(0.0, 1.0); gl.glVertex2f(x, y + h)
        gl.glEnd()
        
        gl.glDisable(gl.GL_TEXTURE_2D)
        
        # Draw border
        gl.glColor4f(screen.border_color[0], screen.border_color[1], 
                    screen.border_color[2], screen.border_color[3])
        gl.glLineWidth(screen.border_width)
        
        gl.glBegin(gl.GL_LINE_LOOP)
        gl.glVertex2f(x, y)
        gl.glVertex2f(x + w, y)
        gl.glVertex2f(x + w, y + h)
        gl.glVertex2f(x, y + h)
        gl.glEnd()
        
        gl.glLineWidth(1.0)
        
        # Restore depth testing
        gl.glEnable(gl.GL_DEPTH_TEST)
        
        # Restore matrices
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_MODELVIEW)
    
    def _render_camera_to_texture(self, screen: Screen, camera: Camera, canvas_ref=None):
        """Render the camera view to a texture for the screen."""
        # Initialize framebuffer and texture if needed
        if screen.texture_id is None:
            self._init_screen_framebuffer(screen)
        
        if not screen.texture_id or not screen.framebuffer_id:
            return
        
        # Save current viewport and matrices
        viewport = gl.glGetIntegerv(gl.GL_VIEWPORT)
        
        # Bind framebuffer and set viewport
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, screen.framebuffer_id)
        gl.glViewport(0, 0, screen.texture_width, screen.texture_height)
        
        # Clear the framebuffer
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        
        # Set up projection matrix for camera
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPushMatrix()
        gl.glLoadIdentity()
        
        aspect_ratio = screen.texture_width / screen.texture_height
        glu.gluPerspective(camera.fov, aspect_ratio, camera.near_plane, camera.far_plane)
        
        # Set up modelview matrix for camera
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glLoadIdentity()
        
        # Apply camera view
        camera.apply_view()
        
        # Render the scene from camera perspective
        self._render_scene_for_camera(screen, camera, canvas_ref)
        
        # Restore matrices
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_MODELVIEW)
        
        # Restore framebuffer and viewport
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        gl.glViewport(viewport[0], viewport[1], viewport[2], viewport[3])
    
    def _init_screen_framebuffer(self, screen: Screen):
        """Initialize framebuffer and texture for screen rendering."""
        # Generate texture
        screen.texture_id = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, screen.texture_id)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, screen.texture_width, screen.texture_height, 
                       0, gl.GL_RGB, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        
        # Generate framebuffer
        screen.framebuffer_id = gl.glGenFramebuffers(1)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, screen.framebuffer_id)
        
        # Attach texture to framebuffer
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, 
                                 gl.GL_TEXTURE_2D, screen.texture_id, 0)
        
        # Generate and attach depth buffer
        screen.renderbuffer_id = gl.glGenRenderbuffers(1)
        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, screen.renderbuffer_id)
        gl.glRenderbufferStorage(gl.GL_RENDERBUFFER, gl.GL_DEPTH_COMPONENT, 
                               screen.texture_width, screen.texture_height)
        gl.glFramebufferRenderbuffer(gl.GL_FRAMEBUFFER, gl.GL_DEPTH_ATTACHMENT, 
                                   gl.GL_RENDERBUFFER, screen.renderbuffer_id)
        
        # Check framebuffer completeness
        if gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER) != gl.GL_FRAMEBUFFER_COMPLETE:
            print("ERROR: Framebuffer not complete for screen!")
        
        # Restore default framebuffer
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
    
    def _render_scene_for_camera(self, screen: Screen, camera: Camera, canvas_ref=None, recursion_depth=0):
        """Render the scene from the camera's perspective."""
        # Check if this is a clean camera (should exclude screens/overlays)
        is_clean_camera = camera.type == CameraType.MAIN_CLEAN
        
        # Render the main sphere
        gl.glPushMatrix()
        
        # Apply sphere transformation
        gl.glTranslatef(self.position[0], self.position[1], self.position[2])
        gl.glRotatef(self.rotation[0], 1, 0, 0)
        gl.glRotatef(self.rotation[1], 0, 1, 0)
        gl.glRotatef(self.rotation[2], 0, 0, 1)
        gl.glScalef(self.scale[0], self.scale[1], self.scale[2])
        
        # Render sphere surface and grids
        self.render_sphere_surface()
        self.render_longitude_latitude_grid()
        self.render_concentric_circles()
        self.render_dot_particles()
        self.render_neon_lines()
        self.render_wireframe()
        
        gl.glPopMatrix()
        
        # Render shapes (outside sphere transformation)
        gl.glPushMatrix()
        gl.glTranslatef(self.position[0], self.position[1], self.position[2])
        gl.glRotatef(self.rotation[0], 1, 0, 0)
        gl.glRotatef(self.rotation[1], 0, 1, 0)
        gl.glRotatef(self.rotation[2], 0, 0, 1)
        
        # Render vector if enabled (but not when stepped into a screen to avoid obstruction)
        if self.vector_enabled and not self._is_stepped_into_screen():
            self.render_vector()
        
        # Render custom shapes
        self.render_shapes()
        
        gl.glPopMatrix()
        
        # Render other world objects that would be visible from the main canvas
        if canvas_ref:
            # Render the red cube
            canvas_ref.draw_rainbow_cube()
            
            # Render the unified screen (original 2D screen)
            canvas_ref.draw_unified_screen()
        
        # Render screens with 1-level deep recursion
        if not is_clean_camera:  # Clean camera excludes other screens
            for other_screen_id, other_screen in self.screens.items():
                if other_screen.visible:
                    # Render this screen as a 3D object in the world
                    if other_screen.type == ScreenType.SCREEN_2D:
                        # Allow showing self at depth 0, but prevent deeper recursion
                        if other_screen.id != screen.id:
                            # Render other screens normally
                            self._render_screen_quad(other_screen, recursion_depth)
                        elif recursion_depth == 0:
                            # Render self but increment recursion depth
                            self._render_screen_quad(other_screen, recursion_depth + 1)
                    # Note: Overlay screens are not rendered in 3D space, they're overlays

    def _render_screen_quad(self, screen: Screen, recursion_depth=0):
        """Render a 2D screen as a visible quad in 3D space."""
        if screen.type != ScreenType.SCREEN_2D:
            return
        
        # If this is a self-reference at depth > 0, don't recurse deeper
        if recursion_depth > 0:
            # Just render a simple colored quad without content
            gl.glPushMatrix()
            gl.glTranslatef(screen.position[0], screen.position[1], screen.position[2])
            gl.glRotatef(screen.rotation[0], 1, 0, 0)
            gl.glRotatef(screen.rotation[1], 0, 1, 0)
            gl.glRotatef(screen.rotation[2], 0, 0, 1)
            
            # Render a simple colored quad to indicate the screen
            gl.glColor4f(0.5, 0.5, 0.8, 0.8)  # Light blue with transparency
            gl.glBegin(gl.GL_QUADS)
            
            half_width = screen.size[0] / 2.0
            half_height = screen.size[1] / 2.0
            
            gl.glVertex3f(-half_width, -half_height, 0.0)
            gl.glVertex3f(half_width, -half_height, 0.0)
            gl.glVertex3f(half_width, half_height, 0.0)
            gl.glVertex3f(-half_width, half_height, 0.0)
            
            gl.glEnd()
            gl.glPopMatrix()
            return
            
        gl.glPushMatrix()
        
        # Apply screen transformation
        gl.glTranslatef(screen.position[0], screen.position[1], screen.position[2])
        gl.glRotatef(screen.rotation[0], 1, 0, 0)
        gl.glRotatef(screen.rotation[1], 0, 1, 0)
        gl.glRotatef(screen.rotation[2], 0, 0, 1)
        
        # Enable texturing if the screen has a texture
        gl.glEnable(gl.GL_TEXTURE_2D)
        
        # Handle media screens with special texture updating
        if isinstance(screen, MediaScreen):
            screen.update_media_texture()
            if screen.media_texture_id:
                gl.glBindTexture(gl.GL_TEXTURE_2D, screen.media_texture_id)
                print(f"DEBUG: Rendering MediaScreen {screen.name} with texture {screen.media_texture_id}")
            else:
                gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
                print(f"DEBUG: MediaScreen {screen.name} has no texture, using fallback")
                # Show a colored quad so we can see the screen exists
                gl.glDisable(gl.GL_TEXTURE_2D)
        elif screen.texture_id:
            gl.glBindTexture(gl.GL_TEXTURE_2D, screen.texture_id)
        else:
            # Use a default white texture or color if no texture
            gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
        
        # Set up blending for transparency
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        
        # Render the quad
        if isinstance(screen, MediaScreen) and not screen.media_texture_id:
            # Use a distinct color for media screens without textures
            gl.glColor4f(1.0, 0.5, 0.8, 1.0)  # Pink to indicate media screen
        else:
            gl.glColor4f(1.0, 1.0, 1.0, 1.0)  # White with full opacity
        gl.glBegin(gl.GL_QUADS)
        
        # Calculate half-sizes
        half_width = screen.size[0] / 2.0
        half_height = screen.size[1] / 2.0
        
        # Bottom-left
        gl.glTexCoord2f(0.0, 0.0)
        gl.glVertex3f(-half_width, -half_height, 0.0)
        
        # Bottom-right
        gl.glTexCoord2f(1.0, 0.0)
        gl.glVertex3f(half_width, -half_height, 0.0)
        
        # Top-right
        gl.glTexCoord2f(1.0, 1.0)
        gl.glVertex3f(half_width, half_height, 0.0)
        
        # Top-left
        gl.glTexCoord2f(0.0, 1.0)
        gl.glVertex3f(-half_width, half_height, 0.0)
        
        gl.glEnd()
        
        # Disable blending and texturing
        gl.glDisable(gl.GL_BLEND)
        gl.glDisable(gl.GL_TEXTURE_2D)
        
        gl.glPopMatrix()

    # Serialization Methods
    
    def save_scene_to_dict(self):
        """Save the complete scene to a dictionary for serialization."""
        scene_data = {
            # Sphere properties
            'radius': self.radius,
            'resolution': self.resolution,
            'position': self.position.tolist(),
            'rotation': self.rotation.tolist(),
            'scale': self.scale.tolist(),
            'sphere_color': self.sphere_color.tolist(),
            'transparency': self.transparency,
            'wireframe_mode': self.wireframe_mode,
            'lighting_enabled': self.lighting_enabled,
            
            # Vector properties
            'vector_enabled': self.vector_enabled,
            'vector_direction': self.vector_direction.tolist(),
            'vector_length': self.vector_length,
            'vector_color': self.vector_color.tolist(),
            'vector_thickness': self.vector_thickness,
            'vector_roll': self.vector_roll,
            'vector_orientation_enabled': self.vector_orientation_enabled,
            
            # Grid properties
            'active_grids': list(self.active_grids),
            'longitude_lines': self.longitude_lines,
            'latitude_lines': self.latitude_lines,
            'concentric_rings': self.concentric_rings,
            'dot_density': self.dot_density,
            'neon_intensity': self.neon_intensity,
            
            # Shapes
            'shapes': [shape.to_dict() for shape in self.shapes.values()],
            
            # Cameras
            'cameras': [camera.to_dict() for camera in self.cameras.values()],
            'main_camera_id': self.main_camera_id,
            'main_clean_camera_id': self.main_clean_camera_id,
            'sphere_vector_camera_id': self.sphere_vector_camera_id,
            'original_screen_id': self.original_screen_id,
            
            # Screens
            'screens': [screen.to_dict() for screen in self.screens.values()]
        }
        
        return scene_data
    
    def load_scene_from_dict(self, scene_data):
        """Load the complete scene from a dictionary."""
        # Load sphere properties
        self.radius = scene_data.get('radius', 1.0)
        self.resolution = scene_data.get('resolution', 32)
        self.position = np.array(scene_data.get('position', [0.0, 0.0, 0.0]))
        self.rotation = np.array(scene_data.get('rotation', [0.0, 0.0, 0.0]))
        self.scale = np.array(scene_data.get('scale', [1.0, 1.0, 1.0]))
        self.sphere_color = np.array(scene_data.get('sphere_color', [0.2, 0.5, 1.0, 0.7]))
        self.transparency = scene_data.get('transparency', 0.7)
        self.wireframe_mode = scene_data.get('wireframe_mode', False)
        self.lighting_enabled = scene_data.get('lighting_enabled', True)
        
        # Load vector properties
        self.vector_enabled = scene_data.get('vector_enabled', True)
        self.vector_direction = np.array(scene_data.get('vector_direction', [1.0, 0.0, 0.0]))
        self.vector_length = scene_data.get('vector_length', 2.0)
        self.vector_color = np.array(scene_data.get('vector_color', [1.0, 0.0, 0.0, 1.0]))
        self.vector_thickness = scene_data.get('vector_thickness', 3.0)
        self.vector_roll = scene_data.get('vector_roll', 0.0)
        self.vector_orientation_enabled = scene_data.get('vector_orientation_enabled', False)
        
        # Load grid properties
        self.active_grids = set(scene_data.get('active_grids', []))
        self.longitude_lines = scene_data.get('longitude_lines', 16)
        self.latitude_lines = scene_data.get('latitude_lines', 12)
        self.concentric_rings = scene_data.get('concentric_rings', 8)
        self.dot_density = scene_data.get('dot_density', 200)
        self.neon_intensity = scene_data.get('neon_intensity', 1.0)
        
        # Load shapes
        self.shapes.clear()
        shapes_data = scene_data.get('shapes', [])
        for shape_data in shapes_data:
            shape = self._create_shape_from_dict(shape_data)
            if shape:
                self.shapes[shape.id] = shape
        
        # Load cameras
        self.cameras.clear()
        cameras_data = scene_data.get('cameras', [])
        for camera_data in cameras_data:
            camera = Camera()
            camera.from_dict(camera_data)
            self.cameras[camera.id] = camera
        
        # Restore camera IDs
        self.main_camera_id = scene_data.get('main_camera_id', self.main_camera_id)
        self.main_clean_camera_id = scene_data.get('main_clean_camera_id', self.main_clean_camera_id)
        self.sphere_vector_camera_id = scene_data.get('sphere_vector_camera_id', self.sphere_vector_camera_id)
        self.original_screen_id = scene_data.get('original_screen_id', self.original_screen_id)
        
        # Load screens
        self.screens.clear()
        screens_data = scene_data.get('screens', [])
        for screen_data in screens_data:
            # Check if this is a media screen
            if 'media_type' in screen_data:
                screen = MediaScreen()
            else:
                screen = Screen()
            screen.from_dict(screen_data)
            self.screens[screen.id] = screen
        
        # Regenerate geometry
        self.generate_sphere_geometry()
        self.generate_wireframe_geometry()
    
    def _create_shape_from_dict(self, shape_data):
        """Create a shape object from dictionary data."""
        shape_type = shape_data.get('type')
        
        # Create the appropriate shape type
        if shape_type == 'DotShape':
            shape = DotShape(shape_data.get('id'))
        elif shape_type == 'LineShape':
            shape = LineShape(shape_data.get('id'))
            # Restore line-specific properties
            if 'start_point' in shape_data:
                shape.start_point = np.array(shape_data['start_point'])
            if 'end_point' in shape_data:
                shape.end_point = np.array(shape_data['end_point'])
            if 'thickness' in shape_data:
                shape.thickness = shape_data['thickness']
        elif shape_type == 'BezierCurve':
            shape = BezierCurve(shape_data.get('id'))
            # Restore bezier-specific properties
            if 'control_points' in shape_data:
                shape.control_points = [np.array(pt) for pt in shape_data['control_points']]
            if 'resolution' in shape_data:
                shape.resolution = shape_data['resolution']
            if 'thickness' in shape_data:
                shape.thickness = shape_data['thickness']
        elif shape_type == 'PlaneShape':
            shape = PlaneShape(shape_data.get('id'))
            # Restore plane-specific properties
            if 'width' in shape_data:
                shape.width = shape_data['width']
            if 'height' in shape_data:
                shape.height = shape_data['height']
            if 'wireframe' in shape_data:
                shape.wireframe = shape_data['wireframe']
        elif shape_type == 'CubeShape':
            shape = CubeShape(shape_data.get('id'))
            # Restore cube-specific properties
            if 'size' in shape_data:
                shape.size = shape_data['size']
            if 'wireframe' in shape_data:
                shape.wireframe = shape_data['wireframe']
        elif shape_type == 'SphereShape':
            shape = SphereShape(shape_data.get('id'))
            # Restore sphere-specific properties
            if 'radius' in shape_data:
                shape.radius = shape_data['radius']
            if 'resolution' in shape_data:
                shape.resolution = shape_data['resolution']
            if 'wireframe' in shape_data:
                shape.wireframe = shape_data['wireframe']
        elif shape_type == 'CylinderShape':
            shape = CylinderShape(shape_data.get('id'))
            # Restore cylinder-specific properties
            if 'radius' in shape_data:
                shape.radius = shape_data['radius']
            if 'height' in shape_data:
                shape.height = shape_data['height']
            if 'resolution' in shape_data:
                shape.resolution = shape_data['resolution']
            if 'wireframe' in shape_data:
                shape.wireframe = shape_data['wireframe']
        else:
            return None
        
        # Load common shape properties
        shape.from_dict(shape_data)
        return shape

class Sphere3DCanvas(wx.glcanvas.GLCanvas):
    """OpenGL canvas for 3D sphere visualization."""
    
    def __init__(self, parent):
        # OpenGL attributes
        attribs = [
        wx.glcanvas.WX_GL_RGBA,
        wx.glcanvas.WX_GL_DOUBLEBUFFER,
        wx.glcanvas.WX_GL_DEPTH_SIZE, 24,
        wx.glcanvas.WX_GL_STENCIL_SIZE, 8,
        wx.glcanvas.WX_GL_SAMPLE_BUFFERS, 1,
        wx.glcanvas.WX_GL_SAMPLES, 4,  # 4x MSAA
        ]
        
        super().__init__(parent, attribList=attribs)
        
        self.context = wx.glcanvas.GLContext(self)
        self.init_gl = False
        
        # Sphere renderer
        self.sphere = SphereRenderer()
        
        # Set up callback for vector changes
        self.sphere._canvas_ref = self  # Allow sphere to call canvas methods
        
        # Camera settings
        self.camera_distance = 5.0
        self.camera_rotation_x = 0.0
        self.camera_rotation_y = 0.0
        self.camera_position = np.array([0.0, 0.0, 0.0])  # Camera offset from center
        
        # Movement settings
        self.movement_speed = 0.2  # Units per key press
        self.zoom_speed = 0.5  # Zoom speed for I/O keys
        
        # Mouse interaction
        self.last_mouse_pos = None
        self.mouse_dragging = False
        
        # Rainbow cube settings (fixed world position)
        self.rainbow_cube_position = np.array([2.0, 0.0, 2.0])  # Fixed position in world space
        self.rainbow_cube_size = 0.3  # Size of the cube
        
        # View vector and unified 2D screen system
        self.view_vector = np.array([0.0, 0.0, -1.0])  # Initial view direction
        
        # Camera projection mode
        self.camera_projection = "perspective"  # "perspective" or "orthographic"
        
        # Unified screen system - one physical screen with switchable rendering modes
        self.screen_enabled = True  # Screen is enabled by default
        self.screen_render_mode = "simple"  # "simple" (framebuffer) or "raytracing" (ray tracing) - start with original view
        self.screen_projection = "perspective"  # "perspective" or "orthographic" - projection mode for 2D screen
        
        # Unified screen properties (used by both rendering modes)
        self.screen_position = np.array([-3.0, 0.0, 0.0])  # Position of the 2D screen in 3D space
        self.screen_width = 2.0
        self.screen_height = 1.5
        
        # Simple mode framebuffer system
        self.framebuffer_width = 256
        self.framebuffer_height = 192
        self.framebuffer_id = None
        self.texture_id = None
        
        # Object selection and manipulation
        self.selected_object = "sphere"  # "sphere", "cube", "screen", or "none"
        
        # Screen stepping functionality
        self.stepped_in_screen_id = None  # ID of screen we're currently "inside"
        self.stepped_in_camera = None  # Camera object we're currently using
        self.original_camera_state = None  # Store original camera state for restoration
        self.rotation_mode = "world"  # "local" or "world"
        self.object_rotations = {
            "sphere": np.array([0.0, 0.0, 0.0]),
            "cube": np.array([0.0, 0.0, 0.0]),
            "screen": np.array([0.0, 0.0, 0.0])
        }
        
        # Bind events
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_mouse_up)
        self.Bind(wx.EVT_MOTION, self.on_mouse_motion)
        self.Bind(wx.EVT_MOUSEWHEEL, self.on_mouse_wheel)
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        
        # Timer for media screen updates
        self.media_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_media_timer, self.media_timer)
        self.media_timer.Start(33)  # ~30 FPS
        
        # Enable keyboard focus
        self.SetCanFocus(True)
    
    
    def update_screen_position_for_sphere_move(self, old_sphere_pos, new_sphere_pos):
        """Update the ray tracing camera when the sphere is moved.
        
        The screen and cube stay in their fixed world positions.
        Only the sphere + vector + shapes move, and the ray tracing camera follows.
        """
        # Update the ray tracing camera position (should follow sphere center)
        self.update_ray_tracing_camera()
        
        print(f"DEBUG: Sphere moved from {old_sphere_pos} to {new_sphere_pos}")
        print(f"DEBUG: Ray tracing camera updated to follow sphere")
    
    def setup_framebuffer(self):
        """Set up framebuffer for simple rendering mode."""
        if self.framebuffer_id is not None:
            return  # Already set up
            
        # Generate framebuffer
        self.framebuffer_id = gl.glGenFramebuffers(1)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.framebuffer_id)
        
        # Generate texture for color attachment
        self.texture_id = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture_id)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, self.framebuffer_width, 
                       self.framebuffer_height, 0, gl.GL_RGB, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        
        # Attach texture to framebuffer
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, 
                                 gl.GL_TEXTURE_2D, self.texture_id, 0)
        
        # Generate renderbuffer for depth attachment
        depth_buffer = gl.glGenRenderbuffers(1)
        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, depth_buffer)
        gl.glRenderbufferStorage(gl.GL_RENDERBUFFER, gl.GL_DEPTH_COMPONENT, 
                                self.framebuffer_width, self.framebuffer_height)
        gl.glFramebufferRenderbuffer(gl.GL_FRAMEBUFFER, gl.GL_DEPTH_ATTACHMENT, 
                                    gl.GL_RENDERBUFFER, depth_buffer)
        
        # Check framebuffer completeness
        if gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER) != gl.GL_FRAMEBUFFER_COMPLETE:
            print("ERROR: Framebuffer not complete!")
        
        # Unbind framebuffer
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        print("DEBUG: Simple framebuffer initialized")
    
    def setup_ray_tracing_screen(self):
        """Set up the ray tracing screen to show the sphere's view."""
        # Enable the sphere's ray tracing screen
        self.sphere.screen_enabled = True
        
        # Position the screen to the left of the sphere
        self.sphere.set_screen_position(-3.0, 0.0, 0.0)
        
        # Set screen size (same as before)
        self.sphere.set_screen_size(2.0, 1.5)
        
        # Set resolution for good performance
        self.sphere.set_screen_resolution(256, 192)
        
        # Configure the virtual camera to look from sphere center in the red vector direction
        self.update_ray_tracing_camera()
        
        print("DEBUG: Ray tracing screen initialized")
    
    def setup_unified_screen_system(self):
        """Set up the unified screen system that can switch between rendering modes."""
        # Always set up framebuffer for simple mode
        self.setup_framebuffer()
        
        # Configure the sphere's ray tracing screen to match our unified screen
        self.sync_raytracing_screen_with_unified()
        
        print(f"DEBUG: Unified screen system initialized, current mode: {self.screen_render_mode}")
    
    def sync_raytracing_screen_with_unified(self):
        """Sync the sphere's ray tracing screen with our unified screen properties."""
        # Set the sphere's ray tracing screen to match our unified screen
        self.sphere.set_screen_position(self.screen_position[0], self.screen_position[1], self.screen_position[2])
        self.sphere.set_screen_size(self.screen_width, self.screen_height)
        
        # Set resolution to match our framebuffer for consistency
        self.sphere.set_screen_resolution(self.framebuffer_width, self.framebuffer_height)
        
        # Ensure the sphere's screen is enabled for ray tracing
        self.sphere.screen_enabled = True
        
        # Configure ray tracing camera
        self.update_ray_tracing_camera()
        
        print(f"DEBUG: Ray tracing screen synced with unified screen properties")
    
    def update_ray_tracing_camera(self):
        """Update the ray tracing camera to look from sphere center along the red vector."""
        # Set camera position at actual sphere center (wherever it is)
        sphere_center = self.sphere.position.copy()
        
        print(f"DEBUG: update_ray_tracing_camera() called")
        print(f"DEBUG: Current sphere camera position: {getattr(self.sphere, 'screen_camera_position', 'NOT SET')}")
        print(f"DEBUG: Current sphere camera target: {getattr(self.sphere, 'screen_camera_target', 'NOT SET')}")
        
        # Update the sphere's camera position directly
        self.sphere.screen_camera_position = sphere_center.copy()
        
        # Set camera target based on red vector direction
        if hasattr(self.sphere, 'vector_direction'):
            red_vector = self.sphere.vector_direction
            normalized_vector = red_vector / np.linalg.norm(red_vector)
            # Look along the red vector from sphere center
            target = sphere_center + normalized_vector * 5.0
            
            # Update the sphere's camera target directly
            self.sphere.screen_camera_target = target.copy()
            
            print(f"DEBUG: NEW camera position set to: {self.sphere.screen_camera_position}")
            print(f"DEBUG: NEW camera target set to: {self.sphere.screen_camera_target}")
            print(f"DEBUG: Red vector used: {red_vector}")
            print(f"DEBUG: Normalized vector: {normalized_vector}")
        else:
            print(f"DEBUG: ERROR - sphere has no vector_direction attribute!")
            print(f"DEBUG: Available sphere attributes: {[attr for attr in dir(self.sphere) if not attr.startswith('_')]}")
    
    def draw_rainbow_cube(self):
        """Draw the rainbow cube at a fixed position."""
        gl.glPushMatrix()
        
        # Move to cube position
        gl.glTranslatef(self.rainbow_cube_position[0], 
                       self.rainbow_cube_position[1], 
                       self.rainbow_cube_position[2])
        
        # Apply cube rotation
        cube_rot = self.object_rotations["cube"]
        print(f"DEBUG: ===== SIMPLE MODE CUBE ROTATION =====")
        print(f"DEBUG: Simple mode applying cube rotation: [{cube_rot[0]:.1f}°, {cube_rot[1]:.1f}°, {cube_rot[2]:.1f}°]")
        print(f"DEBUG: =========================================")
        
        gl.glRotatef(cube_rot[0], 1.0, 0.0, 0.0)  # X rotation
        gl.glRotatef(cube_rot[1], 0.0, 1.0, 0.0)  # Y rotation
        gl.glRotatef(cube_rot[2], 0.0, 0.0, 1.0)  # Z rotation
        
        # Draw cube with different colored faces
        s = self.rainbow_cube_size
        gl.glBegin(gl.GL_QUADS)
        
        # Front face - RED
        gl.glColor3f(1.0, 0.0, 0.0)
        gl.glVertex3f(-s, -s, s)
        gl.glVertex3f(s, -s, s)
        gl.glVertex3f(s, s, s)
        gl.glVertex3f(-s, s, s)
        
        # Back face - BLUE
        gl.glColor3f(0.0, 0.0, 1.0)
        gl.glVertex3f(-s, -s, -s)
        gl.glVertex3f(-s, s, -s)
        gl.glVertex3f(s, s, -s)
        gl.glVertex3f(s, -s, -s)
        
        # Top face - GREEN
        gl.glColor3f(0.0, 1.0, 0.0)
        gl.glVertex3f(-s, s, -s)
        gl.glVertex3f(-s, s, s)
        gl.glVertex3f(s, s, s)
        gl.glVertex3f(s, s, -s)
        
        # Bottom face - YELLOW
        gl.glColor3f(1.0, 1.0, 0.0)
        gl.glVertex3f(-s, -s, -s)
        gl.glVertex3f(s, -s, -s)
        gl.glVertex3f(s, -s, s)
        gl.glVertex3f(-s, -s, s)
        
        # Right face - ORANGE
        gl.glColor3f(1.0, 0.5, 0.0)
        gl.glVertex3f(s, -s, -s)
        gl.glVertex3f(s, s, -s)
        gl.glVertex3f(s, s, s)
        gl.glVertex3f(s, -s, s)
        
        # Left face - PURPLE
        gl.glColor3f(0.5, 0.0, 1.0)
        gl.glVertex3f(-s, -s, -s)
        gl.glVertex3f(-s, -s, s)
        gl.glVertex3f(-s, s, s)
        gl.glVertex3f(-s, s, -s)
        gl.glEnd()
        
        gl.glPopMatrix()
    
    def render_simple_sphere_view(self):
        """Render the view from the sphere's direction to a texture (simple mode)."""
        if self.screen_render_mode != "simple" or not self.framebuffer_id or not self.texture_id:
            return
            
        # Bind framebuffer for off-screen rendering
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.framebuffer_id)
        gl.glViewport(0, 0, self.framebuffer_width, self.framebuffer_height)
        
        # Clear the framebuffer
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        
        # Set up projection matrix for sphere view
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPushMatrix()
        gl.glLoadIdentity()
        
        # Calculate FOV based on geometry angles
        if hasattr(self.sphere, 'cone_angle'):
            fov_vertical = self.sphere.cone_angle * 2.0
        else:
            fov_vertical = 60.0
        
        fov_vertical = max(10.0, min(170.0, fov_vertical))
        
        # Choose projection mode for 2D screen
        aspect_ratio = self.framebuffer_width / self.framebuffer_height
        if self.screen_projection == "orthographic":
            # Orthographic projection for 2D screen
            # Calculate orthographic bounds based on distance and FOV
            distance_to_target = 10.0  # Distance used in look_at calculation
            ortho_height = distance_to_target * math.tan(math.radians(fov_vertical / 2.0))
            ortho_width = ortho_height * aspect_ratio
            gl.glOrtho(-ortho_width, ortho_width, -ortho_height, ortho_height, 0.1, 100.0)
            print(f"DEBUG: 2D screen using orthographic projection - bounds: ±{ortho_width:.2f} x ±{ortho_height:.2f}")
        else:
            # Perspective projection for 2D screen (default)
            glu.gluPerspective(fov_vertical, aspect_ratio, 0.1, 100.0)
            print(f"DEBUG: 2D screen using perspective projection - FOV: {fov_vertical:.1f}°")
        
        # Set up modelview matrix for sphere view
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glLoadIdentity()
        
        # Position camera at actual sphere center looking in view vector direction
        sphere_pos = self.sphere.position.copy()
        view_dir = self.view_vector
        look_at = sphere_pos + view_dir * 10.0
        
        print(f"DEBUG: ===== SIMPLE MODE CAMERA SETUP =====")
        print(f"DEBUG: Simple mode sphere_pos: {sphere_pos}")
        print(f"DEBUG: Simple mode view_dir: {view_dir}")
        print(f"DEBUG: Simple mode look_at: {look_at}")
        
        # Debug: Check if we're looking toward the cube
        cube_pos = np.array([2.0, 0.0, 2.0])  # Known cube position
        direction_to_cube = cube_pos - sphere_pos
        direction_to_cube_normalized = direction_to_cube / np.linalg.norm(direction_to_cube)
        dot_with_cube_dir = np.dot(view_dir, direction_to_cube_normalized)
        angle_to_cube = math.degrees(math.acos(np.clip(dot_with_cube_dir, 
-1.0, 1.0)))
        
        print(f"DEBUG: Cube position: {cube_pos}")
        print(f"DEBUG: Direction to cube: {direction_to_cube_normalized}")
        print(f"DEBUG: View direction: {view_dir}")
        print(f"DEBUG: Angle between view and cube direction: {angle_to_cube:.1f}° (should be close to 0°)")
        print(f"DEBUG: Are we looking toward cube? {angle_to_cube < 30}")
        print(f"DEBUG: ==============================================")
        
        # Calculate up vector with roll rotation applied
        world_up = np.array([0.0, 1.0, 0.0])
        right = np.cross(view_dir, world_up)
        if np.linalg.norm(right) < 0.001:
            right = np.array([1.0, 0.0, 0.0])
        right = right / np.linalg.norm(right)
        up = np.cross(right, view_dir)
        up = -up / np.linalg.norm(up)  # Negate up vector to fix upside-down 2D screen
        
        # Apply roll rotation around the view direction (vector axis)
        roll_angle = math.radians(self.sphere.vector_roll)
        cos_roll = math.cos(roll_angle)
        sin_roll = math.sin(roll_angle)
        
        # Apply 2D rotation to the up and right vectors in their plane
        new_right = cos_roll * right + sin_roll * up
        new_up = -sin_roll * right + cos_roll * up
        
        right = new_right / np.linalg.norm(new_right)
        up = new_up / np.linalg.norm(new_up)
        
        # Keep original look_at direction (forward along vector), only flip up vector for orientation
        flipped_up = -up  # Only flip up vector to fix screen orientation
        glu.gluLookAt(sphere_pos[0], sphere_pos[1], sphere_pos[2],
                     look_at[0], look_at[1], look_at[2],  # Use original look_at (forward direction)
                     flipped_up[0], flipped_up[1], flipped_up[2])
        
        # Render the scene from sphere's perspective
        self.draw_rainbow_cube()  # Actually multicolored now
        # Note: Reference objects disabled in 2D screen to avoid yellow box artifact
        # The reference objects include a yellow cube that was appearing as an artifact
        # self.draw_reference_objects()
        
        print(f"DEBUG: Simple 2D screen rendered - reference objects disabled to prevent yellow box artifact")
        
        # Restore matrices
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_MODELVIEW)
        
        # Unbind framebuffer
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def draw_simple_2d_screen(self):
        """Draw the 2D screen as a quad in 3D space showing the sphere's view (simple mode)."""
        if self.screen_render_mode != "simple" or not self.texture_id:
            return
            
        gl.glPushMatrix()
        
        # Move to screen position
        gl.glTranslatef(self.screen_position[0], 
                       self.screen_position[1], 
                       self.screen_position[2])
        
        # Apply screen rotation
        screen_rot = self.object_rotations["screen"]
        gl.glRotatef(screen_rot[0], 1.0, 0.0, 0.0)  # X rotation
        gl.glRotatef(screen_rot[1], 0.0, 1.0, 0.0)  # Y rotation
        gl.glRotatef(screen_rot[2], 0.0, 0.0, 1.0)  # Z rotation
        
        # Enable texture mapping
        gl.glEnable(gl.GL_TEXTURE_2D)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture_id)
        
        # Set white color for texture
        gl.glColor3f(1.0, 1.0, 1.0)
        
        # Draw the screen as a quad
        w = self.screen_width / 2
        h = self.screen_height / 2
        
        gl.glBegin(gl.GL_QUADS)
        gl.glTexCoord2f(0.0, 0.0); gl.glVertex3f(-w, -h, 0.0)
        gl.glTexCoord2f(1.0, 0.0); gl.glVertex3f(w, -h, 0.0)
        gl.glTexCoord2f(1.0, 1.0); gl.glVertex3f(w, h, 0.0)
        gl.glTexCoord2f(0.0, 1.0); gl.glVertex3f(-w, h, 0.0)
        gl.glEnd()
        
        # Disable texture mapping
        gl.glDisable(gl.GL_TEXTURE_2D)
        
        # Draw a border around the screen
        gl.glColor3f(0.2, 0.2, 0.2)
        gl.glLineWidth(3.0)
        gl.glBegin(gl.GL_LINE_LOOP)
        gl.glVertex3f(-w, -h, 0.01)
        gl.glVertex3f(w, -h, 0.01)
        gl.glVertex3f(w, h, 0.01)
        gl.glVertex3f(-w, h, 0.01)
        gl.glEnd()
        gl.glLineWidth(1.0)
        
        gl.glPopMatrix()
    
    def draw_unified_screen(self):
        """Draw the unified screen using the current rendering mode."""
        print(f"DEBUG: ===== CANVAS draw_unified_screen() CALLED =====")
        print(f"DEBUG: screen_enabled: {self.screen_enabled}, screen_render_mode: {self.screen_render_mode}")
        
        if not self.screen_enabled:
            print(f"DEBUG: Canvas screen disabled - not drawing unified screen")
            return
        
        if self.screen_render_mode == "simple":
            print(f"DEBUG: Canvas drawing simple 2D screen")
            self.draw_simple_2d_screen()
        elif self.screen_render_mode == "raytracing":
            print(f"DEBUG: Canvas in ray tracing mode - sphere should handle screen rendering")
            # The ray tracing screen is drawn by the sphere renderer
            # We just need to ensure it's enabled and positioned correctly
            if hasattr(self.sphere, 'screen_enabled'):
                self.sphere.screen_enabled = True
                print(f"DEBUG: Enabled sphere's ray tracing screen")
        else:
            print(f"DEBUG: Unknown screen render mode: {self.screen_render_mode}")
        
        print(f"DEBUG: Drew unified screen in {self.screen_render_mode} mode")
        
        # Debug: Show which rendering mode is active
        if self.screen_render_mode == "raytracing":
            print(f"DEBUG: Ray tracing mode active - screen follows red vector in real-time")
        elif self.screen_render_mode == "simple":
            print(f"DEBUG: Simple mode active - screen shows original 2D framebuffer view")
        else:
            print(f"DEBUG: Unknown screen mode: {self.screen_render_mode}")
    
    def update_sphere_ray_tracing_view(self):
        """Update the ray tracing screen based on the sphere's red vector direction."""
        print(f"DEBUG: ===== CANVAS update_sphere_ray_tracing_view() CALLED =====")
        print(f"DEBUG: Screen render mode: {self.screen_render_mode}")
        print(f"DEBUG: Screen enabled: {getattr(self.sphere, 'screen_enabled', 'NOT SET')}")
        
        if self.screen_render_mode != "raytracing":
            print(f"DEBUG: Skipping ray tracing update - mode is {self.screen_render_mode}")
            return
        if not hasattr(self.sphere, 'screen_enabled') or not self.sphere.screen_enabled:
            print(f"DEBUG: Skipping ray tracing update - screen not enabled")
            return
        
        print(f"DEBUG: Calling update_ray_tracing_camera()...")
        
        # Update the ray tracing camera to follow the red vector
        self.update_ray_tracing_camera()
        
        # Force screen update
        if hasattr(self.sphere, 'screen_needs_update'):
            self.sphere.screen_needs_update = True
            print(f"DEBUG: Set screen_needs_update = True")
        
        print(f"DEBUG: Updated ray tracing view for red vector: {self.sphere.vector_direction}")
    
    def draw_reference_objects(self):
        """Draw some reference objects in the scene for the sphere view."""
        # Draw a simple grid on the ground
        gl.glColor3f(0.5, 0.5, 0.5)
        gl.glBegin(gl.GL_LINES)
        for i in range(-5, 6):
            # Horizontal lines
            gl.glVertex3f(-5.0, -1.0, i)
            gl.glVertex3f(5.0, -1.0, i)
            # Vertical lines
            gl.glVertex3f(i, -1.0, -5.0)
            gl.glVertex3f(i, -1.0, 5.0)
        gl.glEnd()
        
        # Draw some colored cubes at different positions
        positions = [
            (np.array([1.0, 0.0, 1.0]), (0.0, 1.0, 0.0)),  # Green cube
            (np.array([-1.0, 0.0, 1.0]), (0.0, 0.0, 1.0)), # Blue cube
            (np.array([0.0, 1.0, -1.0]), (1.0, 1.0, 0.0))  # Yellow cube
        ]
        
        for pos, color in positions:
            gl.glPushMatrix()
            gl.glTranslatef(pos[0], pos[1], pos[2])
            gl.glColor3f(color[0], color[1], color[2])
            
            # Draw a small cube
            s = 0.2
            gl.glBegin(gl.GL_QUADS)
            # Just draw a simple cube (abbreviated for space)
            # Front
            gl.glVertex3f(-s, -s, s); gl.glVertex3f(s, -s, s); gl.glVertex3f(s, s, s); gl.glVertex3f(-s, s, s)
            # Back  
            gl.glVertex3f(-s, -s, -s); gl.glVertex3f(-s, s, -s); gl.glVertex3f(s, s, -s); gl.glVertex3f(s, -s, -s)
            # Top
            gl.glVertex3f(-s, s, -s); gl.glVertex3f(-s, s, s); gl.glVertex3f(s, s, s); gl.glVertex3f(s, s, -s)
            # Bottom
            gl.glVertex3f(-s, -s, -s); gl.glVertex3f(s, -s, -s); gl.glVertex3f(s, -s, s); gl.glVertex3f(-s, -s, s)
            # Right
            gl.glVertex3f(s, -s, -s); gl.glVertex3f(s, s, -s); gl.glVertex3f(s, s, s); gl.glVertex3f(s, -s, s)
            # Left
            gl.glVertex3f(-s, -s, -s); gl.glVertex3f(-s, -s, s); gl.glVertex3f(-s, s, s); gl.glVertex3f(-s, s, -s)
            gl.glEnd()
            
            gl.glPopMatrix()
    
    
    def set_selected_object(self, object_name):
        """Set the currently selected object for manipulation."""
        # Accept traditional objects and new dynamic objects
        valid_objects = ["sphere", "cube", "screen", "none"]
        is_dynamic = (object_name.startswith("shape_") or 
                      object_name.startswith("camera_") or 
                      object_name.startswith("screen_"))
        
        if object_name in valid_objects or is_dynamic:
            self.selected_object = object_name
            print(f"DEBUG: Selected object changed to: {object_name}")
        else:
            print(f"DEBUG: Invalid object name: {object_name}")

    def step_into_screen(self, screen_id):
        """Step into a screen's camera view, making it the main view."""
        screen = self.sphere.get_screen(screen_id)
        if not screen or not screen.camera_id:
            print(f"DEBUG: Cannot step into screen {screen_id} - no valid camera")
            return False
        
        camera = self.sphere.get_camera(screen.camera_id)
        if not camera:
            print(f"DEBUG: Cannot step into screen {screen_id} - camera {screen.camera_id} not found")
            return False
        
        print(f"DEBUG: Stepping into screen {screen.name} with camera {camera.name}")
        
        # Store the screen we're stepping into
        self.stepped_in_screen_id = screen_id
        
        # Apply the camera's perspective to the main view
        self._apply_camera_to_main_view(camera)
        
        # If this is a sphere vector camera, ensure it's updated
        if camera.type == CameraType.SPHERE_VECTOR:
            self.sphere.update_sphere_vector_camera()
        
        # Refresh the view
        self.Refresh()
        return True

    def exit_screen_view(self):
        """Exit the current screen view and return to the original camera state."""
        if self.stepped_in_screen_id is None:
            return False
        
        print(f"DEBUG: Exiting screen view, returning to original camera state")
        
        # Restore original camera state
        if self.original_camera_state:
            self.camera_position = self.original_camera_state['position'].copy()
            self.camera_rotation_x = self.original_camera_state['rotation_x']
            self.camera_rotation_y = self.original_camera_state['rotation_y']
            self.camera_distance = self.original_camera_state['distance']
        
        # Clear stepped-in state
        self.stepped_in_screen_id = None
        self.stepped_in_camera = None
        self.original_camera_state = None
        
        # Update main cameras to reflect the restored state
        self.sphere.update_main_cameras(self)
        
        # Refresh the view
        self.Refresh()
        return True

    def _apply_camera_to_main_view(self, camera):
        """Apply a camera's perspective to the main view camera system."""
        print(f"DEBUG: Applying camera {camera.name} to main view")
        print(f"DEBUG: Camera position: {camera.position}")
        print(f"DEBUG: Camera target: {camera.target}")
        
        # Store the original camera parameters for direct usage in rendering
        self.stepped_in_camera = camera
        
        # For UI consistency, we still calculate orbital parameters for mouse controls
        # Set the orbit center to the camera's target
        self.camera_position = np.array([camera.target[0], camera.target[1], camera.target[2]])
        
        # Calculate distance from camera position to target
        camera_to_target = np.array([camera.position[0], camera.position[1], camera.position[2]]) - self.camera_position
        self.camera_distance = np.linalg.norm(camera_to_target)
        
        # Calculate the rotation angles to point from target to camera position
        if self.camera_distance > 0.001:  # Avoid division by zero
            # Normalize the direction vector
            direction = camera_to_target / self.camera_distance
            
            # Calculate Y rotation (horizontal rotation)
            self.camera_rotation_y = math.degrees(math.atan2(direction[0], -direction[2]))
            
            # Calculate X rotation (vertical rotation)
            horizontal_distance = math.sqrt(direction[0]**2 + direction[2]**2)
            self.camera_rotation_x = math.degrees(math.atan2(-direction[1], horizontal_distance))
        else:
            # Camera is at target, use default rotations
            self.camera_rotation_x = 0.0
            self.camera_rotation_y = 0.0
        
        print(f"DEBUG: Converted to orbital camera:")
        print(f"DEBUG: - Position (orbit center): {self.camera_position}")
        print(f"DEBUG: - Distance: {self.camera_distance}")
        print(f"DEBUG: - Rotation X: {self.camera_rotation_x}")
        print(f"DEBUG: - Rotation Y: {self.camera_rotation_y}")
        
        # Update main cameras to reflect the new state
        self.sphere.update_main_cameras(self)

    def on_media_timer(self, event):
        """Timer callback to update media screens and refresh display."""
        # Check if we have any media screens that need updating
        has_media_screens = False
        for screen in self.sphere.get_all_screens():
            if isinstance(screen, MediaScreen):
                has_media_screens = True
                break
        
        # Only refresh if we have media screens to avoid unnecessary redraws
        if has_media_screens:
            self.Refresh()
        
    def set_rotation_mode(self, mode):
        """Set the rotation mode (local or world)."""
        if mode in ["local", "world"]:
            self.rotation_mode = mode
            print(f"DEBUG: Rotation mode changed to: {mode}")
    
    def reset_selected_object(self):
        """Reset the selected object to default position/rotation."""
        if self.selected_object in self.object_rotations:
            self.object_rotations[self.selected_object] = np.array([0.0, 
0.0, 0.0])
            if self.selected_object == "sphere":
                self.camera_rotation_x = 0.0
                self.camera_rotation_y = 0.0
                self.camera_position = np.array([0.0, 0.0, 0.0])
            elif self.selected_object == "cube":
                self.rainbow_cube_position = np.array([2.0, 0.0, 2.0])
            elif self.selected_object == "screen":
                self.screen_position = np.array([-3.0, 0.0, 0.0])
            self.Refresh()
    
    def set_screen_render_mode(self, mode):
        """Set the unified screen's rendering mode: 'simple' or 
'raytracing'."""
        if mode in ["simple", "raytracing"]:
            old_mode = self.screen_render_mode
            self.screen_render_mode = mode
            print(f"DEBUG: Switching unified screen render mode from {old_mode} to {mode}")
            
            # Enable/disable ray tracing screen based on mode
            if mode == "raytracing":
                self.sphere.screen_enabled = True
                self.sync_raytracing_screen_with_unified()
            else:
                if hasattr(self.sphere, 'screen_enabled'):
                    self.sphere.screen_enabled = False
            
            # Update view immediately
            self.update_view_vector()
            self.Refresh()
    
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
        
        # Sphere screen state is now explicitly set in each toggle case above
        # No additional sync needed
        
        sphere_enabled = getattr(self.sphere, 'screen_enabled', 'NOT SET')
        print(f"DEBUG: Screen state - canvas_enabled: {self.screen_enabled}, mode: {self.screen_render_mode}, sphere_enabled: {sphere_enabled}")
        self.Refresh()
    
    def disable_screen(self):
        """Disable the 2D screen completely."""
        self.screen_enabled = False
        
        # Also disable ray tracing screen
        if hasattr(self.sphere, 'screen_enabled'):
            self.sphere.screen_enabled = False
        
        print(f"DEBUG: Screen disabled completely")
        self.Refresh()
    
    def draw_view_vector_indicator(self):
        """Draw a visual indicator showing where the 2D screen is looking."""
        # Draw a bright cyan line showing the 2D screen's view direction
        gl.glColor3f(0.0, 1.0, 1.0)  # Bright cyan to distinguish from red vector
        gl.glLineWidth(2.0)
        
        # Get actual sphere position
        sphere_pos = self.sphere.position
        
        gl.glBegin(gl.GL_LINES)
        # Start at actual sphere center
        gl.glVertex3f(sphere_pos[0], sphere_pos[1], sphere_pos[2])
        # End at view vector direction (what the 2D screen is showing)
        view_end = sphere_pos + self.view_vector * 2.5  # Make line shorter than red vector
        gl.glVertex3f(view_end[0], view_end[1], view_end[2])
        gl.glEnd()
        
        # Draw text indicator near the end
        gl.glPushMatrix()
        gl.glTranslatef(view_end[0], view_end[1], view_end[2])
        gl.glColor3f(0.0, 1.0, 1.0)  # Cyan
        # Draw a small indicator
        s = 0.05
        gl.glBegin(gl.GL_QUADS)
        gl.glVertex3f(-s, -s, s); gl.glVertex3f(s, -s, s); gl.glVertex3f(s, s, s); gl.glVertex3f(-s, s, s)
        gl.glVertex3f(-s, -s, -s); gl.glVertex3f(-s, s, -s); gl.glVertex3f(s, s, -s); gl.glVertex3f(s, -s, -s)
        gl.glEnd()
        gl.glPopMatrix()
        
        gl.glLineWidth(1.0)  # Reset line width
    
    
    def update_sphere_view_vector(self):
        """Update the sphere's view vector to match the red vector arrow direction."""
        print(f"DEBUG: ===== CANVAS update_sphere_view_vector() CALLED =====")
        
        # Use the sphere's red vector direction for ALL screen views (simple and ray tracing)
        if hasattr(self.sphere, 'vector_direction'):
            # Get the red vector direction and normalize it (roll is applied in camera coordinate system)
            red_vector = self.sphere.vector_direction
            self.view_vector = red_vector / np.linalg.norm(red_vector)
            
            print(f"DEBUG: Canvas syncing view_vector with sphere vector_direction: {red_vector}")
            print(f"DEBUG: Normalized view_vector: {self.view_vector}")
            
            # Update the ray tracing screen to follow this direction (if in ray tracing mode)
            if self.screen_render_mode == "raytracing":
                self.update_sphere_ray_tracing_view()
        else:
            # Fallback to default direction if no vector found
            self.view_vector = np.array([1.0, 0.0, 0.0])
            print(f"DEBUG: Canvas using fallback vector direction")
        
        print(f"DEBUG: Red vector direction: {self.sphere.vector_direction}")
        print(f"DEBUG: Normalized view vector: [{self.view_vector[0]:.3f}, {self.view_vector[1]:.3f}, {self.view_vector[2]:.3f}]")
        print(f"DEBUG: Red cube position: {self.rainbow_cube_position}")
        
        # Calculate if cube should be visible
        cube_direction = (self.rainbow_cube_position - self.sphere.position) / np.linalg.norm(self.rainbow_cube_position - self.sphere.position)
        dot_product = np.dot(self.view_vector, cube_direction)
        angle_to_cube = np.arccos(np.clip(dot_product, -1.0, 1.0)) * 180.0 / np.pi
        
        print(f"DEBUG: Expected direction to cube: {cube_direction}")
        print(f"DEBUG: Actual view vector: {self.view_vector}")
        print(f"DEBUG: Dot product: {dot_product:.3f}")
        
        # If the view vector is not pointing toward the cube, suggest correction
        if angle_to_cube > 30:
            print(f"DEBUG: ⚠️ WARNING: View vector not pointing toward cube!")
            print(f"DEBUG: Consider setting vector direction to point toward cube")
            print(f"DEBUG: Suggested vector direction: {cube_direction * 3.0}")  # Scale for visibility
        print(f"DEBUG: Angle to cube: {angle_to_cube:.1f}° (should be < 30° to be visible)")
        print(f"DEBUG: Cube direction: [{cube_direction[0]:.3f}, {cube_direction[1]:.3f}, {cube_direction[2]:.3f}]")
    
    def update_view_vector(self):
        """Update the view vector based on sphere rotation (where the sphere is 'looking')."""
        # Always update the sphere's view vector based on current camera rotation
        # This ensures the 2D screen always shows what the sphere is "looking at"
        self.update_sphere_view_vector()
        
        # Force ray tracing screen update during user interaction
        if hasattr(self.sphere, 'screen_needs_update') and self.mouse_dragging:
            self.sphere.screen_needs_update = True
            self.sphere.screen_last_update = 0.0  # Force immediate update during interaction
    
    def init_opengl(self):
        """Initialize OpenGL settings."""
        if self.init_gl:
            return
        
        self.SetCurrent(self.context)
        
        # Enable depth testing
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glDepthFunc(gl.GL_LESS)
        
        # Enable face culling
        gl.glEnable(gl.GL_CULL_FACE)
        gl.glCullFace(gl.GL_BACK)
        
        # Set clear color (dark background)
        gl.glClearColor(0.1, 0.1, 0.1, 1.0)
        
        # Enable smooth shading
        gl.glShadeModel(gl.GL_SMOOTH)
        
        # Set up lighting
        gl.glEnable(gl.GL_LIGHTING)
        gl.glEnable(gl.GL_LIGHT0)
        
        # Light position
        light_pos = [2.0, 2.0, 5.0, 1.0]
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_POSITION, light_pos)
        
        # Light colors
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_DIFFUSE, [0.8, 0.8, 0.8, 1.0])
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
        
        # Enable point smoothing for better dot rendering
        gl.glEnable(gl.GL_POINT_SMOOTH)
        gl.glHint(gl.GL_POINT_SMOOTH_HINT, gl.GL_NICEST)
        
        # Enable line smoothing
        gl.glEnable(gl.GL_LINE_SMOOTH)
        gl.glHint(gl.GL_LINE_SMOOTH_HINT, gl.GL_NICEST)
        
        # Set up unified screen system
        self.setup_unified_screen_system()
    
        self.init_gl = True
    
    def setup_viewport(self):
        """Set up the viewport and projection matrix."""
        size = self.GetSize()
        gl.glViewport(0, 0, size.width, size.height)
        
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        
        aspect_ratio = size.width / size.height if size.height > 0 else 1.0
        
        # Choose projection mode based on camera_projection setting
        if self.camera_projection == "orthographic":
            # Orthographic projection - no perspective distortion
            # Calculate orthographic bounds based on camera distance and FOV
            if hasattr(self.sphere, 'cone_angle'):
                fov_vertical = self.sphere.cone_angle * 2.0
            else:
                fov_vertical = 60.0  # Default FOV
            
            # Convert FOV to orthographic bounds at camera distance
            ortho_height = self.camera_distance * math.tan(math.radians(fov_vertical / 2.0))
            ortho_width = ortho_height * aspect_ratio
            
            gl.glOrtho(-ortho_width, ortho_width, -ortho_height, ortho_height, 0.1, 100.0)
            print(f"DEBUG: Using orthographic projection - bounds: ±{ortho_width:.2f} x ±{ortho_height:.2f}")
        else:
            # Perspective projection (default)
            if hasattr(self.sphere, 'cone_angle'):
                fov_vertical = self.sphere.cone_angle * 2.0
            else:
                fov_vertical = 60.0  # Default FOV
            glu.gluPerspective(fov_vertical, aspect_ratio, 0.1, 100.0)
            print(f"DEBUG: Using perspective projection - FOV: {fov_vertical:.1f}°")
        
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()
    
    def setup_camera(self):
        """Set up the camera view."""
        # If we're stepped into a screen, use that camera's exact view
        if self.stepped_in_camera:
            # Use gluLookAt with the stepped-in camera's parameters
            glu.gluLookAt(
                self.stepped_in_camera.position[0], self.stepped_in_camera.position[1], self.stepped_in_camera.position[2],  # eye
                self.stepped_in_camera.target[0], self.stepped_in_camera.target[1], self.stepped_in_camera.target[2],      # center
                self.stepped_in_camera.up[0], self.stepped_in_camera.up[1], self.stepped_in_camera.up[2]                 # up
            )
        else:
            # Use the normal orbital camera system
            # Position camera at distance
            gl.glTranslatef(0.0, 0.0, -self.camera_distance)
            
            # Apply camera rotations
            gl.glRotatef(self.camera_rotation_x, 1.0, 0.0, 0.0)
            gl.glRotatef(self.camera_rotation_y, 0.0, 1.0, 0.0)
            
            # Apply camera position offset (for keyboard movement)
            gl.glTranslatef(-self.camera_position[0], 
    -self.camera_position[1], -self.camera_position[2])
    
    def get_camera_forward_vector(self):
        """Get the camera's forward vector based on current rotation."""
        import math
        rot_x_rad = math.radians(self.camera_rotation_x)
        rot_y_rad = math.radians(self.camera_rotation_y)
        
        # Calculate forward vector from rotation
        forward = np.array([
            math.sin(rot_y_rad) * math.cos(rot_x_rad),
            -math.sin(rot_x_rad),
            -math.cos(rot_y_rad) * math.cos(rot_x_rad)
        ])
        return forward / np.linalg.norm(forward)
    
    def get_camera_right_vector(self):
        """Get the camera's right vector."""
        import math
        rot_y_rad = math.radians(self.camera_rotation_y)
        
        # Right vector is perpendicular to forward in the horizontal plane
        right = np.array([
            math.cos(rot_y_rad),
            0.0,
            math.sin(rot_y_rad)
        ])
        return right / np.linalg.norm(right)
    
    def get_camera_up_vector(self):
        """Get the camera's up vector."""
        # Cross product of right and forward vectors
        forward = self.get_camera_forward_vector()
        right = self.get_camera_right_vector()
        up = np.cross(right, forward)
        return up / np.linalg.norm(up)
    
    def on_paint(self, event):
        """Handle paint events."""
        self.SetCurrent(self.context)
        self.init_opengl()
        
        # Update view vector for sphere projection
        self.update_view_vector()
        
        # Render sphere view to texture for simple mode
        if self.screen_render_mode == "simple":
            self.render_simple_sphere_view()
        
        # Clear main buffers
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        
        # Set up viewport and camera
        self.setup_viewport()
        self.setup_camera()
        
        # Render the sphere (includes ray tracing screen if in raytracing mode)
        self.sphere.render()
        
        # Draw the multicolored cube
        self.draw_rainbow_cube()  # Function name kept for compatibility
        
        # Draw the unified screen
        self.draw_unified_screen()
        
        # Render custom screens
        self.sphere.render_screens(self)
        
        # Screen rotation is now handled directly in the respective rendering methods
        
        # Draw view vector indicator - REMOVED per user request
        # self.draw_view_vector_indicator()
        
        # Swap buffers
        self.SwapBuffers()
    
    def on_size(self, event):
        """Handle resize events."""
        self.Refresh()
        event.Skip()
    
    def on_mouse_down(self, event):
        """Handle mouse down events."""
        self.last_mouse_pos = event.GetPosition()
        self.mouse_dragging = True
        self.CaptureMouse()
        
        # Set keyboard focus to enable arrow key navigation
        self.SetFocus()
    
    def on_mouse_up(self, event):
        """Handle mouse up events."""
        if self.HasCapture():
            self.ReleaseMouse()
            self.mouse_dragging = False
            self.last_mouse_pos = None
    
    def on_mouse_motion(self, event):
        """Handle mouse motion for camera rotation."""
        if not self.mouse_dragging or not self.last_mouse_pos:
            return
        
        current_pos = event.GetPosition()
        dx = current_pos.x - self.last_mouse_pos.x
        dy = current_pos.y - self.last_mouse_pos.y
        
        # Apply rotation based on selected object
        if self.selected_object == "sphere":
            # Rotate the sphere's red vector based on mouse movement
            # This will update what the ray tracing camera is looking at
            sensitivity = 0.01
            
            # Get current vector direction
            current_vector = self.sphere.vector_direction.copy()
            
            # Apply rotation based on mouse movement
            # Horizontal movement (dx) rotates around Y axis
            # Vertical movement (dy) rotates around X axis
            
            # Convert to spherical coordinates for easier rotation
            x, y, z = current_vector
            r = np.linalg.norm(current_vector)
            theta = math.atan2(y, x)  # azimuth
            phi = math.acos(z / r) if r > 0 else 0  # polar angle
            
            # Apply mouse deltas
            theta += dx * sensitivity  # Horizontal rotation
            phi += dy * sensitivity    # Vertical rotation
            
            # Clamp phi to avoid gimbal lock
            phi = max(0.01, min(math.pi - 0.01, phi))
            
            # Convert back to Cartesian
            new_x = r * math.sin(phi) * math.cos(theta)
            new_y = r * math.sin(phi) * math.sin(theta)  
            new_z = r * math.cos(phi)
            
            # Update the sphere's vector direction
            self.sphere.set_vector_direction(new_x, new_y, new_z)
            
            # Update the ray tracing camera to follow the new red vector
            self.update_sphere_view_vector()
            
            # Force ray tracing screen update immediately
            if hasattr(self.sphere, 'screen_needs_update'):
                self.sphere.screen_needs_update = True
                # Reset the update timer to force immediate update
                self.sphere.screen_last_update = 0.0
                print(f"DEBUG: Forced immediate ray tracing screen update due to vector change")
        
        elif self.selected_object == "cube":
            # Rotate the red cube
            self.object_rotations["cube"][1] += dx * 0.5  # Y rotation
            self.object_rotations["cube"][0] += dy * 0.5  # X rotation
        
        elif self.selected_object == "screen":
            # Rotate the 2D screen
            self.object_rotations["screen"][1] += dx * 0.5  # Y rotation
            self.object_rotations["screen"][0] += dy * 0.5  # X rotation
        
        # Handle dynamic objects
        elif self.selected_object.startswith("shape_"):
            # Rotate the selected shape
            shape_id = self.selected_object[6:]
            shape = self.sphere.get_shape(shape_id)
            if shape:
                shape.rotation[1] += dx * 0.5  # Y rotation
                shape.rotation[0] += dy * 0.5  # X rotation
                print(f"DEBUG: Rotated shape {shape.name} to {shape.rotation}")
                
        elif self.selected_object.startswith("camera_"):
            # Rotate the selected camera (adjust target)
            camera_id = self.selected_object[7:]
            camera = self.sphere.get_camera(camera_id)
            if camera:
                # Calculate rotation around camera position
                sensitivity = 0.01
                
                # Get direction from camera to target
                direction = camera.target - camera.position
                distance = np.linalg.norm(direction)
                
                if distance > 0:
                    # Convert to spherical coordinates
                    direction_norm = direction / distance
                    x, y, z = direction_norm
                    theta = math.atan2(y, x)  # azimuth
                    phi = math.acos(z) if abs(z) <= 1.0 else 0  # polar angle
                    
                    # Apply mouse deltas
                    theta += dx * sensitivity
                    phi += dy * sensitivity
                    
                    # Clamp phi to avoid gimbal lock
                    phi = max(0.01, min(math.pi - 0.01, phi))
                    
                    # Convert back to Cartesian and update target
                    new_direction = np.array([
                        math.sin(phi) * math.cos(theta),
                        math.sin(phi) * math.sin(theta),
                        math.cos(phi)
                    ])
                    camera.target = camera.position + new_direction * distance
                    print(f"DEBUG: Rotated camera {camera.name} target to {camera.target}")
                
        elif self.selected_object.startswith("screen_"):
            # Rotate the selected screen
            screen_id = self.selected_object[7:]
            screen = self.sphere.get_screen(screen_id)
            if screen and screen.type == ScreenType.SCREEN_2D:
                screen.rotation[1] += dx * 0.5  # Y rotation
                screen.rotation[0] += dy * 0.5  # X rotation
                print(f"DEBUG: Rotated screen {screen.name} to {screen.rotation}")
        
        # If no object selected, default to camera movement
        elif self.selected_object == "none":
            self.camera_rotation_y += dx * 0.5
            self.camera_rotation_x += dy * 0.5
            self.camera_rotation_x = max(-90, min(90, self.camera_rotation_x))
            # Note: Camera movement doesn't affect the red vector direction
            
            # Update main cameras to mirror canvas camera system
            self.sphere.update_main_cameras(self)
    
        self.last_mouse_pos = current_pos
        self.Refresh()
    
    def on_mouse_wheel(self, event):
        """Handle mouse wheel for zooming or scaling selected objects."""
        delta = event.GetWheelRotation()
        zoom_factor = 1.1 if delta > 0 else 0.9
        scale_factor = 1.1 if delta > 0 else 0.9
        
        # Determine what to affect based on selected object
        if self.selected_object == "none" or self.selected_object == "sphere":
            # No object selected or sphere selected, zoom camera
            self.camera_distance *= zoom_factor
            self.camera_distance = max(1.0, min(20.0, self.camera_distance))
            # Update main cameras to mirror canvas camera system
            self.sphere.update_main_cameras(self)
            
        elif self.selected_object == "cube":
            # Scale the red cube
            self.rainbow_cube_size *= scale_factor
            self.rainbow_cube_size = max(0.1, min(2.0, self.rainbow_cube_size))
            print(f"DEBUG: Scaled cube to size {self.rainbow_cube_size}")
            
        elif self.selected_object == "screen":
            # Scale the 2D screen
            self.screen_width *= scale_factor
            self.screen_height *= scale_factor
            self.screen_width = max(0.5, min(10.0, self.screen_width))
            self.screen_height = max(0.5, min(10.0, self.screen_height))
            print(f"DEBUG: Scaled screen to {self.screen_width} x {self.screen_height}")
            
        elif self.selected_object.startswith("shape_"):
            # Scale the selected shape
            shape_id = self.selected_object[6:]
            shape = self.sphere.get_shape(shape_id)
            if shape:
                shape.scale *= scale_factor
                # Clamp scale values
                shape.scale = np.clip(shape.scale, 0.1, 5.0)
                print(f"DEBUG: Scaled shape {shape.name} to {shape.scale}")
                
        elif self.selected_object.startswith("camera_"):
            # Adjust camera FOV
            camera_id = self.selected_object[7:]
            camera = self.sphere.get_camera(camera_id)
            if camera:
                camera.fov *= zoom_factor
                camera.fov = max(10.0, min(120.0, camera.fov))
                print(f"DEBUG: Adjusted camera {camera.name} FOV to {camera.fov}")
                
        elif self.selected_object.startswith("screen_"):
            # Scale the selected screen
            screen_id = self.selected_object[7:]
            screen = self.sphere.get_screen(screen_id)
            if screen:
                if screen.type == ScreenType.SCREEN_2D:
                    screen.size *= scale_factor
                    screen.size = np.clip(screen.size, 0.5, 10.0)
                    print(f"DEBUG: Scaled 2D screen {screen.name} to {screen.size}")
                else:  # Overlay screen
                    screen.overlay_size *= scale_factor
                    screen.overlay_size = np.clip(screen.overlay_size, 0.1, 1.0)
                    print(f"DEBUG: Scaled overlay screen {screen.name} to {screen.overlay_size}")
        else:
            # Default to camera zoom
            self.camera_distance *= zoom_factor
            self.camera_distance = max(1.0, min(20.0, self.camera_distance))
        
        self.Refresh()
    
    def on_key_down(self, event):
        """Handle keyboard input for 3D navigation."""
        key_code = event.GetKeyCode()
        
        # Get current camera direction vectors
        # Convert rotation to radians
        rot_x_rad = math.radians(self.camera_rotation_x)
        rot_y_rad = math.radians(self.camera_rotation_y)
        
        # Calculate camera's forward, right, and up vectors
        forward = np.array([
            math.sin(rot_y_rad) * math.cos(rot_x_rad),
            -math.sin(rot_x_rad),
            -math.cos(rot_y_rad) * math.cos(rot_x_rad)
        ])
        
        right = np.array([
            math.cos(rot_y_rad),
            0.0,
            math.sin(rot_y_rad)
        ])
        
        up = np.array([0.0, 1.0, 0.0])
        
        # Handle different keys
        moved = False
        
        # Determine what to move based on selected object
        if self.selected_object == "none":
            # No object selected, move camera
            target_type = "camera"
        elif self.selected_object in ["sphere", "cube", "screen"]:
            # Traditional objects
            target_type = "traditional"
        elif self.selected_object.startswith(("shape_", "camera_", "screen_")):
            # New dynamic objects
            target_type = "dynamic"
        else:
            target_type = "camera"  # Default fallback
        
        if key_code == wx.WXK_LEFT:
            if target_type == "camera":
                # Move camera left
                self.camera_position -= right * self.movement_speed
                # Update clean main camera to mirror main camera
                self.sphere.update_main_clean_camera(self)
            else:
                # Move selected object left
                self._move_selected_object(-right * self.movement_speed)
            moved = True
            
        elif key_code == wx.WXK_RIGHT:
            if target_type == "camera":
                # Move camera right
                self.camera_position += right * self.movement_speed
                # Update clean main camera to mirror main camera
                self.sphere.update_main_clean_camera(self)
            else:
                # Move selected object right
                self._move_selected_object(right * self.movement_speed)
            moved = True
            
        elif key_code == wx.WXK_UP:
            if target_type == "camera":
                # Move camera up
                self.camera_position += up * self.movement_speed
                # Update clean main camera to mirror main camera
                self.sphere.update_main_clean_camera(self)
            else:
                # Move selected object up
                self._move_selected_object(up * self.movement_speed)
            moved = True
            
        elif key_code == wx.WXK_DOWN:
            if target_type == "camera":
                # Move camera down
                self.camera_position -= up * self.movement_speed
                # Update clean main camera to mirror main camera
                self.sphere.update_main_clean_camera(self)
            else:
                # Move selected object down
                self._move_selected_object(-up * self.movement_speed)
            moved = True
            
        elif key_code == ord('I') or key_code == ord('i'):
            if target_type == "camera":
                # Move camera forward (into the screen)
                self.camera_position += forward * self.movement_speed
                # Update clean main camera to mirror main camera
                self.sphere.update_main_clean_camera(self)
            else:
                # Move selected object forward
                self._move_selected_object(forward * self.movement_speed)
            moved = True
            
        elif key_code == ord('O') or key_code == ord('o'):
            if target_type == "camera":
                # Move camera backward (out of the screen)
                self.camera_position -= forward * self.movement_speed
                # Update clean main camera to mirror main camera
                self.sphere.update_main_clean_camera(self)
            else:
                # Move selected object backward
                self._move_selected_object(-forward * self.movement_speed)
            moved = True
        
        # Additional zoom controls with I/O keys (alternative behavior)
        elif key_code == ord('I') and event.ShiftDown():
            # Shift+I: Zoom in
            self.camera_distance *= 0.9
            self.camera_distance = max(1.0, self.camera_distance)
            moved = True
            
        elif key_code == ord('O') and event.ShiftDown():
            # Shift+O: Zoom out
            self.camera_distance *= 1.1
            self.camera_distance = min(20.0, self.camera_distance)
            moved = True
        
        # Video playback controls
        elif key_code == wx.WXK_SPACE:
            # Space: Play/Pause video screens
            self._toggle_video_playback()
        elif key_code == ord('R'):
            # R: Restart video screens
            self._restart_video_playback()
        elif key_code == ord('S'):
            # S: Stop video screens
            self._stop_video_playback()
        
        # Video speed controls
        elif key_code == ord('1'):
            # 1: 0.5x speed
            self._set_video_speed(0.5)
        elif key_code == ord('2'):
            # 2: Normal speed (1.0x)
            self._set_video_speed(1.0)
        elif key_code == ord('3'):
            # 3: 1.5x speed
            self._set_video_speed(1.5)
        elif key_code == ord('4'):
            # 4: 2.0x speed
            self._set_video_speed(2.0)
        elif key_code == wx.WXK_UP:
            # Up arrow: Increase speed
            self._adjust_video_speed(0.25)
        elif key_code == wx.WXK_DOWN:
            # Down arrow: Decrease speed
            self._adjust_video_speed(-0.25)
        elif key_code == ord('F'):
            # F: Cycle through common frame rates
            self._cycle_frame_rate()
        elif key_code == ord('R'):
            # R: Reset to original frame rate
            self._reset_frame_rate()
        
        # Refresh display if camera moved
        if moved:
            self.Refresh()
            
        event.Skip()
    
    def _toggle_video_playback(self):
        """Toggle play/pause for all video screens."""
        for screen in self.sphere.get_all_screens():
            if isinstance(screen, MediaScreen) and screen.media_type == MediaType.VIDEO:
                screen.pause_video_playback()
                print(f"DEBUG: Toggled playback for {screen.name}")
    
    def _restart_video_playback(self):
        """Restart all video screens from the beginning."""
        for screen in self.sphere.get_all_screens():
            if isinstance(screen, MediaScreen) and screen.media_type == MediaType.VIDEO:
                screen.restart_video_playback()
                print(f"DEBUG: Restarted {screen.name}")
    
    def _stop_video_playback(self):
        """Stop all video screens."""
        for screen in self.sphere.get_all_screens():
            if isinstance(screen, MediaScreen) and screen.media_type == MediaType.VIDEO:
                screen.stop_video_playback()
                print(f"DEBUG: Stopped {screen.name}")
    
    def _set_video_speed(self, speed: float):
        """Set playback speed for all video screens."""
        video_screens = []
        for screen in self.sphere.get_all_screens():
            if isinstance(screen, MediaScreen) and screen.media_type == MediaType.VIDEO:
                screen.set_playback_speed(speed)
                video_screens.append(screen.name)
        
        if video_screens:
            print(f"DEBUG: Set playback speed to {speed:.1f}x for {len(video_screens)} video(s)")
            # Show speed change notification
            wx.CallAfter(self._show_speed_notification, speed)
        else:
            print(f"DEBUG: No video screens to adjust speed")
    
    def _adjust_video_speed(self, speed_delta: float):
        """Adjust playback speed by delta for all video screens."""
        # Get current speed from first video screen
        current_speed = 1.0
        for screen in self.sphere.get_all_screens():
            if isinstance(screen, MediaScreen) and screen.media_type == MediaType.VIDEO:
                current_speed = screen.playback_speed
                break
        
        # Calculate new speed
        new_speed = max(0.25, min(4.0, current_speed + speed_delta))  # Clamp between 0.25x and 4.0x
        
        if new_speed != current_speed:
            self._set_video_speed(new_speed)
    
    def _show_speed_notification(self, speed: float):
        """Show a brief notification about speed change."""
        if hasattr(self, 'speed_notification_timer'):
            self.speed_notification_timer.Stop()
        
        # Create or update speed display
        if not hasattr(self, 'speed_display'):
            self.speed_display = wx.StaticText(self, label="", style=wx.ALIGN_CENTER)
            self.speed_display.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            self.speed_display.SetForegroundColour(wx.Colour(255, 255, 0))  # Yellow text
            self.speed_display.SetBackgroundColour(wx.Colour(0, 0, 0, 128))  # Semi-transparent black
        
        # Update text and show
        self.speed_display.SetLabel(f"Speed: {speed:.1f}x")
        self.speed_display.Show()
        
        # Position in top-right corner
        size = self.GetSize()
        text_size = self.speed_display.GetSize()
        self.speed_display.SetPosition((size.width - text_size.width - 20, 20))
        
        # Hide after 2 seconds
        self.speed_notification_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, lambda evt: self.speed_display.Hide(), self.speed_notification_timer)
        self.speed_notification_timer.Start(2000, oneShot=True)
    
    def _cycle_frame_rate(self):
        """Cycle through common frame rates for all video screens."""
        # Common frame rates to cycle through
        common_fps = [15, 24, 30, 60, None]  # None = original video FPS
        
        # Get current frame rate from first video screen
        current_fps = None
        for screen in self.sphere.get_all_screens():
            if isinstance(screen, MediaScreen) and screen.media_type == MediaType.VIDEO:
                current_fps = screen.target_frame_rate
                break
        
        # Find next frame rate in cycle
        try:
            current_index = common_fps.index(current_fps)
            next_index = (current_index + 1) % len(common_fps)
        except ValueError:
            # Current FPS not in common list, start from beginning
            next_index = 0
        
        next_fps = common_fps[next_index]
        self._set_frame_rate(next_fps)
    
    def _set_frame_rate(self, fps: float):
        """Set frame rate for all video screens."""
        video_screens = []
        for screen in self.sphere.get_all_screens():
            if isinstance(screen, MediaScreen) and screen.media_type == MediaType.VIDEO:
                screen.set_frame_rate(fps)
                video_screens.append(screen.name)
        
        if video_screens:
            fps_text = f"{fps} FPS" if fps else "Original FPS"
            print(f"DEBUG: Set frame rate to {fps_text} for {len(video_screens)} video(s)")
            # Show frame rate change notification
            wx.CallAfter(self._show_frame_rate_notification, fps)
        else:
            print(f"DEBUG: No video screens to adjust frame rate")
    
    def _reset_frame_rate(self):
        """Reset frame rate to original for all video screens."""
        self._set_frame_rate(None)
    
    def _show_frame_rate_notification(self, fps: float):
        """Show a brief notification about frame rate change."""
        if hasattr(self, 'fps_notification_timer'):
            self.fps_notification_timer.Stop()
        
        # Create or update FPS display
        if not hasattr(self, 'fps_display'):
            self.fps_display = wx.StaticText(self, label="", style=wx.ALIGN_CENTER)
            self.fps_display.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            self.fps_display.SetForegroundColour(wx.Colour(0, 255, 255))  # Cyan text
            self.fps_display.SetBackgroundColour(wx.Colour(0, 0, 0, 128))  # Semi-transparent black
        
        # Update text and show
        fps_text = f"{fps} FPS" if fps else "Original FPS"
        self.fps_display.SetLabel(f"Frame Rate: {fps_text}")
        self.fps_display.Show()
        
        # Position in top-left corner
        self.fps_display.SetPosition((20, 20))
        
        # Hide after 2 seconds
        self.fps_notification_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, lambda evt: self.fps_display.Hide(), self.fps_notification_timer)
        self.fps_notification_timer.Start(2000, oneShot=True)

    def _move_selected_object(self, movement_vector):
        """Move the currently selected object by the given movement vector."""
        if self.selected_object == "none":
            return
            
        # Handle traditional objects
        if self.selected_object == "cube":
            self.rainbow_cube_position += movement_vector
            print(f"DEBUG: Moved cube to {self.rainbow_cube_position}")
            
        elif self.selected_object == "screen":
            self.screen_position += movement_vector
            print(f"DEBUG: Moved screen to {self.screen_position}")
            
        elif self.selected_object == "sphere":
            self.camera_position += movement_vector
            print(f"DEBUG: Moved sphere camera to {self.camera_position}")
            
        # Handle dynamic objects
        elif self.selected_object.startswith("shape_"):
            shape_id = self.selected_object[6:]  # Remove "shape_" prefix
            shape = self.sphere.get_shape(shape_id)
            if shape:
                shape.position += movement_vector
                print(f"DEBUG: Moved shape {shape.name} to {shape.position}")
                
        elif self.selected_object.startswith("camera_"):
            camera_id = self.selected_object[7:]  # Remove "camera_" prefix
            camera = self.sphere.get_camera(camera_id)
            if camera:
                camera.position += movement_vector
                print(f"DEBUG: Moved camera {camera.name} to {camera.position}")
                
        elif self.selected_object.startswith("screen_"):
            screen_id = self.selected_object[7:]  # Remove "screen_" prefix
            screen = self.sphere.get_screen(screen_id)
            if screen:
                if screen.type == ScreenType.SCREEN_2D:
                    screen.position += movement_vector
                    print(f"DEBUG: Moved 2D screen {screen.name} to {screen.position}")
                else:  # Overlay screen
                    # For overlay screens, we might want to move them in screen space
                    # Convert 3D movement to 2D overlay movement (simplified)
                    screen.overlay_position[0] += movement_vector[0] * 0.1  # Scale down for overlay
                    screen.overlay_position[1] += movement_vector[1] * 0.1
                    print(f"DEBUG: Moved overlay screen {screen.name} to {screen.overlay_position}")
    
    def get_sphere_renderer(self) -> SphereRenderer:
        """Get the sphere renderer for external control."""
        return self.sphere
    
    def save_canvas_scene_to_dict(self) -> dict:
        """Save canvas-specific properties to a dictionary."""
        canvas_data = {
            "camera": {
                "distance": float(self.camera_distance),
                "rotation_x": float(self.camera_rotation_x),
                "rotation_y": float(self.camera_rotation_y),
                "position": self.camera_position.tolist(),
                "projection": str(self.camera_projection)
            },
            "screen": {
                "enabled": bool(self.screen_enabled),
                "render_mode": str(self.screen_render_mode),
                "projection": str(self.screen_projection),
                "position": self.screen_position.tolist(),
                "width": float(self.screen_width),
                "height": float(self.screen_height),
                "framebuffer_width": int(self.framebuffer_width),
                "framebuffer_height": int(self.framebuffer_height)
            },
            "cube": {
                "position": self.rainbow_cube_position.tolist(),
                "size": float(self.rainbow_cube_size)
            },
            "view_vector": self.view_vector.tolist(),
            "object_rotations": {k: v.tolist() for k, v in self.object_rotations.items()}
        }
        return canvas_data
    
    def load_canvas_scene_from_dict(self, canvas_data: dict):
        """Load canvas-specific properties from a dictionary."""
        try:
            # Camera properties
            if "camera" in canvas_data:
                c = canvas_data["camera"]
                self.camera_distance = c.get("distance", 5.0)
                self.camera_rotation_x = c.get("rotation_x", 0.0)
                self.camera_rotation_y = c.get("rotation_y", 0.0)
                self.camera_position = np.array(c.get("position", [0.0, 
0.0, 0.0]))
                self.camera_projection = c.get("projection", 
"perspective")
            
            # Screen properties
            if "screen" in canvas_data:
                s = canvas_data["screen"]
                self.screen_enabled = s.get("enabled", True)
                self.screen_render_mode = s.get("render_mode", "simple")
                self.screen_projection = s.get("projection", 
"perspective")
                self.screen_position = np.array(s.get("position", [0.0, 
0.0, -3.0]))
                self.screen_width = s.get("width", 2.0)
                self.screen_height = s.get("height", 1.5)
                self.framebuffer_width = s.get("framebuffer_width", 256)
                self.framebuffer_height = s.get("framebuffer_height", 192)
            
            # Cube properties
            if "cube" in canvas_data:
                cb = canvas_data["cube"]
                self.rainbow_cube_position = np.array(cb.get("position", [2.0, 
0.0, 2.0]))
                self.rainbow_cube_size = cb.get("size", 0.3)
            
            # View vector
            if "view_vector" in canvas_data:
                self.view_vector = np.array(canvas_data["view_vector"])
            
            # Object rotations
            if "object_rotations" in canvas_data:
                for k, v in canvas_data["object_rotations"].items():
                    self.object_rotations[k] = np.array(v)
            
            print("Canvas scene loaded successfully")
            
        except Exception as e:
            print(f"Error loading canvas scene: {e}")
            raise

class Sphere3DFrame(wx.Frame):
    """Main frame for 3D sphere visualization with menu controls."""
    
    def __init__(self):
        print("DEBUG: Sphere3DFrame.__init__() called")
        super().__init__(None, title="3D Sphere Visualization", size=(1000, 800))
        
        # Initialize scene file tracking
        self._current_scene_file = None
        print("DEBUG: Frame created with title and size")
        
        # Create the OpenGL canvas
        print("DEBUG: Creating OpenGL canvas")
        self.canvas = Sphere3DCanvas(self)
        self.sphere = self.canvas.get_sphere_renderer()
        print("DEBUG: Canvas and sphere renderer created")
        
        # Create menu bar
        print("DEBUG: Creating menu bar")
        self.create_menu_bar()
        print("DEBUG: Menu bar created")
        
        # Set up layout
        print("DEBUG: Setting up layout")
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.EXPAND)
        self.SetSizer(sizer)
        
        # Center the frame
        self.Center()
        print("DEBUG: Frame initialization completed")
    
    def create_menu_bar(self):
        """Create the menu bar with all sphere controls."""
        menubar = wx.MenuBar()
        
        # File menu
        file_menu = wx.Menu()
        file_menu.Append(wx.ID_NEW, "&New Scene\tCtrl+N", "Create a new scene")
        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_OPEN, "&Open Scene...\tCtrl+O", "Open a saved scene")
        file_menu.Append(wx.ID_SAVE, "&Save Scene\tCtrl+S", "Save the current scene")
        file_menu.Append(wx.ID_SAVEAS, "Save Scene &As...\tCtrl+Shift+S", 
"Save scene with a new name")
        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_EXIT, "E&xit\tCtrl+Q", "Exit the application")
        
        menubar.Append(file_menu, "&File")
        
        # Sphere menu
        sphere_menu = wx.Menu()
        
        # Color submenu
        color_menu = wx.Menu()
        color_menu.Append(wx.ID_ANY, "Set Sphere Color...", "Change sphere color")
        color_menu.Append(wx.ID_ANY, "Set Transparency...", "Change sphere transparency")
        sphere_menu.AppendSubMenu(color_menu, "Appearance")
        
        # Transform submenu
        transform_menu = wx.Menu()
        transform_menu.Append(wx.ID_ANY, "Reset Position", "Reset sphere to origin")
        transform_menu.Append(wx.ID_ANY, "Reset Rotation", "Reset sphere rotation")
        transform_menu.Append(wx.ID_ANY, "Reset Scale", "Reset sphere scale")
        transform_menu.AppendSeparator()
        transform_menu.Append(wx.ID_ANY, "Set Position...", "Set sphere position")
        transform_menu.Append(wx.ID_ANY, "Set Rotation...", "Set sphere rotation")
        transform_menu.Append(wx.ID_ANY, "Set Scale...", "Set sphere scale")
        sphere_menu.AppendSubMenu(transform_menu, "Transform")
        
        menubar.Append(sphere_menu, "Sphere")
        
        # Grid menu
        grid_menu = wx.Menu()
        
        # Grid types
        grid_menu.AppendCheckItem(wx.ID_ANY, "Longitude/Latitude Grid", 
"Toggle longitude/latitude grid")
        grid_menu.AppendCheckItem(wx.ID_ANY, "Concentric Circles", "Toggle concentric circles")
        grid_menu.AppendCheckItem(wx.ID_ANY, "Dot Particles", "Toggle dot particles")
        grid_menu.AppendCheckItem(wx.ID_ANY, "Neon Lines", "Toggle neon-style grid lines")
        grid_menu.AppendCheckItem(wx.ID_ANY, "Wireframe", "Toggle wireframe mode")
        
        grid_menu.AppendSeparator()
        
        # Grid colors submenu
        grid_colors_menu = wx.Menu()
        grid_colors_menu.Append(wx.ID_ANY, "Longitude/Latitude Color...", 
"Set longitude/latitude grid color")
        grid_colors_menu.Append(wx.ID_ANY, "Concentric Circles Color...", 
"Set concentric circles color")
        grid_colors_menu.Append(wx.ID_ANY, "Dot Particles Color...", "Set dot particles color")
        grid_colors_menu.Append(wx.ID_ANY, "Neon Lines Color...", "Set neon lines color")
        grid_colors_menu.Append(wx.ID_ANY, "Wireframe Color...", "Set wireframe color")
        grid_menu.AppendSubMenu(grid_colors_menu, "Grid Colors")
        
        # Grid parameters submenu
        grid_params_menu = wx.Menu()
        grid_params_menu.Append(wx.ID_ANY, "Set Longitude Lines...", "Set number of longitude lines")
        grid_params_menu.Append(wx.ID_ANY, "Set Latitude Lines...", "Set number of latitude lines")
        grid_params_menu.Append(wx.ID_ANY, "Set Concentric Rings...", "Set number of concentric rings")
        grid_params_menu.Append(wx.ID_ANY, "Set Dot Density...", "Set dot particle density")
        grid_params_menu.Append(wx.ID_ANY, "Set Neon Intensity...", "Set neon glow intensity")
        grid_params_menu.Append(wx.ID_ANY, "Set Wireframe Density...", 
"Set wireframe mesh density")
        grid_menu.AppendSubMenu(grid_params_menu, "Grid Parameters")
        
        menubar.Append(grid_menu, "Grids")
        
        # Vector menu
        vector_menu = wx.Menu()
        vector_menu.AppendCheckItem(wx.ID_ANY, "Show Vector", "Toggle vector visibility")
        vector_menu.AppendCheckItem(wx.ID_ANY, "Show Vector Orientation", 
"Toggle vector orientation indicator")
        vector_menu.AppendSeparator()
        vector_menu.AppendCheckItem(wx.ID_ANY, "Show Cone", "Toggle cone visibility")
        vector_menu.AppendCheckItem(wx.ID_ANY, "Show Pyramid", "Toggle pyramid visibility")
        vector_menu.AppendCheckItem(wx.ID_ANY, "Show Cuboid", "Toggle cuboid visibility")
        vector_menu.AppendSeparator()
        
        # Vector properties submenu
        vector_props_menu = wx.Menu()
        vector_props_menu.Append(wx.ID_ANY, "Set Direction...", "Set vector direction (x,y,z)")
        vector_props_menu.Append(wx.ID_ANY, "Set Length...", "Set vector length")
        vector_props_menu.Append(wx.ID_ANY, "Set Color...", "Set vector color")
        vector_props_menu.Append(wx.ID_ANY, "Set Thickness...", "Set vector line thickness")
        vector_menu.AppendSubMenu(vector_props_menu, "Vector Properties")
        
        # Vector orientation submenu
        vector_orientation_menu = wx.Menu()
        vector_orientation_menu.Append(wx.ID_ANY, "Set Roll Angle...", 
"Set vector roll orientation angle")
        vector_orientation_menu.AppendSeparator()
        vector_orientation_menu.Append(wx.ID_ANY, "Roll +15°", "Rotate camera +15° around vector axis")
        vector_orientation_menu.Append(wx.ID_ANY, "Roll -15°", "Rotate camera -15° around vector axis")
        vector_orientation_menu.Append(wx.ID_ANY, "Roll +45°", "Rotate camera +45° around vector axis")
        vector_orientation_menu.Append(wx.ID_ANY, "Roll -45°", "Rotate camera -45° around vector axis")
        vector_orientation_menu.Append(wx.ID_ANY, "Roll +90°", "Rotate camera +90° around vector axis")
        vector_orientation_menu.Append(wx.ID_ANY, "Roll -90°", "Rotate camera -90° around vector axis")
        vector_orientation_menu.AppendSeparator()
        vector_orientation_menu.Append(wx.ID_ANY, "Roll 180°", "Rotate camera 180° around vector axis")
        vector_orientation_menu.Append(wx.ID_ANY, "Reset Roll", "Reset roll angle to 0°")
        vector_menu.AppendSubMenu(vector_orientation_menu, "Vector Orientation")
        
        # Cone properties submenu
        cone_props_menu = wx.Menu()
        cone_props_menu.Append(wx.ID_ANY, "Set Cone Length...", "Set cone length")
        cone_props_menu.Append(wx.ID_ANY, "Set Cone Angle...", "Set cone half-angle in degrees")
        cone_props_menu.Append(wx.ID_ANY, "Set Cone Color...", "Set cone color")
        cone_props_menu.Append(wx.ID_ANY, "Set Cone Transparency...", "Set cone transparency")
        cone_props_menu.Append(wx.ID_ANY, "Set Cone Resolution...", "Set cone smoothness")
        cone_props_menu.AppendSeparator()
        cone_props_menu.AppendCheckItem(wx.ID_ANY, "Infinite Cone Length", 
"Make cone extend infinitely")
        vector_menu.AppendSubMenu(cone_props_menu, "Cone Properties")
        
        # Pyramid properties submenu
        pyramid_props_menu = wx.Menu()
        pyramid_props_menu.Append(wx.ID_ANY, "Set Pyramid Length...", "Set pyramid length")
        pyramid_props_menu.Append(wx.ID_ANY, "Set Horizontal Angle...", 
"Set pyramid horizontal half-angle")
        pyramid_props_menu.Append(wx.ID_ANY, "Set Vertical Angle...", "Set pyramid vertical half-angle")
        pyramid_props_menu.Append(wx.ID_ANY, "Set Pyramid Color...", "Set pyramid color")
        pyramid_props_menu.Append(wx.ID_ANY, "Set Pyramid Transparency...", "Set pyramid transparency")
        pyramid_props_menu.AppendSeparator()
        pyramid_props_menu.AppendCheckItem(wx.ID_ANY, "Infinite Pyramid Length", "Make pyramid extend infinitely")
        vector_menu.AppendSubMenu(pyramid_props_menu, "Pyramid Properties")
        
        # Cuboid properties submenu
        cuboid_props_menu = wx.Menu()
        cuboid_props_menu.Append(wx.ID_ANY, "Set Cuboid Length...", "Set cuboid length along vector")
        cuboid_props_menu.Append(wx.ID_ANY, "Set Cuboid Width...", "Set cuboid width perpendicular to vector")
        cuboid_props_menu.Append(wx.ID_ANY, "Set Cuboid Height...", "Set cuboid height perpendicular to vector")
        cuboid_props_menu.Append(wx.ID_ANY, "Set Cuboid Color...", "Set cuboid color")
        cuboid_props_menu.Append(wx.ID_ANY, "Set Cuboid Transparency...", 
"Set cuboid transparency")
        cuboid_props_menu.AppendSeparator()
        cuboid_props_menu.AppendCheckItem(wx.ID_ANY, "Infinite Cuboid Length", "Make cuboid extend infinitely")
        vector_menu.AppendSubMenu(cuboid_props_menu, "Cuboid Properties")
        
        # Near plane submenu
        near_plane_menu = wx.Menu()
        near_plane_menu.AppendCheckItem(wx.ID_ANY, "Enable Near Plane", 
"Toggle near plane cutting of shapes")
        near_plane_menu.Append(wx.ID_ANY, "Set Near Plane Distance...", 
"Set distance of cutting plane from sphere center")
        vector_menu.AppendSubMenu(near_plane_menu, "Near Plane (Truncate Shapes)")
        
        # Sphere intersection submenu
        sphere_intersection_menu = wx.Menu()
        sphere_intersection_menu.AppendCheckItem(wx.ID_ANY, "Show Sphere Intersections", "Show where shapes intersect sphere surface")
        sphere_intersection_menu.Append(wx.ID_ANY, "Set Intersection Color...", "Set color of sphere intersection areas")
        vector_menu.AppendSubMenu(sphere_intersection_menu, "Sphere Intersections")
        
        # Preset directions submenu
        vector_presets_menu = wx.Menu()
        vector_presets_menu.Append(wx.ID_ANY, "X-Axis (1,0,0)", "Set vector to positive X direction")
        vector_presets_menu.Append(wx.ID_ANY, "Y-Axis (0,1,0)", "Set vector to positive Y direction")
        vector_presets_menu.Append(wx.ID_ANY, "Z-Axis (0,0,1)", "Set vector to positive Z direction")
        vector_presets_menu.Append(wx.ID_ANY, "-X-Axis (-1,0,0)", "Set vector to negative X direction")
        vector_presets_menu.Append(wx.ID_ANY, "-Y-Axis (0,-1,0)", "Set vector to negative Y direction")
        vector_presets_menu.Append(wx.ID_ANY, "-Z-Axis (0,0,-1)", "Set vector to negative Z direction")
        vector_presets_menu.AppendSeparator()
        vector_presets_menu.Append(wx.ID_ANY, "Diagonal (1,1,1)", "Set vector to diagonal direction")
        vector_presets_menu.Append(wx.ID_ANY, "Random Direction", "Set vector to random direction")
        vector_menu.AppendSubMenu(vector_presets_menu, "Preset Directions")
        
        menubar.Append(vector_menu, "Vector")
        
        # View menu
        view_menu = wx.Menu()
        view_menu.Append(wx.ID_ANY, "Reset Camera", "Reset camera to default position")
        view_menu.AppendSeparator()
        
        # Camera movement submenu
        camera_movement_menu = wx.Menu()
        camera_movement_menu.Append(wx.ID_ANY, "Set Camera Position...", 
"Set camera position (x,y,z)")
        camera_movement_menu.Append(wx.ID_ANY, "Set Camera Distance...", 
"Set camera distance from origin")
        camera_movement_menu.AppendSeparator()
        camera_movement_menu.Append(wx.ID_ANY, "Move Forward", "Move camera forward")
        camera_movement_menu.Append(wx.ID_ANY, "Move Backward", "Move camera backward")
        camera_movement_menu.Append(wx.ID_ANY, "Move Left", "Move camera left")
        camera_movement_menu.Append(wx.ID_ANY, "Move Right", "Move camera right")
        camera_movement_menu.Append(wx.ID_ANY, "Move Up", "Move camera up")
        camera_movement_menu.Append(wx.ID_ANY, "Move Down", "Move camera down")
        camera_movement_menu.AppendSeparator()
        camera_movement_menu.Append(wx.ID_ANY, "Increase Movement Speed", 
"Make camera move faster")
        camera_movement_menu.Append(wx.ID_ANY, "Decrease Movement Speed", 
"Make camera move slower")
        view_menu.AppendSubMenu(camera_movement_menu, "Camera Movement")
        
        # Sphere movement submenu (sphere + vector + shapes only)
        sphere_movement_menu = wx.Menu()
        sphere_movement_menu.Append(wx.ID_ANY, "Set Sphere Position...", 
"Set sphere position (affects sphere + vector + shapes only)")
        sphere_movement_menu.AppendSeparator()
        sphere_movement_menu.Append(wx.ID_ANY, "Move Sphere Forward", 
"Move sphere forward (cube and screen stay in place)")
        sphere_movement_menu.Append(wx.ID_ANY, "Move Sphere Backward", 
"Move sphere backward")
        sphere_movement_menu.Append(wx.ID_ANY, "Move Sphere Left", "Move sphere left")
        sphere_movement_menu.Append(wx.ID_ANY, "Move Sphere Right", "Move sphere right")
        sphere_movement_menu.Append(wx.ID_ANY, "Move Sphere Up", "Move sphere up")
        sphere_movement_menu.Append(wx.ID_ANY, "Move Sphere Down", "Move sphere down")
        sphere_movement_menu.AppendSeparator()
        sphere_movement_menu.Append(wx.ID_ANY, "Center Sphere", "Move sphere back to origin (0,0,0)")
        view_menu.AppendSubMenu(sphere_movement_menu, "Sphere Movement")
        
        view_menu.AppendSeparator()
        view_menu.Append(wx.ID_ANY, "Center Camera on Cube", "Move camera to look at the multicolored cube")
        view_menu.AppendSeparator()
        view_menu.AppendCheckItem(wx.ID_ANY, "Wireframe Mode", "Toggle wireframe rendering mode")
        view_menu.AppendCheckItem(wx.ID_ANY, "Enable Lighting", "Toggle lighting on/off")
        view_menu.AppendSeparator()
        view_menu.AppendCheckItem(wx.ID_ANY, "Show Normal Rays", "Show surface normal vectors")
        
        # Normal rays submenu
        normal_rays_menu = wx.Menu()
        normal_rays_menu.Append(wx.ID_ANY, "Set Ray Length...", "Set length of normal rays")
        normal_rays_menu.Append(wx.ID_ANY, "Set Ray Density...", "Set density of normal rays")
        normal_rays_menu.Append(wx.ID_ANY, "Set Ray Color...", "Set color of normal rays")
        normal_rays_menu.Append(wx.ID_ANY, "Set Ray Thickness...", "Set thickness of normal rays")
        view_menu.AppendSubMenu(normal_rays_menu, "Normal Ray Properties")
        
        view_menu.AppendSeparator()
        view_menu.AppendCheckItem(wx.ID_ANY, "Show Intersection Normals", 
"Show normal rays on intersection surfaces")
        
        # Intersection normal rays submenu
        intersection_normals_menu = wx.Menu()
        intersection_normals_menu.Append(wx.ID_ANY, "Set Intersection Ray Length...", "Set length of intersection normal rays")
        intersection_normals_menu.Append(wx.ID_ANY, "Set Intersection Ray Density...", "Set density of intersection normal rays")
        intersection_normals_menu.Append(wx.ID_ANY, "Set Intersection Ray Color...", "Set color of intersection normal rays")
        intersection_normals_menu.Append(wx.ID_ANY, "Set Intersection Ray Thickness...", "Set thickness of intersection normal rays")
        view_menu.AppendSubMenu(intersection_normals_menu, "Intersection Normal Properties")
        
        view_menu.AppendSeparator()
        view_menu.AppendCheckItem(wx.ID_ANY, "Show Truncation Normals", 
"Show normal rays on truncation surfaces")
        
        # Truncation normal rays submenu
        truncation_normals_menu = wx.Menu()
        truncation_normals_menu.Append(wx.ID_ANY, "Set Truncation Ray Length...", "Set length of truncation normal rays")
        truncation_normals_menu.Append(wx.ID_ANY, "Set Truncation Ray Density...", "Set density of truncation normal rays")
        truncation_normals_menu.Append(wx.ID_ANY, "Set Truncation Ray Color...", "Set color of truncation normal rays")
        truncation_normals_menu.Append(wx.ID_ANY, "Set Truncation Ray Thickness...", "Set thickness of truncation normal rays")
        view_menu.AppendSubMenu(truncation_normals_menu, "Truncation Normal Properties")
        
        menubar.Append(view_menu, "View")
        
        # Screen menu (Ray Tracing)
        screen_menu = wx.Menu()
        
        # Main screen toggle
        screen_menu.AppendCheckItem(wx.ID_ANY, "Show Ray Tracing Screen", 
"Show 2D screen with ray-traced image")
        screen_menu.AppendSeparator()
        
        # Screen properties
        screen_menu.Append(wx.ID_ANY, "Set Screen Position...", "Set 3D position of the screen")
        screen_menu.Append(wx.ID_ANY, "Set Screen Rotation...", "Set rotation of the screen")
        screen_menu.Append(wx.ID_ANY, "Set Screen Size...", "Set width and height of the screen")
        screen_menu.AppendSeparator()
        
        # Rendering options
        render_mode_menu = wx.Menu()
        render_mode_menu.AppendRadioItem(wx.ID_ANY, "Ray Tracing", "Basic ray tracing")
        render_mode_menu.AppendRadioItem(wx.ID_ANY, "Path Tracing", "Path tracing with reflections")
        render_mode_menu.AppendRadioItem(wx.ID_ANY, "PBR Rendering", 
"Physically Based Rendering")
        render_mode_menu.AppendRadioItem(wx.ID_ANY, "Ray Marching", "Ray marching with signed distance functions")
        screen_menu.AppendSubMenu(render_mode_menu, "Render Mode")
        
        # Projection mode options
        projection_mode_menu = wx.Menu()
        projection_mode_menu.AppendRadioItem(wx.ID_ANY, "Perspective Projection", "Standard perspective projection with depth")
        projection_mode_menu.AppendRadioItem(wx.ID_ANY, "Orthographic Projection", "Orthographic projection without perspective distortion")
        screen_menu.AppendSubMenu(projection_mode_menu, "Projection Mode")
        
        # 2D Screen projection mode options
        screen_projection_menu = wx.Menu()
        screen_projection_menu.AppendRadioItem(wx.ID_ANY, "2D Screen Perspective", "2D screen uses perspective projection")
        screen_projection_menu.AppendRadioItem(wx.ID_ANY, "2D Screen Orthographic", "2D screen uses orthographic projection")
        screen_menu.AppendSubMenu(screen_projection_menu, "2D Screen Projection")
        
        screen_menu.AppendSeparator()
        screen_menu.Append(wx.ID_ANY, "Set Screen Resolution...", "Set texture resolution")
        screen_menu.Append(wx.ID_ANY, "Set Camera Position...", "Set virtual camera position")
        screen_menu.Append(wx.ID_ANY, "Set Camera Target...", "Set virtual camera target")
        screen_menu.Append(wx.ID_ANY, "Set Update Rate...", "Set screen refresh rate")
        screen_menu.Append(wx.ID_ANY, "Set Samples...", "Set anti-aliasing samples")
        screen_menu.Append(wx.ID_ANY, "Set Max Bounces...", "Set maximum ray bounces for reflections")
        
        menubar.Append(screen_menu, "Screen")
        
        # Objects menu
        objects_menu = wx.Menu()
        
        # Object selection submenu
        selection_menu = wx.Menu()
        self.sphere_selection_item = selection_menu.AppendRadioItem(wx.ID_ANY, "Camera Sphere", "Select sphere for rotation control")
        self.cube_selection_item = selection_menu.AppendRadioItem(wx.ID_ANY, "Rainbow Cube", "Select rainbow cube for manipulation")
        self.screen_selection_item = selection_menu.AppendRadioItem(wx.ID_ANY, "2D Screen", "Select 2D screen for positioning")
        
        selection_menu.AppendSeparator()
        
        # Dynamic shape selection (populated at runtime)
        self.shapes_selection_menu = wx.Menu()
        selection_menu.AppendSubMenu(self.shapes_selection_menu, "Shapes")
        
        # Dynamic camera selection (populated at runtime)
        self.cameras_selection_menu = wx.Menu()
        selection_menu.AppendSubMenu(self.cameras_selection_menu, "Cameras")
        
        # Dynamic screen selection (populated at runtime)
        self.screens_selection_menu = wx.Menu()
        selection_menu.AppendSubMenu(self.screens_selection_menu, "Screens")
        
        selection_menu.AppendSeparator()
        self.none_selection_item = selection_menu.AppendRadioItem(wx.ID_ANY, "None", "No object selected")
        
        objects_menu.AppendSubMenu(selection_menu, "Select Object")
        
        objects_menu.AppendSeparator()
        
        # Selected object manipulation submenu
        manipulation_menu = wx.Menu()
        
        # Rotation controls
        rotation_submenu = wx.Menu()
        rotation_submenu.Append(wx.ID_ANY, "Set Selected Rotation...", 
"Set selected object rotation (pitch, yaw, roll)")
        rotation_submenu.AppendSeparator()
        rotation_submenu.Append(wx.ID_ANY, "Rotate +15° X", "Rotate selected object +15° around X axis")
        rotation_submenu.Append(wx.ID_ANY, "Rotate -15° X", "Rotate selected object -15° around X axis")
        rotation_submenu.Append(wx.ID_ANY, "Rotate +15° Y", "Rotate selected object +15° around Y axis")
        rotation_submenu.Append(wx.ID_ANY, "Rotate -15° Y", "Rotate selected object -15° around Y axis")
        rotation_submenu.Append(wx.ID_ANY, "Rotate +15° Z", "Rotate selected object +15° around Z axis")
        rotation_submenu.Append(wx.ID_ANY, "Rotate -15° Z", "Rotate selected object -15° around Z axis")
        rotation_submenu.AppendSeparator()
        rotation_submenu.Append(wx.ID_ANY, "Reset Selected Rotation", 
"Reset selected object rotation to zero")
        manipulation_menu.AppendSubMenu(rotation_submenu, "Rotate Selected Object")
        
        # Position controls
        position_submenu = wx.Menu()
        position_submenu.Append(wx.ID_ANY, "Set Selected Position...", 
"Set selected object position (x, y, z)")
        position_submenu.AppendSeparator()
        position_submenu.Append(wx.ID_ANY, "Move Selected Forward", "Move selected object forward")
        position_submenu.Append(wx.ID_ANY, "Move Selected Backward", "Move selected object backward")
        position_submenu.Append(wx.ID_ANY, "Move Selected Left", "Move selected object left")
        position_submenu.Append(wx.ID_ANY, "Move Selected Right", "Move selected object right")
        position_submenu.Append(wx.ID_ANY, "Move Selected Up", "Move selected object up")
        position_submenu.Append(wx.ID_ANY, "Move Selected Down", "Move selected object down")
        position_submenu.AppendSeparator()
        position_submenu.Append(wx.ID_ANY, "Reset Selected Position", 
"Reset selected object to default position")
        manipulation_menu.AppendSubMenu(position_submenu, "Move Selected Object")
        
        objects_menu.AppendSubMenu(manipulation_menu, "Manipulate Selected")
        
        objects_menu.AppendSeparator()
        
        # Object manipulation options
        objects_menu.Append(wx.ID_ANY, "Reset Selected Object", "Reset selected object to default position/rotation")
        objects_menu.Append(wx.ID_ANY, "Object Properties...", "Edit properties of selected object")
        
        objects_menu.AppendSeparator()
        
        # Rotation mode
        rotation_menu = wx.Menu()
        self.local_rotation_item = rotation_menu.AppendRadioItem(wx.ID_ANY, "Local Rotation", "Rotate around object's local axes")
        self.world_rotation_item = rotation_menu.AppendRadioItem(wx.ID_ANY, "World Rotation", "Rotate around world axes")
        objects_menu.AppendSubMenu(rotation_menu, "Rotation Mode")
        
        menubar.Append(objects_menu, "Objects")
        
        # Camera Angles menu (for 2D screen FOV control)
        camera_menu = wx.Menu()
        
        # Geometry angle controls that affect 2D camera FOV
        camera_menu.Append(wx.ID_ANY, "Set Cone Angle...", "Set cone angle (affects 2D camera vertical FOV)")
        camera_menu.Append(wx.ID_ANY, "Set Pyramid Horizontal Angle...", 
"Set pyramid horizontal angle (affects 2D camera horizontal FOV)")
        camera_menu.Append(wx.ID_ANY, "Set Pyramid Vertical Angle...", 
"Set pyramid vertical angle (affects 2D camera vertical FOV)")
        camera_menu.Append(wx.ID_ANY, "Set Cuboid Width...", "Set cuboid width (affects 2D camera horizontal view)")
        camera_menu.Append(wx.ID_ANY, "Set Cuboid Height...", "Set cuboid height (affects 2D camera vertical view)")
        
        camera_menu.AppendSeparator()
        
        # Quick presets for common FOV angles
        preset_menu = wx.Menu()
        preset_menu.Append(wx.ID_ANY, "Narrow FOV (20°)", "Set narrow field of view")
        preset_menu.Append(wx.ID_ANY, "Normal FOV (45°)", "Set normal field of view")
        preset_menu.Append(wx.ID_ANY, "Wide FOV (70°)", "Set wide field of view")
        preset_menu.Append(wx.ID_ANY, "Ultra Wide FOV (90°)", "Set ultra wide field of view")
        camera_menu.AppendSubMenu(preset_menu, "FOV Presets")
        
        camera_menu.AppendSeparator()
        
        # Screen rendering mode selection
        screen_render_menu = wx.Menu()
        self.simple_render_item = screen_render_menu.AppendRadioItem(wx.ID_ANY, "Simple Rendering", "Fast framebuffer rendering (original)")
        self.raytracing_render_item = screen_render_menu.AppendRadioItem(wx.ID_ANY, "Ray Tracing Rendering", 
"Advanced ray tracing rendering")
        camera_menu.AppendSubMenu(screen_render_menu, "Screen Rendering Mode")
        
        camera_menu.AppendSeparator()
        
        # Screen toggle
        camera_menu.AppendCheckItem(wx.ID_ANY, "Show 2D Screen", "Toggle 2D screen: Simple → Ray Tracing → Off")
        
        # Screen disable option
        camera_menu.Append(wx.ID_ANY, "Disable Screen", "Turn off the 2D screen completely")
        
        camera_menu.AppendSeparator()
        camera_menu.Append(wx.ID_ANY, "Reset to Default Angles", "Reset all angles to default values")
        
        menubar.Append(camera_menu, "Camera Angles")
        
        # Shapes menu
        shapes_menu = wx.Menu()
        
        # 0D shapes submenu
        shapes_0d_menu = wx.Menu()
        shapes_0d_menu.Append(wx.ID_ANY, "Add Dot", "Add a dot/point shape")
        shapes_menu.AppendSubMenu(shapes_0d_menu, "0D Shapes")
        
        # 1D shapes submenu
        shapes_1d_menu = wx.Menu()
        shapes_1d_menu.Append(wx.ID_ANY, "Add Line", "Add a line shape")
        shapes_1d_menu.Append(wx.ID_ANY, "Add Bezier Curve", "Add a Bezier curve")
        shapes_menu.AppendSubMenu(shapes_1d_menu, "1D Shapes")
        
        # 2D shapes submenu
        shapes_2d_menu = wx.Menu()
        shapes_2d_menu.Append(wx.ID_ANY, "Add Plane", "Add a plane shape")
        shapes_menu.AppendSubMenu(shapes_2d_menu, "2D Shapes")
        
        # 3D shapes submenu
        shapes_3d_menu = wx.Menu()
        shapes_3d_menu.Append(wx.ID_ANY, "Add Cube", "Add a cube shape")
        shapes_3d_menu.Append(wx.ID_ANY, "Add Sphere", "Add a sphere shape")
        shapes_3d_menu.Append(wx.ID_ANY, "Add Cylinder", "Add a cylinder shape")
        shapes_menu.AppendSubMenu(shapes_3d_menu, "3D Shapes")
        
        shapes_menu.AppendSeparator()
        shapes_menu.Append(wx.ID_ANY, "List All Shapes", "Show all shapes in the scene")
        shapes_menu.Append(wx.ID_ANY, "Clear All Shapes", "Remove all shapes from the scene")
        
        menubar.Append(shapes_menu, "Shapes")
        
        # Screens menu
        screens_menu = wx.Menu()
        
        # Add screens
        screens_menu.Append(wx.ID_ANY, "Add 2D Screen", "Add a 2D screen positioned in 3D space")
        screens_menu.Append(wx.ID_ANY, "Add Overlay Screen", "Add an overlay screen on the main view")
        
        screens_menu.AppendSeparator()
        
        # Add media screens
        screens_menu.Append(wx.ID_ANY, "Add Image Screen", "Add a screen displaying an image")
        screens_menu.Append(wx.ID_ANY, "Add Video Screen", "Add a screen displaying a video")
        screens_menu.Append(wx.ID_ANY, "Add GIF Screen", "Add a screen displaying an animated GIF")
        # Always show website screen option, but check availability when used
        screens_menu.Append(wx.ID_ANY, "Add Website Screen", "Add a screen displaying a webpage")
        if SELENIUM_AVAILABLE:
            print(f"DEBUG: Added Website Screen menu option (Selenium available)")
        else:
            print(f"DEBUG: Added Website Screen menu option (Selenium not available - will show error when used)")
        
        screens_menu.AppendSeparator()
        
        # Screen navigation
        screens_menu.Append(wx.ID_ANY, "Step Into Screen...", "Switch main view to a screen's camera perspective")
        screens_menu.Append(wx.ID_ANY, "Exit Screen View", "Return to normal main camera view")
        screens_menu.AppendSeparator()
        # Video playback controls
        screens_menu.Append(wx.ID_ANY, "Play/Pause Videos (Space)", "Toggle playback of all video screens")
        screens_menu.Append(wx.ID_ANY, "Restart Videos (R)", "Restart all video screens from beginning")
        screens_menu.Append(wx.ID_ANY, "Stop Videos (S)", "Stop playback of all video screens")
        
        screens_menu.AppendSeparator()
        
        # Video speed controls
        speed_menu = wx.Menu()
        speed_menu.Append(wx.ID_ANY, "0.5x Speed (1)", "Set video playback to half speed")
        speed_menu.Append(wx.ID_ANY, "1.0x Speed (2)", "Set video playback to normal speed")
        speed_menu.Append(wx.ID_ANY, "1.5x Speed (3)", "Set video playback to 1.5x speed")
        speed_menu.Append(wx.ID_ANY, "2.0x Speed (4)", "Set video playback to double speed")
        speed_menu.AppendSeparator()
        speed_menu.Append(wx.ID_ANY, "Increase Speed (↑)", "Increase video playback speed")
        speed_menu.Append(wx.ID_ANY, "Decrease Speed (↓)", "Decrease video playback speed")
        screens_menu.AppendSubMenu(speed_menu, "Video Speed", "Control video playback speed")
        
        # Frame rate submenu
        fps_menu = wx.Menu()
        fps_menu.Append(wx.ID_ANY, "15 FPS", "Set video frame rate to 15 FPS")
        fps_menu.Append(wx.ID_ANY, "24 FPS", "Set video frame rate to 24 FPS")
        fps_menu.Append(wx.ID_ANY, "30 FPS", "Set video frame rate to 30 FPS")
        fps_menu.Append(wx.ID_ANY, "60 FPS", "Set video frame rate to 60 FPS")
        fps_menu.AppendSeparator()
        fps_menu.Append(wx.ID_ANY, "Original FPS (R)", "Reset to original video frame rate")
        fps_menu.Append(wx.ID_ANY, "Cycle Frame Rate (F)", "Cycle through common frame rates")
        screens_menu.AppendSubMenu(fps_menu, "Frame Rate", "Control video frame rate")
        
        screens_menu.AppendSeparator()
        
        # Cameras submenu
        cameras_menu = wx.Menu()
        cameras_menu.Append(wx.ID_ANY, "Add Camera", "Add a new camera")
        cameras_menu.Append(wx.ID_ANY, "List Cameras", "Show all cameras in the scene")
        screens_menu.AppendSubMenu(cameras_menu, "Cameras")
        
        screens_menu.AppendSeparator()
        screens_menu.Append(wx.ID_ANY, "List All Screens", "Show all screens in the scene")
        screens_menu.Append(wx.ID_ANY, "Clear All Screens", "Remove all screens from the scene")
        
        menubar.Append(screens_menu, "Screens")
        
        # Help menu
        help_menu = wx.Menu()
        help_menu.Append(wx.ID_ANY, "Keyboard Controls...", "Show keyboard control shortcuts")
        help_menu.Append(wx.ID_ANY, "About Camera Movement...", "About camera movement controls")
        menubar.Append(help_menu, "Help")
        
        self.SetMenuBar(menubar)
        
        # Bind menu events
        self.Bind(wx.EVT_MENU, self.on_menu_event)
        
        # Update initial menu states
        self.update_menu_states()
    
    def on_menu_event(self, event):
        """Handle menu events."""
        print(f"DEBUG: Menu event triggered with ID: {event.GetId()}")
        
        menu_item = self.GetMenuBar().FindItemById(event.GetId())
        if not menu_item:
            print("DEBUG: No menu item found for this ID")
            return
        
        label = menu_item.GetItemLabelText()
        print(f"DEBUG: Menu item label: '{label}'")
        print(f"DEBUG: Label length: {len(label)}")
        print(f"DEBUG: Label repr: {repr(label)}")
        
        # File menu handlers
        if label == "New Scene":
            self.new_scene()
        elif label == "Open Scene...":
            self.open_scene()
        elif label == "Save Scene":
            self.save_scene()
        elif label == "Save Scene As...":
            self.save_scene_as()
        elif label == "Exit":
            self.Close()
        
        # Direct check for cone color first
        if "Set Cone Color" in label:
            print("DEBUG: Found cone color in label - calling set_cone_color()")
            self.set_cone_color()
            return
        
        if "Set Pyramid Color" in label:
            print("DEBUG: Found pyramid color in label - calling set_pyramid_color()")
            self.set_pyramid_color()
            return
        
        # Sphere appearance
        if label == "Set Sphere Color...":
            self.set_sphere_color()
        elif label == "Set Transparency...":
            self.set_sphere_transparency()
        
        # Sphere transforms
        elif label == "Reset Position":
            self.sphere.set_position(0, 0, 0)
            self.canvas.Refresh()
        elif label == "Reset Rotation":
            self.sphere.set_rotation(0, 0, 0)
            self.canvas.Refresh()
        elif label == "Reset Scale":
            self.sphere.set_scale(1, 1, 1)
            self.canvas.Refresh()
        elif label == "Set Position...":
            self.set_sphere_position()
        elif label == "Set Rotation...":
            self.set_sphere_rotation()
        elif label == "Set Scale...":
            self.set_sphere_scale()
        
        # Grid toggles
        elif label == "Longitude/Latitude Grid":
            self.sphere.toggle_grid(GridType.LONGITUDE_LATITUDE)
            self.canvas.Refresh()
        elif label == "Concentric Circles":
            self.sphere.toggle_grid(GridType.CONCENTRIC_CIRCLES)
            self.canvas.Refresh()
        elif label == "Dot Particles":
            self.sphere.toggle_grid(GridType.DOT_PARTICLES)
            self.canvas.Refresh()
        elif label == "Neon Lines":
            self.sphere.toggle_grid(GridType.NEON_LINES)
            self.canvas.Refresh()
        elif label == "Wireframe":
            self.sphere.toggle_grid(GridType.WIREFRAME)
            self.canvas.Refresh()
        
        # Grid colors
        elif "Color..." in label:
            self.set_grid_color(label)
        
        # Grid parameters
        elif label == "Set Longitude Lines...":
            self.set_longitude_lines()
        elif label == "Set Latitude Lines...":
            self.set_latitude_lines()
        elif label == "Set Concentric Rings...":
            self.set_concentric_rings()
        elif label == "Set Dot Density...":
            self.set_dot_density()
        elif label == "Set Neon Intensity...":
            self.set_neon_intensity()
        elif label == "Set Wireframe Density...":
            self.set_wireframe_density()
        
        # Vector controls
        elif label == "Show Vector":
            self.sphere.toggle_vector()
            self.canvas.Refresh()
        elif label == "Show Vector Orientation":
            self.sphere.toggle_vector_orientation()
            self.canvas.Refresh()
        elif label == "Show Cone":
            self.sphere.toggle_cone()
            self.canvas.Refresh()
        elif label == "Show Pyramid":
            self.sphere.toggle_pyramid()
            self.canvas.Refresh()
        elif label == "Show Cuboid":
            self.sphere.toggle_cuboid()
            self.canvas.Refresh()
        elif label == "Set Direction...":
            self.set_vector_direction()
        elif label == "Set Length...":
            self.set_vector_length()
        elif label == "Set Color...":
            self.set_vector_color()
        elif label == "Set Thickness...":
            self.set_vector_thickness()
        
        # Vector orientation controls
        elif label == "Set Roll Angle...":
            self.set_vector_roll()
        elif label == "Roll +15°":
            self.sphere.rotate_vector_roll(15.0)
        elif label == "Roll -15°":
            self.sphere.rotate_vector_roll(-15.0)
        elif label == "Roll +45°":
            self.sphere.rotate_vector_roll(45.0)
        elif label == "Roll -45°":
            self.sphere.rotate_vector_roll(-45.0)
        elif label == "Roll +90°":
            self.sphere.rotate_vector_roll(90.0)
        elif label == "Roll -90°":
            self.sphere.rotate_vector_roll(-90.0)
        elif label == "Roll 180°":
            self.sphere.rotate_vector_roll(180.0)
        elif label == "Reset Roll":
            self.sphere.set_vector_roll(0.0)
        
        # Cone controls
        elif label == "Set Cone Length...":
            self.set_cone_length()
        elif label == "Set Cone Angle...":
            self.set_cone_angle()
        elif label == "Set Cone Color...":
            self.set_cone_color()
        elif label == "Set Cone Transparency...":
            self.set_cone_transparency()
        elif label == "Set Cone Resolution...":
            self.set_cone_resolution()
        elif label == "Infinite Cone Length":
            self.sphere.toggle_cone_infinite()
            self.canvas.Refresh()
        
        # Pyramid controls
        elif label == "Set Pyramid Length...":
            self.set_pyramid_length()
        elif label == "Set Horizontal Angle...":
            self.set_pyramid_horizontal_angle()
        elif label == "Set Vertical Angle...":
            self.set_pyramid_vertical_angle()
        elif label == "Set Pyramid Color...":
            self.set_pyramid_color()
        elif label == "Set Pyramid Transparency...":
            self.set_pyramid_transparency()
        elif label == "Infinite Pyramid Length":
            self.sphere.toggle_pyramid_infinite()
            self.canvas.Refresh()
        
        # Cuboid properties
        elif label == "Set Cuboid Length...":
            self.set_cuboid_length()
        elif label == "Set Cuboid Width...":
            self.set_cuboid_width()
        elif label == "Set Cuboid Height...":
            self.set_cuboid_height()
        elif label == "Set Cuboid Color...":
            self.set_cuboid_color()
        elif label == "Set Cuboid Transparency...":
            self.set_cuboid_transparency()
        elif label == "Infinite Cuboid Length":
            self.sphere.toggle_cuboid_infinite()
            self.canvas.Refresh()
        
        # Near plane controls
        elif label == "Enable Near Plane":
            self.sphere.toggle_near_plane()
            self.canvas.Refresh()
        elif label == "Set Near Plane Distance...":
            self.set_near_plane_distance()
        
        # Sphere intersection controls
        elif label == "Show Sphere Intersections":
            self.sphere.toggle_sphere_intersection()
            self.canvas.Refresh()
        elif label == "Set Intersection Color...":
            self.set_sphere_intersection_color()
        
        # Vector presets
        elif label == "X-Axis (1,0,0)":
            self.sphere.set_vector_direction(1, 0, 0)
            self.canvas.update_sphere_view_vector()  # Update ray tracing camera
            self.canvas.Refresh()
        elif label == "Y-Axis (0,1,0)":
            self.sphere.set_vector_direction(0, 1, 0)
            self.canvas.update_sphere_view_vector()  # Update ray tracing camera
            self.canvas.Refresh()
        elif label == "Z-Axis (0,0,1)":
            self.sphere.set_vector_direction(0, 0, 1)
            self.canvas.update_sphere_view_vector()  # Update ray tracing camera
            self.canvas.Refresh()
        elif label == "-X-Axis (-1,0,0)":
            self.sphere.set_vector_direction(-1, 0, 0)
            self.canvas.update_sphere_view_vector()  # Update ray tracing camera
            self.canvas.Refresh()
        elif label == "-Y-Axis (0,-1,0)":
            self.sphere.set_vector_direction(0, -1, 0)
            self.canvas.update_sphere_view_vector()  # Update ray tracing camera
            self.canvas.Refresh()
        elif label == "-Z-Axis (0,0,-1)":
            self.sphere.set_vector_direction(0, 0, -1)
            self.canvas.update_sphere_view_vector()  # Update ray tracing camera
            self.canvas.Refresh()
        elif label == "Diagonal (1,1,1)":
            self.sphere.set_vector_direction(1, 1, 1)
            self.canvas.update_sphere_view_vector()  # Update ray tracing camera
            self.canvas.Refresh()
        elif label == "Random Direction":
            self.set_random_vector_direction()
        
        # View controls
        elif label == "Reset Camera":
            self.canvas.camera_distance = 5.0
            self.canvas.camera_rotation_x = 0.0
            self.canvas.camera_rotation_y = 0.0
            self.canvas.camera_position = np.array([0.0, 0.0, 0.0])
            self.canvas.Refresh()
        
        # Camera movement controls
        elif label == "Set Camera Position...":
            self.set_main_camera_position()
        elif label == "Set Camera Distance...":
            self.set_main_camera_distance()
        elif label == "Move Forward":
            self.move_camera_forward()
        elif label == "Move Backward":
            self.move_camera_backward()
        elif label == "Move Left":
            self.move_camera_left()
        elif label == "Move Right":
            self.move_camera_right()
        elif label == "Move Up":
            self.move_camera_up()
        elif label == "Move Down":
            self.move_camera_down()
        elif label == "Increase Movement Speed":
            self.canvas.movement_speed = min(1.0, self.canvas.movement_speed * 1.5)
            wx.MessageBox(f"Movement speed: {self.canvas.movement_speed:.2f}", "Speed Updated", wx.OK | wx.ICON_INFORMATION)
        elif label == "Decrease Movement Speed":
            self.canvas.movement_speed = max(0.05, self.canvas.movement_speed / 1.5)
            wx.MessageBox(f"Movement speed: {self.canvas.movement_speed:.2f}", "Speed Updated", wx.OK | wx.ICON_INFORMATION)
        
        # Sphere movement controls (sphere + vector + shapes only)
        elif label == "Set Sphere Position...":
            self.set_sphere_position_from_view_menu()
        elif label == "Move Sphere Forward":
            self.move_sphere_forward()
        elif label == "Move Sphere Backward":
            self.move_sphere_backward()
        elif label == "Move Sphere Left":
            self.move_sphere_left()
        elif label == "Move Sphere Right":
            self.move_sphere_right()
        elif label == "Move Sphere Up":
            self.move_sphere_up()
        elif label == "Move Sphere Down":
            self.move_sphere_down()
        elif label == "Center Sphere":
            self.sphere.set_position(0.0, 0.0, 0.0)
            self.canvas.Refresh()
            wx.MessageBox("Sphere centered at origin (0,0,0)", "Sphere Centered", wx.OK | wx.ICON_INFORMATION)
        elif label == "Center Camera on Cube":
            self.center_camera_on_cube()
        elif label == "Wireframe Mode":
            self.sphere.wireframe_mode = not self.sphere.wireframe_mode
            self.canvas.Refresh()
        elif label == "Enable Lighting":
            self.sphere.toggle_lighting()
            self.canvas.Refresh()
        elif label == "Show Normal Rays":
            self.sphere.toggle_normal_rays()
            self.canvas.Refresh()
        
        # Normal ray controls
        elif label == "Set Ray Length...":
            self.set_normal_ray_length()
        elif label == "Set Ray Density...":
            self.set_normal_ray_density()
        elif label == "Set Ray Color...":
            self.set_normal_ray_color()
        elif label == "Set Ray Thickness...":
            self.set_normal_ray_thickness()
        elif label == "Show Intersection Normals":
            self.sphere.toggle_intersection_normals()
            self.canvas.Refresh()
        
        # Intersection normal ray controls
        elif label == "Set Intersection Ray Length...":
            self.set_intersection_ray_length()
        elif label == "Set Intersection Ray Density...":
            self.set_intersection_ray_density()
        elif label == "Set Intersection Ray Color...":
            self.set_intersection_ray_color()
        elif label == "Set Intersection Ray Thickness...":
            self.set_intersection_ray_thickness()
        elif label == "Show Truncation Normals":
            self.sphere.toggle_truncation_normals()
            self.canvas.Refresh()
        
        # Truncation normal ray controls
        elif label == "Set Truncation Ray Length...":
            self.set_truncation_ray_length()
        elif label == "Set Truncation Ray Density...":
            self.set_truncation_ray_density()
        elif label == "Set Truncation Ray Color...":
            self.set_truncation_ray_color()
        elif label == "Set Truncation Ray Thickness...":
            self.set_truncation_ray_thickness()
        
        # Screen controls
        elif label == "Show Ray Tracing Screen":
            self.sphere.toggle_screen()
            self.canvas.Refresh()
        elif label == "Set Screen Position...":
            self.set_screen_position()
        elif label == "Set Screen Rotation...":
            self.set_screen_rotation()
        elif label == "Set Screen Size...":
            self.set_screen_size()
        elif label == "Ray Tracing":
            self.sphere.set_screen_render_mode("ray_tracing")
            self.canvas.Refresh()
        elif label == "Path Tracing":
            self.sphere.set_screen_render_mode("path_tracing")
            self.canvas.Refresh()
        elif label == "PBR Rendering":
            self.sphere.set_screen_render_mode("pbr")
            self.canvas.Refresh()
        elif label == "Ray Marching":
            self.sphere.set_screen_render_mode("ray_marching")
            self.canvas.Refresh()
        elif label == "Set Screen Resolution...":
            self.set_screen_resolution()
        elif label == "Set Camera Position...":
            self.set_camera_position()
        elif label == "Set Camera Target...":
            self.set_camera_target()
        elif label == "Set Update Rate...":
            self.set_screen_update_rate()
        elif label == "Set Samples...":
            self.set_screen_samples()
        elif label == "Set Max Bounces...":
            self.set_screen_max_bounces()
        
        # Object selection menu items
        elif label == "Camera Sphere":
            self.canvas.set_selected_object("sphere")
            self._uncheck_other_selection_items("sphere")
        elif label == "Rainbow Cube":
            self.canvas.set_selected_object("cube")
            self._uncheck_other_selection_items("cube")
        elif label == "2D Screen":
            self.canvas.set_selected_object("screen")
            self._uncheck_other_selection_items("screen")
        elif label == "None":
            self.canvas.set_selected_object("none")
            self._uncheck_other_selection_items("none")
        
        # Selected object rotation controls
        elif label == "Set Selected Rotation...":
            self.set_selected_object_rotation()
        elif label == "Rotate +15° X":
            self.rotate_selected_object(15, 0, 0)
        elif label == "Rotate -15° X":
            self.rotate_selected_object(-15, 0, 0)
        elif label == "Rotate +15° Y":
            self.rotate_selected_object(0, 15, 0)
        elif label == "Rotate -15° Y":
            self.rotate_selected_object(0, -15, 0)
        elif label == "Rotate +15° Z":
            self.rotate_selected_object(0, 0, 15)
        elif label == "Rotate -15° Z":
            self.rotate_selected_object(0, 0, -15)
        elif label == "Reset Selected Rotation":
            self.reset_selected_object_rotation()
        
        # Selected object position controls
        elif label == "Set Selected Position...":
            self.set_selected_object_position()
        elif label == "Move Selected Forward":
            self.move_selected_object_forward()
        elif label == "Move Selected Backward":
            self.move_selected_object_backward()
        elif label == "Move Selected Left":
            self.move_selected_object_left()
        elif label == "Move Selected Right":
            self.move_selected_object_right()
        elif label == "Move Selected Up":
            self.move_selected_object_up()
        elif label == "Move Selected Down":
            self.move_selected_object_down()
        elif label == "Reset Selected Position":
            self.reset_selected_object_position()
        
        # Object manipulation
        elif label == "Reset Selected Object":
            self.canvas.reset_selected_object()
        elif label == "Object Properties...":
            self.show_object_properties()
        
        # Rotation mode
        elif label == "Local Rotation":
            self.canvas.set_rotation_mode("local")
        elif label == "World Rotation":
            self.canvas.set_rotation_mode("world")
        
        # Camera Angles menu items (for 2D screen FOV control)
        elif label == "Set Cone Angle...":
            self.set_camera_cone_angle()
        elif label == "Set Pyramid Horizontal Angle...":
            self.set_camera_pyramid_horizontal_angle()
        elif label == "Set Pyramid Vertical Angle...":
            self.set_camera_pyramid_vertical_angle()
        elif label == "Set Cuboid Width...":
            self.set_camera_cuboid_width()
        elif label == "Set Cuboid Height...":
            self.set_camera_cuboid_height()
        
        # FOV Presets
        elif label == "Narrow FOV (20°)":
            self.set_fov_preset(20.0)
        elif label == "Normal FOV (45°)":
            self.set_fov_preset(45.0)
        elif label == "Wide FOV (70°)":
            self.set_fov_preset(70.0)
        elif label == "Ultra Wide FOV (90°)":
            self.set_fov_preset(90.0)
        elif label == "Reset to Default Angles":
            self.reset_camera_angles()
        
        # Help menu items
        elif label == "Keyboard Controls...":
            self.show_keyboard_controls()
        elif label == "About Camera Movement...":
            self.show_camera_movement_help()
        
        # Screen rendering mode selection
        elif label == "Simple Rendering":
            self.canvas.set_screen_render_mode("simple")
        elif label == "Ray Tracing Rendering":
            self.canvas.set_screen_render_mode("raytracing")
            # Also set sphere's render mode to match
            if hasattr(self.canvas, 'sphere'):
                self.canvas.sphere.set_screen_render_mode("ray_tracing")
        
        # Camera projection mode selection
        elif label == "Perspective Projection":
            self.canvas.camera_projection = "perspective"
            self.canvas.Refresh()
            print(f"DEBUG: Switched to perspective projection")
        elif label == "Orthographic Projection":
            self.canvas.camera_projection = "orthographic"
            self.canvas.Refresh()
            print(f"DEBUG: Switched to orthographic projection")
        
        # 2D Screen projection mode selection
        elif label == "2D Screen Perspective":
            self.canvas.screen_projection = "perspective"
            self.canvas.Refresh()
            print(f"DEBUG: Switched 2D screen to perspective projection")
        elif label == "2D Screen Orthographic":
            self.canvas.screen_projection = "orthographic"
            self.canvas.Refresh()
            print(f"DEBUG: Switched 2D screen to orthographic projection")
        
        # Screen toggle
        elif label == "Show 2D Screen":
            self.canvas.toggle_screen()
        
        # Screen disable
        elif label == "Disable Screen":
            self.canvas.disable_screen()
        
        # Shapes menu handlers
        elif label == "Add Dot":
            self.add_dot_shape()
        elif label == "Add Line":
            self.add_line_shape()
        elif label == "Add Bezier Curve":
            self.add_bezier_curve_shape()
        elif label == "Add Plane":
            self.add_plane_shape()
        elif label == "Add Cube":
            self.add_cube_shape()
        elif label == "Add Sphere":
            self.add_sphere_shape()
        elif label == "Add Cylinder":
            self.add_cylinder_shape()
        elif label == "List All Shapes":
            self.list_all_shapes()
        elif label == "Clear All Shapes":
            self.clear_all_shapes()
        
        # Screens menu handlers
        elif label == "Add 2D Screen":
            self.add_2d_screen()
        elif label == "Add Overlay Screen":
            self.add_overlay_screen()
        elif label == "Add Image Screen":
            self.add_image_screen()
        elif label == "Add Video Screen":
            self.add_video_screen()
        elif label == "Add GIF Screen":
            self.add_gif_screen()
        elif label == "Add Website Screen":
            self.add_website_screen()
        elif label == "Step Into Screen...":
            self.step_into_screen()
        elif label == "Exit Screen View":
            self.exit_screen_view()
        elif label.startswith("Play/Pause Videos"):
            self.canvas._toggle_video_playback()
        elif label.startswith("Restart Videos"):
            self.canvas._restart_video_playback()
        elif label.startswith("Stop Videos"):
            self.canvas._stop_video_playback()
        
        # Video speed controls
        elif label.startswith("0.5x Speed"):
            self.canvas._set_video_speed(0.5)
        elif label.startswith("1.0x Speed"):
            self.canvas._set_video_speed(1.0)
        elif label.startswith("1.5x Speed"):
            self.canvas._set_video_speed(1.5)
        elif label.startswith("2.0x Speed"):
            self.canvas._set_video_speed(2.0)
        elif label.startswith("Increase Speed"):
            self.canvas._adjust_video_speed(0.25)
        elif label.startswith("Decrease Speed"):
            self.canvas._adjust_video_speed(-0.25)
        
        # Frame rate controls
        elif label.startswith("15 FPS"):
            self.canvas._set_frame_rate(15)
        elif label.startswith("24 FPS"):
            self.canvas._set_frame_rate(24)
        elif label.startswith("30 FPS"):
            self.canvas._set_frame_rate(30)
        elif label.startswith("60 FPS"):
            self.canvas._set_frame_rate(60)
        elif label.startswith("Original FPS"):
            self.canvas._reset_frame_rate()
        elif label.startswith("Cycle Frame Rate"):
            self.canvas._cycle_frame_rate()
        
        elif label == "Add Camera":
            self.add_camera()
        elif label == "List Cameras":
            self.list_cameras()
        elif label == "List All Screens":
            self.list_all_screens()
        elif label == "Clear All Screens":
            self.clear_all_screens()
        
        # Update menu states after any change
        self.update_menu_states()
        
        # Add a catch-all at the end to see if we're missing anything
        print(f"DEBUG: Finished processing menu event for: '{label}'")
    
    def show_object_properties(self):
        """Show a dialog with properties of the selected object."""
        selected = self.canvas.selected_object
        if selected == "none":
            wx.MessageBox("No object selected", "Object Properties", wx.OK 
| wx.ICON_INFORMATION)
            return
        
        # Handle dynamic object types
        if selected.startswith("shape_"):
            shape_id = selected[6:]  # Remove "shape_" prefix
            shape = self.sphere.get_shape(shape_id)
            if shape:
                info = f"Selected Shape: {shape.name}\n\n"
                info += f"Type: {shape.__class__.__name__}\n"
                info += f"ID: {shape.id}\n"
                info += f"Position: [{shape.position[0]:.2f}, {shape.position[1]:.2f}, {shape.position[2]:.2f}]\n"
                info += f"Rotation: [{shape.rotation[0]:.1f}°, {shape.rotation[1]:.1f}°, {shape.rotation[2]:.1f}°]\n"
                info += f"Scale: [{shape.scale[0]:.2f}, {shape.scale[1]:.2f}, {shape.scale[2]:.2f}]\n"
                info += f"Color: [{shape.color[0]:.2f}, {shape.color[1]:.2f}, {shape.color[2]:.2f}, {shape.color[3]:.2f}]\n"
                info += f"Visible: {'Yes' if shape.visible else 'No'}\n"
                
                # Add shape-specific properties
                if hasattr(shape, 'size'):
                    info += f"Size: {shape.size:.2f}\n"
                if hasattr(shape, 'radius'):
                    info += f"Radius: {shape.radius:.2f}\n"
                if hasattr(shape, 'width') and hasattr(shape, 'height'):
                    info += f"Dimensions: {shape.width:.2f} x {shape.height:.2f}\n"
                if hasattr(shape, 'thickness'):
                    info += f"Thickness: {shape.thickness:.2f}\n"
            else:
                info = f"Shape not found: {shape_id}\n"
        
        elif selected.startswith("camera_"):
            camera_id = selected[7:]  # Remove "camera_" prefix
            camera = self.sphere.get_camera(camera_id)
            if camera:
                info = f"Selected Camera: {camera.name}\n\n"
                info += f"Type: {camera.type.value}\n"
                info += f"ID: {camera.id}\n"
                info += f"Position: [{camera.position[0]:.2f}, {camera.position[1]:.2f}, {camera.position[2]:.2f}]\n"
                info += f"Target: [{camera.target[0]:.2f}, {camera.target[1]:.2f}, {camera.target[2]:.2f}]\n"
                info += f"Up Vector: [{camera.up[0]:.2f}, {camera.up[1]:.2f}, {camera.up[2]:.2f}]\n"
                info += f"FOV: {camera.fov:.1f}°\n"
                info += f"Near Plane: {camera.near_plane:.2f}\n"
                info += f"Far Plane: {camera.far_plane:.2f}\n"
            else:
                info = f"Camera not found: {camera_id}\n"
        
        elif selected.startswith("screen_"):
            screen_id = selected[7:]  # Remove "screen_" prefix  
            screen = self.sphere.get_screen(screen_id)
            if screen:
                info = f"Selected Screen: {screen.name}\n\n"
                info += f"Type: {screen.type.value}\n"
                info += f"ID: {screen.id}\n"
                if screen.type == ScreenType.SCREEN_2D:
                    info += f"Position: [{screen.position[0]:.2f}, {screen.position[1]:.2f}, {screen.position[2]:.2f}]\n"
                    info += f"Rotation: [{screen.rotation[0]:.1f}°, {screen.rotation[1]:.1f}°, {screen.rotation[2]:.1f}°]\n"
                    info += f"Size: {screen.size[0]:.2f} x {screen.size[1]:.2f}\n"
                else:  # Overlay
                    info += f"Overlay Position: [{screen.overlay_position[0]:.2f}, {screen.overlay_position[1]:.2f}]\n"
                    info += f"Overlay Size: {screen.overlay_size[0]:.2f} x {screen.overlay_size[1]:.2f}\n"
                
                info += f"Camera ID: {screen.camera_id[:8] if screen.camera_id else 'None'}\n"
                info += f"Visible: {'Yes' if screen.visible else 'No'}\n"
                info += f"Texture Size: {screen.texture_width} x {screen.texture_height}\n"
            else:
                info = f"Screen not found: {screen_id}\n"
        
        else:
            info = f"Selected Object: {selected.title()}\n\n"
        
        if selected == "sphere":
            info += f"Position: {self.canvas.camera_position}\n"
            info += f"Rotation X: {self.canvas.camera_rotation_x:.1f}°\n"
            info += f"Rotation Y: {self.canvas.camera_rotation_y:.1f}°\n"
            info += f"Distance: {self.canvas.camera_distance:.1f}\n"
        elif selected == "cube":
            info += f"Position: {self.canvas.rainbow_cube_position}\n"
            info += f"Size: {self.canvas.rainbow_cube_size:.2f}\n"
            cube_rot = self.canvas.object_rotations['cube']
            info += f"Rotation: [{cube_rot[0]:.1f}°, {cube_rot[1]:.1f}°, {cube_rot[2]:.1f}°]\n"
        elif selected == "screen":
            info += f"Screen Status: {'Enabled' if self.canvas.screen_enabled else 'Disabled'}\n"
            info += f"Render Mode: {self.canvas.screen_render_mode.title()}\n"
            info += f"Position: {self.canvas.screen_position}\n"
            info += f"Size: {self.canvas.screen_width:.2f} x {self.canvas.screen_height:.2f}\n"
            
            if self.canvas.screen_render_mode == "simple":
                info += f"Resolution: {self.canvas.framebuffer_width} x {self.canvas.framebuffer_height}\n"
            else:  # raytracing mode
                info += f"Resolution: {self.sphere.screen_resolution}\n"
                info += f"Ray Tracing Mode: {self.sphere.screen_render_mode}\n"
                info += f"Samples: {self.sphere.screen_samples}\n"
                info += f"Max Bounces: {self.sphere.screen_max_bounces}\n"
                info += f"Update Rate: {self.sphere.screen_update_rate:.2f}s\n"
            
            screen_rot = self.canvas.object_rotations['screen']
            info += f"Rotation: [{screen_rot[0]:.1f}°, {screen_rot[1]:.1f}°, {screen_rot[2]:.1f}°]\n"
        
        info += f"\nRotation Mode: {self.canvas.rotation_mode.title()}"
        
        # Add sphere system information
        info += f"\n\n--- Sphere System Settings ---"
        sphere_pos = self.sphere.position
        info += f"\nSystem Position: [{sphere_pos[0]:.2f}, {sphere_pos[1]:.2f}, {sphere_pos[2]:.2f}]"
        info += f"\nSphere Radius: {self.sphere.radius:.2f}"
        
        # Add vector information
        info += f"\n\n--- Vector Settings ---"
        info += f"\nVector Enabled: {'Yes' if self.sphere.vector_enabled else 'No'}"
        if self.sphere.vector_enabled:
            vec_dir = self.sphere.vector_direction
            info += f"\nDirection: [{vec_dir[0]:.2f}, {vec_dir[1]:.2f}, {vec_dir[2]:.2f}]"
            info += f"\nLength: {self.sphere.vector_length:.2f}"
            info += f"\nRoll Orientation: {self.sphere.vector_roll:.1f}°"
        
        # Add main camera information
        info += f"\n\n--- Main Camera Settings ---"
        cam_pos = self.canvas.camera_position
        info += f"\nPosition: [{cam_pos[0]:.2f}, {cam_pos[1]:.2f}, {cam_pos[2]:.2f}]"
        info += f"\nDistance: {self.canvas.camera_distance:.1f}"
        info += f"\nRotation: X={self.canvas.camera_rotation_x:.1f}°, Y={self.canvas.camera_rotation_y:.1f}°"
        info += f"\nMovement Speed: {self.canvas.movement_speed:.2f}"
        
        # Add camera FOV information
        info += f"\n\n--- 2D Camera Settings ---"
        info += f"\nCone Angle: {self.sphere.cone_angle:.1f}° (FOV: {self.sphere.cone_angle * 2:.1f}°)"
        info += f"\nPyramid H-Angle: {self.sphere.pyramid_angle_horizontal:.1f}°"
        info += f"\nPyramid V-Angle: {self.sphere.pyramid_angle_vertical:.1f}°"
        if hasattr(self.sphere, 'cuboid_width') and hasattr(self.sphere, 'cuboid_height'):
            info += f"\nCuboid Size: {self.sphere.cuboid_width:.1f} x {self.sphere.cuboid_height:.1f}"
        
        wx.MessageBox(info, "Object Properties", wx.OK | wx.ICON_INFORMATION)
    
    def update_menu_states(self):
        """Update the checked state of menu items."""
        menubar = self.GetMenuBar()
        
        # Update dynamic selection menus
        self.update_dynamic_selection_menus()
        
        # Update object selection radio items
        if hasattr(self, 'sphere_selection_item'):
            self.sphere_selection_item.Check(self.canvas.selected_object == "sphere")
        if hasattr(self, 'cube_selection_item'):
            self.cube_selection_item.Check(self.canvas.selected_object == "cube")
        if hasattr(self, 'screen_selection_item'):
            self.screen_selection_item.Check(self.canvas.selected_object == "screen")
        if hasattr(self, 'none_selection_item'):
            self.none_selection_item.Check(self.canvas.selected_object == "none")
        
        # Update rotation mode radio items
        if hasattr(self, 'local_rotation_item'):
            self.local_rotation_item.Check(self.canvas.rotation_mode == "local")
        if hasattr(self, 'world_rotation_item'):
            self.world_rotation_item.Check(self.canvas.rotation_mode == "world")
        
        # Update screen rendering mode radio items
        if hasattr(self, 'simple_render_item'):
            self.simple_render_item.Check(self.canvas.screen_render_mode == "simple")
        if hasattr(self, 'raytracing_render_item'):
            self.raytracing_render_item.Check(self.canvas.screen_render_mode == "raytracing")
        
        # Find and update checkable menu items
        for menu_pos in range(menubar.GetMenuCount()):
            menu = menubar.GetMenu(menu_pos)
            for item in menu.GetMenuItems():
                if item.IsCheckable():
                    label = item.GetItemLabelText()
                    if label == "Wireframe Mode":
                        item.Check(self.sphere.wireframe_mode)
                    elif label == "Enable Lighting":
                        item.Check(self.sphere.lighting_enabled)
                    elif label == "Show Normal Rays":
                        item.Check(self.sphere.normal_rays_enabled)
                    elif label == "Show Intersection Normals":
                        item.Check(self.sphere.intersection_normals_enabled)
                    elif label == "Show Truncation Normals":
                        item.Check(self.sphere.truncation_normals_enabled)
                    elif label == "Show 2D Screen":
                        # Check if any screen mode is enabled
                        item.Check(self.canvas.screen_enabled)
                    elif label == "Show Vector":
                        item.Check(self.sphere.vector_enabled)
                    elif label == "Show Vector Orientation":
                        item.Check(self.sphere.vector_orientation_enabled)
                    elif label == "Show Cone":
                        item.Check(self.sphere.cone_enabled)
                    elif label == "Infinite Cone Length":
                        item.Check(self.sphere.cone_infinite)
                    elif label == "Show Pyramid":
                        item.Check(self.sphere.pyramid_enabled)
                    elif label == "Infinite Pyramid Length":
                        item.Check(self.sphere.pyramid_infinite)
                    elif label == "Show Cuboid":
                        item.Check(self.sphere.cuboid_enabled)
                    elif label == "Infinite Cuboid Length":
                        item.Check(self.sphere.cuboid_infinite)
                    elif label == "Enable Near Plane":
                        item.Check(self.sphere.near_plane_enabled)
                    elif label == "Show Sphere Intersections":
                        item.Check(self.sphere.sphere_intersection_enabled)
                                # Add grid states
                    elif label == "Longitude/Latitude Grid":
                        item.Check(GridType.LONGITUDE_LATITUDE in self.sphere.active_grids)
                    elif label == "Concentric Circles":
                        item.Check(GridType.CONCENTRIC_CIRCLES in self.sphere.active_grids)
                    elif label == "Dot Particles":
                        item.Check(GridType.DOT_PARTICLES in self.sphere.active_grids)
                    elif label == "Neon Lines":
                        item.Check(GridType.NEON_LINES in self.sphere.active_grids)
                    elif label == "Wireframe":
                        item.Check(GridType.WIREFRAME in self.sphere.active_grids)
                
    def set_sphere_color(self):
        """Open color dialog for sphere color."""
        color_data = wx.ColourData()
        current_color = self.sphere.sphere_color[:3] * 255
        color_data.SetColour(wx.Colour(int(current_color[0]), int(current_color[1]), int(current_color[2])))
        
        dialog = wx.ColourDialog(self, color_data)
        if dialog.ShowModal() == wx.ID_OK:
            color = dialog.GetColourData().GetColour()
            self.sphere.set_sphere_color((color.Red() / 255.0, color.Green() / 255.0, color.Blue() / 255.0))
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_sphere_transparency(self):
        """Set sphere transparency with slider dialog."""
        current_alpha = int(self.sphere.transparency * 100)
        dialog = wx.NumberEntryDialog(self, "Enter transparency (0-100):", 
"Transparency:", "Set Transparency", current_alpha, 0, 100)
        if dialog.ShowModal() == wx.ID_OK:
            alpha = dialog.GetValue() / 100.0
            self.sphere.set_transparency(alpha)
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_sphere_position(self):
        """Set sphere position with input dialog."""
        current_pos = self.sphere.position
        dialog = wx.TextEntryDialog(self, f"Enter position (x,y,z):", "Set Position", f"{current_pos[0]:.2f},{current_pos[1]:.2f},{current_pos[2]:.2f}")
        if dialog.ShowModal() == wx.ID_OK:
            try:
                coords = [float(x.strip()) for x in dialog.GetValue().split(',')]
                if len(coords) == 3:
                    # Store the old position to calculate the offset
                    old_pos = self.sphere.position.copy()
                    
                    # Set the new sphere position
                    self.sphere.set_position(*coords)
                    
                    # Update the 2D screen position to follow the sphere
                    self.canvas.update_screen_position_for_sphere_move(old_pos, self.sphere.position)
                    
                    self.canvas.Refresh()
            except ValueError:
                wx.MessageBox("Invalid position format. Use: x,y,z", 
"Error", wx.OK | wx.ICON_ERROR)
                dialog.Destroy()
    
    def set_sphere_rotation(self):
        """Set sphere rotation with input dialog."""
        current_rot = self.sphere.rotation
        dialog = wx.TextEntryDialog(self, f"Enter rotation (pitch,yaw,roll) in degrees:", "Set Rotation", f"{current_rot[0]:.1f},{current_rot[1]:.1f},{current_rot[2]:.1f}")
        if dialog.ShowModal() == wx.ID_OK:
            try:
                angles = [float(x.strip()) for x in dialog.GetValue().split(',')]
                if len(angles) == 3:
                    self.sphere.set_rotation(*angles)
                    self.canvas.Refresh()
            except ValueError:
                wx.MessageBox("Invalid rotation format. Use: pitch,yaw,roll", "Error", wx.OK | wx.ICON_ERROR)
                dialog.Destroy()
    
    def set_sphere_scale(self):
        """Set sphere scale with input dialog."""
        current_scale = self.sphere.scale
        dialog = wx.TextEntryDialog(self, f"Enter scale (sx,sy,sz):", "Set Scale", f"{current_scale[0]:.2f},{current_scale[1]:.2f},{current_scale[2]:.2f}")
        if dialog.ShowModal() == wx.ID_OK:
            try:
                scales = [float(x.strip()) for x in dialog.GetValue().split(',')]
                if len(scales) == 3:
                    self.sphere.set_scale(*scales)
                    self.canvas.Refresh()
            except ValueError:
                wx.MessageBox("Invalid scale format. Use: sx,sy,sz", 
"Error", wx.OK | wx.ICON_ERROR)
                dialog.Destroy()
    
    def set_grid_color(self, menu_label: str):
        """Set color for a specific grid type."""
        grid_type_map = {
        "Longitude/Latitude Color...": GridType.LONGITUDE_LATITUDE,
        "Concentric Circles Color...": GridType.CONCENTRIC_CIRCLES,
        "Dot Particles Color...": GridType.DOT_PARTICLES,
        "Neon Lines Color...": GridType.NEON_LINES,
        "Wireframe Color...": GridType.WIREFRAME
        }
            
        grid_type = grid_type_map.get(menu_label)
        if not grid_type:
            return
        
        color_data = wx.ColourData()
        current_color = self.sphere.grid_colors[grid_type][:3] * 255
        color_data.SetColour(wx.Colour(int(current_color[0]), int(current_color[1]), int(current_color[2])))
    
        dialog = wx.ColourDialog(self, color_data)
        if dialog.ShowModal() == wx.ID_OK:
            color = dialog.GetColourData().GetColour()
            new_color = (color.Red() / 255.0, color.Green() / 255.0, color.Blue() / 255.0, 1.0)
            self.sphere.set_grid_color(grid_type, new_color)
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_longitude_lines(self):
        """Set number of longitude lines."""
        dialog = wx.NumberEntryDialog(self, "Enter number of longitude lines:", "Lines:", "Longitude Lines", self.sphere.longitude_lines, 4, 64)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.longitude_lines = dialog.GetValue()
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_latitude_lines(self):
        """Set number of latitude lines."""
        dialog = wx.NumberEntryDialog(self, "Enter number of latitude lines:", "Lines:", "Latitude Lines", self.sphere.latitude_lines, 3, 32)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.latitude_lines = dialog.GetValue()
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_concentric_rings(self):
        """Set number of concentric rings."""
        dialog = wx.NumberEntryDialog(self, "Enter number of concentric rings:", "Rings:", "Concentric Rings", self.sphere.concentric_rings, 3, 
20)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.concentric_rings = dialog.GetValue()
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_dot_density(self):
        """Set dot particle density."""
        dialog = wx.NumberEntryDialog(self, "Enter dot particle density:", 
"Density:", "Dot Density", self.sphere.dot_density, 50, 1000)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.dot_density = dialog.GetValue()
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_neon_intensity(self):
        """Set neon glow intensity."""
        current_intensity = int(self.sphere.neon_intensity * 100)
        dialog = wx.NumberEntryDialog(self, "Enter neon intensity (0-200):", "Intensity:", "Neon Intensity", current_intensity, 0, 200)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.neon_intensity = dialog.GetValue() / 100.0
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_wireframe_density(self):
        """Set wireframe mesh density."""
        dialog = wx.NumberEntryDialog(self, "Enter wireframe density (4-64):", "Density:", "Wireframe Density", self.sphere.wireframe_resolution, 4, 64)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_wireframe_resolution(dialog.GetValue())
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_vector_direction(self):
        """Set vector direction with input dialog."""
        current_dir = self.sphere.vector_direction
        dialog = wx.TextEntryDialog(self, f"Enter vector direction (x,y,z):", "Set Vector Direction", f"{current_dir[0]:.2f},{current_dir[1]:.2f},{current_dir[2]:.2f}")
        if dialog.ShowModal() == wx.ID_OK:
            try:
                coords = [float(x.strip()) for x in dialog.GetValue().split(',')]
                if len(coords) == 3:
                    self.sphere.set_vector_direction(*coords)
                    self.canvas.Refresh()
            except ValueError:
                wx.MessageBox("Invalid direction format. Use: x,y,z", 
"Error", wx.OK | wx.ICON_ERROR)
                dialog.Destroy()
    
    def set_vector_length(self):
        """Set vector length with input dialog."""
        current_length = self.sphere.vector_length
        dialog = wx.NumberEntryDialog(self, "Enter vector length (relative to sphere radius):", "Length:", "Vector Length", int(current_length * 10), 
1, 100)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_vector_length(dialog.GetValue() / 10.0)
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_vector_color(self):
        """Set vector color with color dialog."""
        color_data = wx.ColourData()
        current_color = self.sphere.vector_color[:3] * 255
        color_data.SetColour(wx.Colour(int(current_color[0]), int(current_color[1]), int(current_color[2])))
        
        dialog = wx.ColourDialog(self, color_data)
        if dialog.ShowModal() == wx.ID_OK:
            color = dialog.GetColourData().GetColour()
            new_color = (color.Red() / 255.0, color.Green() / 255.0, color.Blue() / 255.0, 1.0)
            self.sphere.set_vector_color(new_color)
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_vector_thickness(self):
        """Set vector thickness with input dialog."""
        current_thickness = int(self.sphere.vector_thickness)
        dialog = wx.NumberEntryDialog(self, "Enter vector thickness (1-10):", "Thickness:", "Vector Thickness", current_thickness, 1, 10)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_vector_thickness(float(dialog.GetValue()))
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_vector_roll(self):
        """Set vector roll orientation with input dialog."""
        current_roll = self.sphere.vector_roll
        dialog = wx.NumberEntryDialog(self, f"Enter roll angle in degrees:", "Roll Angle:", "Set Vector Roll", int(current_roll), -360, 360)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_vector_roll(float(dialog.GetValue()))
            self.canvas.Refresh()
            wx.MessageBox(f"Vector roll set to: {dialog.GetValue()}°", 
"Roll Updated", wx.OK | wx.ICON_INFORMATION)
            dialog.Destroy()
    
    def set_random_vector_direction(self):
        """Set vector to a random direction."""
        import random
        # Generate random direction on unit sphere
        theta = random.uniform(0, 2 * math.pi)  # Azimuth
        phi = random.uniform(0, math.pi)        # Polar angle
            
        x = math.sin(phi) * math.cos(theta)
        y = math.cos(phi)
        z = math.sin(phi) * math.sin(theta)
        
        self.sphere.set_vector_direction(x, y, z)
        self.canvas.Refresh()
    
    # Camera movement methods
    def set_main_camera_position(self):
        """Set main camera position with input dialog."""
        current_pos = self.canvas.camera_position
        dialog = wx.TextEntryDialog(self, 
                                   f"Current position: ({current_pos[0]:.2f}, {current_pos[1]:.2f}, {current_pos[2]:.2f})\n"
                                   "Enter new position as 'x, y, z':", 
                                   "Set Camera Position", 
                                   f"{current_pos[0]:.2f},{current_pos[1]:.2f},{current_pos[2]:.2f}")
        if dialog.ShowModal() == wx.ID_OK:
            try:
                values = [float(x.strip()) for x in dialog.GetValue().split(',')]
                if len(values) == 3:
                    self.canvas.camera_position = np.array(values)
                    self.canvas.Refresh()
                    wx.MessageBox(f"Camera position set to ({values[0]:.2f}, {values[1]:.2f}, {values[2]:.2f})", 
                                 "Camera Updated", wx.OK | wx.ICON_INFORMATION)
                else:
                    wx.MessageBox("Please enter exactly 3 values separated by commas", "Invalid Input", wx.OK | wx.ICON_ERROR)
            except ValueError:
                wx.MessageBox("Invalid position format. Use: x,y,z (e.g., 0,0,0)", "Error", wx.OK | wx.ICON_ERROR)
        dialog.Destroy()
    
    def set_main_camera_distance(self):
        """Set main camera distance with input dialog."""
        current_distance = self.canvas.camera_distance
        dialog = wx.NumberEntryDialog(self, "Enter camera distance from origin:", "Distance:", "Camera Distance", 
                                     int(current_distance * 10), 10, 200)
        if dialog.ShowModal() == wx.ID_OK:
            self.canvas.camera_distance = dialog.GetValue() / 10.0
            self.canvas.Refresh()
            wx.MessageBox(f"Camera distance set to: {self.canvas.camera_distance:.1f}", "Distance Updated", wx.OK | wx.ICON_INFORMATION)
        dialog.Destroy()
    
    def move_camera_forward(self):
        """Move camera forward."""
        forward = self.canvas.get_camera_forward_vector()
        self.canvas.camera_position += forward * self.canvas.movement_speed
        self.canvas.Refresh()
    
    def move_camera_backward(self):
        """Move camera backward.""" 
        forward = self.canvas.get_camera_forward_vector()
        self.canvas.camera_position -= forward * self.canvas.movement_speed
        self.canvas.Refresh()
    
    def move_camera_left(self):
        """Move camera left."""
        right = self.canvas.get_camera_right_vector()
        self.canvas.camera_position -= right * self.canvas.movement_speed
        self.canvas.Refresh()
    
    def move_camera_right(self):
        """Move camera right."""
        right = self.canvas.get_camera_right_vector()
        self.canvas.camera_position += right * self.canvas.movement_speed
        self.canvas.Refresh()
    
    def move_camera_up(self):
        """Move camera up."""
        up = self.canvas.get_camera_up_vector()
        self.canvas.camera_position += up * self.canvas.movement_speed
        self.canvas.Refresh()
    
    def move_camera_down(self):
        """Move camera down."""
        up = self.canvas.get_camera_up_vector()
        self.canvas.camera_position -= up * self.canvas.movement_speed
        self.canvas.Refresh()
    
    # Sphere movement methods (sphere + vector + shapes only)
    def set_sphere_position_from_view_menu(self):
        """Set sphere position with input dialog (from View menu)."""
        current_pos = self.sphere.position
        dialog = wx.TextEntryDialog(self, 
                                   f"Current sphere position: ({current_pos[0]:.2f}, {current_pos[1]:.2f}, {current_pos[2]:.2f})\n"
                                   "Enter new position as 'x, y, z':\n"
                                   "(This moves sphere + vector + shapes only, cube and screen stay in place)", 
                                   "Set Sphere Position", 
                                   f"{current_pos[0]:.2f},{current_pos[1]:.2f},{current_pos[2]:.2f}")
        if dialog.ShowModal() == wx.ID_OK:
            try:
                values = [float(x.strip()) for x in dialog.GetValue().split(',')]
                if len(values) == 3:
                    self.sphere.set_position(values[0], values[1], values[2])
                    self.canvas.Refresh()
                    wx.MessageBox(f"Sphere position set to ({values[0]:.2f}, {values[1]:.2f}, {values[2]:.2f})", 
                                 "Sphere Updated", wx.OK | wx.ICON_INFORMATION)
                else:
                    wx.MessageBox("Please enter exactly 3 values separated by commas", "Invalid Input", wx.OK | wx.ICON_ERROR)
            except ValueError:
                wx.MessageBox("Invalid position format. Use: x,y,z (e.g., 2,0,-1)", "Error", wx.OK | wx.ICON_ERROR)
        dialog.Destroy()
    
    def move_sphere_forward(self):
        """Move sphere forward (along main camera's forward direction). Cube and screen stay in place."""
        forward = self.canvas.get_camera_forward_vector()
        new_pos = self.sphere.position + forward * self.canvas.movement_speed
        self.sphere.set_position(new_pos[0], new_pos[1], new_pos[2])
        self.canvas.Refresh()
    
    def move_sphere_backward(self):
        """Move sphere backward. Cube and screen stay in place.""" 
        forward = self.canvas.get_camera_forward_vector()
        new_pos = self.sphere.position - forward * self.canvas.movement_speed
        self.sphere.set_position(new_pos[0], new_pos[1], new_pos[2])
        self.canvas.Refresh()
    
    def move_sphere_left(self):
        """Move sphere left. Cube and screen stay in place."""
        right = self.canvas.get_camera_right_vector()
        new_pos = self.sphere.position - right * self.canvas.movement_speed
        self.sphere.set_position(new_pos[0], new_pos[1], new_pos[2])
        self.canvas.Refresh()
    
    def move_sphere_right(self):
        """Move sphere right. Cube and screen stay in place."""
        right = self.canvas.get_camera_right_vector()
        new_pos = self.sphere.position + right * self.canvas.movement_speed
        self.sphere.set_position(new_pos[0], new_pos[1], new_pos[2])
        self.canvas.Refresh()
    
    def move_sphere_up(self):
        """Move sphere up. Cube and screen stay in place."""
        up = self.canvas.get_camera_up_vector()
        new_pos = self.sphere.position + up * self.canvas.movement_speed
        self.sphere.set_position(new_pos[0], new_pos[1], new_pos[2])
        self.canvas.Refresh()
    
    def move_sphere_down(self):
        """Move sphere down. Cube and screen stay in place."""
        up = self.canvas.get_camera_up_vector()
        new_pos = self.sphere.position - up * self.canvas.movement_speed
        self.sphere.set_position(new_pos[0], new_pos[1], new_pos[2])
        self.canvas.Refresh()
    
    def set_camera_cone_angle(self):
        """Set cone angle which affects 2D camera vertical FOV."""
        current_angle = self.sphere.cone_angle
        dialog = wx.NumberEntryDialog(self, "Enter cone angle (degrees):", 
"Angle:", "Cone Angle", 
                                     int(current_angle), 5, 89)
        if dialog.ShowModal() == wx.ID_OK:
            new_angle = float(dialog.GetValue())
            self.sphere.set_cone_angle(new_angle)
            self.canvas.update_sphere_view_vector()  # Update 2D screen
            self.canvas.Refresh()
        dialog.Destroy()
    
    def set_camera_pyramid_horizontal_angle(self):
        """Set pyramid horizontal angle which affects 2D camera horizontal FOV."""
        current_angle = self.sphere.pyramid_angle_horizontal
        dialog = wx.NumberEntryDialog(self, "Enter pyramid horizontal angle (degrees):", "Angle:", 
                                     "Pyramid Horizontal Angle", int(current_angle), 5, 89)
        if dialog.ShowModal() == wx.ID_OK:
            new_angle = float(dialog.GetValue())
            self.sphere.set_pyramid_angle_horizontal(new_angle)
            self.canvas.update_sphere_view_vector()  # Update 2D screen
            self.canvas.Refresh()
        dialog.Destroy()
    
    def set_camera_pyramid_vertical_angle(self):
        """Set pyramid vertical angle which affects 2D camera vertical FOV."""
        current_angle = self.sphere.pyramid_angle_vertical
        dialog = wx.NumberEntryDialog(self, "Enter pyramid vertical angle (degrees):", "Angle:", 
                                     "Pyramid Vertical Angle", int(current_angle), 5, 89)
        if dialog.ShowModal() == wx.ID_OK:
            new_angle = float(dialog.GetValue())
            self.sphere.set_pyramid_angle_vertical(new_angle)
            self.canvas.update_sphere_view_vector()  # Update 2D screen
            self.canvas.Refresh()
        dialog.Destroy()
    
    def set_camera_cuboid_width(self):
        """Set cuboid width which affects 2D camera horizontal view."""
        current_width = self.sphere.cuboid_width
        dialog = wx.NumberEntryDialog(self, "Enter cuboid width:", 
"Width:", "Cuboid Width", 
                                     int(current_width * 10), 1, 100)
        if dialog.ShowModal() == wx.ID_OK:
            new_width = float(dialog.GetValue()) / 10.0
            self.sphere.set_cuboid_width(new_width)
            self.canvas.update_sphere_view_vector()  # Update 2D screen
            self.canvas.Refresh()
        dialog.Destroy()
    
    def set_camera_cuboid_height(self):
        """Set cuboid height which affects 2D camera vertical view."""
        current_height = self.sphere.cuboid_height
        dialog = wx.NumberEntryDialog(self, "Enter cuboid height:", 
"Height:", "Cuboid Height", 
                                     int(current_height * 10), 1, 100)
        if dialog.ShowModal() == wx.ID_OK:
            new_height = float(dialog.GetValue()) / 10.0
            self.sphere.set_cuboid_height(new_height)
            self.canvas.update_sphere_view_vector()  # Update 2D screen
            self.canvas.Refresh()
        dialog.Destroy()
    
    def set_fov_preset(self, fov_degrees):
        """Set FOV preset by adjusting cone and pyramid angles."""
        # Set cone angle to the FOV value
        self.sphere.set_cone_angle(fov_degrees)
        # Set pyramid angles to match (making them roughly square)
        self.sphere.set_pyramid_angle_horizontal(fov_degrees)
        self.sphere.set_pyramid_angle_vertical(fov_degrees)
        # Update 2D screen
        self.canvas.update_sphere_view_vector()
        self.canvas.Refresh()
        print(f"DEBUG: Set FOV preset to {fov_degrees}°")
    
    def reset_camera_angles(self):
        """Reset all camera angles to default values."""
        self.sphere.set_cone_angle(30.0)
        self.sphere.set_pyramid_angle_horizontal(25.0)
        self.sphere.set_pyramid_angle_vertical(20.0)
        self.sphere.set_cuboid_width(2.0)
        self.sphere.set_cuboid_height(1.5)
        self.canvas.update_sphere_view_vector()
        self.canvas.Refresh()
        print("DEBUG: Reset camera angles to defaults")
    
    def show_keyboard_controls(self):
        """Show keyboard control shortcuts."""
        controls = """KEYBOARD CONTROLS:

🎮 CAMERA MOVEMENT:Arrow Keys - Move camera left/right/up/downI/O Keys - Move camera forward/backwardShift+I/O - Zoom in/out

🖱️ MOUSE CONTROLS:Left Click + Drag - Rotate viewMouse Wheel - Zoom in/out

📐 OBJECT ROTATION:When object is selected:
- Mouse drag rotates the selected object
- Use Object menu to select different objects

⚙️ MOVEMENT SPEED:Use View → Camera Movement → Increase/Decrease Movement SpeedCurrent speed shown in Object Properties dialog

💡 TIP: Select different objects (sphere, cube, screen) to control what gets rotated with mouse movement."""
        
        wx.MessageBox(controls, "Keyboard Controls", wx.OK | wx.ICON_INFORMATION)
    
    def show_camera_movement_help(self):
        """Show help about camera movement."""
        help_text = """CAMERA MOVEMENT SYSTEM:

🎥 TWO CAMERA SYSTEMS:
1. MAIN CAMERA - Your 3D viewpoint
2. 2D SCREEN CAMERA - What the sphere "sees"

📍 MAIN CAMERA CONTROLS:
• Position: Where you're looking from in 3D space
• Distance: How far you are from the origin
• Rotation: Your viewing angle

🎯 2D SCREEN CAMERA:
• Always looks from sphere center
• Direction follows the red vector
• Roll can be adjusted with Vector → Vector Orientation

🌐 SPHERE MOVEMENT:
• Move sphere + vector + shapes (cube and screen stay in place)
• View → Sphere Movement
• Multicolored cube and 2D screen maintain fixed world positions

⚡ QUICK ACTIONS:
• View → Camera Movement → Move Forward/Backward/etc.
• View → Sphere Movement → Move Sphere/Set Position
• View → Reset Camera (return to default view)
• Adjust movement speed for fine/coarse control

🔄 COORDINATE SYSTEM:
• X-axis: Left(-) / Right(+)  
• Y-axis: Down(-) / Up(+)
• Z-axis: Into screen(-) / Out of screen(+)

🎛️ THREE INDEPENDENT SYSTEMS:
• Move YOUR viewpoint (camera movement)
• Move the SPHERE + vector + shapes (sphere movement)  
• Multicolored cube and 2D screen stay in fixed world positions!"""
        
        wx.MessageBox(help_text, "About Camera Movement", wx.OK | wx.ICON_INFORMATION)
    
    # Selected object manipulation methods
    def set_selected_object_rotation(self):
        """Set selected object rotation with input dialog."""
        selected = self.canvas.selected_object
        if selected == "none":
            wx.MessageBox("No object selected. Use Object → Select Object to choose an object.", "No Selection", wx.OK | wx.ICON_WARNING)
            return
        
        if selected in self.canvas.object_rotations:
            current_rot = self.canvas.object_rotations[selected]
            dialog = wx.TextEntryDialog(self, 
                                       f"Current {selected} rotation: ({current_rot[0]:.1f}°, {current_rot[1]:.1f}°, {current_rot[2]:.1f}°)\n"
                                       "Enter new rotation as 'pitch, yaw, roll' in degrees:", 
                                       f"Set {selected.title()} Rotation", 
                                       f"{current_rot[0]:.1f},{current_rot[1]:.1f},{current_rot[2]:.1f}")
            if dialog.ShowModal() == wx.ID_OK:
                try:
                    values = [float(x.strip()) for x in dialog.GetValue().split(',')]
                    if len(values) == 3:
                        self.canvas.object_rotations[selected] = np.array(values)
                        self.canvas.Refresh()
                        wx.MessageBox(f"{selected.title()} rotation set to ({values[0]:.1f}°, {values[1]:.1f}°, {values[2]:.1f}°)", 
                                     "Rotation Updated", wx.OK | wx.ICON_INFORMATION)
                    else:
                        wx.MessageBox("Please enter exactly 3 values separated by commas", "Invalid Input", wx.OK | wx.ICON_ERROR)
                except ValueError:
                    wx.MessageBox("Invalid rotation format. Use: pitch,yaw,roll (e.g., 45,0,-30)", "Error", wx.OK | wx.ICON_ERROR)
            dialog.Destroy()
    
    def rotate_selected_object(self, pitch_delta, yaw_delta, roll_delta):
        """Rotate selected object by specified amounts."""
        selected = self.canvas.selected_object
        if selected == "none":
            wx.MessageBox("No object selected. Use Object → Select Object to choose an object.", "No Selection", wx.OK | wx.ICON_WARNING)
            return
        
        if selected in self.canvas.object_rotations:
            self.canvas.object_rotations[selected][0] += pitch_delta  # X/Pitch
            self.canvas.object_rotations[selected][1] += yaw_delta    # Y/Yaw
            self.canvas.object_rotations[selected][2] += roll_delta   # Z/Roll
            self.canvas.Refresh()
    
    def reset_selected_object_rotation(self):
        """Reset selected object rotation to zero."""
        selected = self.canvas.selected_object
        if selected == "none":
            wx.MessageBox("No object selected. Use Object → Select Object to choose an object.", "No Selection", wx.OK | wx.ICON_WARNING)
            return
        
        if selected in self.canvas.object_rotations:
            self.canvas.object_rotations[selected] = np.array([0.0, 0.0, 
0.0])
            self.canvas.Refresh()
            wx.MessageBox(f"{selected.title()} rotation reset to zero", 
"Rotation Reset", wx.OK | wx.ICON_INFORMATION)
    
    def set_selected_object_position(self):
        """Set selected object position with input dialog."""
        selected = self.canvas.selected_object
        if selected == "none":
            wx.MessageBox("No object selected. Use Object → Select Object to choose an object.", "No Selection", wx.OK | wx.ICON_WARNING)
            return
        
        current_pos = None
        if selected == "sphere":
            current_pos = self.sphere.position
        elif selected == "cube":
            current_pos = self.canvas.rainbow_cube_position
        elif selected == "screen":
            current_pos = self.canvas.screen_position
        
        if current_pos is not None:
            dialog = wx.TextEntryDialog(self, 
                                       f"Current {selected} position: ({current_pos[0]:.2f}, {current_pos[1]:.2f}, {current_pos[2]:.2f})\n"
                                       "Enter new position as 'x, y, z':", 
                                       f"Set {selected.title()} Position", 
                                       f"{current_pos[0]:.2f},{current_pos[1]:.2f},{current_pos[2]:.2f}")
            if dialog.ShowModal() == wx.ID_OK:
                try:
                    values = [float(x.strip()) for x in dialog.GetValue().split(',')]
                    if len(values) == 3:
                        if selected == "sphere":
                            self.sphere.set_position(values[0], values[1], values[2])
                        elif selected == "cube":
                            self.canvas.rainbow_cube_position = np.array(values)
                        elif selected == "screen":
                            self.canvas.screen_position = np.array(values)
                        
                        self.canvas.Refresh()
                        wx.MessageBox(f"{selected.title()} position set to ({values[0]:.2f}, {values[1]:.2f}, {values[2]:.2f})", 
                                     "Position Updated", wx.OK | wx.ICON_INFORMATION)
                    else:
                        wx.MessageBox("Please enter exactly 3 values separated by commas", "Invalid Input", wx.OK | wx.ICON_ERROR)
                except ValueError:
                    wx.MessageBox("Invalid position format. Use: x,y,z (e.g., 2,0,-1)", "Error", wx.OK | wx.ICON_ERROR)
            dialog.Destroy()
    
    def move_selected_object_forward(self):
        """Move selected object forward."""
        self.move_selected_object_by_direction("forward")
    
    def move_selected_object_backward(self):
        """Move selected object backward."""
        self.move_selected_object_by_direction("backward")
    
    def move_selected_object_left(self):
        """Move selected object left."""
        self.move_selected_object_by_direction("left")
    
    def move_selected_object_right(self):
        """Move selected object right."""
        self.move_selected_object_by_direction("right")
    
    def move_selected_object_up(self):
        """Move selected object up."""
        self.move_selected_object_by_direction("up")
    
    def move_selected_object_down(self):
        """Move selected object down."""
        self.move_selected_object_by_direction("down")
    
    def move_selected_object_by_direction(self, direction):
        """Move selected object in specified direction."""
        selected = self.canvas.selected_object
        if selected == "none":
            wx.MessageBox("No object selected. Use Object → Select Object to choose an object.", "No Selection", wx.OK | wx.ICON_WARNING)
            return
        
        # Get movement vector based on direction
        if direction == "forward":
            movement = self.canvas.get_camera_forward_vector() * self.canvas.movement_speed
        elif direction == "backward":
            movement = -self.canvas.get_camera_forward_vector() * self.canvas.movement_speed
        elif direction == "left":
            movement = -self.canvas.get_camera_right_vector() * self.canvas.movement_speed
        elif direction == "right":
            movement = self.canvas.get_camera_right_vector() * self.canvas.movement_speed
        elif direction == "up":
            movement = self.canvas.get_camera_up_vector() * self.canvas.movement_speed
        elif direction == "down":
            movement = -self.canvas.get_camera_up_vector() * self.canvas.movement_speed
        else:
            return
        
        # Apply movement to selected object
        if selected == "sphere":
            new_pos = self.sphere.position + movement
            self.sphere.set_position(new_pos[0], new_pos[1], new_pos[2])
        elif selected == "cube":
            self.canvas.rainbow_cube_position += movement
        elif selected == "screen":
            self.canvas.screen_position += movement
        
        self.canvas.Refresh()
    
    def reset_selected_object_position(self):
        """Reset selected object position to default."""
        selected = self.canvas.selected_object
        if selected == "none":
            wx.MessageBox("No object selected. Use Object → Select Object to choose an object.", "No Selection", wx.OK | wx.ICON_WARNING)
            return
        
        if selected == "sphere":
            self.sphere.set_position(0.0, 0.0, 0.0)
            wx.MessageBox("Sphere position reset to origin (0,0,0)", 
"Position Reset", wx.OK | wx.ICON_INFORMATION)
        elif selected == "cube":
            self.canvas.rainbow_cube_position = np.array([2.0, 0.0, 2.0])
            wx.MessageBox("Cube position reset to default (2,0,2)", 
"Position Reset", wx.OK | wx.ICON_INFORMATION)
        elif selected == "screen":
            self.canvas.screen_position = np.array([-3.0, 0.0, 0.0])
            wx.MessageBox("Screen position reset to default (-3,0,0)", 
"Position Reset", wx.OK | wx.ICON_INFORMATION)
        
        self.canvas.Refresh()
    
    def center_camera_on_cube(self):
        """Center the camera to look at the multicolored cube."""
        cube_pos = self.canvas.rainbow_cube_position
        
        # Reset camera to look at cube
        self.canvas.camera_distance = 5.0
        self.canvas.camera_rotation_x = 0.0
        self.canvas.camera_rotation_y = 0.0
        
        # Position camera to look at cube - move camera opposite to cube position
        # Since cube is at [2,0,2], position camera at [-2,0,-2] to look at it
        self.canvas.camera_position = -cube_pos * 0.5  # Move camera to look at cube
        
        self.canvas.Refresh()
        wx.MessageBox(f"Camera centered on cube at position {cube_pos}", 
"Camera Positioned", wx.OK | wx.ICON_INFORMATION)
    
    def set_cone_length(self):
        """Set cone length with input dialog."""
        current_length = self.sphere.cone_length
        dialog = wx.NumberEntryDialog(self, "Enter cone length (relative to sphere radius):", "Length:", "Cone Length", int(current_length * 10), 
5, 100)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_cone_length(dialog.GetValue() / 10.0)
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_cone_angle(self):
        """Set cone angle with input dialog."""
        current_angle = int(self.sphere.cone_angle)
        dialog = wx.NumberEntryDialog(self, "Enter cone half-angle (degrees):", "Angle:", "Cone Angle", current_angle, 5, 89)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_cone_angle(float(dialog.GetValue()))
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_cone_color(self):
        """Set cone color with choice dialog (more reliable than color picker)."""
        colors = [
        ("Red", (1.0, 0.0, 0.0)),
        ("Green", (0.0, 1.0, 0.0)),
        ("Blue", (0.0, 0.0, 1.0)),
        ("Yellow", (1.0, 1.0, 0.0)),
        ("Cyan", (0.0, 1.0, 1.0)),
        ("Magenta", (1.0, 0.0, 1.0)),
        ("Orange", (1.0, 0.5, 0.0)),
        ("Purple", (0.5, 0.0, 1.0)),
        ("Pink", (1.0, 0.5, 0.5)),
        ("White", (1.0, 1.0, 1.0)),
        ("Gray", (0.5, 0.5, 0.5)),
        ("Black", (0.0, 0.0, 0.0))
        ]
            
        color_names = [name for name, _ in colors]
        
        dialog = wx.SingleChoiceDialog(self, "Choose a color for the cone:", "Select Cone Color", color_names)
        dialog.SetSelection(0)  # Default to red
        
        if dialog.ShowModal() == wx.ID_OK:
            selection = dialog.GetSelection()
            color_name, rgb = colors[selection]
            new_color = (rgb[0], rgb[1], rgb[2], self.sphere.cone_color[3])
            self.sphere.set_cone_color(new_color)
            self.canvas.Refresh()
            wx.MessageBox(f"Cone color set to {color_name}", "Color Updated", wx.OK | wx.ICON_INFORMATION)
        
            dialog.Destroy()
    
    def set_cone_transparency(self):
        """Set cone transparency with input dialog."""
        current_alpha = int(self.sphere.cone_color[3] * 100)
        dialog = wx.NumberEntryDialog(self, "Enter transparency (0-100):", 
"Transparency:", "Cone Transparency", current_alpha, 0, 100)
        if dialog.ShowModal() == wx.ID_OK:
            alpha = dialog.GetValue() / 100.0
            new_color = (self.sphere.cone_color[0], self.sphere.cone_color[1], self.sphere.cone_color[2], alpha)
            self.sphere.set_cone_color(new_color)
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_cone_resolution(self):
        """Set cone resolution with input dialog."""
        current_resolution = self.sphere.cone_resolution
        dialog = wx.NumberEntryDialog(self, "Enter cone resolution (6-32):", "Resolution:", "Cone Resolution", current_resolution, 6, 32)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_cone_resolution(dialog.GetValue())
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_pyramid_length(self):
        """Set pyramid length with input dialog."""
        current_length = self.sphere.pyramid_length
        dialog = wx.NumberEntryDialog(self, "Enter pyramid length (relative to sphere radius):", "Length:", "Pyramid Length", int(current_length * 10), 5, 100)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_pyramid_length(dialog.GetValue() / 10.0)
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_pyramid_horizontal_angle(self):
        """Set pyramid horizontal angle with input dialog."""
        current_angle = int(self.sphere.pyramid_angle_horizontal)
        dialog = wx.NumberEntryDialog(self, "Enter horizontal half-angle (degrees):", "Angle:", "Horizontal Angle", current_angle, 5, 89)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_pyramid_angle_horizontal(float(dialog.GetValue()))
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_pyramid_vertical_angle(self):
        """Set pyramid vertical angle with input dialog."""
        current_angle = int(self.sphere.pyramid_angle_vertical)
        dialog = wx.NumberEntryDialog(self, "Enter vertical half-angle (degrees):", "Angle:", "Vertical Angle", current_angle, 5, 89)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_pyramid_angle_vertical(float(dialog.GetValue()))
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_pyramid_color(self):
        """Set pyramid color with choice dialog (more reliable than color picker)."""
        print("DEBUG: set_pyramid_color() method started")
        
        try:
            colors = [
            ("Red", (1.0, 0.0, 0.0)),
            ("Green", (0.0, 1.0, 0.0)),
            ("Blue", (0.0, 0.0, 1.0)),
            ("Yellow", (1.0, 1.0, 0.0)),
            ("Cyan", (0.0, 1.0, 1.0)),
            ("Magenta", (1.0, 0.0, 1.0)),
            ("Orange", (1.0, 0.5, 0.0)),
            ("Purple", (0.5, 0.0, 1.0)),
            ("Pink", (1.0, 0.5, 0.5)),
            ("White", (1.0, 1.0, 1.0)),
            ("Gray", (0.5, 0.5, 0.5)),
            ("Black", (0.0, 0.0, 0.0))
            ]
                
            print(f"DEBUG: Colors list created with {len(colors)} colors")
                
            color_names = [name for name, _ in colors]
            print(f"DEBUG: Color names: {color_names}")
                
            print("DEBUG: About to create SingleChoiceDialog for pyramid")
            dialog = wx.SingleChoiceDialog(self, "Choose a color for the pyramid:", "Select Pyramid Color", color_names)
            print("DEBUG: SingleChoiceDialog for pyramid created successfully")
            
            dialog.SetSelection(2)  # Default to blue (different from cone)
            print("DEBUG: Default selection set to 2 (Blue)")
            
            print("DEBUG: About to show pyramid dialog with ShowModal()")
            result = dialog.ShowModal()
            print(f"DEBUG: Pyramid dialog result: {result} (wx.ID_OK = {wx.ID_OK})")
            
            if result == wx.ID_OK:
                selection = dialog.GetSelection()
                print(f"DEBUG: User selected pyramid index: {selection}")
                color_name, rgb = colors[selection]
                print(f"DEBUG: Selected pyramid color: {color_name} with RGB: {rgb}")
                new_color = (rgb[0], rgb[1], rgb[2], self.sphere.pyramid_color[3])
                print(f"DEBUG: New pyramid color with alpha: {new_color}")
                self.sphere.set_pyramid_color(new_color)
                print("DEBUG: Color set on pyramid")
                self.canvas.Refresh()
                print("DEBUG: Canvas refreshed")
                wx.MessageBox(f"Pyramid color set to {color_name}", "Color Updated", wx.OK | wx.ICON_INFORMATION)
                print("DEBUG: Pyramid confirmation message shown")
            else:
                print("DEBUG: Pyramid dialog was cancelled")
                    
                print("DEBUG: About to destroy pyramid dialog")
                dialog.Destroy()
                print("DEBUG: Pyramid dialog destroyed")
            
        except Exception as e:
            print(f"DEBUG: Exception in set_pyramid_color(): {e}")
            import traceback
            traceback.print_exc()
            # Show error to user too
            wx.MessageBox(f"Error setting pyramid color: {str(e)}", 
"Error", wx.OK | wx.ICON_ERROR)
        
        print("DEBUG: set_pyramid_color() method finished")
    
    def set_pyramid_transparency(self):
        """Set pyramid transparency with input dialog."""
        current_alpha = int(self.sphere.pyramid_color[3] * 100)
        dialog = wx.NumberEntryDialog(self, "Enter transparency (0-100):", 
"Transparency:", "Pyramid Transparency", current_alpha, 0, 100)
        if dialog.ShowModal() == wx.ID_OK:
            alpha = dialog.GetValue() / 100.0
            new_color = (self.sphere.pyramid_color[0], self.sphere.pyramid_color[1], self.sphere.pyramid_color[2], alpha)
            self.sphere.set_pyramid_color(new_color)
            self.canvas.Refresh()
            dialog.Destroy()
    
    # Cuboid dialog methods
    def set_cuboid_length(self):
        """Set cuboid length with input dialog."""
        current_length = self.sphere.cuboid_length
        dialog = wx.NumberEntryDialog(self, "Enter cuboid length along vector (relative to sphere radius):", "Length:", "Cuboid Length", int(current_length * 10), 1, 100)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_cuboid_length(dialog.GetValue() / 10.0)
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_cuboid_width(self):
        """Set cuboid width with input dialog."""
        current_width = self.sphere.cuboid_width
        dialog = wx.NumberEntryDialog(self, "Enter cuboid width perpendicular to vector (relative to sphere radius):", "Width:", "Cuboid Width", int(current_width * 10), 1, 100)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_cuboid_width(dialog.GetValue() / 10.0)
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_cuboid_height(self):
        """Set cuboid height with input dialog."""
        current_height = self.sphere.cuboid_height
        dialog = wx.NumberEntryDialog(self, "Enter cuboid height perpendicular to vector (relative to sphere radius):", "Height:", "Cuboid Height", int(current_height * 10), 1, 100)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_cuboid_height(dialog.GetValue() / 10.0)
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_cuboid_color(self):
        """Set cuboid color with choice dialog (more reliable than color picker)."""
        # Define available colors
        colors = [
        ("Red", (1.0, 0.0, 0.0)),
        ("Green", (0.0, 1.0, 0.0)),
        ("Blue", (0.0, 0.0, 1.0)),
        ("Yellow", (1.0, 1.0, 0.0)),
        ("Cyan", (0.0, 1.0, 1.0)),
        ("Magenta", (1.0, 0.0, 1.0)),
        ("Orange", (1.0, 0.5, 0.0)),
        ("Purple", (0.5, 0.0, 1.0)),
        ("Pink", (1.0, 0.5, 0.5)),
        ("White", (1.0, 1.0, 1.0)),
        ("Gray", (0.5, 0.5, 0.5)),
        ("Black", (0.0, 0.0, 0.0))
        ]
            
        color_names = [name for name, _ in colors]
        
        dialog = wx.SingleChoiceDialog(self, "Choose a color for the cuboid:", "Select Cuboid Color", color_names)
        dialog.SetSelection(6)  # Default to orange (different from cone and pyramid)
        
        if dialog.ShowModal() == wx.ID_OK:
            selection = dialog.GetSelection()
            color_name, rgb = colors[selection]
            new_color = (rgb[0], rgb[1], rgb[2], self.sphere.cuboid_color[3])
            self.sphere.set_cuboid_color(new_color)
            self.canvas.Refresh()
            wx.MessageBox(f"Cuboid color set to {color_name}", "Color Updated", wx.OK | wx.ICON_INFORMATION)
        
            dialog.Destroy()
    
    def set_cuboid_transparency(self):
        """Set cuboid transparency with input dialog."""
        current_alpha = int(self.sphere.cuboid_color[3] * 100)
        dialog = wx.NumberEntryDialog(self, "Enter transparency (0-100):", 
"Transparency:", "Cuboid Transparency", current_alpha, 0, 100)
        if dialog.ShowModal() == wx.ID_OK:
            alpha = dialog.GetValue() / 100.0
            new_color = (self.sphere.cuboid_color[0], self.sphere.cuboid_color[1], self.sphere.cuboid_color[2], alpha)
            self.sphere.set_cuboid_color(new_color)
            self.canvas.Refresh()
            dialog.Destroy()
    
    # Near plane dialog methods
    def set_near_plane_distance(self):
        """Set near plane distance with input dialog."""
        current_distance = self.sphere.near_plane_distance
        dialog = wx.NumberEntryDialog(self, "Enter near plane distance from sphere center (relative to radius):", "Distance:", "Near Plane Distance", int(current_distance * 10), 0, 30)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_near_plane_distance(dialog.GetValue() / 10.0)
            self.canvas.Refresh()
            dialog.Destroy()
    
    # Sphere intersection dialog methods
    def set_sphere_intersection_color(self):
        """Set sphere intersection color with choice dialog."""
        colors = [
        ("Bright Yellow", (1.0, 1.0, 0.0)),
        ("Orange", (1.0, 0.5, 0.0)),
        ("Red", (1.0, 0.0, 0.0)),
        ("Green", (0.0, 1.0, 0.0)),
        ("Blue", (0.0, 0.0, 1.0)),
        ("Cyan", (0.0, 1.0, 1.0)),
        ("Magenta", (1.0, 0.0, 1.0)),
        ("Purple", (0.5, 0.0, 1.0)),
        ("Pink", (1.0, 0.5, 0.5)),
        ("White", (1.0, 1.0, 1.0)),
        ]
            
        color_names = [name for name, _ in colors]
        
        dialog = wx.SingleChoiceDialog(self, "Choose a color for sphere intersections:", "Select Intersection Color", color_names)
        dialog.SetSelection(0)  # Default to bright yellow
        
        if dialog.ShowModal() == wx.ID_OK:
            selection = dialog.GetSelection()
            color_name, rgb = colors[selection]
            new_color = (rgb[0], rgb[1], rgb[2], self.sphere.sphere_intersection_color[3])
            self.sphere.set_sphere_intersection_color(new_color)
            self.canvas.Refresh()
            wx.MessageBox(f"Sphere intersection color set to {color_name}", "Color Updated", wx.OK | wx.ICON_INFORMATION)
        
            dialog.Destroy()
    
    # Normal ray dialog methods
    def set_normal_ray_length(self):
        """Set normal ray length with number dialog."""
        current_length = self.sphere.normal_rays_length
        dialog = wx.NumberEntryDialog(self, "Enter ray length (relative to sphere radius):", "Length:", "Normal Ray Length", int(current_length * 
10), 1, 20)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_normal_rays_length(dialog.GetValue() / 10.0)
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_normal_ray_density(self):
        """Set normal ray density with number dialog."""
        current_density = self.sphere.normal_rays_density
        dialog = wx.NumberEntryDialog(self, "Enter ray density (rays per division):", "Density:", "Normal Ray Density", current_density, 4, 20)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_normal_rays_density(dialog.GetValue())
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_normal_ray_color(self):
        """Set normal ray color with choice dialog."""
        colors = [
        ("Cyan", (0.0, 1.0, 1.0)),
        ("Red", (1.0, 0.0, 0.0)),
        ("Green", (0.0, 1.0, 0.0)),
        ("Blue", (0.0, 0.0, 1.0)),
        ("Yellow", (1.0, 1.0, 0.0)),
        ("Magenta", (1.0, 0.0, 1.0)),
        ("Orange", (1.0, 0.5, 0.0)),
        ("Purple", (0.5, 0.0, 1.0)),
        ("Pink", (1.0, 0.5, 0.5)),
        ("White", (1.0, 1.0, 1.0)),
        ]
            
        color_names = [name for name, _ in colors]
        
        dialog = wx.SingleChoiceDialog(self, "Choose a color for normal rays:", "Select Ray Color", color_names)
        dialog.SetSelection(0)  # Default to cyan
        
        if dialog.ShowModal() == wx.ID_OK:
            selection = dialog.GetSelection()
            color_name, rgb = colors[selection]
            new_color = (rgb[0], rgb[1], rgb[2], self.sphere.normal_rays_color[3])
            self.sphere.set_normal_rays_color(new_color)
            self.canvas.Refresh()
            wx.MessageBox(f"Normal ray color set to {color_name}", "Color Updated", wx.OK | wx.ICON_INFORMATION)
        
            dialog.Destroy()
    
    def set_normal_ray_thickness(self):
        """Set normal ray thickness with number dialog."""
        current_thickness = self.sphere.normal_rays_thickness
        dialog = wx.NumberEntryDialog(self, "Enter ray thickness (1-5):", 
"Thickness:", "Normal Ray Thickness", int(current_thickness), 1, 5)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_normal_rays_thickness(float(dialog.GetValue()))
            self.canvas.Refresh()
            dialog.Destroy()
    
    # Intersection normal ray dialog methods
    def set_intersection_ray_length(self):
        """Set intersection normal ray length with number dialog."""
        current_length = self.sphere.intersection_normals_length
        dialog = wx.NumberEntryDialog(self, "Enter intersection ray length (relative to sphere radius):", "Length:", "Intersection Ray Length", int(current_length * 10), 1, 20)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_intersection_normals_length(dialog.GetValue() 
/ 10.0)
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_intersection_ray_density(self):
        """Set intersection normal ray density with number dialog."""
        current_density = self.sphere.intersection_normals_density
        dialog = wx.NumberEntryDialog(self, "Enter intersection ray density (rays per division):", "Density:", "Intersection Ray Density", current_density, 4, 24)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_intersection_normals_density(dialog.GetValue())
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_intersection_ray_color(self):
        """Set intersection normal ray color with choice dialog."""
        colors = [
        ("Magenta", (1.0, 0.0, 1.0)),
        ("Red", (1.0, 0.0, 0.0)),
        ("Green", (0.0, 1.0, 0.0)),
        ("Blue", (0.0, 0.0, 1.0)),
        ("Cyan", (0.0, 1.0, 1.0)),
        ("Yellow", (1.0, 1.0, 0.0)),
        ("Orange", (1.0, 0.5, 0.0)),
        ("Purple", (0.5, 0.0, 1.0)),
        ("Pink", (1.0, 0.5, 0.5)),
        ("White", (1.0, 1.0, 1.0)),
        ]
            
        color_names = [name for name, _ in colors]
        
        dialog = wx.SingleChoiceDialog(self, "Choose a color for intersection normal rays:", "Select Intersection Ray Color", color_names)
        dialog.SetSelection(0)  # Default to magenta
        
        if dialog.ShowModal() == wx.ID_OK:
            selection = dialog.GetSelection()
            color_name, rgb = colors[selection]
            new_color = (rgb[0], rgb[1], rgb[2], self.sphere.intersection_normals_color[3])
            self.sphere.set_intersection_normals_color(new_color)
            self.canvas.Refresh()
            wx.MessageBox(f"Intersection normal ray color set to {color_name}", "Color Updated", wx.OK | wx.ICON_INFORMATION)
        
            dialog.Destroy()
    
    def set_intersection_ray_thickness(self):
        """Set intersection normal ray thickness with number dialog."""
        current_thickness = self.sphere.intersection_normals_thickness
        dialog = wx.NumberEntryDialog(self, "Enter intersection ray thickness (1-5):", "Thickness:", "Intersection Ray Thickness", int(current_thickness), 1, 5)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_intersection_normals_thickness(float(dialog.GetValue()))
            self.canvas.Refresh()
            dialog.Destroy()
    
    # Truncation normal ray dialog methods
    def set_truncation_ray_length(self):
        """Set truncation normal ray length with number dialog."""
        current_length = self.sphere.truncation_normals_length
        dialog = wx.NumberEntryDialog(self, "Enter truncation ray length (relative to sphere radius):", "Length:", "Truncation Ray Length", int(current_length * 10), 1, 20)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_truncation_normals_length(dialog.GetValue() / 
10.0)
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_truncation_ray_density(self):
        """Set truncation normal ray density with number dialog."""
        current_density = self.sphere.truncation_normals_density
        dialog = wx.NumberEntryDialog(self, "Enter truncation ray density (rays per division):", "Density:", "Truncation Ray Density", current_density, 3, 16)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_truncation_normals_density(dialog.GetValue())
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_truncation_ray_color(self):
        """Set truncation normal ray color with choice dialog."""
        colors = [
        ("White", (1.0, 1.0, 1.0)),
        ("Red", (1.0, 0.0, 0.0)),
        ("Green", (0.0, 1.0, 0.0)),
        ("Blue", (0.0, 0.0, 1.0)),
        ("Cyan", (0.0, 1.0, 1.0)),
        ("Magenta", (1.0, 0.0, 1.0)),
        ("Yellow", (1.0, 1.0, 0.0)),
        ("Orange", (1.0, 0.5, 0.0)),
        ("Purple", (0.5, 0.0, 1.0)),
        ("Pink", (1.0, 0.5, 0.5)),
        ]
        
        color_names = [name for name, _ in colors]
        
        dialog = wx.SingleChoiceDialog(self, "Choose a color for truncation normal rays:", "Select Truncation Ray Color", color_names)
        dialog.SetSelection(0)  # Default to white
        
        if dialog.ShowModal() == wx.ID_OK:
            selection = dialog.GetSelection()
            color_name, rgb = colors[selection]
            new_color = (rgb[0], rgb[1], rgb[2], self.sphere.truncation_normals_color[3])
            self.sphere.set_truncation_normals_color(new_color)
            self.canvas.Refresh()
            wx.MessageBox(f"Truncation normal ray color set to {color_name}", "Color Updated", wx.OK | wx.ICON_INFORMATION)
        
            dialog.Destroy()
    
    def set_truncation_ray_thickness(self):
        """Set truncation normal ray thickness with number dialog."""
        current_thickness = self.sphere.truncation_normals_thickness
        dialog = wx.NumberEntryDialog(self, "Enter truncation ray thickness (1-5):", "Thickness:", "Truncation Ray Thickness", int(current_thickness), 1, 5)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_truncation_normals_thickness(float(dialog.GetValue()))
            self.canvas.Refresh()
            dialog.Destroy()
    
    # ==================== SCREEN DIALOG METHODS ====================
    
    def set_screen_position(self):
        """Set screen 3D position with input dialog."""
        current_pos = self.sphere.screen_position
        dialog = wx.TextEntryDialog(self, 
                                   f"Current position: ({current_pos[0]:.2f}, {current_pos[1]:.2f}, {current_pos[2]:.2f})\n"
                                   "Enter new position as 'x, y, z':", 
                                   "Set Screen Position", 
                                   f"{current_pos[0]:.2f}, {current_pos[1]:.2f}, {current_pos[2]:.2f}")
        if dialog.ShowModal() == wx.ID_OK:
            try:
                values = [float(x.strip()) for x in dialog.GetValue().split(',')]
                if len(values) == 3:
                    self.sphere.set_screen_position(values[0], values[1], values[2])
                    self.canvas.Refresh()
                    wx.MessageBox(f"Screen position set to ({values[0]:.2f}, {values[1]:.2f}, {values[2]:.2f})", 
                                 "Position Updated", wx.OK | wx.ICON_INFORMATION)
                else:
                    wx.MessageBox("Please enter exactly 3 values separated by commas", "Invalid Input", wx.OK | wx.ICON_ERROR)
            except ValueError:
                wx.MessageBox("Please enter valid numbers", "Invalid Input", wx.OK | wx.ICON_ERROR)
        dialog.Destroy()
    
    def set_screen_rotation(self):
        """Set screen rotation with input dialog."""
        current_rot = self.sphere.screen_rotation
        dialog = wx.TextEntryDialog(self, 
                                   f"Current rotation: ({current_rot[0]:.1f}°, {current_rot[1]:.1f}°, {current_rot[2]:.1f}°)\n"
                                   "Enter new rotation as 'pitch, yaw, roll' in degrees:", 
                                   "Set Screen Rotation", 
                                   f"{current_rot[0]:.1f}, {current_rot[1]:.1f}, {current_rot[2]:.1f}")
        if dialog.ShowModal() == wx.ID_OK:
            try:
                values = [float(x.strip()) for x in dialog.GetValue().split(',')]
                if len(values) == 3:
                    self.sphere.set_screen_rotation(values[0], values[1], values[2])
                    self.canvas.Refresh()
                    wx.MessageBox(f"Screen rotation set to ({values[0]:.1f}°, {values[1]:.1f}°, {values[2]:.1f}°)", 
                                 "Rotation Updated", wx.OK | wx.ICON_INFORMATION)
                else:
                    wx.MessageBox("Please enter exactly 3 values separated by commas", "Invalid Input", wx.OK | wx.ICON_ERROR)
            except ValueError:
                wx.MessageBox("Please enter valid numbers", "Invalid Input", wx.OK | wx.ICON_ERROR)
        dialog.Destroy()
    
    def set_screen_size(self):
        """Set screen size with input dialog."""
        current_size = (self.sphere.screen_width, self.sphere.screen_height)
        dialog = wx.TextEntryDialog(self, 
                                   f"Current size: {current_size[0]:.2f} x {current_size[1]:.2f}\n"
                                   "Enter new size as 'width, height':", 
                                   "Set Screen Size", 
                                   f"{current_size[0]:.2f}, {current_size[1]:.2f}")
        if dialog.ShowModal() == wx.ID_OK:
            try:
                values = [float(x.strip()) for x in dialog.GetValue().split(',')]
                if len(values) == 2 and all(v > 0 for v in values):
                    self.sphere.set_screen_size(values[0], values[1])
                    self.canvas.Refresh()
                    wx.MessageBox(f"Screen size set to {values[0]:.2f} x {values[1]:.2f}", 
                                 "Size Updated", wx.OK | wx.ICON_INFORMATION)
                else:
                    wx.MessageBox("Please enter exactly 2 positive values separated by a comma", "Invalid Input", wx.OK | wx.ICON_ERROR)
            except ValueError:
                wx.MessageBox("Please enter valid numbers", "Invalid Input", wx.OK | wx.ICON_ERROR)
        dialog.Destroy()
    
    def set_screen_resolution(self):
        """Set screen texture resolution with input dialog."""
        current_res = self.sphere.screen_resolution
        dialog = wx.TextEntryDialog(self, 
                                   f"Current resolution: {current_res[0]} x {current_res[1]}\n"
                                   "Enter new resolution as 'width, height' (e.g., 512, 384):", 
                                   "Set Screen Resolution", 
                                   f"{current_res[0]}, {current_res[1]}")
        if dialog.ShowModal() == wx.ID_OK:
            try:
                values = [int(x.strip()) for x in dialog.GetValue().split(',')]
                if len(values) == 2 and all(v > 0 for v in values):
                    self.sphere.set_screen_resolution(values[0], values[1])
                    self.canvas.Refresh()
                    wx.MessageBox(f"Screen resolution set to {values[0]} x {values[1]}", 
                                 "Resolution Updated", wx.OK | wx.ICON_INFORMATION)
                else:
                    wx.MessageBox("Please enter exactly 2 positive integers separated by a comma", "Invalid Input", wx.OK | wx.ICON_ERROR)
            except ValueError:
                wx.MessageBox("Please enter valid integers", "Invalid Input", wx.OK | wx.ICON_ERROR)
        dialog.Destroy()
    
    def set_camera_position(self):
        """Set virtual camera position with input dialog."""
        current_pos = self.sphere.screen_camera_position
        dialog = wx.TextEntryDialog(self, 
                                   f"Current camera position: ({current_pos[0]:.2f}, {current_pos[1]:.2f}, {current_pos[2]:.2f})\n"
                                   "Enter new camera position as 'x, y, z':", 
                                   "Set Camera Position", 
                                   f"{current_pos[0]:.2f}, {current_pos[1]:.2f}, {current_pos[2]:.2f}")
        if dialog.ShowModal() == wx.ID_OK:
            try:
                values = [float(x.strip()) for x in dialog.GetValue().split(',')]
                if len(values) == 3:
                    self.sphere.set_camera_position(values[0], values[1], values[2])
                    self.canvas.Refresh()
                    wx.MessageBox(f"Camera position set to ({values[0]:.2f}, {values[1]:.2f}, {values[2]:.2f})", 
                                 "Camera Updated", wx.OK | wx.ICON_INFORMATION)
                else:
                    wx.MessageBox("Please enter exactly 3 values separated by commas", "Invalid Input", wx.OK | wx.ICON_ERROR)
            except ValueError:
                wx.MessageBox("Please enter valid numbers", "Invalid Input", wx.OK | wx.ICON_ERROR)
        dialog.Destroy()
    
    def set_camera_target(self):
        """Set virtual camera target with input dialog."""
        current_target = self.sphere.screen_camera_target
        dialog = wx.TextEntryDialog(self, 
                                   f"Current camera target: ({current_target[0]:.2f}, {current_target[1]:.2f}, {current_target[2]:.2f})\n"
                                   "Enter new camera target as 'x, y, z':", 
                                   "Set Camera Target", 
                                   f"{current_target[0]:.2f}, {current_target[1]:.2f}, {current_target[2]:.2f}")
        if dialog.ShowModal() == wx.ID_OK:
            try:
                values = [float(x.strip()) for x in dialog.GetValue().split(',')]
                if len(values) == 3:
                    self.sphere.set_camera_target(values[0], values[1], values[2])
                    self.canvas.Refresh()
                    wx.MessageBox(f"Camera target set to ({values[0]:.2f}, {values[1]:.2f}, {values[2]:.2f})", 
                                 "Camera Updated", wx.OK | wx.ICON_INFORMATION)
                else:
                    wx.MessageBox("Please enter exactly 3 values separated by commas", "Invalid Input", wx.OK | wx.ICON_ERROR)
            except ValueError:
                wx.MessageBox("Please enter valid numbers", "Invalid Input", wx.OK | wx.ICON_ERROR)
        dialog.Destroy()
    
    def set_screen_update_rate(self):
        """Set screen update rate with number dialog."""
        current_rate = self.sphere.screen_update_rate
        dialog = wx.NumberEntryDialog(self, "Enter screen update rate in seconds (0.1 - 5.0):", "Rate:", "Screen Update Rate", 
                                     int(current_rate * 10), 1, 50)  # Convert to tenths of seconds
        if dialog.ShowModal() == wx.ID_OK:
            rate = dialog.GetValue() / 10.0  # Convert back to seconds
            self.sphere.set_screen_update_rate(rate)
            wx.MessageBox(f"Screen update rate set to {rate:.1f} seconds", 
"Rate Updated", wx.OK | wx.ICON_INFORMATION)
        dialog.Destroy()
    
    def set_screen_samples(self):
        """Set anti-aliasing samples with number dialog."""
        current_samples = self.sphere.screen_samples
        dialog = wx.NumberEntryDialog(self, "Enter anti-aliasing samples per pixel (1-16):", "Samples:", "Screen Samples", 
                                     current_samples, 1, 16)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_screen_samples(dialog.GetValue())
            wx.MessageBox(f"Screen samples set to {dialog.GetValue()}", 
"Samples Updated", wx.OK | wx.ICON_INFORMATION)
        dialog.Destroy()
    
    def set_screen_max_bounces(self):
        """Set maximum ray bounces with number dialog."""
        current_bounces = self.sphere.screen_max_bounces
        dialog = wx.NumberEntryDialog(self, "Enter maximum ray bounces for reflections (0-8):", "Bounces:", "Max Ray Bounces", 
                                     current_bounces, 0, 8)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_screen_max_bounces(dialog.GetValue())
            wx.MessageBox(f"Maximum ray bounces set to {dialog.GetValue()}", "Bounces Updated", wx.OK | wx.ICON_INFORMATION)
        dialog.Destroy()
    
    # ==================== END SCREEN DIALOG METHODS ====================
    
    # ==================== FILE MENU METHODS ====================
    
    def new_scene(self):
        """Create a new scene (reset to defaults)."""
        result = wx.MessageBox("This will reset all settings to defaults. Continue?", 
                              "New Scene", wx.YES_NO | wx.ICON_QUESTION)
        if result == wx.YES:
            # Reset sphere to defaults
            self.sphere = SphereRenderer()
            self.sphere._canvas_ref = self.canvas  # Restore canvas reference
            
            # Reset canvas to defaults
            self.canvas.camera_distance = 5.0
            self.canvas.camera_rotation_x = 0.0
            self.canvas.camera_rotation_y = 0.0
            self.canvas.camera_position = np.array([0.0, 0.0, 0.0])
            self.canvas.view_vector = np.array([0.0, 0.0, -1.0])
            self.canvas.rainbow_cube_position = np.array([2.0, 0.0, 2.0])
            self.canvas.rainbow_cube_size = 0.3
            
            # Reset object rotations
            self.canvas.object_rotations = {
                "sphere": np.array([0.0, 0.0, 0.0]),
                "cube": np.array([0.0, 0.0, 0.0]),
                "screen": np.array([0.0, 0.0, 0.0])
            }
            
            # Update canvas sphere reference
            self.canvas.sphere = self.sphere
            
            # Refresh display
            self.canvas.Refresh()
            
            # Update menu states
            self.update_menu_states()
            
            wx.MessageBox("New scene created successfully!", "New Scene", wx.OK | wx.ICON_INFORMATION)
    
    def open_scene(self):
        """Open a scene from a JSON file."""
        wildcard = "Scene files (*.json)|*.json|All files (*.*)|*.*"
        dialog = wx.FileDialog(self, "Open Scene", wildcard=wildcard, style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        
        if dialog.ShowModal() == wx.ID_OK:
            filepath = dialog.GetPath()
            try:
                with open(filepath, 'r') as f:
                    scene_data = json.load(f)
                
                # Load sphere data
                if "sphere_data" in scene_data:
                    self.sphere.load_scene_from_dict(scene_data["sphere_data"])
                
                # Load canvas data
                if "canvas_data" in scene_data:
                    self.canvas.load_canvas_scene_from_dict(scene_data["canvas_data"])
                
                # Update canvas sphere reference
                self.canvas.sphere = self.sphere
                self.sphere._canvas_ref = self.canvas
                
                # Refresh display
                self.canvas.Refresh()
                
                # Update menu states
                self.update_menu_states()
                
                wx.MessageBox(f"Scene loaded successfully from:\n{filepath}", "Scene Loaded", wx.OK | wx.ICON_INFORMATION)
                
            except Exception as e:
                wx.MessageBox(f"Error loading scene:\n{str(e)}", "Load Error", wx.OK | wx.ICON_ERROR)
        
        dialog.Destroy()
    
    def save_scene(self):
        """Save the current scene to a JSON file."""
        if not hasattr(self, '_current_scene_file') or not self._current_scene_file:
            self.save_scene_as()
        else:
            self._save_scene_to_file(self._current_scene_file)
    
    def save_scene_as(self):
        """Save the current scene to a new JSON file."""
        wildcard = "Scene files (*.json)|*.json|All files (*.*)|*.*"
        dialog = wx.FileDialog(self, "Save Scene As", wildcard=wildcard, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        
        if dialog.ShowModal() == wx.ID_OK:
            filepath = dialog.GetPath()
            
            # Ensure .json extension
            if not filepath.lower().endswith('.json'):
                filepath += '.json'
            
            self._save_scene_to_file(filepath)
            self._current_scene_file = filepath
        
        dialog.Destroy()
    
    def _save_scene_to_file(self, filepath: str):
        """Internal method to save scene data to a file."""
        try:
            # Collect all scene data
            scene_data = {
                "version": "1.0",
                "created": time.strftime("%Y-%m-%d %H:%M:%S"),
                "sphere_data": self.sphere.save_scene_to_dict(),
                "canvas_data": self.canvas.save_canvas_scene_to_dict()
            }
            
            # Save to file
            with open(filepath, 'w') as f:
                json.dump(scene_data, f, indent=2)
            
            wx.MessageBox(f"Scene saved successfully to:\n{filepath}", 
"Scene Saved", wx.OK | wx.ICON_INFORMATION)
            
        except Exception as e:
            wx.MessageBox(f"Error saving scene:\n{str(e)}", "Save Error", wx.OK | wx.ICON_ERROR)
    
    # ==================== END FILE MENU METHODS ====================
    
    # ==================== SHAPES MENU METHODS ====================
    
    def add_dot_shape(self):
        """Add a dot shape to the scene."""
        dialog = wx.TextEntryDialog(self, "Enter position (x,y,z):", "Add Dot", "0,0,0")
        if dialog.ShowModal() == wx.ID_OK:
            try:
                coords = [float(x.strip()) for x in dialog.GetValue().split(',')]
                if len(coords) == 3:
                    shape_id = self.sphere.create_dot(coords[0], coords[1], coords[2])
                    wx.MessageBox(f"Dot added with ID: {shape_id}", "Shape Added", wx.OK | wx.ICON_INFORMATION)
                    self.canvas.Refresh()
                else:
                    wx.MessageBox("Please enter exactly 3 coordinates (x,y,z)", "Invalid Input", wx.OK | wx.ICON_ERROR)
            except ValueError:
                wx.MessageBox("Please enter valid numbers", "Invalid Input", wx.OK | wx.ICON_ERROR)
        dialog.Destroy()
    
    def add_line_shape(self):
        """Add a line shape to the scene."""
        dialog = wx.TextEntryDialog(self, "Enter start and end points (x1,y1,z1,x2,y2,z2):", "Add Line", "0,0,0,1,1,1")
        if dialog.ShowModal() == wx.ID_OK:
            try:
                coords = [float(x.strip()) for x in dialog.GetValue().split(',')]
                if len(coords) == 6:
                    start = np.array(coords[:3])
                    end = np.array(coords[3:])
                    shape_id = self.sphere.create_line(start, end)
                    wx.MessageBox(f"Line added with ID: {shape_id}", "Shape Added", wx.OK | wx.ICON_INFORMATION)
                    self.canvas.Refresh()
                else:
                    wx.MessageBox("Please enter exactly 6 coordinates (x1,y1,z1,x2,y2,z2)", "Invalid Input", wx.OK | wx.ICON_ERROR)
            except ValueError:
                wx.MessageBox("Please enter valid numbers", "Invalid Input", wx.OK | wx.ICON_ERROR)
        dialog.Destroy()
    
    def add_bezier_curve_shape(self):
        """Add a Bezier curve shape to the scene."""
        dialog = wx.TextEntryDialog(self, "Enter 4 control points (x1,y1,z1,x2,y2,z2,x3,y3,z3,x4,y4,z4):", 
                                   "Add Bezier Curve", "0,0,0,0.33,1,0,0.67,1,0,1,0,0")
        if dialog.ShowModal() == wx.ID_OK:
            try:
                coords = [float(x.strip()) for x in dialog.GetValue().split(',')]
                if len(coords) == 12:
                    control_points = [np.array(coords[i:i+3]) for i in range(0, 12, 3)]
                    shape_id = self.sphere.create_bezier_curve(control_points)
                    wx.MessageBox(f"Bezier curve added with ID: {shape_id}", "Shape Added", wx.OK | wx.ICON_INFORMATION)
                    self.canvas.Refresh()
                else:
                    wx.MessageBox("Please enter exactly 12 coordinates for 4 control points", "Invalid Input", wx.OK | wx.ICON_ERROR)
            except ValueError:
                wx.MessageBox("Please enter valid numbers", "Invalid Input", wx.OK | wx.ICON_ERROR)
        dialog.Destroy()
    
    def add_plane_shape(self):
        """Add a plane shape to the scene."""
        dialog = wx.TextEntryDialog(self, "Enter position and size (x,y,z,width,height):", "Add Plane", "0,0,0,2,2")
        if dialog.ShowModal() == wx.ID_OK:
            try:
                values = [float(x.strip()) for x in dialog.GetValue().split(',')]
                if len(values) == 5:
                    shape_id = self.sphere.create_plane(values[0], values[1], values[2], values[3], values[4])
                    wx.MessageBox(f"Plane added with ID: {shape_id}", "Shape Added", wx.OK | wx.ICON_INFORMATION)
                    self.canvas.Refresh()
                else:
                    wx.MessageBox("Please enter exactly 5 values (x,y,z,width,height)", "Invalid Input", wx.OK | wx.ICON_ERROR)
            except ValueError:
                wx.MessageBox("Please enter valid numbers", "Invalid Input", wx.OK | wx.ICON_ERROR)
        dialog.Destroy()
    
    def add_cube_shape(self):
        """Add a cube shape to the scene."""
        dialog = wx.TextEntryDialog(self, "Enter position and size (x,y,z,size):", "Add Cube", "0,0,0,1")
        if dialog.ShowModal() == wx.ID_OK:
            try:
                values = [float(x.strip()) for x in dialog.GetValue().split(',')]
                if len(values) == 4:
                    shape_id = self.sphere.create_cube(values[0], values[1], values[2], values[3])
                    wx.MessageBox(f"Cube added with ID: {shape_id}", "Shape Added", wx.OK | wx.ICON_INFORMATION)
                    self.canvas.Refresh()
                else:
                    wx.MessageBox("Please enter exactly 4 values (x,y,z,size)", "Invalid Input", wx.OK | wx.ICON_ERROR)
            except ValueError:
                wx.MessageBox("Please enter valid numbers", "Invalid Input", wx.OK | wx.ICON_ERROR)
        dialog.Destroy()
    
    def add_sphere_shape(self):
        """Add a sphere shape to the scene."""
        dialog = wx.TextEntryDialog(self, "Enter position and radius (x,y,z,radius):", "Add Sphere", "0,0,0,0.5")
        if dialog.ShowModal() == wx.ID_OK:
            try:
                values = [float(x.strip()) for x in dialog.GetValue().split(',')]
                if len(values) == 4:
                    shape_id = self.sphere.create_sphere_shape(values[0], values[1], values[2], values[3])
                    wx.MessageBox(f"Sphere added with ID: {shape_id}", "Shape Added", wx.OK | wx.ICON_INFORMATION)
                    self.canvas.Refresh()
                else:
                    wx.MessageBox("Please enter exactly 4 values (x,y,z,radius)", "Invalid Input", wx.OK | wx.ICON_ERROR)
            except ValueError:
                wx.MessageBox("Please enter valid numbers", "Invalid Input", wx.OK | wx.ICON_ERROR)
        dialog.Destroy()
    
    def add_cylinder_shape(self):
        """Add a cylinder shape to the scene."""
        dialog = wx.TextEntryDialog(self, "Enter position, radius and height (x,y,z,radius,height):", "Add Cylinder", "0,0,0,0.5,2")
        if dialog.ShowModal() == wx.ID_OK:
            try:
                values = [float(x.strip()) for x in dialog.GetValue().split(',')]
                if len(values) == 5:
                    shape_id = self.sphere.create_cylinder(values[0], values[1], values[2], values[3], values[4])
                    wx.MessageBox(f"Cylinder added with ID: {shape_id}", "Shape Added", wx.OK | wx.ICON_INFORMATION)
                    self.canvas.Refresh()
                else:
                    wx.MessageBox("Please enter exactly 5 values (x,y,z,radius,height)", "Invalid Input", wx.OK | wx.ICON_ERROR)
            except ValueError:
                wx.MessageBox("Please enter valid numbers", "Invalid Input", wx.OK | wx.ICON_ERROR)
        dialog.Destroy()
    
    def list_all_shapes(self):
        """List all shapes in the scene."""
        shapes = self.sphere.get_all_shapes()
        if not shapes:
            wx.MessageBox("No shapes in the scene.", "Shapes List", wx.OK | wx.ICON_INFORMATION)
            return
        
        info = f"Shapes in scene ({len(shapes)} total):\n\n"
        for shape in shapes:
            info += f"• {shape.name} ({shape.__class__.__name__})\n"
            info += f"  ID: {shape.id}\n"
            info += f"  Position: [{shape.position[0]:.2f}, {shape.position[1]:.2f}, {shape.position[2]:.2f}]\n"
            info += f"  Visible: {'Yes' if shape.visible else 'No'}\n\n"
        
        wx.MessageBox(info, "Shapes List", wx.OK | wx.ICON_INFORMATION)
    
    def clear_all_shapes(self):
        """Clear all shapes from the scene."""
        shapes = self.sphere.get_all_shapes()
        if not shapes:
            wx.MessageBox("No shapes to clear.", "Clear Shapes", wx.OK | wx.ICON_INFORMATION)
            return
        
        result = wx.MessageBox(f"This will remove all {len(shapes)} shapes. Continue?", 
                              "Clear All Shapes", wx.YES_NO | wx.ICON_QUESTION)
        if result == wx.YES:
            self.sphere.shapes.clear()
            self.canvas.Refresh()
            wx.MessageBox("All shapes cleared.", "Shapes Cleared", wx.OK | wx.ICON_INFORMATION)
    
    # ==================== SCREENS MENU METHODS ====================
    
    def add_2d_screen(self):
        """Add a 2D screen positioned in 3D space."""
        # First, show available cameras
        cameras = self.sphere.get_all_cameras()
        camera_choices = [f"{cam.name} ({cam.id[:8]})" for cam in cameras]
        
        dialog = wx.SingleChoiceDialog(self, "Select camera for the screen:", "Choose Camera", camera_choices)
        if dialog.ShowModal() == wx.ID_OK:
            selected_camera = cameras[dialog.GetSelection()]
            
            # Get screen position and size
            pos_dialog = wx.TextEntryDialog(self, "Enter screen position and size (x,y,z,width,height):", 
                                          "Add 2D Screen", "3,0,0,2,1.5")
            if pos_dialog.ShowModal() == wx.ID_OK:
                try:
                    values = [float(x.strip()) for x in pos_dialog.GetValue().split(',')]
                    if len(values) == 5:
                        screen_id = self.sphere.create_2d_screen(values[0], values[1], values[2], 
                                                               values[3], values[4], selected_camera.id)
                        wx.MessageBox(f"2D Screen added with ID: {screen_id}", "Screen Added", wx.OK | wx.ICON_INFORMATION)
                        self.canvas.Refresh()
                    else:
                        wx.MessageBox("Please enter exactly 5 values (x,y,z,width,height)", "Invalid Input", wx.OK | wx.ICON_ERROR)
                except ValueError:
                    wx.MessageBox("Please enter valid numbers", "Invalid Input", wx.OK | wx.ICON_ERROR)
            pos_dialog.Destroy()
        dialog.Destroy()
    
    def add_overlay_screen(self):
        """Add an overlay screen on the main view."""
        # First, show available cameras
        cameras = self.sphere.get_all_cameras()
        camera_choices = [f"{cam.name} ({cam.id[:8]})" for cam in cameras]
        
        dialog = wx.SingleChoiceDialog(self, "Select camera for the overlay screen:", "Choose Camera", camera_choices)
        if dialog.ShowModal() == wx.ID_OK:
            selected_camera = cameras[dialog.GetSelection()]
            
            # Get overlay position and size
            pos_dialog = wx.TextEntryDialog(self, "Enter overlay position and size (x,y,width,height) [0-1 normalized]:", 
                                          "Add Overlay Screen", "0.1,0.1,0.3,0.3")
            if pos_dialog.ShowModal() == wx.ID_OK:
                try:
                    values = [float(x.strip()) for x in pos_dialog.GetValue().split(',')]
                    if len(values) == 4:
                        screen_id = self.sphere.create_overlay_screen(values[0], values[1], 
                                                                    values[2], values[3], selected_camera.id)
                        wx.MessageBox(f"Overlay Screen added with ID: {screen_id}", "Screen Added", wx.OK | wx.ICON_INFORMATION)
                        self.canvas.Refresh()
                    else:
                        wx.MessageBox("Please enter exactly 4 values (x,y,width,height)", "Invalid Input", wx.OK | wx.ICON_ERROR)
                except ValueError:
                    wx.MessageBox("Please enter valid numbers", "Invalid Input", wx.OK | wx.ICON_ERROR)
            pos_dialog.Destroy()
        dialog.Destroy()
    
    def add_camera(self):
        """Add a new camera to the scene."""
        dialog = wx.TextEntryDialog(self, "Enter camera position and target (x,y,z,target_x,target_y,target_z):", 
                                   "Add Camera", "0,0,5,0,0,0")
        if dialog.ShowModal() == wx.ID_OK:
            try:
                values = [float(x.strip()) for x in dialog.GetValue().split(',')]
                if len(values) == 6:
                    camera_id = self.sphere.create_camera(values[0], values[1], values[2], 
                                                        values[3], values[4], values[5])
                    wx.MessageBox(f"Camera added with ID: {camera_id}", "Camera Added", wx.OK | wx.ICON_INFORMATION)
                else:
                    wx.MessageBox("Please enter exactly 6 values (x,y,z,target_x,target_y,target_z)", "Invalid Input", wx.OK | wx.ICON_ERROR)
            except ValueError:
                wx.MessageBox("Please enter valid numbers", "Invalid Input", wx.OK | wx.ICON_ERROR)
        dialog.Destroy()
    
    def list_cameras(self):
        """List all cameras in the scene."""
        cameras = self.sphere.get_all_cameras()
        if not cameras:
            wx.MessageBox("No cameras in the scene.", "Cameras List", wx.OK | wx.ICON_INFORMATION)
            return
        
        info = f"Cameras in scene ({len(cameras)} total):\n\n"
        for camera in cameras:
            info += f"• {camera.name} ({camera.type.value})\n"
            info += f"  ID: {camera.id}\n"
            info += f"  Position: [{camera.position[0]:.2f}, {camera.position[1]:.2f}, {camera.position[2]:.2f}]\n"
            info += f"  Target: [{camera.target[0]:.2f}, {camera.target[1]:.2f}, {camera.target[2]:.2f}]\n"
            info += f"  FOV: {camera.fov:.1f}°\n\n"
        
        # Add step-into functionality
        info += "\nDouble-click a camera name to step into its view."
        
        # Show dialog with step-into option
        camera_choices = [f"{cam.name} ({cam.id[:8]})" for cam in cameras]
        choice_dialog = wx.SingleChoiceDialog(self, info + "\n\nSelect a camera to step into its view:", 
                                            "Cameras List", camera_choices)
        if choice_dialog.ShowModal() == wx.ID_OK:
            selected_camera = cameras[choice_dialog.GetSelection()]
            # Create a temporary screen to step into
            temp_screen = Screen()
            temp_screen.camera_id = selected_camera.id
            if self.sphere.step_into_screen(temp_screen.id, self.canvas):
                # Manually set the camera since we're not using a real screen
                direction = selected_camera.target - selected_camera.position
                distance = np.linalg.norm(direction)
                self.canvas.camera_distance = distance
                
                direction_norm = direction / distance if distance > 0 else np.array([0, 0, -1])
                pitch = math.degrees(math.asin(-direction_norm[1]))
                yaw = math.degrees(math.atan2(direction_norm[0], -direction_norm[2]))
                
                self.canvas.camera_rotation_x = pitch
                self.canvas.camera_rotation_y = yaw
                self.canvas.camera_position = -selected_camera.position
                self.canvas.Refresh()
                
                wx.MessageBox(f"Stepped into camera: {selected_camera.name}", "Camera View", wx.OK | wx.ICON_INFORMATION)
        choice_dialog.Destroy()
    
    def list_all_screens(self):
        """List all screens in the scene."""
        screens = self.sphere.get_all_screens()
        if not screens:
            wx.MessageBox("No screens in the scene.", "Screens List", wx.OK | wx.ICON_INFORMATION)
            return
        
        info = f"Screens in scene ({len(screens)} total):\n\n"
        for screen in screens:
            info += f"• {screen.name} ({screen.type.value})\n"
            info += f"  ID: {screen.id}\n"
            if screen.type == ScreenType.SCREEN_2D:
                info += f"  Position: [{screen.position[0]:.2f}, {screen.position[1]:.2f}, {screen.position[2]:.2f}]\n"
                info += f"  Size: {screen.size[0]:.1f} x {screen.size[1]:.1f}\n"
            else:
                info += f"  Overlay Position: [{screen.overlay_position[0]:.2f}, {screen.overlay_position[1]:.2f}]\n"
                info += f"  Overlay Size: {screen.overlay_size[0]:.2f} x {screen.overlay_size[1]:.2f}\n"
            info += f"  Camera: {screen.camera_id[:8] if screen.camera_id else 'None'}\n"
            info += f"  Visible: {'Yes' if screen.visible else 'No'}\n\n"
        
        # Add step-into functionality
        screen_choices = [f"{screen.name} ({screen.id[:8]})" for screen in screens]
        choice_dialog = wx.SingleChoiceDialog(self, info + "\n\nSelect a screen to step into its view:", 
                                            "Screens List", screen_choices)
        if choice_dialog.ShowModal() == wx.ID_OK:
            selected_screen = screens[choice_dialog.GetSelection()]
            if self.sphere.step_into_screen(selected_screen.id, self.canvas):
                wx.MessageBox(f"Stepped into screen: {selected_screen.name}", "Screen View", wx.OK | wx.ICON_INFORMATION)
            else:
                wx.MessageBox("Could not step into screen (no camera assigned?)", "Error", wx.OK | wx.ICON_ERROR)
        choice_dialog.Destroy()
    
    def clear_all_screens(self):
        """Clear all screens from the scene."""
        screens = self.sphere.get_all_screens()
        if not screens:
            wx.MessageBox("No screens to clear.", "Clear Screens", wx.OK | wx.ICON_INFORMATION)
            return
        
        result = wx.MessageBox(f"This will remove all {len(screens)} screens. Continue?", 
                              "Clear All Screens", wx.YES_NO | wx.ICON_QUESTION)
        if result == wx.YES:
            self.sphere.screens.clear()
            self.canvas.Refresh()
            wx.MessageBox("All screens cleared.", "Screens Cleared", wx.OK | wx.ICON_INFORMATION)
    
    # ==================== END SCREENS MENU METHODS ====================
    
    def update_dynamic_selection_menus(self):
        """Update the dynamic selection menus with current shapes, cameras, and screens."""
        # Clear existing items
        if hasattr(self, 'shapes_selection_menu'):
            # Clear shapes menu
            for item in self.shapes_selection_menu.GetMenuItems():
                self.shapes_selection_menu.DestroyItem(item)
            
            # Add current shapes
            for shape in self.sphere.get_all_shapes():
                item_id = wx.NewId()
                menu_item = self.shapes_selection_menu.AppendRadioItem(item_id, 
                    f"{shape.name} ({shape.__class__.__name__})", 
                    f"Select {shape.name}")
                # Bind event handler
                self.Bind(wx.EVT_MENU, lambda evt, shape_id=shape.id: self._on_select_shape(evt, shape_id), id=item_id)
                # Check if this shape is currently selected
                if self.canvas.selected_object == f"shape_{shape.id}":
                    menu_item.Check(True)
        
        if hasattr(self, 'cameras_selection_menu'):
            # Clear cameras menu
            for item in self.cameras_selection_menu.GetMenuItems():
                self.cameras_selection_menu.DestroyItem(item)
            
            # Add current cameras
            for camera in self.sphere.get_all_cameras():
                item_id = wx.NewId()
                menu_item = self.cameras_selection_menu.AppendRadioItem(item_id, 
                    f"{camera.name} ({camera.type.value})", 
                    f"Select {camera.name}")
                # Bind event handler
                self.Bind(wx.EVT_MENU, lambda evt, camera_id=camera.id: self._on_select_camera(evt, camera_id), id=item_id)
                # Check if this camera is currently selected
                if self.canvas.selected_object == f"camera_{camera.id}":
                    menu_item.Check(True)
        
        if hasattr(self, 'screens_selection_menu'):
            # Clear screens menu
            for item in self.screens_selection_menu.GetMenuItems():
                self.screens_selection_menu.DestroyItem(item)
            
            # Add current screens
            for screen in self.sphere.get_all_screens():
                item_id = wx.NewId()
                menu_item = self.screens_selection_menu.AppendRadioItem(item_id, 
                    f"{screen.name} ({screen.type.value})", 
                    f"Select {screen.name}")
                # Bind event handler
                self.Bind(wx.EVT_MENU, lambda evt, screen_id=screen.id: self._on_select_screen(evt, screen_id), id=item_id)
                # Check if this screen is currently selected
                if self.canvas.selected_object == f"screen_{screen.id}":
                    menu_item.Check(True)
    
    def _on_select_shape(self, event, shape_id):
        """Handle selection of a shape from the dynamic menu."""
        self.canvas.set_selected_object(f"shape_{shape_id}")
        self._uncheck_other_selection_items(f"shape_{shape_id}")
        print(f"DEBUG: Selected shape {shape_id}")
    
    def _on_select_camera(self, event, camera_id):
        """Handle selection of a camera from the dynamic menu."""
        self.canvas.set_selected_object(f"camera_{camera_id}")
        self._uncheck_other_selection_items(f"camera_{camera_id}")
        print(f"DEBUG: Selected camera {camera_id}")
    
    def _on_select_screen(self, event, screen_id):
        """Handle selection of a screen from the dynamic menu."""
        screen = self.sphere.get_screen(screen_id)
        if screen:
            self.canvas.set_selected_object(f"screen_{screen_id}")
            self._uncheck_other_selection_items(f"screen_{screen_id}")
            print(f"DEBUG: Selected screen {screen_id} ({screen.name}) at position {screen.position}")
        else:
            print(f"DEBUG: ERROR - Screen {screen_id} not found!")
    
    def _uncheck_other_selection_items(self, selected_object):
        """Uncheck all other selection items to maintain radio button behavior."""
        # Uncheck traditional selection items
        if hasattr(self, 'sphere_selection_item'):
            self.sphere_selection_item.Check(selected_object == "sphere")
        if hasattr(self, 'cube_selection_item'):
            self.cube_selection_item.Check(selected_object == "cube")
        if hasattr(self, 'screen_selection_item'):
            self.screen_selection_item.Check(selected_object == "screen")
        if hasattr(self, 'none_selection_item'):
            self.none_selection_item.Check(selected_object == "none")
        
        # Update dynamic menu items (they'll be updated on next menu refresh)

    def step_into_screen(self):
        """Allow user to select a screen and step into its camera view."""
        screens = self.sphere.get_all_screens()
        if not screens:
            wx.MessageBox("No screens found in the scene.", "Step Into Screen", wx.OK | wx.ICON_INFORMATION)
            return
        
        # Create list of screen names for selection
        screen_names = [f"{screen.name} ({screen.type.value})" for screen in screens]
        
        dialog = wx.SingleChoiceDialog(self, "Select a screen to step into:", "Step Into Screen", screen_names)
        if dialog.ShowModal() == wx.ID_OK:
            selected_index = dialog.GetSelection()
            selected_screen = screens[selected_index]
            
            # Store original camera state if not already stepped in
            if self.canvas.stepped_in_screen_id is None:
                self.canvas.original_camera_state = {
                    'position': self.canvas.camera_position.copy(),
                    'rotation_x': self.canvas.camera_rotation_x,
                    'rotation_y': self.canvas.camera_rotation_y,
                    'distance': self.canvas.camera_distance
                }
            
            # Step into the selected screen
            success = self.canvas.step_into_screen(selected_screen.id)
            if success:
                wx.MessageBox(f"Stepped into screen: {selected_screen.name}\nUse 'Exit Screen View' to return to normal view.", 
                             "Screen View Active", wx.OK | wx.ICON_INFORMATION)
            else:
                wx.MessageBox(f"Could not step into screen: {selected_screen.name}\nMake sure the screen has a valid camera.", 
                             "Step Into Failed", wx.OK | wx.ICON_ERROR)
        
        dialog.Destroy()

    def exit_screen_view(self):
        """Exit the current screen view and return to normal camera."""
        if self.canvas.stepped_in_screen_id is None:
            wx.MessageBox("Not currently in a screen view.", "Exit Screen View", wx.OK | wx.ICON_INFORMATION)
            return
        
        # Restore original camera state
        success = self.canvas.exit_screen_view()
        if success:
            wx.MessageBox("Returned to normal camera view.", "Exit Screen View", wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox("Error returning to normal view.", "Exit Screen View", wx.OK | wx.ICON_ERROR)

    def add_image_screen(self):
        """Add a screen displaying an image."""
        # File picker dialog
        wildcard = "Image files (*.png;*.jpg;*.jpeg;*.bmp;*.tiff)|*.png;*.jpg;*.jpeg;*.bmp;*.tiff"
        dialog = wx.FileDialog(self, "Choose an image file", wildcard=wildcard, style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        
        if dialog.ShowModal() == wx.ID_OK:
            file_path = dialog.GetPath()
            
            # Position dialog
            pos_dialog = wx.TextEntryDialog(self, "Enter screen position (x,y,z):", "Screen Position", "1,0,1")
            if pos_dialog.ShowModal() == wx.ID_OK:
                try:
                    x, y, z = map(float, pos_dialog.GetValue().split(','))
                    
                    # Create media screen
                    media_screen = MediaScreen(ScreenType.SCREEN_2D, MediaType.IMAGE)
                    media_screen.name = f"Image Screen ({Path(file_path).name})"
                    media_screen.set_position(x, y, z)
                    media_screen.set_size(2.0, 1.5)  # Default size
                    media_screen.camera_id = None  # Media screens don't use cameras
                    
                    # Add the screen first, then load the media (ensures OpenGL context is available)
                    self.sphere.add_screen(media_screen)
                    
                    # Load the image after adding to scene
                    if media_screen.load_media(file_path):
                        wx.MessageBox(f"Added image screen: {media_screen.name}", "Image Screen Added", wx.OK | wx.ICON_INFORMATION)
                    else:
                        wx.MessageBox("Failed to load image file.", "Error", wx.OK | wx.ICON_ERROR)
                        
                except ValueError:
                    wx.MessageBox("Invalid position format. Use x,y,z format.", "Error", wx.OK | wx.ICON_ERROR)
            pos_dialog.Destroy()
        dialog.Destroy()

    def add_video_screen(self):
        """Add a screen displaying a video with sound and playback controls."""
        # File picker dialog
        wildcard = "Video files (*.mp4;*.avi;*.mov;*.mkv;*.webm)|*.mp4;*.avi;*.mov;*.mkv;*.webm"
        dialog = wx.FileDialog(self, "Choose a video file", wildcard=wildcard, style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        
        if dialog.ShowModal() == wx.ID_OK:
            file_path = dialog.GetPath()
            
            # Position dialog
            pos_dialog = wx.TextEntryDialog(self, "Enter screen position (x,y,z):", "Screen Position", "1,0,1")
            if pos_dialog.ShowModal() == wx.ID_OK:
                try:
                    x, y, z = map(float, pos_dialog.GetValue().split(','))
                    
                    # Create media screen
                    media_screen = MediaScreen(ScreenType.SCREEN_2D, MediaType.VIDEO)
                    media_screen.name = f"Video Screen ({Path(file_path).name})"
                    media_screen.set_position(x, y, z)
                    media_screen.set_size(2.0, 1.5)  # Default size
                    media_screen.camera_id = None  # Media screens don't use cameras
                    
                    # Add the screen first, then load the media (ensures OpenGL context is available)
                    self.sphere.add_screen(media_screen)
                    
                    # Load the video after adding to scene
                    print(f"DEBUG: ===== LOADING VIDEO FILE: {file_path} =====")
                    load_result = media_screen.load_media(file_path)
                    print(f"DEBUG: Video load result: {load_result}")
                    print(f"DEBUG: Media screen media_type after load: {media_screen.media_type}")
                    
                    if load_result:
                        # Start video playback automatically
                        print(f"DEBUG: ===== ABOUT TO START VIDEO PLAYBACK =====")
                        media_screen.start_video_playback()
                        print(f"DEBUG: ===== VIDEO PLAYBACK START CALL COMPLETED =====")
                        
                        # Check if audio was successfully loaded
                        has_audio = media_screen.audio_file and os.path.exists(media_screen.audio_file)
                        print(f"DEBUG: Audio file check - has_audio: {has_audio}")
                        audio_status = "✅ With synchronized audio" if has_audio else "⚠️ Video only (no audio track found)"
                        
                        wx.MessageBox(f"Added video screen: {media_screen.name}\n\nStatus: Video is now playing\n{audio_status}\n\nControls:\n• Space Bar: Play/Pause\n• R Key: Restart\n• S Key: Stop\n• Screens Menu: Video controls available\n\nReal-time playback: 1 second video = 1 second real-time\n\nIf you don't hear audio:\n• Check system volume\n• Verify video has audio track\n• Check terminal for debug messages", "Video Screen Added", wx.OK | wx.ICON_INFORMATION)
                    else:
                        wx.MessageBox("Failed to load video file.\n\nPossible issues:\n• Unsupported video format\n• Corrupted file\n• FFmpeg not available\n• File permissions\n\nCheck terminal for detailed error messages.", "Error", wx.OK | wx.ICON_ERROR)
                        
                except ValueError:
                    wx.MessageBox("Invalid position format. Use x,y,z format.", "Error", wx.OK | wx.ICON_ERROR)
            pos_dialog.Destroy()
        dialog.Destroy()

    def add_gif_screen(self):
        """Add a screen displaying an animated GIF."""
        # File picker dialog
        wildcard = "GIF files (*.gif)|*.gif"
        dialog = wx.FileDialog(self, "Choose a GIF file", wildcard=wildcard, style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        
        if dialog.ShowModal() == wx.ID_OK:
            file_path = dialog.GetPath()
            
            # Position dialog
            pos_dialog = wx.TextEntryDialog(self, "Enter screen position (x,y,z):", "Screen Position", "1,0,1")
            if pos_dialog.ShowModal() == wx.ID_OK:
                try:
                    x, y, z = map(float, pos_dialog.GetValue().split(','))
                    
                    # Create media screen
                    media_screen = MediaScreen(ScreenType.SCREEN_2D, MediaType.GIF)
                    media_screen.name = f"GIF Screen ({Path(file_path).name})"
                    media_screen.set_position(x, y, z)
                    media_screen.set_size(2.0, 1.5)  # Default size
                    media_screen.camera_id = None  # Media screens don't use cameras
                    
                    # Add the screen first, then load the media (ensures OpenGL context is available)
                    self.sphere.add_screen(media_screen)
                    
                    # Load the GIF after adding to scene
                    if media_screen.load_media(file_path):
                        wx.MessageBox(f"Added GIF screen: {media_screen.name}", "GIF Screen Added", wx.OK | wx.ICON_INFORMATION)
                    else:
                        wx.MessageBox("Failed to load GIF file.", "Error", wx.OK | wx.ICON_ERROR)
                        
                except ValueError:
                    wx.MessageBox("Invalid position format. Use x,y,z format.", "Error", wx.OK | wx.ICON_ERROR)
            pos_dialog.Destroy()
        dialog.Destroy()
    
    def add_website_screen(self):
        """Add a screen displaying a webpage."""
        if not SELENIUM_AVAILABLE:
            wx.MessageBox("Selenium is not available.\n\nTo use website screens:\n1. Install: pip install selenium\n2. Install Chrome browser\n3. Restart the application", "Website Screen Requirements", wx.OK | wx.ICON_INFORMATION)
            return
        
        # URL input dialog
        url_dialog = wx.TextEntryDialog(self, "Enter website URL:", "Website URL", "https://www.example.com")
        
        if url_dialog.ShowModal() == wx.ID_OK:
            url = url_dialog.GetValue().strip()
            
            # Position dialog
            pos_dialog = wx.TextEntryDialog(self, "Enter screen position (x,y,z):", "Screen Position", "1,0,1")
            if pos_dialog.ShowModal() == wx.ID_OK:
                try:
                    x, y, z = map(float, pos_dialog.GetValue().split(','))
                    
                    # Create media screen
                    media_screen = MediaScreen(ScreenType.SCREEN_2D, MediaType.WEB)
                    
                    # Extract domain name for screen naming
                    try:
                        from urllib.parse import urlparse
                        parsed = urlparse(url)
                        domain = parsed.netloc or "website"
                    except:
                        domain = "website"
                    
                    media_screen.name = f"Website Screen ({domain})"
                    media_screen.set_position(x, y, z)
                    media_screen.set_size(3.2, 1.8)  # 16:9 aspect ratio, larger for readability
                    media_screen.camera_id = None  # Media screens don't use cameras
                    
                    # Add the screen first, then load the website (ensures OpenGL context is available)
                    self.sphere.add_screen(media_screen)
                    
                    # Load the website after adding to scene
                    wx.CallAfter(self._load_website_async, media_screen, url)
                    
                    wx.MessageBox(f"Adding website screen: {media_screen.name}\n\nURL: {url}\n\nNote: The website will load in the background and refresh every 30 seconds.", "Website Screen Added", wx.OK | wx.ICON_INFORMATION)
                        
                except ValueError:
                    wx.MessageBox("Invalid position format. Use x,y,z format.", "Error", wx.OK | wx.ICON_ERROR)
            pos_dialog.Destroy()
        url_dialog.Destroy()
    
    def _load_website_async(self, media_screen, url):
        """Load website in a separate thread to avoid blocking UI."""
        def load_website():
            try:
                if media_screen.load_website(url):
                    wx.CallAfter(lambda: print(f"DEBUG: Website loaded successfully in background: {url}"))
                else:
                    wx.CallAfter(lambda: wx.MessageBox("Failed to load website. Please check the URL and your internet connection.", "Error", wx.OK | wx.ICON_ERROR))
            except Exception as e:
                wx.CallAfter(lambda: wx.MessageBox(f"Error loading website: {e}", "Error", wx.OK | wx.ICON_ERROR))
        
        import threading
        thread = threading.Thread(target=load_website, daemon=True)
        thread.start()


class Sphere3DApp(wx.App):
    """Main application class."""
    
    def OnInit(self):
        print("DEBUG: Sphere3DApp.OnInit() called")
        frame = Sphere3DFrame()
        print("DEBUG: Frame created, about to show")
        frame.Show()
        print("DEBUG: Frame shown, returning True")
        return True

if __name__ == "__main__":
    print("DEBUG: Starting Sphere3DApp")
    app = Sphere3DApp()
    print("DEBUG: App created, starting MainLoop")
    app.MainLoop()
    print("DEBUG: MainLoop ended")
