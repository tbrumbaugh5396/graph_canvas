""" 
Event handlers for zooming the graph canvas.
"""


import wx

# Use absolute imports to avoid relative-import issues when the project root is not a package
import graph_canvas.presentation.desktop.gui.main_window as m_main_window
import graph_canvas.presentation.desktop.gui.graph_canvas as m_graph_canvas


def update_canvas_zoom_sensitivity(main_window: "m_main_window.MainWindow"):
    """Update canvas with current zoom sensitivity setting."""

    if hasattr(main_window, 'canvas'):
        main_window.canvas.set_zoom_sensitivity(
            main_window.zoom_sensitivity_field.GetValue())


def on_zoom_to_fit(main_window: "m_main_window.MainWindow", event):
    """Zoom to fit all content in the view."""

    if hasattr(main_window, 'canvas'):
        main_window.canvas.zoom_to_fit()
        main_window.update_status_bar()


def on_zoom_in(main_window: "m_main_window.MainWindow", event):
    """Zoom in at mouse position."""

    if hasattr(main_window, 'canvas'):
        main_window.canvas.zoom_in_at_mouse()
        main_window.update_status_bar()


def on_zoom_out(main_window: "m_main_window.MainWindow", event):
    """Zoom out at mouse position."""

    if hasattr(main_window, 'canvas'):
        main_window.canvas.zoom_out_at_mouse()
        main_window.update_status_bar()


# View menu handlers
def on_zoom_in_menu(main_window: "m_main_window.MainWindow", event):
    """Handle Zoom In command from menu."""

    if hasattr(main_window, 'canvas'):
        main_window.canvas.zoom_in_at_mouse()
        main_window.update_status_bar()


def on_zoom_out_menu(main_window: "m_main_window.MainWindow", event):
    """Handle Zoom Out command from menu."""

    if hasattr(main_window, 'canvas'):
        main_window.canvas.zoom_out_at_mouse()
        main_window.update_status_bar()


def on_zoom_fit(main_window: "m_main_window.MainWindow", event):
    """Handle Zoom to Fit command."""

    if hasattr(main_window, 'canvas'):
        zoom_to_fit(main_window)


def on_center_zoom_toggle(main_window: "m_main_window.MainWindow", event):
    """Handle center zoom toggle."""

    enabled = main_window.center_zoom_cb.GetValue()
    print(f"DEBUG: 🔍 Center zoom enabled: {enabled}")

    if enabled:
        # Zoom into center of world view
        main_window.canvas.zoom_to_world_center(zoom_in=True)
    else:
        # Zoom out from center of world view
        main_window.canvas.zoom_to_world_center(zoom_in=False)

    # Update canvas center zoom enabled state
    if hasattr(main_window, 'canvas'):
        main_window.canvas.center_zoom_enabled = enabled


def zoom_in(main_window: "m_main_window.MainWindow", factor: float = 1.2):
    """Zoom in by the given factor at current mouse position."""

    if hasattr(main_window, 'canvas'):
        main_window.canvas.zoom_at_point(factor, main_window.canvas.current_mouse_pos)


def zoom_out(main_window: "m_main_window.MainWindow", factor: float = 0.8):
    """Zoom out by the given factor at current mouse position."""

    if hasattr(main_window, 'canvas'):
        main_window.canvas.zoom_at_point(factor, main_window.canvas.current_mouse_pos)


def zoom_to_fit(main_window: "m_main_window.MainWindow"):
    """Zoom to fit all nodes in the view."""

    if not main_window.graph.nodes:
        return

    bounds = main_window.graph.get_bounds()
    left, top, right, bottom = bounds

    if left == right or top == bottom:
        return

    # Add padding
    padding = 50
    content_width = right - left + padding * 2
    content_height = bottom - top + padding * 2

    # Calculate zoom to fit
    size = main_window.canvas.GetSize()
    zoom_x = size.width / content_width
    zoom_y = size.height / content_height
    main_window.canvas.zoom = min(zoom_x, zoom_y, main_window.canvas.max_zoom)

    # Center the content
    center_x = (left + right) / 2
    center_y = (top + bottom) / 2
    main_window.canvas.pan_x = size.width / 2 - center_x * main_window.canvas.zoom
    main_window.canvas.pan_y = size.height / 2 - center_y * main_window.canvas.zoom

    main_window.canvas.Refresh()
