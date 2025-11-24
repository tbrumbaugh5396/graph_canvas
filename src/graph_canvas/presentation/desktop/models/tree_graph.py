"""
Tree graph model that represents hierarchical structures.
"""


from typing import Dict, List, Optional, Any, Set

import graph_canvas.presentation.desktop.models.base_graph as m_base_graph
import graph_canvas.presentation.desktop.models.node as m_node
import graph_canvas.presentation.desktop.models.edge as m_edge


class TreeGraph(m_base_graph.BaseGraph):
    """A graph that represents a tree structure."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metadata["graph_type"] = "tree"

    def validate(self) -> List[str]:
        """Validate the tree structure. Returns a list of error messages."""

        errors = super().validate()
        
        # Check for tree-specific constraints
        
        # 1. Each node should have exactly one parent (except root)
        roots = []
        for node in self._nodes.values():
            parents = self.get_edges_to_node(node.id)
            if len(parents) > 1:
                errors.append(f"Node {node.id} has multiple parents in tree")
            elif len(parents) == 0:
                roots.append(node.id)
        
        # 2. Should have exactly one root
        if len(roots) == 0:
            errors.append("Tree has no root node")
        elif len(roots) > 1:
            errors.append(f"Tree has multiple root nodes: {roots}")
        
        # 3. Check for cycles
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

    def get_root(self) -> Optional[m_node.Node]:
        """Get the root node of the tree."""

        for node in self._nodes.values():
            if not self.get_edges_to_node(node.id):
                return node
        return None

    def get_parent(self, node_id: str) -> Optional[m_node.Node]:
        """Get the parent node."""

        edges = self.get_edges_to_node(node_id)
        if edges:
            return self.get_node(edges[0].source_id)
        return None

    def get_children(self, node_id: str) -> List[m_node.Node]:
        """Get all child nodes."""

        edges = self.get_edges_from_node(node_id)
        return [self.get_node(edge.target_id) for edge in edges]

    def get_siblings(self, node_id: str) -> List[m_node.Node]:
        """Get all sibling nodes (nodes with same parent)."""

        parent = self.get_parent(node_id)
        if parent:
            siblings = self.get_children(parent.id)
            return [node for node in siblings if node.id != node_id]
        return []

    def get_ancestors(self, node_id: str) -> List[m_node.Node]:
        """Get all ancestor nodes in order from parent to root."""

        ancestors = []
        current = self.get_parent(node_id)
        while current:
            ancestors.append(current)
            current = self.get_parent(current.id)
        return ancestors

    def get_descendants(self, node_id: str) -> List[m_node.Node]:
        """Get all descendant nodes."""

        descendants = []
        to_visit = [node_id]
        while to_visit:
            current = to_visit.pop(0)
            children = self.get_children(current)
            descendants.extend(children)
            to_visit.extend(child.id for child in children)
        return descendants

    def get_level(self, node_id: str) -> int:
        """Get the level of the node (distance from root)."""

        level = 0
        current = node_id
        while self.get_parent(current):
            level += 1
            current = self.get_parent(current).id
        return level

    def get_subtree(self, node_id: str) -> 'TreeGraph':
        """Get a new tree containing the node and all its descendants."""

        subtree = TreeGraph(name=f"Subtree of {node_id}")
        
        # Add the root node
        root = self.get_node(node_id)
        if root:
            subtree.add_node(root)
            
            # Add all descendants
            to_process = [(node_id, None)]
            while to_process:
                current_id, parent_id = to_process.pop(0)
                
                # Add edges to parent if needed
                if parent_id:
                    edge = m_edge.Edge(source_id=parent_id, target_id=current_id)
                    subtree.add_edge(edge)
                
                # Add all children
                for child in self.get_children(current_id):
                    subtree.add_node(child)
                    to_process.append((child.id, current_id))
        
        return subtree

    def add_child(self, parent_id: str, child: m_node.Node) -> None:
        """Add a child node to a parent node."""

        if parent_id not in self._nodes:
            raise ValueError(f"Parent node {parent_id} not found")
        
        self.add_node(child)
        edge = m_edge.Edge(source_id=parent_id, target_id=child.id)
        self.add_edge(edge)

    def move_subtree(self, node_id: str, new_parent_id: str) -> None:
        """Move a node and its subtree to a new parent."""

        if node_id not in self._nodes or new_parent_id not in self._nodes:
            raise ValueError("Node or new parent not found")
        
        # Check if new_parent is a descendant of node (would create cycle)
        if new_parent_id in [node.id for node in self.get_descendants(node_id)]:
            raise ValueError("Cannot move node to its own descendant")
        
        # Remove old parent edge
        old_parent_edges = self.get_edges_to_node(node_id)
        if old_parent_edges:
            self.remove_edge(old_parent_edges[0].id)
        
        # Add new parent edge
        edge = m_edge.Edge(source_id=new_parent_id, target_id=node_id)
        self.add_edge(edge)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the tree to a dictionary structure."""

        def build_dict(node_id: str) -> Dict[str, Any]:
            node = self.get_node(node_id)
            if not node:
                return {}
            
            return {
                "id": node.id,
                "data": node.to_dict(),
                "children": [build_dict(child.id) for child in self.get_children(node_id)]
            }
        
        root = self.get_root()
        if root:
            return build_dict(root.id)
        return {}
