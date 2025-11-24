"""
Layout algorithms for graph visualization.
"""


import math
import wx

from typing import TYPE_CHECKING

import graph_canvas.presentation.desktop.gui.main_window as m_main_window

import graph_canvas.presentation.desktop.gui.graph_canvas as m_graph_canvas


# Layout algorithms
def apply_spring_layout(graph_canvas: "m_graph_canvas.GraphCanvas"):
    """Apply spring layout algorithm."""

    # Simple spring layout implementation
    nodes = graph_canvas.graph.get_all_nodes()
    if len(nodes) < 2:
        return

    # Parameters
    k = 100  # Spring constant
    damping = 0.9
    iterations = 50

    # Initialize forces
    forces = {}
    for node in nodes:
        forces[node.id] = [0.0, 0.0]

    for _ in range(iterations):
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
                        force = k * k / distance
                        fx = -force * dx / distance
                        fy = -force * dy / distance
                        forces[node1.id][0] += fx
                        forces[node1.id][1] += fy

        # Attractive forces for connected nodes
        for edge in graph_canvas.graph.get_all_edges():
            source = graph_canvas.graph.get_node(edge.source_id)
            target = graph_canvas.graph.get_node(edge.target_id)

            if source and target:
                dx = target.x - source.x
                dy = target.y - source.y
                distance = math.sqrt(dx * dx + dy * dy)

                if distance > 0:
                    force = distance * distance / k
                    fx = force * dx / distance
                    fy = force * dy / distance
                    forces[source.id][0] += fx
                    forces[source.id][1] += fy
                    forces[target.id][0] -= fx
                    forces[target.id][1] -= fy

                # Apply forces
    for node in nodes:
        node.x += forces[node.id][0] * damping
        node.y += forces[node.id][1] * damping

    graph_canvas.graph.modified = True
    graph_canvas.graph_modified.emit()
    graph_canvas.Refresh()


def apply_circle_layout(graph_canvas: "m_graph_canvas.GraphCanvas"):
    """Apply circular layout algorithm."""

    nodes = graph_canvas.graph.get_all_nodes()
    if not nodes:
        return

    radius = 200
    center_x = 0
    center_y = 0

    for i, node in enumerate(nodes):
        angle = 2 * math.pi * i / len(nodes)
        node.x = center_x + radius * math.cos(angle)
        node.y = center_y + radius * math.sin(angle)

    graph_canvas.graph.modified = True
    graph_canvas.graph_modified.emit()
    graph_canvas.Refresh()


def apply_tree_layout(graph_canvas: "m_graph_canvas.GraphCanvas"):
    """Apply tree layout algorithm."""

    nodes = graph_canvas.graph.get_all_nodes()
    if not nodes:
        return

    # Simple tree layout - arrange nodes in levels
    levels = {}
    visited = set()

    # Find root nodes (nodes with no incoming edges)
    roots = []
    for node in nodes:
        has_incoming = False
        for edge in graph_canvas.graph.get_all_edges():
            if edge.target_id == node.id:
                has_incoming = True
                break
        if not has_incoming:
            roots.append(node)

    if not roots:
        roots = [nodes[0]]  # Use first node as root

    # BFS to assign levels
    queue = [(root, 0) for root in roots]

    while queue:
        node, level = queue.pop(0)
        if node.id in visited:
            continue

        visited.add(node.id)
        if level not in levels:
            levels[level] = []
        levels[level].append(node)

        # Add children
        for edge in graph_canvas.graph.get_all_edges():
            if edge.source_id == node.id:
                child = graph_canvas.graph.get_node(edge.target_id)
                if child and child.id not in visited:
                    queue.append((child, level + 1))

    # Position nodes
    y_spacing = 100
    x_spacing = 150

    for level, level_nodes in levels.items():
        y = level * y_spacing
        start_x = -(len(level_nodes) - 1) * x_spacing / 2

        for i, node in enumerate(level_nodes):
            node.x = start_x + i * x_spacing
            node.y = y

    graph_canvas.graph.modified = True
    graph_canvas.graph_modified.emit()
    graph_canvas.Refresh()


def apply_grid_layout(graph_canvas: "m_graph_canvas.GraphCanvas"):
    """Apply grid layout algorithm."""

    nodes = graph_canvas.graph.get_all_nodes()
    if not nodes:
        return
    
    # Calculate grid dimensions
    num_nodes = len(nodes)
    cols = math.ceil(math.sqrt(num_nodes))
    rows = math.ceil(num_nodes / cols)
    
    # Grid spacing
    spacing_x = 150
    spacing_y = 100
    
    # Center the grid
    start_x = -(cols - 1) * spacing_x / 2
    start_y = -(rows - 1) * spacing_y / 2
    
    # Position nodes in grid
    for i, node in enumerate(nodes):
        row = i // cols
        col = i % cols
        node.x = start_x + col * spacing_x
        node.y = start_y + row * spacing_y
    
    graph_canvas.graph.modified = True
    graph_canvas.graph_modified.emit()
    graph_canvas.Refresh()


