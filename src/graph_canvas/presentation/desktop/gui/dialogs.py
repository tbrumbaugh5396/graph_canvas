"""
Dialog classes for the graph editor.
"""


import wx

import graph_canvas.presentation.desktop.models.node as m_node
import graph_canvas.presentation.desktop.models.edge as m_edge
import graph_canvas.presentation.desktop.models.graph as m_graph


class NodePropertiesDialog(wx.Dialog):
    """Dialog for editing node properties."""

    def __init__(self, parent, node: m_node.Node):
        super().__init__(
            parent,
            title="Node Properties",
            size=(400, 500),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX,
        )

        self.node = node
        self.setup_ui()

    def setup_ui(self):
        """Set up the dialog UI."""

        # Create scrolled panel for the main content
        panel = wx.ScrolledWindow(self, style=wx.VSCROLL)
        # Use SetScrollRate to avoid relayout-induced control resizing on macOS
        panel.SetScrollRate(0, 20)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Basic properties
        basic_box = wx.StaticBox(panel, label="Basic Properties")
        basic_sizer = wx.StaticBoxSizer(basic_box, wx.VERTICAL)

        # Text
        basic_sizer.Add(wx.StaticText(panel, label="Text:"), 0, wx.ALL, 5)
        self.text_ctrl = wx.TextCtrl(panel,
                                     value=self.node.text,
                                     style=wx.TE_MULTILINE)
        basic_sizer.Add(self.text_ctrl, 1, wx.EXPAND | wx.ALL, 5)

        # Position
        pos_sizer = wx.FlexGridSizer(3, 2, 5, 5)
        pos_sizer.AddGrowableCol(1)
        pos_sizer.Add(wx.StaticText(panel, label="X:"), 0,
                      wx.ALIGN_CENTER_VERTICAL)
        self.x_ctrl = wx.SpinCtrlDouble(panel,
                                        min=-10000,
                                        max=10000,
                                        inc=1)
        self.x_ctrl.SetValue(self.node.x)
        pos_sizer.Add(self.x_ctrl, 1, wx.EXPAND)

        pos_sizer.Add(wx.StaticText(panel, label="Y:"), 0,
                      wx.ALIGN_CENTER_VERTICAL)
        self.y_ctrl = wx.SpinCtrlDouble(panel,
                                        min=-10000,
                                        max=10000,
                                        inc=1)
        self.y_ctrl.SetValue(self.node.y)
        pos_sizer.Add(self.y_ctrl, 1, wx.EXPAND)

        pos_sizer.Add(wx.StaticText(panel, label="Z:"), 0,
                      wx.ALIGN_CENTER_VERTICAL)
        self.z_ctrl = wx.SpinCtrlDouble(panel,
                                        min=-10000,
                                        max=10000,
                                        inc=1)
        self.z_ctrl.SetValue(self.node.z)
        pos_sizer.Add(self.z_ctrl, 1, wx.EXPAND)

        basic_sizer.Add(pos_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Node type selection
        type_sizer = wx.BoxSizer(wx.HORIZONTAL)
        type_sizer.Add(wx.StaticText(panel, label="Node Type:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        self.node_type_choice = wx.Choice(panel, choices=[
            "standard_node",
            "uber_node"
        ])
        # Default selection
        self.node_type_choice.SetSelection(1 if getattr(self.node, 'metadata', {}).get('node_type') == 'uber_node' else 0)
        type_sizer.Add(self.node_type_choice, 1, wx.EXPAND | wx.ALL, 5)
        basic_sizer.Add(type_sizer, 0, wx.EXPAND | wx.ALL, 5)

        sizer.Add(basic_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Visual properties
        visual_box = wx.StaticBox(panel, label="Visual Properties")
        visual_sizer = wx.StaticBoxSizer(visual_box, wx.VERTICAL)

        # Size
        size_sizer = wx.FlexGridSizer(2, 2, 5, 5)
        size_sizer.AddGrowableCol(1)
        size_sizer.Add(wx.StaticText(panel, label="Width:"), 0,
                       wx.ALIGN_CENTER_VERTICAL)
        self.width_ctrl = wx.SpinCtrl(panel,
                                      min=10,
                                      max=500)
        self.width_ctrl.SetValue(self.node.width)
        size_sizer.Add(self.width_ctrl, 1, wx.EXPAND)

        size_sizer.Add(wx.StaticText(panel, label="Height:"), 0,
                       wx.ALIGN_CENTER_VERTICAL)
        self.height_ctrl = wx.SpinCtrl(panel,
                                       min=10,
                                       max=500)
        self.height_ctrl.SetValue(self.node.height)
        size_sizer.Add(self.height_ctrl, 1, wx.EXPAND)

        visual_sizer.Add(size_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Colors
        color_sizer = wx.FlexGridSizer(3, 2, 5, 5)
        color_sizer.AddGrowableCol(1)

        color_sizer.Add(wx.StaticText(panel, label="Fill Color:"), 0,
                        wx.ALIGN_CENTER_VERTICAL)
        self.fill_color_btn = wx.Button(panel, label="Choose Color")
        self.fill_color_btn.SetBackgroundColour(wx.Colour(*self.node.color))
        self.fill_color_btn.Bind(wx.EVT_BUTTON, self.on_fill_color)
        color_sizer.Add(self.fill_color_btn, 1, wx.EXPAND)

        color_sizer.Add(wx.StaticText(panel, label="Text Color:"), 0,
                        wx.ALIGN_CENTER_VERTICAL)
        self.text_color_btn = wx.Button(panel, label="Choose Color")
        self.text_color_btn.SetBackgroundColour(
            wx.Colour(*self.node.text_color))
        self.text_color_btn.Bind(wx.EVT_BUTTON, self.on_text_color)
        color_sizer.Add(self.text_color_btn, 1, wx.EXPAND)

        color_sizer.Add(wx.StaticText(panel, label="Border Color:"), 0,
                        wx.ALIGN_CENTER_VERTICAL)
        self.border_color_btn = wx.Button(panel, label="Choose Color")
        self.border_color_btn.SetBackgroundColour(
            wx.Colour(*self.node.border_color))
        self.border_color_btn.Bind(wx.EVT_BUTTON, self.on_border_color)
        color_sizer.Add(self.border_color_btn, 1, wx.EXPAND)

        visual_sizer.Add(color_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Font and border
        font_sizer = wx.FlexGridSizer(2, 2, 5, 5)
        font_sizer.AddGrowableCol(1)
        font_sizer.Add(wx.StaticText(panel, label="Font Size:"), 0,
                       wx.ALIGN_CENTER_VERTICAL)
        self.font_size_ctrl = wx.SpinCtrl(panel,
                                          min=6,
                                          max=72)
        self.font_size_ctrl.SetValue(self.node.font_size)
        font_sizer.Add(self.font_size_ctrl, 1, wx.EXPAND)

        font_sizer.Add(wx.StaticText(panel, label="Border Width:"), 0,
                       wx.ALIGN_CENTER_VERTICAL)
        self.border_width_ctrl = wx.SpinCtrl(panel,
                                             min=0,
                                             max=10)
        self.border_width_ctrl.SetValue(self.node.border_width)
        font_sizer.Add(self.border_width_ctrl, 1, wx.EXPAND)

        visual_sizer.Add(font_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Checkboxes
        self.visible_cb = wx.CheckBox(panel, label="Visible")
        self.visible_cb.SetValue(self.node.visible)
        visual_sizer.Add(self.visible_cb, 0, wx.ALL, 5)

        self.locked_cb = wx.CheckBox(panel, label="Locked")
        self.locked_cb.SetValue(self.node.locked)
        visual_sizer.Add(self.locked_cb, 0, wx.ALL, 5)

        sizer.Add(visual_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Metadata
        metadata_box = wx.StaticBox(panel, label="Metadata")
        metadata_sizer = wx.StaticBoxSizer(metadata_box, wx.VERTICAL)

        self.metadata_list = wx.ListCtrl(panel,
                                         style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.metadata_list.AppendColumn("Key", width=150)
        self.metadata_list.AppendColumn("Value", width=200)
        self.update_metadata_list()
        metadata_sizer.Add(self.metadata_list, 1, wx.EXPAND | wx.ALL, 5)

        # Metadata buttons
        metadata_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        add_btn = wx.Button(panel, label="Add")
        add_btn.Bind(wx.EVT_BUTTON, self.on_add_metadata)
        edit_btn = wx.Button(panel, label="Edit")
        edit_btn.Bind(wx.EVT_BUTTON, self.on_edit_metadata)
        remove_btn = wx.Button(panel, label="Remove")
        remove_btn.Bind(wx.EVT_BUTTON, self.on_remove_metadata)

        metadata_btn_sizer.Add(add_btn, 0, wx.ALL, 5)
        metadata_btn_sizer.Add(edit_btn, 0, wx.ALL, 5)
        metadata_btn_sizer.Add(remove_btn, 0, wx.ALL, 5)

        metadata_sizer.Add(metadata_btn_sizer, 0, wx.EXPAND)

        sizer.Add(metadata_sizer, 1, wx.EXPAND | wx.ALL, 5)

        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_btn = wx.Button(panel, wx.ID_OK, "OK")
        ok_btn.Bind(wx.EVT_BUTTON, self.on_ok)
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")

        btn_sizer.Add(ok_btn, 0, wx.ALL, 5)
        btn_sizer.Add(cancel_btn, 0, wx.ALL, 5)

        sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 5)

        # Set up scrolled panel
        panel.SetSizer(sizer)
        panel.FitInside()  # Tell the scrolled window the minimum size
        
        # Add the scrolled panel to the dialog
        dialog_sizer = wx.BoxSizer(wx.VERTICAL)
        dialog_sizer.Add(panel, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(dialog_sizer)

    def update_metadata_list(self):
        """Update the metadata list control."""

        self.metadata_list.DeleteAllItems()
        for i, (key, value) in enumerate(self.node.metadata.items()):
            self.metadata_list.InsertItem(i, key)
            self.metadata_list.SetItem(i, 1, str(value))

    def on_fill_color(self, event):
        """Handle fill color button click."""

        color = wx.ColourDialog(self)
        if color.ShowModal() == wx.ID_OK:
            new_color = color.GetColourData().GetColour()
            self.fill_color_btn.SetBackgroundColour(new_color)
        color.Destroy()

    def on_text_color(self, event):
        """Handle text color button click."""

        color = wx.ColourDialog(self)
        if color.ShowModal() == wx.ID_OK:
            new_color = color.GetColourData().GetColour()
            self.text_color_btn.SetBackgroundColour(new_color)
        color.Destroy()

    def on_border_color(self, event):
        """Handle border color button click."""

        color = wx.ColourDialog(self)
        if color.ShowModal() == wx.ID_OK:
            new_color = color.GetColourData().GetColour()
            self.border_color_btn.SetBackgroundColour(new_color)
        color.Destroy()

    def on_add_metadata(self, event):
        """Add metadata entry."""

        dialog = MetadataDialog(self, "", "")
        if dialog.ShowModal() == wx.ID_OK:
            key, value = dialog.get_values()
            self.node.set_metadata(key, value)
            self.update_metadata_list()
        dialog.Destroy()

    def on_edit_metadata(self, event):
        """Edit metadata entry."""

        selection = self.metadata_list.GetFirstSelected()
        if selection >= 0:
            key = self.metadata_list.GetItemText(selection, 0)
            value = self.metadata_list.GetItemText(selection, 1)

            dialog = MetadataDialog(self, key, value)
            if dialog.ShowModal() == wx.ID_OK:
                new_key, new_value = dialog.get_values()
                if new_key != key:
                    self.node.remove_metadata(key)
                self.node.set_metadata(new_key, new_value)
                self.update_metadata_list()
            dialog.Destroy()

    def on_remove_metadata(self, event):
        """Remove metadata entry."""

        selection = self.metadata_list.GetFirstSelected()
        if selection >= 0:
            key = self.metadata_list.GetItemText(selection, 0)
            self.node.remove_metadata(key)
            self.update_metadata_list()

    def on_ok(self, event):
        """Handle OK button click."""

        # Apply changes
        self.node.text = self.text_ctrl.GetValue()
        self.node.x = self.x_ctrl.GetValue()
        self.node.y = self.y_ctrl.GetValue()
        self.node.z = self.z_ctrl.GetValue()
        self.node.width = self.width_ctrl.GetValue()
        self.node.height = self.height_ctrl.GetValue()
        self.node.font_size = self.font_size_ctrl.GetValue()
        self.node.border_width = self.border_width_ctrl.GetValue()
        self.node.visible = self.visible_cb.GetValue()
        self.node.locked = self.locked_cb.GetValue()

        # Apply colors
        self.node.color = self.fill_color_btn.GetBackgroundColour().Get()[:3]
        self.node.text_color = self.text_color_btn.GetBackgroundColour().Get(
        )[:3]
        self.node.border_color = self.border_color_btn.GetBackgroundColour(
        ).Get()[:3]

        # Save node type
        try:
            if self.node_type_choice.GetSelection() == 1:
                self.node.metadata['node_type'] = 'uber_node'
            else:
                self.node.metadata['node_type'] = 'standard_node'
        except Exception:
            pass

        self.EndModal(wx.ID_OK)


class EdgePropertiesDialog(wx.Dialog):
    """Dialog for editing edge properties."""

    def __init__(self, parent, edge: m_edge.Edge):
        super().__init__(
            parent,
            title="Edge Properties",
            size=(400, 450),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX,
        )

        self.edge = edge
        self.setup_ui()

    def setup_ui(self):
        """Set up the dialog UI."""

        # Create scrolled panel for the main content
        panel = wx.ScrolledWindow(self, style=wx.VSCROLL)
        panel.SetScrollRate(0, 20)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Basic properties
        basic_box = wx.StaticBox(panel, label="Basic Properties")
        basic_sizer = wx.StaticBoxSizer(basic_box, wx.VERTICAL)

        # Text
        basic_sizer.Add(wx.StaticText(panel, label="Text:"), 0, wx.ALL, 5)
        self.text_ctrl = wx.TextCtrl(panel,
                                     value=self.edge.text,
                                     style=wx.TE_MULTILINE)
        basic_sizer.Add(self.text_ctrl, 1, wx.EXPAND | wx.ALL, 5)

        # Source nodes list
        basic_sizer.Add(wx.StaticText(panel, label="Source Nodes:"), 0, wx.ALL, 5)
        self.source_list = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.source_list.AppendColumn("Node ID", width=200)
        for node_id in self.edge.source_ids:
            self.source_list.InsertItem(self.source_list.GetItemCount(), node_id)
        basic_sizer.Add(self.source_list, 1, wx.EXPAND | wx.ALL, 5)

        # Source node buttons
        source_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        add_source_btn = wx.Button(panel, label="Add Source")
        add_source_btn.Bind(wx.EVT_BUTTON, self.on_add_source)
        remove_source_btn = wx.Button(panel, label="Remove Source")
        remove_source_btn.Bind(wx.EVT_BUTTON, self.on_remove_source)
        source_btn_sizer.Add(add_source_btn, 0, wx.ALL, 5)
        source_btn_sizer.Add(remove_source_btn, 0, wx.ALL, 5)
        basic_sizer.Add(source_btn_sizer, 0, wx.EXPAND)

        # Target nodes list
        basic_sizer.Add(wx.StaticText(panel, label="Target Nodes:"), 0, wx.ALL, 5)
        self.target_list = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.target_list.AppendColumn("Node ID", width=200)
        for node_id in self.edge.target_ids:
            self.target_list.InsertItem(self.target_list.GetItemCount(), node_id)
        basic_sizer.Add(self.target_list, 1, wx.EXPAND | wx.ALL, 5)

        # Target node buttons
        target_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        add_target_btn = wx.Button(panel, label="Add Target")
        add_target_btn.Bind(wx.EVT_BUTTON, self.on_add_target)
        remove_target_btn = wx.Button(panel, label="Remove Target")
        remove_target_btn.Bind(wx.EVT_BUTTON, self.on_remove_target)
        target_btn_sizer.Add(add_target_btn, 0, wx.ALL, 5)
        target_btn_sizer.Add(remove_target_btn, 0, wx.ALL, 5)
        basic_sizer.Add(target_btn_sizer, 0, wx.EXPAND)

        # Edge type selection
        type_sizer = wx.BoxSizer(wx.HORIZONTAL)
        type_sizer.Add(wx.StaticText(panel, label="Edge Type:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        self.edge_type_choice = wx.Choice(panel, choices=[
            "standard_edge",
            "hyperedge",
            "uberedge"
        ])
        # Default selection based on flags
        if getattr(self.edge, 'is_hyperedge', False) and getattr(self.edge, 'hyperedge_visualization', 'lines') == 'ubergraph':
            self.edge_type_choice.SetSelection(2)
        elif getattr(self.edge, 'is_hyperedge', False):
            self.edge_type_choice.SetSelection(1)
        else:
            self.edge_type_choice.SetSelection(0)
        type_sizer.Add(self.edge_type_choice, 1, wx.EXPAND | wx.ALL, 5)
        basic_sizer.Add(type_sizer, 0, wx.EXPAND | wx.ALL, 5)

        sizer.Add(basic_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Hyperedge properties
        hyperedge_box = wx.StaticBox(panel, label="Hyperedge Properties")
        hyperedge_sizer = wx.StaticBoxSizer(hyperedge_box, wx.VERTICAL)
        
        # Connection points
        connection_sizer = wx.FlexGridSizer(2, 2, 5, 5)
        connection_sizer.AddGrowableCol(1)
        
        connection_sizer.Add(wx.StaticText(panel, label="From Connection Point:"), 0,
                     wx.ALIGN_CENTER_VERTICAL)
        self.from_connection_slider = wx.Slider(panel, value=int(self.edge.from_connection_point * 100),
                                              minValue=0, maxValue=100,
                                              style=wx.SL_HORIZONTAL)
        connection_sizer.Add(self.from_connection_slider, 1, wx.EXPAND)
        
        connection_sizer.Add(wx.StaticText(panel, label="To Connection Point:"), 0,
                     wx.ALIGN_CENTER_VERTICAL)
        self.to_connection_slider = wx.Slider(panel, value=int(self.edge.to_connection_point * 100),
                                            minValue=0, maxValue=100,
                                            style=wx.SL_HORIZONTAL)
        connection_sizer.Add(self.to_connection_slider, 1, wx.EXPAND)
        
        hyperedge_sizer.Add(connection_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # From nodes list
        hyperedge_sizer.Add(wx.StaticText(panel, label="From Nodes:"), 0, wx.ALL, 5)
        self.from_nodes_list = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.from_nodes_list.AppendColumn("Node ID", width=200)
        for node_id in self.edge.from_nodes:
            self.from_nodes_list.InsertItem(self.from_nodes_list.GetItemCount(), node_id)
        hyperedge_sizer.Add(self.from_nodes_list, 1, wx.EXPAND | wx.ALL, 5)
        
        # To nodes list
        hyperedge_sizer.Add(wx.StaticText(panel, label="To Nodes:"), 0, wx.ALL, 5)
        self.to_nodes_list = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.to_nodes_list.AppendColumn("Node ID", width=200)
        for node_id in self.edge.to_nodes:
            self.to_nodes_list.InsertItem(self.to_nodes_list.GetItemCount(), node_id)
        hyperedge_sizer.Add(self.to_nodes_list, 1, wx.EXPAND | wx.ALL, 5)
        
        sizer.Add(hyperedge_sizer, 1, wx.EXPAND | wx.ALL, 5)
        
        # Arrow properties
        arrow_box = wx.StaticBox(panel, label="Arrow Properties")
        arrow_sizer = wx.StaticBoxSizer(arrow_box, wx.VERTICAL)
        
        # Arrow position slider
        arrow_sizer.Add(wx.StaticText(panel, label="Arrow Position:"), 0, wx.ALL, 5)
        self.arrow_position_slider = wx.Slider(panel, value=int(self.edge.arrow_position * 100),
                                             minValue=0, maxValue=100,
                                             style=wx.SL_HORIZONTAL)
        arrow_sizer.Add(self.arrow_position_slider, 0, wx.EXPAND | wx.ALL, 5)
        
        # Arrow options for hyperedges
        if self.edge.is_hyperedge:
            self.split_arrows_cb = wx.CheckBox(panel, label="Split Arrows")
            self.split_arrows_cb.SetValue(self.edge.split_arrows)
            arrow_sizer.Add(self.split_arrows_cb, 0, wx.ALL, 5)

            # Hyperedge visualization options
            viz_box = wx.StaticBox(panel, label="Hyperedge Visualization")
            viz_sizer = wx.StaticBoxSizer(viz_box, wx.VERTICAL)
            
            viz_choices = [
                "Lines (Default)",
                "Curved Surface",
                "Blob Boundary",
                "Pie Chart Nodes",
                "Polygon",
                "Zykov",
                "Radial Layout",
                "PAOH Layout",
                "Force-Directed",
                "Ubergraph"
            ]
            self.viz_choice = wx.Choice(panel, choices=viz_choices)
            # Set current selection
            viz_map = {
                "lines": 0,
                "curved_surface": 1,
                "blob_boundary": 2,
                "pie_chart": 3,
                "polygon": 4,
                "zykov": 5,
                "radial": 6,
                "paoh": 7,
                "force_directed": 8,
                "ubergraph": 9
            }
            self.viz_choice.SetSelection(viz_map.get(self.edge.hyperedge_visualization, 0))
            
            def on_viz_change(event):
                # Update visualization immediately
                viz_map_reverse = {
                    0: "lines",
                    1: "curved_surface",
                    2: "blob_boundary",
                    3: "pie_chart",
                    4: "polygon",
                    5: "zykov",
                    6: "radial",
                    7: "paoh",
                    8: "force_directed",
                    9: "ubergraph"
                }
                self.edge.hyperedge_visualization = viz_map_reverse.get(self.viz_choice.GetSelection(), "lines")
                # Force a refresh of the canvas
                try:
                    parent = self.GetParent()
                    # Parent is GraphCanvas in context-menu flow; main window in sidebar flow
                    if hasattr(parent, 'Refresh'):
                        wx.CallAfter(parent.Refresh)
                    elif hasattr(parent, 'canvas') and hasattr(parent.canvas, 'Refresh'):
                        wx.CallAfter(parent.canvas.Refresh)
                except Exception:
                    pass
            
            self.viz_choice.Bind(wx.EVT_CHOICE, on_viz_change)
            viz_sizer.Add(self.viz_choice, 0, wx.EXPAND | wx.ALL, 5)
            
            # Add hyperedge view options
            view_choices = [
                "Standard",
                "Line Graph",
                "Derivative Graph"
            ]
            self.view_choice = wx.Choice(panel, choices=view_choices)
            view_map = {
                "standard": 0,
                "line_graph": 1,
                "derivative_graph": 2
            }
            self.view_choice.SetSelection(view_map.get(self.edge.hyperedge_view, 0))
            
            def on_view_change(event):
                view_map_reverse = {
                    0: "standard",
                    1: "line_graph",
                    2: "derivative_graph"
                }
                self.edge.hyperedge_view = view_map_reverse.get(self.view_choice.GetSelection(), "standard")
                try:
                    parent = self.GetParent()
                    if hasattr(parent, 'Refresh'):
                        wx.CallAfter(parent.Refresh)
                    elif hasattr(parent, 'canvas') and hasattr(parent.canvas, 'Refresh'):
                        wx.CallAfter(parent.canvas.Refresh)
                except Exception:
                    pass
            
            self.view_choice.Bind(wx.EVT_CHOICE, on_view_change)
            viz_sizer.Add(wx.StaticText(panel, label="Hyperedge View:"), 0, wx.ALL, 5)
            viz_sizer.Add(self.view_choice, 0, wx.EXPAND | wx.ALL, 5)
            
            # Add auto-layout toggle for ubergraph
            self.auto_layout_cb = wx.CheckBox(panel, label="Auto Layout")
            self.auto_layout_cb.SetValue(self.edge.uber_auto_layout)
            
            def on_auto_layout_toggle(event):
                self.edge.uber_auto_layout = self.auto_layout_cb.GetValue()
                if self.edge.uber_auto_layout:
                    # Trigger layout update
                    wx.CallAfter(self.GetParent().canvas.update_ubergraph_layout)
                wx.CallAfter(self.GetParent().canvas.Refresh)
            
            self.auto_layout_cb.Bind(wx.EVT_CHECKBOX, on_auto_layout_toggle)
            viz_sizer.Add(self.auto_layout_cb, 0, wx.ALL, 5)
            
            sizer.Add(viz_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        sizer.Add(arrow_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Visual properties
        visual_box = wx.StaticBox(panel, label="Visual Properties")
        visual_sizer = wx.StaticBoxSizer(visual_box, wx.VERTICAL)

        # Line properties
        line_sizer = wx.FlexGridSizer(3, 2, 5, 5)

        line_sizer.Add(wx.StaticText(panel, label="Line Width:"), 0,
                       wx.ALIGN_CENTER_VERTICAL)
        self.width_ctrl = wx.SpinCtrl(panel, min=1, max=20)
        self.width_ctrl.SetValue(self.edge.width)
        line_sizer.Add(self.width_ctrl, 1, wx.EXPAND)

        line_sizer.Add(wx.StaticText(panel, label="Arrow Size:"), 0,
                       wx.ALIGN_CENTER_VERTICAL)
        self.arrow_size_ctrl = wx.SpinCtrl(panel, min=5, max=50)
        self.arrow_size_ctrl.SetValue(self.edge.arrow_size)
        line_sizer.Add(self.arrow_size_ctrl, 1, wx.EXPAND)

        line_sizer.Add(wx.StaticText(panel, label="Font Size:"), 0,
                       wx.ALIGN_CENTER_VERTICAL)
        self.font_size_ctrl = wx.SpinCtrl(panel, min=6, max=72)
        self.font_size_ctrl.SetValue(self.edge.font_size)
        line_sizer.Add(self.font_size_ctrl, 1, wx.EXPAND)

        visual_sizer.Add(line_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Colors
        color_sizer = wx.FlexGridSizer(2, 2, 5, 5)

        color_sizer.Add(wx.StaticText(panel, label="Line Color:"), 0,
                        wx.ALIGN_CENTER_VERTICAL)
        self.line_color_btn = wx.Button(panel, label="Choose Color")
        self.line_color_btn.SetBackgroundColour(wx.Colour(*self.edge.color))
        self.line_color_btn.Bind(wx.EVT_BUTTON, self.on_line_color)
        color_sizer.Add(self.line_color_btn, 1, wx.EXPAND)

        color_sizer.Add(wx.StaticText(panel, label="Text Color:"), 0,
                        wx.ALIGN_CENTER_VERTICAL)
        self.text_color_btn = wx.Button(panel, label="Choose Color")
        self.text_color_btn.SetBackgroundColour(
            wx.Colour(*self.edge.text_color))
        self.text_color_btn.Bind(wx.EVT_BUTTON, self.on_text_color)
        color_sizer.Add(self.text_color_btn, 1, wx.EXPAND)

        visual_sizer.Add(color_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Style
        style_sizer = wx.BoxSizer(wx.HORIZONTAL)
        style_sizer.Add(wx.StaticText(panel, label="Line Style:"), 0,
                        wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        self.style_choice = wx.Choice(panel,
                                      choices=["solid", "dashed", "dotted"])
        self.style_choice.SetSelection(["solid", "dashed",
                                        "dotted"].index(self.edge.line_style))
        style_sizer.Add(self.style_choice, 1, wx.EXPAND | wx.ALL, 5)

        visual_sizer.Add(style_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Checkboxes
        self.directed_cb = wx.CheckBox(panel, label="Directed (has arrow)")
        self.directed_cb.SetValue(self.edge.directed)
        visual_sizer.Add(self.directed_cb, 0, wx.ALL, 5)

        self.visible_cb = wx.CheckBox(panel, label="Visible")
        self.visible_cb.SetValue(self.edge.visible)
        visual_sizer.Add(self.visible_cb, 0, wx.ALL, 5)

        self.locked_cb = wx.CheckBox(panel, label="Locked")
        self.locked_cb.SetValue(self.edge.locked)
        visual_sizer.Add(self.locked_cb, 0, wx.ALL, 5)

        sizer.Add(visual_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Metadata
        metadata_box = wx.StaticBox(panel, label="Metadata")
        metadata_sizer = wx.StaticBoxSizer(metadata_box, wx.VERTICAL)

        self.metadata_list = wx.ListCtrl(panel,
                                         style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.metadata_list.AppendColumn("Key", width=150)
        self.metadata_list.AppendColumn("Value", width=200)
        self.update_metadata_list()
        metadata_sizer.Add(self.metadata_list, 1, wx.EXPAND | wx.ALL, 5)

        # Metadata buttons
        metadata_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        add_btn = wx.Button(panel, label="Add")
        add_btn.Bind(wx.EVT_BUTTON, self.on_add_metadata)
        edit_btn = wx.Button(panel, label="Edit")
        edit_btn.Bind(wx.EVT_BUTTON, self.on_edit_metadata)
        remove_btn = wx.Button(panel, label="Remove")
        remove_btn.Bind(wx.EVT_BUTTON, self.on_remove_metadata)

        metadata_btn_sizer.Add(add_btn, 0, wx.ALL, 5)
        metadata_btn_sizer.Add(edit_btn, 0, wx.ALL, 5)
        metadata_btn_sizer.Add(remove_btn, 0, wx.ALL, 5)

        metadata_sizer.Add(metadata_btn_sizer, 0, wx.EXPAND)

        sizer.Add(metadata_sizer, 1, wx.EXPAND | wx.ALL, 5)

        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_btn = wx.Button(panel, wx.ID_OK, "OK")
        ok_btn.Bind(wx.EVT_BUTTON, self.on_ok)
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")

        btn_sizer.Add(ok_btn, 0, wx.ALL, 5)
        btn_sizer.Add(cancel_btn, 0, wx.ALL, 5)

        sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 5)

        # Set up scrolled panel
        panel.SetSizer(sizer)
        panel.FitInside()  # Tell the scrolled window the minimum size
        
        # Add the scrolled panel to the dialog
        dialog_sizer = wx.BoxSizer(wx.VERTICAL)
        dialog_sizer.Add(panel, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(dialog_sizer)

    def update_metadata_list(self):
        """Update the metadata list control."""

        self.metadata_list.DeleteAllItems()
        for i, (key, value) in enumerate(self.edge.metadata.items()):
            self.metadata_list.InsertItem(i, key)
            self.metadata_list.SetItem(i, 1, str(value))

    def on_line_color(self, event):
        """Handle line color button click."""

        color = wx.ColourDialog(self)
        if color.ShowModal() == wx.ID_OK:
            new_color = color.GetColourData().GetColour()
            self.line_color_btn.SetBackgroundColour(new_color)
        color.Destroy()

    def on_text_color(self, event):
        """Handle text color button click."""

        color = wx.ColourDialog(self)
        if color.ShowModal() == wx.ID_OK:
            new_color = color.GetColourData().GetColour()
            self.text_color_btn.SetBackgroundColour(new_color)
        color.Destroy()

    def on_add_metadata(self, event):
        """Add metadata entry."""

        dialog = MetadataDialog(self, "", "")
        if dialog.ShowModal() == wx.ID_OK:
            key, value = dialog.get_values()
            self.edge.set_metadata(key, value)
            self.update_metadata_list()
        dialog.Destroy()

    def on_edit_metadata(self, event):
        """Edit metadata entry."""

        selection = self.metadata_list.GetFirstSelected()
        if selection >= 0:
            key = self.metadata_list.GetItemText(selection, 0)
            value = self.metadata_list.GetItemText(selection, 1)

            dialog = MetadataDialog(self, key, value)
            if dialog.ShowModal() == wx.ID_OK:
                new_key, new_value = dialog.get_values()
                if new_key != key:
                    self.edge.remove_metadata(key)
                self.edge.set_metadata(new_key, new_value)
                self.update_metadata_list()
            dialog.Destroy()

    def on_remove_metadata(self, event):
        """Remove metadata entry."""

        selection = self.metadata_list.GetFirstSelected()
        if selection >= 0:
            key = self.metadata_list.GetItemText(selection, 0)
            self.edge.remove_metadata(key)
            self.update_metadata_list()

    def on_add_source(self, event):
        """Add a source node."""

        dialog = wx.TextEntryDialog(self, "Enter source node ID:", "Add Source Node")
        if dialog.ShowModal() == wx.ID_OK:
            node_id = dialog.GetValue()
            if node_id:
                self.source_list.InsertItem(self.source_list.GetItemCount(), node_id)
        dialog.Destroy()

    def on_remove_source(self, event):
        """Remove a source node."""

        selection = self.source_list.GetFirstSelected()
        if selection >= 0:
            self.source_list.DeleteItem(selection)

    def on_add_target(self, event):
        """Add a target node."""

        dialog = wx.TextEntryDialog(self, "Enter target node ID:", "Add Target Node")
        if dialog.ShowModal() == wx.ID_OK:
            node_id = dialog.GetValue()
            if node_id:
                self.target_list.InsertItem(self.target_list.GetItemCount(), node_id)
        dialog.Destroy()

    def on_remove_target(self, event):
        """Remove a target node."""

        selection = self.target_list.GetFirstSelected()
        if selection >= 0:
            self.target_list.DeleteItem(selection)

    def on_ok(self, event):
        """Handle OK button click."""

        # Apply changes
        self.edge.text = self.text_ctrl.GetValue()
        self.edge.width = self.width_ctrl.GetValue()
        self.edge.arrow_size = self.arrow_size_ctrl.GetValue()
        self.edge.font_size = self.font_size_ctrl.GetValue()
        self.edge.line_style = ["solid", "dashed",
                                "dotted"][self.style_choice.GetSelection()]
        self.edge.directed = self.directed_cb.GetValue()
        self.edge.visible = self.visible_cb.GetValue()
        self.edge.locked = self.locked_cb.GetValue()
        
        # Apply hyperedge properties
        self.edge.from_connection_point = self.from_connection_slider.GetValue() / 100.0
        self.edge.to_connection_point = self.to_connection_slider.GetValue() / 100.0
        
        # Apply arrow properties
        self.edge.arrow_position = self.arrow_position_slider.GetValue() / 100.0
        if hasattr(self, 'split_arrows_cb'):
            self.edge.split_arrows = self.split_arrows_cb.GetValue()
        
        # Apply hyperedge visualization
        if hasattr(self, 'viz_choice'):
            viz_map = {
                0: "lines",
                1: "curved_surface",
                2: "blob_boundary",
                3: "pie_chart",
                4: "polygon",
                5: "zykov",
                6: "radial",
                7: "paoh",
                8: "force_directed"
            }
            self.edge.hyperedge_visualization = viz_map.get(self.viz_choice.GetSelection(), "lines")
            # Force a refresh of the canvas
            try:
                parent = self.GetParent()
                if hasattr(parent, 'Refresh'):
                    wx.CallAfter(parent.Refresh)
                elif hasattr(parent, 'canvas') and hasattr(parent.canvas, 'Refresh'):
                    wx.CallAfter(parent.canvas.Refresh)
            except Exception:
                pass
        
        # Update source and target node lists
        source_ids = []
        for i in range(self.source_list.GetItemCount()):
            source_ids.append(self.source_list.GetItemText(i))
        self.edge.source_ids = source_ids
        self.edge.source_id = source_ids[0] if source_ids else None
        
        target_ids = []
        for i in range(self.target_list.GetItemCount()):
            target_ids.append(self.target_list.GetItemText(i))
        self.edge.target_ids = target_ids
        self.edge.target_id = target_ids[0] if target_ids else None
        
        # Update hyperedge/uberedge type from chooser
        try:
            sel = self.edge_type_choice.GetSelection()
            if sel == 2:  # uberedge
                self.edge.is_hyperedge = True
                self.edge.hyperedge_visualization = 'ubergraph'
                if not getattr(self.edge, 'hyperedge_view', None):
                    self.edge.hyperedge_view = 'standard'
            elif sel == 1:  # hyperedge
                self.edge.is_hyperedge = True
                if getattr(self.edge, 'hyperedge_visualization', None) == 'ubergraph':
                    self.edge.hyperedge_visualization = 'lines'
            else:  # standard
                # keep hyperedge only if multiple endpoints exist
                self.edge.is_hyperedge = len(source_ids) > 1 or len(target_ids) > 1
                if not self.edge.is_hyperedge:
                    self.edge.hyperedge_visualization = 'lines'
        except Exception:
            # Fallback to structure-based
            self.edge.is_hyperedge = len(source_ids) > 1 or len(target_ids) > 1

        # Apply colors
        self.edge.color = self.line_color_btn.GetBackgroundColour().Get()[:3]
        self.edge.text_color = self.text_color_btn.GetBackgroundColour().Get(
        )[:3]

        self.EndModal(wx.ID_OK)


class GraphPropertiesDialog(wx.Dialog):
    """Dialog for editing graph properties."""

    def __init__(self, parent, graph: m_graph.Graph):
        super().__init__(
            parent,
            title="Graph Properties",
            size=(400, 400),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX,
        )

        self.graph = graph
        self.setup_ui()

    def setup_ui(self):
        """Set up the dialog UI."""

        # Create scrolled panel for the main content
        panel = wx.ScrolledWindow(self, style=wx.VSCROLL)
        panel.SetScrollbars(0, 20, 0, 0)  # Only vertical scrolling, 20 pixels per unit
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Basic properties
        basic_box = wx.StaticBox(panel, label="Basic Properties")
        basic_sizer = wx.StaticBoxSizer(basic_box, wx.VERTICAL)

        # Name
        basic_sizer.Add(wx.StaticText(panel, label="Name:"), 0, wx.ALL, 5)
        self.name_ctrl = wx.TextCtrl(panel, value=self.graph.name)
        basic_sizer.Add(self.name_ctrl, 0, wx.EXPAND | wx.ALL, 5)

        # ID (read-only)
        basic_sizer.Add(wx.StaticText(panel, label="ID:"), 0, wx.ALL, 5)
        id_ctrl = wx.TextCtrl(panel, value=self.graph.id, style=wx.TE_READONLY)
        basic_sizer.Add(id_ctrl, 0, wx.EXPAND | wx.ALL, 5)

        sizer.Add(basic_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Visual properties
        visual_box = wx.StaticBox(panel, label="Visual Properties")
        visual_sizer = wx.StaticBoxSizer(visual_box, wx.VERTICAL)

        # Grid
        grid_sizer = wx.FlexGridSizer(2, 2, 5, 5)

        grid_sizer.Add(wx.StaticText(panel, label="Grid Size:"), 0,
                       wx.ALIGN_CENTER_VERTICAL)
        self.grid_size_ctrl = wx.SpinCtrl(panel,
                                          min=5,
                                          max=100)
        self.grid_size_ctrl.SetValue(self.graph.grid_size)
        grid_sizer.Add(self.grid_size_ctrl, 1, wx.EXPAND)

        visual_sizer.Add(grid_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Grid visibility
        self.grid_visible_cb = wx.CheckBox(panel, label="Show Grid")
        self.grid_visible_cb.SetValue(self.graph.grid_visible)
        visual_sizer.Add(self.grid_visible_cb, 0, wx.ALL, 5)

        # Colors
        color_sizer = wx.FlexGridSizer(2, 2, 5, 5)

        color_sizer.Add(wx.StaticText(panel, label="Background Color:"), 0,
                        wx.ALIGN_CENTER_VERTICAL)
        self.bg_color_btn = wx.Button(panel, label="Choose Color")
        self.bg_color_btn.SetBackgroundColour(
            wx.Colour(*self.graph.background_color))
        self.bg_color_btn.Bind(wx.EVT_BUTTON, self.on_bg_color)
        color_sizer.Add(self.bg_color_btn, 1, wx.EXPAND)

        color_sizer.Add(wx.StaticText(panel, label="Grid Color:"), 0,
                        wx.ALIGN_CENTER_VERTICAL)
        self.grid_color_btn = wx.Button(panel, label="Choose Color")
        self.grid_color_btn.SetBackgroundColour(
            wx.Colour(*self.graph.grid_color))
        self.grid_color_btn.Bind(wx.EVT_BUTTON, self.on_grid_color)
        color_sizer.Add(self.grid_color_btn, 1, wx.EXPAND)

        visual_sizer.Add(color_sizer, 0, wx.EXPAND | wx.ALL, 5)

        sizer.Add(visual_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Metadata
        metadata_box = wx.StaticBox(panel, label="Metadata")
        metadata_sizer = wx.StaticBoxSizer(metadata_box, wx.VERTICAL)

        self.metadata_list = wx.ListCtrl(panel,
                                         style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.metadata_list.AppendColumn("Key", width=150)
        self.metadata_list.AppendColumn("Value", width=200)
        self.update_metadata_list()
        metadata_sizer.Add(self.metadata_list, 1, wx.EXPAND | wx.ALL, 5)

        # Metadata buttons
        metadata_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        add_btn = wx.Button(panel, label="Add")
        add_btn.Bind(wx.EVT_BUTTON, self.on_add_metadata)
        edit_btn = wx.Button(panel, label="Edit")
        edit_btn.Bind(wx.EVT_BUTTON, self.on_edit_metadata)
        remove_btn = wx.Button(panel, label="Remove")
        remove_btn.Bind(wx.EVT_BUTTON, self.on_remove_metadata)

        metadata_btn_sizer.Add(add_btn, 0, wx.ALL, 5)
        metadata_btn_sizer.Add(edit_btn, 0, wx.ALL, 5)
        metadata_btn_sizer.Add(remove_btn, 0, wx.ALL, 5)

        metadata_sizer.Add(metadata_btn_sizer, 0, wx.EXPAND)

        sizer.Add(metadata_sizer, 1, wx.EXPAND | wx.ALL, 5)

        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_btn = wx.Button(panel, wx.ID_OK, "OK")
        ok_btn.Bind(wx.EVT_BUTTON, self.on_ok)
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")

        btn_sizer.Add(ok_btn, 0, wx.ALL, 5)
        btn_sizer.Add(cancel_btn, 0, wx.ALL, 5)

        sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 5)

        # Set up scrolled panel
        panel.SetSizer(sizer)
        panel.FitInside()  # Tell the scrolled window the minimum size
        
        # Add the scrolled panel to the dialog
        dialog_sizer = wx.BoxSizer(wx.VERTICAL)
        dialog_sizer.Add(panel, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(dialog_sizer)

    def update_metadata_list(self):
        """Update the metadata list control."""

        self.metadata_list.DeleteAllItems()
        for i, (key, value) in enumerate(self.graph.metadata.items()):
            self.metadata_list.InsertItem(i, key)
            self.metadata_list.SetItem(i, 1, str(value))

    def on_bg_color(self, event):
        """Handle background color button click."""

        color = wx.ColourDialog(self)
        if color.ShowModal() == wx.ID_OK:
            new_color = color.GetColourData().GetColour()
            self.bg_color_btn.SetBackgroundColour(new_color)
        color.Destroy()

    def on_grid_color(self, event):
        """Handle grid color button click."""

        color = wx.ColourDialog(self)
        if color.ShowModal() == wx.ID_OK:
            new_color = color.GetColourData().GetColour()
            self.grid_color_btn.SetBackgroundColour(new_color)
        color.Destroy()

    def on_add_metadata(self, event):
        """Add metadata entry."""

        dialog = MetadataDialog(self, "", "")
        if dialog.ShowModal() == wx.ID_OK:
            key, value = dialog.get_values()
            self.graph.set_metadata(key, value)
            self.update_metadata_list()
        dialog.Destroy()

    def on_edit_metadata(self, event):
        """Edit metadata entry."""

        selection = self.metadata_list.GetFirstSelected()
        if selection >= 0:
            key = self.metadata_list.GetItemText(selection, 0)
            value = self.metadata_list.GetItemText(selection, 1)

            dialog = MetadataDialog(self, key, value)
            if dialog.ShowModal() == wx.ID_OK:
                new_key, new_value = dialog.get_values()
                if new_key != key:
                    self.graph.remove_metadata(key)
                self.graph.set_metadata(new_key, new_value)
                self.update_metadata_list()
            dialog.Destroy()

    def on_remove_metadata(self, event):
        """Remove metadata entry."""

        selection = self.metadata_list.GetFirstSelected()
        if selection >= 0:
            key = self.metadata_list.GetItemText(selection, 0)
            self.graph.remove_metadata(key)
            self.update_metadata_list()

    def on_ok(self, event):
        """Handle OK button click."""

        # Apply changes
        self.graph.name = self.name_ctrl.GetValue()
        self.graph.grid_size = self.grid_size_ctrl.GetValue()
        self.graph.grid_visible = self.grid_visible_cb.GetValue()

        # Apply colors
        self.graph.background_color = self.bg_color_btn.GetBackgroundColour(
        ).Get()[:3]
        self.graph.grid_color = self.grid_color_btn.GetBackgroundColour().Get(
        )[:3]

        self.EndModal(wx.ID_OK)


class MetadataDialog(wx.Dialog):
    """Dialog for editing metadata key-value pairs."""

    def __init__(self, parent, key: str, value: str):
        super().__init__(parent, title="Edit Metadata", size=(300, 200))

        self.key = key
        self.value = value
        self.setup_ui()

    def setup_ui(self):
        """Set up the dialog UI."""

        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Key
        sizer.Add(wx.StaticText(panel, label="Key:"), 0, wx.ALL, 5)
        self.key_ctrl = wx.TextCtrl(panel, value=self.key)
        sizer.Add(self.key_ctrl, 0, wx.EXPAND | wx.ALL, 5)

        # Value
        sizer.Add(wx.StaticText(panel, label="Value:"), 0, wx.ALL, 5)
        self.value_ctrl = wx.TextCtrl(panel,
                                      value=self.value,
                                      style=wx.TE_MULTILINE)
        sizer.Add(self.value_ctrl, 1, wx.EXPAND | wx.ALL, 5)

        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_btn = wx.Button(panel, wx.ID_OK, "OK")
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")

        btn_sizer.Add(ok_btn, 0, wx.ALL, 5)
        btn_sizer.Add(cancel_btn, 0, wx.ALL, 5)

        sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 5)

        panel.SetSizer(sizer)

    def get_values(self):
        """Get the key and value from the dialog."""

        return self.key_ctrl.GetValue(), self.value_ctrl.GetValue()


class PreferencesDialog(wx.Dialog):
    """Dialog for editing application preferences."""
    
    def __init__(self, parent, undo_redo_manager):
        super().__init__(parent, title="Preferences", size=(400, 300))
        
        self.undo_redo_manager = undo_redo_manager
        
        # Create scrolled panel
        panel = wx.ScrolledWindow(self)
        panel.SetScrollbars(0, 20, 0, 0)
        
        # Main sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Undo/Redo settings
        undo_box = wx.StaticBox(panel, label="Undo/Redo Settings")
        undo_sizer = wx.StaticBoxSizer(undo_box, wx.VERTICAL)
        
        # History depth setting
        history_sizer = wx.BoxSizer(wx.HORIZONTAL)
        history_label = wx.StaticText(panel, label="History Depth:")
        self.history_spin = wx.SpinCtrl(panel, min=10, max=1000, initial=self.undo_redo_manager.get_max_history())
        history_sizer.Add(history_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        history_sizer.Add(self.history_spin, 0, wx.ALL, 5)
        
        history_help = wx.StaticText(panel, label="Number of operations to keep in undo history (10-1000)")
        history_help.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        
        undo_sizer.Add(history_sizer, 0, wx.EXPAND | wx.ALL, 5)
        undo_sizer.Add(history_help, 0, wx.EXPAND | wx.ALL, 5)
        
        sizer.Add(undo_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Button sizer
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        ok_btn = wx.Button(panel, wx.ID_OK, "OK")
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        
        btn_sizer.Add(ok_btn, 0, wx.ALL, 5)
        btn_sizer.Add(cancel_btn, 0, wx.ALL, 5)
        
        sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 10)
        
        panel.SetSizer(sizer)
        panel.FitInside()
        
        # Add the scrolled panel to the dialog
        dialog_sizer = wx.BoxSizer(wx.VERTICAL)
        dialog_sizer.Add(panel, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(dialog_sizer)
        
        # Bind events
        ok_btn.Bind(wx.EVT_BUTTON, self.on_ok)
        
    def on_ok(self, event):
        """Apply preferences and close dialog."""

        # Update undo history depth
        new_depth = self.history_spin.GetValue()
        self.undo_redo_manager.set_max_history(new_depth)
        print(f"DEBUG: Set undo history depth to {new_depth}")
        
        self.EndModal(wx.ID_OK)
