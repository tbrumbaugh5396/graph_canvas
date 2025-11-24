"""
Control points and composite segment panel.
"""


import wx

import graph_canvas.presentation.desktop.gui.main_window as m_main_window


def count_edge_crossings(main_window: "m_main_window.MainWindow", edges):
    """Count the number of edge crossings in current layout."""

    count = 0
    for i, edge1 in enumerate(edges):
        for j, edge2 in enumerate(edges):
            if i >= j:
                continue
                
            # Get node positions
            src1 = main_window.current_graph.get_node(edge1.source_id)
            tgt1 = main_window.current_graph.get_node(edge1.target_id)
            src2 = main_window.current_graph.get_node(edge2.source_id)
            tgt2 = main_window.current_graph.get_node(edge2.target_id)
            
            if src1 and tgt1 and src2 and tgt2:
                if main_window.edges_intersect(src1.x, src1.y, tgt1.x, tgt1.y,
                                        src2.x, src2.y, tgt2.x, tgt2.y):
                    count += 1
    return count


def edges_intersect(main_window: "m_main_window.MainWindow", x1, y1, x2, y2, x3, y3, x4, y4):
    """Check if two line segments intersect."""

    def ccw(A_x, A_y, B_x, B_y, C_x, C_y):
        return (C_y - A_y) * (B_x - A_x) > (B_y - A_y) * (C_x - A_x)
    
    return (ccw(x1, y1, x3, y3, x4, y4) != ccw(x2, y2, x3, y3, x4, y4)
            and ccw(x1, y1, x2, y2, x3, y3) != ccw(x1, y1, x2, y2, x4, y4))


def on_composite_segment_selected(main_window: "m_main_window.MainWindow", event):
    """Handle selection of a composite curve segment to show its control points."""

    selected = event.GetIndex()
    main_window._select_composite_segment(selected)


def _select_composite_segment(main_window: "m_main_window.MainWindow", selected):
    """Core logic for selecting a composite segment (can be called directly)."""

    if not hasattr(main_window,
                    'current_curve_edge') or not main_window.current_curve_edge:
        return
    
    edge = main_window.current_curve_edge
    if not edge.is_composite or not hasattr(
            edge, 'curve_segments') or selected >= len(
                edge.curve_segments):
        return
    
    # Get the selected segment
    segment = edge.curve_segments[selected]
    
    # Temporarily populate the regular control points list with the segment's control points
    # Store reference to which segment we're editing
    main_window.current_composite_segment_index = selected
    main_window.canvas.current_composite_segment = selected  # Also update canvas for interaction
    print(
        f"DEBUG: 🔗 Selected composite segment {selected} of type {segment['type']} with {len(segment.get('control_points', []))} control points"
    )
    print(
        f"DEBUG: 🔗 Canvas current_composite_segment set to: {main_window.canvas.current_composite_segment}"
    )
    
    # Clear the regular control points list and populate with segment points
    if hasattr(main_window, 'bspline_list'):
        main_window.bspline_list.DeleteAllItems()
        
        # Add segment control points to the list
        for i, (x, y) in enumerate(segment.get("control_points", [])):
            index = main_window.bspline_list.InsertItem(i, str(i + 1))
            main_window.bspline_list.SetItem(index, 1, f"{x:.1f}")
            main_window.bspline_list.SetItem(index, 2, f"{y:.1f}")
    
    # Update canvas to show control points for this segment
    main_window.canvas.Refresh()
    
    print(
        f"DEBUG: 🔗 Selected composite segment {selected}: {segment['type']} with {len(segment.get('control_points', []))} control points"
    )


