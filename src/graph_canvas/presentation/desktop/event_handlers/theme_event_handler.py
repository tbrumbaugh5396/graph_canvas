"""
Event handlers for the theme.
"""


import wx
import os

import graph_canvas.presentation.desktop.gui.main_window as m_main_window
import graph_canvas.presentation.desktop.gui.theme_dialog as m_theme_dialog
import graph_canvas.presentation.desktop.gui.theme_list_dialog as m_theme_list_dialog

import graph_canvas.presentation.desktop.event_handlers.theme_event_handler as theme_event_handler

theme_db = None


# Theme-related methods
def on_show_themes(main_window: "m_main_window.MainWindow", event):
    """Show theme list dialog."""
    if not getattr(main_window.managers, 'theme_manager', None):
        wx.MessageBox("Theme system not available.", "Error",
                     wx.OK | wx.ICON_ERROR, main_window)
        return

    # Ensure we use the database from the manager
    db = getattr(main_window.managers.theme_manager, 'theme_database', None)
    dialog = m_theme_list_dialog.ThemeListDialog(main_window, db, main_window.managers.theme_manager)
    if dialog.ShowModal() == wx.ID_OK:
        theme = dialog.get_selected_theme()
        if theme:
            main_window.theme_manager.add_custom_theme(theme)
            main_window.theme_manager.set_theme(theme.name)
            refresh_custom_themes_menu(main_window)
            apply_current_theme(main_window)
            update_theme_menu_checks(main_window)
    dialog.Destroy()


def on_select_theme(main_window: "m_main_window.MainWindow", event, theme_name):
    """Handle theme selection from menu."""
    if hasattr(main_window, 'mvu_adapter'):
        try:
            from mvc_mvu.messages import make_message
            import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
            main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_THEME, name=theme_name))
            # Persist selection via manager for next launch
            if getattr(main_window, 'theme_database', None):
                main_window.theme_database.set_last_selected_theme(theme_name)
            return
        except Exception:
            pass

    # Legacy fallback
    if not getattr(main_window.managers, 'theme_manager', None) or not main_window.theme_database:
        return
    if main_window.managers.theme_manager.set_theme(theme_name):
        main_window.theme_database.set_last_selected_theme(theme_name)
        # Apply the theme
        theme_event_handler.apply_current_theme(main_window)
        theme_event_handler.update_theme_menu_checks(main_window)


def initialize_theme_manager(main_window: "m_main_window.MainWindow"):
    """Initialize theme manager with database themes."""
    if not getattr(main_window.managers, 'theme_manager', None):
        return
    
    # ThemeManager already loads themes from its own database and restores last selection
    if not main_window.managers.theme_manager.get_current_theme():
        main_window.managers.theme_manager.set_theme("Light")
    
    apply_current_theme(main_window)
    refresh_custom_themes_menu(main_window)
    update_theme_menu_checks(main_window)


def on_new_theme(main_window: "m_main_window.MainWindow", event, template_theme=None):
    """Handle new theme creation."""

    if not getattr(main_window.managers, 'theme_manager', None):
        wx.MessageBox("Theme system not available.", "Error",
                        wx.OK | wx.ICON_ERROR, main_window)
        return
    
    # Create dialog with optional template theme
    dialog = m_theme_dialog.ThemeDialog(
        main_window, 
        main_window.managers.theme_manager,
        template_theme,
        is_template=template_theme is not None
    )
    
    if dialog.ShowModal() == wx.ID_OK:
        theme = dialog.get_theme()
        if theme:
            main_window.managers.theme_manager.add_custom_theme(theme)
            theme_db.add_theme(theme)
            main_window.managers.theme_manager.set_theme(theme.name)
            theme_db.set_last_selected_theme(theme.name)
            refresh_custom_themes_menu(main_window)
            try:
                if hasattr(main_window, 'mvu_adapter'):
                    from mvc_mvu.messages import make_message
                    import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
                    main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_THEME, name=theme.name))
                else:
                    theme_event_handler.apply_current_theme(main_window)
                    update_theme_menu_checks(main_window)
            except Exception:
                theme_event_handler.apply_current_theme(main_window)
                update_theme_menu_checks(main_window)
    dialog.Destroy()


def on_edit_theme(main_window: "m_main_window.MainWindow", event):
    """Handle theme editing."""

    if not getattr(main_window.managers, 'theme_manager', None):
        wx.MessageBox("Theme system not available.", "Error",
                        wx.OK | wx.ICON_ERROR, main_window)
        return
    current_theme = main_window.managers.theme_manager.get_current_theme()
    if not current_theme:
        wx.MessageBox("No theme selected.", "Error", wx.OK | wx.ICON_ERROR,
                        main_window)
        return

    # Check if it's a predefined theme (cannot be edited)
    predefined_names = {
        "Light", "Dark", "High Contrast Light", "High Contrast Dark",
        "Blue", "Green", "Purple"
    }
    if current_theme.name in predefined_names:
        wx.MessageBox(
            "Predefined themes cannot be edited. Create a new theme based on this one instead.",
            "Cannot Edit", wx.OK | wx.ICON_INFORMATION, main_window)
        return

    dialog = m_theme_dialog.ThemeDialog(main_window, main_window.managers.theme_manager, current_theme)
    if dialog.ShowModal() == wx.ID_OK:
        theme = dialog.get_theme()
        if theme:
            main_window.managers.theme_manager.add_custom_theme(theme)
            main_window.managers.theme_manager.set_theme(theme.name)
            refresh_custom_themes_menu(main_window)
            try:
                if hasattr(main_window, 'mvu_adapter'):
                    from mvc_mvu.messages import make_message
                    import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
                    main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_THEME, name=theme.name))
                else:
                    apply_current_theme(main_window)
                    update_theme_menu_checks(main_window)
            except Exception:
                apply_current_theme(main_window)
                update_theme_menu_checks(main_window)
    dialog.Destroy()


