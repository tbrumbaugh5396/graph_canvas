"""
Algorithms for nested graphs.
"""


from typing import List, Set, Dict, Optional, Any, Tuple, Callable
from collections import defaultdict, deque

import graph_canvas.presentation.desktop.models.nested_graph as m_nested_graph
import graph_canvas.presentation.desktop.models.basic_graph as m_basic_graph
import graph_canvas.presentation.desktop.models.node as m_node
import graph_canvas.presentation.desktop.models.edge as m_edge


# Flatten a nested graph into a graph (i.e. a graph that has no nested graphs)
def flatten_nested_graph(graph: m_nested_graph.NestedGraph) -> m_basic_graph.BasicGraph:
    """Convert nested graph to flat graph."""

    flat = m_basic_graph.BasicGraph(name=f"Flattened {graph.name}")
    
    def get_full_path(node: m_nested_graph.NestedNode) -> str:
        """Get full path to node including parent nodes."""

        path = [node.text]
        current_graph = graph
        while current_graph.parent_node:
            path.append(current_graph.parent_node.text)
            current_graph = current_graph.parent_node.subgraph
        return " > ".join(reversed(path))
    
    def flatten_recursive(current_graph: m_nested_graph.NestedGraph,
                        path_prefix: str = "") -> Dict[str, str]:
        """Recursively flatten graph, returning mapping of old to new node IDs."""

        node_mapping = {}
        
        # Add nodes
        for node in current_graph.get_all_nodes():
            if isinstance(node, NestedNode):
                # Create flattened node
                node_path = f"{path_prefix}/{node.text}" if path_prefix else node.text
                flat_node = m_node.Node(
                    text=get_full_path(node),
                    x=node.x,
                    y=node.y,
                    width=node.width,
                    height=node.height,
                    color=node.color,
                    metadata={"original_id": node.id, "path": node_path}
                )
                flat.add_node(flat_node)
                node_mapping[node.id] = flat_node.id
                
                # Recursively flatten subgraph
                if node.subgraph:
                    sub_mapping = flatten_recursive(node.subgraph, node_path)
                    node_mapping.update(sub_mapping)
        
        # Add edges
        for edge in current_graph.get_all_edges():
            if isinstance(edge, m_nested_graph.NestedEdge):
                source_id = node_mapping.get(edge.source_id)
                target_id = node_mapping.get(edge.target_id)
                if source_id and target_id:
                    flat_edge = m_edge.Edge(
                        source_id=source_id,
                        target_id=target_id,
                        directed=edge.directed
                    )
                    flat.add_edge(flat_edge)
        
        return node_mapping
    
    flatten_recursive(graph)
    return flat


# Traverse a nested graph recursively
def recursive_traversal(graph: m_nested_graph.NestedGraph,
                       node_func: Optional[Callable[[m_nested_graph.NestedNode, int], None]] = None,
                       edge_func: Optional[Callable[[m_nested_graph.NestedEdge, int], None]] = None) -> None:
    """Traverse nested graph recursively."""

    def traverse_recursive(current_graph: m_nested_graph.NestedGraph, level: int) -> None:
        # Process nodes
        for node in current_graph.get_all_nodes():
            if isinstance(node, m_nested_graph.NestedNode):
                if node_func:
                    node_func(node, level)
                
                # Traverse subgraph
                if node.subgraph:
                    traverse_recursive(node.subgraph, level + 1)
        
        # Process edges
        for edge in current_graph.get_all_edges():
            if isinstance(edge, m_nested_graph.NestedEdge) and edge_func:
                edge_func(edge, level)
    
    traverse_recursive(graph, 0)


