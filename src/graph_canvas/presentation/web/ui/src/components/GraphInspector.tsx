import { useEffect, useMemo, useState } from "react";
import type { EdgeInput, GraphDTO, NodeInput } from "../types";

type Props = {
  graph: GraphDTO | null;
  selectedNodeId: string | null;
  selectedEdgeId: string | null;
  onSelectNode: (nodeId: string | null) => void;
  onSelectEdge: (edgeId: string | null) => void;
  onCreateNode: (input: NodeInput) => Promise<void> | void;
  onUpdateNode: (nodeId: string, input: NodeInput) => Promise<void> | void;
  onDeleteNode: (nodeId: string) => Promise<void> | void;
  onCreateEdge: (
    input: EdgeInput & { source_id: string; target_id: string },
  ) => Promise<void> | void;
  onUpdateEdge: (
    edgeId: string,
    input: EdgeInput & { source_id?: string; target_id?: string },
  ) => Promise<void> | void;
  onDeleteEdge: (edgeId: string) => Promise<void> | void;
};

function safeParseMetadata(text: string): Record<string, unknown> | undefined {
  if (!text.trim()) {
    return undefined;
  }
  try {
    return JSON.parse(text);
  } catch {
    throw new Error("Metadata must be valid JSON");
  }
}

export function GraphInspector({
  graph,
  selectedNodeId,
  selectedEdgeId,
  onSelectNode,
  onSelectEdge,
  onCreateNode,
  onUpdateNode,
  onDeleteNode,
  onCreateEdge,
  onUpdateEdge,
  onDeleteEdge,
}: Props) {
  const selectedNode = useMemo(
    () => graph?.nodes.find((node) => node.id === selectedNodeId) ?? null,
    [graph, selectedNodeId],
  );
  const selectedEdge = useMemo(
    () => graph?.edges.find((edge) => edge.id === selectedEdgeId) ?? null,
    [graph, selectedEdgeId],
  );

  const [newNodeLabel, setNewNodeLabel] = useState("");
  const [nodeText, setNodeText] = useState("");
  const [nodeMetadata, setNodeMetadata] = useState("");
  const [edgeText, setEdgeText] = useState("");
  const [edgeMetadata, setEdgeMetadata] = useState("");
  const [createEdgeSource, setCreateEdgeSource] = useState("");
  const [createEdgeTarget, setCreateEdgeTarget] = useState("");
  const [createHyperSources, setCreateHyperSources] = useState<string[]>([]);
  const [createHyperTargets, setCreateHyperTargets] = useState<string[]>([]);
  const [createEdgeLabel, setCreateEdgeLabel] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedNode) {
      setNodeText("");
      setNodeMetadata("");
      return;
    }
    setNodeText(selectedNode.text ?? "");
    setNodeMetadata(
      JSON.stringify(selectedNode.metadata ?? {}, null, 2).replace(/{}$/, ""),
    );
  }, [selectedNode?.id]);

  useEffect(() => {
    if (!selectedEdge) {
      setEdgeText("");
      setEdgeMetadata("");
      return;
    }
    setEdgeText(selectedEdge.text ?? "");
    setEdgeMetadata(
      JSON.stringify(selectedEdge.metadata ?? {}, null, 2).replace(/{}$/, ""),
    );
  }, [selectedEdge?.id]);

  const handleCreateNode = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!graph) return;
    try {
      await onCreateNode({ text: newNodeLabel || "New Node" });
      setNewNodeLabel("");
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create node");
    }
  };

  const handleNodeUpdate = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!graph || !selectedNode) return;
    try {
      const metadata = safeParseMetadata(nodeMetadata);
      await onUpdateNode(selectedNode.id, {
        text: nodeText,
        metadata,
      });
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update node");
    }
  };

  const handleNodeDelete = async () => {
    if (!graph || !selectedNode) return;
    try {
      await onDeleteNode(selectedNode.id);
      onSelectNode(null);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete node");
    }
  };

  const graphType = graph?.graph_type?.toLowerCase();
  const isHyperEdge = graphType === "hypergraph" || graphType === "ubergraph";
  const allowEdgeTargets = graphType === "ubergraph";
  const sortedNodes = useMemo(
    () =>
      (graph?.nodes ?? []).map((node) => ({
        id: node.id,
        label: node.text?.trim() ? node.text : node.id,
      })),
    [graph?.nodes],
  );
  const sortedEdges = useMemo(
    () =>
      (graph?.edges ?? []).map((edge) => ({
        id: edge.id,
        label: edge.text?.trim()
          ? edge.text
          : `${edge.id.slice(0, 4)}…${edge.id.slice(-4)}`,
      })),
    [graph?.edges],
  );

  useEffect(() => {
    setCreateHyperSources([]);
    setCreateHyperTargets([]);
  }, [graphType]);

  const handleCreateEdge = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!graph) return;
    const sources = isHyperEdge
      ? createHyperSources
      : createEdgeSource
      ? [createEdgeSource]
      : [];
    const targets = isHyperEdge
      ? createHyperTargets
      : createEdgeTarget
      ? [createEdgeTarget]
      : [];
    if (sources.length === 0 || targets.length === 0) {
      setError("Select at least one source and target");
      return;
    }
    try {
      const payload: EdgeInput & { source_id: string; target_id: string; source_ids?: string[]; target_ids?: string[] } =
        {
          source_id: sources[0],
          target_id: targets[0],
        };
      if (isHyperEdge) {
        payload.source_ids = sources;
        payload.target_ids = targets;
      }
      await onCreateEdge({
        ...payload,
        text: createEdgeLabel || undefined,
      });
      setCreateEdgeLabel("");
      setCreateEdgeSource("");
      setCreateEdgeTarget("");
      setCreateHyperSources([]);
      setCreateHyperTargets([]);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create edge");
    }
  };

  const handleEdgeUpdate = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!graph || !selectedEdge) return;
    try {
      const metadata = safeParseMetadata(edgeMetadata);
      await onUpdateEdge(selectedEdge.id, {
        text: edgeText,
        metadata,
      });
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update edge");
    }
  };

  const handleEdgeDelete = async () => {
    if (!graph || !selectedEdge) return;
    try {
      await onDeleteEdge(selectedEdge.id);
      onSelectEdge(null);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete edge");
    }
  };

  return (
    <section>
      <h2>Editor</h2>
      {error && (
        <p style={{ color: "#b91c1c" }}>
          {error}
        </p>
      )}
      <div
        style={{
          display: "grid",
          gap: 16,
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          gridTemplateAreas: `
            "add-node add-edge"
            "selected-node selected-edge"
          `,
          alignItems: "stretch",
        }}
      >
        <form
          onSubmit={handleCreateNode}
          style={{
            gridArea: "add-node",
            border: "1px solid #cbd5f5",
            borderRadius: 8,
            padding: 16,
            background: "#fff",
          }}
        >
          <h3 style={{ marginTop: 0 }}>Add Node</h3>
          <label style={{ display: "block", marginBottom: 12 }}>
            Label
            <input
              value={newNodeLabel}
              onChange={(event) => setNewNodeLabel(event.target.value)}
              placeholder="Node label"
              style={{ width: "100%", marginTop: 4 }}
            />
          </label>
          <button
            type="submit"
            style={{
              padding: "6px 12px",
              borderRadius: 6,
              border: "none",
              background: "#2563eb",
              color: "#fff",
            }}
          >
            Create Node
          </button>
        </form>

        <form
          onSubmit={handleCreateEdge}
          style={{
            gridArea: "add-edge",
            border: "1px solid #fde4cf",
            borderRadius: 8,
            padding: 16,
            background: "#fff7ed",
          }}
        >
          <h3 style={{ marginTop: 0 }}>Add Edge</h3>
          {isHyperEdge ? (
            <>
              <label style={{ display: "block", marginBottom: 12 }}>
                Tails (choose one or more)
                <select
                  multiple
                  value={createHyperSources}
                  onChange={(event) =>
                    setCreateHyperSources(
                      Array.from(event.target.selectedOptions).map((opt) => opt.value),
                    )
                  }
                  style={{ width: "100%", marginTop: 4, minHeight: 120 }}
                >
                  <optgroup label="Nodes">
                    {sortedNodes.map((node) => (
                      <option key={node.id} value={node.id}>
                        {node.label}
                      </option>
                    ))}
                  </optgroup>
                  {allowEdgeTargets && (
                    <optgroup label="Edges">
                      {sortedEdges.map((edge) => (
                        <option key={edge.id} value={edge.id}>
                          {edge.label}
                        </option>
                      ))}
                    </optgroup>
                  )}
                </select>
              </label>
              <label style={{ display: "block", marginBottom: 12 }}>
                Heads (choose one or more)
                <select
                  multiple
                  value={createHyperTargets}
                  onChange={(event) =>
                    setCreateHyperTargets(
                      Array.from(event.target.selectedOptions).map((opt) => opt.value),
                    )
                  }
                  style={{ width: "100%", marginTop: 4, minHeight: 120 }}
                >
                  <optgroup label="Nodes">
                    {sortedNodes.map((node) => (
                      <option key={node.id} value={node.id}>
                        {node.label}
                      </option>
                    ))}
                  </optgroup>
                  {allowEdgeTargets && (
                    <optgroup label="Edges">
                      {sortedEdges.map((edge) => (
                        <option key={edge.id} value={edge.id}>
                          {edge.label}
                        </option>
                      ))}
                    </optgroup>
                  )}
                </select>
              </label>
              {allowEdgeTargets && (
                <p style={{ fontSize: 12, color: "#92400e" }}>
                  After creating the uberedge, use the head/tail handles to attach other
                  edges as members.
                </p>
              )}
            </>
          ) : (
            <>
              <label style={{ display: "block", marginBottom: 12 }}>
                Source
                <select
                  required
                  value={createEdgeSource}
                  onChange={(event) => setCreateEdgeSource(event.target.value)}
                  style={{ width: "100%", marginTop: 4 }}
                >
                  <option value="">Select source</option>
                  {sortedNodes.map((node) => (
                    <option key={node.id} value={node.id}>
                      {node.label}
                    </option>
                  ))}
                </select>
              </label>
              <label style={{ display: "block", marginBottom: 12 }}>
                Target
                <select
                  required
                  value={createEdgeTarget}
                  onChange={(event) => setCreateEdgeTarget(event.target.value)}
                  style={{ width: "100%", marginTop: 4 }}
                >
                  <option value="">Select target</option>
                  {sortedNodes.map((node) => (
                    <option key={node.id} value={node.id}>
                      {node.label}
                    </option>
                  ))}
                </select>
              </label>
            </>
          )}
          <label style={{ display: "block", marginBottom: 12 }}>
            Label
            <input
              value={createEdgeLabel}
              onChange={(event) => setCreateEdgeLabel(event.target.value)}
              placeholder="Optional label"
              style={{ width: "100%", marginTop: 4 }}
            />
          </label>
          <button
            type="submit"
            style={{
              padding: "6px 12px",
              borderRadius: 6,
              border: "none",
              background: "#f97316",
              color: "#fff",
            }}
          >
            Create Edge
          </button>
        </form>

        <form
          onSubmit={handleNodeUpdate}
          style={{
            gridArea: "selected-node",
            border: "1px solid #cbd5f5",
            borderRadius: 8,
            padding: 16,
            background: "#fff",
            minHeight: "100%",
          }}
        >
          <h3 style={{ marginTop: 0 }}>Selected Node</h3>
          {selectedNode ? (
            <>
              <label style={{ display: "block", marginBottom: 12 }}>
                Label
                <input
                  value={nodeText}
                  onChange={(event) => setNodeText(event.target.value)}
                  style={{ width: "100%", marginTop: 4 }}
                />
              </label>
              <label style={{ display: "block", marginBottom: 12 }}>
                Metadata (JSON)
                <textarea
                  value={nodeMetadata}
                  onChange={(event) => setNodeMetadata(event.target.value)}
                  rows={5}
                  style={{ width: "100%", marginTop: 4, fontFamily: "monospace" }}
                />
              </label>
              <div style={{ display: "flex", gap: 8 }}>
                <button
                  type="submit"
                  style={{
                    padding: "6px 12px",
                    borderRadius: 6,
                    border: "none",
                    background: "#16a34a",
                    color: "#fff",
                    flex: 1,
                  }}
                >
                  Update Node
                </button>
                <button
                  type="button"
                  onClick={handleNodeDelete}
                  style={{
                    padding: "6px 12px",
                    borderRadius: 6,
                    border: "none",
                    background: "#dc2626",
                    color: "#fff",
                  }}
                >
                  Delete
                </button>
              </div>
            </>
          ) : (
            <p>Select a node to edit its properties.</p>
          )}
        </form>

        <form
          onSubmit={handleEdgeUpdate}
          style={{
            gridArea: "selected-edge",
            border: "1px solid #fde4cf",
            borderRadius: 8,
            padding: 16,
            background: "#fff7ed",
            minHeight: "100%",
          }}
        >
          <h3 style={{ marginTop: 0 }}>Selected Edge</h3>
          {selectedEdge ? (
            <>
              <p style={{ marginTop: 0, color: "#92400e" }}>
                {selectedEdge.source_id} → {selectedEdge.target_id}
              </p>
              <label style={{ display: "block", marginBottom: 12 }}>
                Label
                <input
                  value={edgeText}
                  onChange={(event) => setEdgeText(event.target.value)}
                  style={{ width: "100%", marginTop: 4 }}
                />
              </label>
              <label style={{ display: "block", marginBottom: 12 }}>
                Metadata (JSON)
                <textarea
                  value={edgeMetadata}
                  onChange={(event) => setEdgeMetadata(event.target.value)}
                  rows={4}
                  style={{ width: "100%", marginTop: 4, fontFamily: "monospace" }}
                />
              </label>
              <div style={{ display: "flex", gap: 8 }}>
                <button
                  type="submit"
                  style={{
                    padding: "6px 12px",
                    borderRadius: 6,
                    border: "none",
                    background: "#f97316",
                    color: "#fff",
                    flex: 1,
                  }}
                >
                  Update Edge
                </button>
                <button
                  type="button"
                  onClick={handleEdgeDelete}
                  style={{
                    padding: "6px 12px",
                    borderRadius: 6,
                    border: "none",
                    background: "#dc2626",
                    color: "#fff",
                  }}
                >
                  Delete
                </button>
              </div>
            </>
          ) : (
            <p>Select an edge to edit its properties.</p>
          )}
        </form>
      </div>
    </section>
  );
}

