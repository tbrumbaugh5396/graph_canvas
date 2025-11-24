"""
Simple HTTP client to communicate with the FastAPI backend.
"""

from __future__ import annotations

import json
from typing import Dict, Iterable, List, Optional, Tuple

import requests


class BackendClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000") -> None:
        self.base_url = base_url.rstrip("/")

    def is_available(self) -> bool:
        endpoints = ("/healthz", "/health")
        for endpoint in endpoints:
            try:
                r = requests.get(f"{self.base_url}{endpoint}", timeout=1.0)
                if r.status_code == 200:
                    return True
            except Exception:
                continue
        return False

    def get_graph(self) -> Optional[Dict]:
        try:
            r = requests.get(f"{self.base_url}/graph", timeout=2.0)
            if r.ok:
                return r.json()
        except Exception:
            pass
        return None

    def set_graph(self, graph_dict: Dict) -> bool:
        try:
            r = requests.post(f"{self.base_url}/graph", json=graph_dict, timeout=3.0)
            return r.ok
        except Exception:
            return False

    def patch_node_positions(self, items: Iterable[Tuple[str, float, float]]) -> bool:
        payload = [{"id": nid, "x": x, "y": y} for nid, x, y in items]
        try:
            r = requests.patch(f"{self.base_url}/nodes/positions", json=payload, timeout=2.5)
            return r.ok
        except Exception:
            return False

    def create_node(self, x: float, y: float, text: str = "") -> Optional[Dict]:
        try:
            r = requests.post(f"{self.base_url}/nodes", json={"x": x, "y": y, "text": text}, timeout=2.5)
            if r.ok:
                return r.json()
        except Exception:
            pass
        return None

    def create_edge(self, source_id: str, target_id: str, text: str = "") -> Optional[Dict]:
        try:
            r = requests.post(
                f"{self.base_url}/edges",
                json={"source_id": source_id, "target_id": target_id, "text": text},
                timeout=2.5,
            )
            if r.ok:
                return r.json()
        except Exception:
            pass
        return None

    def update_node(self, graph_id: str, node_id: str, payload: Dict) -> bool:
        """Update a node using the graph-scoped API."""

        try:
            r = requests.patch(
                f"{self.base_url}/graphs/{graph_id}/nodes/{node_id}",
                json=payload,
                timeout=2.5,
            )
            return r.ok
        except Exception:
            return False

    def delete_node(self, graph_id: str, node_id: str) -> bool:
        """Delete a node via the API with compatibility fallback."""

        try:
            r = requests.delete(
                f"{self.base_url}/graphs/{graph_id}/nodes/{node_id}",
                timeout=2.5,
            )
            if r.ok:
                return True
        except Exception:
            pass

        # Fallback to legacy endpoint
        try:
            r = requests.delete(f"{self.base_url}/nodes/{node_id}", timeout=2.5)
            return r.ok
        except Exception:
            return False






