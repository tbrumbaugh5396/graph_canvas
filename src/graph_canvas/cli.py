"""Command-line entry points for Graph Canvas."""

from __future__ import annotations

import sys
from typing import Optional

import typer

app = typer.Typer(help="Graph Canvas launcher")


def run() -> None:
    """Entry point used by both `python3 -m graph_canvas` and `python3 -m main`."""
    if len(sys.argv) <= 1:
        _launch_desktop()
    else:
        app()


@app.command()
def desktop(debug: bool = typer.Option(False, "--debug", help="Enable wxPython debug logging")):
    """Launch the wxPython desktop UI explicitly."""
    _launch_desktop(debug=debug)


@app.command()
def api(
    host: str = typer.Option("0.0.0.0", help="Host interface to bind"),
    port: int = typer.Option(8000, help="Port to expose the API"),
    reload: bool = typer.Option(False, help="Enable uvicorn reload (dev only)"),
) -> None:
    """Run the FastAPI backend (required for desktop + web)."""
    _serve_api(host=host, port=port, reload=reload)


@app.command()
def web(
    host: str = typer.Option("0.0.0.0", help="Host interface to bind"),
    port: int = typer.Option(5173, help="Port for the Vite dev server"),
    api_url: Optional[str] = typer.Option(
        None,
        help="Base URL for the Graph Canvas API (defaults to current origin if omitted)",
    ),
    skip_install: bool = typer.Option(
        False, "--skip-install", help="Skip npm install even if node_modules missing"
    ),
) -> None:
    """Run the React/Vite development server."""
    _launch_web_ui(port=port, host=host, api_url=api_url, install=not skip_install)


def _launch_desktop(debug: bool = False) -> None:
    from .presentation.desktop.runner import launch as _launch

    _launch(debug=debug)


def _serve_api(host: str, port: int, reload: bool) -> None:
    from .presentation.api.server import serve as _serve

    _serve(host=host, port=port, reload=reload)


def _launch_web_ui(host: str, port: int, api_url: Optional[str], install: bool) -> None:
    from .presentation.web.runner import launch_web_ui as _launch_web

    _launch_web(port=port, host=host, api_url=api_url, install=install)