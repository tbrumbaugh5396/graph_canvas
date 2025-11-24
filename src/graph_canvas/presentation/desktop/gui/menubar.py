"""
Menubar for the graph editor application.
"""


import wx

from functools import partial
from typing import TYPE_CHECKING
import graph_canvas.presentation.desktop.gui.main_window as m_main_window

import graph_canvas.presentation.desktop.gui.layouts as m_layouts
import graph_canvas.presentation.desktop.event_handlers.menubar_event_handler as m_menubar_event_handler
import graph_canvas.presentation.desktop.event_handlers.theme_event_handler as m_theme_event_handler


def setup_menus(main_window: "m_main_window.MainWindow"):
        """Set up the menu bar."""

        print("DEBUG: setup_menus() started")
        menubar = wx.MenuBar()

        # File menu
        file_menu = wx.Menu()

        new_item = file_menu.Append(wx.ID_NEW, "&New Graph\tCtrl+N",
                                    "Create a new graph")
        open_item = file_menu.Append(wx.ID_OPEN, "&Open Graph\tCtrl+O",
                                     "Open an existing graph")
        save_item = file_menu.Append(wx.ID_SAVE, "&Save Graph\tCtrl+S",
                                     "Save the current graph")
        saveas_item = file_menu.Append(wx.ID_SAVEAS,
                                       "Save &As...\tCtrl+Shift+S",
                                       "Save graph with a new name")
        file_menu.AppendSeparator()
        import_item = file_menu.Append(wx.ID_ANY, "&Import Graph...",
                                       "Import another graph into current")
        copy_graph_item = file_menu.Append(wx.ID_ANY, "&Copy Graph...",
                                     "Copy current graph")
        delete_graph_item = file_menu.Append(wx.ID_ANY, "&Delete Graph...",
                                       "Delete a graph")
        file_menu.AppendSeparator()
        exit_item = file_menu.Append(wx.ID_EXIT, "E&xit\tCtrl+Q",
                                     "Exit the application")

        # Edit menu
        edit_menu = wx.Menu()

        main_window.undo_item = edit_menu.Append(wx.ID_UNDO, "&Undo\tCtrl+Z",
                                     "Undo last action")
        main_window.redo_item = edit_menu.Append(wx.ID_REDO, "&Redo\tCtrl+Y",
                                     "Redo last action")
        edit_menu.AppendSeparator()
        cut_item = edit_menu.Append(wx.ID_CUT, "Cu&t\tCtrl+X",
                                    "Cut selected items")
        copy_item = edit_menu.Append(wx.ID_COPY, "&Copy\tCtrl+C",
                                     "Copy selected items")
        paste_item = edit_menu.Append(wx.ID_PASTE, "&Paste\tCtrl+V",
                                      "Paste items")
        delete_item = edit_menu.Append(wx.ID_DELETE, "&Delete\tDel",
                                       "Delete selected items")
        edit_menu.AppendSeparator()
        selectall_item = edit_menu.Append(wx.ID_SELECTALL,
                                          "Select &All\tCtrl+A",
                                          "Select all items")
        edit_menu.AppendSeparator()
        preferences_item = edit_menu.Append(wx.ID_ANY, "&Preferences...",
                                           "Edit application preferences")

        # View menu
        view_menu = wx.Menu()

        zoom_in_item = view_menu.Append(wx.ID_ZOOM_IN, "Zoom &In\tCtrl++",
                                        "Zoom in")
        zoom_out_item = view_menu.Append(wx.ID_ZOOM_OUT, "Zoom &Out\tCtrl+-",
                                         "Zoom out")
        zoom_fit_item = view_menu.Append(wx.ID_ZOOM_FIT,
                                         "Zoom to &Fit\tCtrl+0",
                                         "Zoom to fit all")
        view_menu.AppendSeparator()
        grid_item = view_menu.AppendCheckItem(wx.ID_ANY, "Show &Grid",
                                              "Show/hide grid")
        grid_item.Check(main_window.current_graph.grid_visible)
        view_menu.AppendSeparator()
        
        # Panel toggle items
        sidebar_item = view_menu.AppendCheckItem(wx.ID_ANY, "Show &Sidebar",
                                                "Show/hide sidebar panel")
        sidebar_item.Check(True)  # Sidebar is visible by default
        
        status_bar_item = view_menu.AppendCheckItem(wx.ID_ANY, "Show &Status Bar",
                                                   "Show/hide status bar panel")
        status_bar_item.Check(True)  # Status bar is visible by default
        
        view_menu.AppendSeparator()
        background_item = view_menu.Append(wx.ID_ANY, "&Background Layers...",
                                         "Manage background images and layers")

        # Layout menu
        layout_menu = wx.Menu()

        spring_item = layout_menu.Append(wx.ID_ANY, "&Spring Layout",
                                         "Apply spring layout")
        circle_item = layout_menu.Append(wx.ID_ANY, "&Circle Layout",
                                         "Apply circle layout")
        tree_item = layout_menu.Append(wx.ID_ANY, "&Tree Layout",
                                       "Apply tree layout")
        random_item = layout_menu.Append(wx.ID_ANY, "&Random Layout",
                                         "Apply random layout")

        # Theme menu (simplified for testing)
        print("DEBUG: Creating Theme menu...")

        # Initialize theme-related attributes early to prevent AttributeError
        main_window.theme_menu_items = {}
        main_window.custom_themes_submenu = wx.Menu()
        print("DEBUG: Theme menu attributes initialized")

        theme_menu = wx.Menu()

        try:
            # Add theme items directly to main theme menu (no submenus for now)
            if getattr(main_window.managers, 'theme_manager', None):
                theme_count = len(main_window.managers.theme_manager.get_theme_names())
                print(
                    f"DEBUG: ThemeManager available, adding {theme_count} themes"
                )

                # Add all themes as radio items
                predefined_names = {
                    "Light", "Dark", "High Contrast Light",
                    "High Contrast Dark", "Blue", "Green", "Purple"
                }
                
                # Add predefined themes first
                for theme_name in sorted(predefined_names):
                    if theme_name in main_window.managers.theme_manager.get_theme_names():
                        item = theme_menu.AppendRadioItem(wx.ID_ANY, theme_name)
                        main_window.theme_menu_items[theme_name] = item
                        main_window.Bind(wx.EVT_MENU,
                                  lambda evt, name=theme_name: m_theme_event_handler.on_select_theme(main_window, evt, name),
                                  item)
                        print(f"DEBUG: Added predefined theme: {theme_name}")
                
                # Add separator between predefined and custom themes
                theme_menu.AppendSeparator()
                
                # Add custom themes
                custom_themes = [name for name in main_window.managers.theme_manager.get_theme_names()
                               if name not in predefined_names]
                for theme_name in sorted(custom_themes):
                    item = theme_menu.AppendRadioItem(wx.ID_ANY, theme_name)
                    main_window.theme_menu_items[theme_name] = item
                    main_window.Bind(wx.EVT_MENU,
                                lambda evt, name=theme_name: m_theme_event_handler.on_select_theme(main_window, evt, name),
                                item)
                    print(f"DEBUG: Added custom theme: {theme_name}")
                
                # Separator before management items
                theme_menu.AppendSeparator()
            else:
                print("DEBUG: Theme manager not available, adding placeholder")
                placeholder = theme_menu.Append(wx.ID_ANY,
                                                "(Themes unavailable)")
                placeholder.Enable(False)
                theme_menu.AppendSeparator()

            print("DEBUG: Theme items added successfully")

        except Exception as e:
            print(f"ERROR: Failed to set up theme menu: {e}")
            import traceback
            traceback.print_exc()
            # Make sure we still have basic menu structure
            if not hasattr(main_window, 'theme_menu_items'):
                main_window.theme_menu_items = {}
            if not hasattr(main_window, 'custom_themes_submenu'):
                main_window.custom_themes_submenu = wx.Menu()

        # Theme management items
        theme_list_item = theme_menu.Append(wx.ID_ANY, "&Manage Themes...",
                                          "View and manage all themes")
        theme_menu.AppendSeparator()
        new_theme_item = theme_menu.Append(wx.ID_ANY, "&New Theme...",
                                         "Create a new custom theme")
        edit_theme_item = theme_menu.Append(wx.ID_ANY, "&Edit Theme...",
                                          "Edit the current theme")
        delete_theme_item = theme_menu.Append(wx.ID_ANY, "&Delete Theme...",
                                            "Delete a custom theme")

        print("DEBUG: Theme management items added")

        # Help menu
        help_menu = wx.Menu()

        about_item = help_menu.Append(wx.ID_ABOUT, "&About",
                                      "About this application")

        # Add menus to menubar
        print("DEBUG: Adding menus to menubar...")
        menubar.Append(file_menu, "&File")
        menubar.Append(edit_menu, "&Edit")
        menubar.Append(view_menu, "&View")
        # Settings menu
        settings_menu = wx.Menu()
        hotkeys_item = settings_menu.Append(wx.ID_ANY, "&Hotkeys...\tCtrl+K", "Configure keyboard shortcuts")

        menubar.Append(layout_menu, "&Layout")
        menubar.Append(theme_menu, "&Theme")
        menubar.Append(settings_menu, "&Settings")
        menubar.Append(help_menu, "&Help")
        print("DEBUG: Theme menu added to menubar")

        main_window.SetMenuBar(menubar)
        print("DEBUG: Menubar set on window")

        # Verify the menubar was set
        current_menubar = main_window.GetMenuBar()
        if current_menubar:
            menu_count = current_menubar.GetMenuCount()
            print(f"DEBUG: Menubar has {menu_count} menus:")
            for i in range(menu_count):
                menu_label = current_menubar.GetMenuLabelText(i)
                print(f"  {i}: {menu_label}")
        else:
            print("ERROR: No menubar found after SetMenuBar!")

        # Bind menu events
        main_window.Bind(wx.EVT_MENU, partial(m_menubar_event_handler.on_new_graph, main_window), new_item)
        main_window.Bind(wx.EVT_MENU, partial(m_menubar_event_handler.on_open_graph, main_window), open_item)
        main_window.Bind(wx.EVT_MENU, partial(m_menubar_event_handler.on_save_graph, main_window), save_item)
        main_window.Bind(wx.EVT_MENU, partial(m_menubar_event_handler.on_save_graph_as, main_window), saveas_item)
        main_window.Bind(wx.EVT_MENU, partial(m_menubar_event_handler.on_import_graph, main_window), import_item)
        main_window.Bind(wx.EVT_MENU, partial(m_menubar_event_handler.on_copy_graph, main_window), copy_graph_item)
        main_window.Bind(wx.EVT_MENU, partial(m_menubar_event_handler.on_delete_graph, main_window), delete_graph_item)
        main_window.Bind(wx.EVT_MENU, partial(m_menubar_event_handler.on_exit, main_window), exit_item)

        main_window.Bind(wx.EVT_MENU, partial(m_menubar_event_handler.on_undo, main_window), main_window.undo_item)
        main_window.Bind(wx.EVT_MENU, partial(m_menubar_event_handler.on_redo, main_window), main_window.redo_item)
        main_window.Bind(wx.EVT_MENU, partial(m_menubar_event_handler.on_cut_selected, main_window), cut_item)
        main_window.Bind(wx.EVT_MENU, partial(m_menubar_event_handler.on_copy_selected, main_window), copy_item)
        main_window.Bind(wx.EVT_MENU, partial(m_menubar_event_handler.on_paste_selected, main_window), paste_item)
        main_window.Bind(wx.EVT_MENU, partial(m_menubar_event_handler.on_delete_selected, main_window), delete_item)
        main_window.Bind(wx.EVT_MENU, partial(m_menubar_event_handler.on_select_all, main_window), selectall_item)
        main_window.Bind(wx.EVT_MENU, partial(m_menubar_event_handler.on_preferences, main_window), preferences_item)

        main_window.Bind(wx.EVT_MENU, partial(m_menubar_event_handler.on_zoom_in, main_window), zoom_in_item)
        main_window.Bind(wx.EVT_MENU, partial(m_menubar_event_handler.on_zoom_out, main_window), zoom_out_item)
        main_window.Bind(wx.EVT_MENU, partial(m_menubar_event_handler.on_zoom_fit, main_window), zoom_fit_item)
        main_window.Bind(wx.EVT_MENU, partial(m_menubar_event_handler.on_toggle_grid, main_window), grid_item)
        
        # Bind panel toggle events
        main_window.Bind(wx.EVT_MENU, partial(m_menubar_event_handler.on_toggle_sidebar, main_window), sidebar_item)
        main_window.Bind(wx.EVT_MENU, partial(m_menubar_event_handler.on_toggle_status_bar, main_window), status_bar_item)
        
        main_window.Bind(wx.EVT_MENU, partial(m_menubar_event_handler.on_background_layers, main_window), background_item)

        main_window.Bind(wx.EVT_MENU, partial(m_layouts.on_spring_layout, main_window), spring_item)
        main_window.Bind(wx.EVT_MENU, partial(m_layouts.on_circle_layout, main_window), circle_item)
        main_window.Bind(wx.EVT_MENU, partial(m_layouts.on_tree_layout, main_window), tree_item)
        main_window.Bind(wx.EVT_MENU, partial(m_layouts.on_random_layout, main_window), random_item)

        # Bind theme menu events
        print("DEBUG: Binding theme menu events...")
        main_window.Bind(wx.EVT_MENU, partial(m_theme_event_handler.on_show_themes, main_window), theme_list_item)
        main_window.Bind(wx.EVT_MENU, partial(m_theme_event_handler.on_new_theme, main_window), new_theme_item)
        main_window.Bind(wx.EVT_MENU, partial(m_theme_event_handler.on_edit_theme, main_window), edit_theme_item)
        main_window.Bind(wx.EVT_MENU, partial(m_theme_event_handler.on_delete_theme, main_window), delete_theme_item)
        print("DEBUG: Theme menu events bound")

        main_window.Bind(wx.EVT_MENU, partial(m_menubar_event_handler.on_about, main_window), about_item)
        main_window.Bind(wx.EVT_MENU, partial(m_menubar_event_handler.on_configure_hotkeys, main_window), hotkeys_item)

        print("DEBUG: setup_menus() completed successfully")
        print(
            f"DEBUG: custom_themes_submenu exists: {hasattr(main_window, 'custom_themes_submenu')}"
        )


