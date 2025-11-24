"""
Edge model for the graph editor.
"""


import uuid
from typing import Dict, Any, Optional, Tuple
import math


class Edge:
    """
    Represents an edge in a graph connecting two nodes with metadata and visual properties.
    """

    def __init__(self,
                 source_id: str,
                 target_id: str,
                 text: str = "",
                 edge_id: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a new edge.
        
        Args:
            source_id: ID of the source node
            target_id: ID of the target node
            text: Text content of the edge
            edge_id: Unique identifier (auto-generated if None)
            metadata: Additional metadata dictionary
        """

        self.id = edge_id or str(uuid.uuid4())
        self.source_id = source_id
        self.target_id = target_id
        self.source_ids = [source_id] if source_id else []  # List of source nodes for hyperedges
        self.target_ids = [target_id] if target_id else []  # List of target nodes for hyperedges
        self.text = text
        self.metadata = metadata or {}

        # Visual properties
        self.selected = False
        self.color = (40, 40, 40)  # Dark gray line - better contrast
        self.width = 3  # Thicker line for better visibility
        self.text_color = (0, 0, 0)  # Black text
        self.font_size = 11  # Slightly larger font
        self.arrow_size = 18  # Larger arrow for better visibility
        self.line_style = 'solid'  # solid, dashed, dotted
        self.split_arrows = False  # Whether to show arrows on all segments when outside main segment
        self.hyperedge_visualization = "lines"  # lines, curved_surface, blob_boundary, pie_chart, polygon, zykov, radial, paoh, force_directed, ubergraph
        # Ubergraph visualization properties
        self.uber_x = 0.0  # X position when displayed as a node in ubergraph view
        self.uber_y = 0.0  # Y position when displayed as a node in ubergraph view
        self.uber_width = 40  # Width when displayed as a node
        self.uber_height = 40  # Height when displayed as a node
        self.uber_shape = "rectangle"  # Shape when displayed as a node (rectangle, ellipse)
        self.uber_auto_layout = False  # Whether to automatically layout the edge in ubergraph view
        self.hyperedge_view = "standard"  # standard, line_graph, derivative_graph
        # Additional visualization properties
        self.radial_angle = 0.0  # Starting angle for radial layout
        self.radial_radius = 100.0  # Radius for radial layout
        self.paoh_layer = 0  # Layer index for PAOH visualization
        self.force_directed_pos = None  # (x, y) position for force-directed layout

        # Edge positioning (for custom positioning)
        self.control_points = []  # List of (x, y, z) tuples for bezier curves
        self.custom_position = False  # Whether to use custom positioning
        self.rendering_type = None  # Individual edge rendering type (overrides global if set)
        self.arrow_position = 1.0  # Position along curve where arrow is placed (0.0 = source, 1.0 = target)
        
        # Composite curve support
        self.is_composite = False  # Whether this edge uses composite curve segments
        self.curve_segments = []  # List of curve segments: [{"type": "bezier", "control_points": [...], "weight": 1.0}, ...]

        # Freeform edge support
        self.freeform_points = []  # List of (x, y, z) tuples for freeform path

        # Internal properties
        self.visible = True  # Whether the edge is visible
        self.locked = False  # Whether the edge is locked from editing
        self.directed = True  # Whether the edge is directed (has arrow)
        
        # Hyperedge support
        self.is_hyperedge = False  # Whether this edge is a hyperedge
        self.from_nodes = []  # List of node IDs that this edge comes from
        self.to_nodes = []  # List of node IDs that this edge goes to
        self.from_connection_point = 0.25  # Position of cyan dot (0.0 to 1.0)
        self.to_connection_point = 0.75  # Position of purple dot (0.0 to 1.0)

    def get_text(self) -> str:
        """Get the text content of the edge."""

        return self.text

    def set_text(self, text: str):
        """Set the text content of the edge."""

        self.text = text

    def set_metadata(self, key: str, value: Any):
        """Set a metadata key-value pair."""

        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get a metadata value by key."""

        return self.metadata.get(key, default)

    def remove_metadata(self, key: str):
        """Remove a metadata key."""

        if key in self.metadata:
            del self.metadata[key]

    def get_all_metadata(self) -> Dict[str, Any]:
        """Get all metadata."""

        return self.metadata.copy()

    def set_all_metadata(self, metadata: Dict[str, Any]):
        """Set all metadata."""

        self.metadata = metadata.copy()

    def add_control_point(self, x: float, y: float, z: float = 0.0):
        """Add a control point for custom edge positioning."""

        self.control_points.append((x, y, z))
        self.custom_position = True

    def remove_control_point(self, index: int):
        """Remove a control point by index."""

        if 0 <= index < len(self.control_points):
            del self.control_points[index]
            if not self.control_points:
                self.custom_position = False

    def clear_control_points(self):
        """Clear all control points."""

        self.control_points.clear()
        self.custom_position = False

    def add_freeform_point(self, x: float, y: float, z: float = 0.0):
        """Add a point to the freeform path."""

        self.freeform_points.append((x, y, z))

    def clear_freeform_points(self):
        """Clear all freeform path points."""

        self.freeform_points.clear()

    def get_freeform_points(self) -> list:
        """Get all freeform path points."""

        return self.freeform_points.copy()

    def get_control_points(self) -> list:
        """Get all control points."""

        return self.control_points.copy()

    def calculate_midpoint(
            self, source_pos: Tuple[float, float],
            target_pos: Tuple[float, float]) -> Tuple[float, float]:
        """Calculate the midpoint between source and target positions."""

        return ((source_pos[0] + target_pos[0]) / 2,
                (source_pos[1] + target_pos[1]) / 2)

    def calculate_angle(self, source_pos: Tuple[float, float],
                        target_pos: Tuple[float, float]) -> float:
        """Calculate the angle of the edge in radians."""

        dx = target_pos[0] - source_pos[0]
        dy = target_pos[1] - source_pos[1]
        return math.atan2(dy, dx)

    def calculate_length(self, source_pos: Tuple[float, float],
                         target_pos: Tuple[float, float]) -> float:
        """Calculate the length of the edge."""

        dx = target_pos[0] - source_pos[0]
        dy = target_pos[1] - source_pos[1]
        return math.sqrt(dx * dx + dy * dy)

    def get_text_position(
            self, source_pos: Tuple[float, float],
            target_pos: Tuple[float, float]) -> Tuple[float, float]:
        """Get the position where text should be rendered."""

        if self.custom_position and self.control_points:
            # Use the first control point for text positioning
            return (self.control_points[0][0], self.control_points[0][1])
        else:
            # Use midpoint
            return self.calculate_midpoint(source_pos, target_pos)

    def contains_point(self,
                       x: float,
                       y: float,
                       source_pos: Tuple[float, float],
                       target_pos: Tuple[float, float],
                       tolerance: float = 5.0) -> bool:
        """Check if a point is near the edge line."""

        if self.rendering_type == "freeform" and self.freeform_points and len(self.freeform_points) >= 2:
            # For freeform edges, check along the freeform path
            points = [(p[0], p[1]) for p in self.freeform_points]
            for i in range(len(points) - 1):
                if self._point_to_line_distance(x, y, points[i],
                                                points[i + 1]) <= tolerance:
                    return True
            return False
        elif self.custom_position and len(self.control_points) >= 1:
            # Check along the bezier curve (simplified as line segments)
            points = [source_pos] + [
                (cp[0], cp[1]) for cp in self.control_points
            ] + [target_pos]
            for i in range(len(points) - 1):
                if self._point_to_line_distance(x, y, points[i],
                                                points[i + 1]) <= tolerance:
                    return True
            return False
        else:
            # Check distance to straight line
            return self._point_to_line_distance(x, y, source_pos,
                                                target_pos) <= tolerance

    def _point_to_line_distance(self, px: float, py: float, p1: Tuple[float,
                                                                      float],
                                p2: Tuple[float, float]) -> float:
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

    def copy(self) -> 'Edge':
        """Create a copy of this edge with a new ID."""

        new_edge = Edge(source_id=self.source_id,
                        target_id=self.target_id,
                        text=self.text,
                        metadata=self.metadata.copy())

        # Copy node lists
        new_edge.source_ids = self.source_ids.copy()
        new_edge.target_ids = self.target_ids.copy()

        # Copy visual properties
        new_edge.color = self.color
        new_edge.width = self.width
        new_edge.text_color = self.text_color
        new_edge.font_size = self.font_size
        new_edge.arrow_size = self.arrow_size
        new_edge.line_style = self.line_style
        new_edge.split_arrows = self.split_arrows
        new_edge.hyperedge_visualization = self.hyperedge_visualization
        
        # Copy ubergraph properties
        new_edge.uber_x = self.uber_x
        new_edge.uber_y = self.uber_y
        new_edge.uber_width = self.uber_width
        new_edge.uber_height = self.uber_height
        new_edge.uber_shape = self.uber_shape
        new_edge.uber_auto_layout = self.uber_auto_layout
        new_edge.hyperedge_view = self.hyperedge_view
        
        # Copy visualization properties
        new_edge.radial_angle = self.radial_angle
        new_edge.radial_radius = self.radial_radius
        new_edge.paoh_layer = self.paoh_layer
        new_edge.force_directed_pos = self.force_directed_pos.copy() if self.force_directed_pos else None
        
        # Copy edge positioning
        new_edge.control_points = self.control_points.copy()
        new_edge.custom_position = self.custom_position
        new_edge.rendering_type = self.rendering_type
        new_edge.arrow_position = self.arrow_position
        
        # Copy composite curve properties
        new_edge.is_composite = self.is_composite
        new_edge.curve_segments = [segment.copy() for segment in self.curve_segments]
        
        # Copy freeform properties
        new_edge.freeform_points = self.freeform_points.copy()
        
        # Copy internal properties
        new_edge.visible = self.visible
        new_edge.locked = self.locked
        new_edge.directed = self.directed
        
        # Copy hyperedge properties
        new_edge.is_hyperedge = self.is_hyperedge
        new_edge.from_nodes = self.from_nodes.copy()
        new_edge.to_nodes = self.to_nodes.copy()
        new_edge.from_connection_point = self.from_connection_point
        new_edge.to_connection_point = self.to_connection_point

        return new_edge

    def to_dict(self) -> Dict[str, Any]:
        """Convert edge to dictionary for serialization."""

        return {
            'id': self.id,
            'source_id': self.source_id,
            'target_id': self.target_id,
            'source_ids': self.source_ids,
            'target_ids': self.target_ids,
            'text': self.text,
            'metadata': self.metadata,
            'color': self.color,
            'width': self.width,
            'text_color': self.text_color,
            'font_size': self.font_size,
            'arrow_size': self.arrow_size,
            'line_style': self.line_style,
            'split_arrows': self.split_arrows,
            'hyperedge_visualization': self.hyperedge_visualization,
            'uber_x': self.uber_x,
            'uber_y': self.uber_y,
            'uber_width': self.uber_width,
            'uber_height': self.uber_height,
            'uber_shape': self.uber_shape,
            'uber_auto_layout': self.uber_auto_layout,
            'hyperedge_view': self.hyperedge_view,
            'radial_angle': self.radial_angle,
            'radial_radius': self.radial_radius,
            'paoh_layer': self.paoh_layer,
            'force_directed_pos': self.force_directed_pos,
            'control_points': self.control_points,
            'custom_position': self.custom_position,
            'rendering_type': self.rendering_type,
            'arrow_position': self.arrow_position,
            'is_composite': self.is_composite,
            'curve_segments': self.curve_segments,
            'freeform_points': self.freeform_points,
            'visible': self.visible,
            'locked': self.locked,
            'directed': self.directed,
            'is_hyperedge': self.is_hyperedge,
            'from_nodes': self.from_nodes,
            'to_nodes': self.to_nodes,
            'from_connection_point': self.from_connection_point,
            'to_connection_point': self.to_connection_point
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Edge':
        """Create edge from dictionary."""

        edge = cls(source_id=data['source_id'],
                   target_id=data['target_id'],
                   text=data.get('text', ''),
                   edge_id=data.get('id'),
                   metadata=data.get('metadata', {}))
        
        # Restore hyperedge node lists
        edge.source_ids = data.get('source_ids', [edge.source_id] if edge.source_id else [])
        edge.target_ids = data.get('target_ids', [edge.target_id] if edge.target_id else [])

        # Restore visual properties
        edge.color = tuple(data.get('color', (40, 40, 40)))
        edge.width = data.get('width', 3)
        edge.text_color = tuple(data.get('text_color', (0, 0, 0)))
        edge.font_size = data.get('font_size', 11)
        edge.arrow_size = data.get('arrow_size', 18)
        edge.line_style = data.get('line_style', 'solid')
        edge.split_arrows = data.get('split_arrows', False)
        edge.hyperedge_visualization = data.get('hyperedge_visualization', 'lines')
        
        # Restore ubergraph properties
        edge.uber_x = data.get('uber_x', 0.0)
        edge.uber_y = data.get('uber_y', 0.0)
        edge.uber_width = data.get('uber_width', 40)
        edge.uber_height = data.get('uber_height', 40)
        edge.uber_shape = data.get('uber_shape', 'rectangle')
        edge.uber_auto_layout = data.get('uber_auto_layout', False)
        edge.hyperedge_view = data.get('hyperedge_view', 'standard')
        
        # Restore visualization properties
        edge.radial_angle = data.get('radial_angle', 0.0)
        edge.radial_radius = data.get('radial_radius', 100.0)
        edge.paoh_layer = data.get('paoh_layer', 0)
        edge.force_directed_pos = data.get('force_directed_pos', None)
        
        # Restore edge positioning
        edge.control_points = data.get('control_points', [])
        edge.custom_position = data.get('custom_position', False)
        edge.rendering_type = data.get('rendering_type', None)
        edge.arrow_position = data.get('arrow_position', 1.0)
        
        # Restore composite curve properties
        edge.is_composite = data.get('is_composite', False)
        edge.curve_segments = data.get('curve_segments', [])
        
        # Restore freeform properties
        edge.freeform_points = data.get('freeform_points', [])
        
        # Restore internal properties
        edge.visible = data.get('visible', True)
        edge.locked = data.get('locked', False)
        edge.directed = data.get('directed', True)
        
        # Restore hyperedge properties
        edge.is_hyperedge = data.get('is_hyperedge', False)
        edge.from_nodes = data.get('from_nodes', [])
        edge.to_nodes = data.get('to_nodes', [])
        edge.from_connection_point = data.get('from_connection_point', 0.25)
        edge.to_connection_point = data.get('to_connection_point', 0.75)

        return edge

    def __str__(self) -> str:
        """String representation of the edge."""

        return f"Edge({self.id}, {self.source_id} -> {self.target_id}, text='{self.text}')"

    def __repr__(self) -> str:
        """String representation of the edge."""

        return self.__str__()

    def shares_nodes_with(self, other: 'Edge') -> bool:
        """Check if this edge shares any nodes with another edge."""

        # Include regular source/target in the comparison
        my_sources = set(self.source_ids) | {self.source_id}
        my_targets = set(self.target_ids) | {self.target_id}
        other_sources = set(other.source_ids) | {other.source_id}
        other_targets = set(other.target_ids) | {other.target_id}
            
        # Check if any source or target nodes are shared
        return (bool(my_sources & other_sources) or
                bool(my_sources & other_targets) or
                bool(my_targets & other_sources) or
                bool(my_targets & other_targets))

    # Hyperedge methods
    def add_from_node(self, node_id: str):
        """Add a node to the source nodes list."""

        if node_id not in self.source_ids:
            self.source_ids.append(node_id)
            self.is_hyperedge = True
            # Update source_id to be the first node in the list
            self.source_id = self.source_ids[0] if self.source_ids else None

    def add_to_node(self, node_id: str):
        """Add a node to the target nodes list."""

        if node_id not in self.target_ids:
            self.target_ids.append(node_id)
            self.is_hyperedge = True
            # Update target_id to be the first node in the list
            self.target_id = self.target_ids[0] if self.target_ids else None

    def remove_from_node(self, node_id: str):
        """Remove a node from the source nodes list."""

        if node_id in self.source_ids:
            self.source_ids.remove(node_id)
            # Update source_id to be the first remaining node
            self.source_id = self.source_ids[0] if self.source_ids else None
            if not self.source_ids and not self.target_ids:
                self.is_hyperedge = False

    def remove_to_node(self, node_id: str):
        """Remove a node from the target nodes list."""

        if node_id in self.target_ids:
            self.target_ids.remove(node_id)
            # Update target_id to be the first remaining node
            self.target_id = self.target_ids[0] if self.target_ids else None
            if not self.source_ids and not self.target_ids:
                self.is_hyperedge = False

    def set_from_connection_point(self, position: float):
        """Set the position of the cyan (from) connection point."""

        position = max(0.0, min(1.0, position))
        # Ensure from point is not after to point
        self.from_connection_point = min(position, self.to_connection_point)

    def set_to_connection_point(self, position: float):
        """Set the position of the purple (to) connection point."""

        position = max(0.0, min(1.0, position))
        # Ensure to point is not before from point
        self.to_connection_point = max(position, self.from_connection_point)