# Pattern matching
def pattern_matching(graph: m_nested_graph.NestedGraph, pattern: m_nested_graph.NestedGraph) -> List[Dict[str, str]]:
    """Find all occurrences of pattern in graph."""

    def is_match(node1: m_nested_graph.NestedNode, node2: m_nested_graph.NestedNode) -> bool:
        """Check if two nodes match."""

        # Check basic properties
        if not (node1.text == node2.text and
                isinstance(node1, m_nested_graph.NestedNode) and
                isinstance(node2, m_nested_graph.NestedNode)):
            return False
        
        # Check subgraphs
        if bool(node1.subgraph) != bool(node2.subgraph):
            return False
        
        if node1.subgraph and node2.subgraph:
            return is_subgraph_match(node1.subgraph, node2.subgraph)
        
        return True
    
    def is_subgraph_match(graph1: m_nested_graph.NestedGraph, graph2: m_nested_graph.NestedGraph) -> bool:
        """Check if two subgraphs match."""

        # Check number of nodes and edges
        if (len(graph1.get_all_nodes()) != len(graph2.get_all_nodes()) or
            len(graph1.get_all_edges()) != len(graph2.get_all_edges())):
            return False
        
        # Try to find bijective mapping between nodes
        def find_mapping(nodes1: List[m_nested_graph.NestedNode], nodes2: List[m_nested_graph.NestedNode],
                        mapping: Dict[str, str]) -> Optional[Dict[str, str]]:
            if not nodes1:
                # Check if edge structure matches under mapping
                for edge2 in graph2.get_all_edges():
                    found_match = False
                    for edge1 in graph1.get_all_edges():
                        if (mapping[edge2.source_id] == edge1.source_id and
                            mapping[edge2.target_id] == edge1.target_id):
                            found_match = True
                            break
                    if not found_match:
                        return None
                return mapping
            
            node1 = nodes1[0]
            remaining1 = nodes1[1:]
            
            # Try matching with each available node in graph2
            for i, node2 in enumerate(nodes2):
                if is_match(node1, node2):
                    new_mapping = mapping.copy()
                    new_mapping[node2.id] = node1.id
                    result = find_mapping(remaining1,
                                       nodes2[:i] + nodes2[i+1:],
                                       new_mapping)
                    if result:
                        return result
            
            return None
        
        return bool(find_mapping(list(graph1.get_all_nodes()),
                               list(graph2.get_all_nodes()), {}))
    
    matches = []
    
    # Try matching pattern at each node
    for node in graph.get_all_nodes():
        if isinstance(node, m_nested_graph.NestedNode):
            mapping = {}
            pattern_root = next(iter(pattern.get_all_nodes()))
            if pattern_root and is_match(node, pattern_root):
                # Found potential match, try to extend
                if node.subgraph and pattern_root.subgraph:
                    if is_subgraph_match(node.subgraph, pattern_root.subgraph):
                        mapping[pattern_root.id] = node.id
                        matches.append(mapping)
                else:
                    mapping[pattern_root.id] = node.id
                    matches.append(mapping)
    
    return matches


