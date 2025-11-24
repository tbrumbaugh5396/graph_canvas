"""
Event handlers for menu bar actions.
"""

import wx
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from graph_canvas.presentation.desktop.gui.main_window import MainWindow

import graph_canvas.presentation.desktop.models.graph as m_graph
import graph_canvas.presentation.desktop.models.node as m_node
import graph_canvas.presentation.desktop.models.edge as m_edge


# File menu handlers
def on_new_graph(main_window: "MainWindow", event):
    """Create a new graph."""
    if main_window.current_graph.modified:
        dialog = wx.MessageDialog(
            main_window,
            "Current graph has unsaved changes. Save before creating new graph?",
            "Save Changes?",
            wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION
        )
        result = dialog.ShowModal()
        dialog.Destroy()
        
        if result == wx.ID_CANCEL:
            return
        elif result == wx.ID_YES:
            if not on_save_graph(main_window, event):
                return  # Cancel if save failed
    
    # Create new graph
    main_window.current_graph = m_graph.Graph()
    main_window.canvas.Refresh()
    main_window.SetTitle("Graph Editor - Untitled Graph")


def on_open_graph(main_window: "MainWindow", event):
    """Open an existing graph."""
    print("DEBUG: on_open_graph invoked")
    if main_window.current_graph.modified:
        dialog = wx.MessageDialog(
            main_window,
            "Current graph has unsaved changes. Save before opening?",
            "Save Changes?",
            wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION
        )
        result = dialog.ShowModal()
        dialog.Destroy()
        
        if result == wx.ID_CANCEL:
            return
        elif result == wx.ID_YES:
            if not on_save_graph(main_window, event):
                return  # Cancel if save failed
    
    # Show file dialog
    with wx.FileDialog(
        main_window, "Open Graph", wildcard="Graph files (*.graph;*.json)|*.graph;*.json",
        style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
    ) as fileDialog:
        if fileDialog.ShowModal() == wx.ID_CANCEL:
            print("DEBUG: Open Graph canceled by user")
            return
        
        # Load graph via MVU if available
        pathname = fileDialog.GetPath()
        print(f"DEBUG: Open Graph selected path: {pathname}")
        try:
            if hasattr(main_window, 'mvu_adapter'):
                from mvc_mvu.messages import make_message
                import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
                # Use command-based read to avoid blocking UI
                print("DEBUG: Dispatching MVU LOAD_GRAPH_FROM_PATH")
                main_window.mvu_adapter.dispatch(
                    make_message(m_main_mvu.Msg.LOAD_GRAPH_FROM_PATH, path=pathname)
                )
                print("DEBUG: MVU dispatch issued for open")
            else:
                with open(pathname, 'r') as file:
                    data = json.load(file)
                    main_window.current_graph = m_graph.Graph.from_dict(data)
                    main_window.current_graph.file_path = pathname
                    main_window.SetTitle(f"Graph Editor - {main_window.current_graph.name}")
                    main_window.canvas.Refresh()
                    print("DEBUG: Open Graph fallback loaded and refreshed")
        except Exception as e:
            wx.MessageBox(f"Failed to open graph: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
            print(f"DEBUG: Open Graph error: {e}")


def on_save_graph(main_window: "MainWindow", event) -> bool:
    """Save the current graph. Returns True if saved successfully."""
    if not main_window.current_graph.file_path:
        return on_save_graph_as(main_window, event)
    
    try:
        if hasattr(main_window, 'mvu_adapter'):
            from mvc_mvu.messages import make_message
            import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
            path = main_window.current_graph.file_path
            content = json.dumps(main_window.current_graph.to_dict(), indent=2)
            main_window.mvu_adapter.dispatch(
                make_message(m_main_mvu.Msg.SAVE_GRAPH_TO_PATH, path=path, content=content)
            )
            return True
        else:
            with open(main_window.current_graph.file_path, 'w') as file:
                json.dump(main_window.current_graph.to_dict(), file, indent=2)
                main_window.current_graph.modified = False
                main_window.SetTitle(f"Graph Editor - {main_window.current_graph.name}")
                return True
    except Exception as e:
        wx.MessageBox(f"Failed to save graph: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
        return False


def on_save_graph_as(main_window: "MainWindow", event) -> bool:
    """Save the current graph with a new name. Returns True if saved successfully."""
    with wx.FileDialog(
        main_window, "Save Graph As", wildcard="Graph files (*.graph)|*.graph",
        style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
    ) as fileDialog:
        if fileDialog.ShowModal() == wx.ID_CANCEL:
            return False
        
        # Save graph
        pathname = fileDialog.GetPath()
        try:
            if hasattr(main_window, 'mvu_adapter'):
                from mvc_mvu.messages import make_message
                import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
                content = json.dumps(main_window.current_graph.to_dict(), indent=2)
                main_window.mvu_adapter.dispatch(
                    make_message(m_main_mvu.Msg.SAVE_GRAPH_TO_PATH, path=pathname, content=content)
                )
                return True
            else:
                with open(pathname, 'w') as file:
                    json.dump(main_window.current_graph.to_dict(), file, indent=2)
                    main_window.current_graph.file_path = pathname
                    main_window.current_graph.modified = False
                    main_window.SetTitle(f"Graph Editor - {main_window.current_graph.name}")
                    return True
        except Exception as e:
            wx.MessageBox(f"Failed to save graph: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
            return False


def on_import_graph(main_window: "MainWindow", event):
    """Import another graph into current."""
    with wx.FileDialog(
        main_window, "Import Graph", wildcard="Graph files (*.graph)|*.graph",
        style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
    ) as fileDialog:
        if fileDialog.ShowModal() == wx.ID_CANCEL:
            return
        
        # Load and merge graph
        pathname = fileDialog.GetPath()
        try:
            with open(pathname, 'r') as file:
                data = json.load(file)
                imported_graph = m_graph.Graph.from_dict(data)
                
                # Add nodes and edges to current graph
                for node in imported_graph.get_all_nodes():
                    if node.id not in main_window.current_graph.nodes:
                        main_window.current_graph.add_node(node)
                
                for edge in imported_graph.get_all_edges():
                    if edge.id not in main_window.current_graph.edges:
                        main_window.current_graph.add_edge(edge)
                
                main_window.current_graph.modified = True
                main_window.canvas.Refresh()
        except Exception as e:
            wx.MessageBox(f"Failed to import graph: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)


def on_copy_graph(main_window: "MainWindow", event):
    """Copy current graph."""
    # Create new graph with same data but new IDs
    new_graph = m_graph.Graph()
    new_graph.name = f"{main_window.current_graph.name} (Copy)"
    
    # Copy nodes with new IDs
    id_map = {}  # old_id -> new_id
    for node in main_window.current_graph.get_all_nodes():
        new_node = m_node.Node(
            x=node.x,
            y=node.y,
            text=node.text,
            width=node.width,
            height=node.height
        )
        new_graph.add_node(new_node)
        id_map[node.id] = new_node.id
    
    # Copy edges with new IDs and mapped node references
    for edge in main_window.current_graph.get_all_edges():
        new_edge = m_edge.Edge(
            source_id=id_map[edge.source_id],
            target_id=id_map[edge.target_id],
            text=edge.text
        )
        new_graph.add_edge(new_edge)
    
    # Add to graphs dictionary
    main_window.graphs[new_graph.id] = new_graph
    wx.MessageBox(f"Created copy: {new_graph.name}", "Graph Copied", wx.OK | wx.ICON_INFORMATION)


def on_delete_graph(main_window: "MainWindow", event):
    """Delete a graph."""
    if len(main_window.graphs) <= 1:
        wx.MessageBox("Cannot delete the last graph.", "Error", wx.OK | wx.ICON_ERROR)
        return
    
    dialog = wx.MessageDialog(
        main_window,
        f"Delete graph '{main_window.current_graph.name}'?",
        "Delete Graph",
        wx.YES_NO | wx.ICON_QUESTION
    )
    if dialog.ShowModal() == wx.ID_YES:
        # Remove from graphs dictionary
        del main_window.graphs[main_window.current_graph.id]
        
        # Switch to another graph
        main_window.current_graph = next(iter(main_window.graphs.values()))
        main_window.SetTitle(f"Graph Editor - {main_window.current_graph.name}")
        main_window.canvas.Refresh()
    dialog.Destroy()


def on_exit(main_window: "MainWindow", event):
    """Exit the application."""
    if main_window.current_graph.modified:
        dialog = wx.MessageDialog(
            main_window,
            "Current graph has unsaved changes. Save before exiting?",
            "Save Changes?",
            wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION
        )
        result = dialog.ShowModal()
        dialog.Destroy()
        
        if result == wx.ID_CANCEL:
            return
        elif result == wx.ID_YES:
            if not on_save_graph(main_window, event):
                return  # Cancel if save failed
    
    main_window.Close()


# Edit menu handlers
def on_undo(main_window: "MainWindow", event):
    """Undo last action."""
    if main_window.managers.undo_redo_manager.can_undo():
        main_window.managers.undo_redo_manager.undo()
        # Dispatch new undo/redo state and counts to MVU
        try:
            if hasattr(main_window, 'mvu_adapter'):
                from mvc_mvu.messages import make_message
                import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
                can_undo = main_window.managers.undo_redo_manager.can_undo()
                can_redo = main_window.managers.undo_redo_manager.can_redo()
                nodes = len(main_window.current_graph.get_all_nodes())
                edges = len(main_window.current_graph.get_all_edges())
                main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_UNDO_REDO_STATE, can_undo=can_undo, can_redo=can_redo))
                main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_COUNTS, nodes=nodes, edges=edges))
        except Exception:
            pass
        main_window.update_ui()
        main_window.canvas.Refresh()


