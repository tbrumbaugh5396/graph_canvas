"""
Algorithms for tree-based graph structures.
"""


from typing import List, Optional, Set, Dict, Any, Callable
from collections import deque

import graph_canvas.presentation.desktop.models.tree_graph as m_tree_graph
import graph_canvas.presentation.desktop.models.node as m_node


# Traversal Algorithms
def preorder_traversal(graph: m_tree_graph.TreeGraph, node_id: Optional[str] = None) -> List[m_node.Node]:
    """Traverse tree in preorder (root, left, right)."""

    result = []
    
    def traverse(current_id: str) -> None:
        node = graph.get_node(current_id)
        if node:
            result.append(node)
            for child in graph.get_children(current_id):
                traverse(child.id)
    
    start_id = node_id if node_id else graph.get_root().id if graph.get_root() else None
    if start_id:
        traverse(start_id)
    return result


def inorder_traversal(graph: m_tree_graph.TreeGraph, node_id: Optional[str] = None) -> List[m_node.Node]:
    """Traverse binary tree in inorder (left, root, right)."""

    result = []
    
    def traverse(current_id: str) -> None:
        node = graph.get_node(current_id)
        if node:
            children = graph.get_children(current_id)
            # Process left child
            if len(children) > 0:
                traverse(children[0].id)
            # Process root
            result.append(node)
            # Process right child
            if len(children) > 1:
                traverse(children[1].id)
    
    start_id = node_id if node_id else graph.get_root().id if graph.get_root() else None
    if start_id:
        traverse(start_id)
    return result


def postorder_traversal(graph: m_tree_graph.TreeGraph, node_id: Optional[str] = None) -> List[m_node.Node]:
    """Traverse tree in postorder (left, right, root)."""

    result = []
    
    def traverse(current_id: str) -> None:
        node = graph.get_node(current_id)
        if node:
            for child in graph.get_children(current_id):
                traverse(child.id)
            result.append(node)
    
    start_id = node_id if node_id else graph.get_root().id if graph.get_root() else None
    if start_id:
        traverse(start_id)
    return result


def levelorder_traversal(graph: m_tree_graph.TreeGraph, node_id: Optional[str] = None) -> List[List[m_node.Node]]:
    """Traverse tree in level order (BFS)."""

    result = []
    start_id = node_id if node_id else graph.get_root().id if graph.get_root() else None
    
    if not start_id:
        return result
    
    queue = deque([(start_id, 0)])  # (node_id, level)
    current_level = []
    current_level_num = 0
    
    while queue:
        current_id, level = queue.popleft()
        node = graph.get_node(current_id)
        
        if level > current_level_num:
            result.append(current_level)
            current_level = []
            current_level_num = level
        
        current_level.append(node)
        
        for child in graph.get_children(current_id):
            queue.append((child.id, level + 1))
    
    if current_level:
        result.append(current_level)
    
    return result


# Compute the depth of a node (distance from root)
def compute_depth(graph: m_tree_graph.TreeGraph, node_id: str) -> int:
    """Compute the depth of a node (distance from root)."""

    depth = 0
    current = node_id
    
    while current:
        parent = graph.get_parent(current)
        if parent:
            depth += 1
            current = parent.id
        else:
            break
    
    return depth


# Compute the height of a subtree (Maximum depth of any node in the subtree)
def compute_height(graph: m_tree_graph.TreeGraph, node_id: Optional[str] = None) -> int:
    """Compute the height of a subtree."""

    def height_recursive(current_id: str) -> int:
        node = graph.get_node(current_id)
        if not node:
            return -1
        
        children = graph.get_children(current_id)
        if not children:
            return 0
        
        return 1 + max(height_recursive(child.id) for child in children)
    
    start_id = node_id if node_id else graph.get_root().id if graph.get_root() else None
    return height_recursive(start_id) if start_id else -1


# Find the lowest common ancestor of two nodes (what is the node that is the first ancestor of both nodes)
def lowest_common_ancestor(graph: m_tree_graph.TreeGraph, node1_id: str, node2_id: str) -> Optional[m_node.Node]:
    """Find the lowest common ancestor of two nodes."""

    # Get paths from root to nodes
    def get_path(node_id: str) -> List[str]:
        path = []
        current = node_id
        while current:
            path.append(current)
            parent = graph.get_parent(current)
            current = parent.id if parent else None
        return list(reversed(path))
    
    path1 = get_path(node1_id)
    path2 = get_path(node2_id)
    
    # Find last common node
    i = 0
    while i < len(path1) and i < len(path2) and path1[i] == path2[i]:
        i += 1
    
    return graph.get_node(path1[i-1]) if i > 0 else None


