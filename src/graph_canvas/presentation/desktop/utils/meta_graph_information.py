"""
Holds meta information about graph-level settings and restrictions.
"""


class MetaGraphInformation:
    def __init__(self):
        # Whether self-loops are allowed in the current graph
        self.no_loops = False
        # Whether multiple edges between the same pair of nodes are allowed
        self.no_multigraphs = False
        # 0 = No Restrictions, 1 = Directed only, 2 = Undirected only
        self.graph_type_restriction = 0
        # Selected graph type in the UI (project-specific enum/index)
        self.selected_graph_type = 0


