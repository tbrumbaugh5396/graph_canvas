"""
Algorithms for list-based graph structures.
"""


from typing import List, Optional, TypeVar, Callable, Any

import graph_canvas.presentation.desktop.models.list_graph as m_list_graph
import graph_canvas.presentation.desktop.models.node as m_node


T = TypeVar('T')


# Search Algorithms
def linear_search(graph: m_list_graph.ListGraph, predicate: Callable[[m_node.Node], bool]) -> Optional[m_node.Node]:
    """Linear search through the list."""

    current = graph.get_head()
    while current:
        if predicate(current):
            return current
        current = graph.get_next(current.id)
    return None


# Binary search (requires sorted list)
def binary_search(graph: m_list_graph.ListGraph, key: Any, key_func: Callable[[m_node.Node], Any]) -> Optional[m_node.Node]:
    """Binary search (requires sorted list)."""

    # Convert to array for binary search
    nodes = graph.to_array()
    left, right = 0, len(nodes) - 1
    
    while left <= right:
        mid = (left + right) // 2
        mid_key = key_func(nodes[mid])
        
        if mid_key == key:
            return nodes[mid]
        elif mid_key < key:
            left = mid + 1
        else:
            right = mid - 1
    
    return None


# Reverse the list in-place
def reverse_list(graph: m_list_graph.ListGraph) -> None:
    """Reverse the list in-place."""

    if not graph.get_head():
        return
    
    prev_id = None
    current = graph.get_head()
    
    while current:
        next_node = graph.get_next(current.id)
        
        # Remove old edge
        old_edges = graph.get_edges_from_node(current.id)
        if old_edges:
            graph.remove_edge(old_edges[0].id)
        
        # Add new edge
        if prev_id:
            graph.insert_after(current, prev_id)
        
        prev_id = current.id
        current = next_node


# Sorting Algorithms
def quicksort(graph: m_list_graph.ListGraph, key_func: Callable[[m_node.Node], Any]) -> None:
    """Sort the list using quicksort."""

    def partition(start: m_node.Node, end: Optional[m_node.Node]) -> m_node.Node:
        pivot_val = key_func(start)
        pivot = start
        current = graph.get_next(start.id)
        
        while current and current != end:
            if key_func(current) < pivot_val:
                # Move current before pivot
                graph.remove_node(current.id)
                graph.insert_before(current, pivot.id)
                pivot = current
            current = graph.get_next(current.id)
        
        return pivot
    
    def quicksort_recursive(start: Optional[m_node.Node], end: Optional[m_node.Node]) -> None:
        if not start or start == end:
            return
        
        pivot = partition(start, end)
        quicksort_recursive(start, pivot)
        quicksort_recursive(graph.get_next(pivot.id), end)
    
    quicksort_recursive(graph.get_head(), None)


def mergesort(graph: m_list_graph.ListGraph, key_func: Callable[[m_node.Node], Any]) -> None:
    """Sort the list using mergesort."""

    def split_list(head: m_node.Node) -> Tuple[m_node.Node, Optional[m_node.Node]]:
        if not head or not graph.get_next(head.id):
            return head, None
        
        # Find middle using slow/fast pointers
        slow = head
        fast = head
        prev = None
        
        while fast and graph.get_next(fast.id):
            fast = graph.get_next(graph.get_next(fast.id).id)
            prev = slow
            slow = graph.get_next(slow.id)
        
        # Split the list
        if prev:
            edges = graph.get_edges_from_node(prev.id)
            if edges:
                graph.remove_edge(edges[0].id)
        
        return head, slow
    
    def merge(left: Optional[m_node.Node], right: Optional[m_node.Node]) -> m_node.Node:
        if not left:
            return right
        if not right:
            return left
        
        # Choose head of merged list
        if key_func(left) <= key_func(right):
            result = left
            result_tail = left
            left = graph.get_next(left.id)
        else:
            result = right
            result_tail = right
            right = graph.get_next(right.id)
        
        # Merge remaining nodes
        while left and right:
            if key_func(left) <= key_func(right):
                edges = graph.get_edges_from_node(result_tail.id)
                if edges:
                    graph.remove_edge(edges[0].id)
                graph.insert_after(left, result_tail.id)
                result_tail = left
                left = graph.get_next(left.id)
            else:
                edges = graph.get_edges_from_node(result_tail.id)
                if edges:
                    graph.remove_edge(edges[0].id)
                graph.insert_after(right, result_tail.id)
                result_tail = right
                right = graph.get_next(right.id)
        
        # Append remaining nodes
        if left:
            edges = graph.get_edges_from_node(result_tail.id)
            if edges:
                graph.remove_edge(edges[0].id)
            graph.insert_after(left, result_tail.id)
        if right:
            edges = graph.get_edges_from_node(result_tail.id)
            if edges:
                graph.remove_edge(edges[0].id)
            graph.insert_after(right, result_tail.id)
        
        return result
    
    def mergesort_recursive(head: Optional[m_node.Node]) -> Optional[m_node.Node]:
        if not head or not graph.get_next(head.id):
            return head
        
        # Split list and sort recursively
        left, right = split_list(head)
        left = mergesort_recursive(left)
        right = mergesort_recursive(right)
        
        # Merge sorted halves
        return merge(left, right)
    
    if graph.get_head():
        mergesort_recursive(graph.get_head())


def bubblesort(graph: m_list_graph.ListGraph, key_func: Callable[[m_node.Node], Any]) -> None:
    """Sort the list using bubblesort."""

    if not graph.get_head():
        return
    
    n = len(graph.to_array())
    for i in range(n):
        current = graph.get_head()
        for j in range(n - i - 1):
            next_node = graph.get_next(current.id)
            if next_node and key_func(current) > key_func(next_node):
                # Swap nodes
                graph.remove_node(next_node.id)
                graph.insert_before(next_node, current.id)
            current = graph.get_next(current.id)


# Map, Filter, Reduce
def map_list(graph: m_list_graph.ListGraph, func: Callable[[m_node.Node], None]) -> None:
    """Apply a function to each node in the list."""

    current = graph.get_head()
    while current:
        func(current)
        current = graph.get_next(current.id)


def filter_list(graph: m_list_graph.ListGraph, predicate: Callable[[m_node.Node], bool]) -> None:
    """Remove nodes that don't satisfy the predicate."""

    current = graph.get_head()
    while current:
        next_node = graph.get_next(current.id)
        if not predicate(current):
            graph.remove_node(current.id)
        current = next_node


def reduce_list(graph: m_list_graph.ListGraph, func: Callable[[T, m_node.Node], T], initial: T) -> T:
    """Reduce the list to a single value."""

    result = initial
    current = graph.get_head()
    while current:
        result = func(result, current)
        current = graph.get_next(current.id)
    return result
