"""
Event handlers for the sidebar.
"""


import wx
from functools import partial

import graph_canvas.presentation.desktop.gui.main_window as m_main_window

def _is_wx_object_alive(widget) -> bool:
    """Best-effort check if a wxPython widget's C++ object is still alive."""
    if widget is None:
        return False
    try:
        # Most widgets implement GetId; calling it will raise if underlying C++ is gone
        _ = widget.GetId()
        return True
    except Exception:
        return False

def _ensure_bspline_controls_alive(main_window: "m_main_window.MainWindow") -> None:
    """Recreate control-points UI if any critical widget was deleted by wx."""
    need_recreate = False
    if not getattr(main_window, 'bspline_controls_created', False):
        need_recreate = True
    else:
        critical_widgets = [
            getattr(main_window, 'bspline_box', None),
            getattr(main_window, 'bspline_list', None),
        ]
        for w in critical_widgets:
            if not _is_wx_object_alive(w):
                need_recreate = True
                break

    if need_recreate:
        try:
            create_bspline_controls(main_window)
        except Exception:
            # As a last resort, ignore – callers also wrap access in try/except
            pass


def on_expand_all_sections(main_window: "m_main_window.MainWindow", event):
    """Expand all collapsible sections."""

    for pane in main_window.collapsible_panes:
        if not pane.IsExpanded():
            pane.Expand()

    # Force layout update
    main_window.sidebar.FitInside()
    main_window.Layout()


def on_collapse_all_sections(main_window: "m_main_window.MainWindow", event):
    """Collapse all collapsible sections."""

    for pane in main_window.collapsible_panes:
        if pane.IsExpanded():
            pane.Collapse()
    # Force layout update
    main_window.sidebar.FitInside()
    main_window.Layout()


def on_individual_pane_changed(main_window: "m_main_window.MainWindow", event):
    """Handle individual collapsible pane expansion/collapse to match expand all behavior."""

    # Force the same layout updates that expand all does
    main_window.sidebar.FitInside()
    main_window.Layout()
    print("DEBUG: Individual pane changed - layout updated")


def on_center_x_changed(main_window: "m_main_window.MainWindow", event):
    """Handle center X coordinate change."""

    try:
        # Skip if this is a programmatic update
        if hasattr(main_window, 'suppress_view_option_events'
                   ) and main_window.suppress_view_option_events:
            return
        center_x = float(main_window.center_x_value.GetValue())
        # Update canvas pan position
        main_window.canvas.pan_x = center_x
        main_window.canvas.Refresh()
        print(f"DEBUG: Center X changed to {center_x}")
    except ValueError:
        print("DEBUG: Invalid center X value")


def on_center_y_changed(main_window: "m_main_window.MainWindow", event):
    """Handle center Y coordinate change."""

    try:
        # Skip if this is a programmatic update
        if hasattr(main_window, 'suppress_view_option_events'
                   ) and main_window.suppress_view_option_events:
            return
        center_y = float(main_window.center_y_value.GetValue())
        # Update canvas pan position
        main_window.canvas.pan_y = center_y
        main_window.canvas.Refresh()
        print(f"DEBUG: Center Y changed to {center_y}")
    except ValueError:
        print("DEBUG: Invalid center Y value")


def on_width_changed(main_window: "m_main_window.MainWindow", event):
    """Handle world width change."""
    try:
        # Skip if this is a programmatic update
        if hasattr(main_window, 'suppress_view_option_events') and main_window.suppress_view_option_events:
            return
        world_width = float(main_window.width_value.GetValue())
        # Calculate new zoom factor to achieve desired world width
        canvas_size = main_window.canvas.GetSize()
        new_zoom = canvas_size.GetWidth() / world_width
        main_window.canvas.zoom = new_zoom
        main_window.canvas.Refresh()
        print(f"DEBUG: World width changed to {world_width}, new zoom: {new_zoom:.3f}")
    except ValueError:
        print("DEBUG: Invalid world width value")


def on_height_changed(main_window: "m_main_window.MainWindow", event):
    """Handle world height change."""
    try:
        # Skip if this is a programmatic update
        if hasattr(main_window, 'suppress_view_option_events') and main_window.suppress_view_option_events:
            return
        world_height = float(main_window.height_value.GetValue())
        # Calculate new zoom factor to achieve desired world height
        canvas_size = main_window.canvas.GetSize()
        new_zoom = canvas_size.GetHeight() / world_height
        main_window.canvas.zoom = new_zoom
        main_window.canvas.Refresh()
        print(f"DEBUG: World height changed to {world_height}, new zoom: {new_zoom:.3f}")
    except ValueError:
        print("DEBUG: Invalid world height value")


def on_default_node_properties(main_window: "m_main_window.MainWindow", event):
    """Edit default node properties."""

    # Create a temporary node with default properties
    from graph_canvas.presentation.desktop.models.node import Node
    default_node = Node(0, 0, "Default Node")

    # Open properties dialog
    from graph_canvas.presentation.desktop.gui.dialogs import NodePropertiesDialog
    dialog = NodePropertiesDialog(main_window, default_node)
    main_window.apply_theme_to_dialog(dialog)
    if dialog.ShowModal() == wx.ID_OK:
        # Store default properties (you could save these to graph metadata or config)
        print("DEBUG: Default node properties updated")
        # TODO: Apply these defaults to new nodes
    dialog.Destroy()


def on_default_edge_properties(main_window: "m_main_window.MainWindow", event):
    """Edit default edge properties."""

    # Create a temporary edge with default properties
    from graph_canvas.presentation.desktop.models.edge import Edge
    default_edge = Edge("temp_source", "temp_target", "Default Edge")

    # Open properties dialog
    from graph_canvas.presentation.desktop.gui.dialogs import EdgePropertiesDialog
    dialog = EdgePropertiesDialog(main_window, default_edge)
    main_window.apply_theme_to_dialog(dialog)
    if dialog.ShowModal() == wx.ID_OK:
        # Store default properties (you could save these to graph metadata or config)
        print("DEBUG: Default edge properties updated")
        # TODO: Apply these defaults to new edges
    dialog.Destroy()


