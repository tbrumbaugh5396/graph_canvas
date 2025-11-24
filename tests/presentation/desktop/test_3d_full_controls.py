#!/usr/bin/env python3
"""
Complete 3D Canvas test with all movement and speed controls
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


class FullControlsFrame(wx.Frame):
    """Frame demonstrating all 3D canvas controls and settings."""
    
    def __init__(self):
        super().__init__(None, 
                        title="3D Canvas - Complete Controls Demo",
                        size=(1200, 800))
        
        # Create status bar
        self.CreateStatusBar()
        self.SetStatusText("Ready - Check menubar for Grid Colors and Movement Controls")
        
        # Create main panel
        main_panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Create 3D canvas
        self.canvas_3d = Canvas3D(main_panel)
        
        # Set some nice initial colors
        self.canvas_3d.set_grid_color_x((255, 100, 100))  # Red
        self.canvas_3d.set_grid_color_z((100, 100, 255))  # Blue
        
        # Create control panel
        control_panel = self.create_control_panel(main_panel)
        
        # Layout
        main_sizer.Add(self.canvas_3d, 3, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(control_panel, 1, wx.EXPAND | wx.ALL, 5)
        main_panel.SetSizer(main_sizer)
        
        # Create menubar
        self.create_complete_menubar()
        
        # Center window
        self.Center()
        
        print("Full controls demo ready!")
    
    def create_control_panel(self, parent):
        """Create a control panel showing current settings."""
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Title
        title = wx.StaticText(panel, label="Movement Settings")
        title.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(title, 0, wx.ALL, 5)
        
        # Current settings display
        self.settings_text = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.settings_text.SetFont(wx.Font(9, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sizer.Add(self.settings_text, 1, wx.EXPAND | wx.ALL, 5)
        
        # Update button
        update_btn = wx.Button(panel, label="Refresh Settings")
        update_btn.Bind(wx.EVT_BUTTON, self.on_update_settings)
        sizer.Add(update_btn, 0, wx.EXPAND | wx.ALL, 5)
        
        # Quick test buttons
        test_label = wx.StaticText(panel, label="Quick Tests:")
        test_label.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(test_label, 0, wx.ALL, 5)
        
        # Test buttons
        fast_btn = wx.Button(panel, label="Fast Mode")
        fast_btn.Bind(wx.EVT_BUTTON, self.on_fast_mode)
        sizer.Add(fast_btn, 0, wx.EXPAND | wx.ALL, 2)
        
        slow_btn = wx.Button(panel, label="Slow Mode")
        slow_btn.Bind(wx.EVT_BUTTON, self.on_slow_mode)
        sizer.Add(slow_btn, 0, wx.EXPAND | wx.ALL, 2)
        
        invert_btn = wx.Button(panel, label="Toggle All Inverts")
        invert_btn.Bind(wx.EVT_BUTTON, self.on_toggle_inverts)
        sizer.Add(invert_btn, 0, wx.EXPAND | wx.ALL, 2)
        
        reset_btn = wx.Button(panel, label="Reset All Settings")
        reset_btn.Bind(wx.EVT_BUTTON, self.on_reset_settings)
        sizer.Add(reset_btn, 0, wx.EXPAND | wx.ALL, 2)
        
        panel.SetSizer(sizer)
        
        # Initial settings update
        wx.CallAfter(self.update_settings_display)
        
        return panel
    
    def create_complete_menubar(self):
        """Create complete menubar with all controls."""
        menubar = wx.MenuBar()
        
        # File menu
        file_menu = wx.Menu()
        file_menu.Append(wx.ID_NEW, "&New\tCmd+N", "Reset everything")
        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_EXIT, "&Quit\tCmd+Q", "Quit")
        
        # View menu
        view_menu = wx.Menu()
        
        # Grid colors submenu
        grid_submenu = wx.Menu()
        self.ID_X_GRID = wx.NewIdRef()
        self.ID_Y_GRID = wx.NewIdRef()
        self.ID_Z_GRID = wx.NewIdRef()
        
        grid_submenu.Append(self.ID_X_GRID, "🔴 X Grid Color...", "Change X grid color")
        grid_submenu.Append(self.ID_Y_GRID, "🟡 Y Grid Color...", "Change Y grid color")
        grid_submenu.Append(self.ID_Z_GRID, "🔵 Z Grid Color...", "Change Z grid color")
        
        view_menu.AppendSubMenu(grid_submenu, "Grid Colors", "Change grid colors")
        view_menu.AppendSeparator()
        
        # Display toggles
        self.ID_TOGGLE_GRID = wx.NewIdRef()
        self.ID_TOGGLE_AXES = wx.NewIdRef()
        
        view_menu.Append(self.ID_TOGGLE_GRID, "Toggle Grid\tG", "Show/hide grid")
        view_menu.Append(self.ID_TOGGLE_AXES, "Toggle Axes\tA", "Show/hide axes")
        
        # Movement menu
        movement_menu = wx.Menu()
        
        # Inversion options
        invert_submenu = wx.Menu()
        self.ID_INVERT_MOUSE_X = wx.NewIdRef()
        self.ID_INVERT_MOUSE_Y = wx.NewIdRef()
        self.ID_INVERT_MOVEMENT = wx.NewIdRef()
        
        invert_submenu.Append(self.ID_INVERT_MOUSE_X, "Invert Mouse X", "Invert horizontal mouse")
        invert_submenu.Append(self.ID_INVERT_MOUSE_Y, "Invert Mouse Y", "Invert vertical mouse")
        invert_submenu.Append(self.ID_INVERT_MOVEMENT, "Invert Keyboard", "Invert WASD keys")
        
        movement_menu.AppendSubMenu(invert_submenu, "Inversion Options", "Mouse and keyboard inversion")
        movement_menu.AppendSeparator()
        
        # Speed settings submenu
        speed_submenu = wx.Menu()
        self.ID_ROTATION_SPEED = wx.NewIdRef()
        self.ID_PAN_SPEED = wx.NewIdRef()
        self.ID_MOVE_SPEED = wx.NewIdRef()
        self.ID_ZOOM_SPEED = wx.NewIdRef()
        
        speed_submenu.Append(self.ID_ROTATION_SPEED, "Mouse Rotation Speed...", "Set rotation speed")
        speed_submenu.Append(self.ID_PAN_SPEED, "Mouse Pan Speed...", "Set pan speed")
        speed_submenu.Append(self.ID_MOVE_SPEED, "Keyboard Speed...", "Set keyboard speed")
        speed_submenu.Append(self.ID_ZOOM_SPEED, "Zoom Speed...", "Set zoom speed")
        
        movement_menu.AppendSubMenu(speed_submenu, "Speed Settings", "Adjust movement speeds")
        
        # Tools menu
        tools_menu = wx.Menu()
        self.ID_CAMERA_MODE = wx.NewIdRef()
        self.ID_WORLD_MODE = wx.NewIdRef()
        self.ID_TOGGLE_PROJECTION = wx.NewIdRef()
        
        tools_menu.Append(self.ID_CAMERA_MODE, "Camera Mode\tC", "Control camera")
        tools_menu.Append(self.ID_WORLD_MODE, "World Mode\tW", "Control world")
        tools_menu.AppendSeparator()
        tools_menu.Append(self.ID_TOGGLE_PROJECTION, "Toggle Projection\tP", "Switch perspective/orthographic")
        
        # Help menu
        help_menu = wx.Menu()
        help_menu.Append(wx.ID_HELP, "Controls Help", "Show all controls")
        help_menu.AppendSeparator()
        help_menu.Append(wx.ID_ABOUT, "&About", "About this demo")
        
        # Add to menubar
        menubar.Append(file_menu, "&File")
        menubar.Append(view_menu, "&View")
        menubar.Append(movement_menu, "&Movement")
        menubar.Append(tools_menu, "&Tools")
        menubar.Append(help_menu, "&Help")
        
        # Set menubar
        self.SetMenuBar(menubar)
        
        # Bind all events
        self.bind_all_events()
    
    def bind_all_events(self):
        """Bind all menu events."""
        # File menu
        self.Bind(wx.EVT_MENU, self.on_new, id=wx.ID_NEW)
        self.Bind(wx.EVT_MENU, self.on_quit, id=wx.ID_EXIT)
        
        # View menu
        self.Bind(wx.EVT_MENU, self.on_x_grid, id=self.ID_X_GRID)
        self.Bind(wx.EVT_MENU, self.on_y_grid, id=self.ID_Y_GRID)
        self.Bind(wx.EVT_MENU, self.on_z_grid, id=self.ID_Z_GRID)
        self.Bind(wx.EVT_MENU, self.on_toggle_grid, id=self.ID_TOGGLE_GRID)
        self.Bind(wx.EVT_MENU, self.on_toggle_axes, id=self.ID_TOGGLE_AXES)
        
        # Movement menu
        self.Bind(wx.EVT_MENU, self.on_invert_mouse_x, id=self.ID_INVERT_MOUSE_X)
        self.Bind(wx.EVT_MENU, self.on_invert_mouse_y, id=self.ID_INVERT_MOUSE_Y)
        self.Bind(wx.EVT_MENU, self.on_invert_movement, id=self.ID_INVERT_MOVEMENT)
        self.Bind(wx.EVT_MENU, self.on_rotation_speed, id=self.ID_ROTATION_SPEED)
        self.Bind(wx.EVT_MENU, self.on_pan_speed, id=self.ID_PAN_SPEED)
        self.Bind(wx.EVT_MENU, self.on_move_speed, id=self.ID_MOVE_SPEED)
        self.Bind(wx.EVT_MENU, self.on_zoom_speed, id=self.ID_ZOOM_SPEED)
        
        # Tools menu
        self.Bind(wx.EVT_MENU, self.on_camera_mode, id=self.ID_CAMERA_MODE)
        self.Bind(wx.EVT_MENU, self.on_world_mode, id=self.ID_WORLD_MODE)
        self.Bind(wx.EVT_MENU, self.on_toggle_projection, id=self.ID_TOGGLE_PROJECTION)
        
        # Help menu
        self.Bind(wx.EVT_MENU, self.on_help, id=wx.ID_HELP)
        self.Bind(wx.EVT_MENU, self.on_about, id=wx.ID_ABOUT)
    
    # Event handlers
    def on_new(self, event):
        self.canvas_3d.reset_camera()
        self.canvas_3d.reset_world()
        self.update_settings_display()
        self.SetStatusText("Reset to defaults")
    
    def on_quit(self, event):
        self.Close()
    
    def on_x_grid(self, event):
        colors = self.canvas_3d.get_grid_colors()
        data = wx.ColourData()
        data.SetColour(wx.Colour(*colors[0]))
        
        with wx.ColourDialog(self, data) as dialog:
            dialog.SetTitle("X Grid Color")
            if dialog.ShowModal() == wx.ID_OK:
                color = dialog.GetColourData().GetColour()
                rgb = (color.Red(), color.Green(), color.Blue())
                self.canvas_3d.set_grid_color_x(rgb)
                self.SetStatusText(f"X grid color: RGB{rgb}")
    
    def on_y_grid(self, event):
        wx.MessageBox("Y Grid Color is reserved for future Y-plane grids.", "Y Grid", wx.OK | wx.ICON_INFORMATION)
    
    def on_z_grid(self, event):
        colors = self.canvas_3d.get_grid_colors()
        data = wx.ColourData()
        data.SetColour(wx.Colour(*colors[2]))
        
        with wx.ColourDialog(self, data) as dialog:
            dialog.SetTitle("Z Grid Color")
            if dialog.ShowModal() == wx.ID_OK:
                color = dialog.GetColourData().GetColour()
                rgb = (color.Red(), color.Green(), color.Blue())
                self.canvas_3d.set_grid_color_z(rgb)
                self.SetStatusText(f"Z grid color: RGB{rgb}")
    
    def on_toggle_grid(self, event):
        self.canvas_3d.show_grid = not self.canvas_3d.show_grid
        self.canvas_3d.Refresh()
        self.SetStatusText(f"Grid: {'ON' if self.canvas_3d.show_grid else 'OFF'}")
    
    def on_toggle_axes(self, event):
        self.canvas_3d.show_axes = not self.canvas_3d.show_axes
        self.canvas_3d.Refresh()
        self.SetStatusText(f"Axes: {'ON' if self.canvas_3d.show_axes else 'OFF'}")
    
    def on_invert_mouse_x(self, event):
        self.canvas_3d.toggle_mouse_x_invert()
        self.update_settings_display()
        self.SetStatusText(f"Mouse X invert: {'ON' if self.canvas_3d.invert_mouse_x else 'OFF'}")
    
    def on_invert_mouse_y(self, event):
        self.canvas_3d.toggle_mouse_y_invert()
        self.update_settings_display()
        self.SetStatusText(f"Mouse Y invert: {'ON' if self.canvas_3d.invert_mouse_y else 'OFF'}")
    
    def on_invert_movement(self, event):
        self.canvas_3d.toggle_movement_invert()
        self.update_settings_display()
        self.SetStatusText(f"Movement invert: {'ON' if self.canvas_3d.invert_movement else 'OFF'}")
    
    def on_rotation_speed(self, event):
        current = self.canvas_3d.mouse_rotation_speed
        dialog = wx.NumberEntryDialog(self, "Enter mouse rotation speed (0.1 - 10.0):",
                                    "Speed:", "Mouse Rotation Speed", current, 0.1, 10.0)
        if dialog.ShowModal() == wx.ID_OK:
            self.canvas_3d.set_mouse_rotation_speed(dialog.GetValue())
            self.update_settings_display()
            self.SetStatusText(f"Rotation speed: {dialog.GetValue():.1f}x")
        dialog.Destroy()
    
    def on_pan_speed(self, event):
        current = self.canvas_3d.mouse_pan_speed
        dialog = wx.NumberEntryDialog(self, "Enter mouse pan speed (0.1 - 10.0):",
                                    "Speed:", "Mouse Pan Speed", current, 0.1, 10.0)
        if dialog.ShowModal() == wx.ID_OK:
            self.canvas_3d.set_mouse_pan_speed(dialog.GetValue())
            self.update_settings_display()
            self.SetStatusText(f"Pan speed: {dialog.GetValue():.1f}x")
        dialog.Destroy()
    
    def on_move_speed(self, event):
        current = self.canvas_3d.keyboard_move_speed
        dialog = wx.NumberEntryDialog(self, "Enter keyboard move speed (0.1 - 10.0):",
                                    "Speed:", "Keyboard Speed", current, 0.1, 10.0)
        if dialog.ShowModal() == wx.ID_OK:
            self.canvas_3d.set_keyboard_move_speed(dialog.GetValue())
            self.update_settings_display()
            self.SetStatusText(f"Move speed: {dialog.GetValue():.1f}x")
        dialog.Destroy()
    
    def on_zoom_speed(self, event):
        current = self.canvas_3d.zoom_speed
        dialog = wx.NumberEntryDialog(self, "Enter zoom speed (0.1 - 10.0):",
                                    "Speed:", "Zoom Speed", current, 0.1, 10.0)
        if dialog.ShowModal() == wx.ID_OK:
            self.canvas_3d.set_zoom_speed(dialog.GetValue())
            self.update_settings_display()
            self.SetStatusText(f"Zoom speed: {dialog.GetValue():.1f}x")
        dialog.Destroy()
    
    def on_camera_mode(self, event):
        self.canvas_3d.control_mode = "camera"
        self.SetStatusText("Camera control mode")
    
    def on_world_mode(self, event):
        self.canvas_3d.control_mode = "world"
        self.SetStatusText("World control mode")
    
    def on_toggle_projection(self, event):
        if self.canvas_3d.camera.projection_mode == ProjectionMode.PERSPECTIVE:
            self.canvas_3d.camera.projection_mode = ProjectionMode.ORTHOGRAPHIC
            mode = "Orthographic"
        else:
            self.canvas_3d.camera.projection_mode = ProjectionMode.PERSPECTIVE
            mode = "Perspective"
        self.canvas_3d.Refresh()
        self.SetStatusText(f"Projection: {mode}")
    
    def on_help(self, event):
        help_text = """Complete 3D Canvas Controls:

