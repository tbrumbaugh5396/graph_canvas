""""
Event handlers for the graph canvas.
"""


import wx

import graph_canvas.presentation.desktop.gui.main_window as m_main_window


def on_toggle_grid(main_window: "m_main_window.MainWindow", event):
    """Toggle grid visibility."""

    main_window.current_graph.grid_visible = not main_window.current_graph.grid_visible
    main_window.canvas.Refresh()


def on_grid_style_changed(main_window: "m_main_window.MainWindow", event):
    """Handle grid style change."""
    
    styles = ["none", "grid", "dots"]
    selection = event.GetEventObject().GetSelection()
    if hasattr(main_window.canvas, 'grid_style'):
        # Update canvas
        main_window.canvas.grid_style = styles[selection] if selection >= 0 else "grid"
        main_window.canvas.Refresh()
        
        # Sync both grid style choices
        if hasattr(main_window, 'main_grid_style_choice'):
            main_window.main_grid_style_choice.SetSelection(selection)
        
        print(f"DEBUG: Grid style changed to: {main_window.canvas.grid_style}")


def on_grid_spacing_changed(main_window: "m_main_window.MainWindow", event):
    """Handle grid/dot spacing change."""
    
    if hasattr(main_window.canvas, 'grid_spacing'):
        main_window.canvas.grid_spacing = main_window.grid_spacing_field.GetValue()
        main_window.canvas.Refresh()
        print(f"DEBUG: Grid/dot spacing changed to: {main_window.canvas.grid_spacing}")

def on_dot_size_changed(main_window: "m_main_window.MainWindow", event):
    """Handle dot size slider change."""
    
    if hasattr(main_window.canvas, 'dot_size'):
        main_window.canvas.dot_size = main_window.dot_size_slider.GetValue()
        main_window.canvas.Refresh()
        print(f"DEBUG: Dot size changed to: {main_window.canvas.dot_size}")

def on_snap_to_grid_changed(main_window: "m_main_window.MainWindow", event):
    """Handle snap to grid toggle."""
    
    if hasattr(main_window.canvas, 'snap_to_grid'):
        main_window.canvas.snap_to_grid = main_window.snap_to_grid_cb.GetValue()
        print(f"DEBUG: Snap to grid {'enabled' if main_window.canvas.snap_to_grid else 'disabled'}")




def on_grid_color(main_window: "m_main_window.MainWindow", event):
    pass


def on_arrow_position_changed(main_window: "m_main_window.MainWindow", event):
    """Handle arrow position slider change."""

    if not hasattr(main_window,
                    'current_curve_edge') or not main_window.current_curve_edge:
        return
    
    edge = main_window.current_curve_edge
    slider_value = main_window.arrow_position_slider.GetValue()
    arrow_pos = slider_value / 100.0  # Convert to 0.0-1.0 range
    
    edge.arrow_position = arrow_pos
    main_window.arrow_position_text.SetValue(f"{arrow_pos:.2f}")
    
    main_window.canvas.Refresh()
    print(f"DEBUG: 🏹 Arrow position changed to {arrow_pos:.2f}")


def on_arrow_position_text_changed(main_window: "m_main_window.MainWindow", event):
    """Handle arrow position text input change."""

    if not hasattr(main_window,
                    'current_curve_edge') or not main_window.current_curve_edge:
        return
    
    try:
        arrow_pos = float(main_window.arrow_position_text.GetValue())
        arrow_pos = max(0.0, min(1.0, arrow_pos))  # Clamp to 0.0-1.0
        
        edge = main_window.current_curve_edge
        edge.arrow_position = arrow_pos
        main_window.arrow_position_slider.SetValue(int(arrow_pos * 100))
        
        main_window.canvas.Refresh()
        print(f"DEBUG: 🏹 Arrow position set to {arrow_pos:.2f}")
    except ValueError:
        # Invalid input, ignore
        pass


