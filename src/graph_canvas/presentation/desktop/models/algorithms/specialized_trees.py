"""
Specialized tree implementations.
"""


from typing import Dict, List, Set, Optional, Any, Tuple, TypeVar, Generic, Union
from enum import Enum
import random
import math

import graph_canvas.presentation.desktop.models.tree_graph as m_tree_graph
import graph_canvas.presentation.desktop.models.node as m_node


T = TypeVar('T')


class Color(Enum):
    """Color for Red-Black tree nodes."""

    RED = 'red'
    BLACK = 'black'


# Treap (Tree + Heap)
class TreapNode(m_node.Node):
    """Node for Treap with priority."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.priority = kwargs.get('priority', random.random())  # Random heap priority
        self.value: Any = kwargs.get('value')  # BST value


class Treap(m_tree_graph.TreeGraph):
    """
    Treap implementation.
    Combines BST (by value) and Heap (by priority) properties.
    - BST property: Left subtree values < node value < right subtree values
    - Heap property: Parent priority > children priorities
    """

    def insert(self, value: Any, priority: Optional[float] = None) -> None:
        """Insert value into treap."""
        node = TreapNode(value=value, priority=priority)
        self.add_node(node)
        
        if not self.get_root():
            return
        
        self._insert_recursive(self.get_root().id, node)
    
    def _insert_recursive(self, root_id: str, node: TreapNode) -> None:
        """Recursively insert node maintaining BST and heap properties."""
        root = self.get_node(root_id)
        if not isinstance(root, TreapNode):
            return
        
        # BST insertion
        if node.value < root.value:
            children = self.get_children(root_id)
            if not children or len(children) == 0:
                self.add_edge(root_id, node.id)
            else:
                left_child = children[0]
                if isinstance(left_child, TreapNode):
                    self._insert_recursive(left_child.id, node)
                else:
                    self.add_edge(root_id, node.id)
        else:
            children = self.get_children(root_id)
            if not children or len(children) < 2:
                self.add_edge(root_id, node.id)
            else:
                right_child = children[1]
                if isinstance(right_child, TreapNode):
                    self._insert_recursive(right_child.id, node)
                else:
                    self.add_edge(root_id, node.id)
        
        # Heap property maintenance through rotations
        self._heapify(node.id)
    
    def _heapify(self, node_id: str) -> None:
        """Maintain heap property by rotating nodes with higher priority up."""
        node = self.get_node(node_id)
        if not isinstance(node, TreapNode):
            return
        
        parent = self.get_parent(node_id)
        if not parent or not isinstance(parent, TreapNode):
            return
        
        # If node's priority is higher than parent's, rotate
        if node.priority > parent.priority:
            children = self.get_children(parent.id)
            if node_id == children[0].id:
                self._rotate_right(parent.id)
            else:
                self._rotate_left(parent.id)
            self._heapify(node_id)  # Continue heapifying up
    
    def delete(self, value: Any) -> None:
        """Delete value from treap."""
        node_id = self._find_node(value)
        if not node_id:
            return
        
        self._delete_recursive(node_id)
    
    def _delete_recursive(self, node_id: str) -> None:
        """Recursively delete node by rotating it down to a leaf."""
        node = self.get_node(node_id)
        if not isinstance(node, TreapNode):
            return
        
        children = self.get_children(node_id)
        if not children:
            # Leaf node - just remove it
            parent = self.get_parent(node_id)
            if parent:
                self.remove_edge(parent.id, node_id)
            self.remove_node(node_id)
            return
        
        # Rotate with higher priority child until node becomes leaf
        if len(children) == 1:
            child = children[0]
            if isinstance(child, TreapNode):
                self._rotate_right(node_id)
                self._delete_recursive(node_id)
        else:
            left_child, right_child = children
            if not (isinstance(left_child, TreapNode) and isinstance(right_child, TreapNode)):
                return
            
            # Rotate with the child that has higher priority
            if left_child.priority > right_child.priority:
                self._rotate_right(node_id)
            else:
                self._rotate_left(node_id)
            self._delete_recursive(node_id)
    
    def _find_node(self, value: Any) -> Optional[str]:
        """Find node with given value."""
        return self._find_recursive(self.get_root().id, value)
    
    def _find_recursive(self, node_id: str, value: Any) -> Optional[str]:
        """Recursively find node with value."""
        node = self.get_node(node_id)
        if not isinstance(node, TreapNode):
            return None
        
        if node.value == value:
            return node_id
        
        children = self.get_children(node_id)
        if value < node.value:
            if not children or len(children) == 0:
                return None
            return self._find_recursive(children[0].id, value)
        else:
            if not children or len(children) < 2:
                return None
            return self._find_recursive(children[1].id, value)
    
    def _rotate_left(self, node_id: str) -> None:
        """Perform left rotation."""
        node = self.get_node(node_id)
        children = self.get_children(node_id)
        if not children or len(children) < 2:
            return
        
        right_child = children[1]
        self.move_subtree(right_child.id, node_id)
    
    def _rotate_right(self, node_id: str) -> None:
        """Perform right rotation."""
        node = self.get_node(node_id)
        children = self.get_children(node_id)
        if not children:
            return
        
        left_child = children[0]
        self.move_subtree(left_child.id, node_id)
    
    def split(self, value: Any) -> Tuple[m_tree_graph.TreeGraph, m_tree_graph.TreeGraph]:
        """Split treap into two treaps around value."""
        # Create new treaps for left and right parts
        left_treap = Treap()
        right_treap = Treap()
        
        # Split current treap recursively
        self._split_recursive(self.get_root().id, value, left_treap, right_treap)
        
        return left_treap, right_treap
    
    def _split_recursive(self, node_id: str, value: Any, 
                        left_treap: m_tree_graph.TreeGraph, right_treap: m_tree_graph.TreeGraph) -> None:
        """Recursively split treap."""
        node = self.get_node(node_id)
        if not isinstance(node, TreapNode):
            return
        
        children = self.get_children(node_id)
        
        if node.value <= value:
            # Node goes to left treap
            new_node = TreapNode(
                value=node.value,
                priority=node.priority
            )
            left_treap.add_node(new_node)
            
            # Process left subtree
            if children and len(children) > 0:
                self._split_recursive(children[0].id, value, left_treap, right_treap)
            
            # Process right subtree
            if children and len(children) > 1:
                self._split_recursive(children[1].id, value, left_treap, right_treap)
        else:
            # Node goes to right treap
            new_node = TreapNode(
                value=node.value,
                priority=node.priority
            )
            right_treap.add_node(new_node)
            
            # Process subtrees
            if children:
                for child in children:
                    self._split_recursive(child.id, value, left_treap, right_treap)
    
    def merge(self, other: 'Treap') -> None:
        """Merge another treap into this one."""
        if not other.get_root():
            return
        
        # Merge nodes recursively
        self._merge_recursive(other.get_root().id, other)
    
    def _merge_recursive(self, node_id: str, other: 'Treap') -> None:
        """Recursively merge nodes from other treap."""
        node = other.get_node(node_id)
        if not isinstance(node, TreapNode):
            return
        
        # Insert node into this treap
        self.insert(node.value, node.priority)
        
        # Process children
        children = other.get_children(node_id)
        if children:
            for child in children:
                self._merge_recursive(child.id, other)


# AVL Tree
class AVLNode(m_node.Node):
    """Node for AVL trees with balance factor."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.height = 1
        self.balance_factor = 0


