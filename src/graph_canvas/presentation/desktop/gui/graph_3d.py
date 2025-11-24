"""
3D Sphere visualization with advanced grid systems, transformations, and 
visual controls.
Supports longitude/latitude grids, concentric circles, dot particles, and 
neon-style effects.
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
        self.wireframe_resolution = 16  # Separate resolution for 
wireframe
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
        self.vector_direction = np.array([1.0, 0.0, 0.0])  # Default: 
X-axis
        self.vector_length = 2.0  # Length relative to sphere radius
        self.vector_color = np.array([1.0, 0.0, 0.0, 1.0])  # Red RGBA
        self.vector_thickness = 3.0
        
        # Vector orientation properties
        self.vector_roll = 0.0  # Roll rotation around the vector axis 
(camera orientation)
        self.vector_orientation_enabled = False  # Show orientation vector 
at tail of main vector
        self.vector_orientation_length = 0.8  # Length of orientation 
vector relative to main vector
        self.vector_orientation_color = np.array([0.0, 1.0, 0.0, 1.0])  # 
Green RGBA
        self.vector_orientation_thickness = 2.0
        
        # Cone properties
        self.cone_enabled = False
        self.cone_length = 3.0  # Length relative to sphere radius
        self.cone_infinite = False  # Whether cone extends infinitely
        self.cone_angle = 30.0  # Cone half-angle in degrees
        self.cone_color = np.array([1.0, 1.0, 0.0, 0.3])  # Yellow with 
transparency
        self.cone_resolution = 16  # Number of sides for cone base
        
        # Pyramid properties
        self.pyramid_enabled = False
        self.pyramid_length = 3.0  # Length relative to sphere radius
        self.pyramid_infinite = False  # Whether pyramid extends 
infinitely
        self.pyramid_angle_horizontal = 25.0  # Horizontal half-angle in 
degrees
        self.pyramid_angle_vertical = 20.0  # Vertical half-angle in 
degrees
        self.pyramid_color = np.array([0.0, 1.0, 1.0, 0.3])  # Cyan with 
transparency
        
        # Cuboid properties
        self.cuboid_enabled = False
        self.cuboid_length = 2.0   # Along vector direction
        self.cuboid_infinite = False  # Whether cuboid extends infinitely
        self.cuboid_width = 1.0    # Perpendicular to vector
        self.cuboid_height = 0.8   # Perpendicular to vector and width
        self.cuboid_color = np.array([1.0, 0.5, 0.0, 0.3])  # Orange with 
transparency
        
        # Near plane properties (for truncating shapes)
        self.near_plane_enabled = False
        self.near_plane_distance = 0.5  # Distance from sphere center 
along vector (0 = at center, 1 = at sphere surface)
        
        # Sphere intersection properties (show where shapes intersect 
sphere surface)
        self.sphere_intersection_enabled = False
        self.sphere_intersection_color = np.array([1.0, 1.0, 0.0, 0.8])  # 
Bright yellow with some transparency
        
        # Normal ray properties (show surface normal vectors)
        self.normal_rays_enabled = False
        self.normal_rays_length = 0.5  # Length of normal rays relative to 
sphere radius
        self.normal_rays_density = 8   # Number of rays per 
latitude/longitude division
        self.normal_rays_color = np.array([0.0, 1.0, 1.0, 1.0])  # Cyan 
color
        self.normal_rays_thickness = 2.0
        
        # Intersection normal ray properties (show normals only on 
intersection surfaces)
        self.intersection_normals_enabled = False
        self.intersection_normals_length = 0.3  # Length of intersection 
normal rays
        self.intersection_normals_density = 12  # Higher density for 
intersection areas
        self.intersection_normals_color = np.array([1.0, 0.0, 1.0, 1.0])  
# Magenta color
        self.intersection_normals_thickness = 2.5
        
        # Truncation normal ray properties (show normals on near plane cut 
surfaces)
        self.truncation_normals_enabled = False
        self.truncation_normals_length = 0.4  # Length of truncation 
normal rays
        self.truncation_normals_density = 8   # Density for truncation 
surfaces
        self.truncation_normals_color = np.array([1.0, 1.0, 1.0, 1.0])  # 
White color
        self.truncation_normals_thickness = 3.0
        
        # Grid properties
        self.active_grids = set()
        self.grid_colors = {
        GridType.LONGITUDE_LATITUDE: np.array([0.0, 1.0, 1.0, 1.0]),  # 
Cyan
        GridType.CONCENTRIC_CIRCLES: np.array([1.0, 0.0, 1.0, 1.0]),  # 
Magenta
        GridType.DOT_PARTICLES: np.array([0.0, 1.0, 0.0, 1.0]),       # 
Green
        GridType.NEON_LINES: np.array([0.0, 0.5, 1.0, 1.0]),          # 
Neon blue
        GridType.WIREFRAME: np.array([1.0, 1.0, 1.0, 1.0])            # 
White
        }
        
        # Grid parameters
        self.longitude_lines = 16
        self.latitude_lines = 12
        self.concentric_rings = 8
        self.dot_density = 200
        self.neon_intensity = 1.0
        
        # 2D Screen properties for ray tracing
        self.screen_enabled = False
        self.screen_width = 3.0  # Width in 3D space (bigger for better 
visibility)
        self.screen_height = 2.25  # Height in 3D space (bigger for better 
visibility)
        self.screen_position = np.array([0.0, 0.0, 4.0])  # Position in 
front of sphere
        self.screen_rotation = np.array([0.0, 0.0, 0.0])  # Screen facing 
-Z direction (toward camera)
        self.screen_resolution = (128, 96)  # Lower resolution for better 
performance
        self.screen_render_mode = "simple"  # Start with simple mode, can 
switch to "ray_tracing", "path_tracing", "pbr", "ray_marching"
        self.screen_camera_position = np.array([0.0, 0.0, 0.0])  # Virtual 
camera position (sphere center)
        self.screen_camera_target = np.array([1.0, 0.0, 1.0])  # Virtual 
camera target (toward red cube)
        self.screen_samples = 1  # Lower samples for better performance
        self.screen_max_bounces = 1  # Fewer bounces for better 
performance
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
                self.normals.extend([cos_lat * cos_lon, sin_lat, cos_lat * 
sin_lon])
                
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
        """Generate separate geometry for wireframe with adjustable 
density."""
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
        """Calculate ray-sphere intersection. Returns (hit, distance, 
point, normal)."""
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
        
        t = t1 if t1 > 0.001 else t2  # Use epsilon to avoid 
self-intersection
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
        direction = self.vector_direction / 
np.linalg.norm(self.vector_direction)
        cone_angle_rad = math.radians(self.cone_angle)
        cos_angle = math.cos(cone_angle_rad)
        cos_angle_sq = cos_angle * cos_angle
        
        # Transform ray to cone space (cone axis along Z)
        # For simplicity, assume cone along positive vector direction
        oc = ray_origin
        
        # Cone equation: (x² + y²) = (z * tan(angle))²
        # This is a simplified implementation
        a = ray_direction[0] * ray_direction[0] + ray_direction[1] * 
ray_direction[1] - \
            (ray_direction[2] * ray_direction[2]) * (1 - cos_angle_sq) / 
cos_angle_sq
        b = 2.0 * (oc[0] * ray_direction[0] + oc[1] * ray_direction[1] - \
                   (oc[2] * ray_direction[2]) * (1 - cos_angle_sq) / 
cos_angle_sq)
        c = oc[0] * oc[0] + oc[1] * oc[1] - (oc[2] * oc[2]) * (1 - 
cos_angle_sq) / cos_angle_sq
        
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
            # Use fixed base radius so cone size is independent of sphere 
scale
            base_radius = 1.0
            if dist_along_axis < 0 or dist_along_axis > self.cone_length * 
base_radius:
                return False, float('inf'), None, None
        
        # Calculate normal (simplified)
        normal = np.array([hit_point[0], hit_point[1], 0.0])
        if np.linalg.norm(normal) > 0:
            normal = normal / np.linalg.norm(normal)
        
        return True, t, hit_point, normal
    
    def ray_box_intersection(self, ray_origin, ray_direction, box_center, 
box_size):
        """Check ray intersection with an axis-aligned box using proper 
slab method."""
        # Calculate box bounds (slab method)
        box_min = box_center - box_size
        box_max = box_center + box_size
        
        # Debug flag - enable detailed debugging for specific rays
        debug_this_ray = False
        if np.allclose(ray_origin, [0, 0, 0], atol=0.01) and 
np.allclose(box_center, [2, 0, 2], atol=0.01):
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
        
        # Determine which face by finding the component closest to the box 
boundary
        normalized_pos = rel_pos / box_size
        abs_normalized = np.abs(normalized_pos)
        max_component = np.argmax(abs_normalized)
        
        normal = np.zeros(3)
        normal[max_component] = 1.0 if rel_pos[max_component] > 0 else 
-1.0
        
        return True, t, hit_point, normal
    
    def ray_rotated_box_intersection(self, ray_origin, ray_direction, 
box_center, box_size, rotation_degrees):
        """Check ray intersection with a rotated box by transforming ray 
to box's local space."""
        import math
        
        # Debug: Check if we have any rotation
        has_rotation = np.any(np.abs(rotation_degrees) > 0.1)
        if has_rotation:
            print(f"DEBUG: ray_rotated_box_intersection called with 
rotation: {rotation_degrees}")
            print(f"DEBUG: Box center: {box_center}, Box size: 
{box_size}")
            print(f"DEBUG: Ray origin: {ray_origin}, Ray direction: 
{ray_direction}")
        
        # Convert rotation from degrees to radians
        rotation_rad = np.radians(rotation_degrees)
        
        # Create rotation matrices to match OpenGL's glRotatef order: X, 
Y, Z
        # Use positive angles (no negation) to match OpenGL behavior
        cos_x, sin_x = math.cos(rotation_rad[0]), 
math.sin(rotation_rad[0])
        cos_y, sin_y = math.cos(rotation_rad[1]), 
math.sin(rotation_rad[1])
        cos_z, sin_z = math.cos(rotation_rad[2]), 
math.sin(rotation_rad[2])
        
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
        
        # Combined rotation matrix - apply in same order as OpenGL: X, 
then Y, then Z
        R_forward = R_z @ R_y @ R_x  # Forward transformation (local to 
world)
        R_inverse = R_forward.T      # Inverse transformation (world to 
local)
        
        # Transform ray to box's local coordinate system (world to local)
        local_ray_origin = R_inverse @ (ray_origin - box_center)
        local_ray_direction = R_inverse @ ray_direction
        
        # Test intersection with axis-aligned box in local space
        hit, t, local_hit_point, local_normal = self.ray_box_intersection(
            local_ray_origin, local_ray_direction, np.array([0, 0, 0]), 
box_size
        )
        
        if hit:
            # Transform hit point and normal back to world space (local to 
world)
            world_hit_point = R_forward @ local_hit_point + box_center
            world_normal = R_forward @ local_normal
            
            if has_rotation:
                print(f"DEBUG: ✅ ROTATED BOX HIT!")
                print(f"DEBUG: Hit at local: {local_hit_point}, world: 
{world_hit_point}")
                print(f"DEBUG: Normal local: {local_normal}, world: 
{world_normal}")
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
        
        # Use a larger tolerance for rotated cubes and find the closest 
face
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
            face_name = face_names[best_face_idx] if best_face_idx >= 0 
else "UNKNOWN"
            color_name = colors[best_face_idx] if best_face_idx >= 0 else 
"UNKNOWN"
            print(f"DEBUG: Face {face_name} detected, color {color_name}, 
normal={normal}, dot={best_dot:.3f}")
        
        return np.array(best_match) if best_match is not None else 
np.array([1.0, 0.0, 0.0])
    
    def trace_ray(self, ray_origin, ray_direction, depth=0):
        """Trace a ray through the scene and return color."""
        if depth > self.screen_max_bounces:
            return np.array([0.0, 0.0, 0.0])  # Black
        
        closest_t = float('inf')
        closest_hit = None
        closest_normal = None
        closest_material = None
        
        # Test sphere intersection - DISABLED for ray tracing (camera is 
inside sphere)
        # hit, t, hit_point, normal = 
self.ray_sphere_intersection(ray_origin, ray_direction)
        # if hit and t < closest_t:
        #     closest_t = t
        #     closest_hit = hit_point
        #     closest_normal = normal
        #     closest_material = "sphere"
        
        # Test cone intersection - DISABLED for ray tracing (camera is 
inside cone at origin)
        # if self.cone_enabled:
        #     hit, t, hit_point, normal = 
self.ray_cone_intersection(ray_origin, ray_direction)
        #     if hit and t < closest_t:
        #         closest_t = t
        #         closest_hit = hit_point
        #         closest_normal = normal
        #         closest_material = "cone"
        
        # Test red cube intersection - match simple mode size, position 
AND rotation
        if hasattr(self, '_canvas_ref') and self._canvas_ref and 
hasattr(self._canvas_ref, 'red_cube_position'):
            red_cube_pos = self._canvas_ref.red_cube_position.copy()
        else:
            red_cube_pos = np.array([2.0, 0.0, 2.0])  # Fallback position
        # Use the same size as simple mode to ensure visual consistency
        if hasattr(self, '_canvas_ref') and self._canvas_ref and 
hasattr(self._canvas_ref, 'red_cube_size'):
            cube_size = self._canvas_ref.red_cube_size
            red_cube_size = np.array([cube_size, cube_size, cube_size])
        else:
            red_cube_size = np.array([0.3, 0.3, 0.3])  # Fallback to match 
simple mode default
        
        # Get cube rotation to match simple mode rendering
        if hasattr(self, '_canvas_ref') and self._canvas_ref and 
hasattr(self._canvas_ref, 'object_rotations'):
            cube_rotation = self._canvas_ref.object_rotations.get("cube", 
np.array([0.0, 0.0, 0.0]))
        else:
            cube_rotation = np.array([0.0, 0.0, 0.0])
        
        # Debug cube rotation and render mode
        if depth == 0:  # Only print for primary rays
            print(f"DEBUG: ===== CUBE ROTATION DEBUG =====")
            print(f"DEBUG: Cube rotation from canvas: {cube_rotation}")
            if hasattr(self, '_canvas_ref') and self._canvas_ref:
                canvas_cube_rot = 
self._canvas_ref.object_rotations.get("cube", "NOT_FOUND")
                print(f"DEBUG: Canvas object_rotations['cube']: 
{canvas_cube_rot}")
            
            if np.any(np.abs(cube_rotation) > 0.1):  # Only print if 
there's significant rotation
                print(f"DEBUG: ⚠️ SIGNIFICANT CUBE ROTATION DETECTED: 
[{cube_rotation[0]:.1f}°, {cube_rotation[1]:.1f}°, 
{cube_rotation[2]:.1f}°]")
                print(f"DEBUG: Will use rotated box intersection method")
            else:
                print(f"DEBUG: No significant rotation, will use standard 
box intersection")
            print(f"DEBUG: =====================================")
            
            # Also debug render mode to make sure we're in ray tracing
            print(f"DEBUG: Sphere render mode: 
'{self.screen_render_mode}', Canvas render mode: 
'{getattr(self._canvas_ref, 'screen_render_mode', 'unknown') if 
self._canvas_ref else 'no_canvas'}')")
        
        # Apply rotation to ray intersection (transform ray to cube's 
local space)
        hit, t, hit_point, normal = 
self.ray_rotated_box_intersection(ray_origin, ray_direction, red_cube_pos, 
red_cube_size, cube_rotation)
        
        # Debug red cube intersection - more detailed
        if depth == 0:  # Only print for primary rays to avoid spam
            ray_dir_normalized = ray_direction / 
np.linalg.norm(ray_direction)
            cube_direction = red_cube_pos / np.linalg.norm(red_cube_pos)
            dot_to_cube = np.dot(ray_dir_normalized, cube_direction)
            
            # Test if we're close to the ideal ray that should hit dead 
center
            ideal_ray = red_cube_pos / np.linalg.norm(red_cube_pos)  # 
(0.707, 0, 0.707)
            dot_to_ideal = np.dot(ray_dir_normalized, ideal_ray)
            
            if dot_to_ideal > 0.95:  # Close to ideal ray (lowered 
threshold)
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
                    box_min = red_cube_pos - red_cube_size
                    box_max = red_cube_pos + red_cube_size
                    print(f"  - Box bounds: min={box_min}, max={box_max}")
                    
                    # Test if ray passes through the box bounds
                    ray_end = ray_origin + ray_direction * 10.0  # Extend 
ray
                    print(f"  - Ray extended to: {ray_end}")
                    
                print(f"  - Cube bounds: [{red_cube_pos - red_cube_size}] 
to [{red_cube_pos + red_cube_size}]")
        
            if hit and t < closest_t:
                closest_t = t
                closest_hit = hit_point
                closest_normal = normal
            closest_material = "red_cube"
        
        # No intersection - return background color (match main 3D scene)
        if closest_hit is None:
            # Match the main 3D scene background: gl.glClearColor(0.1, 
0.1, 0.1, 1.0)
            bg_color = np.array([0.1, 0.1, 0.1])
            
            # Debug background rays occasionally
            if depth == 0 and abs(ray_direction[0] - 0.707) < 0.01 and 
abs(ray_direction[2] - 0.707) < 0.01:
                print(f"DEBUG BACKGROUND: ray={ray_direction}, 
color={bg_color}")
            
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
        elif closest_material == "red_cube":
            base_color = self.get_cube_face_color(closest_normal)  # 
Multicolored cube faces
        else:
            base_color = np.array([0.8, 0.8, 0.8])
        
        # Simple lighting model
        ambient = 0.3
        color = base_color * (ambient + diffuse * 0.7)
        
        # Debug color calculation (reduced spam)
        if depth == 0 and closest_material == "red_cube" and 
np.random.random() < 0.01:  # Only 1% of hits
            print(f"DEBUG RED CUBE HIT!")
            print(f"  - Material: {closest_material}")
            print(f"  - Base color: {base_color}")
            print(f"  - Diffuse: {diffuse:.3f}")
            print(f"  - Final color: {color}")
            print(f"  - Hit point: {closest_hit}")
        
        # Debug if we're getting white colors from non-background sources
        if depth == 0 and np.all(color > 0.9):
            print(f"DEBUG WHITE HIT: material={closest_material}, 
color={color}, base={base_color}")
        
        # Reflection (simplified)
        if depth < self.screen_max_bounces and self.screen_render_mode in 
["path_tracing", "pbr"]:
            reflect_dir = ray_direction - 2.0 * np.dot(ray_direction, 
closest_normal) * closest_normal
            reflect_color = self.trace_ray(closest_hit + 0.001 * 
closest_normal, reflect_dir, depth + 1)
            color = 0.7 * color + 0.3 * reflect_color
        
        return np.clip(color, 0.0, 1.0)
    
    # ==================== RAY MARCHING (SDF) SYSTEM ====================
    
    def sdf_sphere(self, point, center, radius):
        """Signed distance function for a sphere."""
        return np.linalg.norm(point - center) - radius
    
    def sdf_box(self, point, center, size):
        """Signed distance function for a box."""
        q = np.abs(point - center) - size
        return np.linalg.norm(np.maximum(q, 0.0)) + min(max(q[0], 
max(q[1], q[2])), 0.0)
    
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
        perp1 = np.array([1.0, 0.0, 0.0]) if abs(axis[0]) < 0.9 else 
np.array([0.0, 1.0, 0.0])
        perp2 = np.cross(axis, perp1)
        perp1 = np.cross(perp2, axis)
        
        # Transform to local box space
        radial_vec = local_point - axis * axis_projection
        local_x = np.dot(radial_vec, perp1)
        local_y = np.dot(radial_vec, perp2)
        local_box_point = np.array([local_x, local_y, 0.0])
        
        return self.sdf_box(local_box_point, np.array([0.0, 0.0, 0.0]), 
box_size)
    
    def scene_sdf(self, point):
        """Combined SDF for the entire scene."""
        min_dist = float('inf')
        closest_material = "background"
        
        # Sphere SDF - DISABLED for ray tracing (camera is inside sphere)
        # sphere_dist = self.sdf_sphere(point, self.position, self.radius)
        # if sphere_dist < min_dist:
        #     min_dist = sphere_dist
        #     closest_material = "sphere"
        
        # Cone SDF - DISABLED for ray tracing (camera is inside cone at 
origin)
        # if self.cone_enabled:
        #     direction = self.vector_direction / 
np.linalg.norm(self.vector_direction)
        #     cone_angle_rad = math.radians(self.cone_angle)
        #     cone_height = self.cone_length * self.radius if not 
self.cone_infinite else 1000.0
        #     cone_dist = self.sdf_cone(point, np.array([0.0, 0.0, 0.0]), 
direction, cone_angle_rad, cone_height)
        #     if cone_dist < min_dist:
        #         min_dist = cone_dist
        #         closest_material = "cone"
        
        # Pyramid SDF - DISABLED for ray tracing (camera is inside pyramid 
at origin)
        # if self.pyramid_enabled:
        #     direction = self.vector_direction / 
np.linalg.norm(self.vector_direction)
        #     pyramid_length = self.pyramid_length * self.radius if not 
self.pyramid_infinite else 1000.0
        #     pyramid_width = pyramid_length * 
math.tan(math.radians(self.pyramid_angle_horizontal))
        #     pyramid_height = pyramid_length * 
math.tan(math.radians(self.pyramid_angle_vertical))
        #     pyramid_dist = self.sdf_pyramid(point, np.array([0.0, 0.0, 
0.0]), direction, 
        #                                   pyramid_width, pyramid_height, 
pyramid_length)
        #     if pyramid_dist < min_dist:
        #         min_dist = pyramid_dist
        #         closest_material = "pyramid"
        
        # Cuboid SDF - DISABLED for ray tracing (camera is inside cuboid 
area)
        # if self.cuboid_enabled:
        #     direction = self.vector_direction / 
np.linalg.norm(self.vector_direction)
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
        #     # Transform point to cuboid local space (simplified - 
assumes axis-aligned)
        #     cuboid_dist = self.sdf_box(point, cuboid_center, 
cuboid_size)
        #     if cuboid_dist < min_dist:
        #         min_dist = cuboid_dist
        #         closest_material = "cuboid"
        
        # Add the red cube to the ray tracing scene - match simple mode 
size and position
        if hasattr(self, '_canvas_ref') and self._canvas_ref and 
hasattr(self._canvas_ref, 'red_cube_position'):
            red_cube_pos = self._canvas_ref.red_cube_position.copy()
        else:
            red_cube_pos = np.array([2.0, 0.0, 2.0])  # Fallback position
        # Use the same size as simple mode to ensure visual consistency
        if hasattr(self, '_canvas_ref') and self._canvas_ref and 
hasattr(self._canvas_ref, 'red_cube_size'):
            cube_size = self._canvas_ref.red_cube_size
            red_cube_size = np.array([cube_size, cube_size, cube_size])
        else:
            red_cube_size = np.array([0.3, 0.3, 0.3])  # Fallback to match 
simple mode default
        
        red_cube_dist = self.sdf_box(point, red_cube_pos, red_cube_size)
        if red_cube_dist < min_dist:
            min_dist = red_cube_dist
            closest_material = "red_cube"
        
        return min_dist, closest_material
    
    def calculate_normal_sdf(self, point, epsilon=0.001):
        """Calculate normal using SDF gradient."""
        grad_x = self.scene_sdf(point + np.array([epsilon, 0.0, 0.0]))[0] 
- \
                 self.scene_sdf(point - np.array([epsilon, 0.0, 0.0]))[0]
        grad_y = self.scene_sdf(point + np.array([0.0, epsilon, 0.0]))[0] 
- \
                 self.scene_sdf(point - np.array([0.0, epsilon, 0.0]))[0]
        grad_z = self.scene_sdf(point + np.array([0.0, 0.0, epsilon]))[0] 
- \
                 self.scene_sdf(point - np.array([0.0, 0.0, epsilon]))[0]
        
        normal = np.array([grad_x, grad_y, grad_z])
        norm = np.linalg.norm(normal)
        return normal / norm if norm > 0 else np.array([0.0, 1.0, 0.0])
    
    def ray_march(self, ray_origin, ray_direction, max_steps=64, 
max_distance=20.0, epsilon=0.001):
        """Ray marching using signed distance functions."""
        total_distance = 0.0
        
        for step in range(max_steps):
            current_point = ray_origin + ray_direction * total_distance
            
            distance, material = self.scene_sdf(current_point)
            
            # Hit surface
            if distance < epsilon:
                normal = self.calculate_normal_sdf(current_point, epsilon)
                return True, total_distance, current_point, normal, 
