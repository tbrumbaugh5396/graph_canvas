import { useCallback, useEffect, useRef, useState } from "react";
import { GraphList } from "./components/GraphList";
import { GraphForm } from "./components/GraphForm";
import { GraphDetails } from "./components/GraphDetails";
import { GraphCanvas } from "./components/GraphCanvas";
import { GraphInspector } from "./components/GraphInspector";
import { GridControls } from "./components/GridControls";
import { GraphTaskList, type TaskStatus, type TaskFormData } from "./components/GraphTaskList";
import "./App.css";
import {
  createGraph,
  deleteGraph,
  createNode,
  updateNode,
  deleteNode,
  createEdge,
  updateEdge,
  deleteEdge,
  updateNodePositions,
  updateGraphSettings,
  replaceGraph,
} from "./api";
import type {
  EdgeInput,
  GraphDTO,
  GraphSettingsInput,
  NodeDTO,
  NodeInput,
} from "./types";
import { useGraphWorkspace } from "./hooks/useGraphWorkspace";

const rgbArrayToHex = (arr?: number[]) => {
  if (!arr || arr.length < 3) {
    return "#f8fafc";
  }
  return `#${arr
    .slice(0, 3)
    .map((value) => {
      const clamped = Math.max(0, Math.min(255, value));
      return clamped.toString(16).padStart(2, "0");
    })
    .join("")}`;
};

const hexToRgbArray = (hex: string): number[] => {
  const normalized = hex.replace("#", "");
  const chunkSize = normalized.length === 3 ? 1 : 2;
  const expanded =
    chunkSize === 1
      ? normalized
        .split("")
        .map((char) => char + char)
        .join("")
      : normalized.padEnd(6, "0");
  const result = [];
  for (let i = 0; i < 6; i += 2) {
    result.push(parseInt(expanded.slice(i, i + 2), 16));
  }
  return result;
};

const UI_PREFERENCES_KEY = "graph-canvas-web-ui";
const MAX_HISTORY = 50;

const cloneGraph = (graph?: GraphDTO | null): GraphDTO | null =>
  graph ? JSON.parse(JSON.stringify(graph)) : null;

type StoredUIState = {
  selectedGraphId?: string | null;
  gridVisible?: boolean;
  gridColorHex?: string;
  backgroundHex?: string;
  gridSpacing?: number;
  gridThickness?: number;
  viewMode?: "canvas" | "list";
};

type SelectedSegment = {
  edgeId: string;
  kind: "head" | "tail";
  memberId: string;
};

