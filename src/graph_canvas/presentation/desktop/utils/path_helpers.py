"""
Utilities to ensure the project and optional sibling dependencies are importable
both when running as a source checkout (python -m main) and when installed as a
package (entry points).
"""

import os
import sys
from pathlib import Path
from typing import Optional


def ensure_project_on_path(anchor_file: Optional[str] = None) -> None:
    """Ensure project root is on sys.path for direct execution.

    If anchor_file is provided, it is used to resolve the project root; otherwise
    we walk up from this file.
    """
    try:
        current = Path(anchor_file).resolve() if anchor_file else Path(__file__).resolve()
        project_root = current.parent if current.is_file() else current
        # bubble up to repo root (contains src/)
        for _ in range(3):
            if (project_root / "src").exists():
                break
            project_root = project_root.parent
        candidates = [str(project_root), str(project_root / "src")]
        for candidate in candidates:
            if os.path.isdir(candidate) and candidate not in sys.path:
                sys.path.insert(0, candidate)
    except Exception:
        pass


def ensure_mvc_mvu_on_path() -> None:
    """Ensure the optional MVC_MVU sibling repo is importable if present."""
    try:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sibling = os.path.join(root, 'MVC_MVU')
        if os.path.isdir(sibling) and sibling not in sys.path:
            sys.path.insert(0, sibling)
    except Exception:
        pass


