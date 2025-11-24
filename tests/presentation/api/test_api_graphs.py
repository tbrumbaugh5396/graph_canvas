from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from graph_canvas.application.graph_service import GraphService
from graph_canvas.domain.entities import Graph, Node
from graph_canvas.presentation.api.app import create_api_app
from tests.support.mocks import MockGraphRepository


def make_app(graphs=None):
    repo = MockGraphRepository(graphs=graphs or {})

    def _get_service():
        from graph_canvas.application.graph_service import GraphService

        return GraphService(repo)

    app = create_api_app(_get_service())
    app.state.repo = repo
    return app, repo


def test_list_graphs_returns_seed():
    graph = Graph(id="one", name="One")
    graph.add_node(Node(id="n1", data={"text": "Node"}))
    app, _ = make_app({"one": graph})
    client = TestClient(app)

    response = client.get("/graphs")

    assert response.status_code == 200
    data = response.json()
    assert data[0]["id"] == "one"
    assert data[0]["nodes"][0]["text"] == "Node"


def test_create_graph_persists():
    app, repo = make_app()
    client = TestClient(app)

    payload = {
        "id": "g2",
        "name": "Created",
        "graph_type": "tree",
        "directed": False,
        "nodes": [],
        "edges": [],
        "metadata": {},
    }
    response = client.post("/graphs", json=payload)

    assert response.status_code == 201
    assert "g2" in repo.graphs
    assert response.json()["graph_type"] == "tree"
    assert response.json()["directed"] is False


def test_create_graph_rejects_invalid_type():
    app, _ = make_app()
    client = TestClient(app)

    payload = {"id": "g3", "name": "Bad", "graph_type": "invalid", "nodes": [], "edges": []}
    response = client.post("/graphs", json=payload)

    assert response.status_code == 422


def test_compat_graph_roundtrip():
    app, repo = make_app()
    client = TestClient(app)

    response = client.get("/graph")
    assert response.status_code == 200

    payload = response.json()
    payload["name"] = "Updated Workspace"
    client.post("/graph", json=payload)

    assert repo.graphs["workspace"].name == "Updated Workspace"


def test_compat_create_node():
    graph = Graph(id="workspace", name="Workspace")
    repo = MockGraphRepository(graphs={"workspace": graph})
    app = create_api_app(GraphService(repo))  # type: ignore[name-defined]
    client = TestClient(app)

    response = client.post("/nodes", json={"x": 1.0, "y": 2.0, "text": "hello"})

    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "hello"


def test_node_crud_endpoints():
    graph = Graph(id="g1", name="Graph")
    repo = MockGraphRepository(graphs={"g1": graph})
    app = create_api_app(GraphService(repo))  # type: ignore[name-defined]
    client = TestClient(app)

    create_res = client.post("/graphs/g1/nodes", json={"text": "Node A", "x": 10, "y": 20})
    assert create_res.status_code == 201
    node_id = create_res.json()["id"]

    patch_res = client.patch(f"/graphs/g1/nodes/{node_id}", json={"text": "Node B"})
    assert patch_res.status_code == 200
    assert patch_res.json()["text"] == "Node B"

    positions_res = client.patch(
        "/graphs/g1/nodes/positions",
        json={"positions": [{"id": node_id, "x": 50, "y": 60}]},
    )
    assert positions_res.status_code == 200
    assert positions_res.json()["updated"][0]["x"] == 50

    delete_res = client.delete(f"/graphs/g1/nodes/{node_id}")
    assert delete_res.status_code == 204


def test_edge_crud_endpoints():
    graph = Graph(id="g1", name="Graph")
    graph.add_node(Node(id="a", data={"x": 0, "y": 0}))
    graph.add_node(Node(id="b", data={"x": 10, "y": 10}))
    repo = MockGraphRepository(graphs={"g1": graph})
    app = create_api_app(GraphService(repo))  # type: ignore[name-defined]
    client = TestClient(app)

    create_res = client.post(
        "/graphs/g1/edges",
        json={"source_id": "a", "target_id": "b", "text": "edge"},
    )
    assert create_res.status_code == 201
    edge_id = create_res.json()["id"]

    patch_res = client.patch(f"/graphs/g1/edges/{edge_id}", json={"text": "updated"})
    assert patch_res.status_code == 200
    assert patch_res.json()["text"] == "updated"

    delete_res = client.delete(f"/graphs/g1/edges/{edge_id}")
    assert delete_res.status_code == 204


def test_update_graph_type_endpoint():
    graph = Graph(id="g1", name="Graph")
    repo = MockGraphRepository(graphs={"g1": graph})
    app = create_api_app(GraphService(repo))  # type: ignore[name-defined]
    client = TestClient(app)

    response = client.patch("/graphs/g1", json={"graph_type": "dag", "directed": False})

    assert response.status_code == 200
    assert response.json()["graph_type"] == "dag"
    assert response.json()["directed"] is False
    assert repo.graphs["g1"].graph_type == "dag"
    assert repo.graphs["g1"].directed is False


def test_replace_graph_snapshot_endpoint():
    graph = Graph(id="g1", name="Graph")
    graph.add_node(Node(id="a", data={"x": 0, "y": 0, "text": "A"}))
    repo = MockGraphRepository(graphs={"g1": graph})
    app = create_api_app(GraphService(repo))  # type: ignore[name-defined]
    client = TestClient(app)

    snapshot = graph.to_dict()
    snapshot["name"] = "Restored"
    snapshot["graph_type"] = "hypergraph"
    snapshot["directed"] = False

    response = client.put("/graphs/g1/snapshot", json=snapshot)

    assert response.status_code == 200
    assert repo.graphs["g1"].name == "Restored"
    assert repo.graphs["g1"].graph_type == "hypergraph"
    assert repo.graphs["g1"].directed is False

