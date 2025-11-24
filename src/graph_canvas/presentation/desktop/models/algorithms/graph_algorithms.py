"""
Algorithms for general graphs (directed or undirected).
"""


from typing import List, Set, Dict, Optional, Any, Tuple, Callable
from collections import defaultdict, deque
import heapq

import graph_canvas.presentation.desktop.models.basic_graph as m_basic_graph
import graph_canvas.presentation.desktop.models.node as m_node
import graph_canvas.presentation.desktop.models.edge as m_edge


# Search Algorithms
def depth_first_search(graph: m_basic_graph.BasicGraph, start_id: str,
                      visit_func: Optional[Callable[[m_node.Node], None]] = None) -> List[m_node.Node]:
    """Perform depth-first search starting from a node."""

    visited = set()
    result = []
    
    def dfs(node_id: str) -> None:
        node = graph.get_node(node_id)
        if not node:
            return
        
        visited.add(node_id)
        result.append(node)
        if visit_func:
            visit_func(node)
        
        for edge in graph.get_edges_from_node(node_id):
            if edge.target_id not in visited:
                dfs(edge.target_id)
    
    dfs(start_id)
    return result


def breadth_first_search(graph: m_basic_graph.BasicGraph, start_id: str,
                        visit_func: Optional[Callable[[m_node.Node], None]] = None) -> List[m_node.Node]:
    """Perform breadth-first search starting from a node."""

    visited = {start_id}
    result = []
    queue = deque([start_id])
    
    while queue:
        node_id = queue.popleft()
        node = graph.get_node(node_id)
        if node:
            result.append(node)
            if visit_func:
                visit_func(node)
            
            for edge in graph.get_edges_from_node(node_id):
                if edge.target_id not in visited:
                    visited.add(edge.target_id)
                    queue.append(edge.target_id)
    
    return result


# Shortest Paths Trees (Dijkstra and Bellman-Ford (for negative weights))
def dijkstra_shortest_path_tree(graph: m_basic_graph.BasicGraph, start_id: str, goal_id: Optional[str] = None,
                          weights: Optional[Dict[str, float]] = None) -> Tuple[Dict[str, float], Dict[str, str], Optional[List[m_node.Node]]]:
    """
    Find shortest path trees using Dijkstra's algorithm.
    If not goal_id is provided, it will find the shortest spanning path to all nodes.
    
    Args:
        graph: The graph to search
        start_id: Starting node ID
        goal_id: Optional target node ID. If provided, stops when target is found
        weights: Edge weights. If None, uses weight 1 for all edges
    
    Returns:
        Tuple of:
        - distances: Dict mapping node IDs to shortest distances
        - previous: Dict mapping node IDs to previous node in shortest path
        - path: List of nodes in shortest path if goal_id provided, None otherwise
    """
    weights = weights or {}
    dist = {node.id: float('inf') for node in graph.get_all_nodes()}
    prev = {node.id: None for node in graph.get_all_nodes()}
    dist[start_id] = 0
    
    # Priority queue of (distance, node_id)
    pq = [(0, start_id)]
    visited = set()
    
    while pq:
        d, node_id = heapq.heappop(pq)
        if node_id in visited:
            continue
        
        visited.add(node_id)
        
        # If we found the goal, we can stop
        if goal_id and node_id == goal_id:
            break
        
        for edge in graph.get_edges_from_node(node_id):
            if edge.target_id not in visited:
                new_dist = dist[node_id] + weights.get(edge.id, 1)
                if new_dist < dist[edge.target_id]:
                    dist[edge.target_id] = new_dist
                    prev[edge.target_id] = node_id
                    heapq.heappush(pq, (new_dist, edge.target_id))
    
    # If goal was specified, reconstruct the path
    path = None
    if goal_id and goal_id in visited:
        path = []
        current = goal_id
        while current is not None:
            path.append(graph.get_node(current))
            current = prev[current]
        path.reverse()
    
    return dist, prev, path


