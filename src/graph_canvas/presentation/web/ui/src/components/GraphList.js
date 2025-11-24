import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
export function GraphList({ graphs, onRefresh, isLoading, onSelect, selectedGraphId, onDelete, deletingGraphId, }) {
    return (_jsxs("section", { children: [_jsxs("header", { style: { display: "flex", justifyContent: "space-between" }, children: [_jsx("h2", { children: "Graphs" }), _jsx("button", { onClick: onRefresh, disabled: isLoading, children: isLoading ? "Refreshing..." : "Refresh" })] }), _jsxs("div", { children: [graphs.length === 0 && _jsx("p", { children: "No graphs yet." }), graphs.map((graph) => (_jsxs("article", { style: {
                            border: "1px solid #d0d7e2",
                            borderRadius: 8,
                            padding: 16,
                            marginBottom: 12,
                            background: graph.id === selectedGraphId ? "#e0e7ff" : "#fff",
                        }, children: [_jsx("h3", { children: graph.name }), _jsxs("small", { children: ["ID: ", graph.id] }), _jsxs("p", { style: { marginBottom: 8 }, children: ["Nodes: ", graph.nodes.length, " \u00B7 Edges: ", graph.edges.length] }), _jsxs("p", { style: { marginTop: 0, color: "#475569" }, children: ["Type: ", graph.graph_type ?? "graph", " \u00B7", " ", graph.directed === false ? "Undirected" : "Directed"] }), _jsx("button", { onClick: () => onSelect(graph), style: {
                                    padding: "4px 12px",
                                    borderRadius: 6,
                                    border: "1px solid #1d4ed8",
                                    background: graph.id === selectedGraphId ? "#1d4ed8" : "transparent",
                                    color: graph.id === selectedGraphId ? "#fff" : "#1d4ed8",
                                }, children: graph.id === selectedGraphId ? "Selected" : "Inspect" }), onDelete && (_jsx("button", { onClick: () => onDelete(graph), disabled: deletingGraphId === graph.id, style: {
                                    marginLeft: 12,
                                    padding: "4px 12px",
                                    borderRadius: 6,
                                    border: "1px solid #b91c1c",
                                    background: deletingGraphId === graph.id ? "#fecaca" : "transparent",
                                    color: "#b91c1c",
                                }, children: deletingGraphId === graph.id ? "Deleting..." : "Delete" }))] }, graph.id)))] })] }));
}