def on_nested_edge_indicators_changed(main_window: "m_main_window.MainWindow", event):
    """Handle nested edge indicators toggle."""

    if hasattr(main_window.canvas, 'show_nested_edge_indicators'):
        main_window.canvas.show_nested_edge_indicators = main_window.nested_edge_indicators_cb.GetValue(
        )
        main_window.canvas.Refresh()
    print(
        f"DEBUG: Nested edge indicators: {main_window.nested_edge_indicators_cb.GetValue()}"
    )


def on_grid_snap_changed(main_window: "m_main_window.MainWindow", event):
    """Handle grid snapping toggle."""

    if hasattr(main_window.canvas, 'grid_snapping_enabled'):
        main_window.canvas.grid_snapping_enabled = main_window.grid_snap_cb.GetValue()
        print(f"DEBUG: Grid snapping: {main_window.grid_snap_cb.GetValue()}")


def on_snap_anchor_changed(main_window: "m_main_window.MainWindow", event):
    """Handle snap anchor point change."""

    anchor_names = [
        "upper_left", "upper_center", "upper_right", "left_center",
        "center", "right_center", "bottom_left", "bottom_center",
        "bottom_right"
    ]
    selection = main_window.snap_anchor_choice.GetSelection()
    if hasattr(main_window.canvas, 'snap_anchor'):
        main_window.canvas.snap_anchor = anchor_names[
            selection] if selection >= 0 else "center"
        print(
            f"DEBUG: 🔗 Snap anchor changed to: {main_window.canvas.snap_anchor}")
    else:
        print(f"DEBUG: 🔗 ❌ Canvas doesn't have snap_anchor attribute!")


def on_edge_type_changed(main_window: "m_main_window.MainWindow", event):
    """Handle edge type change."""

    edge_types = [
        "straight", "curved", "bspline", "bezier", "cubic_spline", "nurbs",
        "polyline", "composite", "freeform"
    ]
    selection = main_window.edge_type_choice.GetSelection()
    if hasattr(main_window.canvas, 'edge_rendering_type'):
        new_edge_type = edge_types[
            selection] if selection >= 0 else "bspline"
        main_window.canvas.edge_rendering_type = new_edge_type
        
        # Update rendering type and reinitialize control points for selected edges
        selected_edges = main_window.current_graph.get_selected_edges()
        for edge in selected_edges:
            # Store previous type for debugging
            previous_type = getattr(
                edge, 'rendering_type',
                None) or main_window.canvas.edge_rendering_type
            # Always set the edge's rendering type to the new global type for selected edges
            edge.rendering_type = new_edge_type
            source_node = main_window.current_graph.get_node(edge.source_id)
            target_node = main_window.current_graph.get_node(edge.target_id)
            if source_node and target_node:
                print(
                    f"DEBUG: 🔄 Setting edge {edge.id} type: {previous_type} -> {new_edge_type}, reinitializing control points"
                )
                main_window.canvas.initialize_control_points(
                    edge, source_node, target_node)
                # Check for any invisible nodes after edge type change
                main_window.canvas.debug_check_node_visibility(
                    f"After edge type change to {new_edge_type}")
                print(
                    f"DEBUG: 🎛️ Edge {edge.id} now has {len(edge.control_points)} control points"
                )
        
        main_window.canvas.Refresh()
        print(
            f"DEBUG: Edge rendering type: {main_window.canvas.edge_rendering_type}"
        )
        
        # Update selection display to show/hide curve controls when global type changes
        main_window.update_selection_display()


def on_edge_directed_changed(main_window: "m_main_window.MainWindow", event):
    """Handle edge directed checkbox change for selected edges."""

    directed_value = main_window.edge_directed_cb.GetValue()
    selected_edges = main_window.current_graph.get_selected_edges()

    if selected_edges:
        # Update all selected edges
        for edge in selected_edges:
            edge.directed = directed_value
            print(
                f"DEBUG: Updated edge {edge.id} directed = {directed_value}"
            )

        # Mark graph as modified and refresh
        main_window.current_graph.modified = True
        main_window.canvas.Refresh()
        main_window.update_ui()

        print(
            f"DEBUG: Set {len(selected_edges)} selected edges to directed={directed_value}"
        )
    else:
        print(
            f"DEBUG: No edges selected, directed checkbox will affect new edges only"
        )


