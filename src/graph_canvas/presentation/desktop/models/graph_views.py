"""
Graph view factory and view type definitions.
"""


from typing import Dict, Any, Optional, Type, Union

import graph_canvas.presentation.desktop.models.base_graph as m_base_graph
import graph_canvas.presentation.desktop.models.list_graph as m_list_graph
import graph_canvas.presentation.desktop.models.tree_graph as m_tree_graph
import graph_canvas.presentation.desktop.models.dag_graph as m_dag_graph
import graph_canvas.presentation.desktop.models.basic_graph as m_basic_graph
import graph_canvas.presentation.desktop.models.hypergraph as m_hypergraph
import graph_canvas.presentation.desktop.models.nested_graph as m_nested_graph
import graph_canvas.presentation.desktop.models.ubergraph as m_ubergraph
import graph_canvas.presentation.desktop.models.typed_ubergraph as m_typed_ubergraph
import graph_canvas.presentation.desktop.models.data_views as m_data_views
# from graph_canvas.presentation.desktop.models.data_views import (
#     AdjacencyListView,
#     EdgeListView,
#     ParentMapView,
#     AdjacencyMatrixView,
#     IncidenceMatrixView,
#     IncidenceListView,
#     DualIncidenceListView,
#     HierarchicalDictView,
#     GraphOfGraphsView,
#     RecursiveIncidenceView,
#     DirectedAcyclicMetagraphView
# )


# Define available views for each graph type
GRAPH_VIEWS = {
    m_list_graph.ListGraph: {
        "adjacency_list": m_data_views.AdjacencyListView,
        "edge_list": m_data_views.EdgeListView,
        "parent_map": m_data_views.ParentMapView
    },
    m_tree_graph.TreeGraph: {
        "adjacency_list": m_data_views.AdjacencyListView,
        "parent_map": m_data_views.ParentMapView,
        "edge_list": m_data_views.EdgeListView
    },
    m_dag_graph.DAGGraph: {
        "adjacency_list": m_data_views.AdjacencyListView,
        "adjacency_matrix": m_data_views.AdjacencyMatrixView,
        "edge_list": m_data_views.EdgeListView
    },
    m_basic_graph.BasicGraph: {
        "adjacency_list": m_data_views.AdjacencyListView,
        "adjacency_matrix": m_data_views.AdjacencyMatrixView,
        "edge_list": m_data_views.EdgeListView,
        "incidence_matrix": m_data_views.IncidenceMatrixView
    },
    m_hypergraph.Hypergraph: {
        "incidence_list": m_data_views.IncidenceListView,
        "dual_incidence_list": m_data_views.DualIncidenceListView,
        "incidence_matrix": m_data_views.IncidenceMatrixView,
        "line_graph": m_data_views.EdgeListView,  # Special case - returns line graph edges
        "derivative_graph": m_data_views.EdgeListView  # Special case - returns derivative graph edges
    },
    m_nested_graph.NestedGraph: {
        "hierarchical_dict": m_data_views.HierarchicalDictView,
        "graph_of_graphs": m_data_views.GraphOfGraphsView
    },
    m_ubergraph.Ubergraph: {
        "recursive_incidence": m_data_views.RecursiveIncidenceView,
        "directed_acyclic_metagraph": m_data_views.DirectedAcyclicMetagraphView,
        "adjacency_matrix": m_data_views.AdjacencyMatrixView,
        "adjacency_list": m_data_views.AdjacencyListView
    },
    m_typed_ubergraph.TypedUbergraph: {
        "recursive_incidence": m_data_views.RecursiveIncidenceView,
        "directed_acyclic_metagraph": m_data_views.DirectedAcyclicMetagraphView,
        "adjacency_matrix": m_data_views.AdjacencyMatrixView,
        "adjacency_list": m_data_views.AdjacencyListView
    }
}


def get_available_views(graph: "m_base_graph.BaseGraph") -> Dict[str, Type]:
    """Get available view types for a graph."""

    graph_type = type(graph)
    return GRAPH_VIEWS.get(graph_type, {})


def create_view(graph: "m_base_graph.BaseGraph", view_type: str) -> Optional[Any]:
    """Create a view of the specified type for a graph."""

    available_views = get_available_views(graph)
    view_class = available_views.get(view_type)
    
    if view_class:
        if view_type == "line_graph" and isinstance(graph, Hypergraph):
            return graph.get_line_graph()
        elif view_type == "derivative_graph" and isinstance(graph, Hypergraph):
            return graph.get_derivative_graph()
        else:
            return view_class(graph)
    
    return None
