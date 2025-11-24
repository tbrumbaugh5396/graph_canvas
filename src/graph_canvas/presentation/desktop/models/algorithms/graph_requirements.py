"""
Algorithms for checking complex graph requirements.
"""

from typing import List, Set, Dict, Optional, Any, Tuple
from collections import defaultdict, deque

import graph_canvas.presentation.desktop.models.basic_graph as m_basic_graph
import graph_canvas.presentation.desktop.models.node as m_node
import graph_canvas.presentation.desktop.models.edge as m_edge


def has_euler_path(graph: m_basic_graph.BasicGraph) -> Tuple[bool, Optional[str]]:
    """
    Check if graph has an Euler path.
    Returns (has_path, reason) where reason is None if has_path is True.
    
    A graph has an Euler path if:
    - For undirected graphs: Either all vertices have even degree, or exactly two vertices have odd degree
    - For directed graphs: Either all vertices have equal in/out degrees, or exactly one vertex has out-degree = in-degree + 1
      and exactly one vertex has in-degree = out-degree + 1
    """
    if graph.is_directed:
        # Check in/out degrees
        in_degrees = defaultdict(int)
        out_degrees = defaultdict(int)
        for edge in graph.get_all_edges():
            out_degrees[edge.source_id] += 1
            in_degrees[edge.target_id] += 1
        
        # Count vertices with unequal in/out degrees
        diff_vertices = []
        for node_id in graph.get_all_nodes():
            in_deg = in_degrees[node_id]
            out_deg = out_degrees[node_id]
            if in_deg != out_deg:
                diff_vertices.append((node_id, in_deg, out_deg))
        
        if len(diff_vertices) == 0:
            return True, None
        elif len(diff_vertices) == 2:
            v1, in1, out1 = diff_vertices[0]
            v2, in2, out2 = diff_vertices[1]
            if (out1 == in1 + 1 and in2 == out2 + 1) or (in1 == out1 + 1 and out2 == in2 + 1):
                return True, None
        return False, f"Graph does not satisfy Euler path conditions for directed graphs"
    
    else:
        # Count vertices with odd degree
        odd_vertices = []
        for node_id in graph.get_all_nodes():
            degree = len(graph.get_edges_from_node(node_id)) + len(graph.get_edges_to_node(node_id))
            if degree % 2 == 1:
                odd_vertices.append(node_id)
        
        if len(odd_vertices) == 0:
            return True, None
        elif len(odd_vertices) == 2:
            return True, None
        return False, f"Graph has {len(odd_vertices)} vertices with odd degree, must be 0 or 2"


def has_euler_circuit(graph: m_basic_graph.BasicGraph) -> Tuple[bool, Optional[str]]:
    """
    Check if graph has an Euler circuit.
    Returns (has_circuit, reason) where reason is None if has_circuit is True.
    
    A graph has an Euler circuit if:
    - For undirected graphs: All vertices have even degree
    - For directed graphs: All vertices have equal in/out degrees
    """
    if graph.is_directed:
        # Check in/out degrees
        in_degrees = defaultdict(int)
        out_degrees = defaultdict(int)
        for edge in graph.get_all_edges():
            out_degrees[edge.source_id] += 1
            in_degrees[edge.target_id] += 1
        
        # All vertices must have equal in/out degrees
        for node_id in graph.get_all_nodes():
            in_deg = in_degrees[node_id]
            out_deg = out_degrees[node_id]
            if in_deg != out_deg:
                return False, f"Vertex {node_id} has unequal in-degree ({in_deg}) and out-degree ({out_deg})"
        return True, None
    
    else:
        # All vertices must have even degree
        for node_id in graph.get_all_nodes():
            degree = len(graph.get_edges_from_node(node_id)) + len(graph.get_edges_to_node(node_id))
            if degree % 2 == 1:
                return False, f"Vertex {node_id} has odd degree ({degree})"
        return True, None


def _try_hamilton_path(graph: m_basic_graph.BasicGraph, start_id: str, visited: Set[str], path: List[str]) -> bool:
    """Helper function for Hamilton path check using backtracking."""
    if len(path) == len(graph.get_all_nodes()):
        return True
    
    for edge in graph.get_edges_from_node(path[-1]):
        next_id = edge.target_id
        if next_id not in visited:
            visited.add(next_id)
            path.append(next_id)
            if _try_hamilton_path(graph, start_id, visited, path):
                return True
            visited.remove(next_id)
            path.pop()
    return False


def has_hamilton_path(graph: m_basic_graph.BasicGraph) -> Tuple[bool, Optional[str]]:
    """
    Check if graph has a Hamilton path.
    Returns (has_path, reason) where reason is None if has_path is True.
    
    Uses backtracking to try all possible paths.
    Warning: This is NP-hard and may be slow for large graphs.
    """
    if not graph.get_all_nodes():
        return True, None
    
    # Try starting from each vertex
    for start_id in graph.get_all_nodes():
        visited = {start_id}
        path = [start_id]
        if _try_hamilton_path(graph, start_id, visited, path):
            return True, None
    
    return False, "No Hamilton path found"


