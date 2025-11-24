"""FastAPI application exposing graph use cases."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import Body, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ValidationError

from graph_canvas.application.dto import (
    EdgeDTO,
    GraphCreateDTO,
    GraphUpdateDTO,
    NodeDTO,
)
from graph_canvas.application.graph_service import GraphService
from graph_canvas.container import get_graph_service
from graph_canvas.domain.exceptions import (
    EdgeNotFoundError,
    GraphAlreadyExistsError,
    GraphNotFoundError,
    NodeNotFoundError,
)
from graph_canvas.presentation.api.schemas import (
    EdgeCreateSchema,
    EdgeSchema,
    EdgeUpdateSchema,
    GraphCreateSchema,
    GraphResponseSchema,
    GraphUpdateSchema,
    NodeCreateSchema,
    NodeSchema,
    NodeUpdateSchema,
)

DEFAULT_GRAPH_ID = "workspace"
DEFAULT_GRAPH_NAME = "Workspace"


class GraphPayload(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    graph_type: Optional[str] = None
    directed: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)
    background_color: Optional[List[int]] = None
    grid_visible: Optional[bool] = None
    grid_size: Optional[int] = None
    grid_color: Optional[List[int]] = None


class NodePosition(BaseModel):
    id: str
    x: float
    y: float


class NewNode(BaseModel):
    x: float
    y: float
    text: Optional[str] = ""


class NewEdge(BaseModel):
    source_id: str
    target_id: str
    text: Optional[str] = ""


def _schema_payload(schema: BaseModel, exclude: Optional[set[str]] = None) -> Dict[str, Any]:
    data = schema.model_dump(exclude_none=True)
    for field in exclude or set():
        data.pop(field, None)
    return data


def _parse_positions(payload: Any) -> List[NodePosition]:
    try:
        if isinstance(payload, list):
            items = payload
        elif isinstance(payload, dict) and "positions" in payload:
            items = payload["positions"]
        else:
            raise ValueError("Expected a list of positions or an object with 'positions'")
        return [NodePosition.model_validate(item) for item in items]
    except (ValidationError, ValueError) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


def create_api_app(graph_service: Optional[GraphService] = None) -> FastAPI:
    service = graph_service or get_graph_service()
    app = FastAPI(title="Graph Canvas API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/healthz", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/graphs", response_model=list[GraphResponseSchema], tags=["graphs"])
    def list_graphs():
        graphs = service.list_graphs()
        return [graph.to_dict() for graph in graphs]

    @app.get(
        "/graphs/{graph_id}",
        response_model=GraphResponseSchema,
        tags=["graphs"],
    )
    def get_graph(graph_id: str):
        try:
            return service.get_graph(graph_id).to_dict()
        except GraphNotFoundError as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

    @app.post(
        "/graphs",
        response_model=GraphResponseSchema,
        status_code=status.HTTP_201_CREATED,
        tags=["graphs"],
    )
    def create_graph(payload: GraphCreateSchema):
        try:
            dto = GraphCreateDTO(
                id=payload.id,
                name=payload.name,
                graph_type=payload.graph_type,
                directed=payload.directed,
                metadata=payload.metadata,
                background_color=payload.background_color,
                grid_visible=payload.grid_visible,
                grid_size=payload.grid_size,
                grid_color=payload.grid_color,
                grid_line_thickness=payload.grid_line_thickness,
                nodes=[
                    NodeDTO(id=node.id, payload=_schema_payload(node, {"id"}))
                    for node in payload.nodes
                ],
                edges=[
                    EdgeDTO(
                        id=edge.id,
                        source_id=edge.source_id,
                        target_id=edge.target_id,
                        payload=_schema_payload(edge, {"id", "source_id", "target_id"}),
                    )
                    for edge in payload.edges
                ],
            )
            graph = service.create_graph(dto)
            return graph.to_dict()
        except GraphAlreadyExistsError as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    @app.patch(
        "/graphs/{graph_id}",
        response_model=GraphResponseSchema,
        tags=["graphs"],
    )
    def update_graph(graph_id: str, payload: GraphUpdateSchema):
        try:
            graph = service.update_graph(
                graph_id,
                GraphUpdateDTO(
                    name=payload.name,
                    graph_type=payload.graph_type,
                    directed=payload.directed,
                    metadata=payload.metadata,
                    background_color=payload.background_color,
                    grid_visible=payload.grid_visible,
                    grid_size=payload.grid_size,
                    grid_color=payload.grid_color,
                    grid_line_thickness=payload.grid_line_thickness,
                ),
            )
            return graph.to_dict()
        except GraphNotFoundError as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    @app.put(
        "/graphs/{graph_id}/snapshot",
        response_model=GraphResponseSchema,
        tags=["graphs"],
    )
    def replace_graph_snapshot(graph_id: str, payload: GraphResponseSchema):
        data = payload.model_dump()
        data["id"] = graph_id
        try:
            graph = service.replace_graph(data)
            return graph.to_dict()
        except GraphNotFoundError as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

    @app.delete(
        "/graphs/{graph_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        tags=["graphs"],
    )
    def delete_graph(graph_id: str):
        try:
            service.delete_graph(graph_id)
        except GraphNotFoundError as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

    # Node CRUD
    @app.post(
        "/graphs/{graph_id}/nodes",
        response_model=NodeSchema,
        status_code=status.HTTP_201_CREATED,
        tags=["nodes"],
    )
    def create_node(graph_id: str, payload: NodeCreateSchema):
        body = _schema_payload(payload)
        node = service.create_node(
            graph_id,
            x=body.pop("x", 0.0),
            y=body.pop("y", 0.0),
            text=body.pop("text", "") or "",
            data=body,
        )
        return node.to_dict()

    @app.patch(
        "/graphs/{graph_id}/nodes/positions",
        tags=["nodes"],
    )
    async def update_node_positions(graph_id: str, request: Request):
        try:
            payload = await request.json()
            parsed = _parse_positions(payload)
            updated = service.patch_node_positions(
                graph_id, [(p.id, p.x, p.y) for p in parsed]
            )
            return {"updated": updated}
        except GraphNotFoundError as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

    @app.patch(
        "/graphs/{graph_id}/nodes/{node_id}",
        response_model=NodeSchema,
        tags=["nodes"],
    )
    def update_node(graph_id: str, node_id: str, payload: NodeUpdateSchema):
        try:
            node = service.update_node(graph_id, node_id, _schema_payload(payload))
            return node.to_dict()
        except (GraphNotFoundError, NodeNotFoundError) as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

    @app.delete(
        "/graphs/{graph_id}/nodes/{node_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        tags=["nodes"],
    )
    def delete_node(graph_id: str, node_id: str):
        try:
            service.delete_node(graph_id, node_id)
        except (GraphNotFoundError, NodeNotFoundError) as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

    # Edge CRUD
    @app.post(
        "/graphs/{graph_id}/edges",
        response_model=EdgeSchema,
        status_code=status.HTTP_201_CREATED,
        tags=["edges"],
    )
    def create_edge(graph_id: str, payload: EdgeCreateSchema):
        body = _schema_payload(payload)
        try:
            edge = service.create_edge(
                graph_id,
                source_id=body.pop("source_id"),
                target_id=body.pop("target_id"),
                text=body.pop("text", "") or "",
                data=body,
            )
            return edge.to_dict()
        except GraphNotFoundError as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

    @app.patch(
        "/graphs/{graph_id}/edges/{edge_id}",
        response_model=EdgeSchema,
        tags=["edges"],
    )
    def update_edge(graph_id: str, edge_id: str, payload: EdgeUpdateSchema):
        try:
            edge = service.update_edge(graph_id, edge_id, _schema_payload(payload))
            return edge.to_dict()
        except (GraphNotFoundError, EdgeNotFoundError) as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

    @app.delete(
        "/graphs/{graph_id}/edges/{edge_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        tags=["edges"],
    )
    def delete_edge(graph_id: str, edge_id: str):
        try:
            service.delete_edge(graph_id, edge_id)
        except (GraphNotFoundError, EdgeNotFoundError) as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

    # Compatibility endpoints for the wx backend client
    @app.get("/graph", tags=["compat"])
    def compat_get_graph():
        return service.ensure_graph(DEFAULT_GRAPH_ID, DEFAULT_GRAPH_NAME).to_dict()

    @app.post("/graph", tags=["compat"])
    def compat_set_graph(payload: GraphPayload):
        graph_dict = payload.model_dump(exclude_none=True)
        graph_dict.setdefault("id", DEFAULT_GRAPH_ID)
        graph_dict.setdefault("name", graph_dict.get("id", DEFAULT_GRAPH_NAME))
        graph_dict.setdefault("graph_type", graph_dict.get("graph_type", "graph"))
        graph_dict.setdefault("directed", graph_dict.get("directed", True))
        try:
            service.replace_graph(graph_dict)
        except ValueError as exc:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
        return {"ok": True}

    @app.patch("/nodes/positions", tags=["compat"])
    async def compat_patch_positions(request: Request):
        payload = await request.json()
        parsed = _parse_positions(payload)
        updated = service.patch_node_positions(
            DEFAULT_GRAPH_ID, [(p.id, p.x, p.y) for p in parsed]
        )
        return {"updated": updated}

    @app.post("/nodes", tags=["compat"])
    def compat_create_node(payload: NewNode):
        node = service.create_node(
            DEFAULT_GRAPH_ID, x=payload.x, y=payload.y, text=payload.text or ""
        )
        return node.to_dict()

    @app.delete("/nodes/{node_id}", tags=["compat"])
    def compat_delete_node(node_id: str):
        try:
            service.delete_node(DEFAULT_GRAPH_ID, node_id)
        except (GraphNotFoundError, NodeNotFoundError) as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
        return {"ok": True}

    @app.post("/edges", tags=["compat"])
    def compat_create_edge(payload: NewEdge):
        try:
            edge = service.create_edge(
                DEFAULT_GRAPH_ID,
                source_id=payload.source_id,
                target_id=payload.target_id,
                text=payload.text or "",
            )
            return edge.to_dict()
        except GraphNotFoundError as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

    @app.delete("/edges/{edge_id}", tags=["compat"])
    def compat_delete_edge(edge_id: str):
        try:
            service.delete_edge(DEFAULT_GRAPH_ID, edge_id)
        except (GraphNotFoundError, EdgeNotFoundError) as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
        return {"ok": True}

    return app

