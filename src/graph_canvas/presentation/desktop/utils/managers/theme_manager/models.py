"""
Theme models used by the theme manager package.
"""


from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass
class Theme:
    """Represents a color theme for the application."""

    # Required fields (no defaults)
    name: str
    background: str  # Main window background
    panel_background: str  # Sidebar and panel backgrounds
    text_foreground: str  # Primary text color
    text_background: str  # Text input backgrounds
    button_background: str  # Button backgrounds
    button_foreground: str  # Button text color
    border_color: str  # Border colors
    accent_color: str  # Accent/highlight color
    selection_color: str  # Selection highlight color
    disabled_color: str  # Disabled control color
    error_color: str  # Error text/highlights
    success_color: str  # Success indicators
    warning_color: str  # Warning indicators
    dialog_background: str  # Dialog window backgrounds
    menu_background: str  # Menu backgrounds
    menu_foreground: str  # Menu text color
    status_background: str  # Status bar background
    status_foreground: str  # Status bar text
    # Optional fields (with defaults)
    is_dark: bool = False  # Whether this is a dark theme
    expandable_panel_background: str = "#E8E8E8"  # Expandable panel backgrounds
    expandable_panel_foreground: str = "#000000"  # Expandable panel text color
    selectable_background: str = "#FFFFFF"  # Background for selectable items
    selectable_foreground: str = "#000000"  # Text color for selectable items
    selectable_hover_background: str = "#F0F0F0"  # Background for hovered items
    selectable_hover_foreground: str = "#000000"  # Text color for hovered items
    toggle_background: str = "#FFFFFF"  # Background for checkboxes and radio buttons
    toggle_foreground: str = "#000000"  # Text color for checkboxes and radio buttons
    toggle_checked_background: str = "#0078D4"  # Background for checked toggles
    toggle_checked_foreground: str = "#FFFFFF"  # Text color for checked toggles

    def to_dict(self) -> Dict[str, Any]:
        """Convert theme to dictionary for serialization."""
        return asdict(self)


