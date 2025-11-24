"""
Algorithms for ubergraphs (graphs with edges as nodes).
"""


from typing import List, Set, Dict, Optional, Any, Tuple, Callable
from collections import defaultdict, deque

import graph_canvas.presentation.desktop.models.ubergraph as m_ubergraph
import graph_canvas.presentation.desktop.models.node as m_node
import graph_canvas.presentation.desktop.models.edge as m_edge


def semantic_subgraph_matching(graph: m_ubergraph.Ubergraph, pattern: m_ubergraph.Ubergraph,
                             similarity_func: Callable[[m_node.Node, m_node.Node], float],
                             threshold: float = 0.8) -> List[Dict[str, str]]:
    """Find semantic matches of pattern in graph."""

    def node_similarity(node1: m_node.Node, node2: m_node.Node) -> float:
        """Compute semantic similarity between nodes."""

        return similarity_func(node1, node2)
    
    def edge_similarity(edge1: m_ubergraph.UberEdge, edge2: m_ubergraph.UberEdge) -> float:
        """Compute similarity between edges based on structure."""

        # Compare source and target sets
        source_overlap = len(set(edge1.source_ids) & set(edge2.source_ids))
        source_union = len(set(edge1.source_ids) | set(edge2.source_ids))
        target_overlap = len(set(edge1.target_ids) & set(edge2.target_ids))
        target_union = len(set(edge1.target_ids) | set(edge2.target_ids))
        
        source_sim = source_overlap / source_union if source_union > 0 else 1.0
        target_sim = target_overlap / target_union if target_union > 0 else 1.0
        
        return (source_sim + target_sim) / 2
    
    def find_matches(pattern_nodes: List[m_node.Node], graph_nodes: List[m_node.Node],
                    pattern_edges: List[m_ubergraph.UberEdge], graph_edges: List[m_ubergraph.UberEdge],
                    current_mapping: Dict[str, str]) -> List[Dict[str, str]]:
        """Recursively find all valid mappings."""

        if not pattern_nodes and not pattern_edges:
            return [current_mapping]
        
        results = []
        
        if pattern_nodes:
            # Try matching next pattern node
            pattern_node = pattern_nodes[0]
            remaining_pattern_nodes = pattern_nodes[1:]
            
            for graph_node in graph_nodes:
                if (graph_node.id not in current_mapping.values() and
                    node_similarity(pattern_node, graph_node) >= threshold):
                    # Try this mapping
                    new_mapping = current_mapping.copy()
                    new_mapping[pattern_node.id] = graph_node.id
                    
                    results.extend(find_matches(
                        remaining_pattern_nodes,
                        [n for n in graph_nodes if n.id != graph_node.id],
                        pattern_edges,
                        graph_edges,
                        new_mapping
                    ))
        
        elif pattern_edges:
            # Try matching next pattern edge
            pattern_edge = pattern_edges[0]
            remaining_pattern_edges = pattern_edges[1:]
            
            for graph_edge in graph_edges:
                if (graph_edge.id not in current_mapping.values() and
                    edge_similarity(pattern_edge, graph_edge) >= threshold):
                    # Try this mapping
                    new_mapping = current_mapping.copy()
                    new_mapping[pattern_edge.id] = graph_edge.id
                    
                    results.extend(find_matches(
                        pattern_nodes,
                        graph_nodes,
                        remaining_pattern_edges,
                        [e for e in graph_edges if e.id != graph_edge.id],
                        new_mapping
                    ))
        
        return results
    
    # Get nodes and edges that can be matched
    pattern_nodes = [n for n in pattern.get_all_nodes()
                    if not isinstance(n, m_ubergraph.UberEdge)]
    pattern_edges = [e for e in pattern.get_all_edges()
                    if isinstance(e, m_ubergraph.UberEdge) and e.metadata.get("is_uber_node")]
    
    graph_nodes = [n for n in graph.get_all_nodes()
                  if not isinstance(n, m_ubergraph.UberEdge)]
    graph_edges = [e for e in graph.get_all_edges()
                  if isinstance(e, m_ubergraph.UberEdge) and e.metadata.get("is_uber_node")]
    
    return find_matches(pattern_nodes, graph_nodes,
                       pattern_edges, graph_edges, {})


