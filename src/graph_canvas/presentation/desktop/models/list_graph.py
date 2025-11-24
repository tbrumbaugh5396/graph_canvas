"""
List graph model that represents linear sequences of nodes.
"""


from typing import Dict, List, Optional, Any, Tuple

import graph_canvas.presentation.desktop.models.base_graph as m_base_graph
import graph_canvas.presentation.desktop.models.node as m_node
import graph_canvas.presentation.desktop.models.edge as m_edge


class ListGraph(m_base_graph.BaseGraph):
    """A graph that represents a linear sequence of nodes."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metadata["graph_type"] = "list"

    def validate(self) -> List[str]:
        """Validate the list structure. Returns a list of error messages."""

        errors = super().validate()
        
        # Check for list-specific constraints
        for node in self._nodes.values():
            incoming = self.get_edges_to_node(node.id)
            outgoing = self.get_edges_from_node(node.id)
            
            # Each node should have at most one incoming and one outgoing edge
            if len(incoming) > 1:
                errors.append(f"Node {node.id} has multiple incoming edges in a list")
            if len(outgoing) > 1:
                errors.append(f"Node {node.id} has multiple outgoing edges in a list")
        
        # Check for cycles
        visited = set()
        current_node = None
        
        # Find the start node (node with no incoming edges)
        for node in self._nodes.values():
            if not self.get_edges_to_node(node.id):
                if current_node:
                    errors.append("Multiple start nodes found in list")
                current_node = node.id
        
        # Traverse the list
        while current_node and current_node not in visited:
            visited.add(current_node)
            outgoing = self.get_edges_from_node(current_node)
            if outgoing:
                current_node = outgoing[0].target_id
            else:
                current_node = None
        
        if current_node:  # We stopped because we found a cycle
            errors.append("Cycle detected in list")
        
        # Check if all nodes are connected
        if len(visited) != len(self._nodes):
            errors.append("List contains disconnected nodes")
        
        return errors

    def get_head(self) -> Optional[m_node.Node]:
        """Get the first node in the list."""

        for node in self._nodes.values():
            if not self.get_edges_to_node(node.id):
                return node
        return None

    def get_tail(self) -> Optional[m_node.Node]:
        """Get the last node in the list."""

        for node in self._nodes.values():
            if not self.get_edges_from_node(node.id):
                return node
        return None

    def get_next(self, node_id: str) -> Optional[m_node.Node]:
        """Get the next node in the list."""

        edges = self.get_edges_from_node(node_id)
        if edges:
            return self.get_node(edges[0].target_id)
        return None

    def get_prev(self, node_id: str) -> Optional[m_node.Node]:
        """Get the previous node in the list."""

        edges = self.get_edges_to_node(node_id)
        if edges:
            return self.get_node(edges[0].source_id)
        return None

    def insert_after(self, node: m_node.Node, after_id: str) -> None:
        """Insert a node after the specified node."""

        after_node = self.get_node(after_id)
        if not after_node:
            raise ValueError(f"Node {after_id} not found")
        
        # Add the new node
        self.add_node(node)
        
        # Get the next node (if any)
        next_edges = self.get_edges_from_node(after_id)
        next_node_id = next_edges[0].target_id if next_edges else None
        
        # Remove the old edge to the next node
        if next_edges:
            self.remove_edge(next_edges[0].id)
        
        # Add edge from after_node to new node
        edge1 = m_edge.Edge(source_id=after_id, target_id=node.id)
        self.add_edge(edge1)
        
        # Add edge from new node to next node (if any)
        if next_node_id:
            edge2 = m_edge.Edge(source_id=node.id, target_id=next_node_id)
            self.add_edge(edge2)

    def insert_before(self, node: m_node.Node, before_id: str) -> None:
        """Insert a node before the specified node."""

        before_node = self.get_node(before_id)
        if not before_node:
            raise ValueError(f"Node {before_id} not found")
        
        # Add the new node
        self.add_node(node)
        
        # Get the previous node (if any)
        prev_edges = self.get_edges_to_node(before_id)
        prev_node_id = prev_edges[0].source_id if prev_edges else None
        
        # Remove the old edge from the previous node
        if prev_edges:
            self.remove_edge(prev_edges[0].id)
        
        # Add edge from previous node to new node (if any)
        if prev_node_id:
            edge1 = m_edge.Edge(source_id=prev_node_id, target_id=node.id)
            self.add_edge(edge1)
        
        # Add edge from new node to before_node
        edge2 = m_edge.Edge(source_id=node.id, target_id=before_id)
        self.add_edge(edge2)

    def append(self, node: m_node.Node) -> None:
        """Add a node to the end of the list."""

        tail = self.get_tail()
        if tail:
            self.insert_after(node, tail.id)
        else:
            self.add_node(node)

    def prepend(self, node: m_node.Node) -> None:
        """Add a node to the start of the list."""

        head = self.get_head()
        if head:
            self.insert_before(node, head.id)
        else:
            self.add_node(node)

    def to_array(self) -> List[m_node.Node]:
        """Convert the list to an array of nodes in order."""

        result = []
        current = self.get_head()
        while current:
            result.append(current)
            current = self.get_next(current.id)
        return result
