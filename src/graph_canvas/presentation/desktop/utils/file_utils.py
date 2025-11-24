"""
File utility functions for the graph editor.
"""


import os
import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
import graph_canvas.presentation.desktop.models.graph as m_graph
import graph_canvas.presentation.desktop.models.node as m_node
import graph_canvas.presentation.desktop.models.edge as m_edge


def ensure_directory_exists(directory: str) -> None:
    """Ensure that a directory exists, creating it if necessary."""

    if not os.path.exists(directory):
        os.makedirs(directory)


def get_file_extension(filename: str) -> str:
    """Get the file extension from a filename."""

    return os.path.splitext(filename)[1].lower()


def is_valid_graph_file(filename: str) -> bool:
    """Check if a file has a valid graph file extension."""

    valid_extensions = ['.json', '.xml', '.gml', '.graphml']
    return get_file_extension(filename) in valid_extensions


def backup_file(filename: str, backup_suffix: str = '.backup') -> str:
    """Create a backup of a file."""

    backup_filename = filename + backup_suffix
    if os.path.exists(filename):
        import shutil
        shutil.copy2(filename, backup_filename)
    return backup_filename


def save_graph_json(graph: m_graph.Graph, filename: str) -> None:
    """Save a graph to a JSON file."""

    ensure_directory_exists(os.path.dirname(filename))

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(graph.to_dict(), f, indent=2, ensure_ascii=False)


def load_graph_json(filename: str) -> m_graph.Graph:
    """Load a graph from a JSON file."""

    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return m_graph.Graph.from_dict(data)


def export_graph_gml(graph: m_graph.Graph, filename: str) -> None:
    """Export a graph to GML format."""

    ensure_directory_exists(os.path.dirname(filename))

    with open(filename, 'w', encoding='utf-8') as f:
        f.write("graph [\n")
        f.write(f'  comment "{graph.name}"\n')
        f.write("  directed 1\n")

        # Write nodes
        for node in graph.get_all_nodes():
            f.write("  node [\n")
            f.write(f'    id {node.id}\n')
            f.write(f'    label "{node.text}"\n')
            f.write(f'    x {node.x}\n')
            f.write(f'    y {node.y}\n')
            f.write(f'    z {node.z}\n')
            f.write("  ]\n")

        # Write edges
        for edge in graph.get_all_edges():
            f.write("  edge [\n")
            f.write(f'    source {edge.source_id}\n')
            f.write(f'    target {edge.target_id}\n')
            f.write(f'    label "{edge.text}"\n')
            f.write("  ]\n")

        f.write("]\n")


def import_graph_gml(filename: str) -> m_graph.Graph:
    """Import a graph from GML format (simplified parser)."""

    graph = m_graph.Graph()

    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    # Simple GML parser (this is a basic implementation)
    lines = content.split('\n')
    current_section = None
    current_node = None
    current_edge = None

    for line in lines:
        line = line.strip()
        if not line or line.startswith('comment'):
            continue

        if line.startswith('node ['):
            current_section = 'node'
            current_node = {'id': None, 'label': '', 'x': 0, 'y': 0, 'z': 0}
        elif line.startswith('edge ['):
            current_section = 'edge'
            current_edge = {'source': None, 'target': None, 'label': ''}
        elif line == ']':
            if current_section == 'node' and current_node:
                node = m_node.Node(x=current_node['x'],
                            y=current_node['y'],
                            z=current_node['z'],
                            text=current_node['label'],
                            node_id=current_node['id'])
                graph.add_node(node)
                current_node = None
            elif current_section == 'edge' and current_edge:
                edge = m_edge.Edge(source_id=current_edge['source'],
                            target_id=current_edge['target'],
                            text=current_edge['label'])
                graph.add_edge(edge)
                current_edge = None
            current_section = None
        else:
            # Parse attributes
            if current_section == 'node' and current_node:
                if line.startswith('id '):
                    current_node['id'] = line.split(' ', 1)[1]
                elif line.startswith('label '):
                    current_node['label'] = line.split(' ', 1)[1].strip('"')
                elif line.startswith('x '):
                    current_node['x'] = float(line.split(' ', 1)[1])
                elif line.startswith('y '):
                    current_node['y'] = float(line.split(' ', 1)[1])
                elif line.startswith('z '):
                    current_node['z'] = float(line.split(' ', 1)[1])
            elif current_section == 'edge' and current_edge:
                if line.startswith('source '):
                    current_edge['source'] = line.split(' ', 1)[1]
                elif line.startswith('target '):
                    current_edge['target'] = line.split(' ', 1)[1]
                elif line.startswith('label '):
                    current_edge['label'] = line.split(' ', 1)[1].strip('"')

    return graph


