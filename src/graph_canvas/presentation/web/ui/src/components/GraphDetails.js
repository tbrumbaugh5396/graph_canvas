import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { GRAPH_TYPES } from "../types";
export function GraphDetails({ graph, selectedNodeId, selectedEdgeId, selectedSegment, onSelectNode, onSelectEdge, showGrid, onToggleGrid, nameDraft, onNameChange, onSaveName, isSavingName, graphType, onTypeChange, directed, onDirectedChange, onDeleteGraph, isDeletingGraph, }) {
    if (!graph) {
        return (_jsxs("section", { children: [_jsx("h2", { children: "Details" }), _jsx("p", { children: "Select a graph to inspect its nodes and edges." })] }));
    }
    const pendingName = (nameDraft ?? graph.name).trim();
    const pendingType = graphType ?? graph.graph_type ?? "graph";
    const pendingDirected = directed ?? (graph.directed ?? true);
    const segmentSummary = (() => {
        if (!selectedSegment)
            return null;
        const owningEdge = graph.edges.find((edge) => edge.id === selectedSegment.edgeId);
        if (!owningEdge)
            return null;
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
    return (_jsxs("section", { children: [_jsxs("h2", { children: ["Details \u00B7 ", graph.name] }), onNameChange && (_jsxs("form", { onSubmit: (event) => {
                    event.preventDefault();
                    onSaveName?.();
                }, style: { marginBottom: 12 }, children: [_jsxs("label", { style: { display: "flex", flexDirection: "column", gap: 4 }, children: [_jsx("span", { style: { fontSize: 13, color: "#475569" }, children: "Graph name" }), _jsxs("div", { style: { display: "flex", gap: 8 }, children: [_jsx("input", { type: "text", value: nameDraft ?? graph.name, onChange: (event) => onNameChange(event.target.value), style: {
                                            flex: 1,
                                            borderRadius: 6,
                                            border: "1px solid #cbd5f5",
                                            padding: "6px 10px",
                                        }, placeholder: "Workspace name", required: true }), _jsx("button", { type: "submit", disabled: disableSave, style: {
                                            padding: "6px 14px",
                                            borderRadius: 6,
                                            border: "1px solid #2563eb",
                                            background: isSavingName ? "#bfdbfe" : "#2563eb",
                                            color: "#fff",
                                            cursor: disableSave ? "not-allowed" : "pointer",
                                        }, children: "Save" })] })] }), _jsxs("label", { style: { display: "flex", flexDirection: "column", gap: 4, marginTop: 12 }, children: [_jsx("span", { style: { fontSize: 13, color: "#475569" }, children: "Graph type" }), _jsx("select", { value: graphType ?? graph.graph_type ?? "graph", onChange: (event) => onTypeChange?.(event.target.value), style: {
                                    borderRadius: 6,
                                    border: "1px solid #cbd5f5",
                                    padding: "6px 10px",
                                }, children: GRAPH_TYPES.map((type) => (_jsx("option", { value: type, children: type.charAt(0).toUpperCase() + type.slice(1) }, type))) })] }), _jsxs("label", { style: { display: "flex", alignItems: "center", gap: 8, marginTop: 12 }, children: [_jsx("input", { type: "checkbox", checked: directed ?? graph.directed ?? true, onChange: (event) => onDirectedChange?.(event.target.checked) }), "Directed"] })] })), onDeleteGraph && (_jsx("button", { type: "button", onClick: onDeleteGraph, disabled: isDeletingGraph, style: {
                    marginBottom: 12,
                    padding: "6px 14px",
                    borderRadius: 6,
                    border: "1px solid #b91c1c",
                    background: isDeletingGraph ? "#fecaca" : "#fff5f5",
                    color: "#b91c1c",
                    cursor: isDeletingGraph ? "not-allowed" : "pointer",
                }, children: isDeletingGraph ? "Deleting…" : "Delete Graph" })), typeof showGrid === "boolean" && (_jsxs("label", { style: { display: "inline-flex", alignItems: "center", gap: 8, marginBottom: 8 }, children: [_jsx("input", { type: "checkbox", checked: showGrid, onChange: onToggleGrid }), "Show grid"] })), _jsxs("div", { style: {
                    display: "grid",
                    gap: 16,
                    gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
                }, children: [_jsxs("div", { style: {
                            border: "1px solid #d0d7e2",
                            borderRadius: 8,
                            padding: 16,
                            background: "#fff",
                        }, children: [_jsxs("h3", { style: { marginTop: 0 }, children: ["Nodes (", graph.nodes.length, ")"] }), _jsx("ul", { style: { maxHeight: 220, overflow: "auto", paddingLeft: 18, marginBottom: 0 }, children: graph.nodes.map((node) => {
                                    const isSelected = selectedNodeId === node.id;
                                    return (_jsx("li", { style: { marginBottom: 6 }, children: _jsxs("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center" }, children: [_jsxs("div", { children: [_jsx("strong", { children: node.text ?? node.id }), _jsxs("small", { style: { color: "#64748b", marginLeft: 6 }, children: ["(", node.x ?? 0, ", ", node.y ?? 0, ")"] })] }), _jsx("button", { onClick: () => onSelectNode?.(node.id), style: {
                                                        border: "1px solid #2563eb",
                                                        borderRadius: 6,
                                                        padding: "2px 8px",
                                                        background: isSelected ? "#2563eb" : "transparent",
                                                        color: isSelected ? "#fff" : "#2563eb",
                                                        fontSize: 12,
                                                    }, children: isSelected ? "Selected" : "Select" })] }) }, node.id));
                                }) }), segmentSummary && (_jsxs("div", { style: {
                                    marginTop: 12,
                                    padding: 12,
                                    borderRadius: 8,
                                    background: "#f1f5f9",
                                    border: "1px solid #cbd5f5",
                                    fontSize: 13,
                                    color: "#0f172a",
                                }, children: [_jsx("p", { style: { margin: 0, fontWeight: 600, fontSize: 14 }, children: "Selected Segment" }), _jsxs("p", { style: { margin: "4px 0 0" }, children: [_jsx("strong", { children: "Edge:" }), " ", segmentSummary.edgeLabel] }), _jsxs("p", { style: { margin: "2px 0 0" }, children: [_jsx("strong", { children: "Direction:" }), " ", segmentSummary.directionLabel] }), _jsxs("p", { style: { margin: "2px 0 0" }, children: [_jsx("strong", { children: "Member:" }), " ", segmentSummary.memberLabel] })] }))] }), _jsxs("div", { style: {
                            border: "1px solid #d0d7e2",
                            borderRadius: 8,
                            padding: 16,
                            background: "#fff",
                        }, children: [_jsxs("h3", { style: { marginTop: 0 }, children: ["Edges (", graph.edges.length, ")"] }), _jsx("ul", { style: { maxHeight: 220, overflow: "auto", paddingLeft: 18, marginBottom: 0 }, children: graph.edges.map((edge) => {
                                    const isSelected = selectedEdgeId === edge.id;
                                    return (_jsx("li", { style: { marginBottom: 6 }, children: _jsxs("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center" }, children: [_jsxs("div", { children: [edge.source_id, " \u2192 ", edge.target_id, " ", edge.text ? (_jsxs("small", { style: { color: "#64748b" }, children: ["(", edge.text, ")"] })) : null] }), _jsx("button", { onClick: () => onSelectEdge?.(edge.id), style: {
                                                        border: "1px solid #f97316",
                                                        borderRadius: 6,
                                                        padding: "2px 8px",
                                                        background: isSelected ? "#fb923c" : "transparent",
                                                        color: isSelected ? "#fff" : "#c2410c",
                                                        fontSize: 12,
                                                    }, children: isSelected ? "Selected" : "Select" })] }) }, edge.id));
                                }) })] })] })] }));
}