def on_redo(main_window: "MainWindow", event):
    """Redo last undone action."""
    if main_window.managers.undo_redo_manager.can_redo():
        main_window.managers.undo_redo_manager.redo()
        # Dispatch new undo/redo state and counts to MVU
        try:
            if hasattr(main_window, 'mvu_adapter'):
                from mvc_mvu.messages import make_message
                import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
                can_undo = main_window.managers.undo_redo_manager.can_undo()
                can_redo = main_window.managers.undo_redo_manager.can_redo()
                nodes = len(main_window.current_graph.get_all_nodes())
                edges = len(main_window.current_graph.get_all_edges())
                main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_UNDO_REDO_STATE, can_undo=can_undo, can_redo=can_redo))
                main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_COUNTS, nodes=nodes, edges=edges))
        except Exception:
            pass
        main_window.update_ui()
        main_window.canvas.Refresh()


def update_undo_redo_ui(main_window: "MainWindow"):
    """Update undo/redo UI elements."""
    can_undo = main_window.managers.undo_redo_manager.can_undo()
    can_redo = main_window.managers.undo_redo_manager.can_redo()
    if hasattr(main_window, 'mvu_adapter'):
        try:
            from mvc_mvu.messages import make_message
            import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
            main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_UNDO_REDO_STATE, can_undo=can_undo, can_redo=can_redo))
        except Exception:
            pass
    if hasattr(main_window, 'undo_item'):
        main_window.undo_item.Enable(can_undo)
    if hasattr(main_window, 'redo_item'):
        main_window.redo_item.Enable(can_redo)
    toolbar = main_window.GetToolBar()
    if toolbar:
        toolbar.EnableTool(wx.ID_UNDO, can_undo)
        toolbar.EnableTool(wx.ID_REDO, can_redo)