def on_composite_add_segment(main_window: "m_main_window.MainWindow", event):
    """Add a new composite curve segment."""

    if not hasattr(main_window,
                    'current_curve_edge') or not main_window.current_curve_edge:
        return
    
    edge = main_window.current_curve_edge
    
    # Dialog to choose curve type
    curve_types = [
        "straight", "curved", "bezier", "bspline", "cubic_spline", "nurbs",
        "polyline", "freeform"
    ]
    dialog = wx.SingleChoiceDialog(main_window, "Choose curve segment type:",
                                    "Add Curve Segment", curve_types)
    
    if dialog.ShowModal() == wx.ID_OK:
        curve_type = curve_types[dialog.GetSelection()]
        
        # Create default control points based on type
        if curve_type == "straight":
            control_points = []
        elif curve_type == "curved":
            control_points = [(25, -15)]
        elif curve_type in ["bezier", "cubic_spline"]:
            control_points = [(20, -20), (80, 20)]
        elif curve_type == "bspline":
            control_points = [(25, -15), (75, 15)]
        elif curve_type == "nurbs":
            control_points = [(15, -20), (35, 25), (65, -15), (85, 10)]
        elif curve_type == "polyline":
            control_points = [(25, -10), (50, 15), (75, -5)]
        elif curve_type == "freeform":
            # Start freeform drawing mode
            main_window.canvas.start_freeform_composite_segment(edge)
            dialog.Destroy()
            return
        
        # Add new segment
        new_segment = {
            "type": curve_type,
            "control_points": control_points,
            "weight": 1.0
        }
        edge.curve_segments.append(new_segment)
        main_window.update_composite_list()
        main_window.canvas.Refresh()
    
    dialog.Destroy()


def on_composite_edit_segment(main_window: "m_main_window.MainWindow", event):
    """Edit selected composite curve segment."""

    selected = main_window.composite_list.GetFirstSelected()
    if selected < 0:
        wx.MessageBox("Please select a segment to edit.", "No Selection",
                        wx.OK | wx.ICON_INFORMATION)
        return
    
    if not hasattr(main_window,
                    'current_curve_edge') or not main_window.current_curve_edge:
        return
    
    edge = main_window.current_curve_edge
    if selected >= len(edge.curve_segments):
        return
    
    segment = edge.curve_segments[selected]
    
    # Simple dialog for editing control points
    points_str = ", ".join(
        [f"({cp[0]:.1f},{cp[1]:.1f})" for cp in segment["control_points"]])
    dialog = wx.TextEntryDialog(
        main_window, f"Edit control points for {segment['type']}:",
        "Edit Segment", points_str)
    
    if dialog.ShowModal() == wx.ID_OK:
        try:
            # Parse the new control points
            points_text = dialog.GetValue()
            # Simple parsing: extract (x,y) pairs
            import re
            matches = re.findall(r'\(([-\d.]+),([-\d.]+)\)', points_text)
            new_points = [(float(x), float(y)) for x, y in matches]
            
            if new_points:
                segment["control_points"] = new_points
                main_window.update_composite_list()
                main_window.canvas.Refresh()
            else:
                wx.MessageBox("Invalid format. Use: (x1,y1), (x2,y2), ...",
                                "Error", wx.OK | wx.ICON_ERROR)
        except ValueError:
            wx.MessageBox("Invalid coordinates format.", "Error",
                            wx.OK | wx.ICON_ERROR)
    
    dialog.Destroy()


def on_composite_delete_segment(main_window: "m_main_window.MainWindow", event):
    """Delete selected composite curve segment."""

    selected = main_window.composite_list.GetFirstSelected()
    if selected < 0:
        wx.MessageBox("Please select a segment to delete.", "No Selection",
                        wx.OK | wx.ICON_INFORMATION)
        return
    
    if not hasattr(main_window,
                    'current_curve_edge') or not main_window.current_curve_edge:
        return
    
    edge = main_window.current_curve_edge
    if selected < len(edge.curve_segments):
        edge.curve_segments.pop(selected)
        main_window.update_composite_list()
        main_window.canvas.Refresh()


def update_composite_list(main_window: "m_main_window.MainWindow"):
    """Update the composite curve segments list."""

    if not hasattr(main_window, 'composite_list'):
        return
    
    main_window.composite_list.DeleteAllItems()
    
    if not hasattr(main_window,
                    'current_curve_edge') or not main_window.current_curve_edge:
        return
    
    edge = main_window.current_curve_edge
    for i, segment in enumerate(edge.curve_segments):
        index = main_window.composite_list.InsertItem(i, str(i + 1))
        main_window.composite_list.SetItem(index, 1, segment["type"])
        main_window.composite_list.SetItem(index, 2,
                                    str(len(segment["control_points"])))
        main_window.composite_list.SetItem(index, 3, f"{segment['weight']:.1f}")


def _auto_select_first_composite_segment(main_window: "m_main_window.MainWindow"):
    """Auto-select the first composite segment to show its control points."""

    if hasattr(
            main_window,
            'composite_list') and main_window.composite_list.GetItemCount() > 0:
        # Select the first item
        main_window.composite_list.Select(0)
        # Manually trigger the selection logic without creating a mock event
        main_window._select_composite_segment(0)
