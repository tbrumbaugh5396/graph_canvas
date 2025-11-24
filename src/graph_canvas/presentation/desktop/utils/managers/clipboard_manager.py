"""
Manages clipboard operations for graph elements.
"""

from typing import List, Dict, Any, Set, Optional
import wx

import graph_canvas.presentation.desktop.models.graph as m_graph
import graph_canvas.presentation.desktop.models.node as m_node
import graph_canvas.presentation.desktop.models.edge as m_edge
from graph_canvas.presentation.desktop.utils.commands import PasteCommand, DeleteNodeCommand, DeleteEdgeCommand, CompositeCommand


class ClipboardManager:
    """Manages clipboard operations for graph elements."""
    
    def __init__(self):
        """Initialize clipboard manager."""
        self.clipboard_nodes: List[Dict[str, Any]] = []  # List of node dictionaries
        self.clipboard_edges: List[Dict[str, Any]] = []  # List of edge dictionaries
    
    def copy_selection(self, graph: m_graph.Graph) -> None:
        """Copy selected items to clipboard."""
        print("COPY operation started")
        selected_nodes = graph.get_selected_nodes()
        selected_edges = graph.get_selected_edges()
        
        print(f"DEBUG: Found {len(selected_nodes)} selected nodes:")
        for node in selected_nodes:
            print(f"  - Node {node.id}: {node.text}")
            
        print(f"DEBUG: Found {len(selected_edges)} selected edges:")
        for edge in selected_edges:
            print(f"  - Edge {edge.id}: {edge.source_id} -> {edge.target_id} ('{edge.text}')")
            
        print(f"Copying {len(selected_nodes)} nodes and {len(selected_edges)} edges")
        
        # Clear clipboard
        self.clipboard_nodes = []
        self.clipboard_edges = []
        
        # Build a set of all nodes that need to be copied (selected nodes + nodes connected to selected edges)
        nodes_to_copy = set()
        
        # Add explicitly selected nodes
        for node in selected_nodes:
            nodes_to_copy.add(node.id)
        
        # Add nodes connected to selected edges
        for edge in selected_edges:
            source_node = graph.get_node(edge.source_id)
            target_node = graph.get_node(edge.target_id)
            
            if source_node:
                nodes_to_copy.add(source_node.id)
                print(f"DEBUG: Auto-adding source node {source_node.id} for edge {edge.id}")
            if target_node:
                nodes_to_copy.add(target_node.id)
                print(f"DEBUG: Auto-adding target node {target_node.id} for edge {edge.id}")
        
        print(f"DEBUG: Final nodes to copy: {nodes_to_copy}")
        
        # Copy all required nodes
        for node_id in nodes_to_copy:
            node = graph.get_node(node_id)
            if node:
                self.clipboard_nodes.append(node.to_dict())
        
        # Copy all selected edges (now we know all required nodes are included)
        print(f"DEBUG: Selected edges: {[edge.id for edge in selected_edges]}")
        
        for edge in selected_edges:
            print(f"DEBUG: Copying edge {edge.id}: {edge.source_id} -> {edge.target_id}")
            self.clipboard_edges.append(edge.to_dict())
        
        print(f"Copied {len(self.clipboard_nodes)} nodes and {len(self.clipboard_edges)} edges to clipboard")
    
    def cut_selection(self, graph: m_graph.Graph, undo_redo_manager=None) -> None:
        """Cut selected items (copy then delete)."""
        print("CUT operation started")
        self.copy_selection(graph)
        
        # Delete using undo system
        selected_nodes = graph.get_selected_nodes()
        selected_edges = graph.get_selected_edges()
        
        if selected_nodes or selected_edges:
            # Create composite command for multiple deletions
            commands = []
            
            # Add delete commands for selected edges first (to avoid orphaned edges)
            for edge in selected_edges:
                commands.append(DeleteEdgeCommand(graph, edge.id))
            
            # Add delete commands for selected nodes
            for node in selected_nodes:
                commands.append(DeleteNodeCommand(graph, node.id))
            
            if commands:
                composite_command = CompositeCommand("Cut Selection", commands)
                if undo_redo_manager:
                    undo_redo_manager.execute_command(composite_command)
                else:
                    # Fallback if no undo manager
                    for edge in selected_edges:
                        graph.remove_edge(edge.id)
                    for node in selected_nodes:
                        graph.remove_node(node.id)
    
    def paste_selection(self, graph: m_graph.Graph, undo_redo_manager=None, offset: tuple=(50, 50)) -> None:
        """Paste items from clipboard."""
        print("PASTE operation started")
        if not self.clipboard_nodes:
            print("Nothing to paste")
            return
        
        # Use undo system for paste
        paste_command = PasteCommand(graph, self.clipboard_nodes, self.clipboard_edges, paste_offset=offset)
        
        if undo_redo_manager:
            undo_redo_manager.execute_command(paste_command)
        else:
            # Fallback if no undo manager
            paste_command.execute()
        
        print(f"Pasted {len(self.clipboard_nodes)} nodes and {len(self.clipboard_edges)} edges successfully")
    
    def has_data(self) -> bool:
        """Check if clipboard has data to paste."""
        return bool(self.clipboard_nodes)
