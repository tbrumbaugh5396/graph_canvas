#!/usr/bin/env python3
"""
macOS-specific menubar test with 3D canvas
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


import wx
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import numpy as np
    from graph_canvas.presentation.desktop.gui.3d_canvas import Canvas3D, ProjectionMode
    print("✓ All modules imported successfully")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)


class MacOSFrame(wx.Frame):
    """Frame optimized for macOS menubar display."""
    
    def __init__(self):
        super().__init__(None, 
                        title="3D Canvas - macOS Menubar Test",
                        size=(1000, 700))
        
        print("DEBUG: Frame created")
        
        # Create status bar for feedback
        self.CreateStatusBar()
        self.SetStatusText("Ready - Check screen top for menubar")
        
        # Create 3D canvas
        self.canvas_3d = Canvas3D(self)
        print("DEBUG: 3D Canvas created")
        
        # Set default grid colors to make them visible
        self.canvas_3d.set_grid_color_x((255, 100, 100))  # Red-ish
        self.canvas_3d.set_grid_color_z((100, 100, 255))  # Blue-ish
        
        # Create layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Add instructions at top
        instructions = wx.StaticText(self, label="🔍 MENUBAR LOCATION: Look at the TOP OF YOUR SCREEN for File, View, Tools, Help menus")
        instructions.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        instructions.SetForegroundColour(wx.Colour(0, 100, 0))
        
        sizer.Add(instructions, 0, wx.EXPAND | wx.ALL, 10)
        sizer.Add(self.canvas_3d, 1, wx.EXPAND)
        
        self.SetSizer(sizer)
        
        # Create menubar AFTER layout
        self.setup_macos_menubar()
        
        # Center window
        self.Center()
        
        print("DEBUG: Frame setup complete")
    
    def setup_macos_menubar(self):
        """Create menubar optimized for macOS."""
        print("DEBUG: Creating macOS-optimized menubar...")
        
        # Create menubar
        menubar = wx.MenuBar()
        
        # File menu (required for macOS)
        file_menu = wx.Menu()
        file_menu.Append(wx.ID_NEW, "&New\tCmd+N", "Reset view")
        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_EXIT, "&Quit\tCmd+Q", "Quit application")
        
        # View menu - main functionality
        view_menu = wx.Menu()
        
        # Grid colors (main feature we're testing)
        view_menu.Append(wx.ID_ANY, "X Grid Color (Red Lines)...", "Change X-axis grid color")
        view_menu.Append(wx.ID_ANY, "Y Grid Color (Future)...", "Change Y-axis grid color")
        view_menu.Append(wx.ID_ANY, "Z Grid Color (Blue Lines)...", "Change Z-axis grid color")
        
        view_menu.AppendSeparator()
        
        # Display toggles
        view_menu.Append(wx.ID_ANY, "Toggle Grid\tG", "Show/hide grid")
        view_menu.Append(wx.ID_ANY, "Toggle Axes\tA", "Show/hide coordinate axes")
        
        view_menu.AppendSeparator()
        
        # Camera controls
        view_menu.Append(wx.ID_ANY, "Reset Camera\tR", "Reset camera position")
        view_menu.Append(wx.ID_ANY, "Toggle Projection\tP", "Switch perspective/orthographic")
        
        # Tools menu
        tools_menu = wx.Menu()
        tools_menu.Append(wx.ID_ANY, "Camera Control Mode\tC", "Control camera")
        tools_menu.Append(wx.ID_ANY, "World Control Mode\tW", "Control world")
        
        # Help menu (important for macOS)
        help_menu = wx.Menu()
        help_menu.Append(wx.ID_ANY, "Controls...", "Show controls help")
        help_menu.AppendSeparator()
        help_menu.Append(wx.ID_ABOUT, "&About", "About this application")
        
        # Add menus to menubar
        menubar.Append(file_menu, "&File")
        menubar.Append(view_menu, "&View")
        menubar.Append(tools_menu, "&Tools")
        menubar.Append(help_menu, "&Help")
        
        # Set menubar
        self.SetMenuBar(menubar)
        
        # Verify menubar
        if self.GetMenuBar():
            count = self.GetMenuBar().GetMenuCount()
            print(f"DEBUG: ✓ Menubar created with {count} menus")
        else:
            print("DEBUG: ✗ Menubar creation failed!")
        
        # Store menu items for binding
        self.bind_macos_events()
        
        print("DEBUG: macOS menubar setup complete")
    
    def bind_macos_events(self):
        """Bind menu events."""
        # We'll bind by ID using the menu system
        self.Bind(wx.EVT_MENU, self.on_quit, id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.on_new, id=wx.ID_NEW)
        self.Bind(wx.EVT_MENU, self.on_about, id=wx.ID_ABOUT)
        
        # For custom menu items, we need to bind differently
        # Let's use a simpler approach and rebuild with explicit IDs
        self.rebuild_menubar_with_ids()
    
    def rebuild_menubar_with_ids(self):
        """Rebuild menubar with explicit IDs for easier binding."""
        # Define custom IDs
        ID_X_GRID = wx.NewIdRef()
        ID_Y_GRID = wx.NewIdRef()
        ID_Z_GRID = wx.NewIdRef()
        ID_TOGGLE_GRID = wx.NewIdRef()
        ID_TOGGLE_AXES = wx.NewIdRef()
        ID_RESET_CAMERA = wx.NewIdRef()
        ID_TOGGLE_PROJECTION = wx.NewIdRef()
        ID_CAMERA_MODE = wx.NewIdRef()
        ID_WORLD_MODE = wx.NewIdRef()
        ID_CONTROLS = wx.NewIdRef()
        
        # Create new menubar
        menubar = wx.MenuBar()
        
        # File menu
        file_menu = wx.Menu()
        file_menu.Append(wx.ID_NEW, "&New\tCmd+N", "Reset view")
        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_EXIT, "&Quit\tCmd+Q", "Quit application")
        
        # View menu
        view_menu = wx.Menu()
        view_menu.Append(ID_X_GRID, "X Grid Color (Red)...", "Change X-axis grid color")
        view_menu.Append(ID_Y_GRID, "Y Grid Color...", "Change Y-axis grid color")
        view_menu.Append(ID_Z_GRID, "Z Grid Color (Blue)...", "Change Z-axis grid color")
        view_menu.AppendSeparator()
        view_menu.Append(ID_TOGGLE_GRID, "Toggle Grid\tG", "Show/hide grid")
        view_menu.Append(ID_TOGGLE_AXES, "Toggle Axes\tA", "Show/hide axes")
        view_menu.AppendSeparator()
        view_menu.Append(ID_RESET_CAMERA, "Reset Camera\tR", "Reset camera")
        view_menu.Append(ID_TOGGLE_PROJECTION, "Toggle Projection\tP", "Switch projection")
        
        # Tools menu
        tools_menu = wx.Menu()
        tools_menu.Append(ID_CAMERA_MODE, "Camera Mode\tC", "Control camera")
        tools_menu.Append(ID_WORLD_MODE, "World Mode\tW", "Control world")
        
        # Help menu
        help_menu = wx.Menu()
        help_menu.Append(ID_CONTROLS, "Controls...", "Show controls")
        help_menu.AppendSeparator()
        help_menu.Append(wx.ID_ABOUT, "&About", "About")
        
        # Add to menubar
        menubar.Append(file_menu, "&File")
        menubar.Append(view_menu, "&View")
        menubar.Append(tools_menu, "&Tools")
        menubar.Append(help_menu, "&Help")
        
        # Set menubar
        self.SetMenuBar(menubar)
        
        # Bind events with specific IDs
        self.Bind(wx.EVT_MENU, self.on_quit, id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.on_new, id=wx.ID_NEW)
        self.Bind(wx.EVT_MENU, self.on_about, id=wx.ID_ABOUT)
        
        self.Bind(wx.EVT_MENU, self.on_x_grid_color, id=ID_X_GRID)
        self.Bind(wx.EVT_MENU, self.on_y_grid_color, id=ID_Y_GRID)
        self.Bind(wx.EVT_MENU, self.on_z_grid_color, id=ID_Z_GRID)
        self.Bind(wx.EVT_MENU, self.on_toggle_grid, id=ID_TOGGLE_GRID)
        self.Bind(wx.EVT_MENU, self.on_toggle_axes, id=ID_TOGGLE_AXES)
        self.Bind(wx.EVT_MENU, self.on_reset_camera, id=ID_RESET_CAMERA)
        self.Bind(wx.EVT_MENU, self.on_toggle_projection, id=ID_TOGGLE_PROJECTION)
        self.Bind(wx.EVT_MENU, self.on_camera_mode, id=ID_CAMERA_MODE)
        self.Bind(wx.EVT_MENU, self.on_world_mode, id=ID_WORLD_MODE)
        self.Bind(wx.EVT_MENU, self.on_controls, id=ID_CONTROLS)
        
        print("DEBUG: Menubar rebuilt with explicit IDs and events bound")
    
    # Event handlers
    def on_quit(self, event):
        print("DEBUG: Quit requested")
        self.Close()
    
    def on_new(self, event):
        print("DEBUG: New/Reset requested")
        self.canvas_3d.reset_camera()
        self.canvas_3d.reset_world()
        self.SetStatusText("Reset to defaults")
    
    def on_about(self, event):
        info = wx.adv.AboutDialogInfo()
        info.SetName("3D Canvas macOS Test")
        info.SetVersion("1.0")
        info.SetDescription("Testing 3D Canvas with macOS menubar\n\nGrid colors should work from View menu!")
        wx.adv.AboutBox(info, self)
    
    def on_x_grid_color(self, event):
        print("DEBUG: X Grid Color requested")
        self.SetStatusText("Opening X Grid Color picker...")
        
        current_colors = self.canvas_3d.get_grid_colors()
        current_color = wx.Colour(*current_colors[0])
        
        data = wx.ColourData()
        data.SetColour(current_color)
        
        with wx.ColourDialog(self, data) as dialog:
            dialog.SetTitle("Choose X Grid Color (Red Lines)")
            if dialog.ShowModal() == wx.ID_OK:
                color = dialog.GetColourData().GetColour()
                rgb = (color.Red(), color.Green(), color.Blue())
                self.canvas_3d.set_grid_color_x(rgb)
                self.SetStatusText(f"X grid color set to RGB{rgb}")
                print(f"DEBUG: X grid color changed to {rgb}")
    
    def on_y_grid_color(self, event):
        print("DEBUG: Y Grid Color requested")
        wx.MessageBox("Y Grid Color is reserved for future Y-plane grid lines.\n\nCurrently the grid is only drawn in the XZ plane.",
                     "Y Grid Color", wx.OK | wx.ICON_INFORMATION)
        self.SetStatusText("Y Grid Color - feature reserved for future use")
    
    def on_z_grid_color(self, event):
        print("DEBUG: Z Grid Color requested")
        self.SetStatusText("Opening Z Grid Color picker...")
        
        current_colors = self.canvas_3d.get_grid_colors()
        current_color = wx.Colour(*current_colors[2])
        
        data = wx.ColourData()
        data.SetColour(current_color)
        
        with wx.ColourDialog(self, data) as dialog:
            dialog.SetTitle("Choose Z Grid Color (Blue Lines)")
            if dialog.ShowModal() == wx.ID_OK:
                color = dialog.GetColourData().GetColour()
                rgb = (color.Red(), color.Green(), color.Blue())
                self.canvas_3d.set_grid_color_z(rgb)
                self.SetStatusText(f"Z grid color set to RGB{rgb}")
                print(f"DEBUG: Z grid color changed to {rgb}")
    
    def on_toggle_grid(self, event):
        self.canvas_3d.show_grid = not self.canvas_3d.show_grid
        self.canvas_3d.Refresh()
        status = "Grid visible" if self.canvas_3d.show_grid else "Grid hidden"
        self.SetStatusText(status)
        print(f"DEBUG: {status}")
    
    def on_toggle_axes(self, event):
        self.canvas_3d.show_axes = not self.canvas_3d.show_axes
        self.canvas_3d.Refresh()
        status = "Axes visible" if self.canvas_3d.show_axes else "Axes hidden"
        self.SetStatusText(status)
        print(f"DEBUG: {status}")
    
    def on_reset_camera(self, event):
        self.canvas_3d.reset_camera()
        self.SetStatusText("Camera reset")
        print("DEBUG: Camera reset")
    
    def on_toggle_projection(self, event):
        if self.canvas_3d.camera.projection_mode == ProjectionMode.PERSPECTIVE:
            self.canvas_3d.camera.projection_mode = ProjectionMode.ORTHOGRAPHIC
            mode = "Orthographic"
        else:
            self.canvas_3d.camera.projection_mode = ProjectionMode.PERSPECTIVE
            mode = "Perspective"
        
        self.canvas_3d.Refresh()
        self.SetStatusText(f"Projection: {mode}")
        print(f"DEBUG: Switched to {mode}")
    
    def on_camera_mode(self, event):
        self.canvas_3d.control_mode = "camera"
        self.SetStatusText("Camera control mode active")
        print("DEBUG: Camera control mode")
    
    def on_world_mode(self, event):
        self.canvas_3d.control_mode = "world"
        self.SetStatusText("World control mode active")
        print("DEBUG: World control mode")
    
    def on_controls(self, event):
        help_text = """3D Canvas Controls:

MOUSE:
• Left drag: Rotate camera/world
• Middle drag: Pan camera/world
• Scroll: Zoom

KEYBOARD:
• WASD: Move
• QE: Up/Down
• TAB: Toggle camera/world mode
• P: Toggle projection
• G: Toggle grid
• F1: Toggle axes

MENU:
• View → Grid Colors: Change colors!
• Tools: Switch control modes
"""
        wx.MessageDialog(self, help_text, "Controls Help", wx.OK | wx.ICON_INFORMATION).ShowModal()


class MacOSApp(wx.App):
    """macOS-optimized application."""
    
    def OnInit(self):
        print("DEBUG: Starting macOS application...")
        
        # Set app properties for macOS
        self.SetAppName("3D Canvas Test")
        self.SetAppDisplayName("3D Canvas Grid Colors")
        
        # Create frame
        frame = MacOSFrame()
        
        # Show and activate
        frame.Show()
        frame.Raise()
        
        # On macOS, request user attention to ensure app is active
        if wx.Platform == '__WXMAC__':
            frame.RequestUserAttention(wx.USER_ATTENTION_INFO)
        
        print("DEBUG: Application ready!")
        print("\n" + "="*70)
        print("🍎 macOS MENUBAR INSTRUCTIONS:")
        print("="*70)
        print("1. The menubar appears at the TOP OF YOUR SCREEN, not in the window")
        print("2. Look for: File | View | Tools | Help")
        print("3. Click 'View' menu to see grid color options")
        print("4. Try 'View → X Grid Color (Red)...' to test color picker")
        print("5. The 3D canvas should show a wireframe cube with colored grid")
        print("="*70)
        
        return True


if __name__ == "__main__":
    print("macOS 3D Canvas Menubar Test")
    print(f"wxPython: {wx.version()}")
    print(f"Platform: {wx.Platform}")
    
    app = MacOSApp()
    app.MainLoop()

