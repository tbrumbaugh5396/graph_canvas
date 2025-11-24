from typing import Any, Optional

from mvc_mvu.core import UpdateResult


def update(t: Any, d: dict, model) -> Optional[UpdateResult]:
    name = getattr(t, 'name', None)
    if name in ('CLIPBOARD_COPY', 'CLIPBOARD_CUT', 'CLIPBOARD_PASTE'):
        return UpdateResult(model=model)
    return None


def render(ui_state, model, last) -> None:
    try:
        mw = ui_state.get_widget('main_window') if ui_state else None
        if not mw:
            return
        # Clipboard actions are invoked by handlers; no extra render work
    except Exception as e:
        print(f"clipboard_mvu.render error: {e}")


