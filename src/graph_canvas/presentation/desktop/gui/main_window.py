"""
Main window for the graph editor application.
"""


import copy
import os
import wx
from typing import Optional, List, Tuple
from graph_canvas.presentation.desktop.utils.meta_graph_information import MetaGraphInformation
from graph_canvas.presentation.desktop.utils.display_settings import DisplaySettings
from functools import partial
from graph_canvas.presentation.desktop.utils.path_helpers import ensure_project_on_path, ensure_mvc_mvu_on_path

# Handle imports for both module and direct execution
import sys

# Ensure paths for both direct execution and package run
ensure_project_on_path(__file__)
ensure_mvc_mvu_on_path()

# MVC_MVU path handled by utils.path_helpers

# Use absolute imports for better compatibility
# event handlers
# -graph canvas
import graph_canvas.presentation.desktop.event_handlers.control_points_and_composite_segments_panel_event_handler as m_control_points_and_composite_segments_panel_event_handler
import graph_canvas.presentation.desktop.event_handlers.graph_canvas_background_event_handler as m_graph_canvas_background_event_handler
import graph_canvas.presentation.desktop.event_handlers.graph_canvas_event_handler as m_graph_canvas_event_handler
import graph_canvas.presentation.desktop.event_handlers.graph_canvas_grid_event_handler as m_graph_canvas_grid_event_handler
import graph_canvas.presentation.desktop.event_handlers.graph_canvas_movement_event_handler as m_graph_canvas_movement_event_handler
import graph_canvas.presentation.desktop.event_handlers.graph_canvas_rotator_event_handler as m_graph_canvas_rotator_event_handler
import graph_canvas.presentation.desktop.event_handlers.graph_canvas_selector_event_handler as m_graph_canvas_selector_event_handler
import graph_canvas.presentation.desktop.event_handlers.graph_canvas_view_manager_event_handler as m_graph_canvas_view_manager_event_handler
import graph_canvas.presentation.desktop.event_handlers.graph_canvas_zoom_event_handler as m_graph_canvas_zoom_event_handler
# -menubar
import graph_canvas.presentation.desktop.event_handlers.menubar_event_handler as m_menubar_event_handler
# -sidebar
import graph_canvas.presentation.desktop.event_handlers.sidebar_event_handler as m_sidebar_event_handler
# -status bar
import graph_canvas.presentation.desktop.event_handlers.status_bar_event_handler as m_status_bar_event_handler
# -theme
import graph_canvas.presentation.desktop.event_handlers.theme_event_handler as m_theme_event_handler
# -tool selector
import graph_canvas.presentation.desktop.event_handlers.tool_selector_event_handler as m_tool_selector_event_handler
import graph_canvas.presentation.desktop.event_handlers.toolbar_event_handler as m_toolbar_event_handler
import graph_canvas.presentation.desktop.event_handlers.undo_redo_event_handler as m_undo_redo_event_handler

# file io 
from graph_canvas.presentation.desktop.file_io.dot_format import save_graph_to_dot, load_graph_from_dot

# gui
import graph_canvas.presentation.desktop.gui.control_points_and_composite_segment_panel as m_control_points_and_composite_segment_panel
import graph_canvas.presentation.desktop.gui.dialogs as m_dialogs
import graph_canvas.presentation.desktop.gui.drawer as m_drawer
import graph_canvas.presentation.desktop.gui.graph_canvas as m_graph_canvas
import graph_canvas.presentation.desktop.gui.layouts as m_layouts
import graph_canvas.presentation.desktop.gui.menubar as m_menubar
import graph_canvas.presentation.desktop.gui.selector as m_selector
import graph_canvas.presentation.desktop.gui.sidebar as m_sidebar
import graph_canvas.presentation.desktop.gui.dependency_list_panel as m_dependency_list_panel
import graph_canvas.presentation.desktop.gui.signal as m_signal
import graph_canvas.presentation.desktop.gui.status_bar as m_status_bar
import graph_canvas.presentation.desktop.gui.theme_dialog as m_theme_dialog
import graph_canvas.presentation.desktop.gui.tool_selector as m_tool_selector
import graph_canvas.presentation.desktop.gui.toolbar as m_toolbar

# models
import graph_canvas.presentation.desktop.models.graph as m_graph
import graph_canvas.presentation.desktop.models.node as m_node
import graph_canvas.presentation.desktop.models.edge as m_edge

# utils
from graph_canvas.presentation.desktop.utils.app_managers import AppManagers
import graph_canvas.presentation.desktop.utils.managers.theme_manager as m_theme_manager
from graph_canvas.presentation.desktop.utils.commands import ChangeColorCommand
import graph_canvas.presentation.desktop.utils.commands as m_commands
from graph_canvas.presentation.desktop.utils.backend_client import BackendClient

# MVU imports
from mvc_mvu.mvc_adapter import MVUAdapter, UIState
from mvc_mvu.messages import make_message
import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu


class MainWindow(wx.Frame):
    """Main application window."""


    def __init__(self):
        super().__init__(None, title="Graph Editor", size=(1200, 800))

        # Make the application fullscreen
        self.Maximize(True)

        # Application state
        self.current_graph = m_graph.Graph()
        self.graphs = {}  # Dictionary of graph_id -> Graph
        self.graphs[self.current_graph.id] = self.current_graph
        self.recent_files = []
        # Backend client
        self.backend = BackendClient()
        
        # Meta graph information (replaces individual fields)
        self.meta_graph_information = MetaGraphInformation()

        # Display settings container
        self.display = DisplaySettings()
        
        # Initialize managers container
        self.managers = AppManagers(self)

        # Set up UI (this creates splitters)
        self.setup_ui()
        
        # Load from backend if available, else local default
        self._maybe_load_from_backend()
        # Update UI state
        self.update_ui()

        # Initialize MVU adapter after UI is ready
        self._init_mvu_adapter()


    def setup_ui(self):
        """Set up the main UI layout."""

        # Create vertical splitter for main area and status bar
        self.vertical_splitter = wx.SplitterWindow(self, style=wx.SP_3D | wx.SP_LIVE_UPDATE)
        self.vertical_splitter.SetMinimumPaneSize(100)  # Minimum height for status bar
        
        # Create main panel
        self.main_panel = wx.Panel(self.vertical_splitter)
        self.main_panel.SetBackgroundColour(self.display.background_color)  # White background

        # Create horizontal splitter for canvas and sidebar
        self.horizontal_splitter = wx.SplitterWindow(self.main_panel, style=wx.SP_3D | wx.SP_LIVE_UPDATE)
        self.horizontal_splitter.SetMinimumPaneSize(200)  # Minimum width for sidebar

        # Create canvas
        self.canvas = m_graph_canvas.GraphCanvas(self.horizontal_splitter, self.current_graph, self.managers.undo_redo_manager)

        # Set up bidirectional reference for UI updates
        self.canvas.main_window = self

        # Initialize canvas restrictions
        self.canvas.meta_graph_information = self.meta_graph_information
        self.canvas.display = self.display

        # Create sidebar
        m_sidebar.setup_sidebar(self)

        # Set up horizontal splitter
        self.horizontal_splitter.SplitVertically(self.canvas, self.sidebar, -250)  # -250 means 250px from right
        
        # Create status panel
        self.status_panel = wx.Panel(self.vertical_splitter)
        self.status_panel.SetBackgroundColour(self.display.status_panel_background_color)
        status_sizer = wx.BoxSizer(wx.VERTICAL)
        self.status_panel.SetSizer(status_sizer)

        # Set up vertical splitter
        self.vertical_splitter.SplitHorizontally(self.main_panel, self.status_panel, -150)  # -150 means 150px from bottom
        
        # Initialize panel visibility state
        self.sidebar_visible = True
        self.status_bar_visible = True
        
        # Bind splitter events for drag-to-collapse functionality
        self.horizontal_splitter.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.on_horizontal_splitter_changed)
        self.vertical_splitter.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.on_vertical_splitter_changed)
        
        # Main layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.horizontal_splitter, 1, wx.EXPAND)
        self.main_panel.SetSizer(main_sizer)

        # Create main layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.vertical_splitter, 1, wx.EXPAND)
        self.SetSizer(main_sizer)

        # Create menus and status bar
        m_menubar.setup_menus(self)
        m_status_bar.setup_status_bar(self)

        # Bind events
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)

        # Flag to suppress sidebar EVT_TEXT handlers during programmatic updates
        self.suppress_view_option_events = False
        
        # Bind hotkey events to canvas
        self.canvas.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.canvas.Bind(wx.EVT_KEY_UP, lambda evt: self.managers.hotkey_manager.on_key_up(evt))
        self.canvas.Bind(wx.EVT_LEFT_DOWN, lambda evt: self.managers.hotkey_manager.on_mouse_left_down(evt))
        self.canvas.Bind(wx.EVT_RIGHT_DOWN, lambda evt: self.managers.hotkey_manager.on_mouse_right_down(evt))
        self.canvas.Bind(wx.EVT_MIDDLE_DOWN, lambda evt: self.managers.hotkey_manager.on_mouse_middle_down(evt))
        
        # Removed extra mouse wheel binding to hotkey manager to avoid double-handling zoom events
        self.canvas.Bind(wx.EVT_MOTION, lambda evt: self.managers.hotkey_manager.on_mouse_move(evt))


    def toggle_sidebar(self):
        """Toggle sidebar visibility."""
        if hasattr(self, 'mvu_adapter'):
            self.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.TOGGLE_SIDEBAR))
        else:
            # Fallback to direct behavior if MVU not initialized yet
            self.set_sidebar_visible(not getattr(self, 'sidebar_visible', True))


    def toggle_status_bar(self):
        """Toggle status bar visibility."""
        if hasattr(self, 'mvu_adapter'):
            self.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.TOGGLE_STATUS))
        else:
            # Fallback to direct behavior if MVU not initialized yet
            self.set_status_bar_visible(not getattr(self, 'status_bar_visible', True))

    def set_sidebar_visible(self, visible: bool):
        """Idempotently show/hide sidebar and refresh UI."""
        if getattr(self, 'sidebar_visible', True) == visible:
            return
        if visible:
            # Show sidebar
            self.sidebar.Show()
            self.horizontal_splitter.SplitVertically(self.canvas, self.sidebar, -250)
            self.sidebar_visible = True
            print("DEBUG: Sidebar shown (set)")
            self.remove_sidebar_expand_button()
        else:
            # Hide sidebar
            self.sidebar.Hide()
            self.horizontal_splitter.Unsplit(self.sidebar)
            self.sidebar_visible = False
            print("DEBUG: Sidebar hidden (set)")
            self.add_sidebar_expand_button()
        # Refresh the layout and force canvas redraw
        self.horizontal_splitter.Refresh()
        self.Layout()
        wx.CallAfter(self.canvas.Refresh)
        print("DEBUG: Canvas refresh scheduled after set_sidebar_visible")

    def set_status_bar_visible(self, visible: bool):
        """Idempotently show/hide status bar and refresh UI."""
        if getattr(self, 'status_bar_visible', True) == visible:
            return
        if visible:
            # Show status bar
            self.status_panel.Show()
            self.vertical_splitter.SplitHorizontally(self.main_panel, self.status_panel, -150)
            self.status_bar_visible = True
            print("DEBUG: Status bar shown (set)")
            self.remove_status_bar_expand_button()
        else:
            # Hide status bar
            self.status_panel.Hide()
            self.vertical_splitter.Unsplit(self.status_panel)
            self.status_bar_visible = False
            print("DEBUG: Status bar hidden (set)")
            self.add_status_bar_expand_button()
        # Refresh the layout and force canvas redraw
        self.vertical_splitter.Refresh()
        self.Layout()
        wx.CallAfter(self.canvas.Refresh)
        print("DEBUG: Canvas refresh scheduled after set_status_bar_visible")

    def _init_mvu_adapter(self):
        """Initialize MVU adapter and sync with current UI state."""
        try:
            ui_state = UIState()
            ui_state.bind_widget('main_window', self)
            initial_model = m_main_mvu.initial_model_fn(
                sidebar_visible=getattr(self, 'sidebar_visible', True),
                status_bar_visible=getattr(self, 'status_bar_visible', True),
                grid_visible=(getattr(self, 'canvas', None) is not None and getattr(self.canvas, 'grid_style', 'grid') != 'none'),
                snap_enabled=(getattr(self, 'canvas', None) is not None and (
                    getattr(self.canvas, 'grid_snapping_enabled', True) or getattr(self.canvas, 'snap_to_grid', True)
                ))
            )
            self.mvu_adapter = MVUAdapter(
                initial_model=initial_model,
                update_fn=m_main_mvu.update_fn,
                ui_state=ui_state,
                ui_render=m_main_mvu.ui_render,
            )
            # Apply initial render to ensure UI and model are in sync
            self.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_SIDEBAR_VISIBLE, visible=initial_model.sidebar_visible))
            self.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_STATUS_VISIBLE, visible=initial_model.status_bar_visible))
            self.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_GRID_VISIBLE, visible=initial_model.grid_visible))
            self.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_SNAP_ENABLED, enabled=initial_model.snap_enabled))
            # Seed theme from ThemeManager if available
            try:
                if getattr(self.managers, 'theme_manager', None) and self.managers.theme_manager.get_current_theme():
                    theme = self.managers.theme_manager.get_current_theme()
                    if theme and hasattr(theme, 'name'):
                        self.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_THEME, name=theme.name))
            except Exception:
                pass
            # Seed undo/redo state and counts
            try:
                can_undo = self.managers.undo_redo_manager.can_undo()
                can_redo = self.managers.undo_redo_manager.can_redo()
                self.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_UNDO_REDO_STATE, can_undo=can_undo, can_redo=can_redo))
                nodes = len(self.current_graph.get_all_nodes())
                edges = len(self.current_graph.get_all_edges())
                self.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_COUNTS, nodes=nodes, edges=edges))
            except Exception:
                pass
            # Seed movement/zoom/rotation from current UI if available
            try:
                move_x = getattr(self, 'x_sensitivity_field', None).GetValue() if hasattr(self, 'x_sensitivity_field') else 1.0
                move_y = getattr(self, 'y_sensitivity_field', None).GetValue() if hasattr(self, 'y_sensitivity_field') else 1.0
                inverted = getattr(self, 'move_inverted_cb', None).GetValue() if hasattr(self, 'move_inverted_cb') else False
                self.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_MOVE_SENSITIVITY, x=move_x, y=move_y, inverted=inverted))
                zoom_sens = getattr(self, 'zoom_sensitivity_field', None).GetValue() if hasattr(self, 'zoom_sensitivity_field') else 1.0
                self.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_ZOOM_SENSITIVITY, value=zoom_sens))
                # Persisted zoom input mode and sensitivity via ZoomManager
                try:
                    zm = self.managers.zoom_manager
                    # Mode first
                    self.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_ZOOM_INPUT_MODE, mode=zm.get_mode()))
                    # Sensitivity override if no UI value yet
                    if not hasattr(self, 'zoom_sensitivity_field'):
                        self.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_ZOOM_SENSITIVITY, value=zm.get_sensitivity()))
                except Exception:
                    pass
                rotation = getattr(self, 'rotation_field', None).GetValue() if hasattr(self, 'rotation_field') else 0.0
                self.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_ROTATION, angle=rotation))
            except Exception:
                pass
        except Exception as e:
            print(f"DEBUG: Failed to initialize MVU adapter: {e}")

    def _maybe_load_from_backend(self):
        """Fetch graph from backend on startup if the server is available."""
        try:
            if self.backend.is_available():
                data = self.backend.get_graph()
                if data and isinstance(data, dict) and data.get('nodes') is not None:
                    try:
                        self.current_graph = m_graph.Graph.from_dict(data)
                        self.graphs[self.current_graph.id] = self.current_graph
                        if hasattr(self, 'canvas'):
                            self.canvas.set_graph(self.current_graph, emit_signal=False)
                        print("DEBUG: Loaded graph state from backend")
                    except Exception as e:
                        print(f"DEBUG: Error constructing graph from backend: {e}")
        except Exception as e:
            print(f"DEBUG: Backend not available: {e}")


    def on_horizontal_splitter_changed(self, event):
        """Handle horizontal splitter (sidebar) position changes."""

        sash_pos = event.GetSashPosition()
        splitter_size = self.horizontal_splitter.GetSize().GetWidth()
        
        print(f"DEBUG: Horizontal splitter changed - sash_pos: {sash_pos}, splitter_size: {splitter_size}")
        print(f"DEBUG: Collapse threshold: {splitter_size - 300}, Current position: {sash_pos}")
        
        # Only handle horizontal splitter if the sash position is reasonable for horizontal splitter
        # (i.e., not a vertical splitter position that got misrouted)
        if sash_pos < splitter_size:  # Valid horizontal splitter position
            # If sash is dragged to the right edge (within 300 pixels), collapse sidebar
            if sash_pos > splitter_size - 300:
                if self.sidebar_visible:
                    self.sidebar.Hide()
                    self.horizontal_splitter.Unsplit(self.sidebar)
                    self.sidebar_visible = False
                    if hasattr(self, 'mvu_adapter'):
                        self.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_SIDEBAR_VISIBLE, visible=False))
                    print("DEBUG: Sidebar collapsed via drag")
                    self.update_menu_states()
                    self.add_sidebar_expand_button()
                    # Force canvas to redraw with new dimensions
                    wx.CallAfter(self.canvas.Refresh)
                    print("DEBUG: Canvas refresh scheduled after sidebar collapse via drag")
            
            # If sash is dragged away from the edge, ensure sidebar is visible
            elif sash_pos < splitter_size - 400 and not self.sidebar_visible:
                self.sidebar.Show()
                self.horizontal_splitter.SplitVertically(self.canvas, self.sidebar, -250)
                self.sidebar_visible = True
                if hasattr(self, 'mvu_adapter'):
                    self.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_SIDEBAR_VISIBLE, visible=True))
                print("DEBUG: Sidebar expanded via drag")
                self.update_menu_states()
                self.remove_sidebar_expand_button()
                # Force canvas to redraw with new dimensions
                wx.CallAfter(self.canvas.Refresh)
                print("DEBUG: Canvas refresh scheduled after sidebar expansion via drag")
        
        event.Skip()


    def on_vertical_splitter_changed(self, event):
        """Handle vertical splitter (status bar) position changes."""

        sash_pos = event.GetSashPosition()
        splitter_size = self.vertical_splitter.GetSize().GetHeight()
        
        print(f"DEBUG: Vertical splitter changed - sash_pos: {sash_pos}, splitter_size: {splitter_size}")
        print(f"DEBUG: Collapse threshold: {splitter_size - 200}, Current position: {sash_pos}")
        
        # Only handle vertical splitter if the sash position is reasonable for vertical splitter
        # (i.e., not a horizontal splitter position that got misrouted)
        if sash_pos < splitter_size:  # Valid vertical splitter position
            # If sash is dragged to the bottom edge (within 200 pixels), collapse status bar
            if sash_pos > splitter_size - 200:
                if self.status_bar_visible:
                    self.status_panel.Hide()
                    self.vertical_splitter.Unsplit(self.status_panel)
                    self.status_bar_visible = False
                    if hasattr(self, 'mvu_adapter'):
                        self.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_STATUS_VISIBLE, visible=False))
                    print("DEBUG: Status bar collapsed via drag")
                    self.update_menu_states()
                    self.add_status_bar_expand_button()
                    # Force canvas to redraw with new dimensions
                    wx.CallAfter(self.canvas.Refresh)
                    print("DEBUG: Canvas refresh scheduled after status bar collapse via drag")
            
            # If sash is dragged away from the edge, ensure status bar is visible
            elif sash_pos < splitter_size - 300 and not self.status_bar_visible:
                self.status_panel.Show()
                self.vertical_splitter.SplitHorizontally(self.main_panel, self.status_panel, -150)
                self.status_bar_visible = True
                if hasattr(self, 'mvu_adapter'):
                    self.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_STATUS_VISIBLE, visible=True))
                print("DEBUG: Status bar expanded via drag")
                self.update_menu_states()
                self.remove_status_bar_expand_button()
                # Force canvas to redraw with new dimensions
                wx.CallAfter(self.canvas.Refresh)
                print("DEBUG: Canvas refresh scheduled after status bar expansion via drag")
        
        event.Skip()


    def update_menu_states(self):
        """Update menu check states to reflect current panel visibility."""

        try:
            menubar = self.GetMenuBar()
            if menubar:
                # Find the View menu (index 2)
                view_menu = menubar.GetMenu(2)
                if view_menu:
                    # Update sidebar menu item (assuming it's the first toggle item after separators)
                    for i in range(view_menu.GetMenuItemCount()):
                        item = view_menu.FindItemByPosition(i)
                        if item and item.GetItemLabelText() == "Show &Sidebar":
                            item.Check(self.sidebar_visible)
                        elif item and item.GetItemLabelText() == "Show &Status Bar":
                            item.Check(self.status_bar_visible)
        except Exception as e:
            print(f"DEBUG: Error updating menu states: {e}")


    def add_sidebar_expand_button(self):
        """Add expand button for collapsed sidebar."""

        if hasattr(self, 'sidebar_expand_button'):
            self.sidebar_expand_button.Destroy()
        
        # Create a small button on the right edge of the canvas
        self.sidebar_expand_button = wx.Button(self.canvas, label="◀", size=(30, 100))
        self.sidebar_expand_button.SetPosition((self.canvas.GetSize().GetWidth() - 30, 50))
        self.sidebar_expand_button.Bind(wx.EVT_BUTTON, self.on_expand_sidebar)
        self.sidebar_expand_button.Show()
        print("DEBUG: Sidebar expand button added")


    def remove_sidebar_expand_button(self):
        """Remove sidebar expand button."""

        if hasattr(self, 'sidebar_expand_button'):
            self.sidebar_expand_button.Destroy()
            delattr(self, 'sidebar_expand_button')
            print("DEBUG: Sidebar expand button removed")


    def add_status_bar_expand_button(self):
        """Add expand button for collapsed status bar."""

        if hasattr(self, 'status_bar_expand_button'):
            self.status_bar_expand_button.Destroy()
        
        # Create a small button on the bottom edge of the canvas
        self.status_bar_expand_button = wx.Button(self.canvas, label="▲", size=(100, 30))
        self.status_bar_expand_button.SetPosition((50, self.canvas.GetSize().GetHeight() - 30))
        self.status_bar_expand_button.Bind(wx.EVT_BUTTON, self.on_expand_status_bar)
        self.status_bar_expand_button.Show()
        print("DEBUG: Status bar expand button added")


    def remove_status_bar_expand_button(self):
        """Remove status bar expand button."""

        if hasattr(self, 'status_bar_expand_button'):
            self.status_bar_expand_button.Destroy()
            delattr(self, 'status_bar_expand_button')
            print("DEBUG: Status bar expand button removed")


    def on_expand_sidebar(self, event):
        """Handle sidebar expand button click."""

        self.sidebar.Show()
        self.horizontal_splitter.SplitVertically(self.canvas, self.sidebar, -250)
        self.sidebar_visible = True
        if hasattr(self, 'mvu_adapter'):
            self.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_SIDEBAR_VISIBLE, visible=True))
        self.update_menu_states()
        self.remove_sidebar_expand_button()
        print("DEBUG: Sidebar expanded via button")


    def on_expand_status_bar(self, event):
        """Handle status bar expand button click."""

        self.status_panel.Show()
        self.vertical_splitter.SplitHorizontally(self.main_panel, self.status_panel, -150)
        self.status_bar_visible = True
        if hasattr(self, 'mvu_adapter'):
            self.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_STATUS_VISIBLE, visible=True))
        self.update_menu_states()
        self.remove_status_bar_expand_button()
        print("DEBUG: Status bar expanded via button")


    def apply_enhanced_styling(self):
        """Apply enhanced styling to all UI elements for better visibility."""

        # Define colors for enhanced visibility (from display settings)
        button_bg = self.display.button_background_color
        button_fg = self.display.button_text_color
        label_fg = self.display.label_text_color
        control_bg = self.display.control_background_color
        
        # Style the Properties button
        if hasattr(self, 'properties_btn'):
            self.properties_btn.SetBackgroundColour(button_bg)
            self.properties_btn.SetForegroundColour(button_fg)
            font = self.properties_btn.GetFont()
            font.SetWeight(wx.FONTWEIGHT_BOLD)
            self.properties_btn.SetFont(font)
        
        # Style the Make All Nodes Readable button
        if hasattr(self, 'make_readable_btn'):
            self.make_readable_btn.SetBackgroundColour(button_bg)
            self.make_readable_btn.SetForegroundColour(button_fg)
            font = self.make_readable_btn.GetFont()
            font.SetWeight(wx.FONTWEIGHT_BOLD)
            self.make_readable_btn.SetFont(font)
        
        # Style the Set Origin button
        if hasattr(self, 'set_origin_btn'):
            self.set_origin_btn.SetBackgroundColour(button_bg)
            self.set_origin_btn.SetForegroundColour(button_fg)
            font = self.set_origin_btn.GetFont()
            font.SetWeight(wx.FONTWEIGHT_BOLD)
            self.set_origin_btn.SetFont(font)
        
        # Style the Set Rotation button
        if hasattr(self, 'set_rotation_btn'):
            self.set_rotation_btn.SetBackgroundColour(button_bg)
            self.set_rotation_btn.SetForegroundColour(button_fg)
            font = self.set_rotation_btn.GetFont()
            font.SetWeight(wx.FONTWEIGHT_BOLD)
            self.set_rotation_btn.SetFont(font)
        
        # Style sensitivity +/- buttons
        for btn_name in [
            'x_sensitivity_minus', 'x_sensitivity_plus',
            'y_sensitivity_minus', 'y_sensitivity_plus',
            'combined_sensitivity_minus', 'combined_sensitivity_plus',
            'zoom_sensitivity_minus', 'zoom_sensitivity_plus'
        ]:
            if hasattr(self, btn_name):
                btn = getattr(self, btn_name)
                btn.SetBackgroundColour(button_bg)
                btn.SetForegroundColour(button_fg)
                font = btn.GetFont()
                font.SetWeight(wx.FONTWEIGHT_BOLD)
                font.SetPointSize(self.display.small_button_font_point_size)
                btn.SetFont(font)
        
        # Style default properties buttons
        for btn_name in ['default_node_btn', 'default_edge_btn']:
            if hasattr(self, btn_name):
                btn = getattr(self, btn_name)
                btn.SetBackgroundColour(button_bg)
                btn.SetForegroundColour(button_fg)
                font = btn.GetFont()
                font.SetWeight(wx.FONTWEIGHT_BOLD)
                btn.SetFont(font)
        
        # Style color buttons and view control buttons
        for btn_name in [
            'bg_color_btn', 'grid_color_btn', 'snap_to_original_btn',
            'set_origin_btn', 'set_rotation_btn', 'set_zoom_btn', 'set_current_view_btn'
        ]:
            if hasattr(self, btn_name):
                btn = getattr(self, btn_name)
                btn.SetForegroundColour(button_fg)
                font = btn.GetFont()
                font.SetWeight(wx.FONTWEIGHT_BOLD)
                btn.SetFont(font)
        
        # Dropdown and B-spline controls are styled directly when created
        
        # Style rotation +/- buttons
        for btn_name in ['rotation_minus', 'rotation_plus']:
            if hasattr(self, btn_name):
                btn = getattr(self, btn_name)
                btn.SetBackgroundColour(button_bg)
                btn.SetForegroundColour(button_fg)
                font = btn.GetFont()
                font.SetWeight(wx.FONTWEIGHT_BOLD)
                font.SetPointSize(self.display.small_button_font_point_size)
                btn.SetFont(font)
        
        # Style spin controls - macOS-specific approach for better visibility
        def style_spin_control(ctrl, ctrl_name):
            try:
                # Try multiple approaches for macOS compatibility
                
                # Method 1: Direct color setting
                ctrl.SetForegroundColour(self.display.spin_ctrl_text_color)
                ctrl.SetBackgroundColour(self.display.spin_ctrl_background_color)
                
                # Method 2: Set font with high contrast
                font = ctrl.GetFont()
                font.SetWeight(wx.FONTWEIGHT_BOLD)
                font.SetPointSize(self.display.spin_ctrl_font_point_size)
                ctrl.SetFont(font)
                
                # Method 3: Force update
                ctrl.Refresh()
                ctrl.Update()
                
                # Method 4: Try to access the text control inside SpinCtrlDouble
                for child in ctrl.GetChildren():
                    if hasattr(child, 'SetForegroundColour'):
                        child.SetForegroundColour(self.display.spin_ctrl_text_color)
                        child.SetBackgroundColour(self.display.spin_ctrl_background_color)
                        child.Refresh()
                
                print(
                    f"DEBUG: Applied multiple styling methods to {ctrl_name}")
                
            except Exception as e:
                print(f"DEBUG: Error styling {ctrl_name}: {e}")
        
        for ctrl_name in [
            'x_sensitivity_field', 'y_sensitivity_field',
            'combined_sensitivity_field', 'zoom_sensitivity_field',
            'rotation_field'
        ]:
            if hasattr(self, ctrl_name):
                ctrl = getattr(self, ctrl_name)
                style_spin_control(ctrl, ctrl_name)
                
                # Schedule another styling attempt after UI is fully loaded
                wx.CallAfter(style_spin_control, ctrl, f"{ctrl_name}_delayed")
        
        # Bind tool selector events (guarded for legacy ToggleButtons)
        import graph_canvas.presentation.desktop.event_handlers.tool_selector_event_handler as m_tool_selector_event_handler
        
        if hasattr(self, 'tool_select') and isinstance(self.tool_select, wx.ToggleButton):
            self.tool_select.Bind(wx.EVT_TOGGLEBUTTON, lambda evt: m_tool_selector_event_handler.on_tool_select(self, evt))
        if hasattr(self, 'tool_node') and isinstance(self.tool_node, wx.ToggleButton):
            self.tool_node.Bind(wx.EVT_TOGGLEBUTTON, lambda evt: m_tool_selector_event_handler.on_tool_select(self, evt))
        if hasattr(self, 'tool_edge') and isinstance(self.tool_edge, wx.ToggleButton):
            self.tool_edge.Bind(wx.EVT_TOGGLEBUTTON, lambda evt: m_tool_selector_event_handler.on_tool_select(self, evt))
        if hasattr(self, 'tool_move') and isinstance(self.tool_move, wx.ToggleButton):
            self.tool_move.Bind(wx.EVT_TOGGLEBUTTON, lambda evt: m_tool_selector_event_handler.on_tool_select(self, evt))
        if hasattr(self, 'tool_rotate') and isinstance(self.tool_rotate, wx.ToggleButton):
            self.tool_rotate.Bind(wx.EVT_TOGGLEBUTTON, lambda evt: m_tool_selector_event_handler.on_tool_select(self, evt))
        
        # Style basic controls with black text and better fonts
        # Do not override tool radios here; they are styled in the sidebar
        control_list = [
            'graph_name_ctrl', 'edge_directed_cb', 'grid_enabled_cb',
            'move_inverted_cb', 'sensitivity_locked_cb'
        ]
        
        for ctrl_name in control_list:
            if hasattr(self, ctrl_name):
                ctrl = getattr(self, ctrl_name)
                ctrl.SetForegroundColour(label_fg)
                font = ctrl.GetFont()
                font.SetWeight(wx.FONTWEIGHT_NORMAL)
                font.SetPointSize(self.display.default_label_font_point_size)
                ctrl.SetFont(font)
        
        # Explicitly style sensitivity labels to ensure they're bold and black
        label_list = ['x_label', 'y_label', 'combined_label', 'zoom_label']
        for label_name in label_list:
            if hasattr(self, label_name):
                label = getattr(self, label_name)
                label.SetForegroundColour(label_fg)
                font = label.GetFont()
                font.SetWeight(wx.FONTWEIGHT_BOLD)
                font.SetPointSize(self.display.bold_label_font_point_size)
                label.SetFont(font)
        
        # Apply enhanced styling to all static text labels
        def style_labels(widget):
            if isinstance(widget, wx.StaticText):
                widget.SetForegroundColour(label_fg)
                font = widget.GetFont()
                font.SetWeight(wx.FONTWEIGHT_BOLD)
                font.SetPointSize(self.display.default_label_font_point_size)
                widget.SetFont(font)
            elif isinstance(widget, wx.StaticBox):
                widget.SetForegroundColour(label_fg)
                font = widget.GetFont()
                font.SetWeight(wx.FONTWEIGHT_BOLD)
                font.SetPointSize(self.display.bold_label_font_point_size)
                widget.SetFont(font)
            
            # Recursively apply to children
            for child in widget.GetChildren():
                style_labels(child)
        
        style_labels(self.sidebar)
        
        # Refresh the sidebar to apply changes
        self.sidebar.Refresh()
        self.sidebar.Layout()
    
    def update_curve_list(self):
        """Delegate to sidebar event handler to refresh curve control list."""
        try:
            import graph_canvas.presentation.desktop.event_handlers.sidebar_event_handler as _sidebar_evt
            _sidebar_evt.update_curve_list(self)
        except Exception:
            pass

    def update_bspline_list(self):
        """Delegate to sidebar event handler to refresh B-spline control list."""
        try:
            import graph_canvas.presentation.desktop.event_handlers.sidebar_event_handler as _sidebar_evt
            _sidebar_evt.update_bspline_list(self)
        except Exception:
            pass

    def update_composite_list(self):
        """Delegate to composite segment panel to refresh composite segments list."""
        try:
            import graph_canvas.presentation.desktop.gui.control_points_and_composite_segment_panel as _cp_panel
            _cp_panel.update_composite_list(self)
        except Exception:
            pass

    def apply_theme_to_dialog(self, dialog: wx.Dialog):
        """Apply current theme to a dialog if ThemeManager is available."""
        try:
            if getattr(self.managers, 'theme_manager', None):
                self.managers.theme_manager.apply_theme_to_window(dialog)
        except Exception:
            pass
    

    def zoom_to_fit(self):
        """Zoom to fit all items."""
        if hasattr(self, 'mvu_adapter'):
            self.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.ZOOM_FIT))
        else:
            if hasattr(self, 'canvas'):
                self.canvas.zoom_to_fit()


    def on_zoom_in(self):
        """Zoom in at current mouse position."""
        if hasattr(self, 'mvu_adapter'):
            self.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.ZOOM_IN))
        else:
            if hasattr(self, 'canvas'):
                self.canvas.zoom_in_at_mouse()
                self.update_status_bar()


    def on_zoom_out(self):
        """Zoom out at current mouse position."""
        if hasattr(self, 'mvu_adapter'):
            self.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.ZOOM_OUT))
        else:
            if hasattr(self, 'canvas'):
                self.canvas.zoom_out_at_mouse()
                self.update_status_bar()


    def change_grid_color(self):
        """Change grid color."""

        color_dialog = wx.ColourDialog(self)
        if color_dialog.ShowModal() == wx.ID_OK:
            new_color = color_dialog.GetColourData().GetColour()
            # Convert to RGB tuple and store
            rgb_tuple = (new_color.Red(), new_color.Green(), new_color.Blue())
            if hasattr(self, 'mvu_adapter'):
                self.mvu_adapter.dispatch(
                    make_message(m_main_mvu.Msg.SET_GRID_COLOR, r=rgb_tuple[0], g=rgb_tuple[1], b=rgb_tuple[2])
                )
            else:
                old_color = self.canvas.grid_color
                # Create and execute command (legacy fallback)
                command = ChangeColorCommand(self.canvas, 'grid', old_color, rgb_tuple)
            self.managers.undo_redo_manager.execute_command(command)
            # Update the button to show the selected color
            self.grid_color_btn.SetBackgroundColour(new_color)
            print(f"DEBUG: Grid color changed to RGB{rgb_tuple}")
        color_dialog.Destroy()


    def update_ui(self):
        """Update UI state including status bar and counters."""

        # Update graph name in the text control
        if hasattr(self, 'graph_name_ctrl'):
            self.graph_name_ctrl.SetValue(self.current_graph.name)
        
        # Update node and edge counts
        node_count = len(self.current_graph.get_all_nodes())
        edge_count = len(self.current_graph.get_all_edges())
        if hasattr(self, 'mvu_adapter'):
            try:
                self.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_COUNTS, nodes=node_count, edges=edge_count))
            except Exception:
                pass
        
        if hasattr(self, 'node_count_label'):
            self.node_count_label.SetLabel(f"Nodes: {node_count}")
        if hasattr(self, 'edge_count_label'):
            self.edge_count_label.SetLabel(f"Edges: {edge_count}")
        
        # Update status bar
        if hasattr(self, 'statusbar'):
            self.statusbar.SetStatusText(f"Nodes: {node_count}", 1)
            self.statusbar.SetStatusText(f"Edges: {edge_count}", 2)
        
        # Update window title
        title = f"Graph Editor - {self.current_graph.name}"
        if self.current_graph.modified:
            title += "*"
        if hasattr(self.current_graph, 'file_path') and self.current_graph.file_path:
            title += f" - {os.path.basename(self.current_graph.file_path)}"
        self.SetTitle(title)
        
        # Update selection display
        if hasattr(self, 'update_selection_display'):
            self.update_selection_display()
            
        # Update canvas
        if hasattr(self, 'canvas'):
            self.canvas.set_graph(self.current_graph, emit_signal=False)
        
        self.update_dependency_list_panel()
            
        # Ensure enhanced styling is applied
        self.apply_enhanced_styling()


    def update_dependency_list_panel(self):
        """Refresh the dependency list sidebar pane."""

        try:
            m_dependency_list_panel.rebuild_dependency_list(self)
        except Exception as exc:
            print(f"DEBUG: Failed to update dependency list: {exc}")


    def dependency_list_set_status(self, node_id: str, status: Optional[str]) -> None:
        """Handle status changes originating from the dependency list."""

        node = self.current_graph.get_node(node_id)
        if not node:
            return

        old_metadata = copy.deepcopy(node.metadata)
        new_metadata = copy.deepcopy(node.metadata)
        changed = False
        if status:
            if new_metadata.get("status") != status:
                new_metadata["status"] = status
                changed = True
        elif "status" in new_metadata:
            new_metadata.pop("status", None)
            changed = True

        if not changed:
            return

        if self.managers.undo_redo_manager:
            command = m_commands.EditPropertiesCommand(
                node,
                {"metadata": old_metadata},
                {"metadata": new_metadata},
                "Update Task Status",
            )
            self.managers.undo_redo_manager.execute_command(command)
        else:
            node.metadata = new_metadata

        self.current_graph.modified = True
        self._sync_node_to_backend(node_id, {"metadata": new_metadata})
        self.update_dependency_list_panel()
        self.canvas.Refresh()


    def dependency_list_delete_node(self, node_id: str) -> None:
        """Delete a node via the dependency list panel."""

        node = self.current_graph.get_node(node_id)
        if not node:
            return

        if self.managers.undo_redo_manager:
            command = m_commands.DeleteNodeCommand(self.current_graph, node_id)
            self.managers.undo_redo_manager.execute_command(command)
        else:
            self.current_graph.remove_node(node_id)

        self.current_graph.modified = True
        self._sync_node_deletion(node_id)
        self.update_ui()


    def dependency_list_create_task(
        self, label: str, prereq_ids: List[str], post_ids: List[str]
    ) -> None:
        """Create a new task (node) and connect it to the requested dependencies."""

        new_x, new_y = self._next_task_position()
        node = m_node.Node(x=new_x, y=new_y, text=label)
        commands: List[m_commands.Command] = [m_commands.AddNodeCommand(self.current_graph, node)]

        valid_prereqs = {
            node_id
            for node_id in prereq_ids
            if node_id != node.id and self.current_graph.get_node(node_id)
        }
        valid_posts = {
            node_id
            for node_id in post_ids
            if node_id != node.id and self.current_graph.get_node(node_id)
        }

        for source_id in valid_prereqs:
            edge = m_edge.Edge(source_id=source_id, target_id=node.id)
            commands.append(m_commands.AddEdgeCommand(self.current_graph, edge))

        for target_id in valid_posts:
            edge = m_edge.Edge(source_id=node.id, target_id=target_id)
            commands.append(m_commands.AddEdgeCommand(self.current_graph, edge))

        self._execute_commands(commands, "Add Dependency Task")
        self.current_graph.modified = True
        self._sync_full_graph()
        self.update_ui()


    def dependency_list_edit_task(
        self, node_id: str, label: str, prereq_ids: List[str], post_ids: List[str]
    ) -> None:
        """Edit an existing task's label and dependency connections."""

        node = self.current_graph.get_node(node_id)
        if not node:
            return

        commands: List[m_commands.Command] = []
        if node.text != label:
            commands.append(
                m_commands.EditPropertiesCommand(
                    node,
                    {"text": node.text},
                    {"text": label},
                    "Rename Task",
                )
            )

        desired_prereqs = {
            node_id
            for node_id in prereq_ids
            if node_id != node.id and self.current_graph.get_node(node_id)
        }
        desired_posts = {
            node_id
            for node_id in post_ids
            if node_id != node.id and self.current_graph.get_node(node_id)
        }

        incoming_edges = [
            edge for edge in self.current_graph.get_all_edges() if edge.target_id == node.id
        ]
        outgoing_edges = [
            edge for edge in self.current_graph.get_all_edges() if edge.source_id == node.id
        ]

        for edge in incoming_edges:
            if edge.source_id not in desired_prereqs:
                commands.append(m_commands.DeleteEdgeCommand(self.current_graph, edge.id))

        for source_id in desired_prereqs:
            if not any(edge.source_id == source_id for edge in incoming_edges):
                edge = m_edge.Edge(source_id=source_id, target_id=node.id)
                commands.append(m_commands.AddEdgeCommand(self.current_graph, edge))

        for edge in outgoing_edges:
            if edge.target_id not in desired_posts:
                commands.append(m_commands.DeleteEdgeCommand(self.current_graph, edge.id))

        for target_id in desired_posts:
            if not any(edge.target_id == target_id for edge in outgoing_edges):
                edge = m_edge.Edge(source_id=node.id, target_id=target_id)
                commands.append(m_commands.AddEdgeCommand(self.current_graph, edge))

        if not commands:
            return

        self._execute_commands(commands, "Update Dependency Task")
        self.current_graph.modified = True
        self._sync_full_graph()
        self.update_ui()


    def _sync_node_to_backend(self, node_id: str, payload: dict) -> None:
        """Attempt to mirror node updates to the backend API."""

        backend = getattr(self, "backend", None)
        if not backend or not backend.is_available():
            return
        try:
            if not backend.update_node(self.current_graph.id, node_id, payload):
                backend.set_graph(self.current_graph.to_dict())
        except Exception as exc:
            print(f"DEBUG: Failed to sync node update for {node_id}: {exc}")


    def _sync_node_deletion(self, node_id: str) -> None:
        """Attempt to mirror node deletions to the backend API."""

        backend = getattr(self, "backend", None)
        if not backend or not backend.is_available():
            return
        try:
            if not backend.delete_node(self.current_graph.id, node_id):
                backend.set_graph(self.current_graph.to_dict())
        except Exception as exc:
            print(f"DEBUG: Failed to sync node deletion for {node_id}: {exc}")


    def _sync_full_graph(self) -> None:
        """Best-effort sync of the full graph snapshot to the backend."""

        backend = getattr(self, "backend", None)
        if not backend or not backend.is_available():
            return
        try:
            backend.set_graph(self.current_graph.to_dict())
        except Exception as exc:
            print(f"DEBUG: Failed to sync full graph: {exc}")


    def _next_task_position(self) -> Tuple[float, float]:
        """Determine a default XY position for a newly created task node."""

        nodes = [
            node for node in self.current_graph.get_all_nodes() if isinstance(node.y, (int, float))
        ]
        if not nodes:
            return (0.0, 0.0)
        max_y = max(node.y for node in nodes)
        return (0.0, float(max_y) + 80.0)


    def _execute_commands(self, commands: List[m_commands.Command], label: str) -> None:
        """Execute a list of commands with undo/redo support."""

        if not commands:
            return
        manager = getattr(self.managers, "undo_redo_manager", None)
        if manager:
            if len(commands) == 1:
                manager.execute_command(commands[0])
            else:
                composite = m_commands.CompositeCommand(label, commands)
                manager.execute_command(composite)
        else:
            for command in commands:
                command.execute()


    def on_exit(self, event):
        """Handle Exit command."""

        self.Close()
    

    def on_key_down(self, event):
        """Handle key down events."""
    
        # Let the hotkey manager handle the event first
        if self.managers.hotkey_manager.handle_key_event(event):
            return
        
        # If not handled by hotkeys, let the event propagate
        event.Skip()


    def on_close(self, event):
        """Handle window closing."""

        # Check for unsaved changes
        if not self.managers.file_manager.check_unsaved_changes():
            event.Veto()  # Prevent closing
            return
            
        # Save settings
        self.managers.layout_manager.save_settings()
        self.managers.file_manager.save_recent_files()
        
        # Allow closing
        event.Skip()
        
        
    def update_canvas_sensitivity(self):
        """Update canvas with current sensitivity settings."""
    
        if hasattr(self, 'canvas'):
            self.canvas.set_move_sensitivity(
                self.x_sensitivity_field.GetValue(),
                self.y_sensitivity_field.GetValue(),
                self.move_inverted_cb.GetValue())


    def update_canvas_info(self):
        """Update canvas information display in View Options."""

        if hasattr(self, 'canvas') and hasattr(self, 'center_x_value'):
            # Prevent sidebar EVT_TEXT handlers from reacting to these programmatic updates
            self.suppress_view_option_events = True
            # Get canvas center coordinates (pan values represent the center)
            center_x = self.canvas.pan_x
            center_y = self.canvas.pan_y
            
            # Update center coordinates
            # Use ChangeValue to avoid emitting EVT_TEXT and triggering handlers
            self.center_x_value.ChangeValue(f"{center_x:.1f}")
            self.center_y_value.ChangeValue(f"{center_y:.1f}")
            
            # Calculate world dimensions based on zoom level
            canvas_size = self.canvas.GetSize()
            zoom_factor = self.canvas.zoom
            world_width = canvas_size.GetWidth() / zoom_factor
            world_height = canvas_size.GetHeight() / zoom_factor
            
            # Update world dimensions
            # Use ChangeValue to avoid emitting EVT_TEXT and triggering handlers
            self.width_value.ChangeValue(f"{world_width:.1f}")
            self.height_value.ChangeValue(f"{world_height:.1f}")
            
            print(f"DEBUG: Updated canvas info - Center: ({center_x:.1f}, {center_y:.1f}), World Size: {world_width:.1f}x{world_height:.1f} (zoom: {zoom_factor:.3f})")
            print(f"DEBUG: Width field value: {self.width_value.GetValue()}, Height field value: {self.height_value.GetValue()}")
            # Re-enable handlers
            self.suppress_view_option_events = False