def apply_radial_layout(graph_canvas: "m_graph_canvas.GraphCanvas"):
    """Apply radial layout algorithm."""

    nodes = graph_canvas.graph.get_all_nodes()
    if not nodes:
        return
    
    # Find the most connected node as center
    center_node = None
    max_connections = -1
    
    for node in nodes:
        connections = len(graph_canvas.graph.get_node_edges(node.id))
        if connections > max_connections:
            max_connections = connections
            center_node = node
    
    if not center_node:
        center_node = nodes[0]
    
    # Place center node at origin
    center_node.x = 0
    center_node.y = 0
    
    # Group other nodes by distance from center
    remaining_nodes = [n for n in nodes if n != center_node]
    if not remaining_nodes:
        return
    
    # Calculate distances using BFS
    distances = {}
    queue = [(center_node, 0)]
    visited = set()
    
    while queue:
        node, dist = queue.pop(0)
        if node.id in visited:
            continue
        
        visited.add(node.id)
        distances[node.id] = dist
        
        # Add connected nodes
        for edge in graph_canvas.graph.get_all_edges():
            next_node = None
            if edge.source_id == node.id:
                next_node = graph_canvas.graph.get_node(edge.target_id)
            elif edge.target_id == node.id:
                next_node = graph_canvas.graph.get_node(edge.source_id)
            
            if next_node and next_node.id not in visited:
                queue.append((next_node, dist + 1))
    
    # Group nodes by distance
    distance_groups = {}
    for node in remaining_nodes:
        dist = distances.get(node.id, 1)  # Default distance 1
        if dist not in distance_groups:
            distance_groups[dist] = []
        distance_groups[dist].append(node)
    
    # Position nodes in concentric circles
    base_radius = 120
    for dist, group_nodes in distance_groups.items():
        radius = base_radius * dist
        for i, node in enumerate(group_nodes):
            angle = 2 * math.pi * i / len(group_nodes)
            node.x = radius * math.cos(angle)
            node.y = radius * math.sin(angle)
    
    graph_canvas.graph.modified = True
    graph_canvas.graph_modified.emit()
    graph_canvas.Refresh()


def apply_layered_layout(graph_canvas: "m_graph_canvas.GraphCanvas"):
    """Apply layered layout algorithm (similar to tree but horizontal)."""

    nodes = graph_canvas.graph.get_all_nodes()
    if not nodes:
        return
    
    # Find layers using topological sort
    in_degree = {}
    for node in nodes:
        in_degree[node.id] = 0
    
    for edge in graph_canvas.graph.get_all_edges():
        if edge.target_id in in_degree:
            in_degree[edge.target_id] += 1
    
    # Start with nodes that have no incoming edges
    queue = [node for node in nodes if in_degree[node.id] == 0]
    if not queue:
        queue = [nodes[0]]  # If cyclic, start with first node
    
    layers = {}
    layer = 0
    processed = set()
    
    while queue:
        current_layer = queue[:]
        queue = []
        layers[layer] = current_layer
        
        for node in current_layer:
            processed.add(node.id)
            
            # Add children to next layer
            for edge in graph_canvas.graph.get_all_edges():
                if edge.source_id == node.id:
                    target = graph_canvas.graph.get_node(edge.target_id)
                    if target and target.id not in processed:
                        in_degree[target.id] -= 1
                        if in_degree[target.id] <= 0 and target not in queue:
                            queue.append(target)
        
        layer += 1
        if layer > len(nodes):  # Prevent infinite loop
            break
    
    # Position nodes
    layer_spacing = 200
    node_spacing = 100
    
    for layer_num, layer_nodes in layers.items():
        x = layer_num * layer_spacing
        start_y = -(len(layer_nodes) - 1) * node_spacing / 2
        
        for i, node in enumerate(layer_nodes):
            node.x = x
            node.y = start_y + i * node_spacing
    
    graph_canvas.graph.modified = True
    graph_canvas.graph_modified.emit()
    graph_canvas.Refresh()
    

