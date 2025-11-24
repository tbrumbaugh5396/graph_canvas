"""Simple in-memory repository implementation."""

from __future__ import annotations

from typing import Dict, Iterable, Optional

from graph_canvas.domain.entities import Graph
from graph_canvas.domain.exceptions import GraphNotFoundError
from graph_canvas.domain.repositories import GraphRepository


class InMemoryGraphRepository(GraphRepository):
    """Stores graphs in an in-memory dictionary."""

    def __init__(self, seed: Optional[Iterable[Graph]] = None):
        self._store: Dict[str, Graph] = {}
        if seed:
            for graph in seed:
                self._store[graph.id] = graph

    def list_graphs(self) -> Iterable[Graph]:
        return list(self._store.values())

    def get_graph(self, graph_id: str) -> Graph:
        try:
            return self._store[graph_id]
        except KeyError as exc:
            raise GraphNotFoundError(f"Graph '{graph_id}' not found") from exc

    def save_graph(self, graph: Graph) -> Graph:
        self._store[graph.id] = graph
        return graph

    def delete_graph(self, graph_id: str) -> None:
        if graph_id not in self._store:
            raise GraphNotFoundError(f"Graph '{graph_id}' not found")
        del self._store[graph_id]

