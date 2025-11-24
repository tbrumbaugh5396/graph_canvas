"""
Command pattern implementation for undo/redo functionality.
"""


from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import copy


class Command(ABC):
    """Base class for all commands that can be undone/redone."""
    
    def __init__(self, description: str):
        self.description = description
    
    @abstractmethod
    def execute(self) -> None:
        """Execute the command."""

        pass
    
    @abstractmethod
    def undo(self) -> None:
        """Undo the command."""

        pass
    
    def __str__(self) -> str:
        return self.description


class AddNodeCommand(Command):
    """Command to add a node to the graph."""
    
    def __init__(self, graph, node):
        super().__init__(f"Add Node: {node.text}")
        self.graph = graph
        self.node = node
        self.node_data = node.to_dict()
    
    def execute(self) -> None:
        """Add the node to the graph."""

        self.graph.add_node(self.node)
    
    def undo(self) -> None:
        """Remove the node from the graph."""

        self.graph.remove_node(self.node.id)


class DeleteNodeCommand(Command):
    """Command to delete a node from the graph."""
    
    def __init__(self, graph, node_id):
        super().__init__(f"Delete Node")
        self.graph = graph
        self.node_id = node_id
        # Store node data and connected edges for restoration
        self.node = self.graph.get_node(node_id)
        self.node_data = self.node.to_dict() if self.node else None
        self.connected_edges = []
        
        # Store all edges connected to this node
        for edge in self.graph.get_all_edges():
            if edge.source_id == node_id or edge.target_id == node_id:
                self.connected_edges.append(edge.to_dict())
    
    def execute(self) -> None:
        """Remove the node and its connected edges."""

        self.graph.remove_node(self.node_id)
    
    def undo(self) -> None:
        """Restore the node and its connected edges."""

        if self.node_data:
            from graph_canvas.presentation.desktop.models.node import Node
            from graph_canvas.presentation.desktop.models.edge import Edge
            
            # Restore the node
            restored_node = Node.from_dict(self.node_data)
            self.graph.add_node(restored_node)
            
            # Restore connected edges
            for edge_data in self.connected_edges:
                restored_edge = Edge.from_dict(edge_data)
                self.graph.add_edge(restored_edge)


class MoveNodeCommand(Command):
    """Command to move a node."""
    
    def __init__(self, graph, node_id, old_pos, new_pos):
        super().__init__(f"Move Node")
        self.graph = graph
        self.node_id = node_id
        self.old_pos = old_pos
        self.new_pos = new_pos
    
    def execute(self) -> None:
        """Move the node to new position."""

        node = self.graph.get_node(self.node_id)
        if node:
            node.x, node.y = self.new_pos
    
    def undo(self) -> None:
        """Move the node back to old position."""

        node = self.graph.get_node(self.node_id)
        if node:
            node.x, node.y = self.old_pos


class AddEdgeCommand(Command):
    """Command to add an edge to the graph."""
    
    def __init__(self, graph, edge):
        super().__init__(f"Add Edge")
        self.graph = graph
        self.edge = edge
        self.edge_data = edge.to_dict()
    
    def execute(self) -> None:
        """Add the edge to the graph."""

        self.graph.add_edge(self.edge)
    
    def undo(self) -> None:
        """Remove the edge from the graph."""

        self.graph.remove_edge(self.edge.id)


class DeleteEdgeCommand(Command):
    """Command to delete an edge from the graph."""
    
    def __init__(self, graph, edge_id):
        super().__init__(f"Delete Edge")
        self.graph = graph
        self.edge_id = edge_id
        self.edge = self.graph.get_edge(edge_id)
        self.edge_data = self.edge.to_dict() if self.edge else None
    
    def execute(self) -> None:
        """Remove the edge from the graph."""

        self.graph.remove_edge(self.edge_id)
    
    def undo(self) -> None:
        """Restore the edge to the graph."""

        if self.edge_data:
            from graph_canvas.presentation.desktop.models.edge import Edge
            restored_edge = Edge.from_dict(self.edge_data)
            self.graph.add_edge(restored_edge)


