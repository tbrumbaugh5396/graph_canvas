"""
Dialog for configuring hotkey bindings.
"""


import wx
from typing import Dict, Tuple, Callable, Optional, Set
import graph_canvas.presentation.desktop.utils.managers.hotkey_manager as m_hotkey_manager


class HotkeyDialog(wx.Dialog):
    """Dialog for viewing and editing hotkey bindings."""
    
    def __init__(self, parent, hotkey_manager: m_hotkey_manager.HotkeyManager):
        super().__init__(parent, title="Hotkey Configuration", size=(700, 600))
        self.hotkey_manager = hotkey_manager
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dialog's UI elements."""
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Instructions
        instructions = wx.StaticText(panel, label="Double-click a binding to change it, or press the keys/mouse buttons you want to use.")
        instructions.SetForegroundColour(wx.Colour(0, 0, 0))
        sizer.Add(instructions, 0, wx.ALL, 5)
        
        # Create list control
        self.hotkey_list = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.hotkey_list.InsertColumn(0, "Command", width=200)
        self.hotkey_list.InsertColumn(1, "Type", width=100)
        self.hotkey_list.InsertColumn(2, "Keys", width=150)
        self.hotkey_list.InsertColumn(3, "Mouse Actions", width=150)
        
        # Populate list
        self.populate_list()
        
        # Bind events
        self.hotkey_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_item_activated)
        self.hotkey_list.Bind(wx.EVT_KEY_DOWN, self.on_list_key)
        
        sizer.Add(self.hotkey_list, 1, wx.EXPAND | wx.ALL, 5)
        
        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        reset_btn = wx.Button(panel, label="Reset to Defaults")
        reset_btn.Bind(wx.EVT_BUTTON, self.on_reset)
        btn_sizer.Add(reset_btn, 0, wx.ALL, 5)
        
        btn_sizer.AddStretchSpacer()
        
        ok_btn = wx.Button(panel, wx.ID_OK, "OK")
        ok_btn.Bind(wx.EVT_BUTTON, self.on_ok)
        btn_sizer.Add(ok_btn, 0, wx.ALL, 5)
        
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        btn_sizer.Add(cancel_btn, 0, wx.ALL, 5)
        
        sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        panel.SetSizer(sizer)
        
        # Store original bindings in case of cancel
        self.original_bindings = self.hotkey_manager.get_all_bindings()
        
    def populate_list(self):
        """Populate the list control with current bindings."""
        self.hotkey_list.DeleteAllItems()
        bindings = self.hotkey_manager.get_all_bindings()
        
        # First add menubar items, organized by section
        i = 0
        for section in MenuSection:
            # Add section header
            index = self.hotkey_list.InsertItem(i, section.name)
            self.hotkey_list.SetItem(index, 1, "")
            self.hotkey_list.SetItem(index, 2, "")
            self.hotkey_list.SetItem(index, 3, "")
            self.hotkey_list.SetItemBackgroundColour(index, wx.Colour(240, 240, 240))
            i += 1
            
            # Add section items
            section_bindings = [(bid, b) for bid, b in bindings.items() 
                              if b.action_type == ActionType.MENUBAR and b.menu_section == section]
            section_bindings.sort(key=lambda x: x[1].description)
            
            for binding_id, binding in section_bindings:
                index = self.hotkey_list.InsertItem(i, "    " + binding.description)
                self.hotkey_list.SetItem(index, 1, binding.action_type.name)
                self.hotkey_list.SetItem(index, 2, ' + '.join(sorted(binding.keys)) if binding.keys else 'None')
                self.hotkey_list.SetItem(index, 3, ' + '.join(a.name for a in binding.mouse_actions) if binding.mouse_actions else 'None')
                self.hotkey_list.SetItemData(index, i)
                i += 1
        
        # Add separator
        if i > 0:
            index = self.hotkey_list.InsertItem(i, "")
            self.hotkey_list.SetItem(index, 1, "")
            self.hotkey_list.SetItem(index, 2, "")
            self.hotkey_list.SetItem(index, 3, "")
            i += 1
        
        # Add other bindings
        other_bindings = [(bid, b) for bid, b in bindings.items() if b.action_type != ActionType.MENUBAR]
        other_bindings.sort(key=lambda x: (x[1].action_type.name, x[1].description))
        
        for binding_id, binding in other_bindings:
            index = self.hotkey_list.InsertItem(i, binding.description)
            self.hotkey_list.SetItem(index, 1, binding.action_type.name)
            self.hotkey_list.SetItem(index, 2, ' + '.join(sorted(binding.keys)) if binding.keys else 'None')
            self.hotkey_list.SetItem(index, 3, ' + '.join(a.name for a in binding.mouse_actions) if binding.mouse_actions else 'None')
            self.hotkey_list.SetItemData(index, i)
            i += 1
            
    def setup_ui(self):
        """Set up the dialog's UI elements."""
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Instructions
        instructions = wx.StaticText(panel, label="Right-click a binding to set keyboard or mouse actions.")
        instructions.SetForegroundColour(wx.Colour(0, 0, 0))
        sizer.Add(instructions, 0, wx.ALL, 5)
        
        # Create list control
        self.hotkey_list = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.hotkey_list.InsertColumn(0, "Command", width=200)
        self.hotkey_list.InsertColumn(1, "Type", width=100)
        self.hotkey_list.InsertColumn(2, "Keys", width=150)
        self.hotkey_list.InsertColumn(3, "Mouse Actions", width=150)
        
        # Create context menu
        self.hotkey_list.Bind(wx.EVT_CONTEXT_MENU, self.on_context_menu)
        
        # Populate list
        self.populate_list()
        
        sizer.Add(self.hotkey_list, 1, wx.EXPAND | wx.ALL, 5)
        
        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        reset_btn = wx.Button(panel, label="Reset to Defaults")
        reset_btn.Bind(wx.EVT_BUTTON, self.on_reset)
        btn_sizer.Add(reset_btn, 0, wx.ALL, 5)
        
        btn_sizer.AddStretchSpacer()
        
        ok_btn = wx.Button(panel, wx.ID_OK, "OK")
        ok_btn.Bind(wx.EVT_BUTTON, self.on_ok)
        btn_sizer.Add(ok_btn, 0, wx.ALL, 5)
        
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        btn_sizer.Add(cancel_btn, 0, wx.ALL, 5)
        
        sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        panel.SetSizer(sizer)
        
        # Store original bindings in case of cancel
        self.original_bindings = self.hotkey_manager.get_all_bindings()

    def on_context_menu(self, event):
        """Show context menu for setting keyboard or mouse bindings."""
        index = self.hotkey_list.GetFirstSelected()
        if index == -1:
            return

        binding_id = self._get_binding_id_from_index(index)
        if not binding_id:
            return

        # Create context menu
        menu = wx.Menu()
        set_keys = menu.Append(wx.ID_ANY, "Set Keyboard Shortcut")
        set_mouse = menu.Append(wx.ID_ANY, "Set Mouse Actions")

        # Bind menu events
        self.Bind(wx.EVT_MENU, lambda evt: self.on_set_keyboard(binding_id), set_keys)
        self.Bind(wx.EVT_MENU, lambda evt: self.on_set_mouse(binding_id), set_mouse)

        # Show menu
        self.PopupMenu(menu)
        menu.Destroy()

    def on_set_keyboard(self, binding_id):
        """Handle setting keyboard shortcuts."""
        current_binding = self.hotkey_manager.bindings[binding_id]
        dialog = CaptureKeyboardDialog(self, current_binding)
        if dialog.ShowModal() == wx.ID_OK:
            new_keys = dialog.get_keys()
            if new_keys:
                # Create new binding with updated keys but same mouse actions
                new_binding = m_hotkey_manager.ActionBinding(
                    action_type=current_binding.action_type,
                    keys=new_keys,
                    mouse_actions=current_binding.mouse_actions,
                    callback=current_binding.callback,
                    description=current_binding.description,
                    mode_name=current_binding.mode_name,
                    menu_section=current_binding.menu_section,
                    menu_item=current_binding.menu_item
                )
                if self.hotkey_manager.add_binding(binding_id, new_binding):
                    self.populate_list()
                else:
                    wx.MessageBox(
                        "This key combination is already assigned to another command.",
                        "Binding Conflict",
                        wx.OK | wx.ICON_WARNING
                    )
        dialog.Destroy()

    def on_set_mouse(self, binding_id):
        """Handle setting mouse actions."""
        current_binding = self.hotkey_manager.bindings[binding_id]
        dialog = CaptureMouseDialog(self, current_binding)
        if dialog.ShowModal() == wx.ID_OK:
            new_mouse_actions = dialog.get_mouse_actions()
            if new_mouse_actions is not None:  # Allow empty set
                # Create new binding with updated mouse actions but same keys
                new_binding = m_hotkey_manager.ActionBinding(
                    action_type=current_binding.action_type,
                    keys=current_binding.keys,
                    mouse_actions=new_mouse_actions,
                    callback=current_binding.callback,
                    description=current_binding.description,
                    mode_name=current_binding.mode_name,
                    menu_section=current_binding.menu_section,
                    menu_item=current_binding.menu_item
                )
                if self.hotkey_manager.add_binding(binding_id, new_binding):
                    self.populate_list()
                else:
                    wx.MessageBox(
                        "This mouse combination is already assigned to another command.",
                        "Binding Conflict",
                        wx.OK | wx.ICON_WARNING
                    )
        dialog.Destroy()
        
    def on_list_key(self, event):
        """Handle key events in the list to capture new bindings directly."""
        index = self.hotkey_list.GetFirstSelected()
        if index == -1:
            event.Skip()
            return
            
        binding_id = self._get_binding_id_from_index(index)
        if not binding_id:
            event.Skip()
            return
            
        # Get the current binding
        current_binding = self.hotkey_manager.bindings[binding_id]
        
        # Create a new binding with the pressed key
        new_binding = m_hotkey_manager.ActionBinding(
            action_type=current_binding.action_type,
            keys={self.hotkey_manager._get_key_name(event.GetKeyCode())},
            mouse_actions=set(),
            callback=current_binding.callback,
            description=current_binding.description,
            mode_name=current_binding.mode_name
        )
        
        # Try to update the binding
        if self.hotkey_manager.add_binding(binding_id, new_binding):
            self.populate_list()
        else:
            wx.MessageBox(
                "This key is already assigned to another command.",
                "Binding Conflict",
                wx.OK | wx.ICON_WARNING
            )
        
    def _get_binding_id_from_index(self, index: int) -> Optional[str]:
        """Get the binding ID for a list item index."""
        description = self.hotkey_list.GetItem(index, 0).GetText()
        # Find binding ID by description
        for binding_id, binding in self.hotkey_manager.bindings.items():
            if binding.description == description:
                return binding_id
        return None
        
    def on_reset(self, event):
        """Reset all bindings to defaults."""
        if wx.MessageBox(
            "This will reset all bindings to their default values. Continue?",
            "Confirm Reset",
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION
        ) == wx.YES:
            self.hotkey_manager._create_default_bindings()
            self.populate_list()
            
    def on_ok(self, event):
        """Handle OK button click."""
        # Save the current bindings
        self.hotkey_manager.save_bindings()
        self.EndModal(wx.ID_OK)


