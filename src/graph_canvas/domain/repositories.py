"""Abstract repository contracts for the domain layer."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from graph_canvas.domain.entities import Graph


class GraphRepository(ABC):
    """Port describing how graphs are persisted."""

    @abstractmethod
    def list_graphs(self) -> Iterable[Graph]:
        ...

    @abstractmethod
    def get_graph(self, graph_id: str) -> Graph:
        ...

    @abstractmethod
    def save_graph(self, graph: Graph) -> Graph:
        ...

    @abstractmethod
    def delete_graph(self, graph_id: str) -> None:
        ...


