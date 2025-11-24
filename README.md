# Graph Editor Tool

A comprehensive graph editing application supporting both a web and desktop
interface built with Python that supports creating, editing, and managing
graphs with nodes and edges.

## Table of Contents

1. [Features](#features)
2. [Installation](#installation)
3. [Usage](#usage)
   - [Launching the API (Required for All UIs)](#launching-the-api-required-for-all-uis)
   - [Launching the Desktop UI](#launching-the-desktop-ui)
   - [Launching the Web UI](#launching-the-web-ui)
4. [Clean Architecture Overview](#clean-architecture-overview)
5. [API Reference](#api-reference)
   - [Graph Endpoints](#graph-endpoints)
   - [Node Endpoints](#node-endpoints)
   - [Edge Endpoints](#edge-endpoints)
   - [Compatibility Endpoints](#compatibility-endpoints)
6. [Packaging & Executables](#packaging--executables)
   - [Generating Icons](#generating-icons)
   - [Building a macOS .app/.dmg](#building-a-macos-appdmg)
7. [Running as a Python Module](#running-as-a-python-module)
8. [Testing](#testing)
9. [Documentation](#documentation)

## Features

- **Graph Management**: Create, load, save, import, copy, and delete graphs
- **DOT Format Support**: Full import/export compatibility with Graphviz DOT format
- **Cluster/Container System**: Hierarchical node organization with expand/collapse functionality
- **Node and Edge Editing**: Add, delete, copy, and modify graph elements
- **Advanced Edge Types**: Straight, curved, Bézier, B-spline, NURBS, polyline, and composite curves
- **Selection Tools**: Select nodes, edges, or everything including convex shape selection
- **3D Positioning**: Set x, y, z coordinates for nodes and edges
- **Infinite Zoom**: Zoom in and out of the canvas infinitely
- **Layout Algorithms**: Apply various layout algorithms to organize graphs
- **Metadata Support**: Add and modify metadata for graphs, nodes, and edges
- **Drag and Drop**: Move elements around the canvas with smart snapping

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Add `src/` to your `PYTHONPATH` (or install the project in editable mode) so the
packages resolve:

```bash
export PYTHONPATH=src
```

Then run the unified launcher (defaults to desktop when no subcommand is
provided):

```bash
python3 -m graph_canvas
```

### Launching the API (required for all UIs)

Both the desktop and web experiences read/write through the shared FastAPI
service. Make sure it is running before starting either UI:

```bash
python3 -m graph_canvas api --host 0.0.0.0 --port 8000
```

### Launching the Desktop UI

```bash
python3 -m graph_canvas desktop --debug
```

### Launching the Web UI

The React/Vite client proxies through the API, so supply the same base URL you
used above (defaults to `http://127.0.0.1:8000`):

```bash
python3 -m graph_canvas web --api-url http://127.0.0.1:8000
```

## Clean Architecture Overview

| Layer | Description | Key Paths |
| --- | --- | --- |
| **Domain** | Entities, value objects, repositories | `src/graph_canvas/domain` |
| **Application** | Use cases (`GraphService`) + DTOs | `src/graph_canvas/application` |
| **Infrastructure** | Repository implementations (JSON, in-memory) | `src/graph_canvas/infrastructure` |
| **Presentation** | API (FastAPI), Desktop (wxPython), Web (React) | `src/graph_canvas/presentation` |

The presentation layers are thin adapters that depend on the shared application
layer. The React client communicates with the FastAPI service, while the
existing wxPython UI continues to run unchanged via the desktop adapter.

### Shared API + Persistence

- The FastAPI adapter exposes REST endpoints for managing graphs, nodes, and
  edges. Each mutation flows through `GraphService`, which persists to
  `data/graphs.json` via the JSON repository. Restarting the API retains every
  change regardless of presentation.
- The desktop `BackendClient` automatically detects the API health endpoint and
  mirrors node/edge inserts when the server is online, so the desktop and web
  stay in sync.

### React Workspace

- `src/graph_canvas/presentation/web/ui` is a Vite + React 18 project. Run it
  with `python3 -m graph_canvas web --api-url http://127.0.0.1:8000`.
- The UI now mirrors the core desktop experience: add nodes/edges, drag nodes to
  reposition them (edges follow live), edit labels/metadata, pan/zoom the canvas,
  double-click anywhere to drop a node, drag a node’s outer ring onto another
  node to create an edge, and drag an existing edge’s endpoint handle to reroute
  it to a different node.
- Grid controls let you toggle visibility, adjust spacing/line thickness, and
  pick custom grid/background colors directly in the browser.
- A dependency list view surfaces the recommended task order (topological
  sort) next to the Graph Canvas, so you can quickly review what should happen
  next without leaving the browser.
- Each dependency list item can be marked as Started, In Progress, or Complete
  (stored on the node metadata) or deleted outright, keeping task tracking in
  the same workspace.
- Both the web and desktop UIs include an “Add/Edit Task” workflow that lets
  you specify prerequisites/postrequisites, automatically wiring the new node
  into the graph while keeping undo/redo and backend sync in place.
- Graph types are first-class: pick from list, tree, DAG, graph, multigraph,
  hypergraph, or ubergraph when creating/editing (plus directed vs. undirected)
  and every choice is persisted via the shared API.
- Built-in undo/redo plus copy/cut/paste shortcuts (`⌘/Ctrl+Z`, `Shift+⌘/Ctrl+Z`,
  `⌘/Ctrl+C/X/V`) make it easy to experiment in the visualization while keeping
  the underlying API data in sync.
- All edits update the shared API immediately, so the desktop and web views stay
  in sync.

## API Reference

All endpoints are rooted at `/` (e.g. `http://127.0.0.1:8000`). JSON responses
are abbreviated below; see the FastAPI schema definitions under
`src/graph_canvas/presentation/api/schemas.py` for complete shapes.

### Graph Endpoints

| Method & Path | Description | Notes |
| --- | --- | --- |
| `GET /graphs` | List all graphs | Returns `GraphDTO[]` |
| `POST /graphs` | Create a graph | Body: `GraphDTO` |
| `GET /graphs/{graph_id}` | Fetch a graph | |
| `PATCH /graphs/{graph_id}` | Update settings (`graph_type`, `directed`, name, grid) | Body: `GraphSettingsInput` |
| `DELETE /graphs/{graph_id}` | Delete a graph | |
| `PUT /graphs/{graph_id}/snapshot` | Replace graph with snapshot (undo/redo) | Body: full `GraphDTO` |

### Node Endpoints

| Method & Path | Description | Notes |
| --- | --- | --- |
| `POST /graphs/{graph_id}/nodes` | Create a node | Body: `NodeInput` |
| `PATCH /graphs/{graph_id}/nodes/{node_id}` | Update node payload/metadata/position | Body: `NodeInput` |
| `PATCH /graphs/{graph_id}/nodes/positions` | Bulk update positions | Body: `{ positions: Array<{ id, x, y }> }` |
| `DELETE /graphs/{graph_id}/nodes/{node_id}` | Delete node | |

### Edge Endpoints

| Method & Path | Description | Notes |
| --- | --- | --- |
| `POST /graphs/{graph_id}/edges` | Create edge/hyperedge | Body: `EdgeInput` + heads/tails |
| `PATCH /graphs/{graph_id}/edges/{edge_id}` | Update edge | Body: subset of `EdgeInput` |
| `DELETE /graphs/{graph_id}/edges/{edge_id}` | Delete edge | |

### Compatibility Endpoints

Legacy desktop workflows still call the older endpoints:

- `GET /graph`, `POST /graph`
- `POST /nodes`, `DELETE /nodes/{node_id}`
- `POST /edges`, `DELETE /edges/{edge_id}`
- `PATCH /nodes/positions`

These are now thin wrappers around the graph-scoped equivalents to maintain
backward compatibility.

## Packaging & Executables

### Generating Icons

`./scripts/create_icon.py` regenerates the full PNG + ICO icon set under
`icons/`. Ensure you have Pillow installed (already in `requirements.txt`):

```bash
python3 scripts/create_icon.py
```

### Building a macOS .app/.dmg

`./scripts/create_app_bundle.py` assembles a self-contained `.app` bundle (and
optionally a `.dmg`) using the current Python interpreter and vendored deps:

```bash
python3 scripts/create_app_bundle.py
```

The script copies the entire `src/` tree and supporting assets into
`Graph Canvas.app`, installs Python dependencies into `Resources/vendor`, and
creates a launch script that boots `python3 -m graph_canvas desktop`. Answer
“y” at the prompt to package a `.dmg` via `hdiutil`.

## Running as a Python Module

The entire CLI is exposed via `graph_canvas.__main__`, so you can always rely on
module execution:

```bash
python3 -m graph_canvas             # launches the desktop UI (default)
python3 -m graph_canvas desktop     # explicit desktop launch
python3 -m graph_canvas api --help  # backend options
python3 -m graph_canvas web --help  # web server options
```

If you prefer an absolute interpreter path:

```bash
/usr/bin/env python3 -m graph_canvas desktop
```

## Testing

Unit tests live in `tests/`, mirroring the clean-architecture folders
(`tests/application`, `tests/presentation/api`, `tests/presentation/desktop`,
`tests/support`, etc.). Run them with:

```bash
PYTHONPATH=src pytest
```

Each module also bootstraps `sys.path`, so you can run a single file directly—
for example `python tests/application/test_graph_service.py`—without setting
`PYTHONPATH` manually.

## Documentation

- `examples/README_layouts.md` - Layout algorithms guide
- `examples/README_clusters.md` - DOT cluster and container integration guide 