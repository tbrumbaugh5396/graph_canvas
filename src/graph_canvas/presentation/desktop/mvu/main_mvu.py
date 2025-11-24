from dataclasses import dataclass, replace
from typing import Any, Optional, Tuple

# MVU framework imports (expects MVC_MVU on sys.path)
from mvc_mvu.core import Model
from mvc_mvu.core import UpdateResult
from mvc_mvu.messages import MessageEnum, make_message, get_msg_type, get_msg_data
from mvc_mvu.effects import Commands
from mvc_mvu.mvc_adapter import UIState
from . import file_mvu, theme_mvu, view_mvu, canvas_mvu, status_mvu, background_mvu, clipboard_mvu


@dataclass
class AppModel(Model):
    sidebar_visible: bool = True
    status_bar_visible: bool = True
    zoom_seq: int = 0  # monotonic counter to trigger zoom actions in ui_render
    last_zoom_action: str = ""  # one of: "in", "out", "fit"
    grid_color: Optional[Tuple[int, int, int]] = None  # RGB
    # File ops
    current_file_path: Optional[str] = None
    last_file_seq: int = 0
    last_loaded_json: Optional[str] = None
    last_file_status: str = ""  # 'loaded' | 'saved' | 'error'
    # Grid visibility and snapping
    grid_visible: bool = True
    snap_enabled: bool = True
    # Theme
    current_theme_name: Optional[str] = None
    last_theme_seq: int = 0
    # Undo/Redo UI state
    can_undo: bool = False
    can_redo: bool = False
    last_undo_seq: int = 0
    # Status bar counts
    node_count: int = 0
    edge_count: int = 0
    last_status_seq: int = 0
    # Movement/zoom sensitivity and rotation
    move_x_sens: float = 1.0
    move_y_sens: float = 1.0
    move_inverted: bool = False
    zoom_sensitivity: float = 1.0
    rotation_deg: float = 0.0
    zoom_input_mode: str = "wheel"  # 'wheel' | 'touchpad' | 'both'
    # Background updates sequence
    bg_seq: int = 0
    bg_image_seq: int = 0
    bg_last_load_path: Optional[str] = None
    bg_last_load_index: int = -1
    # Layout
    layout_seq: int = 0
    last_layout_name: Optional[str] = None
    # Property edits
    node_text_seq: int = 0
    last_node_text_id: Optional[str] = None
    last_node_text_value: Optional[str] = None
    edge_text_seq: int = 0
    last_edge_text_id: Optional[str] = None
    last_edge_text_value: Optional[str] = None