class CaptureKeyboardDialog(wx.Dialog):
    """Dialog for capturing keyboard shortcuts."""
    
    def __init__(self, parent, current_binding):
        super().__init__(parent, title="Set Keyboard Shortcut", size=(400, 200))
        self.current_binding = current_binding
        self.captured_keys = set()
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dialog's UI elements."""
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Instructions
        instructions = wx.StaticText(
            panel,
            label="Press the desired key combination.\nPress OK when done."
        )
        instructions.SetForegroundColour(wx.Colour(0, 0, 0))
        sizer.Add(instructions, 0, wx.ALL | wx.ALIGN_CENTER, 10)
        
        # Display area
        self.display = wx.TextCtrl(
            panel,
            style=wx.TE_READONLY | wx.TE_CENTER
        )
        self.display.SetForegroundColour(wx.Colour(0, 0, 0))
        sizer.Add(self.display, 0, wx.EXPAND | wx.ALL, 10)
        
        # Bind events
        self.display.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.display.Bind(wx.EVT_KEY_UP, self.on_key_up)
        
        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        ok_btn = wx.Button(panel, wx.ID_OK, "OK")
        ok_btn.Enable(False)  # Disabled until keys are captured
        self.ok_btn = ok_btn
        btn_sizer.Add(ok_btn, 0, wx.ALL, 5)
        
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        btn_sizer.Add(cancel_btn, 0, wx.ALL, 5)
        
        sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        
        panel.SetSizer(sizer)
        
        # Focus the display area
        self.display.SetFocus()
        
        # Show current keys
        if self.current_binding.keys:
            self.captured_keys = self.current_binding.keys.copy()
            self.update_display()
        
    def on_key_down(self, event):
        """Handle key down events."""
        key_name = self.Parent.hotkey_manager._get_key_name(event.GetKeyCode())
        self.captured_keys.add(key_name)
        self.update_display()
        event.Skip()
        
    def on_key_up(self, event):
        """Handle key up events."""
        key_name = self.Parent.hotkey_manager._get_key_name(event.GetKeyCode())
        self.captured_keys.discard(key_name)
        self.update_display()
        event.Skip()
        
    def update_display(self):
        """Update the display with current keys."""
        if self.captured_keys:
            self.display.SetValue(' + '.join(sorted(self.captured_keys)))
            self.ok_btn.Enable(True)
        else:
            self.display.SetValue("Press keys...")
            self.ok_btn.Enable(False)
        
    def get_keys(self) -> Optional[Set[str]]:
        """Get the captured keys."""
        return self.captured_keys if self.captured_keys else None