def apply_organic_layout(graph_canvas: "m_graph_canvas.GraphCanvas"):
    """Apply organic layout algorithm (improved force-directed)."""

    nodes = graph_canvas.graph.get_all_nodes()
    if len(nodes) < 2:
        return
    
    # Enhanced parameters for organic look
    k = 150  # Optimal edge length
    c1 = 2.0  # Repulsion strength
    c2 = 1.0  # Attraction strength
    c3 = 1.0  # Damping factor
    c4 = 0.1  # Temperature cooling rate
    
    # More iterations for organic appearance
    max_iterations = 100
    initial_temp = 100.0
    
    # Initialize random positions if nodes are clustered
    import random
    for node in nodes:
        if abs(node.x) < 10 and abs(node.y) < 10:
            node.x = random.uniform(-200, 200)
            node.y = random.uniform(-200, 200)
    
    for iteration in range(max_iterations):
        # Calculate temperature (cooling schedule)
        temp = initial_temp * (1 - iteration / max_iterations)
        
        # Initialize forces
        forces = {}
        for node in nodes:
            forces[node.id] = [0.0, 0.0]
        
        # Repulsive forces between all node pairs
        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes):
                if i != j:
                    dx = node2.x - node1.x
                    dy = node2.y - node1.y
                    distance = math.sqrt(dx * dx + dy * dy) + 0.01  # Avoid division by zero
                    
                    # Repulsive force (stronger for organic look)
                    force = c1 * (k * k) / distance
                    fx = -force * dx / distance
                    fy = -force * dy / distance
                    
                    forces[node1.id][0] += fx
                    forces[node1.id][1] += fy
        
        # Attractive forces for connected nodes
        for edge in graph_canvas.graph.get_all_edges():
            source = graph_canvas.graph.get_node(edge.source_id)
            target = graph_canvas.graph.get_node(edge.target_id)
            
            if source and target:
                dx = target.x - source.x
                dy = target.y - source.y
                distance = math.sqrt(dx * dx + dy * dy) + 0.01
                
                # Attractive force
                force = c2 * distance / k
                fx = force * dx / distance
                fy = force * dy / distance
                
                forces[source.id][0] += fx
                forces[source.id][1] += fy
                forces[target.id][0] -= fx
                forces[target.id][1] -= fy
        
        # Apply forces with temperature-based movement
        max_displacement = temp / 10.0
        for node in nodes:
            fx, fy = forces[node.id]
            
            # Limit displacement
            displacement = math.sqrt(fx * fx + fy * fy)
            if displacement > max_displacement:
                fx = fx / displacement * max_displacement
                fy = fy / displacement * max_displacement
            
            node.x += fx * c3
            node.y += fy * c3
    
    graph_canvas.graph.modified = True
    graph_canvas.graph_modified.emit()
    graph_canvas.Refresh()


def apply_random_layout(graph_canvas: "m_graph_canvas.GraphCanvas"):
    """Apply random layout algorithm."""

    import random

    nodes = graph_canvas.graph.get_all_nodes()
    if not nodes:
        return

    # Random positions in a reasonable area
    for node in nodes:
        node.x = random.uniform(-400, 400)
        node.y = random.uniform(-300, 300)

    graph_canvas.graph.modified = True
    graph_canvas.graph_modified.emit()
    graph_canvas.Refresh()
  

def apply_random_2_layout(graph_canvas: "m_graph_canvas.GraphCanvas", event):
    """Apply random layout."""

    import random
    
    nodes = graph_canvas.current_graph.get_all_nodes()
    if not nodes:
        return
    
    print(f"DEBUG: Applying random 2 layout to {len(nodes)} nodes")
    
    # Random positions within a reasonable area
    area_size = max(300, 100 * len(nodes)**0.5)
    
    for node in nodes:
        node.x = random.uniform(-area_size / 2, area_size / 2)
        node.y = random.uniform(-area_size / 2, area_size / 2)
    
    graph_canvas.zoom_to_fit()
    graph_canvas.Refresh()
    print("DEBUG: Random 2 layout complete")


def apply_compact_layout(graph_canvas: "m_graph_canvas.GraphCanvas"):
    """Apply compact layout algorithm to minimize graph area."""

    nodes = graph_canvas.graph.get_all_nodes()
    if not nodes:
        return
    
    # Start with current positions and gradually compact
    iterations = 20
    compression_factor = 0.95
    
    for _ in range(iterations):
        # Find current bounds
        min_x = min(node.x for node in nodes)
        max_x = max(node.x for node in nodes)
        min_y = min(node.y for node in nodes)
        max_y = max(node.y for node in nodes)
        
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        # Move nodes toward center while avoiding overlaps
        for node in nodes:
            # Vector from center to node
            dx = node.x - center_x
            dy = node.y - center_y
            
            # Compress toward center
            node.x = center_x + dx * compression_factor
            node.y = center_y + dy * compression_factor
        
        # Resolve overlaps using simple repulsion
        min_distance = 80  # Minimum distance between nodes
        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes):
                if i < j:  # Avoid duplicate comparisons
                    dx = node2.x - node1.x
                    dy = node2.y - node1.y
                    distance = math.sqrt(dx * dx + dy * dy)
                    
                    if distance < min_distance and distance > 0:
                        # Push nodes apart
                        overlap = min_distance - distance
                        push_x = (dx / distance) * overlap * 0.5
                        push_y = (dy / distance) * overlap * 0.5
                        
                        node1.x -= push_x
                        node1.y -= push_y
                        node2.x += push_x
                        node2.y += push_y
    
    graph_canvas.graph.modified = True
    graph_canvas.graph_modified.emit()
    graph_canvas.Refresh()


