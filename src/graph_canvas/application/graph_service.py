"""Use cases that orchestrate repository operations."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Sequence, Tuple

from graph_canvas.application.dto import (
    EdgeDTO,
    GraphCreateDTO,
    GraphUpdateDTO,
    NodeDTO,
)
from graph_canvas.domain.entities import Edge, Graph, Node, normalize_graph_type
from graph_canvas.domain.exceptions import (
    EdgeNotFoundError,
    GraphAlreadyExistsError,
    GraphNotFoundError,
    NodeNotFoundError,
)
from graph_canvas.domain.repositories import GraphRepository


class GraphService:
    """Coordinates operations on the Graph aggregate."""

    def __init__(self, repository: GraphRepository):
        self._repository = repository

    def list_graphs(self) -> Iterable[Graph]:
        return self._repository.list_graphs()

    def get_graph(self, graph_id: str) -> Graph:
        try:
            return self._repository.get_graph(graph_id)
        except KeyError as exc:  # pragma: no cover - defensive for custom repos
            raise GraphNotFoundError(str(exc)) from exc

    def ensure_graph(self, graph_id: str, name: str = "Workspace") -> Graph:
        try:
            return self.get_graph(graph_id)
        except GraphNotFoundError:
            graph = Graph(id=graph_id, name=name)
            return self._repository.save_graph(graph)

    def create_graph(self, data: GraphCreateDTO) -> Graph:
        existing = next(
            (graph for graph in self._repository.list_graphs() if graph.id == data.id),
            None,
        )
        if existing:
            raise GraphAlreadyExistsError(f"Graph '{data.id}' already exists")

        graph = Graph(
            id=data.id,
            name=data.name,
            graph_type=normalize_graph_type(data.graph_type),
            directed=data.directed if data.directed is not None else True,
            metadata=data.metadata or {},
        )
        if data.background_color:
            graph.background_color = tuple(data.background_color)  # type: ignore[assignment]
        if data.grid_visible is not None:
            graph.grid_visible = data.grid_visible
        if data.grid_size is not None:
            graph.grid_size = data.grid_size
        if data.grid_color:
            graph.grid_color = tuple(data.grid_color)  # type: ignore[assignment]
        if data.grid_line_thickness is not None:
            graph.grid_line_thickness = data.grid_line_thickness

        for node in data.nodes:
            graph.add_node(self._node_from_dto(node))
        for edge in data.edges:
            graph.add_edge(self._edge_from_dto(edge))

        return self._repository.save_graph(graph)

    def replace_graph(self, payload: Dict[str, Any]) -> Graph:
        graph = Graph.from_dict(payload)
        return self._repository.save_graph(graph)

    def update_graph(self, graph_id: str, data: GraphUpdateDTO) -> Graph:
        graph = self.get_graph(graph_id)

        if data.name is not None:
            graph.name = data.name
        if data.metadata is not None:
            graph.metadata = data.metadata
        if data.graph_type is not None:
            graph.graph_type = normalize_graph_type(data.graph_type)
        if data.directed is not None:
            graph.directed = bool(data.directed)
        if data.background_color:
            graph.background_color = tuple(data.background_color)  # type: ignore[assignment]
        if data.grid_visible is not None:
            graph.grid_visible = data.grid_visible
        if data.grid_size is not None:
            graph.grid_size = data.grid_size
        if data.grid_color:
            graph.grid_color = tuple(data.grid_color)  # type: ignore[assignment]
        if data.grid_line_thickness is not None:
            graph.grid_line_thickness = data.grid_line_thickness

        return self._repository.save_graph(graph)

    def delete_graph(self, graph_id: str) -> None:
        self._repository.delete_graph(graph_id)

    def create_node(
        self,
        graph_id: str,
        x: float = 0.0,
        y: float = 0.0,
        text: str = "",
        data: Dict[str, Any] | None = None,
    ) -> Node:
        graph = self.get_graph(graph_id)
        node = graph.create_node(x=x, y=y, text=text, data=data)
        self._repository.save_graph(graph)
        return node

    def update_node(self, graph_id: str, node_id: str, payload: Dict[str, Any]) -> Node:
        graph = self.get_graph(graph_id)
        node = graph.get_node(node_id)
        if not node:
            raise NodeNotFoundError(f"Node '{node_id}' not found in graph '{graph_id}'")

        updates = payload.copy()
        updates.pop("id", None)

        if {"x", "y", "z"} & updates.keys():
            node.set_position(
                updates.pop("x", node.data.get("x", 0.0)),
                updates.pop("y", node.data.get("y", 0.0)),
                updates.pop("z", node.data.get("z", node.data.get("z", 0.0))),
            )

        metadata = updates.pop("metadata", None)
        if metadata is not None:
            node.data["metadata"] = metadata
        node.data.update(updates)

        self._repository.save_graph(graph)
        return node

    def create_edge(
        self,
        graph_id: str,
        source_id: str,
        target_id: str,
        text: str = "",
        data: Dict[str, Any] | None = None,
    ) -> Edge:
        graph = self.get_graph(graph_id)
        edge = graph.create_edge(source_id=source_id, target_id=target_id, text=text, data=data)
        self._repository.save_graph(graph)
        return edge

    def update_edge(self, graph_id: str, edge_id: str, payload: Dict[str, Any]) -> Edge:
        graph = self.get_graph(graph_id)
        edge = graph.get_edge(edge_id)
        if not edge:
            raise EdgeNotFoundError(f"Edge '{edge_id}' not found in graph '{graph_id}'")

        updates = payload.copy()
        updates.pop("id", None)

        source_ids = updates.pop("source_ids", None)
        target_ids = updates.pop("target_ids", None)

        source_id = updates.pop("source_id", None)
        if source_id:
            edge.source_id = source_id
            edge.data["source_ids"] = source_ids or [source_id]
        elif source_ids:
            edge.data["source_ids"] = source_ids
            edge.source_id = source_ids[0]

        target_id = updates.pop("target_id", None)
        if target_id:
            edge.target_id = target_id
            edge.data["target_ids"] = target_ids or [target_id]
        elif target_ids:
            edge.data["target_ids"] = target_ids
            edge.target_id = target_ids[0]

        metadata = updates.pop("metadata", None)
        if metadata is not None:
            edge.data["metadata"] = metadata
        edge.data.update(updates)

        self._repository.save_graph(graph)
        return edge

    def patch_node_positions(
        self, graph_id: str, positions: Sequence[Tuple[str, float, float]]
    ) -> List[Dict[str, Any]]:
        graph = self.ensure_graph(graph_id)
        updated = graph.patch_node_positions(list(positions))
        self._repository.save_graph(graph)
        return updated

    def delete_node(self, graph_id: str, node_id: str) -> None:
        graph = self.get_graph(graph_id)
        if not graph.get_node(node_id):
            raise NodeNotFoundError(f"Node '{node_id}' not found in graph '{graph_id}'")
        graph.remove_node(node_id)
        self._repository.save_graph(graph)

    def delete_edge(self, graph_id: str, edge_id: str) -> None:
        graph = self.get_graph(graph_id)
        if not graph.get_edge(edge_id):
            raise EdgeNotFoundError(f"Edge '{edge_id}' not found in graph '{graph_id}'")
        graph.remove_edge(edge_id)
        self._repository.save_graph(graph)

    @staticmethod
    def _node_from_dto(dto: NodeDTO) -> Node:
        return Node(id=dto.id, data=dto.payload)

    @staticmethod
    def _edge_from_dto(dto: EdgeDTO) -> Edge:
        return Edge(
            id=dto.id,
            source_id=dto.source_id,
            target_id=dto.target_id,
            data=dto.payload,
        )

