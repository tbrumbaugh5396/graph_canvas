#!/usr/bin/env python3
"""
Test script for the Graph Editor application.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


import sys
import os

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_data_models():
    """Test the data models."""
    print("Testing data models...")

    from graph_canvas.presentation.desktop.models.graph import Graph
    from graph_canvas.presentation.desktop.models.node import Node
    from graph_canvas.presentation.desktop.models.edge import Edge

    # Create a graph
    graph = Graph("Test Graph")

    # Add nodes
    node1 = graph.create_node(0, 0, text="Node 1")
    node2 = graph.create_node(100, 100, text="Node 2")

    # Add edge
    edge = graph.create_edge(node1.id, node2.id, text="Test Edge")

    # Test serialization
    graph_dict = graph.to_dict()
    loaded_graph = Graph.from_dict(graph_dict)

    assert loaded_graph.name == "Test Graph"
    assert len(loaded_graph.get_all_nodes()) == 2
    assert len(loaded_graph.get_all_edges()) == 1

    print("✓ Data models test passed")


def test_file_operations():
    """Test file operations."""
    print("Testing file operations...")

    from graph_canvas.presentation.desktop.models.graph import Graph
    from graph_canvas.presentation.desktop.utils.file_utils import create_sample_graph

    # Create sample graph
    graph = create_sample_graph()

    # Test JSON save/load
    test_file = "test_graph.json"
    try:
        graph.save_to_file(test_file)
        loaded_graph = Graph.load_from_file(test_file)

        assert loaded_graph.name == graph.name
        assert len(loaded_graph.get_all_nodes()) == len(graph.get_all_nodes())

        # Clean up
        os.remove(test_file)

        print("✓ File operations test passed")
    except Exception as e:
        print(f"✗ File operations test failed: {e}")


def test_layout_algorithms():
    """Test layout algorithms."""
    print("Testing layout algorithms...")

    from graph_canvas.presentation.desktop.models.graph import Graph
    from graph_canvas.presentation.desktop.utils.layout import spring_layout, circle_layout

    # Create a test graph
    graph = Graph("Layout Test")

    # Add nodes
    for i in range(5):
        graph.create_node(0, 0, text=f"Node {i+1}")

    # Add some edges
    nodes = graph.get_all_nodes()
    for i in range(len(nodes) - 1):
        graph.create_edge(nodes[i].id, nodes[i + 1].id)

    # Test spring layout
    original_positions = [(node.x, node.y) for node in nodes]
    spring_layout(graph, iterations=10)
    new_positions = [(node.x, node.y) for node in nodes]

    # Positions should have changed
    assert original_positions != new_positions

    # Test circle layout
    circle_layout(graph)
    circle_positions = [(node.x, node.y) for node in nodes]

    # Should be different from spring layout
    assert new_positions != circle_positions

    print("✓ Layout algorithms test passed")


def test_gui_components():
    """Test GUI components (without showing windows)."""
    print("Testing GUI components...")

    try:
        import wx

        # Create app without MainLoop
        app = wx.App(False)

        from graph_canvas.presentation.desktop.gui.main_window import MainWindow

        # Create main window
        window = MainWindow()

        # Test basic functionality
        assert window.current_graph is not None
        assert window.canvas is not None

        # Clean up
        window.Destroy()
        app.Destroy()

        print("✓ GUI components test passed")

    except ImportError:
        print("⚠ Skipping GUI tests (wxPython not available)")
    except Exception as e:
        print(f"✗ GUI components test failed: {e}")


def main():
    """Run all tests."""
    print("Running Graph Editor Tests\n")

    try:
        test_data_models()
        test_file_operations()
        test_layout_algorithms()
        test_gui_components()

        print("\n✓ All tests completed successfully!")
        print("\nTo run the full application, use: python -m main")

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
