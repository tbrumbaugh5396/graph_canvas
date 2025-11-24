"""
Data representation views for different graph structures.
"""


from typing import Dict, List, Set, Optional, Any, Tuple, Protocol
import numpy as np

import graph_canvas.presentation.desktop.models.base_graph as m_base_graph
import graph_canvas.presentation.desktop.models.node as m_node
import graph_canvas.presentation.desktop.models.edge as m_edge


class DataView(Protocol):
    """Protocol for data representation views."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the view to a dictionary representation."""

        ...

    def to_string(self) -> str:
        """Convert the view to a string representation."""

        ...


class AdjacencyListView:
    """Adjacency list representation."""
    
    def __init__(self, graph: "m_base_graph.BaseGraph"):
        self.graph = graph
        self._build_view()

    def _build_view(self) -> None:
        """Build the adjacency list representation."""

        self.adj_list: Dict[str, List[str]] = {}
        for node in self.graph.get_all_nodes():
            self.adj_list[node.id] = []
            for edge in self.graph.get_edges_from_node(node.id):
                self.adj_list[node.id].append(edge.target_id)

    def to_dict(self) -> Dict[str, List[str]]:
        """Get the adjacency list as a dictionary."""

        return self.adj_list

    def to_string(self) -> str:
        """Get a string representation of the adjacency list."""

        lines = []
        for node_id, neighbors in self.adj_list.items():
            node = self.graph.get_node(node_id)
            lines.append(f"{node.text} -> {', '.join(self.graph.get_node(n).text for n in neighbors)}")
        return "\n".join(lines)


class EdgeListView:
    """Edge list representation."""
    
    def __init__(self, graph: "m_base_graph.BaseGraph"):
        self.graph = graph
        self._build_view()

    def _build_view(self) -> None:
        """Build the edge list representation."""

        self.edge_list: List[Tuple[str, str]] = []
        for edge in self.graph.get_all_edges():
            self.edge_list.append((edge.source_id, edge.target_id))

    def to_dict(self) -> List[Dict[str, str]]:
        """Get the edge list as a list of dictionaries."""

        return [{"source": s, "target": t} for s, t in self.edge_list]

    def to_string(self) -> str:
        """Get a string representation of the edge list."""

        lines = []
        for source_id, target_id in self.edge_list:
            source = self.graph.get_node(source_id)
            target = self.graph.get_node(target_id)
            lines.append(f"{source.text} -> {target.text}")
        return "\n".join(lines)


class ParentMapView:
    """Parent map representation."""
    
    def __init__(self, graph: "m_base_graph.BaseGraph"):
        self.graph = graph
        self._build_view()

    def _build_view(self) -> None:
        """Build the parent map representation."""

        self.parent_map: Dict[str, Optional[str]] = {}
        for node in self.graph.get_all_nodes():
            parents = self.graph.get_edges_to_node(node.id)
            self.parent_map[node.id] = parents[0].source_id if parents else None

    def to_dict(self) -> Dict[str, Optional[str]]:
        """Get the parent map as a dictionary."""

        return self.parent_map

    def to_string(self) -> str:
        """Get a string representation of the parent map."""

        lines = []
        for node_id, parent_id in self.parent_map.items():
            node = self.graph.get_node(node_id)
            parent = self.graph.get_node(parent_id) if parent_id else None
            lines.append(f"{node.text} <- {parent.text if parent else 'None'}")
        return "\n".join(lines)