def ontology_based_query(graph: m_ubergraph.Ubergraph,
                        query: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Query graph using ontology-based patterns."""

    def matches_constraints(entity: Any,
                          constraints: Dict[str, Any]) -> bool:
        """Check if entity matches constraint pattern."""

        for key, value in constraints.items():
            if key not in entity.__dict__:
                return False
            if isinstance(value, dict):
                if not matches_constraints(entity.__dict__[key], value):
                    return False
            elif entity.__dict__[key] != value:
                return False
        return True
    
    def find_matches(pattern: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find all matches for a query pattern."""

        results = []
        
        # Handle different entity types
        if "node" in pattern:
            # Match nodes
            for node in graph.get_all_nodes():
                if matches_constraints(node, pattern["node"]):
                    results.append({"node": node})
        
        elif "edge" in pattern:
            # Match edges
            for edge in graph.get_all_edges():
                if isinstance(edge, m_ubergraph.UberEdge):
                    if matches_constraints(edge, pattern["edge"]):
                        results.append({"edge": edge})
        
        elif "path" in pattern:
            # Match paths
            def find_paths(start: str, end: str,
                         constraints: List[Dict[str, Any]]) -> List[List[str]]:
                """Find paths matching constraints."""

                paths = []
                visited = {start}
                current_path = [start]
                
                def dfs(current: str, depth: int) -> None:
                    if depth == len(constraints):
                        if current == end:
                            paths.append(current_path[:])
                        return
                    
                    for edge in graph.get_edges_from_node(current):
                        if (isinstance(edge, m_ubergraph.UberEdge) and
                            matches_constraints(edge, constraints[depth])):
                            next_node = edge.target_id
                            if next_node not in visited:
                                visited.add(next_node)
                                current_path.append(next_node)
                                dfs(next_node, depth + 1)
                                current_path.pop()
                                visited.remove(next_node)
                
                dfs(start, 0)
                return paths
            
            path_pattern = pattern["path"]
            paths = find_paths(path_pattern["start"],
                             path_pattern["end"],
                             path_pattern["constraints"])
            
            for path in paths:
                results.append({"path": path})
        
        return results
    
    return find_matches(query)


def hypergraph_to_ubergraph(graph: m_ubergraph.Ubergraph) -> m_ubergraph.Ubergraph:
    """Convert hypergraph representation to ubergraph."""

    result = m_ubergraph.Ubergraph(name=f"Ubergraph of {graph.name}")
    
    # Copy nodes
    for node in graph.get_all_nodes():
        if not isinstance(node, m_ubergraph.UberEdge):
            result.add_node(node)
    
    # Convert hyperedges to uber-edges
    for edge in graph.get_all_edges():
        if isinstance(edge, m_ubergraph.UberEdge) and edge.is_hyperedge:
            # Create node representation of edge
            uber_edge = m_ubergraph.UberEdge(
                id=edge.id,
                text=f"Edge {edge.id}",
                directed=edge.directed
            )
            uber_edge.metadata["is_uber_node"] = True
            uber_edge.source_ids = edge.source_ids
            uber_edge.target_ids = edge.target_ids
            result.add_edge(uber_edge)
            
            # Create edges for connections
            for source_id in edge.source_ids:
                conn_edge = Edge(source_id=source_id,
                               target_id=uber_edge.id)
                result.add_edge(conn_edge)
            
            for target_id in edge.target_ids:
                conn_edge = Edge(source_id=uber_edge.id,
                               target_id=target_id)
                result.add_edge(conn_edge)
    
    return result


def provenance_tracking(graph: m_ubergraph.Ubergraph) -> Dict[str, List[Dict[str, Any]]]:
    """Track provenance information for nodes and edges."""

    provenance = defaultdict(list)
    
    def record_provenance(entity_id: str,
                         operation: str,
                         details: Dict[str, Any]) -> None:
        """Record provenance information."""

        provenance[entity_id].append({
            "operation": operation,
            "timestamp": details.get("timestamp"),
            "user": details.get("user"),
            "details": details
        })
    
    def track_edge_operations(edge: m_ubergraph.UberEdge) -> None:
        """Track operations on an edge."""

        # Record creation
        record_provenance(edge.id, "created", {
            "timestamp": edge.metadata.get("created_at"),
            "user": edge.metadata.get("created_by")
        })
        
        # Record modifications
        if "modifications" in edge.metadata:
            for mod in edge.metadata["modifications"]:
                record_provenance(edge.id, "modified", mod)
        
        # Track source/target changes
        if "source_changes" in edge.metadata:
            for change in edge.metadata["source_changes"]:
                record_provenance(edge.id, "source_changed", change)
        
        if "target_changes" in edge.metadata:
            for change in edge.metadata["target_changes"]:
                record_provenance(edge.id, "target_changed", change)
    
    # Track provenance for all entities
    for node in graph.get_all_nodes():
        if not isinstance(node, m_ubergraph.UberEdge):
            record_provenance(node.id, "created", {
                "timestamp": node.metadata.get("created_at"),
                "user": node.metadata.get("created_by")
            })
            
            if "modifications" in node.metadata:
                for mod in node.metadata["modifications"]:
                    record_provenance(node.id, "modified", mod)
    
    for edge in graph.get_all_edges():
        if isinstance(edge, m_ubergraph.UberEdge):
            track_edge_operations(edge)
    
    return dict(provenance)


def multigraph_traversal(graph: m_ubergraph.Ubergraph,
                        start_id: str,
                        edge_filter: Optional[Callable[[m_ubergraph.UberEdge], bool]] = None
                        ) -> List[Tuple[str, str, m_ubergraph.UberEdge]]:
    """Traverse multi-edges with filtering."""

    visited_edges = set()
    path = []
    
    def should_traverse(edge: m_ubergraph.UberEdge) -> bool:
        """Check if edge should be traversed."""

        if edge.id in visited_edges:
            return False
        return not edge_filter or edge_filter(edge)
    
    def traverse(current_id: str) -> None:
        """Recursively traverse graph."""

        for edge in graph.get_edges_from_node(current_id):
            if isinstance(edge, m_ubergraph.UberEdge) and should_traverse(edge):
                visited_edges.add(edge.id)
                
                # Record edge in path
                path.append((current_id, edge.target_id, edge))
                
                # Continue traversal
                traverse(edge.target_id)
    
    traverse(start_id)
    return path


def recursive_edge_matching(graph: m_ubergraph.Ubergraph,
                          pattern: Dict[str, Any]) -> List[m_ubergraph.UberEdge]:
    """Find edges matching recursive patterns."""

    def matches_pattern(edge: m_ubergraph.UberEdge,
                       pattern: Dict[str, Any],
                       depth: int = 0) -> bool:
        """Check if edge matches pattern recursively."""

        if depth > 100:  # Prevent infinite recursion
            return False
        
        # Check basic properties
        for key, value in pattern.items():
            if key == "nested_edges":
                continue
            if key not in edge.__dict__ or edge.__dict__[key] != value:
                return False
        
        # Check nested edges if specified
        if "nested_edges" in pattern:
            nested_pattern = pattern["nested_edges"]
            nested_edges = [e for e in graph.get_edges_to_edge(edge.id)
                          if isinstance(e, m_ubergraph.UberEdge)]
            
            if len(nested_edges) != len(nested_pattern):
                return False
            
            # Try to match nested edges recursively
            used = set()
            for p in nested_pattern:
                found_match = False
                for e in nested_edges:
                    if e.id not in used and matches_pattern(e, p, depth + 1):
                        used.add(e.id)
                        found_match = True
                        break
                if not found_match:
                    return False
        
        return True
    
    matches = []
    for edge in graph.get_all_edges():
        if isinstance(edge, m_ubergraph.UberEdge) and matches_pattern(edge, pattern):
            matches.append(edge)
    
    return matches


def inference_engine(graph: m_ubergraph.Ubergraph,
                    rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Perform inference using semantic rules."""

    def apply_rule(rule: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply a single inference rule."""

        results = []
        
        if rule["type"] == "subclass":
            # Infer subclass relationships
            class_a = rule["class_a"]
            class_b = rule["class_b"]
            
            for edge in graph.get_all_edges():
                if (isinstance(edge, m_ubergraph.UberEdge) and
                    edge.metadata.get("type") == class_a):
                    # Create inferred edge
                    inferred = {
                        "type": "inference",
                        "edge_id": edge.id,
                        "rule": "subclass",
                        "inferred_class": class_b
                    }
                    results.append(inferred)
        
        elif rule["type"] == "transitive":
            # Infer transitive relationships
            rel_type = rule["relation"]
            
            for edge1 in graph.get_all_edges():
                if (isinstance(edge1, m_ubergraph.UberEdge) and
                    edge1.metadata.get("type") == rel_type):
                    for edge2 in graph.get_all_edges():
                        if (isinstance(edge2, m_ubergraph.UberEdge) and
                            edge2.metadata.get("type") == rel_type and
                            edge1.target_id == edge2.source_id):
                            # Create inferred transitive relation
                            inferred = {
                                "type": "inference",
                                "edge1_id": edge1.id,
                                "edge2_id": edge2.id,
                                "rule": "transitive",
                                "source_id": edge1.source_id,
                                "target_id": edge2.target_id
                            }
                            results.append(inferred)
        
        elif rule["type"] == "symmetric":
            # Infer symmetric relationships
            rel_type = rule["relation"]
            
            for edge in graph.get_all_edges():
                if (isinstance(edge, m_ubergraph.UberEdge) and
                    edge.metadata.get("type") == rel_type):
                    # Create inferred symmetric relation
                    inferred = {
                        "type": "inference",
                        "edge_id": edge.id,
                        "rule": "symmetric",
                        "source_id": edge.target_id,
                        "target_id": edge.source_id
                    }
                    results.append(inferred)
        
        return results
    
    # Apply all rules
    inferences = []
    for rule in rules:
        inferences.extend(apply_rule(rule))
    
    return inferences