def has_hamilton_cycle(graph: m_basic_graph.BasicGraph) -> Tuple[bool, Optional[str]]:
    """
    Check if graph has a Hamilton cycle.
    Returns (has_cycle, reason) where reason is None if has_cycle is True.
    
    Uses backtracking to try all possible cycles.
    Warning: This is NP-hard and may be slow for large graphs.
    """
    if not graph.get_all_nodes():
        return True, None
    
    def try_complete_cycle(start_id: str, current_id: str, visited: Set[str], path: List[str]) -> bool:
        if len(path) == len(graph.get_all_nodes()):
            # Check if we can get back to start
            for edge in graph.get_edges_from_node(current_id):
                if edge.target_id == start_id:
                    return True
            return False
        
        for edge in graph.get_edges_from_node(current_id):
            next_id = edge.target_id
            if next_id not in visited:
                visited.add(next_id)
                path.append(next_id)
                if try_complete_cycle(start_id, next_id, visited, path):
                    return True
                visited.remove(next_id)
                path.pop()
        return False
    
    # Try starting from each vertex
    for start_id in graph.get_all_nodes():
        visited = {start_id}
        path = [start_id]
        if try_complete_cycle(start_id, start_id, visited, path):
            return True, None
    
    return False, "No Hamilton cycle found"


def is_binary_tree(graph: m_basic_graph.BasicGraph) -> Tuple[bool, Optional[str]]:
    """
    Check if graph is a binary tree.
    Returns (is_binary, reason) where reason is None if is_binary is True.
    
    A binary tree:
    - Is a tree (connected, acyclic)
    - Each node has at most 2 children
    """
    if not graph.get_all_nodes():
        return True, None
    
    # Find root (node with no incoming edges)
    roots = []
    for node_id in graph.get_all_nodes():
        if not graph.get_edges_to_node(node_id):
            roots.append(node_id)
    
    if len(roots) != 1:
        return False, f"Found {len(roots)} roots, binary tree must have exactly one root"
    
    root_id = roots[0]
    visited = {root_id}
    queue = deque([root_id])
    
    while queue:
        node_id = queue.popleft()
        children = graph.get_edges_from_node(node_id)
        
        if len(children) > 2:
            return False, f"Node {node_id} has {len(children)} children, maximum is 2"
        
        for edge in children:
            child_id = edge.target_id
            if child_id in visited:
                return False, f"Found cycle involving node {child_id}"
            visited.add(child_id)
            queue.append(child_id)
    
    if len(visited) != len(graph.get_all_nodes()):
        return False, "Graph is not connected"
    
    return True, None


def is_full_binary_tree(graph: m_basic_graph.BasicGraph) -> Tuple[bool, Optional[str]]:
    """
    Check if graph is a full binary tree.
    Returns (is_full, reason) where reason is None if is_full is True.
    
    A full binary tree:
    - Is a binary tree
    - Each node has either 0 or 2 children
    """
    is_binary, reason = is_binary_tree(graph)
    if not is_binary:
        return False, reason
    
    # Check each non-leaf node has exactly 2 children
    for node_id in graph.get_all_nodes():
        children = graph.get_edges_from_node(node_id)
        if children and len(children) != 2:
            return False, f"Node {node_id} has {len(children)} children, must be 0 or 2"
    
    return True, None


def _tree_height(graph: m_basic_graph.BasicGraph, node_id: str, heights: Dict[str, int]) -> int:
    """Helper function to compute height of each node in a tree."""
    if node_id in heights:
        return heights[node_id]
    
    children = graph.get_edges_from_node(node_id)
    if not children:
        heights[node_id] = 0
        return 0
    
    child_heights = [_tree_height(graph, edge.target_id, heights) for edge in children]
    heights[node_id] = 1 + max(child_heights)
    return heights[node_id]


def is_perfect_binary_tree(graph: m_basic_graph.BasicGraph) -> Tuple[bool, Optional[str]]:
    """
    Check if graph is a perfect binary tree.
    Returns (is_perfect, reason) where reason is None if is_perfect is True.
    
    A perfect binary tree:
    - Is a full binary tree
    - All leaves are at the same level
    """
    is_full, reason = is_full_binary_tree(graph)
    if not is_full:
        return False, reason
    
    if not graph.get_all_nodes():
        return True, None
    
    # Find root
    root_id = next(node_id for node_id in graph.get_all_nodes() 
                   if not graph.get_edges_to_node(node_id))
    
    # Compute heights
    heights = {}
    _tree_height(graph, root_id, heights)
    
    # Check all leaves are at same level
    leaf_heights = set()
    for node_id in graph.get_all_nodes():
        if not graph.get_edges_from_node(node_id):  # Is leaf
            leaf_heights.add(heights[node_id])
    
    if len(leaf_heights) > 1:
        return False, f"Leaves found at different heights: {leaf_heights}"
    
    return True, None


