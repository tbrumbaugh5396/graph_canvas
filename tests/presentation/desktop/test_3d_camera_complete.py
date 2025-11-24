#!/usr/bin/env python3
"""
Complete 3D Camera Controls Test - All camera options in menubar
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


class CameraCompleteFrame(wx.Frame):
    """Frame demonstrating all camera controls and settings."""
    
    def __init__(self):
        super().__init__(None, 
                        title="3D Canvas - Complete Camera Controls",
                        size=(1400, 900))
        
        # Create status bar
        self.CreateStatusBar()
        self.SetStatusText("Complete Camera Controls - Check Camera menu for all options")
        
        # Create main panel
        main_panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Create 3D canvas
        self.canvas_3d = Canvas3D(main_panel)
        
        # Set some nice initial colors
        self.canvas_3d.set_grid_color_x((255, 120, 120))  # Light red
        self.canvas_3d.set_grid_color_z((120, 120, 255))  # Light blue
        
        # Create camera info panel
        camera_panel = self.create_camera_info_panel(main_panel)
        
        # Layout
        main_sizer.Add(self.canvas_3d, 3, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(camera_panel, 1, wx.EXPAND | wx.ALL, 5)
        main_panel.SetSizer(main_sizer)
        
        # Create complete menubar
        self.create_complete_camera_menubar()
        
        # Center window
        self.Center()
        
        # Start update timer for real-time camera info
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer)
        self.timer.Start(100)  # Update every 100ms
        
        print("Complete camera controls demo ready!")
    
    def create_camera_info_panel(self, parent):
        """Create a panel showing real-time camera information."""
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Title
        title = wx.StaticText(panel, label="Camera Information")
        title.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(title, 0, wx.ALL, 5)
        
        # Real-time camera info
        self.camera_info_text = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.camera_info_text.SetFont(wx.Font(9, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sizer.Add(self.camera_info_text, 1, wx.EXPAND | wx.ALL, 5)
        
        # Quick camera presets
        presets_label = wx.StaticText(panel, label="Camera Presets:")
        presets_label.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(presets_label, 0, wx.ALL, 5)
        
        # Preset buttons
        preset_buttons = [
            ("Wide FOV (120°)", self.on_wide_fov),
            ("Normal FOV (60°)", self.on_normal_fov),
            ("Narrow FOV (30°)", self.on_narrow_fov),
            ("Close View", self.on_close_view),
            ("Far View", self.on_far_view),
            ("Orthographic", self.on_ortho_preset),
            ("Perspective", self.on_persp_preset),
        ]
        
        for label, handler in preset_buttons:
            btn = wx.Button(panel, label=label)
            btn.Bind(wx.EVT_BUTTON, handler)
            sizer.Add(btn, 0, wx.EXPAND | wx.ALL, 2)
        
        panel.SetSizer(sizer)
        return panel
    
    def create_complete_camera_menubar(self):
        """Create complete menubar with all camera controls."""
        menubar = wx.MenuBar()
        
        # File menu
        file_menu = wx.Menu()
        file_menu.Append(wx.ID_NEW, "&Reset All\tCmd+N", "Reset camera and world")
        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_EXIT, "&Quit\tCmd+Q", "Quit")
        
        # View menu
        view_menu = wx.Menu()
        
        # Grid colors
        self.ID_X_GRID = wx.NewIdRef()
        self.ID_Z_GRID = wx.NewIdRef()
        self.ID_TOGGLE_GRID = wx.NewIdRef()
        self.ID_TOGGLE_AXES = wx.NewIdRef()
        
        view_menu.Append(self.ID_X_GRID, "🔴 X Grid Color...", "Change X grid color")
        view_menu.Append(self.ID_Z_GRID, "🔵 Z Grid Color...", "Change Z grid color")
        view_menu.AppendSeparator()
        view_menu.Append(self.ID_TOGGLE_GRID, "Toggle Grid\tG", "Show/hide grid")
        view_menu.Append(self.ID_TOGGLE_AXES, "Toggle Axes\tA", "Show/hide axes")
        
        # Camera menu - THE MAIN FEATURE
        camera_menu = wx.Menu()
        
        # Projection submenu
        projection_submenu = wx.Menu()
        self.ID_TOGGLE_PROJECTION = wx.NewIdRef()
        self.ID_SET_FOV = wx.NewIdRef()
        self.ID_SET_ORTHO_SIZE = wx.NewIdRef()
        
        projection_submenu.Append(self.ID_TOGGLE_PROJECTION, "Toggle Perspective/Orthographic\tP", "Switch projection mode")
        projection_submenu.AppendSeparator()
        projection_submenu.Append(self.ID_SET_FOV, "Field of View...", "Set perspective FOV (10°-170°)")
        projection_submenu.Append(self.ID_SET_ORTHO_SIZE, "Orthographic Size...", "Set orthographic view size")
        
        camera_menu.AppendSubMenu(projection_submenu, "Projection Settings", "Perspective and orthographic settings")
        
        # Clipping planes submenu
        clipping_submenu = wx.Menu()
        self.ID_SET_NEAR_PLANE = wx.NewIdRef()
        self.ID_SET_FAR_PLANE = wx.NewIdRef()
        self.ID_RESET_CLIPPING = wx.NewIdRef()
        
        clipping_submenu.Append(self.ID_SET_NEAR_PLANE, "Near Clipping Plane...", "Set near clipping distance")
        clipping_submenu.Append(self.ID_SET_FAR_PLANE, "Far Clipping Plane...", "Set far clipping distance")
        clipping_submenu.AppendSeparator()
        clipping_submenu.Append(self.ID_RESET_CLIPPING, "Reset to Defaults", "Reset clipping planes")
        
        camera_menu.AppendSubMenu(clipping_submenu, "Clipping Planes", "Near and far clipping settings")
        
        # View limits submenu
        view_limits_submenu = wx.Menu()
        self.ID_TOGGLE_VIEW_LIMITS = wx.NewIdRef()
        self.ID_SET_VIEW_LIMITS = wx.NewIdRef()
        self.ID_RESET_VIEW_LIMITS = wx.NewIdRef()
        
        view_limits_submenu.Append(self.ID_TOGGLE_VIEW_LIMITS, "Enable/Disable View Limits\tL", "Toggle view distance limits")
        view_limits_submenu.Append(self.ID_SET_VIEW_LIMITS, "Set View Limits...", "Configure view distance limits")
        view_limits_submenu.AppendSeparator()
        view_limits_submenu.Append(self.ID_RESET_VIEW_LIMITS, "Reset View Limits", "Reset to default limits")
        
        camera_menu.AppendSubMenu(view_limits_submenu, "View Distance Limits", "Control how far objects are visible")
        
        camera_menu.AppendSeparator()
        
        # Camera position and rotation
        self.ID_SET_CAMERA_POS = wx.NewIdRef()
        self.ID_SET_CAMERA_ROT = wx.NewIdRef()
        self.ID_RESET_CAMERA = wx.NewIdRef()
        
        camera_menu.Append(self.ID_SET_CAMERA_POS, "Set Camera Position...", "Set camera XYZ position directly")
        camera_menu.Append(self.ID_SET_CAMERA_ROT, "Set Camera Rotation...", "Set camera pitch/yaw/roll directly")
        camera_menu.AppendSeparator()
        camera_menu.Append(self.ID_RESET_CAMERA, "Reset Camera\tR", "Reset camera to default position")
        
        # Vanish point and advanced info
        camera_menu.AppendSeparator()
        self.ID_SHOW_VANISH_POINT = wx.NewIdRef()
        self.ID_SHOW_CAMERA_MATRIX = wx.NewIdRef()
        
        camera_menu.Append(self.ID_SHOW_VANISH_POINT, "Show Vanish Point Info", "Display vanish point information")
        camera_menu.Append(self.ID_SHOW_CAMERA_MATRIX, "Show Camera Details", "Display detailed camera information")
        
        # Movement menu (from previous implementation)
        movement_menu = wx.Menu()
        
        # Control mode
        self.ID_CAMERA_MODE = wx.NewIdRef()
        self.ID_WORLD_MODE = wx.NewIdRef()
        
        movement_menu.Append(self.ID_CAMERA_MODE, "Camera Control Mode\tC", "Control camera movement")
        movement_menu.Append(self.ID_WORLD_MODE, "World Control Mode\tW", "Control world movement")
        movement_menu.AppendSeparator()
        
        # Speed settings
        speed_submenu = wx.Menu()
        self.ID_ROTATION_SPEED = wx.NewIdRef()
        self.ID_ZOOM_SPEED = wx.NewIdRef()
        
        speed_submenu.Append(self.ID_ROTATION_SPEED, "Mouse Rotation Speed...", "Set rotation speed")
        speed_submenu.Append(self.ID_ZOOM_SPEED, "Zoom Speed...", "Set zoom speed")
        
        movement_menu.AppendSubMenu(speed_submenu, "Movement Speeds", "Adjust movement speeds")
        
        # Help menu
        help_menu = wx.Menu()
        help_menu.Append(wx.ID_HELP, "Camera Controls Help", "Show all camera controls")
        help_menu.AppendSeparator()
        help_menu.Append(wx.ID_ABOUT, "&About", "About this demo")
        
        # Add to menubar
        menubar.Append(file_menu, "&File")
        menubar.Append(view_menu, "&View")
        menubar.Append(camera_menu, "&Camera")  # ⭐ THE MAIN CAMERA MENU
        menubar.Append(movement_menu, "&Movement")
        menubar.Append(help_menu, "&Help")
        
        # Set menubar
        self.SetMenuBar(menubar)
        
        # Bind all events
        self.bind_all_camera_events()
    
    def bind_all_camera_events(self):
        """Bind all camera menu events."""
        # File menu
        self.Bind(wx.EVT_MENU, self.on_reset_all, id=wx.ID_NEW)
        self.Bind(wx.EVT_MENU, self.on_quit, id=wx.ID_EXIT)
        
        # View menu
        self.Bind(wx.EVT_MENU, self.on_x_grid, id=self.ID_X_GRID)
        self.Bind(wx.EVT_MENU, self.on_z_grid, id=self.ID_Z_GRID)
        self.Bind(wx.EVT_MENU, self.on_toggle_grid, id=self.ID_TOGGLE_GRID)
        self.Bind(wx.EVT_MENU, self.on_toggle_axes, id=self.ID_TOGGLE_AXES)
        
        # Camera menu - projection
        self.Bind(wx.EVT_MENU, self.on_toggle_projection, id=self.ID_TOGGLE_PROJECTION)
        self.Bind(wx.EVT_MENU, self.on_set_fov, id=self.ID_SET_FOV)
        self.Bind(wx.EVT_MENU, self.on_set_ortho_size, id=self.ID_SET_ORTHO_SIZE)
        
        # Camera menu - clipping
        self.Bind(wx.EVT_MENU, self.on_set_near_plane, id=self.ID_SET_NEAR_PLANE)
        self.Bind(wx.EVT_MENU, self.on_set_far_plane, id=self.ID_SET_FAR_PLANE)
        self.Bind(wx.EVT_MENU, self.on_reset_clipping, id=self.ID_RESET_CLIPPING)
        
        # Camera menu - view limits
        self.Bind(wx.EVT_MENU, self.on_toggle_view_limits, id=self.ID_TOGGLE_VIEW_LIMITS)
        self.Bind(wx.EVT_MENU, self.on_set_view_limits, id=self.ID_SET_VIEW_LIMITS)
        self.Bind(wx.EVT_MENU, self.on_reset_view_limits, id=self.ID_RESET_VIEW_LIMITS)
        
        # Camera menu - position/rotation
        self.Bind(wx.EVT_MENU, self.on_set_camera_pos, id=self.ID_SET_CAMERA_POS)
        self.Bind(wx.EVT_MENU, self.on_set_camera_rot, id=self.ID_SET_CAMERA_ROT)
        self.Bind(wx.EVT_MENU, self.on_reset_camera, id=self.ID_RESET_CAMERA)
        
        # Camera menu - info
        self.Bind(wx.EVT_MENU, self.on_show_vanish_point, id=self.ID_SHOW_VANISH_POINT)
        self.Bind(wx.EVT_MENU, self.on_show_camera_matrix, id=self.ID_SHOW_CAMERA_MATRIX)
        
        # Movement menu
        self.Bind(wx.EVT_MENU, self.on_camera_mode, id=self.ID_CAMERA_MODE)
        self.Bind(wx.EVT_MENU, self.on_world_mode, id=self.ID_WORLD_MODE)
        self.Bind(wx.EVT_MENU, self.on_rotation_speed, id=self.ID_ROTATION_SPEED)
        self.Bind(wx.EVT_MENU, self.on_zoom_speed, id=self.ID_ZOOM_SPEED)
        
        # Help menu
        self.Bind(wx.EVT_MENU, self.on_help, id=wx.ID_HELP)
        self.Bind(wx.EVT_MENU, self.on_about, id=wx.ID_ABOUT)
    
    # Event handlers
    def on_reset_all(self, event):
        self.canvas_3d.reset_camera()
        self.canvas_3d.reset_world()
        self.SetStatusText("Reset to defaults")
    
    def on_quit(self, event):
        self.timer.Stop()
        self.Close()
    
    def on_x_grid(self, event):
        colors = self.canvas_3d.get_grid_colors()
        data = wx.ColourData()
        data.SetColour(wx.Colour(*colors[0]))
        
        with wx.ColourDialog(self, data) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                color = dialog.GetColourData().GetColour()
                rgb = (color.Red(), color.Green(), color.Blue())
                self.canvas_3d.set_grid_color_x(rgb)
    
    def on_z_grid(self, event):
        colors = self.canvas_3d.get_grid_colors()
        data = wx.ColourData()
        data.SetColour(wx.Colour(*colors[2]))
        
        with wx.ColourDialog(self, data) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                color = dialog.GetColourData().GetColour()
                rgb = (color.Red(), color.Green(), color.Blue())
                self.canvas_3d.set_grid_color_z(rgb)
    
    def on_toggle_grid(self, event):
        self.canvas_3d.show_grid = not self.canvas_3d.show_grid
        self.canvas_3d.Refresh()
    
    def on_toggle_axes(self, event):
        self.canvas_3d.show_axes = not self.canvas_3d.show_axes
        self.canvas_3d.Refresh()
    
    # Camera menu handlers
    def on_toggle_projection(self, event):
        self.canvas_3d.toggle_projection_mode()
        mode = self.canvas_3d.camera.projection_mode.value
        self.SetStatusText(f"Projection: {mode}")
    
    def on_set_fov(self, event):
        current = self.canvas_3d.camera.fov
        dialog = wx.NumberEntryDialog(self, "Field of View (10° - 170°):", "FOV:", "Field of View", current, 10.0, 170.0)
        if dialog.ShowModal() == wx.ID_OK:
            self.canvas_3d.set_field_of_view(dialog.GetValue())
            self.SetStatusText(f"FOV: {dialog.GetValue():.1f}°")
        dialog.Destroy()
    
    def on_set_ortho_size(self, event):
        current = self.canvas_3d.camera.ortho_size
        dialog = wx.NumberEntryDialog(self, "Orthographic Size (0.1 - 100.0):", "Size:", "Orthographic Size", current, 0.1, 100.0)
        if dialog.ShowModal() == wx.ID_OK:
            self.canvas_3d.set_orthographic_size(dialog.GetValue())
            self.SetStatusText(f"Ortho Size: {dialog.GetValue():.1f}")
        dialog.Destroy()
    
    def on_set_near_plane(self, event):
        current = self.canvas_3d.camera.near_plane
        max_val = self.canvas_3d.camera.far_plane - 0.1
        dialog = wx.NumberEntryDialog(self, f"Near Clipping Plane (0.01 - {max_val:.2f}):", "Near:", "Near Plane", current, 0.01, max_val)
        if dialog.ShowModal() == wx.ID_OK:
            self.canvas_3d.set_near_plane(dialog.GetValue())
            self.SetStatusText(f"Near Plane: {dialog.GetValue():.2f}")
        dialog.Destroy()
    
    def on_set_far_plane(self, event):
        current = self.canvas_3d.camera.far_plane
        min_val = self.canvas_3d.camera.near_plane + 0.1
        dialog = wx.NumberEntryDialog(self, f"Far Clipping Plane ({min_val:.2f} - 10000.0):", "Far:", "Far Plane", current, min_val, 10000.0)
        if dialog.ShowModal() == wx.ID_OK:
            self.canvas_3d.set_far_plane(dialog.GetValue())
            self.SetStatusText(f"Far Plane: {dialog.GetValue():.1f}")
        dialog.Destroy()
    
    def on_reset_clipping(self, event):
        self.canvas_3d.set_near_plane(0.1)
        self.canvas_3d.set_far_plane(1000.0)
        self.SetStatusText("Clipping planes reset")
    
    def on_toggle_view_limits(self, event):
        self.canvas_3d.toggle_view_limits()
        status = "ON" if self.canvas_3d.camera.use_view_limits else "OFF"
        self.SetStatusText(f"View limits: {status}")
    
    def on_set_view_limits(self, event):
        current = (self.canvas_3d.camera.view_limit_x, self.canvas_3d.camera.view_limit_y, self.canvas_3d.camera.view_limit_z)
        
        # Simple sequential dialogs
        x_dialog = wx.NumberEntryDialog(self, f"Current limits: {current}\n\nX Limit (1.0 - 1000.0):", "X:", "View Limit X", current[0], 1.0, 1000.0)
        if x_dialog.ShowModal() == wx.ID_OK:
            x = x_dialog.GetValue()
            y_dialog = wx.NumberEntryDialog(self, "Y Limit (1.0 - 1000.0):", "Y:", "View Limit Y", current[1], 1.0, 1000.0)
            if y_dialog.ShowModal() == wx.ID_OK:
                y = y_dialog.GetValue()
                z_dialog = wx.NumberEntryDialog(self, "Z Limit (1.0 - 1000.0):", "Z:", "View Limit Z", current[2], 1.0, 1000.0)
                if z_dialog.ShowModal() == wx.ID_OK:
                    z = z_dialog.GetValue()
                    self.canvas_3d.set_view_limits(x, y, z)
                    self.SetStatusText(f"View limits: ({x:.1f}, {y:.1f}, {z:.1f})")
                z_dialog.Destroy()
            y_dialog.Destroy()
        x_dialog.Destroy()
    
    def on_reset_view_limits(self, event):
        self.canvas_3d.set_view_limits(50.0, 50.0, 50.0)
        self.SetStatusText("View limits reset")
    
    def on_set_camera_pos(self, event):
        pos = self.canvas_3d.camera.position
        
        x_dialog = wx.NumberEntryDialog(self, f"Current: ({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f})\n\nX Position:", "X:", "Camera X", pos[0], -1000.0, 1000.0)
        if x_dialog.ShowModal() == wx.ID_OK:
            x = x_dialog.GetValue()
            y_dialog = wx.NumberEntryDialog(self, "Y Position:", "Y:", "Camera Y", pos[1], -1000.0, 1000.0)
            if y_dialog.ShowModal() == wx.ID_OK:
                y = y_dialog.GetValue()
                z_dialog = wx.NumberEntryDialog(self, "Z Position:", "Z:", "Camera Z", pos[2], -1000.0, 1000.0)
                if z_dialog.ShowModal() == wx.ID_OK:
                    z = z_dialog.GetValue()
                    self.canvas_3d.set_camera_position(x, y, z)
                    self.SetStatusText(f"Camera pos: ({x:.1f}, {y:.1f}, {z:.1f})")
                z_dialog.Destroy()
            y_dialog.Destroy()
        x_dialog.Destroy()
    
    def on_set_camera_rot(self, event):
        pitch = np.degrees(self.canvas_3d.camera.pitch)
        yaw = np.degrees(self.canvas_3d.camera.yaw)
        roll = np.degrees(self.canvas_3d.camera.roll)
        
        p_dialog = wx.NumberEntryDialog(self, f"Current: ({pitch:.1f}°, {yaw:.1f}°, {roll:.1f}°)\n\nPitch:", "Pitch:", "Camera Pitch", pitch, -180.0, 180.0)
        if p_dialog.ShowModal() == wx.ID_OK:
            p = p_dialog.GetValue()
            y_dialog = wx.NumberEntryDialog(self, "Yaw:", "Yaw:", "Camera Yaw", yaw, -180.0, 180.0)
            if y_dialog.ShowModal() == wx.ID_OK:
                y = y_dialog.GetValue()
                r_dialog = wx.NumberEntryDialog(self, "Roll:", "Roll:", "Camera Roll", roll, -180.0, 180.0)
                if r_dialog.ShowModal() == wx.ID_OK:
                    r = r_dialog.GetValue()
                    self.canvas_3d.set_camera_rotation(p, y, r)
                    self.SetStatusText(f"Camera rot: ({p:.1f}°, {y:.1f}°, {r:.1f}°)")
                r_dialog.Destroy()
            y_dialog.Destroy()
        p_dialog.Destroy()
    
    def on_reset_camera(self, event):
        self.canvas_3d.reset_camera()
        self.SetStatusText("Camera reset")
    
    def on_show_vanish_point(self, event):
        vanish_point = self.canvas_3d.get_vanish_point_screen_coords()
        settings = self.canvas_3d.get_camera_settings()
        
        if vanish_point:
            info = f"""🎯 VANISH POINT INFORMATION

