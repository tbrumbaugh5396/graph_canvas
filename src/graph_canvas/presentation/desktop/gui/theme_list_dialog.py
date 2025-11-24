"""
Dialog for managing themes.
"""


import wx
from typing import Optional, List

import graph_canvas.presentation.desktop.utils.managers.theme_manager as m_theme_manager


class ThemeListDialog(wx.Dialog):
    """Dialog for viewing and managing themes."""
    
    def __init__(self, parent, theme_database, theme_manager=None):
        super().__init__(parent, title="Theme Manager", size=(400, 500),
                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)
        
        self.theme_database = theme_database
        self.theme_manager = theme_manager
        self.selected_theme: Optional[m_theme_manager.Theme] = None
        self.selected_theme_is_default = False
        
        self.setup_ui()
        self.load_themes()
    
    def setup_ui(self):
        """Set up the dialog UI."""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Theme list
        list_label = wx.StaticText(panel, label="Available Themes:")
        main_sizer.Add(list_label, 0, wx.ALL, 5)
        
        self.theme_list = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.theme_list.InsertColumn(0, "Theme Name", width=200)
        self.theme_list.InsertColumn(1, "Type", width=100)
        
        main_sizer.Add(self.theme_list, 1, wx.EXPAND | wx.ALL, 5)
        
        # Preview panel
        preview_box = wx.StaticBox(panel, label="Preview")
        preview_sizer = wx.StaticBoxSizer(preview_box, wx.VERTICAL)
        
        self.preview_panel = wx.Panel(panel, size=(380, 100))
        self.preview_panel.SetBackgroundColour(wx.Colour("#FFFFFF"))
        
        # Add some preview controls
        preview_panel_sizer = wx.BoxSizer(wx.VERTICAL)
        self.preview_text = wx.StaticText(self.preview_panel, label="Sample text")
        self.preview_button = wx.Button(self.preview_panel, label="Sample Button")
        self.preview_textctrl = wx.TextCtrl(self.preview_panel, value="Sample input text")
        
        preview_panel_sizer.Add(self.preview_text, 0, wx.ALL, 5)
        preview_panel_sizer.Add(self.preview_button, 0, wx.ALL, 5)
        preview_panel_sizer.Add(self.preview_textctrl, 0, wx.EXPAND | wx.ALL, 5)
        self.preview_panel.SetSizer(preview_panel_sizer)
        
        preview_sizer.Add(self.preview_panel, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(preview_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        edit_btn = wx.Button(panel, label="Edit")
        use_template_btn = wx.Button(panel, label="Use as Template")
        delete_btn = wx.Button(panel, label="Delete")
        apply_btn = wx.Button(panel, label="Apply")
        close_btn = wx.Button(panel, wx.ID_CLOSE, "Close")
        
        btn_sizer.Add(edit_btn, 0, wx.ALL, 5)
        btn_sizer.Add(use_template_btn, 0, wx.ALL, 5)
        btn_sizer.Add(delete_btn, 0, wx.ALL, 5)
        btn_sizer.AddStretchSpacer()
        btn_sizer.Add(apply_btn, 0, wx.ALL, 5)
        btn_sizer.Add(close_btn, 0, wx.ALL, 5)
        
        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        panel.SetSizer(main_sizer)
        
        # Bind events
        self.theme_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_theme_selected)
        edit_btn.Bind(wx.EVT_BUTTON, self.on_edit)
        use_template_btn.Bind(wx.EVT_BUTTON, self.on_use_template)
        delete_btn.Bind(wx.EVT_BUTTON, self.on_delete)
        apply_btn.Bind(wx.EVT_BUTTON, self.on_apply)
        close_btn.Bind(wx.EVT_BUTTON, lambda evt: self.Close())
    
    def load_themes(self):
        """Load themes into the list."""
        self.theme_list.DeleteAllItems()
        
        # Add default themes first
        if self.theme_manager:
            predefined_names = {
                "Light", "Dark", "High Contrast Light", "High Contrast Dark",
                "Blue", "Green", "Purple"
            }
            for theme_name in sorted(predefined_names):
                theme = self.theme_manager.get_theme(theme_name)
                if theme:
                    index = self.theme_list.GetItemCount()
                    self.theme_list.InsertItem(index, theme.name)
                    self.theme_list.SetItem(index, 1, "Default")
                    
                    # Select if this was the last selected theme
                    if theme.name == self.theme_database.last_selected_theme:
                        self.theme_list.Select(index)
                        self.selected_theme = theme
                        self.selected_theme_is_default = True
                        self.update_preview(theme)
        
        # Add custom themes
        for theme in self.theme_database.get_all_themes():
            index = self.theme_list.GetItemCount()
            self.theme_list.InsertItem(index, theme.name)
            self.theme_list.SetItem(index, 1, "Custom")
            
            # Select if this was the last selected theme
            if theme.name == self.theme_database.last_selected_theme:
                self.theme_list.Select(index)
                self.selected_theme = theme
                self.selected_theme_is_default = False
                self.update_preview(theme)
    
    def update_preview(self, theme: m_theme_manager.Theme):
        """Update the preview panel with theme colors."""
        self.preview_panel.SetBackgroundColour(wx.Colour(theme.panel_background))
        self.preview_text.SetForegroundColour(wx.Colour(theme.text_foreground))
        self.preview_text.SetBackgroundColour(wx.Colour(theme.panel_background))
        
        self.preview_button.SetBackgroundColour(wx.Colour(theme.button_background))
        self.preview_button.SetForegroundColour(wx.Colour(theme.button_foreground))
        
        self.preview_textctrl.SetBackgroundColour(wx.Colour(theme.text_background))
        self.preview_textctrl.SetForegroundColour(wx.Colour(theme.text_foreground))
        
        self.preview_panel.Refresh()
    
    def on_theme_selected(self, event):
        """Handle theme selection."""
        index = event.GetIndex()
        theme_name = self.theme_list.GetItem(index, 0).GetText()
        theme_type = self.theme_list.GetItem(index, 1).GetText()
        
        # Get theme from appropriate source
        if theme_type == "Default" and self.theme_manager:
            theme = self.theme_manager.get_theme(theme_name)
            self.selected_theme_is_default = True
        else:
            theme = self.theme_database.get_theme(theme_name)
            self.selected_theme_is_default = False
            
        if theme:
            self.selected_theme = theme
            self.update_preview(theme)
    
    def on_edit(self, event):
        """Handle edit button."""
        if not self.selected_theme:
            return
        
        if self.selected_theme_is_default:
            wx.MessageBox(
                "Default themes cannot be edited. Use 'Use as Template' to create a new theme based on this one.",
                "Cannot Edit", wx.OK | wx.ICON_INFORMATION, self)
            return
        
        import graph_canvas.presentation.desktop.gui.theme_dialog as m_theme_dialog
        dialog = m_theme_dialog.ThemeDialog(self, self.theme_database, self.selected_theme)
        if dialog.ShowModal() == wx.ID_OK:
            theme = dialog.get_theme()
            if theme:
                self.theme_database.add_theme(theme)
                self.load_themes()
    
    def on_delete(self, event):
        """Handle delete button."""
        if not self.selected_theme:
            return
        
        if self.selected_theme_is_default:
            wx.MessageBox("Default themes cannot be deleted.", "Error",
                        wx.OK | wx.ICON_ERROR, self)
            return
        
        result = wx.MessageBox(f"Delete theme '{self.selected_theme.name}'?",
                            "Confirm Delete",
                            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
                            self)
        
        if result == wx.YES:
            self.theme_database.remove_theme(self.selected_theme.name)
            self.selected_theme = None
            self.load_themes()
    
    def on_apply(self, event):
        """Handle apply button."""
        if not self.selected_theme:
            return
        
        self.theme_database.set_last_selected_theme(self.selected_theme.name)
        self.EndModal(wx.ID_OK)
    
    def on_use_template(self, event):
        """Handle use as template button."""
        if not self.selected_theme:
            return
        
        import graph_canvas.presentation.desktop.gui.theme_dialog as m_theme_dialog
        dialog = m_theme_dialog.ThemeDialog(self, self.theme_database, self.selected_theme, is_template=True)
        if dialog.ShowModal() == wx.ID_OK:
            theme = dialog.get_theme()
            if theme:
                self.theme_database.add_theme(theme)
                self.load_themes()
    
    def get_selected_theme(self) -> Optional[m_theme_manager.Theme]:
        """Get the selected theme."""
        return self.selected_theme
