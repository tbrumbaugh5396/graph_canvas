from typing import Any, Optional

from mvc_mvu.core import UpdateResult


def update(t: Any, d: dict, model) -> Optional[UpdateResult]:
    name = getattr(t, 'name', None)
    if name == 'SET_THEME':
        # Bump sequence handled at top-level; keep simple here
        new_model = type(model)(**{**model.__dict__, 'current_theme_name': d['name'], 'last_theme_seq': model.last_theme_seq + 1})
        return UpdateResult(model=new_model)
    return None


def render(ui_state, model, last) -> None:
    try:
        if last is None or getattr(last, 'last_theme_seq', None) != model.last_theme_seq:
            main_window = ui_state.get_widget('main_window') if ui_state else None
            if not main_window:
                return
            name = model.current_theme_name
            if name and hasattr(main_window, 'managers') and getattr(main_window.managers, 'theme_manager', None):
                tm = main_window.managers.theme_manager
                tm.set_theme(name)
                tm.apply_theme_to_window(main_window)
                if hasattr(main_window, 'canvas') and main_window.canvas:
                    tm.apply_theme_to_window(main_window.canvas)
                if hasattr(main_window, 'theme_menu_items') and isinstance(main_window.theme_menu_items, dict):
                    for theme_name, item in main_window.theme_menu_items.items():
                        try:
                            item.Check(theme_name == name)
                        except Exception:
                            pass
    except Exception as e:
        print(f"theme_mvu.render error: {e}")