material
            
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
        
        hit, distance, hit_point, normal, material = 
self.ray_march(ray_origin, ray_direction)
        
        # No intersection - return background color (match main 3D scene)
        if not hit:
            # Match the main 3D scene background: gl.glClearColor(0.1, 
0.1, 0.1, 1.0)
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
        elif material == "red_cube":
            base_color = self.get_cube_face_color(normal)  # Multicolored 
cube faces
        else:
            base_color = np.array([0.8, 0.8, 0.8])
        
        # Enhanced lighting model for ray marching
        ambient = 0.2
        specular_strength = 0.3
        
        # Specular highlight
        view_dir = -ray_direction
        reflect_dir = 2.0 * np.dot(normal, light_dir) * normal - light_dir
        specular = specular_strength * pow(max(0.0, np.dot(view_dir, 
reflect_dir)), 32)
        
        color = base_color * (ambient + diffuse * 0.7) + np.array([1.0, 
1.0, 1.0]) * specular
        
        # Reflection for ray marching
        if depth < self.screen_max_bounces:
            reflect_dir = ray_direction - 2.0 * np.dot(ray_direction, 
normal) * normal
            reflect_color = self.trace_ray_marching(hit_point + 0.01 * 
normal, reflect_dir, depth + 1)
            color = 0.8 * color + 0.2 * reflect_color
        
        return np.clip(color, 0.0, 1.0)
    
    # ==================== END RAY MARCHING SYSTEM ====================
    
    def render_screen_texture(self):
        """Generate ray-traced image for the 2D screen (optimized)."""
        if not self.screen_enabled:
            return
        
        print(f"DEBUG: Rendering ray tracing screen texture, mode: 
{self.screen_render_mode}")
        print(f"DEBUG: Screen resolution: 
{self.screen_resolution}x{self.screen_resolution}")
        
        current_time = time.time()
        # Always update if screen_needs_update is True (user interaction)
        if not self.screen_needs_update and current_time - 
self.screen_last_update < self.screen_update_rate:
            return  # Don't update too frequently for automatic updates 
only
        
        self.screen_last_update = current_time
        self.screen_needs_update = False
        
        width, height = self.screen_resolution
        
        # Fast mode: Use even lower resolution for real-time updates
        # Check both sphere and canvas render modes for ray tracing
        is_ray_tracing = (self.screen_render_mode == "ray_tracing" or 
                         (hasattr(self, '_canvas_ref') and 
self._canvas_ref and 
                          getattr(self._canvas_ref, 'screen_render_mode', 
'') == "raytracing"))
        
        if is_ray_tracing:
            render_width = width // 2  # Quarter resolution for speed
            render_height = height // 2
        else:
            render_width = width // 4  # Even lower for path tracing
            render_height = height // 4
        
        image_data = np.zeros((render_height, render_width, 3), 
dtype=np.uint8)
        
        # Set up virtual camera - match simple mode camera setup exactly
        camera_pos = self.position.copy()  # Actual sphere center
        
        # Use EXACT SAME camera setup as simple mode
        if hasattr(self, '_canvas_ref') and self._canvas_ref and 
hasattr(self._canvas_ref, 'view_vector'):
            view_dir = self._canvas_ref.view_vector.copy()  # Same as 
simple mode
            print(f"DEBUG: Using canvas view_vector: {view_dir}")
        else:
            # Fallback: use sphere's vector direction
            view_dir = self.vector_direction / 
np.linalg.norm(self.vector_direction)
            print(f"DEBUG: Using sphere vector_direction (fallback): 
{view_dir}")
        
        print(f"DEBUG: ===== RAY TRACING CAMERA SETUP (MATCHING SIMPLE 
MODE) =====")
        print(f"DEBUG: Camera position (sphere center): {camera_pos}")
        print(f"DEBUG: View direction: {view_dir}")
        
        # Check if camera is pointing toward red cube (for debugging)
        cube_pos = np.array([2.0, 0.0, 2.0])
        cube_dir = cube_pos - camera_pos
        cube_dir = cube_dir / np.linalg.norm(cube_dir)
        dot_product = np.dot(view_dir, cube_dir)
        angle_to_cube = math.degrees(math.acos(np.clip(dot_product, -1.0, 
1.0)))
        print(f"DEBUG: Direction to cube: {cube_dir}")
        print(f"DEBUG: Angle to cube: {angle_to_cube:.1f}° (should be 
close to 0°)")
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
        up = -up / np.linalg.norm(up)  # Negate up vector to match simple 
mode fix
        
        # EXACT SAME roll rotation as simple mode
        roll_angle = math.radians(self.vector_roll if hasattr(self, 
'vector_roll') else 0.0)
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
        print(f"  - camera·up: {np.dot(camera_dir, up):.6f} (should be 
~0)")
        print(f"  - camera·right: {np.dot(camera_dir, right):.6f} (should 
be ~0)")
        print(f"  - up·right: {np.dot(up, right):.6f} (should be ~0)")
        
        # Check if vectors are pointing in expected directions
        print(f"DEBUG: Vector direction check:")
        print(f"  - right should be perpendicular to camera and roughly 
horizontal")
        print(f"  - up should be perpendicular to camera and roughly 
vertical")
        print(f"  - Expected camera direction toward cube: [0.707, 0, 
0.707]")
        print(f"  - Actual camera direction: {camera_dir}")
        print(f"  - Match? {np.allclose(camera_dir, [0.707, 0, 0.707], 
atol=0.1)}")
        
        
        # Screen plane - match 2D screen projection mode
        if hasattr(self, '_canvas_ref') and self._canvas_ref and 
self._canvas_ref.screen_projection == "orthographic":
            # Orthographic projection for 2D screen - rays are parallel
            print(f"DEBUG: Using orthographic ray tracing for 2D screen")
            # Calculate orthographic bounds based on distance and FOV 
(match simple mode)
            fov = self.cone_angle * 2.0
            aspect_ratio = render_width / render_height
            distance_to_target = 10.0  # Same distance as simple mode 
look_at calculation
            half_height = distance_to_target * math.tan(math.radians(fov) 
/ 2.0)
            half_width = half_height * aspect_ratio
            is_orthographic = True
        else:
            # Perspective projection for 2D screen - rays converge at 
camera point
            print(f"DEBUG: Using perspective ray tracing for 2D screen")
            fov = self.cone_angle * 2.0  # Use same FOV as 2D viewing 
(cone_angle * 2)
            aspect_ratio = render_width / render_height
            half_height = math.tan(math.radians(fov) / 2.0)
            half_width = half_height * aspect_ratio
            is_orthographic = False
        
        # Optimized ray tracing - skip pixels for speed
        step = 2 if self.screen_render_mode == "ray_tracing" else 4
        
        total_rays = 0
        red_cube_hits = 0
        background_hits = 0
        
        print(f"DEBUG: Starting ray trace with step={step}, 
resolution={render_width}x{render_height}")
        
        # MANUAL TEST: Test perfect ray toward cube
        test_origin = np.array([0.0, 0.0, 0.0])
        test_direction = np.array([0.70710678, 0.0, 0.70710678])  # 
Perfect direction to cube
        cube_pos = np.array([2.0, 0.0, 2.0])
        # Use the same size as simple mode for consistency
        if hasattr(self, '_canvas_ref') and self._canvas_ref and 
hasattr(self._canvas_ref, 'red_cube_size'):
            cube_size = self._canvas_ref.red_cube_size
            cube_size = np.array([cube_size, cube_size, cube_size])
        else:
            cube_size = np.array([0.3, 0.3, 0.3])  # Match simple mode 
default
        
        print(f"DEBUG: MANUAL RAY TEST:")
        print(f"  - Test ray origin: {test_origin}")
        print(f"  - Test ray direction: {test_direction}")
        print(f"  - Cube position: {cube_pos}")
        print(f"  - Cube size: {cube_size}")
        
        # Test the intersection
        hit, t, hit_point, normal = self.ray_box_intersection(test_origin, 
test_direction, cube_pos, cube_size)
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
                    ray_origin_offset = u * half_width * right + v * 
half_height * up  # up vector already flipped above
                    ray_origin = camera_pos + ray_origin_offset
                    ray_dir = camera_dir  # All rays have same direction
                else:
                    # Perspective projection - rays converge at camera 
point
                    ray_origin = camera_pos
                    ray_dir = camera_dir + u * half_width * right + v * 
half_height * up  # up vector already flipped above
                ray_dir = ray_dir / np.linalg.norm(ray_dir)
                
                # Debug ray directions to see if they're perpendicular to 
camera direction
                if total_rays <= 10:  # Debug first few rays
                    dot_with_camera = np.dot(ray_dir, camera_dir)
                    print(f"DEBUG: Ray {total_rays} at pixel ({x},{y})")
                    print(f"  - Camera direction: {camera_dir}")
                    print(f"  - Ray direction: {ray_dir}")
                    print(f"  - Dot with camera: {dot_with_camera:.6f} 
(should be close to 1.0 for center rays)")
                    print(f"  - u={u:.3f}, v={v:.3f}")
                    print(f"  - right component: {u * half_width}")
                    print(f"  - up component: {v * half_height}")
                
                # Also check center ray specifically
                if abs(u) < 0.1 and abs(v) < 0.1:  # Near center
                    dot_with_camera = np.dot(ray_dir, camera_dir)
                    print(f"DEBUG: CENTER RAY - should match camera 
direction closely")
                    print(f"  - Camera direction: {camera_dir}")
                    print(f"  - Center ray direction: {ray_dir}")
                    print(f"  - Dot product: {dot_with_camera:.6f} (should 
be ~1.0)")
                    if dot_with_camera < 0.9:
                        print(f"  - ⚠️ CENTER RAY IS NOT ALIGNED WITH 
CAMERA!")
                
                # Choose rendering method based on mode
                if self.screen_render_mode == "ray_marching":
                    color = self.trace_ray_marching(ray_origin, ray_dir)
                else:
                    color = self.trace_ray(ray_origin, ray_dir)
                
                    # Count hits for debugging - fix the color detection
                    if np.any(color > 0.4) and color[0] > color[1] and 
color[0] > color[2]:  # Red-ish color (cube hit)
                        red_cube_hits += 1
                    elif np.allclose(color, [0.1, 0.1, 0.1], atol=0.05):  
# Background color
                        background_hits += 1
                
                # Convert to 8-bit
                pixel_color = (color * 255).astype(np.uint8)
                
                # Debug color conversion for non-background pixels
                if not np.allclose(color, [0.1, 0.1, 0.1], atol=0.05) and 
total_rays <= 10:
                    print(f"DEBUG COLOR: pixel({x},{y}) - 
float_color={color}, uint8_color={pixel_color}")
                
                # Fill a block of pixels for speed
                for dy in range(step):
                    for dx in range(step):
                        py = min(y + dy, render_height - 1)
                        px = min(x + dx, render_width - 1)
                        image_data[py, px] = pixel_color  # Fixed: Remove 
Y flip to match simple mode
        
        # Store the low-res image data for now (we could upscale later if 
needed)
        self.screen_current_size = (render_width, render_height)
        
        print(f"DEBUG: ===== RAY TRACING TEXTURE COMPLETED =====")
        print(f"DEBUG: Ray tracing statistics:")
        print(f"  - Total rays cast: {total_rays}")
        print(f"  - Red cube hits: {red_cube_hits}")
        print(f"  - Background hits: {background_hits}")
        print(f"  - Other hits: {total_rays - red_cube_hits - 
background_hits}")
        print(f"  - Cube hit percentage: 
{(red_cube_hits/total_rays*100):.2f}%")
        
        if red_cube_hits == 0:
            print(f"DEBUG: ⚠️  NO CUBE HITS DETECTED!")
            print(f"DEBUG: This suggests the camera is not pointing toward 
the cube")
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
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, render_width, 
render_height, 0, 
                       gl.GL_RGB, gl.GL_UNSIGNED_BYTE, image_data)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, 
gl.GL_NEAREST)  # Nearest for pixelated look
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, 
gl.GL_NEAREST)
    
    def create_placeholder_texture(self):
        """Create a simple placeholder texture for the screen."""
        width, height = 64, 48  # Small placeholder
        # Create a simple pattern: blue background with "RAY TRACING" text 
simulation
        image_data = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Blue background
        image_data[:, :] = [0, 100, 200]
        
        # Add some simple pattern lines to indicate it's loading
        for y in range(0, height, 8):
            image_data[y:y+2, :] = [255, 255, 255]  # White horizontal 
lines
        
        # Create texture
        if self.screen_texture_id is None:
            self.screen_texture_id = gl.glGenTextures(1)
        
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.screen_texture_id)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, width, height, 0, 
                       gl.GL_RGB, gl.GL_UNSIGNED_BYTE, image_data)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, 
gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, 
gl.GL_NEAREST)
    
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
        gl.glTranslatef(self.screen_position[0], self.screen_position[1], 
self.screen_position[2])
        
        # Apply screen rotation from object_rotations to match simple mode 
behavior
        if hasattr(self, '_canvas_ref') and self._canvas_ref and 
hasattr(self._canvas_ref, 'object_rotations'):
            screen_rot = self._canvas_ref.object_rotations.get("screen", 
np.array([0.0, 0.0, 0.0]))
            gl.glRotatef(screen_rot[0], 1.0, 0.0, 0.0)  # Pitch (X 
rotation)
            gl.glRotatef(screen_rot[1], 0.0, 1.0, 0.0)  # Yaw (Y rotation)
            gl.glRotatef(screen_rot[2], 0.0, 0.0, 1.0)  # Roll (Z 
rotation)
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
        
        gl.glVertex3f(-border_width, -border_height, 0.001)  # Slightly in 
front
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
            self.screen_needs_update = True  # Force immediate update when 
enabled
    
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
        gl.glTranslatef(self.position[0], self.position[1], 
self.position[2])
        
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
                    
                    gl.glVertex3f(self.vertices[idx1], self.vertices[idx1 
+ 1], self.vertices[idx1 + 2])
                    gl.glVertex3f(self.vertices[idx2], self.vertices[idx2 
+ 1], self.vertices[idx2 + 2])
            gl.glEnd()
            gl.glEnable(gl.GL_CULL_FACE)
        else:
            # Render solid sphere surface
            # If transparent, disable face culling to see both sides
            if self.transparency < 1.0:
                gl.glDisable(gl.GL_CULL_FACE)
                gl.glEnable(gl.GL_BLEND)
                gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
                gl.glDepthMask(gl.GL_FALSE)  # Don't write to depth buffer 
for transparent objects
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
                gl.glMaterialfv(gl.GL_FRONT_AND_BACK, 
gl.GL_AMBIENT_AND_DIFFUSE, color)
                gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_SPECULAR, 
[1.0, 1.0, 1.0, 1.0])
                gl.glMaterialf(gl.GL_FRONT_AND_BACK, gl.GL_SHININESS, 
50.0)
            else:
                gl.glDisable(gl.GL_LIGHTING)
            
            # Render triangles
            gl.glBegin(gl.GL_TRIANGLES)
            for i in range(0, len(self.indices), 3):
                for j in range(3):
                    idx = self.indices[i + j] * 3
                    gl.glNormal3f(self.normals[idx], self.normals[idx + 
1], self.normals[idx + 2])
                    gl.glVertex3f(self.vertices[idx], self.vertices[idx + 
1], self.vertices[idx + 2])
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
        """Render wireframe representation of the sphere with adjustable 
density."""
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
                
                gl.glVertex3f(self.wireframe_vertices[idx1], 
self.wireframe_vertices[idx1 + 1], self.wireframe_vertices[idx1 + 2])
                gl.glVertex3f(self.wireframe_vertices[idx2], 
self.wireframe_vertices[idx2 + 1], self.wireframe_vertices[idx2 + 2])
        gl.glEnd()
        
        # Re-enable face culling
        gl.glEnable(gl.GL_CULL_FACE)
    
    def render_vector(self):
        """Render 3D vector from sphere center with arrow head."""
        if not self.vector_enabled:
            return
        
        # Normalize the direction vector
        direction = self.vector_direction / 
np.linalg.norm(self.vector_direction)
        
        # Calculate vector end point - use fixed size regardless of sphere 
scale
        base_radius = 1.0  # Use fixed base radius so vector size is 
independent of sphere scale
        vector_end = direction * self.vector_length * base_radius
        
        # Set vector color
        gl.glColor4f(*self.vector_color)
        gl.glLineWidth(self.vector_thickness)
        
        # Disable lighting for vector (we want solid colors)
        gl.glDisable(gl.GL_LIGHTING)
        
        # Draw main vector line
        gl.glBegin(gl.GL_LINES)
        gl.glVertex3f(0.0, 0.0, 0.0)  # Start at sphere center
        gl.glVertex3f(vector_end[0], vector_end[1], vector_end[2])  # End 
point
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
        """Render orientation vector showing the 'up' direction at the 
tail of the main vector."""
        if not self.vector_enabled or not self.vector_orientation_enabled:
            return
        
        # Normalize the main vector direction
        direction = self.vector_direction / 
np.linalg.norm(self.vector_direction)
        
        # Calculate the up vector based on roll rotation (same logic as 
camera system)
        world_up = np.array([0.0, 1.0, 0.0])
        right = np.cross(direction, world_up)
        if np.linalg.norm(right) < 0.001:
            # If vector is pointing up/down, use right vector as reference
            right = np.array([1.0, 0.0, 0.0])
        right = right / np.linalg.norm(right)
        up = np.cross(right, direction)
        up = up / np.linalg.norm(up)
        
        # Apply roll rotation around the vector direction (same method as 
camera system)
        roll_angle = math.radians(self.vector_roll)
        cos_roll = math.cos(roll_angle)
        sin_roll = math.sin(roll_angle)
        
        # Debug: Print roll angle to verify it's being used
        print(f"DEBUG: Orientation vector roll angle: 
{self.vector_roll:.1f}° (radians: {roll_angle:.3f})")
        
        # Apply 2D rotation to the up and right vectors in their plane 
(same as camera system)
        new_right = cos_roll * right + sin_roll * up
        new_up = -sin_roll * right + cos_roll * up
        
        right = new_right / np.linalg.norm(new_right)
        up_rotated = new_up / np.linalg.norm(new_up)
        
        # Debug: Print vectors to verify rotation
        print(f"DEBUG: Original up: {up}")
        print(f"DEBUG: Rotated up: {up_rotated}")
        print(f"DEBUG: Angle between them: 
{math.degrees(math.acos(np.clip(np.dot(up, up_rotated), -1.0, 
1.0))):.1f}°")
        
        # Calculate orientation vector end point (from sphere center)
        base_radius = 1.0  # Use fixed base radius so orientation vector 
size is independent of sphere scale
        orientation_end = up_rotated * self.vector_orientation_length * 
base_radius
        
        # Set orientation vector color and thickness
        gl.glColor4f(*self.vector_orientation_color)
        gl.glLineWidth(self.vector_orientation_thickness)
        
        # Disable lighting for orientation vector (we want solid colors)
        lighting_was_enabled = self.lighting_enabled
        if lighting_was_enabled:
            gl.glDisable(gl.GL_LIGHTING)
        
        # Draw orientation vector line from sphere center
        gl.glBegin(gl.GL_LINES)
        gl.glVertex3f(0.0, 0.0, 0.0)  # Start at sphere center (tail of 
main vector)
        gl.glVertex3f(orientation_end[0], orientation_end[1], 
orientation_end[2])  # End point
        gl.glEnd()
        
        # Draw small arrow head for orientation vector
        self.render_orientation_arrow_head(orientation_end, up_rotated)
        
        # Re-enable lighting if it was enabled
        if lighting_was_enabled:
            gl.glEnable(gl.GL_LIGHTING)
    
    def render_orientation_arrow_head(self, tip_position, direction):
        """Render small arrow head at the tip of the orientation 
vector."""
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
            base_point = arrow_base + (perp1 * cos_angle + perp2 * 
sin_angle) * arrow_width
            
            # Next point on the base circle
            next_angle = 2 * math.pi * (i + 1) / 4
            next_cos = math.cos(next_angle)
            next_sin = math.sin(next_angle)
            next_base_point = arrow_base + (perp1 * next_cos + perp2 * 
next_sin) * arrow_width
            
            # Triangle from tip to base edge
            gl.glVertex3f(tip_position[0], tip_position[1], 
tip_position[2])
            gl.glVertex3f(base_point[0], base_point[1], base_point[2])
            gl.glVertex3f(next_base_point[0], next_base_point[1], 
next_base_point[2])
        
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
            gl.glVertex3f(tip_position[0], tip_position[1], 
tip_position[2])
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
        """Render cone section or truncated cone with tip at sphere center 
pointing along vector direction."""
        if not self.cone_enabled:
            return
        
        # Use vector direction for cone axis
        direction = self.vector_direction / 
np.linalg.norm(self.vector_direction)
        
        # Calculate cone end point and base radius - use fixed size 
regardless of sphere scale
        base_radius = 1.0  # Use fixed base radius so cone size is 
independent of sphere scale
        if self.cone_infinite:
            # Use a very large length for infinite cone rendering to cover 
entire screen
            effective_length = 1000.0 * base_radius
            cone_end = direction * effective_length
            cone_base_radius = effective_length * 
math.tan(math.radians(self.cone_angle))
        else:
            cone_end = direction * self.cone_length * base_radius
            cone_base_radius = self.cone_length * base_radius * 
math.tan(math.radians(self.cone_angle))
        
        # Create perpendicular vectors for cone base
        if abs(direction[0]) < 0.9:
            perp1 = np.array([0.0, direction[2], -direction[1]])
        else:
            perp1 = np.array([-direction[2], 0.0, direction[0]])
            
            perp1 = perp1 / np.linalg.norm(perp1)
        
        # Second perpendicular vector
        perp2 = np.cross(direction, perp1)
        perp2 = perp2 / np.linalg.norm(perp2)
        
        # Set cone color and enable blending for transparency (only if 
managing blend state)
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
            self._render_truncated_cone(direction, cone_end, perp1, perp2, 
cone_base_radius)
        else:
            # Render full cone
            self._render_full_cone(cone_end, perp1, perp2, 
cone_base_radius)
        
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
            # For infinite cone, only render the edge rays, not the 
surface
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
                angle2 = 2 * math.pi * ((i + 1) % self.cone_resolution) / 
self.cone_resolution
                
                # Points on the cone base circle
                base_point1 = (cone_end +
                              perp1_scaled * math.cos(angle1) +
                              perp2_scaled * math.sin(angle1))
                base_point2 = (cone_end +
                              perp1_scaled * math.cos(angle2) +
                              perp2_scaled * math.sin(angle2))
                
                # Triangle from tip to base edge
                gl.glVertex3f(0.0, 0.0, 0.0)  # Tip at sphere center
                gl.glVertex3f(base_point1[0], base_point1[1], 
base_point1[2])
                gl.glVertex3f(base_point2[0], base_point2[1], 
base_point2[2])
            
            gl.glEnd()
        
        # Render cone outline wireframe for better visibility
        gl.glColor4f(self.cone_color[0], self.cone_color[1], 
self.cone_color[2], 1.0)
        gl.glLineWidth(2.0)
        
        # Draw lines from tip to base circle
        gl.glBegin(gl.GL_LINES)
        for i in range(0, self.cone_resolution, 2):  # Every other line to 
avoid clutter
            angle = 2 * math.pi * i / self.cone_resolution
            base_point = (cone_end +
            perp1_scaled * math.cos(angle) +
            perp2_scaled * math.sin(angle))
            
            gl.glVertex3f(0.0, 0.0, 0.0)  # From tip
            gl.glVertex3f(base_point[0], base_point[1], base_point[2])  # 
To base
        
        # Draw base circle outline
        for i in range(self.cone_resolution):
            angle1 = 2 * math.pi * i / self.cone_resolution
            angle2 = 2 * math.pi * ((i + 1) % self.cone_resolution) / 
