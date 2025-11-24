# Graph Layout Algorithms

This graph editor includes comprehensive layout algorithms that are fully integrated with the DOT format. All layout information is preserved when saving and loading graphs.

## Available Layout Algorithms

### Force-Directed Layouts

**Spring Layout** (`Ctrl+L`)
- Classic force-directed layout using spring physics
- Best for: Medium-sized connected graphs
- Features: Repulsion between nodes, attraction along edges
- Progress dialog for long operations

**Organic Layout**
- Enhanced force-directed with temperature cooling
- Best for: Complex graphs requiring natural appearance
- Features: Simulated annealing, organic clustering
- 100 iterations with cooling schedule

### Geometric Layouts

**Circle Layout**
- Arranges all nodes in a perfect circle
- Best for: Small graphs, cycle visualization
- Features: Equal angular spacing

**Grid Layout**
- Arranges nodes in a regular rectangular grid
- Best for: Systematic organization, matrices
- Features: Automatic grid sizing, centered placement

**Tree Layout**
- Hierarchical arrangement with levels
- Best for: Directed acyclic graphs, hierarchies
- Features: BFS-based level assignment, root detection

### Specialized Layouts

**Radial Layout**
- Concentric circles around a central hub
- Best for: Star topologies, hub-and-spoke graphs
- Features: Automatic center selection, distance-based grouping

**Layered Layout**
- Horizontal layers using topological sort
- Best for: Process flows, data pipelines
- Features: Directed flow visualization, cycle handling

**Compact Layout**
- Minimizes total graph area
- Best for: Space-constrained displays
- Features: Gradual compression, overlap resolution

### Utility Layouts

**Random Layout**
- Randomly positions all nodes
- Best for: Initial placement, breaking clusters
- Features: Reasonable bounds, quick execution

## DOT Format Integration

### Saved Layout Information

When saving to DOT format, the following layout metadata is preserved:

```dot
// Layout tracking
_last_layout="organic";
_graph_density="0.267";
_suggested_layouts="[\"spring\", \"organic\", \"compact\"]";
```

### Layout Suggestions

The system automatically analyzes graph structure and suggests optimal layouts:

- **Small graphs (≤10 nodes)**: Circle, Grid, Tree
- **Dense graphs (>30% density)**: Spring, Organic, Compact  
- **Sparse graphs**: Tree, Layered, Radial

### Graph Density

Automatically calculated as: `edges / (nodes * (nodes-1) / 2)`

Used to recommend appropriate layout algorithms.

## Usage Examples

### Via Menu
- **Layout → Spring Layout** - Apply force-directed layout
- **Layout → Circle Layout** - Arrange in circle
- **Layout → Organic Layout** - Natural clustering

### Via Keyboard
- **Ctrl+L** - Quick spring layout

### Via DOT Files
Load `examples/layout_demo.dot` to see all layout features demonstrated.

## Technical Details

### Algorithm Parameters

**Spring Layout**
```python
k = 100          # Spring constant
damping = 0.9    # Movement damping
iterations = 50  # Simulation steps
```

**Organic Layout**
```python
k = 150                  # Optimal edge length
c1 = 2.0                # Repulsion strength
c2 = 1.0                # Attraction strength
max_iterations = 100    # Annealing steps
```

**Grid Layout**
```python
cols = ceil(sqrt(nodes))     # Grid columns
spacing_x = 150             # Horizontal spacing
spacing_y = 100            # Vertical spacing
```

### Performance

- **Spring/Organic**: O(n²) per iteration - use progress dialogs
- **Circle/Grid**: O(n) - instant execution
- **Tree/Layered**: O(n+e) - BFS/topological sort
- **Radial**: O(n+e) - BFS for distance calculation

### Integration Features

- **Undo/Redo Support**: All layout operations can be undone
- **Real-time Updates**: Canvas refreshes automatically
- **Status Feedback**: Status bar shows applied layout
- **Progress Dialogs**: For computationally intensive layouts
- **DOT Preservation**: Layout metadata saved with graphs

## Best Practices

1. **Start with suggested layouts** based on graph structure
2. **Use spring layout** for general-purpose arrangement
3. **Apply organic layout** for final polishing
4. **Use compact layout** to minimize screen space
5. **Save layout metadata** for consistent results

## Example Workflow

1. Create or load a graph
2. Check suggested layouts in DOT comments
3. Apply appropriate layout algorithm
4. Fine-tune with compact layout if needed
5. Save with preserved layout information
6. Share DOT file with layout metadata intact

The layout system is designed to work seamlessly with all graph features including custom curves, control points, and edge anchoring.
