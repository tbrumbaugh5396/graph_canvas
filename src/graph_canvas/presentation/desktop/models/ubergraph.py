"""
Ubergraph model that supports edges as nodes and recursive edge-node relationships.
"""


from typing import Dict, List, Set, Optional, Any, Tuple

import graph_canvas.presentation.desktop.models.base_graph as m_base_graph
import graph_canvas.presentation.desktop.models.node as m_node
import graph_canvas.presentation.desktop.models.edge as m_edge
import graph_canvas.presentation.desktop.models.hypergraph as m_hypergraph


class UberEdge(m_hypergraph.HypergraphEdge):
    """Extended edge class that can act as a node in an ubergraph."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Visual properties when acting as a node
        self.uber_x = 0.0
        self.uber_y = 0.0
        self.uber_width = 100.0
        self.uber_height = 60.0
        self.uber_shape = "rectangle"  # rectangle, ellipse, diamond
        self.uber_auto_layout = True
        
        # Connection points for edges connecting to this edge-as-node
        self.connection_points: Dict[str, Dict[str, float]] = {}
        
        # Metadata for edge-as-node behavior
        self.metadata["is_uber_node"] = True

    def add_connection_point(self, edge_id: str, position: Dict[str, float]) -> None:
        """Add a connection point for an edge."""

        self.connection_points[edge_id] = position

    def remove_connection_point(self, edge_id: str) -> None:
        """Remove a connection point."""

        self.connection_points.pop(edge_id, None)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the uber-edge to a dictionary."""

        data = super().to_dict()
        data.update({
            "uber_x": self.uber_x,
            "uber_y": self.uber_y,
            "uber_width": self.uber_width,
            "uber_height": self.uber_height,
            "uber_shape": self.uber_shape,
            "uber_auto_layout": self.uber_auto_layout,
            "connection_points": self.connection_points
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UberEdge':
        """Create an uber-edge from a dictionary."""

        edge = super().from_dict(data)
        edge.uber_x = data.get("uber_x", 0.0)
        edge.uber_y = data.get("uber_y", 0.0)
        edge.uber_width = data.get("uber_width", 100.0)
        edge.uber_height = data.get("uber_height", 60.0)
        edge.uber_shape = data.get("uber_shape", "rectangle")
        edge.uber_auto_layout = data.get("uber_auto_layout", True)
        edge.connection_points = data.get("connection_points", {})
        return edge


class Ubergraph(m_base_graph.BaseGraph):
    """A graph where edges can act as nodes and be connected by other edges."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metadata["graph_type"] = "ubergraph"

    def add_edge(self, edge: m_edge.Edge) -> None:
        """Add an edge, converting to UberEdge if needed."""

        if not isinstance(edge, UberEdge):
            uber_edge = UberEdge(
                id=edge.id,
                source_id=edge.source_id,
                target_id=edge.target_id,
                directed=edge.directed
            )
            if hasattr(edge, 'source_ids'):
                uber_edge.source_ids = edge.source_ids
            if hasattr(edge, 'target_ids'):
                uber_edge.target_ids = edge.target_ids
            edge = uber_edge
        super().add_edge(edge)

    def get_edge_as_node(self, edge_id: str) -> Optional[UberEdge]:
        """Get an edge that's being used as a node."""

        edge = self.get_edge(edge_id)
        if isinstance(edge, UberEdge) and edge.metadata.get("is_uber_node"):
            return edge
        return None

    def convert_edge_to_node(self, edge_id: str) -> Optional[UberEdge]:
        """Convert an existing edge to an edge-as-node."""

        edge = self.get_edge(edge_id)
        if not isinstance(edge, UberEdge):
            return None
        
        edge.metadata["is_uber_node"] = True
        return edge

    def convert_node_to_edge(self, edge_id: str) -> Optional[UberEdge]:
        """Convert an edge-as-node back to a regular edge."""

        edge = self.get_edge(edge_id)
        if not isinstance(edge, UberEdge):
            return None
        
        edge.metadata["is_uber_node"] = False
        return edge

    def get_edges_to_edge(self, edge_id: str) -> List[UberEdge]:
        """Get all edges that connect to an edge-as-node."""

        return [
            edge for edge in self._edges.values()
            if isinstance(edge, UberEdge) and (
                edge_id in edge.source_ids or
                edge_id in edge.target_ids
            )
        ]

    def get_connected_edges_as_nodes(self, edge_id: str) -> List[UberEdge]:
        """Get all edge-as-nodes connected to this edge."""

        edge = self.get_edge(edge_id)
        if not isinstance(edge, UberEdge):
            return []
        
        connected = []
        for other in self._edges.values():
            if isinstance(other, UberEdge) and other.metadata.get("is_uber_node"):
                # Check if edges are connected
                if (edge.source_id == other.id or
                    edge.target_id == other.id or
                    (hasattr(edge, 'source_ids') and other.id in edge.source_ids) or
                    (hasattr(edge, 'target_ids') and other.id in edge.target_ids)):
                    connected.append(other)
        
        return connected

    def update_edge_layout(self, edge_id: str, x: float, y: float,
                          width: Optional[float] = None,
                          height: Optional[float] = None) -> None:
        """Update the layout of an edge-as-node."""

        edge = self.get_edge_as_node(edge_id)
        if edge:
            edge.uber_x = x
            edge.uber_y = y
            if width is not None:
                edge.uber_width = width
            if height is not None:
                edge.uber_height = height

    def auto_layout_edges(self) -> None:
        """Automatically layout edge-as-nodes using force-directed placement."""

        import math
        
        # Constants for force-directed layout
        REPULSION = 1000.0
        ATTRACTION = 0.1
        TIMESTEP = 0.1
        MAX_ITERATIONS = 100
        
        # Get all edge-as-nodes
        uber_nodes = [e for e in self._edges.values()
                     if isinstance(e, UberEdge) and e.metadata.get("is_uber_node")]
        
        if not uber_nodes:
            return
        
        # Initialize velocities
        velocities = {node.id: [0.0, 0.0] for node in uber_nodes}
        
        for _ in range(MAX_ITERATIONS):
            # Calculate forces
            forces = {node.id: [0.0, 0.0] for node in uber_nodes}
            
            # Repulsion between all pairs
            for i, node1 in enumerate(uber_nodes):
                for node2 in uber_nodes[i+1:]:
                    dx = node2.uber_x - node1.uber_x
                    dy = node2.uber_y - node1.uber_y
                    distance = math.sqrt(dx*dx + dy*dy) + 0.1
                    
                    # Normalized direction
                    dx /= distance
                    dy /= distance
                    
                    # Repulsive force
                    force = REPULSION / (distance * distance)
                    
                    # Apply to both nodes in opposite directions
                    forces[node1.id][0] -= force * dx
                    forces[node1.id][1] -= force * dy
                    forces[node2.id][0] += force * dx
                    forces[node2.id][1] += force * dy
            
            # Attraction along edges
            for edge in self._edges.values():
                if isinstance(edge, UberEdge):
                    source = self.get_edge_as_node(edge.source_id)
                    target = self.get_edge_as_node(edge.target_id)
                    
                    if source and target:
                        dx = target.uber_x - source.uber_x
                        dy = target.uber_y - source.uber_y
                        distance = math.sqrt(dx*dx + dy*dy)
                        
                        if distance > 0:
                            # Normalized direction
                            dx /= distance
                            dy /= distance
                            
                            # Attractive force
                            force = ATTRACTION * distance
                            
                            # Apply to both nodes
                            forces[source.id][0] += force * dx
                            forces[source.id][1] += force * dy
                            forces[target.id][0] -= force * dx
                            forces[target.id][1] -= force * dy
            
            # Update positions
            max_movement = 0.0
            for node in uber_nodes:
                if not node.uber_auto_layout:
                    continue
                
                # Update velocity (with damping)
                velocities[node.id][0] = (velocities[node.id][0] + forces[node.id][0] * TIMESTEP) * 0.9
                velocities[node.id][1] = (velocities[node.id][1] + forces[node.id][1] * TIMESTEP) * 0.9
                
                # Update position
                dx = velocities[node.id][0] * TIMESTEP
                dy = velocities[node.id][1] * TIMESTEP
                
                node.uber_x += dx
                node.uber_y += dy
                
                max_movement = max(max_movement, abs(dx), abs(dy))
            
            # Check for convergence
            if max_movement < 0.1:
                break

    def validate(self) -> List[str]:
        """Validate the ubergraph structure."""

        errors = super().validate()
        
        # Check for invalid edge-as-node references
        for edge in self._edges.values():
            if isinstance(edge, UberEdge):
                # Check source/target references to edge-as-nodes
                if edge.source_id in self._edges:
                    source_edge = self._edges[edge.source_id]
                    if not isinstance(source_edge, UberEdge) or not source_edge.metadata.get("is_uber_node"):
                        errors.append(f"Edge {edge.id} references non-uber-node edge {edge.source_id} as source")
                
                if edge.target_id in self._edges:
                    target_edge = self._edges[edge.target_id]
                    if not isinstance(target_edge, UberEdge) or not target_edge.metadata.get("is_uber_node"):
                        errors.append(f"Edge {edge.id} references non-uber-node edge {edge.target_id} as target")
                
                # Check hyperedge references to edge-as-nodes
                for node_id in edge.source_ids:
                    if node_id in self._edges:
                        source_edge = self._edges[node_id]
                        if not isinstance(source_edge, UberEdge) or not source_edge.metadata.get("is_uber_node"):
                            errors.append(f"Edge {edge.id} references non-uber-node edge {node_id} in source_ids")
                
                for node_id in edge.target_ids:
                    if node_id in self._edges:
                        target_edge = self._edges[node_id]
                        if not isinstance(target_edge, UberEdge) or not target_edge.metadata.get("is_uber_node"):
                            errors.append(f"Edge {edge.id} references non-uber-node edge {node_id} in target_ids")
        
        return errors
