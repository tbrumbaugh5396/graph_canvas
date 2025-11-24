"""
Container for application managers accessible via main_window.managers.
"""


from graph_canvas.presentation.desktop.utils.managers.undo_redo_manager import UndoRedoManager
from graph_canvas.presentation.desktop.utils.managers.hotkey_manager import HotkeyManager
from graph_canvas.presentation.desktop.utils.managers.clipboard_manager import ClipboardManager
from graph_canvas.presentation.desktop.utils.managers.layout_manager import LayoutManager
from graph_canvas.presentation.desktop.utils.managers.file_manager import FileManager
from graph_canvas.presentation.desktop.utils.managers.theme_manager import ThemeManager
from graph_canvas.presentation.desktop.utils.managers.zoom_manager import ZoomManager


class AppManagers:
    def __init__(self, main_window):
        # Instantiate core managers
        self.undo_redo_manager = UndoRedoManager(max_history=50)
        self.clipboard_manager = ClipboardManager()
        self.layout_manager = LayoutManager(main_window)
        self.file_manager = FileManager(main_window)
        self.hotkey_manager = HotkeyManager(main_window)
        self.theme_manager = ThemeManager()
        self.zoom_manager = ZoomManager()

        # Ensure a default theme is set and expose theme database on main_window
        if not self.theme_manager.get_current_theme():
            self.theme_manager.set_theme("Light")
        # Provide legacy access path for existing code
        try:
            main_window.theme_database = self.theme_manager.theme_database
        except Exception:
            # In case main_window isn't fully constructed; ignore
            pass