SCREEN COORDINATES:
X: {vanish_point[0]:.1f} pixels
Y: {vanish_point[1]:.1f} pixels

CAMERA SETTINGS:
Projection: {settings['projection_mode']}
Field of View: {settings['fov']:.1f}°
Position: ({settings['position'][0]:.1f}, {settings['position'][1]:.1f}, {settings['position'][2]:.1f})
Rotation: ({settings['pitch']:.1f}°, {settings['yaw']:.1f}°, {settings['roll']:.1f}°)

CLIPPING PLANES:
Near: {settings['near_plane']:.2f} | Far: {settings['far_plane']:.1f}

VIEW LIMITS:
Enabled: {settings['use_view_limits']}
Limits: ({settings['view_limit_x']:.1f}, {settings['view_limit_y']:.1f}, {settings['view_limit_z']:.1f})

📐 The vanish point is where parallel lines converge in perspective projection."""
        else:
            info = f"""🎯 VANISH POINT INFORMATION

ORTHOGRAPHIC PROJECTION:
No vanish point - parallel lines stay parallel.

CAMERA SETTINGS:
Projection: {settings['projection_mode']}
Orthographic Size: {settings['ortho_size']:.1f}
Position: ({settings['position'][0]:.1f}, {settings['position'][1]:.1f}, {settings['position'][2]:.1f})

