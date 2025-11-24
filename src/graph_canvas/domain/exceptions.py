"""Domain-specific exceptions."""


class GraphAlreadyExistsError(Exception):
    """Raised when attempting to insert a graph that already exists."""


class GraphNotFoundError(Exception):
    """Raised when a graph could not be located."""


class NodeNotFoundError(Exception):
    """Raised when a node could not be located within a graph."""


class EdgeNotFoundError(Exception):
    """Raised when an edge could not be located within a graph."""