class CaptureMouseDialog(wx.Dialog):
    """Dialog for capturing mouse actions."""
    
    def __init__(self, parent, current_binding):
        super().__init__(parent, title="Set Mouse Actions", size=(400, 300))
        self.current_binding = current_binding
        self.captured_actions = set()
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dialog's UI elements."""
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Instructions
        instructions = wx.StaticText(
            panel,
            label="Select the desired mouse actions.\nMultiple actions can be combined."
        )
        instructions.SetForegroundColour(wx.Colour(0, 0, 0))
        sizer.Add(instructions, 0, wx.ALL | wx.ALIGN_CENTER, 10)
        
        # Checkboxes for mouse actions
        self.checkboxes = {}
        for action in m_hotkey_manager.MouseAction:
            cb = wx.CheckBox(panel, label=action.name.replace('_', ' ').title())
            cb.SetValue(action in self.current_binding.mouse_actions)
            cb.Bind(wx.EVT_CHECKBOX, self.on_checkbox)
            self.checkboxes[action] = cb
            sizer.Add(cb, 0, wx.ALL, 5)
        
        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        ok_btn = wx.Button(panel, wx.ID_OK, "OK")
        btn_sizer.Add(ok_btn, 0, wx.ALL, 5)
        
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        btn_sizer.Add(cancel_btn, 0, wx.ALL, 5)
        
        sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        
        panel.SetSizer(sizer)
        
        # Initialize with current actions
        self.captured_actions = self.current_binding.mouse_actions.copy()
        
    def on_checkbox(self, event):
        """Handle checkbox changes."""
        for action, cb in self.checkboxes.items():
            if cb.GetValue():
                self.captured_actions.add(action)
            else:
                self.captured_actions.discard(action)
        
    def get_mouse_actions(self) -> Set[m_hotkey_manager.MouseAction]:
        """Get the selected mouse actions."""
        return self.captured_actions


