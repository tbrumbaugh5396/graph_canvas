export interface NodeDTO {
  id: string;
  text?: string;
  x?: number;
  y?: number;
  z?: number;
  metadata?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface EdgeDTO {
  id: string;
  source_id: string;
  target_id: string;
  text?: string;
  metadata?: Record<string, unknown>;
  [key: string]: unknown;
}

export const GRAPH_TYPES = [
  "graph",
  "list",
  "tree",
  "dag",
  "multigraph",
  "hypergraph",
  "ubergraph",
] as const;
export type GraphType = (typeof GRAPH_TYPES)[number];

export interface GraphDTO {
  id: string;
  name: string;
  graph_type?: GraphType | string;
  directed?: boolean;
  nodes: NodeDTO[];
  edges: EdgeDTO[];
  metadata?: Record<string, unknown>;
  background_color?: number[];
  grid_visible?: boolean;
  grid_size?: number;
  grid_color?: number[];
  grid_line_thickness?: number;
}

export type NodeInput = Partial<Omit<NodeDTO, "id">>;
export type EdgeInput = Partial<Omit<EdgeDTO, "id" | "source_id" | "target_id">> & {
  source_id?: string;
  target_id?: string;
};

export type GraphSettingsInput = {
  name?: string;
  graph_type?: GraphType | string;
  directed?: boolean;
  grid_visible?: boolean;
  grid_size?: number;
  grid_color?: number[];
  grid_line_thickness?: number;
  background_color?: number[];
};