def setup_menus_duplicate_DISABLED(main_window: "m_main_window.MainWindow"):
    """DISABLED - Duplicate setup_menus method that was overriding the theme menu setup."""

    return  # Exit early to disable this duplicate method

    menubar = wx.MenuBar()

    # File menu
    file_menu = wx.Menu()
    file_menu.Append(wx.ID_NEW, "&New\tCtrl+N", "Create a new graph")
    file_menu.Append(wx.ID_OPEN, "&Open\tCtrl+O", "Open a graph file")
    file_menu.Append(wx.ID_SAVE, "&Save\tCtrl+S", "Save the current graph")
    file_menu.Append(wx.ID_SAVEAS, "Save &As\tCtrl+Shift+S",
                        "Save the graph with a new name")
    file_menu.AppendSeparator()
    file_menu.Append(wx.ID_EXIT, "E&xit\tCtrl+Q", "Exit the application")
    menubar.Append(file_menu, "&File")

    # Edit menu
    edit_menu = wx.Menu()
    edit_menu.Append(wx.ID_UNDO, "&Undo\tCtrl+Z", "Undo the last action")
    edit_menu.Append(wx.ID_REDO, "&Redo\tCtrl+Y",
                        "Redo the last undone action")
    edit_menu.AppendSeparator()
    edit_menu.Append(wx.ID_CUT, "Cu&t\tCtrl+X", "Cut selected items")
    edit_menu.Append(wx.ID_COPY, "&Copy\tCtrl+C", "Copy selected items")
    edit_menu.Append(wx.ID_PASTE, "&Paste\tCtrl+V",
                        "Paste items from clipboard")
    edit_menu.Append(wx.ID_DELETE, "&Delete\tDel", "Delete selected items")
    edit_menu.AppendSeparator()
    edit_menu.Append(wx.ID_SELECTALL, "Select &All\tCtrl+A",
                        "Select all items")
    menubar.Append(edit_menu, "&Edit")

    # View menu
    view_menu = wx.Menu()
    zoom_fit_id = wx.NewId()
    view_menu.Append(zoom_fit_id, "Zoom to &Fit\tCtrl+0",
                        "Zoom to fit all content")
    view_menu.Append(wx.ID_ZOOM_IN, "Zoom &In\tCtrl++", "Zoom in")
    view_menu.Append(wx.ID_ZOOM_OUT, "Zoom &Out\tCtrl+-", "Zoom out")
    reset_view_id = wx.NewId()
    view_menu.Append(reset_view_id, "&Reset View\tCtrl+R",
                        "Reset zoom, pan, and rotation")
    view_menu.AppendSeparator()
    
    # Grid submenu
    grid_submenu = wx.Menu()
    toggle_grid_id = wx.NewId()
    grid_submenu.Append(toggle_grid_id, "&Toggle Grid\tCtrl+G",
                        "Show/hide grid", wx.ITEM_CHECK)
    view_menu.AppendSubMenu(grid_submenu, "&Grid")
    
    menubar.Append(view_menu, "&View")

    # Layout menu
    layout_menu = wx.Menu()
    
    # Force-directed layout
    force_layout_id = wx.NewId()
    layout_menu.Append(force_layout_id, "&Force-Directed Layout",
                        "Apply spring-based force layout")
    
    # Circular layout
    circular_layout_id = wx.NewId()
    layout_menu.Append(circular_layout_id, "&Circular Layout",
                        "Arrange nodes in a circle")
    
    # Grid layout
    grid_layout_id = wx.NewId()
    layout_menu.Append(grid_layout_id, "&Grid Layout",
                        "Arrange nodes in a grid pattern")
    
    # Tree layout
    tree_layout_id = wx.NewId()
    layout_menu.Append(tree_layout_id, "&Tree Layout",
                        "Arrange nodes in a tree structure")
    
    # Hierarchical layout
    hierarchical_layout_id = wx.NewId()
    layout_menu.Append(hierarchical_layout_id, "&Hierarchical Layout",
                        "Arrange nodes in layers")
    
    # Random layout
    random_layout_id = wx.NewId()
    layout_menu.Append(random_layout_id, "&Random Layout",
                        "Randomly distribute nodes")
    
    layout_menu.AppendSeparator()
    
    # Non-overlapping layout
    non_overlapping_layout_id = wx.NewId()
    layout_menu.Append(non_overlapping_layout_id,
                        "&Non-Overlapping Layout",
                        "Arrange nodes to prevent overlaps")
    
    # Minimize edge overlap layout
    minimize_edge_overlap_id = wx.NewId()
    layout_menu.Append(minimize_edge_overlap_id, "&Minimize Edge Overlaps",
                        "Arrange to reduce edge intersections")
    
    menubar.Append(layout_menu, "&Layout")

    # Tools menu
    tools_menu = wx.Menu()
    tools_menu.Append(wx.ID_PREFERENCES, "&Preferences\tCtrl+,",
                        "Open preferences dialog")
    menubar.Append(tools_menu, "&Tools")

    # Help menu
    help_menu = wx.Menu()
    help_menu.Append(wx.ID_ABOUT, "&About", "Show about dialog")
    menubar.Append(help_menu, "&Help")

    main_window.SetMenuBar(menubar)

    # Bind menu events
    main_window.Bind(wx.EVT_MENU, main_window.on_new_graph, id=wx.ID_NEW)
    main_window.Bind(wx.EVT_MENU, main_window.on_open_graph, id=wx.ID_OPEN)
    main_window.Bind(wx.EVT_MENU, main_window.on_save_graph, id=wx.ID_SAVE)
    main_window.Bind(wx.EVT_MENU, main_window.on_save_as_graph, id=wx.ID_SAVEAS)
    main_window.Bind(wx.EVT_MENU, main_window.on_close, id=wx.ID_EXIT)
    
    main_window.Bind(wx.EVT_MENU, main_window.on_undo, id=wx.ID_UNDO)
    main_window.Bind(wx.EVT_MENU, main_window.on_redo, id=wx.ID_REDO)
    main_window.Bind(wx.EVT_MENU, main_window.on_cut_selected, id=wx.ID_CUT)
    main_window.Bind(wx.EVT_MENU, main_window.on_copy_selected, id=wx.ID_COPY)
    main_window.Bind(wx.EVT_MENU, main_window.on_paste_selected, id=wx.ID_PASTE)
    main_window.Bind(wx.EVT_MENU, main_window.on_delete_selected, id=wx.ID_DELETE)
    main_window.Bind(wx.EVT_MENU, main_window.on_select_all, id=wx.ID_SELECTALL)
    
    main_window.Bind(wx.EVT_MENU, main_window.on_zoom_to_fit, id=zoom_fit_id)
    main_window.Bind(wx.EVT_MENU, main_window.on_zoom_in, id=wx.ID_ZOOM_IN)
    main_window.Bind(wx.EVT_MENU, main_window.on_zoom_out, id=wx.ID_ZOOM_OUT)
    main_window.Bind(wx.EVT_MENU, main_window.on_reset_view, id=reset_view_id)
    main_window.Bind(wx.EVT_MENU, main_window.on_toggle_grid, id=toggle_grid_id)
    
    main_window.Bind(wx.EVT_MENU, partial(m_layouts.on_force_layout, main_window), id=force_layout_id)
    main_window.Bind(wx.EVT_MENU, partial(m_layouts.on_circular_layout, main_window), id=circular_layout_id)
    main_window.Bind(wx.EVT_MENU, partial(m_layouts.on_grid_layout, main_window), id=grid_layout_id)
    main_window.Bind(wx.EVT_MENU, partial(m_layouts.on_tree_layout, main_window), id=tree_layout_id)
    main_window.Bind(wx.EVT_MENU,
                partial(m_layouts.on_hierarchical_layout, main_window),
                id=hierarchical_layout_id)
    main_window.Bind(wx.EVT_MENU, partial(m_layouts.on_random_layout, main_window), id=random_layout_id)
    main_window.Bind(wx.EVT_MENU,
                partial(m_layouts.on_non_overlapping_layout, main_window),
                id=non_overlapping_layout_id)
    main_window.Bind(wx.EVT_MENU,
                partial(m_layouts.on_minimize_edge_overlap_layout, main_window),
                id=minimize_edge_overlap_id)
    
    main_window.Bind(wx.EVT_MENU, main_window.on_preferences, id=wx.ID_PREFERENCES)
    main_window.Bind(wx.EVT_MENU, main_window.on_about, id=wx.ID_ABOUT)