def on_prevent_edge_overlap_changed(main_window: "m_main_window.MainWindow", event):
    """Handle prevent edge overlap toggle."""

    if hasattr(main_window.canvas, 'prevent_edge_overlap'):
        main_window.canvas.prevent_edge_overlap = main_window.prevent_edge_overlap_cb.GetValue(
        )
        main_window.canvas.Refresh()
        print(
            f"DEBUG: Prevent edge overlap: {main_window.prevent_edge_overlap_cb.GetValue()}"
        )


def on_enable_control_points_changed(main_window: "m_main_window.MainWindow", event):
    """Handle enable control points toggle."""

    if hasattr(main_window.canvas, 'control_points_enabled'):
        main_window.canvas.control_points_enabled = main_window.enable_control_points_cb.GetValue(
        )
        main_window.canvas.Refresh()
        print(
            f"DEBUG: 🎛️ Control points enabled: {main_window.enable_control_points_cb.GetValue()}"
        )
    else:
        print(
            f"DEBUG: 🎛️ ❌ Canvas doesn't have control_points_enabled attribute!"
        )


def on_relative_control_points_changed(main_window: "m_main_window.MainWindow", event):
    """Handle relative control points toggle."""

    if hasattr(main_window.canvas, 'relative_control_points'):
        main_window.canvas.relative_control_points = main_window.relative_control_points_cb.GetValue(
        )
        print(
            f"DEBUG: 🎛️ Relative control points: {main_window.relative_control_points_cb.GetValue()}"
        )
    else:
        print(
            f"DEBUG: 🎛️ ❌ Canvas doesn't have relative_control_points attribute!"
        )


def on_edge_anchor_changed(main_window: "m_main_window.MainWindow", event):
    """Handle edge anchor position change."""

    anchor_names = [
        "free", "center", "nearest_face", "left_center", "right_center",
                    "top_center", "bottom_center", "top_left", "top_right", 
        "bottom_left", "bottom_right"
    ]
    selection = main_window.edge_anchor_choice.GetSelection()
    if hasattr(main_window.canvas, 'edge_anchor_mode'):
        main_window.canvas.edge_anchor_mode = anchor_names[
            selection] if selection >= 0 else "nearest_face"
        main_window.canvas.Refresh()
        print(
            f"DEBUG: 🔗 Edge anchor mode changed to: {main_window.canvas.edge_anchor_mode}"
        )
    else:
        print(
            f"DEBUG: 🔗 ❌ Canvas doesn't have edge_anchor_mode attribute!")


def on_show_anchor_points_changed(main_window: "m_main_window.MainWindow", event):
    """Handle show anchor points toggle."""

    if hasattr(main_window.canvas, 'show_anchor_points'):
        main_window.canvas.show_anchor_points = main_window.show_anchor_points_cb.GetValue(
        )
        main_window.canvas.Refresh()
        print(
            f"DEBUG: 🔗 Show anchor points: {main_window.show_anchor_points_cb.GetValue()}"
        )
    else:
        print(
            f"DEBUG: 🔗 ❌ Canvas doesn't have show_anchor_points attribute!"
        )


    # Graph restriction event handlers


def on_no_loops_changed(main_window: "m_main_window.MainWindow", event):
    """Handle no loops checkbox change."""

    main_window.meta_graph_information.no_loops = main_window.no_loops_cb.GetValue()
    print(f"DEBUG: 🔒 No loops restriction: {main_window.meta_graph_information.no_loops}")
    # Update canvas restrictions
    if hasattr(main_window, 'canvas'):
        main_window.canvas.no_loops = main_window.meta_graph_information.no_loops