self.cone_resolution
            
            point1 = (cone_end +
                     perp1_scaled * math.cos(angle1) +
                     perp2_scaled * math.sin(angle1))
            point2 = (cone_end +
                     perp1_scaled * math.cos(angle2) +
                     perp2_scaled * math.sin(angle2))
            
            gl.glVertex3f(point1[0], point1[1], point1[2])
            gl.glVertex3f(point2[0], point2[1], point2[2])
        
        gl.glEnd()
        
    def _render_truncated_cone(self, direction, cone_end, perp1, perp2, 
cone_base_radius):
        """Render truncated cone by cutting at near plane."""
        # For proper truncation, interpolate along the cone's existing 
surface
        # The cone goes from tip (0,0,0) to base circle at cone_end
        
        # Use fixed base radius so cone size is independent of sphere 
scale
        base_radius = 1.0
        full_length = self.cone_length * base_radius
        if self.near_plane_distance >= full_length:
            # Near plane is beyond the cone, render nothing
            return
        
        # Calculate interpolation factor (0 = at tip, 1 = at base)
        t = self.near_plane_distance / full_length
        
        # Calculate near plane position and radius by interpolating along 
cone surface
        near_plane_pos = t * cone_end  # Position along cone axis
        near_radius = t * cone_base_radius  # Radius scales linearly from 
tip
        
        # Scale perpendicular vectors
        perp1_near = perp1 * near_radius
        perp2_near = perp2 * near_radius
        perp1_base = perp1 * cone_base_radius
        perp2_base = perp2 * cone_base_radius
        
        # Render truncated cone surface as triangles
        gl.glBegin(gl.GL_TRIANGLES)
        
        for i in range(self.cone_resolution):
            angle1 = 2 * math.pi * i / self.cone_resolution
            angle2 = 2 * math.pi * ((i + 1) % self.cone_resolution) / 
self.cone_resolution
            
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
            angle2 = 2 * math.pi * ((i + 1) % self.cone_resolution) / 
self.cone_resolution
            
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
            angle2 = 2 * math.pi * ((i + 1) % self.cone_resolution) / 
self.cone_resolution
            
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
        gl.glColor4f(self.cone_color[0], self.cone_color[1], 
self.cone_color[2], 1.0)
        gl.glLineWidth(2.0)
    
        gl.glBegin(gl.GL_LINES)
        
        # Draw near plane circle outline
        for i in range(self.cone_resolution):
            angle1 = 2 * math.pi * i / self.cone_resolution
            angle2 = 2 * math.pi * ((i + 1) % self.cone_resolution) / 
self.cone_resolution
            
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
            angle2 = 2 * math.pi * ((i + 1) % self.cone_resolution) / 
self.cone_resolution
            
            point1 = (cone_end +
            perp1_base * math.cos(angle1) +
            perp2_base * math.sin(angle1))
            point2 = (cone_end +
            perp1_base * math.cos(angle2) +
            perp2_base * math.sin(angle2))
            
            gl.glVertex3f(point1[0], point1[1], point1[2])
            gl.glVertex3f(point2[0], point2[1], point2[2])
        
        # Draw connecting lines between circles
        for i in range(0, self.cone_resolution, 2):  # Every other line to 
avoid clutter
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
        """Render 4-sided pyramid or hexahedron (truncated pyramid) with 
tip at sphere center."""
        if not self.pyramid_enabled:
            return
        
        # Use vector direction for pyramid axis
        direction = self.vector_direction / 
np.linalg.norm(self.vector_direction)
        
        # Calculate pyramid end point - use fixed size regardless of 
sphere scale
        base_radius = 1.0  # Use fixed base radius so pyramid size is 
independent of sphere scale
        if self.pyramid_infinite:
            # Use a very large length for infinite pyramid rendering to 
cover entire screen
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
            half_width = effective_length * 
math.tan(math.radians(self.pyramid_angle_horizontal))
            half_height = effective_length * 
math.tan(math.radians(self.pyramid_angle_vertical))
        else:
            half_width = self.pyramid_length * base_radius * 
math.tan(math.radians(self.pyramid_angle_horizontal))
            half_height = self.pyramid_length * base_radius * 
math.tan(math.radians(self.pyramid_angle_vertical))
        
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
        
        # Set pyramid color and enable blending for transparency (only if 
managing blend state)
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
            self._render_hexahedron(direction, horizontal, vertical, 
base_corners)
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
            # For infinite pyramid, only render the edge rays, not the 
surface
            gl.glBegin(gl.GL_LINES)
            
            # Four edge rays from tip to infinite distance
            for i in range(4):
                gl.glVertex3f(0.0, 0.0, 0.0)  # Tip at sphere center
                gl.glVertex3f(base_corners[i][0], base_corners[i][1], 
base_corners[i][2])
            
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
            gl.glVertex3f(base_corners[0][0], base_corners[0][1], 
base_corners[0][2])
            gl.glVertex3f(base_corners[1][0], base_corners[1][1], 
base_corners[1][2])
            gl.glVertex3f(base_corners[2][0], base_corners[2][1], 
base_corners[2][2])
            
            # Triangle 2: corners 0, 2, 3
            gl.glVertex3f(base_corners[0][0], base_corners[0][1], 
base_corners[0][2])
            gl.glVertex3f(base_corners[2][0], base_corners[2][1], 
base_corners[2][2])
            gl.glVertex3f(base_corners[3][0], base_corners[3][1], 
base_corners[3][2])
            
            gl.glEnd()
        
        # Render pyramid outline wireframe for better visibility
        gl.glColor4f(self.pyramid_color[0], self.pyramid_color[1], 
self.pyramid_color[2], 1.0)
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
    
    def _render_hexahedron(self, direction, horizontal, vertical, 
base_corners):
        """Render hexahedron (truncated pyramid) by cutting at near 
plane."""
        # Calculate near plane position
        near_plane_pos = direction * self.near_plane_distance * 
self.radius
        
        # For proper truncation, interpolate along the pyramid's existing 
edges
        # The pyramid goes from tip (0,0,0) to base_corners
        # Near plane cuts at distance near_plane_distance along the 
pyramid length
        
        # Use fixed base radius so pyramid size is independent of sphere 
scale
        base_radius = 1.0
        full_length = self.pyramid_length * base_radius
        if self.near_plane_distance >= full_length:
            # Near plane is beyond the pyramid, render nothing
            return
        
        # Calculate interpolation factor (0 = at tip, 1 = at base)
        t = self.near_plane_distance / full_length
        
        # Calculate the four corners of the near plane by interpolating 
from tip to each base corner
        near_corners = []
        for base_corner in base_corners:
            # Interpolate from tip (0,0,0) to base_corner
            near_corner = t * base_corner  # t=0 gives tip, t=1 gives 
base_corner
            near_corners.append(near_corner)
        
        # Render hexahedron faces as triangles
        gl.glBegin(gl.GL_TRIANGLES)
        
        # Four trapezoidal faces (each split into 2 triangles)
        for i in range(4):
            next_i = (i + 1) % 4
            
            # Bottom triangle of trapezoid (near plane)
            gl.glVertex3f(near_corners[i][0], near_corners[i][1], 
near_corners[i][2])
            gl.glVertex3f(near_corners[next_i][0], 
near_corners[next_i][1], near_corners[next_i][2])
            gl.glVertex3f(base_corners[next_i][0], 
base_corners[next_i][1], base_corners[next_i][2])
            
            # Top triangle of trapezoid
            gl.glVertex3f(near_corners[i][0], near_corners[i][1], 
near_corners[i][2])
            gl.glVertex3f(base_corners[next_i][0], 
base_corners[next_i][1], base_corners[next_i][2])
            gl.glVertex3f(base_corners[i][0], base_corners[i][1], 
base_corners[i][2])
        
        # Near plane (smaller rectangle) - split into two triangles
        # Triangle 1: corners 0, 1, 2
        gl.glVertex3f(near_corners[0][0], near_corners[0][1], 
near_corners[0][2])
        gl.glVertex3f(near_corners[1][0], near_corners[1][1], 
near_corners[1][2])
        gl.glVertex3f(near_corners[2][0], near_corners[2][1], 
near_corners[2][2])
        
        # Triangle 2: corners 0, 2, 3
        gl.glVertex3f(near_corners[0][0], near_corners[0][1], 
near_corners[0][2])
        gl.glVertex3f(near_corners[2][0], near_corners[2][1], 
near_corners[2][2])
        gl.glVertex3f(near_corners[3][0], near_corners[3][1], 
near_corners[3][2])
        
        # Base (larger rectangle) - split into two triangles
        # Triangle 1: corners 0, 1, 2
        gl.glVertex3f(base_corners[0][0], base_corners[0][1], 
base_corners[0][2])
        gl.glVertex3f(base_corners[1][0], base_corners[1][1], 
base_corners[1][2])
        gl.glVertex3f(base_corners[2][0], base_corners[2][1], 
base_corners[2][2])
        
        # Triangle 2: corners 0, 2, 3
        gl.glVertex3f(base_corners[0][0], base_corners[0][1], 
base_corners[0][2])
        gl.glVertex3f(base_corners[2][0], base_corners[2][1], 
base_corners[2][2])
        gl.glVertex3f(base_corners[3][0], base_corners[3][1], 
base_corners[3][2])
    
        gl.glEnd()
        
        # Render hexahedron outline wireframe
        gl.glColor4f(self.pyramid_color[0], self.pyramid_color[1], 
self.pyramid_color[2], 1.0)
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
            gl.glVertex3f(near_corners[i][0], near_corners[i][1], 
near_corners[i][2])
            gl.glVertex3f(base_corners[i][0], base_corners[i][1], 
base_corners[i][2])
        
        gl.glEnd()
    
    def render_cuboid(self, manage_blend=True):
        """Render rectangular cuboid or smaller cuboid when near plane 
cuts it."""
        if not self.cuboid_enabled:
            return
        
        # Use vector direction for cuboid central axis
        direction = self.vector_direction / 
np.linalg.norm(self.vector_direction)
        
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
        
        # Set cuboid color and enable blending for transparency (only if 
managing blend state)
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
            self._render_truncated_cuboid(direction, width_axis, 
height_axis)
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
            # For infinite cuboid, render as 4-sided pyramid (far face 
vanishes)
            self._render_infinite_cuboid_as_pyramid(direction, width_axis, 
height_axis)
            return
        
        # Calculate half-dimensions for finite cuboid - use fixed size 
regardless of sphere scale
        base_radius = 1.0  # Use fixed base radius so cuboid size is 
independent of sphere scale
        half_length = (self.cuboid_length * base_radius) / 2.0
        half_width = (self.cuboid_width * base_radius) / 2.0
        half_height = (self.cuboid_height * base_radius) / 2.0
        
        # Calculate the 8 corners of the cuboid
        # Center the cuboid so it extends from sphere center along vector 
direction
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
    
    def _render_truncated_cuboid(self, direction, width_axis, 
height_axis):
        """Render smaller cuboid starting from near plane."""
        # Calculate near plane position
        # Calculate near plane position - use fixed base size regardless 
of sphere scale
        base_radius = 1.0
        near_plane_pos = direction * self.near_plane_distance * 
base_radius
        
        # Calculate remaining length after near plane cut
        if self.cuboid_infinite:
            # For infinite cuboid, always render from near plane to a 
large distance
            full_length = 50.0 * base_radius
            remaining_length = full_length - self.near_plane_distance * 
base_radius
        else:
            full_length = self.cuboid_length * base_radius
            remaining_length = full_length - self.near_plane_distance * 
base_radius
        
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
                             direction * (length_sign * 
half_remaining_length) +
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
        gl.glColor4f(self.cuboid_color[0], self.cuboid_color[1], 
self.cuboid_color[2], 1.0)
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
    
    def _render_infinite_cuboid_as_pyramid(self, direction, width_axis, 
height_axis):
        """Render infinite cuboid with normal size at center and infinite 
extension."""
        # Calculate the dimensions for the central cuboid - use fixed size 
regardless of sphere scale
        base_radius = 1.0  # Use fixed base radius so cuboid size is 
independent of sphere scale
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
        # Use a large distance for the "infinite" end - use fixed size 
regardless of sphere scale
        infinite_distance = 50.0 * base_radius
        
        # Get the four corners of the far face (where the cuboid ends)
        far_face_center = direction * (half_length * 2)  # Far end of the 
central cuboid
        far_face_corners = [
            far_face_center + width_axis * half_width + height_axis * 
half_height,    # Top-right
            far_face_center - width_axis * half_width + height_axis * 
half_height,    # Top-left
            far_face_center - width_axis * half_width - height_axis * 
half_height,    # Bottom-left
            far_face_center + width_axis * half_width - height_axis * 
half_height     # Bottom-right
        ]
        
        # Calculate infinite extension points
        infinite_corners = []
        for corner in far_face_corners:
            # Extend from the far face corner to infinity in the same 
direction
            infinite_point = corner + direction * infinite_distance
            infinite_corners.append(infinite_point)
        
        # Render infinite extension rays
        gl.glBegin(gl.GL_LINES)
        for i in range(4):
            # Line from far face corner to infinite distance
            gl.glVertex3f(far_face_corners[i][0], far_face_corners[i][1], 
far_face_corners[i][2])
            gl.glVertex3f(infinite_corners[i][0], infinite_corners[i][1], 
infinite_corners[i][2])
        
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
            
            # Render all active grid systems (but not the wireframe grid 
if we're in wireframe mode)
            self.render_longitude_latitude_grid()
            self.render_concentric_circles()
            self.render_dot_particles()
            self.render_neon_lines()
            
        # Only render wireframe grid if not in wireframe mode (to avoid 
double wireframe)
        if not self.wireframe_mode:
            self.render_wireframe()
        
        gl.glPopMatrix()  # End sphere transformation matrix (position, 
rotation, scale)
        
        # Render shapes OUTSIDE the sphere's scale transformation
        # Apply only sphere position and rotation, but NOT scale
        gl.glPushMatrix()
        gl.glTranslatef(self.position[0], self.position[1], 
self.position[2])
        gl.glRotatef(self.rotation[0], 1, 0, 0)  # Pitch
        gl.glRotatef(self.rotation[1], 0, 1, 0)  # Yaw
        gl.glRotatef(self.rotation[2], 0, 0, 1)  # Roll
        # NOTE: No glScalef here - shapes maintain their own size 
regardless of sphere scale
        
        # Render shapes with proper transparency handling
        # For transparent objects, disable depth writes and render 
back-to-front
        
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
            
            # Render shapes back-to-front (roughly ordered by distance 
from center)
            # Cuboid is closest to center, then pyramid, then cone 
(extends furthest)
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
        if self.vector_enabled:
            self.render_vector()
        
        gl.glPopMatrix()  # End shapes transformation matrix
        
        # Render 2D screen with ray-traced image (outside transformation 
matrix)
        # Only render if canvas is in raytracing mode and screen is 
enabled
        if hasattr(self, '_canvas_ref') and self._canvas_ref:
            canvas_enabled = self._canvas_ref.screen_enabled
            canvas_mode = self._canvas_ref.screen_render_mode
            # Check for ray tracing in either canvas or sphere mode
            is_ray_tracing_mode = (canvas_mode == "raytracing" or 
self.screen_render_mode == "ray_tracing")
            should_render = canvas_enabled and is_ray_tracing_mode
            # Debug the render mode mismatch
            print(f"DEBUG: Canvas mode: '{canvas_mode}', Sphere mode: 
'{self.screen_render_mode}'")
            sphere_enabled = self.screen_enabled
            print(f"DEBUG: Sphere screen render check - canvas_enabled: 
{canvas_enabled}, canvas_mode: {canvas_mode}, sphere_enabled: 
{sphere_enabled}, should_render: {should_render}")
            if should_render:
                print(f"DEBUG: Sphere rendering ray tracing screen")
                self.render_screen_geometry()
            else:
                print(f"DEBUG: Sphere skipping screen render (canvas mode: 
{canvas_mode})")
        else:
            # Fallback: render if screen is enabled (for backward 
compatibility)
            if self.screen_enabled:
                print(f"DEBUG: Sphere rendering screen (fallback mode)")
                self.render_screen_geometry()
            else:
                print(f"DEBUG: Sphere screen disabled (fallback mode)")
    
    def render_sphere_intersections(self):
        """Render sphere surface areas where shapes intersect the 
sphere."""
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
        """Render normal rays (surface normals) extending from sphere 
surface."""
        # Set normal ray color and properties
        gl.glColor4f(*self.normal_rays_color)
        gl.glLineWidth(self.normal_rays_thickness)
        
        # Disable lighting for rays (we want uniform color)
        lighting_was_enabled = self.lighting_enabled
        if lighting_was_enabled:
            gl.glDisable(gl.GL_LIGHTING)
        
        # Calculate ray length - use fixed base radius so ray length is 
independent of sphere scale
        base_radius = 1.0
        ray_length = self.normal_rays_length * base_radius
        
        gl.glBegin(gl.GL_LINES)
        
        # Generate rays using spherical coordinates
        density = self.normal_rays_density
        
        # Create rays at regular intervals across the sphere surface
        for i in range(density):
            for j in range(density):
                # Spherical coordinates (theta = azimuth, phi = polar 
angle)
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
                    
                # Normal vector at this point (for a sphere, normal = 
position / radius)
                normal_vector = sphere_point / self.radius
                
                # End point of the ray
                ray_end = sphere_point + normal_vector * ray_length
                
                # Draw the ray
                gl.glVertex3f(sphere_point[0], sphere_point[1], 
sphere_point[2])
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
        
        # Calculate ray length - use fixed base radius so ray length is 
independent of sphere scale
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
        # Only render if near plane is enabled and at least one shape is 
enabled
        if not self.near_plane_enabled or self.near_plane_distance <= 0:
            return
        
        # Set truncation normal ray color and properties
        gl.glColor4f(*self.truncation_normals_color)
        gl.glLineWidth(self.truncation_normals_thickness)
        
        # Disable lighting for rays (we want uniform color)
        lighting_was_enabled = self.lighting_enabled
        if lighting_was_enabled:
            gl.glDisable(gl.GL_LIGHTING)
        
        # Calculate ray length - use fixed base radius so ray length is 
independent of sphere scale
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
        direction = self.vector_direction / 
np.linalg.norm(self.vector_direction)
        
        # Near plane position along the vector - use fixed base radius so 
position is independent of sphere scale
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
                radius = truncation_radius * (j + 1) / 2  # Inner and 
outer ring
                
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
        direction = self.vector_direction / 
np.linalg.norm(self.vector_direction)
        
        # Create orthogonal coordinate system
        if abs(direction[0]) < 0.9:
            horizontal = np.array([0.0, direction[2], -direction[1]])
        else:
            horizontal = np.array([-direction[2], 0.0, direction[0]])
            
        horizontal = horizontal / np.linalg.norm(horizontal)
        vertical = np.cross(direction, horizontal)
        vertical = vertical / np.linalg.norm(vertical)
        
        # Near plane position along the vector - use fixed base radius so 
position is independent of sphere scale
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
        direction = self.vector_direction / 
np.linalg.norm(self.vector_direction)
        
        # Create orthogonal coordinate system
        if abs(direction[0]) < 0.9:
            width_axis = np.array([0.0, direction[2], -direction[1]])
        else:
            width_axis = np.array([-direction[2], 0.0, direction[0]])
        
        width_axis = width_axis / np.linalg.norm(width_axis)
        height_axis = np.cross(direction, width_axis)
        height_axis = height_axis / np.linalg.norm(height_axis)
        
        # Near plane position along the vector - use fixed base radius so 
position is independent of sphere scale
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
        direction = self.vector_direction / 
np.linalg.norm(self.vector_direction)
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
            for j in range(int(density * cone_angle_rad / math.pi)):  # 
Scale by cone angle
                angle = 2 * math.pi * i / density
                ring_angle = cone_angle_rad * j / int(density * 
cone_angle_rad / math.pi)
                
                # Point on sphere surface within cone
                sphere_direction = (direction * math.cos(ring_angle) +
                (perp1 * math.cos(angle) + perp2 * math.sin(angle)) * 
math.sin(ring_angle))
                sphere_point = sphere_direction / 
np.linalg.norm(sphere_direction) * self.radius
                
                # Normal vector (same as position for sphere)
                normal_vector = sphere_point / self.radius
                ray_end = sphere_point + normal_vector * ray_length
                
                # Draw the ray
                gl.glVertex3f(sphere_point[0], sphere_point[1], 
sphere_point[2])
                gl.glVertex3f(ray_end[0], ray_end[1], ray_end[2])
    
    def _render_pyramid_intersection_normals(self, ray_length):
        """Render normal rays on pyramid intersection surface."""
        # Get vector direction and pyramid parameters
        direction = self.vector_direction / 
np.linalg.norm(self.vector_direction)
        
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
        # Use fixed base radius so pyramid size is independent of sphere 
scale
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
                    sphere_point = point_direction / direction_length * 
self.radius
                    
                    # Verify this point is within the pyramid bounds
                    length_proj = np.dot(sphere_point, direction)
                    width_proj = np.dot(sphere_point, horizontal)
                    height_proj = np.dot(sphere_point, vertical)
                    
                    # Check if within pyramid
                    if length_proj > 0 and length_proj <= pyramid_length:
                        pyramid_half_width = length_proj * 
math.tan(h_angle_rad)
                        pyramid_half_height = length_proj * 
math.tan(v_angle_rad)
                                        
                        if (abs(width_proj) <= pyramid_half_width and
                        abs(height_proj) <= pyramid_half_height):
                            
                            # Normal vector (same as position for sphere)
                            normal_vector = sphere_point / self.radius
                            ray_end = sphere_point + normal_vector * 
ray_length
                            
                            # Draw the ray
                            gl.glVertex3f(sphere_point[0], 
sphere_point[1], sphere_point[2])
                            gl.glVertex3f(ray_end[0], ray_end[1], 
ray_end[2])
    
    def _render_cuboid_intersection_normals(self, ray_length):
        """Render normal rays on cuboid intersection surface."""
        # Get vector direction and cuboid parameters
        direction = self.vector_direction / 
np.linalg.norm(self.vector_direction)
        
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
        # Use fixed base radius so cuboid size is independent of sphere 
scale
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
                
                # Map to cuboid coordinates (sample at middle of cuboid 
length)
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
                    gl.glVertex3f(sphere_point[0], sphere_point[1], 
sphere_point[2])
                    gl.glVertex3f(ray_end[0], ray_end[1], ray_end[2])
    
    def _render_sphere_cone_intersection(self):
        """Render the spherical cap surface that's inside the cone."""
        # Disable face culling to ensure visibility from all angles
        gl.glDisable(gl.GL_CULL_FACE)
        
        # Get vector direction
        direction = self.vector_direction / 
np.linalg.norm(self.vector_direction)
        
        # For a cone with half-angle, we want to show the spherical cap 
that's inside the cone
        cone_angle_rad = math.radians(self.cone_angle)
        
        # Create perpendicular vectors for the circular intersection
        if abs(direction[0]) < 0.9:
            perp1 = np.array([0.0, direction[2], -direction[1]])
        else:
            perp1 = np.array([-direction[2], 0.0, direction[0]])
        
        perp1 = perp1 / np.linalg.norm(perp1)
        perp2 = np.cross(direction, perp1)
        perp2 = perp2 / np.linalg.norm(perp2)
        
        # The spherical cap extends from the sphere center along the 
vector direction
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
                # Current and next ring angles (from center to cone 
boundary)
                ring_angle1 = cone_angle_rad * ring / num_rings
                ring_angle2 = cone_angle_rad * (ring + 1) / num_rings
                
                # Points on sphere surface at these angles - these are 
already normalized unit vectors
                # pointing in the right direction, so we just multiply by 
radius
                direction1 = (direction * math.cos(ring_angle1) +
                (perp1 * math.cos(angle1) + perp2 * math.sin(angle1)) * 
math.sin(ring_angle1))
                direction2 = (direction * math.cos(ring_angle1) +
                (perp1 * math.cos(angle2) + perp2 * math.sin(angle2)) * 
math.sin(ring_angle1))
                direction3 = (direction * math.cos(ring_angle2) +
                (perp1 * math.cos(angle1) + perp2 * math.sin(angle1)) * 
math.sin(ring_angle2))
                direction4 = (direction * math.cos(ring_angle2) +
                (perp1 * math.cos(angle2) + perp2 * math.sin(angle2)) * 
math.sin(ring_angle2))
                
                # Ensure these are unit vectors and scale to sphere radius
                point1 = direction1 / np.linalg.norm(direction1) * 