class CaptureBindingDialog(wx.Dialog):
    """Dialog for capturing a new binding configuration."""
    
    def __init__(self, parent, current_binding):
        super().__init__(parent, title="Configure Binding", size=(400, 300))
        self.current_binding = current_binding
        self.captured_keys = set()
        self.captured_mouse_actions = set()
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dialog's UI elements."""
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Instructions
        instructions = wx.StaticText(
            panel,
            label="Press the desired keys and/or click mouse buttons.\nClick OK when done."
        )
        instructions.SetForegroundColour(wx.Colour(0, 0, 0))
        sizer.Add(instructions, 0, wx.ALL | wx.ALIGN_CENTER, 10)
        
        # Current binding display
        self.display = wx.TextCtrl(
            panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_CENTER
        )
        self.display.SetForegroundColour(wx.Colour(0, 0, 0))
        sizer.Add(self.display, 1, wx.EXPAND | wx.ALL, 10)
        
        # Bind events
        self.display.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.display.Bind(wx.EVT_KEY_UP, self.on_key_up)
        self.display.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_left_down)
        self.display.Bind(wx.EVT_RIGHT_DOWN, self.on_mouse_right_down)
        self.display.Bind(wx.EVT_MIDDLE_DOWN, self.on_mouse_middle_down)
        self.display.Bind(wx.EVT_MOUSEWHEEL, self.on_mouse_wheel)
        
        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        ok_btn = wx.Button(panel, wx.ID_OK, "OK")
        ok_btn.Enable(False)  # Disabled until a binding is captured
        self.ok_btn = ok_btn
        btn_sizer.Add(ok_btn, 0, wx.ALL, 5)
        
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        btn_sizer.Add(cancel_btn, 0, wx.ALL, 5)
        
        sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        
        panel.SetSizer(sizer)
        
        # Focus the display area
        self.display.SetFocus()
        
        # Update display with current binding
        self.update_display()
        
    def on_key_down(self, event):
        """Handle key down events."""
        key_name = self.Parent.hotkey_manager._get_key_name(event.GetKeyCode())
        self.captured_keys.add(key_name)
        self.update_display()
        event.Skip()
        
    def on_key_up(self, event):
        """Handle key up events."""
        key_name = self.Parent.hotkey_manager._get_key_name(event.GetKeyCode())
        self.captured_keys.discard(key_name)
        self.update_display()
        event.Skip()
        
    def on_mouse_left_down(self, event):
        """Handle left mouse button."""
        self.captured_mouse_actions.add(m_hotkey_manager.MouseAction.LEFT_CLICK)
        self.update_display()
        event.Skip()
        
    def on_mouse_right_down(self, event):
        """Handle right mouse button."""
        self.captured_mouse_actions.add(m_hotkey_manager.MouseAction.RIGHT_CLICK)
        self.update_display()
        event.Skip()
        
    def on_mouse_middle_down(self, event):
        """Handle middle mouse button."""
        self.captured_mouse_actions.add(m_hotkey_manager.MouseAction.MIDDLE_CLICK)
        self.update_display()
        event.Skip()
        
    def on_mouse_wheel(self, event):
        """Handle mouse wheel."""
        if event.GetWheelRotation() > 0:
            self.captured_mouse_actions.add(m_hotkey_manager.MouseAction.WHEEL_UP)
        else:
            self.captured_mouse_actions.add(m_hotkey_manager.MouseAction.WHEEL_DOWN)
        self.update_display()
        event.Skip()
        
    def update_display(self):
        """Update the display with current binding state."""
        lines = []
        if self.captured_keys:
            lines.append("Keys: " + " + ".join(sorted(self.captured_keys)))
        if self.captured_mouse_actions:
            lines.append("Mouse: " + " + ".join(a.name for a in self.captured_mouse_actions))
            
        self.display.SetValue("\n".join(lines) if lines else "Press keys or click mouse buttons...")
        
        # Enable OK button if we have a valid binding
        self.ok_btn.Enable(bool(self.captured_keys or self.captured_mouse_actions))
        
    def get_binding(self) -> Optional[m_hotkey_manager.ActionBinding]:
        """Get the captured binding."""
        if not (self.captured_keys or self.captured_mouse_actions):
            return None
            
        return m_hotkey_manager.ActionBinding(
            action_type=self.current_binding.action_type,
            keys=self.captured_keys,
            mouse_actions=self.captured_mouse_actions,
            callback=self.current_binding.callback,
            description=self.current_binding.description,
            mode_name=self.current_binding.mode_name
        )
        

