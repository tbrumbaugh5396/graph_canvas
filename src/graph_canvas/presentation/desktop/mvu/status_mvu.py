from typing import Any, Optional

from mvc_mvu.core import UpdateResult


def update(t: Any, d: dict, model) -> Optional[UpdateResult]:
    name = getattr(t, 'name', None)
    if name == 'SET_UNDO_REDO_STATE':
        new_model = type(model)(**{**model.__dict__, 'can_undo': bool(d['can_undo']), 'can_redo': bool(d['can_redo']), 'last_undo_seq': model.last_undo_seq + 1})
        return UpdateResult(model=new_model)
    if name == 'SET_COUNTS':
        new_model = type(model)(**{**model.__dict__, 'node_count': int(d['nodes']), 'edge_count': int(d['edges']), 'last_status_seq': model.last_status_seq + 1})
        return UpdateResult(model=new_model)
    return None


def render(ui_state, model, last) -> None:
    try:
        mw = ui_state.get_widget('main_window') if ui_state else None
        if not mw:
            return
        # Undo/Redo
        if last is None or getattr(last, 'last_undo_seq', None) != model.last_undo_seq:
            if hasattr(mw, 'undo_item'):
                mw.undo_item.Enable(bool(model.can_undo))
            if hasattr(mw, 'redo_item'):
                mw.redo_item.Enable(bool(model.can_redo))
            tb = mw.GetToolBar()
            if tb:
                import wx as _wx
                try:
                    tb.EnableTool(_wx.ID_UNDO, bool(model.can_undo))
                    tb.EnableTool(_wx.ID_REDO, bool(model.can_redo))
                except Exception:
                    pass
        # Status bar counts
        if last is None or getattr(last, 'last_status_seq', None) != model.last_status_seq:
            if hasattr(mw, 'statusbar') and mw.statusbar:
                mw.statusbar.SetStatusText(f"Nodes: {model.node_count}", 1)
                mw.statusbar.SetStatusText(f"Edges: {model.edge_count}", 2)
    except Exception as e:
        print(f"status_mvu.render error: {e}")