def apply_force_layout(graph_canvas: "m_graph_canvas.GraphCanvas", event):
    """Apply force-directed layout."""

    import math
    import random
    
    nodes = graph_canvas.current_graph.get_all_nodes()
    edges = graph_canvas.current_graph.get_all_edges()
    
    if len(nodes) < 2:
        print("DEBUG: Need at least 2 nodes for force layout")
        return

    print(
        f"DEBUG: Applying force-directed layout to {len(nodes)} nodes and {len(edges)} edges"
    )
    
    # Initialize random positions if nodes are clustered
    for i, node in enumerate(nodes):
        if i == 0:
            continue
        # Spread nodes out initially
        angle = (2 * math.pi * i) / len(nodes)
        radius = 100 + 50 * len(nodes)**0.5
        node.x = radius * math.cos(angle)
        node.y = radius * math.sin(angle)
    
    # Force-directed algorithm parameters
    iterations = 100
    spring_length = 150
    spring_strength = 0.01
    repulsion_strength = 1000
    damping = 0.9
    
    # Create adjacency for connected nodes
    adjacency = {}
    for node in nodes:
        adjacency[node.id] = set()
    for edge in edges:
        if edge.source_id in adjacency and edge.target_id in adjacency:
            adjacency[edge.source_id].add(edge.target_id)
            adjacency[edge.target_id].add(edge.source_id)
    
    # Simulate forces
    for iteration in range(iterations):
        forces = {}
        for node in nodes:
            forces[node.id] = [0, 0]
        
        # Spring forces (attractive)
        for edge in edges:
            source = graph_canvas.current_graph.get_node(edge.source_id)
            target = graph_canvas.current_graph.get_node(edge.target_id)
            if source and target:
                dx = target.x - source.x
                dy = target.y - source.y
                distance = math.sqrt(dx * dx + dy *
                                        dy) + 0.01  # Avoid division by zero
                
                force = spring_strength * (distance - spring_length)
                fx = force * dx / distance
                fy = force * dy / distance
                
                forces[source.id][0] += fx
                forces[source.id][1] += fy
                forces[target.id][0] -= fx
                forces[target.id][1] -= fy
        
        # Repulsion forces
        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes):
                if i != j:
                    dx = node2.x - node1.x
                    dy = node2.y - node1.y
                    distance = math.sqrt(dx * dx + dy * dy) + 0.01
                    
                    force = repulsion_strength / (distance * distance)
                    fx = force * dx / distance
                    fy = force * dy / distance
                    
                    forces[node1.id][0] -= fx
                    forces[node1.id][1] -= fy
        
        # Apply forces
        for node in nodes:
            node.x += forces[node.id][0] * damping
            node.y += forces[node.id][1] * damping
    
    graph_canvas.zoom_to_fit(padding=100)
    graph_canvas.Refresh()
    print("DEBUG: Force-directed layout complete")


def apply_circular_layout(graph_canvas: "m_graph_canvas.GraphCanvas", event):
    """Apply circular layout."""

    import math
    
    nodes = graph_canvas.current_graph.get_all_nodes()
    if not nodes:
        return
    
    print(f"DEBUG: Applying circular layout to {len(nodes)} nodes")
    
    center_x, center_y = 0, 0
    radius = max(100, 50 * len(nodes))
    
    for i, node in enumerate(nodes):
        angle = (2 * math.pi * i) / len(nodes)
        node.x = center_x + radius * math.cos(angle)
        node.y = center_y + radius * math.sin(angle)
    
    graph_canvas.zoom_to_fit()
    graph_canvas.Refresh()
    print("DEBUG: Circular layout complete")


def apply_grid_layout(graph_canvas: "m_graph_canvas.GraphCanvas", event):
    """Apply grid layout."""

    import math
    
    nodes = graph_canvas.current_graph.get_all_nodes()
    if not nodes:
        return
    
    print(f"DEBUG: Applying grid layout to {len(nodes)} nodes")
    
    # Calculate grid dimensions
    cols = int(math.ceil(math.sqrt(len(nodes))))
    rows = int(math.ceil(len(nodes) / cols))
    
    spacing_x = 150
    spacing_y = 100
    start_x = -(cols - 1) * spacing_x / 2
    start_y = -(rows - 1) * spacing_y / 2
    
    for i, node in enumerate(nodes):
        row = i // cols
        col = i % cols
        node.x = start_x + col * spacing_x
        node.y = start_y + row * spacing_y
    
    graph_canvas.zoom_to_fit()
    graph_canvas.Refresh()
    print("DEBUG: Grid layout complete")