class AdjacencyMatrixView:
    """Adjacency matrix representation."""
    
    def __init__(self, graph: "m_base_graph.BaseGraph"):
        self.graph = graph
        self._build_view()

    def _build_view(self) -> None:
        """Build the adjacency matrix representation."""

        nodes = list(self.graph.get_all_nodes())
        self.node_indices = {node.id: i for i, node in enumerate(nodes)}
        n = len(nodes)
        
        self.matrix = np.zeros((n, n), dtype=int)
        for edge in self.graph.get_all_edges():
            i = self.node_indices[edge.source_id]
            j = self.node_indices[edge.target_id]
            self.matrix[i][j] = 1

    def to_dict(self) -> Dict[str, Any]:
        """Get the adjacency matrix as a dictionary."""

        return {
            "matrix": self.matrix.tolist(),
            "node_indices": self.node_indices
        }

    def to_string(self) -> str:
        """Get a string representation of the adjacency matrix."""

        nodes = sorted(self.node_indices.items(), key=lambda x: x[1])
        node_labels = [self.graph.get_node(id).text for id, _ in nodes]
        
        lines = ["   " + " ".join(f"{label:>8}" for label in node_labels)]
        for i, (node_id, _) in enumerate(nodes):
            node = self.graph.get_node(node_id)
            row = [f"{node.text:>3}"] + [f"{self.matrix[i][j]:>8}" for j in range(len(nodes))]
            lines.append(" ".join(row))
        return "\n".join(lines)


class IncidenceMatrixView:
    """Incidence matrix representation."""
    
    def __init__(self, graph: "m_base_graph.BaseGraph"):
        self.graph = graph
        self._build_view()

    def _build_view(self) -> None:
        """Build the incidence matrix representation."""

        nodes = list(self.graph.get_all_nodes())
        edges = list(self.graph.get_all_edges())
        
        self.node_indices = {node.id: i for i, node in enumerate(nodes)}
        self.edge_indices = {edge.id: i for i, edge in enumerate(edges)}
        
        self.matrix = np.zeros((len(nodes), len(edges)), dtype=int)
        for edge in edges:
            j = self.edge_indices[edge.id]
            self.matrix[self.node_indices[edge.source_id]][j] = -1
            self.matrix[self.node_indices[edge.target_id]][j] = 1

    def to_dict(self) -> Dict[str, Any]:
        """Get the incidence matrix as a dictionary."""

        return {
            "matrix": self.matrix.tolist(),
            "node_indices": self.node_indices,
            "edge_indices": self.edge_indices
        }

    def to_string(self) -> str:
        """Get a string representation of the incidence matrix."""

        nodes = sorted(self.node_indices.items(), key=lambda x: x[1])
        edges = sorted(self.edge_indices.items(), key=lambda x: x[1])
        
        edge_labels = [f"E{i}" for i in range(len(edges))]
        lines = ["   " + " ".join(f"{label:>4}" for label in edge_labels)]
        
        for i, (node_id, _) in enumerate(nodes):
            node = self.graph.get_node(node_id)
            row = [f"{node.text:>3}"] + [f"{self.matrix[i][j]:>4}" for j in range(len(edges))]
            lines.append(" ".join(row))
        
        # Add edge descriptions
        lines.append("\nEdge descriptions:")
        for edge_id, j in self.edge_indices.items():
            edge = self.graph.get_edge(edge_id)
            source = self.graph.get_node(edge.source_id)
            target = self.graph.get_node(edge.target_id)
            lines.append(f"E{j}: {source.text} -> {target.text}")
        
        return "\n".join(lines)


class IncidenceListView:
    """Incidence list representation for hypergraphs."""
    
    def __init__(self, graph: "m_base_graph.BaseGraph"):
        self.graph = graph
        self._build_view()

    def _build_view(self) -> None:
        """Build the incidence list representation."""

        self.incidence_list: Dict[str, List[str]] = {}
        for node in self.graph.get_all_nodes():
            self.incidence_list[node.id] = []
            for edge in self.graph.get_all_edges():
                if hasattr(edge, 'is_hyperedge') and edge.is_hyperedge:
                    if node.id in edge.source_ids or node.id in edge.target_ids:
                        self.incidence_list[node.id].append(edge.id)

    def to_dict(self) -> Dict[str, List[str]]:
        """Get the incidence list as a dictionary."""

        return self.incidence_list

    def to_string(self) -> str:
        """Get a string representation of the incidence list."""

        lines = []
        for node_id, edge_ids in self.incidence_list.items():
            node = self.graph.get_node(node_id)
            edges = [self.graph.get_edge(e) for e in edge_ids]
            lines.append(f"{node.text} in edges: {', '.join(f'E{i}' for i, _ in enumerate(edges))}")
        return "\n".join(lines)


