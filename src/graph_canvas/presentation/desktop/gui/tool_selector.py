"""
Tool selector for the graph editor application.
"""


import graph_canvas.presentation.desktop.gui.main_window as m_main_window


def get_current_tool(main_window: "m_main_window.MainWindow"):
        """Get the currently selected tool."""

        if main_window.tool_select.GetValue():
            return "select"
        elif main_window.tool_node.GetValue():
            return "node"
        elif main_window.tool_edge.GetValue():
            return "edge"
        elif main_window.tool_move.GetValue():
            return "move"
        elif main_window.tool_rotate.GetValue():
            return "rotate"
        elif main_window.tool_rotate_element.GetValue():
            return "rotate_element"
        elif main_window.tool_drag_into.GetValue():
            return "drag_into"
        elif main_window.tool_expand.GetValue():
            return "expand"
        elif main_window.tool_collapse.GetValue():
            return "collapse"
        elif main_window.tool_recursive_expand.GetValue():
            return "recursive_expand"
        elif main_window.tool_recursive_collapse.GetValue():
            return "recursive_collapse"
        return "select"
