"""
Defines graph restrictions and requirements.
"""

from enum import Enum, auto
from typing import Dict, Any, Set


class GraphRestriction(Enum):
    """Enumeration of possible graph restrictions."""
    # Basic structure restrictions
    NO_LOOPS = auto()           # No self-loops allowed
    NO_MULTIEDGES = auto()      # No multiple edges between same nodes
    SIMPLE = auto()             # No loops or multiple edges
    
    # Direction restrictions
    DIRECTED = auto()           # All edges must be directed
    UNDIRECTED = auto()         # All edges must be undirected
    
    # Connectivity restrictions
    ACYCLIC = auto()            # No cycles allowed
    CONNECTED = auto()          # Must be connected
    STRONGLY_CONNECTED = auto() # Must be strongly connected
    WEAKLY_CONNECTED = auto()   # Must be weakly connected
    
    # Graph type restrictions
    PLANAR = auto()            # Must be planar
    BIPARTITE = auto()         # Must be bipartite
    TREE = auto()              # Must be a tree
    DAG = auto()               # Must be a directed acyclic graph
    FOREST = auto()            # Must be a forest (collection of trees)


class GraphRequirement(Enum):
    """Enumeration of possible graph requirements."""
    # Degree requirements
    MIN_DEGREE_1 = auto()       # Each node must have degree >= 1
    MIN_DEGREE_2 = auto()       # Each node must have degree >= 2
    MIN_DEGREE_3 = auto()       # Each node must have degree >= 3
    MAX_DEGREE_2 = auto()       # Each node must have degree <= 2
    MAX_DEGREE_3 = auto()       # Each node must have degree <= 3
    MAX_DEGREE_4 = auto()       # Each node must have degree <= 4
    
    # In/Out degree requirements for directed graphs
    MIN_IN_DEGREE_1 = auto()    # Each node must have in-degree >= 1
    MIN_OUT_DEGREE_1 = auto()   # Each node must have out-degree >= 1
    MAX_IN_DEGREE_1 = auto()    # Each node must have in-degree <= 1
    MAX_OUT_DEGREE_1 = auto()   # Each node must have out-degree <= 1
    
    # Path requirements
    HAS_EULER_PATH = auto()     # Must have an Euler path
    HAS_EULER_CIRCUIT = auto()  # Must have an Euler circuit
    HAS_HAMILTON_PATH = auto()  # Must have a Hamilton path
    HAS_HAMILTON_CYCLE = auto() # Must have a Hamilton cycle
    
    # Tree/Forest requirements
    IS_BINARY_TREE = auto()     # Must be a binary tree
    IS_FULL_BINARY = auto()     # Must be a full binary tree
    IS_PERFECT_BINARY = auto()  # Must be a perfect binary tree
    IS_COMPLETE_BINARY = auto() # Must be a complete binary tree
    IS_BALANCED = auto()        # Must be a balanced tree
    
    # Special graph requirements
    IS_REGULAR = auto()         # All nodes must have same degree
    IS_COMPLETE = auto()        # Must be a complete graph
    IS_TOURNAMENT = auto()      # Must be a tournament graph
    IS_FLOW_NETWORK = auto()    # Must be a valid flow network


class GraphConstraints:
    """Container for graph restrictions and requirements."""
    
    def __init__(self):
        self.restrictions: Set[GraphRestriction] = set()
        self.requirements: Set[GraphRequirement] = set()

    def add_restriction(self, restriction: GraphRestriction) -> None:
        """Add a restriction to the graph."""
        self.restrictions.add(restriction)

    def remove_restriction(self, restriction: GraphRestriction) -> None:
        """Remove a restriction from the graph."""
        self.restrictions.discard(restriction)

    def add_requirement(self, requirement: GraphRequirement) -> None:
        """Add a requirement to the graph."""
        self.requirements.add(requirement)

    def remove_requirement(self, requirement: GraphRequirement) -> None:
        """Remove a requirement from the graph."""
        self.requirements.discard(requirement)

    def to_dict(self) -> Dict[str, Any]:
        """Convert constraints to a dictionary for serialization."""
        return {
            'restrictions': [r.name for r in self.restrictions],
            'requirements': [r.name for r in self.requirements]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GraphConstraints':
        """Create constraints from a dictionary."""
        constraints = cls()
        
        # Load restrictions
        for name in data.get('restrictions', []):
            try:
                restriction = GraphRestriction[name]
                constraints.add_restriction(restriction)
            except KeyError:
                print(f"Warning: Unknown restriction '{name}' ignored")

        # Load requirements
        for name in data.get('requirements', []):
            try:
                requirement = GraphRequirement[name]
                constraints.add_requirement(requirement)
            except KeyError:
                print(f"Warning: Unknown requirement '{name}' ignored")

        return constraints