def apply_tree_layout(graph_canvas: "m_graph_canvas.GraphCanvas", event):
    """Apply tree layout."""

    nodes = graph_canvas.current_graph.get_all_nodes()
    edges = graph_canvas.current_graph.get_all_edges()
    
    if not nodes:
        return
    
    print(f"DEBUG: Applying tree layout to {len(nodes)} nodes")
    
    # Find root node (node with no incoming edges or first node)
    incoming = set()
    for edge in edges:
        incoming.add(edge.target_id)
    
    root = None
    for node in nodes:
        if node.id not in incoming:
            root = node
            break
    
    if not root:
        root = nodes[0]
    
    # Build adjacency list for children
    children = {}
    for node in nodes:
        children[node.id] = []
    
    for edge in edges:
        if edge.source_id in children:
            children[edge.source_id].append(edge.target_id)
    
    # Layout tree recursively
    def layout_tree(node_id, x, y, level, width_per_level):
        node = graph_canvas.current_graph.get_node(node_id)
        if not node:
            return x
        
        node.x = x
        node.y = y
        
        child_nodes = children[node_id]
        if child_nodes:
            child_width = width_per_level / len(
                child_nodes) if child_nodes else width_per_level
            child_x = x - (len(child_nodes) - 1) * child_width / 2
            
            for child_id in child_nodes:
                layout_tree(child_id, child_x, y + 100, level + 1,
                            child_width)
                child_x += child_width
        
        return x + width_per_level
    
    layout_tree(root.id, 0, 0, 0, 200)
    
    graph_canvas.zoom_to_fit()
    graph_canvas.Refresh()
    print("DEBUG: Tree layout complete")


def apply_hierarchical_layout(graph_canvas: "m_graph_canvas.GraphCanvas", event):
    """Apply hierarchical layout."""

    nodes = graph_canvas.current_graph.get_all_nodes()
    edges = graph_canvas.current_graph.get_all_edges()
    
    if not nodes:
        return
    
    print(f"DEBUG: Applying hierarchical layout to {len(nodes)} nodes")
    
    # Calculate in-degrees
    in_degree = {}
    for node in nodes:
        in_degree[node.id] = 0
    
    for edge in edges:
        if edge.target_id in in_degree:
            in_degree[edge.target_id] += 1
    
    # Topological sort to find layers
    layers = []
    remaining = set(node.id for node in nodes)
    
    while remaining:
        current_layer = []
        for node_id in list(remaining):
            if in_degree[node_id] == 0:
                current_layer.append(node_id)
                remaining.remove(node_id)
        
        if not current_layer:
            # Handle cycles - add remaining nodes to final layer
            current_layer = list(remaining)
            remaining.clear()
        
        layers.append(current_layer)
        
        # Update in-degrees
        for node_id in current_layer:
            for edge in edges:
                if edge.source_id == node_id and edge.target_id in remaining:
                    in_degree[edge.target_id] -= 1
    
    # Position nodes in layers
    y_spacing = 100
    x_spacing = 150
    
    for level, layer in enumerate(layers):
        y = level * y_spacing
        start_x = -(len(layer) - 1) * x_spacing / 2
        
        for i, node_id in enumerate(layer):
            node = graph_canvas.current_graph.get_node(node_id)
            if node:
                node.x = start_x + i * x_spacing
                node.y = y
    
    graph_canvas.zoom_to_fit()
    graph_canvas.Refresh()
    print("DEBUG: Hierarchical layout complete")


def apply_non_overlapping_layout(graph_canvas: "m_graph_canvas.GraphCanvas", event):
    """Apply non-overlapping layout algorithm."""

    nodes = graph_canvas.current_graph.get_all_nodes()
    if not nodes:
        return
        
    print(f"DEBUG: Applying non-overlapping layout to {len(nodes)} nodes")
    
    # Start with a grid layout as base
    import math
    
    grid_size = math.ceil(math.sqrt(len(nodes)))
    spacing = 120  # Minimum spacing to prevent overlaps
    
    for i, node in enumerate(nodes):
        row = i // grid_size
        col = i % grid_size
        node.x = col * spacing - (grid_size * spacing) / 2
        node.y = row * spacing - (grid_size * spacing) / 2
        
    # Apply force-based repulsion to further separate overlapping nodes
    for _ in range(50):  # Iterations
        forces = {}
        for node in nodes:
            forces[node.id] = [0.0, 0.0]
            
        # Calculate repulsive forces between nodes
        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes):
                if i >= j:
                    continue
                    
                dx = node2.x - node1.x
                dy = node2.y - node1.y
                distance = max(math.sqrt(dx * dx + dy * dy), 1.0)
                
                # If nodes are too close, apply repulsive force
                if distance < spacing * 0.8:
                    force_magnitude = (spacing * 0.8 -
                                        distance) / distance * 10.0
                    fx = dx * force_magnitude
                    fy = dy * force_magnitude
                    
                    forces[node1.id][0] -= fx
                    forces[node1.id][1] -= fy
                    forces[node2.id][0] += fx
                    forces[node2.id][1] += fy
        
        # Apply forces
        for node in nodes:
            node.x += forces[node.id][0] * 0.1
            node.y += forces[node.id][1] * 0.1
    
    graph_canvas.zoom_to_fit()
    graph_canvas.Refresh()
    print("DEBUG: Non-overlapping layout complete")