def export_graph_graphml(graph: m_graph.Graph, filename: str) -> None:
    """Export a graph to GraphML format."""

    ensure_directory_exists(os.path.dirname(filename))

    root = ET.Element('graphml')
    root.set('xmlns', 'http://graphml.graphdrawing.org/xmlns')
    root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    root.set(
        'xsi:schemaLocation',
        'http://graphml.graphdrawing.org/xmlns http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd'
    )

    # Define keys
    key_node_label = ET.SubElement(root, 'key')
    key_node_label.set('id', 'node_label')
    key_node_label.set('for', 'node')
    key_node_label.set('attr.name', 'label')
    key_node_label.set('attr.type', 'string')

    key_node_x = ET.SubElement(root, 'key')
    key_node_x.set('id', 'node_x')
    key_node_x.set('for', 'node')
    key_node_x.set('attr.name', 'x')
    key_node_x.set('attr.type', 'double')

    key_node_y = ET.SubElement(root, 'key')
    key_node_y.set('id', 'node_y')
    key_node_y.set('for', 'node')
    key_node_y.set('attr.name', 'y')
    key_node_y.set('attr.type', 'double')

    key_edge_label = ET.SubElement(root, 'key')
    key_edge_label.set('id', 'edge_label')
    key_edge_label.set('for', 'edge')
    key_edge_label.set('attr.name', 'label')
    key_edge_label.set('attr.type', 'string')

    # Create graph element
    graph_elem = ET.SubElement(root, 'graph')
    graph_elem.set('id', graph.id)
    graph_elem.set('edgedefault', 'directed')

    # Add nodes
    for node in graph.get_all_nodes():
        node_elem = ET.SubElement(graph_elem, 'node')
        node_elem.set('id', node.id)

        # Add node attributes
        label_data = ET.SubElement(node_elem, 'data')
        label_data.set('key', 'node_label')
        label_data.text = node.text

        x_data = ET.SubElement(node_elem, 'data')
        x_data.set('key', 'node_x')
        x_data.text = str(node.x)

        y_data = ET.SubElement(node_elem, 'data')
        y_data.set('key', 'node_y')
        y_data.text = str(node.y)

    # Add edges
    for edge in graph.get_all_edges():
        edge_elem = ET.SubElement(graph_elem, 'edge')
        edge_elem.set('id', edge.id)
        edge_elem.set('source', edge.source_id)
        edge_elem.set('target', edge.target_id)

        # Add edge attributes
        label_data = ET.SubElement(edge_elem, 'data')
        label_data.set('key', 'edge_label')
        label_data.text = edge.text

    # Write to file
    tree = ET.ElementTree(root)
    tree.write(filename, encoding='utf-8', xml_declaration=True)