def on_copy_selected(main_window: "MainWindow", event):
    """Copy selected items to clipboard."""
    try:
        if hasattr(main_window, 'mvu_adapter'):
            from mvc_mvu.messages import make_message
            import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
            main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.CLIPBOARD_COPY))
    except Exception:
        pass
    main_window.managers.clipboard_manager.copy_selection(main_window.current_graph)


def on_cut_selected(main_window: "MainWindow", event):
    """Cut selected items (copy then delete)."""
    try:
        if hasattr(main_window, 'mvu_adapter'):
            from mvc_mvu.messages import make_message
            import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
            main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.CLIPBOARD_CUT))
    except Exception:
        pass
    main_window.managers.clipboard_manager.cut_selection(main_window.current_graph, main_window.managers.undo_redo_manager)
    main_window.update_ui()
    main_window.canvas.Refresh()


def on_paste_selected(main_window: "MainWindow", event):
    """Paste items from clipboard."""
    try:
        if hasattr(main_window, 'mvu_adapter'):
            from mvc_mvu.messages import make_message
            import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
            main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.CLIPBOARD_PASTE))
    except Exception:
        pass
    main_window.managers.clipboard_manager.paste_selection(main_window.current_graph, main_window.managers.undo_redo_manager)
    main_window.update_ui()
    main_window.canvas.Refresh()


