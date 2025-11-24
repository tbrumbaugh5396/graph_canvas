"""
Algorithms for directed acyclic graphs (DAGs).
"""


from typing import List, Set, Dict, Optional, Any, Tuple
from collections import defaultdict, deque

import graph_canvas.presentation.desktop.models.dag_graph as m_dag_graph
import graph_canvas.presentation.desktop.models.node as m_node
import graph_canvas.presentation.desktop.models.edge as m_edge


# Check if graph is actually a DAG (no cycles)
def is_dag(graph: m_dag_graph.DAGGraph) -> bool:
    """Check if graph is actually a DAG (no cycles)."""

    try:
        topological_sort_kahn(graph)
        return True
    except ValueError:
        return False


def topological_sort_kahn(graph: m_dag_graph.DAGGraph) -> List[m_node.Node]:
    """Perform topological sort using Kahn's algorithm."""

    # Calculate in-degree for each node
    in_degree = defaultdict(int)
    for edge in graph.get_all_edges():
        in_degree[edge.target_id] += 1
    
    # Initialize queue with nodes having no incoming edges
    queue = deque()
    for node in graph.get_all_nodes():
        if in_degree[node.id] == 0:
            queue.append(node)
    
    result = []
    while queue:
        node = queue.popleft()
        result.append(node)
        
        # Reduce in-degree of neighbors
        for edge in graph.get_edges_from_node(node.id):
            in_degree[edge.target_id] -= 1
            if in_degree[edge.target_id] == 0:
                queue.append(graph.get_node(edge.target_id))
    
    # Check for cycles
    if len(result) != len(graph.get_all_nodes()):
        raise ValueError("Graph contains a cycle")
    
    return result


def topological_sort_dfs(graph: m_dag_graph.DAGGraph) -> List[m_node.Node]:
    """Perform topological sort using depth-first search."""

    result = []
    visited = set()
    temp_mark = set()  # For cycle detection
    
    def visit(node_id: str) -> None:
        if node_id in temp_mark:
            raise ValueError("Graph contains a cycle")
        if node_id in visited:
            return
        
        temp_mark.add(node_id)
        for edge in graph.get_edges_from_node(node_id):
            visit(edge.target_id)
        temp_mark.remove(node_id)
        visited.add(node_id)
        result.insert(0, graph.get_node(node_id))
    
    for node in graph.get_all_nodes():
        if node.id not in visited:
            visit(node.id)
    
    return result


def detect_cycle(graph: m_dag_graph.DAGGraph) -> Optional[List[m_node.Node]]:
    """Detect a cycle in the graph if one exists."""

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
                return list(reversed(cycle))
    
    return None


def critical_path(graph: m_dag_graph.DAGGraph, weights: Dict[str, float]) -> Tuple[List[m_node.Node], float]:
    """Find the critical path in a weighted DAG."""

    # Initialize distances
    dist = {node.id: float('-inf') for node in graph.get_all_nodes()}
    prev = {node.id: None for node in graph.get_all_nodes()}
    
    # Find sources (nodes with no incoming edges)
    sources = []
    for node in graph.get_all_nodes():
        if not graph.get_edges_to_node(node.id):
            sources.append(node)
            dist[node.id] = weights.get(node.id, 0)
    
    # Process nodes in topological order
    for node in topological_sort_kahn(graph):
        # Update distances of neighbors
        for edge in graph.get_edges_from_node(node.id):
            new_dist = dist[node.id] + weights.get(edge.target_id, 0)
            if new_dist > dist[edge.target_id]:
                dist[edge.target_id] = new_dist
                prev[edge.target_id] = node.id
    
    # Find sink with maximum distance
    max_dist = float('-inf')
    max_sink = None
    for node in graph.get_all_nodes():
        if not graph.get_edges_from_node(node.id):
            if dist[node.id] > max_dist:
                max_dist = dist[node.id]
                max_sink = node.id
    
    # Reconstruct path
    path = []
    current = max_sink
    while current:
        path.append(graph.get_node(current))
        current = prev[current]
    
    return list(reversed(path)), max_dist


