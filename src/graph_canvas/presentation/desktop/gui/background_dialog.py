"""
Dialog for managing canvas background layers.
"""

import wx
import os
from typing import Optional
from graph_canvas.presentation.desktop.models.background_layer import BackgroundLayer, BackgroundMode, ImagePosition


class BackgroundDialog(wx.Dialog):
    """Dialog for managing background layers."""
    
    def __init__(self, parent, background_manager):
        super().__init__(parent, title="Background Layers", size=(600, 400),
                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)
        self.background_manager = background_manager
        self.selected_layer: Optional[BackgroundLayer] = None
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dialog UI."""
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Left side - layer list
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Layer list
        self.layer_list = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.layer_list.InsertColumn(0, "Layer Name")
        self.layer_list.InsertColumn(1, "Mode")
        self.layer_list.InsertColumn(2, "Visible")
        self.layer_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_layer_selected)
        left_sizer.Add(self.layer_list, 1, wx.EXPAND | wx.ALL, 5)
        
        # Layer buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        add_btn = wx.Button(self, label="Add Layer")
        add_btn.Bind(wx.EVT_BUTTON, self.on_add_layer)
        remove_btn = wx.Button(self, label="Remove Layer")
        remove_btn.Bind(wx.EVT_BUTTON, self.on_remove_layer)
        move_up_btn = wx.Button(self, label="Move Up")
        move_up_btn.Bind(wx.EVT_BUTTON, self.on_move_up)
        move_down_btn = wx.Button(self, label="Move Down")
        move_down_btn.Bind(wx.EVT_BUTTON, self.on_move_down)
        
        button_sizer.Add(add_btn, 0, wx.RIGHT, 5)
        button_sizer.Add(remove_btn, 0, wx.RIGHT, 5)
        button_sizer.Add(move_up_btn, 0, wx.RIGHT, 5)
        button_sizer.Add(move_down_btn, 0)
        left_sizer.Add(button_sizer, 0, wx.ALL, 5)
        
        main_sizer.Add(left_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Right side - layer properties
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Layer name
        name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        name_label = wx.StaticText(self, label="Name:")
        self.name_field = wx.TextCtrl(self)
        self.name_field.Bind(wx.EVT_TEXT, self.on_name_changed)
        name_sizer.Add(name_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        name_sizer.Add(self.name_field, 1)
        right_sizer.Add(name_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Layer visibility, opacity, and position
        vis_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Visibility checkbox
        self.visible_cb = wx.CheckBox(self, label="Visible")
        self.visible_cb.Bind(wx.EVT_CHECKBOX, self.on_visible_changed)
        vis_sizer.Add(self.visible_cb, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        
        # Fixed position controls
        fixed_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Fixed position checkbox and options
        fixed_top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.fixed_cb = wx.CheckBox(self, label="Fixed Position")
        self.fixed_cb.SetToolTip("When checked, the background stays fixed in screen space instead of moving with the world")
        self.fixed_cb.Bind(wx.EVT_CHECKBOX, self.on_fixed_changed)
        fixed_top_sizer.Add(self.fixed_cb, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        
        self.follow_rotation_cb = wx.CheckBox(self, label="Follow Rotation")
        self.follow_rotation_cb.SetToolTip("When checked, the background rotates with the world")
        self.follow_rotation_cb.Bind(wx.EVT_CHECKBOX, self.on_follow_rotation_changed)
        fixed_top_sizer.Add(self.follow_rotation_cb, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        
        self.world_pos_cb = wx.CheckBox(self, label="Use World Position")
        self.world_pos_cb.SetToolTip("When checked, positions are in world coordinates instead of screen coordinates")
        self.world_pos_cb.Bind(wx.EVT_CHECKBOX, self.on_world_pos_changed)
        fixed_top_sizer.Add(self.world_pos_cb, 0, wx.ALIGN_CENTER_VERTICAL)
        
        fixed_sizer.Add(fixed_top_sizer, 0, wx.EXPAND)
        
        # Fixed size controls
        fixed_size_sizer = wx.BoxSizer(wx.HORIZONTAL)
        width_label = wx.StaticText(self, label="Width:")
        self.width_ctrl = wx.SpinCtrl(self, min=-1, max=10000, initial=-1)
        self.width_ctrl.SetToolTip("Fixed width in pixels (-1 = auto)")
        self.width_ctrl.Bind(wx.EVT_SPINCTRL, self.on_fixed_size_changed)
        height_label = wx.StaticText(self, label="Height:")
        self.height_ctrl = wx.SpinCtrl(self, min=-1, max=10000, initial=-1)
        self.height_ctrl.SetToolTip("Fixed height in pixels (-1 = auto)")
        self.height_ctrl.Bind(wx.EVT_SPINCTRL, self.on_fixed_size_changed)
        
        fixed_size_sizer.Add(width_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        fixed_size_sizer.Add(self.width_ctrl, 0, wx.RIGHT, 10)
        fixed_size_sizer.Add(height_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        fixed_size_sizer.Add(self.height_ctrl, 0)
        fixed_sizer.Add(fixed_size_sizer, 0, wx.TOP, 5)
        
        vis_sizer.Add(fixed_sizer, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        
        # Opacity slider
        opacity_label = wx.StaticText(self, label="Opacity:")
        self.opacity_slider = wx.Slider(self, value=100, minValue=0, maxValue=100)
        self.opacity_slider.Bind(wx.EVT_SLIDER, self.on_opacity_changed)
        vis_sizer.Add(opacity_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        vis_sizer.Add(self.opacity_slider, 1)
        right_sizer.Add(vis_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Image selection
        img_sizer = wx.BoxSizer(wx.HORIZONTAL)
        img_label = wx.StaticText(self, label="Image:")
        self.img_path = wx.TextCtrl(self, style=wx.TE_READONLY)
        browse_btn = wx.Button(self, label="Browse...")
        browse_btn.Bind(wx.EVT_BUTTON, self.on_browse_image)
        img_sizer.Add(img_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        img_sizer.Add(self.img_path, 1, wx.RIGHT, 5)
        img_sizer.Add(browse_btn, 0)
        right_sizer.Add(img_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Display mode
        mode_sizer = wx.BoxSizer(wx.HORIZONTAL)
        mode_label = wx.StaticText(self, label="Display Mode:")
        self.mode_choice = wx.Choice(self, choices=["Single", "Tiled", "Positioned"])
        self.mode_choice.Bind(wx.EVT_CHOICE, self.on_mode_changed)
        mode_sizer.Add(mode_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        mode_sizer.Add(self.mode_choice, 1)
        right_sizer.Add(mode_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Single mode options
        self.single_panel = wx.Panel(self)
        single_sizer = wx.BoxSizer(wx.VERTICAL)
        self.stretch_cb = wx.CheckBox(self.single_panel, label="Stretch to Fill")
        self.stretch_cb.Bind(wx.EVT_CHECKBOX, self.on_stretch_changed)
        self.aspect_cb = wx.CheckBox(self.single_panel, label="Maintain Aspect Ratio")
        self.aspect_cb.Bind(wx.EVT_CHECKBOX, self.on_aspect_changed)
        single_sizer.Add(self.stretch_cb, 0, wx.ALL, 5)
        single_sizer.Add(self.aspect_cb, 0, wx.ALL, 5)
        self.single_panel.SetSizer(single_sizer)
        right_sizer.Add(self.single_panel, 0, wx.EXPAND | wx.ALL, 5)
        
        # Tiled mode options
        self.tiled_panel = wx.Panel(self)
        tiled_sizer = wx.BoxSizer(wx.VERTICAL)
        spacing_sizer = wx.BoxSizer(wx.HORIZONTAL)
        x_label = wx.StaticText(self.tiled_panel, label="X Spacing:")
        self.x_spacing = wx.SpinCtrlDouble(self.tiled_panel, wx.ID_ANY, "0", min=0, max=1000, inc=10)
        self.x_spacing.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_spacing_changed)
        y_label = wx.StaticText(self.tiled_panel, label="Y Spacing:")
        self.y_spacing = wx.SpinCtrlDouble(self.tiled_panel, wx.ID_ANY, "0", min=0, max=1000, inc=10)
        self.y_spacing.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_spacing_changed)
        spacing_sizer.Add(x_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        spacing_sizer.Add(self.x_spacing, 1, wx.RIGHT, 10)
        spacing_sizer.Add(y_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        spacing_sizer.Add(self.y_spacing, 1)
        tiled_sizer.Add(spacing_sizer, 0, wx.EXPAND | wx.ALL, 5)
        self.tiled_panel.SetSizer(tiled_sizer)
        right_sizer.Add(self.tiled_panel, 0, wx.EXPAND | wx.ALL, 5)
        
        # Positioned mode options
        self.positioned_panel = wx.Panel(self)
        positioned_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Position list
        self.position_list = wx.ListCtrl(self.positioned_panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.position_list.InsertColumn(0, "X")
        self.position_list.InsertColumn(1, "Y")
        self.position_list.InsertColumn(2, "Scale")
        self.position_list.InsertColumn(3, "Rotation")
        self.position_list.InsertColumn(4, "Opacity")
        positioned_sizer.Add(self.position_list, 1, wx.EXPAND | wx.ALL, 5)
        
        # Position buttons
        pos_button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        add_pos_btn = wx.Button(self.positioned_panel, label="Add Position")
        add_pos_btn.Bind(wx.EVT_BUTTON, self.on_add_position)
        edit_pos_btn = wx.Button(self.positioned_panel, label="Edit Position")
        edit_pos_btn.Bind(wx.EVT_BUTTON, self.on_edit_position)
        remove_pos_btn = wx.Button(self.positioned_panel, label="Remove Position")
        remove_pos_btn.Bind(wx.EVT_BUTTON, self.on_remove_position)
        pos_button_sizer.Add(add_pos_btn, 0, wx.RIGHT, 5)
        pos_button_sizer.Add(edit_pos_btn, 0, wx.RIGHT, 5)
        pos_button_sizer.Add(remove_pos_btn, 0)
        positioned_sizer.Add(pos_button_sizer, 0, wx.ALL, 5)
        
        self.positioned_panel.SetSizer(positioned_sizer)
        right_sizer.Add(self.positioned_panel, 1, wx.EXPAND | wx.ALL, 5)
        
        main_sizer.Add(right_sizer, 1, wx.EXPAND | wx.ALL, 5)
        
        # OK/Cancel buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_button = wx.Button(self, wx.ID_OK, "OK")
        cancel_button = wx.Button(self, wx.ID_CANCEL, "Cancel")
        button_sizer.Add(ok_button, 0, wx.RIGHT, 5)
        button_sizer.Add(cancel_button, 0)
        right_sizer.Add(button_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 5)
        
        self.SetSizer(main_sizer)
        
        # Initial state
        self.update_layer_list()
        self.update_mode_panels()
        
    def update_layer_list(self):
        """Update the layer list display."""
        self.layer_list.DeleteAllItems()
        for layer in self.background_manager.layers:
            index = self.layer_list.GetItemCount()
            self.layer_list.InsertItem(index, layer.name)
            self.layer_list.SetItem(index, 1, layer.mode.value)
            self.layer_list.SetItem(index, 2, "Yes" if layer.visible else "No")
            
    def update_mode_panels(self):
        """Show/hide mode-specific panels based on selected mode."""
        mode = self.mode_choice.GetSelection()
        self.single_panel.Show(mode == 0)
        self.tiled_panel.Show(mode == 1)
        self.positioned_panel.Show(mode == 2)
        self.Layout()
        
    def update_position_list(self):
        """Update the position list for positioned mode."""
        self.position_list.DeleteAllItems()
        if not self.selected_layer or not self.selected_layer.positions:
            return
            
        for pos in self.selected_layer.positions:
            index = self.position_list.GetItemCount()
            self.position_list.InsertItem(index, f"{pos.x:.1f}")
            self.position_list.SetItem(index, 1, f"{pos.y:.1f}")
            self.position_list.SetItem(index, 2, f"{pos.scale:.2f}")
            self.position_list.SetItem(index, 3, f"{pos.rotation:.1f}")
            self.position_list.SetItem(index, 4, f"{pos.opacity:.2f}")
            
    def on_layer_selected(self, event):
        """Handle layer selection."""
        index = event.GetIndex()
        self.selected_layer = self.background_manager.layers[index]
        
        # Update UI
        self.name_field.SetValue(self.selected_layer.name)
        self.visible_cb.SetValue(self.selected_layer.visible)
        self.fixed_cb.SetValue(self.selected_layer.fixed_position)
        self.follow_rotation_cb.SetValue(self.selected_layer.follow_rotation)
        self.world_pos_cb.SetValue(self.selected_layer.use_world_position)
        self.width_ctrl.SetValue(-1 if self.selected_layer.fixed_width is None else self.selected_layer.fixed_width)
        self.height_ctrl.SetValue(-1 if self.selected_layer.fixed_height is None else self.selected_layer.fixed_height)
        self.opacity_slider.SetValue(int(self.selected_layer.opacity * 100))
        self.img_path.SetValue(self.selected_layer.image_path or "")
        
        mode_map = {
            BackgroundMode.SINGLE: 0,
            BackgroundMode.TILED: 1,
            BackgroundMode.POSITIONED: 2
        }
        self.mode_choice.SetSelection(mode_map[self.selected_layer.mode])
        
        # Update mode-specific controls
        self.stretch_cb.SetValue(self.selected_layer.stretch)
        self.aspect_cb.SetValue(self.selected_layer.maintain_aspect)
        self.x_spacing.SetValue(self.selected_layer.tile_spacing[0])
        self.y_spacing.SetValue(self.selected_layer.tile_spacing[1])
        self.update_position_list()
        
        self.update_mode_panels()
        
    def on_add_layer(self, event):
        """Add a new layer."""
        layer = self.background_manager.add_layer()
        self.update_layer_list()
        # Select the new layer
        self.layer_list.Select(len(self.background_manager.layers) - 1)
        try:
            # Notify MVU to refresh (bg_seq bump)
            main_window = self.GetParent()
            if hasattr(main_window, 'mvu_adapter'):
                from mvc_mvu.messages import make_message
                import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
                main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.BG_UPDATE))
        except Exception:
            pass
        
    def on_remove_layer(self, event):
        """Remove the selected layer."""
        if self.selected_layer:
            self.background_manager.remove_layer(self.selected_layer)
            self.update_layer_list()
            self.selected_layer = None
            try:
                main_window = self.GetParent()
                if hasattr(main_window, 'mvu_adapter'):
                    from mvc_mvu.messages import make_message
                    import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
                    main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.BG_UPDATE))
            except Exception:
                pass
            
    def on_move_up(self, event):
        """Move selected layer up in z-order."""
        if self.selected_layer:
            index = self.background_manager.layers.index(self.selected_layer)
            if index > 0:
                self.background_manager.move_layer(self.selected_layer, index - 1)
                self.update_layer_list()
                self.layer_list.Select(index - 1)
                try:
                    main_window = self.GetParent()
                    if hasattr(main_window, 'mvu_adapter'):
                        from mvc_mvu.messages import make_message
                        import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
                        main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.BG_UPDATE))
                except Exception:
                    pass
                
    def on_move_down(self, event):
        """Move selected layer down in z-order."""
        if self.selected_layer:
            index = self.background_manager.layers.index(self.selected_layer)
            if index < len(self.background_manager.layers) - 1:
                self.background_manager.move_layer(self.selected_layer, index + 1)
                self.update_layer_list()
                self.layer_list.Select(index + 1)
                try:
                    main_window = self.GetParent()
                    if hasattr(main_window, 'mvu_adapter'):
                        from mvc_mvu.messages import make_message
                        import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
                        main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.BG_UPDATE))
                except Exception:
                    pass
                
    def on_name_changed(self, event):
        """Handle layer name change."""
        if self.selected_layer:
            self.selected_layer.name = self.name_field.GetValue()
            self.update_layer_list()
            
    def on_visible_changed(self, event):
        """Handle layer visibility toggle."""
        if self.selected_layer:
            self.selected_layer.visible = self.visible_cb.GetValue()
            self.update_layer_list()
            
    def on_fixed_changed(self, event):
        """Handle fixed position toggle."""
        if self.selected_layer:
            is_fixed = self.fixed_cb.GetValue()
            self.selected_layer.fixed_position = is_fixed
            self.width_ctrl.Enable(is_fixed)
            self.height_ctrl.Enable(is_fixed)
            self.follow_rotation_cb.Enable(is_fixed)
            self.world_pos_cb.Enable(is_fixed)
            self.background_manager.canvas.Refresh()
            try:
                main_window = self.GetParent()
                if hasattr(main_window, 'mvu_adapter'):
                    from mvc_mvu.messages import make_message
                    import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
                    main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.BG_UPDATE))
            except Exception:
                pass
            
    def on_follow_rotation_changed(self, event):
        """Handle follow rotation toggle."""
        if self.selected_layer:
            self.selected_layer.follow_rotation = self.follow_rotation_cb.GetValue()
            self.background_manager.canvas.Refresh()
            try:
                main_window = self.GetParent()
                if hasattr(main_window, 'mvu_adapter'):
                    from mvc_mvu.messages import make_message
                    import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
                    main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.BG_UPDATE))
            except Exception:
                pass
            
    def on_world_pos_changed(self, event):
        """Handle world position toggle."""
        if self.selected_layer:
            self.selected_layer.use_world_position = self.world_pos_cb.GetValue()
            self.background_manager.canvas.Refresh()
            try:
                main_window = self.GetParent()
                if hasattr(main_window, 'mvu_adapter'):
                    from mvc_mvu.messages import make_message
                    import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
                    main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.BG_UPDATE))
            except Exception:
                pass
            
    def on_fixed_size_changed(self, event):
        """Handle fixed size change."""
        if self.selected_layer:
            width = self.width_ctrl.GetValue()
            height = self.height_ctrl.GetValue()
            self.selected_layer.fixed_width = None if width == -1 else width
            self.selected_layer.fixed_height = None if height == -1 else height
            self.background_manager.canvas.Refresh()
            try:
                main_window = self.GetParent()
                if hasattr(main_window, 'mvu_adapter'):
                    from mvc_mvu.messages import make_message
                    import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
                    main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.BG_UPDATE))
            except Exception:
                pass
            
    def on_opacity_changed(self, event):
        """Handle layer opacity change."""
        if self.selected_layer:
            self.selected_layer.opacity = self.opacity_slider.GetValue() / 100.0
            try:
                main_window = self.GetParent()
                if hasattr(main_window, 'mvu_adapter'):
                    from mvc_mvu.messages import make_message
                    import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
                    main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.BG_UPDATE))
            except Exception:
                pass
            
    def on_browse_image(self, event):
        """Handle image file selection."""
        if not self.selected_layer:
            return
            
        with wx.FileDialog(self, "Choose an image file",
                          wildcard="Image files (*.png;*.jpg;*.jpeg;*.bmp)|*.png;*.jpg;*.jpeg;*.bmp",
                          style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dialog:
            if dialog.ShowModal() == wx.ID_CANCEL:
                return
                
            path = dialog.GetPath()
            try:
                main_window = self.GetParent()
                if hasattr(main_window, 'mvu_adapter'):
                    # Dispatch async image load to MVU
                    index = self.background_manager.layers.index(self.selected_layer) if self.selected_layer in self.background_manager.layers else -1
                    if index >= 0:
                        from mvc_mvu.messages import make_message
                        import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
                        main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.BG_LOAD_IMAGE, index=index, path=path))
                        self.img_path.SetValue(path)
                        return
            except Exception:
                pass
            # Fallback: direct load
            if self.selected_layer.load_image(path):
                self.img_path.SetValue(path)
                
    def on_mode_changed(self, event):
        """Handle display mode change."""
        if not self.selected_layer:
            return
            
        mode_map = {
            0: BackgroundMode.SINGLE,
            1: BackgroundMode.TILED,
            2: BackgroundMode.POSITIONED
        }
        self.selected_layer.mode = mode_map[self.mode_choice.GetSelection()]
        self.update_layer_list()
        self.update_mode_panels()
        try:
            main_window = self.GetParent()
            if hasattr(main_window, 'mvu_adapter'):
                from mvc_mvu.messages import make_message
                import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
                main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.BG_UPDATE))
        except Exception:
            pass
        
    def on_stretch_changed(self, event):
        """Handle stretch toggle."""
        if self.selected_layer:
            self.selected_layer.stretch = self.stretch_cb.GetValue()
            try:
                main_window = self.GetParent()
                if hasattr(main_window, 'mvu_adapter'):
                    from mvc_mvu.messages import make_message
                    import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
                    main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.BG_UPDATE))
            except Exception:
                pass
            
    def on_aspect_changed(self, event):
        """Handle aspect ratio toggle."""
        if self.selected_layer:
            self.selected_layer.maintain_aspect = self.aspect_cb.GetValue()
            try:
                main_window = self.GetParent()
                if hasattr(main_window, 'mvu_adapter'):
                    from mvc_mvu.messages import make_message
                    import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
                    main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.BG_UPDATE))
            except Exception:
                pass
            
    def on_spacing_changed(self, event):
        """Handle tile spacing change."""
        if self.selected_layer:
            self.selected_layer.set_tile_spacing(
                self.x_spacing.GetValue(),
                self.y_spacing.GetValue()
            )
            try:
                main_window = self.GetParent()
                if hasattr(main_window, 'mvu_adapter'):
                    from mvc_mvu.messages import make_message
                    import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
                    main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.BG_UPDATE))
            except Exception:
                pass
            
    def on_add_position(self, event):
        """Add a new image position."""
        if not self.selected_layer:
            return
            
        dialog = wx.Dialog(self, title="Add Image Position",
                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Position controls
        grid = wx.FlexGridSizer(5, 2, 5, 5)
        
        x_label = wx.StaticText(dialog, label="X:")
        x_ctrl = wx.SpinCtrlDouble(dialog, wx.ID_ANY, "", min=-10000, max=10000, inc=10)
        y_label = wx.StaticText(dialog, label="Y:")
        y_ctrl = wx.SpinCtrlDouble(dialog, wx.ID_ANY, "", min=-10000, max=10000, inc=10)
        scale_label = wx.StaticText(dialog, label="Scale:")
        scale_ctrl = wx.SpinCtrlDouble(dialog, wx.ID_ANY, "1.0", min=0.1, max=10, inc=0.1)
        rotation_label = wx.StaticText(dialog, label="Rotation:")
        rotation_ctrl = wx.SpinCtrlDouble(dialog, wx.ID_ANY, "", min=-360, max=360, inc=15)
        opacity_label = wx.StaticText(dialog, label="Opacity:")
        opacity_ctrl = wx.SpinCtrlDouble(dialog, wx.ID_ANY, "1.0", min=0, max=1, inc=0.1)
        
        grid.AddMany([
            (x_label, 0, wx.ALIGN_CENTER_VERTICAL),
            (x_ctrl, 1, wx.EXPAND),
            (y_label, 0, wx.ALIGN_CENTER_VERTICAL),
            (y_ctrl, 1, wx.EXPAND),
            (scale_label, 0, wx.ALIGN_CENTER_VERTICAL),
            (scale_ctrl, 1, wx.EXPAND),
            (rotation_label, 0, wx.ALIGN_CENTER_VERTICAL),
            (rotation_ctrl, 1, wx.EXPAND),
            (opacity_label, 0, wx.ALIGN_CENTER_VERTICAL),
            (opacity_ctrl, 1, wx.EXPAND)
        ])
        
        sizer.Add(grid, 0, wx.EXPAND | wx.ALL, 10)
        
        # OK/Cancel buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_button = wx.Button(dialog, wx.ID_OK, "OK")
        cancel_button = wx.Button(dialog, wx.ID_CANCEL, "Cancel")
        button_sizer.Add(ok_button, 0, wx.RIGHT, 5)
        button_sizer.Add(cancel_button, 0)
        sizer.Add(button_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 10)
        
        dialog.SetSizer(sizer)
        dialog.Fit()
        
        try:
            if dialog.ShowModal() == wx.ID_OK:
                self.selected_layer.add_position(
                    x_ctrl.GetValue(),
                    y_ctrl.GetValue(),
                    scale_ctrl.GetValue(),
                    rotation_ctrl.GetValue(),
                    opacity_ctrl.GetValue()
                )
                self.update_position_list()
        finally:
            dialog.Destroy()
                
    def on_edit_position(self, event):
        """Edit the selected image position."""
        if not self.selected_layer or self.position_list.GetSelectedItemCount() == 0:
            return
            
        index = self.position_list.GetFirstSelected()
        pos = self.selected_layer.positions[index]
        
        dialog = wx.Dialog(self, title="Edit Image Position",
                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Position controls
        grid = wx.FlexGridSizer(5, 2, 5, 5)
        
        x_label = wx.StaticText(dialog, label="X:")
        x_ctrl = wx.SpinCtrlDouble(dialog, wx.ID_ANY, str(pos.x), min=-10000, max=10000, inc=10)
        y_label = wx.StaticText(dialog, label="Y:")
        y_ctrl = wx.SpinCtrlDouble(dialog, wx.ID_ANY, str(pos.y), min=-10000, max=10000, inc=10)
        scale_label = wx.StaticText(dialog, label="Scale:")
        scale_ctrl = wx.SpinCtrlDouble(dialog, wx.ID_ANY, str(pos.scale), min=0.1, max=10, inc=0.1)
        rotation_label = wx.StaticText(dialog, label="Rotation:")
        rotation_ctrl = wx.SpinCtrlDouble(dialog, wx.ID_ANY, str(pos.rotation), min=-360, max=360, inc=15)
        opacity_label = wx.StaticText(dialog, label="Opacity:")
        opacity_ctrl = wx.SpinCtrlDouble(dialog, wx.ID_ANY, str(pos.opacity), min=0, max=1, inc=0.1)
        
        grid.AddMany([
            (x_label, 0, wx.ALIGN_CENTER_VERTICAL),
            (x_ctrl, 1, wx.EXPAND),
            (y_label, 0, wx.ALIGN_CENTER_VERTICAL),
            (y_ctrl, 1, wx.EXPAND),
            (scale_label, 0, wx.ALIGN_CENTER_VERTICAL),
            (scale_ctrl, 1, wx.EXPAND),
            (rotation_label, 0, wx.ALIGN_CENTER_VERTICAL),
            (rotation_ctrl, 1, wx.EXPAND),
            (opacity_label, 0, wx.ALIGN_CENTER_VERTICAL),
            (opacity_ctrl, 1, wx.EXPAND)
        ])
        
        sizer.Add(grid, 0, wx.EXPAND | wx.ALL, 10)
        
        # OK/Cancel buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_button = wx.Button(dialog, wx.ID_OK, "OK")
        cancel_button = wx.Button(dialog, wx.ID_CANCEL, "Cancel")
        button_sizer.Add(ok_button, 0, wx.RIGHT, 5)
        button_sizer.Add(cancel_button, 0)
        sizer.Add(button_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 10)
        
        dialog.SetSizer(sizer)
        dialog.Fit()
        
        try:
            if dialog.ShowModal() == wx.ID_OK:
                pos.x = x_ctrl.GetValue()
                pos.y = y_ctrl.GetValue()
                pos.scale = scale_ctrl.GetValue()
                pos.rotation = rotation_ctrl.GetValue()
                pos.opacity = opacity_ctrl.GetValue()
                self.update_position_list()
        finally:
            dialog.Destroy()
                
    def on_remove_position(self, event):
        """Remove the selected image position."""
        if not self.selected_layer or self.position_list.GetSelectedItemCount() == 0:
            return
            
        index = self.position_list.GetFirstSelected()
        pos = self.selected_layer.positions[index]
        self.selected_layer.remove_position(pos)
        self.update_position_list()
