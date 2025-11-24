"""Entry point for `python3 -m graph_canvas`."""

from __future__ import annotations

from .cli import run as run_cli


def main() -> None:
    run_cli()


if __name__ == "__main__":
    main()