def on_no_multigraphs_changed(main_window, event):
    """Handle no multigraphs checkbox change."""

    main_window.meta_graph_information.no_multigraphs = main_window.no_multigraphs_cb.GetValue()
    print(f"DEBUG: 🔒 No multigraphs restriction: {main_window.meta_graph_information.no_multigraphs}")
    # Update canvas restrictions
    if hasattr(main_window, 'canvas'):
        main_window.canvas.no_multigraphs = main_window.meta_graph_information.no_multigraphs


def on_graph_type_restriction_changed(main_window: "m_main_window.MainWindow", event):
    """Handle graph type restriction dropdown change."""

    main_window.meta_graph_information.graph_type_restriction = main_window.graph_type_restriction_choice.GetSelection(
    )
    restriction_names = [
        "No Restrictions", "Require Directed Graph",
        "Require Undirected Graph"
    ]
    print(
        f"DEBUG: 🔒 Graph type restriction: {restriction_names[main_window.meta_graph_information.graph_type_restriction]}"
    )
    # Update canvas restrictions
    if hasattr(main_window, 'canvas'):
        main_window.canvas.graph_type_restriction = main_window.meta_graph_information.graph_type_restriction


def on_graph_type_changed(main_window: "m_main_window.MainWindow", event):
    """Handle graph type dropdown change."""

    main_window.meta_graph_information.selected_graph_type = main_window.graph_type_choice.GetSelection()
    graph_types = [
        "List", "Tree", "DAG",
        "Graph",
        "├─ Hypergraph",
        "├─ Nested Graph",
        "└─ Ubergraph",
        "   └─ Typed Ubergraph"
    ]
    print(
        f"DEBUG: 📊 Graph type changed to: {graph_types[main_window.meta_graph_information.selected_graph_type]}"
    )
    # Update canvas graph type
    if hasattr(main_window, 'canvas'):
        main_window.canvas.selected_graph_type = main_window.meta_graph_information.selected_graph_type

    # Convert existing items based on selected graph type
    try:
        sel = main_window.meta_graph_information.selected_graph_type
        # 6: Ubergraph, 7: Typed Ubergraph
        if sel in (6, 7):
            # Convert all edges to uberedges (hyperedges with ubergraph visualization)
            for edge in main_window.current_graph.get_all_edges():
                # Ensure hyperedge flags and lists
                if getattr(edge, 'source_id', None) and edge.source_id not in edge.source_ids:
                    edge.source_ids.append(edge.source_id)
                if getattr(edge, 'target_id', None) and edge.target_id not in edge.target_ids:
                    edge.target_ids.append(edge.target_id)
                edge.is_hyperedge = True
                edge.hyperedge_visualization = "ubergraph"
                # Default to line_graph view so uberedges connect edge-to-edge
                edge.hyperedge_view = "line_graph"
                # Seed uber position at midpoint
                try:
                    src = main_window.current_graph.get_node(edge.source_id)
                    tgt = main_window.current_graph.get_node(edge.target_id)
                    if src and tgt:
                        edge.uber_x = (src.x + tgt.x) / 2.0
                        edge.uber_y = (src.y + tgt.y) / 2.0
                except Exception:
                    pass
        elif sel == 4:  # Hypergraph
            for edge in main_window.current_graph.get_all_edges():
                # Keep as hyperedge but default to line visualization
                if getattr(edge, 'source_id', None) and edge.source_id not in edge.source_ids:
                    edge.source_ids.append(edge.source_id)
                if getattr(edge, 'target_id', None) and edge.target_id not in edge.target_ids:
                    edge.target_ids.append(edge.target_id)
                edge.is_hyperedge = True
                edge.hyperedge_visualization = "lines"
        else:
            # For normal graph types, revert to standard edges
            for edge in main_window.current_graph.get_all_edges():
                edge.hyperedge_visualization = "lines"
                # Keep is_hyperedge only if multiple endpoints remain
                if len(getattr(edge, 'source_ids', []) or []) <= 1 and len(getattr(edge, 'target_ids', []) or []) <= 1:
                    edge.is_hyperedge = False
        # Refresh view
        if hasattr(main_window, 'canvas'):
            main_window.canvas.Refresh()
    except Exception as e:
        print(f"DEBUG: Graph type conversion error: {e}")