class CaptureHotkeyDialog(wx.Dialog):
    """Dialog for capturing a new hotkey binding."""
    
    def __init__(self, parent):
        super().__init__(parent, title="Press New Hotkey", size=(300, 150))
        self.hotkey = None
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the dialog's UI elements."""
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Instructions
        instructions = wx.StaticText(
            panel,
            label="Press the desired key combination\n(e.g., Ctrl+S, Alt+X)"
        )
        instructions.SetForegroundColour(wx.Colour(0, 0, 0))
        sizer.Add(instructions, 0, wx.ALL | wx.ALIGN_CENTER, 10)
        
        # Display area
        self.display = wx.TextCtrl(
            panel,
            style=wx.TE_READONLY | wx.TE_CENTER
        )
        self.display.SetForegroundColour(wx.Colour(0, 0, 0))
        sizer.Add(self.display, 0, wx.EXPAND | wx.ALL, 10)
        
        # Bind key events
        self.display.Bind(wx.EVT_KEY_DOWN, self.on_key)
        self.display.Bind(wx.EVT_KEY_UP, self.on_key_up)
        
        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        ok_btn = wx.Button(panel, wx.ID_OK, "OK")
        ok_btn.Enable(False)  # Disabled until a hotkey is captured
        self.ok_btn = ok_btn
        btn_sizer.Add(ok_btn, 0, wx.ALL, 5)
        
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        btn_sizer.Add(cancel_btn, 0, wx.ALL, 5)
        
        sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        
        panel.SetSizer(sizer)
        
        # Focus the display area
        self.display.SetFocus()
        
    def on_key(self, event):
        """Handle key down events."""
        # Convert the key event to a hotkey string
        key_code = event.GetKeyCode()
        
        # Ignore modifier keys by themselves
        if key_code in (wx.WXK_CONTROL, wx.WXK_ALT, wx.WXK_SHIFT, wx.WXK_RAW_CONTROL):
            event.Skip()
            return
            
        # Build the hotkey string
        parts = []
        if event.ControlDown():
            parts.append('Ctrl')
        if event.AltDown():
            parts.append('Alt')
        if event.ShiftDown():
            parts.append('Shift')
        if event.MetaDown():  # Command key on macOS
            parts.append('Cmd')
            
        # Get the key name
        key_name = self._get_key_name(key_code)
        if key_name:
            parts.append(key_name)
            
        # Update display
        if parts:
            hotkey_str = '+'.join(parts)
            self.display.SetValue(hotkey_str)
            self.hotkey = hotkey_str
            self.ok_btn.Enable(True)
            
    def on_key_up(self, event):
        """Handle key up events."""
        # Skip the event to maintain focus
        event.Skip()
        
    def _get_key_name(self, key_code: int) -> Optional[str]:
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
            
        return None
        
    def get_hotkey(self) -> Optional[str]:
        """Get the captured hotkey string."""
        return self.hotkey
