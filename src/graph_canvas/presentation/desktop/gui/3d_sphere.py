"""
3D Sphere visualization with advanced grid systems, transformations, and visual controls.
Supports longitude/latitude grids, concentric circles, dot particles, and neon-style effects.
"""

import wx
import wx.glcanvas
import math
import numpy as np
from typing import Tuple, Optional, List, Dict
from enum import Enum
import OpenGL.GL as gl
import OpenGL.GLU as glu


class GridType(Enum):
    """Types of grid systems for the sphere."""
    LONGITUDE_LATITUDE = "longitude_latitude"
    CONCENTRIC_CIRCLES = "concentric_circles"
    DOT_PARTICLES = "dot_particles"
    NEON_LINES = "neon_lines"
    WIREFRAME = "wireframe"


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
        self.vector_enabled = False
        self.vector_direction = np.array([1.0, 0.0, 0.0])  # Default: X-axis
        self.vector_length = 2.0  # Length relative to sphere radius
        self.vector_color = np.array([1.0, 0.0, 0.0, 1.0])  # Red RGBA
        self.vector_thickness = 3.0
        
        # Cone properties
        self.cone_enabled = False
        self.cone_length = 3.0  # Length relative to sphere radius
        self.cone_angle = 30.0  # Cone half-angle in degrees
        self.cone_color = np.array([1.0, 1.0, 0.0, 0.3])  # Yellow with transparency
        self.cone_resolution = 16  # Number of sides for cone base
        
        # Pyramid properties
        self.pyramid_enabled = False
        self.pyramid_length = 3.0  # Length relative to sphere radius
        self.pyramid_angle_horizontal = 25.0  # Horizontal half-angle in degrees
        self.pyramid_angle_vertical = 20.0  # Vertical half-angle in degrees
        self.pyramid_color = np.array([0.0, 1.0, 1.0, 0.3])  # Cyan with transparency
        
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
        
        # Geometry data
        self.vertices = []
        self.indices = []
        self.normals = []
        self.texture_coords = []
        
        # Generate initial geometry
        self.generate_sphere_geometry()
        self.generate_wireframe_geometry()
    
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
                self.wireframe_indices.extend([second, second + 1, first + 1])
    
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
        
        # Calculate vector end point
        vector_end = direction * self.vector_length * self.radius
        
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
    
    def render_cone(self):
        """Render cone section with tip at sphere center pointing along vector direction."""
        if not self.cone_enabled:
            return
        
        # Use vector direction for cone axis
        direction = self.vector_direction / np.linalg.norm(self.vector_direction)
        
        # Calculate cone end point
        cone_end = direction * self.cone_length * self.radius
        
        # Calculate cone base radius
        cone_base_radius = self.cone_length * self.radius * math.tan(math.radians(self.cone_angle))
        
        # Create perpendicular vectors for cone base
        if abs(direction[0]) < 0.9:
            perp1 = np.array([0.0, direction[2], -direction[1]])
        else:
            perp1 = np.array([-direction[2], 0.0, direction[0]])
        
        perp1 = perp1 / np.linalg.norm(perp1) * cone_base_radius
        
        # Second perpendicular vector
        perp2 = np.cross(direction, perp1)
        perp2 = perp2 / np.linalg.norm(perp2) * cone_base_radius
        
        # Set cone color and enable blending for transparency
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glColor4f(*self.cone_color)
        
        # Disable lighting for cone (we want uniform color)
        gl.glDisable(gl.GL_LIGHTING)
        
        # Render cone surface as triangles
        gl.glBegin(gl.GL_TRIANGLES)
        
        for i in range(self.cone_resolution):
            angle1 = 2 * math.pi * i / self.cone_resolution
            angle2 = 2 * math.pi * ((i + 1) % self.cone_resolution) / self.cone_resolution
            
            # Points on the cone base circle
            base_point1 = (cone_end + 
                          perp1 * math.cos(angle1) + 
                          perp2 * math.sin(angle1))
            base_point2 = (cone_end + 
                          perp1 * math.cos(angle2) + 
                          perp2 * math.sin(angle2))
            
            # Triangle from tip to base edge
            gl.glVertex3f(0.0, 0.0, 0.0)  # Tip at sphere center
            gl.glVertex3f(base_point1[0], base_point1[1], base_point1[2])
            gl.glVertex3f(base_point2[0], base_point2[1], base_point2[2])
        
        gl.glEnd()
        
        # Render cone outline wireframe for better visibility
        gl.glColor4f(self.cone_color[0], self.cone_color[1], self.cone_color[2], 1.0)  # Solid color for outline
        gl.glLineWidth(2.0)
        
        # Draw lines from tip to base circle
        gl.glBegin(gl.GL_LINES)
        for i in range(0, self.cone_resolution, 2):  # Every other line to avoid clutter
            angle = 2 * math.pi * i / self.cone_resolution
            base_point = (cone_end + 
                         perp1 * math.cos(angle) + 
                         perp2 * math.sin(angle))
            
            gl.glVertex3f(0.0, 0.0, 0.0)  # From tip
            gl.glVertex3f(base_point[0], base_point[1], base_point[2])  # To base
        
        # Draw base circle outline
        for i in range(self.cone_resolution):
            angle1 = 2 * math.pi * i / self.cone_resolution
            angle2 = 2 * math.pi * ((i + 1) % self.cone_resolution) / self.cone_resolution
            
            point1 = (cone_end + 
                     perp1 * math.cos(angle1) + 
                     perp2 * math.sin(angle1))
            point2 = (cone_end + 
                     perp1 * math.cos(angle2) + 
                     perp2 * math.sin(angle2))
            
            gl.glVertex3f(point1[0], point1[1], point1[2])
            gl.glVertex3f(point2[0], point2[1], point2[2])
        
        gl.glEnd()
        
        # Re-enable lighting if it was enabled
        if self.lighting_enabled:
            gl.glEnable(gl.GL_LIGHTING)
        
        gl.glDisable(gl.GL_BLEND)
    
    def render_pyramid(self):
        """Render 4-sided pyramid with tip at sphere center pointing along vector direction."""
        if not self.pyramid_enabled:
            return
        
        # Use vector direction for pyramid axis
        direction = self.vector_direction / np.linalg.norm(self.vector_direction)
        
        # Calculate pyramid end point
        pyramid_end = direction * self.pyramid_length * self.radius
        
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
        half_width = self.pyramid_length * self.radius * math.tan(math.radians(self.pyramid_angle_horizontal))
        half_height = self.pyramid_length * self.radius * math.tan(math.radians(self.pyramid_angle_vertical))
        
        # Calculate the four corners of the pyramid base
        base_corners = [
            pyramid_end + horizontal * half_width + vertical * half_height,    # Top-right
            pyramid_end - horizontal * half_width + vertical * half_height,    # Top-left
            pyramid_end - horizontal * half_width - vertical * half_height,    # Bottom-left
            pyramid_end + horizontal * half_width - vertical * half_height     # Bottom-right
        ]
        
        # Set pyramid color and enable blending for transparency
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glColor4f(*self.pyramid_color)
        
        # Disable lighting for pyramid (we want uniform color)
        gl.glDisable(gl.GL_LIGHTING)
        
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
        
        # Optional: Render base of pyramid (usually not needed for visualization)
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
        gl.glColor4f(self.pyramid_color[0], self.pyramid_color[1], self.pyramid_color[2], 1.0)  # Solid color for outline
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
        
        # Re-enable lighting if it was enabled
        if self.lighting_enabled:
            gl.glEnable(gl.GL_LIGHTING)
        
        gl.glDisable(gl.GL_BLEND)
    
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
        
        # Render cone and pyramid before vector (so vector appears on top)
        self.render_cone()
        self.render_pyramid()
        
        # Always render vector last (on top of everything)
        self.render_vector()
        
        gl.glPopMatrix()
    
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
        self.position = np.array([x, y, z])
    
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
    
    def set_vector_direction(self, x: float, y: float, z: float):
        """Set vector direction (will be normalized)."""
        direction = np.array([x, y, z])
        if np.linalg.norm(direction) > 0:
            self.vector_direction = direction
    
    def set_vector_length(self, length: float):
        """Set vector length relative to sphere radius."""
        self.vector_length = max(0.1, length)
    
    def set_vector_color(self, color: Tuple[float, float, float, float]):
        """Set vector color (RGBA)."""
        self.vector_color = np.array(color)
    
    def set_vector_thickness(self, thickness: float):
        """Set vector line thickness."""
        self.vector_thickness = max(1.0, thickness)
    
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
        
        # Camera settings
        self.camera_distance = 5.0
        self.camera_rotation_x = 0.0
        self.camera_rotation_y = 0.0
        
        # Mouse interaction
        self.last_mouse_pos = None
        self.mouse_dragging = False
        
        # Bind events
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_mouse_up)
        self.Bind(wx.EVT_MOTION, self.on_mouse_motion)
        self.Bind(wx.EVT_MOUSEWHEEL, self.on_mouse_wheel)
    
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
        
        self.init_gl = True
    
    def setup_viewport(self):
        """Set up the viewport and projection matrix."""
        size = self.GetSize()
        gl.glViewport(0, 0, size.width, size.height)
        
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        
        aspect_ratio = size.width / size.height if size.height > 0 else 1.0
        glu.gluPerspective(45.0, aspect_ratio, 0.1, 100.0)
        
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()
    
    def setup_camera(self):
        """Set up the camera view."""
        # Position camera
        gl.glTranslatef(0.0, 0.0, -self.camera_distance)
        
        # Apply camera rotations
        gl.glRotatef(self.camera_rotation_x, 1.0, 0.0, 0.0)
        gl.glRotatef(self.camera_rotation_y, 0.0, 1.0, 0.0)
    
    def on_paint(self, event):
        """Handle paint events."""
        self.SetCurrent(self.context)
        self.init_opengl()
        
        # Clear buffers
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        
        # Set up viewport and camera
        self.setup_viewport()
        self.setup_camera()
        
        # Render the sphere
        self.sphere.render()
        
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
        
        # Update camera rotation
        self.camera_rotation_y += dx * 0.5
        self.camera_rotation_x += dy * 0.5
        
        # Clamp vertical rotation
        self.camera_rotation_x = max(-90, min(90, self.camera_rotation_x))
        
        self.last_mouse_pos = current_pos
        self.Refresh()
    
    def on_mouse_wheel(self, event):
        """Handle mouse wheel for zooming."""
        delta = event.GetWheelRotation()
        zoom_factor = 1.1 if delta > 0 else 0.9
        
        self.camera_distance *= zoom_factor
        self.camera_distance = max(1.0, min(20.0, self.camera_distance))
        
        self.Refresh()
    
    def get_sphere_renderer(self) -> SphereRenderer:
        """Get the sphere renderer for external control."""
        return self.sphere