class ChangeEdgeConnectionCommand(Command):
    """Command to change edge connection (dragging endpoints)."""
    
    def __init__(self, graph, edge_id, old_source_id, old_target_id, new_source_id, new_target_id):
        super().__init__(f"Reconnect Edge")
        self.graph = graph
        self.edge_id = edge_id
        self.old_source_id = old_source_id
        self.old_target_id = old_target_id
        self.new_source_id = new_source_id
        self.new_target_id = new_target_id
    
    def execute(self) -> None:
        """Apply the new connection."""

        edge = self.graph.get_edge(self.edge_id)
        if edge:
            edge.source_id = self.new_source_id
            edge.target_id = self.new_target_id
    
    def undo(self) -> None:
        """Restore the old connection."""

        edge = self.graph.get_edge(self.edge_id)
        if edge:
            edge.source_id = self.old_source_id
            edge.target_id = self.old_target_id


class EditPropertiesCommand(Command):
    """Command to edit object properties."""
    
    def __init__(self, obj, old_properties, new_properties, description):
        super().__init__(description)
        self.obj = obj
        self.old_properties = copy.deepcopy(old_properties)
        self.new_properties = copy.deepcopy(new_properties)
    
    def execute(self) -> None:
        """Apply the new properties."""

        for key, value in self.new_properties.items():
            setattr(self.obj, key, value)
    
    def undo(self) -> None:
        """Restore the old properties."""

        for key, value in self.old_properties.items():
            setattr(self.obj, key, value)


class ChangeColorCommand(Command):
    """Command to change canvas colors."""
    
    def __init__(self, canvas, color_type, old_color, new_color):
        super().__init__(f"Change {color_type} Color")
        self.canvas = canvas
        self.color_type = color_type  # 'background' or 'grid'
        self.old_color = old_color
        self.new_color = new_color
    
    def execute(self) -> None:
        """Apply the new color."""

        import wx
        if self.color_type == 'background':
            self.canvas.background_color = self.new_color
            self.canvas.SetBackgroundColour(wx.Colour(*self.new_color))
        elif self.color_type == 'grid':
            self.canvas.grid_color = self.new_color
        self.canvas.Refresh()
    
    def undo(self) -> None:
        """Restore the old color."""

        import wx
        if self.color_type == 'background':
            self.canvas.background_color = self.old_color
            self.canvas.SetBackgroundColour(wx.Colour(*self.old_color))
        elif self.color_type == 'grid':
            self.canvas.grid_color = self.old_color
        self.canvas.Refresh()


class PasteCommand(Command):
    """Command to paste nodes and edges from clipboard."""
    
    def __init__(self, graph, clipboard_nodes, clipboard_edges, paste_offset=(50, 50)):
        super().__init__(f"Paste {len(clipboard_nodes)} nodes and {len(clipboard_edges)} edges")
        self.graph = graph
        self.clipboard_nodes = clipboard_nodes.copy()
        self.clipboard_edges = clipboard_edges.copy()
        self.paste_offset = paste_offset
        self.pasted_nodes = []
        self.pasted_edges = []
        self.node_id_map = {}
    
    def execute(self) -> None:
        """Paste items from clipboard."""

        from graph_canvas.presentation.desktop.models.node import Node
        from graph_canvas.presentation.desktop.models.edge import Edge
        
        # Clear current selection
        self.graph.clear_selection()
        
        # Create new nodes
        for node_data in self.clipboard_nodes:
            old_id = node_data['id']
            
            # Create new node with offset and new ID
            new_node = Node(
                x=node_data['x'] + self.paste_offset[0],
                y=node_data['y'] + self.paste_offset[1], 
                z=node_data.get('z', 0),
                text=node_data['text'],
                node_id=None,  # Generate new ID
                metadata=node_data.get('metadata', {}).copy()
            )
            
            # Copy visual properties
            for attr in ['width', 'height', 'color', 'text_color', 'border_color', 
                        'border_width', 'font_size', 'visible', 'locked']:
                if attr in node_data:
                    setattr(new_node, attr, node_data[attr])
            
            self.graph.add_node(new_node)
            self.graph.select_node(new_node.id)
            
            self.pasted_nodes.append(new_node.id)
            self.node_id_map[old_id] = new_node.id
        
        # Create new edges
        for edge_data in self.clipboard_edges:
            old_source_id = edge_data['source_id']
            old_target_id = edge_data['target_id']
            
            # Only create edge if both nodes were pasted
            if old_source_id in self.node_id_map and old_target_id in self.node_id_map:
                new_edge = Edge(
                    source_id=self.node_id_map[old_source_id],
                    target_id=self.node_id_map[old_target_id],
                    text=edge_data['text'],
                    edge_id=None,  # Generate new ID
                    metadata=edge_data.get('metadata', {}).copy()
                )
                
                # Copy visual properties
                for attr in ['color', 'width', 'text_color', 'font_size', 'arrow_size',
                           'line_style', 'control_points', 'custom_position', 'visible', 
                           'locked', 'directed']:
                    if attr in edge_data:
                        if attr == 'control_points':
                            setattr(new_edge, attr, edge_data[attr].copy())
                        else:
                            setattr(new_edge, attr, edge_data[attr])
                
                self.graph.add_edge(new_edge)
                self.graph.select_edge(new_edge.id)
                
                self.pasted_edges.append(new_edge.id)
    
    def undo(self) -> None:
        """Remove pasted items."""

        # Remove pasted edges first
        for edge_id in self.pasted_edges:
            self.graph.remove_edge(edge_id)
        
        # Remove pasted nodes
        for node_id in self.pasted_nodes:
            self.graph.remove_node(node_id)


