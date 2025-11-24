"""
Algorithms for analyzing graph properties.
"""


from typing import List, Set, Dict, Optional, Any, Tuple
from collections import defaultdict, deque

import graph_canvas.presentation.desktop.models.basic_graph as m_basic_graph
import graph_canvas.presentation.desktop.models.node as m_node
import graph_canvas.presentation.desktop.models.edge as m_edge


def analyze_direction_properties(graph: m_basic_graph.BasicGraph) -> Dict[str, Any]:
    """
    Analyze graph direction properties.
    Returns dict with:
    - is_directed: True if all edges are directed
    - is_undirected: True if all edges are undirected
    - is_mixed: True if graph has both directed and undirected edges
    - directed_edges: List of directed edges
    - undirected_edges: List of undirected edges
    - direction_ratio: Ratio of directed to total edges
    - bidirectional_pairs: List of node pairs with edges in both directions
    """

    directed_edges = []
    undirected_edges = []
    bidirectional_pairs = []
    edge_pairs = defaultdict(list)  # (source, target) -> [edges]
    
    # Analyze each edge
    for edge in graph.get_all_edges():
        if edge.directed:
            directed_edges.append(edge)
            # Track edge for bidirectional analysis
            edge_pairs[(edge.source_id, edge.target_id)].append(edge)
        else:
            undirected_edges.append(edge)
    
    # Find bidirectional pairs
    for (source, target), edges in edge_pairs.items():
        reverse_edges = edge_pairs.get((target, source), [])
        if reverse_edges:
            # Found edges in both directions
            pair = {
                'node1': graph.get_node(source),
                'node2': graph.get_node(target),
                'forward_edges': edges,
                'reverse_edges': reverse_edges
            }
            bidirectional_pairs.append(pair)
    
    total_edges = len(graph.get_all_edges())
    direction_ratio = len(directed_edges) / total_edges if total_edges > 0 else 0
    
    return {
        'is_directed': len(directed_edges) == total_edges,
        'is_undirected': len(undirected_edges) == total_edges,
        'is_mixed': len(directed_edges) > 0 and len(undirected_edges) > 0,
        'directed_edges': directed_edges,
        'undirected_edges': undirected_edges,
        'direction_ratio': direction_ratio,
        'bidirectional_pairs': bidirectional_pairs,
        'stats': {
            'total_edges': total_edges,
            'directed_count': len(directed_edges),
            'undirected_count': len(undirected_edges),
            'bidirectional_count': len(bidirectional_pairs)
        }
    }


def find_direction_violations(graph: m_basic_graph.BasicGraph, expected_type: str) -> List[Dict[str, Any]]:
    """
    Find edges that violate expected graph direction type.
    
    Args:
        graph: The graph to analyze
        expected_type: One of 'directed', 'undirected', or 'mixed'
    
    Returns:
        List of violations, each containing:
        - edge: The violating edge
        - reason: Description of the violation
        - fix_suggestion: Suggested fix for the violation
    """

    violations = []
    
    if expected_type == 'directed':
        # Check for undirected edges
        for edge in graph.get_all_edges():
            if not edge.directed:
                violations.append({
                    'edge': edge,
                    'reason': 'Undirected edge in directed graph',
                    'fix_suggestion': 'Convert to directed edge'
                })
                
        # Check for bidirectional edges (might be unintended)
        edge_pairs = defaultdict(list)
        for edge in graph.get_all_edges():
            if edge.directed:
                edge_pairs[(edge.source_id, edge.target_id)].append(edge)
        
        for (source, target), edges in edge_pairs.items():
            reverse_edges = edge_pairs.get((target, source), [])
            if reverse_edges:
                violations.append({
                    'edges': edges + reverse_edges,
                    'reason': 'Bidirectional edges (might be unintended)',
                    'fix_suggestion': 'Consider using single undirected edge'
                })
    
    elif expected_type == 'undirected':
        # Check for directed edges
        for edge in graph.get_all_edges():
            if edge.directed:
                violations.append({
                    'edge': edge,
                    'reason': 'Directed edge in undirected graph',
                    'fix_suggestion': 'Convert to undirected edge'
                })
    
    elif expected_type == 'mixed':
        # Check for consistency in edge types between same nodes
        edge_types = {}  # (node1, node2) -> edge_type
        for edge in graph.get_all_edges():
            nodes = tuple(sorted([edge.source_id, edge.target_id]))
            edge_type = 'directed' if edge.directed else 'undirected'
            
            if nodes in edge_types:
                if edge_types[nodes] != edge_type:
                    violations.append({
                        'edge': edge,
                        'reason': 'Inconsistent edge types between same nodes',
                        'fix_suggestion': f'Make all edges between these nodes {edge_types[nodes]}'
                    })
            else:
                edge_types[nodes] = edge_type
    
    return violations


