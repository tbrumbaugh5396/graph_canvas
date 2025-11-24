"""
Graph algorithms package.
"""


from .list_algorithms import (
    linear_search,
    binary_search,
    reverse_list,
    quicksort,
    mergesort,
    bubblesort,
    map_list,
    filter_list,
    reduce_list
)

from .tree_algorithms import (
    preorder_traversal,
    inorder_traversal,
    postorder_traversal,
    levelorder_traversal,
    compute_depth,
    compute_height,
    lowest_common_ancestor,
    compute_tree_diameter,
    balance_avl,
    is_binary_search_tree,
    binary_search_tree_operations
)

from .dag_algorithms import (
    topological_sort_kahn,
    topological_sort_dfs,
    detect_cycle,
    critical_path,
    shortest_paths_dag,
    transitive_closure,
    longest_path_dag,
    minimum_height_dag,
    is_dag,
    count_paths,
    layer_assignment
)

from .graph_algorithms import (
    depth_first_search,
    breadth_first_search,
    dijkstra_shortest_path,
    a_star_search,
    bellman_ford_shortest_path,
    kruskal_minimum_spanning_tree,
    prim_minimum_spanning_tree,
    find_cycles,
    find_connected_components,
    graph_coloring,
    ford_fulkerson_max_flow,
    centrality_measures
)

from .hypergraph_algorithms import (
    hypergraph_traversal,
    hypergraph_cut,
    hypergraph_clustering,
    minimal_transversals,
    dual_hypergraph,
    set_cover_approximation,
    connected_components_hypergraph,
    s_t_connectivity
)

from .nested_graph_algorithms import (
    flatten_nested_graph,
    recursive_traversal,
    pattern_matching,
    hierarchical_clustering,
    query_nested_graph
)

from .ubergraph_algorithms import (
    semantic_subgraph_matching,
    ontology_based_query,
    hypergraph_to_ubergraph,
    provenance_tracking,
    multigraph_traversal,
    recursive_edge_matching,
    inference_engine
)

from .graph_properties import (
    is_cyclic,
    analyze_connectivity,
    analyze_graph_type,
    analyze_density,
    is_planar,
    find_eulerian_path,
    find_hamiltonian_path,
    find_hamiltonian_circuit,
    analyze_euler_hamilton_properties,
    analyze_direction_properties,
    find_direction_violations,
    convert_graph_direction
)


__all__ = [
    # List algorithms
    'linear_search',
    'binary_search',
    'reverse_list',
    'quicksort',
    'mergesort',
    'bubblesort',
    'map_list',
    'filter_list',
    'reduce_list',
    
    # Tree algorithms
    'preorder_traversal',
    'inorder_traversal',
    'postorder_traversal',
    'levelorder_traversal',
    'compute_depth',
    'compute_height',
    'lowest_common_ancestor',
    'compute_tree_diameter',
    'balance_avl',
    'is_binary_search_tree',
    'binary_search_tree_operations',
    
    # DAG algorithms
    'topological_sort_kahn',
    'topological_sort_dfs',
    'detect_cycle',
    'critical_path',
    'shortest_paths_dag',
    'transitive_closure',
    'longest_path_dag',
    'minimum_height_dag',
    'is_dag',
    'count_paths',
    'layer_assignment',
    
    # Graph algorithms
    'depth_first_search',
    'breadth_first_search',
    'dijkstra_shortest_path',
    'a_star_search',
    'bellman_ford_shortest_path',
    'kruskal_minimum_spanning_tree',
    'prim_minimum_spanning_tree',
    'find_cycles',
    'find_connected_components',
    'graph_coloring',
    'ford_fulkerson_max_flow',
    'centrality_measures',
    
    # Hypergraph algorithms
    'hypergraph_traversal',
    'hypergraph_cut',
    'hypergraph_clustering',
    'minimal_transversals',
    'dual_hypergraph',
    'set_cover_approximation',
    'connected_components_hypergraph',
    's_t_connectivity',
    
    # Nested graph algorithms
    'flatten_nested_graph',
    'recursive_traversal',
    'pattern_matching',
    'hierarchical_clustering',
    'query_nested_graph',
    
    # Ubergraph algorithms
    'semantic_subgraph_matching',
    'ontology_based_query',
    'hypergraph_to_ubergraph',
    'provenance_tracking',
    'multigraph_traversal',
    'recursive_edge_matching',
    'inference_engine',
    
    # Graph properties
    'is_cyclic',
    'analyze_connectivity',
    'analyze_graph_type',
    'analyze_density',
    'is_planar',
    'find_eulerian_path',
    'find_hamiltonian_path',
    'find_hamiltonian_circuit',
    'analyze_euler_hamilton_properties',
    'analyze_direction_properties',
    'find_direction_violations',
    'convert_graph_direction'
]
