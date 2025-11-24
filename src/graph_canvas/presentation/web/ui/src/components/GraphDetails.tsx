import type { GraphDTO } from "../types";
import { GRAPH_TYPES } from "../types";

type Props = {
  graph?: GraphDTO | null;
  selectedNodeId?: string | null;
  selectedEdgeId?: string | null;
  selectedSegment?: { edgeId: string; kind: "head" | "tail"; memberId: string } | null;
  onSelectNode?: (nodeId: string) => void;
  onSelectEdge?: (edgeId: string) => void;
  showGrid?: boolean;
  onToggleGrid?: () => void;
  nameDraft?: string;
  onNameChange?: (value: string) => void;
  onSaveName?: () => void;
  isSavingName?: boolean;
  graphType?: string;
  onTypeChange?: (value: string) => void;
  directed?: boolean;
  onDirectedChange?: (value: boolean) => void;
  onDeleteGraph?: () => void;
  isDeletingGraph?: boolean;
};

export function GraphDetails({
  graph,
  selectedNodeId,
  selectedEdgeId,
  selectedSegment,
  onSelectNode,
  onSelectEdge,
  showGrid,
  onToggleGrid,
  nameDraft,
  onNameChange,
  onSaveName,
  isSavingName,
  graphType,
  onTypeChange,
  directed,
  onDirectedChange,
  onDeleteGraph,
  isDeletingGraph,
}: Props) {
  if (!graph) {
    return (
      <section>
        <h2>Details</h2>
        <p>Select a graph to inspect its nodes and edges.</p>
      </section>
    );
  }

  const pendingName = (nameDraft ?? graph.name).trim();
  const pendingType = graphType ?? graph.graph_type ?? "graph";
  const pendingDirected = directed ?? (graph.directed ?? true);
  const segmentSummary = (() => {
    if (!selectedSegment) return null;
    const owningEdge = graph.edges.find((edge) => edge.id === selectedSegment.edgeId);
    if (!owningEdge) return null;
    const memberNode = graph.nodes.find((node) => node.id === selectedSegment.memberId);
    const memberEdge = graph.edges.find((edge) => edge.id === selectedSegment.memberId);
    const memberLabel = memberNode
      ? memberNode.text || memberNode.id
      : memberEdge
      ? `${memberEdge.source_id} → ${memberEdge.target_id}`
      : selectedSegment.memberId;
    const directionLabel = selectedSegment.kind === "head" ? "Head" : "Tail";
    return {
      edgeLabel: `${owningEdge.source_id} → ${owningEdge.target_id}`,
      memberLabel,
      directionLabel,
    };
  })();
  const hasNameChange = pendingName !== graph.name;
  const hasTypeChange = pendingType !== (graph.graph_type ?? "graph");
  const hasDirectedChange = pendingDirected !== (graph.directed ?? true);
  const disableSave = isSavingName || (!hasNameChange && !hasTypeChange && !hasDirectedChange);

  return (
    <section>
      <h2>Details · {graph.name}</h2>
      {onNameChange && (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            onSaveName?.();
          }}
          style={{ marginBottom: 12 }}
        >
          <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span style={{ fontSize: 13, color: "#475569" }}>Graph name</span>
            <div style={{ display: "flex", gap: 8 }}>
              <input
                type="text"
                value={nameDraft ?? graph.name}
                onChange={(event) => onNameChange(event.target.value)}
                style={{
                  flex: 1,
                  borderRadius: 6,
                  border: "1px solid #cbd5f5",
                  padding: "6px 10px",
                }}
                placeholder="Workspace name"
                required
              />
              <button
                type="submit"
                disabled={disableSave}
                style={{
                  padding: "6px 14px",
                  borderRadius: 6,
                  border: "1px solid #2563eb",
                  background: isSavingName ? "#bfdbfe" : "#2563eb",
                  color: "#fff",
                  cursor: disableSave ? "not-allowed" : "pointer",
                }}
              >
                Save
              </button>
            </div>
          </label>
          <label style={{ display: "flex", flexDirection: "column", gap: 4, marginTop: 12 }}>
            <span style={{ fontSize: 13, color: "#475569" }}>Graph type</span>
            <select
              value={graphType ?? graph.graph_type ?? "graph"}
              onChange={(event) => onTypeChange?.(event.target.value)}
              style={{
                borderRadius: 6,
                border: "1px solid #cbd5f5",
                padding: "6px 10px",
              }}
            >
              {GRAPH_TYPES.map((type) => (
                <option key={type} value={type}>
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </option>
              ))}
            </select>
          </label>
          <label style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 12 }}>
            <input
              type="checkbox"
              checked={directed ?? graph.directed ?? true}
              onChange={(event) => onDirectedChange?.(event.target.checked)}
            />
            Directed
          </label>
        </form>
      )}
      {onDeleteGraph && (
        <button
          type="button"
          onClick={onDeleteGraph}
          disabled={isDeletingGraph}
          style={{
            marginBottom: 12,
            padding: "6px 14px",
            borderRadius: 6,
            border: "1px solid #b91c1c",
            background: isDeletingGraph ? "#fecaca" : "#fff5f5",
            color: "#b91c1c",
            cursor: isDeletingGraph ? "not-allowed" : "pointer",
          }}
        >
          {isDeletingGraph ? "Deleting…" : "Delete Graph"}
        </button>
      )}
      {typeof showGrid === "boolean" && (
        <label style={{ display: "inline-flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
          <input
            type="checkbox"
            checked={showGrid}
            onChange={onToggleGrid}
          />
          Show grid
        </label>
      )}
      <div
        style={{
          display: "grid",
          gap: 16,
          gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
        }}
      >
        <div
          style={{
            border: "1px solid #d0d7e2",
            borderRadius: 8,
            padding: 16,
            background: "#fff",
          }}
        >
          <h3 style={{ marginTop: 0 }}>Nodes ({graph.nodes.length})</h3>
          <ul style={{ maxHeight: 220, overflow: "auto", paddingLeft: 18, marginBottom: 0 }}>
            {graph.nodes.map((node) => {
              const isSelected = selectedNodeId === node.id;
              return (
                <li key={node.id} style={{ marginBottom: 6 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div>
                      <strong>{node.text ?? node.id}</strong>
                      <small style={{ color: "#64748b", marginLeft: 6 }}>
                        ({node.x ?? 0}, {node.y ?? 0})
                      </small>
                    </div>
                    <button
                      onClick={() => onSelectNode?.(node.id)}
                      style={{
                        border: "1px solid #2563eb",
                        borderRadius: 6,
                        padding: "2px 8px",
                        background: isSelected ? "#2563eb" : "transparent",
                        color: isSelected ? "#fff" : "#2563eb",
                        fontSize: 12,
                      }}
                    >
                      {isSelected ? "Selected" : "Select"}
                    </button>
                  </div>
                </li>
              );
            })}
          </ul>
          {segmentSummary && (
            <div
              style={{
                marginTop: 12,
                padding: 12,
                borderRadius: 8,
                background: "#f1f5f9",
                border: "1px solid #cbd5f5",
                fontSize: 13,
                color: "#0f172a",
              }}
            >
              <p style={{ margin: 0, fontWeight: 600, fontSize: 14 }}>Selected Segment</p>
              <p style={{ margin: "4px 0 0" }}>
                <strong>Edge:</strong> {segmentSummary.edgeLabel}
              </p>
              <p style={{ margin: "2px 0 0" }}>
                <strong>Direction:</strong> {segmentSummary.directionLabel}
              </p>
              <p style={{ margin: "2px 0 0" }}>
                <strong>Member:</strong> {segmentSummary.memberLabel}
              </p>
            </div>
          )}
        </div>
        <div
          style={{
            border: "1px solid #d0d7e2",
            borderRadius: 8,
            padding: 16,
            background: "#fff",
          }}
        >
          <h3 style={{ marginTop: 0 }}>Edges ({graph.edges.length})</h3>
          <ul style={{ maxHeight: 220, overflow: "auto", paddingLeft: 18, marginBottom: 0 }}>
            {graph.edges.map((edge) => {
              const isSelected = selectedEdgeId === edge.id;
              return (
                <li key={edge.id} style={{ marginBottom: 6 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div>
                      {edge.source_id} → {edge.target_id}{" "}
                      {edge.text ? (
                        <small style={{ color: "#64748b" }}>({edge.text})</small>
                      ) : null}
                    </div>
                    <button
                      onClick={() => onSelectEdge?.(edge.id)}
                      style={{
                        border: "1px solid #f97316",
                        borderRadius: 6,
                        padding: "2px 8px",
                        background: isSelected ? "#fb923c" : "transparent",
                        color: isSelected ? "#fff" : "#c2410c",
                        fontSize: 12,
                      }}
                    >
                      {isSelected ? "Selected" : "Select"}
                    </button>
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      </div>
    </section>
  );
}