def apply_minimize_edge_overlap_layout(graph_canvas: "m_graph_canvas.GraphCanvas", event):
    """Apply layout that minimizes edge overlaps."""

    nodes = graph_canvas.current_graph.get_all_nodes()
    edges = graph_canvas.current_graph.get_all_edges()
    if not nodes:
        return
        
    print(
        f"DEBUG: Applying minimize edge overlap layout to {len(nodes)} nodes, {len(edges)} edges"
    )
    
    # Start with circular layout
    import math
    
    if len(nodes) == 1:
        nodes[0].x = 0
        nodes[0].y = 0
    else:
        radius = max(100, 50 * len(nodes)**0.5)
        
        for i, node in enumerate(nodes):
            angle = 2 * math.pi * i / len(nodes)
            node.x = radius * math.cos(angle)
            node.y = radius * math.sin(angle)
    
    # Iteratively optimize to reduce edge crossings
    for iteration in range(100):
        best_improvement = 0
        best_swap = None
        
        # Try swapping positions of nodes to reduce edge crossings
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                node1, node2 = nodes[i], nodes[j]
                
                # Count current crossings
                current_crossings = graph_canvas.count_edge_crossings(edges)
                
                # Swap positions temporarily
                node1.x, node2.x = node2.x, node1.x
                node1.y, node2.y = node2.y, node1.y
                
                # Count crossings after swap
                new_crossings = graph_canvas.count_edge_crossings(edges)
                improvement = current_crossings - new_crossings
                
                if improvement > best_improvement:
                    best_improvement = improvement
                    best_swap = (i, j)
                
                # Swap back
                node1.x, node2.x = node2.x, node1.x
                node1.y, node2.y = node2.y, node1.y
        
        # Apply best swap if found
        if best_swap:
            node1, node2 = nodes[best_swap[0]], nodes[best_swap[1]]
            node1.x, node2.x = node2.x, node1.x
            node1.y, node2.y = node2.y, node1.y
        else:
            break  # No improvement found
    
    graph_canvas.zoom_to_fit()
    graph_canvas.Refresh()
    print("DEBUG: Minimize edge overlap layout complete")


def apply_ubergraph_layout(graph_canvas: "m_graph_canvas.GraphCanvas"):
        """Update the automatic layout for ubergraph visualization."""

        # Collect all edges that need auto-layout
        auto_layout_edges = [edge for edge in graph_canvas.graph.get_all_edges() 
                           if edge.is_hyperedge and edge.uber_auto_layout]
        
        if not auto_layout_edges:
            return
            
        # Calculate center of all connected nodes for each edge
        for edge in auto_layout_edges:
            nodes = []
            if edge.source_id:
                source_node = graph_canvas.graph.get_node(edge.source_id)
                if source_node:
                    nodes.append((source_node.x, source_node.y))
            
            for node_id in edge.source_ids:
                node = graph_canvas.graph.get_node(node_id)
                if node:
                    nodes.append((node.x, node.y))
            
            if edge.target_id:
                target_node = graph_canvas.graph.get_node(edge.target_id)
                if target_node:
                    nodes.append((target_node.x, target_node.y))
            
            for node_id in edge.target_ids:
                node = graph_canvas.graph.get_node(node_id)
                if node:
                    nodes.append((node.x, node.y))
            
            if nodes:
                # Calculate center position
                center_x = sum(x for x, y in nodes) / len(nodes)
                center_y = sum(y for x, y in nodes) / len(nodes)
                
                # Add some random offset to prevent overlapping
                import random
                offset = 50  # Adjust this value to control spread
                edge.uber_x = center_x + random.uniform(-offset, offset)
                edge.uber_y = center_y + random.uniform(-offset, offset)


# Layout pop-up then application handlers
def on_spring_layout(window: "m_main_window.MainWindow", event):
    """Handle Spring Layout command."""

    # Show progress dialog for potentially long operation
    progress = wx.ProgressDialog("Applying Layout",
                                    "Calculating spring layout...", 100,
                                    window,
                                wx.PD_AUTO_HIDE | wx.PD_APP_MODAL)
    try:
        wx.SafeYield()  # Allow UI to update
        apply_spring_layout(window.canvas)
        window.current_graph.last_layout_applied = "spring"
        window.statusbar.SetStatusText("Spring layout applied", 0)
    finally:
        progress.Destroy()


def on_circle_layout(window: "m_main_window.MainWindow", event):
    """Handle Circle Layout command."""

    # Show progress dialog for potentially long operation
    progress = wx.ProgressDialog("Applying Layout",
                                    "Calculating circle layout...", 100,
                                    window,
                                wx.PD_AUTO_HIDE | wx.PD_APP_MODAL)
    try:
        wx.SafeYield()  # Allow UI to update#if hasattr(window.canvas, 'apply_circle_layout'):
        apply_circle_layout(window.canvas)
        window.current_graph.last_layout_applied = "circle"
        window.statusbar.SetStatusText("Circle layout applied", 0)
    finally:
        progress.Destroy()


def on_tree_layout(window: "m_main_window.MainWindow", event):
    """Handle Tree Layout command."""

    # Show progress dialog for potentially long operation
    progress = wx.ProgressDialog("Applying Layout",
                                    "Calculating tree layout...", 100,
                                    window,
                                wx.PD_AUTO_HIDE | wx.PD_APP_MODAL)
    try:
        wx.SafeYield()  # Allow UI to update#if hasattr(window.canvas, 'apply_circle_layout'):
        apply_tree_layout(window.canvas)
        window.current_graph.last_layout_applied = "tree"
        window.statusbar.SetStatusText("Tree layout applied", 0)
    finally:
        progress.Destroy()


