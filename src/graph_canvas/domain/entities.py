"""
Domain entities for Graph Canvas.

They operate purely on dictionaries so that rich GUI-specific payloads
(positions, colors, hyperedge metadata, etc.) round-trip without loss.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Tuple
from uuid import uuid4


def _tuple_color(value: Iterable[int] | None, default: Tuple[int, int, int]) -> Tuple[int, int, int]:
    if value is None:
        return default
    data = list(value)
    if len(data) != 3:
        return default
    return tuple(int(v) for v in data)  # type: ignore[return-value]


GRAPH_TYPE_CHOICES: Tuple[str, ...] = (
    "list",
    "tree",
    "dag",
    "graph",
    "multigraph",
    "hypergraph",
    "ubergraph",
)


def normalize_graph_type(value: str | None) -> str:
    if not value:
        return "graph"
    normalized = value.strip().lower()
    if normalized not in GRAPH_TYPE_CHOICES:
        raise ValueError(
            f"graph_type '{value}' is invalid. Choose one of: {', '.join(GRAPH_TYPE_CHOICES)}"
        )
    return normalized


@dataclass
class Node:
    """Graph node that stores arbitrary attributes."""

    id: str
    data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "Node":
        payload = payload.copy()
        node_id = payload.pop("id")
        return cls(id=node_id, data=payload)

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, **self.data}

    def set_position(self, x: float, y: float, z: float | None = None) -> None:
        self.data["x"] = x
        self.data["y"] = y
        if z is not None:
            self.data["z"] = z

    @property
    def text(self) -> str:
        return str(self.data.get("text", ""))


@dataclass
class Edge:
    """Graph edge connecting nodes with arbitrary attributes."""

    id: str
    source_id: str
    target_id: str
    data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "Edge":
        payload = payload.copy()
        edge_id = payload.pop("id")
        source_id = payload.pop("source_id")
        target_id = payload.pop("target_id")
        return cls(id=edge_id, source_id=source_id, target_id=target_id, data=payload)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            **self.data,
        }


@dataclass
class Graph:
    """Aggregate root that groups nodes, edges, and rendering metadata."""

    id: str
    name: str
    graph_type: str = "graph"
    directed: bool = True
    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: Dict[str, Edge] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    background_color: Tuple[int, int, int] = (255, 255, 255)
    grid_visible: bool = True
    grid_size: int = 20
    grid_color: Tuple[int, int, int] = (240, 240, 240)
    grid_line_thickness: float = 1.0

    def __post_init__(self) -> None:
        self.graph_type = normalize_graph_type(self.graph_type)
        self.directed = bool(self.directed)

    def add_node(self, node: Node) -> None:
        self.nodes[node.id] = node

    def create_node(
        self,
        x: float = 0.0,
        y: float = 0.0,
        text: str = "",
        data: Dict[str, Any] | None = None,
    ) -> Node:
        payload: Dict[str, Any] = {
            "text": text,
            "x": x,
            "y": y,
            "z": 0.0,
            "metadata": {},
        }
        if data:
            payload.update(data)
        payload.setdefault("text", text or payload.get("label", ""))
        payload.setdefault("x", x)
        payload.setdefault("y", y)
        payload.setdefault("z", 0.0)
        payload.setdefault("metadata", {})

        node = Node(
            id=str(uuid4()),
            data=payload,
        )
        self.add_node(node)
        return node

    def add_edge(self, edge: Edge) -> None:
        self.edges[edge.id] = edge

    def create_edge(
        self,
        source_id: str,
        target_id: str,
        text: str = "",
        data: Dict[str, Any] | None = None,
    ) -> Edge:
        payload: Dict[str, Any] = {
            "text": text,
            "metadata": {},
            "source_ids": [source_id],
            "target_ids": [target_id],
        }
        if data:
            payload.update(data)
        payload.setdefault("source_ids", [source_id])
        payload.setdefault("target_ids", [target_id])
        payload.setdefault("metadata", {})

        edge = Edge(
            id=str(uuid4()),
            source_id=source_id,
            target_id=target_id,
            data=payload,
        )
        self.add_edge(edge)
        return edge

    def get_node(self, node_id: str) -> Node | None:
        return self.nodes.get(node_id)

    def get_edge(self, edge_id: str) -> Edge | None:
        return self.edges.get(edge_id)

    def remove_node(self, node_id: str) -> None:
        self.nodes.pop(node_id, None)
        self.edges = {
            edge_id: edge
            for edge_id, edge in self.edges.items()
            if node_id not in {edge.source_id, edge.target_id}
        }

    def remove_edge(self, edge_id: str) -> None:
        self.edges.pop(edge_id, None)

    def patch_node_positions(self, positions: List[Tuple[str, float, float]]) -> List[Dict[str, Any]]:
        updated = []
        for node_id, x, y in positions:
            node = self.nodes.get(node_id)
            if not node:
                continue
            node.set_position(x, y)
            updated.append(node.to_dict())
        return updated

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "graph_type": self.graph_type,
            "directed": self.directed,
            "metadata": self.metadata,
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [edge.to_dict() for edge in self.edges.values()],
            "background_color": list(self.background_color),
            "grid_visible": self.grid_visible,
            "grid_size": self.grid_size,
            "grid_color": list(self.grid_color),
            "grid_line_thickness": self.grid_line_thickness,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "Graph":
        graph = cls(
            id=payload["id"],
            name=payload.get("name", payload["id"]),
            graph_type=payload.get("graph_type", "graph"),
            directed=payload.get("directed", True),
            metadata=payload.get("metadata", {}),
            background_color=_tuple_color(payload.get("background_color"), (255, 255, 255)),
            grid_visible=payload.get("grid_visible", True),
            grid_size=payload.get("grid_size", 20),
            grid_color=_tuple_color(payload.get("grid_color"), (240, 240, 240)),
            grid_line_thickness=payload.get("grid_line_thickness", 1.0),
        )
        for node_data in payload.get("nodes", []):
            node = Node.from_dict(node_data)
            graph.add_node(node)
        for edge_data in payload.get("edges", []):
            edge = Edge.from_dict(edge_data)
            graph.add_edge(edge)
        return graph