export default function App() {
  // Centralised graph + selection state lives inside a dedicated hook so this component
  // can stay focused on UI orchestration instead of request plumbing.
  const {
    graphs,
    selectedGraphId,
    selectedGraph,
    isLoading,
    error,
    setError,
    setSelectedGraphId,
    loadGraphs,
  } = useGraphWorkspace(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null);
  const [selectedSegment, setSelectedSegment] = useState<SelectedSegment | null>(null);
  const [edgeSelectionScope, setEdgeSelectionScope] = useState<"none" | "mainline" | "whole">(
    "none",
  );
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [isCanvasFullscreen, setIsCanvasFullscreen] = useState(false);
  const [uiHydrated, setUiHydrated] = useState(false);
  const [graphNameDraft, setGraphNameDraft] = useState("");
  const [graphTypeDraft, setGraphTypeDraft] = useState("graph");
  const [directedDraft, setDirectedDraft] = useState(true);
  const [isRenamingGraph, setIsRenamingGraph] = useState(false);
  const [deletingGraphId, setDeletingGraphId] = useState<string | null>(null);
  const [history, setHistory] = useState<GraphDTO[]>([]);
  const [future, setFuture] = useState<GraphDTO[]>([]);
  const [clipboard, setClipboard] = useState<{ type: "node"; data: NodeDTO } | null>(
    null,
  );
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const restoringRef = useRef(false);

  const [gridVisible, setGridVisible] = useState(true);
  const [gridColorHex, setGridColorHex] = useState("#e2e8f0");
  const [backgroundHex, setBackgroundHex] = useState("#f8fafc");
  const [gridSpacing, setGridSpacing] = useState(20);
  const [gridThickness, setGridThickness] = useState(1);
  const [workspaceView, setWorkspaceView] = useState<"canvas" | "list">("canvas");

  useEffect(() => {
    if (typeof window === "undefined") {
      setUiHydrated(true);
      return;
    }
    try {
      const raw = window.localStorage.getItem(UI_PREFERENCES_KEY);
      if (!raw) {
        setUiHydrated(true);
        return;
      }
      const stored: StoredUIState = JSON.parse(raw);
      if (stored.selectedGraphId) {
        setSelectedGraphId(stored.selectedGraphId);
      }
      if (stored.gridVisible !== undefined) {
        setGridVisible(stored.gridVisible);
      }
      if (stored.gridColorHex) {
        setGridColorHex(stored.gridColorHex);
      }
      if (stored.backgroundHex) {
        setBackgroundHex(stored.backgroundHex);
      }
      if (stored.gridSpacing !== undefined) {
        setGridSpacing(stored.gridSpacing);
      }
      if (stored.gridThickness !== undefined) {
        setGridThickness(stored.gridThickness);
      }
      if (stored.viewMode === "canvas" || stored.viewMode === "list") {
        setWorkspaceView(stored.viewMode);
      }
    } catch (err) {
      console.warn("Failed to restore UI state", err);
    }
    setUiHydrated(true);
  }, []);

  useEffect(() => {
    if (!uiHydrated) {
      return;
    }
    loadGraphs();
  }, [uiHydrated, loadGraphs]);

  useEffect(() => {
    setSelectedNodeId(null);
    setSelectedEdgeId(null);
    setSelectedSegment(null);
    setEdgeSelectionScope("none");
    setIsCanvasFullscreen(false);
    setHistory([]);
    setFuture([]);
  }, [selectedGraphId]);

  useEffect(() => {
    if (!selectedEdgeId) {
      setEdgeSelectionScope("none");
    }
  }, [selectedEdgeId]);

  useEffect(() => {
    if (!selectedGraph) {
      setGraphNameDraft("");
      setGraphTypeDraft("graph");
      setDirectedDraft(true);
      return;
    }
    setGridVisible(selectedGraph.grid_visible ?? true);
    setGridColorHex(rgbArrayToHex(selectedGraph.grid_color ?? [226, 232, 240]));
    setBackgroundHex(
      rgbArrayToHex(selectedGraph.background_color ?? [248, 250, 252]),
    );
    setGridSpacing(selectedGraph.grid_size ?? 20);
    setGridThickness(selectedGraph.grid_line_thickness ?? 1);
    setGraphNameDraft(selectedGraph.name);
    setGraphTypeDraft(selectedGraph.graph_type ?? "graph");
    setDirectedDraft(selectedGraph.directed ?? true);
  }, [selectedGraph?.id, selectedGraph?.graph_type, selectedGraph?.directed]);

  const pushHistory = useCallback(() => {
    if (restoringRef.current) {
      return;
    }
    const snapshot = cloneGraph(selectedGraph);
    if (!snapshot) {
      return;
    }
    setHistory((prev) => {
      const next = [...prev, snapshot];
      return next.length > MAX_HISTORY ? next.slice(next.length - MAX_HISTORY) : next;
    });
    setFuture([]);
  }, [selectedGraph]);

  const restoreSnapshot = useCallback(
    (snapshot: GraphDTO, label: string) => {
      if (!selectedGraphId) return Promise.resolve();
      restoringRef.current = true;
      return withStatus(
        () => replaceGraph(selectedGraphId, snapshot),
        label,
      ).finally(() => {
        restoringRef.current = false;
      });
    },
    [selectedGraphId],
  );

  const handleUndo = useCallback(() => {
    if (!selectedGraph || !selectedGraphId || history.length === 0) {
      return Promise.resolve();
    }
    const snapshot = history[history.length - 1];
    const currentSnapshot = cloneGraph(selectedGraph);
    if (!currentSnapshot) {
      return Promise.resolve();
    }
    setHistory((prev) => prev.slice(0, -1));
    setFuture((prev) => {
      const next = [...prev, currentSnapshot];
      return next.length > MAX_HISTORY ? next.slice(next.length - MAX_HISTORY) : next;
    });
    return restoreSnapshot(snapshot, "Undone change");
  }, [history, selectedGraph, selectedGraphId, restoreSnapshot]);

  const handleRedo = useCallback(() => {
    if (!selectedGraph || !selectedGraphId || future.length === 0) {
      return Promise.resolve();
    }
    const snapshot = future[future.length - 1];
    const currentSnapshot = cloneGraph(selectedGraph);
    if (!currentSnapshot) {
      return Promise.resolve();
    }
    setFuture((prev) => prev.slice(0, -1));
    setHistory((prev) => {
      const next = [...prev, currentSnapshot];
      return next.length > MAX_HISTORY ? next.slice(next.length - MAX_HISTORY) : next;
    });
    return restoreSnapshot(snapshot, "Redone change");
  }, [future, selectedGraph, selectedGraphId, restoreSnapshot]);


  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    const snapshot: StoredUIState = {
      selectedGraphId,
      gridVisible,
      gridColorHex,
      backgroundHex,
      gridSpacing,
      gridThickness,
      viewMode: workspaceView,
    };
    window.localStorage.setItem(UI_PREFERENCES_KEY, JSON.stringify(snapshot));
  }, [
    selectedGraphId,
    gridVisible,
    gridColorHex,
    backgroundHex,
    gridSpacing,
    gridThickness,
    workspaceView,
  ]);

  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    if (isCanvasFullscreen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [isCanvasFullscreen]);

  async function handleCreate(graph: GraphDTO) {
    try {
      await createGraph(graph);
      await loadGraphs(false);
      setSelectedGraphId(graph.id);
      setStatusMessage("Graph created");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create graph");
    }
  }

  async function withStatus<T>(action: () => Promise<T>, message: string) {
    try {
      await action();
      setStatusMessage(message);
      setError(null);
      await loadGraphs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Operation failed");
    }
  }

  const handleCreateNode = (input: NodeInput) => {
    if (!selectedGraphId) return Promise.resolve();
    pushHistory();
    return withStatus(
      () => createNode(selectedGraphId, input),
      "Node created",
    );
  };

  const handleUpdateNode = (nodeId: string, input: NodeInput) => {
    if (!selectedGraphId) return Promise.resolve();
    pushHistory();
    return withStatus(
      () => updateNode(selectedGraphId, nodeId, input),
      "Node updated",
    );
  };

  const handleDeleteNode = (nodeId: string) => {
    if (!selectedGraphId) return Promise.resolve();
    if (selectedNodeId === nodeId) {
      setSelectedNodeId(null);
    }
    if (selectedSegment) {
      setSelectedSegment(null);
    }
    if (selectedEdgeId) {
      setSelectedEdgeId(null);
      setEdgeSelectionScope("none");
    }
    pushHistory();
    return withStatus(
      () => deleteNode(selectedGraphId, nodeId),
      "Node deleted",
    );
  };

  const handleCreateEdge = (
    input: EdgeInput & { source_id: string; target_id: string },
  ) => {
    if (!selectedGraphId) return Promise.resolve();
    pushHistory();
    return withStatus(
      () => createEdge(selectedGraphId, input),
      "Edge created",
    );
  };

  const handleUpdateEdge = (
    edgeId: string,
    input: EdgeInput & { source_id?: string; target_id?: string },
  ) => {
    if (!selectedGraphId) return Promise.resolve();
    pushHistory();
    return withStatus(
      () => updateEdge(selectedGraphId, edgeId, input),
      "Edge updated",
    );
  };

  const handleDeleteEdge = (edgeId: string) => {
    if (!selectedGraphId) return Promise.resolve();
    if (selectedEdgeId === edgeId) {
      setSelectedEdgeId(null);
      setEdgeSelectionScope("none");
    }
    if (selectedSegment && selectedSegment.edgeId === edgeId) {
      setSelectedSegment(null);
    }
    pushHistory();
    return withStatus(
      () => deleteEdge(selectedGraphId, edgeId),
      "Edge deleted",
    );
  };

  const handleReconnectEdge = (
    edgeId: string,
    updates: { source_id?: string; target_id?: string },
  ) => {
    if (!selectedGraphId) return Promise.resolve();
    pushHistory();
    return withStatus(
      async () => {
        await updateEdge(selectedGraphId, edgeId, updates);
        setSelectedEdgeId(edgeId);
        setEdgeSelectionScope("whole");
        setSelectedSegment(null);
      },
      "Edge updated",
    );
  };

  const handleConnectNodes = (sourceId: string, targetId: string) => {
    if (!selectedGraphId) return Promise.resolve();
    pushHistory();
    return withStatus(
      async () => {
        const edge = await createEdge(selectedGraphId, {
          source_id: sourceId,
          target_id: targetId,
        });
        setSelectedEdgeId(edge.id);
        setEdgeSelectionScope("whole");
        setSelectedSegment(null);
        return edge;
      },
      "Edge created",
    );
  };

  const handleNodePositionChange = (nodeId: string, x: number, y: number) => {
    if (!selectedGraphId) return;
    pushHistory();
    updateNodePositions(selectedGraphId, [{ id: nodeId, x, y }]).catch((err) => {
      setError(err instanceof Error ? err.message : "Failed to move node");
    });
  };

  const handleCanvasAddNode = async (x: number, y: number) => {
    if (!selectedGraphId) return;
    try {
      pushHistory();
      const node = await createNode(selectedGraphId, { x, y, text: "Node" });
      setStatusMessage("Node created");
      setError(null);
      await loadGraphs();
      setSelectedNodeId(node.id);
      return node;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add node");
    }
  };

  const handleDeleteGraph = (graphId: string) => {
    if (!graphId) return Promise.resolve();
    const proceed =
      typeof window === "undefined" ? true : window.confirm("Delete this graph?");
    if (!proceed) {
      return Promise.resolve();
    }
    if (graphId === selectedGraphId) {
      setSelectedGraphId(null);
      setSelectedNodeId(null);
      setSelectedEdgeId(null);
      setSelectedSegment(null);
      setEdgeSelectionScope("none");
      setGraphNameDraft("");
      setGraphTypeDraft("graph");
      setDirectedDraft(true);
    }
    setDeletingGraphId(graphId);
    return withStatus(
      () => deleteGraph(graphId),
      "Graph deleted",
    )
      .catch(() => undefined)
      .finally(() => {
        setDeletingGraphId((prev) => (prev === graphId ? null : prev));
      });
  };

  const handleSaveGraphInfo = () => {
    if (!selectedGraphId || !selectedGraph) return Promise.resolve();
    const trimmed = graphNameDraft.trim();
    const payload: GraphSettingsInput = {};
    if (trimmed && trimmed !== selectedGraph.name) {
      payload.name = trimmed;
    }
    const normalizedType = graphTypeDraft || "graph";
    if (normalizedType !== (selectedGraph.graph_type ?? "graph")) {
      payload.graph_type = normalizedType;
    }
    if ((directedDraft ?? true) !== (selectedGraph.directed ?? true)) {
      payload.directed = directedDraft;
    }
    if (
      !payload.name &&
      payload.graph_type === undefined &&
      payload.directed === undefined
    ) {
      return Promise.resolve();
    }
    pushHistory();
    setIsRenamingGraph(true);
    return withStatus(
      () => updateGraphSettings(selectedGraphId, payload),
      "Graph settings updated",
    ).finally(() => setIsRenamingGraph(false));
  };

  const handleAttachEdgeMember = (
    edgeId: string,
    attachment: { kind: "head" | "tail"; targetNodeId?: string; targetEdgeId?: string },
  ) => {
    if (!selectedGraphId || !selectedGraph) return Promise.resolve();
    const edge = selectedGraph.edges.find((item) => item.id === edgeId);
    if (!edge) return Promise.resolve();

    const extractIds = (value: unknown, fallback: string | undefined) => {
      if (Array.isArray(value)) {
        return value.filter((item): item is string => typeof item === "string");
      }
      return fallback ? [fallback] : [];
    };

    const currentSourceIds = extractIds((edge as any).source_ids, edge.source_id);
    const currentTargetIds = extractIds((edge as any).target_ids, edge.target_id);
    const addition = attachment.targetNodeId ?? attachment.targetEdgeId;
    const payload: EdgeInput & { source_ids?: string[]; target_ids?: string[] } = {};

    if (attachment.kind === "tail" && addition) {
      payload.source_ids = Array.from(new Set([...currentSourceIds, addition]));
    }
    if (attachment.kind === "head" && addition) {
      payload.target_ids = Array.from(new Set([...currentTargetIds, addition]));
    }

    if (!payload.source_ids && !payload.target_ids) {
      return Promise.resolve();
    }
    pushHistory();

    return withStatus(
      async () => {
        await updateEdge(selectedGraphId, edgeId, payload);
        setSelectedEdgeId(edgeId);
        setSelectedSegment(null);
      },
      "Edge updated",
    );
  };

  const handleDetachEdgeMember = (
    edgeId: string,
    attachment: { kind: "head" | "tail"; memberId: string },
  ) => {
    if (!selectedGraphId || !selectedGraph) return Promise.resolve();
    const edge = selectedGraph.edges.find((item) => item.id === edgeId);
    if (!edge) return Promise.resolve();

    const extractIds = (value: unknown, fallback: string | undefined) => {
      if (Array.isArray(value)) {
        return value.filter((item): item is string => typeof item === "string");
      }
      return fallback ? [fallback] : [];
    };

    const currentSourceIds = extractIds((edge as any).source_ids, edge.source_id);
    const currentTargetIds = extractIds((edge as any).target_ids, edge.target_id);

    let payload: EdgeInput & { source_ids?: string[]; target_ids?: string[] } = {};
    if (attachment.kind === "tail") {
      const nextSources = currentSourceIds.filter((id) => id !== attachment.memberId);
      if (
        nextSources.length === currentSourceIds.length ||
        nextSources.length === 0
      ) {
        return Promise.resolve();
      }
      payload.source_ids = nextSources;
    } else {
      const nextTargets = currentTargetIds.filter((id) => id !== attachment.memberId);
      if (
        nextTargets.length === currentTargetIds.length ||
        nextTargets.length === 0
      ) {
        return Promise.resolve();
      }
      payload.target_ids = nextTargets;
    }
    pushHistory();

    return withStatus(
      async () => {
        await updateEdge(selectedGraphId, edgeId, payload);
        setSelectedEdgeId(edgeId);
      },
      "Edge updated",
    );
  };

  const handleSelectSegment = (segment: SelectedSegment | null) => {
    setSelectedSegment(segment);
    if (segment) {
      setSelectedEdgeId(segment.edgeId);
      setSelectedNodeId(null);
      setEdgeSelectionScope("none");
    }
  };

  const handlePanelSelectEdge = useCallback((id: string | null) => {
    setSelectedEdgeId(id);
    setSelectedNodeId(null);
    setSelectedSegment(null);
    setEdgeSelectionScope(id ? "whole" : "none");
  }, []);

  const handleCanvasSelectEdge = useCallback((id: string | null) => {
    setSelectedEdgeId(id);
    setSelectedNodeId(null);
    setSelectedSegment(null);
    if (!id) {
      setEdgeSelectionScope("none");
    }
  }, []);

  const getNextTaskPosition = () => {
    const nodes = selectedGraph?.nodes ?? [];
    if (nodes.length === 0) {
      return { x: 0, y: 0 };
    }
    const yValues = nodes
      .map((node) => (typeof node.y === "number" ? node.y : null))
      .filter((value): value is number => value !== null && Number.isFinite(value));
    if (yValues.length === 0) {
      return { x: 0, y: 0 };
    }
    const maxY = Math.max(...yValues);
    return { x: 0, y: maxY + 100 };
  };

  const handleCreateTask = (input: TaskFormData) => {
    if (!selectedGraphId) return Promise.resolve();
    const { label, prereqIds, postIds } = input;
    pushHistory();
    return withStatus(
      async () => {
        const { x, y } = getNextTaskPosition();
        const newNode = await createNode(selectedGraphId, { text: label, x, y });
        const prereqSet = new Set(
          prereqIds.filter((id) => id && id !== newNode.id),
        );
        for (const sourceId of prereqSet) {
          await createEdge(selectedGraphId, {
            source_id: sourceId,
            target_id: newNode.id,
          });
        }
        const postSet = new Set(postIds.filter((id) => id && id !== newNode.id));
        for (const targetId of postSet) {
          await createEdge(selectedGraphId, {
            source_id: newNode.id,
            target_id: targetId,
          });
        }
      },
      "Task created",
    );
  };

  const handleEditTask = (nodeId: string, input: TaskFormData) => {
    if (!selectedGraphId || !selectedGraph) return Promise.resolve();
    const targetNode = selectedGraph.nodes.find((node) => node.id === nodeId);
    if (!targetNode) {
      return Promise.resolve();
    }
    const { label, prereqIds, postIds } = input;
    const desiredPrereqs = new Set(prereqIds.filter((id) => id && id !== nodeId));
    const desiredPosts = new Set(postIds.filter((id) => id && id !== nodeId));
    const incoming = selectedGraph.edges.filter((edge) => edge.target_id === nodeId);
    const outgoing = selectedGraph.edges.filter((edge) => edge.source_id === nodeId);
    pushHistory();
    return withStatus(
      async () => {
        if ((targetNode.text ?? "") !== label) {
          await updateNode(selectedGraphId, nodeId, { text: label });
        }
        for (const edge of incoming) {
          if (!desiredPrereqs.has(edge.source_id)) {
            await deleteEdge(selectedGraphId, edge.id);
          }
        }
        const existingPrereqs = new Set(incoming.map((edge) => edge.source_id));
        for (const sourceId of desiredPrereqs) {
          if (!existingPrereqs.has(sourceId)) {
            await createEdge(selectedGraphId, { source_id: sourceId, target_id: nodeId });
          }
        }
        for (const edge of outgoing) {
          if (!desiredPosts.has(edge.target_id)) {
            await deleteEdge(selectedGraphId, edge.id);
          }
        }
        const existingPosts = new Set(outgoing.map((edge) => edge.target_id));
        for (const targetId of desiredPosts) {
          if (!existingPosts.has(targetId)) {
            await createEdge(selectedGraphId, { source_id: nodeId, target_id: targetId });
          }
        }
      },
      "Task updated",
    );
  };

  const handleCopy = useCallback(() => {
    if (!selectedGraph || !selectedNodeId) {
      return;
    }
    const node = selectedGraph.nodes.find((item) => item.id === selectedNodeId);
    if (node) {
      setClipboard({ type: "node", data: JSON.parse(JSON.stringify(node)) });
    }
  }, [selectedGraph, selectedNodeId]);

  const handleCut = useCallback(() => {
    handleCopy();
    if (selectedNodeId) {
      void handleDeleteNode(selectedNodeId);
    }
  }, [handleCopy, handleDeleteNode, selectedNodeId]);

  const handlePaste = useCallback(() => {
    if (!clipboard || !selectedGraphId) {
      return Promise.resolve();
    }
    if (clipboard.type === "node") {
      const node = clipboard.data;
      pushHistory();
      return withStatus(
        () =>
          createNode(selectedGraphId, {
            text: node.text,
            metadata: node.metadata,
            x: (node.x ?? 0) + 24,
            y: (node.y ?? 0) + 24,
          }),
        "Node pasted",
      );
    }
    return Promise.resolve();
  }, [clipboard, pushHistory, selectedGraphId]);

  const handleSaveGraphToFile = () => {
    const graph = graphs.find((g) => g.id === selectedGraphId);
    if (!graph) {
      setError("Select a graph to save.");
      return;
    }
    const blob = new Blob([JSON.stringify(graph, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${graph.name || graph.id}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleLoadGraphFromFile = () => {
    fileInputRef.current?.click();
  };

  const handleGraphFileChange = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      const text = await file.text();
      const parsed = JSON.parse(text);
      const normalized: GraphDTO = {
        id:
          typeof parsed.id === "string" && parsed.id.trim()
            ? parsed.id
            : crypto.randomUUID(),
        name:
          typeof parsed.name === "string" && parsed.name.trim()
            ? parsed.name
            : file.name.replace(/\.json$/i, "") || "Imported Graph",
        graph_type: parsed.graph_type ?? "graph",
        directed: parsed.directed ?? true,
        metadata: parsed.metadata ?? {},
        nodes: Array.isArray(parsed.nodes) ? parsed.nodes : [],
        edges: Array.isArray(parsed.edges) ? parsed.edges : [],
        background_color: parsed.background_color,
        grid_visible: parsed.grid_visible,
        grid_size: parsed.grid_size,
        grid_color: parsed.grid_color,
        grid_line_thickness: parsed.grid_line_thickness,
      };
      const exists = graphs.some((graph) => graph.id === normalized.id);
      if (exists) {
        await replaceGraph(normalized.id, normalized);
      } else {
        try {
          await createGraph(normalized);
        } catch {
          await replaceGraph(normalized.id, normalized);
        }
      }
      setStatusMessage("Graph loaded from file");
      setError(null);
      await loadGraphs(false);
      setSelectedGraphId(normalized.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load graph file");
    } finally {
      event.target.value = "";
    }
  };



  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.defaultPrevented) {
        return;
      }
      const target = event.target as HTMLElement | null;
      const isEditable =
        target &&
        (target.closest("input, textarea, select, [contenteditable='true']") ||
          target.isContentEditable);
      const isMeta = event.metaKey || event.ctrlKey;

      if (isMeta) {
        const key = event.key.toLowerCase();
        if (key === "z") {
          event.preventDefault();
          if (event.shiftKey) {
            void handleRedo();
          } else {
            void handleUndo();
          }
          return;
        }
        if (key === "y") {
          event.preventDefault();
          void handleRedo();
          return;
        }
      }

      if (
        (event.key === "Delete" || event.key === "Backspace") &&
        !isEditable &&
        !isMeta
      ) {
        if (selectedNodeId) {
          event.preventDefault();
          void handleDeleteNode(selectedNodeId);
        } else if (selectedSegment) {
          event.preventDefault();
          const segment = selectedSegment;
          setSelectedSegment(null);
          void handleDetachEdgeMember(segment.edgeId, {
            kind: segment.kind,
            memberId: segment.memberId,
          });
        } else if (selectedEdgeId) {
          event.preventDefault();
          void handleDeleteEdge(selectedEdgeId);
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [
    handleRedo,
    handleUndo,
    selectedEdgeId,
    selectedNodeId,
    selectedSegment,
    handleDeleteNode,
    handleDeleteEdge,
    handleCopy,
    handleCut,
    handlePaste,
    handleDetachEdgeMember,
  ]);

  const persistGridSettings = async (
    overrides: Partial<{
      visible: boolean;
      gridColor: string;
      backgroundColor: string;
      spacing: number;
      thickness: number;
    }> = {},
  ) => {
    if (!selectedGraphId) return;
    pushHistory();
    const payload = {
      grid_visible: overrides.visible ?? gridVisible,
      grid_size: Math.max(5, Math.min(400, overrides.spacing ?? gridSpacing)),
      grid_color: hexToRgbArray(overrides.gridColor ?? gridColorHex),
      background_color: hexToRgbArray(
        overrides.backgroundColor ?? backgroundHex,
      ),
      grid_line_thickness: Math.max(
        0.5,
        Math.min(10, overrides.thickness ?? gridThickness),
      ),
    };

    await withStatus(
      () => updateGraphSettings(selectedGraphId, payload),
      "Grid updated",
    );
  };

  const handleToggleGrid = () => {
    const next = !gridVisible;
    setGridVisible(next);
    void persistGridSettings({ visible: next });
  };

  const handleGridSettingsChange = (
    partial: Partial<{
      visible: boolean;
      gridColor: string;
      backgroundColor: string;
      spacing: number;
      thickness: number;
    }>,
  ) => {
    if (partial.visible !== undefined) {
      setGridVisible(partial.visible);
    }
    if (partial.gridColor !== undefined) {
      setGridColorHex(partial.gridColor);
    }
    if (partial.backgroundColor !== undefined) {
      setBackgroundHex(partial.backgroundColor);
    }
    if (partial.spacing !== undefined) {
      setGridSpacing(partial.spacing);
    }
    if (partial.thickness !== undefined) {
      setGridThickness(partial.thickness);
    }
  };

  const handleTaskStatusChange = (nodeId: string, nextStatus: TaskStatus | null) => {
    if (!selectedGraph) {
      return Promise.resolve();
    }
    const node = selectedGraph.nodes.find((item) => item.id === nodeId);
    if (!node) {
      return Promise.resolve();
    }
    const metadata = { ...(node.metadata as Record<string, unknown> | undefined) };
    const currentStatus =
      typeof metadata?.status === "string" ? (metadata.status as string) : null;
    if (currentStatus === nextStatus) {
      return Promise.resolve();
    }
    const nextMetadata: Record<string, unknown> = { ...(metadata ?? {}) };
    if (nextStatus) {
      nextMetadata.status = nextStatus;
    } else {
      delete nextMetadata.status;
    }
    return handleUpdateNode(nodeId, { metadata: nextMetadata });
  };

  return (
    <main className="app-shell">
      <header className="app-header">
        <p style={{ margin: 0, color: "#64748b", letterSpacing: 2 }}>Graph</p>
        <h1>A shared visual workspace</h1>
        <p style={{ maxWidth: 720 }}>
          A React workspace to collaborate with the shared Graph API. You can add nodes/edges,
          edit properties, and reposition elements directly in the browser with changes synced
          to the desktop client.
        </p>
        <div className="app-actions">
          <button
            type="button"
            onClick={handleSaveGraphToFile}
            disabled={!selectedGraph}
            style={{
              padding: "8px 16px",
              borderRadius: 6,
              border: "1px solid #0f172a",
              background: selectedGraph ? "#0f172a" : "#cbd5f5",
              color: "#fff",
              cursor: selectedGraph ? "pointer" : "not-allowed",
            }}
          >
            Save Graph
          </button>
          <button
            type="button"
            onClick={handleLoadGraphFromFile}
            style={{
              padding: "8px 16px",
              borderRadius: 6,
              border: "1px solid #0f172a",
              background: "#fff",
              color: "#0f172a",
              cursor: "pointer",
            }}
          >
            Load Graph
          </button>
        </div>
      </header>
      <input
        ref={fileInputRef}
        type="file"
        accept="application/json"
        style={{ display: "none" }}
        onChange={handleGraphFileChange}
      />
      <GraphForm onSubmit={handleCreate} />
      {error && (
        <p style={{ color: "#b91c1c" }}>
          Something went wrong while loading graphs: {error}
        </p>
      )}
      {statusMessage && !error && (
        <p style={{ color: "#15803d" }}>{statusMessage}</p>
      )}
      <GraphList
        graphs={graphs}
        onRefresh={loadGraphs}
        isLoading={isLoading}
        onSelect={(graph) => setSelectedGraphId(graph.id)}
        selectedGraphId={selectedGraphId}
        onDelete={(graph) => handleDeleteGraph(graph.id)}
        deletingGraphId={deletingGraphId}
      />
      <GraphDetails
        graph={selectedGraph}
        selectedNodeId={selectedNodeId}
        selectedEdgeId={selectedEdgeId}
        selectedSegment={selectedSegment}
        onSelectNode={(id) => {
          setSelectedNodeId(id);
          setSelectedEdgeId(null);
          setSelectedSegment(null);
          setEdgeSelectionScope("none");
        }}
        onSelectEdge={handlePanelSelectEdge}
        showGrid={gridVisible}
        onToggleGrid={handleToggleGrid}
        nameDraft={graphNameDraft}
        onNameChange={setGraphNameDraft}
        graphType={graphTypeDraft}
        onTypeChange={setGraphTypeDraft}
        directed={directedDraft}
        onDirectedChange={setDirectedDraft}
        onSaveName={() => handleSaveGraphInfo()}
        isSavingName={isRenamingGraph}
        onDeleteGraph={() => {
          if (selectedGraphId) {
            void handleDeleteGraph(selectedGraphId);
          }
        }}
        isDeletingGraph={
          !!selectedGraphId && deletingGraphId === selectedGraphId
        }
      />
      <GraphInspector
        graph={selectedGraph}
        selectedNodeId={selectedNodeId}
        selectedEdgeId={selectedEdgeId}
        onSelectNode={(id) => {
          setSelectedNodeId(id);
          if (id) {
            setSelectedEdgeId(null);
            setEdgeSelectionScope("none");
          }
          setSelectedSegment(null);
        }}
        onSelectEdge={handlePanelSelectEdge}
        onCreateNode={handleCreateNode}
        onUpdateNode={handleUpdateNode}
        onDeleteNode={handleDeleteNode}
        onCreateEdge={handleCreateEdge}
        onUpdateEdge={handleUpdateEdge}
        onDeleteEdge={handleDeleteEdge}
      />
      <GridControls
        visible={gridVisible}
        gridColor={gridColorHex}
        backgroundColor={backgroundHex}
        spacing={gridSpacing}
        thickness={gridThickness}
        onChange={handleGridSettingsChange}
        onApply={() => persistGridSettings()}
      />
      <section className="workspace-section">
        <div className="workspace-toolbar">
          <div>
            <p style={{ margin: 0, fontSize: 13, letterSpacing: 1, color: "#94a3b8" }}>
              WORKSPACE VIEW
            </p>
            <h2 style={{ margin: "6px 0 0", color: "#0f172a" }}>Graph Canvas & Dependency List</h2>
            <p style={{ margin: "4px 0 0", color: "#475569", maxWidth: 520 }}>
              Toggle between the interactive canvas and an ordered task list derived from the same graph.
            </p>
          </div>
          <div className="view-toggle">
            {(
              [
                { mode: "canvas", label: "Graph Canvas" },
                { mode: "list", label: "Dependency List" },
              ] as const
            ).map((option) => {
              const active = workspaceView === option.mode;
              return (
                <button
                  key={option.mode}
                  type="button"
                  onClick={() => setWorkspaceView(option.mode)}
                  style={{
                    border: "none",
                    borderRadius: 999,
                    padding: "8px 16px",
                    fontWeight: 600,
                    cursor: "pointer",
                    background: active ? "#0f172a" : "transparent",
                    color: active ? "#fff" : "#0f172a",
                    boxShadow: active ? "0 1px 2px rgba(15,23,42,0.25)" : "none",
                  }}
                >
                  {option.label}
                </button>
              );
            })}
          </div>
        </div>
        {workspaceView === "canvas" ? (
          <GraphCanvas
            graph={selectedGraph}
            selectedNodeId={selectedNodeId}
            selectedEdgeId={selectedEdgeId}
            selectedSegment={selectedSegment}
            selectedEdgeScope={edgeSelectionScope}
            onSelectNode={(id) => {
              setSelectedNodeId(id);
              setSelectedEdgeId(null);
              setSelectedSegment(null);
              setEdgeSelectionScope("none");
            }}
            onSelectEdge={handleCanvasSelectEdge}
            onEdgeScopeChange={(scope) => {
              setEdgeSelectionScope(scope);
            }}
            onSelectSegment={handleSelectSegment}
            onNodePositionChange={handleNodePositionChange}
            onCanvasAddNode={handleCanvasAddNode}
            onConnectNodes={handleConnectNodes}
            onReconnectEdge={handleReconnectEdge}
            onAttachEdgeMember={handleAttachEdgeMember}
            onDeleteNode={(nodeId) => void handleDeleteNode(nodeId)}
            onDeleteEdge={(edgeId) => void handleDeleteEdge(edgeId)}
            showGrid={gridVisible}
            gridColor={gridColorHex}
            backgroundColor={backgroundHex}
            gridSpacing={gridSpacing}
            gridThickness={gridThickness}
            isFullscreen={isCanvasFullscreen}
            onToggleFullscreen={() => setIsCanvasFullscreen((prev) => !prev)}
          />
        ) : (
          <GraphTaskList
            graph={selectedGraph}
            selectedNodeId={selectedNodeId}
            onSelectNode={(id) => {
              setSelectedNodeId(id);
              setSelectedEdgeId(null);
              setSelectedSegment(null);
              setEdgeSelectionScope("none");
            }}
            onStatusChange={(nodeId, status) => void handleTaskStatusChange(nodeId, status)}
            onDeleteNode={(nodeId) => void handleDeleteNode(nodeId)}
            onCreateTask={(payload) => void handleCreateTask(payload)}
            onEditTask={(nodeId, payload) => void handleEditTask(nodeId, payload)}
          />
        )}
      </section>
    </main>
  );
}

