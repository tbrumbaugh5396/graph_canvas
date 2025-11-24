"""
Base graph model that provides common functionality for all graph types.
"""


from __future__ import annotations
from typing import Dict, List, Set, Optional, Any, Tuple, TYPE_CHECKING

import graph_canvas.presentation.desktop.models.node as m_node
import graph_canvas.presentation.desktop.models.edge as m_edge
import graph_canvas.presentation.desktop.models.graph_restrictions as m_graph_restrictions

if TYPE_CHECKING:
    import graph_canvas.presentation.desktop.models.algorithms.graph_properties as m_graph_properties
    import graph_canvas.presentation.desktop.models.algorithms.graph_requirements as m_graph_requirements


class BaseGraph:
    """Base class for all graph types."""
    
    def __init__(self,
                 name: str = "Untitled Graph",
                 graph_id: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """Initialize a new graph."""

        self.name = name
        self.graph_id = graph_id
        self.metadata = metadata or {}
        self._nodes: Dict[str, Node] = {}
        self._edges: Dict[str, Edge] = {}
        self._selected_nodes: Set[str] = set()
        self._selected_edges: Set[str] = set()
        self.constraints = m_graph_restrictions.GraphConstraints()

    def add_node(self, node: "m_node.Node") -> None:
        """Add a node to the graph."""

        self._nodes[node.id] = node

    def remove_node(self, node_id: str) -> bool:
        """Remove a node and its connected edges from the graph."""

        if node_id in self._nodes:
            # Remove connected edges first
            edges_to_remove = []
            for edge in self._edges.values():
                if edge.source_id == node_id or edge.target_id == node_id:
                    edges_to_remove.append(edge.id)
            
            for edge_id in edges_to_remove:
                self.remove_edge(edge_id)
            
            # Remove the node
            del self._nodes[node_id]
            self._selected_nodes.discard(node_id)
            return True

        return False

    def add_edge(self, edge: "m_edge.Edge") -> None:
        """Add an edge to the graph."""

        self._edges[edge.id] = edge

    def remove_edge(self, edge_id: str) -> bool:
        """Remove an edge from the graph."""

        if edge_id in self._edges:
            del self._edges[edge_id]
            self._selected_edges.discard(edge_id)
            return True
        return False

    def get_node(self, node_id: str) -> Optional["m_node.Node"]:
        """Get a node by its ID."""

        return self._nodes.get(node_id)

    def get_edge(self, edge_id: str) -> Optional["m_edge.Edge"]:
        """Get an edge by its ID."""

        return self._edges.get(edge_id)

    def get_all_nodes(self) -> List["m_node.Node"]:
        """Get all nodes in the graph."""

        return list(self._nodes.values())

    def get_all_edges(self) -> List["m_edge.Edge"]:
        """Get all edges in the graph."""

        return list(self._edges.values())

    def get_edges_from_node(self, node_id: str) -> List["m_edge.Edge"]:
        """Get all edges that start from a node."""

        return [edge for edge in self._edges.values() if edge.source_id == node_id]

    def get_edges_to_node(self, node_id: str) -> List["m_edge.Edge"]:
        """Get all edges that end at a node."""

        return [edge for edge in self._edges.values() if edge.target_id == node_id]

    def get_connected_nodes(self, node_id: str) -> List["m_node.Node"]:
        """Get all nodes connected to a node."""

        connected_nodes = set()
        for edge in self._edges.values():
            if edge.source_id == node_id:
                connected_nodes.add(edge.target_id)
            elif edge.target_id == node_id:
                connected_nodes.add(edge.source_id)
        return [self._nodes[nid] for nid in connected_nodes if nid in self._nodes]

    def select_node(self, node_id: str) -> bool:
        """Select a node."""

        if node_id in self._nodes:
            self._nodes[node_id].selected = True
            self._selected_nodes.add(node_id)
            return True
        return False

    def deselect_node(self, node_id: str) -> bool:
        """Deselect a node."""

        if node_id in self._nodes:
            self._nodes[node_id].selected = False
            self._selected_nodes.discard(node_id)
            return True
        return False

    def select_edge(self, edge_id: str) -> bool:
        """Select an edge."""

        if edge_id in self._edges:
            self._edges[edge_id].selected = True
            self._selected_edges.add(edge_id)
            return True
        return False

    def deselect_edge(self, edge_id: str) -> bool:
        """Deselect an edge."""

        if edge_id in self._edges:
            self._edges[edge_id].selected = False
            self._selected_edges.discard(edge_id)
            return True
        return False

    def clear_selection(self) -> None:
        """Clear all selections."""

        for node_id in self._selected_nodes:
            if node_id in self._nodes:
                self._nodes[node_id].selected = False
        for edge_id in self._selected_edges:
            if edge_id in self._edges:
                self._edges[edge_id].selected = False
        self._selected_nodes.clear()
        self._selected_edges.clear()

    def get_selected_nodes(self) -> List["m_node.Node"]:
        """Get all selected nodes."""

        return [self._nodes[nid] for nid in self._selected_nodes if nid in self._nodes]

    def get_selected_edges(self) -> List["m_edge.Edge"]:
        """Get all selected edges."""

        return [self._edges[eid] for eid in self._selected_edges if eid in self._edges]

    def to_dict(self) -> Dict[str, Any]:
        """Convert the graph to a dictionary."""

        return {
            "name": self.name,
            "graph_id": self.graph_id,
            "metadata": self.metadata,
            "nodes": [node.to_dict() for node in self._nodes.values()],
            "edges": [edge.to_dict() for edge in self._edges.values()],
            "constraints": self.constraints.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseGraph':
        """Create a graph from a dictionary."""

        graph = cls(
            name=data.get("name", "Untitled Graph"),
            graph_id=data.get("graph_id"),
            metadata=data.get("metadata", {})
        )
        
        # Add nodes first
        for node_data in data.get("nodes", []):
            node = Node.from_dict(node_data)
            graph.add_node(node)
        
        # Then add edges
        for edge_data in data.get("edges", []):
            edge = Edge.from_dict(edge_data)
            graph.add_edge(edge)

        # Load constraints if present
        if "constraints" in data:
            graph.constraints = m_graph_restrictions.GraphConstraints.from_dict(data["constraints"])
        
        return graph

    def validate(self) -> List[str]:
        """Validate the graph structure and constraints. Returns a list of error messages."""

        errors = []
        
        # Check for nodes referenced by edges that don't exist
        for edge in self._edges.values():
            if edge.source_id not in self._nodes:
                errors.append(f"Edge {edge.id} references non-existent source node {edge.source_id}")
            if edge.target_id not in self._nodes:
                errors.append(f"Edge {edge.id} references non-existent target node {edge.target_id}")
            
            # Check hyperedge node references
            if edge.is_hyperedge:
                for node_id in edge.source_ids:
                    if node_id not in self._nodes:
                        errors.append(f"Hyperedge {edge.id} references non-existent source node {node_id}")
                for node_id in edge.target_ids:
                    if node_id not in self._nodes:
                        errors.append(f"Hyperedge {edge.id} references non-existent target node {node_id}")

        # Check graph restrictions
        if self.constraints.restrictions:
            import graph_canvas.presentation.desktop.models.algorithms.graph_properties as m_graph_properties
            
            graph_type = m_graph_properties.analyze_graph_type(self)
            connectivity = m_graph_properties.analyze_connectivity(self)
            direction = m_graph_properties.analyze_direction_properties(self)
            
            # Check NO_LOOPS restriction
            if m_graph_restrictions.GraphRestriction.NO_LOOPS in self.constraints.restrictions:
                if not graph_type['simple'] and any(edge.source_id == edge.target_id for edge in self._edges.values()):
                    errors.append("Graph violates NO_LOOPS restriction: contains self-loops")

            # Check NO_MULTIEDGES restriction
            if m_graph_restrictions.GraphRestriction.NO_MULTIEDGES in self.constraints.restrictions:
                if not graph_type['simple'] and graph_type['multigraph']:
                    errors.append("Graph violates NO_MULTIEDGES restriction: contains multiple edges between same nodes")

            # Check SIMPLE restriction
            if m_graph_restrictions.GraphRestriction.SIMPLE in self.constraints.restrictions:
                if not graph_type['simple']:
                    errors.append("Graph violates SIMPLE restriction: contains loops or multiple edges")

            # Check DIRECTED restriction
            if m_graph_restrictions.GraphRestriction.DIRECTED in self.constraints.restrictions:
                if not direction['is_directed']:
                    errors.append("Graph violates DIRECTED restriction: contains undirected edges")

            # Check UNDIRECTED restriction
            if m_graph_restrictions.GraphRestriction.UNDIRECTED in self.constraints.restrictions:
                if not direction['is_undirected']:
                    errors.append("Graph violates UNDIRECTED restriction: contains directed edges")

            # Check ACYCLIC restriction
            if m_graph_restrictions.GraphRestriction.ACYCLIC in self.constraints.restrictions:
                has_cycle, cycle_nodes = m_graph_properties.is_cyclic(self)
                if has_cycle:
                    node_names = [node.name for node in cycle_nodes] if cycle_nodes else []
                    errors.append(f"Graph violates ACYCLIC restriction: contains cycle through nodes {', '.join(node_names)}")

            # Check CONNECTED restriction
            if m_graph_restrictions.GraphRestriction.CONNECTED in self.constraints.restrictions:
                if not connectivity['connected']:
                    errors.append("Graph violates CONNECTED restriction: graph is not connected")

            # Check STRONGLY_CONNECTED restriction
            if m_graph_restrictions.GraphRestriction.STRONGLY_CONNECTED in self.constraints.restrictions:
                if not connectivity['strongly_connected']:
                    errors.append("Graph violates STRONGLY_CONNECTED restriction: graph is not strongly connected")

        # Check graph requirements
        for requirement in self.constraints.requirements:
            # Degree requirements
            if requirement == m_graph_restrictions.GraphRequirement.MIN_DEGREE_1:
                for node_id in self._nodes:
                    degree = len(self.get_edges_from_node(node_id)) + len(self.get_edges_to_node(node_id))
                    if degree < 1:
                        errors.append(f"Node {node_id} violates MIN_DEGREE_1 requirement: has degree {degree}")
            
            elif requirement == m_graph_restrictions.GraphRequirement.MIN_DEGREE_2:
                for node_id in self._nodes:
                    degree = len(self.get_edges_from_node(node_id)) + len(self.get_edges_to_node(node_id))
                    if degree < 2:
                        errors.append(f"Node {node_id} violates MIN_DEGREE_2 requirement: has degree {degree}")
            
            elif requirement == m_graph_restrictions.GraphRequirement.MIN_DEGREE_3:
                for node_id in self._nodes:
                    degree = len(self.get_edges_from_node(node_id)) + len(self.get_edges_to_node(node_id))
                    if degree < 3:
                        errors.append(f"Node {node_id} violates MIN_DEGREE_3 requirement: has degree {degree}")
            
            elif requirement == m_graph_restrictions.GraphRequirement.MAX_DEGREE_2:
                for node_id in self._nodes:
                    degree = len(self.get_edges_from_node(node_id)) + len(self.get_edges_to_node(node_id))
                    if degree > 2:
                        errors.append(f"Node {node_id} violates MAX_DEGREE_2 requirement: has degree {degree}")
            
            elif requirement == m_graph_restrictions.GraphRequirement.MAX_DEGREE_3:
                for node_id in self._nodes:
                    degree = len(self.get_edges_from_node(node_id)) + len(self.get_edges_to_node(node_id))
                    if degree > 3:
                        errors.append(f"Node {node_id} violates MAX_DEGREE_3 requirement: has degree {degree}")
            
            elif requirement == m_graph_restrictions.GraphRequirement.MAX_DEGREE_4:
                for node_id in self._nodes:
                    degree = len(self.get_edges_from_node(node_id)) + len(self.get_edges_to_node(node_id))
                    if degree > 4:
                        errors.append(f"Node {node_id} violates MAX_DEGREE_4 requirement: has degree {degree}")

            # In/Out degree requirements
            elif requirement == m_graph_restrictions.GraphRequirement.MIN_IN_DEGREE_1:
                for node_id in self._nodes:
                    in_degree = len(self.get_edges_to_node(node_id))
                    if in_degree < 1:
                        errors.append(f"Node {node_id} violates MIN_IN_DEGREE_1 requirement: has in-degree {in_degree}")
            
            elif requirement == m_graph_restrictions.GraphRequirement.MIN_OUT_DEGREE_1:
                for node_id in self._nodes:
                    out_degree = len(self.get_edges_from_node(node_id))
                    if out_degree < 1:
                        errors.append(f"Node {node_id} violates MIN_OUT_DEGREE_1 requirement: has out-degree {out_degree}")
            
            elif requirement == m_graph_restrictions.GraphRequirement.MAX_IN_DEGREE_1:
                for node_id in self._nodes:
                    in_degree = len(self.get_edges_to_node(node_id))
                    if in_degree > 1:
                        errors.append(f"Node {node_id} violates MAX_IN_DEGREE_1 requirement: has in-degree {in_degree}")
            
            elif requirement == m_graph_restrictions.GraphRequirement.MAX_OUT_DEGREE_1:
                for node_id in self._nodes:
                    out_degree = len(self.get_edges_from_node(node_id))
                    if out_degree > 1:
                        errors.append(f"Node {node_id} violates MAX_OUT_DEGREE_1 requirement: has out-degree {out_degree}")

            # Path requirements
            elif requirement in (m_graph_restrictions.GraphRequirement.HAS_EULER_PATH,
                               m_graph_restrictions.GraphRequirement.HAS_EULER_CIRCUIT,
                               m_graph_restrictions.GraphRequirement.HAS_HAMILTON_PATH,
                               m_graph_restrictions.GraphRequirement.HAS_HAMILTON_CYCLE,
                               m_graph_restrictions.GraphRequirement.IS_BINARY_TREE,
                               m_graph_restrictions.GraphRequirement.IS_FULL_BINARY,
                               m_graph_restrictions.GraphRequirement.IS_PERFECT_BINARY,
                               m_graph_restrictions.GraphRequirement.IS_COMPLETE_BINARY,
                               m_graph_restrictions.GraphRequirement.IS_BALANCED,
                               m_graph_restrictions.GraphRequirement.IS_FLOW_NETWORK):
                import graph_canvas.presentation.desktop.models.algorithms.graph_requirements as m_graph_requirements
                
                # Map requirements to their check functions
                check_funcs = {
                    m_graph_restrictions.GraphRequirement.HAS_EULER_PATH: m_graph_requirements.has_euler_path,
                    m_graph_restrictions.GraphRequirement.HAS_EULER_CIRCUIT: m_graph_requirements.has_euler_circuit,
                    m_graph_restrictions.GraphRequirement.HAS_HAMILTON_PATH: m_graph_requirements.has_hamilton_path,
                    m_graph_restrictions.GraphRequirement.HAS_HAMILTON_CYCLE: m_graph_requirements.has_hamilton_cycle,
                    m_graph_restrictions.GraphRequirement.IS_BINARY_TREE: m_graph_requirements.is_binary_tree,
                    m_graph_restrictions.GraphRequirement.IS_FULL_BINARY: m_graph_requirements.is_full_binary_tree,
                    m_graph_restrictions.GraphRequirement.IS_PERFECT_BINARY: m_graph_requirements.is_perfect_binary_tree,
                    m_graph_restrictions.GraphRequirement.IS_COMPLETE_BINARY: m_graph_requirements.is_complete_binary_tree,
                    m_graph_restrictions.GraphRequirement.IS_BALANCED: m_graph_requirements.is_balanced_tree,
                    m_graph_restrictions.GraphRequirement.IS_FLOW_NETWORK: m_graph_requirements.is_flow_network
                }
                
                is_valid, reason = check_funcs[requirement](self)
                if not is_valid:
                    errors.append(f"Graph violates {requirement.name} requirement: {reason}")

            # Special graph requirements
            elif requirement == m_graph_restrictions.GraphRequirement.IS_REGULAR:
                if self._nodes:
                    first_degree = len(self.get_edges_from_node(next(iter(self._nodes)))) + len(self.get_edges_to_node(next(iter(self._nodes))))
                    for node_id in self._nodes:
                        degree = len(self.get_edges_from_node(node_id)) + len(self.get_edges_to_node(node_id))
                        if degree != first_degree:
                            errors.append(f"Node {node_id} violates IS_REGULAR requirement: has degree {degree}, expected {first_degree}")
            
            elif requirement == m_graph_restrictions.GraphRequirement.IS_COMPLETE:
                n = len(self._nodes)
                expected_edges = n * (n - 1) // 2
                if len(self._edges) != expected_edges:
                    errors.append(f"Graph violates IS_COMPLETE requirement: has {len(self._edges)} edges, expected {expected_edges}")
            
            elif requirement == m_graph_restrictions.GraphRequirement.IS_TOURNAMENT:
                n = len(self._nodes)
                expected_edges = n * (n - 1) // 2
                if len(self._edges) != expected_edges:
                    errors.append(f"Graph violates IS_TOURNAMENT requirement: has {len(self._edges)} edges, expected {expected_edges}")
                # Check that exactly one directed edge exists between each pair of vertices
                for i, node1_id in enumerate(self._nodes):
                    for node2_id in list(self._nodes.keys())[i+1:]:
                        forward = any(e.source_id == node1_id and e.target_id == node2_id for e in self._edges.values())
                        backward = any(e.source_id == node2_id and e.target_id == node1_id for e in self._edges.values())
                        if not (forward ^ backward):  # XOR - exactly one must be true
                            errors.append(f"Graph violates IS_TOURNAMENT requirement: missing or duplicate edge between nodes {node1_id} and {node2_id}")

        return errors
