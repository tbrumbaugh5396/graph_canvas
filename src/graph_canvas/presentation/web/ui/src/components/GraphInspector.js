import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useEffect, useMemo, useState } from "react";
function safeParseMetadata(text) {
    if (!text.trim()) {
        return undefined;
    }
    try {
        return JSON.parse(text);
    }
    catch {
        throw new Error("Metadata must be valid JSON");
    }
}
export function GraphInspector({ graph, selectedNodeId, selectedEdgeId, onSelectNode, onSelectEdge, onCreateNode, onUpdateNode, onDeleteNode, onCreateEdge, onUpdateEdge, onDeleteEdge, }) {
    const selectedNode = useMemo(() => graph?.nodes.find((node) => node.id === selectedNodeId) ?? null, [graph, selectedNodeId]);
    const selectedEdge = useMemo(() => graph?.edges.find((edge) => edge.id === selectedEdgeId) ?? null, [graph, selectedEdgeId]);
    const [newNodeLabel, setNewNodeLabel] = useState("");
    const [nodeText, setNodeText] = useState("");
    const [nodeMetadata, setNodeMetadata] = useState("");
    const [edgeText, setEdgeText] = useState("");
    const [edgeMetadata, setEdgeMetadata] = useState("");
    const [createEdgeSource, setCreateEdgeSource] = useState("");
    const [createEdgeTarget, setCreateEdgeTarget] = useState("");
    const [createHyperSources, setCreateHyperSources] = useState([]);
    const [createHyperTargets, setCreateHyperTargets] = useState([]);
    const [createEdgeLabel, setCreateEdgeLabel] = useState("");
    const [error, setError] = useState(null);
    useEffect(() => {
        if (!selectedNode) {
            setNodeText("");
            setNodeMetadata("");
            return;
        }
        setNodeText(selectedNode.text ?? "");
        setNodeMetadata(JSON.stringify(selectedNode.metadata ?? {}, null, 2).replace(/{}$/, ""));
    }, [selectedNode?.id]);
    useEffect(() => {
        if (!selectedEdge) {
            setEdgeText("");
            setEdgeMetadata("");
            return;
        }
        setEdgeText(selectedEdge.text ?? "");
        setEdgeMetadata(JSON.stringify(selectedEdge.metadata ?? {}, null, 2).replace(/{}$/, ""));
    }, [selectedEdge?.id]);
    const handleCreateNode = async (event) => {
        event.preventDefault();
        if (!graph)
            return;
        try {
            await onCreateNode({ text: newNodeLabel || "New Node" });
            setNewNodeLabel("");
            setError(null);
        }
        catch (err) {
            setError(err instanceof Error ? err.message : "Failed to create node");
        }
    };
    const handleNodeUpdate = async (event) => {
        event.preventDefault();
        if (!graph || !selectedNode)
            return;
        try {
            const metadata = safeParseMetadata(nodeMetadata);
            await onUpdateNode(selectedNode.id, {
                text: nodeText,
                metadata,
            });
            setError(null);
        }
        catch (err) {
            setError(err instanceof Error ? err.message : "Failed to update node");
        }
    };
    const handleNodeDelete = async () => {
        if (!graph || !selectedNode)
            return;
        try {
            await onDeleteNode(selectedNode.id);
            onSelectNode(null);
            setError(null);
        }
        catch (err) {
            setError(err instanceof Error ? err.message : "Failed to delete node");
        }
    };
    const graphType = graph?.graph_type?.toLowerCase();
    const isHyperEdge = graphType === "hypergraph" || graphType === "ubergraph";
    const allowEdgeTargets = graphType === "ubergraph";
    const sortedNodes = useMemo(() => (graph?.nodes ?? []).map((node) => ({
        id: node.id,
        label: node.text?.trim() ? node.text : node.id,
    })), [graph?.nodes]);
    const sortedEdges = useMemo(() => (graph?.edges ?? []).map((edge) => ({
        id: edge.id,
        label: edge.text?.trim()
            ? edge.text
            : `${edge.id.slice(0, 4)}…${edge.id.slice(-4)}`,
    })), [graph?.edges]);
    useEffect(() => {
        setCreateHyperSources([]);
        setCreateHyperTargets([]);
    }, [graphType]);
    const handleCreateEdge = async (event) => {
        event.preventDefault();
        if (!graph)
            return;
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
            const payload = {
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
        }
        catch (err) {
            setError(err instanceof Error ? err.message : "Failed to create edge");
        }
    };
    const handleEdgeUpdate = async (event) => {
        event.preventDefault();
        if (!graph || !selectedEdge)
            return;
        try {
            const metadata = safeParseMetadata(edgeMetadata);
            await onUpdateEdge(selectedEdge.id, {
                text: edgeText,
                metadata,
            });
            setError(null);
        }
        catch (err) {
            setError(err instanceof Error ? err.message : "Failed to update edge");
        }
    };
    const handleEdgeDelete = async () => {
        if (!graph || !selectedEdge)
            return;
        try {
            await onDeleteEdge(selectedEdge.id);
            onSelectEdge(null);
            setError(null);
        }
        catch (err) {
            setError(err instanceof Error ? err.message : "Failed to delete edge");
        }
    };
    return (_jsxs("section", { children: [_jsx("h2", { children: "Editor" }), error && (_jsx("p", { style: { color: "#b91c1c" }, children: error })), _jsxs("div", { style: {
                    display: "grid",
                    gap: 16,
                    gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
                    gridTemplateAreas: `
            "add-node add-edge"
            "selected-node selected-edge"
          `,
                    alignItems: "stretch",
                }, children: [_jsxs("form", { onSubmit: handleCreateNode, style: {
                            gridArea: "add-node",
                            border: "1px solid #cbd5f5",
                            borderRadius: 8,
                            padding: 16,
                            background: "#fff",
                        }, children: [_jsx("h3", { style: { marginTop: 0 }, children: "Add Node" }), _jsxs("label", { style: { display: "block", marginBottom: 12 }, children: ["Label", _jsx("input", { value: newNodeLabel, onChange: (event) => setNewNodeLabel(event.target.value), placeholder: "Node label", style: { width: "100%", marginTop: 4 } })] }), _jsx("button", { type: "submit", style: {
                                    padding: "6px 12px",
                                    borderRadius: 6,
                                    border: "none",
                                    background: "#2563eb",
                                    color: "#fff",
                                }, children: "Create Node" })] }), _jsxs("form", { onSubmit: handleCreateEdge, style: {
                            gridArea: "add-edge",
                            border: "1px solid #fde4cf",
                            borderRadius: 8,
                            padding: 16,
                            background: "#fff7ed",
                        }, children: [_jsx("h3", { style: { marginTop: 0 }, children: "Add Edge" }), isHyperEdge ? (_jsxs(_Fragment, { children: [_jsxs("label", { style: { display: "block", marginBottom: 12 }, children: ["Tails (choose one or more)", _jsxs("select", { multiple: true, value: createHyperSources, onChange: (event) => setCreateHyperSources(Array.from(event.target.selectedOptions).map((opt) => opt.value)), style: { width: "100%", marginTop: 4, minHeight: 120 }, children: [_jsx("optgroup", { label: "Nodes", children: sortedNodes.map((node) => (_jsx("option", { value: node.id, children: node.label }, node.id))) }), allowEdgeTargets && (_jsx("optgroup", { label: "Edges", children: sortedEdges.map((edge) => (_jsx("option", { value: edge.id, children: edge.label }, edge.id))) }))] })] }), _jsxs("label", { style: { display: "block", marginBottom: 12 }, children: ["Heads (choose one or more)", _jsxs("select", { multiple: true, value: createHyperTargets, onChange: (event) => setCreateHyperTargets(Array.from(event.target.selectedOptions).map((opt) => opt.value)), style: { width: "100%", marginTop: 4, minHeight: 120 }, children: [_jsx("optgroup", { label: "Nodes", children: sortedNodes.map((node) => (_jsx("option", { value: node.id, children: node.label }, node.id))) }), allowEdgeTargets && (_jsx("optgroup", { label: "Edges", children: sortedEdges.map((edge) => (_jsx("option", { value: edge.id, children: edge.label }, edge.id))) }))] })] }), allowEdgeTargets && (_jsx("p", { style: { fontSize: 12, color: "#92400e" }, children: "After creating the uberedge, use the head/tail handles to attach other edges as members." }))] })) : (_jsxs(_Fragment, { children: [_jsxs("label", { style: { display: "block", marginBottom: 12 }, children: ["Source", _jsxs("select", { required: true, value: createEdgeSource, onChange: (event) => setCreateEdgeSource(event.target.value), style: { width: "100%", marginTop: 4 }, children: [_jsx("option", { value: "", children: "Select source" }), sortedNodes.map((node) => (_jsx("option", { value: node.id, children: node.label }, node.id)))] })] }), _jsxs("label", { style: { display: "block", marginBottom: 12 }, children: ["Target", _jsxs("select", { required: true, value: createEdgeTarget, onChange: (event) => setCreateEdgeTarget(event.target.value), style: { width: "100%", marginTop: 4 }, children: [_jsx("option", { value: "", children: "Select target" }), sortedNodes.map((node) => (_jsx("option", { value: node.id, children: node.label }, node.id)))] })] })] })), _jsxs("label", { style: { display: "block", marginBottom: 12 }, children: ["Label", _jsx("input", { value: createEdgeLabel, onChange: (event) => setCreateEdgeLabel(event.target.value), placeholder: "Optional label", style: { width: "100%", marginTop: 4 } })] }), _jsx("button", { type: "submit", style: {
                                    padding: "6px 12px",
                                    borderRadius: 6,
                                    border: "none",
                                    background: "#f97316",
                                    color: "#fff",
                                }, children: "Create Edge" })] }), _jsxs("form", { onSubmit: handleNodeUpdate, style: {
                            gridArea: "selected-node",
                            border: "1px solid #cbd5f5",
                            borderRadius: 8,
                            padding: 16,
                            background: "#fff",
                            minHeight: "100%",
                        }, children: [_jsx("h3", { style: { marginTop: 0 }, children: "Selected Node" }), selectedNode ? (_jsxs(_Fragment, { children: [_jsxs("label", { style: { display: "block", marginBottom: 12 }, children: ["Label", _jsx("input", { value: nodeText, onChange: (event) => setNodeText(event.target.value), style: { width: "100%", marginTop: 4 } })] }), _jsxs("label", { style: { display: "block", marginBottom: 12 }, children: ["Metadata (JSON)", _jsx("textarea", { value: nodeMetadata, onChange: (event) => setNodeMetadata(event.target.value), rows: 5, style: { width: "100%", marginTop: 4, fontFamily: "monospace" } })] }), _jsxs("div", { style: { display: "flex", gap: 8 }, children: [_jsx("button", { type: "submit", style: {
                                                    padding: "6px 12px",
                                                    borderRadius: 6,
                                                    border: "none",
                                                    background: "#16a34a",
                                                    color: "#fff",
                                                    flex: 1,
                                                }, children: "Update Node" }), _jsx("button", { type: "button", onClick: handleNodeDelete, style: {
                                                    padding: "6px 12px",
                                                    borderRadius: 6,
                                                    border: "none",
                                                    background: "#dc2626",
                                                    color: "#fff",
                                                }, children: "Delete" })] })] })) : (_jsx("p", { children: "Select a node to edit its properties." }))] }), _jsxs("form", { onSubmit: handleEdgeUpdate, style: {
                            gridArea: "selected-edge",
                            border: "1px solid #fde4cf",
                            borderRadius: 8,
                            padding: 16,
                            background: "#fff7ed",
                            minHeight: "100%",
                        }, children: [_jsx("h3", { style: { marginTop: 0 }, children: "Selected Edge" }), selectedEdge ? (_jsxs(_Fragment, { children: [_jsxs("p", { style: { marginTop: 0, color: "#92400e" }, children: [selectedEdge.source_id, " \u2192 ", selectedEdge.target_id] }), _jsxs("label", { style: { display: "block", marginBottom: 12 }, children: ["Label", _jsx("input", { value: edgeText, onChange: (event) => setEdgeText(event.target.value), style: { width: "100%", marginTop: 4 } })] }), _jsxs("label", { style: { display: "block", marginBottom: 12 }, children: ["Metadata (JSON)", _jsx("textarea", { value: edgeMetadata, onChange: (event) => setEdgeMetadata(event.target.value), rows: 4, style: { width: "100%", marginTop: 4, fontFamily: "monospace" } })] }), _jsxs("div", { style: { display: "flex", gap: 8 }, children: [_jsx("button", { type: "submit", style: {
                                                    padding: "6px 12px",
                                                    borderRadius: 6,
                                                    border: "none",
                                                    background: "#f97316",
                                                    color: "#fff",
                                                    flex: 1,
                                                }, children: "Update Edge" }), _jsx("button", { type: "button", onClick: handleEdgeDelete, style: {
                                                    padding: "6px 12px",
                                                    borderRadius: 6,
                                                    border: "none",
                                                    background: "#dc2626",
                                                    color: "#fff",
                                                }, children: "Delete" })] })] })) : (_jsx("p", { children: "Select an edge to edit its properties." }))] })] })] }));
}
