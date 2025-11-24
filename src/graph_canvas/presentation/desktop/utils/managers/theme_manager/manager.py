"""
Theme manager logic plus integration with ThemeDatabase.
"""


from typing import Optional, List
import os
import json
import wx

from .models import Theme
from .database import ThemeDatabase


class ThemeManager:
    """Manages application themes and provides access to the theme database."""
    
    def __init__(self, database: ThemeDatabase = None):
        self.theme_database: ThemeDatabase = database or ThemeDatabase()
        
        self.current_theme: Optional[Theme] = None
        self.themes: dict[str, Theme] = {}
        self.custom_themes_file = "custom_themes.json"
        
        self._init_predefined_themes()
        self._load_custom_themes()
        
        # Load themes stored in database as custom themes available here
        for theme in self.theme_database.get_all_themes():
            self.themes[theme.name] = theme
        
        # Set default theme based on database setting or Light
        if self.theme_database.last_selected_theme and self.theme_database.last_selected_theme in self.themes:
            self.current_theme = self.themes[self.theme_database.last_selected_theme]
        else:
            self.current_theme = self.themes.get("Light", next(iter(self.themes.values())))
    
    def _init_predefined_themes(self):
        """Initialize predefined common themes."""
        self.themes["Light"] = Theme(
            name="Light",
            background="#FFFFFF",
            panel_background="#F5F5F5",
            text_foreground="#000000",
            text_background="#FFFFFF",
            button_background="#E1E1E1",
            button_foreground="#000000",
            expandable_panel_background="#E8E8E8",
            expandable_panel_foreground="#000000",
            border_color="#CCCCCC",
            accent_color="#0078D4",
            selection_color="#CCE8FF",
            disabled_color="#999999",
            error_color="#D13438",
            success_color="#107C10",
            warning_color="#FF8C00",
            dialog_background="#FFFFFF",
            menu_background="#F0F0F0",
            menu_foreground="#000000",
            status_background="#E1E1E1",
            status_foreground="#000000",
            selectable_background="#FFFFFF",
            selectable_foreground="#000000",
            selectable_hover_background="#F0F0F0",
            selectable_hover_foreground="#000000",
            toggle_background="#FFFFFF",
            toggle_foreground="#000000",
            toggle_checked_background="#0078D4",
            toggle_checked_foreground="#FFFFFF",
            is_dark=False
        )
        
        self.themes["Dark"] = Theme(
            name="Dark",
            background="#2D2D30",
            panel_background="#383838",
            text_foreground="#FFFFFF",
            text_background="#3F3F46",
            button_background="#4A4A4A",
            button_foreground="#FFFFFF",
            expandable_panel_background="#454545",
            expandable_panel_foreground="#FFFFFF",
            border_color="#555555",
            accent_color="#0E639C",
            selection_color="#094771",
            disabled_color="#666666",
            error_color="#F14C4C",
            success_color="#73C991",
            warning_color="#FFB347",
            dialog_background="#2D2D30",
            menu_background="#383838",
            menu_foreground="#FFFFFF",
            status_background="#007ACC",
            status_foreground="#FFFFFF",
            selectable_background="#3C3C3C",
            selectable_foreground="#FFFFFF",
            selectable_hover_background="#505050",
            selectable_hover_foreground="#FFFFFF",
            toggle_background="#3C3C3C",
            toggle_foreground="#FFFFFF",
            toggle_checked_background="#0E639C",
            toggle_checked_foreground="#FFFFFF",
            is_dark=True
        )
        
        # Additional palettes
        self.themes["High Contrast Light"] = Theme(
            name="High Contrast Light",
            background="#FFFFFF",
            panel_background="#FFFFFF",
            text_foreground="#000000",
            text_background="#FFFFFF",
            button_background="#FFFFFF",
            button_foreground="#000000",
            expandable_panel_background="#F0F0F0",
            expandable_panel_foreground="#000000",
            border_color="#000000",
            accent_color="#0000FF",
            selection_color="#0000FF",
            disabled_color="#808080",
            error_color="#FF0000",
            success_color="#008000",
            warning_color="#FF8000",
            dialog_background="#FFFFFF",
            menu_background="#FFFFFF",
            menu_foreground="#000000",
            status_background="#000000",
            status_foreground="#FFFFFF",
            selectable_background="#FFFFFF",
            selectable_foreground="#000000",
            selectable_hover_background="#E0E0E0",
            selectable_hover_foreground="#000000",
            toggle_background="#FFFFFF",
            toggle_foreground="#000000",
            toggle_checked_background="#0000FF",
            toggle_checked_foreground="#FFFFFF",
            is_dark=False
        )
        
        self.themes["High Contrast Dark"] = Theme(
            name="High Contrast Dark",
            background="#000000",
            panel_background="#000000",
            text_foreground="#FFFFFF",
            text_background="#000000",
            button_background="#000000",
            button_foreground="#FFFFFF",
            expandable_panel_background="#101010",
            expandable_panel_foreground="#FFFFFF",
            border_color="#FFFFFF",
            accent_color="#FFFF00",
            selection_color="#FFFF00",
            disabled_color="#808080",
            error_color="#FF0000",
            success_color="#00FF00",
            warning_color="#FFFF00",
            dialog_background="#000000",
            menu_background="#000000",
            menu_foreground="#FFFFFF",
            status_background="#FFFFFF",
            status_foreground="#000000",
            selectable_background="#000000",
            selectable_foreground="#FFFFFF",
            selectable_hover_background="#202020",
            selectable_hover_foreground="#FFFFFF",
            toggle_background="#000000",
            toggle_foreground="#FFFFFF",
            toggle_checked_background="#FFFF00",
            toggle_checked_foreground="#000000",
            is_dark=True
        )
        
        self.themes["Blue"] = Theme(
            name="Blue",
            background="#E6F3FF",
            panel_background="#CCE7FF",
            text_foreground="#003366",
            text_background="#FFFFFF",
            button_background="#B3D9FF",
            button_foreground="#003366",
            expandable_panel_background="#D9ECFF",
            expandable_panel_foreground="#003366",
            border_color="#66CCFF",
            accent_color="#0066CC",
            selection_color="#99D6FF",
            disabled_color="#4D79A4",
            error_color="#CC0000",
            success_color="#006600",
            warning_color="#FF6600",
            dialog_background="#E6F3FF",
            menu_background="#CCE7FF",
            menu_foreground="#003366",
            status_background="#0066CC",
            status_foreground="#FFFFFF",
            selectable_background="#FFFFFF",
            selectable_foreground="#003366",
            selectable_hover_background="#E6F3FF",
            selectable_hover_foreground="#003366",
            toggle_background="#FFFFFF",
            toggle_foreground="#003366",
            toggle_checked_background="#0066CC",
            toggle_checked_foreground="#FFFFFF",
            is_dark=False
        )
        
        self.themes["Green"] = Theme(
            name="Green",
            background="#F0F8F0",
            panel_background="#E8F5E8",
            text_foreground="#1B5E20",
            text_background="#FFFFFF",
            button_background="#C8E6C9",
            button_foreground="#1B5E20",
            expandable_panel_background="#E8F5E9",
            expandable_panel_foreground="#1B5E20",
            border_color="#81C784",
            accent_color="#388E3C",
            selection_color="#A5D6A7",
            disabled_color="#689F38",
            error_color="#D32F2F",
            success_color="#2E7D32",
            warning_color="#F57C00",
            dialog_background="#F0F8F0",
            menu_background="#E8F5E8",
            menu_foreground="#1B5E20",
            status_background="#388E3C",
            status_foreground="#FFFFFF",
            selectable_background="#FFFFFF",
            selectable_foreground="#1B5E20",
            selectable_hover_background="#F0F8F0",
            selectable_hover_foreground="#1B5E20",
            toggle_background="#FFFFFF",
            toggle_foreground="#1B5E20",
            toggle_checked_background="#388E3C",
            toggle_checked_foreground="#FFFFFF",
            is_dark=False
        )
        
        self.themes["Purple"] = Theme(
            name="Purple",
            background="#F3E5F5",
            panel_background="#E1BEE7",
            text_foreground="#4A148C",
            text_background="#FFFFFF",
            button_background="#CE93D8",
            button_foreground="#4A148C",
            expandable_panel_background="#F3E5F5",
            expandable_panel_foreground="#4A148C",
            border_color="#BA68C8",
            accent_color="#7B1FA2",
            selection_color="#D1C4E9",
            disabled_color="#8E24AA",
            error_color="#C62828",
            success_color="#2E7D32",
            warning_color="#EF6C00",
            dialog_background="#F3E5F5",
            menu_background="#E1BEE7",
            menu_foreground="#4A148C",
            status_background="#7B1FA2",
            status_foreground="#FFFFFF",
            selectable_background="#FFFFFF",
            selectable_foreground="#4A148C",
            selectable_hover_background="#F3E5F5",
            selectable_hover_foreground="#4A148C",
            toggle_background="#FFFFFF",
            toggle_foreground="#4A148C",
            toggle_checked_background="#7B1FA2",
            toggle_checked_foreground="#FFFFFF",
            is_dark=False
        )
    
    def _load_custom_themes(self):
        if os.path.exists(self.custom_themes_file):
            try:
                with open(self.custom_themes_file, 'r') as f:
                    data = json.load(f)
                    for theme_data in data:
                        theme = Theme(**theme_data)
                        self.themes[theme.name] = theme
            except Exception as e:
                print(f"Error loading custom themes: {e}")
    
    def _save_custom_themes(self):
        try:
            predefined_names = {"Light", "Dark", "High Contrast Light", "High Contrast Dark", 
                                "Blue", "Green", "Purple"}
            custom_themes = [t.__dict__ for name, t in self.themes.items() if name not in predefined_names]
            with open(self.custom_themes_file, 'w') as f:
                json.dump(custom_themes, f, indent=2)
        except Exception as e:
            print(f"Error saving custom themes: {e}")
    
    def get_theme_names(self) -> List[str]:
        return sorted(self.themes.keys())
    
    def get_theme(self, name: str) -> Optional[Theme]:
        return self.themes.get(name)
    
    def get_current_theme(self) -> Optional[Theme]:
        return self.current_theme
    
    def set_theme(self, name: str) -> bool:
        if name in self.themes:
            self.current_theme = self.themes[name]
            # Persist choice via database
            self.theme_database.set_last_selected_theme(name)
            return True
        return False
    
    def add_custom_theme(self, theme: Theme):
        self.themes[theme.name] = theme
        self._save_custom_themes()
        # Also persist to database for global availability
        self.theme_database.add_theme(theme)
    
    def delete_custom_theme(self, name: str) -> bool:
        predefined_names = {"Light", "Dark", "High Contrast Light", "High Contrast Dark", 
                            "Blue", "Green", "Purple"}
        if name in predefined_names:
            return False
        if name in self.themes:
            del self.themes[name]
            self._save_custom_themes()
            if self.current_theme and self.current_theme.name == name:
                self.current_theme = self.themes.get("Light")
            # Remove from database as well
            self.theme_database.remove_theme(name)
            return True
        return False
    
    def apply_theme_to_window(self, window: wx.Window):
        if not self.current_theme:
            return
        theme = self.current_theme
        window.SetBackgroundColour(wx.Colour(theme.background))
        window.SetForegroundColour(wx.Colour(theme.text_foreground))
        self._apply_theme_to_children(window, theme)
        window.Refresh()
    
    def _apply_theme_to_children(self, parent: wx.Window, theme: Theme):
        for child in parent.GetChildren():
            try:
                if isinstance(child, (wx.Panel, wx.ScrolledWindow)):
                    child.SetBackgroundColour(wx.Colour(theme.panel_background))
                    child.SetForegroundColour(wx.Colour(theme.text_foreground))
                elif isinstance(child, (wx.TextCtrl, wx.SpinCtrl, wx.SpinCtrlDouble)):
                    child.SetBackgroundColour(wx.Colour(theme.text_background))
                    child.SetForegroundColour(wx.Colour(theme.text_foreground))
                elif isinstance(child, (wx.Choice, wx.ComboBox, wx.ListBox)):
                    child.SetBackgroundColour(wx.Colour(theme.selectable_background))
                    child.SetForegroundColour(wx.Colour(theme.selectable_foreground))
                elif isinstance(child, wx.Button):
                    child.SetBackgroundColour(wx.Colour(theme.button_background))
                    child.SetForegroundColour(wx.Colour(theme.button_foreground))
                elif isinstance(child, wx.CollapsiblePane):
                    child.SetBackgroundColour(wx.Colour(theme.expandable_panel_background))
                    child.SetForegroundColour(wx.Colour(theme.expandable_panel_foreground))
                    pane = child.GetPane()
                    if pane:
                        pane.SetBackgroundColour(wx.Colour(theme.expandable_panel_background))
                        pane.SetForegroundColour(wx.Colour(theme.expandable_panel_foreground))
                elif isinstance(child, (wx.CheckBox, wx.RadioButton)):
                    child.SetBackgroundColour(wx.Colour(theme.toggle_background))
                    child.SetForegroundColour(wx.Colour(theme.toggle_foreground))
                elif isinstance(child, (wx.StaticText, wx.StaticBox)):
                    child.SetBackgroundColour(wx.Colour(theme.panel_background))
                    child.SetForegroundColour(wx.Colour(theme.text_foreground))
                elif isinstance(child, wx.ListCtrl):
                    child.SetBackgroundColour(wx.Colour(theme.selectable_background))
                    child.SetForegroundColour(wx.Colour(theme.selectable_foreground))
                self._apply_theme_to_children(child, theme)
            except Exception as e:
                print(f"Warning: Could not apply theme to control {type(child).__name__}: {e}")
    
    def get_wx_colour(self, color_name: str) -> wx.Colour:
        if not self.current_theme:
            return wx.Colour(255, 255, 255)
        color_hex = getattr(self.current_theme, color_name, "#FFFFFF")
        return wx.Colour(color_hex)