self.radius
                point2 = direction2 / np.linalg.norm(direction2) * 
self.radius
                point3 = direction3 / np.linalg.norm(direction3) * 
self.radius
                point4 = direction4 / np.linalg.norm(direction4) * 
self.radius
                
                # Two triangles to form the quad with consistent winding 
order
                # First triangle (counter-clockwise when viewed from 
outside sphere)
                gl.glVertex3f(point1[0], point1[1], point1[2])
                gl.glVertex3f(point2[0], point2[1], point2[2])
                gl.glVertex3f(point3[0], point3[1], point3[2])
                
                # Second triangle (counter-clockwise when viewed from 
outside sphere)
                gl.glVertex3f(point2[0], point2[1], point2[2])
                gl.glVertex3f(point4[0], point4[1], point4[2])
                gl.glVertex3f(point3[0], point3[1], point3[2])
                
                # Also render the triangles with opposite winding for 
double-sided visibility
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
        direction = self.vector_direction / 
np.linalg.norm(self.vector_direction)
        
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
        # Use fixed base radius so pyramid size is independent of sphere 
scale
        base_radius = 1.0
        pyramid_length = self.pyramid_length * base_radius
        
        # Create smooth pyramid intersection surface using proper 
parametric mapping
        resolution = 32  # Higher resolution for smoother surface
    
        gl.glBegin(gl.GL_TRIANGLES)
        
        # Map the pyramid volume to sphere surface using angular 
coordinates
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
                for angle_u, angle_v in [(angle_u1, angle_v1), (angle_u2, 
angle_v1),
                (angle_u2, angle_v2), (angle_u1, angle_v2)]:
                    
                    # Create direction vector from angles
                    # This creates a smooth mapping from pyramid volume to 
sphere surface
                    point_direction = (direction +
                    horizontal * math.tan(angle_u) +
                    vertical * math.tan(angle_v))
                    
                    # Normalize to get point on sphere surface
                    direction_length = np.linalg.norm(point_direction)
                    if direction_length > 0:
                        sphere_point = point_direction / direction_length 
* self.radius
                        
                        # Verify this point is within the pyramid bounds
                        length_proj = np.dot(sphere_point, direction)
                        width_proj = np.dot(sphere_point, horizontal)
                        height_proj = np.dot(sphere_point, vertical)
                        
                        # Check if within pyramid (pyramid extends from 
origin)
                        if length_proj > 0 and length_proj <= 
pyramid_length:
                            # Calculate pyramid bounds at this distance
                            pyramid_half_width = length_proj * 
math.tan(h_angle_rad)
                            pyramid_half_height = length_proj * 
math.tan(v_angle_rad)
                                                
                            inside = (abs(width_proj) <= 
pyramid_half_width and
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
        """Render the sphere surface area that's inside the cuboid, 
aligned with cuboid faces."""
        # Get vector direction and cuboid parameters
        direction = self.vector_direction / 
np.linalg.norm(self.vector_direction)
        
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
        # Use fixed base radius so cuboid size is independent of sphere 
scale
        base_radius = 1.0
        if self.cuboid_infinite:
            cuboid_length = 50.0 * base_radius
        else:
            cuboid_length = self.cuboid_length * base_radius
        
        # Create the intersection surface by mapping the cuboid face onto 
the sphere
        # We'll create a grid that follows the cuboid's rectangular shape
        resolution = 32
    
        gl.glBegin(gl.GL_TRIANGLES)
        
        # Create a rectangular grid in cuboid coordinate space, then 
project to sphere
        for i in range(resolution):
            for j in range(resolution):
                # Parametric coordinates for the rectangular patch (0 to 
1)
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
                height_coords = [half_height * (2 * v1 - 1), half_height * 
(2 * v2 - 1)]  # -half_height to +half_height
                        
                quad_points = []
                quad_valid = []
                
                # Generate the four corners of this patch
                for length_coord in length_coords:
                    for width_coord in width_coords[:1]:  # Only use first 
width coord for this iteration
                        for height_coord in height_coords[:1]:  # Only use 
first height coord for this iteration
                            # Point in cuboid coordinate system
                            cuboid_point = (direction * length_coord +
                            width_axis * width_coord +
                            height_axis * height_coord)
                            
                            # Project onto sphere surface
                            distance = np.linalg.norm(cuboid_point)
                            if distance > 0:
                                sphere_point = cuboid_point / distance * 
self.radius
                                                    
                                # Verify this point is actually inside the 
cuboid bounds
                                length_proj = np.dot(sphere_point, 
direction)
                                width_proj = np.dot(sphere_point, 
width_axis)
                                height_proj = np.dot(sphere_point, 
height_axis)
                                                    
                                inside = (0 <= length_proj <= 
cuboid_length and
                                -half_width <= width_proj <= half_width 
and
                                -half_height <= height_proj <= 
half_height)
                                                    
                                quad_points.append(sphere_point)
                                quad_valid.append(inside)
                
                # Create points for the rectangular patch corners
                points = []
                for u, v in [(u1, v1), (u2, v1), (u2, v2), (u1, v2)]:
                    # Map to cuboid coordinates
                    length = cuboid_length * 0.5  # Middle of cuboid 
length
                    width = half_width * (2 * u - 1)
                    height = half_height * (2 * v - 1)
                    
                    # Point in 3D space
                    cuboid_point = (direction * length +
                    width_axis * width +
                    height_axis * height)
                    
                    # Project to sphere surface
                    distance = np.linalg.norm(cuboid_point)
                    if distance > 0:
                        sphere_point = cuboid_point / distance * 
self.radius
                                    
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
    
    def set_grid_color(self, grid_type: GridType, color: Tuple[float, 
float, float, float]):
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
        
        # Notify canvas if it has the update method
        if hasattr(self, '_canvas_ref') and self._canvas_ref and 
hasattr(self._canvas_ref, 'update_screen_position_for_sphere_move'):
            
self._canvas_ref.update_screen_position_for_sphere_move(old_pos, 
self.position)
    
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
        self.vector_orientation_enabled = not 
self.vector_orientation_enabled
    
    def set_vector_orientation_enabled(self, enabled: bool):
        """Set vector orientation visibility state."""
        self.vector_orientation_enabled = enabled
    
    def set_vector_orientation_length(self, length: float):
        """Set vector orientation length."""
        self.vector_orientation_length = max(0.1, min(2.0, length))
    
    def set_vector_orientation_color(self, r: float, g: float, b: float, 
a: float = 1.0):
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
            
            # Force ray tracing screen update when vector changes
            if hasattr(self, 'screen_needs_update'):
                self.screen_needs_update = True
                print(f"DEBUG: Vector direction changed to {direction}, 
forcing screen update")
            
            # Notify canvas to update ray tracing camera
            if hasattr(self, '_canvas_ref') and self._canvas_ref:
                self._canvas_ref.update_sphere_view_vector()
                # Force immediate screen refresh
                self._canvas_ref.Refresh()
                print(f"DEBUG: Notified canvas of vector direction change 
and forced refresh")
    
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
        """Set vector roll rotation (camera orientation around the vector 
axis)."""
        self.vector_roll = roll_degrees % 360.0
        
        # Force ray tracing screen update when roll changes
        if hasattr(self, 'screen_needs_update'):
            self.screen_needs_update = True
        
        # Notify canvas to update ray tracing camera
        if hasattr(self, '_canvas_ref') and self._canvas_ref:
            self._canvas_ref.update_sphere_view_vector()
            # Force immediate screen refresh
            self._canvas_ref.Refresh()
    
    def rotate_vector_roll(self, degrees: float):
        """Rotate vector roll (camera orientation around the vector 
axis)."""
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
        """Set cuboid length along vector direction relative to sphere 
radius."""
        self.cuboid_length = max(0.1, length)
    
    def set_cuboid_width(self, width: float):
        """Set cuboid width perpendicular to vector relative to sphere 
radius."""
        self.cuboid_width = max(0.1, width)
    
    def set_cuboid_height(self, height: float):
        """Set cuboid height perpendicular to vector relative to sphere 
radius."""
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
        """Set near plane distance from sphere center along vector (0-1 
range)."""
        self.near_plane_distance = max(0.0, min(3.0, distance))  # Allow 
up to 3 radius units
    
    # Sphere intersection control methods
    def toggle_sphere_intersection(self):
        """Toggle sphere intersection visibility."""
        self.sphere_intersection_enabled = not 
self.sphere_intersection_enabled
    
    def set_sphere_intersection_enabled(self, enabled: bool):
        """Set sphere intersection visibility state."""
        self.sphere_intersection_enabled = enabled
    
    def set_sphere_intersection_color(self, color: Tuple[float, float, 
float, float]):
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
    
    def set_normal_rays_color(self, color: Tuple[float, float, float, 
float]):
        """Set normal ray color (RGBA)."""
        self.normal_rays_color = np.array(color)
    
    def set_normal_rays_thickness(self, thickness: float):
        """Set normal ray line thickness."""
        self.normal_rays_thickness = max(1.0, min(5.0, thickness))
    
    # Intersection normal ray control methods
    def toggle_intersection_normals(self):
        """Toggle intersection normal ray visibility."""
        self.intersection_normals_enabled = not 
self.intersection_normals_enabled
    
    def set_intersection_normals_enabled(self, enabled: bool):
        """Set intersection normal ray visibility state."""
        self.intersection_normals_enabled = enabled
    
    def set_intersection_normals_length(self, length: float):
        """Set intersection normal ray length relative to sphere 
radius."""
        self.intersection_normals_length = max(0.1, min(2.0, length))
    
    def set_intersection_normals_density(self, density: int):
        """Set intersection normal ray density (rays per division)."""
        self.intersection_normals_density = max(4, min(24, density))
    
    def set_intersection_normals_color(self, color: Tuple[float, float, 
float, float]):
        """Set intersection normal ray color (RGBA)."""
        self.intersection_normals_color = np.array(color)
    
    def set_intersection_normals_thickness(self, thickness: float):
        """Set intersection normal ray line thickness."""
        self.intersection_normals_thickness = max(1.0, min(5.0, 
thickness))
    
    # Truncation normal ray control methods
    def toggle_truncation_normals(self):
        """Toggle truncation normal ray visibility."""
        self.truncation_normals_enabled = not 
self.truncation_normals_enabled
    
    def set_truncation_normals_enabled(self, enabled: bool):
        """Set truncation normal ray visibility state."""
        self.truncation_normals_enabled = enabled
    
    def set_truncation_normals_length(self, length: float):
        """Set truncation normal ray length relative to sphere radius."""
        self.truncation_normals_length = max(0.1, min(2.0, length))
    
    def set_truncation_normals_density(self, density: int):
        """Set truncation normal ray density (rays per division)."""
        self.truncation_normals_density = max(3, min(16, density))
    
    def set_truncation_normals_color(self, color: Tuple[float, float, 
float, float]):
        """Set truncation normal ray color (RGBA)."""
        self.truncation_normals_color = np.array(color)
    
    def set_truncation_normals_thickness(self, thickness: float):
        """Set truncation normal ray line thickness."""
        self.truncation_normals_thickness = max(1.0, min(5.0, thickness))
    
    def save_scene_to_dict(self) -> dict:
        """Save all sphere properties to a dictionary for 
serialization."""
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
                "orientation_enabled": 
bool(self.vector_orientation_enabled),
                "orientation_length": 
float(self.vector_orientation_length),
                "orientation_color": 
self.vector_orientation_color.tolist(),
                "orientation_thickness": 
float(self.vector_orientation_thickness)
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
                "grid_colors": {str(k): v.tolist() for k, v in 
self.grid_colors.items()},
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
                self.vector_orientation_enabled = 
v.get("orientation_enabled", False)
                self.vector_orientation_length = 
v.get("orientation_length", 0.8)
                self.vector_orientation_color = 
np.array(v.get("orientation_color", [0.0, 1.0, 0.0, 1.0]))
                self.vector_orientation_thickness = 
v.get("orientation_thickness", 2.0)
            
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
                self.sphere_intersection_enabled = si.get("enabled", 
False)
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
                self.intersection_normals_enabled = inr.get("enabled", 
False)
                self.intersection_normals_length = inr.get("length", 0.3)
                self.intersection_normals_density = inr.get("density", 6)
                self.intersection_normals_color = 
np.array(inr.get("color", [1.0, 1.0, 0.0, 1.0]))
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
        self.sphere._canvas_ref = self  # Allow sphere to call canvas 
methods
        
        # Camera settings
        self.camera_distance = 5.0
        self.camera_rotation_x = 0.0
        self.camera_rotation_y = 0.0
        self.camera_position = np.array([0.0, 0.0, 0.0])  # Camera offset 
from center
        
        # Movement settings
        self.movement_speed = 0.2  # Units per key press
        self.zoom_speed = 0.5  # Zoom speed for I/O keys
        
        # Mouse interaction
        self.last_mouse_pos = None
        self.mouse_dragging = False
        
        # Red cube settings (fixed world position)
        self.red_cube_position = np.array([2.0, 0.0, 2.0])  # Fixed 
position in world space
        self.red_cube_size = 0.3  # Size of the cube
        
        # View vector and unified 2D screen system
        self.view_vector = np.array([0.0, 0.0, -1.0])  # Initial view 
direction
        
        # Camera projection mode
        self.camera_projection = "perspective"  # "perspective" or 
"orthographic"
        
        # Unified screen system - one physical screen with switchable 
rendering modes
        self.screen_enabled = True  # Screen is enabled by default
        self.screen_render_mode = "simple"  # "simple" (framebuffer) or 
"raytracing" (ray tracing) - start with original view
        self.screen_projection = "perspective"  # "perspective" or 
"orthographic" - projection mode for 2D screen
        
        # Unified screen properties (used by both rendering modes)
        self.screen_position = np.array([-3.0, 0.0, 0.0])  # Position of 
the 2D screen in 3D space
        self.screen_width = 2.0
        self.screen_height = 1.5
        
        # Simple mode framebuffer system
        self.framebuffer_width = 256
        self.framebuffer_height = 192
        self.framebuffer_id = None
        self.texture_id = None
        
        # Object selection and manipulation
        self.selected_object = "sphere"  # "sphere", "cube", "screen", or 
"none"
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
        
        # Enable keyboard focus
        self.SetCanFocus(True)
    
    
    def update_screen_position_for_sphere_move(self, old_sphere_pos, 
new_sphere_pos):
        """Update the ray tracing camera when the sphere is moved.
        
        The screen and cube stay in their fixed world positions.
        Only the sphere + vector + shapes move, and the ray tracing camera 
follows.
        """
        # Update the ray tracing camera position (should follow sphere 
center)
        self.update_ray_tracing_camera()
        
        print(f"DEBUG: Sphere moved from {old_sphere_pos} to 
{new_sphere_pos}")
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
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, 
self.framebuffer_width, 
                       self.framebuffer_height, 0, gl.GL_RGB, 
gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, 
gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, 
gl.GL_LINEAR)
        
        # Attach texture to framebuffer
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, 
gl.GL_COLOR_ATTACHMENT0, 
                                 gl.GL_TEXTURE_2D, self.texture_id, 0)
        
        # Generate renderbuffer for depth attachment
        depth_buffer = gl.glGenRenderbuffers(1)
        gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, depth_buffer)
        gl.glRenderbufferStorage(gl.GL_RENDERBUFFER, 
gl.GL_DEPTH_COMPONENT, 
                                self.framebuffer_width, 
self.framebuffer_height)
        gl.glFramebufferRenderbuffer(gl.GL_FRAMEBUFFER, 
gl.GL_DEPTH_ATTACHMENT, 
                                    gl.GL_RENDERBUFFER, depth_buffer)
        
        # Check framebuffer completeness
        if gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER) != 
gl.GL_FRAMEBUFFER_COMPLETE:
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
        
        # Configure the virtual camera to look from sphere center in the 
red vector direction
        self.update_ray_tracing_camera()
        
        print("DEBUG: Ray tracing screen initialized")
    
    def setup_unified_screen_system(self):
        """Set up the unified screen system that can switch between 
rendering modes."""
        # Always set up framebuffer for simple mode
        self.setup_framebuffer()
        
        # Configure the sphere's ray tracing screen to match our unified 
