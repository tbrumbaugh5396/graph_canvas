"""
Graph model for the graph editor.
"""


import json
import uuid
from typing import Dict, List, Any, Optional, Tuple, Set

import graph_canvas.presentation.desktop.models.node as m_node
import graph_canvas.presentation.desktop.models.edge as m_edge


class Graph:
    """
    Represents a complete graph with nodes, edges, and metadata.
    """

    def __init__(self,
                 name: str = "Untitled Graph",
                 graph_id: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a new graph.
        
        Args:
            name: Name of the graph
            graph_id: Unique identifier (auto-generated if None)
            metadata: Additional metadata dictionary
        """

        self.id = graph_id or str(uuid.uuid4())
        self.name = name
        self.metadata = metadata or {}

        # Graph data
        self.nodes: Dict[str, m_node.Node] = {}
        self.edges: Dict[str, Edge] = {}

        # Graph properties
        self.selected_nodes: Set[str] = set()
        self.selected_edges: Set[str] = set()
        self.modified = False
        self.file_path = None

        # Visual properties
        self.background_color = (255, 255, 255)  # White background
        self.grid_visible = True
        self.grid_size = 20
        self.grid_color = (200, 200, 200)  # Darker grid for better contrast

    def add_node(self, node: m_node.Node) -> str:
        """Add a node to the graph."""

        print(f"DEBUG: Adding node {node.id} to graph")
        self.nodes[node.id] = node
        self.modified = True
        return node.id

    def remove_node(self, node_id: str) -> bool:
        """Remove a node and all connected edges."""

        print(f"DEBUG: Removing node {node_id} from graph")
        if node_id not in self.nodes:
            print(f"DEBUG: Node {node_id} not found in graph")
            return False

        # Remove all edges connected via source/target and sanitize hyperedge lists
        edges_to_remove = []
        for edge_id, edge in self.edges.items():
            # Mark edges that directly reference this node via source/target
            if edge.source_id == node_id or edge.target_id == node_id:
                edges_to_remove.append(edge_id)
            # Clean up hyperedge multi-endpoint lists if present
            try:
                if hasattr(edge, 'source_ids') and isinstance(edge.source_ids, list):
                    if node_id in edge.source_ids:
                        edge.source_ids = [nid for nid in edge.source_ids if nid != node_id]
                if hasattr(edge, 'target_ids') and isinstance(edge.target_ids, list):
                    if node_id in edge.target_ids:
                        edge.target_ids = [nid for nid in edge.target_ids if nid != node_id]
            except Exception:
                pass

        for edge_id in edges_to_remove:
            self.remove_edge(edge_id)

        # Remove the node
        del self.nodes[node_id]
        self.selected_nodes.discard(node_id)
        self.modified = True
        print(f"DEBUG: Successfully removed node {node_id}")
        return True

    def get_node(self, node_id: str) -> Optional[m_node.Node]:
        """Get a node by its ID."""

        return self.nodes.get(node_id)

    def get_all_nodes(self) -> List[m_node.Node]:
        """Get all nodes in the graph."""

        return list(self.nodes.values())

    def add_edge(self, edge: m_edge.Edge) -> str:
        """Add an edge to the graph."""

        # Validate that source and target nodes exist
        if edge.source_id not in self.nodes or edge.target_id not in self.nodes:
            raise ValueError("Source or target node does not exist")

        print(f"DEBUG: Adding edge {edge.id} to graph: {edge.source_id} -> {edge.target_id}")
        self.edges[edge.id] = edge
        self.modified = True
        print(f"DEBUG: Total edges in graph: {len(self.edges)}")
        return edge.id

    def remove_edge(self, edge_id: str) -> bool:
        """Remove an edge from the graph."""

        if edge_id not in self.edges:
            return False

        # Remove references to this uberedge from other edges (e.g., connected_uberedges and arrow maps)
        for other in list(self.edges.values()):
            try:
                # Remove from explicit uberedge links
                if hasattr(other, 'metadata') and isinstance(other.metadata, dict):
                    lst = other.metadata.get('connected_uberedges')
                    if isinstance(lst, list) and edge_id in lst:
                        other.metadata['connected_uberedges'] = [eid for eid in lst if eid != edge_id]
                    amap = other.metadata.get('arrow_pos_edges')
                    if isinstance(amap, dict) and edge_id in amap:
                        try:
                            # keys may be strings
                            if edge_id in amap:
                                del amap[edge_id]
                            elif str(edge_id) in amap:
                                del amap[str(edge_id)]
                            other.metadata['arrow_pos_edges'] = amap
                        except Exception:
                            pass
            except Exception:
                pass

        del self.edges[edge_id]
        self.selected_edges.discard(edge_id)
        self.modified = True
        return True

    def get_edge(self, edge_id: str) -> Optional[m_edge.Edge]:
        """Get an edge by its ID."""

        return self.edges.get(edge_id)

    def get_all_edges(self) -> List[m_edge.Edge]:
        """Get all edges in the graph."""

        return list(self.edges.values())

    def get_node_edges(self, node_id: str) -> List[m_edge.Edge]:
        """Get all edges connected to a node."""

        return [
            edge for edge in self.edges.values()
            if edge.source_id == node_id or edge.target_id == node_id
        ]

    def get_edge_between_nodes(self, source_id: str,
                               target_id: str) -> Optional[m_edge.Edge]:
        """Get the edge between two nodes (if exists)."""

        for edge in self.edges.values():
            if edge.source_id == source_id and edge.target_id == target_id:
                return edge
        return None

    def create_node(self,
                    x: float = 0.0,
                    y: float = 0.0,
                    z: float = 0.0,
                    text: str = "") -> m_node.Node:
        """Create and add a new node to the graph."""

        node = m_node.Node(x=x, y=y, z=z, text=text)
        self.add_node(node)
        return node

    def create_edge(self,
                    source_id: str,
                    target_id: str,
                    text: str = "") -> m_edge.Edge:
        """Create and add a new edge to the graph."""

        edge = m_edge.Edge(source_id=source_id, target_id=target_id, text=text)
        self.add_edge(edge)
        return edge

    def copy_node(self, node_id: str) -> Optional[m_node.Node]:
        """Copy a node and add it to the graph."""

        original_node = self.get_node(node_id)
        if not original_node:
            return None

        new_node = original_node.copy()
        # Offset the position slightly
        new_node.x += 50
        new_node.y += 50
        self.add_node(new_node)
        return new_node

    def copy_edge(self, edge_id: str) -> Optional[m_edge.Edge]:
        """Copy an edge (only if both nodes exist)."""

        original_edge = self.get_edge(edge_id)
        if not original_edge:
            return None

        new_edge = original_edge.copy()
        # Only add if both nodes still exist
        if (new_edge.source_id in self.nodes
                and new_edge.target_id in self.nodes):
            self.add_edge(new_edge)
            return new_edge
        return None

    def select_node(self, node_id: str):
        """Select a node."""

        if node_id in self.nodes:
            self.selected_nodes.add(node_id)
            self.nodes[node_id].selected = True

    def deselect_node(self, node_id: str):
        """Deselect a node."""

        if node_id in self.nodes:
            self.selected_nodes.discard(node_id)
            self.nodes[node_id].selected = False

    def select_edge(self, edge_id: str):
        """Select an edge and any connected hyperedges."""

        if edge_id in self.edges:
            print(f"DEBUG: Graph selecting edge {edge_id}")
            edge = self.edges[edge_id]
            self.selected_edges.add(edge_id)
            edge.selected = True
            
            # If this is a hyperedge, select all connected hyperedges
            if edge.is_hyperedge:
                for other_edge in self.edges.values():
                    if other_edge.id != edge_id and other_edge.is_hyperedge:
                        if edge.shares_nodes_with(other_edge):
                            self.selected_edges.add(other_edge.id)
                            other_edge.selected = True
            
            print(f"DEBUG: Total selected edges: {len(self.selected_edges)}")
        else:
            print(f"DEBUG: Edge {edge_id} not found in graph!")

    def deselect_edge(self, edge_id: str):
        """Deselect an edge and any connected hyperedges."""

        if edge_id in self.edges:
            print(f"DEBUG: Graph deselecting edge {edge_id}")
            edge = self.edges[edge_id]
            self.selected_edges.discard(edge_id)
            edge.selected = False
            
            # If this is a hyperedge, deselect all connected hyperedges
            if edge.is_hyperedge:
                for other_edge in self.edges.values():
                    if other_edge.id != edge_id and other_edge.is_hyperedge:
                        if edge.shares_nodes_with(other_edge):
                            self.selected_edges.discard(other_edge.id)
                            other_edge.selected = False
            
            print(f"DEBUG: Total selected edges: {len(self.selected_edges)}")
        else:
            print(f"DEBUG: Edge {edge_id} not found in graph for deselection!")

    def clear_selection(self):
        """Clear all selections."""

        for node_id in self.selected_nodes:
            if node_id in self.nodes:
                self.nodes[node_id].selected = False
        for edge_id in self.selected_edges:
            if edge_id in self.edges:
                self.edges[edge_id].selected = False

        self.selected_nodes.clear()
        self.selected_edges.clear()

    def select_all(self):
        """Select all nodes and edges."""

        for node in self.nodes.values():
            node.selected = True
            self.selected_nodes.add(node.id)
        for edge in self.edges.values():
            edge.selected = True
            self.selected_edges.add(edge.id)

    def get_selected_nodes(self) -> List[m_node.Node]:
        """Get all selected nodes."""

        return [
            self.nodes[node_id] for node_id in self.selected_nodes
            if node_id in self.nodes
        ]

    def get_selected_edges(self) -> List[m_edge.Edge]:
        """Get all selected edges."""

        print(f"DEBUG: get_selected_edges called")
        print(f"DEBUG: self.selected_edges set contains: {list(self.selected_edges)}")
        print(f"DEBUG: Available edges in graph: {list(self.edges.keys())}")
        
        result = [
            self.edges[edge_id] for edge_id in self.selected_edges
            if edge_id in self.edges
        ]
        print(f"DEBUG: Returning {len(result)} selected edges")
        return result

    def delete_selected(self):
        """Delete all selected nodes and edges."""

        print(f"DEBUG: delete_selected called - {len(self.selected_nodes)} nodes, {len(self.selected_edges)} edges selected")
        # Delete selected edges first
        for edge_id in list(self.selected_edges):
            self.remove_edge(edge_id)

        # Delete selected nodes (this will also delete connected edges)
        for node_id in list(self.selected_nodes):
            self.remove_node(node_id)

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get the bounding box of all nodes (left, top, right, bottom)."""

        if not self.nodes:
            return (0, 0, 0, 0)

        positions = [(node.x, node.y) for node in self.nodes.values()]
        xs, ys = zip(*positions)

        return (min(xs), min(ys), max(xs), max(ys))

    def set_metadata(self, key: str, value: Any):
        """Set a metadata key-value pair."""

        self.metadata[key] = value
        self.modified = True

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get a metadata value by key."""

        return self.metadata.get(key, default)

    def remove_metadata(self, key: str):
        """Remove a metadata key."""

        if key in self.metadata:
            del self.metadata[key]
            self.modified = True

    def get_all_metadata(self) -> Dict[str, Any]:
        """Get all metadata."""

        return self.metadata.copy()

    def set_all_metadata(self, metadata: Dict[str, Any]):
        """Set all metadata."""

        self.metadata = metadata.copy()
        self.modified = True

    def import_graph(self,
                     other_graph: 'Graph',
                     offset_x: float = 0,
                     offset_y: float = 0):
        """Import nodes and edges from another graph."""

        # Map old node IDs to new node IDs
        node_id_map = {}

        # Import nodes
        for node in other_graph.get_all_nodes():
            new_node = node.copy()
            new_node.x += offset_x
            new_node.y += offset_y
            old_id = node.id
            self.add_node(new_node)
            node_id_map[old_id] = new_node.id

        # Import edges
        for edge in other_graph.get_all_edges():
            if edge.source_id in node_id_map and edge.target_id in node_id_map:
                new_edge = edge.copy()
                new_edge.source_id = node_id_map[edge.source_id]
                new_edge.target_id = node_id_map[edge.target_id]
                self.add_edge(new_edge)

    def clear(self):
        """Clear all nodes and edges."""

        self.nodes.clear()
        self.edges.clear()
        self.selected_nodes.clear()
        self.selected_edges.clear()
        self.modified = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to dictionary for serialization."""

        return {
            'id': self.id,
            'name': self.name,
            'metadata': self.metadata,
            'nodes': [node.to_dict() for node in self.nodes.values()],
            'edges': [edge.to_dict() for edge in self.edges.values()],
            'background_color': self.background_color,
            'grid_visible': self.grid_visible,
            'grid_size': self.grid_size,
            'grid_color': self.grid_color
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Graph':
        """Create graph from dictionary."""

        graph = cls(name=data.get('name', 'Untitled Graph'),
                    graph_id=data.get('id'),
                    metadata=data.get('metadata', {}))

        # Restore visual properties
        graph.background_color = tuple(
            data.get('background_color', (255, 255, 255)))
        graph.grid_visible = data.get('grid_visible', True)
        graph.grid_size = data.get('grid_size', 20)
        graph.grid_color = tuple(data.get('grid_color', (240, 240, 240)))

        # Restore nodes
        for node_data in data.get('nodes', []):
            node = m_node.Node.from_dict(node_data)
            graph.nodes[node.id] = node

        # Restore edges
        for edge_data in data.get('edges', []):
            edge = m_edge.Edge.from_dict(edge_data)
            graph.edges[edge.id] = edge

        graph.modified = False
        return graph

    def save_to_file(self, file_path: str):
        """Save graph to JSON file."""

        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        self.file_path = file_path
        self.modified = False

    @classmethod
    def load_from_file(cls, file_path: str) -> 'Graph':
        """Load graph from JSON file."""

        with open(file_path, 'r') as f:
            data = json.load(f)

        graph = cls.from_dict(data)
        graph.file_path = file_path
        graph.modified = False
        return graph

    def get_statistics(self) -> Dict[str, Any]:
        """Get graph statistics."""

        return {
            'node_count': len(self.nodes),
            'edge_count': len(self.edges),
            'selected_nodes': len(self.selected_nodes),
            'selected_edges': len(self.selected_edges),
            'bounds': self.get_bounds(),
            'modified': self.modified
        }

    def __str__(self) -> str:
        """String representation of the graph."""

        return f"Graph({self.name}, {len(self.nodes)} nodes, {len(self.edges)} edges)"

    def __repr__(self) -> str:
        """String representation of the graph."""

        return self.__str__()
