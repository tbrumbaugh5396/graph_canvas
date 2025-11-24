"""
Layout algorithm utilities for the graph editor.
"""


import math
import random
from typing import List, Dict, Tuple, Set

import graph_canvas.presentation.desktop.models.graph as m_graph
import graph_canvas.presentation.desktop.models.node as m_node
import graph_canvas.presentation.desktop.models.edge as m_edge


def spring_layout(graph: m_graph.Graph,
                  iterations: int = 50,
                  k: float = 100.0,
                  damping: float = 0.9,
                  initial_temp: float = 1.0) -> bool:
    """
    Apply spring layout algorithm to a graph.
    
    Args:
        graph: The graph to layout
        iterations: Number of iterations to run
        k: Spring constant
        damping: Damping factor
        initial_temp: Initial temperature for simulated annealing
    """

    nodes = graph.get_all_nodes()
    if len(nodes) < 2:
        return False

    # Initialize forces
    forces = {}
    for node in nodes:
        forces[node.id] = [0.0, 0.0]

    temp = initial_temp

    for iteration in range(iterations):
        # Reset forces
        for node_id in forces:
            forces[node_id] = [0.0, 0.0]

        # Repulsive forces between all nodes
        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes):
                if i != j:
                    dx = node2.x - node1.x
                    dy = node2.y - node1.y
                    distance = math.sqrt(dx * dx + dy * dy)

                    if distance > 0:
                        # Repulsive force
                        force = k * k / distance
                        fx = -force * dx / distance
                        fy = -force * dy / distance
                        forces[node1.id][0] += fx
                        forces[node1.id][1] += fy

        # Attractive forces for connected nodes
        for edge in graph.get_all_edges():
            source = graph.get_node(edge.source_id)
            target = graph.get_node(edge.target_id)

            if source and target:
                dx = target.x - source.x
                dy = target.y - source.y
                distance = math.sqrt(dx * dx + dy * dy)

                if distance > 0:
                    # Attractive force
                    force = distance * distance / k
                    fx = force * dx / distance
                    fy = force * dy / distance
                    forces[source.id][0] += fx
                    forces[source.id][1] += fy
                    forces[target.id][0] -= fx
                    forces[target.id][1] -= fy

        # Apply forces with temperature cooling
        for node in nodes:
            if not node.locked:
                # Limit displacement by temperature
                displacement = math.sqrt(forces[node.id][0]**2 +
                                         forces[node.id][1]**2)
                if displacement > temp:
                    forces[
                        node.id][0] = forces[node.id][0] / displacement * temp
                    forces[
                        node.id][1] = forces[node.id][1] / displacement * temp

                node.x += forces[node.id][0] * damping
                node.y += forces[node.id][1] * damping

        # Cool down
        temp *= 0.95
    
    return True


def circle_layout(graph: m_graph.Graph,
                  radius: float = 200.0,
                  center: Tuple[float, float] = (0, 0)) -> bool:
    """
    Apply circular layout algorithm to a graph.
    
    Args:
        graph: The graph to layout
        radius: Radius of the circle
        center: Center of the circle
    """

    nodes = graph.get_all_nodes()
    if not nodes:
        return False

    center_x, center_y = center

    for i, node in enumerate(nodes):
        if not node.locked:
            angle = 2 * math.pi * i / len(nodes)
            node.x = center_x + radius * math.cos(angle)
            node.y = center_y + radius * math.sin(angle)

    return True