def on_bspline_add_control_point(main_window: "m_main_window.MainWindow", event):
    """Add a new curve control point via dialog (works for all curve types and composite segments)."""

    print(f"DEBUG: 🔧🔧🔧 *** ADD CONTROL POINT BUTTON CLICKED *** 🔧🔧🔧")
    print(f"DEBUG: 🔧 Event: {event}")
    print(f"DEBUG: 🔧 Event type: {type(event)}")
    current_edge = getattr(main_window, 'current_curve_edge', None) or getattr(
        main_window, 'current_bspline_edge', None)
    print(
        f"DEBUG: 🔧 on_bspline_add_control_point called, current_edge = {current_edge}"
    )
    if not current_edge:
        print(f"DEBUG: 🔧 No current edge found!")
        return

    # Check if we're editing a composite segment
    if hasattr(main_window, 'current_composite_segment_index'
                ) and current_edge.is_composite:
        segment_index = main_window.current_composite_segment_index
        segment = current_edge.curve_segments[segment_index]
        curve_name = f"{segment['type'].title()} Segment"
    else:
        # Set the canvas to work with our current edge
        print(
            f"DEBUG: 🔧 Setting canvas.bspline_editing_edge to {current_edge.id}"
        )
        main_window.canvas.bspline_editing_edge = current_edge
        # Get curve type for dialog title
        curve_type = getattr(main_window, 'current_curve_type', 'curve')
        curve_name = "Bézier" if curve_type == "bezier" else curve_type.title(
        )
        print(
            f"DEBUG: 🔧 Current edge has {len(current_edge.control_points) if hasattr(current_edge, 'control_points') else 'NO'} control points"
        )

    # Simple coordinate input dialog
    dialog = wx.TextEntryDialog(main_window, "Enter coordinates (x,y):",
                                f"Add {curve_name} Control Point", "0,0")
    print(f"DEBUG: 🔧 Showing dialog for coordinates")
    if dialog.ShowModal() == wx.ID_OK:
        print(f"DEBUG: 🔧 Dialog OK pressed")
        try:
            coords_text = dialog.GetValue()
            print(f"DEBUG: 🔧 User entered: '{coords_text}'")
            coords = coords_text.split(',')
            print(f"DEBUG: 🔧 Split coords: {coords}")
            if len(coords) == 2:
                x, y = float(coords[0].strip()), float(coords[1].strip())
                print(f"DEBUG: 🔧 Parsed coordinates: x={x}, y={y}")

                if hasattr(main_window, 'current_composite_segment_index'
                            ) and current_edge.is_composite:
                    # Add to composite segment
                    segment = current_edge.curve_segments[
                        main_window.current_composite_segment_index]
                    if "control_points" not in segment:
                        segment["control_points"] = []
                    segment["control_points"].append((x, y))
                    # Update both the segment list and control points list
                    main_window.update_composite_list()
                    main_window._select_composite_segment(
                    main_window.current_composite_segment_index)
                else:
                    # Add to regular edge
                    print(
                        f"DEBUG: 🔧 Calling canvas.add_curve_control_point({x}, {y})"
                    )
                    main_window.canvas.add_curve_control_point(x, y)
                    print(f"DEBUG: 🔧 After add_curve_control_point call")
                    main_window.update_curve_list()

                main_window.canvas.Refresh()
                print(
                    f"DEBUG: 🔧 Canvas refreshed after adding control point"
                )
            else:
                print(
                    f"DEBUG: 🔧 ERROR: Wrong number of coordinates. Expected 2, got {len(coords)}"
                )
                wx.MessageBox("Invalid coordinates format. Use: x,y",
                                "Error", wx.OK | wx.ICON_ERROR)
        except ValueError as e:
            print(f"DEBUG: 🔧 ERROR: ValueError parsing coordinates: {e}")
            wx.MessageBox("Invalid coordinates format. Use: x,y", "Error",
                            wx.OK | wx.ICON_ERROR)
    else:
        print(f"DEBUG: 🔧 Dialog cancelled by user")
    dialog.Destroy()
    print(f"DEBUG: 🔧 Dialog destroyed, method complete")


def on_bspline_edit_control_point(main_window: "m_main_window.MainWindow", event):
    """Edit selected control point (works for both regular curves and composite segments)."""

    selected = main_window.bspline_list.GetFirstSelected()
    if selected < 0:
        wx.MessageBox("Please select a control point to edit.",
                        "No Selection", wx.OK | wx.ICON_WARNING)
        return

    current_edge = getattr(main_window, 'current_curve_edge', None) or getattr(
        main_window, 'current_bspline_edge', None)
    if not current_edge:
        return

    # Check if we're editing a composite segment
    if hasattr(main_window, 'current_composite_segment_index'
                ) and current_edge.is_composite:
        segment = current_edge.curve_segments[
            main_window.current_composite_segment_index]
        if selected >= len(segment["control_points"]):
            return

        current_x, current_y = segment["control_points"][selected]
        dialog = wx.TextEntryDialog(main_window, "Enter coordinates (x,y):",
                                    "Edit Segment Control Point",
                                    f"{current_x:.1f},{current_y:.1f}")
        if dialog.ShowModal() == wx.ID_OK:
            try:
                coords = dialog.GetValue().split(',')
                if len(coords) == 2:
                    x, y = float(coords[0].strip()), float(
                        coords[1].strip())
                    segment["control_points"][selected] = (x, y)
                    # Update both the segment list and control points list
                    main_window.update_composite_list()
                    main_window._select_composite_segment(
                    main_window.current_composite_segment_index)
                    main_window.canvas.Refresh()
            except ValueError:
                wx.MessageBox("Invalid coordinates format. Use: x,y",
                                "Error", wx.OK | wx.ICON_ERROR)
    else:
        # Regular edge control point
        edge = current_edge
        if selected >= len(edge.control_points):
            return

        current_x, current_y = edge.control_points[selected]
        dialog = wx.TextEntryDialog(main_window, "Enter coordinates (x,y):",
                                    "Edit Control Point",
                                    f"{current_x:.1f},{current_y:.1f}")
        if dialog.ShowModal() == wx.ID_OK:
            try:
                coords = dialog.GetValue().split(',')
                if len(coords) == 2:
                    x, y = float(coords[0].strip()), float(
                        coords[1].strip())
                    edge.control_points[selected] = (x, y)
                    edge.custom_position = True
                    main_window.update_curve_list()
                    main_window.canvas.Refresh()
            except ValueError:
                wx.MessageBox("Invalid coordinates format. Use: x,y",
                                "Error", wx.OK | wx.ICON_ERROR)
    dialog.Destroy()


def on_bspline_delete_control_point(main_window: "m_main_window.MainWindow", event):
    """Delete selected control point (works for both regular curves and composite segments)."""

    selected = main_window.bspline_list.GetFirstSelected()
    if selected < 0:
        wx.MessageBox("Please select a control point to delete.",
                        "No Selection", wx.OK | wx.ICON_WARNING)
        return

    current_edge = getattr(main_window, 'current_curve_edge', None) or getattr(
        main_window, 'current_bspline_edge', None)
    if not current_edge:
        return

    # Check if we're deleting from a composite segment
    if hasattr(main_window, 'current_composite_segment_index'
                ) and current_edge.is_composite:
        segment = current_edge.curve_segments[
            main_window.current_composite_segment_index]
        if selected >= len(segment["control_points"]):
            return

        # Delete the control point from the segment
        del segment["control_points"][selected]
        # Update both the segment list and control points list
        main_window.update_composite_list()
        main_window._select_composite_segment(
        main_window.current_composite_segment_index)
        main_window.canvas.Refresh()
    else:
        # Regular edge control point - use the existing canvas method
        if hasattr(main_window,
                    'current_bspline_edge') and main_window.current_bspline_edge:
            main_window.canvas.bspline_editing_edge = main_window.current_bspline_edge

        main_window.canvas.delete_bspline_control_point(selected)
        main_window.update_curve_list()
        main_window.canvas.Refresh()


def on_bspline_move_up(main_window: "m_main_window.MainWindow", event):
    """Move selected control point up in the list."""

    selected = main_window.bspline_list.GetFirstSelected()
    if selected <= 0:
        return

    # Set the canvas to work with our current edge
    if hasattr(main_window, 'current_bspline_edge') and main_window.current_bspline_edge:
        main_window.canvas.bspline_editing_edge = main_window.current_bspline_edge

    main_window.canvas.move_bspline_control_point(selected, selected - 1)
    main_window.update_bspline_list()
    # Maintain selection
    main_window.bspline_list.Select(selected - 1)
    main_window.canvas.Refresh()


def on_bspline_move_down(main_window: "m_main_window.MainWindow", event):
    """Move selected control point down in the list."""

    selected = main_window.bspline_list.GetFirstSelected()
    if not hasattr(
            main_window, 'current_bspline_edge') or not main_window.current_bspline_edge:
        return

    if selected < 0 or selected >= len(
            main_window.current_bspline_edge.control_points) - 1:
        return

    # Set the canvas to work with our current edge
    main_window.canvas.bspline_editing_edge = main_window.current_bspline_edge

    main_window.canvas.move_bspline_control_point(selected, selected + 1)
    main_window.update_bspline_list()
    # Maintain selection
    main_window.bspline_list.Select(selected + 1)
    main_window.canvas.Refresh()