Switch to perspective projection to see vanish point behavior."""
        
        wx.MessageDialog(self, info, "Vanish Point Information", wx.OK | wx.ICON_INFORMATION).ShowModal()
    
    def on_show_camera_matrix(self, event):
        settings = self.canvas_3d.get_camera_settings()
        
        info = f"""📊 DETAILED CAMERA INFORMATION

PROJECTION SETTINGS:
Mode: {settings['projection_mode']}
Field of View: {settings['fov']:.1f}°
Orthographic Size: {settings['ortho_size']:.1f}

POSITION & ROTATION:
Position: ({settings['position'][0]:.2f}, {settings['position'][1]:.2f}, {settings['position'][2]:.2f})
Pitch: {settings['pitch']:.2f}°
Yaw: {settings['yaw']:.2f}°
Roll: {settings['roll']:.2f}°

CLIPPING PLANES:
Near Plane: {settings['near_plane']:.3f}
Far Plane: {settings['far_plane']:.1f}
Clipping Range: {settings['far_plane'] - settings['near_plane']:.1f}

VIEW DISTANCE LIMITS:
Enabled: {settings['use_view_limits']}
X Limit: {settings['view_limit_x']:.1f}
Y Limit: {settings['view_limit_y']:.1f}
Z Limit: {settings['view_limit_z']:.1f}

