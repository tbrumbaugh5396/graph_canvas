#!/usr/bin/env python3
"""Shim so `python3 -m main ...` continues to work alongside `python3 -m graph_canvas`."""

from __future__ import annotations

from graph_canvas.cli import run as run_cli


def main() -> None:
    run_cli()


if __name__ == "__main__":
    main()