def create_bspline_controls(main_window: "m_main_window.MainWindow"):
    """Create B-spline control point management controls on-demand."""

    print(f"DEBUG: 🔧 create_bspline_controls() called")
    if getattr(main_window, 'bspline_controls_created', False):
        # Only skip if the underlying widgets are still alive; otherwise, rebuild
        bspline_box_alive = _is_wx_object_alive(getattr(main_window, 'bspline_box', None))
        bspline_list_alive = _is_wx_object_alive(getattr(main_window, 'bspline_list', None))
        if bspline_box_alive and bspline_list_alive:
            print(f"DEBUG: 🔧 Controls already created and alive, returning early")
            return
        else:
            print(f"DEBUG: 🔧 Controls flagged created but widgets dead; rebuilding controls")
            # Best effort cleanup of old references
            try:
                if hasattr(main_window, 'bspline_box') and main_window.bspline_box:
                    main_window.bspline_box.Destroy()
            except Exception:
                pass
            # Mark as not created so we can rebuild below
            main_window.bspline_controls_created = False

    # Control Points panel should live inside the Property Panel (below Graph Properties)
    prop_panel = getattr(main_window, 'property_panel_pane', None)
    parent_window = prop_panel.GetPane() if prop_panel else main_window.sidebar
    # Prefer explicit sizer exposed on main_window
    preferred_sizer = getattr(main_window, 'property_panel_sizer', None)
    target_sizer = None

    # Use the always-present Control Points pane created in gui/sidebar.py
    if not hasattr(main_window, 'control_points_pane'):
        print("DEBUG: ❗ control_points_pane not found; expected to be created in gui/sidebar.py")
        return
    control_points_window = main_window.control_points_pane.GetPane()

    main_window.bspline_box = wx.StaticBox(control_points_window,
                                    label="B-spline Control Points")
    main_window.bspline_box.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
    main_window.bspline_sizer = wx.StaticBoxSizer(main_window.bspline_box, wx.VERTICAL)

    # Control points list
    main_window.bspline_list = wx.ListCtrl(control_points_window,
                                    style=wx.LC_REPORT | wx.LC_SINGLE_SEL,
                                    size=(220, 120))
    try:
        main_window.bspline_list.SetMinSize((250, 120))
    except Exception:
        pass
    main_window.bspline_list.AppendColumn("Index", width=50)
    main_window.bspline_list.AppendColumn("X", width=70)
    main_window.bspline_list.AppendColumn("Y", width=70)
    main_window.bspline_sizer.Add(main_window.bspline_list, 1, wx.EXPAND | wx.ALL, 5)

    # Control buttons
    bspline_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

    main_window.bspline_add_btn = wx.Button(control_points_window,
                                        label="Add",
                                        size=(50, 25))
    main_window.bspline_add_btn.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.bspline_add_btn.SetBackgroundColour(wx.Colour(255, 255, 255))
    main_window.bspline_add_btn.Refresh()
    print(f"DEBUG: 🔧 Created bspline_add_btn button")
    print(f"DEBUG: 🔧 Button ID: {main_window.bspline_add_btn.GetId()}")
    print(f"DEBUG: 🔧 Button label: '{main_window.bspline_add_btn.GetLabel()}'")
    main_window.bspline_add_btn.Bind(wx.EVT_BUTTON,
                                partial(on_bspline_add_control_point, main_window))
    print(
        f"DEBUG: 🔧 Bound bspline_add_btn to on_bspline_add_control_point")

    # Test binding by trying to trigger a test event
    def test_handler(event):
        print("DEBUG: 🔧 TEST: Button event handler is working!")

    # Don't actually bind this, just log that we could
    bspline_btn_sizer.Add(main_window.bspline_add_btn, 1, wx.ALL, 2)

    main_window.bspline_edit_btn = wx.Button(control_points_window,
                                        label="Edit",
                                        size=(50, 25))
    main_window.bspline_edit_btn.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.bspline_edit_btn.SetBackgroundColour(wx.Colour(255, 255, 255))
    main_window.bspline_edit_btn.Refresh()
    main_window.bspline_edit_btn.Bind(wx.EVT_BUTTON,
                                partial(on_bspline_edit_control_point, main_window))
    bspline_btn_sizer.Add(main_window.bspline_edit_btn, 1, wx.ALL, 2)

    main_window.bspline_delete_btn = wx.Button(control_points_window,
                                        label="Delete",
                                        size=(50, 25))
    main_window.bspline_delete_btn.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.bspline_delete_btn.SetBackgroundColour(wx.Colour(255, 255, 255))
    main_window.bspline_delete_btn.Refresh()
    main_window.bspline_delete_btn.Bind(wx.EVT_BUTTON,
                                    partial(on_bspline_delete_control_point, main_window))
    bspline_btn_sizer.Add(main_window.bspline_delete_btn, 0, wx.ALL, 2)

    main_window.bspline_sizer.Add(bspline_btn_sizer, 1, wx.ALIGN_CENTER | wx.ALL,
                            2)

    # Reorder buttons
    reorder_sizer = wx.BoxSizer(wx.HORIZONTAL)

    main_window.bspline_up_btn = wx.Button(control_points_window, label="↑", size=(30, 25))
    main_window.bspline_up_btn.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.bspline_up_btn.SetBackgroundColour(wx.Colour(255, 255, 255))
    main_window.bspline_up_btn.Refresh()
    main_window.bspline_up_btn.Bind(wx.EVT_BUTTON, partial(on_bspline_move_up, main_window))
    reorder_sizer.Add(main_window.bspline_up_btn, 1, wx.ALL, 2)

    main_window.bspline_down_btn = wx.Button(control_points_window,
                                        label="↓",
                                        size=(30, 25))
    main_window.bspline_down_btn.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.bspline_down_btn.SetBackgroundColour(wx.Colour(255, 255, 255))
    main_window.bspline_down_btn.Refresh()
    main_window.bspline_down_btn.Bind(wx.EVT_BUTTON, partial(on_bspline_move_down, main_window))
    reorder_sizer.Add(main_window.bspline_down_btn, 1, wx.ALL, 2)

    # Add click mode toggle
    main_window.bspline_click_mode_btn = wx.Button(control_points_window,
                                            label="Click to Add",
                                            size=(80, 25))
    main_window.bspline_click_mode_btn.SetForegroundColour(wx.Colour(
        0, 0, 0))  # Black text
    main_window.bspline_click_mode_btn.SetBackgroundColour(
        wx.Colour(255, 255, 255))  # White background
    main_window.bspline_click_mode_btn.Refresh()
    print(f"DEBUG: 🔧 Created bspline_click_mode_btn button")
    print(
        f"DEBUG: 🔧 Click button ID: {main_window.bspline_click_mode_btn.GetId()}")
    print(
        f"DEBUG: 🔧 Click button label: '{main_window.bspline_click_mode_btn.GetLabel()}'"
    )
    main_window.bspline_click_mode_btn.Bind(wx.EVT_BUTTON,
                                        partial(on_bspline_toggle_click_mode, main_window))
    print(
        f"DEBUG: 🔧 Bound bspline_click_mode_btn to on_bspline_toggle_click_mode"
    )
    reorder_sizer.Add(main_window.bspline_click_mode_btn, 1, wx.ALL, 2)

    main_window.bspline_sizer.Add(reorder_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 2)

    # Source and Target info (read-only)
    info_sizer = wx.BoxSizer(wx.VERTICAL)
    main_window.bspline_source_label = wx.StaticText(control_points_window,
                                                label="Source: ")
    main_window.bspline_source_label.SetForegroundColour(wx.Colour(0, 100, 0))
    info_sizer.Add(main_window.bspline_source_label, 0, wx.ALL, 2)

    main_window.bspline_target_label = wx.StaticText(control_points_window,
                                                label="Target: ")
    main_window.bspline_target_label.SetForegroundColour(wx.Colour(100, 0, 0))
    info_sizer.Add(main_window.bspline_target_label, 0, wx.ALL, 2)

    main_window.bspline_sizer.Add(info_sizer, 0, wx.EXPAND | wx.ALL, 5)

    # Arrow position controls
    arrow_sizer = wx.BoxSizer(wx.VERTICAL)
    arrow_label = wx.StaticText(control_points_window, label="Arrow Position:")
    arrow_label.SetForegroundColour(wx.Colour(0, 0, 0))
    arrow_sizer.Add(arrow_label, 0, wx.ALL, 2)

    # Arrow position slider (0.0 to 1.0)
    main_window.arrow_position_slider = wx.Slider(control_points_window,
                                            value=100,
                                            minValue=0,
                                            maxValue=100,
                                            style=wx.SL_HORIZONTAL
                                            | wx.SL_LABELS,
                                            size=(200, -1))
    try:
        import graph_canvas.presentation.desktop.event_handlers.graph_canvas_event_handler as m_graph_canvas_event_handler
        main_window.arrow_position_slider.Bind(wx.EVT_SLIDER, partial(m_graph_canvas_event_handler.on_arrow_position_changed, main_window))
    except Exception:
        # Fallback: no-op bind to avoid AttributeError
        main_window.arrow_position_slider.Bind(wx.EVT_SLIDER, lambda evt: None)
    arrow_sizer.Add(main_window.arrow_position_slider, 0, wx.EXPAND | wx.ALL, 2)

    # Arrow position text input for precise control
    arrow_input_sizer = wx.BoxSizer(wx.HORIZONTAL)
    arrow_input_label = wx.StaticText(control_points_window, label="Position:")
    arrow_input_label.SetForegroundColour(wx.Colour(0, 0, 0))
    arrow_input_sizer.Add(arrow_input_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 2)

    main_window.arrow_position_text = wx.TextCtrl(control_points_window, value="1.0", size=(60, -1))
    try:
        import graph_canvas.presentation.desktop.event_handlers.graph_canvas_event_handler as m_graph_canvas_event_handler
        main_window.arrow_position_text.Bind(wx.EVT_TEXT, partial(m_graph_canvas_event_handler.on_arrow_position_text_changed, main_window))
    except Exception:
        main_window.arrow_position_text.Bind(wx.EVT_TEXT, lambda evt: None)
    arrow_input_sizer.Add(main_window.arrow_position_text, 0, wx.ALL, 2)

    arrow_sizer.Add(arrow_input_sizer, 0, wx.EXPAND | wx.ALL, 2)

    main_window.bspline_sizer.Add(arrow_sizer, 0, wx.EXPAND | wx.ALL, 5)
    try:
        # Ensure a reasonable minimum so contents are visible even when pane is newly expanded
        main_window.bspline_sizer.SetMinSize((250, 220))
    except Exception:
        pass

    # Use the always-present Composite pane created in gui/sidebar.py
    composite_window = main_window.composite_pane.GetPane()
    composite_sizer = wx.BoxSizer(wx.VERTICAL)
    main_window.composite_list = wx.ListCtrl(composite_window,
                                        style=wx.LC_REPORT | wx.LC_SINGLE_SEL,
                                        size=(250, 100))
    main_window.composite_list.AppendColumn("#", width=30)
    main_window.composite_list.AppendColumn("Type", width=80)
    main_window.composite_list.AppendColumn("Control Points", width=90)
    main_window.composite_list.AppendColumn("Weight", width=50)
    try:
        import graph_canvas.presentation.desktop.gui.control_points_and_composite_segment_panel as m_cp_panel
        main_window._select_composite_segment = partial(m_cp_panel._select_composite_segment, main_window)
        main_window.on_composite_segment_selected = partial(m_cp_panel.on_composite_segment_selected, main_window)
        main_window.composite_list.Bind(wx.EVT_LIST_ITEM_SELECTED, main_window.on_composite_segment_selected)
    except Exception:
        # Fallback: no-op
        main_window.composite_list.Bind(wx.EVT_LIST_ITEM_SELECTED, lambda evt: None)
    composite_sizer.Add(main_window.composite_list, 0, wx.EXPAND | wx.ALL, 2)
    composite_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
    main_window.composite_add_btn = wx.Button(composite_window, label="Add Segment", size=(100, 28))
    main_window.composite_add_btn.SetForegroundColour(wx.Colour(255, 255, 255))
    main_window.composite_add_btn.SetBackgroundColour(wx.Colour(0, 0, 0))
    main_window.composite_add_btn.Refresh()
    try:
        import graph_canvas.presentation.desktop.gui.control_points_and_composite_segment_panel as m_cp_panel
        main_window.on_composite_add_segment = partial(m_cp_panel.on_composite_add_segment, main_window)
        main_window.composite_add_btn.Bind(wx.EVT_BUTTON, main_window.on_composite_add_segment)
    except Exception:
        main_window.composite_add_btn.Bind(wx.EVT_BUTTON, lambda evt: None)
    composite_btn_sizer.Add(main_window.composite_add_btn, 0, wx.ALL, 2)
    main_window.composite_edit_btn = wx.Button(composite_window, label="Edit", size=(70, 28))
    main_window.composite_edit_btn.SetForegroundColour(wx.Colour(255, 255, 255))
    main_window.composite_edit_btn.SetBackgroundColour(wx.Colour(0, 0, 0))
    main_window.composite_edit_btn.Refresh()
    try:
        import graph_canvas.presentation.desktop.gui.control_points_and_composite_segment_panel as m_cp_panel
        main_window.on_composite_edit_segment = partial(m_cp_panel.on_composite_edit_segment, main_window)
        main_window.composite_edit_btn.Bind(wx.EVT_BUTTON, main_window.on_composite_edit_segment)
    except Exception:
        main_window.composite_edit_btn.Bind(wx.EVT_BUTTON, lambda evt: None)
    composite_btn_sizer.Add(main_window.composite_edit_btn, 0, wx.ALL, 2)
    main_window.composite_delete_btn = wx.Button(composite_window, label="Delete", size=(70, 28))
    main_window.composite_delete_btn.SetForegroundColour(wx.Colour(255, 255, 255))
    main_window.composite_delete_btn.SetBackgroundColour(wx.Colour(0, 0, 0))
    main_window.composite_delete_btn.Refresh()
    try:
        import graph_canvas.presentation.desktop.gui.control_points_and_composite_segment_panel as m_cp_panel
        main_window.on_composite_delete_segment = partial(m_cp_panel.on_composite_delete_segment, main_window)
        main_window.composite_delete_btn.Bind(wx.EVT_BUTTON, main_window.on_composite_delete_segment)
    except Exception:
        main_window.composite_delete_btn.Bind(wx.EVT_BUTTON, lambda evt: None)
    composite_btn_sizer.Add(main_window.composite_delete_btn, 0, wx.ALL, 2)
    composite_sizer.Add(composite_btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 2)
    try:
        comp_container = composite_window.GetSizer()
        if comp_container is not None:
            comp_container.Add(composite_sizer, 0, wx.EXPAND | wx.ALL, 2)
        else:
            composite_window.SetSizer(composite_sizer)
        composite_window.Layout()
        main_window.composite_pane.Layout()
    except Exception:
        composite_window.SetSizer(composite_sizer)
    main_window.composite_sizer = composite_sizer

    # Attach built sizers to their panes (layout happens in gui/sidebar.py)
    try:
        cp_container = control_points_window.GetSizer()
        if cp_container is not None:
            cp_container.Add(main_window.bspline_sizer, 1, wx.EXPAND | wx.ALL, 2)
        else:
            control_points_window.SetSizer(main_window.bspline_sizer)
        main_window.bspline_attached_to_cp_pane = True
        control_points_window.Layout()
        main_window.control_points_pane.Layout()
    except Exception:
        pass
    try:
        main_window.sidebar.Layout()
        main_window.sidebar.FitInside()
        main_window.Layout()
    except Exception:
        pass
    if not main_window.bspline_added_to_sizer:
        # Mark added; panes were added above
        main_window.bspline_added_to_sizer = True

    main_window.bspline_controls_created = True
    print(f"DEBUG: 🔧 create_bspline_controls() completed successfully")

    # Ensure final ordering: place panes right after the Property Panel once it exists
    try:
        wx.CallAfter(partial(_reposition_curve_panes_below_property_panel, main_window))
    except Exception:
        pass