def on_grid_layout(window: "m_main_window.MainWindow", event):
    """Handle Grid Layout command."""

    # Show progress dialog for potentially long operation
    progress = wx.ProgressDialog("Applying Layout",
                                    "Calculating grid layout...", 100,
                                    window,
                                wx.PD_AUTO_HIDE | wx.PD_APP_MODAL)
    try:
        wx.SafeYield()  # Allow UI to update#if hasattr(window.canvas, 'apply_circle_layout'):
        apply_grid_layout(window.canvas)
        window.current_graph.last_layout_applied = "grid"
        window.statusbar.SetStatusText("Grid layout applied", 0)
    finally:
        progress.Destroy()


def on_radial_layout(window: "m_main_window.MainWindow", event):
    """Handle Radial Layout command."""

    # Show progress dialog for potentially long operation
    progress = wx.ProgressDialog("Applying Layout",
                                    "Calculating radial layout...", 100,
                                    window,
                                wx.PD_AUTO_HIDE | wx.PD_APP_MODAL)
    try:
        wx.SafeYield()  # Allow UI to update#if hasattr(window.canvas, 'apply_circle_layout'):
        apply_radial_layout(window.canvas)
        window.current_graph.last_layout_applied = "radial"
        window.statusbar.SetStatusText("Radial layout applied", 0)
    finally:
        progress.Destroy()


def on_layered_layout(window: "m_main_window.MainWindow", event):
    """Handle Layered Layout command."""

    # Show progress dialog for potentially long operation
    progress = wx.ProgressDialog("Applying Layout",
                                    "Calculating layered layout...", 100,
                                    window,
                                wx.PD_AUTO_HIDE | wx.PD_APP_MODAL)
    try:
        wx.SafeYield()  # Allow UI to update#if hasattr(window.canvas, 'apply_circle_layout'):
        apply_layered_layout(window.canvas)
        window.current_graph.last_layout_applied = "layered"
        window.statusbar.SetStatusText("Layered layout applied", 0)
    finally:
        progress.Destroy()


def on_organic_layout(window: "m_main_window.MainWindow", event):
    """Handle Organic Layout command."""

    # Show progress dialog for potentially long operation
    progress = wx.ProgressDialog("Applying Layout",
                                 "Calculating organic layout...", 100,
                                 window,
                                 wx.PD_AUTO_HIDE | wx.PD_APP_MODAL)
    try:
        wx.SafeYield()  # Allow UI to update
        apply_organic_layout(window.canvas)
        window.current_graph.last_layout_applied = "organic"
        window.statusbar.SetStatusText("Organic layout applied", 0)
    finally:
        progress.Destroy()


def on_random_layout(window: "m_main_window.MainWindow", event):
    """Handle Random Layout command."""

    # Show progress dialog for potentially long operation
    progress = wx.ProgressDialog("Applying Layout",
                                    "Calculating random layout...", 100,
                                    window,
                                wx.PD_AUTO_HIDE | wx.PD_APP_MODAL)
    try:
        wx.SafeYield()  # Allow UI to update#if hasattr(window.canvas, 'apply_circle_layout'):
        apply_random_layout(window.canvas)
        window.current_graph.last_layout_applied = "random"
        window.statusbar.SetStatusText("Random layout applied", 0)
    finally:
        progress.Destroy()


def on_random_2_layout(window: "m_main_window.MainWindow", event):
    """Handle Random 2 Layout command."""

    # Show progress dialog for potentially long operation
    progress = wx.ProgressDialog("Applying Layout",
                                    "Calculating random 2 layout...", 100,
                                    window,
                                wx.PD_AUTO_HIDE | wx.PD_APP_MODAL)
    try:
        wx.SafeYield()  # Allow UI to update#
        apply_random_2_layout(window.canvas)
        window.current_graph.last_layout_applied = "random 2"
        window.statusbar.SetStatusText("Random 2 layout applied", 0)
    finally:
        progress.Destroy()


def on_compact_layout(window: "m_main_window.MainWindow", event):
    """Handle Compact Layout command."""

    # Show progress dialog for potentially long operation
    progress = wx.ProgressDialog("Applying Layout",
                                    "Calculating compact layout...", 100,
                                    window,
                                wx.PD_AUTO_HIDE | wx.PD_APP_MODAL)
    try:
        wx.SafeYield()  # Allow UI to update#if hasattr(window.canvas, 'apply_circle_layout'):
        apply_compact_layout(window.canvas)
        window.current_graph.last_layout_applied = "compact"
        window.statusbar.SetStatusText("Compact layout applied", 0)
    finally:
        progress.Destroy()