CONTROL MODE:
Current Mode: {self.canvas_3d.control_mode.upper()}

🎮 Use Camera menu to modify all these settings!"""
        
        wx.MessageDialog(self, info, "Complete Camera Details", wx.OK | wx.ICON_INFORMATION).ShowModal()
    
    # Movement handlers
    def on_camera_mode(self, event):
        self.canvas_3d.control_mode = "camera"
        self.SetStatusText("Camera control mode")
    
    def on_world_mode(self, event):
        self.canvas_3d.control_mode = "world"
        self.SetStatusText("World control mode")
    
    def on_rotation_speed(self, event):
        current = self.canvas_3d.mouse_rotation_speed
        dialog = wx.NumberEntryDialog(self, "Rotation Speed (0.1 - 10.0):", "Speed:", "Rotation Speed", current, 0.1, 10.0)
        if dialog.ShowModal() == wx.ID_OK:
            self.canvas_3d.set_mouse_rotation_speed(dialog.GetValue())
        dialog.Destroy()
    
    def on_zoom_speed(self, event):
        current = self.canvas_3d.zoom_speed
        dialog = wx.NumberEntryDialog(self, "Zoom Speed (0.1 - 10.0):", "Speed:", "Zoom Speed", current, 0.1, 10.0)
        if dialog.ShowModal() == wx.ID_OK:
            self.canvas_3d.set_zoom_speed(dialog.GetValue())
        dialog.Destroy()
    
    def on_help(self, event):
        help_text = """🎮 COMPLETE CAMERA CONTROLS