def convert_graph_direction(graph: m_basic_graph.BasicGraph, target_type: str) -> Dict[str, Any]:
    """
    Convert graph to specified direction type.
    
    Args:
        graph: The graph to convert
        target_type: One of 'directed', 'undirected', or 'mixed'
    
    Returns:
        Dict with:
        - changes: List of changes made
        - stats: Statistics about the conversion
    """

    changes = []
    stats = {
        'edges_converted': 0,
        'edges_removed': 0,
        'edges_added': 0
    }
    
    if target_type == 'directed':
        # Convert all edges to directed
        for edge in graph.get_all_edges():
            if not edge.directed:
                edge.directed = True
                changes.append({
                    'type': 'convert',
                    'edge': edge,
                    'from': 'undirected',
                    'to': 'directed'
                })
                stats['edges_converted'] += 1
    
    elif target_type == 'undirected':
        # Convert all edges to undirected
        processed_pairs = set()
        edges_to_remove = []
        
        for edge in graph.get_all_edges():
            nodes = tuple(sorted([edge.source_id, edge.target_id]))
            
            if nodes not in processed_pairs:
                # First edge between these nodes
                edge.directed = False
                processed_pairs.add(nodes)
                changes.append({
                    'type': 'convert',
                    'edge': edge,
                    'from': 'directed' if edge.directed else 'undirected',
                    'to': 'undirected'
                })
                stats['edges_converted'] += 1
            else:
                # Additional edge between same nodes - mark for removal
                edges_to_remove.append(edge)
        
        # Remove redundant edges
        for edge in edges_to_remove:
            graph.remove_edge(edge.id)
            changes.append({
                'type': 'remove',
                'edge': edge,
                'reason': 'redundant after undirected conversion'
            })
            stats['edges_removed'] += 1
    
    elif target_type == 'mixed':
        # Convert based on edge patterns
        edge_patterns = defaultdict(list)  # (node1, node2) -> [edges]
        
        # Group edges by node pairs
        for edge in graph.get_all_edges():
            nodes = tuple(sorted([edge.source_id, edge.target_id]))
            edge_patterns[nodes].append(edge)
        
        # Analyze and convert each pattern
        for nodes, edges in edge_patterns.items():
            if len(edges) == 2:
                # Two edges between same nodes - check for bidirectional
                edge1, edge2 = edges
                if (edge1.source_id == edge2.target_id and
                    edge1.target_id == edge2.source_id):
                    # Convert bidirectional edges to single undirected edge
                    edge1.directed = False
                    graph.remove_edge(edge2.id)
                    changes.append({
                        'type': 'convert',
                        'edge': edge1,
                        'from': 'bidirectional',
                        'to': 'undirected'
                    })
                    changes.append({
                        'type': 'remove',
                        'edge': edge2,
                        'reason': 'redundant after bidirectional conversion'
                    })
                    stats['edges_converted'] += 1
                    stats['edges_removed'] += 1
    
    return {
        'changes': changes,
        'stats': stats
    }


# Check if graph contains cycles
def is_cyclic(graph: m_basic_graph.BasicGraph) -> Tuple[bool, Optional[List[m_node.Node]]]:
    """
    Check if graph contains cycles.
    Returns (has_cycle, cycle_nodes) where cycle_nodes is None if no cycle exists.
    """

    visited = set()
    rec_stack = set()
    cycle = []
    
    def dfs(node_id: str) -> bool:
        visited.add(node_id)
        rec_stack.add(node_id)
        
        for edge in graph.get_edges_from_node(node_id):
            if edge.target_id not in visited:
                if dfs(edge.target_id):
                    cycle.append(graph.get_node(node_id))
                    return True
            elif edge.target_id in rec_stack:
                cycle.append(graph.get_node(node_id))
                return True
        
        rec_stack.remove(node_id)
        return False
    
    for node in graph.get_all_nodes():
        if node.id not in visited:
            if dfs(node.id):
                return True, list(reversed(cycle))
    
    return False, None