class AVLTree(m_tree_graph.TreeGraph):
    """
    AVL Tree implementation with self-balancing.
    Maintains height balance factor between -1 and 1.
    """

    def add_node(self, node: Node) -> None:
        """Add node maintaining AVL properties."""

        if not isinstance(node, AVLNode):
            avl_node = AVLNode(
                id=node.id,
                text=node.text,
                x=node.x,
                y=node.y,
                metadata=node.metadata
            )
            node = avl_node
        
        super().add_node(node)
        self._rebalance(node.id)
    
    def _rebalance(self, node_id: str) -> None:
        """Rebalance tree after insertion."""

        node = self.get_node(node_id)
        if not isinstance(node, AVLNode):
            return
        
        # Update height and balance factor
        self._update_height(node_id)
        
        # Check balance
        if node.balance_factor > 1:
            # Left heavy
            left_child = self.get_children(node_id)[0]
            if left_child.balance_factor < 0:
                # Left-Right case
                self._rotate_left(left_child.id)
            self._rotate_right(node_id)
        elif node.balance_factor < -1:
            # Right heavy
            right_child = self.get_children(node_id)[1]
            if right_child.balance_factor > 0:
                # Right-Left case
                self._rotate_right(right_child.id)
            self._rotate_left(node_id)
    
    def _update_height(self, node_id: str) -> None:
        """Update height and balance factor of a node."""

        node = self.get_node(node_id)
        if not isinstance(node, AVLNode):
            return
        
        children = self.get_children(node_id)
        left_height = children[0].height if len(children) > 0 else 0
        right_height = children[1].height if len(children) > 1 else 0
        
        node.height = 1 + max(left_height, right_height)
        node.balance_factor = left_height - right_height
    
    def _rotate_left(self, node_id: str) -> None:
        """Perform left rotation."""

        node = self.get_node(node_id)
        right_child = self.get_children(node_id)[1]
        
        # Update edges
        self.move_subtree(right_child.id, node_id)
        
        # Update heights
        self._update_height(node_id)
        self._update_height(right_child.id)
    
    def _rotate_right(self, node_id: str) -> None:
        """Perform right rotation."""

        node = self.get_node(node_id)
        left_child = self.get_children(node_id)[0]
        
        # Update edges
        self.move_subtree(left_child.id, node_id)
        
        # Update heights
        self._update_height(node_id)
        self._update_height(left_child.id)


