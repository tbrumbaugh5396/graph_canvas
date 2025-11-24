"""
Hotkey manager for handling keyboard shortcuts, mouse actions, and mode toggles.
"""

import json
import os
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Tuple, Callable, Optional, Set
import wx


class ActionType(Enum):
    """Types of actions that can be bound to hotkeys."""
    MENUBAR = auto()  # Menubar action
    COMMAND = auto()  # One-time command execution
    MODE_TOGGLE = auto()  # Toggle a mode on/off


class MenuSection(Enum):
    """Sections in the menubar."""
    FILE = auto()
    EDIT = auto()
    VIEW = auto()
    LAYOUT = auto()
    THEME = auto()
    SETTINGS = auto()
    HELP = auto()


class MouseAction(Enum):
    """Types of mouse actions that can be part of a binding."""
    LEFT_CLICK = auto()
    RIGHT_CLICK = auto()
    MIDDLE_CLICK = auto()
    WHEEL_UP = auto()
    WHEEL_DOWN = auto()
    DRAG = auto()
    MOVE = auto()


@dataclass
class ActionBinding:
    """Represents a complete action binding."""
    action_type: ActionType
    keys: Set[str]  # Set of key names that must be pressed
    mouse_actions: Set[MouseAction]  # Required mouse actions
    callback: Callable
    description: str
    mode_name: Optional[str] = None  # For MODE_TOGGLE actions
    menu_section: Optional[MenuSection] = None  # For MENUBAR actions
    menu_item: Optional[wx.MenuItem] = None  # For MENUBAR actions to update labels


