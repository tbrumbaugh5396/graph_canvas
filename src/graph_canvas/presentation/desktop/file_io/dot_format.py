"""
DOT format import/export for the graph editor.
Supports saving and loading graphs with all custom features preserved.
"""


import re
import json
import math
from typing import Dict, List, Any, Optional, Tuple, Union

import graph_canvas.presentation.desktop.models.graph as m_graph
import graph_canvas.presentation.desktop.models.node as m_node
import graph_canvas.presentation.desktop.models.edge as m_edge


class DOTExporter:
    """Export graphs to DOT format with custom attributes."""
    
    def __init__(self):
        """Initialize DOT exporter."""

        pass
    
    def export_graph(self, graph: m_graph.Graph, directed: bool = None) -> str:
        """
        Export a graph to DOT format string.
        
        Args:
            graph: The graph to export
            directed: Whether to export as directed graph (digraph) or undirected (graph).
                     If None, auto-detect based on edge types in the graph.
            
        Returns:
            DOT format string
        """

        lines = []
        
        # Auto-detect graph type if not specified
        if directed is None:
            directed = self._should_export_as_directed(graph)
        
        # Graph declaration
        graph_type = "digraph" if directed else "graph"
        default_edge_op = "->" if directed else "--"
        
        # Sanitize graph name
        graph_name = self._sanitize_id(graph.name) if graph.name else "G"
        lines.append(f"{graph_type} {graph_name} {{")
        
        # Graph-level attributes and metadata
        lines.extend(self._export_graph_attributes(graph))
        
        # Export container nodes as subgraphs/clusters
        containers = [node for node in graph.get_all_nodes() if getattr(node, 'is_container', False)]
        exported_nodes = set()
        
        for container in containers:
            lines.extend(self._export_container_as_subgraph(container, graph, default_edge_op))
            exported_nodes.add(container.id)
            # Mark contained nodes as exported
            for child_id in getattr(container, 'child_ids', set()):
                exported_nodes.add(child_id)
        
        # Export remaining nodes (not in containers)
        for node in graph.get_all_nodes():
            if node.id not in exported_nodes:
                lines.extend(self._export_node(node))
        
        # Export edges (not contained in subgraphs)
        for edge in graph.get_all_edges():
            # Only export edges that aren't fully contained within a subgraph
            source_node = graph.get_node(edge.source_id)
            target_node = graph.get_node(edge.target_id)
            
            source_container = getattr(source_node, 'parent_id', None) if source_node else None
            target_container = getattr(target_node, 'parent_id', None) if target_node else None
            
            # Export edge if nodes are in different containers or no container
            if source_container != target_container or (not source_container and not target_container):
                lines.extend(self._export_edge(edge, default_edge_op))
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def _should_export_as_directed(self, graph: m_graph.Graph) -> bool:
        """
        Determine whether a graph should be exported as directed based on edge types.
        
        Args:
            graph: The graph to analyze
            
        Returns:
            True if should export as digraph, False if as undirected graph
        """

        directed_count = 0
        undirected_count = 0
        
        for edge in graph.get_all_edges():
            if hasattr(edge, 'directed'):
                if edge.directed:
                    directed_count += 1
                else:
                    undirected_count += 1
            else:
                # Default to directed if not specified
                directed_count += 1
        
        # If we have mixed types or all directed, use digraph (which supports both)
        # Only use undirected graph if ALL edges are undirected
        if directed_count > 0:
            return True
        else:
            return False
    
    def _export_graph_attributes(self, graph: m_graph.Graph) -> List[str]:
        """Export graph-level attributes."""

        lines = []
        lines.append("    // Graph metadata and visual properties")
        
        # Graph properties
        if hasattr(graph, 'background_color'):
            bg_color = self._color_to_hex(graph.background_color)
            lines.append(f'    bgcolor="{bg_color}";')
        
        # Custom graph metadata
        if graph.metadata:
            metadata_json = json.dumps(graph.metadata).replace('"', '\\"')
            lines.append(f'    _graph_metadata="{metadata_json}";')
        
        # Visual properties as custom attributes
        if hasattr(graph, 'grid_visible'):
            lines.append(f'    _grid_visible="{graph.grid_visible}";')
        if hasattr(graph, 'grid_size'):
            lines.append(f'    _grid_size="{graph.grid_size}";')
        if hasattr(graph, 'grid_color'):
            grid_color = self._color_to_hex(graph.grid_color)
            lines.append(f'    _grid_color="{grid_color}";')
        
        # Layout information
        if hasattr(graph, 'last_layout_applied'):
            lines.append(f'    _last_layout="{graph.last_layout_applied}";')
        
        # Add layout algorithm suggestions based on graph structure
        node_count = len(graph.get_all_nodes())
        edge_count = len(graph.get_all_edges())
        if node_count > 0:
            density = edge_count / (node_count * (node_count - 1) / 2) if node_count > 1 else 0
            lines.append(f'    _graph_density="{density:.3f}";')
            
            # Suggest optimal layouts
            if node_count <= 10:
                suggested_layouts = ["circle", "grid", "tree"]
            elif density > 0.3:
                suggested_layouts = ["spring", "organic", "compact"]
            else:
                suggested_layouts = ["tree", "layered", "radial"]
            
            layouts_json = json.dumps(suggested_layouts).replace('"', '\\"')
            lines.append(f'    _suggested_layouts="{layouts_json}";')
        
        lines.append("")
        return lines
    
    def _export_container_as_subgraph(self, container: m_node.Node, graph: m_graph.Graph, default_edge_op: str) -> List[str]:
        """Export a container node as a DOT subgraph/cluster."""

        lines = []
        
        # Create cluster name (must start with "cluster" for Graphviz)
        cluster_name = f"cluster_{self._sanitize_id(container.id)}"
        lines.append(f"    subgraph {cluster_name} {{")
        
        # Container attributes
        lines.append(f'        label="{self._escape_string(container.text)}";')
        
        # Visual attributes for container
        if hasattr(container, 'color'):
            color = self._color_to_hex(container.color)
            lines.append(f'        bgcolor="{color}";')
        
        # Container metadata
        if hasattr(container, 'is_expanded') and not container.is_expanded:
            lines.append('        _is_expanded="false";')
        
        # Export contained nodes
        for child_id in getattr(container, 'child_ids', set()):
            child_node = graph.get_node(child_id)
            if child_node:
                # Export child node with indentation
                child_lines = self._export_node(child_node)
                for child_line in child_lines:
                    lines.append(f"    {child_line}")
        
        # Export edges within this container
        for edge in graph.get_all_edges():
            source_node = graph.get_node(edge.source_id)
            target_node = graph.get_node(edge.target_id)
            
            # Check if both nodes are in this container
            source_in_container = (source_node and 
                                 getattr(source_node, 'parent_id', None) == container.id)
            target_in_container = (target_node and 
                                 getattr(target_node, 'parent_id', None) == container.id)
            
            if source_in_container and target_in_container:
                # Export edge within container with indentation
                edge_lines = self._export_edge(edge, default_edge_op)
                for edge_line in edge_lines:
                    lines.append(f"    {edge_line}")
        
        lines.append("    }")
        return lines
    
    def _export_node(self, node: m_node.Node) -> List[str]:
        """Export a single node with all its attributes."""

        lines = []
        
        # Node ID and basic attributes
        node_id = self._sanitize_id(node.id)
        attrs = []
        
        # Standard DOT attributes
        if node.text:
            attrs.append(f'label="{self._escape_string(node.text)}"')
        
        # Position (scale down by 20 for DOT compatibility and use pos attribute for Graphviz compatibility)
        scaled_x = node.x / 20
        scaled_y = node.y / 20
        attrs.append(f'pos="{scaled_x},{scaled_y}"')
        
        # Visual attributes
        if hasattr(node, 'color'):
            color = self._color_to_hex(node.color)
            attrs.append(f'fillcolor="{color}"')
            attrs.append('style="filled"')
        
        if hasattr(node, 'border_color'):
            border_color = self._color_to_hex(node.border_color)
            attrs.append(f'color="{border_color}"')
        
        if hasattr(node, 'width') and hasattr(node, 'height'):
            # Convert to inches (Graphviz default)
            width_inches = node.width / 72.0  # 72 points per inch
            height_inches = node.height / 72.0
            attrs.append(f'width="{width_inches:.3f}"')
            attrs.append(f'height="{height_inches:.3f}"')
        
        # Custom attributes for our specific features (also scaled)
        attrs.append(f'_node_id="{node.id}"')
        attrs.append(f'_x="{scaled_x}"')
        attrs.append(f'_y="{scaled_y}"')
        attrs.append(f'_z="{node.z}"')
        
        if hasattr(node, 'rotation') and node.rotation != 0:
            attrs.append(f'_rotation="{node.rotation}"')
        
        if hasattr(node, 'font_size'):
            attrs.append(f'fontsize="{node.font_size}"')
            attrs.append(f'_font_size="{node.font_size}"')
        
        # Visual properties
        if hasattr(node, 'border_width'):
            attrs.append(f'_border_width="{node.border_width}"')
        
        if hasattr(node, 'text_color'):
            text_color = self._color_to_hex(node.text_color)
            attrs.append(f'fontcolor="{text_color}"')
            attrs.append(f'_text_color="{text_color}"')
        
        # State properties
        if hasattr(node, 'visible') and not node.visible:
            attrs.append('_visible="false"')
        if hasattr(node, 'locked') and node.locked:
            attrs.append('_locked="true"')
        if hasattr(node, 'selected') and node.selected:
            attrs.append('_selected="true"')
        
        # Containment hierarchy
        if hasattr(node, 'is_container') and node.is_container:
            attrs.append('_is_container="true"')
        if hasattr(node, 'is_expanded') and not node.is_expanded:
            attrs.append('_is_expanded="false"')
        if hasattr(node, 'parent_id') and node.parent_id:
            attrs.append(f'_parent_id="{node.parent_id}"')
        if hasattr(node, 'child_ids') and node.child_ids:
            child_ids_json = json.dumps(list(node.child_ids)).replace('"', '\\"')
            attrs.append(f'_child_ids="{child_ids_json}"')
        
        # Node metadata
        if node.metadata:
            metadata_json = json.dumps(node.metadata).replace('"', '\\"')
            attrs.append(f'_metadata="{metadata_json}"')
        
        # Construct node line
        attrs_str = ", ".join(attrs)
        lines.append(f'    {node_id} [{attrs_str}];')
        
        return lines
    
    def _export_edge(self, edge: m_edge.Edge, default_edge_op: str) -> List[str]:
        """Export a single edge with all its attributes."""

        lines = []
        
        # Edge IDs
        source_id = self._sanitize_id(edge.source_id)
        target_id = self._sanitize_id(edge.target_id)
        
        # Determine edge operator based on individual edge's directed property
        # Use edge.directed if available, otherwise fall back to default
        if hasattr(edge, 'directed'):
            edge_op = "->" if edge.directed else "--"
        else:
            edge_op = default_edge_op
        
        attrs = []
        
        # Standard DOT attributes
        if edge.text:
            attrs.append(f'label="{self._escape_string(edge.text)}"')
        
        if hasattr(edge, 'color'):
            color = self._color_to_hex(edge.color)
            attrs.append(f'color="{color}"')
        
        if hasattr(edge, 'width'):
            attrs.append(f'penwidth="{edge.width}"')
        
        # Custom edge attributes
        attrs.append(f'_edge_id="{edge.id}"')
        
        # Rendering type and curve properties
        if hasattr(edge, 'rendering_type') and edge.rendering_type:
            attrs.append(f'_rendering_type="{edge.rendering_type}"')
        
        if hasattr(edge, 'arrow_position'):
            attrs.append(f'_arrow_position="{edge.arrow_position}"')
        
        # Control points
        if hasattr(edge, 'control_points') and edge.control_points:
            control_points_json = json.dumps(edge.control_points).replace('"', '\\"')
            attrs.append(f'_control_points="{control_points_json}"')
        
        # Composite curve segments
        if hasattr(edge, 'is_composite') and edge.is_composite:
            attrs.append('_is_composite="true"')
        if hasattr(edge, 'curve_segments') and edge.curve_segments:
            segments_json = json.dumps(edge.curve_segments).replace('"', '\\"')
            attrs.append(f'_curve_segments="{segments_json}"')
        
        # Custom endpoints
        if hasattr(edge, 'custom_endpoints') and edge.custom_endpoints:
            endpoints_json = json.dumps(edge.custom_endpoints).replace('"', '\\"')
            attrs.append(f'_custom_endpoints="{endpoints_json}"')
        
        # Visual properties
        if hasattr(edge, 'text_color'):
            text_color = self._color_to_hex(edge.text_color)
            attrs.append(f'fontcolor="{text_color}"')
            attrs.append(f'_text_color="{text_color}"')
        
        if hasattr(edge, 'font_size'):
            attrs.append(f'fontsize="{edge.font_size}"')
            attrs.append(f'_font_size="{edge.font_size}"')
        
        if hasattr(edge, 'arrow_size'):
            attrs.append(f'_arrow_size="{edge.arrow_size}"')
        
        if hasattr(edge, 'line_style') and edge.line_style != 'solid':
            if edge.line_style == 'dashed':
                attrs.append('style="dashed"')
            elif edge.line_style == 'dotted':
                attrs.append('style="dotted"')
            attrs.append(f'_line_style="{edge.line_style}"')
        
        # State properties
        if hasattr(edge, 'visible') and not edge.visible:
            attrs.append('_visible="false"')
        if hasattr(edge, 'locked') and edge.locked:
            attrs.append('_locked="true"')
        if hasattr(edge, 'selected') and edge.selected:
            attrs.append('_selected="true"')
        if hasattr(edge, 'directed') and not edge.directed:
            attrs.append('_directed="false"')
        
        # Edge metadata
        if edge.metadata:
            metadata_json = json.dumps(edge.metadata).replace('"', '\\"')
            attrs.append(f'_metadata="{metadata_json}"')
        
        # Construct edge line
        attrs_str = ", ".join(attrs)
        lines.append(f'    {source_id} {edge_op} {target_id} [{attrs_str}];')
        
        return lines
    
    def _sanitize_id(self, node_id: str) -> str:
        """Sanitize node/edge ID for DOT format."""

        # Replace invalid characters with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', node_id)
        # Ensure it doesn't start with a digit
        if sanitized and sanitized[0].isdigit():
            sanitized = f"node_{sanitized}"
        return sanitized or "node_default"
    
    def _escape_string(self, text: str) -> str:
        """Escape string for DOT format."""

        return text.replace('"', '\\"').replace('\n', '\\n').replace('\t', '\\t')
    
    def _color_to_hex(self, color: Union[Tuple[int, int, int], str]) -> str:
        """Convert color tuple to hex string."""

        if isinstance(color, str):
            return color
        r, g, b = color[:3]  # Take first 3 components
        return f"#{r:02x}{g:02x}{b:02x}"


