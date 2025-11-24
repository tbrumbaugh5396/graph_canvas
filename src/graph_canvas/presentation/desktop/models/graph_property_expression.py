"""
Graph property expressions with logical connectives.
"""

from enum import Enum, auto
from typing import List, Optional, Dict, Any, Set, Callable, Union
from dataclasses import dataclass
from enum import Enum, auto

import graph_canvas.presentation.desktop.models.graph_restrictions as m_graph_restrictions
import graph_canvas.presentation.desktop.models.base_graph as m_base_graph


class LogicalOperator(Enum):
    """Logical operators for combining properties."""
    AND = auto()
    OR = auto()
    NOT = auto()
    IMPLIES = auto()  # A implies B is equivalent to (NOT A) OR B


@dataclass
class PropertyTerm:
    """A single property or restriction term."""
    is_restriction: bool  # True if GraphRestriction, False if GraphRequirement
    value: Union[m_graph_restrictions.GraphRestriction, m_graph_restrictions.GraphRequirement]


@dataclass
class PropertyExpression:
    """
    A property expression that can be evaluated on a graph.
    Can be a single term or a combination of terms with logical operators.
    """
    operator: Optional[LogicalOperator]  # None for leaf nodes (single terms)
    terms: List['PropertyExpression']  # Empty for leaf nodes
    term: Optional[PropertyTerm]  # None for non-leaf nodes
    
    @classmethod
    def create_term(cls, term: PropertyTerm) -> 'PropertyExpression':
        """Create a leaf node expression with a single term."""
        return cls(operator=None, terms=[], term=term)
    
    @classmethod
    def create_not(cls, expr: 'PropertyExpression') -> 'PropertyExpression':
        """Create a NOT expression."""
        return cls(operator=LogicalOperator.NOT, terms=[expr], term=None)
    
    @classmethod
    def create_and(cls, exprs: List['PropertyExpression']) -> 'PropertyExpression':
        """Create an AND expression."""
        return cls(operator=LogicalOperator.AND, terms=exprs, term=None)
    
    @classmethod
    def create_or(cls, exprs: List['PropertyExpression']) -> 'PropertyExpression':
        """Create an OR expression."""
        return cls(operator=LogicalOperator.OR, terms=exprs, term=None)
    
    @classmethod
    def create_implies(cls, antecedent: 'PropertyExpression', consequent: 'PropertyExpression') -> 'PropertyExpression':
        """Create an IMPLIES expression (antecedent -> consequent)."""
        not_antecedent = cls.create_not(antecedent)
        return cls.create_or([not_antecedent, consequent])
    
    def evaluate(self, graph: 'm_base_graph.BaseGraph') -> bool:
        """
        Evaluate the expression on a graph.
        Returns True if the expression is satisfied.
        """
        if self.term is not None:  # Leaf node
            # Temporarily add the term to graph constraints and check for errors
            if self.term.is_restriction:
                old_restrictions = graph.constraints.restrictions.copy()
                graph.constraints.restrictions = {self.term.value}
            else:
                old_requirements = graph.constraints.requirements.copy()
                graph.constraints.requirements = {self.term.value}
            
            errors = graph.validate()
            
            # Restore original constraints
            if self.term.is_restriction:
                graph.constraints.restrictions = old_restrictions
            else:
                graph.constraints.requirements = old_requirements
            
            return not errors
        
        # Non-leaf node
        if self.operator == LogicalOperator.NOT:
            return not self.terms[0].evaluate(graph)
        elif self.operator == LogicalOperator.AND:
            return all(term.evaluate(graph) for term in self.terms)
        elif self.operator == LogicalOperator.OR:
            return any(term.evaluate(graph) for term in self.terms)
        else:
            raise ValueError(f"Unknown operator: {self.operator}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert expression to a dictionary for serialization."""
        if self.term is not None:
            return {
                "type": "term",
                "is_restriction": self.term.is_restriction,
                "value": self.term.value.name
            }
        return {
            "type": "operator",
            "operator": self.operator.name,
            "terms": [term.to_dict() for term in self.terms]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PropertyExpression':
        """Create expression from a dictionary."""
        if data["type"] == "term":
            value = (m_graph_restrictions.GraphRestriction[data["value"]] 
                    if data["is_restriction"] 
                    else m_graph_restrictions.GraphRequirement[data["value"]])
            term = PropertyTerm(is_restriction=data["is_restriction"], value=value)
            return cls.create_term(term)
        
        operator = LogicalOperator[data["operator"]]
        terms = [cls.from_dict(term_data) for term_data in data["terms"]]
        return cls(operator=operator, terms=terms, term=None)
    
    def get_validation_errors(self, graph: 'm_base_graph.BaseGraph') -> List[str]:
        """Get validation errors for this expression."""
        if self.term is not None:  # Leaf node
            if self.term.is_restriction:
                old_restrictions = graph.constraints.restrictions.copy()
                graph.constraints.restrictions = {self.term.value}
            else:
                old_requirements = graph.constraints.requirements.copy()
                graph.constraints.requirements = {self.term.value}
            
            errors = graph.validate()
            
            # Restore original constraints
            if self.term.is_restriction:
                graph.constraints.restrictions = old_restrictions
            else:
                graph.constraints.requirements = old_requirements
            
            return errors
        
        # Non-leaf node
        if self.operator == LogicalOperator.NOT:
            if self.terms[0].evaluate(graph):
                return ["NOT expression is false"]
            return []
        elif self.operator == LogicalOperator.AND:
            return [error 
                   for term in self.terms 
                   for error in term.get_validation_errors(graph)]
        elif self.operator == LogicalOperator.OR:
            if not any(term.evaluate(graph) for term in self.terms):
                return ["No OR terms are satisfied"]
            return []
        else:
            raise ValueError(f"Unknown operator: {self.operator}")
    
    def __str__(self) -> str:
        """Convert expression to string for display."""
        if self.term is not None:
            return self.term.value.name
        
        if self.operator == LogicalOperator.NOT:
            return f"NOT ({self.terms[0]})"
        elif self.operator == LogicalOperator.AND:
            return f"({' AND '.join(str(term) for term in self.terms)})"
        elif self.operator == LogicalOperator.OR:
            return f"({' OR '.join(str(term) for term in self.terms)})"
        else:
            raise ValueError(f"Unknown operator: {self.operator}")
