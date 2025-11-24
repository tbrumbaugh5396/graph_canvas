import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from "react";
import { GRAPH_TYPES } from "../types";
export function GraphForm({ onSubmit }) {
    const [name, setName] = useState("");
    const [id, setId] = useState("");
    const [graphType, setGraphType] = useState("graph");
    const [directed, setDirected] = useState(true);
    const [status, setStatus] = useState("idle");
    const [error, setError] = useState(null);
    async function handleSubmit(event) {
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
        }
        catch (err) {
            setStatus("error");
            setError(err instanceof Error ? err.message : "Unknown error");
        }
    }
    return (_jsxs("form", { onSubmit: handleSubmit, style: {
            border: "1px dashed #cbd5f5",
            padding: 16,
            borderRadius: 8,
            background: "#fdfdff",
        }, children: [_jsx("h2", { children: "Create Graph" }), _jsxs("label", { style: { display: "block", marginBottom: 12 }, children: ["Name", _jsx("input", { value: name, onChange: (event) => setName(event.target.value), placeholder: "My graph", required: true, style: { display: "block", width: "100%", marginTop: 4 } })] }), _jsxs("label", { style: { display: "block", marginBottom: 12 }, children: ["Identifier (optional)", _jsx("input", { value: id, onChange: (event) => setId(event.target.value), placeholder: "leave blank for UUID", style: { display: "block", width: "100%", marginTop: 4 } })] }), _jsxs("label", { style: { display: "block", marginBottom: 12 }, children: ["Graph type", _jsx("select", { value: graphType, onChange: (event) => setGraphType(event.target.value), style: { display: "block", width: "100%", marginTop: 4 }, children: GRAPH_TYPES.map((type) => (_jsx("option", { value: type, children: type.charAt(0).toUpperCase() + type.slice(1) }, type))) })] }), _jsxs("label", { style: { display: "block", marginBottom: 12 }, children: ["Direction", _jsxs("select", { value: directed ? "directed" : "undirected", onChange: (event) => setDirected(event.target.value === "directed"), style: { display: "block", width: "100%", marginTop: 4 }, children: [_jsx("option", { value: "directed", children: "Directed" }), _jsx("option", { value: "undirected", children: "Undirected" })] })] }), _jsx("button", { type: "submit", disabled: status === "submitting", style: {
                    padding: "8px 16px",
                    borderRadius: 6,
                    background: "#2563eb",
                    color: "#fff",
                    border: "none",
                }, children: status === "submitting" ? "Creating..." : "Create Graph" }), error && (_jsxs("p", { style: { color: "#b91c1c", marginTop: 12 }, children: ["Could not create graph: ", error] }))] }));
}
