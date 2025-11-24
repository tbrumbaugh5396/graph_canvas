"""
Nested graph model that supports hierarchical graph structures.
"""


from typing import Dict, List, Set, Optional, Any, Tuple

import graph_canvas.presentation.desktop.models.base_graph as m_base_graph
import graph_canvas.presentation.desktop.models.node as m_node
import graph_canvas.presentation.desktop.models.edge as m_edge


class NestedNode(m_node.Node):
    """Extended node class that can contain a subgraph."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subgraph: Optional[NestedGraph] = None
        self.collapsed = True  # Whether the subgraph is visually collapsed

    def set_subgraph(self, subgraph: Optional['NestedGraph']) -> None:
        """Set the subgraph contained in this node."""

        self.subgraph = subgraph
        if subgraph:
            subgraph.parent_node = self

    def to_dict(self) -> Dict[str, Any]:
        """Convert the nested node to a dictionary."""

        data = super().to_dict()
        data.update({
            "subgraph": self.subgraph.to_dict() if self.subgraph else None,
            "collapsed": self.collapsed
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NestedNode':
        """Create a nested node from a dictionary."""

        node = super().from_dict(data)
        if data.get("subgraph"):
            node.subgraph = NestedGraph.from_dict(data["subgraph"])
            node.subgraph.parent_node = node
        node.collapsed = data.get("collapsed", True)
        return node


class NestedEdge(m_edge.Edge):
    """Extended edge class that can cross hierarchy levels."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.source_path: List[str] = []  # Path of containing nodes to source
        self.target_path: List[str] = []  # Path of containing nodes to target

    def to_dict(self) -> Dict[str, Any]:
        """Convert the nested edge to a dictionary."""

        data = super().to_dict()
        data.update({
            "source_path": self.source_path,
            "target_path": self.target_path
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NestedEdge':
        """Create a nested edge from a dictionary."""

        edge = super().from_dict(data)
        edge.source_path = data.get("source_path", [])
        edge.target_path = data.get("target_path", [])
        return edge


class NestedGraph(m_base_graph.BaseGraph):
    """A graph that supports nested subgraphs within nodes."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metadata["graph_type"] = "nested_graph"
        self.parent_node: Optional[NestedNode] = None

    def add_node(self, node: m_node.Node) -> None:
        """Add a node, converting to NestedNode if needed."""

        if not isinstance(node, NestedNode):
            nested_node = NestedNode(
                id=node.id,
                text=node.text,
                x=node.x,
                y=node.y,
                width=node.width,
                height=node.height,
                color=node.color,
                metadata=node.metadata
            )
            node = nested_node
        super().add_node(node)

    def add_edge(self, edge: m_edge.Edge) -> None:
        """Add an edge, converting to NestedEdge if needed."""

        if not isinstance(edge, NestedEdge):
            nested_edge = NestedEdge(
                id=edge.id,
                source_id=edge.source_id,
                target_id=edge.target_id,
                directed=edge.directed
            )
            edge = nested_edge
        super().add_edge(edge)

    def create_subgraph(self, node_id: str) -> 'NestedGraph':
        """Create a new subgraph within a node."""

        node = self.get_node(node_id)
        if not isinstance(node, NestedNode):
            raise ValueError(f"Node {node_id} is not a NestedNode")
        
        subgraph = NestedGraph(name=f"Subgraph of {node.text}")
        node.set_subgraph(subgraph)
        return subgraph

    def get_node_path(self, node_id: str) -> List[str]:
        """Get the path of containing nodes to reach this node."""

        path = []
        current_graph = self
        
        while current_graph:
            if current_graph.parent_node:
                path.insert(0, current_graph.parent_node.id)
            current_graph = current_graph.parent_node.subgraph if current_graph.parent_node else None
        
        return path

    def get_node_by_path(self, path: List[str]) -> Optional[m_node.Node]:
        """Get a node by following a path through the hierarchy."""

        current_graph = self
        
        for node_id in path[:-1]:
            node = current_graph.get_node(node_id)
            if not isinstance(node, NestedNode) or not node.subgraph:
                return None
            current_graph = node.subgraph
        
        return current_graph.get_node(path[-1]) if path else None

    def get_containing_graph(self, node_id: str) -> Optional['NestedGraph']:
        """Get the graph that directly contains a node."""

        if node_id in self._nodes:
            return self
        
        for node in self._nodes.values():
            if isinstance(node, NestedNode) and node.subgraph:
                result = node.subgraph.get_containing_graph(node_id)
                if result:
                    return result
        
        return None

    def get_all_nodes_recursive(self) -> List[m_node.Node]:
        """Get all nodes in this graph and its subgraphs."""

        nodes = list(self._nodes.values())
        for node in self._nodes.values():
            if isinstance(node, NestedNode) and node.subgraph:
                nodes.extend(node.subgraph.get_all_nodes_recursive())
        return nodes

    def get_all_edges_recursive(self) -> List[m_edge.Edge]:
        """Get all edges in this graph and its subgraphs."""

        edges = list(self._edges.values())
        for node in self._nodes.values():
            if isinstance(node, NestedNode) and node.subgraph:
                edges.extend(node.subgraph.get_all_edges_recursive())
        return edges

    def collapse_node(self, node_id: str) -> None:
        """Collapse a node's subgraph."""

        node = self.get_node(node_id)
        if isinstance(node, NestedNode):
            node.collapsed = True

    def expand_node(self, node_id: str) -> None:
        """Expand a node's subgraph."""

        node = self.get_node(node_id)
        if isinstance(node, NestedNode):
            node.collapsed = False

    def move_node(self, node_id: str, target_graph_path: List[str]) -> None:
        """Move a node to a different graph in the hierarchy."""

        # Find the node and its containing graph
        source_graph = self.get_containing_graph(node_id)
        if not source_graph:
            raise ValueError(f"Node {node_id} not found")
        
        # Find the target graph
        target_graph = self
        for node_id in target_graph_path:
            node = target_graph.get_node(node_id)
            if not isinstance(node, NestedNode) or not node.subgraph:
                raise ValueError(f"Invalid target graph path at node {node_id}")
            target_graph = node.subgraph
        
        # Move the node
        node = source_graph.get_node(node_id)
        if node:
            source_graph.remove_node(node_id)
            target_graph.add_node(node)

    def flatten(self) -> 'BaseGraph':
        """Create a flat graph representation."""

        from .basic_graph import BasicGraph
        
        flat = BasicGraph(name=f"Flattened {self.name}")
        
        # Helper to generate unique node IDs
        def make_unique_id(node_id: str, path: List[str]) -> str:
            return "_".join(path + [node_id])
        
        # Helper to add a graph's contents to the flat graph
        def add_graph_contents(graph: 'NestedGraph', path: List[str]) -> None:
            for node in graph.get_all_nodes():
                flat_id = make_unique_id(node.id, path)
                flat_node = m_node.Node(
                    id=flat_id,
                    text=f"{' > '.join(path)}{' > ' if path else ''}{node.text}"
                )
                flat.add_node(flat_node)
                
                if isinstance(node, NestedNode) and node.subgraph:
                    add_graph_contents(node.subgraph, path + [node.id])
            
            for edge in graph.get_all_edges():
                source_id = make_unique_id(edge.source_id, path)
                target_id = make_unique_id(edge.target_id, path)
                flat_edge = m_edge.Edge(source_id=source_id, target_id=target_id)
                flat.add_edge(flat_edge)
        
        add_graph_contents(self, [])
        return flat

    def validate(self) -> List[str]:
        """Validate the nested graph structure."""

        errors = super().validate()
        
        # Check for cycles in the containment hierarchy
        def has_cycle(graph: 'NestedGraph', visited: Set[str]) -> bool:
            if id(graph) in visited:
                return True
            
            visited.add(id(graph))
            for node in graph.get_all_nodes():
                if isinstance(node, NestedNode) and node.subgraph:
                    if has_cycle(node.subgraph, visited.copy()):
                        errors.append(f"Cycle detected in containment hierarchy at node {node.id}")
                        return True
            return False
        
        has_cycle(self, set())
        
        # Validate all subgraphs
        for node in self.get_all_nodes():
            if isinstance(node, NestedNode) and node.subgraph:
                errors.extend(node.subgraph.validate())
        
        return errors
