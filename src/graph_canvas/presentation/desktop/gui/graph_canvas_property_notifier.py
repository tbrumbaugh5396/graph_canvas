"""
Mixin class for notifying property panel of graph changes.
"""

import graph_canvas.presentation.desktop.event_handlers.property_panel_event_handler as m_property_panel_event_handler


class GraphCanvasPropertyNotifierMixin:
    """Mixin class to add property panel notification to GraphCanvas."""
    
    def notify_graph_modified(self):
        """Notify listeners that the graph has been modified."""
        self.graph_modified.emit()
        if hasattr(self, 'main_window'):
            m_property_panel_event_handler.on_graph_changed(self.main_window)
        self.Refresh()
