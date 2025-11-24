const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";
async function handle(response) {
    if (!response.ok) {
        const message = await response.text();
        throw new Error(message || response.statusText);
    }
    return response.json();
}
export async function fetchGraphs() {
    const res = await fetch(`${API_URL}/graphs`);
    return handle(res);
}
export async function createGraph(graph) {
    const res = await fetch(`${API_URL}/graphs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(graph),
    });
    return handle(res);
}
export async function deleteGraph(graphId) {
    const res = await fetch(`${API_URL}/graphs/${graphId}`, {
        method: "DELETE",
    });
    if (!res.ok) {
        const message = await res.text();
        throw new Error(message || res.statusText);
    }
}
export async function createNode(graphId, input) {
    let res = await fetch(`${API_URL}/graphs/${graphId}/nodes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input),
    });
    if (res.status === 404) {
        res = await fetch(`${API_URL}/nodes`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                x: input.x ?? 0,
                y: input.y ?? 0,
                text: input.text ?? "",
            }),
        });
    }
    return handle(res);
}
export async function updateNode(graphId, nodeId, input) {
    const res = await fetch(`${API_URL}/graphs/${graphId}/nodes/${nodeId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input),
    });
    return handle(res);
}
export async function deleteNode(graphId, nodeId) {
    const res = await fetch(`${API_URL}/graphs/${graphId}/nodes/${nodeId}`, {
        method: "DELETE",
    });
    if (!res.ok) {
        const message = await res.text();
        throw new Error(message || res.statusText);
    }
}
export async function updateNodePositions(graphId, positions) {
    let res = await fetch(`${API_URL}/graphs/${graphId}/nodes/positions`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ positions }),
    });
    if (res.status === 404) {
        res = await fetch(`${API_URL}/nodes/positions`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(positions.map((position) => ({
                id: position.id,
                x: position.x,
                y: position.y,
            }))),
        });
    }
    if (!res.ok) {
        const message = await res.text();
        throw new Error(message || res.statusText);
    }
}
export async function createEdge(graphId, input) {
    const res = await fetch(`${API_URL}/graphs/${graphId}/edges`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input),
    });
    return handle(res);
}
export async function updateEdge(graphId, edgeId, input) {
    const res = await fetch(`${API_URL}/graphs/${graphId}/edges/${edgeId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input),
    });
    return handle(res);
}
export async function deleteEdge(graphId, edgeId) {
    const res = await fetch(`${API_URL}/graphs/${graphId}/edges/${edgeId}`, {
        method: "DELETE",
    });
    if (!res.ok) {
        const message = await res.text();
        throw new Error(message || res.statusText);
    }
}
export async function updateGraphSettings(graphId, payload) {
    const res = await fetch(`${API_URL}/graphs/${graphId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    return handle(res);
}
export async function replaceGraph(graphId, snapshot) {
    const res = await fetch(`${API_URL}/graphs/${graphId}/snapshot`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(snapshot),
    });
    return handle(res);
}