# Compute the diameter of the tree (longest path between any two nodes)
def compute_tree_diameter(graph: m_tree_graph.TreeGraph) -> int:
    """Compute the diameter of the tree (longest path between any two nodes)."""

    def height_and_diameter(node_id: str) -> Tuple[int, int]:
        """Returns (height, diameter) of subtree."""

        node = graph.get_node(node_id)
        if not node:
            return (-1, 0)
        
        children = graph.get_children(node_id)
        if not children:
            return (0, 0)
        
        # Get heights of children
        heights = []
        max_diameter = 0
        for child in children:
            h, d = height_and_diameter(child.id)
            heights.append(h + 1)
            max_diameter = max(max_diameter, d)
        
        # Diameter is max of:
        # 1. Maximum diameter in subtrees
        # 2. Sum of two highest heights
        heights.sort(reverse=True)
        path_through_root = sum(heights[:2]) if len(heights) >= 2 else heights[0]
        
        return (heights[0], max(max_diameter, path_through_root))
    
    root = graph.get_root()
    return height_and_diameter(root.id)[1] if root else 0


# Balance the tree using AVL rotations
def balance_avl(graph: m_tree_graph.TreeGraph) -> None:
    """Balance the tree using AVL rotations."""

    def get_balance(node_id: str) -> int:
        """Get balance factor of node."""

        node = graph.get_node(node_id)
        if not node:
            return 0
        
        left_height = compute_height(graph, graph.get_children(node_id)[0].id) if len(graph.get_children(node_id)) > 0 else -1
        right_height = compute_height(graph, graph.get_children(node_id)[1].id) if len(graph.get_children(node_id)) > 1 else -1
        
        return left_height - right_height
    
    def rotate_right(node_id: str) -> str:
        """Perform right rotation."""

        node = graph.get_node(node_id)
        left_child = graph.get_children(node_id)[0]
        
        # Update parent pointers
        parent = graph.get_parent(node_id)
        if parent:
            parent_children = graph.get_children(parent.id)
            if parent_children[0].id == node_id:
                graph.remove_node(node_id)
                graph.add_child(parent.id, left_child)
            else:
                graph.remove_node(node_id)
                graph.add_child(parent.id, left_child)
        else:
            graph.remove_node(node_id)
            graph.add_node(left_child)
        
        # Move right subtree of left child
        if len(graph.get_children(left_child.id)) > 1:
            right_subtree = graph.get_children(left_child.id)[1]
            graph.remove_node(right_subtree.id)
            graph.add_child(node_id, right_subtree)
        
        # Add original node as right child
        graph.add_child(left_child.id, node)
        
        return left_child.id
    
    def rotate_left(node_id: str) -> str:
        """Perform left rotation."""

        node = graph.get_node(node_id)
        right_child = graph.get_children(node_id)[1]
        
        # Update parent pointers
        parent = graph.get_parent(node_id)
        if parent:
            parent_children = graph.get_children(parent.id)
            if parent_children[0].id == node_id:
                graph.remove_node(node_id)
                graph.add_child(parent.id, right_child)
            else:
                graph.remove_node(node_id)
                graph.add_child(parent.id, right_child)
        else:
            graph.remove_node(node_id)
            graph.add_node(right_child)
        
        # Move left subtree of right child
        if len(graph.get_children(right_child.id)) > 0:
            left_subtree = graph.get_children(right_child.id)[0]
            graph.remove_node(left_subtree.id)
            graph.add_child(node_id, left_subtree)
        
        # Add original node as left child
        graph.add_child(right_child.id, node)
        
        return right_child.id
    
    def balance_node(node_id: str) -> str:
        """Balance a single node and return new root of subtree."""

        balance = get_balance(node_id)
        
        if balance > 1:  # Left heavy
            left_child = graph.get_children(node_id)[0]
            if get_balance(left_child.id) < 0:  # Left-Right case
                rotate_left(left_child.id)
            return rotate_right(node_id)
        
        if balance < -1:  # Right heavy
            right_child = graph.get_children(node_id)[1]
            if get_balance(right_child.id) > 0:  # Right-Left case
                rotate_right(right_child.id)
            return rotate_left(node_id)
        
        return node_id
    
    def balance_recursive(node_id: str) -> None:
        """Balance tree recursively."""

        node = graph.get_node(node_id)
        if not node:
            return
        
        # Balance children first
        for child in graph.get_children(node_id):
            balance_recursive(child.id)
        
        # Balance current node
        balance_node(node_id)
    
    root = graph.get_root()
    if root:
        balance_recursive(root.id)


