"""
Algorithms for hypergraphs.
"""


from typing import List, Set, Dict, Optional, Any, Tuple, Callable
from collections import defaultdict, deque
import numpy as np

import graph_canvas.presentation.desktop.models.hypergraph as m_hypergraph
import graph_canvas.presentation.desktop.models.node as m_node


def hypergraph_traversal(graph: m_hypergraph.Hypergraph, start_id: str,
                        visit_func: Optional[Callable[[m_node.Node], None]] = None) -> List[m_node.Node]:
    """Traverse hypergraph starting from a node."""

    visited_nodes = set()
    visited_edges = set()
    result = []
    
    def visit_node(node_id: str) -> None:
        if node_id in visited_nodes:
            return
        
        node = graph.get_node(node_id)
        if node:
            visited_nodes.add(node_id)
            result.append(node)
            if visit_func:
                visit_func(node)
            
            # Visit all hyperedges containing this node
            for edge in graph.get_node_hyperedges(node_id):
                visit_edge(edge.id)
    
    def visit_edge(edge_id: str) -> None:
        if edge_id in visited_edges:
            return
        
        edge = graph.get_edge(edge_id)
        if isinstance(edge, m_hypergraph.HypergraphEdge):
            visited_edges.add(edge_id)
            
            # Visit all nodes in the hyperedge
            for node_id in edge.source_ids + edge.target_ids:
                visit_node(node_id)
    
    visit_node(start_id)
    return result


