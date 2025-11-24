"""Tool selector event handler."""


import wx

import graph_canvas.presentation.desktop.gui.main_window as m_main_window


def on_tool_select(main_window: "m_main_window.MainWindow", event):
    """Handle tool selection."""
    # Get all tool buttons
    tool_buttons = {
        'select': main_window.tool_select,
        'node': main_window.tool_node,
        'edge': main_window.tool_edge,
        'move': main_window.tool_move,
        'rotate': main_window.tool_rotate,
    }
    
    # Find which tool was selected
    selected_tool = None
    for tool_name, button in tool_buttons.items():
        if button.GetValue():
            selected_tool = tool_name
            break
    
    if selected_tool:
        print(f"DEBUG: Tool selected: {selected_tool}")
        # Update canvas tool
        main_window.canvas.set_tool(selected_tool)
        # Update other buttons
        for tool_name, button in tool_buttons.items():
            if tool_name != selected_tool:
                button.SetValue(False)
    
    event.Skip()


def on_tool_change(main_window: "m_main_window.MainWindow", tool_name: str):
    """Change the current tool programmatically."""
    # Get all tool buttons
    tool_buttons = {
        'select': main_window.tool_select,
        'node': main_window.tool_node,
        'edge': main_window.tool_edge,
        'move': main_window.tool_move,
        'rotate': main_window.tool_rotate,
    }
    
    # Update button states
    for name, button in tool_buttons.items():
        button.SetValue(name == tool_name)
    
    # Update canvas tool
    main_window.canvas.set_tool(tool_name)
    print(f"DEBUG: Tool changed to: {tool_name}")

