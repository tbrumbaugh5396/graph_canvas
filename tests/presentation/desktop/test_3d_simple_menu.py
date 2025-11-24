#!/usr/bin/env python3
"""
Simplified test for 3D Canvas with inline menubar - no external dependencies
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
    sys.exit(1)

try:
    from graph_canvas.presentation.desktop.gui.3d_canvas import Canvas3D, ProjectionMode
    print("✓ 3D Canvas imports successfully")
except ImportError as e:
    print(f"✗ 3D Canvas import failed: {e}")
    sys.exit(1)


class Simple3DFrame(wx.Frame):
    """Simple test frame with 3D canvas and inline menubar handlers."""
    
    def __init__(self):
        super().__init__(None, title="3D Canvas - Grid Color Test", size=(1200, 800))
        
        # Create 3D canvas
        self.canvas_3d = Canvas3D(self)
        
        # Create menubar
        self.create_menubar()
        
        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas_3d, 1, wx.EXPAND)
        self.SetSizer(sizer)
        
        # Center the frame
        self.Center()
        
        print("DEBUG: Simple 3D Canvas frame created successfully")
    
    def create_menubar(self):
        """Create menubar with 3D canvas options."""
        print("DEBUG: Creating simple menubar...")
        
        # Create menubar
        menubar = wx.MenuBar()
        
        # File menu (helps with macOS menubar display)
        file_menu = wx.Menu()
        exit_item = file_menu.Append(wx.ID_EXIT, "E&xit\tCtrl+Q", "Exit the application")
        
        # View menu
        view_menu = wx.Menu()
        
        # Grid color items (directly in View menu for simplicity)
        grid_color_x_item = view_menu.Append(wx.ID_ANY, "X Grid Color...\tShift+X", "Change color of X-direction grid lines")
        grid_color_y_item = view_menu.Append(wx.ID_ANY, "Y Grid Color...\tShift+Y", "Change color of Y-direction grid lines")
        grid_color_z_item = view_menu.Append(wx.ID_ANY, "Z Grid Color...\tShift+Z", "Change color of Z-direction grid lines")
        
        view_menu.AppendSeparator()
        
        # Grid toggle
        grid_toggle_item = view_menu.Append(wx.ID_ANY, "Toggle Grid\tG", "Show/hide 3D grid")
        axes_toggle_item = view_menu.Append(wx.ID_ANY, "Toggle Axes\tF1", "Show/hide coordinate axes")
        
        view_menu.AppendSeparator()
        
        # Camera items
        projection_item = view_menu.Append(wx.ID_ANY, "Toggle Projection\tP", "Switch between perspective and orthographic")
        reset_camera_item = view_menu.Append(wx.ID_ANY, "Reset Camera\tR", "Reset camera to default position")
        
        # Help menu
        help_menu = wx.Menu()
        about_item = help_menu.Append(wx.ID_ABOUT, "&About", "About this application")
        
        # Add menus to menubar
        menubar.Append(file_menu, "&File")
        menubar.Append(view_menu, "&View")
        menubar.Append(help_menu, "&Help")
        
        # Set the menubar
        result = self.SetMenuBar(menubar)
        print(f"DEBUG: SetMenuBar returned: {result}")
        
        # Verify menubar was set
        current_menubar = self.GetMenuBar()
        if current_menubar:
            print(f"DEBUG: Menubar successfully attached with {current_menubar.GetMenuCount()} menus")
            for i in range(current_menubar.GetMenuCount()):
                menu_label = current_menubar.GetMenuLabel(i)
                print(f"DEBUG: Menu {i}: {menu_label}")
        else:
            print("DEBUG: WARNING - No menubar found after SetMenuBar!")
        
        # Bind events
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
        self.Bind(wx.EVT_MENU, self.on_about, about_item)
        self.Bind(wx.EVT_MENU, self.on_grid_color_x, grid_color_x_item)
        self.Bind(wx.EVT_MENU, self.on_grid_color_y, grid_color_y_item)
        self.Bind(wx.EVT_MENU, self.on_grid_color_z, grid_color_z_item)
        self.Bind(wx.EVT_MENU, self.on_toggle_grid, grid_toggle_item)
        self.Bind(wx.EVT_MENU, self.on_toggle_axes, axes_toggle_item)
        self.Bind(wx.EVT_MENU, self.on_toggle_projection, projection_item)
        self.Bind(wx.EVT_MENU, self.on_reset_camera, reset_camera_item)
        
        print("DEBUG: Menu events bound successfully")
    
    def on_exit(self, event):
        """Handle exit menu item."""
        print("DEBUG: Exit requested")
        self.Close()
    
    def on_about(self, event):
        """Handle about menu item."""
        info = wx.adv.AboutDialogInfo()
        info.SetName("3D Canvas Grid Color Test")
        info.SetVersion("1.0")
        info.SetDescription("Test application for 3D Canvas grid color selectors.\n\nUse the View menu to change grid colors!")
        info.SetCopyright("(C) 2025")
        
        wx.adv.AboutBox(info, self)
    
    def on_grid_color_x(self, event):
        """Show color picker for X-direction grid lines."""
        print("DEBUG: X grid color picker requested")
        
        current_colors = self.canvas_3d.get_grid_colors()
        current_color = wx.Colour(*current_colors[0])  # X color
        
        data = wx.ColourData()
        data.SetColour(current_color)
        
        dialog = wx.ColourDialog(self, data)
        dialog.SetTitle("Choose X Grid Color")
        
        if dialog.ShowModal() == wx.ID_OK:
            selected_color = dialog.GetColourData().GetColour()
            color_tuple = (selected_color.Red(), selected_color.Green(), selected_color.Blue())
            self.canvas_3d.set_grid_color_x(color_tuple)
            print(f"DEBUG: Set X grid color to {color_tuple}")
        
        dialog.Destroy()
    
    def on_grid_color_y(self, event):
        """Show color picker for Y-direction grid lines."""
        print("DEBUG: Y grid color picker requested")
        
        current_colors = self.canvas_3d.get_grid_colors()
        current_color = wx.Colour(*current_colors[1])  # Y color
        
        data = wx.ColourData()
        data.SetColour(current_color)
        
        dialog = wx.ColourDialog(self, data)
        dialog.SetTitle("Choose Y Grid Color")
        
        if dialog.ShowModal() == wx.ID_OK:
            selected_color = dialog.GetColourData().GetColour()
            color_tuple = (selected_color.Red(), selected_color.Green(), selected_color.Blue())
            self.canvas_3d.set_grid_color_y(color_tuple)
            print(f"DEBUG: Set Y grid color to {color_tuple}")
        
        dialog.Destroy()
    
    def on_grid_color_z(self, event):
        """Show color picker for Z-direction grid lines."""
        print("DEBUG: Z grid color picker requested")
        
        current_colors = self.canvas_3d.get_grid_colors()
        current_color = wx.Colour(*current_colors[2])  # Z color
        
        data = wx.ColourData()
        data.SetColour(current_color)
        
        dialog = wx.ColourDialog(self, data)
        dialog.SetTitle("Choose Z Grid Color")
        
        if dialog.ShowModal() == wx.ID_OK:
            selected_color = dialog.GetColourData().GetColour()
            color_tuple = (selected_color.Red(), selected_color.Green(), selected_color.Blue())
            self.canvas_3d.set_grid_color_z(color_tuple)
            print(f"DEBUG: Set Z grid color to {color_tuple}")
        
        dialog.Destroy()
    
    def on_toggle_grid(self, event):
        """Toggle 3D grid visibility."""
        print("DEBUG: Toggle grid requested")
        
        self.canvas_3d.show_grid = not self.canvas_3d.show_grid
        self.canvas_3d.Refresh()
        print(f"DEBUG: 3D grid {'enabled' if self.canvas_3d.show_grid else 'disabled'}")
    
    def on_toggle_axes(self, event):
        """Toggle 3D axes visibility."""
        print("DEBUG: Toggle axes requested")
        
        self.canvas_3d.show_axes = not self.canvas_3d.show_axes
        self.canvas_3d.Refresh()
        print(f"DEBUG: 3D axes {'enabled' if self.canvas_3d.show_axes else 'disabled'}")
    
    def on_toggle_projection(self, event):
        """Toggle between perspective and orthographic projection."""
        print("DEBUG: Toggle projection requested")
        
        if self.canvas_3d.camera.projection_mode == ProjectionMode.PERSPECTIVE:
            self.canvas_3d.camera.projection_mode = ProjectionMode.ORTHOGRAPHIC
        else:
            self.canvas_3d.camera.projection_mode = ProjectionMode.PERSPECTIVE
        
        self.canvas_3d.Refresh()
        print(f"DEBUG: Switched to {self.canvas_3d.camera.projection_mode.value} projection")
    
    def on_reset_camera(self, event):
        """Reset 3D camera to default position."""
        print("DEBUG: Reset camera requested")
        
        self.canvas_3d.reset_camera()
        print("DEBUG: 3D camera reset to default position")


class Simple3DApp(wx.App):
    """Simple test application for 3D canvas with menubar."""
    
    def OnInit(self):
        # Set app properties for better macOS integration
        self.SetAppName("3D Canvas Grid Test")
        self.SetAppDisplayName("3D Canvas Grid Color Test")
        
        print("DEBUG: Creating application frame...")
        frame = Simple3DFrame()
        
        print("DEBUG: Showing frame...")
        frame.Show()
        
        # Force focus and raise window (helps with macOS menubar)
        frame.Raise()
        frame.SetFocus()
        
        print("DEBUG: Application ready - menubar should be visible!")
        print("DEBUG: Try using the View menu to change grid colors")
        
        return True


if __name__ == "__main__":
    print("="*50)
    print("3D Canvas Grid Color Test")
    print("="*50)
    print("Starting application...")
    
    app = Simple3DApp()
    
    print("DEBUG: Starting main loop...")
    app.MainLoop()
    
    print("DEBUG: Application closed")
