"""
Layout manager for handling graph layout algorithms and settings.
"""

import json
import os
import math
import random
from typing import Dict, List, Set, Optional, Any, Tuple, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum, auto
import wx

if TYPE_CHECKING:
    from graph_canvas.presentation.desktop.gui.main_window import MainWindow
    from graph_canvas.presentation.desktop.models.node import Node
    from graph_canvas.presentation.desktop.models.edge import Edge
    from graph_canvas.presentation.desktop.models.graph import Graph


class LayoutAlgorithm(Enum):
    """Available layout algorithms."""
    SPRING = auto()
    CIRCLE = auto()
    TREE = auto()
    GRID = auto()
    RANDOM = auto()
    RADIAL = auto()
    LAYERED = auto()
    ORGANIC = auto()
    COMPACT = auto()


@dataclass
class LayoutSettings:
    """Settings for layout algorithms."""
    # Spring layout
    spring_k: float = 1.0  # Spring constant
    spring_c: float = 0.1  # Damping coefficient
    spring_l: float = 100  # Natural spring length
    max_iterations: int = 100
    
    # Circle layout
    circle_radius: Optional[float] = None  # None = auto-calculate
    start_angle: float = 0.0
    angle_step: Optional[float] = None  # None = auto-calculate
    
    # Tree layout
    tree_spacing_x: float = 100.0
    tree_spacing_y: float = 100.0
    tree_orientation: str = "TB"  # TB, BT, LR, RL
    
    # Grid layout
    grid_spacing_x: float = 100.0
    grid_spacing_y: float = 100.0
    grid_columns: Optional[int] = None  # None = auto-calculate
    
    # Radial layout
    radial_levels: Optional[int] = None  # None = auto-calculate
    radial_radius: float = 100.0
    
    # Layered layout
    layer_spacing: float = 100.0
    node_spacing: float = 50.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            'spring': {
                'k': self.spring_k,
                'c': self.spring_c,
                'l': self.spring_l,
                'max_iterations': self.max_iterations
            },
            'circle': {
                'radius': self.circle_radius,
                'start_angle': self.start_angle,
                'angle_step': self.angle_step
            },
            'tree': {
                'spacing_x': self.tree_spacing_x,
                'spacing_y': self.tree_spacing_y,
                'orientation': self.tree_orientation
            },
            'grid': {
                'spacing_x': self.grid_spacing_x,
                'spacing_y': self.grid_spacing_y,
                'columns': self.grid_columns
            },
            'radial': {
                'levels': self.radial_levels,
                'radius': self.radial_radius
            },
            'layered': {
                'layer_spacing': self.layer_spacing,
                'node_spacing': self.node_spacing
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LayoutSettings':
        """Create settings from dictionary."""
        settings = cls()
        
        if 'spring' in data:
            spring = data['spring']
            settings.spring_k = spring.get('k', settings.spring_k)
            settings.spring_c = spring.get('c', settings.spring_c)
            settings.spring_l = spring.get('l', settings.spring_l)
            settings.max_iterations = spring.get('max_iterations', settings.max_iterations)
        
        if 'circle' in data:
            circle = data['circle']
            settings.circle_radius = circle.get('radius', settings.circle_radius)
            settings.start_angle = circle.get('start_angle', settings.start_angle)
            settings.angle_step = circle.get('angle_step', settings.angle_step)
        
        if 'tree' in data:
            tree = data['tree']
            settings.tree_spacing_x = tree.get('spacing_x', settings.tree_spacing_x)
            settings.tree_spacing_y = tree.get('spacing_y', settings.tree_spacing_y)
            settings.tree_orientation = tree.get('orientation', settings.tree_orientation)
        
        if 'grid' in data:
            grid = data['grid']
            settings.grid_spacing_x = grid.get('spacing_x', settings.grid_spacing_x)
            settings.grid_spacing_y = grid.get('spacing_y', settings.grid_spacing_y)
            settings.grid_columns = grid.get('columns', settings.grid_columns)
        
        if 'radial' in data:
            radial = data['radial']
            settings.radial_levels = radial.get('levels', settings.radial_levels)
            settings.radial_radius = radial.get('radius', settings.radial_radius)
        
        if 'layered' in data:
            layered = data['layered']
            settings.layer_spacing = layered.get('layer_spacing', settings.layer_spacing)
            settings.node_spacing = layered.get('node_spacing', settings.node_spacing)
        
        return settings


class LayoutManager:
    """Manages graph layout algorithms and settings."""
    
    def __init__(self, main_window: 'MainWindow'):
        self.main_window = main_window
        self.settings = LayoutSettings()
        self.current_algorithm: Optional[LayoutAlgorithm] = None
        self.is_running = False
        self.progress = 0.0
        self.config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'layout.json')
        
        # Create config directory if it doesn't exist
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        
        # Load settings
        self.load_settings()
    
    def apply_layout(self, algorithm: LayoutAlgorithm, graph: Optional['Graph'] = None):
        """Apply a layout algorithm to the graph."""
        if self.is_running:
            return
            
        self.is_running = True
        self.current_algorithm = algorithm
        self.progress = 0.0
        
        if graph is None:
            graph = self.main_window.current_graph
        
        try:
            if algorithm == LayoutAlgorithm.SPRING:
                self._apply_spring_layout(graph)
            elif algorithm == LayoutAlgorithm.CIRCLE:
                self._apply_circle_layout(graph)
            elif algorithm == LayoutAlgorithm.TREE:
                self._apply_tree_layout(graph)
            elif algorithm == LayoutAlgorithm.GRID:
                self._apply_grid_layout(graph)
            elif algorithm == LayoutAlgorithm.RANDOM:
                self._apply_random_layout(graph)
            elif algorithm == LayoutAlgorithm.RADIAL:
                self._apply_radial_layout(graph)
            elif algorithm == LayoutAlgorithm.LAYERED:
                self._apply_layered_layout(graph)
            elif algorithm == LayoutAlgorithm.ORGANIC:
                self._apply_organic_layout(graph)
            elif algorithm == LayoutAlgorithm.COMPACT:
                self._apply_compact_layout(graph)
        finally:
            self.is_running = False
            self.progress = 1.0
            self.main_window.canvas.Refresh()
    
    def _apply_spring_layout(self, graph: 'Graph'):
        """Apply force-directed spring layout."""
        nodes = graph.get_all_nodes()
        if not nodes:
            return
            
        # Initialize random positions if needed
        for node in nodes:
            if node.x == 0 and node.y == 0:
                node.x = random.uniform(-100, 100)
                node.y = random.uniform(-100, 100)
        
        # Force-directed layout
        for i in range(self.settings.max_iterations):
            # Calculate forces
            forces = {node.id: [0.0, 0.0] for node in nodes}
            
            # Repulsive forces between all nodes
            for n1 in nodes:
                for n2 in nodes:
                    if n1.id != n2.id:
                        dx = n1.x - n2.x
                        dy = n1.y - n2.y
                        distance = math.sqrt(dx * dx + dy * dy) + 0.1
                        force = self.settings.spring_k / (distance * distance)
                        forces[n1.id][0] += force * dx / distance
                        forces[n1.id][1] += force * dy / distance
            
            # Attractive forces along edges
            for edge in graph.get_all_edges():
                source = graph.get_node(edge.source_id)
                target = graph.get_node(edge.target_id)
                if source and target:
                    dx = source.x - target.x
                    dy = source.y - target.y
                    distance = math.sqrt(dx * dx + dy * dy) + 0.1
                    force = distance / self.settings.spring_l
                    
                    forces[source.id][0] -= force * dx
                    forces[source.id][1] -= force * dy
                    forces[target.id][0] += force * dx
                    forces[target.id][1] += force * dy
            
            # Apply forces with damping
            max_force = 0.0
            for node in nodes:
                fx, fy = forces[node.id]
                force_mag = math.sqrt(fx * fx + fy * fy)
                max_force = max(max_force, force_mag)
                
                node.x += fx * self.settings.spring_c
                node.y += fy * self.settings.spring_c
            
            # Update progress
            self.progress = (i + 1) / self.settings.max_iterations
            
            # Check for convergence
            if max_force < 0.1:
                break
    
    def _apply_circle_layout(self, graph: 'Graph'):
        """Apply circular layout."""
        nodes = graph.get_all_nodes()
        if not nodes:
            return
            
        # Calculate radius if not specified
        radius = self.settings.circle_radius
        if radius is None:
            radius = len(nodes) * 50.0
        
        # Calculate angle step if not specified
        angle_step = self.settings.angle_step
        if angle_step is None:
            angle_step = 2 * math.pi / len(nodes)
        
        # Position nodes in a circle
        angle = self.settings.start_angle
        for node in nodes:
            node.x = radius * math.cos(angle)
            node.y = radius * math.sin(angle)
            angle += angle_step
            self.progress = angle / (2 * math.pi)
    
    def _apply_tree_layout(self, graph: 'Graph'):
        """Apply hierarchical tree layout."""
        nodes = graph.get_all_nodes()
        if not nodes:
            return
            
        # Find root node (node with no incoming edges or first node)
        root_id = nodes[0].id
        for node in nodes:
            if not any(edge.target_id == node.id for edge in graph.get_all_edges()):
                root_id = node.id
                break
        
        # Build tree structure
        children: Dict[str, List[str]] = {node.id: [] for node in nodes}
        visited = set()
        
        def build_tree(node_id: str):
            if node_id in visited:
                return
            visited.add(node_id)
            for edge in graph.get_node_edges(node_id):
                child_id = edge.target_id if edge.source_id == node_id else edge.source_id
                if child_id not in visited:
                    children[node_id].append(child_id)
                    build_tree(child_id)
        
        build_tree(root_id)
        
        # Position nodes
        def position_node(node_id: str, x: float, y: float, level_width: float):
            node = graph.get_node(node_id)
            if not node:
                return
                
            node.x = x
            node.y = y
            
            child_count = len(children[node_id])
            if child_count > 0:
                child_width = level_width / child_count
                child_x = x - (level_width / 2) + (child_width / 2)
                for child_id in children[node_id]:
                    position_node(child_id, child_x, y + self.settings.tree_spacing_y, child_width)
                    child_x += child_width
            
            self.progress = len(visited) / len(nodes)
        
        # Start layout from root
        position_node(root_id, 0, 0, len(nodes) * self.settings.tree_spacing_x)
    
    def _apply_grid_layout(self, graph: 'Graph'):
        """Apply grid layout."""
        nodes = graph.get_all_nodes()
        if not nodes:
            return
            
        # Calculate columns if not specified
        columns = self.settings.grid_columns
        if columns is None:
            columns = int(math.sqrt(len(nodes)))
        
        # Position nodes in a grid
        for i, node in enumerate(nodes):
            row = i // columns
            col = i % columns
            node.x = col * self.settings.grid_spacing_x
            node.y = row * self.settings.grid_spacing_y
            self.progress = (i + 1) / len(nodes)
    
    def _apply_random_layout(self, graph: 'Graph'):
        """Apply random layout."""
        nodes = graph.get_all_nodes()
        if not nodes:
            return
            
        # Calculate bounds based on node count
        bound = math.sqrt(len(nodes)) * 100
        
        # Position nodes randomly
        for i, node in enumerate(nodes):
            node.x = random.uniform(-bound, bound)
            node.y = random.uniform(-bound, bound)
            self.progress = (i + 1) / len(nodes)
    
    def _apply_radial_layout(self, graph: 'Graph'):
        """Apply radial layout."""
        nodes = graph.get_all_nodes()
        if not nodes:
            return
            
        # Find center node (most connected or first node)
        center_id = nodes[0].id
        max_edges = 0
        for node in nodes:
            edge_count = len(graph.get_node_edges(node.id))
            if edge_count > max_edges:
                max_edges = edge_count
                center_id = node.id
        
        # Build levels from center
        levels: List[Set[str]] = [{center_id}]
        visited = {center_id}
        
        while True:
            next_level = set()
            for node_id in levels[-1]:
                for edge in graph.get_node_edges(node_id):
                    other_id = edge.target_id if edge.source_id == node_id else edge.source_id
                    if other_id not in visited:
                        next_level.add(other_id)
                        visited.add(other_id)
            if not next_level:
                break
            levels.append(next_level)
            self.progress = len(visited) / len(nodes)
        
        # Position nodes in levels
        center = graph.get_node(center_id)
        if center:
            center.x = 0
            center.y = 0
        
        for i, level in enumerate(levels[1:], 1):
            radius = i * self.settings.radial_radius
            angle = 0
            angle_step = 2 * math.pi / len(level)
            for node_id in level:
                node = graph.get_node(node_id)
                if node:
                    node.x = radius * math.cos(angle)
                    node.y = radius * math.sin(angle)
                    angle += angle_step
    
    def _apply_layered_layout(self, graph: 'Graph'):
        """Apply layered layout."""
        nodes = graph.get_all_nodes()
        if not nodes:
            return
            
        # Assign layers based on longest path from any root
        layers: Dict[str, int] = {}
        roots = []
        
        # Find roots (nodes with no incoming edges)
        for node in nodes:
            if not any(edge.target_id == node.id for edge in graph.get_all_edges()):
                roots.append(node.id)
        
        if not roots:
            roots = [nodes[0].id]  # Use first node if no roots found
        
        # Assign initial layers
        def assign_layer(node_id: str, layer: int):
            if node_id in layers:
                layers[node_id] = max(layers[node_id], layer)
            else:
                layers[node_id] = layer
            for edge in graph.get_node_edges(node_id):
                if edge.source_id == node_id:
                    assign_layer(edge.target_id, layer + 1)
        
        for root in roots:
            assign_layer(root, 0)
        
        # Group nodes by layer
        layer_nodes: Dict[int, List[str]] = {}
        for node_id, layer in layers.items():
            if layer not in layer_nodes:
                layer_nodes[layer] = []
            layer_nodes[layer].append(node_id)
        
        # Position nodes in layers
        max_layer = max(layer_nodes.keys())
        for layer, node_ids in layer_nodes.items():
            y = layer * self.settings.layer_spacing
            width = (len(node_ids) - 1) * self.settings.node_spacing
            x = -width / 2
            for node_id in node_ids:
                node = graph.get_node(node_id)
                if node:
                    node.x = x
                    node.y = y
                    x += self.settings.node_spacing
            self.progress = (layer + 1) / (max_layer + 1)
    
    def _apply_organic_layout(self, graph: 'Graph'):
        """Apply organic layout (modified spring layout)."""
        # Similar to spring layout but with different force calculations
        self._apply_spring_layout(graph)  # For now, use spring layout
    
    def _apply_compact_layout(self, graph: 'Graph'):
        """Apply compact layout (minimize area while preserving structure)."""
        # Start with grid layout then optimize positions
        self._apply_grid_layout(graph)
        
        nodes = graph.get_all_nodes()
        if not nodes:
            return
            
        # Optimize positions to minimize area while maintaining minimum distances
        min_distance = min(self.settings.grid_spacing_x, self.settings.grid_spacing_y) / 2
        
        for iteration in range(50):  # Limited iterations for responsiveness
            moved = False
            for i, node in enumerate(nodes):
                # Try to move node closer to connected nodes
                connected = []
                for edge in graph.get_node_edges(node.id):
                    other_id = edge.target_id if edge.source_id == node.id else edge.source_id
                    other = graph.get_node(other_id)
                    if other:
                        connected.append(other)
                
                if not connected:
                    continue
                
                # Calculate center of connected nodes
                cx = sum(n.x for n in connected) / len(connected)
                cy = sum(n.y for n in connected) / len(connected)
                
                # Try to move toward center while maintaining minimum distances
                dx = (cx - node.x) * 0.1
                dy = (cy - node.y) * 0.1
                
                can_move = True
                for other in nodes:
                    if other.id != node.id:
                        new_dx = (other.x - (node.x + dx))
                        new_dy = (other.y - (node.y + dy))
                        dist = math.sqrt(new_dx * new_dx + new_dy * new_dy)
                        if dist < min_distance:
                            can_move = False
                            break
                
                if can_move:
                    node.x += dx
                    node.y += dy
                    moved = True
            
            self.progress = (iteration + 1) / 50
            if not moved:
                break
    
    def save_settings(self):
        """Save layout settings to config file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings.to_dict(), f, indent=4)
        except Exception as e:
            print(f"Error saving layout settings: {e}")
    
    def load_settings(self):
        """Load layout settings from config file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.settings = LayoutSettings.from_dict(data)
        except Exception as e:
            print(f"Error loading layout settings: {e}")
            self.settings = LayoutSettings()  # Use defaults