def on_delete_selected(main_window: "MainWindow", event):
    """Delete selected items."""
    main_window.canvas.on_delete_selection()
    try:
        if hasattr(main_window, 'mvu_adapter'):
            from mvc_mvu.messages import make_message
            import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
            nodes = len(main_window.current_graph.get_all_nodes())
            edges = len(main_window.current_graph.get_all_edges())
            main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_COUNTS, nodes=nodes, edges=edges))
    except Exception:
        pass


def on_select_all(main_window: "MainWindow", event):
    """Select all items."""
    main_window.canvas.select_all()
    try:
        if hasattr(main_window, 'mvu_adapter'):
            from mvc_mvu.messages import make_message
            import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
            nodes = len(main_window.current_graph.get_all_nodes())
            edges = len(main_window.current_graph.get_all_edges())
            main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_COUNTS, nodes=nodes, edges=edges))
    except Exception:
        pass


# View menu handlers
def on_zoom_in(main_window: "MainWindow", event):
    """Zoom in at current mouse position."""
    try:
        if hasattr(main_window, 'mvu_adapter'):
            from mvc_mvu.messages import make_message
            import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
            main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.ZOOM_IN))
            return
    except Exception:
        pass
    main_window.canvas.zoom_in_at_mouse()
    main_window.update_status_bar()


def on_zoom_out(main_window: "MainWindow", event):
    """Zoom out at current mouse position."""
    try:
        if hasattr(main_window, 'mvu_adapter'):
            from mvc_mvu.messages import make_message
            import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
            main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.ZOOM_OUT))
            return
    except Exception:
        pass
    main_window.canvas.zoom_out_at_mouse()
    main_window.update_status_bar()


def on_zoom_fit(main_window: "MainWindow", event):
    """Zoom to fit all items."""
    try:
        if hasattr(main_window, 'mvu_adapter'):
            from mvc_mvu.messages import make_message
            import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
            main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.ZOOM_FIT))
            return
    except Exception:
        pass
    main_window.canvas.zoom_to_fit()


def on_toggle_grid(main_window: "MainWindow", event):
    """Toggle grid visibility."""
    try:
        if hasattr(main_window, 'mvu_adapter'):
            from mvc_mvu.messages import make_message
            import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
            # Infer next visibility from current canvas state (grid_style)
            visible = True
            try:
                visible = getattr(main_window.canvas, 'grid_style', 'grid') != 'grid'
            except Exception:
                visible = False
            main_window.mvu_adapter.dispatch(
                make_message(m_main_mvu.Msg.TOGGLE_GRID)
            )
        else:
            main_window.canvas.toggle_grid()
    except Exception:
        # Fallback to legacy behavior on error
        try:
            main_window.canvas.toggle_grid()
        except Exception:
            pass