def on_checkboard_background_toggle(main_window: "m_main_window.MainWindow", event):
    """Handle checkboard background toggle."""

    main_window.display.checkerboard_background = main_window.checkboard_bg_cb.GetValue()
    print(f"DEBUG: 🏁 Checkboard background: {main_window.display.checkerboard_background}")
    # Update canvas checkboard background
    if hasattr(main_window, 'canvas'):
        main_window.canvas.checkerboard_background = main_window.display.checkerboard_background
        if main_window.display.checkerboard_background and hasattr(main_window.canvas, '_checkboard_crash_disabled'):
            # Reset crash guard when re-enabling
            main_window.canvas._checkboard_crash_disabled = False
        main_window.canvas.Refresh()  # Refresh to show/hide checkboard


def on_checker_color1(main_window: "m_main_window.MainWindow", event):
    """Handle checker color 1 selection with background synchronization."""

    current_color = main_window.canvas.checker_color1 if hasattr(
        main_window, 'canvas') else wx.Colour(240, 240, 240)
    dialog = wx.ColourDialog(main_window)
    dialog.GetColourData().SetColour(current_color)

    if dialog.ShowModal() == wx.ID_OK:
        new_color = dialog.GetColourData().GetColour()
        rgb_tuple = (new_color.Red(), new_color.Green(), new_color.Blue())
        
        # Update checkboard color 1 button (fix: was updating wrong button)
        main_window.checker_color1_btn.SetBackgroundColour(new_color)
        
        if hasattr(main_window, 'canvas'):
            # Update checkboard color 1
            main_window.canvas.checker_color1 = new_color
            
            # SYNC: Update background color to match checkboard color 1
            main_window.canvas.background_color = rgb_tuple
            
            # Update background color button to match
            if hasattr(main_window, 'bg_color_btn'):
                main_window.bg_color_btn.SetBackgroundColour(new_color)
            
            main_window.canvas.Refresh()
            print(f"DEBUG: 🏁 Checkboard color 1 changed to: {rgb_tuple}")
            print(f"DEBUG: 🎨 Background color synced to match checkboard color 1")

    dialog.Destroy()


def on_checker_color2(main_window: "m_main_window.MainWindow", event):
    """Handle checker color 2 (alternating squares) selection."""

    # Current color comes from canvas.checker_color2 if available
    if hasattr(main_window, 'canvas') and hasattr(main_window.canvas, 'checker_color2'):
        current_color = main_window.canvas.checker_color2
    else:
        current_color = wx.Colour(200, 200, 200)

    dialog = wx.ColourDialog(main_window)
    dialog.GetColourData().SetColour(current_color)

    if dialog.ShowModal() == wx.ID_OK:
        new_color = dialog.GetColourData().GetColour()
        rgb_tuple = (new_color.Red(), new_color.Green(), new_color.Blue())
        # Update button
        if hasattr(main_window, 'checker_color2_btn'):
            main_window.checker_color2_btn.SetBackgroundColour(new_color)

        # Update canvas color and refresh (store as tuple to avoid wx lifetime issues)
        if hasattr(main_window, 'canvas'):
            main_window.canvas.checker_color2 = rgb_tuple
            main_window.canvas.Refresh()
            print(f"DEBUG: 🏁 Checkboard color 2 (alternating) changed to tuple: {rgb_tuple}")

    dialog.Destroy()

