import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type {
  PointerEvent as ReactPointerEvent,
  WheelEvent as ReactWheelEvent,
  MouseEvent as ReactMouseEvent,
} from "react";
import type { GraphDTO, NodeDTO } from "../types";

type TouchConnectSource =
  | { kind: "node"; nodeId: string }
  | { kind: "hyper"; edgeId: string; role: "head" | "tail"; allowEdgeTargets: boolean };

type Props = {
  graph?: GraphDTO | null;
  selectedNodeId?: string | null;
  selectedEdgeId?: string | null;
  selectedSegment?: {
    edgeId: string;
    kind: "head" | "tail";
    memberId: string;
  } | null;
  selectedEdgeScope?: "none" | "mainline" | "whole";
  onSelectNode?: (nodeId: string | null) => void;
  onSelectEdge?: (edgeId: string | null) => void;
  onSelectSegment?: (
    segment: { edgeId: string; kind: "head" | "tail"; memberId: string } | null,
  ) => void;
  onEdgeScopeChange?: (scope: "none" | "mainline" | "whole") => void;
  onNodePositionChange?: (nodeId: string, x: number, y: number) => void;
  onCanvasAddNode?: (x: number, y: number) => void;
  onConnectNodes?: (sourceId: string, targetId: string) => Promise<void> | void;
  onReconnectEdge?: (
    edgeId: string,
    payload: { source_id?: string; target_id?: string },
  ) => Promise<void> | void;
  onAttachEdgeMember?: (
    edgeId: string,
    payload: { kind: "head" | "tail"; targetNodeId?: string; targetEdgeId?: string },
  ) => Promise<void> | void;
  onDeleteNode?: (nodeId: string) => Promise<void> | void;
  onDeleteEdge?: (edgeId: string) => Promise<void> | void;
  showGrid?: boolean;
  gridColor?: string;
  gridSpacing?: number;
  gridThickness?: number;
  backgroundColor?: string;
  isFullscreen?: boolean;
  onToggleFullscreen?: () => void;
};

type DragState =
  | {
    type: "pan";
    pointerId: number;
    originX: number;
    originY: number;
    startPan: { x: number; y: number };
  }
  | {
    type: "node";
    pointerId: number;
    nodeId: string;
    originX: number;
    originY: number;
    startNode: { x: number; y: number };
    moved: boolean;
  }
  | {
    type: "edge";
    pointerId: number;
    mode: "new" | "rewire-source" | "rewire-target" | "attach-head" | "attach-tail";
    edgeId?: string;
    dragNodeId: string;
    anchorNodeId: string;
    anchorPos: { x: number; y: number };
    currentPos: { x: number; y: number };
    hoverTargetId?: string;
    hoverEdgeId?: string;
    allowEdgeTargets?: boolean;
  };

const CANVAS_HEIGHT = 520;
const GRID_EXTENT = 8000;
const MIN_ZOOM = 0.25;
const MAX_ZOOM = 4;
const LONG_PRESS_DURATION_MS = 650;
const LONG_PRESS_MOVE_THRESHOLD = 18;