def show_curve_controls(main_window: "m_main_window.MainWindow", edge, curve_type):
    """Show and populate curve control point management controls for both B-spline and Bézier curves."""

    print(
        f"DEBUG: 🎛️ show_curve_controls called for edge {edge.id}, type: {curve_type}"
    )
    print(
        f"DEBUG: 🎛️ Edge has {len(edge.control_points) if hasattr(edge, 'control_points') else 'NO'} control points"
    )

    main_window.current_curve_edge = edge
    main_window.current_curve_type = curve_type

    # For now, use the existing B-spline controls for both curve types
    # We'll update the labels to be more generic
    main_window.current_bspline_edge = edge  # Keep compatibility

    # CRITICAL: Set the canvas editing edge so add control point works
    main_window.canvas.bspline_editing_edge = edge
    print(
        f"DEBUG: 🎛️ Set current_curve_edge and current_bspline_edge to {edge.id}"
    )

    # Create controls if they don't exist yet or if previous widgets were destroyed by wx
    _ensure_bspline_controls_alive(main_window)
    
    # Ensure the Control Points pane contains our control-points UI
    try:
        control_points_window = main_window.control_points_pane.GetPane()
        cp_container = control_points_window.GetSizer()
        if cp_container is None:
            cp_container = wx.BoxSizer(wx.VERTICAL)
            control_points_window.SetSizer(cp_container)
        # Clear existing and insert our sizer so it becomes visible reliably
        try:
            cp_container.Detach(main_window.bspline_sizer)
        except Exception:
            pass
        cp_container.Clear(False)
        if _is_wx_object_alive(main_window.bspline_sizer.GetStaticBox() if hasattr(main_window.bspline_sizer, 'GetStaticBox') else None):
            cp_container.Add(main_window.bspline_sizer, 1, wx.EXPAND | wx.ALL, 2)
        else:
            _ensure_bspline_controls_alive(main_window)
            cp_container.Add(main_window.bspline_sizer, 1, wx.EXPAND | wx.ALL, 2)
        main_window.bspline_attached_to_cp_pane = True
        # Make sure children are shown and laid out
        try:
            if hasattr(main_window, 'bspline_list'):
                main_window.bspline_list.Show(True)
            if hasattr(main_window, 'bspline_add_btn'):
                main_window.bspline_add_btn.Show(True)
            if hasattr(main_window, 'bspline_edit_btn'):
                main_window.bspline_edit_btn.Show(True)
            if hasattr(main_window, 'bspline_delete_btn'):
                main_window.bspline_delete_btn.Show(True)
        except Exception:
            pass
        try:
            main_window.bspline_sizer.Layout()
        except Exception:
            pass
        control_points_window.Layout()
        main_window.control_points_pane.Collapse(False)
        main_window.control_points_pane.Layout()
    except Exception:
        pass

    # Update the static box label to reflect curve type (guard against deleted C++ widget)
    try:
        curve_labels = {
            "straight": "Straight Line (No Control Points)",
            "curved": "Curved/Arc Control Point",
            "bspline": "B-Spline Control Points",
            "bezier": "Bézier Control Points",
            "cubic_spline": "Cubic Spline Control Points",
            "nurbs": "NURBS Control Points",
            "polyline": "Polyline Control Points",
            "composite": "Composite Curve Segments"
        }
        if hasattr(main_window, 'bspline_box') and _is_wx_object_alive(main_window.bspline_box):
            main_window.bspline_box.SetLabel(curve_labels.get(curve_type, "Curve Control Points"))
    except Exception:
        # Recreate controls if the underlying wx objects were deleted
        _ensure_bspline_controls_alive(main_window)

    # Ensure edge has the correct rendering type and control points
    previous_type = edge.rendering_type if edge.rendering_type else main_window.canvas.edge_rendering_type
    edge.rendering_type = curve_type

    # Ensure control points are properly initialized for the curve type
    source_node = main_window.current_graph.get_node(edge.source_id)
    target_node = main_window.current_graph.get_node(edge.target_id)

    # Always check if control points match expected count for the curve type
    # Most curves now start with 0 control points except arcs (curved) and main_window-loops
    expected_counts = {
        "straight": 0,
        "curved": 1,  # Arcs keep 1 control point
        "bezier": 0,  # Start with 0, user can add manually
        "cubic_spline": 0,  # Start with 0, user can add manually
        "nurbs": 0,  # Start with 0, user can add manually
        "bspline": 0,  # Start with 0, user can add manually
        "polyline": 0,  # Start with 0, user can add manually
        "composite": 0  # Composite uses segments instead
    }

    # Check if this is a main_window-loop
    is_main_window_loop = source_node and target_node and source_node.id == target_node.id

    # Self-loops have different expected counts
    if is_main_window_loop:
        main_window_loop_expected_counts = {
            "straight": 1,
        "curved": 1,
        "bezier": 2,
        "cubic_spline": 3,
        "nurbs": 4,
        "bspline": 2,
        "polyline": 3,
            "composite": 0
        }
        expected_count = main_window_loop_expected_counts.get(curve_type, 0)
    else:
        expected_count = expected_counts.get(curve_type, 0)

    current_count = len(edge.control_points) if hasattr(
            edge, 'control_points') else 0

    # Only reinitialize control points if:
    # 1. Curve type actually changed, OR
    # 2. Control points attribute is missing, OR
    # 3. It's a main_window-loop that needs specific control points, OR
    # 4. It's a curve type that requires specific control points (curved/arc)
    needs_reinit = ((previous_type != curve_type)
                    or (not hasattr(edge, 'control_points'))
                    or (is_main_window_loop and current_count != expected_count)
                    or (curve_type == "curved"
                        and current_count != expected_count))

    if needs_reinit:
        print(
            f"DEBUG: 🔄 Reinitializing control points for edge {edge.id}: {previous_type} -> {curve_type} (expected: {expected_count}, current: {current_count})"
        )
        print(
            f"DEBUG: 🔄 Reason: previous_type({previous_type}) != curve_type({curve_type}): {previous_type != curve_type}, missing control_points: {not hasattr(edge, 'control_points')}, is_main_window_loop: {is_main_window_loop}"
        )
        main_window.canvas.initialize_control_points(edge, source_node,
                                                target_node)
        print(
            f"DEBUG: 🎛️ After initialization: {len(edge.control_points)} control points"
        )
    else:
        print(
            f"DEBUG: 🔄 PRESERVING existing {current_count} control points for {curve_type} edge {edge.id}"
        )

    # Ensure the collapsible pane is expanded; insertion handled at creation time
    if hasattr(main_window, 'control_points_pane'):
        try:
            main_window.control_points_pane.Collapse(False)
        except Exception:
            pass

    print(
        f"DEBUG: 🎛️ About to show bspline_box control panel in show_curve_controls"
    )
    try:
        if hasattr(main_window, 'bspline_box') and _is_wx_object_alive(main_window.bspline_box):
            main_window.bspline_box.Show(True)
        else:
            _ensure_bspline_controls_alive(main_window)
    except Exception:
        _ensure_bspline_controls_alive(main_window)
    try:
        print(f"DEBUG: 🧩 Attaching control-points UI into Control Points pane")
        print(f"DEBUG: 🧩 bspline_list shown? {main_window.bspline_list.IsShown()}")
    except Exception:
        pass
    # Ensure controls are visible inside the Control Points pane
    try:
        main_window.control_points_pane.Collapse(False)
    except Exception:
        pass
    if hasattr(main_window, 'control_points_pane'):
        try:
            main_window.control_points_pane.Collapse(False)
        except Exception:
            pass
    print(f"DEBUG: 🎛️ bspline_box.Show(True) called successfully")

    # Check if buttons exist and are visible after showing the box
    if hasattr(main_window, 'bspline_add_btn'):
        print(
            f"DEBUG: 🎛️ bspline_add_btn exists and is enabled: {main_window.bspline_add_btn.IsEnabled()}"
        )
        print(
            f"DEBUG: 🎛️ bspline_add_btn is shown: {main_window.bspline_add_btn.IsShown()}"
        )
    else:
        print(f"DEBUG: 🎛️ ERROR: bspline_add_btn does NOT exist!")

    if hasattr(main_window, 'bspline_click_mode_btn'):
        print(
            f"DEBUG: 🎛️ bspline_click_mode_btn exists and is enabled: {main_window.bspline_click_mode_btn.IsEnabled()}"
        )
        print(
            f"DEBUG: 🎛️ bspline_click_mode_btn is shown: {main_window.bspline_click_mode_btn.IsShown()}"
        )
    else:
        print(f"DEBUG: 🎛️ ERROR: bspline_click_mode_btn does NOT exist!")

    # Update source/target labels
    source_node = main_window.current_graph.get_node(edge.source_id)
    target_node = main_window.current_graph.get_node(edge.target_id)

    if source_node:
        main_window.bspline_source_label.SetLabel(
            f"Source: ({source_node.x:.1f}, {source_node.y:.1f}) - {source_node.text}"
        )
    if target_node:
        main_window.bspline_target_label.SetLabel(
            f"Target: ({target_node.x:.1f}, {target_node.y:.1f}) - {target_node.text}"
        )

    # Populate control points list
    main_window.update_curve_list()

    # Always show control point management UI so users can add points even when currently 0
    show_control_buttons = True
    print(
        f"DEBUG: 🎛️ Curve type '{curve_type}' -> show_control_buttons = {show_control_buttons}"
    )

    if hasattr(main_window, 'bspline_add_btn'):
        print(
            f"DEBUG: 🎛️ Setting bspline_add_btn visibility to {show_control_buttons}"
        )
        main_window.bspline_add_btn.Show(show_control_buttons)
        print(
            f"DEBUG: 🎛️ After Show({show_control_buttons}): bspline_add_btn.IsShown() = {main_window.bspline_add_btn.IsShown()}"
        )
    else:
        print(f"DEBUG: 🎛️ WARNING: bspline_add_btn does not exist!")

    if hasattr(main_window, 'bspline_edit_btn'):
        main_window.bspline_edit_btn.Show(show_control_buttons)
    if hasattr(main_window, 'bspline_delete_btn'):
        main_window.bspline_delete_btn.Show(show_control_buttons)
    if hasattr(main_window, 'bspline_up_btn'):
        main_window.bspline_up_btn.Show(show_control_buttons)
    if hasattr(main_window, 'bspline_down_btn'):
        main_window.bspline_down_btn.Show(show_control_buttons)
    if hasattr(main_window, 'bspline_click_mode_btn'):
        print(
            f"DEBUG: 🎛️ Setting bspline_click_mode_btn visibility to {show_control_buttons}"
        )
        main_window.bspline_click_mode_btn.Show(show_control_buttons)
        print(
            f"DEBUG: 🎛️ After Show({show_control_buttons}): bspline_click_mode_btn.IsShown() = {main_window.bspline_click_mode_btn.IsShown()}"
        )
    else:
        print(f"DEBUG: 🎛️ WARNING: bspline_click_mode_btn does not exist!")

    # Update arrow position controls
    if hasattr(main_window, 'arrow_position_slider'):
        arrow_pos = getattr(edge, 'arrow_position', 1.0)
        main_window.arrow_position_slider.SetValue(int(arrow_pos * 100))
        main_window.arrow_position_text.SetValue(f"{arrow_pos:.2f}")

    # Update composite controls (no toggle button - controlled by dropdown)
    if hasattr(main_window, 'composite_list'):
        # If curve type is explicitly "composite", enable composite mode
        if curve_type == "composite":
            edge.is_composite = True
            if not getattr(edge, 'curve_segments', None):
                # Initialize with absolute world coordinates
                dx = target_node.x - source_node.x
                dy = target_node.y - source_node.y
                cp1_x = source_node.x + dx * 0.3
                cp1_y = source_node.y + dy * 0.3 - 30
                cp2_x = source_node.x + dx * 0.7
                cp2_y = source_node.y + dy * 0.7 + 30
                edge.curve_segments = [{
                    "type":
                    "bezier",
                    "control_points": [(cp1_x, cp1_y), (cp2_x, cp2_y)],
                    "weight":
                    1.0
                }]
            if hasattr(main_window, 'composite_pane'):
                try:
                    main_window.composite_pane.Collapse(False)
                except Exception:
                    pass
            main_window.update_composite_list()
            # Auto-select the first segment to show its control points
            if edge.curve_segments and hasattr(main_window, 'composite_list'):
                wx.CallAfter(main_window._auto_select_first_composite_segment)
        else:
            # For non-composite types, ensure composite mode is disabled
            edge.is_composite = False
            if hasattr(main_window, 'composite_pane'):
                try:
                    main_window.composite_pane.Collapse(True)
                except Exception:
                    pass

    # Force layout update after showing/hiding controls
    control_points_window = main_window.control_points_pane.GetPane()
    control_points_window.Layout()
    main_window.control_points_pane.Layout()
    main_window.sidebar.Layout()
    main_window.sidebar.FitInside()

    # Update the control points list to show current points
    print(
        f"DEBUG: 🎛️ Calling update_bspline_list to populate control points"
    )
    try:
        main_window.update_bspline_list()
    except Exception as e:
        print(f"DEBUG: 🛑 update_bspline_list failed: {e}")
    # Ensure the pane is visible and laid out after list population
    try:
        cpw = main_window.control_points_pane.GetPane()
        cpw.Layout()
        main_window.control_points_pane.Collapse(False)
        main_window.control_points_pane.Layout()
        # Additional sidebar relayout to ensure visibility
        main_window.sidebar.Layout()
        main_window.sidebar.FitInside()
        try:
            main_window.control_points_pane.SendSizeEvent()
            main_window.sidebar.SendSizeEvent()
        except Exception:
            pass
    except Exception:
        pass

    print(
        f"DEBUG: 🎛️ Showing curve controls for {curve_type} edge with {len(edge.control_points)} control points (buttons {'hidden' if curve_type == 'straight' else 'visible'})"
    )