class Msg(MessageEnum):
    SET_SIDEBAR_VISIBLE = ("SET_SIDEBAR_VISIBLE", "visible")
    SET_STATUS_VISIBLE = ("SET_STATUS_VISIBLE", "visible")
    TOGGLE_SIDEBAR = ("TOGGLE_SIDEBAR",)
    TOGGLE_STATUS = ("TOGGLE_STATUS",)
    ZOOM_IN = ("ZOOM_IN",)
    ZOOM_OUT = ("ZOOM_OUT",)
    ZOOM_FIT = ("ZOOM_FIT",)
    SET_GRID_COLOR = ("SET_GRID_COLOR", "r", "g", "b")
    SET_GRID_VISIBLE = ("SET_GRID_VISIBLE", "visible")
    TOGGLE_GRID = ("TOGGLE_GRID",)
    SET_SNAP_ENABLED = ("SET_SNAP_ENABLED", "enabled")
    TOGGLE_SNAP = ("TOGGLE_SNAP",)
    LOAD_GRAPH_FROM_PATH = ("LOAD_GRAPH_FROM_PATH", "path")
    FILE_LOADED = ("FILE_LOADED", "content")
    FILE_LOAD_ERROR = ("FILE_LOAD_ERROR", "error")
    SAVE_GRAPH_TO_PATH = ("SAVE_GRAPH_TO_PATH", "path", "content")
    FILE_SAVED = ("FILE_SAVED",)
    FILE_SAVE_ERROR = ("FILE_SAVE_ERROR", "error")
    # Theme
    SET_THEME = ("SET_THEME", "name")
    # Undo/Redo state
    SET_UNDO_REDO_STATE = ("SET_UNDO_REDO_STATE", "can_undo", "can_redo")
    # Status bar counts
    SET_COUNTS = ("SET_COUNTS", "nodes", "edges")
    # Sensitivity and rotation
    SET_MOVE_SENSITIVITY = ("SET_MOVE_SENSITIVITY", "x", "y", "inverted")
    SET_ZOOM_SENSITIVITY = ("SET_ZOOM_SENSITIVITY", "value")
    SET_ROTATION = ("SET_ROTATION", "angle")
    SET_ZOOM_INPUT_MODE = ("SET_ZOOM_INPUT_MODE", "mode")
    # Background
    BG_UPDATE = ("BG_UPDATE",)
    BG_LOAD_IMAGE = ("BG_LOAD_IMAGE", "index", "path")
    BG_IMAGE_LOADED = ("BG_IMAGE_LOADED", "index", "path")
    BG_IMAGE_ERROR = ("BG_IMAGE_ERROR", "index", "error")
    # Layout
    LAYOUT_APPLY = ("LAYOUT_APPLY", "name")
    # Properties
    SET_NODE_TEXT = ("SET_NODE_TEXT", "node_id", "text")
    SET_EDGE_TEXT = ("SET_EDGE_TEXT", "edge_id", "text")
    # Clipboard
    CLIPBOARD_COPY = ("CLIPBOARD_COPY",)
    CLIPBOARD_CUT = ("CLIPBOARD_CUT",)
    CLIPBOARD_PASTE = ("CLIPBOARD_PASTE",)


def initial_model_fn(
    sidebar_visible: bool = True,
    status_bar_visible: bool = True,
    grid_visible: bool = True,
    snap_enabled: bool = True,
) -> AppModel:
    return AppModel(
        sidebar_visible=sidebar_visible,
        status_bar_visible=status_bar_visible,
        grid_visible=grid_visible,
        snap_enabled=snap_enabled,
    )


