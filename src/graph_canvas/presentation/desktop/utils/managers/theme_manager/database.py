"""
Persistent storage for themes.
"""


import json
import os
from typing import Dict, Optional, List

from .models import Theme


class ThemeDatabase:
    """Manages persistent storage of themes."""

    def __init__(self, config_dir: str = None):
        if config_dir is None:
            config_dir = os.path.expanduser("~/.graph-canvas")
        self.config_dir = config_dir
        self.themes_file = os.path.join(config_dir, "themes.json")
        self.settings_file = os.path.join(config_dir, "theme_settings.json")
        
        # Create config directory if it doesn't exist
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        
        # Load themes and settings
        self.themes: Dict[str, Theme] = {}
        self.last_selected_theme: Optional[str] = None
        self.load_themes()
        self.load_settings()
    
    def load_themes(self) -> None:
        """Load themes from disk."""
        if not os.path.exists(self.themes_file):
            self._create_default_themes()
            return
        
        try:
            with open(self.themes_file, 'r') as f:
                themes_data = json.load(f)
                for theme_data in themes_data:
                    theme = Theme(**theme_data)
                    self.themes[theme.name] = theme
        except Exception as e:
            print(f"Error loading themes: {e}")
            self._create_default_themes()
    
    def load_settings(self) -> None:
        """Load theme settings from disk."""
        if not os.path.exists(self.settings_file):
            return
        
        try:
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
                self.last_selected_theme = settings.get('last_selected_theme')
        except Exception as e:
            print(f"Error loading theme settings: {e}")
    
    def save_themes(self) -> None:
        """Save themes to disk."""
        try:
            themes_data = [theme.to_dict() for theme in self.themes.values()]
            with open(self.themes_file, 'w') as f:
                json.dump(themes_data, f, indent=2)
        except Exception as e:
            print(f"Error saving themes: {e}")
    
    def save_settings(self) -> None:
        """Save theme settings to disk."""
        try:
            settings = {
                'last_selected_theme': self.last_selected_theme
            }
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Error saving theme settings: {e}")
    
    def add_theme(self, theme: Theme) -> None:
        """Add or update a theme."""
        self.themes[theme.name] = theme
        self.save_themes()
    
    def remove_theme(self, theme_name: str) -> None:
        """Remove a theme."""
        if theme_name in self.themes:
            del self.themes[theme_name]
            self.save_themes()
    
    def get_theme(self, theme_name: str) -> Optional[Theme]:
        """Get a theme by name."""
        return self.themes.get(theme_name)
    
    def get_all_themes(self) -> List[Theme]:
        """Get all themes."""
        return list(self.themes.values())
    
    def set_last_selected_theme(self, theme_name: str) -> None:
        """Set and save the last selected theme."""
        self.last_selected_theme = theme_name
        self.save_settings()
    
    def _create_default_themes(self) -> None:
        """Create and save default light and dark themes."""
        light_theme = Theme(
            name="Light",
            is_dark=False,
            background="#FFFFFF",
            panel_background="#F0F0F0",
            text_foreground="#000000",
            text_background="#FFFFFF",
            button_background="#E0E0E0",
            button_foreground="#000000",
            border_color="#C0C0C0",
            accent_color="#0078D7",
            selection_color="#CCE8FF",
            disabled_color="#A0A0A0",
            error_color="#FF0000",
            success_color="#00FF00",
            warning_color="#FFA500",
            dialog_background="#FFFFFF",
            menu_background="#F0F0F0",
            menu_foreground="#000000",
            status_background="#F0F0F0",
            status_foreground="#000000",
            expandable_panel_background="#E8E8E8",
            expandable_panel_foreground="#000000"
        )
        
        dark_theme = Theme(
            name="Dark",
            is_dark=True,
            background="#1E1E1E",
            panel_background="#252526",
            text_foreground="#D4D4D4",
            text_background="#3C3C3C",
            button_background="#0E639C",
            button_foreground="#FFFFFF",
            border_color="#454545",
            accent_color="#0078D7",
            selection_color="#264F78",
            disabled_color="#848484",
            error_color="#F48771",
            success_color="#89D185",
            warning_color="#CCA700",
            dialog_background="#252526",
            menu_background="#3C3C3C",
            menu_foreground="#D4D4D4",
            status_background="#007ACC",
            status_foreground="#FFFFFF",
            expandable_panel_background="#454545",
            expandable_panel_foreground="#FFFFFF"
        )
        
        self.themes = {
            "Light": light_theme,
            "Dark": dark_theme
        }
        self.save_themes()


