from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from graph_canvas.application.dto import GraphCreateDTO, GraphUpdateDTO, NodeDTO
from graph_canvas.application.graph_service import GraphService
from graph_canvas.domain.entities import Edge, Graph, Node
from graph_canvas.domain.exceptions import (
    EdgeNotFoundError,
    GraphAlreadyExistsError,
    NodeNotFoundError,
)
from tests.support.mocks import MockGraphRepository


def test_create_graph_persists_data():
    repo = MockGraphRepository()
    service = GraphService(repo)

    service.create_graph(
        GraphCreateDTO(
            id="g1",
            name="Sample",
            nodes=[NodeDTO(id="n1", payload={"text": "Node 1"})],
        )
    )

    assert "g1" in repo.graphs
    assert repo.graphs["g1"].name == "Sample"
    assert "n1" in repo.graphs["g1"].nodes


def test_create_graph_with_type():
    repo = MockGraphRepository()
    service = GraphService(repo)

    created = service.create_graph(GraphCreateDTO(id="g1", name="Sample", graph_type="tree"))

    assert created.graph_type == "tree"
    assert repo.graphs["g1"].graph_type == "tree"


def test_create_graph_invalid_type_raises():
    repo = MockGraphRepository()
    service = GraphService(repo)

    with pytest.raises(ValueError):
        service.create_graph(GraphCreateDTO(id="g1", name="Sample", graph_type="invalid"))


def test_create_graph_with_directed_flag():
    repo = MockGraphRepository()
    service = GraphService(repo)

    created = service.create_graph(GraphCreateDTO(id="g1", name="Sample", directed=False))

    assert created.directed is False
    assert repo.graphs["g1"].directed is False


def test_duplicate_graph_raises():
    repo = MockGraphRepository(graphs={"g1": Graph(id="g1", name="Existing")})
    service = GraphService(repo)

    with pytest.raises(GraphAlreadyExistsError):
        service.create_graph(GraphCreateDTO(id="g1", name="Sample"))


def test_update_graph_changes_title():
    repo = MockGraphRepository(graphs={"g1": Graph(id="g1", name="Before")})
    service = GraphService(repo)

    updated = service.update_graph("g1", GraphUpdateDTO(name="After"))

    assert updated.name == "After"
    assert repo.graphs["g1"].name == "After"


def test_update_graph_changes_type():
    repo = MockGraphRepository(graphs={"g1": Graph(id="g1", name="Before")})
    service = GraphService(repo)

    updated = service.update_graph("g1", GraphUpdateDTO(graph_type="dag"))

    assert updated.graph_type == "dag"
    assert repo.graphs["g1"].graph_type == "dag"


def test_update_graph_changes_directed():
    repo = MockGraphRepository(graphs={"g1": Graph(id="g1", name="Before")})
    service = GraphService(repo)

    updated = service.update_graph("g1", GraphUpdateDTO(directed=False))

    assert updated.directed is False
    assert repo.graphs["g1"].directed is False


def test_replace_graph_snapshot():
    original = Graph(id="g1", name="Before")
    repo = MockGraphRepository(graphs={"g1": original})
    service = GraphService(repo)

    snapshot = Graph(id="g1", name="After", graph_type="hypergraph", directed=False).to_dict()

    restored = service.replace_graph(snapshot)

    assert restored.name == "After"
    assert repo.graphs["g1"].graph_type == "hypergraph"
    assert repo.graphs["g1"].directed is False


def test_create_node_uses_repository():
    graph = Graph(id="g1", name="Graph")
    graph.add_node(Node(id="existing", data={"text": "Existing"}))
    repo = MockGraphRepository(graphs={"g1": graph})
    service = GraphService(repo)

    node = service.create_node("g1", 10.0, 11.0, text="New Node")

    assert node.id in repo.graphs["g1"].nodes
    assert repo.saved_graph_ids[-1] == "g1"


def test_patch_node_positions_updates_coordinates():
    node = Node(id="n1", data={"x": 0.0, "y": 0.0})
    graph = Graph(id="g1", name="Graph", nodes={"n1": node})
    repo = MockGraphRepository(graphs={"g1": graph})
    service = GraphService(repo)

    updated = service.patch_node_positions("g1", [("n1", 5.0, 6.0)])

    assert updated[0]["x"] == 5.0
    assert repo.graphs["g1"].nodes["n1"].data["x"] == 5.0


def test_update_node_overwrites_metadata():
    node = Node(id="n1", data={"text": "Old", "metadata": {"color": "red"}})
    graph = Graph(id="g1", name="Graph", nodes={"n1": node})
    repo = MockGraphRepository(graphs={"g1": graph})
    service = GraphService(repo)

    updated = service.update_node("g1", "n1", {"text": "New", "metadata": {"color": "blue"}})

    assert updated.data["text"] == "New"
    assert updated.data["metadata"]["color"] == "blue"


def test_update_edge_changes_source_target():
    edge = Edge(id="e1", source_id="a", target_id="b", data={"text": "Old"})
    graph = Graph(id="g1", name="Graph", edges={"e1": edge})
    repo = MockGraphRepository(graphs={"g1": graph})
    service = GraphService(repo)

    updated = service.update_edge("g1", "e1", {"source_id": "x", "target_id": "y", "text": "New"})

    assert updated.source_id == "x"
    assert updated.target_id == "y"
    assert updated.data["text"] == "New"


def test_delete_node_missing_raises():
    graph = Graph(id="g1", name="Graph")
    repo = MockGraphRepository(graphs={"g1": graph})
    service = GraphService(repo)

    with pytest.raises(NodeNotFoundError):
        service.delete_node("g1", "unknown")


def test_delete_edge_missing_raises():
    graph = Graph(id="g1", name="Graph")
    repo = MockGraphRepository(graphs={"g1": graph})
    service = GraphService(repo)

    with pytest.raises(EdgeNotFoundError):
        service.delete_edge("g1", "unknown")


def test_update_graph_grid_settings():
    repo = MockGraphRepository(graphs={"g1": Graph(id="g1", name="Graph")})
    service = GraphService(repo)

    service.update_graph(
        "g1",
        GraphUpdateDTO(
            grid_visible=False,
            grid_size=80,
            grid_color=[10, 20, 30],
            background_color=[255, 240, 220],
            grid_line_thickness=2.5,
        ),
    )

    graph = repo.graphs["g1"]
    assert graph.grid_visible is False
    assert graph.grid_size == 80
    assert graph.grid_color == (10, 20, 30)
    assert graph.background_color == (255, 240, 220)
    assert graph.grid_line_thickness == 2.5

