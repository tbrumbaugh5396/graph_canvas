"""
Event handlers for the status bar.
"""


import graph_canvas.presentation.desktop.gui.main_window as m_main_window
import graph_canvas.presentation.desktop.gui.tool_selector as m_tool_selector


def update_status_bar(main_window: "m_main_window.MainWindow"):
        """Update status bar with current information."""

        if hasattr(main_window, 'statusbar'):
            # Update zoom percentage
            zoom_percent = int(main_window.canvas.zoom *
                               100) if hasattr(main_window, 'canvas') else 100
            main_window.statusbar.SetStatusText(f"Zoom: {zoom_percent}%", 2)
            
            # Update tool info
            current_tool = m_tool_selector.get_current_tool(main_window)
            main_window.statusbar.SetStatusText(f"Tool: {current_tool.title()}", 1)
