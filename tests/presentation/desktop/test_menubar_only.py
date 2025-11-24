#!/usr/bin/env python3
"""
Minimal test to verify wxPython menubar visibility on macOS
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


class MenuBarTestFrame(wx.Frame):
    """Minimal frame to test menubar visibility."""
    
    def __init__(self):
        super().__init__(None, title="Menubar Test - Check if you can see the menubar", size=(800, 600))
        
        # Create a simple panel with instructions
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Instructions
        text = wx.StaticText(panel, label="""
Menubar Visibility Test

If you can see this window, check if there's a menubar at the top.

Expected menubar structure:
- File menu (with Exit)
- Test menu (with Grid Colors submenu)
- Help menu (with About)

On macOS: The menubar should appear at the top of the screen
On Windows/Linux: The menubar should appear at the top of this window

If you don't see a menubar, there may be a wxPython setup issue.
        """)
        
        sizer.Add(text, 1, wx.EXPAND | wx.ALL, 20)
        panel.SetSizer(sizer)
        
        # Create menubar
        self.create_test_menubar()
        
        # Center the window
        self.Center()
        
        print("="*60)
        print("MENUBAR TEST INSTRUCTIONS:")
        print("1. Look for a menubar (File, Test, Help)")
        print("2. On macOS: menubar should be at top of screen")
        print("3. On Windows/Linux: menubar should be at top of window")
        print("4. Try clicking 'Test > Grid Colors > X Grid Color...'")
        print("="*60)
    
    def create_test_menubar(self):
        """Create test menubar."""
        print("Creating test menubar...")
        
        # Create menus
        file_menu = wx.Menu()
        exit_item = file_menu.Append(wx.ID_EXIT, "E&xit\tCtrl+Q", "Exit the test")
        
        test_menu = wx.Menu()
        
        # Grid colors submenu
        grid_submenu = wx.Menu()
        x_color_item = grid_submenu.Append(wx.ID_ANY, "X Grid Color...", "Test X grid color")
        y_color_item = grid_submenu.Append(wx.ID_ANY, "Y Grid Color...", "Test Y grid color")
        z_color_item = grid_submenu.Append(wx.ID_ANY, "Z Grid Color...", "Test Z grid color")
        
        test_menu.AppendSubMenu(grid_submenu, "Grid Colors", "Grid color options")
        test_menu.AppendSeparator()
        test_menu.Append(wx.ID_ANY, "Test Item", "A test menu item")
        
        help_menu = wx.Menu()
        about_item = help_menu.Append(wx.ID_ABOUT, "&About", "About this test")
        
        # Create menubar
        menubar = wx.MenuBar()
        menubar.Append(file_menu, "&File")
        menubar.Append(test_menu, "&Test")
        menubar.Append(help_menu, "&Help")
        
        # Set menubar
        print("Setting menubar...")
        self.SetMenuBar(menubar)
        
        # Verify
        current_menubar = self.GetMenuBar()
        if current_menubar:
            count = current_menubar.GetMenuCount()
            print(f"✓ Menubar set successfully with {count} menus")
            for i in range(count):
                label = current_menubar.GetMenuLabel(i)
                print(f"  Menu {i}: {label}")
        else:
            print("✗ ERROR: Menubar not found after SetMenuBar!")
        
        # Bind events
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
        self.Bind(wx.EVT_MENU, self.on_about, about_item)
        self.Bind(wx.EVT_MENU, self.on_test_x_color, x_color_item)
        self.Bind(wx.EVT_MENU, self.on_test_y_color, y_color_item)
        self.Bind(wx.EVT_MENU, self.on_test_z_color, z_color_item)
        
        print("Menu events bound")
    
    def on_exit(self, event):
        print("Exit requested")
        self.Close()
    
    def on_about(self, event):
        wx.MessageBox("This is a menubar visibility test.\n\nIf you can see this dialog, the menubar is working!",
                     "About Menubar Test", wx.OK | wx.ICON_INFORMATION)
    
    def on_test_x_color(self, event):
        print("X Grid Color menu item clicked!")
        data = wx.ColourData()
        data.SetColour(wx.Colour(255, 0, 0))  # Default to red
        
        dialog = wx.ColourDialog(self, data)
        dialog.SetTitle("Test X Grid Color Picker")
        
        if dialog.ShowModal() == wx.ID_OK:
            color = dialog.GetColourData().GetColour()
            print(f"Selected color: R={color.Red()}, G={color.Green()}, B={color.Blue()}")
            wx.MessageBox(f"You selected:\nRed: {color.Red()}\nGreen: {color.Green()}\nBlue: {color.Blue()}",
                         "Color Selected", wx.OK | wx.ICON_INFORMATION)
        
        dialog.Destroy()
    
    def on_test_y_color(self, event):
        print("Y Grid Color menu item clicked!")
        wx.MessageBox("Y Grid Color menu is working!", "Menu Test", wx.OK | wx.ICON_INFORMATION)
    
    def on_test_z_color(self, event):
        print("Z Grid Color menu item clicked!")
        wx.MessageBox("Z Grid Color menu is working!", "Menu Test", wx.OK | wx.ICON_INFORMATION)


class MenuBarTestApp(wx.App):
    """Test application for menubar visibility."""
    
    def OnInit(self):
        print("Initializing menubar test app...")
        
        # Set app properties (important for macOS)
        self.SetAppName("Menubar Test")
        self.SetAppDisplayName("wxPython Menubar Test")
        
        frame = MenuBarTestFrame()
        frame.Show()
        
        # Force window to front (important for macOS menubar activation)
        frame.Raise()
        frame.SetFocus()
        
        print("Test app ready! Check for menubar visibility.")
        return True


if __name__ == "__main__":
    print("wxPython Menubar Visibility Test")
    print("="*40)
    
    try:
        import wx
        print(f"✓ wxPython version: {wx.version()}")
    except ImportError as e:
        print(f"✗ wxPython not available: {e}")
        exit(1)
    
    print("Starting menubar test...")
    app = MenuBarTestApp()
    app.MainLoop()
    print("Test completed.")