def bellman_ford_shortest_path(graph: m_basic_graph.BasicGraph, start_id: str,
                             weights: Dict[str, float]) -> Optional[Dict[str, float]]:
    """Find shortest paths using Bellman-Ford algorithm (handles negative weights)."""

    dist = {node.id: float('inf') for node in graph.get_all_nodes()}
    dist[start_id] = 0
    
    # Relax edges |V|-1 times
    V = len(graph.get_all_nodes())
    for _ in range(V - 1):
        for edge in graph.get_all_edges():
            if dist[edge.source_id] != float('inf'):
                new_dist = dist[edge.source_id] + weights.get(edge.id, 1)
                if new_dist < dist[edge.target_id]:
                    dist[edge.target_id] = new_dist
    
    # Check for negative cycles
    for edge in graph.get_all_edges():
        if (dist[edge.source_id] != float('inf') and
            dist[edge.source_id] + weights.get(edge.id, 1) < dist[edge.target_id]):
            return None  # Negative cycle exists
    
    return dist


def a_star_search(graph: m_basic_graph.BasicGraph, start_id: str, goal_id: str,
                  heuristic: Callable[[m_node.Node, m_node.Node], float],
                  weights: Dict[str, float]) -> Optional[List[m_node.Node]]:
    """Find shortest path using A* search."""

    start_node = graph.get_node(start_id)
    goal_node = graph.get_node(goal_id)
    if not (start_node and goal_node):
        return None
    
    # Priority queue of (f_score, node_id)
    open_set = {start_id}
    closed_set = set()
    
    g_score = {node.id: float('inf') for node in graph.get_all_nodes()}
    g_score[start_id] = 0
    
    f_score = {node.id: float('inf') for node in graph.get_all_nodes()}
    f_score[start_id] = heuristic(start_node, goal_node)
    
    came_from = {}
    pq = [(f_score[start_id], start_id)]
    
    while open_set:
        current_id = heapq.heappop(pq)[1]
        if current_id == goal_id:
            # Reconstruct path
            path = []
            while current_id in came_from:
                path.append(graph.get_node(current_id))
                current_id = came_from[current_id]
            path.append(start_node)
            return list(reversed(path))
        
        open_set.remove(current_id)
        closed_set.add(current_id)
        
        for edge in graph.get_edges_from_node(current_id):
            neighbor_id = edge.target_id
            if neighbor_id in closed_set:
                continue
            
            tentative_g_score = g_score[current_id] + weights.get(edge.id, 1)
            
            if neighbor_id not in open_set:
                open_set.add(neighbor_id)
            elif tentative_g_score >= g_score[neighbor_id]:
                continue
            
            came_from[neighbor_id] = current_id
            g_score[neighbor_id] = tentative_g_score
            f_score[neighbor_id] = g_score[neighbor_id] + heuristic(
                graph.get_node(neighbor_id), goal_node)
            heapq.heappush(pq, (f_score[neighbor_id], neighbor_id))
    
    return None


# Minimum Spanning Trees (Kruskal and Prim)
def kruskal_minimum_spanning_tree(graph: m_basic_graph.BasicGraph,
                                weights: Dict[str, float]) -> List[m_edge.Edge]:
    """Find minimum spanning tree using Kruskal's algorithm."""

    def find(parent: Dict[str, str], node_id: str) -> str:
        """Find set representative with path compression."""

        if parent[node_id] != node_id:
            parent[node_id] = find(parent, parent[node_id])
        return parent[node_id]
    
    def union(parent: Dict[str, str], rank: Dict[str, int],
             x: str, y: str) -> None:
        """Union by rank."""

        px, py = find(parent, x), find(parent, y)
        if rank[px] < rank[py]:
            parent[px] = py
        elif rank[px] > rank[py]:
            parent[py] = px
        else:
            parent[py] = px
            rank[px] += 1
    
    # Initialize disjoint set
    parent = {node.id: node.id for node in graph.get_all_nodes()}
    rank = {node.id: 0 for node in graph.get_all_nodes()}
    
    # Sort edges by weight
    edges = [(weights.get(edge.id, 1), edge) for edge in graph.get_all_edges()]
    edges.sort()
    
    mst = []
    for weight, edge in edges:
        if find(parent, edge.source_id) != find(parent, edge.target_id):
            union(parent, rank, edge.source_id, edge.target_id)
            mst.append(edge)
    
    return mst