# Red-Black Tree
class RedBlackTree(m_tree_graph.TreeGraph):
    """
    Red-Black Tree implementation.
    Properties:
    1. Root is black
    2. All leaves (NIL) are black
    3. If node is red, children are black
    4. All paths from root to leaves have same number of black nodes
    """

    def add_node(self, node: Node) -> None:
        """Add node maintaining Red-Black properties."""

        if not isinstance(node, RedBlackNode):
            rb_node = RedBlackNode(
                id=node.id,
                text=node.text,
                x=node.x,
                y=node.y,
                metadata=node.metadata
            )
            node = rb_node
        
        super().add_node(node)
        self._fix_insertion(node.id)
    
    def _fix_insertion(self, node_id: str) -> None:
        """Fix Red-Black properties after insertion."""

        node = self.get_node(node_id)
        if not isinstance(node, RedBlackNode):
            return
        
        # Case 1: Root node
        if node_id == self.get_root().id:
            node.color = Color.BLACK
            return
        
        # Get parent
        parent = self.get_parent(node_id)
        if not isinstance(parent, RedBlackNode):
            return
        
        # Case 2: Parent is black
        if parent.color == Color.BLACK:
            return
        
        # Get grandparent and uncle
        grandparent = self.get_parent(parent.id)
        if not grandparent:
            return
        
        uncle = None
        for child in self.get_children(grandparent.id):
            if child.id != parent.id and isinstance(child, RedBlackNode):
                uncle = child
                break
        
        # Case 3: Parent and uncle are red
        if uncle and uncle.color == Color.RED:
            parent.color = Color.BLACK
            uncle.color = Color.BLACK
            grandparent.color = Color.RED
            self._fix_insertion(grandparent.id)
            return
        
        # Case 4: Parent is red, uncle is black (triangle)
        if node_id == self.get_children(parent.id)[1].id:
            self._rotate_left(parent.id)
            node = parent
            parent = self.get_parent(node.id)
        
        # Case 5: Parent is red, uncle is black (line)
        parent.color = Color.BLACK
        grandparent.color = Color.RED
        self._rotate_right(grandparent.id)


# B-Tree
class BTreeNode(m_node.Node):
    """Node for B-trees with multiple keys and children."""

    def __init__(self, *args, degree: int = 2, **kwargs):
        super().__init__(*args, **kwargs)
        self.keys: List[Any] = []
        self.child_ids: List[str] = []
        self.is_leaf = True
        self.degree = degree  # Minimum degree


class BTree(m_tree_graph.TreeGraph):
    """
    B-Tree implementation.
    Each node has between t-1 and 2t-1 keys where t is the minimum degree.
    """

    def __init__(self, *args, degree: int = 2, **kwargs):
        super().__init__(*args, **kwargs)
        self.degree = degree
    
    def insert_key(self, key: Any) -> None:
        """Insert a key into the B-tree."""

        root = self.get_root()
        if not root:
            # Create root node
            root = BTreeNode(degree=self.degree)
            root.keys = [key]
            self.add_node(root)
            return
        
        # Split root if full
        if len(root.keys) == 2 * self.degree - 1:
            new_root = BTreeNode(degree=self.degree)
            self.add_node(new_root)
            old_root = root
            
            # Split old root
            mid = self.degree - 1
            new_root.keys = [old_root.keys[mid]]
            new_root.is_leaf = False
            
            # Create new node for right half
            right_node = BTreeNode(degree=self.degree)
            right_node.keys = old_root.keys[mid+1:]
            right_node.child_ids = old_root.child_ids[mid+1:]
            self.add_node(right_node)
            
            # Update old root
            old_root.keys = old_root.keys[:mid]
            old_root.child_ids = old_root.child_ids[:mid+1]
            
            # Update edges
            new_root.child_ids = [old_root.id, right_node.id]
            
            root = new_root
        
        self._insert_non_full(root.id, key)
    
    def _insert_non_full(self, node_id: str, key: Any) -> None:
        """Insert key into non-full node."""

        node = self.get_node(node_id)
        if not isinstance(node, BTreeNode):
            return
        
        i = len(node.keys) - 1
        
        if node.is_leaf:
            # Insert key into leaf
            while i >= 0 and key < node.keys[i]:
                i -= 1
            node.keys.insert(i + 1, key)
        else:
            # Find child to recurse on
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1
            
            child = self.get_node(node.child_ids[i])
            if len(child.keys) == 2 * self.degree - 1:
                # Split child if full
                self._split_child(node_id, i)
                if key > node.keys[i]:
                    i += 1
            
            self._insert_non_full(node.child_ids[i], key)
    
    def _split_child(self, parent_id: str, child_index: int) -> None:
        """Split the child at given index of parent."""

        parent = self.get_node(parent_id)
        if not isinstance(parent, BTreeNode):
            return
        
        child = self.get_node(parent.child_ids[child_index])
        if not isinstance(child, BTreeNode):
            return
        
        # Create new node for right half
        new_node = BTreeNode(degree=self.degree)
        new_node.is_leaf = child.is_leaf
        
        # Move keys and children
        mid = self.degree - 1
        new_node.keys = child.keys[mid+1:]
        if not child.is_leaf:
            new_node.child_ids = child.child_ids[mid+1:]
        
        # Update parent
        parent.keys.insert(child_index, child.keys[mid])
        parent.child_ids.insert(child_index + 1, new_node.id)
        
        # Update child
        child.keys = child.keys[:mid]
        if not child.is_leaf:
            child.child_ids = child.child_ids[:mid+1]
        
        self.add_node(new_node)


