"""Utility to launch the React web client via Vite."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Optional


WEB_UI_ROOT = Path(__file__).resolve().parent / "ui"


def launch_web_ui(
    port: int = 5173,
    host: str = "0.0.0.0",
    api_url: Optional[str] = None,
    install: bool = True,
) -> None:
    """Run the React development server."""
    if not WEB_UI_ROOT.exists():
        raise RuntimeError(f"Web UI not found at {WEB_UI_ROOT}")

    env = os.environ.copy()
    if api_url is not None:
        env["VITE_API_URL"] = api_url

    if install and not (WEB_UI_ROOT / "node_modules").exists():
        subprocess.run(["npm", "install"], cwd=WEB_UI_ROOT, check=True)

    command = ["npm", "run", "dev", "--", "--host", host, "--port", str(port)]
    subprocess.run(command, cwd=WEB_UI_ROOT, env=env, check=True)