# Analyze graph connectivity properties (connected (path between all nodes), strongly connected (path between all nodes), weakly connected (path between all nodes ignoring edge directions))
def analyze_connectivity(graph: m_basic_graph.BasicGraph) -> Dict[str, bool]:
    """
    Analyze graph connectivity properties.
    Returns dict with keys: 'connected', 'strongly_connected', 'weakly_connected'.
    """

    def bfs_reach(start_id: str, edges_func) -> Set[str]:
        """Get all nodes reachable from start using given edge function."""

        reached = {start_id}
        queue = deque([start_id])
        
        while queue:
            node_id = queue.popleft()
            for edge in edges_func(node_id):
                next_id = edge.target_id
                if next_id not in reached:
                    reached.add(next_id)
                    queue.append(next_id)
        
        return reached
    
    def is_connected() -> bool:
        """Check if graph is connected (ignoring edge directions)."""

        if not graph.get_all_nodes():
            return True
        
        start = next(iter(graph.get_all_nodes())).id
        
        def get_all_edges(node_id: str):
            return (graph.get_edges_from_node(node_id) +
                   graph.get_edges_to_node(node_id))
        
        reached = bfs_reach(start, get_all_edges)
        return len(reached) == len(graph.get_all_nodes())
    
    def is_strongly_connected() -> bool:
        """Check if graph is strongly connected."""

        if not graph.get_all_nodes():
            return True
        
        start = next(iter(graph.get_all_nodes())).id
        
        # Check forward reachability
        forward = bfs_reach(start, graph.get_edges_from_node)
        if len(forward) != len(graph.get_all_nodes()):
            return False
        
        # Check backward reachability
        backward = bfs_reach(start, graph.get_edges_to_node)
        return len(backward) == len(graph.get_all_nodes())
    
    return {
        'connected': is_connected(),
        'strongly_connected': is_strongly_connected(),
        'weakly_connected': is_connected()  # By definition
    }


def analyze_graph_type(graph: m_basic_graph.BasicGraph) -> Dict[str, bool]:
    """
    Analyze if graph is simple, multigraph, or pseudograph.
    Returns dict with keys: 'simple', 'multigraph', 'pseudograph'.
    """

    has_self_loops = False
    has_multiple_edges = False
    edge_counts = defaultdict(int)
    
    for edge in graph.get_all_edges():
        # Check for self-loops
        if edge.source_id == edge.target_id:
            has_self_loops = True
        
        # Count edges between each pair of nodes
        if graph.is_directed:
            key = (edge.source_id, edge.target_id)
        else:
            key = tuple(sorted([edge.source_id, edge.target_id]))
        
        edge_counts[key] += 1
        if edge_counts[key] > 1:
            has_multiple_edges = True
    
    return {
        'simple': not (has_self_loops or has_multiple_edges),
        'multigraph': has_multiple_edges and not has_self_loops,
        'pseudograph': has_self_loops or has_multiple_edges
    }


def analyze_density(graph: m_basic_graph.BasicGraph) -> Dict[str, Any]:
    """
    Analyze graph density properties.
    Returns dict with keys: 'density', 'is_sparse', 'is_dense', 'edge_count',
    'max_possible_edges'.
    """

    V = len(graph.get_all_nodes())
    E = len(graph.get_all_edges())
    
    # Maximum possible edges
    if graph.is_directed:
        max_edges = V * (V - 1)  # n(n-1) for directed
    else:
        max_edges = (V * (V - 1)) // 2  # n(n-1)/2 for undirected
    
    # Calculate density
    density = E / max_edges if max_edges > 0 else 0
    
    # Classify sparsity
    # Using common thresholds: sparse if E = O(V), dense if E = Ω(V²)
    is_sparse = E < 2 * V  # Less than 2|V| edges
    is_dense = density > 0.5  # More than half of possible edges
    
    return {
        'density': density,
        'is_sparse': is_sparse,
        'is_dense': is_dense,
        'edge_count': E,
        'max_possible_edges': max_edges
    }


