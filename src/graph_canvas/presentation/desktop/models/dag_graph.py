"""
Directed Acyclic Graph (DAG) model.
"""


from typing import Dict, List, Set, Optional, Any, Tuple

import graph_canvas.presentation.desktop.models.base_graph as m_base_graph
import graph_canvas.presentation.desktop.models.node as m_node
import graph_canvas.presentation.desktop.models.edge as m_edge


class DAGGraph(m_base_graph.BaseGraph):
    """A graph that represents a directed acyclic graph."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metadata["graph_type"] = "dag"

    def validate(self) -> List[str]:
        """Validate the DAG structure. Returns a list of error messages."""

        errors = super().validate()
        
        # Check for cycles using DFS
        def has_cycle(node_id: str, visited: Set[str], path: Set[str]) -> bool:
            if node_id in path:
                return True
            if node_id in visited:
                return False
            
            visited.add(node_id)
            path.add(node_id)
            
            for edge in self.get_edges_from_node(node_id):
                if has_cycle(edge.target_id, visited, path):
                    return True
            
            path.remove(node_id)
            return False
        
        visited = set()
        for node in self._nodes.values():
            if has_cycle(node.id, visited, set()):
                errors.append(f"Cycle detected starting from node {node.id}")
        
        return errors

    def get_sources(self) -> List["m_node.Node"]:
        """Get all source nodes (nodes with no incoming edges)."""

        return [node for node in self._nodes.values() if not self.get_edges_to_node(node.id)]

    def get_sinks(self) -> List["m_node.Node"]:
        """Get all sink nodes (nodes with no outgoing edges)."""

        return [node for node in self._nodes.values() if not self.get_edges_from_node(node.id)]

    def get_ancestors(self, node_id: str) -> List["m_node.Node"]:
        """Get all ancestor nodes (nodes with paths to this node)."""

        ancestors = set()
        to_visit = [node_id]
        
        while to_visit:
            current = to_visit.pop()
            for edge in self.get_edges_to_node(current):
                if edge.source_id not in ancestors:
                    ancestors.add(edge.source_id)
                    to_visit.append(edge.source_id)
        
        return [self.get_node(nid) for nid in ancestors]

    def get_descendants(self, node_id: str) -> List["m_node.Node"]:
        """Get all descendant nodes (nodes reachable from this node)."""

        descendants = set()
        to_visit = [node_id]
        
        while to_visit:
            current = to_visit.pop()
            for edge in self.get_edges_from_node(current):
                if edge.target_id not in descendants:
                    descendants.add(edge.target_id)
                    to_visit.append(edge.target_id)
        
        return [self.get_node(nid) for nid in descendants]

    def get_topological_sort(self) -> List["m_node.Node"]:
        """Get nodes in topological order."""

        # Kahn's algorithm
        result = []
        in_degree = {node.id: 0 for node in self._nodes.values()}
        
        # Calculate in-degrees
        for edge in self._edges.values():
            in_degree[edge.target_id] += 1
        
        # Start with nodes that have no incoming edges
        queue = [node.id for node, degree in in_degree.items() if degree == 0]
        
        while queue:
            current = queue.pop(0)
            result.append(self.get_node(current))
            
            # Reduce in-degree of neighbors
            for edge in self.get_edges_from_node(current):
                in_degree[edge.target_id] -= 1
                if in_degree[edge.target_id] == 0:
                    queue.append(edge.target_id)
        
        if len(result) != len(self._nodes):
            raise ValueError("Graph contains a cycle")
        
        return result

    def get_longest_path(self, source_id: str, target_id: str) -> List["m_node.Node"]:
        """Get the longest path between two nodes."""

        if source_id not in self._nodes or target_id not in self._nodes:
            return []
        
        # Dynamic programming approach
        distances = {node.id: float('-inf') for node in self._nodes.values()}
        predecessors = {node.id: None for node in self._nodes.values()}
        distances[source_id] = 0
        
        # Process nodes in topological order
        for node in self.get_topological_sort():
            if distances[node.id] != float('-inf'):
                for edge in self.get_edges_from_node(node.id):
                    new_distance = distances[node.id] + 1
                    if new_distance > distances[edge.target_id]:
                        distances[edge.target_id] = new_distance
                        predecessors[edge.target_id] = node.id
        
        if distances[target_id] == float('-inf'):
            return []  # No path exists
        
        # Reconstruct path
        path = []
        current = target_id
        while current is not None:
            path.append(self.get_node(current))
            current = predecessors[current]
        
        return list(reversed(path))

    def get_critical_path(self) -> List["m_node.Node"]:
        """Get the critical path (longest path) in the DAG."""

        sources = self.get_sources()
        sinks = self.get_sinks()
        
        # Find the longest path among all source-sink pairs
        longest_path = []
        max_length = -1
        
        for source in sources:
            for sink in sinks:
                path = self.get_longest_path(source.id, sink.id)
                if len(path) > max_length:
                    max_length = len(path)
                    longest_path = path
        
        return longest_path

    def get_layers(self) -> List[List["m_node.Node"]]:
        """Get nodes organized in layers based on longest path from any source."""

        layers: Dict[str, int] = {}
        
        # Calculate longest path length to each node
        for node in self._nodes.values():
            max_layer = 0
            for ancestor in self.get_ancestors(node.id):
                path = self.get_longest_path(ancestor.id, node.id)
                max_layer = max(max_layer, len(path) - 1)
            layers[node.id] = max_layer
        
        # Group nodes by layer
        max_layer = max(layers.values()) if layers else 0
        result = [[] for _ in range(max_layer + 1)]
        
        for node_id, layer in layers.items():
            result[layer].append(self.get_node(node_id))
        
        return result

    def add_edge_safe(self, source_id: str, target_id: str) -> Optional["m_edge.Edge"]:
        """Add an edge only if it won't create a cycle."""

        # Temporarily add the edge
        edge = Edge(source_id=source_id, target_id=target_id)
        self.add_edge(edge)
        
        # Check for cycles
        errors = self.validate()
        
        if errors:
            # Remove the edge if it creates a cycle
            self.remove_edge(edge.id)
            return None
        
        return edge
