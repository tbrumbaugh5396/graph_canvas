"""Application layer DTOs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class NodeDTO:
    id: str
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EdgeDTO:
    id: str
    source_id: str
    target_id: str
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphCreateDTO:
    id: str
    name: str
    graph_type: Optional[str] = None
    directed: Optional[bool] = None
    nodes: List[NodeDTO] = field(default_factory=list)
    edges: List[EdgeDTO] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    background_color: Optional[List[int]] = None
    grid_visible: Optional[bool] = None
    grid_size: Optional[int] = None
    grid_color: Optional[List[int]] = None
    grid_line_thickness: Optional[float] = None


@dataclass
class GraphUpdateDTO:
    name: Optional[str] = None
    graph_type: Optional[str] = None
    directed: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None
    background_color: Optional[List[int]] = None
    grid_visible: Optional[bool] = None
    grid_size: Optional[int] = None
    grid_color: Optional[List[int]] = None
    grid_line_thickness: Optional[float] = None

