import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useMemo, useState } from "react";
export const TASK_STATUS_OPTIONS = [
    { value: "started", label: "Started", color: "#f97316" },
    { value: "in_progress", label: "In Progress", color: "#0ea5e9" },
    { value: "blocked", label: "Blocked", color: "#b91c1c" },
    { value: "complete", label: "Complete", color: "#16a34a" },
];
export function GraphTaskList({ graph, selectedNodeId, onSelectNode, onStatusChange, onDeleteNode, onCreateTask, onEditTask, }) {
    const tasks = useMemo(() => deriveTaskRows(graph), [graph]);
    const readyCount = tasks.filter((task) => task.status === "ready").length;
    const blockedStatusCount = tasks.filter((task) => readTaskStatus(task.node) === "blocked").length;
    const [modalState, setModalState] = useState(null);
    const [isSavingModal, setIsSavingModal] = useState(false);
    const handleSubmitModal = async (payload) => {
        if (!modalState)
            return;
        setIsSavingModal(true);
        try {
            if (modalState.mode === "create") {
                await onCreateTask(payload);
            }
            else {
                await onEditTask(modalState.nodeId, payload);
            }
            setModalState(null);
        }
        finally {
            setIsSavingModal(false);
        }
    };
    if (!graph) {
        return (_jsxs("section", { style: {
                border: "1px solid #e2e8f0",
                borderRadius: 16,
                padding: 32,
                background: "#fff",
                boxShadow: "0 1px 3px rgba(15, 23, 42, 0.08)",
            }, children: [_jsx("h2", { style: { margin: 0, fontSize: 20, color: "#0f172a" }, children: "Dependency List" }), _jsx("p", { style: { marginTop: 8, color: "#475569" }, children: "Select a graph to see its tasks ordered by dependency." })] }));
    }
    if (graph.nodes.length === 0) {
        return (_jsxs("section", { style: {
                border: "1px solid #e2e8f0",
                borderRadius: 16,
                padding: 32,
                background: "#fff",
                boxShadow: "0 1px 3px rgba(15, 23, 42, 0.08)",
            }, children: [_jsx("h2", { style: { margin: 0, fontSize: 20, color: "#0f172a" }, children: "Dependency List" }), _jsx("p", { style: { marginTop: 8, color: "#475569" }, children: "This graph does not have any nodes yet. Add a node to start building the task list." })] }));
    }
    return (_jsxs("section", { style: {
            border: "1px solid #e2e8f0",
            borderRadius: 16,
            padding: 24,
            background: "#fff",
            boxShadow: "0 1px 3px rgba(15, 23, 42, 0.08)",
        }, children: [_jsxs("header", { style: {
                    display: "flex",
                    flexWrap: "wrap",
                    gap: 12,
                    alignItems: "center",
                    justifyContent: "space-between",
                }, children: [_jsxs("div", { children: [_jsx("p", { style: { margin: 0, fontSize: 13, letterSpacing: 1, color: "#94a3b8" }, children: "DEPENDENCY LIST" }), _jsx("h2", { style: { margin: "4px 0 0", color: "#0f172a" }, children: graph.name }), _jsxs("p", { style: { margin: "4px 0 0", color: "#475569" }, children: ["Ordered automatically from ", graph.edges.length, " ", graph.edges.length === 1 ? "dependency" : "dependencies", "."] })] }), _jsxs("div", { style: { display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }, children: [_jsx(Badge, { label: "Ready", value: readyCount, tone: "#0f172a" }), _jsx(Badge, { label: "Blocked", value: blockedStatusCount, tone: "#b91c1c" }), _jsx("button", { type: "button", onClick: () => setModalState({ mode: "create" }), style: {
                                    marginLeft: "auto",
                                    borderRadius: 999,
                                    border: "1px solid #2563eb",
                                    background: "#2563eb",
                                    color: "#fff",
                                    padding: "6px 16px",
                                    fontWeight: 600,
                                    cursor: graph ? "pointer" : "not-allowed",
                                }, disabled: !graph, children: "Add Task" })] })] }), _jsx("ol", { style: {
                    listStyle: "none",
                    margin: "20px 0 0",
                    padding: 0,
                    display: "flex",
                    flexDirection: "column",
                    gap: 12,
                }, children: tasks.map((task) => {
                    const label = formatNodeLabel(task.node);
                    const isSelected = selectedNodeId === task.node.id;
                    const taskStatus = readTaskStatus(task.node);
                    return (_jsx("li", { children: _jsxs("button", { type: "button", onClick: () => onSelectNode(task.node.id), style: {
                                width: "100%",
                                textAlign: "left",
                                borderRadius: 12,
                                border: isSelected ? "2px solid #2563eb" : "1px solid #e2e8f0",
                                background: isSelected ? "#dbeafe" : "#f8fafc",
                                padding: "16px 18px",
                                cursor: "pointer",
                                display: "flex",
                                gap: 16,
                                alignItems: "flex-start",
                            }, children: [_jsx("div", { style: {
                                        minWidth: 48,
                                        height: 48,
                                        borderRadius: 12,
                                        border: "1px solid #cbd5f5",
                                        background: "#fff",
                                        display: "flex",
                                        alignItems: "center",
                                        justifyContent: "center",
                                        fontSize: 18,
                                        fontWeight: 600,
                                        color: "#0f172a",
                                    }, children: task.order ?? "—" }), _jsxs("div", { style: { flex: 1 }, children: [_jsxs("div", { style: {
                                                display: "flex",
                                                alignItems: "center",
                                                gap: 8,
                                                flexWrap: "wrap",
                                            }, children: [_jsxs("div", { style: { display: "flex", alignItems: "center", gap: 8 }, children: [_jsx("p", { style: {
                                                                margin: 0,
                                                                fontSize: 16,
                                                                fontWeight: 600,
                                                                color: "#0f172a",
                                                            }, children: label }), taskStatus && (_jsx(StatusBadge, { color: TASK_STATUS_OPTIONS.find((option) => option.value === taskStatus)
                                                                ?.color ?? "#0f172a", label: TASK_STATUS_OPTIONS.find((option) => option.value === taskStatus)
                                                                ?.label ?? taskStatus }))] }), task.status === "blocked" && (_jsx("span", { style: {
                                                        fontSize: 12,
                                                        padding: "2px 8px",
                                                        borderRadius: 999,
                                                        background: "#fee2e2",
                                                        color: "#b91c1c",
                                                        border: "1px solid #fecaca",
                                                    }, children: "Resolve cycle" }))] }), _jsx("p", { style: { margin: "6px 0 0", color: "#475569", fontSize: 14 }, children: task.prerequisites.length === 0
                                                ? "No prerequisites"
                                                : `Depends on ${task.prerequisites
                                                    .map((node) => formatNodeLabel(node))
                                                    .join(", ")}` }), _jsxs("div", { style: {
                                                marginTop: 8,
                                                display: "flex",
                                                flexWrap: "wrap",
                                                gap: 8,
                                                fontSize: 13,
                                                color: "#475569",
                                            }, children: [_jsxs("span", { children: ["Unblocks", " ", _jsx("strong", { style: { color: "#0f172a" }, children: task.dependents.length }), " ", "task", task.dependents.length === 1 ? "" : "s"] }), task.dependents.length > 0 && (_jsxs("span", { style: { color: "#94a3b8" }, children: ["Next: ", formatNodeLabel(task.dependents[0]), task.dependents.length > 1 ? " +" : ""] }))] }), _jsxs("div", { style: {
                                                marginTop: 12,
                                                display: "flex",
                                                flexWrap: "wrap",
                                                gap: 12,
                                                alignItems: "center",
                                                justifyContent: "space-between",
                                            }, onClick: (event) => event.stopPropagation(), children: [_jsxs("div", { style: {
                                                        display: "flex",
                                                        gap: 8,
                                                        flexWrap: "wrap",
                                                        alignItems: "center",
                                                    }, children: [_jsx("span", { style: { fontSize: 13, color: "#94a3b8" }, children: "Status:" }), _jsx("div", { style: {
                                                                display: "flex",
                                                                gap: 6,
                                                                background: "#e2e8f0",
                                                                padding: 4,
                                                                borderRadius: 999,
                                                            }, children: TASK_STATUS_OPTIONS.map((option) => {
                                                                const active = taskStatus === option.value;
                                                                return (_jsx("button", { type: "button", onClick: () => onStatusChange(task.node.id, active ? null : option.value), style: {
                                                                        border: "none",
                                                                        borderRadius: 999,
                                                                        padding: "6px 14px",
                                                                        fontSize: 13,
                                                                        fontWeight: 600,
                                                                        cursor: "pointer",
                                                                        background: active ? option.color : "transparent",
                                                                        color: active ? "#fff" : "#0f172a",
                                                                    }, children: option.label }, option.value));
                                                            }) })] }), _jsxs("div", { style: { display: "flex", gap: 8 }, children: [_jsx("button", { type: "button", onClick: (event) => {
                                                                event.stopPropagation();
                                                                setModalState({ mode: "edit", nodeId: task.node.id });
                                                            }, style: {
                                                                borderRadius: 999,
                                                                border: "1px solid #0f172a",
                                                                background: "#fff",
                                                                color: "#0f172a",
                                                                padding: "6px 12px",
                                                                fontSize: 13,
                                                                fontWeight: 600,
                                                                cursor: "pointer",
                                                            }, children: "Edit" }), _jsx("button", { type: "button", onClick: () => {
                                                                const ok = typeof window === "undefined"
                                                                    ? true
                                                                    : window.confirm(`Delete "${formatNodeLabel(task.node)}" from this graph?`);
                                                                if (ok) {
                                                                    onDeleteNode(task.node.id);
                                                                }
                                                            }, style: {
                                                                borderRadius: 999,
                                                                border: "1px solid #b91c1c",
                                                                background: "#fff",
                                                                color: "#b91c1c",
                                                                padding: "6px 12px",
                                                                fontSize: 13,
                                                                fontWeight: 600,
                                                                cursor: "pointer",
                                                            }, children: "Delete" })] })] })] })] }) }, task.node.id));
                }) }), modalState && graph && (_jsx(TaskDialog, { mode: modalState.mode, node: modalState.mode === "edit"
                    ? graph.nodes.find((candidate) => candidate.id === modalState.nodeId) ?? null
                    : null, nodes: graph.nodes, edges: graph.edges, isSaving: isSavingModal, onCancel: () => {
                    if (!isSavingModal) {
                        setModalState(null);
                    }
                }, onSubmit: (payload) => void handleSubmitModal(payload) }))] }));
}
// Builds a topologically sorted view (with best-effort fallbacks for cycles) so we can render
// a human-friendly “ready vs blocked” task list without reimplementing the same logic inline.
function deriveTaskRows(graph) {
    if (!graph || graph.nodes.length === 0) {
        return [];
    }
    const nodeMap = new Map();
    graph.nodes.forEach((node) => nodeMap.set(node.id, node));
    const prerequisiteMap = new Map();
    const dependentsMap = new Map();
    nodeMap.forEach((_, id) => {
        prerequisiteMap.set(id, new Set());
        dependentsMap.set(id, new Set());
    });
    const registerDependency = (sourceId, targetId) => {
        if (sourceId === targetId)
            return;
        const sourceNode = nodeMap.get(sourceId);
        const targetNode = nodeMap.get(targetId);
        if (!sourceNode || !targetNode) {
            return;
        }
        prerequisiteMap.get(targetId)?.add(sourceId);
        dependentsMap.get(sourceId)?.add(targetId);
    };
    const gatherMembers = (edge, key) => {
        const singularKey = key === "source" ? "source_id" : "target_id";
        const pluralKey = key === "source" ? "source_ids" : "target_ids";
        const ids = new Set();
        const singular = edge[singularKey];
        if (typeof singular === "string" && nodeMap.has(singular)) {
            ids.add(singular);
        }
        const plural = edge[pluralKey];
        if (Array.isArray(plural)) {
            plural.forEach((value) => {
                if (typeof value === "string" && nodeMap.has(value)) {
                    ids.add(value);
                }
            });
        }
        return Array.from(ids);
    };
    graph.edges.forEach((edge) => {
        const sources = gatherMembers(edge, "source");
        const targets = gatherMembers(edge, "target");
        sources.forEach((sourceId) => {
            targets.forEach((targetId) => {
                registerDependency(sourceId, targetId);
            });
        });
    });
    const originalPrereqs = new Map();
    prerequisiteMap.forEach((value, id) => {
        originalPrereqs.set(id, Array.from(value));
    });
    const originalDependents = new Map();
    dependentsMap.forEach((value, id) => {
        originalDependents.set(id, Array.from(value));
    });
    const compareByLayout = (aId, bId) => compareNodes(nodeMap.get(aId), nodeMap.get(bId));
    const ready = Array.from(nodeMap.keys()).filter((id) => (prerequisiteMap.get(id)?.size ?? 0) === 0);
    ready.sort(compareByLayout);
    const visited = new Set();
    const ordered = [];
    while (ready.length > 0) {
        const currentId = ready.shift();
        if (visited.has(currentId)) {
            continue;
        }
        visited.add(currentId);
        ordered.push({
            node: nodeMap.get(currentId),
            order: ordered.length + 1,
            prerequisites: (originalPrereqs.get(currentId) ?? [])
                .map((id) => nodeMap.get(id))
                .filter(Boolean),
            dependents: (originalDependents.get(currentId) ?? [])
                .map((id) => nodeMap.get(id))
                .filter(Boolean),
            status: "ready",
        });
        dependentsMap.get(currentId)?.forEach((dependentId) => {
            const prereqs = prerequisiteMap.get(dependentId);
            if (!prereqs)
                return;
            prereqs.delete(currentId);
            if (prereqs.size === 0 && !visited.has(dependentId)) {
                ready.push(dependentId);
                ready.sort(compareByLayout);
            }
        });
    }
    const blocked = [];
    nodeMap.forEach((node, id) => {
        if (visited.has(id)) {
            return;
        }
        blocked.push({
            node,
            order: null,
            prerequisites: (originalPrereqs.get(id) ?? [])
                .map((depId) => nodeMap.get(depId))
                .filter(Boolean),
            dependents: (originalDependents.get(id) ?? [])
                .map((depId) => nodeMap.get(depId))
                .filter(Boolean),
            status: "blocked",
        });
    });
    blocked.sort((a, b) => compareNodes(a.node, b.node));
    return [...ordered, ...blocked];
}
function compareNodes(a, b) {
    if (!a || !b)
        return 0;
    const orderA = readNumericMetadata(a, "order");
    const orderB = readNumericMetadata(b, "order");
    if (orderA !== null && orderB !== null && orderA !== orderB) {
        return orderA - orderB;
    }
    if (orderA !== null && orderB === null) {
        return -1;
    }
    if (orderA === null && orderB !== null) {
        return 1;
    }
    const yA = typeof a.y === "number" ? a.y : Number.MAX_SAFE_INTEGER;
    const yB = typeof b.y === "number" ? b.y : Number.MAX_SAFE_INTEGER;
    if (yA !== yB) {
        return yA - yB;
    }
    const textA = (a.text ?? "").toLowerCase();
    const textB = (b.text ?? "").toLowerCase();
    if (textA && textB && textA !== textB) {
        return textA.localeCompare(textB);
    }
    return a.id.localeCompare(b.id);
}
function readNumericMetadata(node, key) {
    const metadata = node.metadata;
    const value = metadata?.[key];
    return typeof value === "number" ? value : null;
}
function formatNodeLabel(node) {
    if (!node) {
        return "Unknown";
    }
    const text = node.text?.trim();
    if (text) {
        return text;
    }
    const metadata = node.metadata;
    const fallback = typeof metadata?.label === "string"
        ? metadata.label
        : typeof metadata?.name === "string"
            ? metadata.name
            : null;
    return fallback ?? node.id;
}
function TaskDialog({ mode, node, nodes, edges, onSubmit, onCancel, isSaving, }) {
    const [label, setLabel] = useState(node?.text ?? "");
    const availableNodes = useMemo(() => nodes.filter((candidate) => !node || candidate.id !== node.id), [nodes, node]);
    const initialPrereqs = useMemo(() => {
        if (!node)
            return new Set();
        return new Set(edges.filter((edge) => edge.target_id === node.id).map((edge) => edge.source_id));
    }, [edges, node]);
    const initialPosts = useMemo(() => {
        if (!node)
            return new Set();
        return new Set(edges.filter((edge) => edge.source_id === node.id).map((edge) => edge.target_id));
    }, [edges, node]);
    const [selectedPrereqs, setSelectedPrereqs] = useState(initialPrereqs);
    const [selectedPosts, setSelectedPosts] = useState(initialPosts);
    const toggleSetValue = (current, setFn, value) => {
        const next = new Set(current);
        if (next.has(value)) {
            next.delete(value);
        }
        else {
            next.add(value);
        }
        setFn(next);
    };
    const handleSubmit = (event) => {
        event.preventDefault();
        const trimmed = label.trim();
        if (!trimmed) {
            window.alert("Task label is required.");
            return;
        }
        onSubmit({
            label: trimmed,
            prereqIds: Array.from(selectedPrereqs),
            postIds: Array.from(selectedPosts),
        });
    };
    return (_jsx("div", { style: {
            position: "fixed",
            inset: 0,
            background: "rgba(15,23,42,0.55)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 50,
        }, children: _jsxs("form", { onSubmit: handleSubmit, style: {
                width: "min(520px, 92vw)",
                maxHeight: "90vh",
                overflow: "auto",
                background: "#fff",
                borderRadius: 16,
                padding: 24,
                boxShadow: "0 25px 50px rgba(15,23,42,0.35)",
                display: "flex",
                flexDirection: "column",
                gap: 16,
            }, children: [_jsxs("div", { children: [_jsx("h3", { style: { margin: 0, color: "#0f172a" }, children: mode === "create" ? "Add Dependency Task" : "Edit Dependency Task" }), _jsx("p", { style: { margin: "4px 0 0", color: "#475569" }, children: "Configure the label along with prerequisite and postrequisite nodes." })] }), _jsxs("label", { style: { display: "flex", flexDirection: "column", gap: 6, color: "#0f172a" }, children: [_jsx("span", { children: "Label" }), _jsx("input", { value: label, onChange: (event) => setLabel(event.target.value), style: {
                                padding: "8px 12px",
                                border: "1px solid #cbd5f5",
                                borderRadius: 8,
                                fontSize: 15,
                            }, disabled: isSaving })] }), _jsxs("div", { children: [_jsx("p", { style: { marginBottom: 8, color: "#0f172a", fontWeight: 600 }, children: "Prerequisites" }), _jsxs("div", { style: {
                                maxHeight: 180,
                                overflowY: "auto",
                                border: "1px solid #e2e8f0",
                                borderRadius: 12,
                                padding: 12,
                                display: "grid",
                                gap: 8,
                            }, children: [availableNodes.length === 0 && (_jsx("p", { style: { margin: 0, color: "#94a3b8", fontSize: 13 }, children: "No other nodes available." })), availableNodes.map((candidate) => (_jsxs("label", { style: { display: "flex", gap: 8, fontSize: 14, color: "#0f172a" }, children: [_jsx("input", { type: "checkbox", checked: selectedPrereqs.has(candidate.id), onChange: () => toggleSetValue(selectedPrereqs, setSelectedPrereqs, candidate.id), disabled: isSaving }), _jsx("span", { children: formatNodeLabel(candidate) })] }, candidate.id)))] })] }), _jsxs("div", { children: [_jsx("p", { style: { marginBottom: 8, color: "#0f172a", fontWeight: 600 }, children: "Postrequisites" }), _jsxs("div", { style: {
                                maxHeight: 180,
                                overflowY: "auto",
                                border: "1px solid #e2e8f0",
                                borderRadius: 12,
                                padding: 12,
                                display: "grid",
                                gap: 8,
                            }, children: [availableNodes.length === 0 && (_jsx("p", { style: { margin: 0, color: "#94a3b8", fontSize: 13 }, children: "No other nodes available." })), availableNodes.map((candidate) => (_jsxs("label", { style: { display: "flex", gap: 8, fontSize: 14, color: "#0f172a" }, children: [_jsx("input", { type: "checkbox", checked: selectedPosts.has(candidate.id), onChange: () => toggleSetValue(selectedPosts, setSelectedPosts, candidate.id), disabled: isSaving }), _jsx("span", { children: formatNodeLabel(candidate) })] }, candidate.id)))] })] }), _jsxs("div", { style: { display: "flex", justifyContent: "flex-end", gap: 12 }, children: [_jsx("button", { type: "button", onClick: onCancel, disabled: isSaving, style: {
                                borderRadius: 8,
                                border: "1px solid #cbd5f5",
                                background: "#fff",
                                padding: "8px 16px",
                                fontWeight: 600,
                                color: "#0f172a",
                                cursor: isSaving ? "not-allowed" : "pointer",
                            }, children: "Cancel" }), _jsx("button", { type: "submit", disabled: isSaving, style: {
                                borderRadius: 8,
                                border: "1px solid #2563eb",
                                background: "#2563eb",
                                padding: "8px 16px",
                                fontWeight: 600,
                                color: "#fff",
                                cursor: isSaving ? "not-allowed" : "pointer",
                            }, children: isSaving ? "Saving..." : "Save" })] })] }) }));
}
function readTaskStatus(node) {
    const metadata = node.metadata;
    const status = metadata?.status;
    if (typeof status === "string" &&
        TASK_STATUS_OPTIONS.some((option) => option.value === status)) {
        return status;
    }
    return null;
}
function StatusBadge({ color, label }) {
    return (_jsx("span", { style: {
            borderRadius: 999,
            padding: "2px 8px",
            fontSize: 12,
            fontWeight: 600,
            background: `${color}22`,
            color,
            border: `1px solid ${color}55`,
        }, children: label }));
}
function Badge({ label, value, tone, }) {
    return (_jsxs("div", { style: {
            borderRadius: 12,
            border: `1px solid ${tone}22`,
            padding: "6px 14px",
            minWidth: 90,
            textAlign: "center",
            background: "#f8fafc",
        }, children: [_jsx("p", { style: { margin: 0, fontSize: 12, color: "#94a3b8", letterSpacing: 1 }, children: label.toUpperCase() }), _jsx("p", { style: { margin: 0, fontSize: 18, fontWeight: 600, color: tone }, children: value })] }));
}
