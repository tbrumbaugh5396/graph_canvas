"""
File manager for handling graph file operations and formats.
"""

import os
import json
import time
from typing import List, Dict, Optional, Any, Tuple, TYPE_CHECKING
from dataclasses import dataclass
import wx

if TYPE_CHECKING:
    from graph_canvas.presentation.desktop.gui.main_window import MainWindow
    from graph_canvas.presentation.desktop.models.graph import Graph


@dataclass
class FileFormat:
    """Represents a supported file format."""
    name: str
    extensions: List[str]
    can_read: bool = True
    can_write: bool = True
    
    @property
    def wildcard(self) -> str:
        """Get wildcard string for file dialog."""
        ext_list = ";".join(f"*.{ext}" for ext in self.extensions)
        return f"{self.name} ({ext_list})|{ext_list}"


class FileManager:
    """Manages file operations and format support."""
    
    def __init__(self, main_window: 'MainWindow'):
        self.main_window = main_window
        self.recent_files: List[str] = []
        self.max_recent = 10
        self.autosave_interval = 300  # 5 minutes
        self.last_autosave = time.time()
        self.config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'files.json')
        
        # Create config directory if it doesn't exist
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        
        # Define supported formats
        self.formats: Dict[str, FileFormat] = {
            'graph': FileFormat("Graph files", ["graph"]),
            'dot': FileFormat("DOT files", ["dot", "gv"]),
            'json': FileFormat("JSON files", ["json"]),
            'txt': FileFormat("Text files", ["txt"], can_write=True, can_read=False)
        }
        
        # Load recent files
        self.load_recent_files()
        
        # Start autosave timer
        self.autosave_timer = wx.Timer(self.main_window)
        self.main_window.Bind(
            wx.EVT_TIMER,
            self.on_autosave_timer,
            self.autosave_timer
        )
        self.autosave_timer.Start(60000)  # Check every minute
    
    def get_save_wildcard(self) -> str:
        """Get wildcard string for save dialog."""
        wildcards = [fmt.wildcard for fmt in self.formats.values() if fmt.can_write]
        return "|".join(wildcards)
    
    def get_open_wildcard(self) -> str:
        """Get wildcard string for open dialog."""
        wildcards = [fmt.wildcard for fmt in self.formats.values() if fmt.can_read]
        return "|".join(wildcards)
    
    def new_graph(self) -> bool:
        """Create a new graph."""
        if self.check_unsaved_changes():
            self.main_window.current_graph = self.main_window.graph_class()
            self.main_window.current_graph.modified = False
            self.main_window.SetTitle("Graph Editor - Untitled Graph")
            self.main_window.canvas.Refresh()
            return True
        return False
    
    def open_graph(self, filepath: Optional[str] = None) -> bool:
        """Open a graph from file."""
        if not self.check_unsaved_changes():
            return False
            
        if filepath is None:
            with wx.FileDialog(
                self.main_window, "Open Graph",
                wildcard=self.get_open_wildcard(),
                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
            ) as dialog:
                if dialog.ShowModal() == wx.ID_CANCEL:
                    return False
                filepath = dialog.GetPath()
        
        try:
            ext = os.path.splitext(filepath)[1].lower()[1:]
            format_name = next(
                (name for name, fmt in self.formats.items()
                 if ext in fmt.extensions and fmt.can_read),
                None
            )
            
            if not format_name:
                raise ValueError(f"Unsupported file format: .{ext}")
            
            if format_name == 'graph':
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    graph = self.main_window.graph_class.from_dict(data)
            elif format_name == 'dot':
                from graph_canvas.presentation.desktop.file_io.dot_format import read_dot
                graph = read_dot(filepath)
            elif format_name == 'json':
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    graph = self.main_window.graph_class.from_dict(data)
            
            self.main_window.current_graph = graph
            self.main_window.current_graph.file_path = filepath
            self.main_window.current_graph.modified = False
            self.main_window.SetTitle(f"Graph Editor - {os.path.basename(filepath)}")
            self.main_window.canvas.Refresh()
            
            self.add_recent_file(filepath)
            return True
            
        except Exception as e:
            wx.MessageBox(
                f"Error opening file: {str(e)}",
                "Error",
                wx.OK | wx.ICON_ERROR
            )
            return False
    
    def save_graph(self, filepath: Optional[str] = None) -> bool:
        """Save current graph to file."""
        if not filepath:
            filepath = self.main_window.current_graph.file_path
        
        if not filepath:
            return self.save_graph_as()
        
        try:
            ext = os.path.splitext(filepath)[1].lower()[1:]
            format_name = next(
                (name for name, fmt in self.formats.items()
                 if ext in fmt.extensions and fmt.can_write),
                None
            )
            
            if not format_name:
                raise ValueError(f"Unsupported file format: .{ext}")
            
            if format_name == 'graph':
                with open(filepath, 'w') as f:
                    json.dump(self.main_window.current_graph.to_dict(), f, indent=2)
            elif format_name == 'dot':
                from graph_canvas.presentation.desktop.file_io.dot_format import write_dot
                write_dot(self.main_window.current_graph, filepath)
            elif format_name == 'json':
                with open(filepath, 'w') as f:
                    json.dump(self.main_window.current_graph.to_dict(), f, indent=2)
            elif format_name == 'txt':
                with open(filepath, 'w') as f:
                    f.write(str(self.main_window.current_graph))
            
            self.main_window.current_graph.file_path = filepath
            self.main_window.current_graph.modified = False
            self.main_window.SetTitle(f"Graph Editor - {os.path.basename(filepath)}")
            
            self.add_recent_file(filepath)
            return True
            
        except Exception as e:
            wx.MessageBox(
                f"Error saving file: {str(e)}",
                "Error",
                wx.OK | wx.ICON_ERROR
            )
            return False
    
    def save_graph_as(self) -> bool:
        """Save current graph with a new name."""
        with wx.FileDialog(
            self.main_window, "Save Graph As",
            wildcard=self.get_save_wildcard(),
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        ) as dialog:
            if dialog.ShowModal() == wx.ID_CANCEL:
                return False
            return self.save_graph(dialog.GetPath())
    
    def import_graph(self, filepath: Optional[str] = None) -> bool:
        """Import another graph into current."""
        if filepath is None:
            with wx.FileDialog(
                self.main_window, "Import Graph",
                wildcard=self.get_open_wildcard(),
                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
            ) as dialog:
                if dialog.ShowModal() == wx.ID_CANCEL:
                    return False
                filepath = dialog.GetPath()
        
        try:
            ext = os.path.splitext(filepath)[1].lower()[1:]
            format_name = next(
                (name for name, fmt in self.formats.items()
                 if ext in fmt.extensions and fmt.can_read),
                None
            )
            
            if not format_name:
                raise ValueError(f"Unsupported file format: .{ext}")
            
            if format_name == 'graph':
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    imported_graph = self.main_window.graph_class.from_dict(data)
            elif format_name == 'dot':
                from graph_canvas.presentation.desktop.file_io.dot_format import read_dot
                imported_graph = read_dot(filepath)
            elif format_name == 'json':
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    imported_graph = self.main_window.graph_class.from_dict(data)
            
            # Merge imported graph into current
            for node in imported_graph.get_all_nodes():
                if node.id not in self.main_window.current_graph.nodes:
                    self.main_window.current_graph.add_node(node)
            
            for edge in imported_graph.get_all_edges():
                if edge.id not in self.main_window.current_graph.edges:
                    self.main_window.current_graph.add_edge(edge)
            
            self.main_window.current_graph.modified = True
            self.main_window.canvas.Refresh()
            return True
            
        except Exception as e:
            wx.MessageBox(
                f"Error importing file: {str(e)}",
                "Error",
                wx.OK | wx.ICON_ERROR
            )
            return False
    
    def check_unsaved_changes(self) -> bool:
        """Check for unsaved changes. Returns True if ok to proceed."""
        if self.main_window.current_graph.modified:
            dialog = wx.MessageDialog(
                self.main_window,
                "Current graph has unsaved changes. Save before proceeding?",
                "Save Changes?",
                wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION
            )
            result = dialog.ShowModal()
            dialog.Destroy()
            
            if result == wx.ID_CANCEL:
                return False
            elif result == wx.ID_YES:
                return self.save_graph()
        return True
    
    def add_recent_file(self, filepath: str):
        """Add a file to recent files list."""
        if filepath in self.recent_files:
            self.recent_files.remove(filepath)
        self.recent_files.insert(0, filepath)
        while len(self.recent_files) > self.max_recent:
            self.recent_files.pop()
        self.save_recent_files()
        self.update_recent_menu()
    
    def clear_recent_files(self):
        """Clear recent files list."""
        self.recent_files.clear()
        self.save_recent_files()
        self.update_recent_menu()
    
    def update_recent_menu(self):
        """Update recent files menu."""
        # Obtain or lazily create the recent files submenu to avoid attribute errors
        menu = getattr(self.main_window, 'recent_menu', None)
        if menu is None:
            try:
                import wx  # local import to avoid issues in headless contexts
                menubar = getattr(self.main_window, 'GetMenuBar', lambda: None)()
                if menubar:
                    # Try common labels for File menu
                    file_index = menubar.FindMenu("File")
                    if getattr(wx, 'NOT_FOUND', -1) == file_index:
                        file_index = menubar.FindMenu("&File")
                    if file_index != getattr(wx, 'NOT_FOUND', -1):
                        file_menu = menubar.GetMenu(file_index)
                        menu = wx.Menu()
                        file_menu.AppendSubMenu(menu, "&Recent Files", "Recently opened files")
                        # Cache on main_window for subsequent updates
                        setattr(self.main_window, 'recent_menu', menu)
            except Exception:
                menu = None
        if not menu:
            return
            
        # Clear existing items
        while menu.GetMenuItemCount() > 0:
            menu.Delete(menu.FindItemByPosition(0))
        
        # Add recent files
        for i, filepath in enumerate(self.recent_files):
            if os.path.exists(filepath):
                item = menu.Append(
                    wx.ID_ANY,
                    f"&{i+1}. {os.path.basename(filepath)}",
                    filepath
                )
                self.main_window.Bind(
                    wx.EVT_MENU,
                    lambda evt, path=filepath: self.open_graph(path),
                    item
                )
        
        if menu.GetMenuItemCount() > 0:
            menu.AppendSeparator()
        
        # Add clear menu item
        clear_item = menu.Append(wx.ID_ANY, "Clear Recent Files")
        self.main_window.Bind(
            wx.EVT_MENU,
            lambda evt: self.clear_recent_files(),
            clear_item
        )
    
    def save_recent_files(self):
        """Save recent files list to config."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump({
                    'recent_files': self.recent_files,
                    'max_recent': self.max_recent,
                    'autosave_interval': self.autosave_interval
                }, f, indent=4)
        except Exception as e:
            print(f"Error saving recent files: {e}")
    
    def load_recent_files(self):
        """Load recent files list from config."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.recent_files = data.get('recent_files', [])
                    self.max_recent = data.get('max_recent', 10)
                    self.autosave_interval = data.get('autosave_interval', 300)
        except Exception as e:
            print(f"Error loading recent files: {e}")
    
    def on_autosave_timer(self, event):
        """Handle autosave timer event."""
        now = time.time()
        if (now - self.last_autosave >= self.autosave_interval and
            self.main_window.current_graph.modified):
            self.autosave()
        event.Skip()
    
    def autosave(self):
        """Perform autosave."""
        if not self.main_window.current_graph.file_path:
            return
            
        autosave_path = self.main_window.current_graph.file_path + '.autosave'
        try:
            with open(autosave_path, 'w') as f:
                json.dump(self.main_window.current_graph.to_dict(), f, indent=2)
            self.last_autosave = time.time()
        except Exception as e:
            print(f"Error during autosave: {e}")
    
    def check_for_autosave(self, filepath: str) -> Optional[str]:
        """Check for and handle autosave file."""
        autosave_path = filepath + '.autosave'
        if os.path.exists(autosave_path):
            dialog = wx.MessageDialog(
                self.main_window,
                "An autosave file exists. Would you like to recover it?",
                "Recover Autosave?",
                wx.YES_NO | wx.ICON_QUESTION
            )
            if dialog.ShowModal() == wx.ID_YES:
                return autosave_path
            else:
                try:
                    os.remove(autosave_path)
                except Exception as e:
                    print(f"Error removing autosave file: {e}")
        return None
