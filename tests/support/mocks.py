"""Simple mocks to support unit tests."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)



from dataclasses import dataclass, field
from typing import Dict, Iterable

from graph_canvas.domain.entities import Graph
from graph_canvas.domain.repositories import GraphRepository


@dataclass
class MockGraphRepository(GraphRepository):
    """GraphRepository double that records interactions."""

    graphs: Dict[str, Graph] = field(default_factory=dict)
    saved_graph_ids: list[str] = field(default_factory=list)
    deleted_graph_ids: list[str] = field(default_factory=list)

    def list_graphs(self) -> Iterable[Graph]:
        return list(self.graphs.values())

    def get_graph(self, graph_id: str) -> Graph:
        return self.graphs[graph_id]

    def save_graph(self, graph: Graph) -> Graph:
        self.graphs[graph.id] = graph
        self.saved_graph_ids.append(graph.id)
        return graph

    def delete_graph(self, graph_id: str) -> None:
        self.graphs.pop(graph_id, None)
        self.deleted_graph_ids.append(graph_id)