# Trie
class TrieNode(Node):
    """Node for Trie with character mapping."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.children: Dict[str, str] = {}  # char -> node_id
        self.is_end = False


class Trie(m_tree_graph.TreeGraph):
    """
    Trie (prefix tree) implementation.
    Efficient for string operations.
    """

    def insert_string(self, s: str) -> None:
        """Insert string into trie."""

        root = self.get_root()
        if not root:
            root = TrieNode()
            self.add_node(root)
        
        current = root
        for char in s:
            if char not in current.children:
                # Create new node for character
                new_node = TrieNode()
                self.add_node(new_node)
                current.children[char] = new_node.id
            
            current = self.get_node(current.children[char])
            if not isinstance(current, TrieNode):
                return
        
        current.is_end = True
    
    def search_string(self, s: str) -> bool:
        """Search for string in trie."""

        node = self._find_node(s)
        return node is not None and node.is_end
    
    def starts_with(self, prefix: str) -> bool:
        """Check if any string starts with given prefix."""

        return self._find_node(prefix) is not None
    
    def _find_node(self, s: str) -> Optional[TrieNode]:
        """Find node corresponding to string."""

        current = self.get_root()
        if not isinstance(current, TrieNode):
            return None
        
        for char in s:
            if char not in current.children:
                return None
            current = self.get_node(current.children[char])
            if not isinstance(current, TrieNode):
                return None
        
        return current


# Splay Tree
class SplayNode(m_node.Node):
    """Node for Splay Tree."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value: Any = kwargs.get('value')


class SplayTree(m_tree_graph.TreeGraph):
    """
    Splay Tree implementation.
    Moves accessed nodes to root for better amortized performance.
    """

    def access(self, node_id: str) -> None:
        """Access node and splay it to root."""

        self._splay(node_id)
    
    def _splay(self, node_id: str) -> None:
        """Move node to root using tree rotations."""

        while self.get_parent(node_id):
            parent = self.get_parent(node_id)
            grandparent = self.get_parent(parent.id) if parent else None
            
            if not grandparent:
                # Zig step
                if self.get_children(parent.id)[0].id == node_id:
                    self._rotate_right(parent.id)
                else:
                    self._rotate_left(parent.id)
            elif self.get_children(grandparent.id)[0].id == parent.id:
                if self.get_children(parent.id)[0].id == node_id:
                    # Zig-zig step
                    self._rotate_right(grandparent.id)
                    self._rotate_right(parent.id)
                else:
                    # Zig-zag step
                    self._rotate_left(parent.id)
                    self._rotate_right(grandparent.id)
            else:
                if self.get_children(parent.id)[1].id == node_id:
                    # Zig-zig step
                    self._rotate_left(grandparent.id)
                    self._rotate_left(parent.id)
                else:
                    # Zig-zag step
                    self._rotate_right(parent.id)
                    self._rotate_left(grandparent.id)


