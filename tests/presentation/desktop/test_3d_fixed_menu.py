#!/usr/bin/env python3
"""
Fixed 3D Canvas test with guaranteed menubar visibility on macOS
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
    from graph_canvas.presentation.desktop.gui.canvas_3d import Canvas3D, ProjectionMode
    print("✓ Modules imported successfully")
except ImportError as e:
    print(f"✗ Import error: {e}")
    # Still continue to test menubar without 3D canvas
    Canvas3D = None
    ProjectionMode = None


class Fixed3DFrame(wx.Frame):
    """3D Frame with forced menubar visibility."""
    
    def __init__(self):
        # Force standard frame style
        super().__init__(None, 
                        title="3D Canvas - FIXED Menubar Test",
                        size=(1000, 700),
                        style=wx.DEFAULT_FRAME_STYLE)
        
        print("Creating frame...")
        
        # Create status bar immediately
        self.CreateStatusBar()
        self.SetStatusText("🔍 LOOK AT TOP OF SCREEN for File, View, Tools, Help menubar")
        
        # Create the main content
        self.setup_content()
        
        # Create menubar LAST (sometimes helps with macOS)
        self.create_forced_menubar()
        
        # Force window properties
        self.Center()
        
        print("Frame created - checking for menubar...")
        
        # Verify menubar exists
        menubar = self.GetMenuBar()
        if menubar:
            print(f"✓ Menubar found with {menubar.GetMenuCount()} menus")
        else:
            print("✗ NO MENUBAR FOUND!")
    
    def setup_content(self):
        """Set up the main content area."""
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Instructions
        instructions = wx.StaticText(panel, label="""
🔍 MENUBAR LOCATION CHECK:

On macOS: Look at the TOP OF YOUR SCREEN for the menubar
Expected menus: File | View | Tools | Help

If you can't see the menubar:
1. Make sure this window is active (click on it)
2. Try Cmd+Tab to switch to this app
3. Look at the very top edge of your screen
4. The menubar should appear next to the Apple logo