def on_toggle_snap(main_window: "MainWindow", event):
    """Toggle grid snapping."""
    try:
        if hasattr(main_window, 'mvu_adapter'):
            from mvc_mvu.messages import make_message
            import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
            main_window.mvu_adapter.dispatch(
                make_message(m_main_mvu.Msg.TOGGLE_SNAP)
            )
        else:
            main_window.canvas.toggle_snap()
    except Exception:
        try:
            main_window.canvas.toggle_snap()
        except Exception:
            pass


# Layout menu handlers
def on_layout_spring(main_window: "MainWindow", event):
    """Apply spring layout."""
    try:
        if hasattr(main_window, 'mvu_adapter'):
            from mvc_mvu.messages import make_message
            import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
            main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.LAYOUT_APPLY, name='spring'))
            return
    except Exception:
        pass
    main_window.canvas.apply_spring_layout()


def on_layout_circular(main_window: "MainWindow", event):
    """Apply circular layout."""
    try:
        if hasattr(main_window, 'mvu_adapter'):
            from mvc_mvu.messages import make_message
            import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
            main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.LAYOUT_APPLY, name='circle'))
            return
    except Exception:
        pass
    main_window.canvas.apply_circular_layout()


def on_layout_hierarchical(main_window: "MainWindow", event):
    """Apply hierarchical layout."""
    try:
        if hasattr(main_window, 'mvu_adapter'):
            from mvc_mvu.messages import make_message
            import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
            main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.LAYOUT_APPLY, name='tree'))
            return
    except Exception:
        pass
    main_window.canvas.apply_hierarchical_layout()


def on_layout_force_directed(main_window: "MainWindow", event):
    """Apply force-directed layout."""
    try:
        if hasattr(main_window, 'mvu_adapter'):
            from mvc_mvu.messages import make_message
            import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
            main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.LAYOUT_APPLY, name='spring'))
            return
    except Exception:
        pass
    main_window.canvas.apply_force_directed_layout()


# Theme menu handlers
def on_manage_themes(main_window: "MainWindow", event):
    """Open theme manager dialog."""
    main_window.manage_themes()


def on_new_theme(main_window: "MainWindow", event):
    """Create new theme."""
    main_window.new_theme()


def on_edit_theme(main_window: "MainWindow", event):
    """Edit current theme."""
    main_window.edit_theme()


def on_delete_theme(main_window: "MainWindow", event):
    """Delete a theme."""
    main_window.delete_theme()


# Settings menu handlers
def on_preferences(main_window: "MainWindow", event):
    """Open preferences dialog."""
    main_window.show_preferences()


def on_configure_hotkeys(main_window: "MainWindow", event):
    """Open hotkey configuration dialog."""
    main_window.configure_hotkeys()


def on_background_layers(main_window: "MainWindow", event):
    """Show background layers dialog."""
    from graph_canvas.presentation.desktop.gui.background_dialog import BackgroundDialog
    dialog = BackgroundDialog(main_window, main_window.canvas.background_manager)
    if dialog.ShowModal() == wx.ID_OK:
        try:
            if hasattr(main_window, 'mvu_adapter'):
                # After changes, just refresh; future: dispatch BG_* messages per action within dialog
                main_window.canvas.Refresh()
            else:
                main_window.canvas.Refresh()
        except Exception:
            main_window.canvas.Refresh()
    dialog.Destroy()


# Graph name handlers
def on_graph_name_changed(main_window: "MainWindow", event):
    """Handle graph name change."""
    new_name = event.GetString()
    main_window.current_graph.name = new_name
    print(f"DEBUG: Graph name changed to: {new_name}")
    # Update window title to reflect new name
    main_window.SetTitle(f"Graph Editor - {new_name}")


