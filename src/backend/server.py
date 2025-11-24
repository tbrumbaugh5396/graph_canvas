"""
FastAPI backend exposing the graph state and basic mutation endpoints.
Run with: uvicorn backend.server:app --reload
"""

from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from . import state


app = FastAPI(title="Graph Canvas Backend", version="0.1.0")


class GraphPayload(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    metadata: Optional[Dict] = None
    nodes: List[Dict]
    edges: List[Dict]
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


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/graph")
def get_graph() -> Dict:
    return state.get_graph_dict()


@app.post("/graph")
def set_graph(payload: GraphPayload) -> Dict:
    state.set_graph_from_dict(payload.dict())
    return {"ok": True}


@app.patch("/nodes/positions")
def patch_node_positions(positions: List[NodePosition]) -> Dict:
    updated = state.update_node_positions([(p.id, p.x, p.y) for p in positions])
    return {"updated": updated}


@app.post("/nodes")
def post_node(new_node: NewNode) -> Dict:
    return state.create_node(new_node.x, new_node.y, new_node.text or "")


@app.delete("/nodes/{node_id}")
def delete_node(node_id: str) -> Dict:
    ok = state.delete_node(node_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Node not found")
    return {"ok": True}


@app.post("/edges")
def post_edge(new_edge: NewEdge) -> Dict:
    try:
        return state.create_edge(new_edge.source_id, new_edge.target_id, new_edge.text or "")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/edges/{edge_id}")
def delete_edge(edge_id: str) -> Dict:
    ok = state.delete_edge(edge_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Edge not found")
    return {"ok": True}


if __name__ == "__main__":
    # Optional local run helper
    import uvicorn
    uvicorn.run("backend.server:app", host="127.0.0.1", port=8000, reload=True)






