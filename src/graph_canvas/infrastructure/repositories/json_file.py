"""JSON-backed repository for persisting graphs across sessions."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Iterable, List

from graph_canvas.domain.entities import Graph
from graph_canvas.domain.exceptions import GraphNotFoundError
from graph_canvas.domain.repositories import GraphRepository


class JsonGraphRepository(GraphRepository):
    """Stores graph aggregates inside a single JSON file."""

    def __init__(self, path: str | Path, seed: Iterable[Graph] | None = None):
        self._path = Path(path)
        self._lock = threading.Lock()
        self._path.parent.mkdir(parents=True, exist_ok=True)

        if not self._path.exists():
            payload = [graph.to_dict() for graph in (seed or [])]
            self._write(payload)

    def list_graphs(self) -> Iterable[Graph]:
        return [Graph.from_dict(item) for item in self._read()]

    def get_graph(self, graph_id: str) -> Graph:
        for payload in self._read():
            if payload.get("id") == graph_id:
                return Graph.from_dict(payload)
        raise GraphNotFoundError(f"Graph '{graph_id}' not found")

    def save_graph(self, graph: Graph) -> Graph:
        data = self._read()
        updated = False
        for idx, payload in enumerate(data):
            if payload.get("id") == graph.id:
                data[idx] = graph.to_dict()
                updated = True
                break
        if not updated:
            data.append(graph.to_dict())
        self._write(data)
        return graph

    def delete_graph(self, graph_id: str) -> None:
        data = self._read()
        new_data = [payload for payload in data if payload.get("id") != graph_id]
        if len(new_data) == len(data):
            raise GraphNotFoundError(f"Graph '{graph_id}' not found")
        self._write(new_data)

    def _read(self) -> List[dict]:
        with self._lock:
            if not self._path.exists():
                return []
            return json.loads(self._path.read_text() or "[]")

    def _write(self, payload: List[dict]) -> None:
        with self._lock:
            self._path.write_text(json.dumps(payload, indent=2))


