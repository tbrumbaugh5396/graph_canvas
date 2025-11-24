"""Desktop presentation layer entry point."""

from __future__ import annotations

from app import GraphEditorApp  # type: ignore


def launch(debug: bool = False) -> None:
    """Start the wxPython desktop experience."""
    app = GraphEditorApp(debug)
    app.MainLoop()