def on_delete_theme(main_window: "m_main_window.MainWindow", event):
    """Handle theme deletion."""

    if not getattr(main_window.managers, 'theme_manager', None):
        wx.MessageBox("Theme system not available.", "Error",
                        wx.OK | wx.ICON_ERROR, main_window)
        return
    # Get list of custom themes
    all_themes = main_window.managers.theme_manager.get_theme_names()
    predefined_names = {
        "Light", "Dark", "High Contrast Light", "High Contrast Dark",
        "Blue", "Green", "Purple"
    }
    custom_themes = [
        name for name in all_themes if name not in predefined_names
    ]

    if not custom_themes:
        wx.MessageBox("No custom themes to delete.", "No Custom Themes",
                        wx.OK | wx.ICON_INFORMATION, main_window)
        return

    # Show selection dialog
    dialog = wx.SingleChoiceDialog(main_window, "Select a theme to delete:",
                                    "Delete Theme", custom_themes)
    if dialog.ShowModal() == wx.ID_OK:
        theme_name = dialog.GetStringSelection()

        # Confirm deletion
        result = wx.MessageBox(
            f"Are you sure you want to delete the theme '{theme_name}'?",
            "Confirm Delete", wx.YES_NO | wx.ICON_QUESTION, main_window)
        if result == wx.YES:
            if main_window.managers.theme_manager.delete_custom_theme(theme_name):
                refresh_custom_themes_menu(main_window)
                # After deletion, ThemeManager will have a current theme; propagate
                try:
                    if hasattr(main_window, 'mvu_adapter'):
                        current = main_window.managers.theme_manager.get_current_theme()
                        if current and hasattr(current, 'name'):
                            from mvc_mvu.messages import make_message
                            import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
                            main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_THEME, name=current.name))
                    else:
                        apply_current_theme(main_window)
                        update_theme_menu_checks(main_window)
                except Exception:
                    apply_current_theme(main_window)
                    update_theme_menu_checks(main_window)
                wx.MessageBox(f"Theme '{theme_name}' has been deleted.",
                                "Theme Deleted", wx.OK | wx.ICON_INFORMATION,
                                main_window)
            else:
                wx.MessageBox(f"Failed to delete theme '{theme_name}'.",
                                "Error", wx.OK | wx.ICON_ERROR, self)

    dialog.Destroy()


def refresh_custom_themes_menu(main_window: "m_main_window.MainWindow"):
    """Refresh the custom themes submenu."""

    if not getattr(main_window.managers, 'theme_manager', None):
        return
    if not hasattr(
            main_window,
            'custom_themes_submenu') or not main_window.custom_themes_submenu:
        print("Warning: Custom themes submenu not initialized")
        return

    # Clear current items
    for item in main_window.custom_themes_submenu.GetMenuItems():
        main_window.custom_themes_submenu.DestroyItem(item)

    # Add custom themes
    all_themes = main_window.managers.theme_manager.get_theme_names()
    predefined_names = {
        "Light", "Dark", "High Contrast Light", "High Contrast Dark",
        "Blue", "Green", "Purple"
    }
    custom_themes = [
        name for name in all_themes if name not in predefined_names
    ]

    if custom_themes:
        for theme_name in sorted(custom_themes):
            item = main_window.custom_themes_submenu.AppendRadioItem(
                wx.ID_ANY, theme_name)
            main_window.theme_menu_items[theme_name] = item
            main_window.Bind(wx.EVT_MENU,
                        lambda evt, name=theme_name: theme_event_handler.on_select_theme(main_window,
                            evt, name),
                        item)
    else:
        # Add disabled placeholder
        item = main_window.custom_themes_submenu.Append(wx.ID_ANY,
                                                    "(No custom themes)")
        item.Enable(False)


def update_theme_menu_checks(main_window: "m_main_window.MainWindow"):
    """Update the theme menu radio button checks."""

    if not hasattr(main_window, 'theme_menu_items') or not main_window.theme_menu_items:
        return

    current_theme = main_window.managers.theme_manager.get_current_theme()
    if current_theme:
        for theme_name, menu_item in main_window.theme_menu_items.items():
            try:
                menu_item.Check(theme_name == current_theme.name)
            except:
                pass  # Ignore errors for individual menu items


def apply_current_theme(main_window: "m_main_window.MainWindow"):
    """Apply the current theme to all UI elements."""

    if not getattr(main_window.managers, 'theme_manager', None) or not main_window.managers.theme_manager.get_current_theme(
    ):
        return

    # Apply to main window
    main_window.managers.theme_manager.apply_theme_to_window(main_window)

    # Apply to canvas if it exists
    if hasattr(main_window, 'canvas') and main_window.canvas:
        main_window.managers.theme_manager.apply_theme_to_window(main_window.canvas)
    
    # Ensure checker color button text remains black
    if hasattr(main_window, 'checker_color1_btn') and main_window.checker_color1_btn:
        main_window.checker_color1_btn.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text


def apply_theme_to_dialog(main_window: "m_main_window.MainWindow", dialog):
    """Apply current theme to a dialog window."""

    if getattr(main_window.managers, 'theme_manager', None):
        main_window.managers.theme_manager.apply_theme_to_window(dialog)