def update_fn(message: Any, model: AppModel) -> UpdateResult[AppModel]:
    t = get_msg_type(message)
    d = get_msg_data(message)

    # Delegate to modular handlers first
    for mod in (file_mvu, theme_mvu, view_mvu, canvas_mvu, status_mvu, background_mvu, clipboard_mvu):
        try:
            res = mod.update(t, d, model)
            if res is not None:
                return res
        except Exception as e:
            print(f"mvu delegate update error in {mod.__name__}: {e}")

    if t == Msg.SET_SIDEBAR_VISIBLE:
        return UpdateResult(model=replace(model, sidebar_visible=bool(d["visible"])))

    if t == Msg.SET_STATUS_VISIBLE:
        return UpdateResult(model=replace(model, status_bar_visible=bool(d["visible"])))

    if t == Msg.TOGGLE_SIDEBAR:
        return UpdateResult(model=replace(model, sidebar_visible=not model.sidebar_visible))

    if t == Msg.TOGGLE_STATUS:
        return UpdateResult(model=replace(model, status_bar_visible=not model.status_bar_visible))

    if t == Msg.ZOOM_IN:
        return UpdateResult(model=replace(model, zoom_seq=model.zoom_seq + 1, last_zoom_action="in"))

    if t == Msg.ZOOM_OUT:
        return UpdateResult(model=replace(model, zoom_seq=model.zoom_seq + 1, last_zoom_action="out"))

    if t == Msg.ZOOM_FIT:
        return UpdateResult(model=replace(model, zoom_seq=model.zoom_seq + 1, last_zoom_action="fit"))

    if t == Msg.SET_GRID_COLOR:
        r, g, b = int(d["r"]), int(d["g"]), int(d["b"])
        return UpdateResult(model=replace(model, grid_color=(r, g, b)))

    if t == Msg.SET_GRID_VISIBLE:
        return UpdateResult(model=replace(model, grid_visible=bool(d["visible"])))

    if t == Msg.TOGGLE_GRID:
        return UpdateResult(model=replace(model, grid_visible=not model.grid_visible))

    if t == Msg.SET_SNAP_ENABLED:
        return UpdateResult(model=replace(model, snap_enabled=bool(d["enabled"])))

    if t == Msg.TOGGLE_SNAP:
        return UpdateResult(model=replace(model, snap_enabled=not model.snap_enabled))

    if t == Msg.LOAD_GRAPH_FROM_PATH:
        path = d["path"]
        return UpdateResult(
            model=replace(model, current_file_path=path),
            commands=[
                Commands.read_file(
                    path,
                    on_success=lambda content: make_message(Msg.FILE_LOADED, content=content),
                    on_error=lambda err: make_message(Msg.FILE_LOAD_ERROR, error=str(err))
                )
            ]
        )

    if t == Msg.FILE_LOADED:
        return UpdateResult(
            model=replace(model, last_loaded_json=d["content"], last_file_seq=model.last_file_seq + 1, last_file_status="loaded")
        )

    if t == Msg.FILE_LOAD_ERROR:
        return UpdateResult(model=replace(model, last_file_status=f"error:{d['error']}"))

    if t == Msg.SAVE_GRAPH_TO_PATH:
        path = d["path"]
        content = d["content"]
        return UpdateResult(
            model=replace(model, current_file_path=path),
            commands=[
                Commands.write_file(
                    path,
                    content,
                    on_success=lambda: make_message(Msg.FILE_SAVED),
                    on_error=lambda err: make_message(Msg.FILE_SAVE_ERROR, error=str(err))
                )
            ]
        )

    if t == Msg.FILE_SAVED:
        return UpdateResult(model=replace(model, last_file_status="saved", last_file_seq=model.last_file_seq + 1))

    if t == Msg.FILE_SAVE_ERROR:
        return UpdateResult(model=replace(model, last_file_status=f"error:{d['error']}"))

    if t == Msg.SET_THEME:
        return UpdateResult(model=replace(model, current_theme_name=d["name"], last_theme_seq=model.last_theme_seq + 1))

    if t == Msg.SET_UNDO_REDO_STATE:
        return UpdateResult(model=replace(model, can_undo=bool(d["can_undo"]), can_redo=bool(d["can_redo"]), last_undo_seq=model.last_undo_seq + 1))

    if t == Msg.SET_COUNTS:
        return UpdateResult(model=replace(model, node_count=int(d["nodes"]), edge_count=int(d["edges"]), last_status_seq=model.last_status_seq + 1))

    if t == Msg.SET_MOVE_SENSITIVITY:
        return UpdateResult(model=replace(model, move_x_sens=float(d["x"]), move_y_sens=float(d["y"]), move_inverted=bool(d["inverted"])) )

    if t == Msg.SET_ZOOM_SENSITIVITY:
        return UpdateResult(model=replace(model, zoom_sensitivity=float(d["value"])) )

    if t == Msg.SET_ROTATION:
        return UpdateResult(model=replace(model, rotation_deg=float(d["angle"])) )

    if t == Msg.SET_ZOOM_INPUT_MODE:
        mode = str(d["mode"]).lower()
        if mode not in ("wheel", "touchpad", "both"):
            mode = "wheel"
        try:
            print(f"DEBUG: MVU update SET_ZOOM_INPUT_MODE -> {mode}")
        except Exception:
            pass
        return UpdateResult(model=replace(model, zoom_input_mode=mode))

    if t == Msg.BG_UPDATE:
        return UpdateResult(model=replace(model, bg_seq=model.bg_seq + 1))

    if t == Msg.BG_LOAD_IMAGE:
        index = int(d["index"]) ; path = d["path"]
        return UpdateResult(
            model=replace(model, bg_last_load_index=index, bg_last_load_path=path),
            commands=[
                Commands.read_file(
                    path,
                    on_success=lambda content: make_message(Msg.BG_IMAGE_LOADED, index=index, path=path),
                    on_error=lambda err: make_message(Msg.BG_IMAGE_ERROR, index=index, error=str(err))
                )
            ]
        )

    if t == Msg.BG_IMAGE_LOADED:
        return UpdateResult(model=replace(model, bg_image_seq=model.bg_image_seq + 1, bg_seq=model.bg_seq + 1))

    if t == Msg.BG_IMAGE_ERROR:
        return UpdateResult(model=model)

    if t == Msg.LAYOUT_APPLY:
        return UpdateResult(model=replace(model, layout_seq=model.layout_seq + 1, last_layout_name=d["name"]))

    if t == Msg.SET_NODE_TEXT:
        return UpdateResult(model=replace(
            model,
            last_node_text_id=d["node_id"],
            last_node_text_value=d["text"],
            node_text_seq=model.node_text_seq + 1
        ))

    if t == Msg.SET_EDGE_TEXT:
        return UpdateResult(model=replace(
            model,
            last_edge_text_id=d["edge_id"],
            last_edge_text_value=d["text"],
            edge_text_seq=model.edge_text_seq + 1
        ))

    if t in (Msg.CLIPBOARD_COPY, Msg.CLIPBOARD_CUT, Msg.CLIPBOARD_PASTE):
        # Render-only clipboard operations
        return UpdateResult(model=model)

    return UpdateResult(model=model)


