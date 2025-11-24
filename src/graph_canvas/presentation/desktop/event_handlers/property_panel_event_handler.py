"""
Event handlers for property panel.
"""

import wx

import graph_canvas.presentation.desktop.gui.main_window as m_main_window
import graph_canvas.presentation.desktop.gui.property_panel as m_property_panel


def on_graph_changed(main_window: 'm_main_window.MainWindow'):
    """Handle graph changes."""
    if hasattr(main_window, 'property_panel'):
        main_window.property_panel.validate_all()


def on_property_changed(main_window: 'm_main_window.MainWindow'):
    """Handle property changes."""
    if hasattr(main_window, 'property_panel'):
        main_window.property_panel.validate_all()


def on_save_properties(main_window: 'm_main_window.MainWindow') -> dict:
    """Save properties to file."""
    if hasattr(main_window, 'property_panel'):
        return {'properties': main_window.property_panel.save_properties()}
    return {'properties': []}


def on_load_properties(main_window: 'm_main_window.MainWindow', data: dict):
    """Load properties from file."""
    if hasattr(main_window, 'property_panel'):
        main_window.property_panel.load_properties(data.get('properties', []))