# Scapegoat Tree
class ScapegoatNode(m_node.Node):
    """Node for Scapegoat Tree."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.size = 1  # Size of subtree


class ScapegoatTree(m_tree_graph.TreeGraph):
    """
    Scapegoat Tree implementation.
    Maintains balance without storing height information.
    """

    def __init__(self, *args, alpha: float = 0.7, **kwargs):
        super().__init__(*args, **kwargs)
        self.alpha = alpha  # Balance parameter
    
    def add_node(self, node: Node) -> None:
        """Add node and rebalance if necessary."""

        if not isinstance(node, ScapegoatNode):
            scapegoat_node = ScapegoatNode(
                id=node.id,
                text=node.text,
                x=node.x,
                y=node.y,
                metadata=node.metadata
            )
            node = scapegoat_node
        
        super().add_node(node)
        
        # Check if rebalancing needed
        current = node
        while current:
            parent = self.get_parent(current.id)
            if parent:
                parent_size = parent.size
                current_size = current.size
                if current_size > self.alpha * parent_size:
                    self._rebuild_subtree(parent.id)
                    break
            current = parent
    
    def _rebuild_subtree(self, root_id: str) -> None:
        """Rebuild subtree to be perfectly balanced."""

        # Get nodes in order
        nodes = []
        def inorder(node_id: str) -> None:
            node = self.get_node(node_id)
            if not node:
                return
            for child in self.get_children(node_id):
                inorder(child.id)
            nodes.append(node)
        
        inorder(root_id)
        
        # Rebuild tree
        def rebuild(start: int, end: int) -> Optional[str]:
            if start > end:
                return None
            
            mid = (start + end) // 2
            node = nodes[mid]
            
            # Clear children
            node.child_ids = []
            
            # Recursively rebuild subtrees
            left = rebuild(start, mid - 1)
            right = rebuild(mid + 1, end)
            
            if left:
                self.add_edge(node.id, left)
            if right:
                self.add_edge(node.id, right)
            
            return node.id
        
        rebuild(0, len(nodes) - 1)


# B+ Tree
class BPlusNode(m_node.Node):
    """Node for B+ Tree."""

    def __init__(self, *args, degree: int = 2, **kwargs):
        super().__init__(*args, **kwargs)
        self.keys: List[Any] = []
        self.child_ids: List[str] = []
        self.next_leaf_id: Optional[str] = None  # For leaf node linked list
        self.is_leaf = True
        self.degree = degree


class BPlusTree(m_tree_graph.TreeGraph):
    """
    B+ Tree implementation.
    Optimized for range queries with linked leaf nodes.
    """

    def __init__(self, *args, degree: int = 2, **kwargs):
        super().__init__(*args, **kwargs)
        self.degree = degree
    
    def insert_key(self, key: Any, value: Any) -> None:
        """Insert key-value pair into B+ tree."""

        root = self.get_root()
        if not root:
            # Create root node
            root = BPlusNode(degree=self.degree)
            root.keys = [key]
            root.values = [value]
            self.add_node(root)
            return
        
        # Split root if full
        if len(root.keys) == 2 * self.degree - 1:
            new_root = BPlusNode(degree=self.degree)
            self.add_node(new_root)
            new_root.is_leaf = False
            new_root.child_ids = [root.id]
            self._split_child(new_root.id, 0)
            self._insert_non_full(new_root.id, key, value)
        else:
            self._insert_non_full(root.id, key, value)
    
    def _insert_non_full(self, node_id: str, key: Any, value: Any) -> None:
        """Insert into non-full node."""

        node = self.get_node(node_id)
        if not isinstance(node, BPlusNode):
            return
        
        i = len(node.keys) - 1
        
        if node.is_leaf:
            # Insert into leaf
            while i >= 0 and key < node.keys[i]:
                i -= 1
            node.keys.insert(i + 1, key)
            node.values.insert(i + 1, value)
        else:
            # Find child to recurse on
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1
            
            child = self.get_node(node.child_ids[i])
            if len(child.keys) == 2 * self.degree - 1:
                self._split_child(node_id, i)
                if key > node.keys[i]:
                    i += 1
            
            self._insert_non_full(node.child_ids[i], key, value)
    
    def _split_child(self, parent_id: str, child_index: int) -> None:
        """Split child node, maintaining B+ tree properties."""

        parent = self.get_node(parent_id)
        if not isinstance(parent, BPlusNode):
            return
        
        child = self.get_node(parent.child_ids[child_index])
        if not isinstance(child, BPlusNode):
            return
        
        new_node = BPlusNode(degree=self.degree)
        new_node.is_leaf = child.is_leaf
        
        # Split differently for leaf and internal nodes
        if child.is_leaf:
            # Copy all keys/values, keep linked list
            mid = self.degree
            new_node.keys = child.keys[mid:]
            new_node.values = child.values[mid:]
            child.keys = child.keys[:mid]
            child.values = child.values[:mid]
            
            # Update leaf node links
            new_node.next_leaf_id = child.next_leaf_id
            child.next_leaf_id = new_node.id
            
            # Insert divider key to parent
            parent.keys.insert(child_index, new_node.keys[0])
        else:
            # Move middle key up, split children
            mid = self.degree - 1
            parent.keys.insert(child_index, child.keys[mid])
            
            new_node.keys = child.keys[mid+1:]
            new_node.child_ids = child.child_ids[mid+1:]
            
            child.keys = child.keys[:mid]
            child.child_ids = child.child_ids[:mid+1]
        
        parent.child_ids.insert(child_index + 1, new_node.id)
        self.add_node(new_node)


# Binomial Heap
class BinomialNode(m_node.Node):
    """Node for Binomial Heap."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value: Any = kwargs.get('value')
        self.degree = 0  # Number of children
        self.parent_id: Optional[str] = None
        self.child_id: Optional[str] = None  # Leftmost child
        self.sibling_id: Optional[str] = None  # Right sibling


