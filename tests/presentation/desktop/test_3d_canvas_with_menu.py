#!/usr/bin/env python3
"""
Test script for the 3D Canvas with menubar integration
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import wx
    print("✓ wxPython available")
except ImportError as e:
    print(f"✗ wxPython not available: {e}")
    sys.exit(1)

try:
    import numpy as np
    print("✓ NumPy available")
except ImportError as e:
    print(f"✗ NumPy not available: {e}")
    print("Install NumPy with: pip install numpy")
    sys.exit(1)

try:
    from graph_canvas.presentation.desktop.gui.3d_canvas import Canvas3D, ProjectionMode
    from graph_canvas.presentation.desktop.event_handlers.3d_canvas_event_handler import (
        on_grid_color_x, on_grid_color_y, on_grid_color_z,
        on_toggle_3d_grid, on_toggle_3d_axes, on_toggle_3d_projection,
        on_toggle_3d_view_limits, on_reset_3d_camera, on_reset_3d_world
    )
    print("✓ 3D Canvas and handlers import successfully")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)


class Test3DFrame(wx.Frame):
    """Test frame with 3D canvas and menubar."""
    
    def __init__(self):
        super().__init__(None, title="3D Canvas with Grid Color Selectors", size=(1200, 800))
        
        # Create 3D canvas
        self.canvas_3d = Canvas3D(self)
        
        # Create menubar
        self.create_menubar()
        
        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas_3d, 1, wx.EXPAND)
        self.SetSizer(sizer)
        
        print("3D Canvas test frame created successfully")
    
    def create_menubar(self):
        """Create menubar with 3D canvas options."""
        print("DEBUG: Creating menubar...")
        
        # Create File menu (required on macOS for proper menubar display)
        file_menu = wx.Menu()
        exit_item = file_menu.Append(wx.ID_EXIT, "E&xit\tCtrl+Q", "Exit the application")
        
        # View menu
        view_menu = wx.Menu()
        
        # Grid submenu
        grid_menu = wx.Menu()
        
        # Grid color items
        grid_color_x_item = grid_menu.Append(wx.ID_ANY, "X Grid Color...", "Change color of X-direction grid lines")
        grid_color_y_item = grid_menu.Append(wx.ID_ANY, "Y Grid Color...", "Change color of Y-direction grid lines") 
        grid_color_z_item = grid_menu.Append(wx.ID_ANY, "Z Grid Color...", "Change color of Z-direction grid lines")
        
        grid_menu.AppendSeparator()
        
        # Grid toggle
        grid_toggle_item = grid_menu.Append(wx.ID_ANY, "Toggle Grid\tG", "Show/hide 3D grid")
        axes_toggle_item = grid_menu.Append(wx.ID_ANY, "Toggle Axes\tF1", "Show/hide coordinate axes")
        
        view_menu.AppendSubMenu(grid_menu, "3D &Grid", "3D grid options")
        view_menu.AppendSeparator()
        
        # Camera menu items
        projection_item = view_menu.Append(wx.ID_ANY, "Toggle &Projection\tP", "Switch between perspective and orthographic")
        view_limits_item = view_menu.Append(wx.ID_ANY, "Toggle View &Limits\tL", "Enable/disable view culling")
        
        view_menu.AppendSeparator()
        
        reset_camera_item = view_menu.Append(wx.ID_ANY, "Reset &Camera\tHome", "Reset camera to default position")
        reset_world_item = view_menu.Append(wx.ID_ANY, "Reset &World\tEnd", "Reset world transformation")
        
        # Help menu (also helps with macOS menubar display)
        help_menu = wx.Menu()
        about_item = help_menu.Append(wx.ID_ABOUT, "&About", "About this application")
        
        # Create menubar and add menus
        menubar = wx.MenuBar()
        menubar.Append(file_menu, "&File")
        menubar.Append(view_menu, "&View")
        menubar.Append(help_menu, "&Help")
        
        # Set the menubar - this is critical
        self.SetMenuBar(menubar)
        
        print("DEBUG: Menubar created and set")
        
        # Bind events
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
        self.Bind(wx.EVT_MENU, self.on_about, about_item)
        
        self.Bind(wx.EVT_MENU, self.on_grid_color_x_menu, grid_color_x_item)
        self.Bind(wx.EVT_MENU, self.on_grid_color_y_menu, grid_color_y_item)
        self.Bind(wx.EVT_MENU, self.on_grid_color_z_menu, grid_color_z_item)
        self.Bind(wx.EVT_MENU, self.on_toggle_grid_menu, grid_toggle_item)
        self.Bind(wx.EVT_MENU, self.on_toggle_axes_menu, axes_toggle_item)
        self.Bind(wx.EVT_MENU, self.on_toggle_projection_menu, projection_item)
        self.Bind(wx.EVT_MENU, self.on_toggle_view_limits_menu, view_limits_item)
        self.Bind(wx.EVT_MENU, self.on_reset_camera_menu, reset_camera_item)
        self.Bind(wx.EVT_MENU, self.on_reset_world_menu, reset_world_item)
        
        print("DEBUG: Menu events bound")
    
    # Event handlers that delegate to the canvas event handlers
    def on_grid_color_x_menu(self, event):
        on_grid_color_x(self, event)
    
    def on_grid_color_y_menu(self, event):
        on_grid_color_y(self, event)
    
    def on_grid_color_z_menu(self, event):
        on_grid_color_z(self, event)
    
    def on_toggle_grid_menu(self, event):
        on_toggle_3d_grid(self, event)
    
    def on_toggle_axes_menu(self, event):
        on_toggle_3d_axes(self, event)
    
    def on_toggle_projection_menu(self, event):
        on_toggle_3d_projection(self, event)
    
    def on_toggle_view_limits_menu(self, event):
        on_toggle_3d_view_limits(self, event)
    
    def on_reset_camera_menu(self, event):
        on_reset_3d_camera(self, event)
    
    def on_reset_world_menu(self, event):
        on_reset_3d_world(self, event)
    
    def on_exit(self, event):
        """Handle exit menu item."""
        self.Close()
    
    def on_about(self, event):
        """Handle about menu item."""
        info = wx.adv.AboutDialogInfo()
        info.SetName("3D Canvas Test")
        info.SetVersion("1.0")
        info.SetDescription("Test application for 3D Canvas with grid color selectors")
        info.SetCopyright("(C) 2025")
        info.AddDeveloper("3D Canvas Developer")
        
        wx.adv.AboutBox(info, self)


class Test3DApp(wx.App):
    """Test application for 3D canvas with menubar."""
    
    def OnInit(self):
        # Enable proper macOS menubar behavior
        self.SetAppName("3D Canvas Test")
        self.SetAppDisplayName("3D Canvas with Grid Colors")
        
        frame = Test3DFrame()
        frame.Show()
        
        # Force focus to ensure menubar appears
        frame.Raise()
        frame.SetFocus()
        
        print("DEBUG: Application initialized and frame shown")
        return True


if __name__ == "__main__":
    print("Starting 3D Canvas test with menubar...")
    app = Test3DApp()
    app.MainLoop()