def setup_menus_duplicate2_DISABLED(main_window: "m_main_window.MainWindow"):
    """DISABLED - Another duplicate setup_menus method that was overriding the theme menu setup."""

    return  # Exit early to disable this duplicate method

    menubar = wx.MenuBar()
    
    # File menu
    file_menu = wx.Menu()
    
    # New
    new_item = file_menu.Append(wx.ID_NEW, "&New\tCtrl+N",
                                "Create a new graph")
    main_window.Bind(wx.EVT_MENU, main_window.on_new, new_item)
    
    file_menu.AppendSeparator()
    
    # Open DOT file
    open_dot_item = file_menu.Append(wx.ID_ANY,
                                        "&Open DOT File...\tCtrl+O",
                                        "Open a DOT format graph file")
    main_window.Bind(wx.EVT_MENU, main_window.on_open_dot, open_dot_item)
    
    # Save as DOT file
    save_dot_item = file_menu.Append(wx.ID_ANY, "&Save as DOT...\tCtrl+S",
                                        "Save graph as DOT format file")
    main_window.Bind(wx.EVT_MENU, main_window.on_save_dot, save_dot_item)
    
    # Save as DOT file (undirected)
    save_dot_undirected_item = file_menu.Append(
        wx.ID_ANY, "Save as &Undirected DOT...",
        "Save graph as undirected DOT format file")
    main_window.Bind(wx.EVT_MENU, main_window.on_save_dot_undirected,
                save_dot_undirected_item)

    # Save as DOT file (mixed edges with auto-detection)
    save_dot_mixed_item = file_menu.Append(
        wx.ID_ANY, "Save as &Mixed DOT...",
        "Save graph with auto-detected edge types (supports both directed and undirected)"
    )
    main_window.Bind(wx.EVT_MENU, main_window.on_save_dot_mixed, save_dot_mixed_item)
    
    file_menu.AppendSeparator()
    
    # Import/Export submenu
    import_export_menu = wx.Menu()
    
    # Export to standard Graphviz
    export_graphviz_item = import_export_menu.Append(
        wx.ID_ANY, "Export for &Graphviz...",
        "Export DOT file optimized for standard Graphviz tools")
    main_window.Bind(wx.EVT_MENU, main_window.on_export_graphviz, export_graphviz_item)
    
    file_menu.AppendSubMenu(import_export_menu, "&Import/Export",
                            "Import and export options")
    
    file_menu.AppendSeparator()
    
    # Recent files submenu
    main_window.recent_menu = wx.Menu()
    file_menu.AppendSubMenu(main_window.recent_menu, "&Recent Files",
                            "Recently opened files")
    
    file_menu.AppendSeparator()
    
    # Exit
    exit_item = file_menu.Append(wx.ID_EXIT, "E&xit\tCtrl+Q",
                                    "Exit the application")
    main_window.Bind(wx.EVT_MENU, partial(m_menubar_event_handler.on_exit, main_window), exit_item)
    
    menubar.Append(file_menu, "&File")
    
    # Edit menu
    edit_menu = wx.Menu()
    
    # Undo/Redo
    undo_item = edit_menu.Append(wx.ID_UNDO, "&Undo\tCtrl+Z",
                                    "Undo the last action")
    redo_item = edit_menu.Append(wx.ID_REDO, "&Redo\tCtrl+Y",
                                    "Redo the last undone action")
    main_window.Bind(wx.EVT_MENU, main_window.on_undo, undo_item)
    main_window.Bind(wx.EVT_MENU, main_window.on_redo, redo_item)
    
    edit_menu.AppendSeparator()
    
    # Copy/Paste
    copy_item = edit_menu.Append(wx.ID_COPY, "&Copy\tCtrl+C",
                                    "Copy selected items")
    paste_item = edit_menu.Append(wx.ID_PASTE, "&Paste\tCtrl+V",
                                    "Paste copied items")
    main_window.Bind(wx.EVT_MENU, main_window.on_copy, copy_item)
    main_window.Bind(wx.EVT_MENU, main_window.on_paste, paste_item)
    
    edit_menu.AppendSeparator()
    
    # Select All
    select_all_item = edit_menu.Append(wx.ID_SELECTALL,
                                        "Select &All\tCtrl+A",
                                        "Select all items")
    main_window.Bind(wx.EVT_MENU, main_window.on_select_all, select_all_item)
    
    menubar.Append(edit_menu, "&Edit")
    
    # View menu
    view_menu = wx.Menu()
    
    # Zoom
    zoom_in_item = view_menu.Append(wx.ID_ZOOM_IN, "Zoom &In\tCtrl+=",
                                    "Zoom in")
    zoom_out_item = view_menu.Append(wx.ID_ZOOM_OUT, "Zoom &Out\tCtrl+-",
                                        "Zoom out")
    zoom_fit_item = view_menu.Append(wx.ID_ZOOM_FIT,
                                        "Zoom to &Fit\tCtrl+0",
                                        "Zoom to fit all content")
    
    main_window.Bind(wx.EVT_MENU, main_window.on_zoom_in, zoom_in_item)
    main_window.Bind(wx.EVT_MENU, main_window.on_zoom_out, zoom_out_item)
    main_window.Bind(wx.EVT_MENU, main_window.on_zoom_fit, zoom_fit_item)
    
    menubar.Append(view_menu, "&View")
    
    # Layout menu
    layout_menu = wx.Menu()
    
    # Force-directed layouts
    spring_item = layout_menu.Append(wx.ID_ANY, "&Spring Layout\tCtrl+L",
                                        "Apply force-directed spring layout")
    main_window.Bind(wx.EVT_MENU, partial(m_layouts.on_spring_layout, main_window), spring_item)
    
    layout_menu.AppendSeparator()
    
    # Geometric layouts
    circle_item = layout_menu.Append(wx.ID_ANY, "&Circle Layout",
                                        "Arrange nodes in a circle")
    tree_item = layout_menu.Append(
        wx.ID_ANY, "&Tree Layout",
        "Arrange nodes in hierarchical tree structure")
    grid_item = layout_menu.Append(wx.ID_ANY, "&Grid Layout",
                                    "Arrange nodes in a regular grid")
    
    main_window.Bind(wx.EVT_MENU, partial(m_layouts.on_circle_layout, main_window), circle_item)
    main_window.Bind(wx.EVT_MENU, partial(m_layouts.on_tree_layout, main_window), tree_item)
    main_window.Bind(wx.EVT_MENU, partial(m_layouts.on_grid_layout, main_window), grid_item)
    
    layout_menu.AppendSeparator()
    
    # Specialized layouts
    radial_item = layout_menu.Append(wx.ID_ANY, "&Radial Layout",
                                        "Arrange nodes radially from center")
    layered_item = layout_menu.Append(
        wx.ID_ANY, "&Layered Layout", "Arrange nodes in horizontal layers")
    organic_item = layout_menu.Append(
        wx.ID_ANY, "&Organic Layout",
        "Apply organic force-directed layout")
    
    main_window.Bind(wx.EVT_MENU, partial(m_layouts.on_radial_layout, main_window), radial_item)
    main_window.Bind(wx.EVT_MENU, partial(m_layouts.on_layered_layout, main_window), layered_item)
    main_window.Bind(wx.EVT_MENU, partial(m_layouts.on_organic_layout, main_window), organic_item)
    
    layout_menu.AppendSeparator()
    
    # Utility layouts
    random_item = layout_menu.Append(wx.ID_ANY, "R&andom Layout",
                                        "Randomly position all nodes")
    compact_item = layout_menu.Append(
        wx.ID_ANY, "Co&mpact Layout",
        "Minimize graph area while preserving relationships")
    
    main_window.Bind(wx.EVT_MENU, partial(m_layouts.on_random_layout, main_window), random_item)
    main_window.Bind(wx.EVT_MENU, partial(m_layouts.on_compact_layout, main_window), compact_item)
    
    menubar.Append(layout_menu, "&Layout")
    
    # Help menu
    help_menu = wx.Menu()
    
    # About
    about_item = help_menu.Append(wx.ID_ABOUT, "&About",
                                    "About this application")
    main_window.Bind(wx.EVT_MENU, main_window.on_about, about_item)
    
    menubar.Append(help_menu, "&Help")
    
    main_window.SetMenuBar(menubar)
    
    # Update recent files menu
    main_window.update_recent_files_menu()
