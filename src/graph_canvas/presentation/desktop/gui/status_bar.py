"""
Status bar for the graph editor application.
"""

import graph_canvas.presentation.desktop.gui.main_window as m_main_window


def setup_status_bar_old(main_window: "m_main_window.MainWindow"):
        """Set up the status bar."""

        main_window.status_bar = main_window.CreateStatusBar(3)
        main_window.status_bar.SetStatusWidths([-2, -1, -1])
        main_window.update_status_bar()


def update_status_bar(main_window: "m_main_window.MainWindow"):
        """Update the status bar with current information."""

        stats = main_window.current_graph.get_statistics()
        main_window.status_bar.SetStatusText(f"Ready - {main_window.current_graph.name}", 0)
        main_window.status_bar.SetStatusText(f"Nodes: {stats['node_count']}", 1)
        main_window.status_bar.SetStatusText(f"Edges: {stats['edge_count']}", 2)


def setup_status_bar(main_window: "m_main_window.MainWindow"):
        """Set up the status bar."""

        main_window.statusbar = main_window.CreateStatusBar(3)
        main_window.statusbar.SetStatusText("Ready", 0)
        main_window.statusbar.SetStatusText("Tool: Select", 1)
        main_window.statusbar.SetStatusText("Zoom: 100%", 2)


def setup_status_bar(main_window: "m_main_window.MainWindow"):
    """Set up the status bar."""

    main_window.statusbar = main_window.CreateStatusBar(3)  # 3 fields
    main_window.statusbar.SetStatusWidths([-1, 150,
                                    150])  # Proportional, fixed, fixed
    main_window.statusbar.SetStatusText("Ready", 0)
    main_window.statusbar.SetStatusText("Nodes: 0", 1)
    main_window.statusbar.SetStatusText("Edges: 0", 2)
  