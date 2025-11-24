import type {
  EdgeDTO,
  EdgeInput,
  GraphDTO,
  GraphSettingsInput,
  NodeDTO,
  NodeInput,
} from "./types";

const API_URL =
    import.meta.env.VITE_API_URL ??
    `${window.location.protocol}//${window.location.hostname}:8000`;

async function handle<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || response.statusText);
  }
  return response.json() as Promise<T>;
}

export async function fetchGraphs(): Promise<GraphDTO[]> {
  const res = await fetch(`${API_URL}/graphs`);
  return handle(res);
}

export async function createGraph(graph: GraphDTO): Promise<GraphDTO> {
  const res = await fetch(`${API_URL}/graphs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(graph),
  });
  return handle(res);
}

export async function deleteGraph(graphId: string): Promise<void> {
  const res = await fetch(`${API_URL}/graphs/${graphId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const message = await res.text();
    throw new Error(message || res.statusText);
  }
}

export async function createNode(
  graphId: string,
  input: NodeInput,
): Promise<NodeDTO> {
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

export async function updateNode(
  graphId: string,
  nodeId: string,
  input: NodeInput,
): Promise<NodeDTO> {
  const res = await fetch(`${API_URL}/graphs/${graphId}/nodes/${nodeId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  return handle(res);
}

export async function deleteNode(graphId: string, nodeId: string): Promise<void> {
  const res = await fetch(`${API_URL}/graphs/${graphId}/nodes/${nodeId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const message = await res.text();
    throw new Error(message || res.statusText);
  }
}

export async function updateNodePositions(
  graphId: string,
  positions: Array<{ id: string; x: number; y: number }>,
): Promise<void> {
  let res = await fetch(`${API_URL}/graphs/${graphId}/nodes/positions`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ positions }),
  });
  if (res.status === 404) {
    res = await fetch(`${API_URL}/nodes/positions`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(
        positions.map((position) => ({
          id: position.id,
          x: position.x,
          y: position.y,
        })),
      ),
    });
  }
  if (!res.ok) {
    const message = await res.text();
    throw new Error(message || res.statusText);
  }
}

export async function createEdge(
  graphId: string,
  input: EdgeInput & { source_id: string; target_id: string },
): Promise<EdgeDTO> {
  const res = await fetch(`${API_URL}/graphs/${graphId}/edges`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  return handle(res);
}

export async function updateEdge(
  graphId: string,
  edgeId: string,
  input: EdgeInput & { source_id?: string; target_id?: string },
): Promise<EdgeDTO> {
  const res = await fetch(`${API_URL}/graphs/${graphId}/edges/${edgeId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  return handle(res);
}

export async function deleteEdge(graphId: string, edgeId: string): Promise<void> {
  const res = await fetch(`${API_URL}/graphs/${graphId}/edges/${edgeId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const message = await res.text();
    throw new Error(message || res.statusText);
  }
}

export async function updateGraphSettings(
  graphId: string,
  payload: GraphSettingsInput,
): Promise<GraphDTO> {
  const res = await fetch(`${API_URL}/graphs/${graphId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handle(res);
}

export async function replaceGraph(
  graphId: string,
  snapshot: GraphDTO,
): Promise<GraphDTO> {
  const res = await fetch(`${API_URL}/graphs/${graphId}/snapshot`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(snapshot),
  });
  return handle(res);
}