class DOTImporter:
    """Import graphs from DOT format."""

    def __init__(self):
        """Initialize DOT importer."""

        self.graph = None
        self.node_id_map = {}  # Map sanitized IDs back to original IDs
    
    def import_graph(self, dot_content: str) -> m_graph.Graph:
        """
        Import a graph from DOT format string.
        
        Args:
            dot_content: DOT format string
            
        Returns:
            Graph object
        """

        # Create new graph
        self.graph = m_graph.Graph()
        self.node_id_map = {}
        
        # Parse the DOT content
        self._parse_dot_content(dot_content)
        
        return self.graph
    
    def _parse_dot_content(self, content: str):
        """Parse DOT content and build graph."""

        # Remove comments
        content = self._remove_comments(content)
        
        # Extract graph name and type
        graph_match = re.search(r'(strict\s+)?(di)?graph\s+(\w+)?\s*\{', content, re.IGNORECASE)
        if not graph_match:
            raise ValueError("Invalid DOT format: No graph declaration found")
        
        is_directed = graph_match.group(2) is not None
        graph_name = graph_match.group(3) or "Imported Graph"
        self.graph.name = graph_name
        
        # Extract graph body
        body_start = content.find('{') + 1
        body_end = content.rfind('}')
        body = content[body_start:body_end]
        
        # Parse statements and extract subgraphs
        statements = self._split_statements(body)
        subgraphs = self._extract_subgraphs(body)
        
        # Process subgraphs first to create container hierarchy
        for subgraph_name, subgraph_body in subgraphs.items():
            self._process_subgraph(subgraph_name, subgraph_body)
        
        # Process regular statements
        for statement in statements:
            statement = statement.strip()
            if not self._is_subgraph_statement(statement):
                self._process_statement(statement)
    
    def _remove_comments(self, content: str) -> str:
        """Remove C++ style comments from DOT content."""

        # Remove // comments
        lines = content.split('\n')
        cleaned_lines = []
        for line in lines:
            comment_pos = line.find('//')
            if comment_pos >= 0:
                line = line[:comment_pos]
            cleaned_lines.append(line)
        content = '\n'.join(cleaned_lines)
        
        # Remove /* */ comments
        while True:
            start = content.find('/*')
            if start == -1:
                break
            end = content.find('*/', start + 2)
            if end == -1:
                break
            content = content[:start] + content[end + 2:]
        
        return content
    
    def _split_statements(self, body: str) -> List[str]:
        """Split body into individual statements."""

        statements = []
        current = ""
        in_quotes = False
        bracket_depth = 0
        
        i = 0
        while i < len(body):
            char = body[i]
            
            if char == '"' and (i == 0 or body[i-1] != '\\'):
                in_quotes = not in_quotes
            elif not in_quotes:
                if char in '[{':
                    bracket_depth += 1
                elif char in ']}':
                    bracket_depth -= 1
                elif char == ';' and bracket_depth == 0:
                    if current.strip():
                        statements.append(current.strip())
                    current = ""
                    i += 1
                    continue
            
            current += char
            i += 1
        
        if current.strip():
            statements.append(current.strip())
        
        return statements
    
    def _process_statement(self, statement: str):
        """Process a single DOT statement."""

        if not statement:
            return
        
        # Check if it's a graph attribute
        if '=' in statement and ('->' not in statement and '--' not in statement):
            self._process_graph_attribute(statement)
        # Check if it's an edge
        elif '->' in statement or '--' in statement:
            self._process_edge_statement(statement)
        # Check if it's a node
        elif '[' in statement and ']' in statement:
            self._process_node_statement(statement)
        # Otherwise, might be a simple node declaration
        else:
            # Simple node without attributes
            node_id = statement.strip()
            if node_id and not node_id.startswith('_'):
                self._create_node_if_not_exists(node_id)
    
    def _process_graph_attribute(self, statement: str):
        """Process graph-level attribute."""

        parts = statement.split('=', 1)
        if len(parts) != 2:
            return
        
        attr_name = parts[0].strip()
        attr_value = parts[1].strip().strip(';').strip('"')
        
        # Handle standard graph attributes
        if attr_name == 'bgcolor':
            self.graph.background_color = self._hex_to_color(attr_value)
        
        # Handle custom graph attributes
        elif attr_name == '_graph_metadata':
            try:
                metadata = json.loads(attr_value.replace('\\"', '"'))
                self.graph.metadata = metadata
            except (json.JSONDecodeError, ValueError):
                pass
        elif attr_name == '_grid_visible':
            self.graph.grid_visible = attr_value.lower() == 'true'
        elif attr_name == '_grid_size':
            try:
                self.graph.grid_size = int(attr_value)
            except ValueError:
                pass
        elif attr_name == '_grid_color':
            self.graph.grid_color = self._hex_to_color(attr_value)
        elif attr_name == '_last_layout':
            self.graph.last_layout_applied = attr_value
        elif attr_name == '_graph_density':
            try:
                self.graph.graph_density = float(attr_value)
            except ValueError:
                pass
        elif attr_name == '_suggested_layouts':
            try:
                suggested_layouts = json.loads(attr_value.replace('\\"', '"'))
                self.graph.suggested_layouts = suggested_layouts
            except (json.JSONDecodeError, ValueError):
                pass
    
    def _process_node_statement(self, statement: str):
        """Process node statement with attributes."""

        # Extract node ID and attributes
        match = re.match(r'(\w+)\s*\[(.*?)\]', statement, re.DOTALL)
        if not match:
            return
        
        node_id = match.group(1)
        attrs_str = match.group(2)
        
        # Parse attributes
        attributes = self._parse_attributes(attrs_str)
        
        # Create or get node
        node = self._create_node_if_not_exists(node_id)
        
        # Apply attributes
        self._apply_node_attributes(node, attributes)
    
    def _process_edge_statement(self, statement: str):
        """Process edge statement."""

        # Extract edge and attributes
        edge_op = '->' if '->' in statement else '--'
        
        # Split on the edge operator
        parts = statement.split(edge_op, 1)
        if len(parts) != 2:
            return
        
        source_id = parts[0].strip()
        
        # Extract target and attributes
        target_part = parts[1].strip()
        attr_match = re.search(r'\[(.*?)\]', target_part, re.DOTALL)
        
        if attr_match:
            target_id = target_part[:attr_match.start()].strip()
            attrs_str = attr_match.group(1)
            attributes = self._parse_attributes(attrs_str)
        else:
            target_id = target_part.strip()
            attributes = {}
        
        # Create nodes if they don't exist
        source_node = self._create_node_if_not_exists(source_id)
        target_node = self._create_node_if_not_exists(target_id)
        
        # Create edge
        edge = m_edge.Edge(source_id=source_node.id, target_id=target_node.id)
        
        # Apply attributes
        self._apply_edge_attributes(edge, attributes)
        
        # Add edge to graph
        self.graph.add_edge(edge)
    
    def _parse_attributes(self, attrs_str: str) -> Dict[str, str]:
        """Parse attribute string into dictionary."""

        attributes = {}
        
        # Split on commas, but respect quoted strings
        current_attr = ""
        in_quotes = False
        
        for char in attrs_str + ',':  # Add comma to flush last attribute
            if char == '"' and (not current_attr or current_attr[-1] != '\\'):
                in_quotes = not in_quotes
                current_attr += char
            elif char == ',' and not in_quotes:
                if current_attr.strip():
                    self._parse_single_attribute(current_attr.strip(), attributes)
                current_attr = ""
            else:
                current_attr += char
        
        return attributes
    
    def _parse_single_attribute(self, attr_str: str, attributes: Dict[str, str]):
        """Parse a single attribute and add to dictionary."""

        parts = attr_str.split('=', 1)
        if len(parts) == 2:
            key = parts[0].strip()
            value = parts[1].strip().strip('"')
            attributes[key] = value
    
    def _create_node_if_not_exists(self, sanitized_id: str) -> m_node.Node:
        """Create node if it doesn't exist, or return existing node."""

        # First check if we already have a node mapped to this sanitized ID
        if sanitized_id in self.node_id_map:
            original_id = self.node_id_map[sanitized_id]
            if original_id in self.graph.nodes:
                return self.graph.nodes[original_id]
        
        # Check if we already have this node by comparing sanitized versions
        for existing_id, node in self.graph.nodes.items():
            if self._sanitize_id_for_comparison(existing_id) == sanitized_id:
                self.node_id_map[sanitized_id] = existing_id
                return node
        
        # Create new node with some initial spacing to avoid overlap
        import random
        # Start with default text - will be overridden by label attribute if present
        node = m_node.Node(text="Node", 
                   x=random.uniform(-50, 50), 
                   y=random.uniform(-50, 50))
        original_id = node.id
        self.node_id_map[sanitized_id] = original_id
        self.graph.add_node(node)
        return node
    
    def _sanitize_id_for_comparison(self, original_id: str) -> str:
        """Sanitize ID the same way as exporter for comparison."""

        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', original_id)
        if sanitized and sanitized[0].isdigit():
            sanitized = f"node_{sanitized}"
        return sanitized or "node_default"
    
    def _apply_node_attributes(self, node: m_node.Node, attributes: Dict[str, str]):
        """Apply parsed attributes to a node."""

        for key, value in attributes.items():
            try:
                if key == 'label':
                    node.text = value.replace('\\n', '\n').replace('\\t', '\t')
                elif key == 'pos':
                    # Parse position "x,y" and scale by 20 for grid alignment
                    coords = value.split(',')
                    if len(coords) >= 2:
                        node.x = float(coords[0]) * 20
                        node.y = float(coords[1]) * 20
                
                # Custom attributes
                elif key == '_node_id':
                    # Update node ID mapping, but check for conflicts first
                    old_id = node.id
                    target_id = value
                    
                    # If target ID already exists and is different from current node, 
                    # we have a duplicate - use the existing node and remove this one
                    if target_id in self.graph.nodes and self.graph.nodes[target_id] != node:
                        existing_node = self.graph.nodes[target_id]
                        # Copy any missing attributes from the duplicate to the existing node
                        if not existing_node.text or existing_node.text == "Node":
                            existing_node.text = node.text
                        # Remove the duplicate node
                        if old_id in self.graph.nodes:
                            del self.graph.nodes[old_id]
                        # Update the reference to point to the existing node
                        node = existing_node
                    else:
                        # Safe to update the ID
                        node.id = target_id
                        if old_id in self.graph.nodes and old_id != target_id:
                            self.graph.nodes[target_id] = self.graph.nodes.pop(old_id)
                elif key == '_x':
                    node.x = float(value) * 20  # Scale by 20 for grid alignment
                elif key == '_y':
                    node.y = float(value) * 20  # Scale by 20 for grid alignment
                elif key == '_z':
                    node.z = float(value)
                elif key == '_rotation':
                    node.rotation = float(value)
                elif key == 'fillcolor' or key.endswith('_color'):
                    color = self._hex_to_color(value)
                    if key == 'fillcolor':
                        node.color = color
                    elif key == '_text_color':
                        node.text_color = color
                    elif key == 'color':
                        node.border_color = color
                elif key == 'width':
                    node.width = float(value) * 72  # Convert inches to points
                elif key == 'height':
                    node.height = float(value) * 72  # Convert inches to points
                elif key == 'fontsize' or key == '_font_size':
                    node.font_size = int(value)
                elif key == '_border_width':
                    node.border_width = int(value)
                elif key == '_visible':
                    node.visible = value.lower() == 'true'
                elif key == '_locked':
                    node.locked = value.lower() == 'true'
                elif key == '_selected':
                    node.selected = value.lower() == 'true'
                elif key == '_is_container':
                    node.is_container = value.lower() == 'true'
                elif key == '_is_expanded':
                    node.is_expanded = value.lower() == 'true'
                elif key == '_parent_id':
                    node.parent_id = value
                elif key == '_child_ids':
                    try:
                        child_ids = json.loads(value.replace('\\"', '"'))
                        node.child_ids = set(child_ids)
                    except (json.JSONDecodeError, ValueError):
                        pass
                elif key == '_metadata':
                    try:
                        metadata = json.loads(value.replace('\\"', '"'))
                        node.metadata = metadata
                    except (json.JSONDecodeError, ValueError):
                        pass
            except (ValueError, TypeError):
                # Skip invalid attribute values
                continue
    
    def _apply_edge_attributes(self, edge: m_edge.Edge, attributes: Dict[str, str]):
        """Apply parsed attributes to an edge."""

        for key, value in attributes.items():
            try:
                if key == 'label':
                    edge.text = value.replace('\\n', '\n').replace('\\t', '\t')
                elif key == 'color':
                    edge.color = self._hex_to_color(value)
                elif key == 'penwidth':
                    edge.width = float(value)
                
                # Custom attributes
                elif key == '_edge_id':
                    edge.id = value
                elif key == '_rendering_type':
                    edge.rendering_type = value
                elif key == '_arrow_position':
                    edge.arrow_position = float(value)
                elif key == '_control_points':
                    try:
                        control_points = json.loads(value.replace('\\"', '"'))
                        edge.control_points = control_points
                    except (json.JSONDecodeError, ValueError):
                        pass
                elif key == '_is_composite':
                    edge.is_composite = value.lower() == 'true'
                elif key == '_curve_segments':
                    try:
                        curve_segments = json.loads(value.replace('\\"', '"'))
                        edge.curve_segments = curve_segments
                    except (json.JSONDecodeError, ValueError):
                        pass
                elif key == '_custom_endpoints':
                    try:
                        custom_endpoints = json.loads(value.replace('\\"', '"'))
                        edge.custom_endpoints = custom_endpoints
                    except (json.JSONDecodeError, ValueError):
                        pass
                elif key == 'fontcolor' or key == '_text_color':
                    edge.text_color = self._hex_to_color(value)
                elif key == 'fontsize' or key == '_font_size':
                    edge.font_size = int(value)
                elif key == '_arrow_size':
                    edge.arrow_size = int(value)
                elif key == 'style' or key == '_line_style':
                    if key == 'style':
                        if value == 'dashed':
                            edge.line_style = 'dashed'
                        elif value == 'dotted':
                            edge.line_style = 'dotted'
                    else:
                        edge.line_style = value
                elif key == '_visible':
                    edge.visible = value.lower() == 'true'
                elif key == '_locked':
                    edge.locked = value.lower() == 'true'
                elif key == '_selected':
                    edge.selected = value.lower() == 'true'
                elif key == '_directed':
                    edge.directed = value.lower() == 'true'
                elif key == '_metadata':
                    try:
                        metadata = json.loads(value.replace('\\"', '"'))
                        edge.metadata = metadata
                    except (json.JSONDecodeError, ValueError):
                        pass
            except (ValueError, TypeError):
                # Skip invalid attribute values
                continue
    
    def _hex_to_color(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color string to RGB tuple."""

        if not hex_color.startswith('#'):
            # Try to parse as named color or return default
            return (200, 200, 200)
        
        try:
            hex_color = hex_color[1:]  # Remove #
            if len(hex_color) == 6:
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                return (r, g, b)
        except ValueError:
            pass
        
        return (200, 200, 200)  # Default gray
    
    def _extract_subgraphs(self, body: str) -> Dict[str, str]:
        """Extract subgraph declarations from DOT body."""

        subgraphs = {}
        
        # Find subgraph declarations
        i = 0
        while i < len(body):
            # Look for "subgraph" keyword
            subgraph_match = re.search(r'\bsubgraph\s*([^{]*)\s*\{', body[i:], re.IGNORECASE)
            if not subgraph_match:
                break
            
            # Extract subgraph name
            subgraph_start = i + subgraph_match.start()
            name_part = subgraph_match.group(1).strip()
            subgraph_name = name_part if name_part else f"subgraph_{len(subgraphs)}"
            
            # Find matching closing brace
            brace_start = i + subgraph_match.end() - 1  # Position of opening brace
            brace_count = 1
            j = brace_start + 1
            
            while j < len(body) and brace_count > 0:
                if body[j] == '{':
                    brace_count += 1
                elif body[j] == '}':
                    brace_count -= 1
                j += 1
            
            if brace_count == 0:
                # Extract subgraph body (without braces)
                subgraph_body = body[brace_start + 1:j - 1]
                subgraphs[subgraph_name] = subgraph_body
                i = j
            else:
                i = brace_start + 1
        
        return subgraphs
    
    def _process_subgraph(self, subgraph_name: str, subgraph_body: str):
        """Process a subgraph and create container structure."""

        # Determine if this is a cluster (container)
        is_cluster = subgraph_name.lower().startswith('cluster')
        
        if is_cluster:
            # Create container node for cluster
            container_name = subgraph_name[7:] if len(subgraph_name) > 7 else "Container"
            container_node = m_node.Node(text=container_name)
            container_node.is_container = True
            container_node.is_expanded = True
            
            # Parse subgraph statements to find contained nodes
            statements = self._split_statements(subgraph_body)
            contained_nodes = []
            
            # First pass: create nodes and collect them
            for statement in statements:
                statement = statement.strip()
                if self._is_node_statement(statement):
                    # Extract node ID
                    node_match = re.match(r'(\w+)', statement)
                    if node_match:
                        node_id = node_match.group(1)
                        node = self._create_node_if_not_exists(node_id)
                        contained_nodes.append(node)
                elif not statement.startswith('_') and '=' not in statement and '->' not in statement and '--' not in statement:
                    # Simple node declaration
                    node_id = statement.strip()
                    if node_id:
                        node = self._create_node_if_not_exists(node_id)
                        contained_nodes.append(node)
            
            # Calculate container position as center of contained nodes
            if contained_nodes:
                # Calculate center position of all contained nodes
                total_x = sum(node.x for node in contained_nodes)
                total_y = sum(node.y for node in contained_nodes)
                container_node.x = total_x / len(contained_nodes)
                container_node.y = total_y / len(contained_nodes)
                
                # Make container larger to accommodate children
                min_x = min(node.x - node.width/2 for node in contained_nodes)
                max_x = max(node.x + node.width/2 for node in contained_nodes)
                min_y = min(node.y - node.height/2 for node in contained_nodes)
                max_y = max(node.y + node.height/2 for node in contained_nodes)
                
                container_node.width = max(120, max_x - min_x + 40)  # Add padding
                container_node.height = max(80, max_y - min_y + 40)  # Add padding
            else:
                # Default position if no contained nodes
                container_node.x = 0
                container_node.y = 0
                container_node.width = 120
                container_node.height = 80
            
            # Add container to graph first
            self.graph.add_node(container_node)
            
            # Set containment relationships for all contained nodes
            for node in contained_nodes:
                node.parent_id = container_node.id
                container_node.add_child(node.id)
                # Make nodes visible initially since container is expanded
                node.visible = True
            
            # Process other statements in subgraph (edges, attributes)
            for statement in statements:
                if not self._is_node_statement(statement) and statement.strip():
                    self._process_statement(statement)
        else:
            # Regular subgraph - just process statements
            statements = self._split_statements(subgraph_body)
            for statement in statements:
                self._process_statement(statement.strip())
    
    def _is_subgraph_statement(self, statement: str) -> bool:
        """Check if statement is a subgraph declaration."""

        return re.match(r'\s*subgraph\s', statement, re.IGNORECASE) is not None
    
    def _is_node_statement(self, statement: str) -> bool:
        """Check if statement is a node declaration with attributes."""

        return '[' in statement and ']' in statement and ('->' not in statement and '--' not in statement)


def save_graph_to_dot(graph: m_graph.Graph, file_path: str, directed: bool = None):
    """
    Save a graph to DOT format file.
    
    Args:
        graph: The graph to save
        file_path: Path to save the DOT file
        directed: Whether to save as directed graph. If None, auto-detect based on edge types.
    """

    exporter = DOTExporter()
    dot_content = exporter.export_graph(graph, directed)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(dot_content)


def load_graph_from_dot(file_path: str) -> m_graph.Graph:
    """
    Load a graph from DOT format file.
    
    Args:
        file_path: Path to the DOT file
        
    Returns:
        Graph object
    """

    with open(file_path, 'r', encoding='utf-8') as f:
        dot_content = f.read()
    
    importer = DOTImporter()
    graph = importer.import_graph(dot_content)
    graph.file_path = file_path
    graph.modified = False
    
    return graph