def prim_minimum_spanning_tree(graph: m_basic_graph.BasicGraph,
                             weights: Dict[str, float]) -> List[m_edge.Edge]:
    """Find minimum spanning tree using Prim's algorithm."""

    start_node = next(iter(graph.get_all_nodes()))
    visited = {start_node.id}
    mst = []
    
    # Priority queue of (weight, edge)
    edges = []
    for edge in graph.get_edges_from_node(start_node.id):
        heapq.heappush(edges, (weights.get(edge.id, 1), edge))
    
    while edges:
        weight, edge = heapq.heappop(edges)
        if edge.target_id in visited:
            continue
        
        visited.add(edge.target_id)
        mst.append(edge)
        
        for next_edge in graph.get_edges_from_node(edge.target_id):
            if next_edge.target_id not in visited:
                heapq.heappush(edges, (weights.get(next_edge.id, 1), next_edge))
    
    return mst


# Cycles
def find_cycles(graph: m_basic_graph.BasicGraph) -> List[List[m_node.Node]]:
    """Find all cycles in the graph."""

    cycles = []
    visited = set()
    
    def find_cycles_util(node_id: str, parent_id: Optional[str],
                        path: List[str]) -> None:
        visited.add(node_id)
        path.append(node_id)
        
        for edge in graph.get_edges_from_node(node_id):
            if edge.target_id not in visited:
                find_cycles_util(edge.target_id, node_id, path)
            elif parent_id != edge.target_id and edge.target_id in path:
                # Found a cycle
                cycle_start = path.index(edge.target_id)
                cycle = path[cycle_start:]
                cycles.append([graph.get_node(nid) for nid in cycle])
        
        path.pop()
        visited.remove(node_id)
    
    for node in graph.get_all_nodes():
        if node.id not in visited:
            find_cycles_util(node.id, None, [])
    
    return cycles


# Connected Components
def find_connected_components(graph: m_basic_graph.BasicGraph) -> List[Set[str]]:
    """Find all connected components in the graph."""

    components = []
    unvisited = set(node.id for node in graph.get_all_nodes())
    
    while unvisited:
        start = next(iter(unvisited))
        component = set()
        
        # DFS to find component
        stack = [start]
        while stack:
            node_id = stack.pop()
            if node_id in unvisited:
                component.add(node_id)
                unvisited.remove(node_id)
                
                for edge in graph.get_edges_from_node(node_id):
                    if edge.target_id in unvisited:
                        stack.append(edge.target_id)
                
                if not graph.is_directed:
                    for edge in graph.get_edges_to_node(node_id):
                        if edge.source_id in unvisited:
                            stack.append(edge.source_id)
        
        components.append(component)
    
    return components


# Graph Coloring
def graph_coloring(graph: m_basic_graph.BasicGraph) -> Dict[str, int]:
    """Color the graph using the minimum number of colors."""

    colors = {}
    available_colors = set()
    
    for node in graph.get_all_nodes():
        # Find colors of neighbors
        neighbor_colors = set()
        for edge in graph.get_edges_from_node(node.id):
            if edge.target_id in colors:
                neighbor_colors.add(colors[edge.target_id])
        if not graph.is_directed:
            for edge in graph.get_edges_to_node(node.id):
                if edge.source_id in colors:
                    neighbor_colors.add(colors[edge.source_id])
        
        # Find first available color
        color = 0
        while color in neighbor_colors:
            color += 1
        
        colors[node.id] = color
        available_colors.add(color)
    
    return colors


