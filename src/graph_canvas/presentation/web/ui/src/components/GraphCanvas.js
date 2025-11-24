import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
const CANVAS_HEIGHT = 520;
const GRID_EXTENT = 8000;
export function GraphCanvas({ graph, selectedNodeId, selectedEdgeId, selectedSegment, selectedEdgeScope = "none", onSelectNode, onSelectEdge, onSelectSegment, onEdgeScopeChange, onNodePositionChange, onCanvasAddNode, onConnectNodes, onReconnectEdge, onAttachEdgeMember, showGrid: showGridProp, gridColor: gridColorProp, gridSpacing: gridSpacingProp, gridThickness: gridThicknessProp, backgroundColor: backgroundColorProp, isFullscreen = false, onToggleFullscreen, }) {
    const svgRef = useRef(null);
    const [pan, setPan] = useState({ x: 0, y: 0 });
    const [zoom, setZoom] = useState(1);
    const [dragState, setDragState] = useState(null);
    const [localNodes, setLocalNodes] = useState({});
    const fallbackHex = (arr) => {
        if (!arr || arr.length < 3) {
            return undefined;
        }
        return `#${arr
            .slice(0, 3)
            .map((value) => Math.max(0, Math.min(255, value)).toString(16).padStart(2, "0"))
            .join("")}`;
    };
    const effectiveShowGrid = showGridProp ?? graph?.grid_visible ?? true;
    const effectiveGridColor = gridColorProp ?? fallbackHex(graph?.grid_color) ?? "#e2e8f0";
    const effectiveBackgroundColor = backgroundColorProp ?? fallbackHex(graph?.background_color) ?? "#f8fafc";
    const selectionGlowId = useMemo(() => `edge-selection-${Math.random().toString(36).slice(2)}`, []);
    const effectiveGridSpacing = Math.max(5, gridSpacingProp ?? graph?.grid_size ?? 20);
    useEffect(() => {
        if (!isFullscreen) {
            return;
        }
        const handleEsc = (event) => {
            if (event.key === "Escape") {
                onToggleFullscreen?.();
            }
        };
        window.addEventListener("keydown", handleEsc);
        return () => window.removeEventListener("keydown", handleEsc);
    }, [isFullscreen, onToggleFullscreen]);
    const effectiveThickness = Math.max(0.5, gridThicknessProp ?? graph?.grid_line_thickness ?? 1);
    useEffect(() => {
        if (!graph) {
            setLocalNodes({});
            return;
        }
        const map = {};
        graph.nodes.forEach((node) => {
            map[node.id] = node;
        });
        setLocalNodes(map);
    }, [graph?.id, graph?.nodes]);
    useEffect(() => {
        if (!graph || graph.nodes.length === 0) {
            return;
        }
        const xs = graph.nodes.map((node) => node.x ?? 0);
        const ys = graph.nodes.map((node) => node.y ?? 0);
        const minX = Math.min(...xs);
        const minY = Math.min(...ys);
        const maxX = Math.max(...xs);
        const maxY = Math.max(...ys);
        const centerX = (minX + maxX) / 2;
        const centerY = (minY + maxY) / 2;
        const width = svgRef.current?.clientWidth ?? 900;
        setPan({
            x: width / 2 - centerX * zoom,
            y: CANVAS_HEIGHT / 2 - centerY * zoom,
        });
    }, [graph?.id]);
    const renderedNodes = useMemo(() => {
        if (!graph) {
            return [];
        }
        return graph.nodes.map((node) => localNodes[node.id] ?? node);
    }, [graph, localNodes]);
    const nodePositionMap = useMemo(() => {
        const map = {};
        renderedNodes.forEach((node) => {
            map[node.id] = { x: node.x ?? 0, y: node.y ?? 0 };
        });
        return map;
    }, [renderedNodes]);
    // Cache all edge midpoints so selection hit-tests and drag previews can reuse a single lookup.
    const edgeMidpoints = useMemo(() => {
        if (!graph)
            return {};
        const map = {};
        graph.edges.forEach((edge) => {
            const source = nodePositionMap[edge.source_id];
            const target = nodePositionMap[edge.target_id];
            if (source && target) {
                map[edge.id] = {
                    x: (source.x + target.x) / 2,
                    y: (source.y + target.y) / 2,
                };
            }
        });
        return map;
    }, [graph?.edges, nodePositionMap]);
    const toWorld = useCallback((clientX, clientY) => {
        const rect = svgRef.current?.getBoundingClientRect();
        if (!rect) {
            return { x: 0, y: 0 };
        }
        return {
            x: (clientX - rect.left - pan.x) / zoom,
            y: (clientY - rect.top - pan.y) / zoom,
        };
    }, [pan, zoom]);
    const handlePointerDown = (event) => {
        // All pointer interactions funnel through this gate so we can decide early whether to pan,
        // start a drag, or simply let the click bubble to a selection handler.
        if (!graph) {
            return;
        }
        const target = event.target;
        const nodeHandleId = target.getAttribute("data-node-handle");
        const edgeHandleAttr = target.getAttribute("data-edge-handle");
        const hyperHandleAttr = target.getAttribute("data-hyper-handle");
        const hyperSegmentAttr = target.getAttribute("data-hyper-segment");
        const edgeHitAttr = target.getAttribute("data-edge-hit");
        const nodeId = target.dataset.nodeId;
        const edgeId = target.dataset.edgeId;
        if (hyperSegmentAttr || edgeHitAttr) {
            // Let click handlers handle selection without initiating drag/pan.
            return;
        }
        if (nodeHandleId) {
            if (!onConnectNodes) {
                return;
            }
            const node = localNodes[nodeHandleId] ?? graph.nodes.find((n) => n.id === nodeHandleId);
            if (!node)
                return;
            onSelectNode?.(nodeHandleId);
            onSelectSegment?.(null);
            const anchorPos = { x: node.x ?? 0, y: node.y ?? 0 };
            setDragState({
                type: "edge",
                pointerId: event.pointerId,
                mode: "new",
                dragNodeId: nodeHandleId,
                anchorNodeId: nodeHandleId,
                anchorPos,
                currentPos: anchorPos,
                hoverTargetId: undefined,
            });
            event.currentTarget.setPointerCapture(event.pointerId);
            return;
        }
        if (edgeHandleAttr) {
            if (!onReconnectEdge) {
                return;
            }
            const [dragEdgeId, anchor] = edgeHandleAttr.split(":");
            const edge = graph.edges.find((item) => item.id === dragEdgeId);
            if (!edge)
                return;
            const sourceNode = renderedNodes.find((node) => node.id === edge.source_id) ??
                graph.nodes.find((node) => node.id === edge.source_id);
            const targetNode = renderedNodes.find((node) => node.id === edge.target_id) ??
                graph.nodes.find((node) => node.id === edge.target_id);
            if (!sourceNode || !targetNode)
                return;
            const isSourceHandle = anchor === "source";
            const fixedNode = isSourceHandle ? targetNode : sourceNode;
            const dragNode = isSourceHandle ? sourceNode : targetNode;
            setDragState({
                type: "edge",
                pointerId: event.pointerId,
                mode: isSourceHandle ? "rewire-source" : "rewire-target",
                edgeId: dragEdgeId,
                dragNodeId: isSourceHandle ? edge.source_id : edge.target_id,
                anchorNodeId: fixedNode.id,
                anchorPos: { x: fixedNode.x ?? 0, y: fixedNode.y ?? 0 },
                currentPos: { x: dragNode.x ?? 0, y: dragNode.y ?? 0 },
                hoverTargetId: undefined,
            });
            event.currentTarget.setPointerCapture(event.pointerId);
            return;
        }
        if (hyperHandleAttr) {
            if (!onAttachEdgeMember) {
                return;
            }
            const [edgeRef, role] = hyperHandleAttr.split(":");
            const anchorX = Number(target.getAttribute("data-anchor-x")) || 0;
            const anchorY = Number(target.getAttribute("data-anchor-y")) || 0;
            const allowEdges = target.getAttribute("data-allow-edge-targets") === "true";
            if (!edgeRef) {
                return;
            }
            setDragState({
                type: "edge",
                pointerId: event.pointerId,
                mode: role === "head" ? "attach-head" : "attach-tail",
                edgeId: edgeRef,
                dragNodeId: edgeRef,
                anchorNodeId: edgeRef,
                anchorPos: { x: anchorX, y: anchorY },
                currentPos: { x: anchorX, y: anchorY },
                hoverTargetId: undefined,
                hoverEdgeId: undefined,
                allowEdgeTargets: allowEdges,
            });
            event.currentTarget.setPointerCapture(event.pointerId);
            return;
        }
        if (edgeId) {
            onSelectEdge?.(edgeId);
            onSelectNode?.(null);
            onSelectSegment?.(null);
            onEdgeScopeChange?.("whole");
            return;
        }
        if (nodeId) {
            const node = localNodes[nodeId] ?? graph.nodes.find((n) => n.id === nodeId);
            if (!node)
                return;
            onSelectNode?.(nodeId);
            onSelectSegment?.(null);
            setDragState({
                type: "node",
                pointerId: event.pointerId,
                nodeId,
                originX: event.clientX,
                originY: event.clientY,
                startNode: {
                    x: node.x ?? 0,
                    y: node.y ?? 0,
                },
                moved: false,
            });
            event.currentTarget.setPointerCapture(event.pointerId);
            return;
        }
        if (event.detail === 2) {
            return;
        }
        setDragState({
            type: "pan",
            pointerId: event.pointerId,
            originX: event.clientX,
            originY: event.clientY,
            startPan: pan,
        });
        event.currentTarget.setPointerCapture(event.pointerId);
    };
    const handlePointerMove = (event) => {
        if (!dragState) {
            return;
        }
        if (dragState.type === "pan") {
            setPan({
                x: dragState.startPan.x + (event.clientX - dragState.originX),
                y: dragState.startPan.y + (event.clientY - dragState.originY),
            });
            return;
        }
        if (dragState.type === "node") {
            event.preventDefault();
            const dx = (event.clientX - dragState.originX) / zoom;
            const dy = (event.clientY - dragState.originY) / zoom;
            const newX = dragState.startNode.x + dx;
            const newY = dragState.startNode.y + dy;
            setLocalNodes((prev) => {
                const current = prev[dragState.nodeId] ??
                    graph?.nodes.find((node) => node.id === dragState.nodeId);
                if (!current) {
                    return prev;
                }
                return {
                    ...prev,
                    [dragState.nodeId]: {
                        ...current,
                        x: newX,
                        y: newY,
                    },
                };
            });
            setDragState({
                ...dragState,
                moved: true,
            });
            return;
        }
        if (dragState.type === "edge") {
            event.preventDefault();
            const world = toWorld(event.clientX, event.clientY);
            const hovered = renderedNodes.find((node) => {
                if (node.id === dragState.dragNodeId)
                    return false;
                const dx = (node.x ?? 0) - world.x;
                const dy = (node.y ?? 0) - world.y;
                return Math.hypot(dx, dy) < 28;
            }) ?? null;
            let hoveredEdgeId;
            if (dragState.allowEdgeTargets) {
                let bestId;
                let bestDist = Number.POSITIVE_INFINITY;
                Object.entries(edgeMidpoints).forEach(([edgeId, pos]) => {
                    if (edgeId === dragState.edgeId) {
                        return;
                    }
                    const dx = pos.x - world.x;
                    const dy = pos.y - world.y;
                    const dist = Math.hypot(dx, dy);
                    if (dist < 30 && dist < bestDist) {
                        bestDist = dist;
                        bestId = edgeId;
                    }
                });
                hoveredEdgeId = bestId;
            }
            setDragState((prev) => {
                if (!prev || prev.type !== "edge") {
                    return prev;
                }
                return {
                    ...prev,
                    currentPos: world,
                    hoverTargetId: hovered?.id,
                    hoverEdgeId: hoveredEdgeId && hoveredEdgeId !== prev.edgeId ? hoveredEdgeId : undefined,
                };
            });
        }
    };
    const handlePointerUp = (event) => {
        if (!dragState) {
            return;
        }
        const releasePointer = () => {
            if (event.currentTarget.hasPointerCapture(event.pointerId)) {
                event.currentTarget.releasePointerCapture(event.pointerId);
            }
            setDragState(null);
        };
        if (dragState.type === "node") {
            if (dragState.moved) {
                const node = localNodes[dragState.nodeId];
                if (node && typeof node.x === "number" && typeof node.y === "number") {
                    onNodePositionChange?.(dragState.nodeId, node.x, node.y);
                }
            }
            releasePointer();
            return;
        }
        if (dragState.type === "edge") {
            const world = toWorld(event.clientX, event.clientY);
            const fallbackTarget = renderedNodes.find((node) => {
                if (node.id === dragState.dragNodeId)
                    return false;
                const dx = (node.x ?? 0) - world.x;
                const dy = (node.y ?? 0) - world.y;
                return Math.hypot(dx, dy) < 28;
            }) ?? null;
            if (dragState.mode === "attach-head" || dragState.mode === "attach-tail") {
                if (dragState.edgeId && onAttachEdgeMember) {
                    const targetNodeId = dragState.hoverTargetId ?? fallbackTarget?.id;
                    const targetEdgeId = dragState.allowEdgeTargets && dragState.hoverEdgeId
                        ? dragState.hoverEdgeId
                        : undefined;
                    if (targetNodeId || targetEdgeId) {
                        const maybe = onAttachEdgeMember(dragState.edgeId, {
                            kind: dragState.mode === "attach-head" ? "head" : "tail",
                            targetNodeId: targetNodeId ?? undefined,
                            targetEdgeId: targetEdgeId,
                        });
                        if (maybe && typeof maybe.then === "function") {
                            maybe.catch(() => undefined);
                        }
                    }
                }
                releasePointer();
                return;
            }
            const targetId = dragState.hoverTargetId ?? fallbackTarget?.id;
            if (targetId &&
                targetId !== dragState.dragNodeId &&
                (dragState.mode === "new" ? targetId !== dragState.anchorNodeId : true)) {
                let maybe = undefined;
                if (dragState.mode === "new") {
                    maybe = onConnectNodes?.(dragState.anchorNodeId, targetId);
                }
                else if (dragState.mode === "rewire-source" && dragState.edgeId) {
                    maybe = onReconnectEdge?.(dragState.edgeId, { source_id: targetId });
                }
                else if (dragState.mode === "rewire-target" && dragState.edgeId) {
                    maybe = onReconnectEdge?.(dragState.edgeId, { target_id: targetId });
                }
                if (maybe && typeof maybe.then === "function") {
                    maybe.catch(() => undefined);
                }
            }
            releasePointer();
            return;
        }
        releasePointer();
    };
    const handleWheel = (event) => {
        event.preventDefault();
        const direction = event.deltaY > 0 ? 0.9 : 1.1;
        setZoom((prev) => {
            const next = Math.min(4, Math.max(0.25, prev * direction));
            return next;
        });
    };
    const handleDoubleClick = (event) => {
        if (!graph)
            return;
        event.preventDefault();
        const world = toWorld(event.clientX, event.clientY);
        const result = onCanvasAddNode?.(world.x, world.y);
        if (!result) {
            return;
        }
        if (typeof result.then === "function") {
            result
                .then((node) => {
                if (node) {
                    setLocalNodes((prev) => ({ ...prev, [node.id]: node }));
                }
            })
                .catch(() => undefined);
        }
        else if (typeof result === "object") {
            const node = result;
            if (node.id) {
                setLocalNodes((prev) => ({ ...prev, [node.id]: node }));
            }
        }
    };
    const gridPatternId = useMemo(() => `grid-${Math.round(effectiveGridSpacing)}-${effectiveGridColor.replace(/[^0-9a-z]/gi, "")}`, [effectiveGridSpacing, effectiveGridColor]);
    const canvasHeight = isFullscreen ? "100%" : CANVAS_HEIGHT;
    const sectionStyle = isFullscreen
        ? {
            position: "fixed",
            inset: 0,
            zIndex: 30,
            padding: "1.5rem",
            background: "rgba(15, 23, 42, 0.92)",
            boxSizing: "border-box",
            display: "flex",
            flexDirection: "column",
            gap: "0.75rem",
        }
        : {
            position: "relative",
            display: "flex",
            flexDirection: "column",
            gap: "0.75rem",
        };
    const canvasWrapperStyle = isFullscreen
        ? { position: "relative", flex: 1 }
        : { position: "relative", minHeight: CANVAS_HEIGHT };
    const selectedEdge = useMemo(() => {
        if (!graph || !selectedEdgeId) {
            return null;
        }
        return graph.edges.find((edge) => edge.id === selectedEdgeId) ?? null;
    }, [graph, selectedEdgeId]);
    const selectedSourceNodes = useMemo(() => {
        if (!graph || !selectedEdge)
            return [];
        const sourceIds = Array.isArray(selectedEdge.source_ids) && selectedEdge.source_ids.length
            ? selectedEdge.source_ids
            : selectedEdge.source_id
                ? [selectedEdge.source_id]
                : [];
        return sourceIds
            .map((id) => renderedNodes.find((node) => node.id === id))
            .filter((node) => !!node);
    }, [graph, selectedEdge, renderedNodes]);
    const selectedTargetNodes = useMemo(() => {
        if (!graph || !selectedEdge)
            return [];
        const targetIds = Array.isArray(selectedEdge.target_ids) && selectedEdge.target_ids.length
            ? selectedEdge.target_ids
            : selectedEdge.target_id
                ? [selectedEdge.target_id]
                : [];
        return targetIds
            .map((id) => renderedNodes.find((node) => node.id === id))
            .filter((node) => !!node);
    }, [graph, selectedEdge, renderedNodes]);
    if (!graph) {
        return (_jsxs("section", { children: [_jsx("h2", { children: "Visualization" }), _jsx("p", { children: "Select a graph to begin editing." })] }));
    }
    const graphType = (graph.graph_type ?? "graph").toLowerCase();
    const showHyperHandles = !!onAttachEdgeMember && (graphType === "hypergraph" || graphType === "ubergraph");
    const allowEdgeAttachments = graphType === "ubergraph";
    const isDirected = graph.directed ?? true;
    // Renders the draggable handles that let users rewire edges (or hyper edge members) in desktop parity mode.
    const renderEdgeHandles = () => {
        if (!selectedEdge || !onReconnectEdge) {
            return null;
        }
        const sourceHandles = selectedSourceNodes.map((node) => (_jsx("circle", { "data-edge-handle": `${selectedEdge.id}:source`, "data-node-id": node.id, cx: node.x ?? 0, cy: node.y ?? 0, r: 12, fill: "#fde68a", stroke: "#f97316", strokeWidth: 3, style: { cursor: "grab" }, filter: `url(#${selectionGlowId})` }, `${selectedEdge.id}:source:${node.id}`)));
        const targetHandles = selectedTargetNodes.map((node) => (_jsx("circle", { "data-edge-handle": `${selectedEdge.id}:target`, "data-node-id": node.id, cx: node.x ?? 0, cy: node.y ?? 0, r: 12, fill: "#bae6fd", stroke: "#0ea5e9", strokeWidth: 3, style: { cursor: "grab" }, filter: `url(#${selectionGlowId})` }, `${selectedEdge.id}:target:${node.id}`)));
        return _jsx("g", { children: [...sourceHandles, ...targetHandles] });
    };
    return (_jsxs("section", { style: sectionStyle, children: [!isFullscreen && (_jsxs("header", { style: {
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    gap: "0.75rem",
                    flexWrap: "wrap",
                    color: "#0f172a",
                }, children: [_jsx("h2", { style: { margin: 0 }, children: "Visualization" }), _jsx("small", { style: { color: "#475569" }, children: "Drag to pan, scroll to zoom, double click to add, drag node ring to connect, drag edge tips to rewire" })] })), _jsxs("div", { style: canvasWrapperStyle, children: [onToggleFullscreen && (_jsxs("button", { type: "button", onClick: onToggleFullscreen, style: {
                            position: "absolute",
                            top: isFullscreen ? 32 : 16,
                            right: isFullscreen ? 32 : 16,
                            padding: "0.35rem 0.85rem",
                            borderRadius: 999,
                            border: "1px solid rgba(255, 255, 255, 0.6)",
                            background: "rgba(15, 23, 42, 0.75)",
                            color: "#f8fafc",
                            cursor: "pointer",
                            zIndex: 2,
                            boxShadow: "0 6px 18px rgba(15, 23, 42, 0.35)",
                            display: "flex",
                            alignItems: "center",
                            gap: 6,
                        }, children: [_jsx("span", { style: { fontSize: 12, fontWeight: 600 }, children: isFullscreen ? "Exit Fullscreen" : "Fullscreen" }), _jsx("span", { "aria-hidden": "true", children: isFullscreen ? "↙" : "↗" })] })), _jsxs("svg", { ref: svgRef, width: "100%", height: canvasHeight, style: {
                            borderRadius: 12,
                            border: "1px solid #e2e8f0",
                            background: effectiveBackgroundColor,
                            touchAction: "none",
                        }, onPointerDown: handlePointerDown, onPointerMove: handlePointerMove, onPointerUp: handlePointerUp, onPointerLeave: () => setDragState(null), onWheel: handleWheel, onDoubleClick: handleDoubleClick, onPointerDownCapture: (event) => {
                            const target = event.target;
                            if (target?.hasAttribute("data-hyper-segment")) {
                                return;
                            }
                            if (event.target === event.currentTarget) {
                                onSelectNode?.(null);
                                onSelectEdge?.(null);
                                onSelectSegment?.(null);
                                event.preventDefault();
                                setDragState({
                                    type: "pan",
                                    pointerId: event.pointerId,
                                    originX: event.clientX,
                                    originY: event.clientY,
                                    startPan: pan,
                                });
                                svgRef.current?.setPointerCapture(event.pointerId);
                            }
                        }, children: [_jsxs("defs", { children: [effectiveShowGrid && (_jsxs("pattern", { id: gridPatternId, width: effectiveGridSpacing, height: effectiveGridSpacing, patternUnits: "userSpaceOnUse", children: [_jsx("rect", { width: effectiveGridSpacing, height: effectiveGridSpacing, fill: effectiveBackgroundColor }), _jsx("path", { d: `M ${effectiveGridSpacing} 0 L 0 0 0 ${effectiveGridSpacing}`, fill: "none", stroke: effectiveGridColor, strokeWidth: effectiveThickness })] })), _jsx("filter", { id: selectionGlowId, x: "-50%", y: "-50%", width: "200%", height: "200%", children: _jsx("feDropShadow", { dx: "0", dy: "0", stdDeviation: "3", floodColor: "#0ea5e9", floodOpacity: "0.8" }) }), _jsx("marker", { id: "canvas-arrow", markerWidth: "8", markerHeight: "8", refX: "8", refY: "4", orient: "auto-start-reverse", children: _jsx("path", { d: "M 0 0 L 8 4 L 0 8 z", fill: "#475569" }) })] }), _jsxs("g", { transform: `translate(${pan.x}, ${pan.y}) scale(${zoom})`, children: [_jsx("rect", { x: -GRID_EXTENT / 2, y: -GRID_EXTENT / 2, width: GRID_EXTENT, height: GRID_EXTENT, fill: effectiveShowGrid ? `url(#${gridPatternId})` : effectiveBackgroundColor, pointerEvents: "none" }), graph.edges.map((edge) => {
                                        const source = renderedNodes.find((node) => node.id === edge.source_id);
                                        const target = renderedNodes.find((node) => node.id === edge.target_id);
                                        if (!source || !target) {
                                            return null;
                                        }
                                        const isEdgeSelected = selectedEdgeId === edge.id;
                                        const isWholeSelected = isEdgeSelected && selectedEdgeScope === "whole";
                                        const isMainlineSelected = isEdgeSelected && selectedEdgeScope === "mainline";
                                        const sourceIds = (Array.isArray(edge.source_ids) && edge.source_ids.length > 0
                                            ? edge.source_ids
                                            : [edge.source_id]) ?? [edge.source_id];
                                        const targetIds = (Array.isArray(edge.target_ids) && edge.target_ids.length > 0
                                            ? edge.target_ids
                                            : [edge.target_id]) ?? [edge.target_id];
                                        const x1 = source.x ?? 0;
                                        const y1 = source.y ?? 0;
                                        const x2 = target.x ?? 0;
                                        const y2 = target.y ?? 0;
                                        const midX = (x1 + x2) / 2;
                                        const midY = (y1 + y2) / 2;
                                        const angleDeg = (Math.atan2((y2 ?? 0) - (y1 ?? 0), (x2 ?? 0) - (x1 ?? 0)) * 180) / Math.PI;
                                        const isAttachHoverEdge = dragState?.type === "edge" &&
                                            (dragState.mode === "attach-head" || dragState.mode === "attach-tail") &&
                                            dragState.hoverEdgeId === edge.id;
                                        const strokeColor = isWholeSelected
                                            ? "#0ea5e9"
                                            : isMainlineSelected
                                                ? "#f97316"
                                                : isAttachHoverEdge
                                                    ? "#ec4899"
                                                    : "#94a3b8";
                                        const strokeWidth = isWholeSelected
                                            ? 5
                                            : isMainlineSelected
                                                ? 4
                                                : isAttachHoverEdge
                                                    ? 3
                                                    : 2;
                                        const strokeDasharray = isMainlineSelected ? "8 4" : undefined;
                                        const showSelectionGlow = isWholeSelected || isMainlineSelected;
                                        const tailHandlePos = {
                                            x: x1 + (x2 - x1) * 0.35,
                                            y: y1 + (y2 - y1) * 0.35,
                                        };
                                        const headHandlePos = {
                                            x: x1 + (x2 - x1) * 0.65,
                                            y: y1 + (y2 - y1) * 0.65,
                                        };
                                        // Each edge is split into "outer" and "inner" segments so the selection scope can
                                        // highlight the mainline or the entire hyper-edge structure independently.
                                        const hitSegments = [
                                            {
                                                key: "outer-tail",
                                                start: { x: x1, y: y1 },
                                                end: tailHandlePos,
                                                scope: "mainline",
                                                width: 18,
                                            },
                                            {
                                                key: "inner",
                                                start: tailHandlePos,
                                                end: headHandlePos,
                                                scope: "whole",
                                                width: 24,
                                            },
                                            {
                                                key: "outer-head",
                                                start: headHandlePos,
                                                end: { x: x2, y: y2 },
                                                scope: "mainline",
                                                width: 18,
                                            },
                                        ];
                                        return (_jsxs("g", { "data-edge-group": edge.id, "data-edge-id": edge.id, style: { cursor: "pointer" }, children: [hitSegments.map((segment) => (_jsx("line", { "data-edge-hit": `${edge.id}:${segment.key}`, x1: segment.start.x, y1: segment.start.y, x2: segment.end.x, y2: segment.end.y, stroke: "transparent", strokeWidth: segment.width, opacity: 0, pointerEvents: "stroke", onClick: (event) => {
                                                        event.stopPropagation();
                                                        onSelectEdge?.(edge.id);
                                                        onSelectSegment?.(null);
                                                        onSelectNode?.(null);
                                                        onEdgeScopeChange?.(segment.scope);
                                                    } }, `edge-hit-${segment.key}`))), showHyperHandles &&
                                                    sourceIds.map((nodeId) => {
                                                        const anchor = nodePositionMap[nodeId] ??
                                                            (allowEdgeAttachments ? edgeMidpoints[nodeId] : undefined);
                                                        if (!anchor)
                                                            return null;
                                                        const isEdgeAnchor = !nodePositionMap[nodeId];
                                                        const isSegmentSelected = selectedSegment?.edgeId === edge.id &&
                                                            selectedSegment.kind === "tail" &&
                                                            selectedSegment.memberId === nodeId;
                                                        const connectorHighlighted = isSegmentSelected || isWholeSelected;
                                                        const connectorColor = connectorHighlighted ? "#0f766e" : "#f97316";
                                                        const connectorWidth = connectorHighlighted ? 5 : 2;
                                                        const connectorOpacity = connectorHighlighted ? 1 : 0.6;
                                                        return (_jsx("line", { "data-hyper-segment": `${edge.id}:tail:${nodeId}`, x1: anchor.x, y1: anchor.y, x2: tailHandlePos.x, y2: tailHandlePos.y, stroke: connectorColor, strokeWidth: connectorWidth, opacity: connectorOpacity, strokeDasharray: isEdgeAnchor ? "4 3" : undefined, pointerEvents: "stroke", strokeLinecap: "round", style: { cursor: "pointer" }, filter: isSegmentSelected ? `url(#${selectionGlowId})` : undefined, onClick: (segmentEvent) => {
                                                                segmentEvent.stopPropagation();
                                                                onSelectEdge?.(edge.id);
                                                                onSelectNode?.(null);
                                                                onSelectSegment?.({
                                                                    edgeId: edge.id,
                                                                    kind: "tail",
                                                                    memberId: nodeId,
                                                                });
                                                                onEdgeScopeChange?.("none");
                                                            } }, `${edge.id}-tail-connector-${nodeId}`));
                                                    }), showHyperHandles &&
                                                    targetIds.map((nodeId) => {
                                                        const anchor = nodePositionMap[nodeId] ??
                                                            (allowEdgeAttachments ? edgeMidpoints[nodeId] : undefined);
                                                        if (!anchor)
                                                            return null;
                                                        const isEdgeAnchor = !nodePositionMap[nodeId];
                                                        const isSegmentSelected = selectedSegment?.edgeId === edge.id &&
                                                            selectedSegment.kind === "head" &&
                                                            selectedSegment.memberId === nodeId;
                                                        const connectorHighlighted = isSegmentSelected || isWholeSelected;
                                                        const connectorColor = connectorHighlighted ? "#0369a1" : "#0ea5e9";
                                                        const connectorWidth = connectorHighlighted ? 5 : 2;
                                                        const connectorOpacity = connectorHighlighted ? 1 : 0.6;
                                                        return (_jsx("line", { "data-hyper-segment": `${edge.id}:head:${nodeId}`, x1: anchor.x, y1: anchor.y, x2: headHandlePos.x, y2: headHandlePos.y, stroke: connectorColor, strokeWidth: connectorWidth, opacity: connectorOpacity, strokeDasharray: isEdgeAnchor ? "4 3" : undefined, pointerEvents: "stroke", strokeLinecap: "round", style: { cursor: "pointer" }, filter: isSegmentSelected ? `url(#${selectionGlowId})` : undefined, onClick: (segmentEvent) => {
                                                                segmentEvent.stopPropagation();
                                                                onSelectEdge?.(edge.id);
                                                                onSelectNode?.(null);
                                                                onSelectSegment?.({
                                                                    edgeId: edge.id,
                                                                    kind: "head",
                                                                    memberId: nodeId,
                                                                });
                                                                onEdgeScopeChange?.("none");
                                                            } }, `${edge.id}-head-connector-${nodeId}`));
                                                    }), _jsx("line", { x1: x1, y1: y1, x2: x2, y2: y2, stroke: strokeColor, strokeWidth: strokeWidth, opacity: 0.9, strokeDasharray: strokeDasharray, filter: showSelectionGlow ? `url(#${selectionGlowId})` : undefined, strokeLinecap: "round", pointerEvents: "none" }), isDirected && (_jsxs("g", { transform: `translate(${midX}, ${midY}) rotate(${angleDeg})`, style: { pointerEvents: "none" }, children: [_jsx("line", { x1: -10, y1: 0, x2: 10, y2: 0, stroke: strokeColor, strokeWidth: strokeWidth, opacity: 0.9, strokeDasharray: strokeDasharray, filter: showSelectionGlow ? `url(#${selectionGlowId})` : undefined }), _jsx("polygon", { points: "10,0 0,-5 0,5", fill: isWholeSelected
                                                                ? "#0ea5e9"
                                                                : isMainlineSelected
                                                                    ? "#f97316"
                                                                    : "#94a3b8" })] })), showHyperHandles && (_jsxs(_Fragment, { children: [_jsx("circle", { "data-hyper-handle": `${edge.id}:tail`, "data-anchor-x": tailHandlePos.x, "data-anchor-y": tailHandlePos.y, "data-allow-edge-targets": allowEdgeAttachments ? "true" : "false", cx: tailHandlePos.x, cy: tailHandlePos.y, r: 7, fill: "#fef3c7", stroke: "#f97316", strokeWidth: 2, style: { cursor: "crosshair" } }), _jsx("circle", { "data-hyper-handle": `${edge.id}:head`, "data-anchor-x": headHandlePos.x, "data-anchor-y": headHandlePos.y, "data-allow-edge-targets": allowEdgeAttachments ? "true" : "false", cx: headHandlePos.x, cy: headHandlePos.y, r: 7, fill: "#e0f2fe", stroke: "#0284c7", strokeWidth: 2, style: { cursor: "crosshair" } })] }))] }, edge.id));
                                    }), dragState?.type === "edge" && (_jsxs(_Fragment, { children: [_jsx("line", { x1: dragState.anchorPos.x, y1: dragState.anchorPos.y, x2: dragState.currentPos.x, y2: dragState.currentPos.y, stroke: "#f97316", strokeWidth: 2, strokeDasharray: "4 4" }), _jsx("g", { transform: `translate(${(dragState.anchorPos.x + dragState.currentPos.x) / 2}, ${(dragState.anchorPos.y + dragState.currentPos.y) / 2}) rotate(${(Math.atan2(dragState.currentPos.y - dragState.anchorPos.y, dragState.currentPos.x - dragState.anchorPos.x) *
                                                    180) /
                                                    Math.PI})`, children: _jsx("polygon", { points: "8,0 0,-4 0,4", fill: "#f97316" }) })] })), renderedNodes.map((node) => {
                                        const isSelected = selectedNodeId === node.id;
                                        const rawLabel = node.text ?? node.metadata?.label ?? node.id;
                                        const label = typeof rawLabel === "string"
                                            ? rawLabel
                                            : String(rawLabel ?? "");
                                        const isEdgeHover = dragState?.type === "edge" && dragState.hoverTargetId === node.id;
                                        return (_jsxs("g", { transform: `translate(${node.x ?? 0}, ${node.y ?? 0})`, children: [onConnectNodes && (_jsx("circle", { "data-node-handle": node.id, r: isSelected ? 32 : 28, fill: "transparent", stroke: dragState?.type === "edge" &&
                                                        dragState.mode === "new" &&
                                                        dragState.anchorNodeId === node.id
                                                        ? "#f97316"
                                                        : "rgba(148, 163, 184, 0.5)", strokeDasharray: "6 4", strokeWidth: 2.5, style: { pointerEvents: "stroke", cursor: "crosshair" } })), _jsx("circle", { "data-node-id": node.id, r: isSelected ? 26 : 22, fill: isSelected ? "#2563eb" : "#3b82f6", opacity: 0.9, stroke: isEdgeHover ? "#f97316" : isSelected ? "#1e40af" : "transparent", strokeWidth: isEdgeHover ? 3 : 2 }), _jsx("text", { "data-node-id": node.id, textAnchor: "middle", fill: "#fff", fontSize: "12", dy: "0.35em", fontWeight: "600", children: label })] }, node.id));
                                    }), renderEdgeHandles()] })] })] })] }));
}
