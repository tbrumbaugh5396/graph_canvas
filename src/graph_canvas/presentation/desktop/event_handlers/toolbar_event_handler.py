"""
Event handlers for the toolbar.
"""


import graph_canvas.presentation.desktop.gui.main_window as m_main_window
import graph_canvas.presentation.desktop.gui.tool_selector as m_tool_selector


def on_tool_changed(main_window: "m_main_window.MainWindow", event):
    """Handle tool selection change."""

    tool = m_tool_selector.get_current_tool(main_window)
    if hasattr(main_window, 'canvas'):
        main_window.canvas.set_tool(tool)
        # Update sensitivity when switching to move tool
        if tool == "move":
            main_window.update_canvas_sensitivity()