class BinomialHeap(m_tree_graph.TreeGraph):
    """
    Binomial Heap implementation.
    Collection of binomial trees with efficient merge operation.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.min_node_id: Optional[str] = None
    
    def insert(self, value: Any) -> None:
        """Insert value into heap."""

        node = BinomialNode(value=value)
        self.add_node(node)
        
        if not self.min_node_id:
            self.min_node_id = node.id
        else:
            self._merge_nodes(node.id, self.min_node_id)
            # Update min node
            if node.value < self.get_node(self.min_node_id).value:
                self.min_node_id = node.id
    
    def _merge_nodes(self, node1_id: str, node2_id: str) -> None:
        """Merge two binomial trees of same degree."""

        node1 = self.get_node(node1_id)
        node2 = self.get_node(node2_id)
        if not (isinstance(node1, BinomialNode) and isinstance(node2, BinomialNode)):
            return
        
        # Ensure node1 has smaller value (will be parent)
        if node1.value > node2.value:
            node1, node2 = node2, node1
        
        # Make node2 child of node1
        node2.parent_id = node1.id
        node2.sibling_id = node1.child_id
        node1.child_id = node2.id
        node1.degree += 1


# Fibonacci Heap
class FibonacciNode(m_node.Node):
    """Node for Fibonacci Heap."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value: Any = kwargs.get('value')
        self.degree = 0  # Number of children
        self.marked = False  # For cascading cuts
        self.parent_id: Optional[str] = None
        self.child_id: Optional[str] = None
        self.left_id: Optional[str] = None  # Circular doubly-linked list
        self.right_id: Optional[str] = None


class FibonacciHeap(m_tree_graph.TreeGraph):
    """
    Fibonacci Heap implementation.
    Optimized for decrease-key operations.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.min_node_id: Optional[str] = None
        self.num_nodes = 0
    
    def insert(self, value: Any) -> None:
        """Insert value into heap."""

        node = FibonacciNode(value=value)
        self.add_node(node)
        
        if not self.min_node_id:
            self.min_node_id = node.id
            node.left_id = node.id
            node.right_id = node.id
        else:
            self._add_to_root_list(node.id)
            if node.value < self.get_node(self.min_node_id).value:
                self.min_node_id = node.id
        
        self.num_nodes += 1
    
    def _add_to_root_list(self, node_id: str) -> None:
        """Add node to root list."""

        node = self.get_node(node_id)
        min_node = self.get_node(self.min_node_id)
        if not (isinstance(node, FibonacciNode) and isinstance(min_node, FibonacciNode)):
            return
        
        # Insert into circular doubly-linked list
        node.left_id = min_node.left_id
        node.right_id = min_node.id
        min_node.left_id = node.id
        if node.left_id:
            left_node = self.get_node(node.left_id)
            if isinstance(left_node, FibonacciNode):
                left_node.right_id = node.id


# Segment Tree
class SegmentNode(m_node.Node):
    """Node for Segment Tree."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start = kwargs.get('start', 0)  # Range start
        self.end = kwargs.get('end', 0)      # Range end
        self.value = kwargs.get('value', 0)  # Aggregate value
        self.lazy = kwargs.get('lazy', 0)    # Lazy propagation value


class SegmentTree(m_tree_graph.TreeGraph):
    """
    Segment Tree implementation.
    Efficient range queries and updates.
    """

    def __init__(self, *args, operation: str = "sum", **kwargs):
        super().__init__(*args, **kwargs)
        self.operation = operation  # "sum", "min", "max", etc.
    
    def build(self, array: List[Any], start: int, end: int) -> str:
        """Build segment tree from array."""

        node = SegmentNode(start=start, end=end)
        self.add_node(node)
        
        if start == end:
            node.value = array[start]
            return node.id
        
        mid = (start + end) // 2
        left_id = self.build(array, start, mid)
        right_id = self.build(array, mid + 1, end)
        
        # Add edges
        self.add_edge(node.id, left_id)
        self.add_edge(node.id, right_id)
        
        # Compute value based on operation
        left_node = self.get_node(left_id)
        right_node = self.get_node(right_id)
        if isinstance(left_node, SegmentNode) and isinstance(right_node, SegmentNode):
            if self.operation == "sum":
                node.value = left_node.value + right_node.value
            elif self.operation == "min":
                node.value = min(left_node.value, right_node.value)
            elif self.operation == "max":
                node.value = max(left_node.value, right_node.value)
        
        return node.id


# Fenwick Tree (Binary Indexed Tree)
class FenwickNode(m_node.Node):
    """Node for Fenwick Tree (Binary Indexed Tree)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.index = kwargs.get('index', 0)  # 1-based index
        self.value = kwargs.get('value', 0)  # Cumulative value


class FenwickTree(m_tree_graph.TreeGraph):
    """
    Fenwick Tree (Binary Indexed Tree) implementation.
    Efficient prefix sums and point updates.
    """

    def __init__(self, *args, size: int = 0, **kwargs):
        super().__init__(*args, **kwargs)
        self.size = size
        if size > 0:
            self._build()
    
    def _build(self) -> None:
        """Build empty Fenwick tree."""

        for i in range(1, self.size + 1):
            node = FenwickNode(index=i)
            self.add_node(node)
            
            # Add edge to parent (i - LSB(i))
            parent_index = i - (i & -i)
            if parent_index > 0:
                self.add_edge(node.id, self.get_node_by_index(parent_index).id)
    
    def get_node_by_index(self, index: int) -> Optional[FenwickNode]:
        """Get node by its 1-based index."""

        for node in self.get_all_nodes():
            if isinstance(node, FenwickNode) and node.index == index:
                return node
        return None


# Spatial partitioning in 2D space
class QuadNode(m_node.Node):
    """Node for Quad Tree."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.boundary = kwargs.get('boundary', (0, 0, 0, 0))  # (x1, y1, x2, y2)
        self.value = kwargs.get('value')
        self.is_leaf = True


