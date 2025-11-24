"""Pydantic schemas for the API layer."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class NodeSchema(BaseModel):
    id: str
    text: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class EdgeSchema(BaseModel):
    id: str
    source_id: str
    target_id: str
    text: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class GraphCreateSchema(BaseModel):
    id: str
    name: str
    graph_type: Optional[str] = None
    directed: Optional[bool] = None
    nodes: List[NodeSchema] = Field(default_factory=list)
    edges: List[EdgeSchema] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    background_color: Optional[List[int]] = None
    grid_visible: Optional[bool] = None
    grid_size: Optional[int] = None
    grid_color: Optional[List[int]] = None
    grid_line_thickness: Optional[float] = None


class GraphUpdateSchema(BaseModel):
    name: Optional[str] = None
    graph_type: Optional[str] = None
    directed: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None
    background_color: Optional[List[int]] = None
    grid_visible: Optional[bool] = None
    grid_size: Optional[int] = None
    grid_color: Optional[List[int]] = None
    grid_line_thickness: Optional[float] = None


class GraphResponseSchema(BaseModel):
    id: str
    name: str
    graph_type: Optional[str] = None
    directed: Optional[bool] = None
    nodes: List[NodeSchema]
    edges: List[EdgeSchema]
    metadata: Dict[str, Any]
    background_color: Optional[List[int]] = None
    grid_visible: Optional[bool] = None
    grid_size: Optional[int] = None
    grid_color: Optional[List[int]] = None
    grid_line_thickness: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class NodeCreateSchema(BaseModel):
    text: Optional[str] = None
    x: float = 0.0
    y: float = 0.0
    z: Optional[float] = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class NodeUpdateSchema(BaseModel):
    text: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(extra="allow")


class EdgeCreateSchema(BaseModel):
    source_id: str
    target_id: str
    text: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class EdgeUpdateSchema(BaseModel):
    source_id: Optional[str] = None
    target_id: Optional[str] = None
    text: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(extra="allow")