TEST: Try View → X Grid Color to test functionality
        """)
        instructions.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        
        sizer.Add(instructions, 0, wx.EXPAND | wx.ALL, 10)
        
        # Add 3D canvas if available
        if Canvas3D:
            try:
                self.canvas_3d = Canvas3D(panel)
                self.canvas_3d.set_grid_color_x((255, 0, 0))  # Red
                self.canvas_3d.set_grid_color_z((0, 0, 255))  # Blue
                sizer.Add(self.canvas_3d, 1, wx.EXPAND | wx.ALL, 5)
                print("✓ 3D Canvas added")
            except Exception as e:
                print(f"✗ 3D Canvas error: {e}")
                self.canvas_3d = None
                # Add placeholder
                placeholder = wx.StaticText(panel, label="3D Canvas failed to load\nMenubar should still work")
                sizer.Add(placeholder, 1, wx.EXPAND | wx.ALL, 10)
        else:
            self.canvas_3d = None
            placeholder = wx.StaticText(panel, label="3D Canvas not available\nTesting menubar only")
            sizer.Add(placeholder, 1, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        
        # Main sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(panel, 1, wx.EXPAND)
        self.SetSizer(main_sizer)
    
    def create_forced_menubar(self):
        """Create menubar with forced visibility."""
        print("Creating forced menubar...")
        
        # Create menubar
        menubar = wx.MenuBar()
        
        # File menu (REQUIRED for macOS)
        file_menu = wx.Menu()
        file_menu.Append(wx.ID_NEW, "&New\tCmd+N", "Reset everything")
        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_EXIT, "&Quit\tCmd+Q", "Quit application")
        
        # View menu (our main functionality)
        view_menu = wx.Menu()
        
        # Use wx.NewIdRef() for custom menu items
        self.ID_X_GRID = wx.NewIdRef()
        self.ID_Y_GRID = wx.NewIdRef()
        self.ID_Z_GRID = wx.NewIdRef()
        self.ID_TOGGLE_GRID = wx.NewIdRef()
        self.ID_TOGGLE_AXES = wx.NewIdRef()
        self.ID_RESET_CAMERA = wx.NewIdRef()
        
        view_menu.Append(self.ID_X_GRID, "🔴 X Grid Color...", "Change X-axis grid color (red lines)")
        view_menu.Append(self.ID_Y_GRID, "🟡 Y Grid Color...", "Change Y-axis grid color")
        view_menu.Append(self.ID_Z_GRID, "🔵 Z Grid Color...", "Change Z-axis grid color (blue lines)")
        view_menu.AppendSeparator()
        view_menu.Append(self.ID_TOGGLE_GRID, "Toggle Grid\tG", "Show/hide grid")
        view_menu.Append(self.ID_TOGGLE_AXES, "Toggle Axes\tA", "Show/hide axes")
        view_menu.AppendSeparator()
        view_menu.Append(self.ID_RESET_CAMERA, "Reset View\tR", "Reset camera and view")
        
        # Tools menu
        tools_menu = wx.Menu()
        tools_menu.Append(wx.ID_ANY, "Test Menu Item", "Test if menus work")
        
        # Help menu (IMPORTANT for macOS)
        help_menu = wx.Menu()
        help_menu.Append(wx.ID_HELP, "Show Help", "Show help information")
        help_menu.AppendSeparator()
        help_menu.Append(wx.ID_ABOUT, "&About", "About this application")
        
        # Add menus to menubar
        menubar.Append(file_menu, "&File")
        menubar.Append(view_menu, "&View")
        menubar.Append(tools_menu, "&Tools")
        menubar.Append(help_menu, "&Help")
        
        print("Setting menubar...")
        
        # Set the menubar
        self.SetMenuBar(menubar)
        
        # Force menubar refresh
        self.Layout()
        self.Refresh()
        
        # Verify immediately
        current_menubar = self.GetMenuBar()
        if current_menubar:
            count = current_menubar.GetMenuCount()
            print(f"✓ Menubar set successfully: {count} menus")
            
            # List menu names
            for i in range(count):
                name = current_menubar.GetMenuLabel(i)
                print(f"  Menu {i}: {name}")
        else:
            print("✗ FAILED: No menubar after SetMenuBar!")
            # Try alternative approach
            self.force_menubar_alternative()
            return
        
        # Bind events
        self.bind_menu_events()
        
        print("Menubar creation complete")
    
    def force_menubar_alternative(self):
        """Alternative menubar creation method."""
        print("Trying alternative menubar approach...")
        
        # Sometimes destroying and recreating helps
        self.SetMenuBar(None)
        
        # Wait a moment
        wx.MilliSleep(100)
        
        # Try simpler menubar
        simple_menubar = wx.MenuBar()
        
        # Just File and Help (minimal for macOS)
        file_menu = wx.Menu()
        file_menu.Append(wx.ID_EXIT, "Quit", "Quit")
        
        help_menu = wx.Menu()  
        help_menu.Append(wx.ID_ABOUT, "About", "About")
        
        simple_menubar.Append(file_menu, "File")
        simple_menubar.Append(help_menu, "Help")
        
        self.SetMenuBar(simple_menubar)
        
        if self.GetMenuBar():
            print("✓ Alternative menubar worked")
        else:
            print("✗ Alternative menubar also failed")
    
    def bind_menu_events(self):
        """Bind menu events."""
        print("Binding menu events...")
        
        # Standard menu items
        self.Bind(wx.EVT_MENU, self.on_quit, id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.on_new, id=wx.ID_NEW)
        self.Bind(wx.EVT_MENU, self.on_about, id=wx.ID_ABOUT)
        self.Bind(wx.EVT_MENU, self.on_help, id=wx.ID_HELP)
        
        # Custom menu items
        self.Bind(wx.EVT_MENU, self.on_x_grid_color, id=self.ID_X_GRID)
        self.Bind(wx.EVT_MENU, self.on_y_grid_color, id=self.ID_Y_GRID)
        self.Bind(wx.EVT_MENU, self.on_z_grid_color, id=self.ID_Z_GRID)
        self.Bind(wx.EVT_MENU, self.on_toggle_grid, id=self.ID_TOGGLE_GRID)
        self.Bind(wx.EVT_MENU, self.on_toggle_axes, id=self.ID_TOGGLE_AXES)
        self.Bind(wx.EVT_MENU, self.on_reset_camera, id=self.ID_RESET_CAMERA)
        
        print("Menu events bound")
    
    # Event handlers
    def on_quit(self, event):
        print("Quit requested")
        self.Close()
    
    def on_new(self, event):
        print("New/Reset requested")
        if self.canvas_3d:
            self.canvas_3d.reset_camera()
            self.canvas_3d.reset_world()
        self.SetStatusText("Reset complete")
    
    def on_about(self, event):
        wx.MessageBox("3D Canvas Menubar Test\n\nIf you can see this dialog, the menubar is working!\n\nTry View → Grid Colors to test 3D functionality.",
                     "About", wx.OK | wx.ICON_INFORMATION)
    
    def on_help(self, event):
        help_text = """MENUBAR HELP:

If you can see this dialog, the menubar IS working!

MENUBAR LOCATION:
• macOS: At the TOP OF YOUR SCREEN (next to Apple logo)
• Windows/Linux: At the top of this window

TO TEST GRID COLORS:
1. Click 'View' in the menubar
2. Click 'X Grid Color...' or 'Z Grid Color...'
3. Choose a color in the color picker
4. See the grid lines change color