# Check if tree is a valid binary search tree
def is_binary_search_tree(graph: m_tree_graph.TreeGraph, key_func: Callable[[m_node.Node], Any]) -> bool:
    """Check if tree is a valid binary search tree."""

    def is_bst_recursive(node_id: str, min_val: Any = float('-inf'),
                        max_val: Any = float('inf')) -> bool:
        node = graph.get_node(node_id)
        if not node:
            return True
        
        val = key_func(node)
        if val <= min_val or val >= max_val:
            return False
        
        children = graph.get_children(node_id)
        if len(children) > 2:
            return False
        
        # Check left subtree
        if len(children) > 0 and not is_bst_recursive(children[0].id, min_val, val):
            return False
        
        # Check right subtree
        if len(children) > 1 and not is_bst_recursive(children[1].id, val, max_val):
            return False
        
        return True
    
    root = graph.get_root()
    return is_bst_recursive(root.id) if root else True


# Add BST operations to the tree
def binary_search_tree_operations(graph: m_tree_graph.TreeGraph, key_func: Callable[[m_node.Node], Any]) -> None:
    """Add BST operations to the tree."""

    def find(key: Any) -> Optional[m_node.Node]:
        """Find node with given key."""

        current = graph.get_root()
        while current:
            current_key = key_func(current)
            if current_key == key:
                return current
            
            children = graph.get_children(current.id)
            if key < current_key and len(children) > 0:
                current = children[0]
            elif key > current_key and len(children) > 1:
                current = children[1]
            else:
                break
        
        return None
    
    def insert(node: m_node.Node) -> None:
        """Insert node maintaining BST property."""

        if not graph.get_root():
            graph.add_node(node)
            return
        
        key = key_func(node)
        current = graph.get_root()
        while current:
            current_key = key_func(current)
            children = graph.get_children(current.id)
            
            if key < current_key:
                if len(children) == 0:
                    graph.add_child(current.id, node)
                    break
                current = children[0]
            else:
                if len(children) <= 1:
                    graph.add_child(current.id, node)
                    break
                current = children[1]
    
    def delete(key: Any) -> None:
        """Delete node with given key."""

        def find_min(node_id: str) -> m_node.Node:
            """Find minimum key in subtree."""

            current = graph.get_node(node_id)
            while True:
                children = graph.get_children(current.id)
                if not children:
                    break
                current = children[0]
            return current
        
        def delete_recursive(node_id: str, key: Any) -> Optional[str]:
            """Delete key from subtree and return new root."""

            node = graph.get_node(node_id)
            if not node:
                return None
            
            current_key = key_func(node)
            children = graph.get_children(node_id)
            
            if key < current_key:
                if len(children) > 0:
                    new_left = delete_recursive(children[0].id, key)
                    if new_left != children[0].id:
                        graph.remove_node(children[0].id)
                        if new_left:
                            left_node = graph.get_node(new_left)
                            graph.add_child(node_id, left_node)
            elif key > current_key:
                if len(children) > 1:
                    new_right = delete_recursive(children[1].id, key)
                    if new_right != children[1].id:
                        graph.remove_node(children[1].id)
                        if new_right:
                            right_node = graph.get_node(new_right)
                            graph.add_child(node_id, right_node)
            else:
                # Node to delete found
                if len(children) == 0:
                    return None
                elif len(children) == 1:
                    return children[0].id
                else:
                    # Two children case
                    successor = find_min(children[1].id)
                    new_right = delete_recursive(children[1].id, key_func(successor))
                    
                    # Replace node with successor
                    graph.remove_node(node_id)
                    graph.add_node(successor)
                    if len(children) > 0:
                        graph.add_child(successor.id, children[0])
                    if new_right:
                        right_node = graph.get_node(new_right)
                        graph.add_child(successor.id, right_node)
                    return successor.id
            
            return node_id
        
        root = graph.get_root()
        if root:
            delete_recursive(root.id, key)
    
    # Add operations to graph
    graph.find = find
    graph.insert_bst = insert
    graph.delete_bst = delete