def hide_curve_controls(main_window: "m_main_window.MainWindow"):
    """Hide curve control point management controls."""

    main_window.current_curve_edge = None
    main_window.current_curve_type = None
    main_window.current_bspline_edge = None  # Keep compatibility

    # CRITICAL: Clear the canvas editing edge when hiding controls
    main_window.canvas.bspline_editing_edge = None

    # Collapse panes if present to reclaim space
    try:
        if hasattr(main_window, 'control_points_pane'):
            main_window.control_points_pane.Collapse(True)
        if hasattr(main_window, 'composite_pane'):
            main_window.composite_pane.Collapse(True)
        if hasattr(main_window, 'property_panel_pane'):
            main_window.property_panel_pane.GetPane().Layout()
            main_window.property_panel_pane.Layout()
        main_window.sidebar.Layout()
        main_window.sidebar.FitInside()
        main_window.Layout()
    except Exception:
        pass


def _reposition_curve_panes_below_property_panel(
        main_window: "m_main_window.MainWindow"):
    """Ensure Control Points and Composite panes are immediately after the Property Panel in the sidebar."""

    try:
        if not hasattr(main_window, 'sidebar') or not hasattr(
                main_window, 'property_panel_pane'):
            return
        sidebar_sizer = main_window.sidebar.GetSizer()
        if sidebar_sizer is None:
            return
        # Detach if already added in wrong position
        for pane_attr in ('control_points_pane', 'composite_pane'):
            if hasattr(main_window, pane_attr):
                pane = getattr(main_window, pane_attr)
                try:
                    sidebar_sizer.Detach(pane)
                except Exception:
                    pass
        # Find property panel index
        insert_index = None
        children = sidebar_sizer.GetChildren()
        for idx, item in enumerate(children):
            try:
                win = item.GetWindow()
            except Exception:
                win = None
            if win == main_window.property_panel_pane:
                insert_index = idx + 1
                break
        # Reinsert panes in order
        if insert_index is None:
            insert_index = len(children)
        if hasattr(main_window, 'control_points_pane'):
            sidebar_sizer.Insert(insert_index, main_window.control_points_pane,
                                 0, wx.EXPAND | wx.ALL, 5)
            insert_index += 1
        if hasattr(main_window, 'composite_pane'):
            sidebar_sizer.Insert(insert_index, main_window.composite_pane, 0,
                                 wx.EXPAND | wx.ALL, 5)
        # Relayout
        main_window.sidebar.Layout()
        main_window.sidebar.FitInside()
        main_window.Layout()
    except Exception:
        pass


