import { useState } from "react";
import type { GraphDTO } from "../types";
import { GRAPH_TYPES } from "../types";

type Props = {
  onSubmit: (graph: GraphDTO) => Promise<void>;
};

export function GraphForm({ onSubmit }: Props) {
  const [name, setName] = useState("");
  const [id, setId] = useState("");
  const [graphType, setGraphType] = useState("graph");
  const [directed, setDirected] = useState(true);
  const [status, setStatus] = useState<"idle" | "submitting" | "error">("idle");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setStatus("submitting");
    setError(null);

    try {
      await onSubmit({
        id: id || crypto.randomUUID(),
        name: name || "Untitled Graph",
        graph_type: graphType,
        directed,
        nodes: [],
        edges: [],
        metadata: {},
      });
      setName("");
      setId("");
      setGraphType("graph");
      setDirected(true);
      setStatus("idle");
    } catch (err) {
      setStatus("error");
      setError(err instanceof Error ? err.message : "Unknown error");
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      style={{
        border: "1px dashed #cbd5f5",
        padding: 16,
        borderRadius: 8,
        background: "#fdfdff",
      }}
    >
      <h2>Create Graph</h2>
      <label style={{ display: "block", marginBottom: 12 }}>
        Name
        <input
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="My graph"
          required
          style={{ display: "block", width: "100%", marginTop: 4 }}
        />
      </label>
      <label style={{ display: "block", marginBottom: 12 }}>
        Identifier (optional)
        <input
          value={id}
          onChange={(event) => setId(event.target.value)}
          placeholder="leave blank for UUID"
          style={{ display: "block", width: "100%", marginTop: 4 }}
        />
      </label>
      <label style={{ display: "block", marginBottom: 12 }}>
        Graph type
        <select
          value={graphType}
          onChange={(event) => setGraphType(event.target.value)}
          style={{ display: "block", width: "100%", marginTop: 4 }}
        >
          {GRAPH_TYPES.map((type) => (
            <option key={type} value={type}>
              {type.charAt(0).toUpperCase() + type.slice(1)}
            </option>
          ))}
        </select>
      </label>
      <label style={{ display: "block", marginBottom: 12 }}>
        Direction
        <select
          value={directed ? "directed" : "undirected"}
          onChange={(event) => setDirected(event.target.value === "directed")}
          style={{ display: "block", width: "100%", marginTop: 4 }}
        >
          <option value="directed">Directed</option>
          <option value="undirected">Undirected</option>
        </select>
      </label>
      <button
        type="submit"
        disabled={status === "submitting"}
        style={{
          padding: "8px 16px",
          borderRadius: 6,
          background: "#2563eb",
          color: "#fff",
          border: "none",
        }}
      >
        {status === "submitting" ? "Creating..." : "Create Graph"}
      </button>
      {error && (
        <p style={{ color: "#b91c1c", marginTop: 12 }}>
          Could not create graph: {error}
        </p>
      )}
    </form>
  );
}

