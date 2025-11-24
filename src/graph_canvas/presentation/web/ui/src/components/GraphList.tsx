import type { GraphDTO } from "../types";

type Props = {
  graphs: GraphDTO[];
  onRefresh: () => void;
  isLoading: boolean;
  onSelect: (graph: GraphDTO) => void;
  selectedGraphId?: string | null;
  onDelete?: (graph: GraphDTO) => void;
  deletingGraphId?: string | null;
};

export function GraphList({
  graphs,
  onRefresh,
  isLoading,
  onSelect,
  selectedGraphId,
  onDelete,
  deletingGraphId,
}: Props) {
  return (
    <section>
      <header style={{ display: "flex", justifyContent: "space-between" }}>
        <h2>Graphs</h2>
        <button onClick={onRefresh} disabled={isLoading}>
          {isLoading ? "Refreshing..." : "Refresh"}
        </button>
      </header>
      <div>
        {graphs.length === 0 && <p>No graphs yet.</p>}
        {graphs.map((graph) => (
          <article
            key={graph.id}
            style={{
              border: "1px solid #d0d7e2",
              borderRadius: 8,
              padding: 16,
              marginBottom: 12,
              background: graph.id === selectedGraphId ? "#e0e7ff" : "#fff",
            }}
          >
            <h3>{graph.name}</h3>
            <small>ID: {graph.id}</small>
            <p style={{ marginBottom: 8 }}>
              Nodes: {graph.nodes.length} · Edges: {graph.edges.length}
            </p>
            <p style={{ marginTop: 0, color: "#475569" }}>
              Type: {graph.graph_type ?? "graph"} ·{" "}
              {graph.directed === false ? "Undirected" : "Directed"}
            </p>
            <button
              onClick={() => onSelect(graph)}
              style={{
                padding: "4px 12px",
                borderRadius: 6,
                border: "1px solid #1d4ed8",
                background:
                  graph.id === selectedGraphId ? "#1d4ed8" : "transparent",
                color: graph.id === selectedGraphId ? "#fff" : "#1d4ed8",
              }}
            >
              {graph.id === selectedGraphId ? "Selected" : "Inspect"}
            </button>
            {onDelete && (
              <button
                onClick={() => onDelete(graph)}
                disabled={deletingGraphId === graph.id}
                style={{
                  marginLeft: 12,
                  padding: "4px 12px",
                  borderRadius: 6,
                  border: "1px solid #b91c1c",
                  background: deletingGraphId === graph.id ? "#fecaca" : "transparent",
                  color: "#b91c1c",
                }}
              >
                {deletingGraphId === graph.id ? "Deleting..." : "Delete"}
              </button>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}

