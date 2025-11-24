"""
Undo/Redo manager for the graph editor.
"""


from typing import List, Optional

import graph_canvas.presentation.desktop.utils.commands as m_commands


class UndoRedoManager:
    """Manages undo/redo command history."""
    
    def __init__(self, max_history: Optional[int] = None):
        self.max_history = max_history
        self.undo_stack: List[m_commands.Command] = []
        self.redo_stack: List[m_commands.Command] = []
        self.callbacks = []  # For UI updates
    
    def set_max_history(self, max_history: Optional[int]):
        """Set the maximum history depth."""

        self.max_history = max_history

        if self.max_history is None:
            self._notify_callbacks()
        else:
            # Trim existing history if needed
            while len(self.undo_stack) > self.max_history:
                self.undo_stack.pop(0)
            while len(self.redo_stack) > self.max_history:
                self.redo_stack.pop(0)
            self._notify_callbacks()
    
    def get_max_history(self) -> Optional[int]:
        """Get the maximum history depth."""

        return self.max_history
    
    def execute_command(self, command: m_commands.Command) -> None:
        """Execute a command and add it to the undo stack."""

        command.execute()
        self.undo_stack.append(command)
        
        if self.max_history is None:
            self._notify_callbacks()
        else:
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
