"""Minimal dependency wiring for the clean architecture layers."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from graph_canvas.application.graph_service import GraphService
from graph_canvas.domain.entities import Edge, Graph, Node
from graph_canvas.infrastructure.repositories.json_file import (
    JsonGraphRepository,
)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _seed_graph() -> Graph:
    graph = Graph(id="workspace", name="Workspace")
    graph.add_node(
        Node(
            id="alpha",
            data={"text": "Alpha Node", "x": 0.0, "y": 0.0, "metadata": {}},
        )
    )
    graph.add_node(
        Node(
            id="beta",
            data={"text": "Beta Node", "x": 150.0, "y": 80.0, "metadata": {}},
        )
    )
    graph.add_edge(
        Edge(
            id="alpha-beta",
            source_id="alpha",
            target_id="beta",
            data={"text": "Sample Edge", "metadata": {}},
        )
    )
    return graph


@lru_cache
def get_graph_service() -> GraphService:
    """Provide a shared GraphService instance backed by JSON persistence."""
    data_dir = _project_root() / "data"
    repository = JsonGraphRepository(data_dir / "graphs.json", seed=[_seed_graph()])
    return GraphService(repository)

