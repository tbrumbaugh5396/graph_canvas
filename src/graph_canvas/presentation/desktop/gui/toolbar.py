

import wx
# import wx.ArtProvider
import graph_canvas.presentation.desktop.gui.main_window as m_main_window


def setup_toolbars(main_window: "m_main_window.MainWindow"):
        """Set up the toolbar."""

        toolbar = main_window.CreateToolBar()

        # File tools
        toolbar.AddTool(wx.ID_NEW, "New", wx.ArtProvider.GetBitmap(wx.ART_NEW))
        toolbar.AddTool(wx.ID_OPEN, "Open",
                        wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN))
        toolbar.AddTool(wx.ID_SAVE, "Save",
                        wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE))
        toolbar.AddSeparator()
        
        # Edit tools
        main_window.undo_tool = toolbar.AddTool(wx.ID_UNDO, "Undo", 
                                        wx.ArtProvider.GetBitmap(wx.ART_UNDO))
        main_window.redo_tool = toolbar.AddTool(wx.ID_REDO, "Redo",
                                        wx.ArtProvider.GetBitmap(wx.ART_REDO))
        toolbar.AddSeparator()

        # Edit tools
        toolbar.AddTool(wx.ID_CUT, "Cut", wx.ArtProvider.GetBitmap(wx.ART_CUT))
        toolbar.AddTool(wx.ID_COPY, "Copy",
                        wx.ArtProvider.GetBitmap(wx.ART_COPY))
        toolbar.AddTool(wx.ID_PASTE, "Paste",
                        wx.ArtProvider.GetBitmap(wx.ART_PASTE))
        toolbar.AddSeparator()

        # View tools
        toolbar.AddTool(wx.ID_ZOOM_IN, "Zoom In",
                        wx.ArtProvider.GetBitmap(wx.ART_PLUS))
        toolbar.AddTool(wx.ID_ZOOM_OUT, "Zoom Out",
                        wx.ArtProvider.GetBitmap(wx.ART_MINUS))
        toolbar.AddTool(wx.ID_ZOOM_FIT, "Zoom Fit",
                        wx.ArtProvider.GetBitmap(wx.ART_FIND))

        toolbar.Realize()
