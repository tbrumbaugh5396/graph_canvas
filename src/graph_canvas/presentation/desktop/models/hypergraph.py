"""
Hypergraph model that supports edges connecting multiple nodes.
"""


from typing import Dict, List, Set, Optional, Any, Tuple

import graph_canvas.presentation.desktop.models.base_graph as m_base_graph
import graph_canvas.presentation.desktop.models.node as m_node
import graph_canvas.presentation.desktop.models.edge as m_edge


class HypergraphEdge(m_edge.Edge):
    """Extended edge class for hypergraphs."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_hyperedge = True
        self.source_ids: List[str] = []
        self.target_ids: List[str] = []
        self.from_connection_point = 0.25  # Default to 25%
        self.to_connection_point = 0.75    # Default to 75%
        self.split_arrows = False
        self.hyperedge_visualization = "lines"  # Default visualization type

    def add_source(self, node_id: str) -> None:
        """Add a source node to the hyperedge."""

        if node_id not in self.source_ids:
            self.source_ids.append(node_id)
            if not self.source_id:  # Set primary source if none exists
                self.source_id = node_id

    def add_target(self, node_id: str) -> None:
        """Add a target node to the hyperedge."""

        if node_id not in self.target_ids:
            self.target_ids.append(node_id)
            if not self.target_id:  # Set primary target if none exists
                self.target_id = node_id

    def remove_source(self, node_id: str) -> None:
        """Remove a source node from the hyperedge."""

        if node_id in self.source_ids:
            self.source_ids.remove(node_id)
            if self.source_id == node_id:
                self.source_id = self.source_ids[0] if self.source_ids else None

    def remove_target(self, node_id: str) -> None:
        """Remove a target node from the hyperedge."""

        if node_id in self.target_ids:
            self.target_ids.remove(node_id)
            if self.target_id == node_id:
                self.target_id = self.target_ids[0] if self.target_ids else None

    def set_from_connection_point(self, value: float) -> None:
        """Set the 'from' connection point, ensuring it's not greater than 'to'."""

        self.from_connection_point = min(value, self.to_connection_point)

    def set_to_connection_point(self, value: float) -> None:
        """Set the 'to' connection point, ensuring it's not less than 'from'."""

        self.to_connection_point = max(value, self.from_connection_point)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the hyperedge to a dictionary."""

        data = super().to_dict()
        data.update({
            "is_hyperedge": True,
            "source_ids": self.source_ids,
            "target_ids": self.target_ids,
            "from_connection_point": self.from_connection_point,
            "to_connection_point": self.to_connection_point,
            "split_arrows": self.split_arrows,
            "hyperedge_visualization": self.hyperedge_visualization
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HypergraphEdge':
        """Create a hyperedge from a dictionary."""

        edge = super().from_dict(data)
        edge.is_hyperedge = True
        edge.source_ids = data.get("source_ids", [])
        edge.target_ids = data.get("target_ids", [])
        edge.from_connection_point = data.get("from_connection_point", 0.25)
        edge.to_connection_point = data.get("to_connection_point", 0.75)
        edge.split_arrows = data.get("split_arrows", False)
        edge.hyperedge_visualization = data.get("hyperedge_visualization", "lines")
        return edge


class Hypergraph(m_base_graph.BaseGraph):
    """A graph that supports hyperedges connecting multiple nodes."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metadata["graph_type"] = "hypergraph"

    def add_edge(self, edge: m_edge.Edge) -> None:
        """Add an edge, converting to hyperedge if needed."""

        if not isinstance(edge, HypergraphEdge):
            # Convert regular edge to hyperedge
            hyperedge = HypergraphEdge(
                id=edge.id,
                source_id=edge.source_id,
                target_id=edge.target_id,
                directed=edge.directed
            )
            if edge.source_id:
                hyperedge.add_source(edge.source_id)
            if edge.target_id:
                hyperedge.add_target(edge.target_id)
            edge = hyperedge
        
        super().add_edge(edge)

    def create_hyperedge(self, source_ids: List[str], target_ids: List[str], directed: bool = True) -> HypergraphEdge:
        """Create and add a new hyperedge."""

        edge = HypergraphEdge(directed=directed)
        for source_id in source_ids:
            edge.add_source(source_id)
        for target_id in target_ids:
            edge.add_target(target_id)
        self.add_edge(edge)
        return edge

    def get_node_hyperedges(self, node_id: str) -> List[HypergraphEdge]:
        """Get all hyperedges that include this node."""

        return [
            edge for edge in self._edges.values()
            if edge.is_hyperedge and (
                node_id in edge.source_ids or
                node_id in edge.target_ids
            )
        ]

    def get_connected_hyperedges(self, edge_id: str) -> List[HypergraphEdge]:
        """Get all hyperedges that share nodes with this edge."""

        edge = self.get_edge(edge_id)
        if not edge or not edge.is_hyperedge:
            return []
        
        connected = []
        for other in self._edges.values():
            if other.is_hyperedge and other.id != edge_id:
                # Check if edges share any nodes
                if (set(edge.source_ids) & set(other.source_ids) or
                    set(edge.source_ids) & set(other.target_ids) or
                    set(edge.target_ids) & set(other.source_ids) or
                    set(edge.target_ids) & set(other.target_ids)):
                    connected.append(other)
        
        return connected

    def get_dual_graph(self) -> 'Hypergraph':
        """Create the dual hypergraph where nodes become edges and vice versa."""

        dual = Hypergraph(name=f"Dual of {self.name}")
        
        # Create nodes for each hyperedge
        for edge in self._edges.values():
            if edge.is_hyperedge:
                node = m_node.Node(text=f"Edge {edge.id}")
                dual.add_node(node)
        
        # Create hyperedges for each node
        for node in self._nodes.values():
            # Get all hyperedges containing this node
            incident_edges = self.get_node_hyperedges(node.id)
            if incident_edges:
                # Create sources from edges where node is a source
                sources = [e.id for e in incident_edges if node.id in e.source_ids]
                # Create targets from edges where node is a target
                targets = [e.id for e in incident_edges if node.id in e.target_ids]
                # Create dual edge
                if sources or targets:
                    dual.create_hyperedge(sources, targets)
        
        return dual

    def get_line_graph(self) -> 'BasicGraph':
        """Create the line graph where vertices represent hyperedges."""

        from .basic_graph import BasicGraph
        
        line = BasicGraph(name=f"Line Graph of {self.name}")
        
        # Create a node for each hyperedge
        for edge in self._edges.values():
            if edge.is_hyperedge:
                node = m_node.Node(text=f"Edge {edge.id}")
                line.add_node(node)
        
        # Create edges between nodes that share vertices
        edges = list(self._edges.values())
        for i, edge1 in enumerate(edges):
            if not edge1.is_hyperedge:
                continue
            for edge2 in edges[i+1:]:
                if not edge2.is_hyperedge:
                    continue
                # Check if edges share any nodes
                if (set(edge1.source_ids) & set(edge2.source_ids) or
                    set(edge1.source_ids) & set(edge2.target_ids) or
                    set(edge1.target_ids) & set(edge2.source_ids) or
                    set(edge1.target_ids) & set(edge2.target_ids)):
                    line_edge = m_edge.Edge(source_id=edge1.id, target_id=edge2.id)
                    line.add_edge(line_edge)
        
        return line

    def get_derivative_graph(self) -> 'BasicGraph':
        """Create the derivative graph where edges connect nodes in the same hyperedge."""

        from .basic_graph import BasicGraph
        
        derivative = BasicGraph(name=f"Derivative Graph of {self.name}")
        
        # Copy all nodes
        for node in self._nodes.values():
            derivative.add_node(node)
        
        # Create edges between all pairs of nodes in each hyperedge
        for edge in self._edges.values():
            if not edge.is_hyperedge:
                continue
            
            # Get all nodes in the hyperedge
            nodes = edge.source_ids + edge.target_ids
            
            # Create edges between all pairs
            for i, node1_id in enumerate(nodes):
                for node2_id in nodes[i+1:]:
                    if not derivative.get_edge_between(node1_id, node2_id):
                        derivative_edge = m_edge.Edge(source_id=node1_id, target_id=node2_id)
                        derivative.add_edge(derivative_edge)
        
        return derivative

    def validate(self) -> List[str]:
        """Validate the hypergraph structure."""

        errors = super().validate()
        
        for edge in self._edges.values():
            if edge.is_hyperedge:
                # Check that source_ids and target_ids contain valid nodes
                for node_id in edge.source_ids:
                    if node_id not in self._nodes:
                        errors.append(f"Hyperedge {edge.id} references non-existent source node {node_id}")
                for node_id in edge.target_ids:
                    if node_id not in self._nodes:
                        errors.append(f"Hyperedge {edge.id} references non-existent target node {node_id}")
                
                # Check that from_connection_point <= to_connection_point
                if edge.from_connection_point > edge.to_connection_point:
                    errors.append(f"Hyperedge {edge.id} has from_connection_point > to_connection_point")
        
        return errors
