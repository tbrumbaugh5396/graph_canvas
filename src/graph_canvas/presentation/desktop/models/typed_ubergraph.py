"""
Typed ubergraph model that extends ubergraphs with type information and constraints.
"""


from typing import Dict, List, Set, Optional, Any, Tuple, Type, Union

import graph_canvas.presentation.desktop.models.ubergraph as m_ubergraph
import graph_canvas.presentation.desktop.models.node as m_node
import graph_canvas.presentation.desktop.models.edge as m_edge


class TypedUberEdge(m_ubergraph.UberEdge):
    """Extended uber-edge class with type information."""
    
    def __init__(self, *args, edge_type: str = "default", **kwargs):
        super().__init__(*args, **kwargs)
        self.edge_type = edge_type
        self.allowed_source_types: Set[str] = set()
        self.allowed_target_types: Set[str] = set()
        self.metadata["edge_type"] = edge_type

    def add_allowed_source_type(self, type_name: str) -> None:
        """Add an allowed type for source connections."""

        self.allowed_source_types.add(type_name)

    def add_allowed_target_type(self, type_name: str) -> None:
        """Add an allowed type for target connections."""

        self.allowed_target_types.add(type_name)

    def can_connect_from(self, source: Union[m_node.Node, 'TypedUberEdge']) -> bool:
        """Check if this edge can accept a connection from the given source."""

        if isinstance(source, m_node.Node):
            return (not self.allowed_source_types or
                   source.metadata.get("node_type") in self.allowed_source_types)
        else:
            return (not self.allowed_source_types or
                   source.edge_type in self.allowed_source_types)

    def can_connect_to(self, target: Union[m_node.Node, 'TypedUberEdge']) -> bool:
        """Check if this edge can connect to the given target."""

        if isinstance(target, m_node.Node):
            return (not self.allowed_target_types or
                   target.metadata.get("node_type") in self.allowed_target_types)
        else:
            return (not self.allowed_target_types or
                   target.edge_type in self.allowed_target_types)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the typed uber-edge to a dictionary."""

        data = super().to_dict()
        data.update({
            "edge_type": self.edge_type,
            "allowed_source_types": list(self.allowed_source_types),
            "allowed_target_types": list(self.allowed_target_types)
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TypedUberEdge':
        """Create a typed uber-edge from a dictionary."""

        edge = super().from_dict(data)
        edge.edge_type = data.get("edge_type", "default")
        edge.allowed_source_types = set(data.get("allowed_source_types", []))
        edge.allowed_target_types = set(data.get("allowed_target_types", []))
        return edge


class TypeSystem:
    """System for managing types and their relationships."""
    
    def __init__(self):
        self.node_types: Dict[str, Dict[str, Any]] = {}
        self.edge_types: Dict[str, Dict[str, Any]] = {}
        self.type_hierarchy: Dict[str, Set[str]] = {}  # type -> subtypes
        self.type_constraints: Dict[str, Dict[str, Set[str]]] = {}  # type -> {source_types, target_types}

    def add_node_type(self, type_name: str, properties: Optional[Dict[str, Any]] = None) -> None:
        """Add a node type definition."""

        self.node_types[type_name] = properties or {}

    def add_edge_type(self, type_name: str, properties: Optional[Dict[str, Any]] = None) -> None:
        """Add an edge type definition."""

        self.edge_types[type_name] = properties or {}

    def add_subtype(self, parent_type: str, child_type: str) -> None:
        """Add a subtype relationship."""

        if parent_type not in self.type_hierarchy:
            self.type_hierarchy[parent_type] = set()
        self.type_hierarchy[parent_type].add(child_type)

    def add_type_constraint(self, type_name: str,
                          allowed_source_types: Optional[Set[str]] = None,
                          allowed_target_types: Optional[Set[str]] = None) -> None:
        """Add connection constraints for a type."""

        if type_name not in self.type_constraints:
            self.type_constraints[type_name] = {
                "source_types": set(),
                "target_types": set()
            }
        
        if allowed_source_types is not None:
            self.type_constraints[type_name]["source_types"].update(allowed_source_types)
        if allowed_target_types is not None:
            self.type_constraints[type_name]["target_types"].update(allowed_target_types)

    def is_subtype_of(self, type_name: str, potential_parent: str) -> bool:
        """Check if one type is a subtype of another."""

        if type_name == potential_parent:
            return True
        
        for parent, children in self.type_hierarchy.items():
            if type_name in children:
                return parent == potential_parent or self.is_subtype_of(parent, potential_parent)
        
        return False

    def get_all_subtypes(self, type_name: str) -> Set[str]:
        """Get all subtypes of a type (including indirect)."""

        subtypes = set()
        
        def collect_subtypes(current_type: str) -> None:
            if current_type in self.type_hierarchy:
                for subtype in self.type_hierarchy[current_type]:
                    subtypes.add(subtype)
                    collect_subtypes(subtype)
        
        collect_subtypes(type_name)
        return subtypes

    def can_connect(self, source_type: str, edge_type: str, target_type: str) -> bool:
        """Check if types can be connected through an edge type."""

        if edge_type not in self.type_constraints:
            return True  # No constraints defined
        
        constraints = self.type_constraints[edge_type]
        
        # Check source constraints
        if constraints["source_types"]:
            valid_source = False
            for allowed_type in constraints["source_types"]:
                if self.is_subtype_of(source_type, allowed_type):
                    valid_source = True
                    break
            if not valid_source:
                return False
        
        # Check target constraints
        if constraints["target_types"]:
            valid_target = False
            for allowed_type in constraints["target_types"]:
                if self.is_subtype_of(target_type, allowed_type):
                    valid_target = True
                    break
            if not valid_target:
                return False
        
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert the type system to a dictionary."""

        return {
            "node_types": self.node_types,
            "edge_types": self.edge_types,
            "type_hierarchy": {k: list(v) for k, v in self.type_hierarchy.items()},
            "type_constraints": {
                k: {
                    "source_types": list(v["source_types"]),
                    "target_types": list(v["target_types"])
                }
                for k, v in self.type_constraints.items()
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TypeSystem':
        """Create a type system from a dictionary."""

        system = cls()
        system.node_types = data.get("node_types", {})
        system.edge_types = data.get("edge_types", {})
        system.type_hierarchy = {
            k: set(v) for k, v in data.get("type_hierarchy", {}).items()
        }
        system.type_constraints = {
            k: {
                "source_types": set(v["source_types"]),
                "target_types": set(v["target_types"])
            }
            for k, v in data.get("type_constraints", {}).items()
        }
        return system


class TypedUbergraph(m_ubergraph.Ubergraph):
    """A graph that extends ubergraphs with type information and constraints."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metadata["graph_type"] = "typed_ubergraph"
        self.type_system = TypeSystem()

    def add_node(self, node: m_node.Node, node_type: str = "default") -> None:
        """Add a node with type information."""

        node.metadata["node_type"] = node_type
        super().add_node(node)

    def add_edge(self, edge: m_edge.Edge) -> None:
        """Add an edge, converting to TypedUberEdge if needed."""

        if not isinstance(edge, TypedUberEdge):
            typed_edge = TypedUberEdge(
                id=edge.id,
                source_id=edge.source_id,
                target_id=edge.target_id,
                directed=edge.directed,
                edge_type=edge.metadata.get("edge_type", "default")
            )
            if hasattr(edge, 'source_ids'):
                typed_edge.source_ids = edge.source_ids
            if hasattr(edge, 'target_ids'):
                typed_edge.target_ids = edge.target_ids
            edge = typed_edge
        super().add_edge(edge)

    def can_connect(self, source_id: str, edge_id: str, target_id: str) -> bool:
        """Check if nodes/edges can be connected based on type constraints."""

        source = self.get_node(source_id) or self.get_edge(source_id)
        edge = self.get_edge(edge_id)
        target = self.get_node(target_id) or self.get_edge(target_id)
        
        if not (source and edge and target):
            return False
        
        source_type = (source.metadata.get("node_type", "default") if isinstance(source, m_node.Node)
                      else source.edge_type if isinstance(source, TypedUberEdge)
                      else "default")
        
        target_type = (target.metadata.get("node_type", "default") if isinstance(target, m_node.Node)
                      else target.edge_type if isinstance(target, TypedUberEdge)
                      else "default")
        
        return self.type_system.can_connect(source_type, edge.edge_type, target_type)

    def get_compatible_sources(self, edge_id: str) -> List[Union[m_node.Node, TypedUberEdge]]:
        """Get all nodes/edges that can be sources for this edge."""

        edge = self.get_edge(edge_id)
        if not isinstance(edge, TypedUberEdge):
            return []
        
        compatible = []
        
        # Check nodes
        for node in self.get_all_nodes():
            if edge.can_connect_from(node):
                compatible.append(node)
        
        # Check edge-as-nodes
        for other in self._edges.values():
            if (isinstance(other, TypedUberEdge) and
                other.metadata.get("is_uber_node") and
                edge.can_connect_from(other)):
                compatible.append(other)
        
        return compatible

    def get_compatible_targets(self, edge_id: str) -> List[Union[m_node.Node, TypedUberEdge]]:
        """Get all nodes/edges that can be targets for this edge."""

        edge = self.get_edge(edge_id)
        if not isinstance(edge, TypedUberEdge):
            return []
        
        compatible = []
        
        # Check nodes
        for node in self.get_all_nodes():
            if edge.can_connect_to(node):
                compatible.append(node)
        
        # Check edge-as-nodes
        for other in self._edges.values():
            if (isinstance(other, TypedUberEdge) and
                other.metadata.get("is_uber_node") and
                edge.can_connect_to(other)):
                compatible.append(other)
        
        return compatible

    def validate(self) -> List[str]:
        """Validate the typed ubergraph structure."""

        errors = super().validate()
        
        # Check type constraints
        for edge in self._edges.values():
            if isinstance(edge, TypedUberEdge):
                # Check source connections
                source = self.get_node(edge.source_id) or self.get_edge(edge.source_id)
                if source and not edge.can_connect_from(source):
                    errors.append(f"Edge {edge.id} has invalid source type")
                
                # Check target connections
                target = self.get_node(edge.target_id) or self.get_edge(edge.target_id)
                if target and not edge.can_connect_to(target):
                    errors.append(f"Edge {edge.id} has invalid target type")
                
                # Check hyperedge connections
                for node_id in edge.source_ids:
                    source = self.get_node(node_id) or self.get_edge(node_id)
                    if source and not edge.can_connect_from(source):
                        errors.append(f"Edge {edge.id} has invalid source type in hyperedge")
                
                for node_id in edge.target_ids:
                    target = self.get_node(node_id) or self.get_edge(node_id)
                    if target and not edge.can_connect_to(target):
                        errors.append(f"Edge {edge.id} has invalid target type in hyperedge")
        
        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert the typed ubergraph to a dictionary."""

        data = super().to_dict()
        data["type_system"] = self.type_system.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TypedUbergraph':
        """Create a typed ubergraph from a dictionary."""

        graph = super().from_dict(data)
        if "type_system" in data:
            graph.type_system = TypeSystem.from_dict(data["type_system"])
        return graph