# Graph modification handlers
def on_graph_modified(main_window: "MainWindow", event=None):
    """Handle graph modification events."""
    # Update window title to show modified state
    title = main_window.GetTitle()
    if not title.endswith('*') and main_window.current_graph.modified:
        main_window.SetTitle(f"{title}*")
    
    # Update UI elements that depend on graph state
    main_window.update_ui()
    
    # Enable save button if graph is modified
    toolbar = main_window.GetToolBar()
    if toolbar:
        toolbar.EnableTool(wx.ID_SAVE, main_window.current_graph.modified)
    
    # Update undo/redo state
    update_undo_redo_ui(main_window)


# Graph view handlers
def on_make_all_readable(main_window: "MainWindow", event):
    """Make all nodes readable by adjusting their size."""
    for node in main_window.current_graph.get_all_nodes():
        # Get text metrics
        dc = wx.ClientDC(main_window.canvas)
        dc.SetFont(wx.Font(wx.FontInfo(10)))  # Use default font size
        text_width, text_height = dc.GetTextExtent(node.text)
        
        # Add padding
        padding = 20
        new_width = text_width + padding
        new_height = text_height + padding
        
        # Update node size if needed
        if new_width > node.width or new_height > node.height:
            node.width = max(node.width, new_width)
            node.height = max(node.height, new_height)
            print(f"DEBUG: Resized node {node.id} to fit text: {node.width}x{node.height}")
    
    # Refresh display
    main_window.canvas.Refresh()


def on_properties(main_window: "MainWindow", event):
    """Show properties dialog for selected items."""
    selected_nodes = main_window.current_graph.get_selected_nodes()
    selected_edges = main_window.current_graph.get_selected_edges()
    
    if len(selected_nodes) == 1 and not selected_edges:
        # Single node selected
        node = selected_nodes[0]
        dialog = wx.TextEntryDialog(main_window, "Enter node text:", "Edit Node", node.text)
        if dialog.ShowModal() == wx.ID_OK:
            try:
                if hasattr(main_window, 'mvu_adapter'):
                    from mvc_mvu.messages import make_message
                    import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
                    main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_NODE_TEXT, node_id=node.id, text=dialog.GetValue()))
                else:
                    node.text = dialog.GetValue()
                    main_window.canvas.Refresh()
            except Exception:
                node.text = dialog.GetValue()
                main_window.canvas.Refresh()
        dialog.Destroy()
    elif len(selected_edges) == 1 and not selected_nodes:
        # Single edge selected
        edge = selected_edges[0]
        dialog = wx.TextEntryDialog(main_window, "Enter edge text:", "Edit Edge", edge.text)
        if dialog.ShowModal() == wx.ID_OK:
            try:
                if hasattr(main_window, 'mvu_adapter'):
                    from mvc_mvu.messages import make_message
                    import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
                    main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_EDGE_TEXT, edge_id=edge.id, text=dialog.GetValue()))
                else:
                    edge.text = dialog.GetValue()
                    main_window.canvas.Refresh()
            except Exception:
                edge.text = dialog.GetValue()
                main_window.canvas.Refresh()
        dialog.Destroy()
    else:
        wx.MessageBox(
            "Please select exactly one node or edge to edit properties.",
            "Properties",
            wx.OK | wx.ICON_INFORMATION,
            main_window
        )


# Help menu handlers
def on_about(main_window: "MainWindow", event):
    """Show about dialog."""
    main_window.show_about()


def on_help(main_window: "MainWindow", event):
    """Show help dialog."""
    main_window.show_help()


# Panel toggle handlers
def on_toggle_sidebar(main_window: "MainWindow", event):
    """Toggle sidebar visibility."""
    main_window.toggle_sidebar()
    # Update menu item check state
    menu_item = event.GetEventObject()
    if hasattr(menu_item, 'Check'):
        menu_item.Check(main_window.sidebar_visible)


def on_toggle_status_bar(main_window: "MainWindow", event):
    """Toggle status bar visibility."""
    main_window.toggle_status_bar()
    # Update menu item check state
    menu_item = event.GetEventObject()
    if hasattr(menu_item, 'Check'):
        menu_item.Check(main_window.status_bar_visible)