screen
        self.sync_raytracing_screen_with_unified()
        
        print(f"DEBUG: Unified screen system initialized, current mode: 
{self.screen_render_mode}")
    
    def sync_raytracing_screen_with_unified(self):
        """Sync the sphere's ray tracing screen with our unified screen 
properties."""
        # Set the sphere's ray tracing screen to match our unified screen
        self.sphere.set_screen_position(self.screen_position[0], 
self.screen_position[1], self.screen_position[2])
        self.sphere.set_screen_size(self.screen_width, self.screen_height)
        
        # Set resolution to match our framebuffer for consistency
        self.sphere.set_screen_resolution(self.framebuffer_width, 
self.framebuffer_height)
        
        # Ensure the sphere's screen is enabled for ray tracing
        self.sphere.screen_enabled = True
        
        # Configure ray tracing camera
        self.update_ray_tracing_camera()
        
        print(f"DEBUG: Ray tracing screen synced with unified screen 
properties")
    
    def update_ray_tracing_camera(self):
        """Update the ray tracing camera to look from sphere center along 
the red vector."""
        # Set camera position at actual sphere center (wherever it is)
        sphere_center = self.sphere.position.copy()
        
        print(f"DEBUG: update_ray_tracing_camera() called")
        print(f"DEBUG: Current sphere camera position: 
{getattr(self.sphere, 'screen_camera_position', 'NOT SET')}")
        print(f"DEBUG: Current sphere camera target: {getattr(self.sphere, 
'screen_camera_target', 'NOT SET')}")
        
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
            
            print(f"DEBUG: NEW camera position set to: 
{self.sphere.screen_camera_position}")
            print(f"DEBUG: NEW camera target set to: 
{self.sphere.screen_camera_target}")
            print(f"DEBUG: Red vector used: {red_vector}")
            print(f"DEBUG: Normalized vector: {normalized_vector}")
        else:
            print(f"DEBUG: ERROR - sphere has no vector_direction 
attribute!")
            print(f"DEBUG: Available sphere attributes: {[attr for attr in 
dir(self.sphere) if not attr.startswith('_')]}")
    
    def draw_red_cube(self):
        """Draw a multicolored cube at a fixed position."""
        gl.glPushMatrix()
        
        # Move to cube position
        gl.glTranslatef(self.red_cube_position[0], 
                       self.red_cube_position[1], 
                       self.red_cube_position[2])
        
        # Apply cube rotation
        cube_rot = self.object_rotations["cube"]
        print(f"DEBUG: ===== SIMPLE MODE CUBE ROTATION =====")
        print(f"DEBUG: Simple mode applying cube rotation: 
[{cube_rot[0]:.1f}°, {cube_rot[1]:.1f}°, {cube_rot[2]:.1f}°]")
        print(f"DEBUG: =========================================")
        
        gl.glRotatef(cube_rot[0], 1.0, 0.0, 0.0)  # X rotation
        gl.glRotatef(cube_rot[1], 0.0, 1.0, 0.0)  # Y rotation
        gl.glRotatef(cube_rot[2], 0.0, 0.0, 1.0)  # Z rotation
        
        # Draw cube with different colored faces
        s = self.red_cube_size
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
        """Render the view from the sphere's direction to a texture 
(simple mode)."""
        if self.screen_render_mode != "simple" or not self.framebuffer_id 
or not self.texture_id:
            return
            
        # Bind framebuffer for off-screen rendering
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.framebuffer_id)
        gl.glViewport(0, 0, self.framebuffer_width, 
self.framebuffer_height)
        
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
            distance_to_target = 10.0  # Distance used in look_at 
calculation
            ortho_height = distance_to_target * 
math.tan(math.radians(fov_vertical / 2.0))
            ortho_width = ortho_height * aspect_ratio
            gl.glOrtho(-ortho_width, ortho_width, -ortho_height, 
ortho_height, 0.1, 100.0)
            print(f"DEBUG: 2D screen using orthographic projection - 
bounds: ±{ortho_width:.2f} x ±{ortho_height:.2f}")
        else:
            # Perspective projection for 2D screen (default)
            glu.gluPerspective(fov_vertical, aspect_ratio, 0.1, 100.0)
            print(f"DEBUG: 2D screen using perspective projection - FOV: 
{fov_vertical:.1f}°")
        
        # Set up modelview matrix for sphere view
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glLoadIdentity()
        
        # Position camera at actual sphere center looking in view vector 
direction
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
        direction_to_cube_normalized = direction_to_cube / 
np.linalg.norm(direction_to_cube)
        dot_with_cube_dir = np.dot(view_dir, direction_to_cube_normalized)
        angle_to_cube = math.degrees(math.acos(np.clip(dot_with_cube_dir, 
-1.0, 1.0)))
        
        print(f"DEBUG: Cube position: {cube_pos}")
        print(f"DEBUG: Direction to cube: {direction_to_cube_normalized}")
        print(f"DEBUG: View direction: {view_dir}")
        print(f"DEBUG: Angle between view and cube direction: 
{angle_to_cube:.1f}° (should be close to 0°)")
        print(f"DEBUG: Are we looking toward cube? {angle_to_cube < 30}")
        print(f"DEBUG: ==============================================")
        
        # Calculate up vector with roll rotation applied
        world_up = np.array([0.0, 1.0, 0.0])
        right = np.cross(view_dir, world_up)
        if np.linalg.norm(right) < 0.001:
            right = np.array([1.0, 0.0, 0.0])
        right = right / np.linalg.norm(right)
        up = np.cross(right, view_dir)
        up = -up / np.linalg.norm(up)  # Negate up vector to fix 
upside-down 2D screen
        
        # Apply roll rotation around the view direction (vector axis)
        roll_angle = math.radians(self.sphere.vector_roll)
        cos_roll = math.cos(roll_angle)
        sin_roll = math.sin(roll_angle)
        
        # Apply 2D rotation to the up and right vectors in their plane
        new_right = cos_roll * right + sin_roll * up
        new_up = -sin_roll * right + cos_roll * up
        
        right = new_right / np.linalg.norm(new_right)
        up = new_up / np.linalg.norm(new_up)
        
        # Keep original look_at direction (forward along vector), only 
flip up vector for orientation
        flipped_up = -up  # Only flip up vector to fix screen orientation
        glu.gluLookAt(sphere_pos[0], sphere_pos[1], sphere_pos[2],
                     look_at[0], look_at[1], look_at[2],  # Use original 
look_at (forward direction)
                     flipped_up[0], flipped_up[1], flipped_up[2])
        
        # Render the scene from sphere's perspective
        self.draw_red_cube()  # Actually multicolored now
        # Note: Reference objects disabled in 2D screen to avoid yellow 
box artifact
        # The reference objects include a yellow cube that was appearing 
as an artifact
        # self.draw_reference_objects()
        
        print(f"DEBUG: Simple 2D screen rendered - reference objects 
disabled to prevent yellow box artifact")
        
        # Restore matrices
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_MODELVIEW)
        
        # Unbind framebuffer
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def draw_simple_2d_screen(self):
        """Draw the 2D screen as a quad in 3D space showing the sphere's 
view (simple mode)."""
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
        print(f"DEBUG: screen_enabled: {self.screen_enabled}, 
screen_render_mode: {self.screen_render_mode}")
        
        if not self.screen_enabled:
            print(f"DEBUG: Canvas screen disabled - not drawing unified 
screen")
            return
        
        if self.screen_render_mode == "simple":
            print(f"DEBUG: Canvas drawing simple 2D screen")
            self.draw_simple_2d_screen()
        elif self.screen_render_mode == "raytracing":
            print(f"DEBUG: Canvas in ray tracing mode - sphere should 
handle screen rendering")
            # The ray tracing screen is drawn by the sphere renderer
            # We just need to ensure it's enabled and positioned correctly
            if hasattr(self.sphere, 'screen_enabled'):
                self.sphere.screen_enabled = True
                print(f"DEBUG: Enabled sphere's ray tracing screen")
        else:
            print(f"DEBUG: Unknown screen render mode: 
{self.screen_render_mode}")
        
        print(f"DEBUG: Drew unified screen in {self.screen_render_mode} 
mode")
        
        # Debug: Show which rendering mode is active
        if self.screen_render_mode == "raytracing":
            print(f"DEBUG: Ray tracing mode active - screen follows red 
vector in real-time")
        elif self.screen_render_mode == "simple":
            print(f"DEBUG: Simple mode active - screen shows original 2D 
framebuffer view")
        else:
            print(f"DEBUG: Unknown screen mode: 
{self.screen_render_mode}")
    
    def update_sphere_ray_tracing_view(self):
        """Update the ray tracing screen based on the sphere's red vector 
direction."""
        print(f"DEBUG: ===== CANVAS update_sphere_ray_tracing_view() 
CALLED =====")
        print(f"DEBUG: Screen render mode: {self.screen_render_mode}")
        print(f"DEBUG: Screen enabled: {getattr(self.sphere, 
'screen_enabled', 'NOT SET')}")
        
        if self.screen_render_mode != "raytracing":
            print(f"DEBUG: Skipping ray tracing update - mode is 
{self.screen_render_mode}")
            return
        if not hasattr(self.sphere, 'screen_enabled') or not 
self.sphere.screen_enabled:
            print(f"DEBUG: Skipping ray tracing update - screen not 
enabled")
            return
        
        print(f"DEBUG: Calling update_ray_tracing_camera()...")
        
        # Update the ray tracing camera to follow the red vector
        self.update_ray_tracing_camera()
        
        # Force screen update
        if hasattr(self.sphere, 'screen_needs_update'):
            self.sphere.screen_needs_update = True
            print(f"DEBUG: Set screen_needs_update = True")
        
        print(f"DEBUG: Updated ray tracing view for red vector: 
{self.sphere.vector_direction}")
    
    def draw_reference_objects(self):
        """Draw some reference objects in the scene for the sphere 
view."""
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
            gl.glVertex3f(-s, -s, s); gl.glVertex3f(s, -s, s); 
gl.glVertex3f(s, s, s); gl.glVertex3f(-s, s, s)
            # Back  
            gl.glVertex3f(-s, -s, -s); gl.glVertex3f(-s, s, -s); 
gl.glVertex3f(s, s, -s); gl.glVertex3f(s, -s, -s)
            # Top
            gl.glVertex3f(-s, s, -s); gl.glVertex3f(-s, s, s); 
gl.glVertex3f(s, s, s); gl.glVertex3f(s, s, -s)
            # Bottom
            gl.glVertex3f(-s, -s, -s); gl.glVertex3f(s, -s, -s); 
gl.glVertex3f(s, -s, s); gl.glVertex3f(-s, -s, s)
            # Right
            gl.glVertex3f(s, -s, -s); gl.glVertex3f(s, s, -s); 
gl.glVertex3f(s, s, s); gl.glVertex3f(s, -s, s)
            # Left
            gl.glVertex3f(-s, -s, -s); gl.glVertex3f(-s, -s, s); 
gl.glVertex3f(-s, s, s); gl.glVertex3f(-s, s, -s)
            gl.glEnd()
            
            gl.glPopMatrix()
    
    
    def set_selected_object(self, object_name):
        """Set the currently selected object for manipulation."""
        if object_name in ["sphere", "cube", "screen", "none"]:
            self.selected_object = object_name
            print(f"DEBUG: Selected object changed to: {object_name}")
        
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
                self.red_cube_position = np.array([2.0, 0.0, 2.0])
            elif self.selected_object == "screen":
                self.screen_position = np.array([-3.0, 0.0, 0.0])
            self.Refresh()
    
    def set_screen_render_mode(self, mode):
        """Set the unified screen's rendering mode: 'simple' or 
'raytracing'."""
        if mode in ["simple", "raytracing"]:
            old_mode = self.screen_render_mode
            self.screen_render_mode = mode
            print(f"DEBUG: Switching unified screen render mode from 
{old_mode} to {mode}")
            
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
        """Toggle between screen modes: simple → raytracing → off → 
simple..."""
        if self.screen_enabled and self.screen_render_mode == "simple":
            # simple → raytracing
            self.screen_render_mode = "raytracing"
            # Ensure ray tracing screen is set up
            self.setup_unified_screen_system()
            # Explicitly enable sphere's ray tracing screen
            if hasattr(self.sphere, 'screen_enabled'):
                self.sphere.screen_enabled = True
            print(f"DEBUG: Switched to ray tracing screen mode")
        elif self.screen_enabled and self.screen_render_mode == 
"raytracing":
            # raytracing → off
            self.screen_enabled = False
            print(f"DEBUG: Screen disabled")
        else:
            # off → simple
            self.screen_enabled = True
            self.screen_render_mode = "simple"
            # Ensure framebuffer is set up for simple mode
            self.setup_framebuffer()
            # Explicitly disable sphere's ray tracing screen for simple 
mode
            if hasattr(self.sphere, 'screen_enabled'):
                self.sphere.screen_enabled = False
            print(f"DEBUG: Switched to simple 2D screen mode")
        
        # Sphere screen state is now explicitly set in each toggle case 
above
        # No additional sync needed
        
        sphere_enabled = getattr(self.sphere, 'screen_enabled', 'NOT SET')
        print(f"DEBUG: Screen state - canvas_enabled: 
{self.screen_enabled}, mode: {self.screen_render_mode}, sphere_enabled: 
{sphere_enabled}")
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
        """Draw a visual indicator showing where the 2D screen is 
looking."""
        # Draw a bright cyan line showing the 2D screen's view direction
        gl.glColor3f(0.0, 1.0, 1.0)  # Bright cyan to distinguish from red 
vector
        gl.glLineWidth(2.0)
        
        # Get actual sphere position
        sphere_pos = self.sphere.position
        
        gl.glBegin(gl.GL_LINES)
        # Start at actual sphere center
        gl.glVertex3f(sphere_pos[0], sphere_pos[1], sphere_pos[2])
        # End at view vector direction (what the 2D screen is showing)
        view_end = sphere_pos + self.view_vector * 2.5  # Make line 
shorter than red vector
        gl.glVertex3f(view_end[0], view_end[1], view_end[2])
        gl.glEnd()
        
        # Draw text indicator near the end
        gl.glPushMatrix()
        gl.glTranslatef(view_end[0], view_end[1], view_end[2])
        gl.glColor3f(0.0, 1.0, 1.0)  # Cyan
        # Draw a small indicator
        s = 0.05
        gl.glBegin(gl.GL_QUADS)
        gl.glVertex3f(-s, -s, s); gl.glVertex3f(s, -s, s); 
gl.glVertex3f(s, s, s); gl.glVertex3f(-s, s, s)
        gl.glVertex3f(-s, -s, -s); gl.glVertex3f(-s, s, -s); 
gl.glVertex3f(s, s, -s); gl.glVertex3f(s, -s, -s)
        gl.glEnd()
        gl.glPopMatrix()
        
        gl.glLineWidth(1.0)  # Reset line width
    
    
    def update_sphere_view_vector(self):
        """Update the sphere's view vector to match the red vector arrow 
direction."""
        print(f"DEBUG: ===== CANVAS update_sphere_view_vector() CALLED 
=====")
        
        # Use the sphere's red vector direction for ALL screen views 
(simple and ray tracing)
        if hasattr(self.sphere, 'vector_direction'):
            # Get the red vector direction and normalize it (roll is 
applied in camera coordinate system)
            red_vector = self.sphere.vector_direction
            self.view_vector = red_vector / np.linalg.norm(red_vector)
            
            print(f"DEBUG: Canvas syncing view_vector with sphere 
vector_direction: {red_vector}")
            print(f"DEBUG: Normalized view_vector: {self.view_vector}")
            
            # Update the ray tracing screen to follow this direction (if 
in ray tracing mode)
            if self.screen_render_mode == "raytracing":
                self.update_sphere_ray_tracing_view()
        else:
            # Fallback to default direction if no vector found
            self.view_vector = np.array([1.0, 0.0, 0.0])
            print(f"DEBUG: Canvas using fallback vector direction")
        
        print(f"DEBUG: Red vector direction: 
{self.sphere.vector_direction}")
        print(f"DEBUG: Normalized view vector: [{self.view_vector[0]:.3f}, 
{self.view_vector[1]:.3f}, {self.view_vector[2]:.3f}]")
        print(f"DEBUG: Red cube position: {self.red_cube_position}")
        
        # Calculate if cube should be visible
        cube_direction = (self.red_cube_position - self.sphere.position) / 
np.linalg.norm(self.red_cube_position - self.sphere.position)
        dot_product = np.dot(self.view_vector, cube_direction)
        angle_to_cube = np.arccos(np.clip(dot_product, -1.0, 1.0)) * 180.0 
/ np.pi
        
        print(f"DEBUG: Expected direction to cube: {cube_direction}")
        print(f"DEBUG: Actual view vector: {self.view_vector}")
        print(f"DEBUG: Dot product: {dot_product:.3f}")
        
        # If the view vector is not pointing toward the cube, suggest 
correction
        if angle_to_cube > 30:
            print(f"DEBUG: ⚠️ WARNING: View vector not pointing toward 
cube!")
            print(f"DEBUG: Consider setting vector direction to point 
toward cube")
            print(f"DEBUG: Suggested vector direction: {cube_direction * 
3.0}")  # Scale for visibility
        print(f"DEBUG: Angle to cube: {angle_to_cube:.1f}° (should be < 
30° to be visible)")
        print(f"DEBUG: Cube direction: [{cube_direction[0]:.3f}, 
{cube_direction[1]:.3f}, {cube_direction[2]:.3f}]")
    
    def update_view_vector(self):
        """Update the view vector based on sphere rotation (where the 
sphere is 'looking')."""
        # Always update the sphere's view vector based on current camera 
rotation
        # This ensures the 2D screen always shows what the sphere is 
"looking at"
        self.update_sphere_view_vector()
        
        # Force ray tracing screen update during user interaction
        if hasattr(self.sphere, 'screen_needs_update') and 
self.mouse_dragging:
            self.sphere.screen_needs_update = True
            self.sphere.screen_last_update = 0.0  # Force immediate update 
during interaction
    
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
        
        aspect_ratio = size.width / size.height if size.height > 0 else 
1.0
        
        # Choose projection mode based on camera_projection setting
        if self.camera_projection == "orthographic":
            # Orthographic projection - no perspective distortion
            # Calculate orthographic bounds based on camera distance and 
FOV
            if hasattr(self.sphere, 'cone_angle'):
                fov_vertical = self.sphere.cone_angle * 2.0
            else:
                fov_vertical = 60.0  # Default FOV
            
            # Convert FOV to orthographic bounds at camera distance
            ortho_height = self.camera_distance * 
math.tan(math.radians(fov_vertical / 2.0))
            ortho_width = ortho_height * aspect_ratio
            
            gl.glOrtho(-ortho_width, ortho_width, -ortho_height, 
ortho_height, 0.1, 100.0)
            print(f"DEBUG: Using orthographic projection - bounds: 
±{ortho_width:.2f} x ±{ortho_height:.2f}")
        else:
            # Perspective projection (default)
            if hasattr(self.sphere, 'cone_angle'):
                fov_vertical = self.sphere.cone_angle * 2.0
            else:
                fov_vertical = 60.0  # Default FOV
            glu.gluPerspective(fov_vertical, aspect_ratio, 0.1, 100.0)
            print(f"DEBUG: Using perspective projection - FOV: 
{fov_vertical:.1f}°")
        
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()
    
    def setup_camera(self):
        """Set up the camera view."""
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
        
        # Render the sphere (includes ray tracing screen if in raytracing 
mode)
        self.sphere.render()
        
        # Draw the multicolored cube
        self.draw_red_cube()  # Function name kept for compatibility
        
        # Draw the unified screen
        self.draw_unified_screen()
        
        # Screen rotation is now handled directly in the respective 
rendering methods
        
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
                print(f"DEBUG: Forced immediate ray tracing screen update 
due to vector change")
        
        elif self.selected_object == "cube":
            # Rotate the red cube
            self.object_rotations["cube"][1] += dx * 0.5  # Y rotation
            self.object_rotations["cube"][0] += dy * 0.5  # X rotation
        
        elif self.selected_object == "screen":
            # Rotate the 2D screen
            self.object_rotations["screen"][1] += dx * 0.5  # Y rotation
            self.object_rotations["screen"][0] += dy * 0.5  # X rotation
        
        # If no object selected, default to camera movement
        elif self.selected_object == "none":
            self.camera_rotation_y += dx * 0.5
            self.camera_rotation_x += dy * 0.5
            self.camera_rotation_x = max(-90, min(90, 
self.camera_rotation_x))
            # Note: Camera movement doesn't affect the red vector 
direction
    
        self.last_mouse_pos = current_pos
        self.Refresh()
    
    def on_mouse_wheel(self, event):
        """Handle mouse wheel for zooming."""
        delta = event.GetWheelRotation()
        zoom_factor = 1.1 if delta > 0 else 0.9
        
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
        
        if key_code == wx.WXK_LEFT:
            # Move camera left
            self.camera_position -= right * self.movement_speed
            moved = True
            
        elif key_code == wx.WXK_RIGHT:
            # Move camera right
            self.camera_position += right * self.movement_speed
            moved = True
            
        elif key_code == wx.WXK_UP:
            # Move camera up
            self.camera_position += up * self.movement_speed
            moved = True
            
        elif key_code == wx.WXK_DOWN:
            # Move camera down
            self.camera_position -= up * self.movement_speed
            moved = True
            
        elif key_code == ord('I') or key_code == ord('i'):
            # Move camera forward (into the screen)
            self.camera_position += forward * self.movement_speed
            moved = True
            
        elif key_code == ord('O') or key_code == ord('o'):
            # Move camera backward (out of the screen)
            self.camera_position -= forward * self.movement_speed
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
        
        # Refresh display if camera moved
        if moved:
            self.Refresh()
            
        event.Skip()
    
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
                "position": self.red_cube_position.tolist(),
                "size": float(self.red_cube_size)
            },
            "view_vector": self.view_vector.tolist(),
            "object_rotations": {k: v.tolist() for k, v in 
self.object_rotations.items()}
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
                self.red_cube_position = np.array(cb.get("position", [2.0, 
0.0, 2.0]))
                self.red_cube_size = cb.get("size", 0.3)
            
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
        super().__init__(None, title="3D Sphere Visualization", 
size=(1000, 800))
        
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
        file_menu.Append(wx.ID_NEW, "&New Scene\tCtrl+N", "Create a new 
scene")
        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_OPEN, "&Open Scene...\tCtrl+O", "Open a 
saved scene")
        file_menu.Append(wx.ID_SAVE, "&Save Scene\tCtrl+S", "Save the 
current scene")
        file_menu.Append(wx.ID_SAVEAS, "Save Scene &As...\tCtrl+Shift+S", 
"Save scene with a new name")
        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_EXIT, "E&xit\tCtrl+Q", "Exit the 
application")
        
        menubar.Append(file_menu, "&File")
        
        # Sphere menu
        sphere_menu = wx.Menu()
        
        # Color submenu
        color_menu = wx.Menu()
        color_menu.Append(wx.ID_ANY, "Set Sphere Color...", "Change sphere 
color")
        color_menu.Append(wx.ID_ANY, "Set Transparency...", "Change sphere 
transparency")
        sphere_menu.AppendSubMenu(color_menu, "Appearance")
        
        # Transform submenu
        transform_menu = wx.Menu()
        transform_menu.Append(wx.ID_ANY, "Reset Position", "Reset sphere 
to origin")
        transform_menu.Append(wx.ID_ANY, "Reset Rotation", "Reset sphere 
rotation")
        transform_menu.Append(wx.ID_ANY, "Reset Scale", "Reset sphere 
scale")
        transform_menu.AppendSeparator()
        transform_menu.Append(wx.ID_ANY, "Set Position...", "Set sphere 
position")
        transform_menu.Append(wx.ID_ANY, "Set Rotation...", "Set sphere 
rotation")
        transform_menu.Append(wx.ID_ANY, "Set Scale...", "Set sphere 
scale")
        sphere_menu.AppendSubMenu(transform_menu, "Transform")
        
        menubar.Append(sphere_menu, "Sphere")
        
        # Grid menu
        grid_menu = wx.Menu()
        
        # Grid types
        grid_menu.AppendCheckItem(wx.ID_ANY, "Longitude/Latitude Grid", 
"Toggle longitude/latitude grid")
        grid_menu.AppendCheckItem(wx.ID_ANY, "Concentric Circles", "Toggle 
concentric circles")
        grid_menu.AppendCheckItem(wx.ID_ANY, "Dot Particles", "Toggle dot 
particles")
        grid_menu.AppendCheckItem(wx.ID_ANY, "Neon Lines", "Toggle 
neon-style grid lines")
        grid_menu.AppendCheckItem(wx.ID_ANY, "Wireframe", "Toggle 
wireframe mode")
        
        grid_menu.AppendSeparator()
        
        # Grid colors submenu
        grid_colors_menu = wx.Menu()
        grid_colors_menu.Append(wx.ID_ANY, "Longitude/Latitude Color...", 
"Set longitude/latitude grid color")
        grid_colors_menu.Append(wx.ID_ANY, "Concentric Circles Color...", 
"Set concentric circles color")
        grid_colors_menu.Append(wx.ID_ANY, "Dot Particles Color...", "Set 
dot particles color")
        grid_colors_menu.Append(wx.ID_ANY, "Neon Lines Color...", "Set 
neon lines color")
        grid_colors_menu.Append(wx.ID_ANY, "Wireframe Color...", "Set 
wireframe color")
        grid_menu.AppendSubMenu(grid_colors_menu, "Grid Colors")
        
        # Grid parameters submenu
        grid_params_menu = wx.Menu()
        grid_params_menu.Append(wx.ID_ANY, "Set Longitude Lines...", "Set 
number of longitude lines")
        grid_params_menu.Append(wx.ID_ANY, "Set Latitude Lines...", "Set 
number of latitude lines")
        grid_params_menu.Append(wx.ID_ANY, "Set Concentric Rings...", "Set 
number of concentric rings")
        grid_params_menu.Append(wx.ID_ANY, "Set Dot Density...", "Set dot 
particle density")
        grid_params_menu.Append(wx.ID_ANY, "Set Neon Intensity...", "Set 
neon glow intensity")
        grid_params_menu.Append(wx.ID_ANY, "Set Wireframe Density...", 
"Set wireframe mesh density")
        grid_menu.AppendSubMenu(grid_params_menu, "Grid Parameters")
        
        menubar.Append(grid_menu, "Grids")
        
        # Vector menu
        vector_menu = wx.Menu()
        vector_menu.AppendCheckItem(wx.ID_ANY, "Show Vector", "Toggle 
vector visibility")
        vector_menu.AppendCheckItem(wx.ID_ANY, "Show Vector Orientation", 
"Toggle vector orientation indicator")
        vector_menu.AppendSeparator()
        vector_menu.AppendCheckItem(wx.ID_ANY, "Show Cone", "Toggle cone 
visibility")
        vector_menu.AppendCheckItem(wx.ID_ANY, "Show Pyramid", "Toggle 
pyramid visibility")
        vector_menu.AppendCheckItem(wx.ID_ANY, "Show Cuboid", "Toggle 
cuboid visibility")
        vector_menu.AppendSeparator()
        
        # Vector properties submenu
        vector_props_menu = wx.Menu()
        vector_props_menu.Append(wx.ID_ANY, "Set Direction...", "Set 
vector direction (x,y,z)")
        vector_props_menu.Append(wx.ID_ANY, "Set Length...", "Set vector 
length")
        vector_props_menu.Append(wx.ID_ANY, "Set Color...", "Set vector 
color")
        vector_props_menu.Append(wx.ID_ANY, "Set Thickness...", "Set 
vector line thickness")
        vector_menu.AppendSubMenu(vector_props_menu, "Vector Properties")
        
        # Vector orientation submenu
        vector_orientation_menu = wx.Menu()
        vector_orientation_menu.Append(wx.ID_ANY, "Set Roll Angle...", 
"Set vector roll orientation angle")
        vector_orientation_menu.AppendSeparator()
        vector_orientation_menu.Append(wx.ID_ANY, "Roll +15°", "Rotate 
camera +15° around vector axis")
        vector_orientation_menu.Append(wx.ID_ANY, "Roll -15°", "Rotate 
camera -15° around vector axis")
        vector_orientation_menu.Append(wx.ID_ANY, "Roll +45°", "Rotate 
camera +45° around vector axis")
        vector_orientation_menu.Append(wx.ID_ANY, "Roll -45°", "Rotate 
camera -45° around vector axis")
        vector_orientation_menu.Append(wx.ID_ANY, "Roll +90°", "Rotate 
camera +90° around vector axis")
        vector_orientation_menu.Append(wx.ID_ANY, "Roll -90°", "Rotate 
camera -90° around vector axis")
        vector_orientation_menu.AppendSeparator()
        vector_orientation_menu.Append(wx.ID_ANY, "Roll 180°", "Rotate 
camera 180° around vector axis")
        vector_orientation_menu.Append(wx.ID_ANY, "Reset Roll", "Reset 
roll angle to 0°")
        vector_menu.AppendSubMenu(vector_orientation_menu, "Vector 
Orientation")
        
        # Cone properties submenu
        cone_props_menu = wx.Menu()
        cone_props_menu.Append(wx.ID_ANY, "Set Cone Length...", "Set cone 
length")
        cone_props_menu.Append(wx.ID_ANY, "Set Cone Angle...", "Set cone 
half-angle in degrees")
        cone_props_menu.Append(wx.ID_ANY, "Set Cone Color...", "Set cone 
color")
        cone_props_menu.Append(wx.ID_ANY, "Set Cone Transparency...", "Set 
cone transparency")
        cone_props_menu.Append(wx.ID_ANY, "Set Cone Resolution...", "Set 
cone smoothness")
        cone_props_menu.AppendSeparator()
        cone_props_menu.AppendCheckItem(wx.ID_ANY, "Infinite Cone Length", 
"Make cone extend infinitely")
        vector_menu.AppendSubMenu(cone_props_menu, "Cone Properties")
        
        # Pyramid properties submenu
        pyramid_props_menu = wx.Menu()
        pyramid_props_menu.Append(wx.ID_ANY, "Set Pyramid Length...", "Set 
pyramid length")
        pyramid_props_menu.Append(wx.ID_ANY, "Set Horizontal Angle...", 
"Set pyramid horizontal half-angle")
        pyramid_props_menu.Append(wx.ID_ANY, "Set Vertical Angle...", "Set 
pyramid vertical half-angle")
        pyramid_props_menu.Append(wx.ID_ANY, "Set Pyramid Color...", "Set 
pyramid color")
        pyramid_props_menu.Append(wx.ID_ANY, "Set Pyramid 
Transparency...", "Set pyramid transparency")
        pyramid_props_menu.AppendSeparator()
        pyramid_props_menu.AppendCheckItem(wx.ID_ANY, "Infinite Pyramid 
Length", "Make pyramid extend infinitely")
        vector_menu.AppendSubMenu(pyramid_props_menu, "Pyramid 
Properties")
        
        # Cuboid properties submenu
        cuboid_props_menu = wx.Menu()
        cuboid_props_menu.Append(wx.ID_ANY, "Set Cuboid Length...", "Set 
cuboid length along vector")
        cuboid_props_menu.Append(wx.ID_ANY, "Set Cuboid Width...", "Set 
cuboid width perpendicular to vector")
        cuboid_props_menu.Append(wx.ID_ANY, "Set Cuboid Height...", "Set 
cuboid height perpendicular to vector")
        cuboid_props_menu.Append(wx.ID_ANY, "Set Cuboid Color...", "Set 
cuboid color")
        cuboid_props_menu.Append(wx.ID_ANY, "Set Cuboid Transparency...", 
"Set cuboid transparency")
        cuboid_props_menu.AppendSeparator()
        cuboid_props_menu.AppendCheckItem(wx.ID_ANY, "Infinite Cuboid 
Length", "Make cuboid extend infinitely")
        vector_menu.AppendSubMenu(cuboid_props_menu, "Cuboid Properties")
        
        # Near plane submenu
        near_plane_menu = wx.Menu()
        near_plane_menu.AppendCheckItem(wx.ID_ANY, "Enable Near Plane", 
"Toggle near plane cutting of shapes")
        near_plane_menu.Append(wx.ID_ANY, "Set Near Plane Distance...", 
"Set distance of cutting plane from sphere center")
        vector_menu.AppendSubMenu(near_plane_menu, "Near Plane (Truncate 
Shapes)")
        
        # Sphere intersection submenu
        sphere_intersection_menu = wx.Menu()
        sphere_intersection_menu.AppendCheckItem(wx.ID_ANY, "Show Sphere 
Intersections", "Show where shapes intersect sphere surface")
        sphere_intersection_menu.Append(wx.ID_ANY, "Set Intersection 
Color...", "Set color of sphere intersection areas")
        vector_menu.AppendSubMenu(sphere_intersection_menu, "Sphere 
Intersections")
        
        # Preset directions submenu
        vector_presets_menu = wx.Menu()
        vector_presets_menu.Append(wx.ID_ANY, "X-Axis (1,0,0)", "Set 
vector to positive X direction")
        vector_presets_menu.Append(wx.ID_ANY, "Y-Axis (0,1,0)", "Set 
vector to positive Y direction")
        vector_presets_menu.Append(wx.ID_ANY, "Z-Axis (0,0,1)", "Set 
vector to positive Z direction")
        vector_presets_menu.Append(wx.ID_ANY, "-X-Axis (-1,0,0)", "Set 
vector to negative X direction")
        vector_presets_menu.Append(wx.ID_ANY, "-Y-Axis (0,-1,0)", "Set 
vector to negative Y direction")
        vector_presets_menu.Append(wx.ID_ANY, "-Z-Axis (0,0,-1)", "Set 
vector to negative Z direction")
        vector_presets_menu.AppendSeparator()
        vector_presets_menu.Append(wx.ID_ANY, "Diagonal (1,1,1)", "Set 
vector to diagonal direction")
        vector_presets_menu.Append(wx.ID_ANY, "Random Direction", "Set 
vector to random direction")
        vector_menu.AppendSubMenu(vector_presets_menu, "Preset 
Directions")
        
        menubar.Append(vector_menu, "Vector")
        
        # View menu
        view_menu = wx.Menu()
        view_menu.Append(wx.ID_ANY, "Reset Camera", "Reset camera to 
default position")
        view_menu.AppendSeparator()
        
        # Camera movement submenu
        camera_movement_menu = wx.Menu()
        camera_movement_menu.Append(wx.ID_ANY, "Set Camera Position...", 
"Set camera position (x,y,z)")
        camera_movement_menu.Append(wx.ID_ANY, "Set Camera Distance...", 
"Set camera distance from origin")
        camera_movement_menu.AppendSeparator()
        camera_movement_menu.Append(wx.ID_ANY, "Move Forward", "Move 
camera forward")
        camera_movement_menu.Append(wx.ID_ANY, "Move Backward", "Move 
camera backward")
        camera_movement_menu.Append(wx.ID_ANY, "Move Left", "Move camera 
left")
        camera_movement_menu.Append(wx.ID_ANY, "Move Right", "Move camera 
right")
        camera_movement_menu.Append(wx.ID_ANY, "Move Up", "Move camera 
up")
        camera_movement_menu.Append(wx.ID_ANY, "Move Down", "Move camera 
down")
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
        sphere_movement_menu.Append(wx.ID_ANY, "Move Sphere Left", "Move 
sphere left")
        sphere_movement_menu.Append(wx.ID_ANY, "Move Sphere Right", "Move 
sphere right")
        sphere_movement_menu.Append(wx.ID_ANY, "Move Sphere Up", "Move 
sphere up")
        sphere_movement_menu.Append(wx.ID_ANY, "Move Sphere Down", "Move 
sphere down")
        sphere_movement_menu.AppendSeparator()
        sphere_movement_menu.Append(wx.ID_ANY, "Center Sphere", "Move 
sphere back to origin (0,0,0)")
        view_menu.AppendSubMenu(sphere_movement_menu, "Sphere Movement")
        
        view_menu.AppendSeparator()
        view_menu.Append(wx.ID_ANY, "Center Camera on Cube", "Move camera 
to look at the multicolored cube")
        view_menu.AppendSeparator()
        view_menu.AppendCheckItem(wx.ID_ANY, "Wireframe Mode", "Toggle 
wireframe rendering mode")
        view_menu.AppendCheckItem(wx.ID_ANY, "Enable Lighting", "Toggle 
lighting on/off")
        view_menu.AppendSeparator()
        view_menu.AppendCheckItem(wx.ID_ANY, "Show Normal Rays", "Show 
surface normal vectors")
        
        # Normal rays submenu
        normal_rays_menu = wx.Menu()
        normal_rays_menu.Append(wx.ID_ANY, "Set Ray Length...", "Set 
length of normal rays")
        normal_rays_menu.Append(wx.ID_ANY, "Set Ray Density...", "Set 
density of normal rays")
        normal_rays_menu.Append(wx.ID_ANY, "Set Ray Color...", "Set color 
of normal rays")
        normal_rays_menu.Append(wx.ID_ANY, "Set Ray Thickness...", "Set 
thickness of normal rays")
        view_menu.AppendSubMenu(normal_rays_menu, "Normal Ray Properties")
        
        view_menu.AppendSeparator()
        view_menu.AppendCheckItem(wx.ID_ANY, "Show Intersection Normals", 
"Show normal rays on intersection surfaces")
        
        # Intersection normal rays submenu
        intersection_normals_menu = wx.Menu()
        intersection_normals_menu.Append(wx.ID_ANY, "Set Intersection Ray 
Length...", "Set length of intersection normal rays")
        intersection_normals_menu.Append(wx.ID_ANY, "Set Intersection Ray 
Density...", "Set density of intersection normal rays")
        intersection_normals_menu.Append(wx.ID_ANY, "Set Intersection Ray 
Color...", "Set color of intersection normal rays")
        intersection_normals_menu.Append(wx.ID_ANY, "Set Intersection Ray 
Thickness...", "Set thickness of intersection normal rays")
        view_menu.AppendSubMenu(intersection_normals_menu, "Intersection 
Normal Properties")
        
        view_menu.AppendSeparator()
        view_menu.AppendCheckItem(wx.ID_ANY, "Show Truncation Normals", 
"Show normal rays on truncation surfaces")
        
        # Truncation normal rays submenu
        truncation_normals_menu = wx.Menu()
        truncation_normals_menu.Append(wx.ID_ANY, "Set Truncation Ray 
Length...", "Set length of truncation normal rays")
        truncation_normals_menu.Append(wx.ID_ANY, "Set Truncation Ray 
Density...", "Set density of truncation normal rays")
        truncation_normals_menu.Append(wx.ID_ANY, "Set Truncation Ray 
Color...", "Set color of truncation normal rays")
        truncation_normals_menu.Append(wx.ID_ANY, "Set Truncation Ray 
Thickness...", "Set thickness of truncation normal rays")
        view_menu.AppendSubMenu(truncation_normals_menu, "Truncation 
Normal Properties")
        
        menubar.Append(view_menu, "View")
        
        # Screen menu (Ray Tracing)
        screen_menu = wx.Menu()
        
        # Main screen toggle
        screen_menu.AppendCheckItem(wx.ID_ANY, "Show Ray Tracing Screen", 
"Show 2D screen with ray-traced image")
        screen_menu.AppendSeparator()
        
        # Screen properties
        screen_menu.Append(wx.ID_ANY, "Set Screen Position...", "Set 3D 
position of the screen")
        screen_menu.Append(wx.ID_ANY, "Set Screen Rotation...", "Set 
rotation of the screen")
        screen_menu.Append(wx.ID_ANY, "Set Screen Size...", "Set width and 
height of the screen")
        screen_menu.AppendSeparator()
        
        # Rendering options
        render_mode_menu = wx.Menu()
        render_mode_menu.AppendRadioItem(wx.ID_ANY, "Ray Tracing", "Basic 
ray tracing")
        render_mode_menu.AppendRadioItem(wx.ID_ANY, "Path Tracing", "Path 
tracing with reflections")
        render_mode_menu.AppendRadioItem(wx.ID_ANY, "PBR Rendering", 
"Physically Based Rendering")
        render_mode_menu.AppendRadioItem(wx.ID_ANY, "Ray Marching", "Ray 
marching with signed distance functions")
        screen_menu.AppendSubMenu(render_mode_menu, "Render Mode")
        
        # Projection mode options
        projection_mode_menu = wx.Menu()
        projection_mode_menu.AppendRadioItem(wx.ID_ANY, "Perspective 
Projection", "Standard perspective projection with depth")
        projection_mode_menu.AppendRadioItem(wx.ID_ANY, "Orthographic 
Projection", "Orthographic projection without perspective distortion")
        screen_menu.AppendSubMenu(projection_mode_menu, "Projection Mode")
        
        # 2D Screen projection mode options
        screen_projection_menu = wx.Menu()
        screen_projection_menu.AppendRadioItem(wx.ID_ANY, "2D Screen 
Perspective", "2D screen uses perspective projection")
        screen_projection_menu.AppendRadioItem(wx.ID_ANY, "2D Screen 
Orthographic", "2D screen uses orthographic projection")
        screen_menu.AppendSubMenu(screen_projection_menu, "2D Screen 
Projection")
        
        screen_menu.AppendSeparator()
        screen_menu.Append(wx.ID_ANY, "Set Screen Resolution...", "Set 
texture resolution")
        screen_menu.Append(wx.ID_ANY, "Set Camera Position...", "Set 
virtual camera position")
        screen_menu.Append(wx.ID_ANY, "Set Camera Target...", "Set virtual 
camera target")
        screen_menu.Append(wx.ID_ANY, "Set Update Rate...", "Set screen 
refresh rate")
        screen_menu.Append(wx.ID_ANY, "Set Samples...", "Set anti-aliasing 
samples")
        screen_menu.Append(wx.ID_ANY, "Set Max Bounces...", "Set maximum 
ray bounces for reflections")
        
        menubar.Append(screen_menu, "Screen")
        
        # Objects menu
        objects_menu = wx.Menu()
        
        # Object selection submenu
        selection_menu = wx.Menu()
        self.sphere_selection_item = 
selection_menu.AppendRadioItem(wx.ID_ANY, "Camera Sphere", "Select sphere 
for rotation control")
        self.cube_selection_item = 
selection_menu.AppendRadioItem(wx.ID_ANY, "Red Cube", "Select red cube for 
manipulation")
        self.screen_selection_item = 
selection_menu.AppendRadioItem(wx.ID_ANY, "2D Screen", "Select 2D screen 
for positioning")
        selection_menu.AppendSeparator()
        self.none_selection_item = 
selection_menu.AppendRadioItem(wx.ID_ANY, "None", "No object selected")
        
        objects_menu.AppendSubMenu(selection_menu, "Select Object")
        
        objects_menu.AppendSeparator()
        
        # Selected object manipulation submenu
        manipulation_menu = wx.Menu()
        
        # Rotation controls
        rotation_submenu = wx.Menu()
        rotation_submenu.Append(wx.ID_ANY, "Set Selected Rotation...", 
"Set selected object rotation (pitch, yaw, roll)")
        rotation_submenu.AppendSeparator()
        rotation_submenu.Append(wx.ID_ANY, "Rotate +15° X", "Rotate 
selected object +15° around X axis")
        rotation_submenu.Append(wx.ID_ANY, "Rotate -15° X", "Rotate 
selected object -15° around X axis")
        rotation_submenu.Append(wx.ID_ANY, "Rotate +15° Y", "Rotate 
selected object +15° around Y axis")
        rotation_submenu.Append(wx.ID_ANY, "Rotate -15° Y", "Rotate 
selected object -15° around Y axis")
        rotation_submenu.Append(wx.ID_ANY, "Rotate +15° Z", "Rotate 
selected object +15° around Z axis")
        rotation_submenu.Append(wx.ID_ANY, "Rotate -15° Z", "Rotate 
selected object -15° around Z axis")
        rotation_submenu.AppendSeparator()
        rotation_submenu.Append(wx.ID_ANY, "Reset Selected Rotation", 
"Reset selected object rotation to zero")
        manipulation_menu.AppendSubMenu(rotation_submenu, "Rotate Selected 
Object")
        
        # Position controls
        position_submenu = wx.Menu()
        position_submenu.Append(wx.ID_ANY, "Set Selected Position...", 
"Set selected object position (x, y, z)")
        position_submenu.AppendSeparator()
        position_submenu.Append(wx.ID_ANY, "Move Selected Forward", "Move 
selected object forward")
        position_submenu.Append(wx.ID_ANY, "Move Selected Backward", "Move 
selected object backward")
        position_submenu.Append(wx.ID_ANY, "Move Selected Left", "Move 
selected object left")
        position_submenu.Append(wx.ID_ANY, "Move Selected Right", "Move 
selected object right")
        position_submenu.Append(wx.ID_ANY, "Move Selected Up", "Move 
selected object up")
        position_submenu.Append(wx.ID_ANY, "Move Selected Down", "Move 
selected object down")
        position_submenu.AppendSeparator()
        position_submenu.Append(wx.ID_ANY, "Reset Selected Position", 
"Reset selected object to default position")
        manipulation_menu.AppendSubMenu(position_submenu, "Move Selected 
Object")
        
        objects_menu.AppendSubMenu(manipulation_menu, "Manipulate 
Selected")
        
        objects_menu.AppendSeparator()
        
        # Object manipulation options
        objects_menu.Append(wx.ID_ANY, "Reset Selected Object", "Reset 
selected object to default position/rotation")
        objects_menu.Append(wx.ID_ANY, "Object Properties...", "Edit 
properties of selected object")
        
        objects_menu.AppendSeparator()
        
        # Rotation mode
        rotation_menu = wx.Menu()
        self.local_rotation_item = 
rotation_menu.AppendRadioItem(wx.ID_ANY, "Local Rotation", "Rotate around 
object's local axes")
        self.world_rotation_item = 
rotation_menu.AppendRadioItem(wx.ID_ANY, "World Rotation", "Rotate around 
world axes")
        objects_menu.AppendSubMenu(rotation_menu, "Rotation Mode")
        
        menubar.Append(objects_menu, "Objects")
        
        # Camera Angles menu (for 2D screen FOV control)
        camera_menu = wx.Menu()
        
        # Geometry angle controls that affect 2D camera FOV
        camera_menu.Append(wx.ID_ANY, "Set Cone Angle...", "Set cone angle 
(affects 2D camera vertical FOV)")
        camera_menu.Append(wx.ID_ANY, "Set Pyramid Horizontal Angle...", 
"Set pyramid horizontal angle (affects 2D camera horizontal FOV)")
        camera_menu.Append(wx.ID_ANY, "Set Pyramid Vertical Angle...", 
"Set pyramid vertical angle (affects 2D camera vertical FOV)")
        camera_menu.Append(wx.ID_ANY, "Set Cuboid Width...", "Set cuboid 
width (affects 2D camera horizontal view)")
        camera_menu.Append(wx.ID_ANY, "Set Cuboid Height...", "Set cuboid 
height (affects 2D camera vertical view)")
        
        camera_menu.AppendSeparator()
        
        # Quick presets for common FOV angles
        preset_menu = wx.Menu()
        preset_menu.Append(wx.ID_ANY, "Narrow FOV (20°)", "Set narrow 
field of view")
        preset_menu.Append(wx.ID_ANY, "Normal FOV (45°)", "Set normal 
field of view")
        preset_menu.Append(wx.ID_ANY, "Wide FOV (70°)", "Set wide field of 
view")
        preset_menu.Append(wx.ID_ANY, "Ultra Wide FOV (90°)", "Set ultra 
wide field of view")
        camera_menu.AppendSubMenu(preset_menu, "FOV Presets")
        
        camera_menu.AppendSeparator()
        
        # Screen rendering mode selection
        screen_render_menu = wx.Menu()
        self.simple_render_item = 
screen_render_menu.AppendRadioItem(wx.ID_ANY, "Simple Rendering", "Fast 
framebuffer rendering (original)")
        self.raytracing_render_item = 
screen_render_menu.AppendRadioItem(wx.ID_ANY, "Ray Tracing Rendering", 
"Advanced ray tracing rendering")
        camera_menu.AppendSubMenu(screen_render_menu, "Screen Rendering 
Mode")
        
        camera_menu.AppendSeparator()
        
        # Screen toggle
        camera_menu.AppendCheckItem(wx.ID_ANY, "Show 2D Screen", "Toggle 
2D screen: Simple → Ray Tracing → Off")
        
        # Screen disable option
        camera_menu.Append(wx.ID_ANY, "Disable Screen", "Turn off the 2D 
screen completely")
        
        camera_menu.AppendSeparator()
        camera_menu.Append(wx.ID_ANY, "Reset to Default Angles", "Reset 
all angles to default values")
        
        menubar.Append(camera_menu, "Camera Angles")
        
        # Help menu
        help_menu = wx.Menu()
        help_menu.Append(wx.ID_ANY, "Keyboard Controls...", "Show keyboard 
control shortcuts")
        help_menu.Append(wx.ID_ANY, "About Camera Movement...", "About 
camera movement controls")
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
            print("DEBUG: Found cone color in label - calling 
set_cone_color()")
            self.set_cone_color()
            return
        
        if "Set Pyramid Color" in label:
            print("DEBUG: Found pyramid color in label - calling 
set_pyramid_color()")
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
            self.canvas.update_sphere_view_vector()  # Update ray tracing 
camera
            self.canvas.Refresh()
        elif label == "Y-Axis (0,1,0)":
            self.sphere.set_vector_direction(0, 1, 0)
            self.canvas.update_sphere_view_vector()  # Update ray tracing 
camera
            self.canvas.Refresh()
        elif label == "Z-Axis (0,0,1)":
            self.sphere.set_vector_direction(0, 0, 1)
            self.canvas.update_sphere_view_vector()  # Update ray tracing 
camera
            self.canvas.Refresh()
        elif label == "-X-Axis (-1,0,0)":
            self.sphere.set_vector_direction(-1, 0, 0)
            self.canvas.update_sphere_view_vector()  # Update ray tracing 
camera
            self.canvas.Refresh()
        elif label == "-Y-Axis (0,-1,0)":
            self.sphere.set_vector_direction(0, -1, 0)
            self.canvas.update_sphere_view_vector()  # Update ray tracing 
camera
            self.canvas.Refresh()
        elif label == "-Z-Axis (0,0,-1)":
            self.sphere.set_vector_direction(0, 0, -1)
            self.canvas.update_sphere_view_vector()  # Update ray tracing 
camera
            self.canvas.Refresh()
        elif label == "Diagonal (1,1,1)":
            self.sphere.set_vector_direction(1, 1, 1)
            self.canvas.update_sphere_view_vector()  # Update ray tracing 
camera
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
            self.canvas.movement_speed = min(1.0, 
self.canvas.movement_speed * 1.5)
            wx.MessageBox(f"Movement speed: 
{self.canvas.movement_speed:.2f}", "Speed Updated", wx.OK | 
wx.ICON_INFORMATION)
        elif label == "Decrease Movement Speed":
            self.canvas.movement_speed = max(0.05, 
self.canvas.movement_speed / 1.5)
            wx.MessageBox(f"Movement speed: 
{self.canvas.movement_speed:.2f}", "Speed Updated", wx.OK | 
wx.ICON_INFORMATION)
        
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
            wx.MessageBox("Sphere centered at origin (0,0,0)", "Sphere 
Centered", wx.OK | wx.ICON_INFORMATION)
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
        elif label == "Red Cube":
            self.canvas.set_selected_object("cube")
        elif label == "2D Screen":
            self.canvas.set_selected_object("screen")
        elif label == "None":
            self.canvas.set_selected_object("none")
        
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
        
        info = f"Selected Object: {selected.title()}\n\n"
        
        if selected == "sphere":
            info += f"Position: {self.canvas.camera_position}\n"
            info += f"Rotation X: {self.canvas.camera_rotation_x:.1f}°\n"
            info += f"Rotation Y: {self.canvas.camera_rotation_y:.1f}°\n"
            info += f"Distance: {self.canvas.camera_distance:.1f}\n"
        elif selected == "cube":
            info += f"Position: {self.canvas.red_cube_position}\n"
            info += f"Size: {self.canvas.red_cube_size:.2f}\n"
            cube_rot = self.canvas.object_rotations['cube']
            info += f"Rotation: [{cube_rot[0]:.1f}°, {cube_rot[1]:.1f}°, 
{cube_rot[2]:.1f}°]\n"
        elif selected == "screen":
            info += f"Screen Status: {'Enabled' if 
self.canvas.screen_enabled else 'Disabled'}\n"
            info += f"Render Mode: 
{self.canvas.screen_render_mode.title()}\n"
            info += f"Position: {self.canvas.screen_position}\n"
            info += f"Size: {self.canvas.screen_width:.2f} x 
{self.canvas.screen_height:.2f}\n"
            
            if self.canvas.screen_render_mode == "simple":
                info += f"Resolution: {self.canvas.framebuffer_width} x 
{self.canvas.framebuffer_height}\n"
            else:  # raytracing mode
                info += f"Resolution: {self.sphere.screen_resolution}\n"
                info += f"Ray Tracing Mode: 
{self.sphere.screen_render_mode}\n"
                info += f"Samples: {self.sphere.screen_samples}\n"
                info += f"Max Bounces: {self.sphere.screen_max_bounces}\n"
                info += f"Update Rate: 
{self.sphere.screen_update_rate:.2f}s\n"
            
            screen_rot = self.canvas.object_rotations['screen']
            info += f"Rotation: [{screen_rot[0]:.1f}°, 
{screen_rot[1]:.1f}°, {screen_rot[2]:.1f}°]\n"
        
        info += f"\nRotation Mode: {self.canvas.rotation_mode.title()}"
        
        # Add sphere system information
        info += f"\n\n--- Sphere System Settings ---"
        sphere_pos = self.sphere.position
        info += f"\nSystem Position: [{sphere_pos[0]:.2f}, 
{sphere_pos[1]:.2f}, {sphere_pos[2]:.2f}]"
        info += f"\nSphere Radius: {self.sphere.radius:.2f}"
        
        # Add vector information
        info += f"\n\n--- Vector Settings ---"
        info += f"\nVector Enabled: {'Yes' if self.sphere.vector_enabled 
else 'No'}"
        if self.sphere.vector_enabled:
            vec_dir = self.sphere.vector_direction
            info += f"\nDirection: [{vec_dir[0]:.2f}, {vec_dir[1]:.2f}, 
{vec_dir[2]:.2f}]"
            info += f"\nLength: {self.sphere.vector_length:.2f}"
            info += f"\nRoll Orientation: {self.sphere.vector_roll:.1f}°"
        
        # Add main camera information
        info += f"\n\n--- Main Camera Settings ---"
        cam_pos = self.canvas.camera_position
        info += f"\nPosition: [{cam_pos[0]:.2f}, {cam_pos[1]:.2f}, 
{cam_pos[2]:.2f}]"
        info += f"\nDistance: {self.canvas.camera_distance:.1f}"
        info += f"\nRotation: X={self.canvas.camera_rotation_x:.1f}°, 
Y={self.canvas.camera_rotation_y:.1f}°"
        info += f"\nMovement Speed: {self.canvas.movement_speed:.2f}"
        
        # Add camera FOV information
        info += f"\n\n--- 2D Camera Settings ---"
        info += f"\nCone Angle: {self.sphere.cone_angle:.1f}° (FOV: 
{self.sphere.cone_angle * 2:.1f}°)"
        info += f"\nPyramid H-Angle: 
{self.sphere.pyramid_angle_horizontal:.1f}°"
        info += f"\nPyramid V-Angle: 
{self.sphere.pyramid_angle_vertical:.1f}°"
        if hasattr(self.sphere, 'cuboid_width') and hasattr(self.sphere, 
'cuboid_height'):
            info += f"\nCuboid Size: {self.sphere.cuboid_width:.1f} x 
{self.sphere.cuboid_height:.1f}"
        
        wx.MessageBox(info, "Object Properties", wx.OK | 
wx.ICON_INFORMATION)
    
    def update_menu_states(self):
        """Update the checked state of menu items."""
        menubar = self.GetMenuBar()
        
        # Update object selection radio items
        if hasattr(self, 'sphere_selection_item'):
            self.sphere_selection_item.Check(self.canvas.selected_object 
== "sphere")
        if hasattr(self, 'cube_selection_item'):
            self.cube_selection_item.Check(self.canvas.selected_object == 
"cube")
        if hasattr(self, 'screen_selection_item'):
            self.screen_selection_item.Check(self.canvas.selected_object 
== "screen")
        if hasattr(self, 'none_selection_item'):
            self.none_selection_item.Check(self.canvas.selected_object == 
"none")
        
        # Update rotation mode radio items
        if hasattr(self, 'local_rotation_item'):
            self.local_rotation_item.Check(self.canvas.rotation_mode == 
"local")
        if hasattr(self, 'world_rotation_item'):
            self.world_rotation_item.Check(self.canvas.rotation_mode == 
"world")
        
        # Update screen rendering mode radio items
        if hasattr(self, 'simple_render_item'):
            self.simple_render_item.Check(self.canvas.screen_render_mode 
== "simple")
        if hasattr(self, 'raytracing_render_item'):
            
self.raytracing_render_item.Check(self.canvas.screen_render_mode == 
"raytracing")
        
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
                        item.Check(GridType.LONGITUDE_LATITUDE in 
self.sphere.active_grids)
                    elif label == "Concentric Circles":
                        item.Check(GridType.CONCENTRIC_CIRCLES in 
self.sphere.active_grids)
                    elif label == "Dot Particles":
                        item.Check(GridType.DOT_PARTICLES in 
self.sphere.active_grids)
                    elif label == "Neon Lines":
                        item.Check(GridType.NEON_LINES in 
self.sphere.active_grids)
                    elif label == "Wireframe":
                        item.Check(GridType.WIREFRAME in 
self.sphere.active_grids)
                
    def set_sphere_color(self):
        """Open color dialog for sphere color."""
        color_data = wx.ColourData()
        current_color = self.sphere.sphere_color[:3] * 255
        color_data.SetColour(wx.Colour(int(current_color[0]), 
int(current_color[1]), int(current_color[2])))
        
        dialog = wx.ColourDialog(self, color_data)
        if dialog.ShowModal() == wx.ID_OK:
            color = dialog.GetColourData().GetColour()
            self.sphere.set_sphere_color((color.Red() / 255.0, 
color.Green() / 255.0, color.Blue() / 255.0))
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
        dialog = wx.TextEntryDialog(self, f"Enter position (x,y,z):", "Set 
Position", 
f"{current_pos[0]:.2f},{current_pos[1]:.2f},{current_pos[2]:.2f}")
        if dialog.ShowModal() == wx.ID_OK:
            try:
                coords = [float(x.strip()) for x in 
dialog.GetValue().split(',')]
                if len(coords) == 3:
                    # Store the old position to calculate the offset
                    old_pos = self.sphere.position.copy()
                    
                    # Set the new sphere position
                    self.sphere.set_position(*coords)
                    
                    # Update the 2D screen position to follow the sphere
                    
self.canvas.update_screen_position_for_sphere_move(old_pos, 
self.sphere.position)
                    
                    self.canvas.Refresh()
            except ValueError:
                wx.MessageBox("Invalid position format. Use: x,y,z", 
"Error", wx.OK | wx.ICON_ERROR)
                dialog.Destroy()
    
    def set_sphere_rotation(self):
        """Set sphere rotation with input dialog."""
        current_rot = self.sphere.rotation
        dialog = wx.TextEntryDialog(self, f"Enter rotation 
(pitch,yaw,roll) in degrees:", "Set Rotation", 
f"{current_rot[0]:.1f},{current_rot[1]:.1f},{current_rot[2]:.1f}")
        if dialog.ShowModal() == wx.ID_OK:
            try:
                angles = [float(x.strip()) for x in 
dialog.GetValue().split(',')]
                if len(angles) == 3:
                    self.sphere.set_rotation(*angles)
                    self.canvas.Refresh()
            except ValueError:
                wx.MessageBox("Invalid rotation format. Use: 
pitch,yaw,roll", "Error", wx.OK | wx.ICON_ERROR)
                dialog.Destroy()
    
    def set_sphere_scale(self):
        """Set sphere scale with input dialog."""
        current_scale = self.sphere.scale
        dialog = wx.TextEntryDialog(self, f"Enter scale (sx,sy,sz):", "Set 
Scale", 
f"{current_scale[0]:.2f},{current_scale[1]:.2f},{current_scale[2]:.2f}")
        if dialog.ShowModal() == wx.ID_OK:
            try:
                scales = [float(x.strip()) for x in 
dialog.GetValue().split(',')]
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
        color_data.SetColour(wx.Colour(int(current_color[0]), 
int(current_color[1]), int(current_color[2])))
    
        dialog = wx.ColourDialog(self, color_data)
        if dialog.ShowModal() == wx.ID_OK:
            color = dialog.GetColourData().GetColour()
            new_color = (color.Red() / 255.0, color.Green() / 255.0, 
color.Blue() / 255.0, 1.0)
            self.sphere.set_grid_color(grid_type, new_color)
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_longitude_lines(self):
        """Set number of longitude lines."""
        dialog = wx.NumberEntryDialog(self, "Enter number of longitude 
lines:", "Lines:", "Longitude Lines", self.sphere.longitude_lines, 4, 64)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.longitude_lines = dialog.GetValue()
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_latitude_lines(self):
        """Set number of latitude lines."""
        dialog = wx.NumberEntryDialog(self, "Enter number of latitude 
lines:", "Lines:", "Latitude Lines", self.sphere.latitude_lines, 3, 32)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.latitude_lines = dialog.GetValue()
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_concentric_rings(self):
        """Set number of concentric rings."""
        dialog = wx.NumberEntryDialog(self, "Enter number of concentric 
rings:", "Rings:", "Concentric Rings", self.sphere.concentric_rings, 3, 
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
        dialog = wx.NumberEntryDialog(self, "Enter neon intensity 
(0-200):", "Intensity:", "Neon Intensity", current_intensity, 0, 200)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.neon_intensity = dialog.GetValue() / 100.0
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_wireframe_density(self):
        """Set wireframe mesh density."""
        dialog = wx.NumberEntryDialog(self, "Enter wireframe density 
(4-64):", "Density:", "Wireframe Density", 
self.sphere.wireframe_resolution, 4, 64)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_wireframe_resolution(dialog.GetValue())
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_vector_direction(self):
        """Set vector direction with input dialog."""
        current_dir = self.sphere.vector_direction
        dialog = wx.TextEntryDialog(self, f"Enter vector direction 
(x,y,z):", "Set Vector Direction", 
f"{current_dir[0]:.2f},{current_dir[1]:.2f},{current_dir[2]:.2f}")
        if dialog.ShowModal() == wx.ID_OK:
            try:
                coords = [float(x.strip()) for x in 
dialog.GetValue().split(',')]
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
        dialog = wx.NumberEntryDialog(self, "Enter vector length (relative 
to sphere radius):", "Length:", "Vector Length", int(current_length * 10), 
1, 100)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_vector_length(dialog.GetValue() / 10.0)
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_vector_color(self):
        """Set vector color with color dialog."""
        color_data = wx.ColourData()
        current_color = self.sphere.vector_color[:3] * 255
        color_data.SetColour(wx.Colour(int(current_color[0]), 
int(current_color[1]), int(current_color[2])))
        
        dialog = wx.ColourDialog(self, color_data)
        if dialog.ShowModal() == wx.ID_OK:
            color = dialog.GetColourData().GetColour()
            new_color = (color.Red() / 255.0, color.Green() / 255.0, 
color.Blue() / 255.0, 1.0)
            self.sphere.set_vector_color(new_color)
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_vector_thickness(self):
        """Set vector thickness with input dialog."""
        current_thickness = int(self.sphere.vector_thickness)
        dialog = wx.NumberEntryDialog(self, "Enter vector thickness 
(1-10):", "Thickness:", "Vector Thickness", current_thickness, 1, 10)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_vector_thickness(float(dialog.GetValue()))
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_vector_roll(self):
        """Set vector roll orientation with input dialog."""
        current_roll = self.sphere.vector_roll
        dialog = wx.NumberEntryDialog(self, f"Enter roll angle in 
degrees:", "Roll Angle:", "Set Vector Roll", int(current_roll), -360, 360)
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
                                   f"Current position: 
({current_pos[0]:.2f}, {current_pos[1]:.2f}, {current_pos[2]:.2f})\n"
                                   "Enter new position as 'x, y, z':", 
                                   "Set Camera Position", 
                                   
f"{current_pos[0]:.2f},{current_pos[1]:.2f},{current_pos[2]:.2f}")
        if dialog.ShowModal() == wx.ID_OK:
            try:
                values = [float(x.strip()) for x in 
dialog.GetValue().split(',')]
                if len(values) == 3:
                    self.canvas.camera_position = np.array(values)
                    self.canvas.Refresh()
                    wx.MessageBox(f"Camera position set to 
({values[0]:.2f}, {values[1]:.2f}, {values[2]:.2f})", 
                                 "Camera Updated", wx.OK | 
wx.ICON_INFORMATION)
                else:
                    wx.MessageBox("Please enter exactly 3 values separated 
by commas", "Invalid Input", wx.OK | wx.ICON_ERROR)
            except ValueError:
                wx.MessageBox("Invalid position format. Use: x,y,z (e.g., 
0,0,0)", "Error", wx.OK | wx.ICON_ERROR)
        dialog.Destroy()
    
    def set_main_camera_distance(self):
        """Set main camera distance with input dialog."""
        current_distance = self.canvas.camera_distance
        dialog = wx.NumberEntryDialog(self, "Enter camera distance from 
origin:", "Distance:", "Camera Distance", 
                                     int(current_distance * 10), 10, 200)
        if dialog.ShowModal() == wx.ID_OK:
            self.canvas.camera_distance = dialog.GetValue() / 10.0
            self.canvas.Refresh()
            wx.MessageBox(f"Camera distance set to: 
{self.canvas.camera_distance:.1f}", "Distance Updated", wx.OK | 
wx.ICON_INFORMATION)
        dialog.Destroy()
    
    def move_camera_forward(self):
        """Move camera forward."""
        forward = self.canvas.get_camera_forward_vector()
        self.canvas.camera_position += forward * 
self.canvas.movement_speed
        self.canvas.Refresh()
    
    def move_camera_backward(self):
        """Move camera backward.""" 
        forward = self.canvas.get_camera_forward_vector()
        self.canvas.camera_position -= forward * 
self.canvas.movement_speed
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
                                   f"Current sphere position: 
({current_pos[0]:.2f}, {current_pos[1]:.2f}, {current_pos[2]:.2f})\n"
                                   "Enter new position as 'x, y, z':\n"
                                   "(This moves sphere + vector + shapes 
only, cube and screen stay in place)", 
                                   "Set Sphere Position", 
                                   
f"{current_pos[0]:.2f},{current_pos[1]:.2f},{current_pos[2]:.2f}")
        if dialog.ShowModal() == wx.ID_OK:
            try:
                values = [float(x.strip()) for x in 
dialog.GetValue().split(',')]
                if len(values) == 3:
                    self.sphere.set_position(values[0], values[1], 
values[2])
                    self.canvas.Refresh()
                    wx.MessageBox(f"Sphere position set to 
({values[0]:.2f}, {values[1]:.2f}, {values[2]:.2f})", 
                                 "Sphere Updated", wx.OK | 
wx.ICON_INFORMATION)
                else:
                    wx.MessageBox("Please enter exactly 3 values separated 
by commas", "Invalid Input", wx.OK | wx.ICON_ERROR)
            except ValueError:
                wx.MessageBox("Invalid position format. Use: x,y,z (e.g., 
2,0,-1)", "Error", wx.OK | wx.ICON_ERROR)
        dialog.Destroy()
    
    def move_sphere_forward(self):
        """Move sphere forward (along main camera's forward direction). 
Cube and screen stay in place."""
        forward = self.canvas.get_camera_forward_vector()
        new_pos = self.sphere.position + forward * 
self.canvas.movement_speed
        self.sphere.set_position(new_pos[0], new_pos[1], new_pos[2])
        self.canvas.Refresh()
    
    def move_sphere_backward(self):
        """Move sphere backward. Cube and screen stay in place.""" 
        forward = self.canvas.get_camera_forward_vector()
        new_pos = self.sphere.position - forward * 
self.canvas.movement_speed
        self.sphere.set_position(new_pos[0], new_pos[1], new_pos[2])
        self.canvas.Refresh()
    
    def move_sphere_left(self):
        """Move sphere left. Cube and screen stay in place."""
        right = self.canvas.get_camera_right_vector()
        new_pos = self.sphere.position - right * 
self.canvas.movement_speed
        self.sphere.set_position(new_pos[0], new_pos[1], new_pos[2])
        self.canvas.Refresh()
    
    def move_sphere_right(self):
        """Move sphere right. Cube and screen stay in place."""
        right = self.canvas.get_camera_right_vector()
        new_pos = self.sphere.position + right * 
self.canvas.movement_speed
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
        """Set pyramid horizontal angle which affects 2D camera horizontal 
FOV."""
        current_angle = self.sphere.pyramid_angle_horizontal
        dialog = wx.NumberEntryDialog(self, "Enter pyramid horizontal 
angle (degrees):", "Angle:", 
                                     "Pyramid Horizontal Angle", 
int(current_angle), 5, 89)
        if dialog.ShowModal() == wx.ID_OK:
            new_angle = float(dialog.GetValue())
            self.sphere.set_pyramid_angle_horizontal(new_angle)
            self.canvas.update_sphere_view_vector()  # Update 2D screen
            self.canvas.Refresh()
        dialog.Destroy()
    
    def set_camera_pyramid_vertical_angle(self):
        """Set pyramid vertical angle which affects 2D camera vertical 
FOV."""
        current_angle = self.sphere.pyramid_angle_vertical
        dialog = wx.NumberEntryDialog(self, "Enter pyramid vertical angle 
(degrees):", "Angle:", 
                                     "Pyramid Vertical Angle", 
int(current_angle), 5, 89)
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

🎮 CAMERA MOVEMENT:
Arrow Keys - Move camera left/right/up/down
I/O Keys - Move camera forward/backward
Shift+I/O - Zoom in/out

🖱️ MOUSE CONTROLS:
Left Click + Drag - Rotate view
Mouse Wheel - Zoom in/out

📐 OBJECT ROTATION:
When object is selected:
- Mouse drag rotates the selected object
- Use Object menu to select different objects

⚙️ MOVEMENT SPEED:
Use View → Camera Movement → Increase/Decrease Movement Speed
Current speed shown in Object Properties dialog

💡 TIP: Select different objects (sphere, cube, screen) 
to control what gets rotated with mouse movement."""
        
        wx.MessageBox(controls, "Keyboard Controls", wx.OK | 
wx.ICON_INFORMATION)
    
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
        
        wx.MessageBox(help_text, "About Camera Movement", wx.OK | 
wx.ICON_INFORMATION)
    
    # Selected object manipulation methods
    def set_selected_object_rotation(self):
        """Set selected object rotation with input dialog."""
        selected = self.canvas.selected_object
        if selected == "none":
            wx.MessageBox("No object selected. Use Object → Select Object 
to choose an object.", "No Selection", wx.OK | wx.ICON_WARNING)
            return
        
        if selected in self.canvas.object_rotations:
            current_rot = self.canvas.object_rotations[selected]
            dialog = wx.TextEntryDialog(self, 
                                       f"Current {selected} rotation: 
({current_rot[0]:.1f}°, {current_rot[1]:.1f}°, {current_rot[2]:.1f}°)\n"
                                       "Enter new rotation as 'pitch, yaw, 
roll' in degrees:", 
                                       f"Set {selected.title()} Rotation", 
                                       
f"{current_rot[0]:.1f},{current_rot[1]:.1f},{current_rot[2]:.1f}")
            if dialog.ShowModal() == wx.ID_OK:
                try:
                    values = [float(x.strip()) for x in 
dialog.GetValue().split(',')]
                    if len(values) == 3:
                        self.canvas.object_rotations[selected] = 
np.array(values)
                        self.canvas.Refresh()
                        wx.MessageBox(f"{selected.title()} rotation set to 
({values[0]:.1f}°, {values[1]:.1f}°, {values[2]:.1f}°)", 
                                     "Rotation Updated", wx.OK | 
wx.ICON_INFORMATION)
                    else:
                        wx.MessageBox("Please enter exactly 3 values 
separated by commas", "Invalid Input", wx.OK | wx.ICON_ERROR)
                except ValueError:
                    wx.MessageBox("Invalid rotation format. Use: 
pitch,yaw,roll (e.g., 45,0,-30)", "Error", wx.OK | wx.ICON_ERROR)
            dialog.Destroy()
    
    def rotate_selected_object(self, pitch_delta, yaw_delta, roll_delta):
        """Rotate selected object by specified amounts."""
        selected = self.canvas.selected_object
        if selected == "none":
            wx.MessageBox("No object selected. Use Object → Select Object 
to choose an object.", "No Selection", wx.OK | wx.ICON_WARNING)
            return
        
        if selected in self.canvas.object_rotations:
            self.canvas.object_rotations[selected][0] += pitch_delta  # 
X/Pitch
            self.canvas.object_rotations[selected][1] += yaw_delta    # 
Y/Yaw
            self.canvas.object_rotations[selected][2] += roll_delta   # 
Z/Roll
            self.canvas.Refresh()
    
    def reset_selected_object_rotation(self):
        """Reset selected object rotation to zero."""
        selected = self.canvas.selected_object
        if selected == "none":
            wx.MessageBox("No object selected. Use Object → Select Object 
to choose an object.", "No Selection", wx.OK | wx.ICON_WARNING)
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
            wx.MessageBox("No object selected. Use Object → Select Object 
to choose an object.", "No Selection", wx.OK | wx.ICON_WARNING)
            return
        
        current_pos = None
        if selected == "sphere":
            current_pos = self.sphere.position
        elif selected == "cube":
            current_pos = self.canvas.red_cube_position
        elif selected == "screen":
            current_pos = self.canvas.screen_position
        
        if current_pos is not None:
            dialog = wx.TextEntryDialog(self, 
                                       f"Current {selected} position: 
({current_pos[0]:.2f}, {current_pos[1]:.2f}, {current_pos[2]:.2f})\n"
                                       "Enter new position as 'x, y, z':", 
                                       f"Set {selected.title()} Position", 
                                       
f"{current_pos[0]:.2f},{current_pos[1]:.2f},{current_pos[2]:.2f}")
            if dialog.ShowModal() == wx.ID_OK:
                try:
                    values = [float(x.strip()) for x in 
dialog.GetValue().split(',')]
                    if len(values) == 3:
                        if selected == "sphere":
                            self.sphere.set_position(values[0], values[1], 
values[2])
                        elif selected == "cube":
                            self.canvas.red_cube_position = 
np.array(values)
                        elif selected == "screen":
                            self.canvas.screen_position = np.array(values)
                        
                        self.canvas.Refresh()
                        wx.MessageBox(f"{selected.title()} position set to 
({values[0]:.2f}, {values[1]:.2f}, {values[2]:.2f})", 
                                     "Position Updated", wx.OK | 
wx.ICON_INFORMATION)
                    else:
                        wx.MessageBox("Please enter exactly 3 values 
separated by commas", "Invalid Input", wx.OK | wx.ICON_ERROR)
                except ValueError:
                    wx.MessageBox("Invalid position format. Use: x,y,z 
(e.g., 2,0,-1)", "Error", wx.OK | wx.ICON_ERROR)
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
            wx.MessageBox("No object selected. Use Object → Select Object 
to choose an object.", "No Selection", wx.OK | wx.ICON_WARNING)
            return
        
        # Get movement vector based on direction
        if direction == "forward":
            movement = self.canvas.get_camera_forward_vector() * 
self.canvas.movement_speed
        elif direction == "backward":
            movement = -self.canvas.get_camera_forward_vector() * 
self.canvas.movement_speed
        elif direction == "left":
            movement = -self.canvas.get_camera_right_vector() * 
self.canvas.movement_speed
        elif direction == "right":
            movement = self.canvas.get_camera_right_vector() * 
self.canvas.movement_speed
        elif direction == "up":
            movement = self.canvas.get_camera_up_vector() * 
self.canvas.movement_speed
        elif direction == "down":
            movement = -self.canvas.get_camera_up_vector() * 
self.canvas.movement_speed
        else:
            return
        
        # Apply movement to selected object
        if selected == "sphere":
            new_pos = self.sphere.position + movement
            self.sphere.set_position(new_pos[0], new_pos[1], new_pos[2])
        elif selected == "cube":
            self.canvas.red_cube_position += movement
        elif selected == "screen":
            self.canvas.screen_position += movement
        
        self.canvas.Refresh()
    
    def reset_selected_object_position(self):
        """Reset selected object position to default."""
        selected = self.canvas.selected_object
        if selected == "none":
            wx.MessageBox("No object selected. Use Object → Select Object 
to choose an object.", "No Selection", wx.OK | wx.ICON_WARNING)
            return
        
        if selected == "sphere":
            self.sphere.set_position(0.0, 0.0, 0.0)
            wx.MessageBox("Sphere position reset to origin (0,0,0)", 
"Position Reset", wx.OK | wx.ICON_INFORMATION)
        elif selected == "cube":
            self.canvas.red_cube_position = np.array([2.0, 0.0, 2.0])
            wx.MessageBox("Cube position reset to default (2,0,2)", 
"Position Reset", wx.OK | wx.ICON_INFORMATION)
        elif selected == "screen":
            self.canvas.screen_position = np.array([-3.0, 0.0, 0.0])
            wx.MessageBox("Screen position reset to default (-3,0,0)", 
"Position Reset", wx.OK | wx.ICON_INFORMATION)
        
        self.canvas.Refresh()
    
    def center_camera_on_cube(self):
        """Center the camera to look at the multicolored cube."""
        cube_pos = self.canvas.red_cube_position
        
        # Reset camera to look at cube
        self.canvas.camera_distance = 5.0
        self.canvas.camera_rotation_x = 0.0
        self.canvas.camera_rotation_y = 0.0
        
        # Position camera to look at cube - move camera opposite to cube 
position
        # Since cube is at [2,0,2], position camera at [-2,0,-2] to look 
at it
        self.canvas.camera_position = -cube_pos * 0.5  # Move camera to 
look at cube
        
        self.canvas.Refresh()
        wx.MessageBox(f"Camera centered on cube at position {cube_pos}", 
"Camera Positioned", wx.OK | wx.ICON_INFORMATION)
    
    def set_cone_length(self):
        """Set cone length with input dialog."""
        current_length = self.sphere.cone_length
        dialog = wx.NumberEntryDialog(self, "Enter cone length (relative 
to sphere radius):", "Length:", "Cone Length", int(current_length * 10), 
5, 100)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_cone_length(dialog.GetValue() / 10.0)
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_cone_angle(self):
        """Set cone angle with input dialog."""
        current_angle = int(self.sphere.cone_angle)
        dialog = wx.NumberEntryDialog(self, "Enter cone half-angle 
(degrees):", "Angle:", "Cone Angle", current_angle, 5, 89)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_cone_angle(float(dialog.GetValue()))
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_cone_color(self):
        """Set cone color with choice dialog (more reliable than color 
picker)."""
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
        
        dialog = wx.SingleChoiceDialog(self, "Choose a color for the 
cone:", "Select Cone Color", color_names)
        dialog.SetSelection(0)  # Default to red
        
        if dialog.ShowModal() == wx.ID_OK:
            selection = dialog.GetSelection()
            color_name, rgb = colors[selection]
            new_color = (rgb[0], rgb[1], rgb[2], 
self.sphere.cone_color[3])
            self.sphere.set_cone_color(new_color)
            self.canvas.Refresh()
            wx.MessageBox(f"Cone color set to {color_name}", "Color 
Updated", wx.OK | wx.ICON_INFORMATION)
        
            dialog.Destroy()
    
    def set_cone_transparency(self):
        """Set cone transparency with input dialog."""
        current_alpha = int(self.sphere.cone_color[3] * 100)
        dialog = wx.NumberEntryDialog(self, "Enter transparency (0-100):", 
"Transparency:", "Cone Transparency", current_alpha, 0, 100)
        if dialog.ShowModal() == wx.ID_OK:
            alpha = dialog.GetValue() / 100.0
            new_color = (self.sphere.cone_color[0], 
self.sphere.cone_color[1], self.sphere.cone_color[2], alpha)
            self.sphere.set_cone_color(new_color)
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_cone_resolution(self):
        """Set cone resolution with input dialog."""
        current_resolution = self.sphere.cone_resolution
        dialog = wx.NumberEntryDialog(self, "Enter cone resolution 
(6-32):", "Resolution:", "Cone Resolution", current_resolution, 6, 32)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_cone_resolution(dialog.GetValue())
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_pyramid_length(self):
        """Set pyramid length with input dialog."""
        current_length = self.sphere.pyramid_length
        dialog = wx.NumberEntryDialog(self, "Enter pyramid length 
(relative to sphere radius):", "Length:", "Pyramid Length", 
int(current_length * 10), 5, 100)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_pyramid_length(dialog.GetValue() / 10.0)
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_pyramid_horizontal_angle(self):
        """Set pyramid horizontal angle with input dialog."""
        current_angle = int(self.sphere.pyramid_angle_horizontal)
        dialog = wx.NumberEntryDialog(self, "Enter horizontal half-angle 
(degrees):", "Angle:", "Horizontal Angle", current_angle, 5, 89)
        if dialog.ShowModal() == wx.ID_OK:
            
self.sphere.set_pyramid_angle_horizontal(float(dialog.GetValue()))
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_pyramid_vertical_angle(self):
        """Set pyramid vertical angle with input dialog."""
        current_angle = int(self.sphere.pyramid_angle_vertical)
        dialog = wx.NumberEntryDialog(self, "Enter vertical half-angle 
(degrees):", "Angle:", "Vertical Angle", current_angle, 5, 89)
        if dialog.ShowModal() == wx.ID_OK:
            
self.sphere.set_pyramid_angle_vertical(float(dialog.GetValue()))
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_pyramid_color(self):
        """Set pyramid color with choice dialog (more reliable than color 
picker)."""
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
            dialog = wx.SingleChoiceDialog(self, "Choose a color for the 
pyramid:", "Select Pyramid Color", color_names)
            print("DEBUG: SingleChoiceDialog for pyramid created 
successfully")
            
            dialog.SetSelection(2)  # Default to blue (different from 
cone)
            print("DEBUG: Default selection set to 2 (Blue)")
            
            print("DEBUG: About to show pyramid dialog with ShowModal()")
            result = dialog.ShowModal()
            print(f"DEBUG: Pyramid dialog result: {result} (wx.ID_OK = 
{wx.ID_OK})")
            
            if result == wx.ID_OK:
                selection = dialog.GetSelection()
                print(f"DEBUG: User selected pyramid index: {selection}")
                color_name, rgb = colors[selection]
                print(f"DEBUG: Selected pyramid color: {color_name} with 
RGB: {rgb}")
                new_color = (rgb[0], rgb[1], rgb[2], 
self.sphere.pyramid_color[3])
                print(f"DEBUG: New pyramid color with alpha: {new_color}")
                self.sphere.set_pyramid_color(new_color)
                print("DEBUG: Color set on pyramid")
                self.canvas.Refresh()
                print("DEBUG: Canvas refreshed")
                wx.MessageBox(f"Pyramid color set to {color_name}", "Color 
Updated", wx.OK | wx.ICON_INFORMATION)
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
            new_color = (self.sphere.pyramid_color[0], 
self.sphere.pyramid_color[1], self.sphere.pyramid_color[2], alpha)
            self.sphere.set_pyramid_color(new_color)
            self.canvas.Refresh()
            dialog.Destroy()
    
    # Cuboid dialog methods
    def set_cuboid_length(self):
        """Set cuboid length with input dialog."""
        current_length = self.sphere.cuboid_length
        dialog = wx.NumberEntryDialog(self, "Enter cuboid length along 
vector (relative to sphere radius):", "Length:", "Cuboid Length", 
int(current_length * 10), 1, 100)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_cuboid_length(dialog.GetValue() / 10.0)
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_cuboid_width(self):
        """Set cuboid width with input dialog."""
        current_width = self.sphere.cuboid_width
        dialog = wx.NumberEntryDialog(self, "Enter cuboid width 
perpendicular to vector (relative to sphere radius):", "Width:", "Cuboid 
Width", int(current_width * 10), 1, 100)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_cuboid_width(dialog.GetValue() / 10.0)
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_cuboid_height(self):
        """Set cuboid height with input dialog."""
        current_height = self.sphere.cuboid_height
        dialog = wx.NumberEntryDialog(self, "Enter cuboid height 
perpendicular to vector (relative to sphere radius):", "Height:", "Cuboid 
Height", int(current_height * 10), 1, 100)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_cuboid_height(dialog.GetValue() / 10.0)
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_cuboid_color(self):
        """Set cuboid color with choice dialog (more reliable than color 
picker)."""
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
        
        dialog = wx.SingleChoiceDialog(self, "Choose a color for the 
cuboid:", "Select Cuboid Color", color_names)
        dialog.SetSelection(6)  # Default to orange (different from cone 
and pyramid)
        
        if dialog.ShowModal() == wx.ID_OK:
            selection = dialog.GetSelection()
            color_name, rgb = colors[selection]
            new_color = (rgb[0], rgb[1], rgb[2], 
self.sphere.cuboid_color[3])
            self.sphere.set_cuboid_color(new_color)
            self.canvas.Refresh()
            wx.MessageBox(f"Cuboid color set to {color_name}", "Color 
Updated", wx.OK | wx.ICON_INFORMATION)
        
            dialog.Destroy()
    
    def set_cuboid_transparency(self):
        """Set cuboid transparency with input dialog."""
        current_alpha = int(self.sphere.cuboid_color[3] * 100)
        dialog = wx.NumberEntryDialog(self, "Enter transparency (0-100):", 
"Transparency:", "Cuboid Transparency", current_alpha, 0, 100)
        if dialog.ShowModal() == wx.ID_OK:
            alpha = dialog.GetValue() / 100.0
            new_color = (self.sphere.cuboid_color[0], 
self.sphere.cuboid_color[1], self.sphere.cuboid_color[2], alpha)
            self.sphere.set_cuboid_color(new_color)
            self.canvas.Refresh()
            dialog.Destroy()
    
    # Near plane dialog methods
    def set_near_plane_distance(self):
        """Set near plane distance with input dialog."""
        current_distance = self.sphere.near_plane_distance
        dialog = wx.NumberEntryDialog(self, "Enter near plane distance 
from sphere center (relative to radius):", "Distance:", "Near Plane 
Distance", int(current_distance * 10), 0, 30)
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
        
        dialog = wx.SingleChoiceDialog(self, "Choose a color for sphere 
intersections:", "Select Intersection Color", color_names)
        dialog.SetSelection(0)  # Default to bright yellow
        
        if dialog.ShowModal() == wx.ID_OK:
            selection = dialog.GetSelection()
            color_name, rgb = colors[selection]
            new_color = (rgb[0], rgb[1], rgb[2], 
self.sphere.sphere_intersection_color[3])
            self.sphere.set_sphere_intersection_color(new_color)
            self.canvas.Refresh()
            wx.MessageBox(f"Sphere intersection color set to 
{color_name}", "Color Updated", wx.OK | wx.ICON_INFORMATION)
        
            dialog.Destroy()
    
    # Normal ray dialog methods
    def set_normal_ray_length(self):
        """Set normal ray length with number dialog."""
        current_length = self.sphere.normal_rays_length
        dialog = wx.NumberEntryDialog(self, "Enter ray length (relative to 
sphere radius):", "Length:", "Normal Ray Length", int(current_length * 
10), 1, 20)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_normal_rays_length(dialog.GetValue() / 10.0)
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_normal_ray_density(self):
        """Set normal ray density with number dialog."""
        current_density = self.sphere.normal_rays_density
        dialog = wx.NumberEntryDialog(self, "Enter ray density (rays per 
division):", "Density:", "Normal Ray Density", current_density, 4, 20)
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
        
        dialog = wx.SingleChoiceDialog(self, "Choose a color for normal 
rays:", "Select Ray Color", color_names)
        dialog.SetSelection(0)  # Default to cyan
        
        if dialog.ShowModal() == wx.ID_OK:
            selection = dialog.GetSelection()
            color_name, rgb = colors[selection]
            new_color = (rgb[0], rgb[1], rgb[2], 
self.sphere.normal_rays_color[3])
            self.sphere.set_normal_rays_color(new_color)
            self.canvas.Refresh()
            wx.MessageBox(f"Normal ray color set to {color_name}", "Color 
Updated", wx.OK | wx.ICON_INFORMATION)
        
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
        dialog = wx.NumberEntryDialog(self, "Enter intersection ray length 
(relative to sphere radius):", "Length:", "Intersection Ray Length", 
int(current_length * 10), 1, 20)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_intersection_normals_length(dialog.GetValue() 
/ 10.0)
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_intersection_ray_density(self):
        """Set intersection normal ray density with number dialog."""
        current_density = self.sphere.intersection_normals_density
        dialog = wx.NumberEntryDialog(self, "Enter intersection ray 
density (rays per division):", "Density:", "Intersection Ray Density", 
current_density, 4, 24)
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
        
        dialog = wx.SingleChoiceDialog(self, "Choose a color for 
intersection normal rays:", "Select Intersection Ray Color", color_names)
        dialog.SetSelection(0)  # Default to magenta
        
        if dialog.ShowModal() == wx.ID_OK:
            selection = dialog.GetSelection()
            color_name, rgb = colors[selection]
            new_color = (rgb[0], rgb[1], rgb[2], 
self.sphere.intersection_normals_color[3])
            self.sphere.set_intersection_normals_color(new_color)
            self.canvas.Refresh()
            wx.MessageBox(f"Intersection normal ray color set to 
{color_name}", "Color Updated", wx.OK | wx.ICON_INFORMATION)
        
            dialog.Destroy()
    
    def set_intersection_ray_thickness(self):
        """Set intersection normal ray thickness with number dialog."""
        current_thickness = self.sphere.intersection_normals_thickness
        dialog = wx.NumberEntryDialog(self, "Enter intersection ray 
thickness (1-5):", "Thickness:", "Intersection Ray Thickness", 
int(current_thickness), 1, 5)
        if dialog.ShowModal() == wx.ID_OK:
            
self.sphere.set_intersection_normals_thickness(float(dialog.GetValue()))
            self.canvas.Refresh()
            dialog.Destroy()
    
    # Truncation normal ray dialog methods
    def set_truncation_ray_length(self):
        """Set truncation normal ray length with number dialog."""
        current_length = self.sphere.truncation_normals_length
        dialog = wx.NumberEntryDialog(self, "Enter truncation ray length 
(relative to sphere radius):", "Length:", "Truncation Ray Length", 
int(current_length * 10), 1, 20)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_truncation_normals_length(dialog.GetValue() / 
10.0)
            self.canvas.Refresh()
            dialog.Destroy()
    
    def set_truncation_ray_density(self):
        """Set truncation normal ray density with number dialog."""
        current_density = self.sphere.truncation_normals_density
        dialog = wx.NumberEntryDialog(self, "Enter truncation ray density 
(rays per division):", "Density:", "Truncation Ray Density", 
current_density, 3, 16)
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
        
        dialog = wx.SingleChoiceDialog(self, "Choose a color for 
truncation normal rays:", "Select Truncation Ray Color", color_names)
        dialog.SetSelection(0)  # Default to white
        
        if dialog.ShowModal() == wx.ID_OK:
            selection = dialog.GetSelection()
            color_name, rgb = colors[selection]
            new_color = (rgb[0], rgb[1], rgb[2], 
self.sphere.truncation_normals_color[3])
            self.sphere.set_truncation_normals_color(new_color)
            self.canvas.Refresh()
            wx.MessageBox(f"Truncation normal ray color set to 
{color_name}", "Color Updated", wx.OK | wx.ICON_INFORMATION)
        
            dialog.Destroy()
    
    def set_truncation_ray_thickness(self):
        """Set truncation normal ray thickness with number dialog."""
        current_thickness = self.sphere.truncation_normals_thickness
        dialog = wx.NumberEntryDialog(self, "Enter truncation ray 
thickness (1-5):", "Thickness:", "Truncation Ray Thickness", 
int(current_thickness), 1, 5)
        if dialog.ShowModal() == wx.ID_OK:
            
self.sphere.set_truncation_normals_thickness(float(dialog.GetValue()))
            self.canvas.Refresh()
            dialog.Destroy()
    
    # ==================== SCREEN DIALOG METHODS ====================
    
    def set_screen_position(self):
        """Set screen 3D position with input dialog."""
        current_pos = self.sphere.screen_position
        dialog = wx.TextEntryDialog(self, 
                                   f"Current position: 
({current_pos[0]:.2f}, {current_pos[1]:.2f}, {current_pos[2]:.2f})\n"
                                   "Enter new position as 'x, y, z':", 
                                   "Set Screen Position", 
                                   f"{current_pos[0]:.2f}, 
{current_pos[1]:.2f}, {current_pos[2]:.2f}")
        if dialog.ShowModal() == wx.ID_OK:
            try:
                values = [float(x.strip()) for x in 
dialog.GetValue().split(',')]
                if len(values) == 3:
                    self.sphere.set_screen_position(values[0], values[1], 
values[2])
                    self.canvas.Refresh()
                    wx.MessageBox(f"Screen position set to 
({values[0]:.2f}, {values[1]:.2f}, {values[2]:.2f})", 
                                 "Position Updated", wx.OK | 
wx.ICON_INFORMATION)
                else:
                    wx.MessageBox("Please enter exactly 3 values separated 
by commas", "Invalid Input", wx.OK | wx.ICON_ERROR)
            except ValueError:
                wx.MessageBox("Please enter valid numbers", "Invalid 
Input", wx.OK | wx.ICON_ERROR)
        dialog.Destroy()
    
    def set_screen_rotation(self):
        """Set screen rotation with input dialog."""
        current_rot = self.sphere.screen_rotation
        dialog = wx.TextEntryDialog(self, 
                                   f"Current rotation: 
({current_rot[0]:.1f}°, {current_rot[1]:.1f}°, {current_rot[2]:.1f}°)\n"
                                   "Enter new rotation as 'pitch, yaw, 
roll' in degrees:", 
                                   "Set Screen Rotation", 
                                   f"{current_rot[0]:.1f}, 
{current_rot[1]:.1f}, {current_rot[2]:.1f}")
        if dialog.ShowModal() == wx.ID_OK:
            try:
                values = [float(x.strip()) for x in 
dialog.GetValue().split(',')]
                if len(values) == 3:
                    self.sphere.set_screen_rotation(values[0], values[1], 
values[2])
                    self.canvas.Refresh()
                    wx.MessageBox(f"Screen rotation set to 
({values[0]:.1f}°, {values[1]:.1f}°, {values[2]:.1f}°)", 
                                 "Rotation Updated", wx.OK | 
wx.ICON_INFORMATION)
                else:
                    wx.MessageBox("Please enter exactly 3 values separated 
by commas", "Invalid Input", wx.OK | wx.ICON_ERROR)
            except ValueError:
                wx.MessageBox("Please enter valid numbers", "Invalid 
Input", wx.OK | wx.ICON_ERROR)
        dialog.Destroy()
    
    def set_screen_size(self):
        """Set screen size with input dialog."""
        current_size = (self.sphere.screen_width, 
self.sphere.screen_height)
        dialog = wx.TextEntryDialog(self, 
                                   f"Current size: {current_size[0]:.2f} x 
{current_size[1]:.2f}\n"
                                   "Enter new size as 'width, height':", 
                                   "Set Screen Size", 
                                   f"{current_size[0]:.2f}, 
{current_size[1]:.2f}")
        if dialog.ShowModal() == wx.ID_OK:
            try:
                values = [float(x.strip()) for x in 
dialog.GetValue().split(',')]
                if len(values) == 2 and all(v > 0 for v in values):
                    self.sphere.set_screen_size(values[0], values[1])
                    self.canvas.Refresh()
                    wx.MessageBox(f"Screen size set to {values[0]:.2f} x 
{values[1]:.2f}", 
                                 "Size Updated", wx.OK | 
wx.ICON_INFORMATION)
                else:
                    wx.MessageBox("Please enter exactly 2 positive values 
separated by a comma", "Invalid Input", wx.OK | wx.ICON_ERROR)
            except ValueError:
                wx.MessageBox("Please enter valid numbers", "Invalid 
Input", wx.OK | wx.ICON_ERROR)
        dialog.Destroy()
    
    def set_screen_resolution(self):
        """Set screen texture resolution with input dialog."""
        current_res = self.sphere.screen_resolution
        dialog = wx.TextEntryDialog(self, 
                                   f"Current resolution: {current_res[0]} 
x {current_res[1]}\n"
                                   "Enter new resolution as 'width, 
height' (e.g., 512, 384):", 
                                   "Set Screen Resolution", 
                                   f"{current_res[0]}, {current_res[1]}")
        if dialog.ShowModal() == wx.ID_OK:
            try:
                values = [int(x.strip()) for x in 
dialog.GetValue().split(',')]
                if len(values) == 2 and all(v > 0 for v in values):
                    self.sphere.set_screen_resolution(values[0], 
values[1])
                    self.canvas.Refresh()
                    wx.MessageBox(f"Screen resolution set to {values[0]} x 
{values[1]}", 
                                 "Resolution Updated", wx.OK | 
wx.ICON_INFORMATION)
                else:
                    wx.MessageBox("Please enter exactly 2 positive 
integers separated by a comma", "Invalid Input", wx.OK | wx.ICON_ERROR)
            except ValueError:
                wx.MessageBox("Please enter valid integers", "Invalid 
Input", wx.OK | wx.ICON_ERROR)
        dialog.Destroy()
    
    def set_camera_position(self):
        """Set virtual camera position with input dialog."""
        current_pos = self.sphere.screen_camera_position
        dialog = wx.TextEntryDialog(self, 
                                   f"Current camera position: 
({current_pos[0]:.2f}, {current_pos[1]:.2f}, {current_pos[2]:.2f})\n"
                                   "Enter new camera position as 'x, y, 
z':", 
                                   "Set Camera Position", 
                                   f"{current_pos[0]:.2f}, 
{current_pos[1]:.2f}, {current_pos[2]:.2f}")
        if dialog.ShowModal() == wx.ID_OK:
            try:
                values = [float(x.strip()) for x in 
dialog.GetValue().split(',')]
                if len(values) == 3:
                    self.sphere.set_camera_position(values[0], values[1], 
values[2])
                    self.canvas.Refresh()
                    wx.MessageBox(f"Camera position set to 
({values[0]:.2f}, {values[1]:.2f}, {values[2]:.2f})", 
                                 "Camera Updated", wx.OK | 
wx.ICON_INFORMATION)
                else:
                    wx.MessageBox("Please enter exactly 3 values separated 
by commas", "Invalid Input", wx.OK | wx.ICON_ERROR)
            except ValueError:
                wx.MessageBox("Please enter valid numbers", "Invalid 
Input", wx.OK | wx.ICON_ERROR)
        dialog.Destroy()
    
    def set_camera_target(self):
        """Set virtual camera target with input dialog."""
        current_target = self.sphere.screen_camera_target
        dialog = wx.TextEntryDialog(self, 
                                   f"Current camera target: 
({current_target[0]:.2f}, {current_target[1]:.2f}, 
{current_target[2]:.2f})\n"
                                   "Enter new camera target as 'x, y, 
z':", 
                                   "Set Camera Target", 
                                   f"{current_target[0]:.2f}, 
{current_target[1]:.2f}, {current_target[2]:.2f}")
        if dialog.ShowModal() == wx.ID_OK:
            try:
                values = [float(x.strip()) for x in 
dialog.GetValue().split(',')]
                if len(values) == 3:
                    self.sphere.set_camera_target(values[0], values[1], 
values[2])
                    self.canvas.Refresh()
                    wx.MessageBox(f"Camera target set to ({values[0]:.2f}, 
{values[1]:.2f}, {values[2]:.2f})", 
                                 "Camera Updated", wx.OK | 
wx.ICON_INFORMATION)
                else:
                    wx.MessageBox("Please enter exactly 3 values separated 
by commas", "Invalid Input", wx.OK | wx.ICON_ERROR)
            except ValueError:
                wx.MessageBox("Please enter valid numbers", "Invalid 
Input", wx.OK | wx.ICON_ERROR)
        dialog.Destroy()
    
    def set_screen_update_rate(self):
        """Set screen update rate with number dialog."""
        current_rate = self.sphere.screen_update_rate
        dialog = wx.NumberEntryDialog(self, "Enter screen update rate in 
seconds (0.1 - 5.0):", "Rate:", "Screen Update Rate", 
                                     int(current_rate * 10), 1, 50)  # 
Convert to tenths of seconds
        if dialog.ShowModal() == wx.ID_OK:
            rate = dialog.GetValue() / 10.0  # Convert back to seconds
            self.sphere.set_screen_update_rate(rate)
            wx.MessageBox(f"Screen update rate set to {rate:.1f} seconds", 
"Rate Updated", wx.OK | wx.ICON_INFORMATION)
        dialog.Destroy()
    
    def set_screen_samples(self):
        """Set anti-aliasing samples with number dialog."""
        current_samples = self.sphere.screen_samples
        dialog = wx.NumberEntryDialog(self, "Enter anti-aliasing samples 
per pixel (1-16):", "Samples:", "Screen Samples", 
                                     current_samples, 1, 16)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_screen_samples(dialog.GetValue())
            wx.MessageBox(f"Screen samples set to {dialog.GetValue()}", 
"Samples Updated", wx.OK | wx.ICON_INFORMATION)
        dialog.Destroy()
    
    def set_screen_max_bounces(self):
        """Set maximum ray bounces with number dialog."""
        current_bounces = self.sphere.screen_max_bounces
        dialog = wx.NumberEntryDialog(self, "Enter maximum ray bounces for 
reflections (0-8):", "Bounces:", "Max Ray Bounces", 
                                     current_bounces, 0, 8)
        if dialog.ShowModal() == wx.ID_OK:
            self.sphere.set_screen_max_bounces(dialog.GetValue())
            wx.MessageBox(f"Maximum ray bounces set to 
{dialog.GetValue()}", "Bounces Updated", wx.OK | wx.ICON_INFORMATION)
        dialog.Destroy()
    
    # ==================== END SCREEN DIALOG METHODS ====================
    
    # ==================== FILE MENU METHODS ====================
    
    def new_scene(self):
        """Create a new scene (reset to defaults)."""
        result = wx.MessageBox("This will reset all settings to defaults. 
Continue?", 
                              "New Scene", wx.YES_NO | wx.ICON_QUESTION)
        if result == wx.YES:
            # Reset sphere to defaults
            self.sphere = SphereRenderer()
            self.sphere._canvas_ref = self.canvas  # Restore canvas 
reference
            
            # Reset canvas to defaults
            self.canvas.camera_distance = 5.0
            self.canvas.camera_rotation_x = 0.0
            self.canvas.camera_rotation_y = 0.0
            self.canvas.camera_position = np.array([0.0, 0.0, 0.0])
            self.canvas.view_vector = np.array([0.0, 0.0, -1.0])
            self.canvas.red_cube_position = np.array([2.0, 0.0, 2.0])
            self.canvas.red_cube_size = 0.3
            
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
            
            wx.MessageBox("New scene created successfully!", "New Scene", 
wx.OK | wx.ICON_INFORMATION)
    
    def open_scene(self):
        """Open a scene from a JSON file."""
        wildcard = "Scene files (*.json)|*.json|All files (*.*)|*.*"
        dialog = wx.FileDialog(self, "Open Scene", wildcard=wildcard, 
style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        
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
                
                wx.MessageBox(f"Scene loaded successfully 
from:\n{filepath}", "Scene Loaded", wx.OK | wx.ICON_INFORMATION)
                
            except Exception as e:
                wx.MessageBox(f"Error loading scene:\n{str(e)}", "Load 
Error", wx.OK | wx.ICON_ERROR)
        
        dialog.Destroy()
    
    def save_scene(self):
        """Save the current scene to a JSON file."""
        if not hasattr(self, '_current_scene_file') or not 
self._current_scene_file:
            self.save_scene_as()
        else:
            self._save_scene_to_file(self._current_scene_file)
    
    def save_scene_as(self):
        """Save the current scene to a new JSON file."""
        wildcard = "Scene files (*.json)|*.json|All files (*.*)|*.*"
        dialog = wx.FileDialog(self, "Save Scene As", wildcard=wildcard, 
style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        
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
            wx.MessageBox(f"Error saving scene:\n{str(e)}", "Save Error", 
wx.OK | wx.ICON_ERROR)
    
    # ==================== END FILE MENU METHODS ====================


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