def import_graph_graphml(filename: str) -> m_graph.Graph:
    """Import a graph from GraphML format."""

    tree = ET.parse(filename)
    root = tree.getroot()

    # Find namespace
    namespace = {'graphml': 'http://graphml.graphdrawing.org/xmlns'}

    # Create graph
    graph = m_graph.Graph()

    # Find the graph element
    graph_elem = root.find('.//graphml:graph', namespace)
    if graph_elem is None:
        # Try without namespace
        graph_elem = root.find('.//graph')

    if graph_elem is None:
        raise ValueError("No graph element found in GraphML file")

    # Import nodes
    for node_elem in graph_elem.findall('.//node'):
        node_id = node_elem.get('id')

        # Extract node data
        label = ''
        x = 0.0
        y = 0.0

        for data_elem in node_elem.findall('data'):
            key = data_elem.get('key')
            if key == 'node_label':
                label = data_elem.text or ''
            elif key == 'node_x':
                x = float(data_elem.text or 0)
            elif key == 'node_y':
                y = float(data_elem.text or 0)

        node = m_node.Node(x=x, y=y, text=label, node_id=node_id)
        graph.add_node(node)

    # Import edges
    for edge_elem in graph_elem.findall('.//edge'):
        edge_id = edge_elem.get('id')
        source_id = edge_elem.get('source')
        target_id = edge_elem.get('target')

        # Skip edges with missing source or target
        if not source_id or not target_id:
            continue

        # Extract edge data
        label = ''
        for data_elem in edge_elem.findall('data'):
            key = data_elem.get('key')
            if key == 'edge_label':
                label = data_elem.text or ''

        edge = m_edge.Edge(source_id=source_id,
                    target_id=target_id,
                    text=label,
                    edge_id=edge_id)
        graph.add_edge(edge)

    return graph


def export_graph_dot(graph: m_graph.Graph, filename: str) -> None:
    """Export a graph to DOT format (Graphviz)."""

    ensure_directory_exists(os.path.dirname(filename))

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f'digraph "{graph.name}" {{\n')
        f.write('    rankdir=TB;\n')
        f.write('    node [shape=box];\n')

        # Write nodes
        for node in graph.get_all_nodes():
            f.write(
                f'    "{node.id}" [label="{node.text}", pos="{node.x},{node.y}!"];\n'
            )

        # Write edges
        for edge in graph.get_all_edges():
            f.write(f'    "{edge.source_id}" -> "{edge.target_id}"')
            if edge.text:
                f.write(f' [label="{edge.text}"]')
            f.write(';\n')

        f.write('}\n')


def get_recent_files(max_files: int = 10) -> List[str]:
    """Get list of recently opened files."""

    # This would typically read from a config file or registry
    # For now, return empty list
    return []


def add_recent_file(filename: str, max_files: int = 10) -> None:
    """Add a file to the recent files list."""

    # This would typically write to a config file or registry
    pass


def get_graph_info(filename: str) -> Dict[str, Any]:
    """Get basic information about a graph file without fully loading it."""

    try:
        if get_file_extension(filename) == '.json':
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    'name': data.get('name', 'Unknown'),
                    'node_count': len(data.get('nodes', [])),
                    'edge_count': len(data.get('edges', [])),
                    'file_size': os.path.getsize(filename),
                    'modified_time': os.path.getmtime(filename)
                }
        else:
            return {
                'name': os.path.basename(filename),
                'node_count': 0,
                'edge_count': 0,
                'file_size': os.path.getsize(filename),
                'modified_time': os.path.getmtime(filename)
            }
    except Exception:
        return {
            'name': os.path.basename(filename),
            'node_count': 0,
            'edge_count': 0,
            'file_size': 0,
            'modified_time': 0
        }


def validate_graph_file(filename: str) -> bool:
    """Validate that a file is a valid graph file."""

    try:
        if get_file_extension(filename) == '.json':
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Check required fields
                return 'nodes' in data and 'edges' in data
        return True  # Assume other formats are valid
    except Exception:
        return False


def create_sample_graph() -> m_graph.Graph:
    """Create a sample graph for testing purposes."""

    graph = m_graph.Graph("Sample Graph")

    # Add sample nodes
    node1 = graph.create_node(0, 0, text="Node 1")
    node2 = graph.create_node(100, 0, text="Node 2")
    node3 = graph.create_node(50, 100, text="Node 3")

    # Add sample edges
    graph.create_edge(node1.id, node2.id, text="Edge 1-2")
    graph.create_edge(node2.id, node3.id, text="Edge 2-3")
    graph.create_edge(node1.id, node3.id, text="Edge 1-3")

    return graph