class QuadTree(m_tree_graph.TreeGraph):
    """
    Quad Tree implementation.
    Spatial partitioning in 2D.
    """

    def insert_point(self, x: float, y: float, value: Any) -> None:
        """Insert point into quad tree."""

        root = self.get_root()
        if not root:
            root = QuadNode(boundary=(float('-inf'), float('-inf'),
                                    float('inf'), float('inf')))
            self.add_node(root)
        
        self._insert_recursive(root.id, x, y, value)
    
    def _insert_recursive(self, node_id: str, x: float, y: float, value: Any) -> None:
        """Recursively insert point."""

        node = self.get_node(node_id)
        if not isinstance(node, QuadNode):
            return
        
        if not self._contains_point(node.boundary, x, y):
            return
        
        if node.is_leaf and node.value is None:
            node.value = value
            return
        
        if node.is_leaf:
            # Split node
            node.is_leaf = False
            old_value = node.value
            node.value = None
            
            # Create four children
            x1, y1, x2, y2 = node.boundary
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            
            children = [
                QuadNode(boundary=(x1, y1, mid_x, mid_y)),    # SW
                QuadNode(boundary=(mid_x, y1, x2, mid_y)),    # SE
                QuadNode(boundary=(x1, mid_y, mid_x, y2)),    # NW
                QuadNode(boundary=(mid_x, mid_y, x2, y2))     # NE
            ]
            
            for child in children:
                self.add_node(child)
                self.add_edge(node.id, child.id)
            
            # Re-insert old value
            old_x = (node.boundary[0] + node.boundary[2]) / 2
            old_y = (node.boundary[1] + node.boundary[3]) / 2
            self._insert_recursive(node.id, old_x, old_y, old_value)
        
        # Insert new value into appropriate child
        for child in self.get_children(node_id):
            if isinstance(child, QuadNode) and self._contains_point(child.boundary, x, y):
                self._insert_recursive(child.id, x, y, value)
                break
    
    def _contains_point(self, boundary: Tuple[float, float, float, float],
                       x: float, y: float) -> bool:
        """Check if boundary contains point."""

        x1, y1, x2, y2 = boundary
        return x1 <= x <= x2 and y1 <= y <= y2