export function GraphCanvas({
  graph,
  selectedNodeId,
  selectedEdgeId,
  selectedSegment,
  selectedEdgeScope = "none",
  onSelectNode,
  onSelectEdge,
  onSelectSegment,
  onEdgeScopeChange,
  onNodePositionChange,
  onCanvasAddNode,
  onConnectNodes,
  onReconnectEdge,
  onAttachEdgeMember,
  onDeleteNode,
  onDeleteEdge,
  showGrid: showGridProp,
  gridColor: gridColorProp,
  gridSpacing: gridSpacingProp,
  gridThickness: gridThicknessProp,
  backgroundColor: backgroundColorProp,
  isFullscreen = false,
  onToggleFullscreen,
}: Props) {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [dragState, setDragState] = useState<DragState | null>(null);
  const [localNodes, setLocalNodes] = useState<Record<string, NodeDTO>>({});
  const pointerPositions = useRef<Map<number, { x: number; y: number }>>(new Map());
  const [isCoarsePointer, setIsCoarsePointer] = useState(false);
  const [touchConnectSource, setTouchConnectSource] = useState<TouchConnectSource | null>(
    null,
  );
  const pinchState = useRef<{
    initialDistance: number;
    initialZoom: number;
    centerWorld: { x: number; y: number };
  } | null>(null);
  const longPressTimerId = useRef<number | null>(null);
  const longPressPointerId = useRef<number | null>(null);
  const longPressOrigin = useRef<{ x: number; y: number } | null>(null);
  const longPressTarget = useRef<{ type: "node" | "edge"; id: string } | null>(null);
  const panRef = useRef(pan);
  const zoomRef = useRef(zoom);

  useEffect(() => {
    panRef.current = pan;
  }, [pan]);

  useEffect(() => {
    zoomRef.current = zoom;
  }, [zoom]);

  useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
      return;
    }
    const query = window.matchMedia("(pointer: coarse)");
    const update = () => setIsCoarsePointer(query.matches);
    update();
    if (typeof query.addEventListener === "function") {
      query.addEventListener("change", update);
      return () => query.removeEventListener("change", update);
    }
    query.addListener(update);
    return () => query.removeListener(update);
  }, []);

  useEffect(() => {
    setTouchConnectSource(null);
  }, [graph?.id]);

  const clampZoom = useCallback(
    (value: number) => Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, value)),
    [],
  );

  const clearPinchIfNeeded = useCallback((pointerId?: number) => {
    if (typeof pointerId === "number") {
      pointerPositions.current.delete(pointerId);
    }
    if (pointerPositions.current.size < 2) {
      pinchState.current = null;
    }
  }, []);

  const clearLongPress = useCallback(() => {
    if (longPressTimerId.current !== null) {
      window.clearTimeout(longPressTimerId.current);
      longPressTimerId.current = null;
    }
    longPressPointerId.current = null;
    longPressOrigin.current = null;
    longPressTarget.current = null;
  }, []);

  const triggerLongPress = useCallback(() => {
    const target = longPressTarget.current;
    clearLongPress();
    if (!target) {
      return;
    }
    if (target.type === "node" && onDeleteNode) {
      const maybe = onDeleteNode(target.id);
      if (maybe && typeof (maybe as Promise<void>).then === "function") {
        (maybe as Promise<void>).catch(() => undefined);
      }
      setTouchConnectSource((prev) => {
        if (prev?.kind === "node" && prev.nodeId === target.id) {
          return null;
        }
        return prev;
      });
    } else if (target.type === "edge" && onDeleteEdge) {
      const maybe = onDeleteEdge(target.id);
      if (maybe && typeof (maybe as Promise<void>).then === "function") {
        (maybe as Promise<void>).catch(() => undefined);
      }
      setTouchConnectSource((prev) => {
        if (prev?.kind === "hyper" && prev.edgeId === target.id) {
          return null;
        }
        return prev;
      });
    }
  }, [clearLongPress, onDeleteEdge, onDeleteNode]);

  const scheduleLongPress = useCallback(
    (event: ReactPointerEvent<Element>, target: { type: "node" | "edge"; id: string }) => {
      if (
        event.pointerType !== "touch" ||
        !isCoarsePointer ||
        (target.type === "node" && !onDeleteNode) ||
        (target.type === "edge" && !onDeleteEdge)
      ) {
        return;
      }
      clearLongPress();
      longPressPointerId.current = event.pointerId;
      longPressOrigin.current = { x: event.clientX, y: event.clientY };
      longPressTarget.current = target;
      longPressTimerId.current = window.setTimeout(() => {
        triggerLongPress();
      }, LONG_PRESS_DURATION_MS);
    },
    [clearLongPress, isCoarsePointer, onDeleteEdge, onDeleteNode, triggerLongPress],
  );

  useEffect(
    () => () => {
      clearLongPress();
    },
    [clearLongPress],
  );

  const handleTouchHyperTap = useCallback(
    (edgeRef: string, role: "head" | "tail", allowEdges: boolean) => {
      if (!onAttachEdgeMember) {
        return;
      }
      setTouchConnectSource((prev) => {
        if (prev && prev.kind === "hyper") {
          const canTargetEdge =
            allowEdges || prev.allowEdgeTargets || prev.edgeId === edgeRef;
          if (!canTargetEdge) {
            return prev;
          }
          const maybe = onAttachEdgeMember(prev.edgeId, {
            kind: prev.role,
            targetEdgeId: edgeRef,
          });
          if (maybe && typeof (maybe as Promise<void>).then === "function") {
            (maybe as Promise<void>).catch(() => undefined);
          }
          return null;
        }
        return {
          kind: "hyper",
          edgeId: edgeRef,
          role,
          allowEdgeTargets: allowEdges,
        };
      });
    },
    [onAttachEdgeMember],
  );

  const applyPinchGesture = useCallback(() => {
    if (!svgRef.current) {
      return;
    }
    const points = Array.from(pointerPositions.current.values());
    if (points.length < 2) {
      return;
    }
    const [first, second] = points;
    const distance = Math.hypot(second.x - first.x, second.y - first.y) || 1;
    const rect = svgRef.current.getBoundingClientRect();
    const centerClient = {
      x: (first.x + second.x) / 2,
      y: (first.y + second.y) / 2,
    };
    if (!pinchState.current) {
      pinchState.current = {
        initialDistance: distance,
        initialZoom: zoomRef.current,
        centerWorld: {
          x: (centerClient.x - rect.left - panRef.current.x) / zoomRef.current,
          y: (centerClient.y - rect.top - panRef.current.y) / zoomRef.current,
        },
      };
    }
    const { initialDistance, initialZoom, centerWorld } = pinchState.current;
    const scale = distance / Math.max(1, initialDistance);
    const nextZoom = clampZoom(initialZoom * scale);
    const nextPan = {
      x: centerClient.x - rect.left - centerWorld.x * nextZoom,
      y: centerClient.y - rect.top - centerWorld.y * nextZoom,
    };
    setZoom(nextZoom);
    setPan(nextPan);
    setDragState(null);
  }, [clampZoom]);

  const fallbackHex = (arr?: number[]) => {
    if (!arr || arr.length < 3) {
      return undefined;
    }
    return `#${arr
      .slice(0, 3)
      .map((value) => Math.max(0, Math.min(255, value)).toString(16).padStart(2, "0"))
      .join("")}`;
  };

  const effectiveShowGrid = showGridProp ?? graph?.grid_visible ?? true;
  const effectiveGridColor =
    gridColorProp ?? fallbackHex(graph?.grid_color) ?? "#e2e8f0";
  const effectiveBackgroundColor =
    backgroundColorProp ?? fallbackHex(graph?.background_color) ?? "#f8fafc";

  const selectionGlowId = useMemo(
    () => `edge-selection-${Math.random().toString(36).slice(2)}`,
    [],
  );
  const effectiveGridSpacing = Math.max(
    5,
    gridSpacingProp ?? graph?.grid_size ?? 20,
  );
  useEffect(() => {
    if (!isFullscreen) {
      return;
    }
    const handleEsc = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onToggleFullscreen?.();
      }
    };
    window.addEventListener("keydown", handleEsc);
    return () => window.removeEventListener("keydown", handleEsc);
  }, [isFullscreen, onToggleFullscreen]);

  const effectiveThickness = Math.max(
    0.5,
    gridThicknessProp ?? graph?.grid_line_thickness ?? 1,
  );

  useEffect(() => {
    if (!graph) {
      setLocalNodes({});
      return;
    }
    const map: Record<string, NodeDTO> = {};
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
    const map: Record<
      string,
      {
        x: number;
        y: number;
      }
    > = {};
    renderedNodes.forEach((node) => {
      map[node.id] = { x: node.x ?? 0, y: node.y ?? 0 };
    });
    return map;
  }, [renderedNodes]);

  // Cache all edge midpoints so selection hit-tests and drag previews can reuse a single lookup.
  const edgeMidpoints = useMemo<Record<string, { x: number; y: number }>>(() => {
    if (!graph) return {};
    const map: Record<string, { x: number; y: number }> = {};
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

  const toWorld = useCallback(
    (clientX: number, clientY: number) => {
      const rect = svgRef.current?.getBoundingClientRect();
      if (!rect) {
        return { x: 0, y: 0 };
      }
      return {
        x: (clientX - rect.left - pan.x) / zoom,
        y: (clientY - rect.top - pan.y) / zoom,
      };
    },
    [pan, zoom],
  );

  const handlePointerDown = (event: ReactPointerEvent<SVGSVGElement>) => {
    clearLongPress();
    // All pointer interactions funnel through this gate so we can decide early whether to pan,
    // start a drag, or simply let the click bubble to a selection handler.
    if (!graph) {
      return;
    }
    if (event.pointerType === "touch") {
      pointerPositions.current.set(event.pointerId, {
        x: event.clientX,
        y: event.clientY,
      });
      if (pointerPositions.current.size >= 2) {
        clearLongPress();
        pinchState.current = null;
        setDragState(null);
        event.currentTarget.setPointerCapture(event.pointerId);
        return;
      }
    }
    const target = event.target as HTMLElement;
    const nodeHandleId = target.getAttribute("data-node-handle");
    const edgeHandleAttr = target.getAttribute("data-edge-handle");
    const hyperHandleAttr = target.getAttribute("data-hyper-handle");
    const hyperSegmentAttr = target.getAttribute("data-hyper-segment");
    const edgeHitAttr = target.getAttribute("data-edge-hit");
    const nodeId = target.dataset.nodeId;
    const edgeId = target.dataset.edgeId;

    if (hyperSegmentAttr) {
      // Let click handlers handle selection without initiating drag/pan.
      return;
    }

    if (edgeHitAttr) {
      const [edgeFromHit] = edgeHitAttr.split(":");
      if (edgeFromHit) {
        scheduleLongPress(event, { type: "edge", id: edgeFromHit });
      }
      return;
    }

    if (nodeHandleId) {
      if (event.pointerType === "touch") {
        event.preventDefault();
      }
      if (!onConnectNodes) {
        return;
      }
      const node =
        localNodes[nodeHandleId] ?? graph.nodes.find((n) => n.id === nodeHandleId);
      if (!node) return;
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
      if (event.pointerType === "touch") {
        event.preventDefault();
      }
      if (!onReconnectEdge) {
        return;
      }
      const [dragEdgeId, anchor] = edgeHandleAttr.split(":");
      const edge = graph.edges.find((item) => item.id === dragEdgeId);
      if (!edge) return;
      const sourceNode =
        renderedNodes.find((node) => node.id === edge.source_id) ??
        graph.nodes.find((node) => node.id === edge.source_id);
      const targetNode =
        renderedNodes.find((node) => node.id === edge.target_id) ??
        graph.nodes.find((node) => node.id === edge.target_id);
      if (!sourceNode || !targetNode) return;
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
      const [edgeRef, role] = hyperHandleAttr.split(":");
      const anchorX = Number(target.getAttribute("data-anchor-x")) || 0;
      const anchorY = Number(target.getAttribute("data-anchor-y")) || 0;
      const allowEdges = target.getAttribute("data-allow-edge-targets") === "true";
      if (!edgeRef) {
        return;
      }
      if (event.pointerType === "touch" && isCoarsePointer) {
        event.preventDefault();
        handleTouchHyperTap(edgeRef, role === "head" ? "head" : "tail", allowEdges);
        return;
      }
      if (!onAttachEdgeMember) {
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
      if (!node) return;
      onSelectNode?.(nodeId);
      onSelectSegment?.(null);
      scheduleLongPress(event, { type: "node", id: nodeId });
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

  const handlePointerMove = (event: ReactPointerEvent<SVGSVGElement>) => {
    if (event.pointerType === "touch") {
      pointerPositions.current.set(event.pointerId, {
        x: event.clientX,
        y: event.clientY,
      });
      if (pointerPositions.current.size >= 2) {
        clearLongPress();
        event.preventDefault();
        applyPinchGesture();
        return;
      }
      if (event.pointerId === longPressPointerId.current && longPressOrigin.current) {
        const dx = event.clientX - longPressOrigin.current.x;
        const dy = event.clientY - longPressOrigin.current.y;
        if (Math.hypot(dx, dy) > LONG_PRESS_MOVE_THRESHOLD) {
          clearLongPress();
        }
      }
    }
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
        const current =
          prev[dragState.nodeId] ??
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
      const hovered =
        renderedNodes.find((node) => {
          if (node.id === dragState.dragNodeId) return false;
          const dx = (node.x ?? 0) - world.x;
          const dy = (node.y ?? 0) - world.y;
          return Math.hypot(dx, dy) < 28;
        }) ?? null;
      let hoveredEdgeId: string | undefined;
      if (dragState.allowEdgeTargets) {
        let bestId: string | undefined;
        let bestDist = Number.POSITIVE_INFINITY;
        Object.entries(edgeMidpoints).forEach(([edgeId, pos]) => {
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
          hoverEdgeId: hoveredEdgeId || undefined,
        };
      });
    }
  };

  const handlePointerUp = (event: ReactPointerEvent<SVGSVGElement>) => {
    if (event.pointerType === "touch") {
      clearPinchIfNeeded(event.pointerId);
    }
    clearLongPress();
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
      } else if (
        event.pointerType === "touch" &&
        isCoarsePointer &&
        touchConnectSource?.kind === "hyper" &&
        onAttachEdgeMember
      ) {
        const source = touchConnectSource;
        setTouchConnectSource(null);
        const maybe = onAttachEdgeMember(source.edgeId, {
          kind: source.role,
          targetNodeId: dragState.nodeId,
        });
        if (maybe && typeof (maybe as Promise<void>).then === "function") {
          (maybe as Promise<void>).catch(() => undefined);
        }
      } else if (
        event.pointerType === "touch" &&
        isCoarsePointer &&
        onConnectNodes
      ) {
        if (touchConnectSource?.kind === "node") {
          const sourceId = touchConnectSource.nodeId;
          setTouchConnectSource(null);
          const maybe = onConnectNodes(sourceId, dragState.nodeId);
          if (maybe && typeof (maybe as Promise<void>).then === "function") {
            (maybe as Promise<void>).catch(() => undefined);
          }
        } else {
          setTouchConnectSource({ kind: "node", nodeId: dragState.nodeId });
        }
      }
      releasePointer();
      return;
    }

    if (dragState.type === "edge") {
      const world = toWorld(event.clientX, event.clientY);
      const fallbackTarget =
        renderedNodes.find((node) => {
          if (node.id === dragState.dragNodeId) return false;
          const dx = (node.x ?? 0) - world.x;
          const dy = (node.y ?? 0) - world.y;
          return Math.hypot(dx, dy) < 28;
        }) ?? null;

      if (dragState.mode === "attach-head" || dragState.mode === "attach-tail") {
        if (dragState.edgeId && onAttachEdgeMember) {
          const targetNodeId = dragState.hoverTargetId ?? fallbackTarget?.id;
          const targetEdgeId =
            dragState.hoverEdgeId &&
            (dragState.allowEdgeTargets || dragState.hoverEdgeId === dragState.edgeId)
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
      if (targetId) {
        let maybe: Promise<void> | void | undefined = undefined;
        if (dragState.mode === "new") {
          maybe = onConnectNodes?.(dragState.anchorNodeId, targetId);
        } else if (dragState.mode === "rewire-source" && dragState.edgeId) {
          maybe = onReconnectEdge?.(dragState.edgeId, { source_id: targetId });
        } else if (dragState.mode === "rewire-target" && dragState.edgeId) {
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

  const handlePointerLeave = (event: ReactPointerEvent<SVGSVGElement>) => {
    if (event.pointerType === "touch") {
      clearPinchIfNeeded(event.pointerId);
      clearLongPress();
    }
    setDragState(null);
  };

  const handlePointerCancel = (event: ReactPointerEvent<SVGSVGElement>) => {
    if (event.pointerType === "touch") {
      clearPinchIfNeeded(event.pointerId);
      clearLongPress();
    }
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
    if (dragState?.pointerId === event.pointerId) {
      setDragState(null);
    }
  };

  const handleWheel = (event: ReactWheelEvent<SVGSVGElement>) => {
    event.preventDefault();
    const direction = event.deltaY > 0 ? 0.9 : 1.1;
    setZoom((prev) => {
      return clampZoom(prev * direction);
    });
  };

  const handleDoubleClick = (event: ReactMouseEvent<SVGSVGElement>) => {
    if (!graph) return;
    event.preventDefault();
    const world = toWorld(event.clientX, event.clientY);
    const result = onCanvasAddNode?.(world.x, world.y);
    if (!result) {
      return;
    }
    if (typeof (result as Promise<NodeDTO | void>).then === "function") {
      (result as Promise<NodeDTO | void>)
        .then((node) => {
          if (node) {
            setLocalNodes((prev) => ({ ...prev, [node.id]: node }));
          }
        })
        .catch(() => undefined);
    } else if (typeof result === "object") {
      const node = result as NodeDTO;
      if (node.id) {
        setLocalNodes((prev) => ({ ...prev, [node.id]: node }));
      }
    }
  };

  const gridPatternId = useMemo(
    () =>
      `grid-${Math.round(effectiveGridSpacing)}-${effectiveGridColor.replace(
        /[^0-9a-z]/gi,
        "",
      )}`,
    [effectiveGridSpacing, effectiveGridColor],
  );

  const canvasHeight = isFullscreen ? "100%" : CANVAS_HEIGHT;
  const sectionStyle = isFullscreen
    ? {
      position: "fixed" as const,
      inset: 0,
      zIndex: 30,
      padding: "1.5rem",
      background: "rgba(15, 23, 42, 0.92)",
      boxSizing: "border-box" as const,
      display: "flex",
      flexDirection: "column" as const,
      gap: "0.75rem",
    }
    : {
      position: "relative" as const,
      display: "flex",
      flexDirection: "column" as const,
      gap: "0.75rem",
    };
  const canvasWrapperStyle = isFullscreen
    ? { position: "relative" as const, flex: 1 }
    : { position: "relative" as const, minHeight: CANVAS_HEIGHT };

  const selectedEdge = useMemo(() => {
    if (!graph || !selectedEdgeId) {
      return null;
    }
    return graph.edges.find((edge) => edge.id === selectedEdgeId) ?? null;
  }, [graph, selectedEdgeId]);

  const selectedSourceNodes = useMemo(() => {
    if (!graph || !selectedEdge) return [];
    const sourceIds: string[] =
      Array.isArray((selectedEdge as any).source_ids) && (selectedEdge as any).source_ids.length
        ? ((selectedEdge as any).source_ids as string[])
        : selectedEdge.source_id
          ? [selectedEdge.source_id]
          : [];
    return sourceIds
      .map((id) => renderedNodes.find((node) => node.id === id))
      .filter((node): node is typeof renderedNodes[number] => !!node);
  }, [graph, selectedEdge, renderedNodes]);

  const selectedTargetNodes = useMemo(() => {
    if (!graph || !selectedEdge) return [];
    const targetIds: string[] =
      Array.isArray((selectedEdge as any).target_ids) && (selectedEdge as any).target_ids.length
        ? ((selectedEdge as any).target_ids as string[])
        : selectedEdge.target_id
          ? [selectedEdge.target_id]
          : [];
    return targetIds
      .map((id) => renderedNodes.find((node) => node.id === id))
      .filter((node): node is typeof renderedNodes[number] => !!node);
  }, [graph, selectedEdge, renderedNodes]);

  if (!graph) {
    return (
      <section>
        <h2>Visualization</h2>
        <p>Select a graph to begin editing.</p>
      </section>
    );
  }
  const graphType = (graph.graph_type ?? "graph").toLowerCase();
  const showHyperHandles =
    !!onAttachEdgeMember && (graphType === "hypergraph" || graphType === "ubergraph");
  const allowEdgeAttachments = graphType === "ubergraph";
  const isDirected = graph.directed ?? true;
  // Renders the draggable handles that let users rewire edges (or hyper edge members) in desktop parity mode.
  const renderEdgeHandles = () => {
    if (!selectedEdge || !onReconnectEdge) {
      return null;
    }
    const sourceHandles = selectedSourceNodes.map((node) => (
      <circle
        key={`${selectedEdge.id}:source:${node.id}`}
        data-edge-handle={`${selectedEdge.id}:source`}
        data-node-id={node.id}
        cx={node.x ?? 0}
        cy={node.y ?? 0}
        r={12}
        fill="#fde68a"
        stroke="#f97316"
        strokeWidth={3}
        style={{ cursor: "grab" }}
        filter={`url(#${selectionGlowId})`}
      />
    ));
    const targetHandles = selectedTargetNodes.map((node) => (
      <circle
        key={`${selectedEdge.id}:target:${node.id}`}
        data-edge-handle={`${selectedEdge.id}:target`}
        data-node-id={node.id}
        cx={node.x ?? 0}
        cy={node.y ?? 0}
        r={12}
        fill="#bae6fd"
        stroke="#0ea5e9"
        strokeWidth={3}
        style={{ cursor: "grab" }}
        filter={`url(#${selectionGlowId})`}
      />
    ));
    return <g>{[...sourceHandles, ...targetHandles]}</g>;
  };

  return (
    <section style={sectionStyle}>
      {!isFullscreen && (
        <header
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: "0.75rem",
            flexWrap: "wrap",
            color: "#0f172a",
          }}
        >
          <h2 style={{ margin: 0 }}>Visualization</h2>
          <small style={{ color: "#475569" }}>
            Drag to pan, scroll or pinch to zoom, double tap to add, drag node ring to connect, drag edge tips to rewire
          </small>
        </header>
      )}
      <div style={canvasWrapperStyle}>
        {onToggleFullscreen && (
          <button
            type="button"
            onClick={onToggleFullscreen}
            style={{
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
            }}
          >
            <span style={{ fontSize: 12, fontWeight: 600 }}>
              {isFullscreen ? "Exit Fullscreen" : "Fullscreen"}
            </span>
            <span aria-hidden="true">{isFullscreen ? "↙" : "↗"}</span>
          </button>
        )}
        <svg
          ref={svgRef}
          width="100%"
          height={canvasHeight}
          style={{
            borderRadius: 12,
            border: "1px solid #e2e8f0",
            background: effectiveBackgroundColor,
            touchAction: "none",
          }}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerLeave={handlePointerLeave}
          onPointerCancel={handlePointerCancel}
          onWheel={handleWheel}
          onDoubleClick={handleDoubleClick}
          onPointerDownCapture={(event) => {
            if (event.pointerType === "touch" && pointerPositions.current.size >= 2) {
              return;
            }
            const target = event.target as HTMLElement;
            if (target?.hasAttribute("data-hyper-segment")) {
              return;
            }
            if (event.target === event.currentTarget) {
              setTouchConnectSource(null);
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
          }}
        >
          <defs>
            {effectiveShowGrid && (
              <pattern
                id={gridPatternId}
                width={effectiveGridSpacing}
                height={effectiveGridSpacing}
                patternUnits="userSpaceOnUse"
              >
                <rect
                  width={effectiveGridSpacing}
                  height={effectiveGridSpacing}
                  fill={effectiveBackgroundColor}
                />
                <path
                  d={`M ${effectiveGridSpacing} 0 L 0 0 0 ${effectiveGridSpacing}`}
                  fill="none"
                  stroke={effectiveGridColor}
                  strokeWidth={effectiveThickness}
                />
              </pattern>
            )}
            <filter id={selectionGlowId} x="-50%" y="-50%" width="200%" height="200%">
              <feDropShadow
                dx="0"
                dy="0"
                stdDeviation="3"
                floodColor="#0ea5e9"
                floodOpacity="0.8"
              />
            </filter>
            <marker
              id="canvas-arrow"
              markerWidth="8"
              markerHeight="8"
              refX="8"
              refY="4"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 8 4 L 0 8 z" fill="#475569" />
            </marker>
          </defs>
          <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
            <rect
              x={-GRID_EXTENT / 2}
              y={-GRID_EXTENT / 2}
              width={GRID_EXTENT}
              height={GRID_EXTENT}
              fill={
                effectiveShowGrid ? `url(#${gridPatternId})` : effectiveBackgroundColor
              }
              pointerEvents="none"
            />
            {graph.edges.map((edge) => {
              const source = renderedNodes.find((node) => node.id === edge.source_id);
              const target = renderedNodes.find((node) => node.id === edge.target_id);
              if (!source || !target) {
                return null;
              }
              const isEdgeSelected = selectedEdgeId === edge.id;
              const isWholeSelected =
                isEdgeSelected && selectedEdgeScope === "whole";
              const isMainlineSelected =
                isEdgeSelected && selectedEdgeScope === "mainline";
              const sourceIds =
                (Array.isArray((edge as any).source_ids) && (edge as any).source_ids.length > 0
                  ? ((edge as any).source_ids as string[])
                  : [edge.source_id]) ?? [edge.source_id];
              const targetIds =
                (Array.isArray((edge as any).target_ids) && (edge as any).target_ids.length > 0
                  ? ((edge as any).target_ids as string[])
                  : [edge.target_id]) ?? [edge.target_id];
              const x1 = source.x ?? 0;
              const y1 = source.y ?? 0;
              const x2 = target.x ?? 0;
              const y2 = target.y ?? 0;
              const midX = (x1 + x2) / 2;
              const midY = (y1 + y2) / 2;
              const angleDeg =
                (Math.atan2((y2 ?? 0) - (y1 ?? 0), (x2 ?? 0) - (x1 ?? 0)) * 180) / Math.PI;
              const isAttachHoverEdge =
                dragState?.type === "edge" &&
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
              const tailTouchActive =
                touchConnectSource?.kind === "hyper" &&
                touchConnectSource.edgeId === edge.id &&
                touchConnectSource.role === "tail";
              const headTouchActive =
                touchConnectSource?.kind === "hyper" &&
                touchConnectSource.edgeId === edge.id &&
                touchConnectSource.role === "head";
            // Each edge is split into "outer" and "inner" segments so the selection scope can
            // highlight the mainline or the entire hyper-edge structure independently.
            const hitSegments: Array<{
                key: string;
                start: { x: number; y: number };
                end: { x: number; y: number };
                scope: "mainline" | "whole";
                width: number;
              }> = [
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
              return (
                <g
                  key={edge.id}
                  data-edge-group={edge.id}
                  data-edge-id={edge.id}
                  style={{ cursor: "pointer" }}
                >
                  {hitSegments.map((segment) => (
                    <line
                      key={`edge-hit-${segment.key}`}
                      data-edge-hit={`${edge.id}:${segment.key}`}
                      x1={segment.start.x}
                      y1={segment.start.y}
                      x2={segment.end.x}
                      y2={segment.end.y}
                      stroke="transparent"
                      strokeWidth={segment.width}
                      opacity={0}
                      pointerEvents="stroke"
                      onClick={(event) => {
                        event.stopPropagation();
                        onSelectEdge?.(edge.id);
                        onSelectSegment?.(null);
                        onSelectNode?.(null);
                        onEdgeScopeChange?.(segment.scope);
                      }}
                    />
                  ))}
                  {showHyperHandles &&
                    sourceIds.map((nodeId) => {
                      const anchor =
                        nodePositionMap[nodeId] ??
                        (allowEdgeAttachments ? edgeMidpoints[nodeId] : undefined);
                      if (!anchor) return null;
                      const isEdgeAnchor = !nodePositionMap[nodeId];
                      const isSegmentSelected =
                        selectedSegment?.edgeId === edge.id &&
                        selectedSegment.kind === "tail" &&
                        selectedSegment.memberId === nodeId;
                      const connectorHighlighted = isSegmentSelected || isWholeSelected;
                      const connectorColor = connectorHighlighted ? "#0f766e" : "#f97316";
                      const connectorWidth = connectorHighlighted ? 5 : 2;
                      const connectorOpacity = connectorHighlighted ? 1 : 0.6;
                      return (
                        <line
                          key={`${edge.id}-tail-connector-${nodeId}`}
                          data-hyper-segment={`${edge.id}:tail:${nodeId}`}
                          x1={anchor.x}
                          y1={anchor.y}
                          x2={tailHandlePos.x}
                          y2={tailHandlePos.y}
                          stroke={connectorColor}
                          strokeWidth={connectorWidth}
                          opacity={connectorOpacity}
                          strokeDasharray={isEdgeAnchor ? "4 3" : undefined}
                          pointerEvents="stroke"
                          strokeLinecap="round"
                          style={{ cursor: "pointer" }}
                          filter={isSegmentSelected ? `url(#${selectionGlowId})` : undefined}
                          onClick={(segmentEvent) => {
                            segmentEvent.stopPropagation();
                            onSelectEdge?.(edge.id);
                            onSelectNode?.(null);
                            onSelectSegment?.({
                              edgeId: edge.id,
                              kind: "tail",
                              memberId: nodeId,
                            });
                            onEdgeScopeChange?.("none");
                          }}
                        />
                      );
                    })}
                  {showHyperHandles &&
                    targetIds.map((nodeId) => {
                      const anchor =
                        nodePositionMap[nodeId] ??
                        (allowEdgeAttachments ? edgeMidpoints[nodeId] : undefined);
                      if (!anchor) return null;
                      const isEdgeAnchor = !nodePositionMap[nodeId];
                      const isSegmentSelected =
                        selectedSegment?.edgeId === edge.id &&
                        selectedSegment.kind === "head" &&
                        selectedSegment.memberId === nodeId;
                      const connectorHighlighted = isSegmentSelected || isWholeSelected;
                      const connectorColor = connectorHighlighted ? "#0369a1" : "#0ea5e9";
                      const connectorWidth = connectorHighlighted ? 5 : 2;
                      const connectorOpacity = connectorHighlighted ? 1 : 0.6;
                      return (
                        <line
                          key={`${edge.id}-head-connector-${nodeId}`}
                          data-hyper-segment={`${edge.id}:head:${nodeId}`}
                          x1={anchor.x}
                          y1={anchor.y}
                          x2={headHandlePos.x}
                          y2={headHandlePos.y}
                          stroke={connectorColor}
                          strokeWidth={connectorWidth}
                          opacity={connectorOpacity}
                          strokeDasharray={isEdgeAnchor ? "4 3" : undefined}
                          pointerEvents="stroke"
                          strokeLinecap="round"
                          style={{ cursor: "pointer" }}
                          filter={isSegmentSelected ? `url(#${selectionGlowId})` : undefined}
                          onClick={(segmentEvent) => {
                            segmentEvent.stopPropagation();
                            onSelectEdge?.(edge.id);
                            onSelectNode?.(null);
                            onSelectSegment?.({
                              edgeId: edge.id,
                              kind: "head",
                              memberId: nodeId,
                            });
                            onEdgeScopeChange?.("none");
                          }}
                        />
                      );
                    })}
                  <line
                    x1={x1}
                    y1={y1}
                    x2={x2}
                    y2={y2}
                    stroke={strokeColor}
                    strokeWidth={strokeWidth}
                    opacity={0.9}
                    strokeDasharray={strokeDasharray}
                    filter={showSelectionGlow ? `url(#${selectionGlowId})` : undefined}
                    strokeLinecap="round"
                    pointerEvents="none"
                  />
                  {isDirected && (
                    <g
                      transform={`translate(${midX}, ${midY}) rotate(${angleDeg})`}
                      style={{ pointerEvents: "none" }}
                    >
                      <line
                        x1={-10}
                        y1={0}
                        x2={10}
                        y2={0}
                        stroke={strokeColor}
                        strokeWidth={strokeWidth}
                        opacity={0.9}
                        strokeDasharray={strokeDasharray}
                        filter={showSelectionGlow ? `url(#${selectionGlowId})` : undefined}
                      />
                      <polygon
                        points="10,0 0,-5 0,5"
                        fill={
                          isWholeSelected
                            ? "#0ea5e9"
                            : isMainlineSelected
                              ? "#f97316"
                              : "#94a3b8"
                        }
                      />
                    </g>
                  )}
                  {showHyperHandles && (
                    <>
                      <circle
                        data-hyper-handle={`${edge.id}:tail`}
                        data-anchor-x={tailHandlePos.x}
                        data-anchor-y={tailHandlePos.y}
                        data-allow-edge-targets={allowEdgeAttachments ? "true" : "false"}
                        cx={tailHandlePos.x}
                        cy={tailHandlePos.y}
                        r={7}
                        fill={tailTouchActive ? "#fde047" : "#fef3c7"}
                        stroke={tailTouchActive ? "#d97706" : "#f97316"}
                        strokeWidth={tailTouchActive ? 3 : 2}
                        style={{ cursor: "crosshair" }}
                      />
                      <circle
                        data-hyper-handle={`${edge.id}:head`}
                        data-anchor-x={headHandlePos.x}
                        data-anchor-y={headHandlePos.y}
                        data-allow-edge-targets={allowEdgeAttachments ? "true" : "false"}
                        cx={headHandlePos.x}
                        cy={headHandlePos.y}
                        r={7}
                        fill={headTouchActive ? "#bae6fd" : "#e0f2fe"}
                        stroke={headTouchActive ? "#0369a1" : "#0284c7"}
                        strokeWidth={headTouchActive ? 3 : 2}
                        style={{ cursor: "crosshair" }}
                      />
                    </>
                  )}
                </g>
              );
            })}
            {dragState?.type === "edge" && (
              <>
                <line
                  x1={dragState.anchorPos.x}
                  y1={dragState.anchorPos.y}
                  x2={dragState.currentPos.x}
                  y2={dragState.currentPos.y}
                  stroke="#f97316"
                  strokeWidth={2}
                  strokeDasharray="4 4"
                />
                <g
                  transform={`translate(${(dragState.anchorPos.x + dragState.currentPos.x) / 2}, ${(dragState.anchorPos.y + dragState.currentPos.y) / 2
                    }) rotate(${(Math.atan2(
                      dragState.currentPos.y - dragState.anchorPos.y,
                      dragState.currentPos.x - dragState.anchorPos.x,
                    ) *
                      180) /
                    Math.PI
                    })`}
                >
                  <polygon points="8,0 0,-4 0,4" fill="#f97316" />
                </g>
              </>
            )}
            {renderedNodes.map((node) => {
              const isSelected = selectedNodeId === node.id;
              const rawLabel = node.text ?? node.metadata?.label ?? node.id;
              const label =
                typeof rawLabel === "string"
                  ? rawLabel
                  : String(rawLabel ?? "");
              const isEdgeHover =
                dragState?.type === "edge" && dragState.hoverTargetId === node.id;
              const isTouchSourceActive =
                touchConnectSource?.kind === "node" &&
                touchConnectSource.nodeId === node.id;
              return (
                <g key={node.id} transform={`translate(${node.x ?? 0}, ${node.y ?? 0})`}>
                  {onConnectNodes && (
                    <>
                      {isCoarsePointer && (
                        <circle
                          data-node-handle={node.id}
                          r={isSelected ? 33 : 29}
                          fill="none"
                          stroke="transparent"
                          strokeWidth={24}
                          pointerEvents="stroke"
                        />
                      )}
                      <circle
                        data-node-handle={node.id}
                        r={isSelected ? 32 : 28}
                        fill="transparent"
                        stroke={
                          isTouchSourceActive
                            ? "#facc15"
                            : dragState?.type === "edge" &&
                                dragState.mode === "new" &&
                                dragState.anchorNodeId === node.id
                              ? "#f97316"
                              : "rgba(148, 163, 184, 0.5)"
                        }
                        strokeDasharray={isTouchSourceActive ? "0" : "6 4"}
                        strokeWidth={isTouchSourceActive ? 4 : 2.5}
                        style={{ pointerEvents: "stroke", cursor: "crosshair" }}
                      />
                    </>
                  )}
                  <circle
                    data-node-id={node.id}
                    r={isSelected ? 26 : 22}
                    fill={isSelected ? "#2563eb" : "#3b82f6"}
                    opacity={0.9}
                    stroke={
                      isEdgeHover ? "#f97316" : isSelected ? "#1e40af" : "transparent"
                    }
                    strokeWidth={isEdgeHover ? 3 : 2}
                  />
                  <text
                    data-node-id={node.id}
                    textAnchor="middle"
                    fill="#fff"
                    fontSize="12"
                    dy="0.35em"
                    fontWeight="600"
                  >
                    {label}
                  </text>
                </g>
              );
            })}
            {renderEdgeHandles()}
          </g>
        </svg>
      </div>
    </section>
  );
}

