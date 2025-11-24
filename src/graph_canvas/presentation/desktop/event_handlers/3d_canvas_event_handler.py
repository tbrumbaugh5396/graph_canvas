"""
Event handlers for 3D Canvas operations and menu items.
"""

import wx
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from graph_canvas.presentation.desktop.gui.main_window import MainWindow


def on_grid_color_x(main_window: "MainWindow", event):
    """Show color picker for X-direction grid lines."""
    if not hasattr(main_window, 'canvas_3d') or main_window.canvas_3d is None:
        wx.MessageBox("3D Canvas is not available.", "Error", wx.OK | wx.ICON_ERROR)
        return
    
    current_colors = main_window.canvas_3d.get_grid_colors()
    current_color = wx.Colour(*current_colors[0])  # X color
    
    data = wx.ColourData()
    data.SetColour(current_color)
    
    dialog = wx.ColourDialog(main_window, data)
    if dialog.ShowModal() == wx.ID_OK:
        selected_color = dialog.GetColourData().GetColour()
        color_tuple = (selected_color.Red(), selected_color.Green(), selected_color.Blue())
        main_window.canvas_3d.set_grid_color_x(color_tuple)
        print(f"DEBUG: Set X grid color to {color_tuple}")
    
    dialog.Destroy()


def on_grid_color_y(main_window: "MainWindow", event):
    """Show color picker for Y-direction grid lines."""
    if not hasattr(main_window, 'canvas_3d') or main_window.canvas_3d is None:
        wx.MessageBox("3D Canvas is not available.", "Error", wx.OK | wx.ICON_ERROR)
        return
    
    current_colors = main_window.canvas_3d.get_grid_colors()
    current_color = wx.Colour(*current_colors[1])  # Y color
    
    data = wx.ColourData()
    data.SetColour(current_color)
    
    dialog = wx.ColourDialog(main_window, data)
    if dialog.ShowModal() == wx.ID_OK:
        selected_color = dialog.GetColourData().GetColour()
        color_tuple = (selected_color.Red(), selected_color.Green(), selected_color.Blue())
        main_window.canvas_3d.set_grid_color_y(color_tuple)
        print(f"DEBUG: Set Y grid color to {color_tuple}")
    
    dialog.Destroy()


def on_grid_color_z(main_window: "MainWindow", event):
    """Show color picker for Z-direction grid lines."""
    if not hasattr(main_window, 'canvas_3d') or main_window.canvas_3d is None:
        wx.MessageBox("3D Canvas is not available.", "Error", wx.OK | wx.ICON_ERROR)
        return
    
    current_colors = main_window.canvas_3d.get_grid_colors()
    current_color = wx.Colour(*current_colors[2])  # Z color
    
    data = wx.ColourData()
    data.SetColour(current_color)
    
    dialog = wx.ColourDialog(main_window, data)
    if dialog.ShowModal() == wx.ID_OK:
        selected_color = dialog.GetColourData().GetColour()
        color_tuple = (selected_color.Red(), selected_color.Green(), selected_color.Blue())
        main_window.canvas_3d.set_grid_color_z(color_tuple)
        print(f"DEBUG: Set Z grid color to {color_tuple}")
    
    dialog.Destroy()


def on_toggle_3d_grid(main_window: "MainWindow", event):
    """Toggle 3D grid visibility."""
    if not hasattr(main_window, 'canvas_3d') or main_window.canvas_3d is None:
        wx.MessageBox("3D Canvas is not available.", "Error", wx.OK | wx.ICON_ERROR)
        return
    
    main_window.canvas_3d.show_grid = not main_window.canvas_3d.show_grid
    main_window.canvas_3d.Refresh()
    print(f"DEBUG: 3D grid {'enabled' if main_window.canvas_3d.show_grid else 'disabled'}")


def on_toggle_3d_axes(main_window: "MainWindow", event):
    """Toggle 3D axes visibility."""
    if not hasattr(main_window, 'canvas_3d') or main_window.canvas_3d is None:
        wx.MessageBox("3D Canvas is not available.", "Error", wx.OK | wx.ICON_ERROR)
        return
    
    main_window.canvas_3d.show_axes = not main_window.canvas_3d.show_axes
    main_window.canvas_3d.Refresh()
    print(f"DEBUG: 3D axes {'enabled' if main_window.canvas_3d.show_axes else 'disabled'}")


def on_reset_3d_camera(main_window: "MainWindow", event):
    """Reset 3D camera to default position."""
    if not hasattr(main_window, 'canvas_3d') or main_window.canvas_3d is None:
        wx.MessageBox("3D Canvas is not available.", "Error", wx.OK | wx.ICON_ERROR)
        return
    
    main_window.canvas_3d.reset_camera()
    print("DEBUG: 3D camera reset to default position")


def on_reset_3d_world(main_window: "MainWindow", event):
    """Reset 3D world transformation to default."""
    if not hasattr(main_window, 'canvas_3d') or main_window.canvas_3d is None:
        wx.MessageBox("3D Canvas is not available.", "Error", wx.OK | wx.ICON_ERROR)
        return
    
    main_window.canvas_3d.reset_world()
    print("DEBUG: 3D world transformation reset to default")


def on_toggle_3d_projection(main_window: "MainWindow", event):
    """Toggle between perspective and orthographic projection."""
    if not hasattr(main_window, 'canvas_3d') or main_window.canvas_3d is None:
        wx.MessageBox("3D Canvas is not available.", "Error", wx.OK | wx.ICON_ERROR)
        return
    
    from graph_canvas.presentation.desktop.gui.3d_canvas import ProjectionMode
    
    if main_window.canvas_3d.camera.projection_mode == ProjectionMode.PERSPECTIVE:
        main_window.canvas_3d.camera.projection_mode = ProjectionMode.ORTHOGRAPHIC
    else:
        main_window.canvas_3d.camera.projection_mode = ProjectionMode.PERSPECTIVE
    
    main_window.canvas_3d.Refresh()
    print(f"DEBUG: Switched to {main_window.canvas_3d.camera.projection_mode.value} projection")


def on_toggle_3d_view_limits(main_window: "MainWindow", event):
    """Toggle 3D view limits on/off."""
    if not hasattr(main_window, 'canvas_3d') or main_window.canvas_3d is None:
        wx.MessageBox("3D Canvas is not available.", "Error", wx.OK | wx.ICON_ERROR)
        return
    
    main_window.canvas_3d.camera.use_view_limits = not main_window.canvas_3d.camera.use_view_limits
    main_window.canvas_3d.Refresh()
    print(f"DEBUG: 3D view limits {'enabled' if main_window.canvas_3d.camera.use_view_limits else 'disabled'}")