def is_complete_binary_tree(graph: m_basic_graph.BasicGraph) -> Tuple[bool, Optional[str]]:
    """
    Check if graph is a complete binary tree.
    Returns (is_complete, reason) where reason is None if is_complete is True.
    
    A complete binary tree:
    - Is a binary tree
    - All levels except possibly the last are completely filled
    - All nodes are as far left as possible
    """
    is_binary, reason = is_binary_tree(graph)
    if not is_binary:
        return False, reason
    
    if not graph.get_all_nodes():
        return True, None
    
    # Find root
    root_id = next(node_id for node_id in graph.get_all_nodes() 
                   if not graph.get_edges_to_node(node_id))
    
    # Do level-order traversal
    queue = deque([(root_id, 0)])  # (node_id, level)
    levels = defaultdict(list)
    
    while queue:
        node_id, level = queue.popleft()
        levels[level].append(node_id)
        
        children = graph.get_edges_from_node(node_id)
        for i, edge in enumerate(children):
            queue.append((edge.target_id, level + 1))
    
    # Check each level except last is full
    max_level = max(levels.keys())
    for level in range(max_level):
        expected_nodes = 2 ** level
        if len(levels[level]) != expected_nodes:
            return False, f"Level {level} has {len(levels[level])} nodes, expected {expected_nodes}"
    
    # Check last level is filled from left to right
    last_level_nodes = levels[max_level]
    max_last_nodes = 2 ** max_level
    if not (0 < len(last_level_nodes) <= max_last_nodes):
        return False, f"Last level has {len(last_level_nodes)} nodes, must be between 1 and {max_last_nodes}"
    
    return True, None


def is_balanced_tree(graph: m_basic_graph.BasicGraph) -> Tuple[bool, Optional[str]]:
    """
    Check if graph is a balanced binary tree.
    Returns (is_balanced, reason) where reason is None if is_balanced is True.
    
    A balanced binary tree:
    - Is a binary tree
    - The heights of the left and right subtrees of every node differ by at most one
    """
    is_binary, reason = is_binary_tree(graph)
    if not is_binary:
        return False, reason
    
    if not graph.get_all_nodes():
        return True, None
    
    # Find root
    root_id = next(node_id for node_id in graph.get_all_nodes() 
                   if not graph.get_edges_to_node(node_id))
    
    def check_balance(node_id: str) -> Tuple[bool, int]:
        """Returns (is_balanced, height)."""
        children = graph.get_edges_from_node(node_id)
        if not children:
            return True, 0
        
        # Get heights of children
        heights = []
        for edge in children:
            is_child_balanced, height = check_balance(edge.target_id)
            if not is_child_balanced:
                return False, 0
            heights.append(height)
        
        # Add missing heights for nodes with < 2 children
        while len(heights) < 2:
            heights.append(-1)
        
        # Check balance
        if abs(heights[0] - heights[1]) > 1:
            return False, 0
        
        return True, 1 + max(heights)
    
    is_balanced, _ = check_balance(root_id)
    if not is_balanced:
        return False, "Found unbalanced subtrees"
    
    return True, None


def is_flow_network(graph: m_basic_graph.BasicGraph) -> Tuple[bool, Optional[str]]:
    """
    Check if graph is a valid flow network.
    Returns (is_valid, reason) where reason is None if is_valid is True.
    
    A flow network:
    - Is directed
    - Has a single source (no incoming edges)
    - Has a single sink (no outgoing edges)
    - Has no self-loops
    - Has no negative weights/capacities
    """
    if not graph.is_directed:
        return False, "Flow network must be directed"
    
    # Find source and sink
    sources = []
    sinks = []
    for node_id in graph.get_all_nodes():
        in_edges = graph.get_edges_to_node(node_id)
        out_edges = graph.get_edges_from_node(node_id)
        
        if not in_edges:
            sources.append(node_id)
        if not out_edges:
            sinks.append(node_id)
    
    if len(sources) != 1:
        return False, f"Found {len(sources)} sources, must have exactly one"
    if len(sinks) != 1:
        return False, f"Found {len(sinks)} sinks, must have exactly one"
    
    # Check for self-loops and negative weights
    for edge in graph.get_edges():
        if edge.source_id == edge.target_id:
            return False, f"Found self-loop at node {edge.source_id}"
        
        weight = edge.metadata.get("weight", 0)
        if isinstance(weight, (int, float)) and weight < 0:
            return False, f"Edge {edge.id} has negative weight {weight}"
        
        capacity = edge.metadata.get("capacity", 0)
        if isinstance(capacity, (int, float)) and capacity < 0:
            return False, f"Edge {edge.id} has negative capacity {capacity}"
    
    return True, None