class DualIncidenceListView:
    """Dual incidence list representation for hypergraphs."""
    
    def __init__(self, graph: "m_base_graph.BaseGraph"):
        self.graph = graph
        self._build_view()

    def _build_view(self) -> None:
        """Build the dual incidence list representation."""

        self.dual_list: Dict[str, Dict[str, List[str]]] = {}
        for edge in self.graph.get_all_edges():
            if hasattr(edge, 'is_hyperedge') and edge.is_hyperedge:
                self.dual_list[edge.id] = {
                    "source_nodes": edge.source_ids,
                    "target_nodes": edge.target_ids
                }

    def to_dict(self) -> Dict[str, Dict[str, List[str]]]:
        """Get the dual incidence list as a dictionary."""

        return self.dual_list

    def to_string(self) -> str:
        """Get a string representation of the dual incidence list."""

        lines = []
        for i, (edge_id, data) in enumerate(self.dual_list.items()):
            sources = [self.graph.get_node(n).text for n in data["source_nodes"]]
            targets = [self.graph.get_node(n).text for n in data["target_nodes"]]
            lines.append(f"E{i}:")
            lines.append(f"  Sources: {', '.join(sources)}")
            lines.append(f"  Targets: {', '.join(targets)}")
        return "\n".join(lines)


class HierarchicalDictView:
    """Hierarchical dictionary representation for nested graphs."""
    
    def __init__(self, graph: "m_base_graph.BaseGraph"):
        self.graph = graph
        self._build_view()

    def _build_view(self) -> None:
        """Build the hierarchical dictionary representation."""

        def build_hierarchy(node_id: str) -> Dict[str, Any]:
            node = self.graph.get_node(node_id)
            if not node:
                return {}
            
            hierarchy = {
                "id": node.id,
                "text": node.text,
                "children": []
            }
            
            if hasattr(node, 'subgraph') and node.subgraph:
                for child in node.subgraph.get_all_nodes():
                    child_hierarchy = build_hierarchy(child.id)
                    if child_hierarchy:
                        hierarchy["children"].append(child_hierarchy)
            
            return hierarchy
        
        # Find root nodes (nodes with no incoming edges)
        root_nodes = []
        for node in self.graph.get_all_nodes():
            if not self.graph.get_edges_to_node(node.id):
                root_nodes.append(node.id)
        
        # Build hierarchy from each root node
        self.forest = []
        for root_id in root_nodes:
            self.forest.append(build_hierarchy(root_id))

    def to_dict(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get the hierarchical dictionary as a dictionary."""

        return {"forest": self.forest}

    def to_string(self) -> str:
        """Get a string representation of the hierarchical dictionary."""

        def format_tree(node: Dict[str, Any], level: int = 0) -> List[str]:
            lines = [("  " * level) + node["text"]]
            for child in node.get("children", []):
                lines.extend(format_tree(child, level + 1))
            return lines
        
        lines = []
        for tree in self.forest:
            lines.extend(format_tree(tree))
        return "\n".join(lines)


class GraphOfGraphsView:
    """Graph of graphs representation for nested graphs."""
    
    def __init__(self, graph: "m_base_graph.BaseGraph"):
        self.graph = graph
        self._build_view()

    def _build_view(self) -> None:
        """Build the graph of graphs representation."""

        self.subgraphs: Dict[str, Dict[str, List[str]]] = {}
        self.connections: List[Dict[str, str]] = []
        
        # Group nodes into subgraphs
        for node in self.graph.get_all_nodes():
            if hasattr(node, 'subgraph') and node.subgraph:
                subgraph_id = node.id
                self.subgraphs[subgraph_id] = {
                    "nodes": [n.id for n in node.subgraph.get_all_nodes()],
                    "edges": [e.id for e in node.subgraph.get_all_edges()]
                }
        
        # Find connections between subgraphs
        for edge in self.graph.get_all_edges():
            source_subgraph = None
            target_subgraph = None
            
            for subgraph_id, subgraph in self.subgraphs.items():
                if edge.source_id in subgraph["nodes"]:
                    source_subgraph = subgraph_id
                if edge.target_id in subgraph["nodes"]:
                    target_subgraph = subgraph_id
            
            if source_subgraph != target_subgraph:
                self.connections.append({
                    "from": source_subgraph,
                    "to": target_subgraph,
                    "edge": edge.id
                })

    def to_dict(self) -> Dict[str, Any]:
        """Get the graph of graphs as a dictionary."""

        return {
            "subgraphs": self.subgraphs,
            "connections": self.connections
        }

    def to_string(self) -> str:
        """Get a string representation of the graph of graphs."""

        lines = ["Subgraphs:"]
        for subgraph_id, data in self.subgraphs.items():
            node = self.graph.get_node(subgraph_id)
            lines.append(f"\n{node.text}:")
            nodes = [self.graph.get_node(n).text for n in data["nodes"]]
            lines.append(f"  Nodes: {', '.join(nodes)}")
        
        lines.append("\nConnections:")
        for conn in self.connections:
            source = self.graph.get_node(conn["from"])
            target = self.graph.get_node(conn["to"])
            edge = self.graph.get_edge(conn["edge"])
            lines.append(f"{source.text} -> {target.text} via {edge.id}")
        
        return "\n".join(lines)


class RecursiveIncidenceView:
    """Recursive incidence structure for ubergraphs."""
    
    def __init__(self, graph: "m_base_graph.BaseGraph"):
        self.graph = graph
        self._build_view()

    def _build_view(self) -> None:
        """Build the recursive incidence structure."""

        def build_recursive_structure(edge_id: str, visited: Set[str]) -> Dict[str, Any]:
            if edge_id in visited:
                return {"id": edge_id, "cyclic": True}
            
            visited.add(edge_id)
            edge = self.graph.get_edge(edge_id)
            if not edge:
                return {}
            
            structure = {
                "id": edge_id,
                "source_nodes": edge.source_ids if hasattr(edge, 'source_ids') else [edge.source_id],
                "target_nodes": edge.target_ids if hasattr(edge, 'target_ids') else [edge.target_id],
                "nested_edges": []
            }
            
            # Find edges connected to this edge when it's viewed as a node
            for other_edge in self.graph.get_all_edges():
                if (hasattr(other_edge, 'is_hyperedge') and other_edge.is_hyperedge and
                    edge_id in other_edge.source_ids + other_edge.target_ids):
                    nested = build_recursive_structure(other_edge.id, visited.copy())
                    if nested:
                        structure["nested_edges"].append(nested)
            
            return structure
        
        # Start with edges that aren't targets of other edges
        self.top_level_edges = set(e.id for e in self.graph.get_all_edges())
        for edge in self.graph.get_all_edges():
            if hasattr(edge, 'is_hyperedge') and edge.is_hyperedge:
                for target_id in edge.target_ids:
                    self.top_level_edges.discard(target_id)
        
        self.recursive_structure = []
        for edge_id in self.top_level_edges:
            structure = build_recursive_structure(edge_id, set())
            if structure:
                self.recursive_structure.append(structure)

    def to_dict(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get the recursive incidence structure as a dictionary."""

        return {"recursive_structure": self.recursive_structure}

    def to_string(self) -> str:
        """Get a string representation of the recursive incidence structure."""

        def format_structure(struct: Dict[str, Any], level: int = 0) -> List[str]:
            edge = self.graph.get_edge(struct["id"])
            indent = "  " * level
            
            lines = [f"{indent}Edge {edge.id}:"]
            if "cyclic" in struct:
                lines.append(f"{indent}  (cyclic reference)")
                return lines
            
            sources = [self.graph.get_node(n).text for n in struct["source_nodes"]]
            targets = [self.graph.get_node(n).text for n in struct["target_nodes"]]
            
            lines.append(f"{indent}  Sources: {', '.join(sources)}")
            lines.append(f"{indent}  Targets: {', '.join(targets)}")
            
            if struct["nested_edges"]:
                lines.append(f"{indent}  Nested edges:")
                for nested in struct["nested_edges"]:
                    lines.extend(format_structure(nested, level + 2))
            
            return lines
        
        lines = []
        for structure in self.recursive_structure:
            lines.extend(format_structure(structure))
        return "\n".join(lines)


class DirectedAcyclicMetagraphView:
    """Directed acyclic meta-graph representation for ubergraphs."""
    
    def __init__(self, graph: "m_base_graph.BaseGraph"):
        self.graph = graph
        self._build_view()

    def _build_view(self) -> None:
        """Build the directed acyclic meta-graph representation."""

        def find_meta_levels() -> Dict[str, int]:
            """Assign level numbers to edges in the meta-graph."""

            levels = {}
            edges = list(self.graph.get_all_edges())
            
            # Initialize with edges that aren't referenced by other edges
            queue = []
            for edge in edges:
                if not any(edge.id in other.target_ids for other in edges
                          if hasattr(other, 'is_hyperedge') and other.is_hyperedge):
                    levels[edge.id] = 0
                    queue.append(edge.id)
            
            # Propagate levels
            while queue:
                current_id = queue.pop(0)
                current_edge = self.graph.get_edge(current_id)
                
                # Look for edges that reference this edge
                for edge in edges:
                    if (hasattr(edge, 'is_hyperedge') and edge.is_hyperedge and
                        current_id in edge.source_ids):
                        new_level = levels[current_id] + 1
                        if edge.id not in levels or levels[edge.id] < new_level:
                            levels[edge.id] = new_level
                            queue.append(edge.id)
            
            return levels
        
        self.levels = find_meta_levels()
        self.meta_edges = []
        
        # Create meta-edges between levels
        for edge in self.graph.get_all_edges():
            if hasattr(edge, 'is_hyperedge') and edge.is_hyperedge:
                for source_id in edge.source_ids:
                    if source_id in self.levels:
                        self.meta_edges.append({
                            "from": source_id,
                            "to": edge.id,
                            "from_level": self.levels[source_id],
                            "to_level": self.levels[edge.id]
                        })

    def to_dict(self) -> Dict[str, Any]:
        """Get the directed acyclic meta-graph as a dictionary."""

        return {
            "levels": self.levels,
            "meta_edges": self.meta_edges
        }

    def to_string(self) -> str:
        """Get a string representation of the directed acyclic meta-graph."""

        # Group edges by level
        level_groups: Dict[int, List[str]] = {}
        for edge_id, level in self.levels.items():
            if level not in level_groups:
                level_groups[level] = []
            level_groups[level].append(edge_id)
        
        lines = ["Levels:"]
        for level in sorted(level_groups.keys()):
            edges = [self.graph.get_edge(e).id for e in level_groups[level]]
            lines.append(f"Level {level}: {', '.join(edges)}")
        
        lines.append("\nMeta-edges:")
        for edge in self.meta_edges:
            source = self.graph.get_edge(edge["from"])
            target = self.graph.get_edge(edge["to"])
            lines.append(f"{source.id} (L{edge['from_level']}) -> {target.id} (L{edge['to_level']})")
        
        return "\n".join(lines)