def update_curve_list(main_window: "m_main_window.MainWindow"):
    """Update the curve control points list (works for both B-spline and Bézier)."""

    # Use the existing B-spline list logic for now
    main_window.update_bspline_list()


def show_bspline_controls(main_window: "m_main_window.MainWindow", edge):
    """Show and populate B-spline control point management controls."""

    main_window.current_bspline_edge = edge

    # CRITICAL: Set the canvas editing edge so add control point works
    main_window.canvas.bspline_editing_edge = edge

    # Create controls if they don't exist yet
    if not main_window.bspline_controls_created:
        create_bspline_controls(main_window)

    # Make sure the controls are visible
    if not main_window.bspline_added_to_sizer:
        main_window.bspline_added_to_sizer = True

    main_window.bspline_box.Show(True)
    if hasattr(main_window, 'control_points_pane'):
        try:
            main_window.control_points_pane.Collapse(False)
        except Exception:
            pass

    # Update source/target labels
    source_node = main_window.current_graph.get_node(edge.source_id)
    target_node = main_window.current_graph.get_node(edge.target_id)

    if source_node:
        main_window.bspline_source_label.SetLabel(
            f"Source: ({source_node.x:.1f}, {source_node.y:.1f}) - {source_node.text}"
        )
    if target_node:
        main_window.bspline_target_label.SetLabel(
            f"Target: ({target_node.x:.1f}, {target_node.y:.1f}) - {target_node.text}"
        )

    # Populate control points list (ensure we use the current edge reference)
    main_window.current_curve_edge = edge
    main_window.update_bspline_list()
    # Also keep legacy pointer in sync
    main_window.current_bspline_edge = edge

    # Force layout update
    main_window.sidebar.Layout()
    main_window.sidebar.FitInside()