class Sphere3DFrame(wx.Frame):
    """Main frame for 3D sphere visualization with menu controls."""
    
    def __init__(self):
        super().__init__(None, title="3D Sphere Visualization", size=(1000, 800))
        
        # Create the OpenGL canvas
        self.canvas = Sphere3DCanvas(self)
        self.sphere = self.canvas.get_sphere_renderer()
        
        # Create menu bar
        self.create_menu_bar()
        
        # Set up layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.EXPAND)
        self.SetSizer(sizer)
        
        # Center the frame
        self.Center()
    
    def create_menu_bar(self):
        """Create the menu bar with all sphere controls."""
        menubar = wx.MenuBar()
        
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
        grid_menu.AppendCheckItem(wx.ID_ANY, "Longitude/Latitude Grid", "Toggle longitude/latitude grid")
        grid_menu.AppendCheckItem(wx.ID_ANY, "Concentric Circles", "Toggle concentric circles")
        grid_menu.AppendCheckItem(wx.ID_ANY, "Dot Particles", "Toggle dot particles")
        grid_menu.AppendCheckItem(wx.ID_ANY, "Neon Lines", "Toggle neon-style grid lines")
        grid_menu.AppendCheckItem(wx.ID_ANY, "Wireframe", "Toggle wireframe mode")
        
        grid_menu.AppendSeparator()
        
        # Grid colors submenu
        grid_colors_menu = wx.Menu()
        grid_colors_menu.Append(wx.ID_ANY, "Longitude/Latitude Color...", "Set longitude/latitude grid color")
        grid_colors_menu.Append(wx.ID_ANY, "Concentric Circles Color...", "Set concentric circles color")
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
        grid_params_menu.Append(wx.ID_ANY, "Set Wireframe Density...", "Set wireframe mesh density")
        grid_menu.AppendSubMenu(grid_params_menu, "Grid Parameters")
        
        menubar.Append(grid_menu, "Grids")
        
        # Vector menu
        vector_menu = wx.Menu()
        vector_menu.AppendCheckItem(wx.ID_ANY, "Show Vector", "Toggle vector visibility")
        vector_menu.AppendCheckItem(wx.ID_ANY, "Show Cone", "Toggle cone visibility")
        vector_menu.AppendCheckItem(wx.ID_ANY, "Show Pyramid", "Toggle pyramid visibility")
        vector_menu.AppendSeparator()
        
        # Vector properties submenu
        vector_props_menu = wx.Menu()
        vector_props_menu.Append(wx.ID_ANY, "Set Direction...", "Set vector direction (x,y,z)")
        vector_props_menu.Append(wx.ID_ANY, "Set Length...", "Set vector length")
        vector_props_menu.Append(wx.ID_ANY, "Set Color...", "Set vector color")
        vector_props_menu.Append(wx.ID_ANY, "Set Thickness...", "Set vector line thickness")
        vector_menu.AppendSubMenu(vector_props_menu, "Vector Properties")
        
        # Cone properties submenu
        cone_props_menu = wx.Menu()
        cone_props_menu.Append(wx.ID_ANY, "Set Cone Length...", "Set cone length")
        cone_props_menu.Append(wx.ID_ANY, "Set Cone Angle...", "Set cone half-angle in degrees")
        cone_props_menu.Append(wx.ID_ANY, "Set Cone Color...", "Set cone color")
        cone_props_menu.Append(wx.ID_ANY, "Set Cone Resolution...", "Set cone smoothness")
        vector_menu.AppendSubMenu(cone_props_menu, "Cone Properties")
        
        # Pyramid properties submenu
        pyramid_props_menu = wx.Menu()
        pyramid_props_menu.Append(wx.ID_ANY, "Set Pyramid Length...", "Set pyramid length")
        pyramid_props_menu.Append(wx.ID_ANY, "Set Horizontal Angle...", "Set pyramid horizontal half-angle")
        pyramid_props_menu.Append(wx.ID_ANY, "Set Vertical Angle...", "Set pyramid vertical half-angle")
        pyramid_props_menu.Append(wx.ID_ANY, "Set Pyramid Color...", "Set pyramid color")
        vector_menu.AppendSubMenu(pyramid_props_menu, "Pyramid Properties")
        
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
        view_menu.AppendCheckItem(wx.ID_ANY, "Wireframe Mode", "Toggle wireframe rendering mode")
        view_menu.AppendCheckItem(wx.ID_ANY, "Enable Lighting", "Toggle lighting on/off")
        
        menubar.Append(view_menu, "View")
        
        self.SetMenuBar(menubar)
        
        # Bind menu events
        self.Bind(wx.EVT_MENU, self.on_menu_event)
        
        # Update initial menu states
        self.update_menu_states()
    
    def on_menu_event(self, event):
        """Handle menu events."""
        menu_item = self.GetMenuBar().FindItemById(event.GetId())
        if not menu_item:
            return
        
        label = menu_item.GetItemLabelText()
        
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
        elif label == "Show Cone":
            self.sphere.toggle_cone()
            self.canvas.Refresh()
        elif label == "Show Pyramid":
            self.sphere.toggle_pyramid()
            self.canvas.Refresh()
        elif label == "Set Direction...":
            self.set_vector_direction()
        elif label == "Set Length...":
            self.set_vector_length()
        elif label == "Set Color...":
            self.set_vector_color()
        elif label == "Set Thickness...":
            self.set_vector_thickness()
        
        # Cone controls
        elif label == "Set Cone Length...":
            self.set_cone_length()
        elif label == "Set Cone Angle...":
            self.set_cone_angle()
        elif label == "Set Cone Color...":
            print("DEBUG: Cone color menu clicked")
            self.set_cone_color()
        elif label == "Set Cone Resolution...":
            self.set_cone_resolution()
        
        # Pyramid controls
        elif label == "Set Pyramid Length...":
            self.set_pyramid_length()
        elif label == "Set Horizontal Angle...":
            self.set_pyramid_horizontal_angle()
        elif label == "Set Vertical Angle...":
            self.set_pyramid_vertical_angle()
        elif label == "Set Pyramid Color...":
            print("DEBUG: Pyramid color menu clicked")
            self.set_pyramid_color()
        
        # Vector presets
        elif label == "X-Axis (1,0,0)":
            self.sphere.set_vector_direction(1, 0, 0)
            self.canvas.Refresh()
        elif label == "Y-Axis (0,1,0)":
            self.sphere.set_vector_direction(0, 1, 0)
            self.canvas.Refresh()
        elif label == "Z-Axis (0,0,1)":
            self.sphere.set_vector_direction(0, 0, 1)
            self.canvas.Refresh()
        elif label == "-X-Axis (-1,0,0)":
            self.sphere.set_vector_direction(-1, 0, 0)
            self.canvas.Refresh()
        elif label == "-Y-Axis (0,-1,0)":
            self.sphere.set_vector_direction(0, -1, 0)
            self.canvas.Refresh()
        elif label == "-Z-Axis (0,0,-1)":
            self.sphere.set_vector_direction(0, 0, -1)
            self.canvas.Refresh()
        elif label == "Diagonal (1,1,1)":
            self.sphere.set_vector_direction(1, 1, 1)
            self.canvas.Refresh()
        elif label == "Random Direction":
            self.set_random_vector_direction()
        
        # View controls
        elif label == "Reset Camera":
            self.canvas.camera_distance = 5.0
            self.canvas.camera_rotation_x = 0.0
            self.canvas.camera_rotation_y = 0.0
            self.canvas.Refresh()
        elif label == "Wireframe Mode":
            self.sphere.wireframe_mode = not self.sphere.wireframe_mode
            self.canvas.Refresh()
        elif label == "Enable Lighting":
            self.sphere.toggle_lighting()
            self.canvas.Refresh()
        
        # Update menu states after any change
        self.update_menu_states()
    
    def update_menu_states(self):
        """Update the checked state of menu items."""
        menubar = self.GetMenuBar()
        
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
                    elif label == "Show Vector":
                        item.Check(self.sphere.vector_enabled)
                    elif label == "Show Cone":
                        item.Check(self.sphere.cone_enabled)
                    elif label == "Show Pyramid":
                        item.Check(self.sphere.pyramid_enabled)
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
        dialog = wx.NumberEntryDialog(self, "Enter transparency (0-100):", "Transparency:", "Set Transparency", current_alpha, 0, 100)
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
                    self.sphere.set_position(*coords)
                    self.canvas.Refresh()
            except ValueError:
                wx.MessageBox("Invalid position format. Use: x,y,z", "Error", wx.OK | wx.ICON_ERROR)
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
                wx.MessageBox("Invalid scale format. Use: sx,sy,sz", "Error", wx.OK | wx.ICON_ERROR)
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
        dialog = wx.NumberEntryDialog(self, "Enter number of concentric rings:", "Rings:", "Concentric Rings", self.sphere.concentric_rings, 3, 20)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.concentric_rings = dialog.GetValue()
            self.canvas.Refresh()
        dialog.Destroy()
    
    def set_dot_density(self):
        """Set dot particle density."""
        dialog = wx.NumberEntryDialog(self, "Enter dot particle density:", "Density:", "Dot Density", self.sphere.dot_density, 50, 1000)
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
                wx.MessageBox("Invalid direction format. Use: x,y,z", "Error", wx.OK | wx.ICON_ERROR)
        dialog.Destroy()
    
    def set_vector_length(self):
        """Set vector length with input dialog."""
        current_length = self.sphere.vector_length
        dialog = wx.NumberEntryDialog(self, "Enter vector length (relative to sphere radius):", "Length:", "Vector Length", int(current_length * 10), 1, 100)
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
    
    def set_cone_length(self):
        """Set cone length with input dialog."""
        current_length = self.sphere.cone_length
        dialog = wx.NumberEntryDialog(self, "Enter cone length (relative to sphere radius):", "Length:", "Cone Length", int(current_length * 10), 5, 100)
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
        """Set cone color with color dialog and transparency."""
        print("DEBUG: set_cone_color method called")
        try:
            color_data = wx.ColourData()
            current_color = self.sphere.cone_color[:3] * 255
            color_data.SetColour(wx.Colour(int(current_color[0]), int(current_color[1]), int(current_color[2])))
            
            dialog = wx.ColourDialog(self, color_data)
            if dialog.ShowModal() == wx.ID_OK:
                color = dialog.GetColourData().GetColour()
                
                # Ask for transparency
                alpha_dialog = wx.NumberEntryDialog(self, "Enter transparency (0-100):", "Transparency:", "Cone Transparency", int(self.sphere.cone_color[3] * 100), 0, 100)
                if alpha_dialog.ShowModal() == wx.ID_OK:
                    alpha = alpha_dialog.GetValue() / 100.0
                    new_color = (color.Red() / 255.0, color.Green() / 255.0, color.Blue() / 255.0, alpha)
                    self.sphere.set_cone_color(new_color)
                    self.canvas.Refresh()
                alpha_dialog.Destroy()
            dialog.Destroy()
        except Exception as e:
            wx.MessageBox(f"Error setting cone color: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
    
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
        """Set pyramid color with color dialog and transparency."""
        print("DEBUG: set_pyramid_color method called")
        try:
            color_data = wx.ColourData()
            current_color = self.sphere.pyramid_color[:3] * 255
            color_data.SetColour(wx.Colour(int(current_color[0]), int(current_color[1]), int(current_color[2])))
            
            dialog = wx.ColourDialog(self, color_data)
            if dialog.ShowModal() == wx.ID_OK:
                color = dialog.GetColourData().GetColour()
                
                # Ask for transparency
                alpha_dialog = wx.NumberEntryDialog(self, "Enter transparency (0-100):", "Transparency:", "Pyramid Transparency", int(self.sphere.pyramid_color[3] * 100), 0, 100)
                if alpha_dialog.ShowModal() == wx.ID_OK:
                    alpha = alpha_dialog.GetValue() / 100.0
                    new_color = (color.Red() / 255.0, color.Green() / 255.0, color.Blue() / 255.0, alpha)
                    self.sphere.set_pyramid_color(new_color)
                    self.canvas.Refresh()
                alpha_dialog.Destroy()
            dialog.Destroy()
        except Exception as e:
            wx.MessageBox(f"Error setting pyramid color: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)


class Sphere3DApp(wx.App):
    """Main application class."""
    
    def OnInit(self):
        frame = Sphere3DFrame()
        frame.Show()
        return True


if __name__ == "__main__":
    app = Sphere3DApp()
    app.MainLoop()
