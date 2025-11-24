from typing import Any, Optional

from mvc_mvu.core import UpdateResult
from mvc_mvu.effects import Commands


def update(t: Any, d: dict, model) -> Optional[UpdateResult]:
    name = getattr(t, 'name', None)
    if name == 'BG_ADD':
        # Increment a version to trigger render; actual data lives in BackgroundManager
        new_model = type(model)(**{**model.__dict__, 'last_status_seq': model.last_status_seq})
        return UpdateResult(model=new_model)
    if name == 'BG_REMOVE':
        return UpdateResult(model=model)
    if name == 'BG_MOVE':
        return UpdateResult(model=model)
    if name == 'BG_UPDATE':
        return UpdateResult(model=model)
    if name == 'BG_LOAD_IMAGE':
        path = d['path']
        layer_index = int(d['index'])
        return UpdateResult(
            model=model,
            commands=[
                Commands.read_file(
                    path,
                    on_success=lambda content: ('BG_IMAGE_LOADED', {'index': layer_index, 'path': path, 'content': content}),
                    on_error=lambda err: ('BG_IMAGE_ERROR', {'index': layer_index, 'error': str(err)})
                )
            ]
        )
    if name in ('BG_IMAGE_LOADED', 'BG_IMAGE_ERROR'):
        # Bump bg_seq so render will refresh after applying bitmap
        return UpdateResult(model=type(model)(**{**model.__dict__, 'bg_seq': model.bg_seq + 1}))
    return None


def render(ui_state, model, last) -> None:
    try:
        mw = ui_state.get_widget('main_window') if ui_state else None
        if not mw or not hasattr(mw, 'canvas'):
            return
        # If background sequence changed, refresh canvas
        if last is None or getattr(last, 'bg_seq', None) != getattr(model, 'bg_seq', None):
            try:
                mw.canvas.Refresh()
            except Exception:
                pass

        # Apply last loaded image path to layer bitmap if changed
        if last is None or getattr(last, 'bg_image_seq', None) != getattr(model, 'bg_image_seq', None):
            try:
                idx = getattr(model, 'bg_last_load_index', -1)
                path = getattr(model, 'bg_last_load_path', None)
                if idx >= 0 and path:
                    # Load bitmap from path (synchronously here; content bytes not persisted)
                    bmp = None
                    import wx
                    if wx.FileExists(path):
                        img = wx.Image(path)
                        if img.IsOk():
                            bmp = img.ConvertToBitmap()
                    if bmp and 0 <= idx < len(mw.canvas.background_manager.layers):
                        layer = mw.canvas.background_manager.layers[idx]
                        layer.bitmap = bmp
                        mw.canvas.Refresh()
            except Exception as e:
                print(f"background_mvu.render load image error: {e}")
    except Exception as e:
        print(f"background_mvu.render error: {e}")