def on_force_layout(window: "m_main_window.MainWindow", event):
    """Handle Force Layout command."""

    # Show progress dialog for potentially long operation
    progress = wx.ProgressDialog("Applying Layout",
                                    "Calculating force layout...", 100,
                                    window,
                                wx.PD_AUTO_HIDE | wx.PD_APP_MODAL)
    try:
        wx.SafeYield()  # Allow UI to update#
        apply_force_layout(window.canvas)
        window.current_graph.last_layout_applied = "force"
        window.statusbar.SetStatusText("Force layout applied", 0)
    finally:
        progress.Destroy()


def on_circular_layout(window: "m_main_window.MainWindow", event):
    """Handle Circular Layout command."""

    # Show progress dialog for potentially long operation
    progress = wx.ProgressDialog("Applying Layout",
                                    "Calculating circular layout...", 100,
                                    window,
                                wx.PD_AUTO_HIDE | wx.PD_APP_MODAL)
    try:
        wx.SafeYield()  # Allow UI to update#
        apply_circular_layout(window.canvas)
        window.current_graph.last_layout_applied = "circular"
        window.statusbar.SetStatusText("Circular layout applied", 0)    
    finally:
        progress.Destroy()


def on_grid_layout(window: "m_main_window.MainWindow", event):
    """Handle Grid Layout command."""

    # Show progress dialog for potentially long operation
    progress = wx.ProgressDialog("Applying Layout",
                                    "Calculating grid layout...", 100,
                                    window,
                                wx.PD_AUTO_HIDE | wx.PD_APP_MODAL)
    try:
        wx.SafeYield()  # Allow UI to update#
        apply_grid_layout(window.canvas)
        window.current_graph.last_layout_applied = "grid"
        window.statusbar.SetStatusText("Grid layout applied", 0)
    finally:
        progress.Destroy()


def on_tree_layout(window: "m_main_window.MainWindow", event):
    """Handle Tree Layout command."""

    # Show progress dialog for potentially long operation
    progress = wx.ProgressDialog("Applying Layout",
                                    "Calculating tree layout...", 100,
                                    window,
                                wx.PD_AUTO_HIDE | wx.PD_APP_MODAL)
    try:
        wx.SafeYield()  # Allow UI to update#
        apply_tree_layout(window.canvas)
        window.current_graph.last_layout_applied = "tree"
        window.statusbar.SetStatusText("Tree layout applied", 0)
    finally:
        progress.Destroy()


def on_hierarchical_layout(window: "m_main_window.MainWindow", event):
    """Handle Hierarchical Layout command."""
    
    # Show progress dialog for potentially long operation
    progress = wx.ProgressDialog("Applying Layout",
                                    "Calculating hierarchical layout...", 100,
                                    window,
                                wx.PD_AUTO_HIDE | wx.PD_APP_MODAL)
    try:
        wx.SafeYield()  # Allow UI to update#
        apply_hierarchical_layout(window.canvas)
        window.current_graph.last_layout_applied = "hierarchical"
        window.statusbar.SetStatusText("Hierarchical layout applied", 0)
    finally:
        progress.Destroy()


def on_non_overlapping_layout(window: "m_main_window.MainWindow", event):
    """Handle Non-overlapping Layout command."""

    # Show progress dialog for potentially long operation
    progress = wx.ProgressDialog("Applying Layout",
                                    "Calculating non-overlapping layout...", 100,
                                    window,
                                wx.PD_AUTO_HIDE | wx.PD_APP_MODAL)
    try:
        wx.SafeYield()  # Allow UI to update#
        apply_non_overlapping_layout(window.canvas)
        window.current_graph.last_layout_applied = "non_overlapping"
        window.statusbar.SetStatusText("Non-overlapping layout applied", 0)
    finally:
        progress.Destroy()


def on_minimize_edge_overlap_layout(window: "m_main_window.MainWindow", event):
    """Handle Minimize Edge Overlap Layout command."""

    # Show progress dialog for potentially long operation
    progress = wx.ProgressDialog("Applying Layout",
                                    "Calculating minimize edge overlap layout...", 100,
                                    window,
                                wx.PD_AUTO_HIDE | wx.PD_APP_MODAL)
    try:
        wx.SafeYield()  # Allow UI to update#
        apply_minimize_edge_overlap_layout(window.canvas)
        window.current_graph.last_layout_applied = "minimize_edge_overlap"
        window.statusbar.SetStatusText("Minimize edge overlap layout applied", 0)
    finally:
        progress.Destroy()

    
def on_ubergraph_layout(window: "m_main_window.MainWindow", event):
    """Handle Ubergraph Layout command."""

    # Show progress dialog for potentially long operation
    progress = wx.ProgressDialog("Applying Layout",
                                    "Calculating ubergraph layout...", 100,
                                    window,
                                wx.PD_AUTO_HIDE | wx.PD_APP_MODAL)
    try:
        wx.SafeYield()  # Allow UI to update#
        apply_ubergraph_layout(window.canvas)
        window.current_graph.last_layout_applied = "ubergraph"
        window.statusbar.SetStatusText("Ubergraph layout applied", 0)
    finally:
        progress.Destroy()
