"""
Node model for the graph editor.
"""


import uuid
from typing import Dict, Any, Optional, Tuple
import json


class Node:
    """
    Represents a node in a graph with position, metadata, and visual properties.
    """

    def __init__(self,
                 x: float = 0.0,
                 y: float = 0.0,
                 z: float = 0.0,
                 text: str = "",
                 node_id: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a new node.
        
        Args:
            x, y, z: 3D position coordinates
            text: Text content of the node
            node_id: Unique identifier (auto-generated if None)
            metadata: Additional metadata dictionary
        """

        self.id = node_id or str(uuid.uuid4())
        self.x = x
        self.y = y
        self.z = z
        self.text = text
        self.metadata = metadata or {}

        # Visual properties
        self.selected = False
        self.width = 60
        self.height = 40
        self.radius = 20  # Default radius for circular nodes
        self.shape = 'circle'  # Can be 'circle' or 'rectangle'
        self.color = (240, 240, 240)  # Light gray background - higher contrast
        self.text_color = (0, 0, 0)  # Black text
        self.border_color = (60, 60, 60)  # Dark gray border - higher contrast
        self.border_width = 3  # Thicker border for better visibility
        self.font_size = 12

        # Internal properties
        self.visible = True
        self.locked = False
        self.rotation = 0.0  # Rotation angle in degrees
        
        # Containment hierarchy properties
        self.parent_id = None  # ID of parent node that contains this node
        self.child_ids = set()  # Set of IDs of child nodes contained in this node
        self.contained_edge_ids = set()  # Set of IDs of edges contained in this node
        self.is_expanded = True  # Whether container node is expanded (showing children)
        self.is_container = False  # Whether this node acts as a container
        
        # Edge redirection for collapse/expand
        self.redirected_edges = {}  # Maps edge_id -> original_node_id for edges redirected to this container

    def get_position(self) -> Tuple[float, float, float]:
        """Get the 3D position of the node."""

        return (self.x, self.y, self.z)

    def set_position(self, x: float, y: float, z: Optional[float] = None):
        """Set the 3D position of the node."""

        self.x = x
        self.y = y
        if z is not None:
            self.z = z

    def get_2d_position(self) -> Tuple[float, float]:
        """Get the 2D position for rendering."""

        return (self.x, self.y)

    def set_2d_position(self, x: float, y: float):
        """Set the 2D position."""

        self.x = x
        self.y = y

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get the bounding box (left, top, right, bottom)."""

        half_width = self.width / 2
        half_height = self.height / 2
        return (self.x - half_width, self.y - half_height, self.x + half_width,
                self.y + half_height)

    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is inside the node."""

        left, top, right, bottom = self.get_bounds()
        return left <= x <= right and top <= y <= bottom

    def set_text(self, text: str):
        """Set the text content of the node."""

        self.text = text

    def get_text(self) -> str:
        """Get the text content of the node."""

        return self.text

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

    def copy(self) -> 'Node':
        """Create a copy of this node with a new ID."""

        new_node = Node(x=self.x,
                        y=self.y,
                        z=self.z,
                        text=self.text,
                        metadata=self.metadata.copy())
        # Copy visual properties
        new_node.width = self.width
        new_node.height = self.height
        new_node.radius = self.radius
        new_node.color = self.color
        new_node.text_color = self.text_color
        new_node.border_color = self.border_color
        new_node.border_width = self.border_width
        new_node.font_size = self.font_size
        new_node.visible = self.visible
        new_node.locked = self.locked
        new_node.rotation = self.rotation
        # Copy containment properties
        new_node.parent_id = None  # Don't copy parent relationship for new node
        new_node.child_ids = set()  # Don't copy children for new node
        new_node.contained_edge_ids = set()  # Don't copy contained edges
        new_node.is_expanded = self.is_expanded
        new_node.is_container = self.is_container
        new_node.redirected_edges = {}  # Don't copy redirected edges
        return new_node

    def add_child(self, child_node_id: str):
        """Add a child node to this container."""

        self.child_ids.add(child_node_id)
        self.is_container = True
        
    def remove_child(self, child_node_id: str):
        """Remove a child node from this container."""

        self.child_ids.discard(child_node_id)
        if not self.child_ids and not self.contained_edge_ids:
            self.is_container = False
            
    def add_contained_edge(self, edge_id: str):
        """Add a contained edge to this container."""

        self.contained_edge_ids.add(edge_id)
        self.is_container = True
        
    def remove_contained_edge(self, edge_id: str):
        """Remove a contained edge from this container."""

        self.contained_edge_ids.discard(edge_id)
        if not self.child_ids and not self.contained_edge_ids:
            self.is_container = False
    
    def toggle_expanded(self):
        """Toggle the expanded/collapsed state of this container."""

        if self.is_container:
            self.is_expanded = not self.is_expanded
            
    def add_redirected_edge(self, edge_id: str, original_node_id: str):
        """Add an edge that was redirected to this container during collapse."""

        self.redirected_edges[edge_id] = original_node_id
        
    def remove_redirected_edge(self, edge_id: str):
        """Remove a redirected edge (during expand)."""

        if edge_id in self.redirected_edges:
            del self.redirected_edges[edge_id]
            
    def get_redirected_edges(self):
        """Get all redirected edges for this container."""

        return self.redirected_edges.copy()
            
    def get_container_label(self) -> str:
        """Get label text for container showing contained count."""

        if not self.is_container:
            return self.text
        
        child_count = len(self.child_ids)
        edge_count = len(self.contained_edge_ids)
        state = "▼" if self.is_expanded else "▶"  # Down arrow (expanded) or right arrow (collapsed)
        
        if child_count > 0 and edge_count > 0:
            return f"{state} {self.text} ({child_count}N, {edge_count}E)"
        elif child_count > 0:
            return f"{state} {self.text} ({child_count} nodes)"
        elif edge_count > 0:
            return f"{state} {self.text} ({edge_count} edges)"
        else:
            return f"{state} {self.text}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary for serialization."""

        return {
            'id': self.id,
            'x': self.x,
            'y': self.y,
            'z': self.z,
            'text': self.text,
            'metadata': self.metadata,
            'width': self.width,
            'height': self.height,
            'radius': self.radius,
            'shape': self.shape,
            'color': self.color,
            'text_color': self.text_color,
            'border_color': self.border_color,
            'border_width': self.border_width,
            'font_size': self.font_size,
            'visible': self.visible,
            'locked': self.locked,
            'rotation': self.rotation,
            'parent_id': self.parent_id,
            'child_ids': list(self.child_ids),
            'contained_edge_ids': list(self.contained_edge_ids),
            'is_expanded': self.is_expanded,
            'is_container': self.is_container,
            'redirected_edges': self.redirected_edges
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Node':
        """Create node from dictionary."""

        node = cls(x=data.get('x', 0.0),
                   y=data.get('y', 0.0),
                   z=data.get('z', 0.0),
                   text=data.get('text', ''),
                   node_id=data.get('id'),
                   metadata=data.get('metadata', {}))

        # Restore visual properties
        node.width = data.get('width', 60)
        node.height = data.get('height', 40)
        node.radius = data.get('radius', 20)  # Default radius for circular nodes
        node.shape = data.get('shape', 'circle')  # Default to circle
        node.color = tuple(data.get('color', (200, 200, 200)))
        node.text_color = tuple(data.get('text_color', (0, 0, 0)))
        node.border_color = tuple(data.get('border_color', (0, 0, 0)))
        node.border_width = data.get('border_width', 2)
        node.font_size = data.get('font_size', 12)
        node.visible = data.get('visible', True)
        node.locked = data.get('locked', False)
        node.rotation = data.get('rotation', 0.0)
        # Restore containment properties
        node.parent_id = data.get('parent_id')
        node.child_ids = set(data.get('child_ids', []))
        node.contained_edge_ids = set(data.get('contained_edge_ids', []))
        node.is_expanded = data.get('is_expanded', True)
        node.is_container = data.get('is_container', False)
        node.redirected_edges = data.get('redirected_edges', {})

        return node

    def __str__(self) -> str:
        """String representation of the node."""

        return f"Node({self.id}, text='{self.text}', pos=({self.x}, {self.y}, {self.z}))"

    def __repr__(self) -> str:
        """String representation of the node."""

        return self.__str__()