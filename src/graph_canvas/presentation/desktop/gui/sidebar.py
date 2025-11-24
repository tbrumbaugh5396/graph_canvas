"""
Sidebar for the graph editor application.
"""


import wx
from functools import partial

import graph_canvas.presentation.desktop.event_handlers as event_handlers
import graph_canvas.presentation.desktop.event_handlers.sidebar_event_handler as m_sidebar_event_handler
import graph_canvas.presentation.desktop.event_handlers.graph_canvas_event_handler as m_graph_canvas_event_handler

import graph_canvas.presentation.desktop.gui.main_window as m_main_window
import graph_canvas.presentation.desktop.gui.selector as m_selector
import graph_canvas.presentation.desktop.gui.dependency_list_panel as m_dependency_list_panel


    # Create sidebar for properties with scrolling capability
def setup_sidebar(main_window: "m_main_window.MainWindow"):
    main_window.sidebar = wx.ScrolledWindow(main_window.horizontal_splitter, size=(250, -1))
    main_window.sidebar.SetBackgroundColour(wx.Colour(245, 245, 245))  # Higher contrast sidebar
    main_window.sidebar.SetForegroundColour(wx.Colour(0, 0, 0))  # Default to black text
    main_window.sidebar.SetScrollRate(5, 20)  # Set scroll rates (x pixels, y pixels per unit)

    # Sidebar content
    sidebar_sizer = wx.BoxSizer(wx.VERTICAL)

    # Expand/Collapse All buttons (moved to top)
    expand_collapse_sizer = wx.BoxSizer(wx.HORIZONTAL)
    
    main_window.expand_all_btn = wx.Button( main_window.sidebar, label="Expand All", size=(80, 28))
    main_window.expand_all_btn.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.expand_all_btn.Bind(wx.EVT_BUTTON,  partial(m_sidebar_event_handler.on_expand_all_sections, main_window))
    expand_collapse_sizer.Add( main_window.expand_all_btn, 0, wx.ALL, 2)
    
    main_window.collapse_all_btn = wx.Button( main_window.sidebar, label="Collapse All", size=(80, 28))
    main_window.collapse_all_btn.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.collapse_all_btn.Bind(wx.EVT_BUTTON,  partial(m_sidebar_event_handler.on_collapse_all_sections, main_window))
    expand_collapse_sizer.Add(main_window.collapse_all_btn, 0, wx.ALL, 2)
    
    sidebar_sizer.Add(expand_collapse_sizer, 0, wx.EXPAND | wx.ALL, 5)

    # Store collapsible panes for expand/collapse all functionality
    main_window.collapsible_panes = []

    # Grid options (now collapsible)
    main_window.grid_options_pane = wx.CollapsiblePane(main_window.sidebar, label="Grid Options")
    main_window.grid_options_pane.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.collapsible_panes.append(main_window.grid_options_pane)
    # Bind individual pane expansion events
    main_window.grid_options_pane.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, partial(m_sidebar_event_handler.on_individual_pane_changed, main_window))
    sidebar_sizer.Add(main_window.grid_options_pane, 0, wx.EXPAND | wx.ALL, 5)
    
    grid_options_window = main_window.grid_options_pane.GetPane()
    grid_options_sizer = wx.BoxSizer(wx.VERTICAL)

    # Grid style choice
    grid_style_sizer = wx.BoxSizer(wx.HORIZONTAL)
    grid_style_label = wx.StaticText(grid_options_window, label="Grid Style:")
    grid_style_sizer.Add(grid_style_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
    
    main_window.grid_style_choice = wx.Choice(grid_options_window, choices=["None", "Grid", "Dots"])
    main_window.grid_style_choice.SetSelection(1)  # Default to Grid
    main_window.grid_style_choice.Bind(wx.EVT_CHOICE, partial(m_graph_canvas_event_handler.on_grid_style_changed, main_window))
    grid_style_sizer.Add(main_window.grid_style_choice, 1, wx.EXPAND)
    grid_options_sizer.Add(grid_style_sizer, 0, wx.EXPAND | wx.ALL, 5)
    
    # Store reference to the main grid style choice for synchronization
    main_window.main_grid_style_choice = main_window.grid_style_choice

    # Grid spacing
    spacing_sizer = wx.BoxSizer(wx.HORIZONTAL)
    spacing_label = wx.StaticText(grid_options_window, label="Spacing:")
    spacing_sizer.Add(spacing_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
    
    main_window.grid_spacing_field = wx.SpinCtrlDouble(grid_options_window, min=10, max=200, initial=50, inc=10)
    main_window.grid_spacing_field.Bind(wx.EVT_SPINCTRLDOUBLE, partial(m_graph_canvas_event_handler.on_grid_spacing_changed, main_window))
    spacing_sizer.Add(main_window.grid_spacing_field, 1, wx.EXPAND)
    grid_options_sizer.Add(spacing_sizer, 0, wx.EXPAND | wx.ALL, 5)

    # Snap to grid toggle
    main_window.snap_to_grid_cb = wx.CheckBox(grid_options_window, label="Snap to Grid")
    main_window.snap_to_grid_cb.SetValue(True)  # Default to enabled
    main_window.snap_to_grid_cb.Bind(wx.EVT_CHECKBOX, partial(m_graph_canvas_event_handler.on_snap_to_grid_changed, main_window))
    grid_options_sizer.Add(main_window.snap_to_grid_cb, 0, wx.ALL, 5)

    # Dot size slider (only shown when dots are selected)
    dot_size_sizer = wx.BoxSizer(wx.HORIZONTAL)
    dot_size_label = wx.StaticText(grid_options_window, label="Dot Size:")
    dot_size_sizer.Add(dot_size_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
    
    main_window.dot_size_slider = wx.Slider(grid_options_window, value=2, minValue=1, maxValue=10,
                                          style=wx.SL_HORIZONTAL | wx.SL_LABELS)
    main_window.dot_size_slider.Bind(wx.EVT_SLIDER, partial(m_graph_canvas_event_handler.on_dot_size_changed, main_window))
    dot_size_sizer.Add(main_window.dot_size_slider, 1, wx.EXPAND)
    grid_options_sizer.Add(dot_size_sizer, 0, wx.EXPAND | wx.ALL, 5)

    grid_options_window.SetSizer(grid_options_sizer)
    
    # Background Options Collapsible Section
    main_window.background_options_pane = wx.CollapsiblePane(main_window.sidebar, label="Background Options")
    main_window.background_options_pane.SetForegroundColour(wx.Colour(0, 0, 0))        
    main_window.collapsible_panes.append(main_window.background_options_pane)
    # Bind individual pane expansion events
    main_window.background_options_pane.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, partial(m_sidebar_event_handler.on_individual_pane_changed, main_window))
    sidebar_sizer.Add(main_window.background_options_pane, 0, wx.EXPAND | wx.ALL, 5)
    
    background_options_panel =  main_window.background_options_pane.GetPane()
    view_sizer = wx.BoxSizer(wx.VERTICAL)

    bg_section_label = wx.StaticText(background_options_panel, label="Background Section:")
    bg_section_label.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
    view_sizer.Add(bg_section_label, 0, wx.ALL, 5)
    
    # Background color
    bg_color_sizer = wx.BoxSizer(wx.HORIZONTAL)
    bg_color_label = wx.StaticText(background_options_panel, label="Background:")
    bg_color_label.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
    bg_color_sizer.Add(bg_color_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 2)

    main_window.bg_color_btn = wx.Button(background_options_panel, label="Color", size=(60, -1))
    main_window.bg_color_btn.SetBackgroundColour(wx.Colour(* main_window.canvas.background_color))  # Default canvas color
    main_window.bg_color_btn.Bind(wx.EVT_BUTTON, partial(event_handlers.graph_canvas_event_handler.on_background_color, main_window))
    bg_color_sizer.Add( main_window.bg_color_btn, 0, wx.ALL, 2)

    view_sizer.Add(bg_color_sizer, 0, wx.EXPAND | wx.ALL, 2)

    grid_section_label = wx.StaticText(background_options_panel, label="Grid Section:")
    grid_section_label.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
    view_sizer.Add(grid_section_label, 0, wx.ALL, 5)

    # Grid/Coordinate Style
    grid_style_sizer = wx.BoxSizer(wx.HORIZONTAL)
    grid_style_label = wx.StaticText(background_options_panel, label="Coordinate Style:")
    grid_style_label.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
    grid_style_sizer.Add(grid_style_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 2)

    # Create a secondary grid style choice that syncs with the main one
    secondary_grid_style_choice = wx.Choice(background_options_panel, choices=["None", "Grid", "Dots"])
    secondary_grid_style_choice.SetSelection(1)  # Default to Grid
    secondary_grid_style_choice.SetForegroundColour(wx.Colour(255, 255, 255))
    secondary_grid_style_choice.SetBackgroundColour(wx.Colour(0, 0, 0))
    secondary_grid_style_choice.Bind(wx.EVT_CHOICE, partial(event_handlers.graph_canvas_event_handler.on_grid_style_changed, main_window))
    grid_style_sizer.Add(secondary_grid_style_choice, 1, wx.ALL, 2)

    view_sizer.Add(grid_style_sizer, 0, wx.EXPAND | wx.ALL, 2)

    # Grid/Dot Spacing
    grid_spacing_sizer = wx.BoxSizer(wx.HORIZONTAL)
    grid_spacing_label = wx.StaticText(background_options_panel, label="Spacing:")
    grid_spacing_label.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
    grid_spacing_sizer.Add(grid_spacing_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 2)

    main_window.grid_spacing_field = wx.SpinCtrlDouble(background_options_panel,
                                            min=10.0,
                                            max=200.0,
                                            initial=50.0,
                                            inc=10.0,
                                            size=(70, 30))
    main_window.grid_spacing_field.SetDigits(1)
    main_window.grid_spacing_field.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.grid_spacing_field.SetBackgroundColour(wx.Colour(255, 255, 255))
    main_window.grid_spacing_field.Bind(wx.EVT_SPINCTRLDOUBLE, partial(event_handlers.graph_canvas_event_handler.on_grid_spacing_changed, main_window))
    grid_spacing_sizer.Add(main_window.grid_spacing_field, 1, wx.ALL, 2)

    view_sizer.Add(grid_spacing_sizer, 0, wx.EXPAND | wx.ALL, 2)

    # Grid color
    grid_color_sizer = wx.BoxSizer(wx.HORIZONTAL)
    grid_color_label = wx.StaticText(background_options_panel, label="Grid/Dot Color:")
    grid_color_label.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
    grid_color_sizer.Add(grid_color_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 2)

    main_window.grid_color_btn = wx.Button(background_options_panel,label="Color", size=(60, -1))
    main_window.grid_color_btn.SetBackgroundColour(
    wx.Colour(* main_window.canvas.grid_color))  # Default grid color
    main_window.grid_color_btn.Bind(wx.EVT_BUTTON, partial(event_handlers.graph_canvas_event_handler.on_grid_color, main_window))
    grid_color_sizer.Add( main_window.grid_color_btn, 0, wx.ALL, 2)

    view_sizer.Add(grid_color_sizer, 0, wx.EXPAND | wx.ALL, 2)

    checker_section_label = wx.StaticText(background_options_panel, label="Checkerboard Section:")
    checker_section_label.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
    view_sizer.Add(checker_section_label, 0, wx.ALL, 5)

    # Checkboard background toggle
    main_window.checkboard_bg_cb = wx.CheckBox(background_options_panel, label="Checkerboard Background")
    main_window.checkboard_bg_cb.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
    main_window.checkboard_bg_cb.SetValue(False)  # Default to disabled
    main_window.checkboard_bg_cb.Bind(wx.EVT_CHECKBOX, partial(event_handlers.graph_canvas_event_handler.on_checkboard_background_toggle, main_window))
    view_sizer.Add( main_window.checkboard_bg_cb, 0, wx.ALL, 5)

    # Checkboard colors
    checker_color1_sizer = wx.BoxSizer(wx.HORIZONTAL)
    checker_color1_label = wx.StaticText(background_options_panel, label="Checkerboard Color 1:")
    checker_color1_label.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
    checker_color1_sizer.Add(checker_color1_label, 0,
                        wx.ALIGN_CENTER_VERTICAL | wx.ALL, 2)

    main_window.checker_color1_btn = wx.Button(background_options_panel, label="Color", size=(60, -1))
    # Initialize from canvas.checker_color1 (synced to background elsewhere)
    if hasattr(main_window.canvas, 'checker_color1') and isinstance(main_window.canvas.checker_color1, wx.Colour):
        main_window.checker_color1_btn.SetBackgroundColour(main_window.canvas.checker_color1)
    else:
        main_window.checker_color1_btn.SetBackgroundColour(wx.Colour(* main_window.canvas.background_color))
    main_window.checker_color1_btn.Bind(wx.EVT_BUTTON,  partial(event_handlers.graph_canvas_event_handler.on_checker_color1, main_window))
    checker_color1_sizer.Add(main_window.checker_color1_btn, 0, wx.ALL, 2)

    view_sizer.Add(checker_color1_sizer, 0, wx.EXPAND | wx.ALL, 2)

    checker_color2_sizer = wx.BoxSizer(wx.HORIZONTAL)
    checker_color2_label = wx.StaticText(background_options_panel, label="Checkerboard Color 2:")
    checker_color2_label.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
    checker_color2_sizer.Add(checker_color2_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 2)

    main_window.checker_color2_btn = wx.Button(background_options_panel, label="Color", size=(60, -1))
    # Initialize from canvas.checker_color2 if available; fallback to darker gray
    if hasattr(main_window.canvas, 'checker_color2'):
        c2 = main_window.canvas.checker_color2
        if isinstance(c2, (list, tuple)):
            main_window.checker_color2_btn.SetBackgroundColour(wx.Colour(*c2))
        elif isinstance(c2, wx.Colour):
            main_window.checker_color2_btn.SetBackgroundColour(c2)
    else:
        main_window.checker_color2_btn.SetBackgroundColour(wx.Colour(180, 180, 180))
    main_window.checker_color2_btn.Bind(wx.EVT_BUTTON,  partial(event_handlers.graph_canvas_event_handler.on_checker_color2, main_window))
    checker_color2_sizer.Add( main_window.checker_color2_btn, 0, wx.ALL, 2)

    view_sizer.Add(checker_color2_sizer, 0, wx.EXPAND | wx.ALL, 2)
    
    # Set the sizer for the view options panel
    background_options_panel.SetSizer(view_sizer)

    
    # View Options Collapsible Section
    main_window.view_options_pane = wx.CollapsiblePane( main_window.sidebar, label="View Options")
    main_window.view_options_pane.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.collapsible_panes.append( main_window.view_options_pane)
    # Bind individual pane expansion events
    main_window.view_options_pane.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, partial(m_sidebar_event_handler.on_individual_pane_changed, main_window))
    sidebar_sizer.Add( main_window.view_options_pane, 0, wx.EXPAND | wx.ALL, 5)
    
    view_options_panel =  main_window.view_options_pane.GetPane()
    view_sizer = wx.BoxSizer(wx.VERTICAL)

    # Canvas Information Section
    canvas_info_label = wx.StaticText(view_options_panel, label="Canvas Information:")
    canvas_info_label.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
    view_sizer.Add(canvas_info_label, 0, wx.ALL, 5)
    
    # Canvas center coordinates
    center_info_sizer = wx.BoxSizer(wx.HORIZONTAL)
    main_window.center_x_label = wx.StaticText(view_options_panel, label="Center X:")
    main_window.center_x_label.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.center_x_value = wx.TextCtrl(view_options_panel, value="0.0", size=(80, -1))
    main_window.center_x_value.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.center_x_value.Bind(wx.EVT_TEXT, partial(m_sidebar_event_handler.on_center_x_changed, main_window))
    center_info_sizer.Add(main_window.center_x_label, 0, wx.ALL, 2)
    center_info_sizer.Add(main_window.center_x_value, 0, wx.ALL, 2)
    view_sizer.Add(center_info_sizer, 0, wx.ALL, 2)
    
    center_y_sizer = wx.BoxSizer(wx.HORIZONTAL)
    main_window.center_y_label = wx.StaticText(view_options_panel, label="Center Y:")
    main_window.center_y_label.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.center_y_value = wx.TextCtrl(view_options_panel, value="0.0", size=(80, -1))
    main_window.center_y_value.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.center_y_value.Bind(wx.EVT_TEXT, partial(m_sidebar_event_handler.on_center_y_changed, main_window))
    center_y_sizer.Add(main_window.center_y_label, 0, wx.ALL, 2)
    center_y_sizer.Add(main_window.center_y_value, 0, wx.ALL, 2)
    view_sizer.Add(center_y_sizer, 0, wx.ALL, 2)
    
    # Canvas dimensions
    dimensions_sizer = wx.BoxSizer(wx.HORIZONTAL)
    main_window.width_label = wx.StaticText(view_options_panel, label="Width:")
    main_window.width_label.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.width_value = wx.TextCtrl(view_options_panel, value="0", size=(80, -1))
    main_window.width_value.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.width_value.Bind(wx.EVT_TEXT, partial(m_sidebar_event_handler.on_width_changed, main_window))
    dimensions_sizer.Add(main_window.width_label, 0, wx.ALL, 2)
    dimensions_sizer.Add(main_window.width_value, 0, wx.ALL, 2)
    view_sizer.Add(dimensions_sizer, 0, wx.ALL, 2)
    
    height_sizer = wx.BoxSizer(wx.HORIZONTAL)
    main_window.height_label = wx.StaticText(view_options_panel, label="Height:")
    main_window.height_label.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.height_value = wx.TextCtrl(view_options_panel, value="0", size=(80, -1))
    main_window.height_value.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.height_value.Bind(wx.EVT_TEXT, partial(m_sidebar_event_handler.on_height_changed, main_window))
    height_sizer.Add(main_window.height_label, 0, wx.ALL, 2)
    height_sizer.Add(main_window.height_value, 0, wx.ALL, 2)
    view_sizer.Add(height_sizer, 0, wx.ALL, 2)
    
    # View Control Buttons
    view_controls_label = wx.StaticText(view_options_panel, label="View Controls:")
    view_controls_label.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
    view_sizer.Add(view_controls_label, 0, wx.ALL, 5)
    
    # Set Custom Origin button
    main_window.set_origin_btn = wx.Button(view_options_panel,
                                label="Set Current Center as Default",
                                size=(-1, 32))
    main_window.set_origin_btn.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
    main_window.set_origin_btn.SetBackgroundColour(wx.Colour(240, 240, 240))  # Light gray background
    main_window.set_origin_btn.Bind(wx.EVT_BUTTON, partial(event_handlers.graph_canvas_event_handler.on_set_custom_origin, main_window))
    view_sizer.Add(main_window.set_origin_btn, 0, wx.EXPAND | wx.ALL, 5)

    # Set Custom Default Rotation button
    main_window.set_rotation_btn = wx.Button(view_options_panel,
                                label="Set Current Rotation as Default",
                                size=(-1, 32))
    main_window.set_rotation_btn.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
    main_window.set_rotation_btn.SetBackgroundColour(wx.Colour(240, 240, 240))  # Light gray background
    main_window.set_rotation_btn.Bind(wx.EVT_BUTTON, partial(event_handlers.graph_canvas_event_handler.on_set_custom_rotation, main_window))
    view_sizer.Add(main_window.set_rotation_btn, 0, wx.EXPAND | wx.ALL, 5)

    # Set Current Zoom as Default button
    main_window.set_zoom_btn = wx.Button(view_options_panel,
                                label="Set Current Zoom as Default",
                                size=(-1, 32))
    main_window.set_zoom_btn.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
    main_window.set_zoom_btn.SetBackgroundColour(wx.Colour(240, 240, 240))  # Light gray background
    main_window.set_zoom_btn.Bind(wx.EVT_BUTTON, partial(event_handlers.graph_canvas_event_handler.on_set_custom_zoom, main_window))
    view_sizer.Add(main_window.set_zoom_btn, 0, wx.EXPAND | wx.ALL, 5)

    # Set Current View as Default button (sets center, rotation, and zoom)
    main_window.set_current_view_btn = wx.Button(view_options_panel,
                                label="Set Current View as Default",
                                size=(-1, 32))
    main_window.set_current_view_btn.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
    main_window.set_current_view_btn.SetBackgroundColour(wx.Colour(240, 240, 240))  # Light gray background
    main_window.set_current_view_btn.Bind(wx.EVT_BUTTON, partial(event_handlers.graph_canvas_event_handler.on_set_current_view_as_default, main_window))
    view_sizer.Add(main_window.set_current_view_btn, 0, wx.EXPAND | wx.ALL, 5)

    # Reset View button
    main_window.snap_to_original_btn = wx.Button(view_options_panel,
                                        label="Reset View",
                                        size=(-1, 32))
    main_window.snap_to_original_btn.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
    main_window.snap_to_original_btn.SetBackgroundColour(wx.Colour(240, 240, 240))  # Light gray background
    main_window.snap_to_original_btn.Bind(wx.EVT_BUTTON, main_window.canvas.on_snap_to_original)
    view_sizer.Add(main_window.snap_to_original_btn, 0, wx.EXPAND | wx.ALL, 5)
    
    # Set the sizer for the view options panel
    view_options_panel.SetSizer(view_sizer)
    
    # Initialize canvas information display
    main_window.update_canvas_info()


    # Movement/Zoom Controls Collapsible Section  
    main_window.movement_pane = wx.CollapsiblePane( main_window.sidebar, label="Movement & Zoom Controls")
    main_window.movement_pane.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.collapsible_panes.append( main_window.movement_pane)
    # Bind individual pane expansion events
    main_window.movement_pane.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, partial(m_sidebar_event_handler.on_individual_pane_changed, main_window))
    sidebar_sizer.Add(main_window.movement_pane, 0, wx.EXPAND | wx.ALL, 5)
    
    movement_panel =  main_window.movement_pane.GetPane()
    movement_sizer = wx.BoxSizer(wx.VERTICAL)

    # Movement options
    # movement_box = wx.StaticBox( main_window.sidebar, label="Movement Options")
    # movement_box.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
    # movement_sizer = wx.StaticBoxSizer(movement_box, wx.VERTICAL)

    # # Move tool options
    # move_options_sizer = wx.BoxSizer(wx.VERTICAL)
    
    # Inverted toggle
    main_window.move_inverted_cb = wx.CheckBox(movement_panel,
                                    label="Inverted Movement")
    main_window.move_inverted_cb.SetForegroundColour(wx.Colour(0, 0,
                                                    0))  # Black text
    main_window.move_inverted_cb.SetValue(False)
    main_window.move_inverted_cb.Bind(wx.EVT_CHECKBOX,  partial(m_sidebar_event_handler.on_inverted_changed, main_window))
    movement_sizer.Add( main_window.move_inverted_cb, 0, wx.ALL, 2)

    zoom_section_label = wx.StaticText(movement_panel, label="Zoom Section:")
    zoom_section_label.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
    movement_sizer.Add(zoom_section_label, 0, wx.ALL, 5)

    # Center Zoom toggle
    main_window.center_zoom_cb = wx.CheckBox(movement_panel, label="Center Zoom")
    main_window.center_zoom_cb.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
    main_window.center_zoom_cb.SetValue(False)  # Default to disabled
    main_window.center_zoom_cb.Bind(wx.EVT_CHECKBOX,  partial(event_handlers.graph_canvas_zoom_event_handler.on_center_zoom_toggle, main_window))
    movement_sizer.Add( main_window.center_zoom_cb, 0, wx.ALL, 5)
    
    # Sensitivity lock toggle
    main_window.sensitivity_locked_cb = wx.CheckBox(movement_panel,
                                            label="Lock X/Y Sensitivity")
    main_window.sensitivity_locked_cb.SetForegroundColour(wx.Colour(
    0, 0, 0))  # Black text
    main_window.sensitivity_locked_cb.SetValue(True)  # Default to locked
    main_window.sensitivity_locked_cb.Bind(wx.EVT_CHECKBOX, partial(m_sidebar_event_handler.on_sensitivity_lock_changed, main_window))
    movement_sizer.Add( main_window.sensitivity_locked_cb, 0, wx.ALL, 2)
    
    # Individual X/Y sensitivity controls
    main_window.x_sensitivity_sizer = wx.BoxSizer(wx.HORIZONTAL)
    main_window.x_label = wx.StaticText(movement_panel, label="X:")
    main_window.x_label.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.x_sensitivity_minus = wx.Button(movement_panel,
                                        label="-",
                                        size=(30, 28))
    main_window.x_sensitivity_field = wx.SpinCtrlDouble(movement_panel, min=0.1, max=10.0, initial=1.0, inc=0.1, size=(70, 30))
    main_window.x_sensitivity_field.SetDigits(1)
    # Try multiple color setting approaches for macOS compatibility
    main_window.x_sensitivity_field.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
    main_window.x_sensitivity_field.SetBackgroundColour(wx.Colour(255, 255, 255))  # White background
    
    # Set larger, bold font immediately
    font =  main_window.x_sensitivity_field.GetFont()
    font.SetWeight(wx.FONTWEIGHT_BOLD)
    font.SetPointSize(12)
    main_window.x_sensitivity_field.SetFont(font)
    main_window.x_sensitivity_plus = wx.Button(movement_panel, label="+", size=(30, 28))

    main_window.x_sensitivity_minus.Bind(wx.EVT_BUTTON, lambda evt:  main_window.adjust_x_sensitivity(-0.1))
    main_window.x_sensitivity_plus.Bind(wx.EVT_BUTTON, lambda evt:  main_window.adjust_x_sensitivity(0.1))

    main_window.x_sensitivity_sizer.Add( main_window.x_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 2)
    main_window.x_sensitivity_sizer.Add( main_window.x_sensitivity_minus, 0, wx.ALL, 1)
    main_window.x_sensitivity_sizer.Add( main_window.x_sensitivity_field, 1, wx.ALL, 1)
    main_window.x_sensitivity_sizer.Add( main_window.x_sensitivity_plus, 0, wx.ALL, 1)
    movement_sizer.Add(main_window.x_sensitivity_sizer, 0, wx.EXPAND | wx.ALL, 2)
    
    main_window.y_sensitivity_sizer = wx.BoxSizer(wx.HORIZONTAL)
    main_window.y_label = wx.StaticText(movement_panel, label="Y:")
    main_window.y_label.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.y_sensitivity_minus = wx.Button(movement_panel,
                                        label="-",
                                        size=(30, 28))
    main_window.y_sensitivity_field = wx.SpinCtrlDouble(movement_panel,
                                                min=0.1,
                                                max=10.0,
                                                initial=1.0,
                                                inc=0.1,
                                                size=(70, 30))
    main_window.y_sensitivity_field.SetDigits(1)
    # Try multiple color setting approaches for macOS compatibility
    main_window.y_sensitivity_field.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
    main_window.y_sensitivity_field.SetBackgroundColour(wx.Colour(255, 255, 255))  # White background
    
    # Set larger, bold font immediately
    font =  main_window.y_sensitivity_field.GetFont()
    font.SetWeight(wx.FONTWEIGHT_BOLD)
    font.SetPointSize(12)
    main_window.y_sensitivity_field.SetFont(font)
    main_window.y_sensitivity_plus = wx.Button(movement_panel,
                                    label="+",
                                    size=(30, 28))

    main_window.y_sensitivity_minus.Bind(
    wx.EVT_BUTTON, lambda evt:  main_window.adjust_y_sensitivity(-0.1))
    main_window.y_sensitivity_plus.Bind(
    wx.EVT_BUTTON, lambda evt:  main_window.adjust_y_sensitivity(0.1))

    main_window.y_sensitivity_sizer.Add( main_window.y_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 2)
    main_window.y_sensitivity_sizer.Add( main_window.y_sensitivity_minus, 0, wx.ALL, 1)
    main_window.y_sensitivity_sizer.Add( main_window.y_sensitivity_field, 1, wx.ALL, 1)
    main_window.y_sensitivity_sizer.Add( main_window.y_sensitivity_plus, 0, wx.ALL, 1)
    movement_sizer.Add( main_window.y_sensitivity_sizer, 0, wx.EXPAND | wx.ALL, 2)
    
    # Combined sensitivity control (shown when locked)
    main_window.combined_sensitivity_sizer = wx.BoxSizer(wx.HORIZONTAL)
    main_window.combined_label = wx.StaticText(movement_panel, label="Sensitivity:")
    main_window.combined_label.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.combined_sensitivity_minus = wx.Button(movement_panel,
                                            label="-",
                                            size=(30, 28))
    main_window.combined_sensitivity_field = wx.SpinCtrlDouble(movement_panel,
                                                    min=0.1,
                                                    max=10.0,
                                                    initial=1.0,
                                                    inc=0.1,
                                                    size=(70, 30))
    main_window.combined_sensitivity_field.SetDigits(1)
    # Try multiple color setting approaches for macOS compatibility
    main_window.combined_sensitivity_field.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
    main_window.combined_sensitivity_field.SetBackgroundColour(wx.Colour(255, 255, 255))  # White background
    
    # Set larger, bold font immediately
    font =  main_window.combined_sensitivity_field.GetFont()
    font.SetWeight(wx.FONTWEIGHT_BOLD)
    font.SetPointSize(12)
    main_window.combined_sensitivity_field.SetFont(font)
    main_window.combined_sensitivity_plus = wx.Button(movement_panel,
                                            label="+",
                                            size=(30, 28))

    main_window.combined_sensitivity_minus.Bind(
    wx.EVT_BUTTON, lambda evt:  main_window.adjust_combined_sensitivity(-0.1))
    main_window.combined_sensitivity_plus.Bind(
    wx.EVT_BUTTON, lambda evt:  main_window.adjust_combined_sensitivity(0.1))
    main_window.combined_sensitivity_field.Bind(
    wx.EVT_SPINCTRLDOUBLE,  m_sidebar_event_handler.on_combined_sensitivity_changed)

    main_window.combined_sensitivity_sizer.Add( main_window.combined_label, 0,
                                    wx.ALIGN_CENTER_VERTICAL | wx.ALL,
                                    2)
    main_window.combined_sensitivity_sizer.Add( main_window.combined_sensitivity_minus, 0,
                                    wx.ALL, 1)
    main_window.combined_sensitivity_sizer.Add( main_window.combined_sensitivity_field, 1,
                                    wx.ALL, 1)
    main_window.combined_sensitivity_sizer.Add( main_window.combined_sensitivity_plus, 0,
                                    wx.ALL, 1)
    movement_sizer.Add( main_window.combined_sensitivity_sizer, 0,
                            wx.EXPAND | wx.ALL, 2)
    
    # Zoom sensitivity control
    zoom_sensitivity_sizer = wx.BoxSizer(wx.HORIZONTAL)
    main_window.zoom_label = wx.StaticText(movement_panel, label="Zoom:")
    main_window.zoom_label.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.zoom_sensitivity_minus = wx.Button(movement_panel,
                                        label="-",
                                        size=(30, 28))
    main_window.zoom_sensitivity_field = wx.SpinCtrlDouble(movement_panel,
                                                min=0.1,
                                                max=5.0,
                                                initial=1.0,
                                                inc=0.1,
                                                size=(70, 30))
    main_window.zoom_sensitivity_field.SetDigits(1)
    # Try multiple color setting approaches for macOS compatibility
    main_window.zoom_sensitivity_field.SetForegroundColour(wx.Colour(
    0, 0, 0))  # Black text
    main_window.zoom_sensitivity_field.SetBackgroundColour(
    wx.Colour(255, 255, 255))  # White background
    
    # Set larger, bold font immediately
    font =  main_window.zoom_sensitivity_field.GetFont()
    font.SetWeight(wx.FONTWEIGHT_BOLD)
    font.SetPointSize(12)
    main_window.zoom_sensitivity_field.SetFont(font)
    main_window.zoom_sensitivity_plus = wx.Button(movement_panel,
                                        label="+",
                                        size=(30, 28))

    main_window.zoom_sensitivity_minus.Bind(
    wx.EVT_BUTTON, lambda evt:  main_window.adjust_zoom_sensitivity(-0.1))
    main_window.zoom_sensitivity_plus.Bind(
    wx.EVT_BUTTON, lambda evt:  main_window.adjust_zoom_sensitivity(0.1))
    main_window.zoom_sensitivity_field.Bind(wx.EVT_SPINCTRLDOUBLE,
                                    m_sidebar_event_handler.on_zoom_sensitivity_changed)
    # Initialize field from persisted ZoomManager, if available
    try:
        if hasattr(main_window, 'managers') and hasattr(main_window.managers, 'zoom_manager'):
            persisted_sens = float(main_window.managers.zoom_manager.get_sensitivity())
            main_window.zoom_sensitivity_field.SetValue(persisted_sens)
            # Apply to canvas immediately
            import graph_canvas.presentation.desktop.event_handlers.graph_canvas_zoom_event_handler as _zoom_ev
            _zoom_ev.update_canvas_zoom_sensitivity(main_window)
            # Optionally sync MVU model
            if hasattr(main_window, 'mvu_adapter'):
                from mvc_mvu.messages import make_message
                import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
                main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_ZOOM_SENSITIVITY, value=persisted_sens))
    except Exception:
        pass

    zoom_sensitivity_sizer.Add( main_window.zoom_label, 0,
                                wx.ALIGN_CENTER_VERTICAL | wx.ALL, 2)
    zoom_sensitivity_sizer.Add( main_window.zoom_sensitivity_minus, 0, wx.ALL, 1)
    zoom_sensitivity_sizer.Add( main_window.zoom_sensitivity_field, 1, wx.ALL, 1)
    zoom_sensitivity_sizer.Add( main_window.zoom_sensitivity_plus, 0, wx.ALL, 1)
    movement_sizer.Add(zoom_sensitivity_sizer, 0, wx.EXPAND | wx.ALL,
                            2)
    
    # Zoom input mode (Wheel vs Touchpad)
    zoom_input_sizer = wx.BoxSizer(wx.HORIZONTAL)
    zoom_input_label = wx.StaticText(movement_panel, label="Zoom Input:")
    zoom_input_label.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.zoom_input_choice = wx.Choice(movement_panel, choices=["Wheel", "Touchpad", "Both"])
    try:
        default_mode = "Wheel"
        # Prefer persisted ZoomManager mode if present
        if hasattr(main_window, 'managers') and hasattr(main_window.managers, 'zoom_manager'):
            zmode = main_window.managers.zoom_manager.get_mode()
        elif hasattr(main_window, 'mvu_adapter'):
            zmode = getattr(main_window.mvu_adapter.model, 'zoom_input_mode', 'wheel')
        else:
            zmode = 'wheel'
        if zmode == 'touchpad':
            default_mode = "Touchpad"
        elif zmode == 'both':
            default_mode = "Both"
        else:
            default_mode = "Wheel"
        main_window.zoom_input_choice.SetStringSelection(default_mode)
        # Apply to canvas immediately
        if hasattr(main_window, 'canvas'):
            main_window.canvas.zoom_input_mode = zmode
        # Optionally sync MVU model
        if hasattr(main_window, 'mvu_adapter'):
            from mvc_mvu.messages import make_message
            import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu
            main_window.mvu_adapter.dispatch(make_message(m_main_mvu.Msg.SET_ZOOM_INPUT_MODE, mode=zmode))
    except Exception:
        main_window.zoom_input_choice.SetStringSelection("Wheel")
    main_window.zoom_input_choice.Bind(wx.EVT_CHOICE, lambda evt: m_sidebar_event_handler._on_zoom_input_mode_changed(main_window, evt))
    zoom_input_sizer.Add(zoom_input_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
    zoom_input_sizer.Add(main_window.zoom_input_choice, 0, wx.ALIGN_CENTER_VERTICAL)
    movement_sizer.Add(zoom_input_sizer, 0, wx.EXPAND | wx.ALL, 2)
    
    # Set the sizer for the movement panel
    movement_panel.SetSizer(movement_sizer)

    # Tools Collapsible Section (ensure single instance)
    if hasattr(main_window, 'tools_pane') and isinstance(main_window.tools_pane, wx.CollapsiblePane):
        try:
            main_window.tools_pane.Destroy()
        except Exception:
            pass
    main_window.tools_pane = wx.CollapsiblePane(main_window.sidebar, label="Tools")
    main_window.collapsible_panes.append(main_window.tools_pane)
    main_window.tools_pane.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, partial(m_sidebar_event_handler.on_individual_pane_changed, main_window))
    sidebar_sizer.Add(main_window.tools_pane, 0, wx.EXPAND | wx.ALL, 5)

    tools_panel = main_window.tools_pane.GetPane()
    try:
        tools_panel.SetBackgroundColour(main_window.sidebar.GetBackgroundColour())
        tools_panel.SetForegroundColour(main_window.sidebar.GetForegroundColour())
    except Exception:
        pass
    tools_sizer = wx.BoxSizer(wx.VERTICAL)

    # Use radio buttons so only one tool is active at a time
    main_window._tool_radio_buttons = []

    def add_tool_radio(attr_name, label, tool_name, is_first=False):
        style = wx.RB_GROUP if is_first else 0
        btn = wx.RadioButton(tools_panel, label=label, style=style)
        # Unified font for all tool items (leave colors to theme)
        font = btn.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        font.SetPointSize(11)
        btn.SetFont(font)
        # Ensure theme-consistent, visible colors
        try:
            btn.SetForegroundColour(main_window.sidebar.GetForegroundColour())
            btn.SetBackgroundColour(tools_panel.GetBackgroundColour())
        except Exception:
            pass
        btn.Bind(wx.EVT_RADIOBUTTON, partial(event_handlers.toolbar_event_handler.on_tool_changed, main_window))
        tools_sizer.Add(btn, 0, wx.EXPAND | wx.ALL, 3)
        setattr(main_window, attr_name, btn)
        main_window._tool_radio_buttons.append((btn, tool_name))

    # Add requested tool buttons
    add_tool_radio("tool_select", "Select", "select", is_first=True)
    add_tool_radio("tool_node", "Add Node", "node")
    add_tool_radio("tool_edge", "Add Edge", "edge")
    add_tool_radio("tool_move", "Move World", "move")
    add_tool_radio("tool_rotate", "Rotate World", "rotate")
    add_tool_radio("tool_rotate_element", "Rotate Element", "rotate_element")
    add_tool_radio("tool_drag_into", "Drag Into Container", "drag_into")
    add_tool_radio("tool_expand", "Expand Node", "expand")
    add_tool_radio("tool_collapse", "Collapse Node", "collapse")
    add_tool_radio("tool_recursive_expand", "Recursive Expand", "recursive_expand")
    add_tool_radio("tool_recursive_collapse", "Recursive Collapse", "recursive_collapse")

    # Default select the current tool if available, otherwise select "select"
    try:
        current_tool = getattr(main_window.canvas, 'tool', 'select')
        matched = False
        for rb, tool_name in main_window._tool_radio_buttons:
            if tool_name == current_tool:
                rb.SetValue(True)
                matched = True
                break
        if not matched and main_window._tool_radio_buttons:
            main_window._tool_radio_buttons[0][0].SetValue(True)
    except Exception:
        pass

    # Edge direction options within Tools pane
    edge_dir_sizer = wx.BoxSizer(wx.HORIZONTAL)
    edge_type_label = wx.StaticText(tools_panel, label="Edge Type:")
    edge_dir_sizer.Add(edge_type_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 2)

    main_window.edge_directed_cb = wx.CheckBox(tools_panel, label="Directed")
    main_window.edge_directed_cb.SetValue(True)
    main_window.edge_directed_cb.Bind(wx.EVT_CHECKBOX, event_handlers.graph_canvas_event_handler.on_edge_directed_changed)
    edge_dir_sizer.Add(main_window.edge_directed_cb, 0, wx.ALL, 2)

    tools_sizer.Add(edge_dir_sizer, 0, wx.EXPAND | wx.ALL, 2)

    tools_panel.SetSizer(tools_sizer)

    #sidebar_sizer.Add(move_options_sizer, 0, wx.EXPAND | wx.ALL, 5)


    # Rotation Controls Collapsible Section
    main_window.rotation_pane = wx.CollapsiblePane( main_window.sidebar, label="Rotation Controls")
    main_window.rotation_pane.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.collapsible_panes.append( main_window.rotation_pane)
    # Bind individual pane expansion events
    main_window.rotation_pane.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, partial(m_sidebar_event_handler.on_individual_pane_changed, main_window))
    sidebar_sizer.Add( main_window.rotation_pane, 0, wx.EXPAND | wx.ALL, 5)
    
    rotation_panel =  main_window.rotation_pane.GetPane()
    rotation_main_sizer = wx.BoxSizer(wx.VERTICAL)

    # World rotation control
    rotation_sizer = wx.BoxSizer(wx.HORIZONTAL)
    rotation_label = wx.StaticText(rotation_panel, label="Rotation:")
    rotation_label.SetForegroundColour(wx.Colour(0, 0, 0))
    rotation_sizer.Add(rotation_label, 0,
                        wx.ALIGN_CENTER_VERTICAL | wx.ALL, 2)

    main_window.rotation_minus = wx.Button(rotation_panel, label="-", size=(30, 28))
    main_window.rotation_field = wx.SpinCtrlDouble(rotation_panel,
                                        min=-360.0,
                                        max=360.0,
                                        initial=0.0,
                                        inc=15.0,
                                        size=(70, 30))
    main_window.rotation_field.SetDigits(1)
    main_window.rotation_field.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.rotation_field.SetBackgroundColour(wx.Colour(255, 255, 255))
    
    # Set larger, bold font for rotation field
    font =  main_window.rotation_field.GetFont()
    font.SetWeight(wx.FONTWEIGHT_BOLD)
    font.SetPointSize(12)
    main_window.rotation_field.SetFont(font)

    main_window.rotation_plus = wx.Button(rotation_panel, label="+", size=(30, 28))

    main_window.rotation_minus.Bind(wx.EVT_BUTTON,
                            lambda evt:  sidebar_event_handler.adjust_rotation(main_window, -15.0))
    main_window.rotation_plus.Bind(wx.EVT_BUTTON,
                        lambda evt:  sidebar_event_handler.adjust_rotation(main_window, 15.0))
    main_window.rotation_field.Bind(wx.EVT_SPINCTRLDOUBLE,
                            partial(m_sidebar_event_handler.on_rotation_changed, main_window))

    rotation_sizer.Add( main_window.rotation_minus, 0, wx.ALL, 1)
    rotation_sizer.Add( main_window.rotation_field, 1, wx.ALL, 1)
    rotation_sizer.Add( main_window.rotation_plus, 0, wx.ALL, 1)
    rotation_main_sizer.Add(rotation_sizer, 0, wx.EXPAND | wx.ALL, 2)
    
    # Set the sizer for the rotation panel
    rotation_panel.SetSizer(rotation_main_sizer)


    # Graph Properties Collapsible Section
    main_window.graph_properties_pane = wx.CollapsiblePane( main_window.sidebar, label="Graph Properties")
    main_window.graph_properties_pane.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.collapsible_panes.append( main_window.graph_properties_pane)
    # Bind individual pane expansion events
    main_window.graph_properties_pane.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, partial(m_sidebar_event_handler.on_individual_pane_changed, main_window))
    sidebar_sizer.Add( main_window.graph_properties_pane, 0, wx.EXPAND | wx.ALL, 5)
    
    graph_properties_panel =  main_window.graph_properties_pane.GetPane()
    graph_sizer = wx.BoxSizer(wx.VERTICAL)
    # Expose graph properties sizer for other UI (e.g., control points) to attach under this section
    main_window.graph_properties_sizer = graph_sizer

    main_window.graph_name_ctrl = wx.TextCtrl(graph_properties_panel,
                                    value= main_window.current_graph.name)
    main_window.graph_name_ctrl.SetForegroundColour(wx.Colour(0, 0,
                                                    0))  # Black text
    main_window.graph_name_ctrl.Bind(wx.EVT_TEXT,  partial(event_handlers.menubar_event_handler.on_graph_name_changed, main_window))

    name_label = wx.StaticText(graph_properties_panel, label="Name:")
    name_label.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
    graph_sizer.Add(name_label, 0, wx.ALL, 5)
    graph_sizer.Add( main_window.graph_name_ctrl, 0, wx.EXPAND | wx.ALL, 5)

    main_window.node_count_label = wx.StaticText(graph_properties_panel, label="Nodes: 0")
    main_window.node_count_label.SetForegroundColour(wx.Colour(0, 0,
                                                        0))  # Black text
    main_window.edge_count_label = wx.StaticText(graph_properties_panel, label="Edges: 0")
    main_window.edge_count_label.SetForegroundColour(wx.Colour(0, 0,
                                                        0))  # Black text
    graph_sizer.Add( main_window.node_count_label, 0, wx.ALL, 5)
    graph_sizer.Add( main_window.edge_count_label, 0, wx.ALL, 5)

    # Default Properties
    defaults_box = wx.StaticBox(graph_properties_panel, label="Default Properties")
    defaults_box.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
    defaults_sizer = wx.StaticBoxSizer(defaults_box, wx.VERTICAL)

    # Default node properties button
    main_window.default_node_btn = wx.Button(graph_properties_panel,
                                    label="Node Defaults...",
                                    size=(-1, 32))
    main_window.default_node_btn.SetForegroundColour(wx.Colour(0, 0,
                                                    0))  # Black text
    main_window.default_node_btn.Bind(wx.EVT_BUTTON,
                            partial(m_sidebar_event_handler.on_default_node_properties, main_window))
    defaults_sizer.Add( main_window.default_node_btn, 0, wx.EXPAND | wx.ALL, 5)

    # Default edge properties button
    main_window.default_edge_btn = wx.Button(graph_properties_panel,
                                    label="Edge Defaults...",
                                    size=(-1, 32))
    main_window.default_edge_btn.SetForegroundColour(wx.Colour(0, 0,
                                                    0))  # Black text
    main_window.default_edge_btn.Bind(wx.EVT_BUTTON,
                            partial(m_sidebar_event_handler.on_default_edge_properties, main_window))
    defaults_sizer.Add( main_window.default_edge_btn, 0, wx.EXPAND | wx.ALL, 5)

    graph_sizer.Add(defaults_sizer, 0, wx.EXPAND | wx.ALL, 5)

    # Graph type selection
    graph_type_label = wx.StaticText(graph_properties_panel, label="Graph Type:")
    graph_type_label.SetForegroundColour(wx.Colour(0, 0, 0))
    graph_sizer.Add(graph_type_label, 0, wx.ALL, 2)

    main_window.graph_type_choice = wx.Choice(graph_properties_panel,
                                    choices=[
                                        "List", "Tree", "DAG",
                                        "Graph",
                                        "├─ Hypergraph",
                                        "├─ Nested Graph",
                                        "└─ Ubergraph",
                                        "   └─ Typed Ubergraph"
                                    ])
    main_window.graph_type_choice.SetSelection(3)  # Default to "Graph"
    main_window.graph_type_choice.SetForegroundColour(wx.Colour(255, 255, 255))
    main_window.graph_type_choice.SetBackgroundColour(wx.Colour(0, 0, 0))
    main_window.graph_type_choice.Refresh()
    main_window.graph_type_choice.Bind(wx.EVT_CHOICE,  partial(event_handlers.graph_canvas_event_handler.on_graph_type_changed, main_window))
    graph_sizer.Add(main_window.graph_type_choice, 0, wx.EXPAND | wx.ALL, 2)

    # Set the sizer for the graph properties panel
    graph_properties_panel.SetSizer(graph_sizer)

    # Graph Restrictions
    restrictions_box = wx.StaticBox( main_window.sidebar,
                                    label="Graph Restrictions")
    restrictions_box.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
    restrictions_sizer = wx.StaticBoxSizer(restrictions_box, wx.VERTICAL)

    # No loops toggle
    main_window.no_loops_cb = wx.CheckBox( main_window.sidebar,
                                label="No Loops ( main_window-edges)")
    main_window.no_loops_cb.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.no_loops_cb.SetValue(False)  # Default to allow loops
    main_window.no_loops_cb.Bind(wx.EVT_CHECKBOX,  partial(event_handlers.graph_canvas_event_handler.on_no_loops_changed, main_window))
    restrictions_sizer.Add( main_window.no_loops_cb, 0, wx.EXPAND | wx.ALL, 2)

    # No multigraphs toggle
    main_window.no_multigraphs_cb = wx.CheckBox(
        main_window.sidebar, label="No Multigraphs (Multiple edges)")
    main_window.no_multigraphs_cb.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.no_multigraphs_cb.SetValue(
    False)  # Default to allow multiple edges
    main_window.no_multigraphs_cb.Bind(wx.EVT_CHECKBOX,
                                partial(event_handlers.graph_canvas_event_handler.on_no_multigraphs_changed, main_window))
    restrictions_sizer.Add( main_window.no_multigraphs_cb, 0, wx.EXPAND | wx.ALL,
                            2)

    # Graph type restriction dropdown
    graph_type_label = wx.StaticText( main_window.sidebar, label="Graph Type:")
    graph_type_label.SetForegroundColour(wx.Colour(0, 0, 0))
    restrictions_sizer.Add(graph_type_label, 0, wx.ALL, 2)

    main_window.graph_type_restriction_choice = wx.Choice(
        main_window.sidebar,
    choices=[
        "No Restrictions", "Require Directed Graph",
        "Require Undirected Graph"
    ])
    main_window.graph_type_restriction_choice.SetSelection(
    0)  # Default to "No Restrictions"
    main_window.graph_type_restriction_choice.SetForegroundColour(
    wx.Colour(255, 255, 255))
    main_window.graph_type_restriction_choice.SetBackgroundColour(
    wx.Colour(0, 0, 0))
    main_window.graph_type_restriction_choice.Refresh()
    main_window.graph_type_restriction_choice.Bind(
    wx.EVT_CHOICE,  partial(event_handlers.graph_canvas_event_handler.on_graph_type_restriction_changed, main_window))
    restrictions_sizer.Add( main_window.graph_type_restriction_choice, 0,
                            wx.EXPAND | wx.ALL, 2)

    sidebar_sizer.Add(restrictions_sizer, 0, wx.EXPAND | wx.ALL, 5)

    graph_control_section_label = wx.StaticText( main_window.sidebar, label="Graph Control Section:")
    graph_control_section_label.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
    sidebar_sizer.Add(graph_control_section_label, 0, wx.ALL, 5)

    # Make All Nodes Readable button
    main_window.make_readable_btn = wx.Button( main_window.sidebar,
                                    label="Make All Nodes Readable",
                                    size=(-1, 32))
    main_window.make_readable_btn.SetForegroundColour(wx.Colour(0, 0,
                                                        0))  # Black text
    main_window.make_readable_btn.SetBackgroundColour(wx.Colour(
    240, 240, 240))  # Light gray background
    main_window.make_readable_btn.Bind(wx.EVT_BUTTON, partial(event_handlers.menubar_event_handler.on_make_all_readable, main_window))
    sidebar_sizer.Add( main_window.make_readable_btn, 0, wx.EXPAND | wx.ALL, 5)

    # Auto-readable nodes toggle
    main_window.auto_readable_cb = wx.CheckBox( main_window.sidebar,
                                    label="Auto-readable Nodes")
    main_window.auto_readable_cb.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.auto_readable_cb.SetValue(False)
    main_window.auto_readable_cb.Bind(wx.EVT_CHECKBOX,
                            main_window.canvas.on_auto_readable_changed)
    sidebar_sizer.Add( main_window.auto_readable_cb, 0, wx.EXPAND | wx.ALL, 2)
    
    # Show nested edges toggle
    main_window.show_nested_edges_cb = wx.CheckBox( main_window.sidebar,
                                        label="Show Nested Edges")
    main_window.show_nested_edges_cb.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.show_nested_edges_cb.SetValue(
    True)  # Default to showing nested edges
    main_window.show_nested_edges_cb.Bind(wx.EVT_CHECKBOX,
                                main_window.canvas.on_show_nested_edges_changed)
    sidebar_sizer.Add( main_window.show_nested_edges_cb, 0, wx.EXPAND | wx.ALL, 2)
    
    # Special indicators for nested edges toggle
    main_window.nested_edge_indicators_cb = wx.CheckBox(
        main_window.sidebar, label="Special Nested Indicators")
    main_window.nested_edge_indicators_cb.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.nested_edge_indicators_cb.SetValue(
    True)  # Default to showing indicators
    main_window.nested_edge_indicators_cb.Bind(
    wx.EVT_CHECKBOX,  event_handlers.graph_canvas_event_handler.on_nested_edge_indicators_changed)
    sidebar_sizer.Add( main_window.nested_edge_indicators_cb, 0, wx.EXPAND | wx.ALL,
                    2)

    # Selection properties
    selection_box = wx.StaticBox( main_window.sidebar, label="Selection")
    selection_box.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
    selection_sizer = wx.StaticBoxSizer(selection_box, wx.VERTICAL)

    main_window.selection_label = wx.StaticText( main_window.sidebar,
                                        label="Nothing selected")
    main_window.selection_label.SetForegroundColour(wx.Colour(0, 0,
                                                    0))  # Black text
    selection_sizer.Add( main_window.selection_label, 0, wx.ALL, 5)

    # Use real wx.Button for reliable clicking - make it more prominent
    main_window.properties_btn = wx.Button( main_window.sidebar,
                                label="Properties...",
                                size=(-1, 32))
    main_window.properties_btn.Bind(wx.EVT_BUTTON,  partial(event_handlers.menubar_event_handler.on_properties, main_window))
    main_window.properties_btn.Enable(False)  # Start disabled
    selection_sizer.Add( main_window.properties_btn, 0, wx.EXPAND | wx.ALL, 5)

    sidebar_sizer.Add(selection_sizer, 0, wx.EXPAND | wx.ALL, 5)

    # (Removed duplicate legacy Tools section)

    

    # Grid Snapping Controls
    snap_box = wx.StaticBox( main_window.sidebar, label="Grid Snapping")
    snap_box.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
    snap_sizer = wx.StaticBoxSizer(snap_box, wx.VERTICAL)

    # Enable grid snapping toggle
    main_window.grid_snap_cb = wx.CheckBox( main_window.sidebar,
                                label="Enable Grid Snapping")
    main_window.grid_snap_cb.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.grid_snap_cb.SetValue(
    True)  # Default to enabled for easier testing
    main_window.grid_snap_cb.Bind(wx.EVT_CHECKBOX,  event_handlers.graph_canvas_event_handler.on_grid_snap_changed)
    snap_sizer.Add( main_window.grid_snap_cb, 0, wx.EXPAND | wx.ALL, 2)

    # Snap anchor point selection
    anchor_label = wx.StaticText( main_window.sidebar, label="Snap Anchor:")
    anchor_label.SetForegroundColour(wx.Colour(0, 0, 0))
    snap_sizer.Add(anchor_label, 0, wx.ALL, 2)

    main_window.snap_anchor_choice = wx.Choice( main_window.sidebar,
                                    choices=[
                                        "Upper Left", "Upper Center",
                                        "Upper Right", "Left Center",
                                        "Center", "Right Center",
                                        "Bottom Left", "Bottom Center",
                                        "Bottom Right"
    ])
    main_window.snap_anchor_choice.SetSelection(4)  # Default to "Center"
    # White text on black background for better visibility
    main_window.snap_anchor_choice.SetForegroundColour(wx.Colour(255, 255, 255))
    main_window.snap_anchor_choice.SetBackgroundColour(wx.Colour(0, 0, 0))
    main_window.snap_anchor_choice.Refresh()
    main_window.snap_anchor_choice.Bind(wx.EVT_CHOICE,
                                event_handlers.graph_canvas_event_handler.on_snap_anchor_changed)
    snap_sizer.Add( main_window.snap_anchor_choice, 0, wx.EXPAND | wx.ALL, 2)
    
    # Initialize canvas with anchor selection
    if hasattr( main_window.canvas, 'snap_anchor'):
        anchor_names = [
            "upper_left", "upper_center", "upper_right", "left_center",
            "center", "right_center", "bottom_left", "bottom_center",
            "bottom_right"
        ]
        selection =  main_window.snap_anchor_choice.GetSelection()
        main_window.canvas.snap_anchor = anchor_names[
            selection] if selection >= 0 else "center"
        print(f"DEBUG: 🔗 Initial snap anchor: { main_window.canvas.snap_anchor}")

    sidebar_sizer.Add(snap_sizer, 0, wx.EXPAND | wx.ALL, 5)

    # Edge Rendering Options
    edge_box = wx.StaticBox( main_window.sidebar, label="Edge Rendering")
    edge_box.SetForegroundColour(wx.Colour(0, 0, 0))  # Black text
    edge_sizer = wx.StaticBoxSizer(edge_box, wx.VERTICAL)

    # Edge type selection
    edge_type_label = wx.StaticText( main_window.sidebar, label="Edge Type:")
    edge_type_label.SetForegroundColour(wx.Colour(0, 0, 0))
    edge_sizer.Add(edge_type_label, 0, wx.ALL, 2)

    main_window.edge_type_choice = wx.Choice( main_window.sidebar,
                                        choices=[
                                            "Straight Line", "Curved/Arc",
                                            "B-Spline", "Bézier Curve",
                                            "Cubic Spline", "NURBS",
                                            "Polyline", "Composite",
                                            "Freeform"
                                        ])
    main_window.edge_type_choice.SetSelection(2)  # Default to "B-Spline"
    # White text on black background for better visibility
    main_window.edge_type_choice.SetForegroundColour(wx.Colour(255, 255, 255))
    main_window.edge_type_choice.SetBackgroundColour(wx.Colour(0, 0, 0))
    main_window.edge_type_choice.Refresh()
    main_window.edge_type_choice.Bind(wx.EVT_CHOICE,  partial(event_handlers.graph_canvas_event_handler.on_edge_type_changed, main_window))
    edge_sizer.Add( main_window.edge_type_choice, 0, wx.EXPAND | wx.ALL, 2)

    # Prevent overlapping edges toggle
    main_window.prevent_edge_overlap_cb = wx.CheckBox(
    main_window.sidebar, label="Prevent Edge Overlaps")
    main_window.prevent_edge_overlap_cb.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.prevent_edge_overlap_cb.SetValue(False)  # Default to disabled
    main_window.prevent_edge_overlap_cb.Bind(wx.EVT_CHECKBOX,
                                        event_handlers.graph_canvas_event_handler.on_prevent_edge_overlap_changed)
    edge_sizer.Add( main_window.prevent_edge_overlap_cb, 0, wx.EXPAND | wx.ALL, 2)

    # Control points editing toggle
    main_window.enable_control_points_cb = wx.CheckBox(main_window.sidebar, label="Enable Control Points")
    main_window.enable_control_points_cb.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.enable_control_points_cb.SetValue(
    True)  # Default to enabled for testing
    main_window.enable_control_points_cb.Bind(
    wx.EVT_CHECKBOX,  event_handlers.graph_canvas_event_handler.on_enable_control_points_changed)
    edge_sizer.Add( main_window.enable_control_points_cb, 0, wx.EXPAND | wx.ALL, 2)

    # Relative control points toggle
    main_window.relative_control_points_cb = wx.CheckBox(
        main_window.sidebar, label="Keep Control Points Relative")
    main_window.relative_control_points_cb.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.relative_control_points_cb.SetValue(True)  # Default to enabled
    main_window.relative_control_points_cb.Bind(
    wx.EVT_CHECKBOX,  event_handlers.graph_canvas_event_handler.on_relative_control_points_changed)
    edge_sizer.Add( main_window.relative_control_points_cb, 0, wx.EXPAND | wx.ALL,
                    2)

    # Edge anchor position choice
    edge_anchor_label = wx.StaticText( main_window.sidebar, label="Edge Anchor:")
    edge_anchor_label.SetForegroundColour(wx.Colour(0, 0, 0))
    edge_sizer.Add(edge_anchor_label, 0, wx.ALL, 2)
    
    anchor_choices = [
        "Free", "Center", "Nearest Face", "Left Center", "Right Center",
                        "Top Center", "Bottom Center", "Top Left", "Top Right", 
        "Bottom Left", "Bottom Right"
    ]
    main_window.edge_anchor_choice = wx.Choice( main_window.sidebar,
                                        choices=anchor_choices)
    main_window.edge_anchor_choice.SetForegroundColour(wx.Colour(255, 255, 255))
    main_window.edge_anchor_choice.SetBackgroundColour(wx.Colour(0, 0, 0))
    main_window.edge_anchor_choice.Refresh()
    main_window.edge_anchor_choice.SetSelection(2)  # Default to "Nearest Face"
    main_window.edge_anchor_choice.Bind(wx.EVT_CHOICE,
                                    event_handlers.graph_canvas_event_handler.on_edge_anchor_changed)
    edge_sizer.Add( main_window.edge_anchor_choice, 0, wx.EXPAND | wx.ALL, 2)

    # Show anchor points toggle
    main_window.show_anchor_points_cb = wx.CheckBox( main_window.sidebar,
                                                label="Show Anchor Points")
    main_window.show_anchor_points_cb.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.show_anchor_points_cb.SetValue(False)  # Default to disabled
    main_window.show_anchor_points_cb.Bind(wx.EVT_CHECKBOX,
                                        event_handlers.graph_canvas_event_handler.on_show_anchor_points_changed)
    edge_sizer.Add( main_window.show_anchor_points_cb, 0, wx.EXPAND | wx.ALL, 2)

    sidebar_sizer.Add(edge_sizer, 0, wx.EXPAND | wx.ALL, 5)
    
    # B-spline controls will be created on-demand
    main_window.bspline_controls_created = False
    main_window.bspline_added_to_sizer = False


    m_dependency_list_panel.setup_dependency_list_panel(
        main_window,
        sidebar_sizer,
        partial(m_sidebar_event_handler.on_individual_pane_changed, main_window),
    )
    main_window.sidebar.SetSizer(sidebar_sizer)
    # Enable scrolling by setting virtual size
    main_window.sidebar.FitInside()

    # Set sidebar sizer
    main_window.sidebar.SetSizer(sidebar_sizer)

    # Bind canvas events
    main_window.canvas.selection_changed.connect(partial(m_selector.on_selection_changed, main_window))
    main_window.canvas.graph_modified.connect(partial(event_handlers.menubar_event_handler.on_graph_modified, main_window))
    
    # Set up undo/redo callback for UI updates
    main_window.managers.undo_redo_manager.add_callback(partial(event_handlers.menubar_event_handler.update_undo_redo_ui, main_window))
    
    # Enhanced styling will be applied later in the setup process
    
    # Initialize undo/redo UI state
    event_handlers.menubar_event_handler.update_undo_redo_ui(main_window)
    
    # Initialize move tool UI state
    m_sidebar_event_handler.update_move_tool_ui(main_window)
    
    # Initialize zoom sensitivity
    event_handlers.graph_canvas_zoom_event_handler.update_canvas_zoom_sensitivity(main_window)
    
    # Apply enhanced styling for better visibility
    main_window.apply_enhanced_styling()
    
    # Initialize canvas with checkbox states (after all UI controls are created)
    if hasattr( main_window.canvas, 'grid_snapping_enabled'):
        main_window.canvas.grid_snapping_enabled =  main_window.grid_snap_cb.GetValue()
        print(
            f"DEBUG: 🔗 Initial grid snapping state: { main_window.canvas.grid_snapping_enabled}"
        )
    if hasattr( main_window.canvas, 'control_points_enabled'):
        main_window.canvas.control_points_enabled =  main_window.enable_control_points_cb.GetValue(
        )
        print(
            f"DEBUG: 🎛️ Initial control points state: { main_window.canvas.control_points_enabled}"
        )
    
    # Add Property Panel (rename to avoid confusion with Graph Properties section)
    main_window.property_panel_pane = wx.CollapsiblePane(main_window.sidebar, label="Property Panel")
    main_window.property_panel_pane.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.collapsible_panes.append(main_window.property_panel_pane)
    # Bind individual pane expansion events
    main_window.property_panel_pane.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, partial(m_sidebar_event_handler.on_individual_pane_changed, main_window))
    
    property_panel_window = main_window.property_panel_pane.GetPane()
    property_panel_sizer = wx.BoxSizer(wx.VERTICAL)
    
    from graph_canvas.presentation.desktop.gui.property_panel import PropertyPanel
    main_window.property_panel = PropertyPanel(property_panel_window)  # Use pane window as parent
    property_panel_sizer.Add(main_window.property_panel, 1, wx.EXPAND | wx.ALL, 2)
    
    property_panel_window.SetSizer(property_panel_sizer)
    sidebar_sizer.Add(main_window.property_panel_pane, 0, wx.EXPAND | wx.ALL, 2)
    # Expose the property panel sizer so other controls (e.g., control points) can be placed under it
    main_window.property_panel_sizer = property_panel_sizer

    # Always-present collapsible: Control Points
    main_window.control_points_pane = wx.CollapsiblePane(main_window.sidebar, label="Control Points")
    main_window.control_points_pane.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.collapsible_panes.append(main_window.control_points_pane)
    main_window.control_points_pane.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, partial(m_sidebar_event_handler.on_individual_pane_changed, main_window))
    cp_window = main_window.control_points_pane.GetPane()
    cp_sizer = wx.BoxSizer(wx.VERTICAL)
    # Empty container; populated by event_handlers.sidebar_event_handler.show_curve_controls
    cp_window.SetSizer(cp_sizer)
    sidebar_sizer.Add(main_window.control_points_pane, 0, wx.EXPAND | wx.ALL, 5)

    # Always-present collapsible: Composite Segments
    main_window.composite_pane = wx.CollapsiblePane(main_window.sidebar, label="Composite Segments")
    main_window.composite_pane.SetForegroundColour(wx.Colour(0, 0, 0))
    main_window.collapsible_panes.append(main_window.composite_pane)
    main_window.composite_pane.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, partial(m_sidebar_event_handler.on_individual_pane_changed, main_window))
    comp_window = main_window.composite_pane.GetPane()
    comp_sizer = wx.BoxSizer(wx.VERTICAL)
    # Empty container; populated by event_handlers.sidebar_event_handler when curve type is composite
    comp_window.SetSizer(comp_sizer)
    sidebar_sizer.Add(main_window.composite_pane, 0, wx.EXPAND | wx.ALL, 5)

    # Initialize edge anchor settings
    main_window.canvas.edge_anchor_mode = "nearest_face"  # Default mode
    main_window.canvas.show_anchor_points =  main_window.show_anchor_points_cb.GetValue()
    print(
        f"DEBUG: 🔗 Initial edge anchor mode: { main_window.canvas.edge_anchor_mode}"
    )
    print(
        f"DEBUG: 🔗 Initial show anchor points: { main_window.canvas.show_anchor_points}"
    )
    
    # Update sidebar virtual size for scrolling after all controls are added
    wx.CallAfter(partial(update_sidebar_scrolling, main_window))


def update_sidebar_scrolling(main_window: "m_main_window.MainWindow"):
        """Update the virtual size of the scrolled sidebar after all controls are added."""

        if hasattr(main_window, 'sidebar'):
            # Get the required size to fit all controls
            main_window.sidebar.FitInside()
            # Enable automatic scrollbar showing/hiding
            main_window.sidebar.ShowScrollbars(wx.SHOW_SB_DEFAULT, wx.SHOW_SB_DEFAULT)
   