class HotkeyManager:
    """Manages hotkey bindings, mouse actions, and mode toggles."""

    def __init__(self, main_window: 'MainWindow'):
        self.main_window = main_window
        self.bindings: Dict[str, ActionBinding] = {}  # {binding_id: ActionBinding}
        self.active_modes: Set[str] = set()  # Currently active mode names
        self.pressed_keys: Set[str] = set()  # Currently pressed keys
        self.current_mouse_actions: Set[MouseAction] = set()  # Current mouse state
        self.hotkey_to_id: Dict[str, str] = {}  # Maps hotkey strings to binding IDs
        self.config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'hotkeys.json')
        
        # Create config directory if it doesn't exist
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        
        # Load or create default bindings
        self.load_bindings()
        
        # Bind mouse events to main window
        self.main_window.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_left_down)
        self.main_window.Bind(wx.EVT_RIGHT_DOWN, self.on_mouse_right_down)
        self.main_window.Bind(wx.EVT_MIDDLE_DOWN, self.on_mouse_middle_down)
        self.main_window.Bind(wx.EVT_MOUSEWHEEL, self.on_mouse_wheel)
        self.main_window.Bind(wx.EVT_MOTION, self.on_mouse_move)
        self.main_window.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.main_window.Bind(wx.EVT_KEY_UP, self.on_key_up)
    
    def add_binding(self, binding_id: str, binding: ActionBinding) -> bool:
        """
        Add a new action binding.
        
        Args:
            binding_id: Unique identifier for this binding (e.g., 'toggle_move_mode')
            binding: ActionBinding object containing all binding details
            
        Returns:
            bool: True if binding was added successfully
        """
        # Check for conflicts with existing bindings
        for existing_binding in self.bindings.values():
            if existing_binding.keys == binding.keys and existing_binding.mouse_actions == binding.mouse_actions:
                return False
            
        self.bindings[binding_id] = binding
        
        # Update menubar item label if this is a menubar action
        if binding.action_type == ActionType.MENUBAR and binding.menu_item:
            self._update_menuitem_label(binding)
            
        return True
        
    def _update_menuitem_label(self, binding: ActionBinding):
        """Update a menubar item's label to include its hotkey."""
        if not binding.menu_item:
            return
            
        # Get the base label without any existing hotkey
        label = binding.menu_item.GetItemLabel()
        tab_pos = label.find('\t')
        if tab_pos != -1:
            label = label[:tab_pos]
            
        # Build the hotkey string
        hotkey_parts = []
        if binding.keys:
            hotkey_parts.append(' + '.join(sorted(binding.keys)))
        if binding.mouse_actions:
            hotkey_parts.append(' + '.join(a.name for a in binding.mouse_actions))
            
        # Update the label
        if hotkey_parts:
            binding.menu_item.SetItemLabel(f"{label}\t{' + '.join(hotkey_parts)}")
        else:
            binding.menu_item.SetItemLabel(label)
        
    def on_key_down(self, event):
        """Handle key down events."""
        key_name = self._get_key_name(event.GetKeyCode())
        self.pressed_keys.add(key_name)
        self._check_bindings()
        event.Skip()
        
    def on_key_up(self, event):
        """Handle key up events."""
        key_name = self._get_key_name(event.GetKeyCode())
        self.pressed_keys.discard(key_name)
        event.Skip()
        
    def on_mouse_left_down(self, event):
        """Handle left mouse button down."""
        self.current_mouse_actions.add(MouseAction.LEFT_CLICK)
        self._check_bindings()
        event.Skip()
        
    def on_mouse_right_down(self, event):
        """Handle right mouse button down."""
        self.current_mouse_actions.add(MouseAction.RIGHT_CLICK)
        self._check_bindings()
        event.Skip()
        
    def on_mouse_middle_down(self, event):
        """Handle middle mouse button down."""
        self.current_mouse_actions.add(MouseAction.MIDDLE_CLICK)
        self._check_bindings()
        event.Skip()
        
    def on_mouse_wheel(self, event):
        """Handle mouse wheel events.

        Let the canvas own all wheel-based zoom to avoid double-handling that causes boomerang.
        """
        event.Skip()
        return
        
    def on_mouse_move(self, event):
        """Handle mouse movement."""
        if event.Dragging():
            self.current_mouse_actions.add(MouseAction.DRAG)
        self.current_mouse_actions.add(MouseAction.MOVE)
        self._check_bindings()
        self.current_mouse_actions.discard(MouseAction.MOVE)
        if not event.Dragging():
            self.current_mouse_actions.discard(MouseAction.DRAG)
        event.Skip()
        
    def _check_bindings(self):
        """Check if any bindings match the current state."""
        for binding_id, binding in self.bindings.items():
            # Check if keys match (if any required)
            keys_match = not binding.keys or binding.keys.issubset(self.pressed_keys)
            # Check if mouse actions match (if any required)
            mouse_match = not binding.mouse_actions or binding.mouse_actions.issubset(self.current_mouse_actions)
            
            if keys_match and mouse_match:
                if binding.action_type == ActionType.MODE_TOGGLE:
                    # For mode toggles, we only toggle on exact key match
                    if binding.keys and len(binding.keys) == len(self.pressed_keys):
                        current_mode = binding.mode_name
                        # Deactivate all other modes
                        self.active_modes.clear()
                        # Toggle this mode
                        if current_mode not in self.active_modes:
                            self.active_modes.add(current_mode)
                            print(f"DEBUG: Mode activated: {current_mode}")
                        binding.callback()
                elif binding.action_type == ActionType.COMMAND:
                    # For commands, check if we're in the right mode (if mode-specific)
                    if binding.mode_name is None or binding.mode_name in self.active_modes:
                        # For mouse-only commands, require exact mouse action match
                        if not binding.keys and binding.mouse_actions:
                            if binding.mouse_actions == self.current_mouse_actions:
                                binding.callback()
                        else:
                            binding.callback()
    
    def remove_binding(self, hotkey_id: str) -> bool:
        """Remove a hotkey binding by its ID."""
        if hotkey_id not in self.bindings:
            return False
            
        hotkey_str = self.bindings[hotkey_id][0]
        del self.bindings[hotkey_id]
        del self.hotkey_to_id[hotkey_str]
        return True
    
    def update_binding(self, hotkey_id: str, new_hotkey_str: str) -> bool:
        """
        Update the hotkey string for an existing binding.
        
        Args:
            hotkey_id: ID of the binding to update
            new_hotkey_str: New hotkey string
            
        Returns:
            bool: True if binding was updated successfully
        """
        if hotkey_id not in self.bindings:
            return False
            
        # Check if new hotkey is already bound to a different action
        if new_hotkey_str in self.hotkey_to_id and self.hotkey_to_id[new_hotkey_str] != hotkey_id:
            return False
            
        old_hotkey_str = self.bindings[hotkey_id][0]
        action = self.bindings[hotkey_id][1]
        
        # Update mappings
        del self.hotkey_to_id[old_hotkey_str]
        self.bindings[hotkey_id] = (new_hotkey_str, action)
        self.hotkey_to_id[new_hotkey_str] = hotkey_id
        
        return True
    
    def get_binding(self, hotkey_id: str) -> Optional[Tuple[str, Callable]]:
        """Get the hotkey string and action for a binding ID."""
        return self.bindings.get(hotkey_id)
    
    def get_all_bindings(self) -> Dict[str, Tuple[str, Callable]]:
        """Get all current bindings."""
        return self.bindings.copy()
    
    def handle_key_event(self, event: wx.KeyEvent) -> bool:
        """
        Handle a key event by checking if it matches any bindings.
        
        Returns:
            bool: True if the event was handled, False otherwise
        """
        # Get the key name
        key_name = self._get_key_name(event.GetKeyCode())
        
        # Add modifiers
        keys = set()
        if event.ControlDown():
            keys.add('Ctrl')
        if event.AltDown():
            keys.add('Alt')
        if event.ShiftDown():
            keys.add('Shift')
        if event.MetaDown():  # Command key on macOS
            keys.add('Cmd')
        keys.add(key_name)
        
        # Check each binding
        for binding_id, binding in self.bindings.items():
            if binding.keys == keys and not binding.mouse_actions:
                # Found a matching keyboard-only binding
                if binding.action_type == ActionType.MODE_TOGGLE:
                    # Toggle mode
                    current_mode = binding.mode_name
                    self.active_modes.clear()  # Deactivate other modes
                    self.active_modes.add(current_mode)  # Activate this mode
                    print(f"DEBUG: Mode activated via key event: {current_mode}")
                binding.callback()
                return True
        
        return False
    
    def _event_to_hotkey_str(self, event: wx.KeyEvent) -> str:
        """Convert a wx.KeyEvent to our hotkey string format."""
        parts = []
        
        # Add modifiers
        if event.ControlDown():
            parts.append('Ctrl')
        if event.AltDown():
            parts.append('Alt')
        if event.ShiftDown():
            parts.append('Shift')
        if event.MetaDown():  # Command key on macOS
            parts.append('Cmd')
            
        # Add the main key
        key_code = event.GetKeyCode()
        key_name = self._get_key_name(key_code)
        parts.append(key_name)
        
        return '+'.join(parts)
    
    def _get_key_name(self, key_code: int) -> str:
        """Convert a wx key code to a readable name."""
        # Handle special keys
        special_keys = {
            wx.WXK_BACK: 'Backspace',
            wx.WXK_TAB: 'Tab',
            wx.WXK_RETURN: 'Return',
            wx.WXK_ESCAPE: 'Escape',
            wx.WXK_SPACE: 'Space',
            wx.WXK_DELETE: 'Delete',
            wx.WXK_UP: 'Up',
            wx.WXK_DOWN: 'Down',
            wx.WXK_LEFT: 'Left',
            wx.WXK_RIGHT: 'Right',
            wx.WXK_INSERT: 'Insert',
            wx.WXK_HOME: 'Home',
            wx.WXK_END: 'End',
            wx.WXK_PAGEUP: 'PageUp',
            wx.WXK_PAGEDOWN: 'PageDown',
            wx.WXK_F1: 'F1',
            wx.WXK_F2: 'F2',
            wx.WXK_F3: 'F3',
            wx.WXK_F4: 'F4',
            wx.WXK_F5: 'F5',
            wx.WXK_F6: 'F6',
            wx.WXK_F7: 'F7',
            wx.WXK_F8: 'F8',
            wx.WXK_F9: 'F9',
            wx.WXK_F10: 'F10',
            wx.WXK_F11: 'F11',
            wx.WXK_F12: 'F12',
            wx.WXK_ADD: 'Plus',
            wx.WXK_SUBTRACT: 'Minus',
            wx.WXK_MULTIPLY: 'Multiply',
            wx.WXK_DIVIDE: 'Divide',
        }
        
        if key_code in special_keys:
            return special_keys[key_code]
            
        # Handle regular characters
        if key_code >= 32 and key_code <= 126:
            return chr(key_code).upper()
            
        # Unknown key
        return f'Key{key_code}'
    
    def load_bindings(self):
        """Load hotkey bindings from config file or create defaults."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    saved_bindings = json.load(f)
                    
                # Restore bindings with their actions
                for hotkey_id, hotkey_str in saved_bindings.items():
                    action = self._get_default_action(hotkey_id)
                    if action:
                        self.add_binding(hotkey_id, hotkey_str, action)
            else:
                self._create_default_bindings()
                
        except Exception as e:
            print(f"Error loading hotkey bindings: {e}")
            self._create_default_bindings()
    
    def save_bindings(self):
        """Save current hotkey bindings to config file."""
        try:
            # Save only the hotkey strings, not the actions
            bindings_dict = {
                hotkey_id: hotkey_str
                for hotkey_id, (hotkey_str, _) in self.bindings.items()
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(bindings_dict, f, indent=4)
                
        except Exception as e:
            print(f"Error saving hotkey bindings: {e}")
    
    def _create_default_bindings(self):
        """Create default bindings including modes and actions."""
        # File menu
        self.add_binding('new_graph', ActionBinding(
            action_type=ActionType.MENUBAR,
            keys={'Ctrl', 'N'},
            mouse_actions=set(),
            callback=lambda: self.main_window.on_new(),
            description="New Graph",
            menu_section=MenuSection.FILE
        ))
        
        self.add_binding('open_graph', ActionBinding(
            action_type=ActionType.MENUBAR,
            keys={'Ctrl', 'O'},
            mouse_actions=set(),
            callback=lambda: self.main_window.on_open(),
            description="Open Graph",
            menu_section=MenuSection.FILE
        ))
        
        self.add_binding('save_graph', ActionBinding(
            action_type=ActionType.MENUBAR,
            keys={'Ctrl', 'S'},
            mouse_actions=set(),
            callback=lambda: self.main_window.on_save(),
            description="Save Graph",
            menu_section=MenuSection.FILE
        ))
        
        self.add_binding('save_as_graph', ActionBinding(
            action_type=ActionType.MENUBAR,
            keys={'Ctrl', 'Shift', 'S'},
            mouse_actions=set(),
            callback=lambda: self.main_window.on_save_as(),
            description="Save Graph As",
            menu_section=MenuSection.FILE
        ))
        
        self.add_binding('import_graph', ActionBinding(
            action_type=ActionType.MENUBAR,
            keys={'Ctrl', 'I'},
            mouse_actions=set(),
            callback=lambda: self.main_window.on_import_graph(),
            description="Import Graph",
            menu_section=MenuSection.FILE
        ))

        self.add_binding('copy_graph', ActionBinding(
            action_type=ActionType.MENUBAR,
            keys={'Ctrl', 'Alt', 'C'},
            mouse_actions=set(),
            callback=lambda: self.main_window.on_copy_graph(),
            description="Copy Graph",
            menu_section=MenuSection.FILE
        ))

        self.add_binding('delete_graph', ActionBinding(
            action_type=ActionType.MENUBAR,
            keys={'Ctrl', 'Alt', 'D'},
            mouse_actions=set(),
            callback=lambda: self.main_window.on_delete_graph(),
            description="Delete Graph",
            menu_section=MenuSection.FILE
        ))

        self.add_binding('exit', ActionBinding(
            action_type=ActionType.MENUBAR,
            keys={'Ctrl', 'Q'},
            mouse_actions=set(),
            callback=lambda: self.main_window.Close(),
            description="Exit",
            menu_section=MenuSection.FILE
        ))
        
        # Edit menu
        self.add_binding('undo', ActionBinding(
            action_type=ActionType.MENUBAR,
            keys={'Ctrl', 'Z'},
            mouse_actions=set(),
            callback=lambda: self.main_window.on_undo(),
            description="Undo",
            menu_section=MenuSection.EDIT
        ))
        
        self.add_binding('redo', ActionBinding(
            action_type=ActionType.MENUBAR,
            keys={'Ctrl', 'Y'},
            mouse_actions=set(),
            callback=lambda: self.main_window.on_redo(),
            description="Redo",
            menu_section=MenuSection.EDIT
        ))
        
        self.add_binding('cut', ActionBinding(
            action_type=ActionType.MENUBAR,
            keys={'Ctrl', 'X'},
            mouse_actions=set(),
            callback=lambda: self.main_window.on_cut(),
            description="Cut",
            menu_section=MenuSection.EDIT
        ))
        
        self.add_binding('copy', ActionBinding(
            action_type=ActionType.MENUBAR,
            keys={'Ctrl', 'C'},
            mouse_actions=set(),
            callback=lambda: self.main_window.on_copy(),
            description="Copy",
            menu_section=MenuSection.EDIT
        ))
        
        self.add_binding('paste', ActionBinding(
            action_type=ActionType.MENUBAR,
            keys={'Ctrl', 'V'},
            mouse_actions=set(),
            callback=lambda: self.main_window.on_paste(),
            description="Paste",
            menu_section=MenuSection.EDIT
        ))
        
        self.add_binding('delete', ActionBinding(
            action_type=ActionType.MENUBAR,
            keys={'Delete'},
            mouse_actions=set(),
            callback=lambda: self.main_window.on_delete(),
            description="Delete",
            menu_section=MenuSection.EDIT
        ))
        
        self.add_binding('select_all', ActionBinding(
            action_type=ActionType.MENUBAR,
            keys={'Ctrl', 'A'},
            mouse_actions=set(),
            callback=lambda: self.main_window.on_select_all(),
            description="Select All",
            menu_section=MenuSection.EDIT
        ))

        self.add_binding('preferences', ActionBinding(
            action_type=ActionType.MENUBAR,
            keys={'Ctrl', ','},
            mouse_actions=set(),
            callback=lambda: self.main_window.on_preferences(),
            description="Preferences",
            menu_section=MenuSection.EDIT
        ))
        
        # View menu
        self.add_binding('zoom_in', ActionBinding(
            action_type=ActionType.MENUBAR,
            keys={'Ctrl', 'Plus'},
            mouse_actions=set(),
            callback=lambda: self.main_window.on_zoom_in(),
            description="Zoom In",
            menu_section=MenuSection.VIEW
        ))
        
        self.add_binding('zoom_out', ActionBinding(
            action_type=ActionType.MENUBAR,
            keys={'Ctrl', 'Minus'},
            mouse_actions=set(),
            callback=lambda: self.main_window.on_zoom_out(),
            description="Zoom Out",
            menu_section=MenuSection.VIEW
        ))
        
        self.add_binding('zoom_fit', ActionBinding(
            action_type=ActionType.MENUBAR,
            keys={'Ctrl', '0'},
            mouse_actions=set(),
            callback=lambda: self.main_window.on_zoom_fit(),
            description="Zoom to Fit",
            menu_section=MenuSection.VIEW
        ))
        
        self.add_binding('toggle_grid', ActionBinding(
            action_type=ActionType.MENUBAR,
            keys={'Ctrl', 'G'},
            mouse_actions=set(),
            callback=lambda: self.main_window.on_toggle_grid(),
            description="Toggle Grid",
            menu_section=MenuSection.VIEW
        ))

        # Layout menu
        self.add_binding('spring_layout', ActionBinding(
            action_type=ActionType.MENUBAR,
            keys={'Ctrl', 'L'},
            mouse_actions=set(),
            callback=lambda: self.main_window.on_spring_layout(),
            description="Spring Layout",
            menu_section=MenuSection.LAYOUT
        ))

        self.add_binding('circle_layout', ActionBinding(
            action_type=ActionType.MENUBAR,
            keys={'Ctrl', 'Alt', 'C'},
            mouse_actions=set(),
            callback=lambda: self.main_window.on_circle_layout(),
            description="Circle Layout",
            menu_section=MenuSection.LAYOUT
        ))

        self.add_binding('tree_layout', ActionBinding(
            action_type=ActionType.MENUBAR,
            keys={'Ctrl', 'Alt', 'T'},
            mouse_actions=set(),
            callback=lambda: self.main_window.on_tree_layout(),
            description="Tree Layout",
            menu_section=MenuSection.LAYOUT
        ))

        self.add_binding('grid_layout', ActionBinding(
            action_type=ActionType.MENUBAR,
            keys={'Ctrl', 'Alt', 'G'},
            mouse_actions=set(),
            callback=lambda: self.main_window.on_grid_layout(),
            description="Grid Layout",
            menu_section=MenuSection.LAYOUT
        ))

        self.add_binding('random_layout', ActionBinding(
            action_type=ActionType.MENUBAR,
            keys={'Ctrl', 'Alt', 'R'},
            mouse_actions=set(),
            callback=lambda: self.main_window.on_random_layout(),
            description="Random Layout",
            menu_section=MenuSection.LAYOUT
        ))
        
        # Settings menu
        self.add_binding('configure_hotkeys', ActionBinding(
            action_type=ActionType.MENUBAR,
            keys={'Ctrl', 'K'},
            mouse_actions=set(),
            callback=lambda: self.main_window.on_configure_hotkeys(),
            description="Configure Hotkeys",
            menu_section=MenuSection.SETTINGS
        ))

        # Theme menu
        self.add_binding('manage_themes', ActionBinding(
            action_type=ActionType.MENUBAR,
            keys={'Ctrl', 'T'},
            mouse_actions=set(),
            callback=lambda: self.main_window.on_show_themes(),
            description="Manage Themes",
            menu_section=MenuSection.THEME
        ))

        self.add_binding('new_theme', ActionBinding(
            action_type=ActionType.MENUBAR,
            keys={'Ctrl', 'Shift', 'T'},
            mouse_actions=set(),
            callback=lambda: self.main_window.on_new_theme(),
            description="New Theme",
            menu_section=MenuSection.THEME
        ))

        self.add_binding('edit_theme', ActionBinding(
            action_type=ActionType.MENUBAR,
            keys={'Ctrl', 'Alt', 'T'},
            mouse_actions=set(),
            callback=lambda: self.main_window.on_edit_theme(),
            description="Edit Theme",
            menu_section=MenuSection.THEME
        ))

        self.add_binding('delete_theme', ActionBinding(
            action_type=ActionType.MENUBAR,
            keys={'Ctrl', 'Alt', 'Shift', 'T'},
            mouse_actions=set(),
            callback=lambda: self.main_window.on_delete_theme(),
            description="Delete Theme",
            menu_section=MenuSection.THEME
        ))
        
        # Import tool selector event handler
        import graph_canvas.presentation.desktop.event_handlers.tool_selector_event_handler as m_tool_selector_event_handler
        
        # Mode toggles
        self.add_binding('toggle_move_mode', ActionBinding(
            action_type=ActionType.MODE_TOGGLE,
            keys={'M'},
            mouse_actions=set(),
            callback=lambda: m_tool_selector_event_handler.on_tool_change(self.main_window, 'move'),
            description="Toggle move mode",
            mode_name="move"
        ))
        
        self.add_binding('toggle_select_mode', ActionBinding(
            action_type=ActionType.MODE_TOGGLE,
            keys={'S'},
            mouse_actions=set(),
            callback=lambda: m_tool_selector_event_handler.on_tool_change(self.main_window, 'select'),
            description="Toggle select mode",
            mode_name="select"
        ))
        
        self.add_binding('toggle_rotate_mode', ActionBinding(
            action_type=ActionType.MODE_TOGGLE,
            keys={'R'},
            mouse_actions=set(),
            callback=lambda: m_tool_selector_event_handler.on_tool_change(self.main_window, 'rotate'),
            description="Toggle rotate mode",
            mode_name="rotate"
        ))
        
        self.add_binding('toggle_zoom_mode', ActionBinding(
            action_type=ActionType.MODE_TOGGLE,
            keys={'Z'},
            mouse_actions=set(),
            callback=lambda: m_tool_selector_event_handler.on_tool_change(self.main_window, 'zoom'),
            description="Toggle zoom mode",
            mode_name="zoom"
        ))
        
        # Mouse actions in move mode
        self.add_binding('move_world_drag', ActionBinding(
            action_type=ActionType.COMMAND,
            keys=set(),  # No keys required
            mouse_actions={MouseAction.LEFT_CLICK, MouseAction.DRAG},
            callback=lambda: self.main_window.canvas.move_world() if "move" in self.active_modes else None,
            description="Move world with left mouse",
            mode_name="move"  # This action only works in move mode
        ))
        
        self.add_binding('move_world_alt_drag', ActionBinding(
            action_type=ActionType.COMMAND,
            keys=set(),  # No keys required
            mouse_actions={MouseAction.RIGHT_CLICK, MouseAction.DRAG},
            callback=lambda: self.main_window.canvas.move_world() if "move" in self.active_modes else None,
            description="Move world with right mouse",
            mode_name="move"  # This action only works in move mode
        ))
        
        # Mouse actions in rotate mode
        self.add_binding('rotate_world', ActionBinding(
            action_type=ActionType.COMMAND,
            keys={'R'},
            mouse_actions={MouseAction.LEFT_CLICK, MouseAction.DRAG},
            callback=lambda: self.main_window.canvas.rotate_world() if "rotate" in self.active_modes else None,
            description="Rotate world"
        ))
        
        # Mouse actions in select mode
        self.add_binding('select_area', ActionBinding(
            action_type=ActionType.COMMAND,
            keys=set(),
            mouse_actions={MouseAction.LEFT_CLICK, MouseAction.DRAG},
            callback=lambda: self.main_window.canvas.select_area() if "select" in self.active_modes else None,
            description="Select area"
        ))
        
        # Mouse actions in zoom mode
        self.add_binding('zoom_wheel', ActionBinding(
            action_type=ActionType.COMMAND,
            keys=set(),
            mouse_actions={MouseAction.WHEEL_UP},
            callback=lambda: self.main_window.canvas.zoom_in_at_mouse() if "zoom" in self.active_modes else None,
            description="Zoom in with mouse wheel"
        ))
        
        self.add_binding('zoom_wheel_out', ActionBinding(
            action_type=ActionType.COMMAND,
            keys=set(),
            mouse_actions={MouseAction.WHEEL_DOWN},
            callback=lambda: self.main_window.canvas.zoom_out_at_mouse() if "zoom" in self.active_modes else None,
            description="Zoom out with mouse wheel"
        ))
        
        # Direct actions (no mode required)
        self.add_binding('quick_zoom_in', ActionBinding(
            action_type=ActionType.COMMAND,
            keys={'Ctrl', 'Plus'},
            mouse_actions=set(),
            callback=lambda: self.main_window.on_zoom_in(),
            description="Quick zoom in"
        ))
        
        self.add_binding('quick_zoom_out', ActionBinding(
            action_type=ActionType.COMMAND,
            keys={'Ctrl', 'Minus'},
            mouse_actions=set(),
            callback=lambda: self.main_window.on_zoom_out(),
            description="Quick zoom out"
        ))
        
        self.add_binding('quick_rotate_left', ActionBinding(
            action_type=ActionType.COMMAND,
            keys={'Alt', 'Left'},
            mouse_actions=set(),
            callback=lambda: self.main_window.canvas.rotate_world_by(-15),
            description="Quick rotate left"
        ))
        
        self.add_binding('quick_rotate_right', ActionBinding(
            action_type=ActionType.COMMAND,
            keys={'Alt', 'Right'},
            mouse_actions=set(),
            callback=lambda: self.main_window.canvas.rotate_world_by(15),
            description="Quick rotate right"
        ))
    
    def _get_default_action(self, hotkey_id: str) -> Optional[Callable]:
        """Get the default action for a hotkey ID."""
        # Map hotkey IDs to main window methods
        action_map = {
            'new_graph': lambda: self.main_window.on_new(),
            'open_graph': lambda: self.main_window.on_open(),
            'save_graph': lambda: m_menubar_event_handler.on_save_graph(self.main_window, None),
            'save_as_graph': lambda: self.main_window.on_save_as(),
            'undo': lambda: self.main_window.on_undo(),
            'redo': lambda: self.main_window.on_redo(),
            'cut': lambda: self.main_window.on_cut(),
            'copy': lambda: self.main_window.on_copy(),
            'paste': lambda: self.main_window.on_paste(),
            'delete': lambda: self.main_window.on_delete(),
            'select_all': lambda: self.main_window.on_select_all(),
            'zoom_in': lambda: self.main_window.on_zoom_in(),
            'zoom_out': lambda: self.main_window.on_zoom_out(),
            'zoom_fit': lambda: self.main_window.on_zoom_fit(),
            'toggle_grid': lambda: self.main_window.on_toggle_grid(),
        }
        
        return action_map.get(hotkey_id)