# Spatial partitioning in 3D space
class OctNode(m_node.Node):
    """Node for Oct Tree."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.boundary = kwargs.get('boundary', (0, 0, 0, 0, 0, 0))  # (x1, y1, z1, x2, y2, z2)
        self.value = kwargs.get('value')
        self.is_leaf = True


class OctTree(m_tree_graph.TreeGraph):
    """
    Oct Tree implementation.
    Spatial partitioning in 3D space.
    """

    def insert_point(self, x: float, y: float, z: float, value: Any) -> None:
        """Insert point into oct tree."""

        root = self.get_root()
        if not root:
            root = OctNode(boundary=(float('-inf'), float('-inf'), float('-inf'),
                                   float('inf'), float('inf'), float('inf')))
            self.add_node(root)
        
        self._insert_recursive(root.id, x, y, z, value)
    
    def _insert_recursive(self, node_id: str, x: float, y: float, z: float, value: Any) -> None:
        """Recursively insert point."""

        node = self.get_node(node_id)
        if not isinstance(node, OctNode):
            return
        
        if not self._contains_point(node.boundary, x, y, z):
            return
        
        if node.is_leaf and node.value is None:
            node.value = value
            return
        
        if node.is_leaf:
            # Split node
            node.is_leaf = False
            old_value = node.value
            node.value = None
            
            # Create eight children
            x1, y1, z1, x2, y2, z2 = node.boundary
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            mid_z = (z1 + z2) / 2
            
            children = [
                # Bottom layer (z1 to mid_z)
                OctNode(boundary=(x1, y1, z1, mid_x, mid_y, mid_z)),      # SW-Bottom
                OctNode(boundary=(mid_x, y1, z1, x2, mid_y, mid_z)),      # SE-Bottom
                OctNode(boundary=(x1, mid_y, z1, mid_x, y2, mid_z)),      # NW-Bottom
                OctNode(boundary=(mid_x, mid_y, z1, x2, y2, mid_z)),      # NE-Bottom
                # Top layer (mid_z to z2)
                OctNode(boundary=(x1, y1, mid_z, mid_x, mid_y, z2)),      # SW-Top
                OctNode(boundary=(mid_x, y1, mid_z, x2, mid_y, z2)),      # SE-Top
                OctNode(boundary=(x1, mid_y, mid_z, mid_x, y2, z2)),      # NW-Top
                OctNode(boundary=(mid_x, mid_y, mid_z, x2, y2, z2))       # NE-Top
            ]
            
            for child in children:
                self.add_node(child)
                self.add_edge(node.id, child.id)
            
            # Re-insert old value
            old_x = (node.boundary[0] + node.boundary[3]) / 2
            old_y = (node.boundary[1] + node.boundary[4]) / 2
            old_z = (node.boundary[2] + node.boundary[5]) / 2
            self._insert_recursive(node.id, old_x, old_y, old_z, old_value)
        
        # Insert new value into appropriate child
        for child in self.get_children(node_id):
            if isinstance(child, OctNode) and self._contains_point(child.boundary, x, y, z):
                self._insert_recursive(child.id, x, y, z, value)
                break
    
    def _contains_point(self, boundary: Tuple[float, float, float, float, float, float],
                       x: float, y: float, z: float) -> bool:
        """Check if boundary contains point."""

        x1, y1, z1, x2, y2, z2 = boundary
        return (x1 <= x <= x2 and 
                y1 <= y <= y2 and 
                z1 <= z <= z2)
    
    def find_points_in_range(self, query_boundary: Tuple[float, float, float, float, float, float]) -> List[Tuple[float, float, float, Any]]:
        """Find all points within the given 3D range."""

        points = []
        self._range_search_recursive(self.get_root().id, query_boundary, points)
        return points
    
    def _range_search_recursive(self, node_id: str, query_boundary: Tuple[float, float, float, float, float, float],
                              points: List[Tuple[float, float, float, Any]]) -> None:
        """Recursively search for points in range."""

        node = self.get_node(node_id)
        if not isinstance(node, OctNode):
            return
        
        if not self._boundaries_overlap(node.boundary, query_boundary):
            return
        
        if node.is_leaf and node.value is not None:
            # Get center point of leaf node
            x = (node.boundary[0] + node.boundary[3]) / 2
            y = (node.boundary[1] + node.boundary[4]) / 2
            z = (node.boundary[2] + node.boundary[5]) / 2
            if self._contains_point(query_boundary, x, y, z):
                points.append((x, y, z, node.value))
        else:
            for child in self.get_children(node_id):
                self._range_search_recursive(child.id, query_boundary, points)
    
    def _boundaries_overlap(self, b1: Tuple[float, float, float, float, float, float],
                          b2: Tuple[float, float, float, float, float, float]) -> bool:
        """Check if two 3D boundaries overlap."""

        x1_1, y1_1, z1_1, x2_1, y2_1, z2_1 = b1
        x1_2, y1_2, z1_2, x2_2, y2_2, z2_2 = b2
        return not (x2_1 < x1_2 or x1_1 > x2_2 or
                   y2_1 < y1_2 or y1_1 > y2_2 or
                   z2_1 < z1_2 or z1_1 > z2_2)


# Merkle Tree (Cryptographic hash tree for data verification)
class MerkleNode(m_node.Node):
    """Node for Merkle Tree."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hash_value = kwargs.get('hash_value', '')  # Cryptographic hash
        self.data = kwargs.get('data')  # Original data for leaf nodes


class MerkleTree(m_tree_graph.TreeGraph):
    """
    Merkle Tree implementation.
    Cryptographic hash tree for data verification.
    """
    
    def __init__(self, *args, hash_func: Callable[[str], str], **kwargs):
        super().__init__(*args, **kwargs)
        self.hash_func = hash_func
    
    def build(self, data: List[str]) -> None:
        """Build Merkle tree from data."""
        if not data:
            return
        
        # Create leaf nodes
        leaves = []
        for item in data:
            node = MerkleNode(
                hash_value=self.hash_func(item),
                data=item
            )
            self.add_node(node)
            leaves.append(node)
        
        # Build tree bottom-up
        current_level = leaves
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                
                parent = MerkleNode(
                    hash_value=self.hash_func(left.hash_value + right.hash_value)
                )
                self.add_node(parent)
                self.add_edge(parent.id, left.id)
                if right != left:
                    self.add_edge(parent.id, right.id)
                
                next_level.append(parent)
            
            current_level = next_level
    
    def verify_data(self, data: str, proof: List[str]) -> bool:
        """Verify data using Merkle proof."""
        current_hash = self.hash_func(data)
        
        for sibling_hash in proof:
            # Combine hashes in order
            current_hash = self.hash_func(current_hash + sibling_hash)
        
        # Compare with root hash
        root = self.get_root()
        return root and isinstance(root, MerkleNode) and root.hash_value == current_hash
