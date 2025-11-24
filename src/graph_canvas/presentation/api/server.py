"""Helper to run the FastAPI server via uvicorn."""

from __future__ import annotations

import uvicorn

from graph_canvas.presentation.api.app import create_api_app


def serve(host: str = "0.0.0.0", port: int = 8000, reload: bool = False) -> None:
    """Start the API server."""
    uvicorn.run(
        create_api_app(),
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


