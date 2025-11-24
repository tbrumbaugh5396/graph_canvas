"""
Selection manager for handling graph selection behavior.
"""

from typing import Set, List, Optional, Tuple, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass
import wx

if TYPE_CHECKING:
    from graph_canvas.presentation.desktop.models.node import Node
    from graph_canvas.presentation.desktop.models.edge import Edge
    from graph_canvas.presentation.desktop.models.graph import Graph
    from graph_canvas.presentation.desktop.gui.graph_canvas import GraphCanvas


@dataclass
class SelectionArea:
    """Represents a rectangular selection area."""
    start_x: float
    start_y: float
    end_x: float
    end_y: float
    
    @property
    def left(self) -> float:
        return min(self.start_x, self.end_x)
        
    @property
    def right(self) -> float:
        return max(self.start_x, self.end_x)
        
    @property
    def top(self) -> float:
        return min(self.start_y, self.end_y)
        
    @property
    def bottom(self) -> float:
        return max(self.start_y, self.end_y)
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is inside the selection area."""
        return (self.left <= x <= self.right and 
                self.top <= y <= self.bottom)


class SelectionManager:
    """Manages graph selection state and operations."""
    
    def __init__(self, canvas: 'GraphCanvas'):
        self.canvas = canvas
        self.selected_nodes: Set[str] = set()  # node IDs
        self.selected_edges: Set[str] = set()  # edge IDs
        self.selection_area: Optional[SelectionArea] = None
        self.drag_start: Optional[Tuple[float, float]] = None
        self.last_clicked_node: Optional[str] = None
        self.last_clicked_edge: Optional[str] = None
        
        # Selection settings
        self.allow_multiple = True  # Allow multiple selections
        self.select_contained_only = False  # True = fully contained, False = intersect
        self.auto_select_connected = False  # Auto-select connected nodes/edges
        
        # Bind to canvas events
        self._bind_events()
    
    def _bind_events(self):
        """Bind to relevant canvas events."""
        self.canvas.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.canvas.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        self.canvas.Bind(wx.EVT_MOTION, self.on_mouse_move)
        self.canvas.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
    
    def on_left_down(self, event):
        """Handle left mouse button down."""
        x, y = self.canvas.screen_to_world(event.GetX(), event.GetY())
        
        # Start potential area selection
        self.drag_start = (x, y)
        self.selection_area = None
        
        # Check for node/edge clicks
        node = self.canvas.find_node_at(x, y)
        edge = self.canvas.find_edge_at(x, y)
        
        if node:
            self.handle_node_click(node.id, event.ControlDown(), event.ShiftDown())
        elif edge:
            self.handle_edge_click(edge.id, event.ControlDown(), event.ShiftDown())
        elif not event.ControlDown() and not event.ShiftDown():
            self.clear_selection()
            
        event.Skip()
    
    def on_left_up(self, event):
        """Handle left mouse button up."""
        if self.selection_area:
            self.finalize_area_selection(event.ControlDown(), event.ShiftDown())
        self.drag_start = None
        self.selection_area = None
        event.Skip()
    
    def on_mouse_move(self, event):
        """Handle mouse movement."""
        if event.Dragging() and self.drag_start:
            x, y = self.canvas.screen_to_world(event.GetX(), event.GetY())
            start_x, start_y = self.drag_start
            self.selection_area = SelectionArea(start_x, start_y, x, y)
            self.canvas.Refresh()  # Redraw to show selection area
        event.Skip()
    
    def on_key_down(self, event):
        """Handle key events."""
        key_code = event.GetKeyCode()
        
        if key_code == ord('A') and event.ControlDown():
            self.select_all()
        elif key_code == wx.WXK_ESCAPE:
            self.clear_selection()
            
        event.Skip()
    
    def handle_node_click(self, node_id: str, ctrl: bool, shift: bool):
        """Handle node click with modifier keys."""
        if not self.allow_multiple or (not ctrl and not shift):
            self.clear_selection()
            
        if shift and self.last_clicked_node:
            # Select path between nodes
            self.select_path(self.last_clicked_node, node_id)
        else:
            if node_id in self.selected_nodes:
                self.deselect_node(node_id)
            else:
                self.select_node(node_id)
                
        self.last_clicked_node = node_id
    
    def handle_edge_click(self, edge_id: str, ctrl: bool, shift: bool):
        """Handle edge click with modifier keys."""
        if not self.allow_multiple or (not ctrl and not shift):
            self.clear_selection()
            
        if edge_id in self.selected_edges:
            self.deselect_edge(edge_id)
        else:
            self.select_edge(edge_id)
            
        self.last_clicked_edge = edge_id
    
    def finalize_area_selection(self, ctrl: bool, shift: bool):
        """Finalize area selection with modifier keys."""
        if not self.selection_area:
            return
            
        if not self.allow_multiple or (not ctrl and not shift):
            self.clear_selection()
            
        # Find nodes and edges in selection area
        for node in self.canvas.graph.get_all_nodes():
            if self.selection_area.contains_point(node.x, node.y):
                self.select_node(node.id)
                
        for edge in self.canvas.graph.get_all_edges():
            # Check if edge intersects selection area
            if not self.select_contained_only:
                if self._edge_intersects_area(edge, self.selection_area):
                    self.select_edge(edge.id)
    
    def _edge_intersects_area(self, edge: 'Edge', area: SelectionArea) -> bool:
        """Check if an edge intersects with the selection area."""
        # Get edge endpoints
        source = self.canvas.graph.get_node(edge.source_id)
        target = self.canvas.graph.get_node(edge.target_id)
        if not source or not target:
            return False
            
        # Check if either endpoint is in area
        if (area.contains_point(source.x, source.y) or 
            area.contains_point(target.x, target.y)):
            return True
            
        # Check if edge line intersects area bounds
        # (simplified - just check if line intersects area bounds)
        return self._line_intersects_rect(
            source.x, source.y, target.x, target.y,
            area.left, area.top, area.right, area.bottom
        )
    
    def _line_intersects_rect(self, x1: float, y1: float, x2: float, y2: float,
                            left: float, top: float, right: float, bottom: float) -> bool:
        """Check if a line segment intersects a rectangle."""
        # Cohen-Sutherland algorithm for line clipping
        INSIDE = 0  # 0000
        LEFT = 1    # 0001
        RIGHT = 2   # 0010
        BOTTOM = 4  # 0100
        TOP = 8     # 1000
        
        def compute_code(x: float, y: float) -> int:
            code = INSIDE
            if x < left:
                code |= LEFT
            elif x > right:
                code |= RIGHT
            if y < top:
                code |= TOP
            elif y > bottom:
                code |= BOTTOM
            return code
        
        code1 = compute_code(x1, y1)
        code2 = compute_code(x2, y2)
        
        while True:
            if not (code1 | code2):  # Both points inside
                return True
            if code1 & code2:  # Both points on same side
                return False
                
            # Get point outside rectangle
            code = code1 if code1 else code2
            
            # Find intersection point
            if code & TOP:
                x = x1 + (x2 - x1) * (top - y1) / (y2 - y1)
                y = top
            elif code & BOTTOM:
                x = x1 + (x2 - x1) * (bottom - y1) / (y2 - y1)
                y = bottom
            elif code & RIGHT:
                y = y1 + (y2 - y1) * (right - x1) / (x2 - x1)
                x = right
            else:  # code & LEFT
                y = y1 + (y2 - y1) * (left - x1) / (x2 - x1)
                x = left
                
            # Replace point outside rectangle
            if code == code1:
                x1, y1 = x, y
                code1 = compute_code(x1, y1)
            else:
                x2, y2 = x, y
                code2 = compute_code(x2, y2)
    
    def select_node(self, node_id: str):
        """Select a node and optionally connected elements."""
        if node_id not in self.selected_nodes:
            self.selected_nodes.add(node_id)
            if self.auto_select_connected:
                self._select_connected(node_id)
            self._notify_selection_changed()
    
    def deselect_node(self, node_id: str):
        """Deselect a node and optionally connected elements."""
        if node_id in self.selected_nodes:
            self.selected_nodes.remove(node_id)
            if self.auto_select_connected:
                self._deselect_connected(node_id)
            self._notify_selection_changed()
    
    def select_edge(self, edge_id: str):
        """Select an edge."""
        if edge_id not in self.selected_edges:
            self.selected_edges.add(edge_id)
            self._notify_selection_changed()
    
    def deselect_edge(self, edge_id: str):
        """Deselect an edge."""
        if edge_id in self.selected_edges:
            self.selected_edges.remove(edge_id)
            self._notify_selection_changed()
    
    def select_all(self):
        """Select all nodes and edges."""
        for node in self.canvas.graph.get_all_nodes():
            self.selected_nodes.add(node.id)
        for edge in self.canvas.graph.get_all_edges():
            self.selected_edges.add(edge.id)
        self._notify_selection_changed()
    
    def clear_selection(self):
        """Clear all selections."""
        if self.selected_nodes or self.selected_edges:
            self.selected_nodes.clear()
            self.selected_edges.clear()
            self._notify_selection_changed()
    
    def select_path(self, start_node_id: str, end_node_id: str):
        """Select all nodes and edges in the shortest path between two nodes."""
        path = self.canvas.graph.find_shortest_path(start_node_id, end_node_id)
        if path:
            for node_id in path:
                self.select_node(node_id)
            for i in range(len(path) - 1):
                edge = self.canvas.graph.find_edge(path[i], path[i + 1])
                if edge:
                    self.select_edge(edge.id)
    
    def _select_connected(self, node_id: str):
        """Select nodes and edges connected to the given node."""
        node = self.canvas.graph.get_node(node_id)
        if not node:
            return
            
        # Select connected edges
        for edge in self.canvas.graph.get_node_edges(node_id):
            self.select_edge(edge.id)
            # Select nodes at other end of edges
            other_node_id = edge.target_id if edge.source_id == node_id else edge.source_id
            self.select_node(other_node_id)
    
    def _deselect_connected(self, node_id: str):
        """Deselect nodes and edges connected to the given node."""
        node = self.canvas.graph.get_node(node_id)
        if not node:
            return
            
        # Deselect connected edges
        for edge in self.canvas.graph.get_node_edges(node_id):
            self.deselect_edge(edge.id)
            # Deselect nodes at other end of edges
            other_node_id = edge.target_id if edge.source_id == node_id else edge.source_id
            self.deselect_node(other_node_id)
    
    def _notify_selection_changed(self):
        """Notify canvas that selection has changed."""
        self.canvas.Refresh()  # Redraw with new selection
        # Emit custom event if needed
        event = wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED)
        event.SetEventType(wx.NewEventType())  # Custom event type
        wx.PostEvent(self.canvas, event)
    
    def get_selected_nodes(self) -> List['Node']:
        """Get list of selected nodes."""
        return [self.canvas.graph.get_node(node_id) 
                for node_id in self.selected_nodes
                if self.canvas.graph.get_node(node_id)]
    
    def get_selected_edges(self) -> List['Edge']:
        """Get list of selected edges."""
        return [self.canvas.graph.get_edge(edge_id) 
                for edge_id in self.selected_edges
                if self.canvas.graph.get_edge(edge_id)]
    
    def has_selection(self) -> bool:
        """Check if anything is selected."""
        return bool(self.selected_nodes or self.selected_edges)
    
    def save_state(self) -> Dict[str, Any]:
        """Save selection state."""
        return {
            'selected_nodes': list(self.selected_nodes),
            'selected_edges': list(self.selected_edges),
            'allow_multiple': self.allow_multiple,
            'select_contained_only': self.select_contained_only,
            'auto_select_connected': self.auto_select_connected
        }
    
    def load_state(self, state: Dict[str, Any]):
        """Load selection state."""
        self.clear_selection()
        self.selected_nodes = set(state.get('selected_nodes', []))
        self.selected_edges = set(state.get('selected_edges', []))
        self.allow_multiple = state.get('allow_multiple', True)
        self.select_contained_only = state.get('select_contained_only', False)
        self.auto_select_connected = state.get('auto_select_connected', False)
        self._notify_selection_changed()
