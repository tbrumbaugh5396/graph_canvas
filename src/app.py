#!/usr/bin/env python3
"""
Main application file for the Graph Editor.

A comprehensive graph editing application built with wxPython that supports
creating, editing, and managing graphs with nodes and edges.
"""

import sys
import os
from graph_canvas.presentation.desktop.utils.path_helpers import ensure_project_on_path, ensure_mvc_mvu_on_path

# Check if wxPython is available
try:
    import wx
except ImportError:
    print("Error: wxPython is not installed.")
    print("Please install it using: pip install wxPython")
    sys.exit(1)


# Ensure paths work for both source and package execution
ensure_project_on_path(__file__)
ensure_mvc_mvu_on_path()

from graph_canvas.presentation.desktop.gui.main_window import MainWindow


class GraphEditorApp(wx.App):
    """Main application class."""

    def OnInit(self):
        """Initialize the application."""

        # Create and show the main window
        self.main_window = MainWindow()
        self.main_window.Show()
        self.SetTopWindow(self.main_window)

        return True

    def OnExit(self):
        """Handle application exit."""
        # Perform any cleanup here if needed
        window = getattr(self, "main_window", None)
        if window is not None:
            try:
                if hasattr(window, "IsBeingDeleted") and not window.IsBeingDeleted():
                    window.Destroy()
            except RuntimeError:
                # Window already destroyed; ignore
                pass
            finally:
                self.main_window = None
        return super().OnExit()
