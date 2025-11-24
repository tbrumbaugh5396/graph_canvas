"""
Basic undirected/directed graph model.
"""


from typing import Dict, List, Set, Optional, Any, Tuple

import graph_canvas.presentation.desktop.models.base_graph as m_base_graph
import graph_canvas.presentation.desktop.models.node as m_node
import graph_canvas.presentation.desktop.models.edge as m_edge


class BasicGraph(m_base_graph.BaseGraph):
    """A graph that represents a basic undirected or directed graph."""
    
    def __init__(self, *args, graph_type: str = "directed", **kwargs):
        """
        Initialize a new graph.
        
        Args:
            graph_type: One of "directed", "undirected", or "mixed"
        """
        super().__init__(*args, **kwargs)
        self.metadata["graph_type"] = "graph"
        if graph_type not in ["directed", "undirected", "mixed"]:
            raise ValueError("graph_type must be 'directed', 'undirected', or 'mixed'")
        self.metadata["graph_type"] = graph_type

    @property
    def is_directed(self) -> bool:
        """Whether the graph is strictly directed."""
        return self.metadata.get("graph_type") == "directed"

    @property
    def is_undirected(self) -> bool:
        """Whether the graph is strictly undirected."""
        return self.metadata.get("graph_type") == "undirected"

    @property
    def is_mixed(self) -> bool:
        """Whether the graph allows both directed and undirected edges."""
        return self.metadata.get("graph_type") == "mixed"

    def validate(self) -> List[str]:
        """Validate the graph structure. Returns a list of error messages."""

        return super().validate()

    def get_degree(self, node_id: str) -> int:
        """Get the degree of a node (number of connected edges)."""

        if node_id not in self._nodes:
            return 0
        
        degree = len(self.get_edges_from_node(node_id))
        if not self.is_directed:
            degree += len(self.get_edges_to_node(node_id))
        return degree

    def get_in_degree(self, node_id: str) -> int:
        """Get the in-degree of a node (number of incoming edges)."""

        if node_id not in self._nodes:
            return 0
        return len(self.get_edges_to_node(node_id))

    def get_out_degree(self, node_id: str) -> int:
        """Get the out-degree of a node (number of outgoing edges)."""

        if node_id not in self._nodes:
            return 0
        return len(self.get_edges_from_node(node_id))

    def get_neighbors(self, node_id: str) -> List["m_node.Node"]:
        """Get all neighboring nodes."""

        if node_id not in self._nodes:
            return []
        
        neighbors = set()
        
        # Add targets of outgoing edges
        for edge in self.get_edges_from_node(node_id):
            neighbors.add(edge.target_id)
        
        # For undirected graphs or to get all neighbors in directed graphs,
        # also add sources of incoming edges
        if not self.is_directed:
            for edge in self.get_edges_to_node(node_id):
                neighbors.add(edge.source_id)
        
        return [self.get_node(nid) for nid in neighbors if nid in self._nodes]

    def get_edge_between(self, node1_id: str, node2_id: str) -> Optional["m_edge.Edge"]:
        """Get the edge between two nodes if it exists."""

        if node1_id not in self._nodes or node2_id not in self._nodes:
            return None
        
        # Check for direct edge
        for edge in self.get_edges_from_node(node1_id):
            if edge.target_id == node2_id:
                return edge
        
        # For undirected graphs, also check reverse direction
        if not self.is_directed:
            for edge in self.get_edges_from_node(node2_id):
                if edge.target_id == node1_id:
                    return edge
        
        return None

    def get_path(self, start_id: str, end_id: str) -> List["m_node.Node"]:
        """Find a path between two nodes using BFS."""

        if start_id not in self._nodes or end_id not in self._nodes:
            return []
        
        # BFS
        queue = [(start_id, [start_id])]
        visited = {start_id}
        
        while queue:
            current_id, path = queue.pop(0)
            
            # Check neighbors
            for neighbor in self.get_neighbors(current_id):
                if neighbor.id not in visited:
                    if neighbor.id == end_id:
                        # Found the target - reconstruct path
                        return [self.get_node(nid) for nid in path + [end_id]]
                    
                    visited.add(neighbor.id)
                    queue.append((neighbor.id, path + [neighbor.id]))
        
        return []  # No path found

    def get_all_paths(self, start_id: str, end_id: str, max_paths: int = 10) -> List[List["m_node.Node"]]:
        """Find all paths between two nodes using DFS."""

        if start_id not in self._nodes or end_id not in self._nodes:
            return []
        
        def dfs(current_id: str, target_id: str, path: List[str], visited: Set[str], paths: List[List[str]]):
            if len(paths) >= max_paths:
                return
            
            if current_id == target_id:
                paths.append(path[:])
                return
            
            for neighbor in self.get_neighbors(current_id):
                if neighbor.id not in visited:
                    visited.add(neighbor.id)
                    dfs(neighbor.id, target_id, path + [neighbor.id], visited, paths)
                    visited.remove(neighbor.id)
        
        paths: List[List[str]] = []
        dfs(start_id, end_id, [start_id], {start_id}, paths)
        
        return [[self.get_node(nid) for nid in path] for path in paths]

    def get_connected_components(self) -> List[Set[str]]:
        """Get all connected components in the graph."""

        components = []
        unvisited = set(self._nodes.keys())
        
        while unvisited:
            # Start a new component
            start = next(iter(unvisited))
            component = set()
            queue = [start]
            
            # BFS to find all connected nodes
            while queue:
                current = queue.pop(0)
                if current in unvisited:
                    component.add(current)
                    unvisited.remove(current)
                    
                    # Add all unvisited neighbors
                    for neighbor in self.get_neighbors(current):
                        if neighbor.id in unvisited:
                            queue.append(neighbor.id)
            
            components.append(component)
        
        return components

    def is_connected(self) -> bool:
        """Check if the graph is connected."""

        if not self._nodes:
            return True
        
        # Start from any node and see if we can reach all others
        start = next(iter(self._nodes.keys()))
        visited = set()
        queue = [start]
        
        while queue:
            current = queue.pop(0)
            if current not in visited:
                visited.add(current)
                queue.extend(n.id for n in self.get_neighbors(current))
        
        return len(visited) == len(self._nodes)

    def get_cycles(self, max_cycles: int = 10) -> List[List["m_node.Node"]]:
        """Find cycles in the graph using DFS."""

        cycles: List[List[str]] = []
        
        def find_cycles(node_id: str, path: List[str], visited: Set[str]):
            if len(cycles) >= max_cycles:
                return
            
            if node_id in path[:-1]:
                # Found a cycle
                cycle_start = path.index(node_id)
                cycles.append(path[cycle_start:])
                return
            
            visited.add(node_id)
            for neighbor in self.get_neighbors(node_id):
                if len(cycles) >= max_cycles:
                    return
                if neighbor.id not in visited:
                    find_cycles(neighbor.id, path + [neighbor.id], visited.copy())
        
        # Start DFS from each node to find all cycles
        for node_id in self._nodes:
            if len(cycles) >= max_cycles:
                break
            find_cycles(node_id, [node_id], set())
        
        return [[self.get_node(nid) for nid in cycle] for cycle in cycles]

    def get_bridges(self) -> List["m_edge.Edge"]:
        """Find all bridges (edges whose removal disconnects the graph)."""

        bridges = []
        
        # Try removing each edge and check if graph becomes disconnected
        for edge in self._edges.values():
            self.remove_edge(edge.id)
            if not self.is_connected():
                bridges.append(edge)
            self.add_edge(edge)
        
        return bridges

    def get_articulation_points(self) -> List["m_node.Node"]:
        """Find all articulation points (nodes whose removal disconnects the graph)."""

        points = []
        
        # Try removing each node and check if graph becomes disconnected
        for node_id in list(self._nodes.keys()):
            self.remove_node(node_id)
            if not self.is_connected() and len(self._nodes) > 1:
                points.append(self.get_node(node_id))
            # Restore the node and its edges
            node = self.get_node(node_id)
            if node:
                self.add_node(node)
        
        return points

    def to_adjacency_matrix(self) -> Tuple[List[List[int]], Dict[str, int]]:
        """
        Convert the graph to an adjacency matrix.
        For mixed graphs:
        - 0: No edge
        - 1: Directed edge
        - 2: Undirected edge
        """

        # Create node index mapping
        nodes = list(self._nodes.values())
        node_indices = {node.id: i for i, node in enumerate(nodes)}
        
        # Create matrix
        n = len(nodes)
        matrix = [[0] * n for _ in range(n)]
        
        # Fill matrix
        for edge in self._edges.values():
            i = node_indices[edge.source_id]
            j = node_indices[edge.target_id]
            
            if self.is_mixed:
                # Use 1 for directed, 2 for undirected
                value = 2 if not edge.directed else 1
                matrix[i][j] = value
                if not edge.directed:
                    matrix[j][i] = value
            else:
                # Traditional 0/1 matrix for purely directed/undirected graphs
                matrix[i][j] = 1
                if self.is_undirected:
                    matrix[j][i] = 1
        
        return matrix, node_indices

    def from_adjacency_matrix(self, matrix: List[List[int]], node_ids: List[str]) -> None:
        """
        Create graph from an adjacency matrix.
        For mixed graphs:
        - 0: No edge
        - 1: Directed edge
        - 2: Undirected edge
        """

        n = len(matrix)
        if n != len(node_ids):
            raise ValueError("Matrix dimensions don't match number of node IDs")
        
        # Clear existing graph
        self._nodes.clear()
        self._edges.clear()
        
        # Add nodes
        for node_id in node_ids:
            self.add_node(Node(id=node_id))
        
        # Add edges
        processed = set()  # Track processed undirected edges
        for i in range(n):
            for j in range(n):
                if matrix[i][j] > 0 and (i, j) not in processed:
                    is_directed = matrix[i][j] == 1
                    edge = Edge(
                        source_id=node_ids[i],
                        target_id=node_ids[j],
                        directed=is_directed
                    )
                    self.add_edge(edge)
                    
                    if not is_directed:
                        processed.add((i, j))
                        processed.add((j, i))

    def to_incidence_matrix(self) -> Tuple[List[List[int]], Dict[str, int], Dict[str, int]]:
        """
        Convert the graph to an incidence matrix.
        For mixed graphs:
        - 0: No connection
        - +1: Target node of directed edge or endpoint of undirected edge
        - -1: Source node of directed edge
        - +2: Endpoint of undirected edge (both entries +2)
        
        Returns:
            Tuple of (matrix, node_indices, edge_indices)
        """

        nodes = list(self._nodes.values())
        edges = list(self._edges.values())
        
        node_indices = {node.id: i for i, node in enumerate(nodes)}
        edge_indices = {edge.id: i for i, edge in enumerate(edges)}
        
        # Create matrix
        matrix = [[0] * len(edges) for _ in range(len(nodes))]
        
        # Fill matrix
        for edge in edges:
            j = edge_indices[edge.id]
            
            if self.is_mixed and not edge.directed:
                # Undirected edge in mixed graph: both entries +2
                matrix[node_indices[edge.source_id]][j] = 2
                matrix[node_indices[edge.target_id]][j] = 2
            else:
                # Directed edge or pure directed/undirected graph
                matrix[node_indices[edge.source_id]][j] = -1
                matrix[node_indices[edge.target_id]][j] = 1
        
        return matrix, node_indices, edge_indices

    def from_incidence_matrix(self, matrix: List[List[int]],
                            node_ids: List[str], edge_ids: List[str]) -> None:
        """
        Create graph from an incidence matrix.
        For mixed graphs:
        - 0: No connection
        - +1: Target node of directed edge or endpoint of undirected edge
        - -1: Source node of directed edge
        - +2: Endpoint of undirected edge (both entries +2)
        """

        if len(matrix) != len(node_ids):
            raise ValueError("Matrix rows don't match number of node IDs")
        if not matrix or len(matrix[0]) != len(edge_ids):
            raise ValueError("Matrix columns don't match number of edge IDs")
        
        # Clear existing graph
        self._nodes.clear()
        self._edges.clear()
        
        # Add nodes
        for node_id in node_ids:
            self.add_node(Node(id=node_id))
        
        # Add edges
        for j, edge_id in enumerate(edge_ids):
            # Find source and target nodes
            source_id = None
            target_id = None
            is_directed = True
            
            for i, node_id in enumerate(node_ids):
                if matrix[i][j] == -1:
                    source_id = node_id
                elif matrix[i][j] == 1:
                    target_id = node_id
                elif matrix[i][j] == 2:
                    # Undirected edge - first +2 is source, second is target
                    if source_id is None:
                        source_id = node_id
                    else:
                        target_id = node_id
                    is_directed = False
            
            if source_id and target_id:
                edge = Edge(
                    id=edge_id,
                    source_id=source_id,
                    target_id=target_id,
                    directed=is_directed
                )
                self.add_edge(edge)
