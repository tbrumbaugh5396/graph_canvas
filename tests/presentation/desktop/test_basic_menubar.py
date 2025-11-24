#!/usr/bin/env python3
"""
Basic wxPython menubar test - no 3D canvas, just menubar
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


class BasicMenuFrame(wx.Frame):
    """Minimal frame to test menubar functionality."""
    
    def __init__(self):
        super().__init__(None, title="Basic Menubar Test", size=(600, 400))
        
        # Create a simple panel
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Add some text
        text = wx.StaticText(panel, label="Basic Menubar Test\n\nCheck if you can see a menubar above.\nTry clicking File → Test Color or View → Grid Options")
        text.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        
        sizer.Add(text, 1, wx.EXPAND | wx.ALL, 20)
        panel.SetSizer(sizer)
        
        # Create menubar
        self.create_menubar()
        
        # Create status bar
        self.CreateStatusBar()
        self.SetStatusText("Ready - Check menubar visibility")
        
        print("Frame created with menubar")
    
    def create_menubar(self):
        """Create a simple menubar."""
        print("Creating menubar...")
        
        # Create menubar
        menubar = wx.MenuBar()
        
        # File menu
        file_menu = wx.Menu()
        test_color_item = file_menu.Append(wx.ID_ANY, "Test Color...", "Test color picker")
        file_menu.AppendSeparator()
        exit_item = file_menu.Append(wx.ID_EXIT, "Exit\tCtrl+Q", "Exit application")
        
        # View menu
        view_menu = wx.Menu()
        
        # Grid submenu
        grid_submenu = wx.Menu()
        x_grid_item = grid_submenu.Append(wx.ID_ANY, "X Grid Color...", "Set X grid color")
        y_grid_item = grid_submenu.Append(wx.ID_ANY, "Y Grid Color...", "Set Y grid color")
        z_grid_item = grid_submenu.Append(wx.ID_ANY, "Z Grid Color...", "Set Z grid color")
        
        view_menu.AppendSubMenu(grid_submenu, "Grid Options", "Grid color options")
        view_menu.AppendSeparator()
        view_menu.Append(wx.ID_ANY, "Reset View", "Reset to default view")
        
        # Help menu
        help_menu = wx.Menu()
        about_item = help_menu.Append(wx.ID_ABOUT, "About", "About this test")
        
        # Add menus to menubar
        menubar.Append(file_menu, "&File")
        menubar.Append(view_menu, "&View")
        menubar.Append(help_menu, "&Help")
        
        # Set menubar
        self.SetMenuBar(menubar)
        print("Menubar set")
        
        # Verify
        if self.GetMenuBar():
            print(f"✓ Menubar verified with {self.GetMenuBar().GetMenuCount()} menus")
        else:
            print("✗ No menubar found!")
        
        # Bind events
        self.Bind(wx.EVT_MENU, self.on_test_color, test_color_item)
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
        self.Bind(wx.EVT_MENU, self.on_x_grid, x_grid_item)
        self.Bind(wx.EVT_MENU, self.on_y_grid, y_grid_item)
        self.Bind(wx.EVT_MENU, self.on_z_grid, z_grid_item)
        self.Bind(wx.EVT_MENU, self.on_about, about_item)
        
        print("Menu events bound")
    
    def on_test_color(self, event):
        """Test color picker."""
        print("Color picker requested")
        
        data = wx.ColourData()
        data.SetColour(wx.Colour(255, 0, 0))
        
        dialog = wx.ColourDialog(self, data)
        dialog.SetTitle("Test Color Picker")
        
        if dialog.ShowModal() == wx.ID_OK:
            color = dialog.GetColourData().GetColour()
            rgb = (color.Red(), color.Green(), color.Blue())
            self.SetStatusText(f"Selected color: RGB{rgb}")
            print(f"Color selected: {rgb}")
            
            # Show confirmation
            wx.MessageBox(f"You selected RGB: {rgb}", "Color Selected", wx.OK | wx.ICON_INFORMATION)
        
        dialog.Destroy()
    
    def on_exit(self, event):
        """Exit application."""
        print("Exit requested")
        self.Close()
    
    def on_x_grid(self, event):
        """X grid color."""
        print("X grid color requested")
        wx.MessageBox("X Grid Color selected!\n\nThis would change X grid color in the 3D canvas.", 
                     "X Grid Color", wx.OK | wx.ICON_INFORMATION)
        self.SetStatusText("X Grid Color menu item worked!")
    
    def on_y_grid(self, event):
        """Y grid color."""
        print("Y grid color requested")
        wx.MessageBox("Y Grid Color selected!", "Y Grid Color", wx.OK | wx.ICON_INFORMATION)
        self.SetStatusText("Y Grid Color menu item worked!")
    
    def on_z_grid(self, event):
        """Z grid color."""
        print("Z grid color requested")
        wx.MessageBox("Z Grid Color selected!", "Z Grid Color", wx.OK | wx.ICON_INFORMATION)
        self.SetStatusText("Z Grid Color menu item worked!")
    
    def on_about(self, event):
        """About dialog."""
        wx.MessageBox("Basic Menubar Test\n\nThis tests if wxPython menubars work properly on your system.",
                     "About", wx.OK | wx.ICON_INFORMATION)


class BasicMenuApp(wx.App):
    """Basic menu test application."""
    
    def OnInit(self):
        print("Starting basic menubar test...")
        
        # Set app properties
        self.SetAppName("Basic Menu Test")
        self.SetAppDisplayName("wxPython Menubar Test")
        
        # Create frame
        frame = BasicMenuFrame()
        frame.Show()
        
        # Activate window
        frame.Raise()
        frame.SetFocus()
        
        print("Application ready")
        print("\nMENUBAR CHECK:")
        print("1. Look for File, View, Help menus")
        print("2. Try File → Test Color...")
        print("3. Try View → Grid Options → X Grid Color...")
        print("4. On macOS: menubar should be at top of screen")
        print("5. On Windows/Linux: menubar should be at top of window")
        
        return True


if __name__ == "__main__":
    print("wxPython Basic Menubar Test")
    print("=" * 30)
    print(f"wxPython version: {wx.version()}")
    print(f"Platform: {wx.Platform}")
    print()
    
    app = BasicMenuApp()
    app.MainLoop()
    
    print("Test completed")