def ui_render(ui_state: UIState, model: AppModel) -> None:
    """
    Apply model changes to the existing MVC UI (MainWindow) idempotently.
    """
    try:
        main_window = ui_state.get_widget("main_window")
        if main_window is None:
            return

        last = ui_state.model_snapshot

        # Delegate renders
        try:
            view_mvu.render(ui_state, model, last)
        except Exception as e:
            print(f"mvu delegate render error (view): {e}")

        try:
            canvas_mvu.render(ui_state, model, last)
        except Exception as e:
            print(f"mvu delegate render error (canvas): {e}")

        # Grid color
        if model.grid_color is not None and (last is None or getattr(last, "grid_color", None) != model.grid_color):
            try:
                if hasattr(main_window, 'canvas') and main_window.canvas:
                    # Apply grid color to canvas via existing command pattern
                    rgb = model.grid_color
                    main_window.canvas.grid_color = rgb
                    if hasattr(main_window, 'grid_color_btn'):
                        import wx as _wx
                        main_window.grid_color_btn.SetBackgroundColour(_wx.Colour(*rgb))
                    main_window.canvas.Refresh()
            except Exception as e:
                print(f"MVU ui_render grid color error: {e}")

        # Grid visibility
        if last is None or getattr(last, "grid_visible", None) != model.grid_visible:
            try:
                if hasattr(main_window, 'canvas') and main_window.canvas:
                    main_window.canvas.grid_style = "grid" if model.grid_visible else "none"
                    main_window.canvas.Refresh()
            except Exception as e:
                print(f"MVU ui_render grid visibility error: {e}")

        # Snap enabled
        if last is None or getattr(last, "snap_enabled", None) != model.snap_enabled:
            try:
                if hasattr(main_window, 'canvas') and main_window.canvas:
                    enabled = model.snap_enabled
                    # Maintain both flags used in canvas
                    if hasattr(main_window.canvas, 'grid_snapping_enabled'):
                        main_window.canvas.grid_snapping_enabled = enabled
                    if hasattr(main_window.canvas, 'snap_to_grid'):
                        main_window.canvas.snap_to_grid = enabled
            except Exception as e:
                print(f"MVU ui_render snap error: {e}")

        try:
            file_mvu.render(ui_state, model, last)
        except Exception as e:
            print(f"mvu delegate render error (file): {e}")
        try:
            background_mvu.render(ui_state, model, last)
        except Exception as e:
            print(f"mvu delegate render error (background): {e}")

        try:
            theme_mvu.render(ui_state, model, last)
        except Exception as e:
            print(f"mvu delegate render error (theme): {e}")

        try:
            status_mvu.render(ui_state, model, last)
        except Exception as e:
            print(f"mvu delegate render error (status): {e}")

        # canvas_mvu already handles sensitivity/zoom/rotation

        # Update snapshot after applying changes
        ui_state.model_snapshot = model
    except Exception as e:
        print(f"MVU ui_render error: {e}")