def hide_bspline_controls(main_window: "m_main_window.MainWindow"):
    """Hide B-spline control point management controls."""

    main_window.current_bspline_edge = None

    # Only hide if controls have been created
    if main_window.bspline_controls_created and hasattr(main_window, 'bspline_box'):
        main_window.bspline_box.Show(False)
        try:
            if hasattr(main_window, 'control_points_pane'):
                main_window.control_points_pane.Collapse(True)
        except Exception:
            pass
        # Force layout update to reclaim space
        main_window.sidebar.Layout()
        main_window.sidebar.FitInside()


def update_bspline_list(main_window: "m_main_window.MainWindow"):
    """Update the B-spline control points list."""

    # Only update if controls have been created
    if not main_window.bspline_controls_created or not hasattr(
            main_window, 'bspline_list'):
        print(
            f"DEBUG: 📝 update_bspline_list: Controls not created or no list"
        )
        return

    main_window.bspline_list.DeleteAllItems()

    # Use either current_curve_edge (new) or current_bspline_edge (legacy)
    edge = getattr(main_window, 'current_curve_edge', None) or getattr(
        main_window, 'current_bspline_edge', None)
    if not edge:
        print(f"DEBUG: 📝 update_bspline_list: No current edge to update")
        return

    print(
        f"DEBUG: 📝 update_bspline_list: Updating list for edge {edge.id} with {len(edge.control_points) if hasattr(edge, 'control_points') else 'NO'} control points"
    )
    for i, control_point in enumerate(edge.control_points):
        # Handle both 2D (x, y) and 3D (x, y, z) coordinates for compatibility
        if len(control_point) >= 2:
            x, y = control_point[0], control_point[1]
            index = main_window.bspline_list.InsertItem(i, str(i + 1))
            main_window.bspline_list.SetItem(index, 1, f"{x:.1f}")
            main_window.bspline_list.SetItem(index, 2, f"{y:.1f}")
            print(f"DEBUG: 📝 Added control point {i+1}: ({x:.1f}, {y:.1f})")
        else:
            print(
                f"DEBUG: 📝 Warning: control point {i} has invalid format: {control_point}"
            )


def reset_bspline_click_mode(main_window: "m_main_window.MainWindow"):
    """Reset the B-spline click mode to inactive state."""

    if hasattr(main_window, 'bspline_click_mode_btn'):
        main_window.bspline_click_mode_btn.SetLabel("Click to Add")
        main_window.bspline_click_mode_btn.SetForegroundColour(
            wx.Colour(0, 0, 0))  # Black text
        main_window.bspline_click_mode_btn.SetBackgroundColour(
            wx.Colour(255, 255, 255))  # White background
        main_window.bspline_click_mode_btn.Refresh()
    print(f"DEBUG: 🌊 Reset B-spline click mode button to 'Click to Add'")


def on_bspline_toggle_click_mode(main_window: "m_main_window.MainWindow", event):
    """Toggle click-to-add mode for curve control points (B-spline or Bézier)."""

    print(f"DEBUG: 🔘🔘🔘 *** CLICK TO ADD BUTTON CLICKED *** 🔘🔘🔘")
    print(f"DEBUG: 🔘 Event: {event}")
    print(f"DEBUG: 🔘 Event type: {type(event)}")
    print(f"DEBUG: 🔘 on_bspline_toggle_click_mode called")
    if not hasattr(main_window.canvas, 'adding_bspline_control_point'):
        print(
            f"DEBUG: 🔘 Canvas has no adding_bspline_control_point attribute"
        )
        return

    print(
        f"DEBUG: 🔘 Current adding_bspline_control_point state: {main_window.canvas.adding_bspline_control_point}"
    )

    if main_window.canvas.adding_bspline_control_point:
        # Exit click mode
        print(f"DEBUG: 🔘 Exiting click mode")
        main_window.canvas.adding_bspline_control_point = False
        main_window.canvas.SetCursor(wx.Cursor(wx.CURSOR_DEFAULT))
        main_window.bspline_click_mode_btn.SetLabel("Click to Add")
        main_window.bspline_click_mode_btn.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
        main_window.bspline_click_mode_btn.SetBackgroundColour(wx.Colour(255, 255, 255))  # White background
        main_window.bspline_click_mode_btn.Refresh()
    else:
        # Enter click mode
        current_edge = getattr(main_window,
                                'current_curve_edge', None) or getattr(
                                    main_window, 'current_bspline_edge', None)
        print(f"DEBUG: 🔘 Current edge for click mode: {current_edge}")
        if current_edge:
            print(
                f"DEBUG: 🔘 Entering click mode for edge {current_edge.id}")
            main_window.canvas.bspline_editing_edge = current_edge
            main_window.canvas.start_adding_bspline_control_point()
            main_window.bspline_click_mode_btn.SetLabel("End Click")
            main_window.bspline_click_mode_btn.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
            main_window.bspline_click_mode_btn.SetBackgroundColour(wx.Colour(255, 255,255))  # White background for active state
            main_window.bspline_click_mode_btn.Refresh()
        else:
            print(
                f"DEBUG: 🔘 No current edge found - cannot enter click mode"
            )


# Move tool event handlers
def on_inverted_changed(main_window: "m_main_window.MainWindow", event):
    """Handle inverted movement toggle change."""
    print(
        f"DEBUG: Inverted movement changed to {main_window.move_inverted_cb.GetValue()}"
    )
    try:
        if hasattr(main_window, 'mvu_adapter'):
            from mvc_mvu.messages import make_message
            import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
            main_window.mvu_adapter.dispatch(make_message(
                m_main_mvu.Msg.SET_MOVE_SENSITIVITY,
                x=main_window.x_sensitivity_field.GetValue(),
                y=main_window.y_sensitivity_field.GetValue(),
                inverted=main_window.move_inverted_cb.GetValue()
            ))
            return
    except Exception:
        pass
    main_window.update_canvas_sensitivity()


def on_sensitivity_lock_changed(main_window: "m_main_window.MainWindow", event):
    """Handle sensitivity lock toggle change."""

    main_window.update_move_tool_ui()


