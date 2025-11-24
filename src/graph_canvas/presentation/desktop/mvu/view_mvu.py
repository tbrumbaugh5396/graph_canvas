from typing import Any, Optional

from mvc_mvu.core import UpdateResult


def update(t: Any, d: dict, model) -> Optional[UpdateResult]:
    name = getattr(t, 'name', None)
    if name in ('SET_SIDEBAR_VISIBLE', 'TOGGLE_SIDEBAR'):
        visible = (not model.sidebar_visible) if name == 'TOGGLE_SIDEBAR' else bool(d['visible'])
        new_model = type(model)(**{**model.__dict__, 'sidebar_visible': visible})
        return UpdateResult(model=new_model)
    if name in ('SET_STATUS_VISIBLE', 'TOGGLE_STATUS'):
        visible = (not model.status_bar_visible) if name == 'TOGGLE_STATUS' else bool(d['visible'])
        new_model = type(model)(**{**model.__dict__, 'status_bar_visible': visible})
        return UpdateResult(model=new_model)
    return None


def render(ui_state, model, last) -> None:
    try:
        mw = ui_state.get_widget('main_window') if ui_state else None
        if not mw:
            return
        if last is None or getattr(last, 'sidebar_visible', None) != model.sidebar_visible:
            if hasattr(mw, 'set_sidebar_visible'):
                mw.set_sidebar_visible(model.sidebar_visible)
        if last is None or getattr(last, 'status_bar_visible', None) != model.status_bar_visible:
            if hasattr(mw, 'set_status_bar_visible'):
                mw.set_status_bar_visible(model.status_bar_visible)
    except Exception as e:
        print(f"view_mvu.render error: {e}")