CONTROLS:
• Mouse drag: Rotate view
• Scroll: Zoom
• WASD: Move camera
"""
        wx.MessageDialog(self, help_text, "Menubar Help", wx.OK | wx.ICON_INFORMATION).ShowModal()
    
    def on_x_grid_color(self, event):
        print("X Grid Color requested")
        self.SetStatusText("Opening X Grid color picker...")
        
        if not self.canvas_3d:
            wx.MessageBox("3D Canvas not available, but menubar is working!", "X Grid Color", wx.OK | wx.ICON_INFORMATION)
            return
        
        try:
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
                    print(f"X grid color changed to {rgb}")
        except Exception as e:
            print(f"Error in X grid color: {e}")
            wx.MessageBox(f"Error changing X grid color: {e}", "Error", wx.OK | wx.ICON_ERROR)
    
    def on_y_grid_color(self, event):
        print("Y Grid Color requested")
        wx.MessageBox("Y Grid Color menu item works!\n\n(Y grids are not yet implemented in the 3D canvas)", 
                     "Y Grid Color", wx.OK | wx.ICON_INFORMATION)
        self.SetStatusText("Y Grid Color menu works!")
    
    def on_z_grid_color(self, event):
        print("Z Grid Color requested")
        self.SetStatusText("Opening Z Grid color picker...")
        
        if not self.canvas_3d:
            wx.MessageBox("3D Canvas not available, but menubar is working!", "Z Grid Color", wx.OK | wx.ICON_INFORMATION)
            return
        
        try:
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
                    print(f"Z grid color changed to {rgb}")
        except Exception as e:
            print(f"Error in Z grid color: {e}")
            wx.MessageBox(f"Error changing Z grid color: {e}", "Error", wx.OK | wx.ICON_ERROR)
    
    def on_toggle_grid(self, event):
        print("Toggle grid requested")
        if self.canvas_3d:
            self.canvas_3d.show_grid = not self.canvas_3d.show_grid
            self.canvas_3d.Refresh()
            status = "Grid visible" if self.canvas_3d.show_grid else "Grid hidden"
            self.SetStatusText(status)
        else:
            wx.MessageBox("Grid toggle menu works!\n\n(3D Canvas not available)", "Toggle Grid", wx.OK | wx.ICON_INFORMATION)
    
    def on_toggle_axes(self, event):
        print("Toggle axes requested")
        if self.canvas_3d:
            self.canvas_3d.show_axes = not self.canvas_3d.show_axes
            self.canvas_3d.Refresh()
            status = "Axes visible" if self.canvas_3d.show_axes else "Axes hidden"
            self.SetStatusText(status)
        else:
            wx.MessageBox("Axes toggle menu works!\n\n(3D Canvas not available)", "Toggle Axes", wx.OK | wx.ICON_INFORMATION)
    
    def on_reset_camera(self, event):
        print("Reset camera requested")
        if self.canvas_3d:
            self.canvas_3d.reset_camera()
            self.SetStatusText("Camera reset")
        else:
            wx.MessageBox("Reset menu works!\n\n(3D Canvas not available)", "Reset Camera", wx.OK | wx.ICON_INFORMATION)


class Fixed3DApp(wx.App):
    """Application with forced menubar activation."""
    
    def OnInit(self):
        print("Starting Fixed 3D App...")
        
        # Set app properties for macOS
        self.SetAppName("3D Canvas Fixed Test")
        self.SetAppDisplayName("3D Canvas - Fixed Menubar")
        
        # Create main frame
        frame = Fixed3DFrame()
        
        # Show frame
        frame.Show()
        
        # FORCE activation (critical for macOS menubar)
        frame.Raise()
        frame.SetFocus()
        
        # Additional macOS activation
        if wx.Platform == '__WXMAC__':
            print("Applying macOS-specific activation...")
            # Request user attention to force app to foreground
            frame.RequestUserAttention(wx.USER_ATTENTION_INFO)
            
            # Set as top window
            self.SetTopWindow(frame)
        
        # Final verification
        wx.CallAfter(self.verify_menubar, frame)
        
        print("App initialization complete")
        return True
    
    def verify_menubar(self, frame):
        """Verify menubar after app is fully loaded."""
        print("\n" + "="*60)
        print("MENUBAR VERIFICATION:")
        
        menubar = frame.GetMenuBar()
        if menubar:
            count = menubar.GetMenuCount()
            print(f"✓ SUCCESS: Menubar found with {count} menus")
            print("📍 LOCATION: Look at TOP OF YOUR SCREEN (macOS) or top of window")
            print("🎯 TEST: Click 'View' → 'X Grid Color...' to test functionality")
        else:
            print("✗ FAILED: No menubar found")
            print("💡 TRY: Run test_basic_menubar.py to test without 3D canvas")
        
        print("="*60)


def main():
    """Main entry point."""
    print("3D Canvas - FIXED Menubar Test")
    print("="*40)
    print(f"Platform: {wx.Platform}")
    print(f"wxPython: {wx.version()}")
    print()
    
    # Create and run app
    app = Fixed3DApp()
    app.MainLoop()


if __name__ == "__main__":
    main()

