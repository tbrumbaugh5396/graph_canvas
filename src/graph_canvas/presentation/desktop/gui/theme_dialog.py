"""
Theme creation and editing dialog.
"""


import wx
from typing import Optional

import graph_canvas.presentation.desktop.utils.managers.theme_manager as m_theme_manager


class ThemeDialog(wx.Dialog):
    """Dialog for creating and editing custom themes."""
    
    def __init__(self, parent, theme_manager: m_theme_manager.ThemeManager, theme: Optional[m_theme_manager.Theme] = None, is_template: bool = False):
        title = "Create New Theme" if is_template else ("Edit Theme" if theme else "Create New Theme")
        super().__init__(parent, title=title, size=(500, 600),
                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)
        
        self.theme_manager = theme_manager
        self.original_theme = theme
        self.is_editing = theme is not None and not is_template
        self.is_template = is_template
        
        self.setup_ui()
        
        if theme:
            self.load_theme_values(theme)
            if is_template:
                self.name_ctrl.SetValue("")  # Clear name when using as template
    
    def setup_ui(self):
        """Set up the dialog UI."""

        panel = wx.ScrolledWindow(self, style=wx.VSCROLL)
        panel.SetScrollbars(0, 20, 0, 0)
        
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Theme name
        name_box = wx.StaticBox(panel, label="Theme Information")
        name_sizer = wx.StaticBoxSizer(name_box, wx.VERTICAL)
        
        name_sizer.Add(wx.StaticText(panel, label="Theme Name:"), 0, wx.ALL, 5)
        self.name_ctrl = wx.TextCtrl(panel, value="")
        name_sizer.Add(self.name_ctrl, 0, wx.EXPAND | wx.ALL, 5)
        
        # Theme options
        self.is_dark_cb = wx.CheckBox(panel, label="Dark Theme")
        name_sizer.Add(self.is_dark_cb, 0, wx.ALL, 5)
        
        main_sizer.Add(name_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Color settings
        colors_box = wx.StaticBox(panel, label="Colors")
        colors_sizer = wx.StaticBoxSizer(colors_box, wx.VERTICAL)
        
        # Create color pickers for all theme colors
        self.color_controls = {}
        color_definitions = [
            ("background", "Main Background"),
            ("panel_background", "Panel Background"),
            ("text_foreground", "Text Color"),
            ("text_background", "Text Input Background"),
            ("button_background", "Button Background"),
            ("button_foreground", "Button Text"),
            ("expandable_panel_background", "Expandable Panel Background"),
            ("expandable_panel_foreground", "Expandable Panel Text"),
            ("selectable_background", "Selectable Item Background"),
            ("selectable_foreground", "Selectable Item Text"),
            ("selectable_hover_background", "Selectable Item Hover Background"),
            ("selectable_hover_foreground", "Selectable Item Hover Text"),
            ("toggle_background", "Toggle Control Background"),
            ("toggle_foreground", "Toggle Control Text"),
            ("toggle_checked_background", "Toggle Control Checked Background"),
            ("toggle_checked_foreground", "Toggle Control Checked Text"),
            ("border_color", "Border Color"),
            ("accent_color", "Accent Color"),
            ("selection_color", "Selection Color"),
            ("disabled_color", "Disabled Color"),
            ("error_color", "Error Color"),
            ("success_color", "Success Color"),
            ("warning_color", "Warning Color"),
            ("dialog_background", "Dialog Background"),
            ("menu_background", "Menu Background"),
            ("menu_foreground", "Menu Text"),
            ("status_background", "Status Bar Background"),
            ("status_foreground", "Status Bar Text"),
        ]
        
        # Create flex grid without specifying rows/cols
        color_grid = wx.FlexGridSizer(cols=2, vgap=5, hgap=5)  # Only specify columns
        color_grid.AddGrowableCol(1)
        
        for color_key, color_label in color_definitions:
            label = wx.StaticText(panel, label=color_label + ":")
            color_picker = wx.ColourPickerCtrl(panel, colour=wx.Colour("#FFFFFF"))
            
            color_grid.Add(label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 2)
            color_grid.Add(color_picker, 1, wx.EXPAND | wx.ALL, 2)
            
            self.color_controls[color_key] = color_picker
        
        colors_sizer.Add(color_grid, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(colors_sizer, 1, wx.EXPAND | wx.ALL, 10)
        
        # Preview section
        preview_box = wx.StaticBox(panel, label="Preview")
        preview_sizer = wx.StaticBoxSizer(preview_box, wx.VERTICAL)
        
        preview_panel = wx.Panel(panel, size=(400, 100))
        preview_panel.SetBackgroundColour(wx.Colour("#FFFFFF"))
        
        # Add some preview controls
        preview_panel_sizer = wx.BoxSizer(wx.VERTICAL)
        preview_text = wx.StaticText(preview_panel, label="Sample text")
        preview_button = wx.Button(preview_panel, label="Sample Button")
        preview_textctrl = wx.TextCtrl(preview_panel, value="Sample input text")
        
        preview_panel_sizer.Add(preview_text, 0, wx.ALL, 5)
        preview_panel_sizer.Add(preview_button, 0, wx.ALL, 5)
        preview_panel_sizer.Add(preview_textctrl, 0, wx.EXPAND | wx.ALL, 5)
        preview_panel.SetSizer(preview_panel_sizer)
        
        self.preview_panel = preview_panel
        self.preview_text = preview_text
        self.preview_button = preview_button
        self.preview_textctrl = preview_textctrl
        
        preview_sizer.Add(preview_panel, 1, wx.EXPAND | wx.ALL, 5)
        
        # Preview update button
        preview_btn = wx.Button(panel, label="Update Preview")
        preview_btn.Bind(wx.EVT_BUTTON, self.on_update_preview)
        preview_sizer.Add(preview_btn, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        
        main_sizer.Add(preview_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # Action buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Preset buttons for quick setup
        if not self.is_editing:
            presets_sizer = wx.BoxSizer(wx.VERTICAL)
            presets_label = wx.StaticText(panel, label="Quick Setup:")
            presets_sizer.Add(presets_label, 0, wx.ALL, 2)
            
            preset_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
            light_preset_btn = wx.Button(panel, label="Light Base", size=(80, -1))
            dark_preset_btn = wx.Button(panel, label="Dark Base", size=(80, -1))
            
            light_preset_btn.Bind(wx.EVT_BUTTON, self.on_light_preset)
            dark_preset_btn.Bind(wx.EVT_BUTTON, self.on_dark_preset)
            
            preset_btn_sizer.Add(light_preset_btn, 0, wx.ALL, 2)
            preset_btn_sizer.Add(dark_preset_btn, 0, wx.ALL, 2)
            
            presets_sizer.Add(preset_btn_sizer, 0, wx.ALL, 2)
            btn_sizer.Add(presets_sizer, 0, wx.ALL, 5)
        
        btn_sizer.AddStretchSpacer()
        
        ok_btn = wx.Button(panel, wx.ID_OK, "Save Theme")
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        
        btn_sizer.Add(ok_btn, 0, wx.ALL, 5)
        btn_sizer.Add(cancel_btn, 0, wx.ALL, 5)
        
        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(main_sizer)
        panel.FitInside()
        
        # Add the scrolled panel to the dialog
        dialog_sizer = wx.BoxSizer(wx.VERTICAL)
        dialog_sizer.Add(panel, 1, wx.EXPAND)
        self.SetSizer(dialog_sizer)
        
        # Bind events
        ok_btn.Bind(wx.EVT_BUTTON, self.on_ok)
        
        # Bind color picker changes for real-time preview
        for color_picker in self.color_controls.values():
            color_picker.Bind(wx.EVT_COLOURPICKER_CHANGED, self.on_color_changed)
    
    def load_theme_values(self, theme: m_theme_manager.Theme):
        """Load values from an existing theme."""

        self.name_ctrl.SetValue(theme.name)
        self.is_dark_cb.SetValue(theme.is_dark)
        
        for color_key, color_picker in self.color_controls.items():
            color_value = getattr(theme, color_key, "#FFFFFF")
            color_picker.SetColour(wx.Colour(color_value))
        
        self.update_preview()
    
    def on_light_preset(self, event):
        """Set up light theme preset."""

        light_theme = self.theme_manager.get_theme("Light")
        if light_theme:
            self.load_theme_values(light_theme)
            self.name_ctrl.SetValue("")  # Clear name for new theme
    
    def on_dark_preset(self, event):
        """Set up dark theme preset."""

        dark_theme = self.theme_manager.get_theme("Dark")
        if dark_theme:
            self.load_theme_values(dark_theme)
            self.name_ctrl.SetValue("")  # Clear name for new theme
    
    def on_color_changed(self, event):
        """Handle color picker changes."""

        # Update preview in real-time
        wx.CallAfter(self.update_preview)
    
    def on_update_preview(self, event):
        """Handle preview update button."""

        self.update_preview()
    
    def update_preview(self):
        """Update the preview panel with current colors."""

        try:
            # Get current colors
            bg_color = self.color_controls["background"].GetColour()
            panel_bg_color = self.color_controls["panel_background"].GetColour()
            text_color = self.color_controls["text_foreground"].GetColour()
            text_bg_color = self.color_controls["text_background"].GetColour()
            button_bg_color = self.color_controls["button_background"].GetColour()
            button_fg_color = self.color_controls["button_foreground"].GetColour()
            
            # Apply to preview panel
            self.preview_panel.SetBackgroundColour(panel_bg_color)
            self.preview_text.SetForegroundColour(text_color)
            self.preview_text.SetBackgroundColour(panel_bg_color)
            
            self.preview_button.SetBackgroundColour(button_bg_color)
            self.preview_button.SetForegroundColour(button_fg_color)
            
            self.preview_textctrl.SetBackgroundColour(text_bg_color)
            self.preview_textctrl.SetForegroundColour(text_color)
            
            # Refresh to show changes
            self.preview_panel.Refresh()
            
        except Exception as e:
            print(f"Error updating preview: {e}")
    
    def on_ok(self, event):
        """Handle OK button."""

        name = self.name_ctrl.GetValue().strip()
        
        if not name:
            wx.MessageBox("Please enter a theme name.", "Missing Name", 
                         wx.OK | wx.ICON_WARNING, self)
            return
        
        # Check if name already exists (unless we're editing the same theme)
        if not self.is_editing or (self.is_editing and name != self.original_theme.name):
            if name in self.theme_manager.themes:
                result = wx.MessageBox(
                    f"Theme '{name}' already exists. Do you want to replace it?", 
                    "Theme Exists", 
                    wx.YES_NO | wx.ICON_QUESTION, self
                )
                if result == wx.NO:
                    return
        
        # Create theme from current values
        theme_data = {
            "name": name,
            "is_dark": self.is_dark_cb.GetValue()
        }
        
        # Get colors from pickers
        for color_key, color_picker in self.color_controls.items():
            color = color_picker.GetColour()
            theme_data[color_key] = color.GetAsString(wx.C2S_HTML_SYNTAX)
        
        # Create theme object
        theme = m_theme_manager.Theme(**theme_data)
        
        # Store the theme
        self.theme = theme
        
        self.EndModal(wx.ID_OK)
    
    def get_theme(self) -> Optional[m_theme_manager.Theme]:
        """Get the created/edited theme."""

        return getattr(self, 'theme', None)
