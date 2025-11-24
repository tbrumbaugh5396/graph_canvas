"""
Tree property checking algorithms.
"""


from typing import Dict, List, Set, Optional, Any, Tuple

import graph_canvas.presentation.desktop.models.tree_graph as m_tree_graph
import graph_canvas.presentation.desktop.models.node as m_node


def is_full_binary_tree(graph: m_tree_graph.TreeGraph) -> Tuple[bool, Optional[str]]:
    """
    Check if tree is a full binary tree (every node has 0 or 2 children).
    Returns (is_full, reason) where reason explains why if not full.
    """

    def check_node(node_id: str) -> bool:
        children = graph.get_children(node_id)
        num_children = len(children)
        
        if num_children == 1:
            return False, f"Node {node_id} has exactly one child"
        
        if num_children > 2:
            return False, f"Node {node_id} has more than two children"
        
        # Recursively check children
        for child in children:
            result, reason = check_node(child.id)
            if not result:
                return False, reason
        
        return True, None
    
    root = graph.get_root()
    if not root:
        return True, None  # Empty tree is full binary tree
    
    result, reason = check_node(root.id)
    return result, reason


def is_perfect_binary_tree(graph: m_tree_graph.TreeGraph) -> Tuple[bool, Optional[str]]:
    """
    Check if tree is a perfect binary tree (all internal nodes have 2 children,
    all leaves at same level).
    Returns (is_perfect, reason) where reason explains why if not perfect.
    """

    def get_height(node_id: str) -> int:
        children = graph.get_children(node_id)
        if not children:
            return 0
        return 1 + max(get_height(child.id) for child in children)
    
    def check_node(node_id: str, expected_height: int, current_level: int) -> Tuple[bool, Optional[str]]:
        children = graph.get_children(node_id)
        num_children = len(children)
        
        # Internal nodes must have exactly 2 children
        if current_level < expected_height and num_children != 2:
            return False, f"Internal node {node_id} has {num_children} children (should be 2)"
        
        # Leaves must be at the bottom level
        if current_level < expected_height and num_children == 0:
            return False, f"Leaf node {node_id} at level {current_level} (should be {expected_height})"
        
        # Recursively check children
        for child in children:
            result, reason = check_node(child.id, expected_height, current_level + 1)
            if not result:
                return False, reason
        
        return True, None
    
    root = graph.get_root()
    if not root:
        return True, None  # Empty tree is perfect binary tree
    
    height = get_height(root.id)
    return check_node(root.id, height, 0)


def is_complete_binary_tree(graph: m_tree_graph.TreeGraph) -> Tuple[bool, Optional[str]]:
    """
    Check if tree is a complete binary tree (all levels filled except possibly last,
    which is filled left to right).
    Returns (is_complete, reason) where reason explains why if not complete.
    """

    def check_level_order() -> Tuple[bool, Optional[str]]:
        if not graph.get_root():
            return True, None
        
        queue = [(graph.get_root().id, 0)]  # (node_id, index)
        i = 0
        
        while queue:
            node_id, index = queue.pop(0)
            if index != i:
                return False, f"Gap at index {i} (found node at {index})"
            
            children = graph.get_children(node_id)
            if len(children) > 2:
                return False, f"Node {node_id} has more than two children"
            
            # Add children to queue
            for child in children:
                queue.append((child.id, 2*i + 1 + children.index(child)))
            
            i += 1
        
        return True, None
    
    return check_level_order()


def is_balanced_binary_tree(graph: m_tree_graph.TreeGraph) -> Tuple[bool, Optional[str]]:
    """
    Check if tree is balanced (height difference between left and right subtrees
    is at most 1 for every node).
    Returns (is_balanced, reason) where reason explains why if not balanced.
    """

    def get_height(node_id: str) -> int:
        children = graph.get_children(node_id)
        if not children:
            return 0
        return 1 + max(get_height(child.id) for child in children)
    
    def check_balance(node_id: str) -> Tuple[bool, int, Optional[str]]:
        children = graph.get_children(node_id)
        if len(children) > 2:
            return False, 0, f"Node {node_id} has more than two children"
        
        if not children:
            return True, 0, None
        
        # Get heights of subtrees
        heights = [get_height(child.id) for child in children]
        while len(heights) < 2:
            heights.append(-1)  # Treat missing subtree as height -1
        
        # Check balance
        if abs(heights[0] - heights[1]) > 1:
            return False, 0, f"Node {node_id} is unbalanced (heights: {heights[0]}, {heights[1]})"
        
        # Recursively check children
        for child in children:
            is_bal, _, reason = check_balance(child.id)
            if not is_bal:
                return False, 0, reason
        
        return True, max(heights) + 1, None
    
    root = graph.get_root()
    if not root:
        return True, None
    
    is_bal, _, reason = check_balance(root.id)
    return is_bal, reason


def is_degenerate_tree(graph: m_tree_graph.TreeGraph) -> Tuple[bool, Optional[str]]:
    """
    Check if tree is degenerate (each parent has only one child).
    Returns (is_degenerate, reason) where reason explains why if not degenerate.
    """

    def check_node(node_id: str) -> Tuple[bool, Optional[str]]:
        children = graph.get_children(node_id)
        if len(children) > 1:
            return False, f"Node {node_id} has multiple children"
        
        # Recursively check single child
        if children:
            return check_node(children[0].id)
        
        return True, None
    
    root = graph.get_root()
    if not root:
        return True, None
    
    return check_node(root.id)


def get_tree_properties(graph: m_tree_graph.TreeGraph) -> Dict[str, Tuple[bool, Optional[str]]]:
    """
    Get all tree properties in one call.
    Returns dict mapping property names to (has_property, reason) tuples.
    """

    return {
        "is_full_binary_tree": is_full_binary_tree(graph),
        "is_perfect_binary_tree": is_perfect_binary_tree(graph),
        "is_complete_binary_tree": is_complete_binary_tree(graph),
        "is_balanced_binary_tree": is_balanced_binary_tree(graph),
        "is_degenerate_tree": is_degenerate_tree(graph)
    }


def get_tree_metrics(graph: m_tree_graph.TreeGraph) -> Dict[str, Any]:
    """
    Get various tree metrics.
    Returns dict with metrics like height, node count, leaf count, etc.
    """

    def get_height(node_id: str) -> int:
        children = graph.get_children(node_id)
        if not children:
            return 0
        return 1 + max(get_height(child.id) for child in children)
    
    def count_leaves(node_id: str) -> int:
        children = graph.get_children(node_id)
        if not children:
            return 1
        return sum(count_leaves(child.id) for child in children)
    
    def count_internal_nodes(node_id: str) -> int:
        children = graph.get_children(node_id)
        if not children:
            return 0
        return 1 + sum(count_internal_nodes(child.id) for child in children)
    
    root = graph.get_root()
    if not root:
        return {
            "height": 0,
            "total_nodes": 0,
            "leaf_nodes": 0,
            "internal_nodes": 0,
            "average_degree": 0.0,
            "max_degree": 0
        }
    
    # Calculate metrics
    total_nodes = len(graph.get_all_nodes())
    leaf_count = count_leaves(root.id)
    internal_count = count_internal_nodes(root.id)
    max_degree = max(len(graph.get_children(node.id)) for node in graph.get_all_nodes())
    total_edges = len(graph.get_all_edges())
    
    return {
        "height": get_height(root.id),
        "total_nodes": total_nodes,
        "leaf_nodes": leaf_count,
        "internal_nodes": internal_count,
        "average_degree": total_edges / total_nodes if total_nodes > 0 else 0,
        "max_degree": max_degree
    }
