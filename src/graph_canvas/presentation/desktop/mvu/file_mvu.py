from typing import Any, Optional

from mvc_mvu.core import UpdateResult
from mvc_mvu.effects import Commands
from mvc_mvu.messages import make_message
import graph_canvas.presentation.desktop.mvu.main_mvu as m_main_mvu


def update(t: Any, d: dict, model) -> Optional[UpdateResult]:
    """Handle file load/save messages and return UpdateResult or None."""
    try:
        # Message enum comparisons are done by identity in caller; here we match by name
        name = getattr(t, 'name', None)
        if name:
            try:
                print(f"file_mvu.update received message: {name}")
            except Exception:
                pass
        if name == 'LOAD_GRAPH_FROM_PATH':
            path = d["path"]
            try:
                print(f"file_mvu.update: LOAD_GRAPH_FROM_PATH path={path}")
            except Exception:
                pass
            return UpdateResult(
                model=type(model)(**{**model.__dict__, 'current_file_path': path}),
                commands=[
                    Commands.read_file(
                        path,
                        on_success=lambda content: make_message(m_main_mvu.Msg.FILE_LOADED, content=content),
                        on_error=lambda err: make_message(m_main_mvu.Msg.FILE_LOAD_ERROR, error=str(err))
                    )
                ]
            )
        if name == 'FILE_LOADED':
            try:
                print("file_mvu.update: FILE_LOADED")
            except Exception:
                pass
            return UpdateResult(
                model=type(model)(**{**model.__dict__, 'last_loaded_json': d['content'], 'last_file_seq': model.last_file_seq + 1, 'last_file_status': 'loaded'})
            )
        if name == 'FILE_LOAD_ERROR':
            try:
                print(f"file_mvu.update: FILE_LOAD_ERROR error={d.get('error')}")
            except Exception:
                pass
            return UpdateResult(model=type(model)(**{**model.__dict__, 'last_file_status': f"error:{d['error']}"}))
        if name == 'SAVE_GRAPH_TO_PATH':
            path = d['path']
            content = d['content']
            return UpdateResult(
                model=type(model)(**{**model.__dict__, 'current_file_path': path}),
                commands=[
                    Commands.write_file(
                        path,
                        content,
                        on_success=lambda: make_message(m_main_mvu.Msg.FILE_SAVED),
                        on_error=lambda err: make_message(m_main_mvu.Msg.FILE_SAVE_ERROR, error=str(err))
                    )
                ]
            )
        if name == 'FILE_SAVED':
            return UpdateResult(model=type(model)(**{**model.__dict__, 'last_file_status': 'saved', 'last_file_seq': model.last_file_seq + 1}))
        if name == 'FILE_SAVE_ERROR':
            return UpdateResult(model=type(model)(**{**model.__dict__, 'last_file_status': f"error:{d['error']}"}))
    except Exception as e:
        print(f"file_mvu.update error: {e}")
    return None


def render(ui_state, model, last) -> None:
    """Apply file load/save effects to MVC UI."""
    try:
        main_window = ui_state.get_widget('main_window') if ui_state else None
        if main_window is None:
            return
        if last is None or getattr(last, 'last_file_seq', None) != model.last_file_seq:
            if model.last_file_status == 'loaded' and model.last_loaded_json is not None:
                try:
                    print("file_mvu.render: applying loaded graph to UI")
                except Exception:
                    pass
                import wx as _wx
                def _apply_loaded():
                    import json
                    import graph_canvas.presentation.desktop.models.graph as m_graph
                    data = json.loads(model.last_loaded_json)
                    new_graph = m_graph.Graph.from_dict(data)
                    new_graph.file_path = model.current_file_path
                    new_graph.modified = False
                    main_window.current_graph = new_graph
                    if hasattr(main_window, 'canvas') and main_window.canvas:
                        main_window.canvas.set_graph(new_graph, emit_signal=False)
                        main_window.canvas.Refresh()
                        try:
                            print("file_mvu.render: canvas updated and refreshed")
                        except Exception:
                            pass
                    main_window.SetTitle(f"Graph Editor - {new_graph.name}")
                _wx.CallAfter(_apply_loaded)
            elif model.last_file_status == 'saved':
                import wx as _wx
                def _apply_saved():
                    if hasattr(main_window, 'current_graph') and main_window.current_graph:
                        main_window.current_graph.file_path = model.current_file_path
                        main_window.current_graph.modified = False
                        main_window.SetTitle(f"Graph Editor - {main_window.current_graph.name}")
                _wx.CallAfter(_apply_saved)
    except Exception as e:
        print(f"file_mvu.render error: {e}")