def tree_layout(
    graph: m_graph.Graph,
    root_node: m_node.Node = None,
    level_spacing: float = 100.0,
    node_spacing: float = 150.0,
    start_pos: Tuple[float, float] = (0, 0)) -> None:
    """
    Apply tree layout algorithm to a graph.
    
    Args:
        graph: The graph to layout
        root_node: Root node to start from (auto-selected if None)
        level_spacing: Vertical spacing between levels
        node_spacing: Horizontal spacing between nodes
        start_pos: Starting position for the root
    """

    nodes = graph.get_all_nodes()
    if not nodes:
        return

    # Find root node if not specified
    if root_node is None:
        # Find nodes with no incoming edges
        roots = []
        for node in nodes:
            has_incoming = False
            for edge in graph.get_all_edges():
                if edge.target_id == node.id:
                    has_incoming = True
                    break
            if not has_incoming:
                roots.append(node)

        if not roots:
            root_node = nodes[0]  # Use first node as root
        else:
            root_node = roots[0]  # Use first root

    # Build tree structure using BFS
    levels = {}
    visited = set()
    queue = [(root_node, 0)]

    while queue:
        node, level = queue.pop(0)
        if node.id in visited:
            continue

        visited.add(node.id)
        if level not in levels:
            levels[level] = []
        levels[level].append(node)

        # Add children
        for edge in graph.get_all_edges():
            if edge.source_id == node.id:
                child = graph.get_node(edge.target_id)
                if child and child.id not in visited:
                    queue.append((child, level + 1))

    # Position nodes
    start_x, start_y = start_pos

    for level, level_nodes in levels.items():
        y = start_y + level * level_spacing

        # Center nodes horizontally
        total_width = (len(level_nodes) - 1) * node_spacing
        start_x_level = start_x - total_width / 2

        for i, node in enumerate(level_nodes):
            if not node.locked:
                node.x = start_x_level + i * node_spacing
                node.y = y


def grid_layout(
    graph: m_graph.Graph,
    cols: int = None,
    spacing: float = 100.0,
    start_pos: Tuple[float, float] = (0, 0)) -> None:
    """
    Apply grid layout algorithm to a graph.
    
    Args:
        graph: The graph to layout
        cols: Number of columns (auto-calculated if None)
        spacing: Spacing between nodes
        start_pos: Starting position for the grid
    """

    nodes = graph.get_all_nodes()
    if not nodes:
        return False

    # Calculate grid dimensions
    if cols is None:
        cols = math.ceil(math.sqrt(len(nodes)))

    rows = math.ceil(len(nodes) / cols)

    start_x, start_y = start_pos

    for i, node in enumerate(nodes):
        if not node.locked:
            row = i // cols
            col = i % cols

            node.x = start_x + col * spacing
            node.y = start_y + row * spacing

    return True


def random_layout(
    graph: m_graph.Graph,
    bounds: Tuple[float, float, float, float] = (-400, -300, 400, 300)
) -> bool:
    """
    Apply random layout algorithm to a graph.
    
    Args:
        graph: The graph to layout
        bounds: Bounding box (left, top, right, bottom)
    """

    nodes = graph.get_all_nodes()
    if not nodes:
        return False

    left, top, right, bottom = bounds

    for node in nodes:
        if not node.locked:
            node.x = random.uniform(left, right)
            node.y = random.uniform(top, bottom)

    return True


def hierarchical_layout(graph: m_graph.Graph,
                        direction: str = "top-down",
                        level_spacing: float = 100.0,
                        node_spacing: float = 150.0) -> bool:
    """
    Apply hierarchical layout algorithm to a graph.
    
    Args:
        graph: The graph to layout
        direction: Layout direction ("top-down", "bottom-up", "left-right", "right-left")
        level_spacing: Spacing between levels
        node_spacing: Spacing between nodes in same level
    """

    nodes = graph.get_all_nodes()
    if not nodes:
        return False

    # Build hierarchy using topological sort
    in_degree = {}
    adj_list = {}

    # Initialize
    for node in nodes:
        in_degree[node.id] = 0
        adj_list[node.id] = []

    # Build adjacency list and calculate in-degrees
    for edge in graph.get_all_edges():
        adj_list[edge.source_id].append(edge.target_id)
        in_degree[edge.target_id] += 1

    # Topological sort with level tracking
    levels = {}
    queue = []

    # Find nodes with no incoming edges
    for node_id, degree in in_degree.items():
        if degree == 0:
            queue.append((node_id, 0))

    while queue:
        node_id, level = queue.pop(0)

        if level not in levels:
            levels[level] = []
        levels[level].append(node_id)

        # Process neighbors
        for neighbor_id in adj_list[node_id]:
            in_degree[neighbor_id] -= 1
            if in_degree[neighbor_id] == 0:
                queue.append((neighbor_id, level + 1))

    # Position nodes based on direction
    for level, node_ids in levels.items():
        level_nodes = [graph.get_node(node_id) for node_id in node_ids]
        level_nodes = [
            node for node in level_nodes if node and not node.locked
        ]

        if not level_nodes:
            continue

        # Calculate positions
        total_width = (len(level_nodes) - 1) * node_spacing
        start_offset = -total_width / 2

        for i, node in enumerate(level_nodes):
            if direction == "top-down":
                node.x = start_offset + i * node_spacing
                node.y = level * level_spacing
            elif direction == "bottom-up":
                node.x = start_offset + i * node_spacing
                node.y = -level * level_spacing
            elif direction == "left-right":
                node.x = level * level_spacing
                node.y = start_offset + i * node_spacing
            elif direction == "right-left":
                node.x = -level * level_spacing
                node.y = start_offset + i * node_spacing

    return True