def hypergraph_cut(graph: m_hypergraph.Hypergraph, weights: Dict[str, float]) -> Tuple[Set[str], float]:
    """Find minimum hypergraph cut using recursive bisection."""

    def compute_cut_value(partition: Set[str]) -> float:
        """Compute the value of a cut."""

        value = 0.0
        for edge in graph.get_all_edges():
            if isinstance(edge, m_hypergraph.HypergraphEdge):
                # Edge contributes to cut if it crosses the partition
                sources_in = any(n in partition for n in edge.source_ids)
                sources_out = any(n not in partition for n in edge.source_ids)
                targets_in = any(n in partition for n in edge.target_ids)
                targets_out = any(n not in partition for n in edge.target_ids)
                
                if (sources_in and sources_out) or (targets_in and targets_out):
                    value += weights.get(edge.id, 1.0)
        return value
    
    def improve_partition(partition: Set[str]) -> Set[str]:
        """Try to improve partition using local search."""

        improved = True
        while improved:
            improved = False
            
            # Try moving each boundary node
            boundary = set()
            for edge in graph.get_all_edges():
                if isinstance(edge, m_hypergraph.HypergraphEdge):
                    if (any(n in partition for n in edge.source_ids + edge.target_ids) and
                        any(n not in partition for n in edge.source_ids + edge.target_ids)):
                        boundary.update(n for n in edge.source_ids + edge.target_ids)
            
            for node_id in boundary:
                old_value = compute_cut_value(partition)
                if node_id in partition:
                    partition.remove(node_id)
                else:
                    partition.add(node_id)
                
                new_value = compute_cut_value(partition)
                if new_value < old_value:
                    improved = True
                else:
                    # Revert move
                    if node_id in partition:
                        partition.remove(node_id)
                    else:
                        partition.add(node_id)
        
        return partition
    
    # Start with random partition
    import random
    nodes = list(graph.get_all_nodes())
    partition = set(node.id for node in random.sample(nodes, len(nodes) // 2))
    
    # Improve partition
    partition = improve_partition(partition)
    cut_value = compute_cut_value(partition)
    
    return partition, cut_value


def hypergraph_clustering(graph: m_hypergraph.Hypergraph, k: int,
                         weights: Dict[str, float]) -> List[Set[str]]:
    """Cluster hypergraph into k clusters using spectral clustering."""

    # Build incidence matrix
    nodes = list(graph.get_all_nodes())
    edges = list(graph.get_all_edges())
    n = len(nodes)
    m = len(edges)
    
    node_indices = {node.id: i for i, node in enumerate(nodes)}
    H = np.zeros((n, m))
    
    for j, edge in enumerate(edges):
        if isinstance(edge, m_hypergraph.HypergraphEdge):
            w = weights.get(edge.id, 1.0)
            for node_id in edge.source_ids + edge.target_ids:
                i = node_indices[node_id]
                H[i, j] = w
    
    # Compute Laplacian
    W = H @ H.T  # Weighted adjacency matrix
    D = np.diag(W.sum(axis=1))  # Degree matrix
    L = D - W  # Laplacian matrix
    
    # Compute eigenvectors
    eigenvalues, eigenvectors = np.linalg.eigh(L)
    
    # Use k smallest non-zero eigenvectors
    k = min(k, n - 1)
    V = eigenvectors[:, 1:k+1]  # Skip first eigenvector (constant)
    
    # Cluster rows using k-means
    from sklearn.cluster import KMeans
    kmeans = KMeans(n_clusters=k, random_state=0)
    labels = kmeans.fit_predict(V)
    
    # Convert back to node sets
    clusters = [set() for _ in range(k)]
    for i, label in enumerate(labels):
        clusters[label].add(nodes[i].id)
    
    return clusters


def minimal_transversals(graph: m_hypergraph.Hypergraph) -> List[Set[str]]:
    """Find all minimal transversals (hitting sets) of the hypergraph."""

    def is_minimal_transversal(nodes: Set[str], transversal: Set[str]) -> bool:
        """Check if transversal is minimal."""

        # Must hit all edges
        for edge in graph.get_all_edges():
            if isinstance(edge, m_hypergraph.HypergraphEdge):
                if not (set(edge.source_ids) & transversal or
                       set(edge.target_ids) & transversal):
                    return False
        
        # Must be minimal
        for node in transversal:
            smaller = transversal - {node}
            all_hit = True
            for edge in graph.get_all_edges():
                if isinstance(edge, m_hypergraph.HypergraphEdge):
                    if not (set(edge.source_ids) & smaller or
                           set(edge.target_ids) & smaller):
                        all_hit = False
                        break
            if all_hit:
                return False
        
        return True
    
    def extend_transversal(nodes: Set[str], current: Set[str],
                          remaining: Set[str]) -> List[Set[str]]:
        """Recursively find all minimal transversals."""

        result = []
        
        # Check if current set is a minimal transversal
        if is_minimal_transversal(nodes, current):
            result.append(current)
            return result
        
        # Try extending with each remaining node
        for node in remaining:
            new_current = current | {node}
            new_remaining = {n for n in remaining if n > node}  # Lexicographic order
            result.extend(extend_transversal(nodes, new_current, new_remaining))
        
        return result
    
    # Get all nodes that appear in edges
    nodes = set()
    for edge in graph.get_all_edges():
        if isinstance(edge, m_hypergraph.HypergraphEdge):
            nodes.update(edge.source_ids)
            nodes.update(edge.target_ids)
    
    return extend_transversal(nodes, set(), nodes)


def dual_hypergraph(graph: m_hypergraph.Hypergraph) -> m_hypergraph.Hypergraph:
    """Construct the dual hypergraph."""

    dual = Hypergraph(name=f"Dual of {graph.name}")
    
    # Create nodes for each hyperedge
    edge_to_node = {}
    for edge in graph.get_all_edges():
        if isinstance(edge, m_hypergraph.HypergraphEdge):
            node = m_node.Node(text=f"Edge {edge.id}")
            dual.add_node(node)
            edge_to_node[edge.id] = node.id
    
    # Create hyperedges for each node
    for node in graph.get_all_nodes():
        # Get all hyperedges containing this node
        incident_edges = graph.get_node_hyperedges(node.id)
        if incident_edges:
            # Create sources from edges where node is a source
            sources = [edge_to_node[e.id] for e in incident_edges
                      if node.id in e.source_ids]
            # Create targets from edges where node is a target
            targets = [edge_to_node[e.id] for e in incident_edges
                      if node.id in e.target_ids]
            
            if sources or targets:
                edge = m_hypergraph.HypergraphEdge()
                edge.source_ids = sources
                edge.target_ids = targets
                dual.add_edge(edge)
    
    return dual


def set_cover_approximation(graph: m_hypergraph.Hypergraph) -> List[str]:
    """Find approximate minimum set cover using greedy algorithm."""

    # Get all nodes that need to be covered
    universe = set()
    for edge in graph.get_all_edges():
        if isinstance(edge, m_hypergraph.HypergraphEdge):
            universe.update(edge.source_ids)
            universe.update(edge.target_ids)
    
    # Initialize sets for each hyperedge
    sets = {}
    for edge in graph.get_all_edges():
        if isinstance(edge, m_hypergraph.HypergraphEdge):
            sets[edge.id] = set(edge.source_ids) | set(edge.target_ids)
    
    # Greedy algorithm
    cover = []
    remaining = universe.copy()
    
    while remaining:
        # Find set that covers most remaining elements
        best_edge = max(sets.items(),
                       key=lambda x: len(x[1] & remaining))[0]
        
        cover.append(best_edge)
        remaining -= sets[best_edge]
    
    return cover


def connected_components_hypergraph(graph: m_hypergraph.Hypergraph) -> List[Set[str]]:
    """Find connected components in hypergraph."""

    components = []
    unvisited = set(node.id for node in graph.get_all_nodes())
    
    while unvisited:
        # Start new component
        start = next(iter(unvisited))
        component = set()
        
        # Traverse component
        stack = [start]
        while stack:
            node_id = stack.pop()
            if node_id in unvisited:
                component.add(node_id)
                unvisited.remove(node_id)
                
                # Add all nodes connected through hyperedges
                for edge in graph.get_node_hyperedges(node_id):
                    stack.extend(n for n in edge.source_ids + edge.target_ids
                               if n in unvisited)
        
        components.append(component)
    
    return components


def s_t_connectivity(graph: m_hypergraph.Hypergraph, source_id: str,
                    target_id: str) -> Optional[List[m_hypergraph.HypergraphEdge]]:
    """Find path between two nodes through hyperedges."""

    visited_nodes = {source_id}
    visited_edges = set()
    queue = deque([(source_id, [])])
    
    while queue:
        node_id, path = queue.popleft()
        
        if node_id == target_id:
            return path
        
        # Try all hyperedges containing this node
        for edge in graph.get_node_hyperedges(node_id):
            if edge.id not in visited_edges:
                visited_edges.add(edge.id)
                
                # Add all nodes in the hyperedge
                for next_id in edge.source_ids + edge.target_ids:
                    if next_id not in visited_nodes:
                        visited_nodes.add(next_id)
                        queue.append((next_id, path + [edge]))
    
    return None  # No path found