# Identifies bottleneck paths (Flow)
def ford_fulkerson_max_flow(graph: m_basic_graph.BasicGraph, source_id: str, sink_id: str,
                           capacities: Dict[str, float]) -> float:
    """Find maximum flow using Ford-Fulkerson algorithm."""

    def find_path(residual_graph: Dict[str, Dict[str, float]]) -> Optional[List[str]]:
        """Find augmenting path using BFS."""

        visited = {source_id}
        paths = {source_id: [source_id]}
        queue = deque([source_id])
        
        while queue:
            node_id = queue.popleft()
            for next_id, res_cap in residual_graph[node_id].items():
                if next_id not in visited and res_cap > 0:
                    visited.add(next_id)
                    paths[next_id] = paths[node_id] + [next_id]
                    if next_id == sink_id:
                        return paths[next_id]
                    queue.append(next_id)
        
        return None
    
    # Initialize residual graph
    residual = defaultdict(lambda: defaultdict(float))
    for edge in graph.get_all_edges():
        residual[edge.source_id][edge.target_id] = capacities.get(edge.id, 0)
    
    max_flow = 0
    while path := find_path(residual):
        # Find minimum residual capacity along path
        flow = float('inf')
        for i in range(len(path) - 1):
            flow = min(flow, residual[path[i]][path[i + 1]])
        
        # Update residual capacities
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            residual[u][v] -= flow
            residual[v][u] += flow
        
        max_flow += flow
    
    return max_flow


# Identifies importance of nodes in the graph (Centrality Measures)
def centrality_measures(graph: m_basic_graph.BasicGraph) -> Dict[str, Dict[str, float]]:
    """Compute various centrality measures for nodes."""

    def compute_shortest_paths() -> Dict[str, Dict[str, float]]:
        """Compute all-pairs shortest paths."""

        dist = {n1.id: {n2.id: float('inf') for n2 in graph.get_all_nodes()}
               for n1 in graph.get_all_nodes()}
        
        for node in graph.get_all_nodes():
            dist[node.id][node.id] = 0
        
        for edge in graph.get_all_edges():
            dist[edge.source_id][edge.target_id] = 1
            if not graph.is_directed:
                dist[edge.target_id][edge.source_id] = 1
        
        for k in dist:
            for i in dist:
                for j in dist:
                    if dist[i][j] > dist[i][k] + dist[k][j]:
                        dist[i][j] = dist[i][k] + dist[k][j]
        
        return dist
    
    # Compute shortest paths
    distances = compute_shortest_paths()
    n = len(graph.get_all_nodes())
    
    # Initialize centrality measures
    centrality = {
        "degree": {},
        "closeness": {},
        "betweenness": defaultdict(float),
        "eigenvector": {node.id: 1.0 for node in graph.get_all_nodes()}
    }
    
    # Degree centrality
    for node in graph.get_all_nodes():
        centrality["degree"][node.id] = (
            len(graph.get_edges_from_node(node.id)) +
            (0 if graph.is_directed else len(graph.get_edges_to_node(node.id)))
        ) / (n - 1)
    
    # Closeness centrality
    for node in graph.get_all_nodes():
        total_distance = sum(d for d in distances[node.id].values()
                           if d != float('inf'))
        if total_distance > 0:
            centrality["closeness"][node.id] = (n - 1) / total_distance
        else:
            centrality["closeness"][node.id] = 0
    
    # Betweenness centrality
    for s in distances:
        for t in distances:
            if s == t:
                continue
            # Count shortest paths through each node
            for v in distances:
                if v not in (s, t):
                    if (distances[s][t] ==
                        distances[s][v] + distances[v][t]):
                        centrality["betweenness"][v] += 1
    
    # Normalize betweenness
    norm = (n - 1) * (n - 2)
    if norm > 0:
        for v in centrality["betweenness"]:
            centrality["betweenness"][v] /= norm
    
    # Eigenvector centrality (power iteration)
    max_iter = 100
    tolerance = 1e-6
    for _ in range(max_iter):
        next_ev = {node.id: 0.0 for node in graph.get_all_nodes()}
        total = 0.0
        
        for node in graph.get_all_nodes():
            for edge in graph.get_edges_to_node(node.id):
                next_ev[node.id] += centrality["eigenvector"][edge.source_id]
            if not graph.is_directed:
                for edge in graph.get_edges_from_node(node.id):
                    next_ev[node.id] += centrality["eigenvector"][edge.target_id]
            total += next_ev[node.id] ** 2
        
        # Normalize
        norm = total ** 0.5
        if norm > 0:
            max_diff = 0.0
            for node_id in next_ev:
                next_ev[node_id] /= norm
                max_diff = max(max_diff,
                             abs(next_ev[node_id] -
                                 centrality["eigenvector"][node_id]))
            
            centrality["eigenvector"] = next_ev
            
            if max_diff < tolerance:
                break
    
    return centrality
