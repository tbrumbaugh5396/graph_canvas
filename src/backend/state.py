"""
Shared backend state for the graph and thread-safe mutation helpers.
"""

from __future__ import annotations

import threading
from typing import Dict, Iterable, List, Tuple

from graph_canvas.presentation.desktop.models.graph import Graph
from graph_canvas.presentation.desktop.models import node as m_node
from graph_canvas.presentation.desktop.models import edge as m_edge


_graph_lock = threading.Lock()
current_graph: Graph = Graph(name="Backend Graph")


def get_graph_dict() -> Dict:
    with _graph_lock:
        return current_graph.to_dict()


def set_graph_from_dict(payload: Dict) -> None:
    global current_graph
    with _graph_lock:
        current_graph = Graph.from_dict(payload)


def update_node_positions(positions: Iterable[Tuple[str, float, float]]) -> List[Dict]:
    """
    Update multiple node positions.
    positions: iterable of (node_id, x, y)
    Returns list of updated node dicts.
    """
    updated: List[Dict] = []
    with _graph_lock:
        for node_id, x, y in positions:
            node = current_graph.get_node(node_id)
            if node is None:
                continue
            node.set_2d_position(x, y)
            updated.append(node.to_dict())
        current_graph.modified = True
    return updated


def create_node(x: float, y: float, text: str = "") -> Dict:
    with _graph_lock:
        node = current_graph.create_node(x=x, y=y, text=text)
        return node.to_dict()


def create_edge(source_id: str, target_id: str, text: str = "") -> Dict:
    with _graph_lock:
        edge = current_graph.create_edge(source_id=source_id, target_id=target_id, text=text)
        return edge.to_dict()


def delete_node(node_id: str) -> bool:
    with _graph_lock:
        return current_graph.remove_node(node_id)


def delete_edge(edge_id: str) -> bool:
    with _graph_lock:
        return current_graph.remove_edge(edge_id)