def force_directed_layout(graph: m_graph.Graph,
                          iterations: int = 100,
                          repulsion_strength: float = 1000.0,
                          attraction_strength: float = 0.1,
                          damping: float = 0.9) -> bool:
    """
    Apply force-directed layout algorithm to a graph.
    
    Args:
        graph: The graph to layout
        iterations: Number of iterations
        repulsion_strength: Strength of repulsive forces
        attraction_strength: Strength of attractive forces
        damping: Damping factor
    """

    nodes = graph.get_all_nodes()
    if len(nodes) < 2:
        return False

    for iteration in range(iterations):
        forces = {}

        # Initialize forces
        for node in nodes:
            forces[node.id] = [0.0, 0.0]

        # Calculate repulsive forces
        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes):
                if i != j:
                    dx = node2.x - node1.x
                    dy = node2.y - node1.y
                    distance = math.sqrt(dx * dx + dy * dy)

                    if distance > 0:
                        force = repulsion_strength / (distance * distance)
                        fx = -force * dx / distance
                        fy = -force * dy / distance
                        forces[node1.id][0] += fx
                        forces[node1.id][1] += fy

        # Calculate attractive forces
        for edge in graph.get_all_edges():
            source = graph.get_node(edge.source_id)
            target = graph.get_node(edge.target_id)

            if source and target:
                dx = target.x - source.x
                dy = target.y - source.y
                distance = math.sqrt(dx * dx + dy * dy)

                if distance > 0:
                    force = attraction_strength * distance
                    fx = force * dx / distance
                    fy = force * dy / distance
                    forces[source.id][0] += fx
                    forces[source.id][1] += fy
                    forces[target.id][0] -= fx
                    forces[target.id][1] -= fy

        # Apply forces
        for node in nodes:
            if not node.locked:
                node.x += forces[node.id][0] * damping
                node.y += forces[node.id][1] * damping

    return True


def layered_layout(graph: m_graph.Graph,
                   layer_height: float = 100.0,
                   node_spacing: float = 150.0) -> bool:
    """
    Apply layered layout algorithm (suitable for DAGs).
    
    Args:
        graph: The graph to layout
        layer_height: Height between layers
        node_spacing: Horizontal spacing between nodes
    """

    nodes = graph.get_all_nodes()
    if not nodes:
        return False

    # Assign layers using longest path from sources
    layers = {}
    node_layers = {}

    # Find source nodes
    sources = []
    for node in nodes:
        is_source = True
        for edge in graph.get_all_edges():
            if edge.target_id == node.id:
                is_source = False
                break
        if is_source:
            sources.append(node)

    if not sources:
        sources = [nodes[0]]  # Use first node if no sources

    # Assign layers using DFS
    def assign_layer(node, layer):
        if node.id in node_layers:
            node_layers[node.id] = max(node_layers[node.id], layer)
        else:
            node_layers[node.id] = layer

        # Process children
        for edge in graph.get_all_edges():
            if edge.source_id == node.id:
                child = graph.get_node(edge.target_id)
                if child:
                    assign_layer(child, layer + 1)

    # Start from sources
    for source in sources:
        assign_layer(source, 0)

    # Group nodes by layer
    for node_id, layer in node_layers.items():
        if layer not in layers:
            layers[layer] = []
        layers[layer].append(node_id)

    # Position nodes
    for layer, node_ids in layers.items():
        layer_nodes = [graph.get_node(node_id) for node_id in node_ids]
        layer_nodes = [
            node for node in layer_nodes if node and not node.locked
        ]

        if not layer_nodes:
            continue

        # Center nodes horizontally
        total_width = (len(layer_nodes) - 1) * node_spacing
        start_x = -total_width / 2

        for i, node in enumerate(layer_nodes):
            node.x = start_x + i * node_spacing
            node.y = layer * layer_height

    return True