CAMERA MENU OPTIONS:
📐 Projection Settings:
  • Toggle Perspective/Orthographic
  • Field of View (10° - 170°)
  • Orthographic Size

✂️ Clipping Planes:
  • Near Clipping Plane
  • Far Clipping Plane
  • Reset to Defaults

👁️ View Distance Limits:
  • Enable/Disable Limits
  • Set X/Y/Z Limits
  • Reset View Limits

📍 Camera Position & Rotation:
  • Set Camera Position (X,Y,Z)
  • Set Camera Rotation (Pitch,Yaw,Roll)
  • Reset Camera

🎯 Information:
  • Show Vanish Point Info
  • Show Camera Details

KEYBOARD CONTROLS:
• WASD: Move camera/world
• QE: Move up/down
• Mouse: Look around
• Scroll: Zoom
• P: Toggle projection
• L: Toggle view limits
• R: Reset camera
• C/W: Switch camera/world mode

All camera settings are accessible through the Camera menu!"""
        
        wx.MessageDialog(self, help_text, "Complete Camera Controls Help", wx.OK | wx.ICON_INFORMATION).ShowModal()
    
    def on_about(self, event):
        info = wx.adv.AboutDialogInfo()
        info.SetName("3D Canvas Complete Camera Controls")
        info.SetVersion("1.0")
        info.SetDescription("Full-featured 3D camera system with vanish point, FOV, clipping planes, and all camera options in menubar")
        wx.adv.AboutBox(info, self)
    
    # Preset button handlers
    def on_wide_fov(self, event):
        self.canvas_3d.camera.projection_mode = ProjectionMode.PERSPECTIVE
        self.canvas_3d.set_field_of_view(120.0)
        self.SetStatusText("Wide FOV (120°)")
    
    def on_normal_fov(self, event):
        self.canvas_3d.camera.projection_mode = ProjectionMode.PERSPECTIVE
        self.canvas_3d.set_field_of_view(60.0)
        self.SetStatusText("Normal FOV (60°)")
    
    def on_narrow_fov(self, event):
        self.canvas_3d.camera.projection_mode = ProjectionMode.PERSPECTIVE
        self.canvas_3d.set_field_of_view(30.0)
        self.SetStatusText("Narrow FOV (30°)")
    
    def on_close_view(self, event):
        self.canvas_3d.set_near_plane(0.01)
        self.canvas_3d.set_far_plane(10.0)
        self.SetStatusText("Close view (0.01 - 10.0)")
    
    def on_far_view(self, event):
        self.canvas_3d.set_near_plane(1.0)
        self.canvas_3d.set_far_plane(5000.0)
        self.SetStatusText("Far view (1.0 - 5000.0)")
    
    def on_ortho_preset(self, event):
        self.canvas_3d.camera.projection_mode = ProjectionMode.ORTHOGRAPHIC
        self.canvas_3d.set_orthographic_size(10.0)
        self.canvas_3d.Refresh()
        self.SetStatusText("Orthographic projection")
    
    def on_persp_preset(self, event):
        self.canvas_3d.camera.projection_mode = ProjectionMode.PERSPECTIVE
        self.canvas_3d.set_field_of_view(60.0)
        self.canvas_3d.Refresh()
        self.SetStatusText("Perspective projection")
    
    def on_timer(self, event):
        """Update camera info display in real-time."""
        self.update_camera_info()
    
    def update_camera_info(self):
        """Update the camera information display."""
        settings = self.canvas_3d.get_camera_settings()
        vanish_point = self.canvas_3d.get_vanish_point_screen_coords()
        
        vanish_text = f"({vanish_point[0]:.0f}, {vanish_point[1]:.0f})" if vanish_point else "N/A"
        
        info = f"""REAL-TIME CAMERA INFO:

PROJECTION:
Mode: {settings['projection_mode']}
FOV: {settings['fov']:.1f}° | Ortho: {settings['ortho_size']:.1f}

POSITION:
X: {settings['position'][0]:.2f}
Y: {settings['position'][1]:.2f}
Z: {settings['position'][2]:.2f}

ROTATION:
Pitch: {settings['pitch']:.1f}°
Yaw: {settings['yaw']:.1f}°
Roll: {settings['roll']:.1f}°

CLIPPING:
Near: {settings['near_plane']:.2f}
Far: {settings['far_plane']:.1f}

VIEW LIMITS:
Enabled: {settings['use_view_limits']}
X: {settings['view_limit_x']:.1f}
Y: {settings['view_limit_y']:.1f}
Z: {settings['view_limit_z']:.1f}

VANISH POINT:
Screen: {vanish_text}

CONTROL:
Mode: {self.canvas_3d.control_mode.upper()}

💡 Use Camera menu for all settings!
"""
        
        self.camera_info_text.SetValue(info)


class CameraCompleteApp(wx.App):
    """Application for complete camera controls demo."""
    
    def OnInit(self):
        self.SetAppName("3D Camera Complete Controls")
        self.SetAppDisplayName("3D Canvas - Complete Camera System")
        
        frame = CameraCompleteFrame()
        frame.Show()
        frame.Raise()
        frame.SetFocus()
        
        if wx.Platform == '__WXMAC__':
            frame.RequestUserAttention(wx.USER_ATTENTION_INFO)
        
        return True


if __name__ == "__main__":
    print("3D Canvas - Complete Camera Controls")
    print("="*50)
    print("🎯 CAMERA MENU FEATURES:")
    print("• Projection Settings (Perspective/Orthographic)")
    print("• Field of View (10° - 170°)")
    print("• Clipping Planes (Near/Far)")
    print("• View Distance Limits")
    print("• Camera Position & Rotation")
    print("• Vanish Point Information")
    print("• Real-time Camera Display")
    print("="*50)
    
    app = CameraCompleteApp()
    app.MainLoop()