class CompositeCommand(Command):
    """Command that contains multiple sub-commands."""
    
    def __init__(self, description, commands: List[Command]):
        super().__init__(description)
        self.commands = commands
    
    def execute(self) -> None:
        """Execute all sub-commands."""

        for command in self.commands:
            command.execute()
    
    def undo(self) -> None:
        """Undo all sub-commands in reverse order."""

        for command in reversed(self.commands):
            command.undo()


class UndoRedoManager:
    """Manages undo/redo command history."""
    
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.undo_stack: List[Command] = []
        self.redo_stack: List[Command] = []
        self.callbacks = []  # For UI updates
    
    def set_max_history(self, max_history: int):
        """Set the maximum history depth."""

        self.max_history = max_history
        # Trim existing history if needed
        while len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
        while len(self.redo_stack) > self.max_history:
            self.redo_stack.pop(0)
        self._notify_callbacks()
    
    def get_max_history(self) -> int:
        """Get the maximum history depth."""

        return self.max_history
    
    def execute_command(self, command: Command) -> None:
        """Execute a command and add it to the undo stack."""

        command.execute()
        self.undo_stack.append(command)
        
        # Limit stack size
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
        
        # Clear redo stack
        self.redo_stack.clear()
        
        # Notify UI
        self._notify_callbacks()
    
    def undo(self) -> bool:
        """Undo the last command."""

        if not self.undo_stack:
            return False
        
        command = self.undo_stack.pop()
        command.undo()
        self.redo_stack.append(command)
        
        print(f"DEBUG: Undid: {command}")
        self._notify_callbacks()
        return True
    
    def redo(self) -> bool:
        """Redo the last undone command."""

        if not self.redo_stack:
            return False
        
        command = self.redo_stack.pop()
        command.execute()
        self.undo_stack.append(command)
        
        print(f"DEBUG: Redid: {command}")
        self._notify_callbacks()
        return True
    
    def can_undo(self) -> bool:
        """Check if undo is possible."""

        return len(self.undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Check if redo is possible."""

        return len(self.redo_stack) > 0
    
    def get_undo_description(self) -> Optional[str]:
        """Get description of the last undoable command."""

        return self.undo_stack[-1].description if self.undo_stack else None
    
    def get_redo_description(self) -> Optional[str]:
        """Get description of the last redoable command."""

        return self.redo_stack[-1].description if self.redo_stack else None
    
    def clear(self) -> None:
        """Clear all command history."""

        self.undo_stack.clear()
        self.redo_stack.clear()
        self._notify_callbacks()
    
    def add_callback(self, callback) -> None:
        """Add a callback for when the undo/redo state changes."""

        self.callbacks.append(callback)
    
    def _notify_callbacks(self) -> None:
        """Notify all callbacks of state changes."""

        for callback in self.callbacks:
            callback()