# Check if graph is planar using Kuratowski's theorem
def is_planar(graph: m_basic_graph.BasicGraph) -> Tuple[bool, Optional[List[m_node.Node]]]:
    """
    Check if graph is planar using Kuratowski's theorem.
    Returns (is_planar, subgraph) where subgraph is K5 or K3,3 if not planar.
    """

    def find_k5_subgraph() -> Optional[List[m_node.Node]]:
        """Find K5 subgraph (complete graph on 5 vertices)."""

        nodes = list(graph.get_all_nodes())
        n = len(nodes)
        
        # Try all possible sets of 5 vertices
        for i1 in range(n):
            for i2 in range(i1 + 1, n):
                for i3 in range(i2 + 1, n):
                    for i4 in range(i3 + 1, n):
                        for i5 in range(i4 + 1, n):
                            vertices = [nodes[i] for i in [i1, i2, i3, i4, i5]]
                            
                            # Check if all pairs are connected
                            is_k5 = True
                            for j1 in range(5):
                                for j2 in range(j1 + 1, 5):
                                    v1, v2 = vertices[j1], vertices[j2]
                                    if not graph.get_edge_between(v1.id, v2.id):
                                        is_k5 = False
                                        break
                                if not is_k5:
                                    break
                            
                            if is_k5:
                                return vertices
        return None
    
    def find_k33_subgraph() -> Optional[List[m_node.Node]]:
        """Find K3,3 subgraph (complete bipartite graph on 3+3 vertices)."""

        nodes = list(graph.get_all_nodes())
        n = len(nodes)
        
        # Try all possible partitions of 3+3 vertices
        for i1 in range(n):
            for i2 in range(i1 + 1, n):
                for i3 in range(i2 + 1, n):
                    for j1 in range(n):
                        if j1 in [i1, i2, i3]:
                            continue
                        for j2 in range(j1 + 1, n):
                            if j2 in [i1, i2, i3]:
                                continue
                            for j3 in range(j2 + 1, n):
                                if j3 in [i1, i2, i3]:
                                    continue
                                
                                part1 = [nodes[i] for i in [i1, i2, i3]]
                                part2 = [nodes[i] for i in [j1, j2, j3]]
                                
                                # Check if all pairs between partitions are connected
                                is_k33 = True
                                for v1 in part1:
                                    for v2 in part2:
                                        if not graph.get_edge_between(v1.id, v2.id):
                                            is_k33 = False
                                            break
                                    if not is_k33:
                                        break
                                
                                if is_k33:
                                    return part1 + part2
        return None
    
    # Check for K5 subgraph
    k5 = find_k5_subgraph()
    if k5:
        return False, k5
    
    # Check for K3,3 subgraph
    k33 = find_k33_subgraph()
    if k33:
        return False, k33
    
    return True, None


# Find Eulerian path: a path that visits every edge exactly once
def find_eulerian_path(graph: m_basic_graph.BasicGraph) -> Optional[List[m_edge.Edge]]:
    """
    Find Eulerian path in graph if one exists.
    Returns list of edges forming path, or None if no path exists.
    """

    def count_degrees():
        """Count in/out degrees of all vertices."""

        in_degree = defaultdict(int)
        out_degree = defaultdict(int)
        
        for edge in graph.get_all_edges():
            out_degree[edge.source_id] += 1
            in_degree[edge.target_id] += 1
        
        return in_degree, out_degree
    
    def find_start_vertex(in_degree, out_degree):
        """Find valid starting vertex for Eulerian path."""

        start = None
        for node in graph.get_all_nodes():
            diff = out_degree[node.id] - in_degree[node.id]
            if diff > 1:
                return None  # Invalid degrees
            if diff == 1:
                if start is not None:
                    return None  # Multiple start vertices
                start = node.id
        
        if start is None:
            # If no start vertex found, use any vertex with outgoing edges
            for node in graph.get_all_nodes():
                if out_degree[node.id] > 0:
                    start = node.id
                    break
        
        return start
    
    # Count degrees
    in_degree, out_degree = count_degrees()
    
    # Find start vertex
    start = find_start_vertex(in_degree, out_degree)
    if start is None:
        return None
    
    # Create copy of graph for edge removal
    remaining_edges = {edge.id: edge for edge in graph.get_all_edges()}
    
    # Find path using Hierholzer's algorithm
    path = []
    stack = [start]
    
    while stack:
        current = stack[-1]
        
        # Find unused edge from current vertex
        next_edge = None
        for edge in graph.get_edges_from_node(current):
            if edge.id in remaining_edges:
                next_edge = edge
                break
        
        if next_edge:
            stack.append(next_edge.target_id)
            path.append(next_edge)
            del remaining_edges[next_edge.id]
        else:
            stack.pop()
    
    # Check if all edges were used
    if remaining_edges:
        return None
    
    return path