MOUSE:
• Left drag: Rotate camera/world
• Middle drag: Pan camera/world
• Scroll: Zoom

KEYBOARD:
• WASD: Move forward/back/left/right
• QE: Move up/down
• TAB: Toggle camera/world mode
• P: Toggle projection mode
• G: Toggle grid, A: Toggle axes

MENU OPTIONS:
• View → Grid Colors: Change grid line colors
• Movement → Inversion: Invert controls
• Movement → Speed Settings: Adjust speeds
• Tools: Switch control modes

SPEED RANGES: All speeds adjustable from 0.1x to 10.0x
INVERSION: Independent X/Y mouse and keyboard inversion
"""
        wx.MessageDialog(self, help_text, "Complete Controls Help", wx.OK | wx.ICON_INFORMATION).ShowModal()
    
    def on_about(self, event):
        info = wx.adv.AboutDialogInfo()
        info.SetName("3D Canvas Complete Controls")
        info.SetVersion("1.0")
        info.SetDescription("Full-featured 3D canvas with configurable movement behavior and speed controls")
        wx.adv.AboutBox(info, self)
    
    # Control panel event handlers
    def on_update_settings(self, event):
        self.update_settings_display()
    
    def on_fast_mode(self, event):
        self.canvas_3d.set_mouse_rotation_speed(3.0)
        self.canvas_3d.set_mouse_pan_speed(3.0)
        self.canvas_3d.set_keyboard_move_speed(3.0)
        self.canvas_3d.set_zoom_speed(3.0)
        self.update_settings_display()
        self.SetStatusText("Fast mode activated")
    
    def on_slow_mode(self, event):
        self.canvas_3d.set_mouse_rotation_speed(0.3)
        self.canvas_3d.set_mouse_pan_speed(0.3)
        self.canvas_3d.set_keyboard_move_speed(0.3)
        self.canvas_3d.set_zoom_speed(0.3)
        self.update_settings_display()
        self.SetStatusText("Slow mode activated")
    
    def on_toggle_inverts(self, event):
        self.canvas_3d.toggle_mouse_x_invert()
        self.canvas_3d.toggle_mouse_y_invert()
        self.canvas_3d.toggle_movement_invert()
        self.update_settings_display()
        self.SetStatusText("All inversions toggled")
    
    def on_reset_settings(self, event):
        # Reset to defaults
        self.canvas_3d.invert_mouse_x = False
        self.canvas_3d.invert_mouse_y = False
        self.canvas_3d.invert_movement = False
        self.canvas_3d.set_mouse_rotation_speed(1.0)
        self.canvas_3d.set_mouse_pan_speed(1.0)
        self.canvas_3d.set_keyboard_move_speed(1.0)
        self.canvas_3d.set_zoom_speed(1.0)
        self.update_settings_display()
        self.SetStatusText("All settings reset to defaults")
    
    def update_settings_display(self):
        """Update the settings display panel."""
        settings = self.canvas_3d.get_movement_settings()
        
        text = f"""Current Movement Settings:

INVERSIONS:
Mouse X Invert: {'ON' if settings['invert_mouse_x'] else 'OFF'}
Mouse Y Invert: {'ON' if settings['invert_mouse_y'] else 'OFF'}
Keyboard Invert: {'ON' if settings['invert_movement'] else 'OFF'}

SPEEDS:
Mouse Rotation: {settings['mouse_rotation_speed']:.1f}x
Mouse Pan: {settings['mouse_pan_speed']:.1f}x
Keyboard Move: {settings['keyboard_move_speed']:.1f}x
Zoom Speed: {settings['zoom_speed']:.1f}x

CONTROL MODE:
Current Mode: {self.canvas_3d.control_mode.upper()}

PROJECTION:
Mode: {self.canvas_3d.camera.projection_mode.value}

💡 TIP: Use the Movement menu to change these settings!
"""
        
        self.settings_text.SetValue(text)


class FullControlsApp(wx.App):
    """Application for complete 3D controls demo."""
    
    def OnInit(self):
        self.SetAppName("3D Canvas Complete Controls")
        self.SetAppDisplayName("3D Canvas - Movement & Speed Controls")
        
        frame = FullControlsFrame()
        frame.Show()
        frame.Raise()
        frame.SetFocus()
        
        if wx.Platform == '__WXMAC__':
            frame.RequestUserAttention(wx.USER_ATTENTION_INFO)
        
        return True


if __name__ == "__main__":
    print("3D Canvas - Complete Controls Demo")
    print("="*40)
    print("Features:")
    print("• Grid color selectors")
    print("• Movement behavior toggles")
    print("• Speed controls (0.1x - 10.0x)")
    print("• Mouse X/Y inversion")
    print("• Keyboard movement inversion")
    print("• Real-time settings display")
    print("="*40)
    
    app = FullControlsApp()
    app.MainLoop()