def shortest_paths_dag(graph: m_dag_graph.DAGGraph, source_id: str,
                      weights: Dict[str, float]) -> Dict[str, float]:
    """Find shortest paths from source in a weighted DAG."""

    # Initialize distances
    dist = {node.id: float('inf') for node in graph.get_all_nodes()}
    dist[source_id] = 0
    
    # Process nodes in topological order
    for node in topological_sort_kahn(graph):
        # Update distances of neighbors
        if dist[node.id] != float('inf'):
            for edge in graph.get_edges_from_node(node.id):
                new_dist = dist[node.id] + weights.get(edge.id, 0)
                if new_dist < dist[edge.target_id]:
                    dist[edge.target_id] = new_dist
    
    return dist


def transitive_closure(graph: m_dag_graph.DAGGraph) -> Dict[str, Set[str]]:
    """Compute the transitive closure of the DAG."""

    closure = {node.id: set() for node in graph.get_all_nodes()}
    
    # Initialize with direct edges
    for edge in graph.get_all_edges():
        closure[edge.source_id].add(edge.target_id)
    
    # Floyd-Warshall algorithm
    nodes = list(graph.get_all_nodes())
    for k in nodes:
        for i in nodes:
            for j in nodes:
                if k.id in closure[i.id] and j.id in closure[k.id]:
                    closure[i.id].add(j.id)
    
    return closure


def longest_path_dag(graph: m_dag_graph.DAGGraph, weights: Dict[str, float]) -> Dict[str, float]:
    """Find longest paths from each node in a weighted DAG."""

    # Initialize distances
    dist = {node.id: float('-inf') for node in graph.get_all_nodes()}
    
    # Process nodes in topological order
    for node in topological_sort_kahn(graph):
        # Base case for sources
        if not graph.get_edges_to_node(node.id):
            dist[node.id] = weights.get(node.id, 0)
        
        # Update distances of neighbors
        for edge in graph.get_edges_from_node(node.id):
            new_dist = dist[node.id] + weights.get(edge.target_id, 0)
            dist[edge.target_id] = max(dist[edge.target_id], new_dist)
    
    return dist


def minimum_height_dag(graph: m_dag_graph.DAGGraph) -> Dict[str, int]:
    """Compute minimum height of each node in DAG."""

    # Initialize heights
    height = {node.id: 0 for node in graph.get_all_nodes()}
    
    # Process nodes in reverse topological order
    for node in reversed(topological_sort_kahn(graph)):
        # Height is 1 + max height of children
        max_child_height = 0
        for edge in graph.get_edges_from_node(node.id):
            max_child_height = max(max_child_height, height[edge.target_id])
        height[node.id] = 1 + max_child_height
    
    return height


def count_paths(graph: m_dag_graph.DAGGraph, source_id: str, target_id: str) -> int:
    """Count number of different paths between two nodes in DAG."""

    count = {node.id: 0 for node in graph.get_all_nodes()}
    count[source_id] = 1
    
    # Process nodes in topological order
    for node in topological_sort_kahn(graph):
        # Add current count to all neighbors
        for edge in graph.get_edges_from_node(node.id):
            count[edge.target_id] += count[node.id]
    
    return count[target_id]


def layer_assignment(graph: m_dag_graph.DAGGraph) -> Dict[str, int]:
    """Assign nodes to layers for visualization."""

    # Use longest path from any source as layer number
    layers = {node.id: 0 for node in graph.get_all_nodes()}
    
    # Process nodes in topological order
    for node in topological_sort_kahn(graph):
        # Layer is 1 + max layer of parents
        max_parent_layer = -1
        for edge in graph.get_edges_to_node(node.id):
            max_parent_layer = max(max_parent_layer, layers[edge.source_id])
        layers[node.id] = max_parent_layer + 1
    
    return layers