# Find Eulerian circuit: a path that visits every edge exactly once and returns to start
def find_eulerian_circuit(graph: m_basic_graph.BasicGraph) -> Optional[List[m_edge.Edge]]:
    """
    Find Eulerian circuit in graph if one exists.
    Returns list of edges forming circuit, or None if no circuit exists.
    """

    def check_degrees():
        """Check if all vertices have equal in and out degrees."""
        in_degree = defaultdict(int)
        out_degree = defaultdict(int)
        
        for edge in graph.get_all_edges():
            out_degree[edge.source_id] += 1
            in_degree[edge.target_id] += 1
        
        # For Eulerian circuit, all vertices must have equal in/out degrees
        for node in graph.get_all_nodes():
            if in_degree[node.id] != out_degree[node.id]:
                return False
            if in_degree[node.id] == 0 and out_degree[node.id] == 0:
                continue  # Skip isolated vertices
            if in_degree[node.id] == 0:
                return False
        return True
    
    # First check degree conditions
    if not check_degrees():
        return None
    
    # Create copy of graph for edge removal
    remaining_edges = {edge.id: edge for edge in graph.get_all_edges()}
    
    # Start from any vertex with outgoing edges
    start = None
    for node in graph.get_all_nodes():
        if graph.get_edges_from_node(node.id):
            start = node.id
            break
    
    if start is None:
        return None if graph.get_all_edges() else []  # Empty list for empty graph
    
    # Find circuit using Hierholzer's algorithm
    circuit = []
    stack = [start]
    
    while stack:
        current = stack[-1]
        
        # Find unused edge from current vertex
        next_edge = None
        for edge in graph.get_edges_from_node(current):
            if edge.id in remaining_edges:
                next_edge = edge
                break
        
        if next_edge:
            stack.append(next_edge.target_id)
            circuit.append(next_edge)
            del remaining_edges[next_edge.id]
        else:
            stack.pop()
    
    # Check if all edges were used and circuit is closed
    if remaining_edges or circuit[0].source_id != circuit[-1].target_id:
        return None
    
    return circuit


# Find Hamiltonian path: a path that visits every node exactly once
def find_hamiltonian_path(graph: m_basic_graph.BasicGraph) -> Optional[List[m_node.Node]]:
    """
    Find Hamiltonian path in graph if one exists.
    Returns list of nodes forming path, or None if no path exists.
    Uses backtracking with branch and bound optimization.
    """

    def is_valid_next(path: List[str], next_id: str) -> bool:
        """Check if vertex can be added to path."""

        if next_id in path:
            return False
        
        if not path:
            return True
        
        return bool(graph.get_edge_between(path[-1], next_id))
    
    def find_path_recursive(path: List[str], remaining: Set[str]) -> Optional[List[str]]:
        """Recursively find Hamiltonian path."""

        if not remaining:
            return path
        
        current = path[-1] if path else None
        
        # Try each remaining vertex
        for next_id in remaining:
            if current is None or is_valid_next(path, next_id):
                new_remaining = remaining - {next_id}
                result = find_path_recursive(path + [next_id], new_remaining)
                if result:
                    return result
        
        return None
    
    # Try each vertex as starting point
    nodes = list(graph.get_all_nodes())
    remaining = set(node.id for node in nodes)
    
    for start in nodes:
        path = find_path_recursive([start.id], remaining - {start.id})
        if path:
            return [graph.get_node(node_id) for node_id in path]
    
    return None


# Find Hamiltonian circuit: a circuit that visits every node exactly once
def find_hamiltonian_circuit(graph: m_basic_graph.BasicGraph) -> Optional[List[m_node.Node]]:
    """
    Find Hamiltonian circuit in graph if one exists.
    Returns list of nodes forming circuit, or None if no circuit exists.
    """

    path = find_hamiltonian_path(graph)
    if not path:
        return None
    
    # Check if last vertex can connect back to first
    if not graph.get_edge_between(path[-1].id, path[0].id):
        return None
    
    return path + [path[0]]  # Add first vertex again to close circuit


def analyze_euler_hamilton_properties(graph: m_basic_graph.BasicGraph) -> Dict[str, Any]:
    """
    Analyze Eulerian and Hamiltonian properties of graph.
    Returns dict with keys: 'has_eulerian_path', 'has_eulerian_circuit',
    'has_hamiltonian_path', 'has_hamiltonian_circuit', plus the actual paths/circuits
    if they exist.
    """

    # Check Eulerian properties
    eulerian_path = find_eulerian_path(graph)
    
    # For Eulerian circuit, check if path starts and ends at same vertex
    eulerian_circuit = None
    if eulerian_path:
        if eulerian_path[0].source_id == eulerian_path[-1].target_id:
            eulerian_circuit = eulerian_path
    
    # Check Hamiltonian properties
    hamiltonian_path = find_hamiltonian_path(graph)
    hamiltonian_circuit = find_hamiltonian_circuit(graph)
    
    return {
        'has_eulerian_path': bool(eulerian_path),
        'eulerian_path': eulerian_path,
        'has_eulerian_circuit': bool(eulerian_circuit),
        'eulerian_circuit': eulerian_circuit,
        'has_hamiltonian_path': bool(hamiltonian_path),
        'hamiltonian_path': hamiltonian_path,
        'has_hamiltonian_circuit': bool(hamiltonian_circuit),
        'hamiltonian_circuit': hamiltonian_circuit
    }