# Hierarchical clustering of a nested graph into k clusters (agglomerative clustering)
def hierarchical_clustering(graph: m_nested_graph.NestedGraph, k: int) -> m_nested_graph.NestedGraph:
    """Cluster graph into k hierarchical clusters."""

    # First flatten graph
    flat = flatten_nested_graph(graph)
    
    # Build distance matrix
    nodes = list(flat.get_all_nodes())
    n = len(nodes)
    distances = [[0.0] * n for _ in range(n)]
    
    for i in range(n):
        for j in range(i + 1, n):
            # Compute distance based on graph structure
            path = flat.get_path(nodes[i].id, nodes[j].id)
            distances[i][j] = distances[j][i] = len(path) if path else float('inf')
    
    # Hierarchical clustering
    clusters = [{i} for i in range(n)]
    
    while len(clusters) > k:
        # Find closest clusters
        min_dist = float('inf')
        merge_i = merge_j = 0
        
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                # Compute average linkage distance
                dist = 0.0
                count = 0
                for ni in clusters[i]:
                    for nj in clusters[j]:
                        dist += distances[ni][nj]
                        count += 1
                dist /= count
                
                if dist < min_dist:
                    min_dist = dist
                    merge_i = i
                    merge_j = j
        
        # Merge clusters
        clusters[merge_i].update(clusters[merge_j])
        clusters.pop(merge_j)
    
    # Create hierarchical structure
    result = m_nested_graph.NestedGraph(name=f"Clustered {graph.name}")
    
    # Create top-level cluster nodes
    for i, cluster in enumerate(clusters):
        cluster_node = m_nested_graph.NestedNode(text=f"Cluster {i}")
        result.add_node(cluster_node)
        
        # Create subgraph for cluster
        subgraph = m_nested_graph.NestedGraph()
        cluster_node.set_subgraph(subgraph)
        
        # Add nodes to subgraph
        node_mapping = {}
        for j in cluster:
            node = nodes[j]
            new_node = m_nested_graph.NestedNode(
                text=node.text,
                x=node.x,
                y=node.y,
                width=node.width,
                height=node.height,
                color=node.color
            )
            subgraph.add_node(new_node)
            node_mapping[node.id] = new_node.id
        
        # Add edges within cluster
        for edge in flat.get_all_edges():
            if (edge.source_id in node_mapping and
                edge.target_id in node_mapping):
                new_edge = m_nested_graph.NestedEdge(
                    source_id=node_mapping[edge.source_id],
                    target_id=node_mapping[edge.target_id],
                    directed=edge.directed
                )
                subgraph.add_edge(new_edge)
    
    # Add edges between clusters
    for edge in flat.get_all_edges():
        source_cluster = None
        target_cluster = None
        
        for i, cluster in enumerate(clusters):
            for j in cluster:
                if nodes[j].id == edge.source_id:
                    source_cluster = i
                if nodes[j].id == edge.target_id:
                    target_cluster = i
        
        if source_cluster != target_cluster:
            result_nodes = list(result.get_all_nodes())
            new_edge = m_nested_graph.NestedEdge(
                source_id=result_nodes[source_cluster].id,
                target_id=result_nodes[target_cluster].id,
                directed=edge.directed
            )
            result.add_edge(new_edge)
    
    return result


# Query a nested graph using simple path expressions
def query_nested_graph(graph: m_nested_graph.NestedGraph, query: str) -> List[m_nested_graph.NestedNode]:
    """Query nested graph using simple path expressions."""

    def parse_query(query: str) -> List[str]:
        """Parse query into path components."""

        return [part.strip() for part in query.split("/") if part.strip()]
    
    def match_component(node: m_nested_graph.NestedNode, component: str) -> bool:
        """Check if node matches query component."""

        if component == "*":
            return True
        if component == "..":
            return bool(graph.get_parent(node.id))
        return node.text == component
    
    def find_matches(current_graph: m_nested_graph.NestedGraph,
                    components: List[str],
                    current_matches: List[m_nested_graph.NestedNode]) -> List[m_nested_graph.NestedNode]:
        """Recursively find nodes matching query components."""

        if not components:
            return current_matches
        
        component = components[0]
        remaining = components[1:]
        matches = []
        
        if component == "..":
            # Move up to parent nodes
            for node in current_matches:
                parent = graph.get_parent(node.id)
                if parent and isinstance(parent, m_nested_graph.NestedNode):
                    matches.append(parent)
        elif component == "**":
            # Recursive descent
            def collect_recursive(node: m_nested_graph.NestedNode) -> None:
                if node.subgraph:
                    for child in node.subgraph.get_all_nodes():
                        if isinstance(child, m_nested_graph.NestedNode):
                            matches.append(child)
                            collect_recursive(child)
            
            for node in current_matches:
                collect_recursive(node)
        else:
            # Match nodes in current level
            for node in current_matches:
                if node.subgraph:
                    for child in node.subgraph.get_all_nodes():
                        if (isinstance(child, m_nested_graph.NestedNode) and
                            match_component(child, component)):
                            matches.append(child)
        
        return find_matches(current_graph, remaining, matches)
    
    # Start with root nodes
    components = parse_query(query)
    if not components:
        return []
    
    root_matches = []
    for node in graph.get_all_nodes():
        if (isinstance(node, m_nested_graph.NestedNode) and
            match_component(node, components[0])):
            root_matches.append(node)
    
    return find_matches(graph, components[1:], root_matches)
