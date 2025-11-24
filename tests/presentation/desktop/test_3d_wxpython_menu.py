#!/usr/bin/env python3
"""
3D Canvas test with robust wxPython menubar integration
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
    print(f"✓ wxPython version: {wx.version()}")
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


class TestFrame(wx.Frame):
    """Test frame with robust menubar and 3D canvas."""
    
    def __init__(self):
        # Initialize frame with explicit style to ensure menubar support
        super().__init__(None, 
                        title="3D Canvas with Grid Color Selectors", 
                        size=(1200, 800),
                        style=wx.DEFAULT_FRAME_STYLE)
        
        print("DEBUG: Frame created")
        
        # Set icon if available (helps with app recognition)
        try:
            self.SetIcon(wx.Icon(wx.ArtProvider.GetBitmap(wx.ART_EXECUTABLE_FILE)))
        except:
            pass  # Ignore if icon setting fails
        
        # Create status bar (helps with proper window setup)
        self.CreateStatusBar()
        self.SetStatusText("3D Canvas ready - Use View menu for grid colors")
        
        # Create 3D canvas BEFORE menubar to ensure proper parent-child relationship
        self.canvas_3d = Canvas3D(self)
        print("DEBUG: 3D Canvas created")
        
        # Create menubar
        self.setup_menubar()
        
        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas_3d, 1, wx.EXPAND)
        self.SetSizer(sizer)
        
        # Center and show
        self.Center()
        
        print("DEBUG: Frame setup complete")
    
    def setup_menubar(self):
        """Set up menubar with proper wxPython integration."""
        print("DEBUG: Setting up menubar...")
        
        # Create menubar first
        menubar = wx.MenuBar()
        
        # File menu (essential for proper menubar on macOS)
        file_menu = wx.Menu()
        
        # Add standard file menu items
        new_item = file_menu.Append(wx.ID_NEW, "&New\tCtrl+N", "Create new")
        file_menu.AppendSeparator()
        exit_item = file_menu.Append(wx.ID_EXIT, "E&xit\tCtrl+Q", "Exit application")
        
        # View menu with grid controls
        view_menu = wx.Menu()
        
        # Grid color section
        view_menu.AppendSeparator()
        grid_x_item = view_menu.Append(wx.ID_ANY, "X Grid Color...", "Change X-axis grid color")
        grid_y_item = view_menu.Append(wx.ID_ANY, "Y Grid Color...", "Change Y-axis grid color") 
        grid_z_item = view_menu.Append(wx.ID_ANY, "Z Grid Color...", "Change Z-axis grid color")
        
        view_menu.AppendSeparator()
        
        # View controls
        toggle_grid_item = view_menu.Append(wx.ID_ANY, "Toggle Grid\tG", "Show/hide grid")
        toggle_axes_item = view_menu.Append(wx.ID_ANY, "Toggle Axes\tA", "Show/hide axes")
        
        view_menu.AppendSeparator()
        
        # Camera controls
        reset_camera_item = view_menu.Append(wx.ID_ANY, "Reset Camera\tR", "Reset camera position")
        toggle_projection_item = view_menu.Append(wx.ID_ANY, "Toggle Projection\tP", "Switch perspective/orthographic")
        
        # Tools menu (adds more substance to menubar)
        tools_menu = wx.Menu()
        camera_mode_item = tools_menu.Append(wx.ID_ANY, "Camera Mode\tC", "Switch to camera control")
        world_mode_item = tools_menu.Append(wx.ID_ANY, "World Mode\tW", "Switch to world control")
        
        # Help menu (important for macOS)
        help_menu = wx.Menu()
        controls_item = help_menu.Append(wx.ID_ANY, "Controls Help", "Show control instructions")
        help_menu.AppendSeparator()
        about_item = help_menu.Append(wx.ID_ABOUT, "&About", "About this application")
        
        # Add all menus to menubar
        menubar.Append(file_menu, "&File")
        menubar.Append(view_menu, "&View")
        menubar.Append(tools_menu, "&Tools")
        menubar.Append(help_menu, "&Help")
        
        # Set the menubar - this is the critical step
        self.SetMenuBar(menubar)
        
        # Verify menubar was set
        if self.GetMenuBar():
            menu_count = self.GetMenuBar().GetMenuCount()
            print(f"DEBUG: ✓ Menubar set successfully with {menu_count} menus")
            
            # List all menus for verification
            for i in range(menu_count):
                menu_label = self.GetMenuBar().GetMenuLabel(i)
                print(f"DEBUG:   Menu {i}: '{menu_label}'")
        else:
            print("DEBUG: ✗ ERROR - Menubar not found after SetMenuBar!")
        
        # Bind all events
        self.bind_menu_events(file_menu, view_menu, tools_menu, help_menu,
                             new_item, exit_item, grid_x_item, grid_y_item, grid_z_item,
                             toggle_grid_item, toggle_axes_item, reset_camera_item,
                             toggle_projection_item, camera_mode_item, world_mode_item,
                             controls_item, about_item)
        
        print("DEBUG: Menubar setup complete")
    
    def bind_menu_events(self, file_menu, view_menu, tools_menu, help_menu,
                        new_item, exit_item, grid_x_item, grid_y_item, grid_z_item,
                        toggle_grid_item, toggle_axes_item, reset_camera_item,
                        toggle_projection_item, camera_mode_item, world_mode_item,
                        controls_item, about_item):
        """Bind all menu events."""
        print("DEBUG: Binding menu events...")
        
        # File menu
        self.Bind(wx.EVT_MENU, self.on_new, new_item)
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
        
        # View menu
        self.Bind(wx.EVT_MENU, self.on_grid_color_x, grid_x_item)
        self.Bind(wx.EVT_MENU, self.on_grid_color_y, grid_y_item)
        self.Bind(wx.EVT_MENU, self.on_grid_color_z, grid_z_item)
        self.Bind(wx.EVT_MENU, self.on_toggle_grid, toggle_grid_item)
        self.Bind(wx.EVT_MENU, self.on_toggle_axes, toggle_axes_item)
        self.Bind(wx.EVT_MENU, self.on_reset_camera, reset_camera_item)
        self.Bind(wx.EVT_MENU, self.on_toggle_projection, toggle_projection_item)
        
        # Tools menu
        self.Bind(wx.EVT_MENU, self.on_camera_mode, camera_mode_item)
        self.Bind(wx.EVT_MENU, self.on_world_mode, world_mode_item)
        
        # Help menu
        self.Bind(wx.EVT_MENU, self.on_controls_help, controls_item)
        self.Bind(wx.EVT_MENU, self.on_about, about_item)
        
        print("DEBUG: Menu events bound successfully")
    
    # File menu handlers
    def on_new(self, event):
        """Handle new action."""
        self.canvas_3d.reset_camera()
        self.canvas_3d.reset_world()
        self.SetStatusText("Reset to defaults")
        print("DEBUG: New/Reset performed")
    
    def on_exit(self, event):
        """Handle exit."""
        print("DEBUG: Exit requested")
        self.Close()
    
    # View menu handlers - Grid Colors
    def on_grid_color_x(self, event):
        """Handle X grid color selection."""
        print("DEBUG: X grid color selector opened")
        
        # Get current color
        current_colors = self.canvas_3d.get_grid_colors()
        current_color = wx.Colour(*current_colors[0])
        
        # Show color dialog
        data = wx.ColourData()
        data.SetColour(current_color)
        
        with wx.ColourDialog(self, data) as dialog:
            dialog.SetTitle("Choose X Grid Color")
            
            if dialog.ShowModal() == wx.ID_OK:
                color = dialog.GetColourData().GetColour()
                rgb = (color.Red(), color.Green(), color.Blue())
                self.canvas_3d.set_grid_color_x(rgb)
                self.SetStatusText(f"X grid color set to RGB{rgb}")
                print(f"DEBUG: X grid color changed to {rgb}")
    
    def on_grid_color_y(self, event):
        """Handle Y grid color selection."""
        print("DEBUG: Y grid color selector opened")
        
        current_colors = self.canvas_3d.get_grid_colors()
        current_color = wx.Colour(*current_colors[1])
        
        data = wx.ColourData()
        data.SetColour(current_color)
        
        with wx.ColourDialog(self, data) as dialog:
            dialog.SetTitle("Choose Y Grid Color")
            
            if dialog.ShowModal() == wx.ID_OK:
                color = dialog.GetColourData().GetColour()
                rgb = (color.Red(), color.Green(), color.Blue())
                self.canvas_3d.set_grid_color_y(rgb)
                self.SetStatusText(f"Y grid color set to RGB{rgb}")
                print(f"DEBUG: Y grid color changed to {rgb}")
    
    def on_grid_color_z(self, event):
        """Handle Z grid color selection."""
        print("DEBUG: Z grid color selector opened")
        
        current_colors = self.canvas_3d.get_grid_colors()
        current_color = wx.Colour(*current_colors[2])
        
        data = wx.ColourData()
        data.SetColour(current_color)
        
        with wx.ColourDialog(self, data) as dialog:
            dialog.SetTitle("Choose Z Grid Color")
            
            if dialog.ShowModal() == wx.ID_OK:
                color = dialog.GetColourData().GetColour()
                rgb = (color.Red(), color.Green(), color.Blue())
                self.canvas_3d.set_grid_color_z(rgb)
                self.SetStatusText(f"Z grid color set to RGB{rgb}")
                print(f"DEBUG: Z grid color changed to {rgb}")
    
    # View menu handlers - Display toggles
    def on_toggle_grid(self, event):
        """Toggle grid visibility."""
        self.canvas_3d.show_grid = not self.canvas_3d.show_grid
        self.canvas_3d.Refresh()
        status = "Grid shown" if self.canvas_3d.show_grid else "Grid hidden"
        self.SetStatusText(status)
        print(f"DEBUG: {status}")
    
    def on_toggle_axes(self, event):
        """Toggle axes visibility."""
        self.canvas_3d.show_axes = not self.canvas_3d.show_axes
        self.canvas_3d.Refresh()
        status = "Axes shown" if self.canvas_3d.show_axes else "Axes hidden"
        self.SetStatusText(status)
        print(f"DEBUG: {status}")
    
    def on_reset_camera(self, event):
        """Reset camera."""
        self.canvas_3d.reset_camera()
        self.SetStatusText("Camera reset")
        print("DEBUG: Camera reset")
    
    def on_toggle_projection(self, event):
        """Toggle projection mode."""
        if self.canvas_3d.camera.projection_mode == ProjectionMode.PERSPECTIVE:
            self.canvas_3d.camera.projection_mode = ProjectionMode.ORTHOGRAPHIC
            mode = "Orthographic"
        else:
            self.canvas_3d.camera.projection_mode = ProjectionMode.PERSPECTIVE
            mode = "Perspective"
        
        self.canvas_3d.Refresh()
        self.SetStatusText(f"Projection: {mode}")
        print(f"DEBUG: Switched to {mode} projection")
    
    # Tools menu handlers
    def on_camera_mode(self, event):
        """Switch to camera control mode."""
        self.canvas_3d.control_mode = "camera"
        self.SetStatusText("Camera control mode")
        print("DEBUG: Switched to camera control mode")
    
    def on_world_mode(self, event):
        """Switch to world control mode."""
        self.canvas_3d.control_mode = "world"
        self.SetStatusText("World control mode")
        print("DEBUG: Switched to world control mode")
    
    # Help menu handlers
    def on_controls_help(self, event):
        """Show controls help."""
        help_text = """3D Canvas Controls:

MOUSE:
• Left drag: Rotate camera/world
• Middle drag: Pan camera/world  
• Scroll wheel: Zoom

KEYBOARD:
• WASD: Move forward/back/left/right
• QE: Move up/down
• TAB: Toggle camera/world mode
• P: Toggle projection mode
• G: Toggle grid
• F1: Toggle axes

MENU:
• View → Grid Colors: Change grid colors
• Tools: Switch control modes
• File → New: Reset everything
"""
        
        dialog = wx.MessageDialog(self, help_text, "3D Canvas Controls", 
                                 wx.OK | wx.ICON_INFORMATION)
        dialog.ShowModal()
        dialog.Destroy()
    
    def on_about(self, event):
        """Show about dialog."""
        info = wx.adv.AboutDialogInfo()
        info.SetName("3D Canvas Test")
        info.SetVersion("1.0")
        info.SetDescription("3D Canvas with wxPython integration\nand grid color selectors")
        info.SetCopyright("(C) 2025")
        info.AddDeveloper("3D Canvas Team")
        
        wx.adv.AboutBox(info, self)


class TestApp(wx.App):
    """Test application with proper wxPython setup."""
    
    def OnInit(self):
        """Initialize the application."""
        print("DEBUG: Initializing wxPython application...")
        
        # Set application properties (important for macOS)
        self.SetAppName("3D Canvas Grid Test")
        self.SetAppDisplayName("3D Canvas with Grid Colors")
        
        # Create and show the main frame
        print("DEBUG: Creating main frame...")
        frame = TestFrame()
        
        print("DEBUG: Showing frame...")
        frame.Show(True)
        
        # Ensure the frame is active (critical for macOS menubar)
        frame.Raise()
        frame.SetFocus()
        
        # Additional macOS-specific activation
        if wx.Platform == '__WXMAC__':
            print("DEBUG: macOS detected - applying additional activation")
            frame.RequestUserAttention(wx.USER_ATTENTION_INFO)
        
        self.SetTopWindow(frame)
        
        print("DEBUG: Application initialization complete")
        print("=" * 60)
        print("MENUBAR CHECK:")
        print("• On macOS: Look for menubar at TOP OF SCREEN")
        print("• On Windows/Linux: Look for menubar at TOP OF WINDOW")
        print("• Expected menus: File, View, Tools, Help")
        print("• Try: View menu → X Grid Color...")
        print("=" * 60)
        
        return True


def main():
    """Main application entry point."""
    print("wxPython 3D Canvas with Grid Color Selectors")
    print("=" * 50)
    
    # Create and run the application
    app = TestApp()
    
    # Run the main event loop
    print("DEBUG: Starting main event loop...")
    app.MainLoop()
    
    print("DEBUG: Application closed")


if __name__ == "__main__":
    main()