def on_combined_sensitivity_changed(main_window: "m_main_window.MainWindow", event):
    """Handle combined sensitivity field change."""
    new_value = main_window.combined_sensitivity_field.GetValue()
    # Update both X and Y when combined sensitivity changes
    main_window.x_sensitivity_field.SetValue(new_value)
    main_window.y_sensitivity_field.SetValue(new_value)
    try:
        if hasattr(main_window, 'mvu_adapter'):
            from mvc_mvu.messages import make_message
            import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
            main_window.mvu_adapter.dispatch(make_message(
                m_main_mvu.Msg.SET_MOVE_SENSITIVITY,
                x=new_value,
                y=new_value,
                inverted=main_window.move_inverted_cb.GetValue()
            ))
            return
    except Exception:
        pass
    main_window.update_canvas_sensitivity()


def adjust_x_sensitivity(main_window: "m_main_window.MainWindow", delta):
    """Adjust X sensitivity by delta amount."""
    current = main_window.x_sensitivity_field.GetValue()
    new_value = max(0.1, min(10.0, current + delta))
    main_window.x_sensitivity_field.SetValue(new_value)
    try:
        if hasattr(main_window, 'mvu_adapter'):
            from mvc_mvu.messages import make_message
            import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
            main_window.mvu_adapter.dispatch(make_message(
                m_main_mvu.Msg.SET_MOVE_SENSITIVITY,
                x=new_value,
                y=main_window.y_sensitivity_field.GetValue(),
                inverted=main_window.move_inverted_cb.GetValue()
            ))
            return
    except Exception:
        pass
    main_window.update_canvas_sensitivity()


def adjust_y_sensitivity(main_window: "m_main_window.MainWindow", delta):
    """Adjust Y sensitivity by delta amount."""
    current = main_window.y_sensitivity_field.GetValue()
    new_value = max(0.1, min(10.0, current + delta))
    main_window.y_sensitivity_field.SetValue(new_value)
    try:
        if hasattr(main_window, 'mvu_adapter'):
            from mvc_mvu.messages import make_message
            import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
            main_window.mvu_adapter.dispatch(make_message(
                m_main_mvu.Msg.SET_MOVE_SENSITIVITY,
                x=main_window.x_sensitivity_field.GetValue(),
                y=new_value,
                inverted=main_window.move_inverted_cb.GetValue()
            ))
            return
    except Exception:
        pass
    main_window.update_canvas_sensitivity()


def adjust_combined_sensitivity(main_window: "m_main_window.MainWindow", delta):
    """Adjust combined sensitivity by delta amount."""
    current = main_window.combined_sensitivity_field.GetValue()
    new_value = max(0.1, min(10.0, current + delta))
    main_window.combined_sensitivity_field.SetValue(new_value)
    # Update both X and Y when combined sensitivity changes
    main_window.x_sensitivity_field.SetValue(new_value)
    main_window.y_sensitivity_field.SetValue(new_value)
    try:
        if hasattr(main_window, 'mvu_adapter'):
            from mvc_mvu.messages import make_message
            import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
            main_window.mvu_adapter.dispatch(make_message(
                m_main_mvu.Msg.SET_MOVE_SENSITIVITY,
                x=new_value,
                y=new_value,
                inverted=main_window.move_inverted_cb.GetValue()
            ))
            return
    except Exception:
        pass
    main_window.update_canvas_sensitivity()


def update_move_tool_ui(main_window: "m_main_window.MainWindow"):
    """Update move tool UI visibility based on lock state."""

    is_locked = main_window.sensitivity_locked_cb.GetValue()

    # Show/hide individual X/Y controls
    for widget in [main_window.x_sensitivity_sizer, main_window.y_sensitivity_sizer]:
        widget.ShowItems(not is_locked)

    # Show/hide combined control
    main_window.combined_sensitivity_sizer.ShowItems(is_locked)

    # Sync combined field value with X/Y when switching to locked
    if is_locked:
        x_value = main_window.x_sensitivity_field.GetValue()
        main_window.combined_sensitivity_field.SetValue(x_value)

    # Refresh layout
    main_window.sidebar.Layout()


def adjust_zoom_sensitivity(main_window: "m_main_window.MainWindow", delta):
    """Adjust zoom sensitivity by delta amount."""
    current = main_window.zoom_sensitivity_field.GetValue()
    new_value = max(0.1, min(5.0, current + delta))
    main_window.zoom_sensitivity_field.SetValue(new_value)
    try:
        if hasattr(main_window, 'mvu_adapter'):
            from mvc_mvu.messages import make_message
            import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
            main_window.mvu_adapter.dispatch(make_message(
                m_main_mvu.Msg.SET_ZOOM_SENSITIVITY,
                value=new_value
            ))
            return
    except Exception:
        pass
    main_window.update_canvas_zoom_sensitivity()


def on_zoom_sensitivity_changed(main_window: "m_main_window.MainWindow", event):
    """Handle zoom sensitivity field change."""
    try:
        if hasattr(main_window, 'mvu_adapter'):
            from mvc_mvu.messages import make_message
            import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
            # Persist via ZoomManager
            try:
                main_window.managers.zoom_manager.set_sensitivity(main_window.zoom_sensitivity_field.GetValue())
            except Exception:
                pass
            main_window.mvu_adapter.dispatch(make_message(
                m_main_mvu.Msg.SET_ZOOM_SENSITIVITY,
                value=main_window.zoom_sensitivity_field.GetValue()
            ))
            return
    except Exception:
        pass
    main_window.update_canvas_zoom_sensitivity()
    # Also update canvas base for smoother scaling responsiveness if provided
    try:
        if hasattr(main_window, 'canvas'):
            main_window.canvas.set_zoom_sensitivity(main_window.zoom_sensitivity_field.GetValue())
    except Exception:
        pass


def _on_zoom_input_mode_changed(main_window: "m_main_window.MainWindow", event):
    """Handle zoom input mode choice (Wheel vs Touchpad vs Both)."""
    try:
        if hasattr(main_window, 'mvu_adapter'):
            from mvc_mvu.messages import make_message
            import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
            label = main_window.zoom_input_choice.GetStringSelection()
            l = (label or '').strip().lower()
            if l == 'both':
                mode = 'both'
            elif l == 'touchpad':
                mode = 'touchpad'
            else:
                mode = 'wheel'
            try:
                print(f"DEBUG: Sidebar zoom input mode changed -> {mode}")
            except Exception:
                pass
            # Persist via ZoomManager
            try:
                main_window.managers.zoom_manager.set_mode(mode)
            except Exception:
                pass
            main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_ZOOM_INPUT_MODE, mode=mode))
    except Exception:
        pass


def update_canvas_sensitivity(main_window: "m_main_window.MainWindow"):
    """Update canvas with current sensitivity settings."""

    if hasattr(main_window, 'canvas'):
        main_window.canvas.set_move_sensitivity(
        main_window.x_sensitivity_field.GetValue(),
        main_window.y_sensitivity_field.GetValue(),
        main_window.move_inverted_cb.GetValue())


def adjust_rotation(main_window: "m_main_window.MainWindow", delta):
    """Adjust rotation by delta amount."""

    current = main_window.rotation_field.GetValue()
    new_value = (current + delta) % 360  # Keep within 0-360 range
    if new_value < 0:
        new_value += 360
    main_window.rotation_field.SetValue(new_value)
    try:
        if hasattr(main_window, 'mvu_adapter'):
            from mvc_mvu.messages import make_message
            import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
            main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_ROTATION, angle=new_value))
            return
    except Exception:
        pass
    update_canvas_rotation(main_window)


def on_rotation_changed(main_window: "m_main_window.MainWindow", event):
    """Handle rotation field change."""
    try:
        if hasattr(main_window, 'mvu_adapter'):
            from mvc_mvu.messages import make_message
            import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
            main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_ROTATION, angle=main_window.rotation_field.GetValue()))
            return
    except Exception:
        pass
    update_canvas_rotation(main_window)


def update_canvas_rotation(main_window: "m_main_window.MainWindow"):
    """Update canvas with current rotation setting."""

    if hasattr(main_window, 'canvas'):
        angle = main_window.rotation_field.GetValue()
        print(f"DEBUG: Setting world rotation to {angle}°")
        main_window.canvas.set_world_rotation(angle)