def on_background_color(main_window: "m_main_window.MainWindow", event):
    """Handle background color selection with checkboard synchronization."""

    current_color = wx.Colour(*main_window.canvas.background_color) if hasattr(
        main_window, 'canvas') else wx.Colour(255, 255, 255)
    dialog = wx.ColourDialog(main_window)
    dialog.GetColourData().SetColour(current_color)

    if dialog.ShowModal() == wx.ID_OK:
        new_color = dialog.GetColourData().GetColour()
        rgb_tuple = (new_color.Red(), new_color.Green(), new_color.Blue())
        
        # Update background color button
        main_window.bg_color_btn.SetBackgroundColour(new_color)
        
        if hasattr(main_window, 'canvas'):
            # Update background color
            main_window.canvas.background_color = rgb_tuple
            
            # SYNC: Update checkboard color 1 to match background (they should always be the same)
            main_window.canvas.checker_color1 = new_color
            
            # Update checkboard color 1 button to match
            if hasattr(main_window, 'checker_color1_btn'):
                main_window.checker_color1_btn.SetBackgroundColour(new_color)
            
            main_window.canvas.Refresh()
            print(f"DEBUG: 🎨 Background color changed to: {rgb_tuple}")
            print(f"DEBUG: 🏁 Checkboard color 1 synced to match background")

    dialog.Destroy()


def on_grid_color(main_window: "m_main_window.MainWindow", event):
    """Handle grid color selection."""

    current_color = wx.Colour(*main_window.canvas.grid_color) if hasattr(
        main_window, 'canvas') else wx.Colour(128, 128, 128)
    dialog = wx.ColourDialog(main_window)
    dialog.GetColourData().SetColour(current_color)

    if dialog.ShowModal() == wx.ID_OK:
        new_color = dialog.GetColourData().GetColour()
        main_window.grid_color_btn.SetBackgroundColour(new_color)
        if hasattr(main_window, 'canvas'):
            main_window.canvas.grid_color = (new_color.Red(), new_color.Green(),
                                        new_color.Blue())
            main_window.canvas.Refresh()
            print(
                f"DEBUG: 🎨 Grid color changed to: {new_color.GetAsString()}"
            )

    dialog.Destroy()


def on_set_custom_origin(main_window: "m_main_window.MainWindow", event):
    """Set the current center of screen as the custom origin."""

    if hasattr(main_window, 'canvas'):
        main_window.canvas.set_custom_origin()
        wx.MessageBox(
            "Current view center set as custom origin.\nReset View will now return to this position.",
                        "Custom Origin Set", wx.OK | wx.ICON_INFORMATION)


def on_set_custom_rotation(main_window: "m_main_window.MainWindow", event):
    """Set the current rotation as the custom default rotation."""

    if hasattr(main_window, 'canvas'):
        main_window.canvas.set_custom_default_rotation()
        current_rotation = main_window.canvas.custom_default_rotation
        wx.MessageBox(
            f"Current rotation ({current_rotation:.1f}°) set as default.\nReset View will now return to this rotation.",
                        "Custom Default Rotation Set", wx.OK | wx.ICON_INFORMATION)


def on_set_custom_zoom(main_window: "m_main_window.MainWindow", event):
    """Set the current zoom level as the custom default zoom."""

    if hasattr(main_window, 'canvas'):
        main_window.canvas.set_custom_default_zoom()
        current_zoom = main_window.canvas.custom_default_zoom
        wx.MessageBox(
            f"Current zoom ({current_zoom:.2f}x) set as default.\nReset View will now return to this zoom level.",
                        "Custom Default Zoom Set", wx.OK | wx.ICON_INFORMATION)


def on_set_current_view_as_default(main_window: "m_main_window.MainWindow", event):
    """Set the current view (center, rotation, and zoom) as the default view."""

    if hasattr(main_window, 'canvas'):
        # Set all three values at once
        main_window.canvas.set_custom_origin()
        main_window.canvas.set_custom_default_rotation()
        main_window.canvas.set_custom_default_zoom()
        
        # Get the values for the confirmation message
        center_x = main_window.canvas.custom_origin_x
        center_y = main_window.canvas.custom_origin_y
        rotation = main_window.canvas.custom_default_rotation
        zoom = main_window.canvas.custom_default_zoom
        
        wx.MessageBox(
            f"Current view set as default:\n"
            f"• Center: ({center_x:.1f}, {center_y:.1f})\n"
            f"• Rotation: {rotation:.1f}°\n"
            f"• Zoom: {zoom:.2f}x\n\n"
            f"Reset View will now return to this view.",
            "Current View Set as Default", wx.OK | wx.ICON_INFORMATION)
